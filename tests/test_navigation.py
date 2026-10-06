"""Тесты команд ls и cd, а также поиска путей в VFS."""

import unittest

from helpers import make_vfs

from emulator.shell import Shell
from emulator.vfs import VfsError


class LookupTest(unittest.TestCase):
    """Проверки Vfs.lookup."""

    def setUp(self):
        """Создать VFS для тестов."""
        self.vfs = make_vfs()

    def test_absolute_and_relative_paths(self):
        """Абсолютные и относительные пути, . и .. нормализуются."""
        cases = {
            ("/docs/sub", "/"): "/docs/sub",
            ("sub", "/docs"): "/docs/sub",
            ("./sub/../a.txt", "/docs"): "/docs/a.txt",
            ("../../..", "/docs/sub"): "/",
            ("//docs///sub/", "/"): "/docs/sub",
        }
        for (path, cwd), expected in cases.items():
            with self.subTest(path=path, cwd=cwd):
                self.assertEqual(self.vfs.lookup(path, cwd)[0], expected)

    def test_errors(self):
        """Несуществующий путь и путь через файл — ошибки."""
        with self.assertRaisesRegex(VfsError, "No such file"):
            self.vfs.lookup("/nope")
        with self.assertRaisesRegex(VfsError, "Not a directory"):
            self.vfs.lookup("/readme.txt/x")


class LsTest(unittest.TestCase):
    """Проверки команды ls."""

    def setUp(self):
        """Создать сеанс с VFS."""
        self.shell = Shell(vfs=make_vfs())

    def ls(self, line):
        """Выполнить ls и вернуть (вывод, ошибка)."""
        result = self.shell.execute(line)
        return result.output, result.error

    def test_current_directory(self):
        """Без аргументов — текущая папка, скрытые файлы не видны."""
        self.assertEqual(self.ls("ls"), ("docs  empty  readme.txt", ""))
        self.shell.execute("cd docs")
        self.assertEqual(self.ls("ls")[0], "a.txt  'my notes.txt'  sub")

    def test_all_option(self):
        """-a показывает скрытые файлы, . и .."""
        output, _ = self.ls("ls -a")
        self.assertEqual(output, ".  ..  .hidden  docs  empty  readme.txt")

    def test_long_option(self):
        """-l выводит права, размер и имя."""
        output, _ = self.ls("ls -l /docs")
        self.assertEqual(output.splitlines(), [
            "-rw-r--r--       14 a.txt",
            "-rw-r--r--        7 'my notes.txt'",
            "drwxr-xr-x     4096 sub",
        ])

    def test_combined_options_and_file(self):
        """Опции можно объединять; для файла выводится он сам."""
        output, _ = self.ls("ls -la readme.txt")
        self.assertEqual(output, "-rw-r--r--       12 readme.txt")

    def test_empty_directory(self):
        """Пустая папка — пустой вывод без ошибки."""
        self.assertEqual(self.ls("ls empty"), ("", ""))

    def test_several_paths(self):
        """Для нескольких папок выводятся заголовки."""
        output, _ = self.ls("ls docs/sub empty")
        self.assertEqual(output, "docs/sub:\ndeep.txt\n\nempty:")

    def test_missing_path_does_not_stop_others(self):
        """Ошибка одного пути не мешает вывести остальные."""
        output, error = self.ls("ls nope readme.txt")
        self.assertEqual(output, "readme.txt")
        self.assertEqual(
            error, "ls: cannot access 'nope': No such file or directory")

    def test_invalid_option(self):
        """Неизвестная опция — ошибка."""
        self.assertEqual(self.ls("ls -x")[1], "ls: invalid option -- 'x'")

    def test_double_dash(self):
        """После -- аргументы не считаются опциями."""
        self.assertIn("No such file", self.ls("ls -- -a")[1])

    def test_without_vfs(self):
        """Без VFS ls сообщает об ошибке."""
        error = Shell().execute("ls").error
        self.assertIn("no VFS loaded", error)


class CdTest(unittest.TestCase):
    """Проверки команды cd."""

    def setUp(self):
        """Создать сеанс с VFS."""
        self.shell = Shell(vfs=make_vfs())

    def test_relative_and_parent(self):
        """Переход по относительным путям и на уровень выше."""
        self.shell.execute("cd docs/sub")
        self.assertEqual(self.shell.cwd, "/docs/sub")
        self.shell.execute("cd ..")
        self.assertEqual(self.shell.cwd, "/docs")

    def test_no_arguments_goes_to_root(self):
        """cd без аргументов — переход в корень."""
        self.shell.execute("cd docs")
        self.shell.execute("cd")
        self.assertEqual(self.shell.cwd, "/")

    def test_previous_directory(self):
        """cd - возвращает в предыдущую папку и печатает её."""
        self.shell.execute("cd /docs/sub")
        self.shell.execute("cd /empty")
        result = self.shell.execute("cd -")
        self.assertEqual(result.output, "/docs/sub")
        self.assertEqual(self.shell.cwd, "/docs/sub")

    def test_errors_keep_directory(self):
        """При ошибке текущая папка не меняется."""
        self.shell.execute("cd docs")
        cases = {
            "cd nope": "cd: nope: No such file or directory",
            "cd a.txt": "cd: a.txt: Not a directory",
            "cd a b": "cd: too many arguments",
        }
        for line, message in cases.items():
            with self.subTest(line=line):
                self.assertEqual(self.shell.execute(line).error, message)
                self.assertEqual(self.shell.cwd, "/docs")


if __name__ == "__main__":
    unittest.main()
