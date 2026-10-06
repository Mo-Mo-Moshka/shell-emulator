"""Команды навигации по VFS: ls и cd."""

from emulator.commands.base import (
    CommandError, CommandResult, find_node, parse_options, require_vfs,
    run_for_each,
)
from emulator.vfs import (
    CURRENT_DIR, NOT_A_DIRECTORY, PARENT_DIR, ROOT_PATH, VfsDir, VfsError,
)

LS_OPTIONS = "al"
ALL_OPTION = "a"
LONG_OPTION = "l"
HIDDEN_PREFIX = "."
DIR_MODE = "drwxr-xr-x"
FILE_MODE = "-rw-r--r--"
DIR_SIZE = 4096
SIZE_WIDTH = 8
COLUMN_GAP = "  "
QUOTED_CHARS = frozenset(" \t'\"")
MAX_CD_ARGS = 1
PREVIOUS_DIR = "-"


def cmd_ls(shell, args):
    """Вывести содержимое папок VFS или сведения о файлах.

    Без аргументов — текущая папка. Опции: ``-a`` — показывать
    скрытые файлы (имена с точки), а также ``.`` и ``..``;
    ``-l`` — подробный формат: тип и права, размер, имя.
    Для нескольких путей перед каждой папкой выводится заголовок.
    """
    flags, paths = parse_options(args, LS_OPTIONS)
    targets = paths or [CURRENT_DIR]
    with_header = len(targets) > 1

    def list_one(path):
        """Сформировать вывод ls для одного пути."""
        return _list_path(shell, path, flags, with_header)

    return run_for_each("ls", targets, list_one)


def _list_path(shell, path, flags, with_header):
    """Вернуть строки вывода ls для одного пути."""
    try:
        _full_path, node = require_vfs(shell).lookup(path, shell.cwd)
    except VfsError as error:
        raise CommandError(f"cannot access '{path}': {error}") from None
    if not isinstance(node, VfsDir):
        return _format_entries([(path, node)], flags)
    lines = _format_entries(_dir_entries(node, flags), flags)
    if with_header:
        lines = [f"{path}:", *lines, ""]
    return lines


def _dir_entries(directory, flags):
    """Вернуть отсортированные пары (имя, узел) содержимого папки."""
    show_all = ALL_OPTION in flags
    entries = [(name, directory.children[name])
               for name in sorted(directory.children)
               if show_all or not name.startswith(HIDDEN_PREFIX)]
    if show_all:
        entries = [(CURRENT_DIR, directory), (PARENT_DIR, directory),
                   *entries]
    return entries


def _format_entries(entries, flags):
    """Отформатировать пары (имя, узел) в строки вывода ls."""
    if LONG_OPTION in flags:
        return [_long_line(name, node) for name, node in entries]
    if not entries:
        return []
    return [COLUMN_GAP.join(_display_name(name) for name, _ in entries)]


def _long_line(name, node):
    """Строка подробного формата: права, размер, имя."""
    if isinstance(node, VfsDir):
        mode, size = DIR_MODE, DIR_SIZE
    else:
        mode, size = FILE_MODE, len(node.data)
    return f"{mode} {size:>{SIZE_WIDTH}} {_display_name(name)}"


def _display_name(name):
    """Взять имя в кавычки, если в нём есть пробелы или кавычки."""
    if QUOTED_CHARS.intersection(name):
        return "'" + name.replace("'", "'\\''") + "'"
    return name


def cmd_cd(shell, args):
    """Сменить текущую папку.

    ``cd`` без аргументов — переход в корень VFS, ``cd -`` — в
    предыдущую папку (новый путь выводится, как в bash).
    """
    if len(args) > MAX_CD_ARGS:
        raise CommandError("too many arguments")
    target = args[0] if args else ROOT_PATH
    output = ""
    if target == PREVIOUS_DIR:
        target = output = shell.previous_cwd
    full_path, node = find_node(shell, target)
    if not isinstance(node, VfsDir):
        raise CommandError(f"{target}: {NOT_A_DIRECTORY}")
    shell.previous_cwd, shell.cwd = shell.cwd, full_path
    return CommandResult(output=output)
