"""Тесты виртуальной файловой системы и команды vfs-info."""

import hashlib
import os
import shutil
import tempfile
import unittest

from emulator.shell import Shell
from emulator.vfs import Vfs, VfsDir, VfsError, VfsFile, load_vfs

EXAMPLES = os.path.join(os.path.dirname(__file__), "..", "examples", "vfs")
MIN_DEPTH = 3
BINARY_DATA = bytes(range(256))


def write_file(path, data):
    """Создать файл с байтами data, создав нужные папки."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as file:
        file.write(data)


def depth(vfs):
    """Максимальная глубина вложенности папок VFS."""
    return max(path.count("/") for path, node in vfs.walk()
               if isinstance(node, VfsDir))


class LoadVfsTest(unittest.TestCase):
    """Проверки загрузки VFS из папки на диске."""

    def setUp(self):
        """Создать на диске папку с деревом файлов."""
        self.tmp = tempfile.TemporaryDirectory()
        self.source = os.path.join(self.tmp.name, "my_vfs")
        write_file(os.path.join(self.source, "a.txt"), b"hello\n")
        write_file(os.path.join(self.source, "bin", "data.bin"),
                   BINARY_DATA)
        os.makedirs(os.path.join(self.source, "empty"))

    def tearDown(self):
        """Удалить временную папку."""
        self.tmp.cleanup()

    def test_loads_structure_and_data(self):
        """Папки, файлы и их содержимое (в том числе двоичное) в памяти."""
        vfs = load_vfs(self.source)
        self.assertEqual(vfs.name, "my_vfs")
        self.assertEqual(sorted(vfs.root.children), ["a.txt", "bin",
                                                     "empty"])
        self.assertEqual(vfs.root.children["a.txt"].data, b"hello\n")
        data = vfs.root.children["bin"].children["data.bin"].data
        self.assertEqual(data, BINARY_DATA)
        self.assertEqual(vfs.root.children["empty"].children, {})

    def test_works_in_memory(self):
        """После загрузки VFS не зависит от папки на диске."""
        vfs = load_vfs(self.source)
        digest = vfs.sha256()
        shutil.rmtree(self.source)
        self.assertEqual(vfs.sha256(), digest)
        self.assertEqual(vfs.root.children["a.txt"].data, b"hello\n")

    def test_does_not_modify_source(self):
        """Загрузка не меняет файлы на диске."""
        before = sorted(os.walk(self.source))
        load_vfs(self.source).sha256()
        self.assertEqual(sorted(os.walk(self.source)), before)

    def test_stats(self):
        """Подсчёт папок (без корня), файлов и размера."""
        stats = load_vfs(self.source).stats()
        self.assertEqual((stats.directories, stats.files, stats.size),
                         (2, 2, len(b"hello\n") + len(BINARY_DATA)))

    def test_missing_directory(self):
        """Несуществующая папка — ошибка загрузки."""
        with self.assertRaisesRegex(VfsError, "no such directory"):
            load_vfs(os.path.join(self.tmp.name, "nope"))

    def test_file_instead_of_directory(self):
        """Файл вместо папки — ошибка загрузки."""
        with self.assertRaisesRegex(VfsError, "not a directory"):
            load_vfs(os.path.join(self.source, "a.txt"))


class Sha256Test(unittest.TestCase):
    """Проверки хеша SHA-256 данных VFS."""

    def make_vfs(self, data=b"x", name="f.txt"):
        """Создать VFS в памяти: папка d и файл в ней."""
        folder = VfsDir("d", {name: VfsFile(name, data)})
        return Vfs("test", VfsDir("", {"d": folder}))

    def test_matches_documented_algorithm(self):
        """Хеш считается по описанному в vfs.py формату."""
        expected = hashlib.sha256(
            b"D /\0" + b"D /d\0" + b"F /d/f.txt\0" + b"1\0" + b"x"
        ).hexdigest()
        self.assertEqual(self.make_vfs().sha256(), expected)

    def test_depends_on_content_and_names(self):
        """Хеш меняется при изменении содержимого или имени файла."""
        base = self.make_vfs().sha256()
        self.assertNotEqual(self.make_vfs(data=b"y").sha256(), base)
        self.assertNotEqual(self.make_vfs(name="g.txt").sha256(), base)

    def test_same_data_same_hash(self):
        """Одинаковые данные в разных местах дают одинаковый хеш."""
        with tempfile.TemporaryDirectory() as tmp:
            for copy in ("one", "two"):
                write_file(os.path.join(tmp, copy, "x", "y.txt"), b"data")
            first = load_vfs(os.path.join(tmp, "one")).sha256()
            second = load_vfs(os.path.join(tmp, "two")).sha256()
        self.assertEqual(first, second)


class ExampleVfsTest(unittest.TestCase):
    """Проверки примеров VFS из папки examples/vfs."""

    def test_minimal(self):
        """Минимальная VFS — один файл."""
        stats = load_vfs(os.path.join(EXAMPLES, "minimal")).stats()
        self.assertEqual((stats.directories, stats.files), (0, 1))

    def test_several_files(self):
        """VFS с несколькими файлами."""
        stats = load_vfs(os.path.join(EXAMPLES, "several")).stats()
        self.assertGreater(stats.files, 1)

    def test_deep(self):
        """В глубокой VFS не менее 3 уровней папок."""
        vfs = load_vfs(os.path.join(EXAMPLES, "deep"))
        self.assertGreaterEqual(depth(vfs), MIN_DEPTH)


class VfsInfoCommandTest(unittest.TestCase):
    """Проверки служебной команды vfs-info."""

    def setUp(self):
        """Загрузить минимальную VFS из примеров."""
        self.vfs = load_vfs(os.path.join(EXAMPLES, "minimal"))
        self.shell = Shell("ignored", vfs=self.vfs)

    def test_prints_name_and_hash(self):
        """vfs-info выводит имя VFS и её хеш SHA-256."""
        output = self.shell.execute("vfs-info").output
        self.assertIn("name:    minimal", output)
        self.assertIn(f"sha256:  {self.vfs.sha256()}", output)
        self.assertIn("0 directories, 1 files", output)

    def test_name_used_in_prompt(self):
        """Имя загруженной VFS используется в приглашении."""
        self.assertTrue(self.shell.prompt.startswith("minimal:"))

    def test_extra_arguments(self):
        """vfs-info не принимает аргументов."""
        result = self.shell.execute("vfs-info -v")
        self.assertEqual(result.error, "vfs-info: too many arguments")

    def test_no_vfs_loaded(self):
        """Без загруженной VFS команда сообщает об ошибке."""
        result = Shell().execute("vfs-info")
        self.assertIn("no VFS loaded", result.error)


if __name__ == "__main__":
    unittest.main()
