"""Unit-тесты для eng_to_ipa_hybrid.py."""
import pytest

from eng_to_ru_transcriber.eng_to_ipa_hybrid import (
    _tokenize,
    _is_word,
    _normalize_ipa_word,
    transcribe,
)


class TestTokenize:
    """Разбиение текста на токены."""

    def test_simple(self):
        assert _tokenize("hello world") == ["hello", " ", "world"]

    def test_with_punctuation(self):
        result = _tokenize("hello, world!")
        # ✅ Запятая и пробел объединяются в один токен (оба не буквы/апострофы)
        assert result == ["hello", ", ", "world", "!"]

    def test_empty(self):
        assert _tokenize("") == []

    def test_only_spaces(self):
        assert _tokenize("   ") == ["   "]

class TestIsWord:
    """Проверка, является ли токен словом."""

    def test_regular_word(self):
        assert _is_word("hello") is True

    def test_with_apostrophe(self):
        assert _is_word("don't") is True

    def test_space(self):
        assert _is_word(" ") is False

    def test_punctuation(self):
        assert _is_word(",") is False
        assert _is_word("!") is False

    def test_mixed(self):
        assert _is_word("hello!") is False


class TestNormalizeIpaWord:
    """Нормализация IPA-слов."""

    def test_diphthong_ei(self):
        # eɪ → ej
        result = _normalize_ipa_word("deɪ")
        assert result == "dej"

    def test_diphthong_ai(self):
        result = _normalize_ipa_word("maɪ")
        assert result == "maj"

    def test_word_normalization(self):
        # "tə" как целое слово → "tu"
        result = _normalize_ipa_word("tə")
        assert result == "tu"

    def test_word_normalization_not_substring(self):
        # "təmɔɹoʊ" НЕ должен превратиться в "tumɔɹoʊ"
        result = _normalize_ipa_word("təmɔɹoʊ")
        assert result == "təmɔɹoʊ"

    def test_slash_removal(self):
        result = _normalize_ipa_word("he/llo")
        assert result == "hello"


class TestTranscribe:
    """Полная транскрипция через гибридный движок."""

    def test_empty(self):
        assert transcribe("", {}) == ""

    def test_with_exceptions(self):
        # Все слова в исключениях — gruut не должен вызываться
        exceptions = {"hello": "hɛˈloʊ", "world": "wɝːld"}
        result = transcribe("hello world", exceptions)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_preserves_punctuation(self):
        exceptions = {"hello": "hɛˈloʊ"}
        result = transcribe("hello!", exceptions)
        assert "!" in result

    def test_mixed_known_unknown(self):
        # Одно слово в исключениях, другое — нет
        exceptions = {"hello": "hɛˈloʊ"}
        result = transcribe("hello xyzzy", exceptions)
        assert isinstance(result, str)