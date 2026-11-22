# Practical English-Russian Transcription

[Читать на русском языке](https://github.com/Isyarname/eng-to-ru-transcriber/blob/main/README.md)

A lightweight Python library for quick and deterministic practical transcription of English words using the Russian alphabet.

## Features & Use Cases

Built for instant Cyrillic transcription of English names, usernames, brands, and technical terms (including fast text preprocessing for TTS pipelines):

- **Practical transcription:** adapts pronunciation to Russian orthography rules rather than doing naive letter-by-letter transliteration.
- **100% offline & lightweight:** unlike cloud APIs or neural models, requires no internet, GPU, or slow model loading — its only dependency (`crispy-ipa`) is pure Python.
- **Fast:** about 10x faster than `ru-normalizr`.
- **Deterministic:** the same word always yields the exact same result.
- **Universal custom vocabulary:** override pronunciations for specific names or roots using either Cyrillic or IPA symbols.

*(See [Experiments](https://github.com/Isyarname/eng-to-ru-transcriber/blob/main/docs/EXPERIMENTS.md) for a detailed comparison with other G2P and normalization tools).*

## Limitations

- **Context-free:** The library does not perform Part-of-Speech (POS) tagging or syntactic analysis. For homographs with multiple pronunciations (like *read* or *use*), it will use the first dictionary entry.
- **Not a translator:** It transcribes *sound*, not *meaning*.

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

You can easily override the pronunciation of specific words or roots (in either Cyrillic or IPA). This is useful for names, brands, and technical terms (not present in the built-in `crispy-ipa` dictionary).

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
