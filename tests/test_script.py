"""Тесты стартового скрипта."""

import os
import tempfile
import unittest

from helpers import make_vfs

from emulator.commands import CommandResult
from emulator.script import ScriptError, read_script, run_script
from emulator.shell import Shell


class RunScriptTest(unittest.TestCase):
    """Проверки run_script."""

    def setUp(self):
        """Подготовить список выполненных строк."""
        self.executed = []
        self.shell = Shell(vfs=make_vfs())

    def run_line(self, line):
        """Выполнить строку и запомнить её."""
        self.executed.append(line)
        return self.shell.execute(line)

    def test_runs_all_lines(self):
        """Скрипт без ошибок выполняется целиком."""
        outcome = run_script(["ls", "cd /"], self.run_line)
        self.assertEqual(self.executed, ["ls", "cd /"])
        self.assertIsNone(outcome.failed_line)
        self.assertFalse(outcome.exited)

    def test_skips_blank_lines_and_comments(self):
        """Пустые строки и комментарии не выполняются."""
        run_script(["", "# comment", "  # indented", "ls"], self.run_line)
        self.assertEqual(self.executed, ["ls"])

    def test_stops_at_first_error(self):
        """Выполнение останавливается на первой ошибке."""
        lines = ["ls", "# comment", "cd a b", "ls never"]
        outcome = run_script(lines, self.run_line)
        self.assertEqual(outcome.failed_line, 3)
        self.assertEqual(self.executed, ["ls", "cd a b"])

    def test_stops_at_exit(self):
        """После exit строки не выполняются."""
        outcome = run_script(["exit 3", "ls"], self.run_line)
        self.assertTrue(outcome.exited)
        self.assertEqual(self.executed, ["exit 3"])

    def test_accepts_any_run_line(self):
        """run_line может быть любой функцией, возвращающей результат."""
        outcome = run_script(["x"], lambda line: CommandResult(error="e"))
        self.assertEqual(outcome.failed_line, 1)


class ReadScriptTest(unittest.TestCase):
    """Проверки read_script."""

    def setUp(self):
        """Создать временную папку."""
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "start.txt")

    def tearDown(self):
        """Удалить временную папку."""
        self.tmp.cleanup()

    def write(self, data):
        """Записать байты в файл скрипта."""
        with open(self.path, "wb") as file:
            file.write(data)

    def test_reads_utf8_with_bom(self):
        """Файл UTF-8 читается, BOM (от Блокнота) отбрасывается."""
        self.write("﻿ls\r\n# комментарий\r\n".encode("utf-8"))
        self.assertEqual(read_script(self.path), ["ls", "# комментарий"])

    def test_missing_file(self):
        """Отсутствующий файл даёт ScriptError."""
        with self.assertRaisesRegex(ScriptError, "missing.txt"):
            read_script(os.path.join(self.tmp.name, "missing.txt"))

    def test_not_utf8(self):
        """Файл не в UTF-8 даёт ScriptError."""
        self.write(b"\xff\xfe\xfa")
        with self.assertRaisesRegex(ScriptError, "UTF-8"):
            read_script(self.path)


if __name__ == "__main__":
    unittest.main()
