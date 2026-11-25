"""Класс-оркестратор транскрипции."""
from __future__ import annotations

from crispy_ipa import Transcriber as IPATranscriber

from . import default_adaptation_rules
from . import rule_engine
from .dsl_compiler import build_rules

# Компилируется один раз при импорте модуля.
_ADAPTATION_RULES: tuple = tuple(
    build_rules(default_adaptation_rules.rules, default_adaptation_rules.macros)
)


class Transcriber:
    """
    Оркестратор транскрипции английского текста в кириллицу.

    Пользовательский словарь дополняет встроенный словарь crispy-ipa,
    а не заменяет его.
    """

    def __init__(self, custom_vocabulary: dict[str, str] | None = None) -> None:
        self._ipa_transcriber = IPATranscriber(custom_vocabulary=custom_vocabulary)

    def transcribe(self, text: str) -> str:
        """Транскрибирует английский текст в кириллицу."""
        ipa_text = self._ipa_transcriber.transcribe(text)
        return rule_engine.apply_rules(ipa_text, _ADAPTATION_RULES)

    def __repr__(self) -> str:
        return (
            f"Transcriber("
            f"adaptation_rules={len(_ADAPTATION_RULES)}, "
            f"ipa={self._ipa_transcriber!r})"
        )
