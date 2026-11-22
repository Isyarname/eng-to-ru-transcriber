# Архитектура проекта

Документ описывает внутреннее устройство библиотеки.

## 📐 Схема работы

```text
[Входной текст]
        │
        ▼
 [Транскрипция EN → IPA]
   └─ зависимость: crispy-ipa (IPATranscriber)
        │
        ▼
   [Текст IPA]
        │
        ▼
 [Нормализация и транслитерация IPA → Кириллица]
   └─ модуль: rule_engine.py
   └─ данные: ipa_to_ru_adaptation.pkl
        │
        ▼
 [Текст на кириллице]
```

## 🔄 Пайплайн

1. **Инициализация (`Transcriber.__init__`):** создаётся экземпляр `IPATranscriber(custom_vocabulary=custom_vocabulary)` из `crispy-ipa` и загружаются скомпилированные правила из `data/ipa_to_ru_adaptation.pkl`.
2. **Вызов (`Transcriber.transcribe`):**
   - `self._ipa_transcriber.transcribe(text)` переводит английский текст в МФА (IPA).
   - `rule_engine.process_text(ipa_text, self._transliteration_rules)` применяет скомпилированные правила адаптации и переводит IPA в кириллицу.

## 📂 Структура проекта

```text
eng-to-ru-transcriber/
├── data_src/                   # Исходные правила (не поставляются)
├── docs/                       # Документация
├── examples/                   # Примеры использования
├── scripts/                    # Скрипты сборки и бенчмарков (не поставляются)
│   ├── build_rules.py          # Компиляция data_src/*.py → data/*.pkl
│   └── benchmark.py
├── src/eng_to_ru_transcriber/  # Код пакета (поставляется в PyPI)
│   ├── data/*.pkl              # Скомпилированные правила
│   ├── __init__.py             # Публичный API
│   ├── transcriber.py          # Оркестратор
│   └── rule_engine.py          # Исполнитель правил
├── LICENSE
├── README.en.md
├── README.md
├── THIRD_PARTY_LICENSES.md
└── pyproject.toml
```

## ⚙️ Сборка правил

Исходные правила в `data_src/ipa_to_ru_adaptation.py` содержат макросы и группы в скобках. Перед сборкой пакета скрипт `scripts/build_rules.py` разворачивает их в плоский список и сохраняет в `src/eng_to_ru_transcriber/data/ipa_to_ru_adaptation.pkl` — в рантайме компиляция не выполняется.
