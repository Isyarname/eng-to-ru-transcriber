# English-to-russian practical transcriber

[Читать на русском языке](https://github.com/Isyarname/eng-to-ru-transcriber/blob/main/README.ru.md)

A Python library for automatic English-to-Cyrillic text transcription using a hybrid engine: dictionary lookup and rule-based transcription for unknown words.

## 💡 Features

- **Universal transcription** — handles any English text, including invented words, neologisms, and rare names.
- **Custom vocabulary** — augment the built-in dictionary with your own overrides.

## ⚡ Key Highlights

- **Two-tier lookup** — IPA via local 120k+ dict + rule-based transcription backup.
- **Graphemic adaptation** — Cyrillic matches Russian orthography.

## 🚀 Installation

```bash
pip install eng-to-ru-transcriber
```

## 💻 Usage

### Basic Example

```python
from eng_to_ru_transcriber import Transcriber

t = Transcriber()
print(t.transcribe("Hello world"))
# → Хэлоу уорлд
```

### Custom Vocabulary

```python
from eng_to_ru_transcriber import Transcriber

custom_vocabulary = {"python": "ˈpaɪθɑn"}
t = Transcriber(custom_vocabulary=custom_vocabulary)
print(t.transcribe("Python is great"))
```

## 🧪 Testing

```bash
pip install pytest
pytest
```

## 📊 Data Sources

Based on curated IPA data from OpenWiktionary.

## 📜 License

MIT
