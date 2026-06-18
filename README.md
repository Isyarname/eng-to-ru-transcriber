# English-to-Russian Phonetic Transcriber 🔤

Python-библиотека для автоматической транскрипции английского текста кириллицей. Использует гибридный движок: словарь + нейросетевая G2P-модель (`gruut`) для неизвестных слов.

## 💡 Возможности

- **Транскрипция любого английского текста** — даже выдуманных слов, неологизмов и редких имён
- **Свой словарь исключений** — пользовательские исключения дополняют встроенный словарь, чтобы переопределить произношение имён, брендов, терминов
- **Динамическое управление исключениями** — добавляйте и удаляйте исключения во время работы программы

## ⚡ Особенности

- **Двухуровневый поиск** — точные транскрипции из локального словаря + нейросетевая G2P-модель (`gruut`) для редких слов, неологизмов и вымышленных имён
- **Графическая адаптация** — русская транскрипция автоматически учитывает правила орфографии (`йэ → е`, `ʲа → я`, `ʲу → ю`)
- **Декларативные правила** — компактный синтаксис и макросы позволяют добавлять новые правила транслитерации без изменения кода

## 🚀 Установка

### Из исходников (пока пакет не опубликован на PyPI)

```bash
git clone https://github.com/Isyarname/eng-to-ru-transcriber
cd eng-to-ru-transcriber
pip install -e .
```

Флаг `-e` (editable) устанавливает пакет в режиме разработки — изменения в коде применяются сразу без переустановки.


## 💻 Использование

### Базовый пример

```python
from eng_to_ru_transcriber import Transcriber

t = Transcriber()
print(t.transcribe("Hello world, this is a test."))
# → Хэлоу уорлд, зис из э тэст.
```

### Пользовательские исключения транскрипции в МФА (дополняют встроенный словарь)

```python
from eng_to_ru_transcriber import Transcriber

custom_exceptions = {
    "python": "ˈpaɪθɑn",
    "docker": "ˈdɑkər",
}

t = Transcriber(custom_exceptions=custom_exceptions)
print(t.transcribe("Python and Docker are great"))
# Встроенные слова (great) + пользовательские (Python, Docker)
```

### Динамическое управление исключениями транскрипции в МФА

```python
from eng_to_ru_transcriber import Transcriber

t = Transcriber()

# Добавить одно исключение
t.add_exception("kubernetes", "ˈkuːbərˌnɛtɪs")

# Добавить несколько
t.add_exceptions({
    "nginx": "ˈɛndʒɪnˌɛks",
    "redis": "ˈrɛdɪs",
})

# Удалить одно
t.remove_exception("kubernetes")

# Удалить все пользовательские
t.clear_custom_exceptions()
```

### Временные исключения транскрипции в МФА для одного вызова

```python
from eng_to_ru_transcriber import Transcriber

t = Transcriber()

# Эти исключения используются только для этого вызова
result = t.transcribe("Special word", custom_exceptions={"special": "ˈspɛʃəl"})

# В объекте они не сохраняются
print(t.get_custom_exceptions())  # {}
```

### Перезагрузка данных

```python
from eng_to_ru_transcriber import Transcriber

t = Transcriber()
t.transcribe("hello")

# После изменения файла словаря
t.reload_dictionary()

# После изменения DSL-правил транслитерации
t.reload_transliteration()
```

### Консольный пример

```bash
git clone https://github.com/Isyarname/eng-to-ru-transcriber
cd eng-to-ru-transcriber
pip install -e .
python examples/basic_usage.py
```

Скрипт читает английский текст из `examples/text.txt` и сохраняет результат в `output_text.txt` в корне проекта.

## 🧪 Тесты

```bash
pip install pytest
pytest
```

## 📊 Источники данных

- **Фонетическая база данных** — встроенный словарь `en_US.txt` использует очищенные данные транскрипций из репозитория [open-dict-data/ipa-dict](https://github.com) (распространяется под лицензией MIT), которые изначально были собраны на основе свободных дампов **Викисловаря (Wiktionary)**.


## 📖 Документация

- [Архитектура проекта](ARCHITECTURE.md) — пайплайны, модули, как устроено внутри
- [Руководство контрибьютора](CONTRIBUTING.md) — как внести вклад

## 📜 Лицензия

MIT