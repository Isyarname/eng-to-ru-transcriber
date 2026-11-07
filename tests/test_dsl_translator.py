"""Unit-тесты для dsl_translator.py."""
import pytest

from dsl_translator import (
    parse,
    prepare_macros,
    expand_macros,
    replace_brackets,
    expand,
    is_capitalizable_letter,
    add_capitalized_pairs,
    build_rules,
)


class TestParse:
    def test_empty_string(self):
        assert parse("") == []

    def test_non_string_input(self):
        with pytest.raises(TypeError):
            parse(None)
        with pytest.raises(TypeError):
            parse(123)

    def test_simple_rule(self):
        assert parse("a -> b") == [("a", "b")]

    def test_multiple_rules(self):
        assert parse("a -> b\nc -> d") == [("a", "b"), ("c", "d")]

    def test_extra_whitespace(self):
        assert parse("  a   ->   b  ") == [("a", "b")]

    def test_skips_empty_lines(self):
        assert parse("a -> b\n\n\nc -> d\n") == [("a", "b"), ("c", "d")]

    def test_custom_transition_symbol(self):
        assert parse("a => b", transition_symbol="=>") == [("a", "b")]


class TestExpandMacros:
    def test_string_macro(self):
        prepared = prepare_macros({"X": "hello"})
        assert expand_macros(("X", "Y"), prepared) == ["hello", "Y"]

    def test_set_macro(self):
        prepared = prepare_macros({"X": {"a", "b"}})
        result = expand_macros(("X", "Y"), prepared)
        assert result[0] in ("[ab]", "[ba]")

    def test_multiple_macros(self):
        prepared = prepare_macros({"A": "x", "B": "y"})
        assert expand_macros(("AB", "CD"), prepared) == ["xy", "CD"]

    def test_empty_macros_returns_copy(self):
        assert expand_macros(("X", "Y"), []) == ["X", "Y"]


class TestReplaceBrackets:
    def test_simple(self):
        assert replace_brackets("[abc]") == "(a|b|c)"

    def test_no_brackets(self):
        assert replace_brackets("abc") == "abc"

    def test_multiple(self):
        assert replace_brackets("[ab]x[cd]") == "(a|b)x(c|d)"


class TestExpand:
    def test_no_groups(self):
        assert expand(("abc", "xyz")) == [("abc", "xyz")]

    def test_single_group(self):
        assert set(expand(("(a|b)", "(x|y)"))) == {("a", "x"), ("b", "y")}

    def test_broadcast_single_option(self):
        assert set(expand(("(a|b|c)", "x"))) == {("a", "x"), ("b", "x"), ("c", "x")}

    def test_mismatched_groups_raises(self):
        with pytest.raises(ValueError):
            expand(("(a|b|c)", "(x|y)"))


class TestIsCapitalizableLetter:
    def test_regular_lowercase(self):
        assert is_capitalizable_letter("a") is True
        assert is_capitalizable_letter("z") is True

    def test_uppercase(self):
        assert is_capitalizable_letter("A") is False

    def test_ipa_symbols(self):
        assert is_capitalizable_letter("ɑ") is False
        assert is_capitalizable_letter("ɪ") is False

    def test_non_alpha(self):
        assert is_capitalizable_letter("1") is False
        assert is_capitalizable_letter(" ") is False


class TestAddCapitalizedPairs:
    def test_adds_capitalized(self):
        pairs = [("abc", "xyz")]
        result = add_capitalized_pairs(pairs)
        assert ("Abc", "Xyz") in result
        assert ("abc", "xyz") in result

    def test_skips_non_capitalizable(self):
        pairs = [("ɑbc", "xyz")]
        result = add_capitalized_pairs(pairs)
        assert len(result) == 1
        assert result[0] == ("ɑbc", "xyz")


class TestBuildRules:
    """Интеграционный тест полной компиляции."""

    def test_full_pipeline(self):
        result = build_rules("a -> x\nb -> y", macros={})
        # build_rules возвращает 3-tuple (L, R, is_regex)
        assert result == [("a", "x", False), ("b", "y", False)]

    def test_with_macros(self):
        result = build_rules("V -> а", {"V": {"a", "e"}})
        assert len(result) == 2
