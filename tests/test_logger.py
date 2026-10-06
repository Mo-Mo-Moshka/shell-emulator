"""Тесты журнала вызовов команд."""

import csv
import os
import tempfile
import unittest
from datetime import datetime

from helpers import make_vfs

from emulator.logger import LOG_FIELDS, CsvLogger
from emulator.shell import Shell

FIXED_TIME = datetime(2026, 10, 6, 18, 30, 15)


def read_rows(path):
    """Прочитать CSV-файл и вернуть список строк."""
    with open(path, newline="", encoding="utf-8") as file:
        return list(csv.reader(file))


class CsvLoggerTest(unittest.TestCase):
    """Проверки CsvLogger."""

    def setUp(self):
        """Создать временную папку для журналов."""
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "logs", "log.csv")

    def tearDown(self):
        """Удалить временную папку."""
        self.tmp.cleanup()

    def make_logger(self):
        """Создать журнал с фиксированным временем."""
        return CsvLogger(self.path, clock=lambda: FIXED_TIME)

    def test_creates_file_with_header(self):
        """Новый файл (и папка для него) создаётся с заголовком."""
        self.make_logger()
        self.assertEqual(read_rows(self.path), [list(LOG_FIELDS)])

    def test_writes_success_and_error_events(self):
        """Событие содержит дату, время, команду, статус и ошибку."""
        logger = self.make_logger()
        logger.log("ls", "-l /tmp")
        logger.log("cd", "a b", "cd: too many arguments")
        rows = read_rows(self.path)[1:]
        self.assertEqual(rows, [
            ["2026-10-06", "18:30:15", "ls", "-l /tmp", "ok", ""],
            ["2026-10-06", "18:30:15", "cd", "a b", "error",
             "cd: too many arguments"],
        ])

    def test_appends_without_second_header(self):
        """Повторное открытие дописывает файл без нового заголовка."""
        self.make_logger().log("ls", "")
        self.make_logger().log("ls", "")
        rows = read_rows(self.path)
        self.assertEqual(rows.count(list(LOG_FIELDS)), 1)
        self.assertEqual(len(rows), 3)

    def test_directory_path_fails(self):
        """Путь к папке вместо файла даёт OSError."""
        with self.assertRaises(OSError):
            CsvLogger(self.tmp.name)


class ShellLoggingTest(unittest.TestCase):
    """Проверки журналирования в Shell."""

    def setUp(self):
        """Создать сеанс с журналом-шпионом."""
        self.events = []
        self.shell = Shell(logger=self, vfs=make_vfs())

    def log(self, command, arguments, error=""):
        """Запомнить событие вместо записи в файл."""
        self.events.append((command, arguments, error))

    def test_logs_every_command(self):
        """Успешные и ошибочные вызовы попадают в журнал."""
        self.shell.execute("ls -l 'docs/my notes.txt'")
        self.shell.execute("foo")
        self.assertEqual(self.events, [
            ("ls", "-l 'docs/my notes.txt'", ""),
            ("foo", "", "foo: command not found"),
        ])

    def test_logs_parse_errors(self):
        """Ошибка разбора тоже журналируется."""
        self.shell.execute("ls 'abc")
        command, arguments, error = self.events[0]
        self.assertEqual((command, arguments), ("", "ls 'abc"))
        self.assertIn("parse error", error)

    def test_skips_empty_lines_and_comments(self):
        """Пустые строки и комментарии не журналируются."""
        self.shell.execute("   ")
        self.shell.execute("# just a comment")
        self.assertEqual(self.events, [])


if __name__ == "__main__":
    unittest.main()
