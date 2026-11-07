"""Unit-тесты для rule_engine.py."""
import re
import pytest

from eng_to_ru_transcriber.rule_engine import apply_rules, process_text


class TestApplyRules:
    """Применение правил к тексту."""

    def test_simple_replacement(self):
        rules = [("a", "x", False), ("b", "y", False)]
        assert apply_rules("ab", rules) == "xy"

    def test_regex_rule(self):
        # Передаем уже скомпилированный паттерн
        rules = [(re.compile(r"a+"), "X", True)]
        assert apply_rules("aaa", rules) == "X"

    def test_mixed_rules(self):
        rules = [("a", "x", False), (re.compile(r"b+"), "Y", True)]
        assert apply_rules("abb", rules) == "xY"

    def test_order_matters(self):
        # Первое правило меняет "a" на "b", второе не должно сработать
        rules = [("a", "b", False), ("b", "c", False)]
        assert apply_rules("a", rules) == "c"

    def test_empty_rules(self):
        assert apply_rules("hello", []) == "hello"

    def test_empty_text(self):
        assert apply_rules("", [("a", "b", False)]) == ""


class TestProcessText:
    """Полный процесс с нормализацией."""

    def test_basic(self):
        rules = [("a", "x", False)]
        assert process_text("abc", rules) == "xbc"

    def test_unicode_normalization(self):
        # ✅ NFC-нормализация объединяет "e" + combining accent в один символ "é"
        text = "cafe\u0301"  # 5 символов: c, a, f, e, combining accent
        result = process_text(text, [])
        # После NFC: c, a, f, é = 4 символа
        assert len(result) == 4
        assert result == "café"
