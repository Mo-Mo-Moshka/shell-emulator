"""Общие части команд: результат, ошибки, разбор опций, доступ к VFS."""

from dataclasses import dataclass
from typing import Optional

from emulator.vfs import VfsDir, VfsError

OPTION_PREFIX = "-"
END_OF_OPTIONS = "--"
TEXT_ENCODING = "utf-8"
IS_A_DIRECTORY = "Is a directory"


@dataclass
class CommandResult:
    """Результат выполнения команды.

    output — обычный вывод, error — текст ошибки,
    exit_code — код завершения, если команда требует выхода.
    """

    output: str = ""
    error: str = ""
    exit_code: Optional[int] = None

    @property
    def should_exit(self):
        """Истина, если эмулятор должен завершить работу."""
        return self.exit_code is not None


class CommandError(Exception):
    """Ошибка выполнения команды (неверные аргументы и т. п.)."""


def parse_options(args, allowed):
    """Отделить опции от операндов, как getopt в UNIX.

    Опции — аргументы вида ``-a`` или ``-la`` (буквы из allowed),
    в любом месте списка; после ``--`` все аргументы — операнды.
    Возвращает пару (множество букв опций, список операндов).
    """
    flags, operands = set(), []
    rest = iter(args)
    for arg in rest:
        if arg == END_OF_OPTIONS:
            operands.extend(rest)
        elif arg.startswith(OPTION_PREFIX) and arg != OPTION_PREFIX:
            flags.update(_check_flags(arg[len(OPTION_PREFIX):], allowed))
        else:
            operands.append(arg)
    return flags, operands


def _check_flags(letters, allowed):
    """Проверить, что все буквы опций допустимы."""
    for letter in letters:
        if letter not in allowed:
            raise CommandError(f"invalid option -- '{letter}'")
    return letters


def require_vfs(shell):
    """Вернуть VFS сеанса или ошибку, если VFS не загружена."""
    if shell.vfs is None:
        raise CommandError("no VFS loaded (use --vfs PATH)")
    return shell.vfs


def find_node(shell, path):
    """Найти узел VFS по пути относительно текущей папки сеанса.

    Возвращает пару (абсолютный путь, узел); ошибку VFS превращает
    в CommandError вида ``<путь>: No such file or directory``.
    """
    try:
        return require_vfs(shell).lookup(path, shell.cwd)
    except VfsError as error:
        raise CommandError(f"{path}: {error}") from None


def read_text(shell, path):
    """Прочитать файл VFS как текст UTF-8."""
    _full_path, node = find_node(shell, path)
    if isinstance(node, VfsDir):
        raise CommandError(f"{path}: {IS_A_DIRECTORY}")
    return node.data.decode(TEXT_ENCODING, errors="replace")


def run_for_each(name, operands, action):
    """Выполнить action(операнд) для каждого операнда.

    action возвращает список строк вывода. Ошибка одного операнда
    не мешает обработать остальные (как в UNIX): все ошибки
    собираются в поле error результата.
    """
    lines, errors = [], []
    for operand in operands:
        try:
            lines.extend(action(operand))
        except CommandError as error:
            errors.append(f"{name}: {error}")
    return CommandResult(output="\n".join(lines).rstrip("\n"),
                         error="\n".join(errors))
