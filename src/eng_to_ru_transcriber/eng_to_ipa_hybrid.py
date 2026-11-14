"""Гибридный движок транскрипции: словарь исключений + rule_based_ipa."""
from __future__ import annotations
import re
from functools import lru_cache
from . import rule_based_ipa

_WORD_PATTERN = re.compile(r"^[a-zA-Z']+$")
_TOKEN_PATTERN = re.compile(r"[a-zA-Z']+|[^a-zA-Z']+")

# Регулярки для умного разбиения и нормализации регистра
_CAMEL_BOUNDARY = re.compile(r'(?<=[a-z])(?=[A-Z])')
_ABBR_WORD_BOUNDARY = re.compile(r'(?<=[A-Z])(?=[A-Z][a-z])')
_UPPER_SEQUENCE = re.compile(r'(?<=[A-Z])(?=[A-Z])')
_WORD_START = re.compile(r'([A-Z])(?=[a-z])')

MAX_DICT_WORD_LEN = 12 # Увеличил, чтобы ловить длинные слова вроде "dockerization"

# ─────────────────────────── Токенизация ───────────────────────────

def smart_lower(text: str) -> str:
    text = _CAMEL_BOUNDARY.sub('-', text)
    text = _ABBR_WORD_BOUNDARY.sub('-', text)
    text = _UPPER_SEQUENCE.sub('-', text)
    text = _WORD_START.sub(lambda m: m.group(1).lower(), text)
    return text

def _tokenize(text: str) -> list[str]:
    return _TOKEN_PATTERN.findall(text)

def _is_word_token(token: str) -> bool:
    return bool(_WORD_PATTERN.match(token))

def _is_abbreviation(token: str) -> bool:
    return len(token) >= 2 and token.isupper()

# ─────────────────────────── Разбиение ───────────────────────────

def _split_word_from_start(
    word: str,
    word_lower: str,
    long_keys: frozenset[str],
) -> list[tuple[str, bool]]:
    """Ищет самый длинный словарный префикс. Всё остальное — одним куском в правила."""
    if not long_keys:
        return [(word, False)]

    n = len(word)
    max_len = min(n, MAX_DICT_WORD_LEN)

    # Ищем самый длинный ключ, с которого начинается слово
    for length in range(max_len, 3, -1):  # Длина от 4 и выше
        candidate = word_lower[:length]
        if candidate in long_keys:
            # Нашли словарное слово в начале!
            # Возвращаем его + весь остаток строки как "неизвестную" часть
            return [
                (word[:length], True),
                (word[length:], False)
            ]

    # Если ни одно словарное слово не подошло с начала — всё слово в правила
    return [(word, False)]


@lru_cache(maxsize=10000)
def _split_word_cached(
    word: str,
    word_lower: str,
    long_keys: frozenset[str],
) -> tuple[tuple[str, bool], ...]:
    return tuple(_split_word_from_start(word, word_lower, long_keys))


# ─────────────────────────── Шаг 1: Разбиение токенов на сегменты ───────────────────────────

def _build_word_segments(
    tokens: list[str],
    custom_exceptions: dict[str, str],
    long_keys: frozenset[str],
) -> dict[str, list[tuple[str, bool]]]:
    """Разбивает каждый токен на сегменты (словарные и нет)."""
    word_segments: dict[str, list[tuple[str, bool]]] = {}

    for token in tokens:
        if not _is_word_token(token):
            continue

        word_lower = token.lower()
        if word_lower in word_segments:
            continue

        # Сокращения не разбиваем
        if _is_abbreviation(token):
            word_segments[word_lower] = [(token, False)]
            continue

        # Слова из словаря исключений (целиком)
        if word_lower in custom_exceptions:
            word_segments[word_lower] = [(token, True)]
            continue

        # Разбиваем по словарному префиксу
        segments = list(_split_word_cached(token, word_lower, long_keys))
        word_segments[word_lower] = segments

    return word_segments


# ─────────────────────────── Шаг 2: Сбор неизвестных слов ───────────────────────────

def _collect_unknown_words(
    word_segments: dict[str, list[tuple[str, bool]]],
) -> list[str]:
    """Собирает уникальные сегменты, которых нет в словаре."""
    unknown: list[str] = []
    seen: set[str] = set()

    for segments in word_segments.values():
        for seg_text, is_dict in segments:
            if not is_dict and seg_text not in seen:
                unknown.append(seg_text)
                seen.add(seg_text)

    return unknown


# ─────────────────────────── Шаг 3: Транскрипция неизвестных слов ───────────────────────────

def _bulk_transcribe(
    words: list[str],
    transcription_rules: list[tuple[str, str]],
) -> dict[str, str]:
    if not words:
        return {}

    rules_tuple = tuple(transcription_rules)
    mapping: dict[str, str] = {}
    for word in words:
        if word not in mapping:
            mapping[word] = rule_based_ipa.transcribe(word, rules_tuple)
    return mapping


# ─────────────────────────── Шаг 4: Сборка результата ───────────────────────────

def _build_final_tokens(
    tokens: list[str],
    word_segments: dict[str, list[tuple[str, bool]]],
    custom_exceptions: dict[str, str],
    english_mapping: dict[str, str]
) -> list[str]:
    """Собирает финальные токены: слова → IPA, остальное как есть."""
    final_tokens: list[str] = []

    for token in tokens:
        if not _is_word_token(token):
            final_tokens.append(token)
            continue

        word_lower = token.lower()
        segments = word_segments[word_lower]
        ipa_parts: list[str] = []

        for seg_text, is_dict in segments:
            if is_dict:
                ipa_parts.append(custom_exceptions[seg_text.lower()])
            else:
                ipa_parts.append(english_mapping.get(seg_text, seg_text))

        ipa_word = "".join(ipa_parts)
        final_tokens.append(ipa_word)

    return final_tokens


# ─────────────────────────── Главная функция ───────────────────────────

def transcribe(
    text: str,
    custom_exceptions: dict[str, str],
    long_keys: frozenset[str] | None,
    transcription_rules: list[tuple[str, str]]
) -> str:
    if not text:
        return ""

    text = smart_lower(text)
    tokens = _tokenize(text)
    if not tokens:
        return ""

    # Fallback для тестов и обратной совместимости
    if long_keys is None:
        long_keys = frozenset(k for k in custom_exceptions if len(k) >= 4)

    # Шаг 1: Разбиваем токены на сегменты
    word_segments = _build_word_segments(tokens, custom_exceptions, long_keys)

    # Шаг 2: Собираем неизвестные слова
    unknown_words = _collect_unknown_words(word_segments)

    # Шаг 3: Транскрибируем неизвестные слова
    english_mapping = _bulk_transcribe(unknown_words, transcription_rules)

    # Шаг 4: Собираем результат
    final_tokens = _build_final_tokens(
        tokens, word_segments, custom_exceptions,
        english_mapping
    )

    return "".join(final_tokens).strip()


def clear_split_cache() -> None:
    _split_word_cached.cache_clear()
    rule_based_ipa.clear_cache()
