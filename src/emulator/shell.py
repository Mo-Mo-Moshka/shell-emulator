"""Ядро эмулятора: выполнение строк команд независимо от интерфейса."""

from emulator.commands import COMMANDS, CommandError, CommandResult
from emulator.parser import ParseError, parse

DEFAULT_VFS_NAME = "vfs"


class Shell:
    """Состояние сеанса оболочки и выполнение команд."""

    def __init__(self, vfs_name=DEFAULT_VFS_NAME):
        """Создать сеанс для VFS с указанным именем."""
        self.vfs_name = vfs_name
        self.cwd = "/"

    @property
    def prompt(self):
        """Приглашение к вводу, например ``vfs:/$ ``."""
        return f"{self.vfs_name}:{self.cwd}$ "

    def execute(self, line):
        """Разобрать и выполнить одну строку, вернуть CommandResult."""
        try:
            words = parse(line)
        except ParseError as error:
            return CommandResult(error=f"parse error: {error}")
        if not words:
            return CommandResult()
        name, args = words[0], words[1:]
        handler = COMMANDS.get(name)
        if handler is None:
            return CommandResult(error=f"{name}: command not found")
        try:
            return handler(self, args)
        except CommandError as error:
            return CommandResult(error=f"{name}: {error}")
