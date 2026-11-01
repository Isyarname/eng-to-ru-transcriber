# Project Architecture

This document describes the internal design of the library for developers and contributors.

## 📐 How it works

```
[Input text]
       │
       ▼
[Tokenization: words + non-words]
       │
       │
       │     [Built-in en_dict.pkl]
       │              │
       │     [Custom vocabulary]
       │              │
       ▼              ▼
[Lookup in merged dictionary]
       │
       ├── Found ────────────────► [IPA from dict] ───┐
       │                                              │
       └── Not found ────────────► [rule_based_ipa]   │
                                        │             │
                                        ▼             │
                                  [IPA from rules] ───┘
                                                      │
                                                      ▼
                                                [IPA text]
                                                      │
                                                      ▼
                                          [IPA normalization]
                                            ├─ Subscript (eɪ → ej, aɪ → aj, ...)
                                            └─ Whole-word (tə → tu, whole words only)
                                                      │
                                                      │
[translated rules] ───────────────────────────────────┘
        (from transliteration_rules.json cache)       │
                                                      ▼
                              [IPA → Cyrillic transliteration]
                                        (rule_engine)
                                                      │
                                                      ▼
                                              [Cyrillic text]
```

## 🔄 Processing pipeline

### 1. `Transcriber` initialization

All resources are loaded **eagerly** in the constructor. The constructor either returns a fully working object or raises; there is no half-initialized state.

- **IPA→Cyrillic rules.** If `transliteration_rules.json` exists in the cache, it is parsed directly. Otherwise `transliteration_rules.py` is loaded as a module, its `macros` and `rules` are compiled by `dsl_translator.build_rules`, and the result is written to the JSON cache.
- **English→IPA rules.** Same procedure for `eng_to_ipa_rules.py` → `eng_to_ipa_rules.json`.
- **Dictionary.** `en_dict.pkl` is deserialized into `dict[str, str]` and stored in `_dict_cache`.
- **Custom vocabulary.** Copied into `_custom_vocabulary` (not merged yet — merging happens on each `get_vocabulary()` call, so custom overrides always win).

If a resource is missing or corrupt, `FileNotFoundError` / `ImportError` is raised from the constructor.

### 2. `transcribe()` call

- `get_vocabulary()` returns `{**_dict_cache, **_custom_vocabulary}` — a fresh dict, so callers cannot mutate internal state.
- `eng_to_ipa_hybrid.transcribe()` tokenizes the input, replaces known words and dictionary segments with IPA, transcribes the rest with `rule_based_ipa`, applies IPA normalizations, and returns IPA text.
- `ipa_to_ru.convert()` applies the compiled transliteration rules to produce Cyrillic.

### 3. Reload and cache management

- `reload_rules()` recompiles both rule sets with `force=True`, overwriting the on-disk JSON caches.
- `reload_dictionary()` re-reads `en_dict.pkl`.
- `reload_all()` combines the two.
- `clear_cache()` deletes the JSON files and immediately calls `reload_rules()`, so in-memory and on-disk state stay consistent.

## 📂 Project structure

```
eng-to-ru-transcriber/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CHANGELOG.md
│   ├── CONTRIBUTING.md
│   └── DSL.md
├── examples/
│   ├── basic_usage.py
│   └── text.txt
├── scripts/
│   ├── convert_dict.py
│   ├── en_dict.txt
│   └── make-tree.py
├── src/
│   └── eng_to_ru_transcriber/
│       ├── data/
│       │   ├── __init__.py
│       │   ├── en_dict.pkl
│       │   ├── eng_to_ipa_rules.py
│       │   ├── phonetic_normalizations.py
│       │   └── transliteration_rules.py
│       ├── __init__.py
│       ├── dsl_translator.py
│       ├── eng_to_ipa_hybrid.py
│       ├── ipa_to_ru.py
│       ├── rule_based_ipa.py
│       ├── rule_engine.py
│       └── transcriber.py
├── tests/
│   ├── conftest.py
│   ├── test_dsl_translator.py
│   ├── test_eng_to_ipa_hybrid.py
│   ├── test_ipa_to_ru.py
│   ├── test_rule_based_ipa.py
│   ├── test_rule_engine.py
│   └── test_transcriber.py
├── .gitignore
├── LICENSE
├── README.md
├── README.ru.md
└── pyproject.toml

```

### Where things live

| What                 | Where                                | Why                               |
|----------------------|--------------------------------------|-----------------------------------|
| Source code          | `src/eng_to_ru_transcriber/`         | src-layout — PyPA standard        |
| Dictionaries, rules  | `src/eng_to_ru_transcriber/data/`    | Included in wheel at build time   |
| Rules cache          | `user_cache_dir/`                    | read-write, not part of package   |
| Sample text          | `examples/text.txt`                  | Demo, not a package resource      |

## 🏗️ Architectural decisions

### Why a `Transcriber` class instead of a function?

- **Explicit state.** It's clear what is loaded into memory and what can be reloaded.
- **Lifecycle management.** `reload_dictionary()`, `reload_rules()`, `clear_cache()`.
- **Testability.** You can inject custom paths and dictionaries via `__init__`.
- **Multiple instances.** Each with its own custom vocabulary.

### Why eager resource loading?

- **Faster transcription.** Loading rules and the dictionary during initialization ensures that the first (and all subsequent) `transcribe()` calls are fast. The user doesn't pay the I/O and compilation cost mid-processing.
- **Simpler internals.** Resources are always present; getters are trivial, and `repr()` simply reports counts. There is no need for `_ensure_rules` / `_ensure_dictionary` wrappers or handling `Optional[...]` states throughout the class.
- **Predictable lifecycle.** All I/O happens exactly once when the object is created. The constructor either gives a fully working instance or raises an error.

The cost is one compile + pickle load per `Transcriber()` (~50-100 ms). For normal library use — including construction from a config factory — this is the right trade-off.

### Why does the custom vocabulary supplement the built-in dictionary?

The built-in `en_dict.txt` contains thousands of words. If the custom vocabulary replaced it, users would have to manually copy all the words they need. Supplementation lets you override the pronunciation of specific words (names, brands, terms) while keeping the standard functionality intact.

### Two dictionary levels

1. **Built-in dictionary** (`en_dict.txt`) — the base, always loaded.
2. **Custom vocabulary** (`custom_vocabulary` in `__init__`) — supplements the built-in one, takes priority on key conflicts.

The custom vocabulary is set once at object creation and cannot be modified at runtime. For different sets of overrides, create different `Transcriber` instances.

### Why src-layout?

Protects against accidentally importing the local folder instead of the installed version. The "test what you ship" principle.

### Why is the cache in `user_cache_dir`, not in the package?

After `pip install`, the package lives in `site-packages/`, where the user has no write permission. The cache must be in a user-writable directory.

### Why two types of IPA normalization?

- **Substring** (`eɪ → ej`) — applied inside words.
- **Whole-word** (`tə → tu`) — only for whole words, to avoid breaking `təmɔɹoʊ`.

### Why is `transliteration_rules.py` a `.py`, not a `.txt`?

Transliteration rules are conveniently expressed as Python variables (`macros`, `rules`). The file is loaded via `importlib.util.spec_from_file_location` — as data, not as part of the package. This lets the IDE hint the structure while keeping a clean code/data separation.

### Source rules vs translated rules

- **Source rules** (`transliteration_rules.py`) — human-readable description with macros and bracket groups.
- **translated rules** (`transliteration_rules.json`) — flat list of `(L, R)` pairs for fast application by the engine.

Compilation happens once and is cached. When the source changes, call `reload_rules()`.

## 🧪 Tests

The project is covered by unit and integration tests:

| File                        | What it checks                                               |
|-----------------------------|--------------------------------------------------------------|
| `test_compiler.py`          | Rules parser, macros, bracket groups, uppercase letters      |
| `test_transducer.py`        | Regex detector, rule application, NFC normalization          |
| `test_eng_to_ipa_hybrid.py` | Tokenization, IPA normalization, hybrid transcription        |
| `test_transcriber.py`       | Integration tests for the `Transcriber` class                |

Run:
```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## 🔧 Development

```bash
# Install in editable mode with test dependencies
pip install -e ".[dev]"

# Verify it works
python -c "from eng_to_ru_transcriber import Transcriber; print(Transcriber().transcribe('hello'))"

# Run the example
python examples/basic_usage.py

# Run tests
pytest

# Build the distribution
pip install build
python -m build
```