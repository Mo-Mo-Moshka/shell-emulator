"""Стартовый скрипт: команды эмулятора, выполняемые при запуске.

Скрипт — текстовый файл (UTF-8), одна команда в строке. Пустые
строки и строки-комментарии (``# ...``) пропускаются. Выполнение
останавливается на первой команде, завершившейся с ошибкой.
"""

from dataclasses import dataclass
from typing import Optional

from emulator.parser import COMMENT

SCRIPT_ENCODING = "utf-8-sig"


class ScriptError(Exception):
    """Стартовый скрипт не удалось прочитать."""


@dataclass
class ScriptOutcome:
    """Итог выполнения скрипта.

    failed_line — номер строки с ошибкой (None, если ошибок нет),
    exited — истина, если скрипт завершил эмулятор командой exit.
    """

    failed_line: Optional[int] = None
    exited: bool = False


def read_script(path):
    """Прочитать скрипт и вернуть список его строк."""
    try:
        with open(path, encoding=SCRIPT_ENCODING) as file:
            return file.read().splitlines()
    except OSError as error:
        reason = error.strerror or str(error)
        raise ScriptError(f"cannot read '{path}': {reason}") from None
    except UnicodeDecodeError:
        raise ScriptError(f"cannot read '{path}': not UTF-8 text") from None


def is_skipped(line):
    """Истина для пустой строки или строки-комментария."""
    text = line.strip()
    return not text or text.startswith(COMMENT)


def run_script(lines, run_line):
    """Выполнить строки скрипта функцией run_line.

    run_line(line) должна вернуть CommandResult. Выполнение
    прекращается на первой ошибке или на команде exit.
    """
    for number, line in enumerate(lines, start=1):
        if is_skipped(line):
            continue
        result = run_line(line)
        if result.error:
            return ScriptOutcome(failed_line=number)
        if result.should_exit:
            return ScriptOutcome(exited=True)
    return ScriptOutcome()
