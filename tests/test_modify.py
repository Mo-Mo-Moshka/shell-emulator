"""Тесты команд rm и rmdir, изменяющих VFS в памяти."""

import os
import tempfile
import unittest

from helpers import make_vfs

from emulator.shell import Shell
from emulator.vfs import VfsError, load_vfs, split_path


def exists(shell, path):
    """Истина, если путь есть в VFS сеанса."""
    try:
        shell.vfs.lookup(path)
    except VfsError:
        return False
    return True


class SplitPathTest(unittest.TestCase):
    """Проверки split_path."""

    def test_split(self):
        """Путь делится на родителя и имя."""
        self.assertEqual(split_path("/a/b"), ("/a", "b"))
        self.assertEqual(split_path("/a"), ("/", "a"))
        self.assertEqual(split_path("/"), ("/", ""))


class RmTest(unittest.TestCase):
    """Проверки команды rm."""

    def setUp(self):
        """Создать сеанс с VFS."""
        self.shell = Shell(vfs=make_vfs())

    def test_removes_files(self):
        """rm удаляет один или несколько файлов."""
        result = self.shell.execute("rm readme.txt 'docs/my notes.txt'")
        self.assertEqual((result.output, result.error), ("", ""))
        self.assertFalse(exists(self.shell, "/readme.txt"))
        self.assertFalse(exists(self.shell, "/docs/my notes.txt"))
        self.assertTrue(exists(self.shell, "/docs/a.txt"))

    def test_relative_path(self):
        """Путь считается от текущей папки."""
        self.shell.execute("cd docs")
        self.shell.execute("rm a.txt")
        self.assertFalse(exists(self.shell, "/docs/a.txt"))

    def test_directory_needs_option(self):
        """Папку без -r или -d удалить нельзя."""
        result = self.shell.execute("rm docs")
        self.assertEqual(result.error, "rm: cannot remove 'docs': "
                                       "Is a directory")
        self.assertTrue(exists(self.shell, "/docs"))

    def test_empty_dir_option(self):
        """-d удаляет только пустую папку."""
        self.assertEqual(self.shell.execute("rm -d empty").error, "")
        self.assertFalse(exists(self.shell, "/empty"))
        error = self.shell.execute("rm -d docs").error
        self.assertEqual(error, "rm: cannot remove 'docs': "
                                "Directory not empty")

    def test_recursive_verbose(self):
        """-rv удаляет папку с содержимым и выводит удалённое."""
        result = self.shell.execute("rm -rv docs")
        self.assertEqual(result.output.splitlines(), [
            "removed 'docs/a.txt'",
            "removed 'docs/my notes.txt'",
            "removed 'docs/sub/deep.txt'",
            "removed directory 'docs/sub'",
            "removed directory 'docs'",
        ])
        self.assertFalse(exists(self.shell, "/docs"))

    def test_force(self):
        """-f молча пропускает несуществующие пути."""
        result = self.shell.execute("rm -f nope readme.txt")
        self.assertEqual(result.error, "")
        self.assertFalse(exists(self.shell, "/readme.txt"))
        self.assertEqual(self.shell.execute("rm -f").error, "")

    def test_errors(self):
        """Ошибки rm."""
        self.shell.execute("cd docs/sub")
        cases = {
            "rm": "rm: missing operand",
            "rm nope": "rm: cannot remove 'nope': "
                       "No such file or directory",
            "rm -r /": "rm: it is dangerous to operate recursively on '/'",
            "rm -r ..": "rm: refusing to remove '.' or '..' directory: "
                        "skipping '..'",
            "rm -r /docs": "rm: cannot remove '/docs': "
                           "Device or resource busy",
            "rm -x a": "rm: invalid option -- 'x'",
        }
        for line, message in cases.items():
            with self.subTest(line=line):
                self.assertEqual(self.shell.execute(line).error, message)
        self.assertTrue(exists(self.shell, "/docs/sub/deep.txt"))

    def test_changes_hash(self):
        """После удаления хеш VFS меняется."""
        before = self.shell.vfs.sha256()
        self.shell.execute("rm readme.txt")
        self.assertNotEqual(self.shell.vfs.sha256(), before)


class RmdirTest(unittest.TestCase):
    """Проверки команды rmdir."""

    def setUp(self):
        """Создать сеанс с VFS."""
        self.shell = Shell(vfs=make_vfs())

    def test_removes_empty_directory(self):
        """rmdir удаляет пустую папку."""
        result = self.shell.execute("rmdir empty")
        self.assertEqual((result.output, result.error), ("", ""))
        self.assertFalse(exists(self.shell, "/empty"))

    def test_parents(self):
        """-p удаляет опустевшие родительские папки."""
        self.shell.execute("rm docs/a.txt 'docs/my notes.txt'")
        self.shell.execute("rm docs/sub/deep.txt")
        result = self.shell.execute("rmdir -pv docs/sub")
        self.assertEqual(result.output.splitlines(), [
            "rmdir: removing directory, 'docs/sub'",
            "rmdir: removing directory, 'docs'",
        ])
        self.assertFalse(exists(self.shell, "/docs"))

    def test_parents_stop_at_non_empty(self):
        """-p останавливается на непустой родительской папке."""
        self.shell.execute("rm docs/sub/deep.txt")
        error = self.shell.execute("rmdir -p docs/sub").error
        self.assertEqual(error, "rmdir: failed to remove 'docs': "
                                "Directory not empty")
        self.assertFalse(exists(self.shell, "/docs/sub"))

    def test_errors(self):
        """Ошибки rmdir; папки при этом не удаляются."""
        cases = {
            "rmdir": "rmdir: missing operand",
            "rmdir docs": "rmdir: failed to remove 'docs': "
                          "Directory not empty",
            "rmdir readme.txt": "rmdir: failed to remove 'readme.txt': "
                                "Not a directory",
            "rmdir nope": "rmdir: failed to remove 'nope': "
                          "No such file or directory",
            "rmdir .": "rmdir: failed to remove '.': Invalid argument",
        }
        for line, message in cases.items():
            with self.subTest(line=line):
                self.assertEqual(self.shell.execute(line).error, message)
        self.assertTrue(exists(self.shell, "/docs"))

    def test_current_directory_is_busy(self):
        """Текущую папку удалить нельзя."""
        self.shell.execute("cd empty")
        error = self.shell.execute("rmdir /empty").error
        self.assertEqual(error, "rmdir: failed to remove '/empty': "
                                "Device or resource busy")


class DiskUnchangedTest(unittest.TestCase):
    """Изменения VFS не затрагивают папку на диске."""

    def test_disk_is_not_modified(self):
        """После rm -r и rmdir файлы на диске остаются на месте."""
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "dir", "empty"))
            with open(os.path.join(tmp, "dir", "f.txt"), "w") as file:
                file.write("data")
            before = sorted(os.walk(tmp))
            shell = Shell(vfs=load_vfs(tmp))
            shell.execute("rmdir dir/empty")
            shell.execute("rm -r dir")
            self.assertFalse(exists(shell, "/dir"))
            self.assertEqual(sorted(os.walk(tmp)), before)


if __name__ == "__main__":
    unittest.main()
