import re
import unicodedata


def apply_rules(text: str, rules: tuple) -> str:
    """Применяет список готовых правил к тексту."""
    for pattern_or_str, R, has_regex in rules:
        if has_regex:
            #print(pattern_or_str)
            text = pattern_or_str.sub(R, text)
        else:
            text = text.replace(pattern_or_str, R)
    return text

def process_text(text: str, rules: tuple) -> str:
    """
    Принимает текст и готовый список правил.
    Применяет правила и возвращает нормализованную строку.
    """
    text = apply_rules(text, rules)
    text = unicodedata.normalize('NFC', text)
    return text
