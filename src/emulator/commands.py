"""Команды эмулятора.

Каждая команда — функция ``handler(shell, args)``, которая возвращает
CommandResult или бросает CommandError. На этапе 1 команды ls и cd
являются заглушками: они только выводят своё имя и аргументы.
"""

from dataclasses import dataclass
from typing import Optional

MAX_CD_ARGS = 1
MAX_EXIT_ARGS = 1
EXIT_STATUS_RANGE = 256


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


def _describe_call(name, args):
    """Сформировать строку с именем команды и её аргументами."""
    return f"{name}: arguments: {args}"


def cmd_ls(shell, args):
    """Заглушка ls: вывести имя команды и аргументы."""
    return CommandResult(output=_describe_call("ls", args))


def cmd_cd(shell, args):
    """Заглушка cd: вывести имя команды и аргументы.

    Как и в bash, принимает не более одного аргумента.
    """
    if len(args) > MAX_CD_ARGS:
        raise CommandError("too many arguments")
    return CommandResult(output=_describe_call("cd", args))


def cmd_exit(shell, args):
    """Завершить работу эмулятора.

    Необязательный аргумент — числовой код завершения (по модулю 256).
    """
    if len(args) > MAX_EXIT_ARGS:
        raise CommandError("too many arguments")
    if not args:
        return CommandResult(exit_code=0)
    try:
        code = int(args[0])
    except ValueError:
        raise CommandError(
            f"{args[0]}: numeric argument required"
        ) from None
    return CommandResult(exit_code=code % EXIT_STATUS_RANGE)


COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
    "exit": cmd_exit,
}
