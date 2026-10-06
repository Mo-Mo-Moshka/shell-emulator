"""Тесты разбора командной строки."""

import os
import unittest
from unittest import mock

from emulator.parser import ParseError, parse

TEST_ENV = {"EMU_HOME": "/home/user", "EMU_EMPTY": ""}


@mock.patch.dict(os.environ, TEST_ENV)
class ParseTest(unittest.TestCase):
    """Проверки функции parse."""

    def test_splits_by_whitespace(self):
        """Слова разделяются любым количеством пробелов."""
        self.assertEqual(parse("  ls   -l\t/tmp "), ["ls", "-l", "/tmp"])

    def test_empty_line(self):
        """Пустая строка даёт пустой список."""
        self.assertEqual(parse("   "), [])

    def test_expands_variable(self):
        """$NAME заменяется значением переменной окружения."""
        self.assertEqual(parse("cd $EMU_HOME"), ["cd", "/home/user"])

    def test_expands_braced_variable(self):
        """${NAME} можно склеивать с текстом."""
        self.assertEqual(parse("ls ${EMU_HOME}/docs"),
                         ["ls", "/home/user/docs"])

    def test_undefined_variable_is_dropped(self):
        """Неизвестная переменная без кавычек исчезает, как в sh."""
        self.assertEqual(parse("ls $EMU_UNDEFINED x"), ["ls", "x"])

    def test_empty_quotes_give_empty_argument(self):
        """Пустые кавычки — это пустой аргумент."""
        self.assertEqual(parse('ls "$EMU_EMPTY" \'\''), ["ls", "", ""])

    def test_single_quotes_are_literal(self):
        """В одинарных кавычках переменные не раскрываются."""
        self.assertEqual(parse("ls '$EMU_HOME a'"), ["ls", "$EMU_HOME a"])

    def test_double_quotes_expand(self):
        """В двойных кавычках переменные раскрываются, пробелы остаются."""
        self.assertEqual(parse('ls "$EMU_HOME/my dir"'),
                         ["ls", "/home/user/my dir"])

    def test_escapes(self):
        """Обратная косая черта экранирует символы."""
        self.assertEqual(parse(r'ls a\ b \$EMU_HOME "\$x \"q\""'),
                         ["ls", "a b", "$EMU_HOME", '$x "q"'])

    def test_lone_dollar_is_literal(self):
        """Знак $ без имени остаётся как есть."""
        self.assertEqual(parse("ls $ a$"), ["ls", "$", "a$"])

    def test_comments(self):
        """# в начале слова открывает комментарий до конца строки."""
        self.assertEqual(parse("# only comment"), [])
        self.assertEqual(parse("ls -a  # list all"), ["ls", "-a"])

    def test_hash_inside_word_or_quotes(self):
        """# внутри слова или в кавычках — обычный символ."""
        self.assertEqual(parse("ls a#b '#c' \\#d"),
                         ["ls", "a#b", "#c", "#d"])

    def test_unclosed_single_quote(self):
        """Незакрытая одинарная кавычка — ошибка."""
        with self.assertRaisesRegex(ParseError, "single quote"):
            parse("ls 'abc")

    def test_unclosed_double_quote(self):
        """Незакрытая двойная кавычка — ошибка."""
        with self.assertRaisesRegex(ParseError, "double quote"):
            parse('ls "abc')

    def test_trailing_backslash(self):
        """Обратная косая черта в конце строки — ошибка."""
        with self.assertRaises(ParseError):
            parse("ls abc\\")

    def test_bad_substitution(self):
        """Некорректная подстановка ${...} — ошибка."""
        for line in ("ls ${EMU_HOME", "ls ${1x}", "ls ${}"):
            with self.subTest(line=line):
                with self.assertRaisesRegex(ParseError, "bad substitution"):
                    parse(line)


if __name__ == "__main__":
    unittest.main()
