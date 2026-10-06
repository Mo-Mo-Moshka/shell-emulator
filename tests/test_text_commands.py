"""Тесты команд rev, tac и date, а также разбора опций."""

import unittest
from datetime import datetime, timedelta, timezone

from helpers import make_vfs

from emulator.commands.base import CommandError, parse_options
from emulator.shell import Shell

MSK = timezone(timedelta(hours=3), "MSK")
FIXED_NOW = datetime(2026, 10, 6, 9, 5, 7, tzinfo=MSK)


class ParseOptionsTest(unittest.TestCase):
    """Проверки parse_options."""

    def test_flags_and_operands(self):
        """Опции отделяются от операндов в любом порядке."""
        flags, operands = parse_options(["-l", "x", "-a", "y"], "al")
        self.assertEqual((flags, operands), ({"a", "l"}, ["x", "y"]))

    def test_combined_and_double_dash(self):
        """Объединённые опции и -- работают как в UNIX."""
        flags, operands = parse_options(["-la", "--", "-a", "-"], "al")
        self.assertEqual((flags, operands), ({"a", "l"}, ["-a", "-"]))

    def test_invalid_option(self):
        """Неизвестная буква опции — ошибка."""
        with self.assertRaisesRegex(CommandError, "invalid option -- 'z'"):
            parse_options(["-az"], "a")


class RevTacTest(unittest.TestCase):
    """Проверки rev и tac."""

    def setUp(self):
        """Создать сеанс с VFS."""
        self.shell = Shell(vfs=make_vfs())

    def test_rev(self):
        """rev переворачивает символы каждой строки."""
        result = self.shell.execute("rev readme.txt")
        self.assertEqual(result.output, "olleh\ndlrow")

    def test_rev_unicode_and_relative_path(self):
        """rev работает с кириллицей и путями от текущей папки."""
        self.shell.execute("cd docs")
        result = self.shell.execute("rev 'my notes.txt'")
        self.assertEqual(result.output, "вба")

    def test_tac(self):
        """tac выводит строки в обратном порядке."""
        result = self.shell.execute("tac docs/a.txt")
        self.assertEqual(result.output, "three\ntwo\none")

    def test_several_files(self):
        """Несколько файлов обрабатываются по очереди."""
        result = self.shell.execute("tac readme.txt docs/sub/deep.txt")
        self.assertEqual(result.output, "world\nhello\nx")

    def test_empty_file(self):
        """Пустой файл даёт пустой вывод."""
        self.assertEqual(self.shell.execute("tac .hidden").output, "")

    def test_errors(self):
        """Ошибки rev и tac."""
        cases = {
            "rev": "rev: missing file operand",
            "tac docs": "tac: docs: Is a directory",
            "rev nope": "rev: nope: No such file or directory",
            "tac -s x": "tac: invalid option -- 's'",
        }
        for line, message in cases.items():
            with self.subTest(line=line):
                self.assertEqual(self.shell.execute(line).error, message)

    def test_error_does_not_stop_other_files(self):
        """Ошибка одного файла не мешает вывести остальные."""
        result = self.shell.execute("rev nope readme.txt")
        self.assertEqual(result.output, "olleh\ndlrow")
        self.assertIn("nope", result.error)


class DateTest(unittest.TestCase):
    """Проверки date с фиксированными часами."""

    def setUp(self):
        """Создать сеанс с подменёнными часами."""
        self.shell = Shell()
        self.shell.clock = lambda: FIXED_NOW

    def date(self, line):
        """Выполнить date и вернуть (вывод, ошибка)."""
        result = self.shell.execute(line)
        return result.output, result.error

    def test_default_format(self):
        """Формат по умолчанию как в GNU date."""
        self.assertEqual(self.date("date"),
                         ("Tue Oct  6 09:05:07 MSK 2026", ""))

    def test_utc(self):
        """-u выводит время UTC."""
        self.assertEqual(self.date("date -u")[0],
                         "Tue Oct  6 06:05:07 UTC 2026")

    def test_custom_format(self):
        """+ФОРМАТ задаёт свой формат."""
        self.assertEqual(self.date("date +%Y-%m-%d")[0], "2026-10-06")
        self.assertEqual(self.date("date '+%H:%M %d.%m'")[0], "09:05 06.10")

    def test_zone_without_short_name(self):
        """Длинное имя пояса (Windows) заменяется смещением."""
        zone = timezone(timedelta(hours=3), "Russia TZ 2 Standard Time")
        self.shell.clock = lambda: FIXED_NOW.replace(tzinfo=zone)
        self.assertEqual(self.date("date")[0],
                         "Tue Oct  6 09:05:07 +0300 2026")

    def test_errors(self):
        """Ошибки date."""
        cases = {
            "date tomorrow": "date: invalid date 'tomorrow'",
            "date +%Y extra": "date: extra operand 'extra'",
            "date -x": "date: invalid option -- 'x'",
        }
        for line, message in cases.items():
            with self.subTest(line=line):
                self.assertEqual(self.date(line)[1], message)


if __name__ == "__main__":
    unittest.main()
