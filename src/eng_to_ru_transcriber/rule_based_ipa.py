"""Модуль транскрипции английского текста в IPA с помощью rule_engine."""
from __future__ import annotations
from . import rule_engine


def transcribe(text: str, transcription_rules: list[tuple[str, str]]) -> str:
    """Применяет правила транскрипции к переданному тексту."""
    return rule_engine.process_text(text, transcription_rules)
