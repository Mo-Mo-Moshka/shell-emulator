"""Системные команды: exit, date и служебная vfs-info."""

from datetime import timezone

from emulator.commands.base import (
    CommandError, CommandResult, parse_options, require_vfs,
)
from emulator.vfs import describe_vfs

MAX_EXIT_ARGS = 1
EXIT_STATUS_RANGE = 256
MAX_DATE_OPERANDS = 1
DATE_OPTIONS = "u"
UTC_OPTION = "u"
FORMAT_PREFIX = "+"


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


def cmd_vfs_info(shell, args):
    """Служебная команда: имя VFS, хеш SHA-256 её данных и размер."""
    if args:
        raise CommandError("too many arguments")
    return CommandResult(output="\n".join(describe_vfs(require_vfs(shell))))


def cmd_date(shell, args):
    """Вывести текущие дату и время.

    ``date`` — формат как в GNU date (``Tue Oct  6 18:30:15 MSK 2026``),
    ``date +ФОРМАТ`` — свой формат с кодами strftime (``+%Y-%m-%d``),
    ``-u`` — время UTC.
    """
    flags, operands = parse_options(args, DATE_OPTIONS)
    if len(operands) > MAX_DATE_OPERANDS:
        raise CommandError(f"extra operand '{operands[MAX_DATE_OPERANDS]}'")
    now = shell.clock()
    if UTC_OPTION in flags:
        now = now.astimezone(timezone.utc)
    if not operands:
        return CommandResult(output=format_default_date(now))
    spec = operands[0]
    if not spec.startswith(FORMAT_PREFIX):
        raise CommandError(f"invalid date '{spec}'")
    try:
        return CommandResult(output=now.strftime(spec[len(FORMAT_PREFIX):]))
    except ValueError:
        raise CommandError(f"invalid format '{spec}'") from None


def format_default_date(moment):
    """Отформатировать дату как GNU date без аргументов.

    Если у часового пояса нет короткого имени (в Windows это
    длинная строка с пробелами), выводится смещение ``+0300``.
    """
    zone = moment.tzname() or ""
    if not zone or " " in zone:
        zone = moment.strftime("%z")
    return (f"{moment:%a %b} {moment.day:>2} {moment:%H:%M:%S} "
            f"{zone} {moment.year}")
