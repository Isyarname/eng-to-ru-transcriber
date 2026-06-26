"""Модуль транслитерации IPA-символов в кириллицу."""
from __future__ import annotations

from . import rule_engine


def convert(ipa_text: str, replacement_pairs: list[tuple[str, str]]) -> str:
    """Передает готовый массив правил в рантайм-движок."""
    return rule_engine.process_text(ipa_text, replacement_pairs)