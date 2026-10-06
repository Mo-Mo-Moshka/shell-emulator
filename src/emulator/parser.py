"""Разбор командной строки эмулятора.

Строка делится на слова по пробелам с учётом кавычек и экранирования,
как в UNIX-оболочке sh:

* ``'...'`` — текст берётся как есть, переменные не раскрываются;
* ``"..."`` — переменные раскрываются, пробелы сохраняются;
* ``\\x`` — символ ``x`` берётся буквально;
* ``$NAME`` и ``${NAME}`` — подстановка переменной окружения реальной ОС;
* ``# ...`` — комментарий до конца строки.
"""

import os
import re

COMMENT = "#"

_TOKEN_RE = re.compile(
    r"""
    (?P<space>\s+)
    | '(?P<single>[^']*)'
    | "(?P<double>(?:\\.|[^"\\])*)"
    | \\(?P<escaped>.)
    | (?P<plain>[^\s'"\\]+)
    """,
    re.VERBOSE | re.DOTALL,
)

_VAR_PATTERN = (
    r"\$\{(?P<braced>[^}]*)(?P<close>\}?)"
    r"|\$(?P<name>[A-Za-z_]\w*)"
)
_VAR_RE = re.compile(_VAR_PATTERN)
_DOUBLE_RE = re.compile(r'\\(?P<esc>[\\"$`])|' + _VAR_PATTERN)
_NAME_RE = re.compile(r"[A-Za-z_]\w*\Z")

_QUOTE_NAMES = {"'": "single quote", '"': "double quote"}


class ParseError(Exception):
    """Ошибка синтаксиса командной строки."""


def parse(line):
    """Разбить строку на слова: имя команды и её аргументы.

    Возвращает список строк. Пустая строка даёт пустой список.
    При незакрытой кавычке или ошибке подстановки бросает ParseError.
    """
    words = []
    parts = []
    quoted = False
    pos = 0
    while pos < len(line):
        match = _TOKEN_RE.match(line, pos)
        if match is None:
            raise ParseError(_describe_error(line[pos]))
        pos = match.end()
        kind = match.lastgroup
        if kind == "space":
            _flush_word(words, parts, quoted)
            parts, quoted = [], False
        elif _starts_comment(kind, match.group(kind), parts):
            break
        else:
            parts.append(_expand_part(kind, match.group(kind)))
            quoted = quoted or kind != "plain"
    _flush_word(words, parts, quoted)
    return words


def expand_variables(text):
    """Подставить в текст значения переменных окружения.

    Неизвестная переменная заменяется пустой строкой, как в sh.
    """
    return _VAR_RE.sub(_substitute_variable, text)


def _expand_double_quoted(text):
    """Обработать содержимое двойных кавычек: экранирование и $NAME."""
    return _DOUBLE_RE.sub(_substitute_in_double, text)


def _substitute_in_double(match):
    """Заменить экранированный символ или переменную внутри "..."."""
    if match.group("esc") is not None:
        return match.group("esc")
    return _substitute_variable(match)


def _substitute_variable(match):
    """Вернуть значение переменной окружения для совпадения $NAME."""
    name = match.group("name")
    if name is None:
        name = match.group("braced")
        if not match.group("close") or not _NAME_RE.match(name):
            raise ParseError(f"{match.group(0)}: bad substitution")
    return os.environ.get(name, "")


def _expand_part(kind, value):
    """Преобразовать фрагмент слова в зависимости от вида кавычек."""
    if kind == "double":
        return _expand_double_quoted(value)
    if kind == "plain":
        return expand_variables(value)
    return value


def _starts_comment(kind, value, parts):
    """Истина, если фрагмент начинает комментарий.

    Как в sh, ``#`` открывает комментарий только в начале слова и
    только вне кавычек: в ``a#b`` и ``'#x'`` это обычный символ.
    """
    return kind == "plain" and not parts and value.startswith(COMMENT)


def _flush_word(words, parts, quoted):
    """Добавить собранное слово в список.

    Слово без кавычек, ставшее пустым после подстановки (например,
    неизвестная переменная), отбрасывается, как в sh. Пустые кавычки
    ``""`` дают пустой аргумент.
    """
    word = "".join(parts)
    if word or quoted:
        words.append(word)


def _describe_error(char):
    """Сформировать текст ошибки для символа, на котором сломался разбор."""
    if char in _QUOTE_NAMES:
        return f"unexpected end of line: unclosed {_QUOTE_NAMES[char]}"
    return "unexpected end of line after '\\'"
