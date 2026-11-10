# Project Architecture

This document describes the internal design of the library for developers and contributors.

## 📐 How it works

```text
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
```

Shared core:

```text
rule_engine.py
```

Executes the compiled rules for both EN → IPA and IPA → Cyrillic stages.

## 🔄 Processing pipeline

### 1. `Transcriber` initialization

All resources are loaded eagerly in the constructor. The constructor either returns a fully working object or raises; there is no half-initialized state.

- **IPA → Cyrillic rules.** Loaded from `data/transliteration_rules.pkl` (compiled at build time).
- **English → IPA rules.** Loaded from `data/eng_to_ipa_rules.pkl`.
- **Phonetic normalizations.** Loaded from `data/phonetic_normalizations.pkl`.
- **Dictionary.** `data/en_dict.pkl` is deserialized into `dict[str, str]` and stored in `_en_dict`.
- **Merged vocabulary.** Built once: `_merged_vocabulary = {**_en_dict, **_custom_vocabulary}` (custom overrides win). If `custom_vocabulary` is empty, `_merged_vocabulary` is a reference to `_en_dict` (no copy).
- **Long keys.** Precomputed frozenset of merged-dictionary keys with length ≥ 4, used for greedy word splitting of unknown words. Computed once and stored in `_long_keys`.

If a required resource is missing, `FileNotFoundError` is raised from the constructor. Corrupt resource data may raise a pickle-related exception.

To use different resources or a different custom vocabulary, create a new `Transcriber` instance.

### 2. `transcribe()` call

`eng_to_ipa_hybrid.transcribe()` tokenizes the input, splits unknown words using `_long_keys`, replaces known words and dictionary segments with IPA, transcribes the rest with `rule_based_ipa`, applies phonetic normalizations, and returns IPA text.

`ipa_to_ru.convert()` applies the compiled transliteration rules to produce Cyrillic.

## 📂 Project structure

```text
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
├── README.md
└── pyproject.toml              # Metadata, build config
```

### Where things live

| What | Where | Why |
|---|---|---|
| Source code | `src/eng_to_ru_transcriber/` | src-layout — PyPA standard |
| Compiled runtime data | `src/eng_to_ru_transcriber/data/*.pkl` | Included in wheel at build time |
| Source rules & dictionary | `data_src/` | Human-editable, not shipped |
| Build tools | `scripts/` | Build-time only, not shipped |
| Sample text | `examples/text.txt` | Demo, not a package resource |

## 🏗️ Architectural decisions

### Why a `Transcriber` class instead of a function?

The main reason is resource lifecycle. The dictionary and rule data are loaded once during initialization and reused by every `transcribe()` call.

A plain function would either reload resources on every call or require hidden global state. The class makes the loaded state explicit and allows different instances to use different custom vocabularies.

### Why eager resource loading?

- **Faster transcription.** Loading rules and the dictionary during initialization ensures that every `transcribe()` call is fast. The user does not pay I/O cost mid-processing.
- **Simpler internals.** Resources are always present; getters are trivial, and `repr()` simply reports counts. There is no `Optional[...]` state.
- **Predictable lifecycle.** All I/O happens exactly once at object creation.

The cost is about 100 ms per `Transcriber()` (pickle load). For TTS pipelines and CLI tools, this is usually not an issue.

### Why merge `custom_vocabulary` in `__init__`?

`custom_vocabulary` is static: it is provided once at construction time. Merging it with the built-in dictionary on every `transcribe()` call would copy 125k keys per call — a catastrophic performance regression. Merging once in `__init__` eliminates this entirely.

### Why precompute `long_keys`?

`_split_word_from_end` needs the set of dictionary keys with length ≥ 4 to split unknown words. Building this set from 125k keys on every `transcribe()` call would cost around 15 ms regardless of input size. Computing it once in `__init__` reduces per-call cost to about 0.07 ms (≈200× faster).

### Why does the custom vocabulary supplement the built-in dictionary?

The built-in dictionary contains 125k+ words. If the custom vocabulary replaced it, users would have to copy all needed words. Supplementation lets you override specific words (names, brands, terms) while keeping standard functionality intact.

### Why src-layout?

It protects against accidentally importing the local folder instead of the installed version. This follows the “test what you ship” principle.

### Why two types of IPA normalization?

Substring normalization applies to recurring IPA sequences inside words.
Whole-word normalization applies only when the entire IPA word matches.

This separation prevents exceptional short-word fixes from being applied inside longer words.

### Why are source rules Python modules?

Because Python already provides a structured, importable data format.

Using `.py` files avoids inventing a custom storage format and writing a parser for it. Macros and rules are ordinary Python objects, and the build script can load them directly.

IDE support and structural validation are useful side effects.

### Source rules vs compiled rules

- **Source rules** (`data_src/transliteration_rules.py`) are human-readable and may contain macros and bracket groups.
- **Compiled rules** (`data/transliteration_rules.pkl`) are a flat list of `(L, R)` pairs, compiled once at build time by `scripts/build_rules.py`.

There is no runtime compilation. The runtime uses precompiled `.pkl` files.

If you modify source rules in a development checkout, run `scripts/build_rules.py`
to regenerate the compiled data. With an editable installation, the updated files
are used directly.

Pip users do not rebuild rules: they install a package version that already
contains the compiled data.

## Testing

Tests live in `tests/` and cover rule compilation, the rule engine,
hybrid transcription, and `Transcriber` integration.