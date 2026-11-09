"""Интеграционные тесты класса Transcriber."""
import pytest

from eng_to_ru_transcriber import Transcriber, __version__


class TestPublicAPI:
    def test_version_defined(self):
        assert __version__

    def test_transcriber_class_exists(self):
        assert Transcriber is not None


class TestTranscriberClass:
    """Тесты объектного API."""

    def test_creation(self):
        t = Transcriber()
        r = repr(t)
        assert r.startswith("Transcriber(translit_rules=")
        assert "eng_to_ipa_rules=" in r
        assert "dict=" in r

    def test_eager_loading(self):
        t = Transcriber()
        assert t._transliteration_rules is not None
        assert t._eng_to_ipa_rules is not None
        assert t._en_dict is not None
        assert t._substring_norms is not None
        assert t._word_norms is not None

    def test_long_keys_precomputed(self):
        """Список длинных ключей для разбиения предвычислен (frozenset)."""
        t = Transcriber()
        assert isinstance(t._long_keys, frozenset)
        assert len(t._long_keys) > 0

    def test_resources_are_non_empty(self):
        t = Transcriber()
        assert len(t._transliteration_rules) > 0
        assert len(t._eng_to_ipa_rules) > 0
        assert len(t._en_dict) > 0

    def test_multiple_calls_use_cache(self):
        t = Transcriber()
        ru_rules_ref = t._transliteration_rules
        eng_rules_ref = t._eng_to_ipa_rules
        dict_ref = t._en_dict
        merged_ref = t._merged_vocabulary
        long_keys_ref = t._long_keys

        t.transcribe("hello")
        t.transcribe("world")

        assert t._transliteration_rules is ru_rules_ref
        assert t._eng_to_ipa_rules is eng_rules_ref
        assert t._en_dict is dict_ref
        assert t._merged_vocabulary is merged_ref
        assert t._long_keys is long_keys_ref


class TestCustomVocabulary:
    def test_custom_vocabulary_on_init(self):
        custom = {"python": "ˈpaɪθɑn"}
        t = Transcriber(custom_vocabulary=custom)
        assert t._custom_vocabulary == custom

    def test_custom_vocabulary_mixed_formats(self):
        """Можно смешивать IPA и кириллицу в одном словаре."""
        custom = {
            "python": "пайтон",               # кириллица
            "kubernetes": "ˌkjuːbəˈnɛtɪs"     # IPA
        }
        t = Transcriber(custom_vocabulary=custom)
        result = t.transcribe("python kubernetes")

        # python должен остаться пайтоном
        assert "пайтон" in result
        # kubernetes должен сконвертироваться в кириллицу (точный вид зависит от правил,
        # но латиницы и IPA-символов там быть не должно)
        assert "kju" not in result
        assert any("\u0400" <= ch <= "\u04FF" for ch in result)

    def test_custom_vocabulary_supplements_builtin(self):
        custom = {"myword": "maɪwɝːd"}
        t = Transcriber(custom_vocabulary=custom)
        combined = t._merged_vocabulary
        assert "hello" in combined
        assert "world" in combined
        assert "myword" in combined
        assert combined["myword"] == "maɪwɝːd"

    def test_custom_vocabulary_overrides_builtin(self):
        custom = {"hello": "hɛˈloʊ_custom"}
        t = Transcriber(custom_vocabulary=custom)
        assert t._merged_vocabulary["hello"] == "hɛˈloʊ_custom"

    def test_empty_custom_vocabulary(self):
        t = Transcriber(custom_vocabulary={})
        assert "hello" in t._merged_vocabulary

    def test_no_custom_vocabulary_by_default(self):
        t = Transcriber()
        assert t._custom_vocabulary == {}

    def test_custom_vocabulary_is_copied(self):
        """Изменение исходного dict не влияет на объект."""
        custom = {"word": "w"}
        t = Transcriber(custom_vocabulary=custom)
        custom["fake_key_xyzzy"] = "n"
        assert "fake_key_xyzzy" not in t._custom_vocabulary
        assert "fake_key_xyzzy" not in t._merged_vocabulary


class TestBasicTranscription:
    def test_empty_string(self):
        t = Transcriber()
        assert t.transcribe("") == ""

    def test_returns_string(self):
        t = Transcriber()
        assert isinstance(t.transcribe("hello"), str)

    def test_contains_cyrillic(self):
        t = Transcriber()
        result = t.transcribe("hello")
        assert any("\u0400" <= ch <= "\u04FF" for ch in result)

    def test_preserves_punctuation(self):
        t = Transcriber()
        result = t.transcribe("hello, world!")
        assert "," in result
        assert "!" in result

    def test_determinism(self):
        t = Transcriber()
        assert t.transcribe("hello world") == t.transcribe("hello world")


class TestEdgeCases:
    def test_numbers(self):
        t = Transcriber()
        assert isinstance(t.transcribe("test 123"), str)

    def test_long_text(self):
        t = Transcriber()
        result = t.transcribe("hello world " * 100)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_only_whitespace(self):
        t = Transcriber()
        assert t.transcribe("   ").strip() == ""

    def test_only_punctuation(self):
        t = Transcriber()
        assert t.transcribe("...") == "..."


class TestMultipleInstances:
    def test_independent_instances(self):
        t1 = Transcriber(custom_vocabulary={"word": "w1"})
        t2 = Transcriber(custom_vocabulary={"word": "w2"})
        assert t1._merged_vocabulary["word"] == "w1"
        assert t2._merged_vocabulary["word"] == "w2"

    def test_instance_without_custom(self):
        t1 = Transcriber(custom_vocabulary={"word": "w"})
        t2 = Transcriber()
        assert "word" in t1._merged_vocabulary
        assert "word" not in t2._custom_vocabulary
