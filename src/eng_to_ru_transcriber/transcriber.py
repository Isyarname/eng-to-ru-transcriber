"""Класс-оркестратор транслитерации."""
from __future__ import annotations
import pickle
from importlib import resources
from pathlib import Path
from . import eng_to_ipa_hybrid, ipa_to_ru

_PACKAGE_DATA = resources.files("eng_to_ru_transcriber.data")

# Пути по умолчанию к скомпилированным данным внутри пакета
_DEFAULT_TRANSLIT_RULES_PATH = Path(str(_PACKAGE_DATA.joinpath("transliteration_rules.pkl")))
_DEFAULT_ENG_TO_IPA_RULES_PATH = Path(str(_PACKAGE_DATA.joinpath("eng_to_ipa_rules.pkl")))
_DEFAULT_EN_DICT_PATH = Path(str(_PACKAGE_DATA.joinpath("en_dict.pkl")))
_DEFAULT_NORMALIZATIONS_PATH = Path(str(_PACKAGE_DATA.joinpath("phonetic_normalizations.pkl")))


class Transcriber:
    """
    Оркестратор транслитерации английского текста в кириллицу.
    Все ресурсы загружаются в конструкторе.
    Пользовательский словарь дополняет встроенный, а не заменяет его.
    """

    def __init__(
        self,
        translit_rules_path: Path | None = None,
        eng_to_ipa_rules_path: Path | None = None,
        en_dict_path: Path | None = None,
        normalizations_path: Path | None = None,
        custom_vocabulary: dict[str, str] | None = None,
    ) -> None:
        """
        Args:
            translit_rules_path: Путь к скомпилированным правилам IPA → RU.
            eng_to_ipa_rules_path: Путь к скомпилированным правилам EN → IPA.
            en_dict_path: Путь к словарю исключений.
            normalizations_path: Путь к фонетическим нормализациям.
            custom_vocabulary: Пользовательский словарь (дополняет встроенный).
        """
        # --- Пути к файлам ---
        self._translit_rules_path = translit_rules_path or _DEFAULT_TRANSLIT_RULES_PATH
        self._eng_to_ipa_rules_path = eng_to_ipa_rules_path or _DEFAULT_ENG_TO_IPA_RULES_PATH
        self._en_dict_path = en_dict_path or _DEFAULT_EN_DICT_PATH
        self._normalizations_path = normalizations_path or _DEFAULT_NORMALIZATIONS_PATH

        # --- Пользовательский словарь ---
        self._custom_vocabulary = dict(custom_vocabulary) if custom_vocabulary else {}

        # --- Загрузка ресурсов ---
        self._transliteration_rules = self._load_pickle(self._translit_rules_path)
        self._eng_to_ipa_rules = self._load_pickle(self._eng_to_ipa_rules_path)
        self._en_dict = self._load_pickle(self._en_dict_path)
        self._substring_norms, self._word_norms = self._load_pickle(self._normalizations_path)

        # --- Объединённый словарь (собирается один раз) ---
        if self._custom_vocabulary:
            self._merged_vocabulary = {**self._en_dict, **self._custom_vocabulary}
        else:
            self._merged_vocabulary = self._en_dict

        # --- Ключи длиной ≥ 4 для разбиения незнакомых слов ---
        self._long_keys = frozenset(
            k for k in self._merged_vocabulary if len(k) >= 4
        )

    # ─────────────────────────── Публичный API ───────────────────────────

    def transcribe(self, text: str) -> str:
        """Транслитерирует английский текст в кириллицу."""
        ipa_text = eng_to_ipa_hybrid.transcribe(
            text,
            self._merged_vocabulary,
            self._long_keys,
            self._eng_to_ipa_rules,
            self._substring_norms,
            self._word_norms,
        )
        return ipa_to_ru.convert(ipa_text, self._transliteration_rules)

    # ─────────────────────────── Доступ к ресурсам ───────────────────────

    def get_transliteration_rules(self) -> list[tuple[str, str]]:
        """Возвращает скомпилированные правила IPA → кириллица."""
        return self._transliteration_rules

    def get_eng_to_ipa_rules(self) -> list[tuple[str, str]]:
        """Возвращает скомпилированные правила English → IPA."""
        return self._eng_to_ipa_rules

    # ─────────────────────────── Внутренние методы ───────────────────────

    @staticmethod
    def _load_pickle(path: Path):
        if not path.exists():
            raise FileNotFoundError(f"Файл не найден: {path}")
        with open(path, "rb") as f:
            return pickle.load(f)

    # ─────────────────────────── Магические методы ────────────────────────

    def __repr__(self) -> str:
        return (
            f"Transcriber("
            f"translit_rules={len(self._transliteration_rules)}, "
            f"eng_to_ipa_rules={len(self._eng_to_ipa_rules)}, "
            f"dict={len(self._merged_vocabulary)})"
        )
