"""Интеграционные тесты класса Transcriber."""
import pytest

from eng_to_ru_transcriber import Transcriber, __version__


class TestPublicAPI:
    """Проверка публичного API."""

    def test_version_defined(self):
        assert __version__ == "0.1.0"

    def test_transcriber_class_exists(self):
        assert Transcriber is not None


class TestTranscriberClass:
    """Тесты объектного API."""

    def test_creation(self):
        t = Transcriber()
        r = repr(t)
        # Формат: Transcriber(ipa_rules=N, eng_rules=N, dict=N)
        assert r.startswith("Transcriber(ipa_rules=")
        assert "eng_rules=" in r
        assert "dict=" in r

    def test_eager_loading(self):
        """Все ресурсы загружаются в конструкторе, без отложенной загрузки."""
        t = Transcriber()
        assert t._transliteration_rules is not None
        assert t._eng_to_ipa_rules is not None
        assert t._dict_cache is not None

    def test_resources_are_non_empty(self):
        """Ресурсы не просто загружены, а содержат данные."""
        t = Transcriber()
        assert len(t._transliteration_rules) > 0
        assert len(t._eng_to_ipa_rules) > 0
        assert len(t._dict_cache) > 0

    def test_multiple_calls_use_cache(self):
        t = Transcriber()
        ru_rules_ref = t._transliteration_rules
        eng_rules_ref = t._eng_to_ipa_rules
        dict_ref = t._dict_cache

        # Вызовы не пересоздают ресурсы
        t.transcribe("hello")
        t.transcribe("world")
        assert t._transliteration_rules is ru_rules_ref
        assert t._eng_to_ipa_rules is eng_rules_ref
        assert t._dict_cache is dict_ref

    def test_reload_dictionary(self):
        t = Transcriber()
        old_dict = t._dict_cache

        t.reload_dictionary()
        assert t._dict_cache is not old_dict

    def test_reload_rules(self):
        t = Transcriber()
        old_ru_rules = t._transliteration_rules
        old_eng_rules = t._eng_to_ipa_rules

        t.reload_rules()
        assert t._transliteration_rules is not old_ru_rules
        assert t._eng_to_ipa_rules is not old_eng_rules

    def test_reload_all(self):
        t = Transcriber()
        old_ru_rules = t._transliteration_rules
        old_eng_rules = t._eng_to_ipa_rules
        old_dict = t._dict_cache

        t.reload_all()
        assert t._transliteration_rules is not old_ru_rules
        assert t._eng_to_ipa_rules is not old_eng_rules
        assert t._dict_cache is not old_dict


class TestCustomVocabulary:
    """Тесты пользовательского словаря."""

    def test_custom_vocabulary_on_init(self):
        custom = {"python": "ˈpaɪθɑn"}
        t = Transcriber(custom_vocabulary=custom)
        assert t._custom_vocabulary == custom

    def test_custom_vocabulary_supplements_builtin(self):
        """Пользовательский словарь дополняет встроенный, а не заменяет."""
        custom = {"myword": "maɪwɝːd"}
        t = Transcriber(custom_vocabulary=custom)

        combined = t.get_vocabulary()

        # Встроенные слова должны быть
        assert "hello" in combined
        assert "world" in combined

        # Пользовательские тоже
        assert "myword" in combined
        assert combined["myword"] == "maɪwɝːd"

    def test_custom_vocabulary_overrides_builtin(self):
        """Пользовательский имеет приоритет при конфликте."""
        custom = {"hello": "hɛˈloʊ_custom"}
        t = Transcriber(custom_vocabulary=custom)

        combined = t.get_vocabulary()
        assert combined["hello"] == "hɛˈloʊ_custom"

    def test_empty_custom_vocabulary(self):
        t = Transcriber(custom_vocabulary={})
        combined = t.get_vocabulary()
        assert "hello" in combined

    def test_no_custom_vocabulary_by_default(self):
        t = Transcriber()
        assert t._custom_vocabulary == {}

    def test_custom_vocabulary_is_copied(self):
        """Изменение исходного dict не влияет на объект."""
        custom = {"word": "w"}
        t = Transcriber(custom_vocabulary=custom)
        custom["new"] = "n"
        assert "new" not in t._custom_vocabulary


class TestBasicTranscription:
    """Базовая транскрипция."""

    def test_empty_string(self):
        t = Transcriber()
        assert t.transcribe("") == ""

    def test_returns_string(self):
        t = Transcriber()
        result = t.transcribe("hello")
        assert isinstance(result, str)

    def test_contains_cyrillic(self):
        t = Transcriber()
        result = t.transcribe("hello")
        # Должна появиться хотя бы одна кириллическая буква
        assert any("\u0400" <= ch <= "\u04FF" for ch in result)

    def test_preserves_punctuation(self):
        t = Transcriber()
        result = t.transcribe("hello, world!")
        assert "," in result
        assert "!" in result

    def test_determinism(self):
        t = Transcriber()
        r1 = t.transcribe("hello world")
        r2 = t.transcribe("hello world")
        assert r1 == r2


class TestEdgeCases:
    """Краевые входы."""

    def test_numbers(self):
        t = Transcriber()
        result = t.transcribe("test 123")
        assert isinstance(result, str)

    def test_long_text(self):
        t = Transcriber()
        text = "hello world " * 100
        result = t.transcribe(text)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_only_whitespace(self):
        t = Transcriber()
        result = t.transcribe("   ")
        assert result.strip() == ""

    def test_only_punctuation(self):
        t = Transcriber()
        result = t.transcribe("...")
        assert result == "..."


class TestMultipleInstances:
    """Несколько экземпляров с разными настройками."""

    def test_independent_instances(self):
        t1 = Transcriber(custom_vocabulary={"word": "w1"})
        t2 = Transcriber(custom_vocabulary={"word": "w2"})

        assert t1.get_vocabulary()["word"] == "w1"
        assert t2.get_vocabulary()["word"] == "w2"

    def test_instance_without_custom(self):
        t1 = Transcriber(custom_vocabulary={"word": "w"})
        t2 = Transcriber()

        assert "word" in t1.get_vocabulary()
        # У t2 пользовательского слова нет
        assert "word" not in t2._custom_vocabulary
