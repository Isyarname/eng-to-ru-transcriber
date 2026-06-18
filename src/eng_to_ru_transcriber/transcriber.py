"""Класс-оркестратор транслитерации."""
from __future__ import annotations

import json
from importlib import resources
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
from typing import Iterable

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
    Пользовательские исключения дополняют встроенный словарь, а не заменяют его.

    Пример:
        >>> t = Transcriber(custom_exceptions={"python": "ˈpaɪθɑn"})
        >>> t.transcribe("Python is great")
        'ˈpaɪθɑn из грэйт'
    """

    def __init__(
        self,
        rules_path: Path | None = None,
        dict_path: Path | None = None,
        cache_dir: Path | None = None,
        custom_exceptions: dict[str, str] | None = None,
    ) -> None:
        self._rules_path = rules_path or _default_rules_path()
        self._dict_path = dict_path or _default_dict_path()
        self._cache_dir = cache_dir or _default_cache_dir()
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        # Лениво загружаемые ресурсы
        self._compiled_rules: list[tuple[str, str]] | None = None
        self._dict_cache: dict[str, str] | None = None

        # Пользовательские исключения (дополняют встроенный словарь)
        self._custom_exceptions: dict[str, str] = dict(custom_exceptions) if custom_exceptions else {}

    # ─────────────────────────── Публичный API ───────────────────────────

    def transcribe(
        self,
        text: str,
        custom_exceptions: dict[str, str] | None = None,
    ) -> str:
        """
        Транслитерирует английский текст в кириллицу.

        Args:
            text: Входной английский текст.
            custom_exceptions: Временные исключения (дополняют объект-уровневые).

        Returns:
            Текст кириллицей.
        """
        compiled_rules = self.get_compiled_rules()
        exceptions = self._merge_exceptions(custom_exceptions)

        ipa_text = eng_to_ipa_hybrid.transcribe(text, exceptions)
        return ipa_to_ru.convert(ipa_text, compiled_rules)

    def transcribe_many(
        self,
        texts: Iterable[str],
        custom_exceptions: dict[str, str] | None = None,
    ) -> list[str]:
        """Транслитерирует несколько текстов."""
        return [self.transcribe(t, custom_exceptions) for t in texts]

    # ─────────────────────────── Доступ к ресурсам ───────────────────────

    def get_compiled_rules(self) -> list[tuple[str, str]]:
        """Возвращает скомпилированные правила."""
        if self._compiled_rules is None:
            self._compiled_rules = self._load_compiled_rules()
        return self._compiled_rules

    def get_dict(self) -> dict[str, str]:
        """
        Возвращает объединённый словарь: встроенный + пользовательские исключения.
        Пользовательские имеют приоритет при конфликте ключей.
        """
        if self._dict_cache is None:
            self._dict_cache = self._parse_ipa_dictionary(self._dict_path)
        
        # Объединяем: встроенный + пользовательские (пользовательские перезаписывают)
        return {**self._dict_cache, **self._custom_exceptions}

    def get_custom_exceptions(self) -> dict[str, str]:
        """Возвращает только пользовательские исключения."""
        return self._custom_exceptions.copy()

    # ─────────────────────────── Управление исключениями ─────────────────

    def add_exception(self, word: str, ipa: str) -> None:
        """Добавляет одно пользовательское исключение."""
        self._custom_exceptions[word.lower()] = ipa

    def add_exceptions(self, exceptions: dict[str, str]) -> None:
        """Добавляет несколько пользовательских исключений."""
        self._custom_exceptions.update({k.lower(): v for k, v in exceptions.items()})

    def remove_exception(self, word: str) -> None:
        """Удаляет пользовательское исключение."""
        self._custom_exceptions.pop(word.lower(), None)

    def clear_custom_exceptions(self) -> None:
        """Удаляет все пользовательские исключения."""
        self._custom_exceptions.clear()

    # ─────────────────────────── Управление состоянием ───────────────────

    def reload_dictionary(self) -> None:
        """Перечитывает встроенный словарь с диска."""
        self._dict_cache = self._parse_ipa_dictionary(self._dict_path)

    def reload_transliteration(self) -> None:
        """Перекомпилирует правила транслитерации IPA → кириллица."""
        self._compiled_rules = self._compile_rules_from_source()

    def reload_all(self) -> None:
        """Перезагружает всё: и словарь, и правила транслитерации."""
        self.reload_dictionary()
        self.reload_transliteration()

    def clear_cache(self) -> None:
        """Удаляет JSON-кэш compiled_rules.json."""
        cache_file = self._cache_dir / "compiled_rules.json"
        if cache_file.exists():
            cache_file.unlink()
        self._compiled_rules = None

    # ─────────────────────────── Внутренние методы ───────────────────────

    def _merge_exceptions(
        self,
        temporary: dict[str, str] | None = None,
    ) -> dict[str, str]:
        """
        Объединяет все уровни исключений:
        1. Встроенный словарь (en_dict.txt)
        2. Пользовательские исключения объекта
        3. Временные исключения вызова (если переданы)
        """
        base = self.get_dict()
        if temporary:
            return {**base, **{k.lower(): v for k, v in temporary.items()}}
        return base

    def _load_compiled_rules(self) -> list[tuple[str, str]]:
        """Загружает правила из JSON-кэша или компилирует."""
        cache_file = self._cache_dir / "compiled_rules.json"

        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                return [tuple(pair) for pair in json.load(f)]

        return self._compile_rules_from_source()

    def _compile_rules_from_source(self) -> list[tuple[str, str]]:
        """Компилирует DSL-правила и сохраняет в JSON-кэш."""
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
        dict_status = "загружен" if self._dict_cache else "нет"
        custom_count = len(self._custom_exceptions)
        custom_info = f", custom={custom_count}" if custom_count > 0 else ""
        return (
            f"Transcriber("
            f"rules={'загружены' if self._compiled_rules else 'нет'}, "
            f"dict={dict_status}{custom_info}"
            f")"
        )