"""Тесты выполнения команд и графического окна."""

import os
import tempfile
import tkinter as tk
import unittest
from unittest import mock

from emulator.gui import TerminalWindow
from emulator.shell import Shell


class ShellTest(unittest.TestCase):
    """Проверки класса Shell и команд этапа 1."""

    def setUp(self):
        """Создать новый сеанс для каждого теста."""
        self.shell = Shell("test_vfs")

    def test_prompt_contains_vfs_name(self):
        """Приглашение содержит имя VFS."""
        self.assertTrue(self.shell.prompt.startswith("test_vfs:"))

    def test_ls_stub_prints_name_and_args(self):
        """Заглушка ls выводит своё имя и аргументы."""
        result = self.shell.execute("ls -l /tmp")
        self.assertEqual(result.output, "ls: arguments: ['-l', '/tmp']")
        self.assertEqual(result.error, "")

    def test_cd_stub_prints_name_and_args(self):
        """Заглушка cd выводит своё имя и аргументы."""
        result = self.shell.execute("cd /home")
        self.assertEqual(result.output, "cd: arguments: ['/home']")

    @mock.patch.dict(os.environ, {"EMU_HOME": "/home/user"})
    def test_command_gets_expanded_args(self):
        """Команда получает аргументы после подстановки переменных."""
        result = self.shell.execute("cd $EMU_HOME")
        self.assertEqual(result.output, "cd: arguments: ['/home/user']")

    def test_cd_too_many_arguments(self):
        """cd с двумя аргументами сообщает об ошибке."""
        result = self.shell.execute("cd a b")
        self.assertEqual(result.error, "cd: too many arguments")

    def test_unknown_command(self):
        """Неизвестная команда даёт ошибку command not found."""
        result = self.shell.execute("foo bar")
        self.assertEqual(result.error, "foo: command not found")
        self.assertFalse(result.should_exit)

    def test_parse_error(self):
        """Ошибка разбора не роняет эмулятор."""
        result = self.shell.execute("ls 'abc")
        self.assertIn("parse error", result.error)

    def test_empty_line(self):
        """Пустая строка ничего не делает."""
        result = self.shell.execute("")
        self.assertEqual((result.output, result.error), ("", ""))

    def test_exit(self):
        """exit без аргументов завершает работу с кодом 0."""
        result = self.shell.execute("exit")
        self.assertTrue(result.should_exit)
        self.assertEqual(result.exit_code, 0)

    def test_exit_with_code(self):
        """exit N завершает работу с кодом N по модулю 256."""
        self.assertEqual(self.shell.execute("exit 3").exit_code, 3)
        self.assertEqual(self.shell.execute("exit 257").exit_code, 1)

    def test_exit_errors(self):
        """Неверные аргументы exit дают ошибку и не завершают работу."""
        cases = {
            "exit abc": "exit: abc: numeric argument required",
            "exit 1 2": "exit: too many arguments",
        }
        for line, message in cases.items():
            with self.subTest(line=line):
                result = self.shell.execute(line)
                self.assertEqual(result.error, message)
                self.assertFalse(result.should_exit)


class TerminalWindowTest(unittest.TestCase):
    """Проверки окна; пропускаются, если нет графической среды."""

    def setUp(self):
        """Создать скрытое окно tkinter."""
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f"no display: {error}")
        self.root.withdraw()
        self.window = TerminalWindow(Shell("my_vfs"), self.root)

    def tearDown(self):
        """Закрыть окно, если оно ещё открыто."""
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def test_exit_closes_window(self):
        """Команда exit закрывает окно и запоминает код завершения."""
        self.window.run_line("exit 5")
        self.assertEqual(self.window.exit_code, 5)
        with self.assertRaises(tk.TclError):
            self.root.title()

    def test_title_contains_vfs_name(self):
        """Заголовок окна содержит имя VFS."""
        self.assertIn("my_vfs", self.root.title())

    def test_run_line_shows_input_and_output(self):
        """В окне видны и введённая команда, и её вывод."""
        self.window.run_line("ls -a")
        text = self.window.output.get("1.0", "end")
        self.assertIn("my_vfs:/$ ls -a", text)
        self.assertIn("ls: arguments: ['-a']", text)

    def test_startup_script_shows_dialog(self):
        """Скрипт показывает ввод и вывод и останавливается на ошибке."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "start.txt")
            with open(path, "w", encoding="utf-8") as file:
                file.write("ls -a\ncd a b\nls never\n")
            outcome = self.window.run_script_file(path)
        text = self.window.output.get("1.0", "end")
        self.assertEqual(outcome.failed_line, 2)
        self.assertIn("my_vfs:/$ ls -a\nls: arguments: ['-a']", text)
        self.assertIn("cd: too many arguments", text)
        self.assertIn("script stopped: error at line 2", text)
        self.assertNotIn("never", text)

    def test_missing_startup_script(self):
        """Ошибка чтения скрипта выводится в окне."""
        self.assertIsNone(self.window.run_script_file("no/such/file.txt"))
        text = self.window.output.get("1.0", "end")
        self.assertIn("startup script: cannot read", text)

    def test_error_is_highlighted(self):
        """Текст ошибки выделяется тегом error."""
        self.window.run_line("nope")
        ranges = self.window.output.tag_ranges("error")
        self.assertTrue(ranges)
