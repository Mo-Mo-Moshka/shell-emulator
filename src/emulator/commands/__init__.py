"""Команды эмулятора.

Каждая команда — функция ``handler(shell, args)``, которая возвращает
CommandResult или бросает CommandError. COMMANDS сопоставляет имя
команды с её функцией.
"""

from emulator.commands.base import CommandError, CommandResult
from emulator.commands.modify import cmd_rm, cmd_rmdir
from emulator.commands.navigation import cmd_cd, cmd_ls
from emulator.commands.system import cmd_date, cmd_exit, cmd_vfs_info
from emulator.commands.text import cmd_rev, cmd_tac

__all__ = ["COMMANDS", "CommandError", "CommandResult"]

COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
    "rev": cmd_rev,
    "tac": cmd_tac,
    "date": cmd_date,
    "rm": cmd_rm,
    "rmdir": cmd_rmdir,
    "exit": cmd_exit,
    "vfs-info": cmd_vfs_info,
}
