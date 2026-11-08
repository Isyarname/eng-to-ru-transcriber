"""Unit-тесты для eng_to_ipa_hybrid.py."""
import pytest

from eng_to_ru_transcriber.eng_to_ipa_hybrid import (
    _tokenize,
    _normalize_ipa_word,
    transcribe,
    smart_lower,
)


class TestSmartLower:
    def test_already_lowercase(self):
        assert smart_lower("hello world") == "hello world"

    def test_camel_case(self):
        assert smart_lower("MacBook") == "macbook"
        assert smart_lower("CamelCase") == "camelcase"

    def test_uppercase_abbreviation(self):
        assert smart_lower("myURL") == "my-URL"
        assert smart_lower("parseXMLData") == "parse-XMLdata"

    def test_mixed_case_and_abbreviation(self):
        assert smart_lower("MacOS") == "mac-OS"
        assert smart_lower("getHTTPResponseCode") == "get-HTTPresponsecode"

    def test_all_caps(self):
        assert smart_lower("USA") == "USA"


class TestTokenize:
    def test_simple(self):
        assert _tokenize("hello world") == ["hello", " ", "world"]

    def test_with_punctuation(self):
        assert _tokenize("hello, world!") == ["hello", ", ", "world", "!"]

    def test_empty(self):
        assert _tokenize("") == []

    def test_only_spaces(self):
        assert _tokenize("   ") == ["   "]


class TestNormalizeIpaWord:
    def test_diphthong_ei(self):
        assert _normalize_ipa_word("deɪ", [("eɪ", "ej")], {}) == "dej"

    def test_diphthong_ai(self):
        assert _normalize_ipa_word("maɪ", [("aɪ", "aj")], {}) == "maj"

    def test_word_normalization(self):
        assert _normalize_ipa_word("tə", [], {"tə": "tu"}) == "tu"

    def test_word_normalization_not_substring(self):
        assert _normalize_ipa_word("təmɔɹoʊ", [], {"tə": "tu"}) == "təmɔɹoʊ"

    def test_slash_removal(self):
        assert _normalize_ipa_word("he/llo", [("/", "")], {}) == "hello"


class TestTranscribe:
    _EMPTY_RULES = []
    _EMPTY_NORMS = ([], {})

    def test_empty(self):
        assert transcribe("", {}, frozenset(), self._EMPTY_RULES, *self._EMPTY_NORMS) == ""

    def test_with_exceptions(self):
        exceptions = {"hello": "hɛˈloʊ", "world": "wɝːld"}
        long_keys = frozenset({"hello", "world"})
        result = transcribe("hello world", exceptions, long_keys, self._EMPTY_RULES, *self._EMPTY_NORMS)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_preserves_punctuation(self):
        exceptions = {"hello": "hɛˈloʊ"}
        long_keys = frozenset({"hello"})
        result = transcribe("hello!", exceptions, long_keys, self._EMPTY_RULES, *self._EMPTY_NORMS)
        assert "!" in result

    def test_mixed_known_unknown(self):
        exceptions = {"hello": "hɛˈloʊ"}
        long_keys = frozenset({"hello"})
        result = transcribe("hello xyzzy", exceptions, long_keys, self._EMPTY_RULES, *self._EMPTY_NORMS)
        assert isinstance(result, str)

    def test_fallback_long_keys(self):
        exceptions = {"hello": "hɛˈloʊ"}
        result = transcribe("hello", exceptions, None, self._EMPTY_RULES, *self._EMPTY_NORMS)
        assert isinstance(result, str)
