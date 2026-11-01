"""Unit-тесты для rule_based_ipa.py."""
import pytest

from eng_to_ru_transcriber.rule_based_ipa import smart_lower, transcribe


class TestSmartLower:
    """Проверка умной обработки регистра."""

    def test_already_lowercase(self):
        assert smart_lower("hello world") == "hello world"

    def test_camel_case(self):
        # Заглавная буква перед строчной становится строчной
        assert smart_lower("MacBook") == "macbook"
        assert smart_lower("CamelCase") == "camelcase"

    def test_uppercase_abbreviation(self):
        # Заглавные буквы (2 и более) отделяются дефисом, но НЕ переводятся в нижний регистр
        assert smart_lower("myURL") == "my-URL"
        assert smart_lower("parseXMLData") == "parse-XMLdata"

    def test_mixed_case_and_abbreviation(self):
        # Комбинация CamelCase и аббревиатур
        assert smart_lower("MacOS") == "mac-OS"
        # Если аббревиатура в середине, а после неё CamelCase
        assert smart_lower("getHTTPResponseCode") == "get-HTTPresponsecode"

    def test_all_caps(self):
        # Строка из одних заглавных не меняется
        assert smart_lower("USA") == "USA"



class TestTranscribe:
    """Проверка транскрипции (интеграция со smart_lower и rule_engine)."""

    def test_empty_text(self):
        assert transcribe("", []) == ""

    def test_empty_rules(self):
        # Если правило не задано, применяется только smart_lower
        assert transcribe("Hello", []) == "hello"
        # Все заглавные остаются заглавными
        assert transcribe("HELLO", []) == "HELLO"

    def test_applies_smart_lower_before_rules(self):
        # Сначала срабатывает smart_lower (Hello -> hello), потом правило (hello -> xyz)
        rules = [("hello", "xyz")]
        assert transcribe("Hello", rules) == "xyz"

    def test_camel_case_with_rules(self):
        # "HelloWorld" -> smart_lower -> "helloworld" -> (правило: hello->привет, world->мир)
        rules = [("hello", "привет"), ("world", "мир")]
        # Дефиса нет, так как это был CamelCase, а не аббревиатура
        assert transcribe("HelloWorld", rules) == "приветмир"

    def test_abbreviation_with_rules(self):
        # "myURL" -> smart_lower -> "my-URL". Затем правила могут обрабатывать отдельно.
        rules = [("my", "май"), ("URL", "урл")]
        assert transcribe("myURL", rules) == "май-урл"

    def test_transcribe_with_regex(self):
        # Проверка, что регулярки в правилах тоже работают
        rules = [("[aeiou]", "*")]
        # "Cat" -> smart_lower -> "cat" -> правило -> "c*t"
        assert transcribe("Cat", rules) == "c*t"
