# Project Architecture

This document describes the internal design of the library for developers and contributors.

## 📐 How it works

```
[Input text]
       │
       ▼
[Tokenization]
  └─ module: eng_to_ipa_hybrid.py
       │
       ▼
[Lookup in merged dictionary]
  └─ module: eng_to_ipa_hybrid.py
  └─ data:   en_dict.pkl + custom_vocabulary
       │
       ├── Found ───────────────────────────────────────────────────────────────┐
       │                                                                        │
       └── Not found ──► [EN → IPA Transcription]                               │
                                └─ module: rule_based_ipa.py                    │
                                └─ data:   eng_to_ipa_rules.pkl                 │
                                │                                               │
                                ▼                                               │
                         [IPA text] ◄───────────────────────────────────────────┘
                                │
                                ▼
                         [IPA Normalization]
                                └─ module: eng_to_ipa_hybrid.py
                                └─ data:   phonetic_normalizations.pkl
                                │
                                ▼
                         [IPA → Cyrillic Transliteration]
                                └─ module: ipa_to_ru.py
                                └─ data:   transliteration_rules.pkl
                                │
                                ▼
                         [Cyrillic text]

Shared core:
  └─ module: rule_engine.py
     (executes the compiled rules for both EN → IPA and IPA → Cyrillic stages)
```

## 🔄 Processing pipeline

### 1. `Transcriber` initialization

All resources are loaded **eagerly** in the constructor. The constructor either returns a fully working object or raises; there is no half-initialized state.

- **IPA→Cyrillic rules.** Loaded from `data/transliteration_rules.pkl` (compiled at build time).
- **English→IPA rules.** Loaded from `data/eng_to_ipa_rules.pkl`.
- **Phonetic normalizations.** Loaded from `data/phonetic_normalizations.pkl`.
- **Dictionary.** `data/en_dict.pkl` is deserialized into `dict[str, str]` and stored in `_en_dict`.
- **Merged vocabulary.** Built once: `_merged_vocabulary = {**_en_dict, **_custom_vocabulary}` (custom overrides win). If `custom_vocabulary` is empty, `_merged_vocabulary` is a reference to `_en_dict` (no copy).
- **Long keys.** Precomputed set of merged-dictionary keys with length ≥ 4, used for greedy word splitting of unknown words. Computed once and stored in `_long_keys`.

If a resource is missing or corrupt, `FileNotFoundError` is raised from the constructor.

### 2. `transcribe()` call

- `eng_to_ipa_hybrid.transcribe()` tokenizes the input, splits unknown words using `_long_keys`, replaces known words and dictionary segments with IPA, transcribes the rest with `rule_based_ipa`, applies phonetic normalizations, and returns IPA text.
- `ipa_to_ru.convert()` applies the compiled transliteration rules to produce Cyrillic.

### 3. No reload methods

Resources are loaded **once** in `__init__`. To pick up changed rules or dictionary, create a new `Transcriber` instance. There is no `reload_rules`, `reload_dictionary`, `reload_all`, or `clear_cache` — this was removed in 0.3.0 in favor of a predictable, immutable lifecycle.

## 📂 Project structure

```
 eng-to-ru-transcriber/
├── data_src/                   # Source rules & dictionary (not shipped)
├── docs/                       # Documentation
├── examples/                   # Usage examples
├── scripts/                    # Build & release tools (not shipped)
│   ├── build_rules.py          # Compiles data_src/*.py → data/*.pkl
│   ├── convert_dict.py         # Compiles data_src/en_dict.txt → data/en_dict.pkl
│   └── ...
├── src/eng_to_ru_transcriber/  # The library (this is what ships to PyPI)
│   ├── data/*.pkl              # Compiled runtime data
│   ├── __init__.py             # Public API
│   ├── transcriber.py          # Orchestrator (entry point)
│   ├── eng_to_ipa_hybrid.py    # EN → IPA (dictionary + rules)
│   ├── rule_based_ipa.py       # Applies EN → IPA rules
│   ├── ipa_to_ru.py            # Applies IPA → Cyrillic rules
│   └── rule_engine.py          # Shared regex/literal rule executor
├── tests/                      # Pytest suite
├── .gitignore
├── LICENSE
├── README.md / README.ru.md
└── pyproject.toml              # Metadata, build config
```

### Where things live

| What                       | Where                                    | Why                                       |
|----------------------------|------------------------------------------|-------------------------------------------|
| Source code                | `src/eng_to_ru_transcriber/`             | src-layout — PyPA standard                |
| Compiled runtime data      | `src/eng_to_ru_transcriber/data/*.pkl`   | Included in wheel at build time           |
| Source rules & dictionary  | `data_src/`                              | Human-editable, not shipped               |
| Build tools                | `scripts/`                               | Build-time only, not shipped              |
| Sample text                | `examples/text.txt`                      | Demo, not a package resource              |

## 🏗️ Architectural decisions

### Why a `Transcriber` class instead of a function?

- **Explicit state.** It's clear what is loaded into memory.
- **Testability.** You can inject custom paths and dictionaries via `__init__`.
- **Multiple instances.** Each with its own custom vocabulary.

### Why eager resource loading?

- **Faster transcription.** Loading rules and the dictionary during initialization ensures that every `transcribe()` call is fast. The user doesn't pay I/O cost mid-processing.
- **Simpler internals.** Resources are always present; getters are trivial, and `repr()` simply reports counts. There is no `Optional[...]` state.
- **Predictable lifecycle.** All I/O happens exactly once at object creation.

The cost is ~100 ms per `Transcriber()` (pickle load). For TTS pipelines and CLI tools, this is a non-issue.

### Why is there no `reload_*` API?

Because resources are immutable within an instance. If you need changed rules, create a new `Transcriber`. This avoids a class of bugs where some internal state (e.g. `_long_keys`, `_merged_vocabulary`) is stale after a partial reload. It also matches the "static custom vocabulary" design (see CHANGELOG 0.2.0).

### Why merge `custom_vocabulary` in `__init__`?

`custom_vocabulary` is static (set once, never modified). Merging it with the built-in dictionary on every `transcribe()` call would copy 125k keys per call — a catastrophic performance regression. Merging once in `__init__` eliminates this entirely.

### Why precompute `long_keys`?

`_split_word_from_end` needs the set of dictionary keys with length ≥ 4 to split unknown words. Building this set from 125k keys on every `transcribe()` call costs ~15 ms regardless of input size. Computing it once in `__init__` reduces per-call cost to ~0.07 ms (≈200× faster).

### Why does the custom vocabulary supplement the built-in dictionary?

The built-in dictionary contains 125k+ words. If the custom vocabulary replaced it, users would have to copy all needed words. Supplementation lets you override specific words (names, brands, terms) while keeping standard functionality intact.

### Why src-layout?

Protects against accidentally importing the local folder instead of the installed version. The "test what you ship" principle.

### Why two types of IPA normalization?

- **Substring** (`eɪ → ej`) — applied inside words.
- **Whole-word** (`tə → tu`) — only for whole words, to avoid breaking `təmɔɹoʊ`.

### Why is `transliteration_rules.py` a `.py`, not a `.txt`?

Rules are conveniently expressed as Python variables (`macros`, `rules`). The compiler loads them via `importlib.util.spec_from_file_location`. This lets the IDE hint the structure while keeping a clean code/data separation.

### Source rules vs compiled rules

- **Source rules** (`data_src/transliteration_rules.py`) — human-readable with macros and bracket groups.
- **Compiled rules** (`data/transliteration_rules.pkl`) — flat list of `(L, R)` pairs, compiled once at build time by `scripts/build_rules.py`.

There is no runtime compilation and no JSON cache. When source rules change, run `scripts/build_rules.py` and reinstall the package.

## 🧪 Tests

The project is covered by unit and integration tests:

| File                        | What it checks                                                       |
|-----------------------------|----------------------------------------------------------------------|
| `test_dsl_translator.py`    | Rules parser, macro preparation, bracket groups, `build_rules`       |
| `test_rule_engine.py`       | Regex detector, rule application, NFC normalization                  |
| `test_ipa_to_ru.py`         | `ipa_to_ru.convert()` wrapper                                        |
| `test_rule_based_ipa.py`    | `smart_lower`, `transcribe` with `lru_cache`                         |
| `test_eng_to_ipa_hybrid.py` | Tokenization, `smart_lower`, hybrid transcription, long-key splitting |
| `test_transcriber.py`       | Integration tests for `Transcriber` (eager loading, custom vocabulary) |

Run:
```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

## 🔧 Development

```bash
# Install in editable mode with test dependencies
pip install -e ".[dev]"

# Rebuild compiled rules and dictionary (after changing data_src/)
python scripts/build_rules.py
python scripts/convert_dict.py

# Verify it works
python -c "from eng_to_ru_transcriber import Transcriber; print(Transcriber().transcribe('hello'))"

# Run the example
python examples/basic_usage.py

# Run tests
python -m pytest

# Benchmark
python scripts/benchmark.py

# Build the distribution
pip install build
python -m build
```