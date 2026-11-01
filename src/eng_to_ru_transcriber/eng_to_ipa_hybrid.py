"""Гибридный движок транскрипции: словарь исключений + rule_based_ipa."""
from __future__ import annotations
import re
from . import rule_based_ipa
from .data.phonetic_normalizations import (
    SUBSTRING_NORMALIZATIONS,
    WORD_NORMALIZATIONS,
)

_WORD_PATTERN = re.compile(r"^[a-zA-Z']+$")
_TOKEN_PATTERN = re.compile(r"[a-zA-Z']+|[^a-zA-Z']+")

# Суффиксы, отделяемые от корня (отсортированы по убыванию длины)
_SUFFIXES = sorted({
    "ment", "ness", "tion", "sion", "able", "ible",
    "ful", "less", "ous", "ive",
    "ing", "ed", "ly", "er", "or", "est",
    "es", "s",
}, key=len, reverse=True)

# Ограничение длины поиска в словаре
MAX_DICT_WORD_LEN = 8

# Кэш разбиений
_SPLIT_CACHE: dict[str, list[tuple[str, bool]]] = {}


def _tokenize(text: str) -> list[str]:
    return _TOKEN_PATTERN.findall(text)


def _find_suffix(word_lower: str) -> tuple[int, str] | None:
    """Ищет самый длинный подходящий суффикс."""
    for suffix in _SUFFIXES:
        if word_lower.endswith(suffix) and len(word_lower) > len(suffix):
            return (len(word_lower) - len(suffix), suffix)
    return None


def _split_word_from_end(
    word: str,
    word_lower: str,
    boundary: int,
    long_keys: set[str],
) -> list[tuple[str, bool]]:
    """Жадно разбивает часть слова до boundary справа налево."""
    if not long_keys:
        return [(word[:boundary], False)]

    segments: list[tuple[str, bool]] = []
    pos = boundary

    while pos > 0:
        best_match = None
        max_len = min(pos, MAX_DICT_WORD_LEN)
        for length in range(max_len, 3, -1):
            start = pos - length
            candidate = word_lower[start:pos]
            if candidate in long_keys:
                best_match = (start, pos)
                break

        if best_match:
            start, end = best_match
            segments.append((word[start:end], True))
            pos = start
        else:
            pos -= 1
            if segments and not segments[-1][1]:
                segments[-1] = (word[pos] + segments[-1][0], False)
            else:
                segments.append((word[pos], False))

    segments.reverse()
    return segments


def _bulk_transcribe(
    words: list[str],
    transcription_rules: list[tuple[str, str]],
) -> dict[str, str]:
    """Пакетная транскрипция только английских сегментов."""
    if not words:
        return {}

    mapping: dict[str, str] = {}
    for word in words:
        if word not in mapping:
            mapping[word] = rule_based_ipa.transcribe(word, transcription_rules)
    return mapping


def _normalize_ipa_word(ipa_word: str) -> str:
    if ipa_word in WORD_NORMALIZATIONS:
        return WORD_NORMALIZATIONS[ipa_word]
    for old, new in SUBSTRING_NORMALIZATIONS:
        ipa_word = ipa_word.replace(old, new)
    return ipa_word


def transcribe(
    text: str,
    custom_exceptions: dict[str, str],
    transcription_rules: list[tuple[str, str]] | None = None,
) -> str:
    """
    Гибридная транскрипция English → IPA.
    Ключевое изменение: готовые IPA-части НЕ отправляются в rule_based_ipa повторно.
    Транскрибируются только английские сегменты, затем всё склеивается.
    """
    if not text:
        return ""
    if transcription_rules is None:
        transcription_rules = []
    tokens = _tokenize(text)
    if not tokens:
        return ""

    long_keys = {k for k in custom_exceptions if len(k) >= 4}

    # word_lower -> список сегментов (текст, is_dict)
    word_segments: dict[str, list[tuple[str, bool]]] = {}

    # 1. Разбираем все слова на сегменты
    for token in tokens:
        if not _WORD_PATTERN.match(token):
            continue

        word_lower = token.lower()
        if word_lower in word_segments:
            continue

        # Проверка целиком
        if word_lower in custom_exceptions:
            word_segments[word_lower] = [(token, True)]
            continue

        # Кэш разбиений
        if word_lower in _SPLIT_CACHE:
            segments = _SPLIT_CACHE[word_lower]
        else:
            suffix_result = _find_suffix(word_lower)
            if suffix_result:
                boundary, suffix = suffix_result
                segments = _split_word_from_end(token, word_lower, boundary, long_keys)
                segments.append((suffix, False))
            else:
                segments = _split_word_from_end(token, word_lower, len(word_lower), long_keys)
            _SPLIT_CACHE[word_lower] = segments

        word_segments[word_lower] = segments

    # 2. Собираем только АНГЛИЙСКИЕ сегменты для rule_based_ipa
    english_to_transcribe: list[str] = []
    seen_english: set[str] = set()

    for segments in word_segments.values():
        for seg_text, is_dict in segments:
            if not is_dict:
                seg_lower = seg_text.lower()
                if seg_lower not in seen_english:
                    english_to_transcribe.append(seg_text)  # оригинальный регистр
                    seen_english.add(seg_lower)

    # 3. Транскрибируем только английские части
    english_mapping = _bulk_transcribe(english_to_transcribe, transcription_rules)

    # 4. Собираем итоговый IPA — склеиваем готовые IPA + транскрибированные английские части
    final_tokens: list[str] = []
    for token in tokens:
        if _WORD_PATTERN.match(token):
            word_lower = token.lower()
            segments = word_segments[word_lower]
            ipa_parts: list[str] = []

            for seg_text, is_dict in segments:
                if is_dict:
                    # Словарная часть — берём готовый IPA
                    ipa_parts.append(custom_exceptions[seg_text.lower()])
                else:
                    # Английская часть — берём из транскрибированных
                    ipa = english_mapping.get(seg_text, seg_text)
                    ipa_parts.append(ipa)

            final_tokens.append(_normalize_ipa_word("".join(ipa_parts)))
        else:
            final_tokens.append(token)

    return "".join(final_tokens).strip()


def clear_split_cache() -> None:
    """Очищает кэш разбиений."""
    _SPLIT_CACHE.clear()
