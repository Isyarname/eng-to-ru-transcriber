"""Модуль транскрипции английского текста в IPA с помощью rule_engine."""
from __future__ import annotations
from functools import lru_cache
from . import rule_engine


@lru_cache(maxsize=10000)
def _transcribe_cached(text: str, rules_tuple: tuple) -> str:
    """Внутренняя функция. Принимает кортеж правил (он хэшируемый)."""
    return rule_engine.process_text(text, rules_tuple)


def transcribe(text: str, transcription_rules: list[tuple[str, str]] | tuple) -> str:
    """Применяет правила транскрипции к тексту (с кэшированием результатов)."""
    # tuple(list) создаёт хэшируемый кортеж. Если уже кортеж — возвращает его же (мгновенно).
    return _transcribe_cached(text, tuple(transcription_rules))


def clear_cache() -> None:
    """Очищает кэш транскрипции."""
    _transcribe_cached.cache_clear()
