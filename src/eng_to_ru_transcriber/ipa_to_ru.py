"""Модуль транслитерации IPA-символов в кириллицу."""
from __future__ import annotations

from . import transducer


def convert(ipa_text: str, compiled_rules: list[tuple[str, str]]) -> str:
    """Передает готовый массив правил в рантайм-движок."""
    return transducer.process_text(ipa_text, compiled_rules)