"""Общие данные для тестов: небольшая VFS в памяти."""

from emulator.vfs import Vfs, VfsDir, VfsFile


def make_dir(name, *children):
    """Создать папку VFS с вложенными узлами."""
    return VfsDir(name, {child.name: child for child in children})


def make_vfs(name="test_vfs"):
    """Создать VFS для тестов.

    ::

        /readme.txt        "hello\\nworld\\n"
        /.hidden           ""
        /docs/a.txt        "one\\ntwo\\nthree\\n"
        /docs/my notes.txt "абв\\n"
        /docs/sub/deep.txt "x\\n"
        /empty/
    """
    docs = make_dir(
        "docs",
        VfsFile("a.txt", b"one\ntwo\nthree\n"),
        VfsFile("my notes.txt", "абв\n".encode("utf-8")),
        make_dir("sub", VfsFile("deep.txt", b"x\n")),
    )
    root = make_dir(
        "",
        VfsFile("readme.txt", b"hello\nworld\n"),
        VfsFile(".hidden", b""),
        docs,
        make_dir("empty"),
    )
    return Vfs(name, root, source="memory")
