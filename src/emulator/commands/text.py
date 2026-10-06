"""Команды обработки текстовых файлов VFS: rev и tac.

В эмуляторе нет стандартного ввода, поэтому обеим командам нужен
хотя бы один файл.
"""

from emulator.commands.base import (
    CommandError, parse_options, read_text, run_for_each,
)

NO_OPTIONS = ""


def _file_operands(args):
    """Проверить аргументы (опций нет) и вернуть список файлов."""
    _flags, files = parse_options(args, NO_OPTIONS)
    if not files:
        raise CommandError("missing file operand")
    return files


def cmd_rev(shell, args):
    """Вывести строки файлов, перевернув символы в каждой строке."""

    def reverse_lines(path):
        """Перевернуть каждую строку одного файла."""
        return [line[::-1] for line in read_text(shell, path).splitlines()]

    return run_for_each("rev", _file_operands(args), reverse_lines)


def cmd_tac(shell, args):
    """Вывести строки каждого файла в обратном порядке."""

    def reverse_order(path):
        """Вернуть строки одного файла от последней к первой."""
        return read_text(shell, path).splitlines()[::-1]

    return run_for_each("tac", _file_operands(args), reverse_order)
