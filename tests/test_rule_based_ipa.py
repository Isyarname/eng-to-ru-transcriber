"""Unit-тесты для rule_based_ipa.py."""
import re
import pytest
from eng_to_ru_transcriber.rule_based_ipa import transcribe


class TestTranscribe:
    """Проверка транскрипции (применения правил)."""

    def test_empty_text(self):
        assert transcribe("", []) == ""

    def test_simple_rule(self):
        # Применение простого правила
        rules = [("a", "б", False)]
        assert transcribe("a", rules) == "б"

    def test_applies_rules(self):
        rules = [("abc", "xyz", False)]
        assert transcribe("abc", rules) == "xyz"

    def test_transcribe_with_regex(self):
        # Проверка, что регулярки в правилах тоже работают.
        # Передаем уже скомпилированный паттерн!
        rules = [(re.compile("[aeiou]"), "*", True)]
        assert transcribe("cat", rules) == "c*t"
