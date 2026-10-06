"""Команды, изменяющие VFS: rm и rmdir.

Все изменения выполняются только в памяти: папка на диске, из которой
загружена VFS, не меняется.
"""

from dataclasses import dataclass

from emulator.commands.base import (
    IS_A_DIRECTORY, CommandError, parse_options, require_vfs, run_for_each,
)
from emulator.vfs import (
    CURRENT_DIR, NOT_A_DIRECTORY, PARENT_DIR, ROOT_PATH, SEPARATOR, VfsDir,
    VfsError, is_inside,
)

RM_OPTIONS = "rRfdv"
RECURSIVE_OPTIONS = frozenset("rR")
FORCE_OPTION = "f"
EMPTY_DIR_OPTION = "d"
VERBOSE_OPTION = "v"
RMDIR_OPTIONS = "pv"
PARENTS_OPTION = "p"
DOT_NAMES = frozenset((CURRENT_DIR, PARENT_DIR))
NOT_EMPTY = "Directory not empty"
BUSY = "Device or resource busy"


@dataclass
class RmOptions:
    """Опции команды rm."""

    recursive: bool = False
    force: bool = False
    empty_dirs: bool = False
    verbose: bool = False


def _is_dot(path):
    """Истина, если последний компонент пути — ``.`` или ``..``."""
    return path.rstrip(SEPARATOR).rpartition(SEPARATOR)[2] in DOT_NAMES


def cmd_rm(shell, args):
    """Удалить файлы и папки VFS.

    Опции: ``-r``/``-R`` — папки вместе с содержимым, ``-d`` — пустые
    папки, ``-f`` — не сообщать о несуществующих путях, ``-v`` —
    выводить каждый удалённый файл и папку.
    """
    flags, operands = parse_options(args, RM_OPTIONS)
    options = RmOptions(
        recursive=bool(RECURSIVE_OPTIONS & flags),
        force=FORCE_OPTION in flags,
        empty_dirs=EMPTY_DIR_OPTION in flags,
        verbose=VERBOSE_OPTION in flags,
    )
    if not operands and not options.force:
        raise CommandError("missing operand")

    def remove_one(path):
        """Удалить один путь."""
        return _rm_path(shell, path, options)

    return run_for_each("rm", operands, remove_one)


def _rm_path(shell, path, options):
    """Удалить один путь командой rm и вернуть строки вывода."""
    if _is_dot(path):
        raise CommandError(
            f"refusing to remove '.' or '..' directory: skipping '{path}'")
    vfs = require_vfs(shell)
    try:
        full_path, node = vfs.lookup(path, shell.cwd)
    except VfsError as error:
        if options.force:
            return []
        raise CommandError(f"cannot remove '{path}': {error}") from None
    if isinstance(node, VfsDir):
        _check_rm_directory(shell, path, full_path, node, options)
    vfs.remove(full_path)
    return _removed_lines(path, node) if options.verbose else []


def _check_rm_directory(shell, path, full_path, node, options):
    """Проверить, можно ли удалить папку командой rm."""
    if not options.recursive and not options.empty_dirs:
        raise CommandError(f"cannot remove '{path}': {IS_A_DIRECTORY}")
    if not options.recursive and node.children:
        raise CommandError(f"cannot remove '{path}': {NOT_EMPTY}")
    if full_path == ROOT_PATH:
        raise CommandError("it is dangerous to operate recursively on '/'")
    if is_inside(shell.cwd, full_path):
        raise CommandError(f"cannot remove '{path}': {BUSY}")


def _removed_lines(path, node):
    """Строки -v для удалённого узла: сначала содержимое, затем папка."""
    if not isinstance(node, VfsDir):
        return [f"removed '{path}'"]
    lines = []
    for name in sorted(node.children):
        child_path = path.rstrip(SEPARATOR) + SEPARATOR + name
        lines.extend(_removed_lines(child_path, node.children[name]))
    lines.append(f"removed directory '{path}'")
    return lines


def cmd_rmdir(shell, args):
    """Удалить пустые папки VFS.

    Опции: ``-p`` — удалить также родительские папки из пути, если
    они стали пустыми (``rmdir -p a/b/c`` удаляет c, b и a);
    ``-v`` — выводить каждую удалённую папку.
    """
    flags, operands = parse_options(args, RMDIR_OPTIONS)
    if not operands:
        raise CommandError("missing operand")

    def remove_one(path):
        """Удалить одну папку (и родителей при -p)."""
        targets = _with_parents(path) if PARENTS_OPTION in flags else [path]
        lines = []
        for target in targets:
            _rmdir_path(shell, target)
            if VERBOSE_OPTION in flags:
                lines.append(f"rmdir: removing directory, '{target}'")
        return lines

    return run_for_each("rmdir", operands, remove_one)


def _with_parents(path):
    """Путь и все его родители: ``a/b/c`` -> ``a/b/c``, ``a/b``, ``a``."""
    chain = []
    current = path.rstrip(SEPARATOR)
    while current:
        chain.append(current)
        current = current.rpartition(SEPARATOR)[0].rstrip(SEPARATOR)
    return chain


def _rmdir_path(shell, path):
    """Удалить одну пустую папку."""
    if _is_dot(path):
        raise CommandError(f"failed to remove '{path}': Invalid argument")
    vfs = require_vfs(shell)
    try:
        full_path, node = vfs.lookup(path, shell.cwd)
    except VfsError as error:
        raise CommandError(f"failed to remove '{path}': {error}") from None
    if not isinstance(node, VfsDir):
        raise CommandError(f"failed to remove '{path}': {NOT_A_DIRECTORY}")
    if node.children:
        raise CommandError(f"failed to remove '{path}': {NOT_EMPTY}")
    if full_path == ROOT_PATH or is_inside(shell.cwd, full_path):
        raise CommandError(f"failed to remove '{path}': {BUSY}")
    vfs.remove(full_path)
