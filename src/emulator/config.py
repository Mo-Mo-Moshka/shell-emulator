"""Параметры запуска эмулятора из командной строки."""

import argparse
import os
from dataclasses import dataclass
from typing import Optional

DEFAULT_VFS_NAME = "vfs"
NOT_SET = "(not set)"


@dataclass
class Config:
    """Настройки эмулятора, заданные пользователем при запуске.

    vfs_path — путь к физическому расположению VFS,
    log_path — путь к лог-файлу CSV,
    script_path — путь к стартовому скрипту.
    """

    vfs_path: Optional[str] = None
    log_path: Optional[str] = None
    script_path: Optional[str] = None

    @property
    def vfs_name(self):
        """Имя VFS — последний компонент пути к ней."""
        if not self.vfs_path:
            return DEFAULT_VFS_NAME
        name = os.path.basename(os.path.normpath(self.vfs_path))
        return name or DEFAULT_VFS_NAME


def build_arg_parser():
    """Создать разборщик параметров командной строки."""
    parser = argparse.ArgumentParser(
        prog="shell-emulator",
        description="UNIX shell emulator with a GUI.",
    )
    parser.add_argument(
        "--vfs", dest="vfs_path", metavar="PATH",
        help="path to the physical location of the VFS",
    )
    parser.add_argument(
        "--log", dest="log_path", metavar="FILE",
        help="path to the CSV log file",
    )
    parser.add_argument(
        "--script", dest="script_path", metavar="FILE",
        help="path to the startup script",
    )
    return parser


def parse_args(argv=None):
    """Разобрать параметры командной строки и вернуть Config.

    При неверных параметрах argparse печатает ошибку и завершает
    программу с кодом 2.
    """
    namespace = build_arg_parser().parse_args(argv)
    return Config(
        vfs_path=namespace.vfs_path,
        log_path=namespace.log_path,
        script_path=namespace.script_path,
    )


def describe_config(config):
    """Вернуть строки отладочного вывода со всеми параметрами."""
    return [
        f"[debug] vfs path     = {config.vfs_path or NOT_SET}",
        f"[debug] vfs name     = {config.vfs_name}",
        f"[debug] log file     = {config.log_path or NOT_SET}",
        f"[debug] start script = {config.script_path or NOT_SET}",
    ]
