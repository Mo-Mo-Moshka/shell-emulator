"""Точка входа эмулятора командной оболочки."""

import sys

from emulator.gui import TerminalWindow
from emulator.shell import Shell


def main():
    """Открыть окно эмулятора и вернуть код завершения."""
    window = TerminalWindow(Shell())
    window.mainloop()
    return window.exit_code


if __name__ == "__main__":
    sys.exit(main())
