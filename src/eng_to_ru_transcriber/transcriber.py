"""Класс-оркестратор транслитерации."""
from __future__ import annotations

import pickle
from importlib import resources
from pathlib import Path
from crispy_ipa import Transcriber as IPATranscriber
from . import rule_engine

_PACKAGE_DATA = resources.files("eng_to_ru_transcriber.data")
_TRANSLIT_RULES_PATH = Path(str(_PACKAGE_DATA.joinpath("ipa_to_ru_adaptation.pkl")))


class Transcriber:
    """
    Оркестратор транслитерации английского текста в кириллицу.
    Все ресурсы загружаются в конструкторе.
    Пользовательский словарь дополняет встроенный словарь crispy-ipa, а не заменяет его.
    """

    def __init__(
        self,
        custom_vocabulary: dict[str, str] | None = None,
    ) -> None:
        self._ipa_transcriber = IPATranscriber(custom_vocabulary=custom_vocabulary)
        self._ipa_to_ru_adaptation = self._load_pickle(_TRANSLIT_RULES_PATH)

    def transcribe(self, text: str) -> str:
        """Транслитерирует английский текст в кириллицу."""
        ipa_text = self._ipa_transcriber.transcribe(text)
        return rule_engine.process_text(ipa_text, self._ipa_to_ru_adaptation)

    @staticmethod
    def _load_pickle(path: Path):
        if not path.exists():
            raise FileNotFoundError(f"Файл не найден: {path}")
        with open(path, "rb") as f:
            return pickle.load(f)

    def __repr__(self) -> str:
        return (
            f"Transcriber("
            f"translit_rules={len(self._ipa_to_ru_adaptation)}, "
            f"ipa={self._ipa_transcriber!r})"
        )
