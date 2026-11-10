# Practical English-Russian Transcription

[Читать на русском языке](https://github.com/Isyarname/eng-to-ru-transcriber/blob/main/README.ru.md)

A lightweight Python library for quick and deterministic practical transcription of English words using the Russian alphabet.

## Why this exists

**This library is built for:**
- **Transcribing names, usernames, brand names, and specific technical terms** (e.g., *Daenerys*, *MacBook*, *Kubernetes*).
- **Fast TTS pipelines**, where instant, offline processing without heavy ML models is critical.

Modern translation tools are powerful, but they are overkill for simple tasks:
- **Cloud APIs** (like Google Translate) require an internet connection and have rate limits.
- **Neural networks** are heavy, slow to initialize, and can produce unpredictable results.

Sometimes you just need to instantly write English names or terms using the Russian alphabet without waiting for models to load.

## Limitations

- **Context-free:** The library does not perform Part-of-Speech (POS) tagging or syntactic analysis. For homographs with multiple pronunciations (like *read* or *use*), it will use the first dictionary entry.
- **Not a translator:** It transcribes *sound*, not *meaning*.

## Features

- **Practical transcription:** adapts IPA pronunciation to match Russian orthography rules, rather than just letter-by-letter replacement.
- **Vowel length indication:** long vowels are marked with an acute accent (e.g., `и́`, `у́`), preserving phonetic accuracy.
- **Zero dependencies & 100% offline:** no heavy ML models or cloud APIs. Works instantly.
- **Deterministic:** the same word always yields the exact same result.
- **Hybrid engine:** uses a built-in 120k+ word dictionary for common words and a fast rule-based engine for everything else.
- **Custom vocabulary:** easily teach the library how to transcribe your specific character names, brands, or terms.

## Installation

Requires Python 3.9 or higher.

```bash
pip install eng-to-ru-transcriber
```

## Usage

### Basic Example

```python
from eng_to_ru_transcriber import Transcriber

t = Transcriber()
print(t.transcribe("Hello, URL!")) 
# → халоу, ю-ар-эл!
```

*Abbreviations (like URL) are automatically detected and read letter-by-letter.*

### Custom Vocabulary

You can easily override the pronunciation of specific words. The dictionary accepts both ready Cyrillic text and IPA phonetic notation:

```python
from eng_to_ru_transcriber import Transcriber

# You can mix formats: Cyrillic and IPA
custom_vocabulary = {
    "python": "пайтон",           # Cyrillic
    "kubernetes": "ˌkjuːbəˈnɛtɪs" # IPA
}

t = Transcriber(custom_vocabulary=custom_vocabulary)
print(t.transcribe("I love Python and Kubernetes"))
# → ай лав пайтон энд къю́банэтис
```

## Testing

```bash
pip install -e ".[dev]"
python -m pytest
```

## Data Sources

English IPA data is derived from [open-dict-data/ipa-dict](https://github.com/open-dict-data/ipa-dict) (MIT License, Copyright © 2016 dohliam).

## License

MIT