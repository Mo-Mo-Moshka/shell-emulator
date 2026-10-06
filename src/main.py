"""Точка входа эмулятора командной оболочки.

Пример: ``python src/main.py --vfs vfs/minimal --log log.csv
--script start.txt``.
"""

import sys

from emulator.config import describe_config, parse_args
from emulator.gui import TerminalWindow
from emulator.logger import CsvLogger, NullLogger
from emulator.shell import Shell


def create_logger(path):
    """Создать журнал по пути path.

    Возвращает пару (журнал, текст ошибки). Если путь не задан или
    файл нельзя открыть, используется NullLogger.
    """
    if path is None:
        return NullLogger(), ""
    try:
        return CsvLogger(path), ""
    except OSError as error:
        reason = error.strerror or str(error)
        return NullLogger(), f"log file '{path}': {reason}"


def main(argv=None):
    """Запустить эмулятор с параметрами argv и вернуть код завершения."""
    config = parse_args(argv)
    debug_lines = describe_config(config)
    print("\n".join(debug_lines), flush=True)
    logger, log_error = create_logger(config.log_path)
    window = TerminalWindow(Shell(config.vfs_name, logger))
    window.write_lines(debug_lines, "debug")
    if log_error:
        print(f"error: {log_error}", file=sys.stderr, flush=True)
        window.write(f"{log_error}\n", "error")
    if config.script_path is not None:
        window.root.after_idle(window.run_script_file, config.script_path)
    window.mainloop()
    return window.exit_code


if __name__ == "__main__":
    sys.exit(main())
