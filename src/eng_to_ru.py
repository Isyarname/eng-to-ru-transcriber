# src/eng_to_ru.py
import eng_to_ipa_hybrid as eng_to_ipa
import ipa_to_ru

def transcribe(text: str, custom_exceptions: dict, compiled_rules: list) -> str:
    """Координирует чистые вычисления без обращения к диску."""
    # 1. English -> IPA
    ipa_text = eng_to_ipa.transcribe(text, custom_exceptions)
    print("🔊 IPA транскрипция:\n", ipa_text, "\n")
    
    # 2. IPA -> RU
    ru_text = ipa_to_ru.convert(ipa_text, compiled_rules)
    
    return ru_text
