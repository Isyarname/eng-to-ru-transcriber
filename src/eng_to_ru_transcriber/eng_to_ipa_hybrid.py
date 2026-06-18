"""Гибридный движок транскрипции: словарь исключений + gruut."""
from __future__ import annotations

import re

from .data.phonetic_normalizations import (
    SUBSTRING_NORMALIZATIONS,
    WORD_NORMALIZATIONS,
)


_WORD_PATTERN = re.compile(r"^[a-zA-Z']+$")


def _tokenize(text: str) -> list[str]:
    """Разбивает текст на слова и не-слова (пробелы, пунктуация)."""
    return re.findall(r"[a-zA-Z']+|[^a-zA-Z']+", text)


def _is_word(token: str) -> bool:
    return bool(_WORD_PATTERN.match(token))


def _bulk_transcribe(words: list[str]) -> dict[str, str]:
    """
    Пакетная транскрипция неизвестных слов через gruut.

    gruut импортируется лениво — только при первом вызове,
    и только если есть слова, которых нет в словаре исключений.
    """
    if not words:
        return {}

    # Ленивый импорт — gruut грузит ML-модель (~1 сек),
    # поэтому не трогаем его, если можно обойтись словарём.
    from gruut import sentences

    bulk_text = " ".join(words)
    mapping: dict[str, str] = {}

    for sent in sentences(bulk_text, lang="en-us"):
        for word in sent:
            if word.phonemes:
                ipa_word = "".join(word.phonemes)
                mapping[word.text.lower()] = ipa_word

    return mapping


def _normalize_ipa_word(ipa_word: str) -> str:
    """
    Применяет нормализации к одному IPA-слову.

    1. Словарная проверка: если всё слово совпадает — заменяем целиком.
    2. Подстрочные замены: применяем последовательно внутри слова.
    """
    if ipa_word in WORD_NORMALIZATIONS:
        return WORD_NORMALIZATIONS[ipa_word]

    for old, new in SUBSTRING_NORMALIZATIONS:
        ipa_word = ipa_word.replace(old, new)

    return ipa_word


def transcribe(text: str, custom_exceptions: dict[str, str]) -> str:
    """
    Гибридная функция транскрипции English → IPA.

    Args:
        text: Входной английский текст.
        custom_exceptions: Словарь исключений {слово: IPA-транскрипция}.

    Returns:
        IPA-транскрипция с лингвистическими нормализациями.
    """
    if not text:
        return ""

    tokens = _tokenize(text)

    # Собираем уникальные слова, которых нет в словаре исключений
    words_to_transcribe: list[str] = []
    seen_words: set[str] = set()

    for token in tokens:
        if _is_word(token):
            word_lower = token.lower()
            if word_lower not in custom_exceptions and word_lower not in seen_words:
                words_to_transcribe.append(word_lower)
                seen_words.add(word_lower)

    # gruut вызывается только если есть неизвестные слова
    bulk_mapping = _bulk_transcribe(words_to_transcribe)

    # Сборка результата с по-словной нормализацией
    final_tokens: list[str] = []
    for token in tokens:
        if _is_word(token):
            word_lower = token.lower()

            if word_lower in custom_exceptions:
                ipa = custom_exceptions[word_lower]
            elif word_lower in bulk_mapping:
                ipa = bulk_mapping[word_lower]
            else:
                ipa = token  # Fallback

            final_tokens.append(_normalize_ipa_word(ipa))
        else:
            final_tokens.append(token)

    return "".join(final_tokens).strip()