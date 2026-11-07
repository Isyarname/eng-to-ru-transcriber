"""Гибридный движок транскрипции: словарь исключений + rule_based_ipa."""
from __future__ import annotations
import re
from . import rule_based_ipa

_WORD_PATTERN = re.compile(r"^[a-zA-Z']+$")
_TOKEN_PATTERN = re.compile(r"[a-zA-Z']+|[^a-zA-Z']+")

_ABBR_SPLIT = re.compile(r'(?<=[a-zа-яё])(?=[A-ZА-ЯЁ]{2,})')
_CAMEL_CASE = re.compile(r'([A-ZА-ЯЁ])(?=[a-zа-яё])')

_SUFFIXES = sorted({
    "ment", "ness", "tion", "sion", "able", "ible",
    "ful", "less", "ous", "ive",
    "ing", "ed", "ly", "er", "or", "est",
    "es", "s",
}, key=len, reverse=True)

MAX_DICT_WORD_LEN = 8
_SPLIT_CACHE: dict[str, list[tuple[str, bool]]] = {}


def smart_lower(text: str) -> str:
    text = _ABBR_SPLIT.sub('-', text)
    text = _CAMEL_CASE.sub(lambda m: m.group(1).lower(), text)
    return text


def _tokenize(text: str) -> list[str]:
    return _TOKEN_PATTERN.findall(text)


def _find_suffix(word_lower: str) -> tuple[int, str] | None:
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
    if not words:
        return {}

    rules_tuple = tuple(transcription_rules)
    mapping: dict[str, str] = {}
    for word in words:
        if word not in mapping:
            mapping[word] = rule_based_ipa.transcribe(word, rules_tuple)
    return mapping


def _normalize_ipa_word(
    ipa_word: str,
    substring_norms: list[tuple[str, str]],
    word_norms: dict[str, str],
) -> str:
    if ipa_word in word_norms:
        return word_norms[ipa_word]
    for old, new in substring_norms:
        ipa_word = ipa_word.replace(old, new)
    return ipa_word


def transcribe(
    text: str,
    custom_exceptions: dict[str, str],
    long_keys: set[str] | None,
    transcription_rules: list[tuple[str, str]],
    substring_norms: list[tuple[str, str]],
    word_norms: dict[str, str],
) -> str:
    if not text:
        return ""

    text = smart_lower(text)
    tokens = _tokenize(text)
    if not tokens:
        return ""

    # Fallback для тестов и обратной совместимости
    if long_keys is None:
        long_keys = {k for k in custom_exceptions if len(k) >= 4}

    word_segments: dict[str, list[tuple[str, bool]]] = {}

    for token in tokens:
        if not _WORD_PATTERN.match(token):
            continue

        word_lower = token.lower()
        if word_lower in word_segments:
            continue

        is_abbreviation = len(token) >= 2 and token.isupper()
        if not is_abbreviation and word_lower in custom_exceptions:
            word_segments[word_lower] = [(token, True)]
            continue

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

    english_to_transcribe: list[str] = []
    seen_english: set[str] = set()

    for segments in word_segments.values():
        for seg_text, is_dict in segments:
            if not is_dict and seg_text not in seen_english:
                english_to_transcribe.append(seg_text)
                seen_english.add(seg_text)

    english_mapping = _bulk_transcribe(english_to_transcribe, transcription_rules)

    final_tokens: list[str] = []
    for token in tokens:
        if _WORD_PATTERN.match(token):
            word_lower = token.lower()
            segments = word_segments[word_lower]
            ipa_parts: list[str] = []

            for seg_text, is_dict in segments:
                if is_dict:
                    ipa_parts.append(custom_exceptions[seg_text.lower()])
                else:
                    ipa = english_mapping.get(seg_text, seg_text)
                    ipa_parts.append(ipa)

            final_tokens.append(_normalize_ipa_word("".join(ipa_parts), substring_norms, word_norms))
        else:
            final_tokens.append(token)

    return "".join(final_tokens).strip()


def clear_split_cache() -> None:
    _SPLIT_CACHE.clear()
    rule_based_ipa.clear_cache()
