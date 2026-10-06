"""Ядро эмулятора: выполнение строк команд независимо от интерфейса."""

import shlex
from datetime import datetime

from emulator.commands import COMMANDS, CommandError, CommandResult
from emulator.config import DEFAULT_VFS_NAME
from emulator.logger import NullLogger
from emulator.parser import ParseError, parse
from emulator.vfs import ROOT_PATH


def local_now():
    """Текущие дата и время с локальным часовым поясом."""
    return datetime.now().astimezone()


class Shell:
    """Состояние сеанса оболочки и выполнение команд."""

    def __init__(self, vfs_name=DEFAULT_VFS_NAME, logger=None, vfs=None):
        """Создать сеанс для VFS с указанным именем.

        logger — журнал вызовов команд (CsvLogger или NullLogger),
        vfs — загруженная VFS (None, если VFS не загружена).
        """
        self.vfs_name = vfs.name if vfs is not None else vfs_name
        self.vfs = vfs
        self.cwd = ROOT_PATH
        self.previous_cwd = ROOT_PATH
        self.logger = logger if logger is not None else NullLogger()
        self.clock = local_now

    @property
    def prompt(self):
        """Приглашение к вводу, например ``vfs:/$ ``."""
        return f"{self.vfs_name}:{self.cwd}$ "

    def execute(self, line):
        """Разобрать и выполнить одну строку, вернуть CommandResult.

        Каждый вызов команды (в том числе ошибочный) записывается
        в журнал. Пустые строки и комментарии не журналируются.
        """
        try:
            words = parse(line)
        except ParseError as error:
            result = CommandResult(error=f"parse error: {error}")
            self.logger.log("", line.strip(), result.error)
            return result
        if not words:
            return CommandResult()
        name, args = words[0], words[1:]
        result = self._run_command(name, args)
        self.logger.log(name, shlex.join(args), result.error)
        return result

    def _run_command(self, name, args):
        """Найти команду по имени и выполнить её."""
        handler = COMMANDS.get(name)
        if handler is None:
            return CommandResult(error=f"{name}: command not found")
        try:
            return handler(self, args)
        except CommandError as error:
            return CommandResult(error=f"{name}: {error}")
