# src/ipa_to_ru.py
import transducer

def convert(ipa_text: str, compiled_rules: list) -> str:
    """Передает готовый массив правил в рантайм-движок."""
    return transducer.process_text(ipa_text, compiled_rules)
