"""Класс-оркестратор транскрипции."""
from __future__ import annotations

import pickle
from importlib import resources
from crispy_ipa import Transcriber as IPATranscriber
from . import rule_engine

_PACKAGE_DATA = resources.files("eng_to_ru_transcriber.data")


class Transcriber:
    """
    Оркестратор транскрипции английского текста в кириллицу.
    Все ресурсы загружаются в конструкторе.
    Пользовательский словарь дополняет встроенный словарь crispy-ipa, а не заменяет его.
    """

    def __init__(self, custom_vocabulary: dict[str, str] | None = None) -> None:
        self._ipa_transcriber = IPATranscriber(custom_vocabulary=custom_vocabulary)
        rules_resource = _PACKAGE_DATA.joinpath("default_adaptation.pkl")
        self._adaptation_rules = self._load_pickle(rules_resource)

    def transcribe(self, text: str) -> str:
        """Транскрибирует английский текст в кириллицу."""
        ipa_text = self._ipa_transcriber.transcribe(text)
        return rule_engine.apply_rules(ipa_text, self._adaptation_rules)

    @staticmethod
    def _load_pickle(resource):
        if not resource.is_file():
            raise FileNotFoundError(f"Файл не найден: {resource}")
        with resource.open("rb") as f:
            return pickle.load(f)

    def __repr__(self) -> str:
        return (
            f"Transcriber("
            f"adaptation_rules={len(self._adaptation_rules)}, "
            f"ipa={self._ipa_transcriber!r})"
        )
