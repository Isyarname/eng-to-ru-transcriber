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
 [Адаптация IPA → Кириллица]
   └─ модуль: rule_engine.py
   └─ данные: default_adaptation_rules.py
        │
        ▼
 [Текст на кириллице]
```

## 🔄 Пайплайн

1. **Импорт модуля (`eng_to_ru_transcriber.transcriber`):** правила из
   `default_adaptation_rules.py` один раз подготавливаются функцией
   `dsl_compiler.build_rules()` в плоский список `(pattern, replacement, has_regex)`
   и сохраняются в модульной константе `_ADAPTATION_RULES`.
2. **Инициализация (`Transcriber.__init__`):** создаётся экземпляр
   `IPATranscriber(custom_vocabulary=custom_vocabulary)` из `crispy-ipa`.
   Правила — не состояние экземпляра, они общие для всех `Transcriber`
   в процессе.
3. **Вызов (`Transcriber.transcribe`):**
   - `self._ipa_transcriber.transcribe(text)` переводит английский текст в МФА (IPA).
   - `rule_engine.apply_rules(ipa_text, _ADAPTATION_RULES)` применяет
     подготовленные правила и переводит IPA в кириллицу.

## 📂 Структура проекта

```text
eng-to-ru-transcriber/
├── docs/                            # Documentation
├── examples/                        # Usage examples
├── scripts/                         # Dev & release tools (not shipped)
│   ├── benchmark.py
│   ├── make-tree.py
│   └── pre_release.py
├── src/eng_to_ru_transcriber/       # The library (this is what ships to PyPI)
│   ├── __init__.py                  # Public API
│   ├── transcriber.py               # Orchestrator (entry point)
│   ├── rule_engine.py               # Applies IPA → Cyrillic rules
│   ├── dsl_compiler.py              # DSL macro expander & rule builder
│   └── default_adaptation_rules.py  # IPA → Cyrillic rule definitions (DSL source)
├── .gitignore
├── LICENSE
├── README.md / README.en.md
└── pyproject.toml                   # Metadata, build config
```