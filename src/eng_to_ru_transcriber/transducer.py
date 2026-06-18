import re
import unicodedata

# Заранее компилируем регулярное выражение для проверки символов регулярки
HAS_REGEX_SYMBOLS = re.compile(r"[\*\+\?\{\}\[\]\(\)\^\$\|\\\.]")

def apply_rules(text: str, rules: list) -> str:
    """Применяет список готовых правил к тексту."""
    prepared_rules = []
    for L, R in rules:
        if HAS_REGEX_SYMBOLS.search(L):
            prepared_rules.append((re.compile(L), R, True))
        else:
            prepared_rules.append((L, R, False))
            
    for pattern_or_str, R, has_regex in prepared_rules:
        if has_regex:
            text = pattern_or_str.sub(R, text)
        else:
            text = text.replace(pattern_or_str, R)
    return text

def process_text(text: str, rules: list) -> str:
    """
    Принимает текст и готовый список правил (загруженный из JSON в main.py).
    Применяет правила и возвращает нормализованную строку.
    """
    text = apply_rules(text, rules)
    text = unicodedata.normalize('NFC', text)
    return text
