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
       │     [Built-in en_dict.txt]
       │              │
       │     [Custom vocabulary]
       │              │
       ▼              ▼
[Lookup in merged dictionary]
       │
       ├── Found ────────────────► [IPA from dict] ───┐
       │                                              │
       └── Not found ────────────► [gruut]            │
                                        │             │
                                        ▼             │
                                  [IPA from gruut] ───┘
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
[Compiled rules] ─────────────────────────────────────┘
        (from compiled_rules.json cache)              │
                                                      ▼
                              [IPA → Cyrillic transliteration]
                                        (transducer)
                                                      │
                                                      ▼
                                              [Cyrillic text]
```

## 🔄 Processing pipeline

### 1. `Transcriber` initialization

When `Transcriber()` is created, resources are **not loaded yet**. Only paths are remembered:
- `rules_path` — path to transliteration rules (default — package resource)
- `dict_path` — path to dictionary (default — package resource)
- `cache_dir` — path to cache (default — `user_cache_dir`)
- `custom_vocabulary` — user's custom vocabulary (if provided)

### 2. First `transcribe()` call

- **Rule compilation.** If `compiled_rules.json` is missing from the cache, transliteration rules from `transliteration_rules.py` are parsed, macros are expanded, variants for uppercase letters are duplicated, and the result is saved to the JSON cache.
- **Dictionary loading.** `en_dict.txt` is read, parsed into `dict[str, str]`, and stored in `_dict_cache`.
- **Dictionary merging.** Built-in + custom vocabulary (custom entries take priority).

### 3. Subsequent calls

- Compiled rules and dictionary are taken from memory (`_compiled_rules`, `_dict_cache`).
- `gruut` is imported lazily — only when there are words missing from both dictionaries.

## 📂 Project structure

```
eng-to-ru-transcriber/
├── pyproject.toml                          # Metadata and build config
├── src/eng_to_ru_transcriber/              # Library package
│   ├── __init__.py                         # Exports Transcriber
│   ├── transcriber.py                      # Orchestrator class
│   ├── compiler.py                         # Transliteration rules compiler
│   ├── transducer.py                       # Rule application engine
│   ├── ipa_to_ru.py                        # IPA → Cyrillic bridge
│   ├── eng_to_ipa_hybrid.py                # Dictionary + gruut (lazy import)
│   └── data/                               # Package resources (included in wheel)
│       ├── __init__.py
│       ├── en_dict.txt                     # Built-in dictionary
│       ├── transliteration_rules.py        # Transliteration rules (source)
│       └── phonetic_normalizations.py      # Linguistic IPA replacements
├── examples/                               # Usage demonstration
│   ├── basic_usage.py
│   └── text.txt                            # Sample text
└── tests/
    ├── conftest.py                         # Shared fixtures
    ├── test_compiler.py                    # Compiler unit tests
    ├── test_transducer.py                  # Engine unit tests
    ├── test_eng_to_ipa_hybrid.py           # Hybrid engine unit tests
    └── test_transcriber.py                 # Transcriber integration tests
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

- **Subscript** (`eɪ → ej`) — applied inside words.
- **Whole-word** (`tə → tu`) — only for whole words, to avoid breaking `təmɔɹoʊ`.

### Why is `gruut` imported lazily?

`gruut` loads an ML model (~50-100 MB). If all words are in the built-in dictionary, `gruut` is never loaded, and package import takes milliseconds.

### Why is `transliteration_rules.py` a `.py`, not a `.txt`?

Transliteration rules are conveniently expressed as Python variables (`macros`, `rules`). The file is loaded via `importlib.util.spec_from_file_location` — as data, not as part of the package. This lets the IDE hint the structure while keeping a clean code/data separation.

### Source rules vs compiled rules

- **Source rules** (`transliteration_rules.py`) — human-readable description with macros and bracket groups.
- **Compiled rules** (`compiled_rules.json`) — flat list of `(L, R)` pairs for fast application by the engine.

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