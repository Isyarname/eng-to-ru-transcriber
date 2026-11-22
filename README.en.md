# Practical English-Russian Transcription

[Читать на русском языке](https://github.com/Isyarname/eng-to-ru-transcriber/blob/main/README.md)

A lightweight Python library for quick and deterministic practical transcription of English words using the Russian alphabet.

## Why this exists

**This library is built for:**
- **Transcribing names, usernames, brand names, and specific technical terms** (e.g., *Daenerys*, *MacBook*, *Kubernetes*).
- **Fast TTS pipelines**, where instant, offline processing without heavy ML models is critical.

Modern translation tools are powerful, but they are overkill for simple tasks:
- **Cloud APIs** (like Google Translate) require an internet connection and have rate limits.
- **Neural networks** are heavy, slow to initialize, and can produce unpredictable results.

Sometimes you just need to instantly write English names or terms using the Russian alphabet without waiting for models to load. Existing G2P and normalization packages were tested for this task and found lacking. You can read the detailed comparison in [Experiments](https://github.com/Isyarname/eng-to-ru-transcriber/blob/main/docs/EXPERIMENTS.md).

## Limitations

- **Context-free:** The library does not perform Part-of-Speech (POS) tagging or syntactic analysis. For homographs with multiple pronunciations (like *read* or *use*), it will use the first dictionary entry.
- **Not a translator:** It transcribes *sound*, not *meaning*.

## Features

- **Practical transcription:** adapts IPA pronunciation to match Russian orthography rules, rather than just letter-by-letter replacement.
- **Lightweight & 100% offline:** no heavy ML models or cloud APIs (depends only on pure-Python `crispy-ipa`). Works instantly.
- **Deterministic:** the same word always yields the exact same result.
- **Fast and accurate:** About 10 times faster than `ru-normalizr` on real text, with superior handling of English slang, names, and abbreviations.
- **Universal custom vocabulary:** define overrides directly in Cyrillic or using IPA symbols.

## Installation

Requires Python 3.10 or higher.

```bash
pip install eng-to-ru-transcriber
```

## Usage

### Basic Example

```python
from eng_to_ru_transcriber import Transcriber

t = Transcriber()
print(t.transcribe("Hello, URL!")) 
# → хэлоу, ю-ар-эл!
```

*Abbreviations (like URL) are automatically detected and read letter-by-letter.*

### Custom Vocabulary

You can easily override the pronunciation of specific words or roots (in either Cyrillic or IPA). This is useful for names, brands, and technical terms not present in the built-in (`crispy-ipa`) dictionary.

```python
from eng_to_ru_transcriber import Transcriber

text = "The dockerizer is dockerizing the docker image."

# Without vocabulary
t1 = Transcriber()
print(t1.transcribe(text))
# → дэ дакэрайзэр из дакэрайзинг дэ дакэр имэдж.

# With vocabulary: teach the library a new root "docker"
t2 = Transcriber(custom_vocabulary={"docker": "докер"})
print(t2.transcribe(text))
# → дэ докерайзэр из докерайзинг дэ докер имэдж.
```

The words `dockerizer` and `dockerizing` are not in the built-in dictionary. However, the `crispy-ipa` engine automatically splits them into the root `docker` and suffixes (`izer`, `izing`), applying your custom pronunciation to the root and transcription rules to the endings.

## Development & Testing

To check that the library works correctly in your environment, run the built-in example:

```bash
pip install -e .
python examples/basic_usage.py
```

## Data Sources

Intermediate IPA transcription is powered by [crispy-ipa](https://pypi.org/project/crispy-ipa), which uses [open-dict-data/ipa-dict](https://github.com/open-dict-data/ipa-dict) (MIT License).

## License

MIT
