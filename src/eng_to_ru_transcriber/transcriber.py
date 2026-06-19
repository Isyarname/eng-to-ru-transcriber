"""Класс-оркестратор транслитерации."""
from __future__ import annotations

import json
from importlib import resources
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

from platformdirs import user_cache_dir

from . import compiler, ipa_to_ru, eng_to_ipa_hybrid


_PACKAGE_DATA = resources.files("eng_to_ru_transcriber.data")


def _default_cache_dir() -> Path:
    return Path(user_cache_dir("eng_to_ru_transcriber", appauthor=False))


def _default_rules_path() -> Path:
    return Path(str(_PACKAGE_DATA.joinpath("transliteration_rules.py")))


def _default_dict_path() -> Path:
    return Path(str(_PACKAGE_DATA.joinpath("en_dict.txt")))


class Transcriber:
    """
    Оркестратор транслитерации английского текста в кириллицу.

    Лениво загружает ресурсы при первом вызове и кэширует их в памяти.
    Пользовательский словарь дополняет встроенный, а не заменяет его.

    Пример:
        >>> t = Transcriber()
        >>> t.transcribe("Hello world")
        'Хэлоу уорлд'
    """

    def __init__(
        self,
        rules_path: Path | None = None,
        dict_path: Path | None = None,
        cache_dir: Path | None = None,
        custom_vocabulary: dict[str, str] | None = None,
    ) -> None:
        """
        Args:
            rules_path: Путь к правилам транслитерации. По умолчанию — ресурс пакета.
            dict_path: Путь к словарю исключений. По умолчанию — ресурс пакета.
            cache_dir: Папка для кэша compiled_rules.json. По умолчанию — user_cache_dir.
            custom_vocabulary: Пользовательский словарь (дополняет встроенный).
        """
        self._rules_path = rules_path or _default_rules_path()
        self._dict_path = dict_path or _default_dict_path()
        self._cache_dir = cache_dir or _default_cache_dir()
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        # Лениво загружаемые ресурсы
        self._compiled_rules: list[tuple[str, str]] | None = None
        self._dict_cache: dict[str, str] | None = None

        # Пользовательский словарь (задаётся один раз при создании)
        self._custom_vocabulary: dict[str, str] = dict(custom_vocabulary) if custom_vocabulary else {}

    # ─────────────────────────── Публичный API ───────────────────────────

    def transcribe(self, text: str) -> str:
        """
        Транслитерирует английский текст в кириллицу.

        Args:
            text: Входной английский текст.

        Returns:
            Текст кириллицей.
        """
        compiled_rules = self.get_compiled_rules()
        vocabulary = self.get_vocabulary()

        ipa_text = eng_to_ipa_hybrid.transcribe(text, vocabulary)
        return ipa_to_ru.convert(ipa_text, compiled_rules)

    # ─────────────────────────── Доступ к ресурсам ───────────────────────

    def get_compiled_rules(self) -> list[tuple[str, str]]:
        """Возвращает скомпилированные правила (ленивая загрузка + кэш)."""
        if self._compiled_rules is None:
            self._compiled_rules = self._load_compiled_rules()
        return self._compiled_rules

    def get_vocabulary(self) -> dict[str, str]:
        """
        Возвращает объединённый словарь: встроенный + пользовательский.
        Пользовательский имеет приоритет при конфликте ключей.
        """
        if self._dict_cache is None:
            self._dict_cache = self._parse_ipa_dictionary(self._dict_path)

        return {**self._dict_cache, **self._custom_vocabulary}

    # ─────────────────────────── Управление состоянием ───────────────────

    def reload_rules(self) -> None:
        """Перекомпилирует правила транслитерации IPA → кириллица."""
        self._compiled_rules = self._compile_rules_from_source()

    def reload_dictionary(self) -> None:
        """Перечитывает встроенный словарь с диска."""
        self._dict_cache = self._parse_ipa_dictionary(self._dict_path)

    def reload_all(self) -> None:
        """Перезагружает всё: и словарь, и правила транслитерации."""
        self.reload_dictionary()
        self.reload_rules()

    def clear_cache(self) -> None:
        """Удаляет JSON-кэш compiled_rules.json с диска."""
        cache_file = self._cache_dir / "compiled_rules.json"
        if cache_file.exists():
            cache_file.unlink()
        self._compiled_rules = None

    # ─────────────────────────── Внутренние методы ───────────────────────

    def _load_compiled_rules(self) -> list[tuple[str, str]]:
        """Загружает правила из JSON-кэша или компилирует заново."""
        cache_file = self._cache_dir / "compiled_rules.json"

        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                return [tuple(pair) for pair in json.load(f)]

        return self._compile_rules_from_source()

    def _compile_rules_from_source(self) -> list[tuple[str, str]]:
        """Компилирует правила транслитерации из исходника и сохраняет в JSON-кэш."""
        if not self._rules_path.exists():
            raise FileNotFoundError(f"Файл правил не найден: {self._rules_path}")

        spec = spec_from_file_location("rules_module", str(self._rules_path))
        if spec is None or spec.loader is None:
            raise ImportError(f"Не удалось загрузить модуль: {self._rules_path}")

        module = module_from_spec(spec)
        spec.loader.exec_module(module)

        raw_macros = getattr(module, "macros", {})
        raw_rules = getattr(module, "rules", "")

        compiled = compiler.compile_rules(raw_rules, raw_macros)

        cache_file = self._cache_dir / "compiled_rules.json"
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(compiled, f, ensure_ascii=False, indent=4)

        return compiled

    @staticmethod
    def _parse_ipa_dictionary(dict_path: Path) -> dict[str, str]:
        """Парсит словарь IPA-исключений."""
        if not dict_path.exists():
            raise FileNotFoundError(f"Словарь не найден: {dict_path}")

        ipa_dict: dict[str, str] = {}
        with open(dict_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split("\t")
                if len(parts) == 2:
                    word, ipa_val = parts
                    word = word.strip()
                    ipa_val = ipa_val.strip().strip("/")
                    if "," in ipa_val:
                        ipa_val = ipa_val.split(",")[0].strip()
                    if word not in ipa_dict:
                        ipa_dict[word] = ipa_val
        return ipa_dict

    # ─────────────────────────── Магические методы ───────────────────────

    def __repr__(self) -> str:
        return (
            f"Transcriber("
            f"rules={'загружены' if self._compiled_rules else 'нет'}, "
            f"dict={'загружен' if self._dict_cache else 'нет'}"
            f")"
        )