"""Unit-тесты для ipa_to_ru.py."""
import pytest

from eng_to_ru_transcriber import ipa_to_ru


class TestIpaToRuConvert:
    """Проверка конвертации IPA в кириллицу."""

    def test_empty_text(self):
        assert ipa_to_ru.convert("", []) == ""

    def test_empty_rules(self):
        assert ipa_to_ru.convert("test", []) == "test"

    def test_simple_replacement(self):
        rules = [("a", "а"), ("b", "б")]
        assert ipa_to_ru.convert("ab", rules) == "аб"

    def test_regex_replacement(self):
        # Проверяем, что регулярки корректно передаются в движок
        rules = [("[aeiou]", "*")]
        assert ipa_to_ru.convert("cat", rules) == "c*t"

    def test_no_match(self):
        rules = [("a", "а")]
        assert ipa_to_ru.convert("xyz", rules) == "xyz"

    def test_normalization(self):
        # Проверка, что NFC-нормализация из rule_engine работает и здесь
        rules = []
        text = "cafe\u0301"  # e + combining accent
        result = ipa_to_ru.convert(text, rules)
        assert len(result) == 4
        assert result == "café"