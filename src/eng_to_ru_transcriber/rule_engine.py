
def apply_rules(text: str, rules: tuple) -> str:
    """Применяет список готовых правил к тексту."""
    for pattern_or_str, R, has_regex in rules:
        if has_regex:
            text = pattern_or_str.sub(R, text)
        else:
            text = text.replace(pattern_or_str, R)
    return text
