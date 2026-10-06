"""Виртуальная файловая система (VFS), хранящаяся в памяти.

Источник VFS — папка на диске пользователя. При загрузке вся папка
(структура и содержимое файлов) читается в память; дальше эмулятор
работает только с копией в памяти и никогда не меняет данные на диске.

Хеш SHA-256 вычисляется по данным VFS в памяти: обходятся все узлы
в порядке сортировки имён, для каждой папки хешируется
``D <путь>\\0``, для каждого файла —
``F <путь>\\0<размер>\\0<содержимое>``. Пути относительные от корня
VFS, начинаются с ``/`` и записываются в UTF-8.
"""

import hashlib
import os
from dataclasses import dataclass, field
from typing import Dict, Union

ROOT_PATH = "/"
SEPARATOR = "/"
CURRENT_DIR = "."
PARENT_DIR = ".."
PATH_ENCODING = "utf-8"
NO_SUCH_FILE = "No such file or directory"
NOT_A_DIRECTORY = "Not a directory"


class VfsError(Exception):
    """Ошибка загрузки или работы с VFS."""


@dataclass
class VfsFile:
    """Файл VFS: имя и содержимое в виде байтов."""

    name: str
    data: bytes = b""


@dataclass
class VfsDir:
    """Папка VFS: имя и словарь вложенных узлов по именам."""

    name: str
    children: Dict[str, Union["VfsDir", VfsFile]] = field(
        default_factory=dict)


@dataclass
class VfsStats:
    """Количество папок (без корня), файлов и общий размер файлов."""

    directories: int = 0
    files: int = 0
    size: int = 0


class Vfs:
    """Загруженная в память VFS."""

    def __init__(self, name, root, source=None):
        """Создать VFS с именем name и корневой папкой root.

        source — путь к папке на диске, из которой загружена VFS.
        """
        self.name = name
        self.root = root
        self.source = source

    def lookup(self, path, cwd=ROOT_PATH):
        """Найти узел по пути и вернуть пару (абсолютный путь, узел).

        path может быть абсолютным (``/etc``) или относительным
        текущей папки cwd; поддерживаются ``.`` и ``..`` (выше
        корня подняться нельзя). Бросает VfsError с текстом
        ``No such file or directory`` или ``Not a directory``.
        """
        if not path.startswith(SEPARATOR):
            path = cwd + SEPARATOR + path
        names, nodes = [], [self.root]
        for part in path.split(SEPARATOR):
            if part in ("", CURRENT_DIR):
                continue
            if part == PARENT_DIR:
                if names:
                    names.pop()
                    nodes.pop()
                continue
            nodes.append(_child(nodes[-1], part))
            names.append(part)
        return SEPARATOR + SEPARATOR.join(names), nodes[-1]

    def walk(self):
        """Обойти все узлы VFS: пары (путь, узел) в порядке имён."""
        yield ROOT_PATH, self.root
        yield from _walk_children(self.root, "")

    def sha256(self):
        """Вернуть хеш SHA-256 данных VFS в виде hex-строки."""
        digest = hashlib.sha256()
        for path, node in self.walk():
            encoded = path.encode(PATH_ENCODING)
            if isinstance(node, VfsFile):
                size = str(len(node.data)).encode(PATH_ENCODING)
                digest.update(b"F " + encoded + b"\0" + size + b"\0")
                digest.update(node.data)
            else:
                digest.update(b"D " + encoded + b"\0")
        return digest.hexdigest()

    def stats(self):
        """Посчитать папки, файлы и общий размер данных."""
        stats = VfsStats()
        for _path, node in self.walk():
            if isinstance(node, VfsFile):
                stats.files += 1
                stats.size += len(node.data)
            elif node is not self.root:
                stats.directories += 1
        return stats


def _child(node, name):
    """Вернуть вложенный узел name папки node."""
    if not isinstance(node, VfsDir):
        raise VfsError(NOT_A_DIRECTORY)
    if name not in node.children:
        raise VfsError(NO_SUCH_FILE)
    return node.children[name]


def _walk_children(directory, prefix):
    """Рекурсивно обойти содержимое папки с путями от prefix."""
    for name in sorted(directory.children):
        node = directory.children[name]
        path = prefix + SEPARATOR + name
        yield path, node
        if isinstance(node, VfsDir):
            yield from _walk_children(node, path)


def load_vfs(path):
    """Загрузить VFS из папки path в память и вернуть объект Vfs.

    Бросает VfsError, если папка не существует, является файлом
    или не может быть прочитана.
    """
    if not os.path.exists(path):
        raise VfsError(f"'{path}': no such directory")
    if not os.path.isdir(path):
        raise VfsError(f"'{path}': not a directory")
    source = os.path.abspath(path)
    name = os.path.basename(os.path.normpath(source))
    return Vfs(name, _load_dir("", source), source)


def _load_dir(name, path):
    """Прочитать папку с диска рекурсивно и вернуть VfsDir."""
    directory = VfsDir(name)
    try:
        with os.scandir(path) as entries:
            for entry in entries:
                node = _load_entry(entry)
                if node is not None:
                    directory.children[entry.name] = node
    except OSError as error:
        failed = error.filename or path
        raise VfsError(f"'{failed}': {error.strerror}") from None
    return directory


def _load_entry(entry):
    """Прочитать элемент папки: файл, папку или None для остального.

    Символические ссылки и специальные файлы пропускаются, чтобы
    VFS не выходила за пределы своей папки.
    """
    if entry.is_dir(follow_symlinks=False):
        return _load_dir(entry.name, entry.path)
    if entry.is_file(follow_symlinks=False):
        with open(entry.path, "rb") as file:
            return VfsFile(entry.name, file.read())
    return None


def describe_vfs(vfs):
    """Вернуть строки с информацией о VFS для команды vfs-info."""
    stats = vfs.stats()
    return [
        f"name:    {vfs.name}",
        f"source:  {vfs.source}",
        f"sha256:  {vfs.sha256()}",
        f"content: {stats.directories} directories, {stats.files} files, "
        f"{stats.size} bytes",
    ]
