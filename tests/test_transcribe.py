"""Тесты публичного API."""
import pytest

from eng_to_ru_transcriber import Transcriber, __version__


class TestPublicAPI:
    def test_version_defined(self):
        assert __version__ == "0.1.0"

    def test_transcriber_class_exists(self):
        assert Transcriber is not None


class TestTranscriberClass:
    """Тесты объектного API."""

    def test_creation(self):
        t = Transcriber()
        assert repr(t) == "Transcriber(rules=нет, dict=нет)"

    def test_lazy_loading(self):
        t = Transcriber()
        assert t._compiled_rules is None
        assert t._dict_cache is None

        t.transcribe("hello")
        assert t._compiled_rules is not None
        assert t._dict_cache is not None
        assert "rules=загружены" in repr(t)

    def test_multiple_calls_use_cache(self):
        t = Transcriber()
        t.transcribe("hello")
        rules_ref = t._compiled_rules
        dict_ref = t._dict_cache

        t.transcribe("world")
        assert t._compiled_rules is rules_ref
        assert t._dict_cache is dict_ref

    def test_reload_dictionary(self):
        t = Transcriber()
        t.transcribe("hello")
        old_dict = t._dict_cache

        t.reload_dictionary()
        assert t._dict_cache is not old_dict

    def test_reload_transliteration(self):
        t = Transcriber()
        t.transcribe("hello")
        old_rules = t._compiled_rules

        t.reload_transliteration()
        assert t._compiled_rules is not old_rules

    def test_transcribe_many(self):
        t = Transcriber()
        results = t.transcribe_many(["hello", "world", "test"])
        assert len(results) == 3
        assert all(isinstance(r, str) for r in results)


class TestCustomExceptions:
    """Тесты пользовательских исключений."""

    def test_custom_exceptions_on_init(self):
        custom = {"python": "ˈpaɪθɑn"}
        t = Transcriber(custom_exceptions=custom)
        # Пользовательские загружены сразу
        assert t._custom_exceptions == custom
        assert "custom=1" in repr(t)

    def test_custom_exceptions_supplement_builtin(self):
        """Пользовательские дополняют встроенный, а не заменяют."""
        custom = {"myword": "maɪwɝːd"}
        t = Transcriber(custom_exceptions=custom)
        
        combined = t.get_dict()
        
        # Встроенные слова должны быть
        assert "hello" in combined
        assert "world" in combined
        
        # Пользовательские тоже
        assert "myword" in combined
        assert combined["myword"] == "maɪwɝːd"

    def test_custom_exceptions_override_builtin(self):
        """Пользовательские имеют приоритет при конфликте."""
        # Переопределяем встроенное слово "hello"
        custom = {"hello": "hɛˈloʊ_custom"}
        t = Transcriber(custom_exceptions=custom)
        
        combined = t.get_dict()
        assert combined["hello"] == "hɛˈloʊ_custom"

    def test_add_exception(self):
        t = Transcriber()
        t.add_exception("newword", "njuːwɝːd")
        assert t._custom_exceptions["newword"] == "njuːwɝːd"
        assert "custom=1" in repr(t)

    def test_add_exceptions(self):
        t = Transcriber()
        t.add_exceptions({"word1": "w1", "word2": "w2"})
        assert len(t._custom_exceptions) == 2

    def test_remove_exception(self):
        t = Transcriber(custom_exceptions={"word": "w"})
        t.remove_exception("word")
        assert "word" not in t._custom_exceptions

    def test_clear_custom_exceptions(self):
        t = Transcriber(custom_exceptions={"w1": "1", "w2": "2"})
        t.clear_custom_exceptions()
        assert len(t._custom_exceptions) == 0

    def test_temporary_exceptions_in_transcribe(self):
        """Временные исключения дополняют объект-уровневые."""
        t = Transcriber(custom_exceptions={"word1": "w1"})
        
        # Временное исключение для одного вызова
        result = t.transcribe("word2", custom_exceptions={"word2": "w2"})
        assert isinstance(result, str)
        
        # Временное не сохраняется в объекте
        assert "word2" not in t._custom_exceptions

    def test_get_custom_exceptions(self):
        custom = {"word": "w"}
        t = Transcriber(custom_exceptions=custom)
        returned = t.get_custom_exceptions()
        assert returned == custom
        # Возвращается копия, а не ссылка
        returned["new"] = "n"
        assert "new" not in t._custom_exceptions


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
        assert any("\u0400" <= ch <= "\u04FF" for ch in result)

    def test_preserves_punctuation(self):
        t = Transcriber()
        result = t.transcribe("hello, world!")
        assert "," in result
        assert "!" in result


class TestEdgeCases:
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