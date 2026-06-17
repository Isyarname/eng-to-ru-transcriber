import re
import eng_to_ipa as ipa

def transcribe(text: str, custom_exceptions: dict) -> str:
    """Чистая функция транскрипции в IPA на основе готовой структуры исключений."""
    tokens = re.findall(r"[a-zA-Z']+|[^a-zA-Z']+", text)
    words_to_bulk_transcribe = []
    
    for token in tokens:
        if re.match(r"^[a-zA-Z']+$", token):
            word_lower = token.lower()
            if word_lower not in custom_exceptions:
                words_to_bulk_transcribe.append(word_lower)

    bulk_mapping = {}
    if words_to_bulk_transcribe:
        bulk_text = " ".join(words_to_bulk_transcribe)
        bulk_ipa_result = ipa.convert(bulk_text, keep_punct=False)
        bulk_ipa_words = bulk_ipa_result.split()
        
        if len(words_to_bulk_transcribe) == len(bulk_ipa_words):
            for w, ipa_w in zip(words_to_bulk_transcribe, bulk_ipa_words):
                bulk_mapping[w] = ipa_w.replace("*", "")

    final_tokens = []
    for token in tokens:
        if re.match(r"^[a-zA-Z']+$", token):
            word_lower = token.lower()
            if word_lower in custom_exceptions:
                final_tokens.append(custom_exceptions[word_lower])
            elif word_lower in bulk_mapping:
                final_tokens.append(bulk_mapping[word_lower])
            else:
                final_tokens.append(token)
        else:
            final_tokens.append(token)

    result_str = "".join(final_tokens).strip()

    result_str = (result_str
                .replace("/", "")
                .replace("ɚi", "əɹi")
                .replace("eɪ", "ej")
                .replace("deɪ", "dej")
                .replace("aɪ", "aj")
                .replace("ɑɪ", "aj")
                .replace("ɔɪ", "ɔj")
                .replace("oɪ", "ɔj")
                .replace(" tə ", " tu ")
                .replace("əl ", "l ")
                .replace("ɝi", "eɹi")
                .replace("əɫ ", "ɫ "))
                  
    return result_str
