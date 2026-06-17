import re
from gruut import sentences  # Импортируем движок gruut

def transcribe(text: str, custom_exceptions: dict) -> str:
    """
    Высокопроизводительная гибридная функция транскрипции.
    Использует gruut для пакетной (bulk) обработки неизвестных слов,
    что исключает просадки по скорости.
    """
    # 1. Токенизация исходного текста
    tokens = re.findall(r"[a-zA-Z']+|[^a-zA-Z']+", text)
    words_to_bulk_transcribe = []
    
    # 2. Собираем только уникальные слова, которых нет в локальном словаре исключений
    seen_words = set()
    for token in tokens:
        if re.match(r"^[a-zA-Z']+$", token):
            word_lower = token.lower()
            if word_lower not in custom_exceptions and word_lower not in seen_words:
                words_to_bulk_transcribe.append(word_lower)
                seen_words.add(word_lower)

    # 3. ПАКЕТНАЯ ОБРАБОТКА (Bulk): Один вызов gruut для всей кучи неизвестных слов
    bulk_mapping = {}
    if words_to_bulk_transcribe:
        bulk_text = " ".join(words_to_bulk_transcribe)
        
        # Запускаем gruut для американского английского (en-us)
        # Он возвращает генератор предложений, слов и их фонем
        for sent in sentences(bulk_text, lang="en-us"):
            for word in sent:
                if word.phonemes:
                    # Склеиваем список фонем в единую строку транскрипции
                    # убирая пробелы между звуками, чтобы получить монолитное IPA слово
                    ipa_word = "".join(word.phonemes)
                    bulk_mapping[word.text] = ipa_word

    # 4. Сборка финального текста из токенов с подстановкой результатов
    final_tokens = []
    for token in tokens:
        if re.match(r"^[a-zA-Z']+$", token):
            word_lower = token.lower()
            if word_lower in custom_exceptions:
                final_tokens.append(custom_exceptions[word_lower])
            elif word_lower in bulk_mapping:
                final_tokens.append(bulk_mapping[word_lower])
            else:
                # Если слова нет вообще нигде, оставляем исходный токен
                final_tokens.append(token)
        else:
            final_tokens.append(token)

    result_str = "".join(final_tokens).strip()

    # 5. Ваши лингвистические замены для адаптации под русскую графику
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
