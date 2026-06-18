"""Unit-тесты для transducer.py."""
import pytest

from eng_to_ru_transcriber.transducer import apply_rules, process_text, HAS_REGEX_SYMBOLS


class TestHasRegexSymbols:
    """Проверка детектора regex-символов."""

    def test_detects_asterisk(self):
        assert HAS_REGEX_SYMBOLS.search("a*") is not None

    def test_detects_brackets(self):
        assert HAS_REGEX_SYMBOLS.search("[abc]") is not None

    def test_detects_parentheses(self):
        assert HAS_REGEX_SYMBOLS.search("(a|b)") is not None

    def test_detects_dot(self):
        assert HAS_REGEX_SYMBOLS.search("a.b") is not None

    def test_no_regex(self):
        assert HAS_REGEX_SYMBOLS.search("abc") is None
        assert HAS_REGEX_SYMBOLS.search("hello world") is None


class TestApplyRules:
    """Применение правил к тексту."""

    def test_simple_replacement(self):
        rules = [("a", "x"), ("b", "y")]
        assert apply_rules("ab", rules) == "xy"

    def test_regex_rule(self):
        rules = [(r"a+", "X")]
        assert apply_rules("aaa", rules) == "X"

    def test_mixed_rules(self):
        rules = [("a", "x"), (r"b+", "Y")]
        assert apply_rules("abb", rules) == "xY"

    def test_order_matters(self):
        # Первое правило меняет "a" на "b", второе не должно сработать
        rules = [("a", "b"), ("b", "c")]
        assert apply_rules("a", rules) == "c"

    def test_empty_rules(self):
        assert apply_rules("hello", []) == "hello"

    def test_empty_text(self):
        assert apply_rules("", [("a", "b")]) == ""

class TestProcessText:
    """Полный процесс с нормализацией."""

    def test_basic(self):
        rules = [("a", "x")]
        assert process_text("abc", rules) == "xbc"

    def test_unicode_normalization(self):
        # ✅ NFC-нормализация объединяет "e" + combining accent в один символ "é"
        text = "cafe\u0301"  # 5 символов: c, a, f, e, combining accent
        result = process_text(text, [])
        # После NFC: c, a, f, é = 4 символа
        assert len(result) == 4
        assert result == "café"