# Фонетический транскриптор английского языка в русский 🔤

[Read in English](https://github.com/Isyarname/eng-to-ru-transcriber/blob/main/README.md)

Python-библиотека для автоматической транскрипции английского текста кириллицей. Использует гибридный движок: поиск по словарю и нейросетевая G2P-модель (`gruut`) для неизвестных слов.

## 💡 Возможности

- **Универсальная транскрипция** — работает с любым английским текстом, включая выдуманные слова, неологизмы и редкие имена.
- **Свой словарь** — дополняйте встроенный словарь своими исключениями.

## ⚡ Ключевые особенности

- **Двухуровневый поиск** — IPA через локальный словарь (120 000+ слов) + нейросетевая G2P-модель в качестве запасного варианта.
- **Графическая адаптация** — кириллическая запись соответствует правилам русской орфографии.

## 🚀 Установка

```bash
pip install eng-to-ru-transcriber
```

## 💻 Использование

### Базовый пример

```python
from eng_to_ru_transcriber import Transcriber

t = Transcriber()
print(t.transcribe("Hello world"))
# → Хэлоу уорлд
```

### Свой словарь

```python
from eng_to_ru_transcriber import Transcriber

custom_vocabulary = {"python": "ˈpaɪθɑn"}
t = Transcriber(custom_vocabulary=custom_vocabulary)
print(t.transcribe("Python is great"))
```

## 🧪 Тесты

```bash
pip install pytest
pytest
```

## 📊 Источники данных

Основано на курируемых IPA-данных из OpenWiktionary.

## 📜 Лицензия

MIT