"""Unit-тесты для compiler.py."""
import pytest

from eng_to_ru_transcriber.compiler import (
    parse,
    expand_macros,
    replace_brackets,
    expand,
    is_capitalizable_letter,
    add_capitalized_pairs,
    compile_rules,
)


class TestParse:
    """Парсинг сырой строки правил."""

    def test_empty_string(self):
        assert parse("") == []

    def test_non_string_input(self):
        assert parse(None) == []
        assert parse(123) == []

    def test_simple_rule(self):
        result = parse("a -> b")
        assert result == [("a", "b")]

    def test_multiple_rules(self):
        rules_str = "a -> b\nc -> d"
        result = parse(rules_str)
        assert result == [("a", "b"), ("c", "d")]

    def test_extra_whitespace(self):
        result = parse("  a   ->   b  ")
        assert result == [("a", "b")]

    def test_skips_empty_lines(self):
        result = parse("a -> b\n\n\nc -> d\n")
        assert result == [("a", "b"), ("c", "d")]

    def test_custom_transition_symbol(self):
        result = parse("a => b", transition_symbol="=>")
        assert result == [("a", "b")]


class TestExpandMacros:
    """Разворачивание макросов."""

    def test_string_macro(self):
        result = expand_macros(("X", "Y"), {"X": "hello"})
        # ✅ expand_macros возвращает list, а не tuple
        assert result == ["hello", "Y"]

    def test_set_macro(self):
        result = expand_macros(("X", "Y"), {"X": {"a", "b"}})
        assert result[0] in ("[ab]", "[ba]")

    def test_multiple_macros(self):
        result = expand_macros(("AB", "CD"), {"A": "x", "B": "y"})
        # ✅ list, а не tuple
        assert result == ["xy", "CD"]


class TestReplaceBrackets:
    """Замена [abc] на (a|b|c)."""

    def test_simple(self):
        assert replace_brackets("[abc]") == "(a|b|c)"

    def test_no_brackets(self):
        assert replace_brackets("abc") == "abc"

    def test_multiple(self):
        assert replace_brackets("[ab]x[cd]") == "(a|b)x(c|d)"


class TestExpand:
    """Разворачивание скобочных групп."""

    def test_no_groups(self):
        result = expand(("abc", "xyz"))
        assert result == [("abc", "xyz")]

    def test_single_group(self):
        result = expand(("(a|b)", "(x|y)"))
        assert set(result) == {("a", "x"), ("b", "y")}

    def test_broadcast_single_option(self):
        # Если в правой части одна опция, она дублируется
        result = expand(("(a|b|c)", "x"))
        assert set(result) == {("a", "x"), ("b", "x"), ("c", "x")}

    def test_mismatched_groups_raises(self):
        with pytest.raises(ValueError):
            expand(("(a|b|c)", "(x|y)"))


class TestIsCapitalizableLetter:
    """Проверка заглавливаемости букв."""

    def test_regular_lowercase(self):
        assert is_capitalizable_letter("a") is True
        assert is_capitalizable_letter("z") is True

    def test_uppercase(self):
        assert is_capitalizable_letter("A") is False

    def test_ipa_symbols(self):
        # IPA-символы из расширений Unicode
        assert is_capitalizable_letter("ɑ") is False  # U+0251
        assert is_capitalizable_letter("ɪ") is False  # U+026A

    def test_non_alpha(self):
        assert is_capitalizable_letter("1") is False
        assert is_capitalizable_letter(" ") is False


class TestAddCapitalizedPairs:
    """Добавление пар для заглавных букв."""

    def test_adds_capitalized(self):
        pairs = [("abc", "xyz")]
        result = add_capitalized_pairs(pairs)
        assert ("Abc", "Xyz") in result
        assert ("abc", "xyz") in result

    def test_skips_non_capitalizable(self):
        # Начинается с IPA-символа
        pairs = [("ɑbc", "xyz")]
        result = add_capitalized_pairs(pairs)
        assert len(result) == 1
        assert result[0] == ("ɑbc", "xyz")


class TestCompileRules:
    """Интеграционный тест полной компиляции."""

    def test_full_pipeline(self):
        rules_str = "a -> x\nb -> y"
        result = compile_rules(rules_str, macros={}, add_capitalized=False)
        assert result == [("a", "x"), ("b", "y")]

    def test_with_macros(self):
        rules_str = "V -> а"
        macros = {"V": {"a", "e"}}
        result = compile_rules(rules_str, macros, add_capitalized=False)
        # Должно развернуться в две строки
        assert len(result) == 2

    def test_with_capitalized(self):
        rules_str = "a -> x"
        result = compile_rules(rules_str, macros={}, add_capitalized=True)
        assert ("A", "X") in result
        assert ("a", "x") in result