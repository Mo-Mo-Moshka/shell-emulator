"""Тесты параметров командной строки."""

import contextlib
import io
import unittest

from emulator.config import (
    DEFAULT_VFS_NAME, NOT_SET, Config, describe_config, parse_args,
)

ARGPARSE_ERROR_CODE = 2


class ParseArgsTest(unittest.TestCase):
    """Проверки parse_args и Config."""

    def test_no_arguments(self):
        """Без параметров все пути не заданы."""
        self.assertEqual(parse_args([]), Config())

    def test_all_arguments(self):
        """Все три параметра попадают в Config."""
        config = parse_args(["--vfs", "data/my_vfs", "--log", "log.csv",
                             "--script", "start.txt"])
        self.assertEqual(config, Config("data/my_vfs", "log.csv",
                                        "start.txt"))

    def test_unknown_argument(self):
        """Неизвестный параметр завершает программу с кодом 2."""
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                parse_args(["--color", "red"])
        self.assertEqual(raised.exception.code, ARGPARSE_ERROR_CODE)

    def test_missing_value(self):
        """Параметр без значения — ошибка."""
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                parse_args(["--log"])


class VfsNameTest(unittest.TestCase):
    """Проверки вычисления имени VFS по пути."""

    def test_name_is_last_component(self):
        """Имя VFS — последняя часть пути, даже с / в конце."""
        for path in ("data/my_vfs", "data/my_vfs/", "my_vfs"):
            with self.subTest(path=path):
                self.assertEqual(Config(vfs_path=path).vfs_name, "my_vfs")

    def test_default_name(self):
        """Без пути используется имя по умолчанию."""
        self.assertEqual(Config().vfs_name, DEFAULT_VFS_NAME)


class DescribeConfigTest(unittest.TestCase):
    """Проверки отладочного вывода параметров."""

    def test_lists_all_parameters(self):
        """Отладочный вывод содержит все параметры."""
        text = "\n".join(describe_config(
            Config("data/my_vfs", "log.csv", "start.txt")))
        for value in ("data/my_vfs", "my_vfs", "log.csv", "start.txt"):
            self.assertIn(value, text)

    def test_marks_missing_parameters(self):
        """Незаданные параметры помечаются как (not set)."""
        lines = describe_config(Config())
        self.assertEqual(sum(NOT_SET in line for line in lines), 3)


if __name__ == "__main__":
    unittest.main()
