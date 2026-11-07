# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-11-07

### Changed
- **Breaking:** `Transcriber` constructor parameters renamed for clarity and to reflect the new `.pkl`-only loading:
  - `rules_path` → `translit_rules_pkl`
  - `eng_rules_path` → `eng_to_ipa_rules_pkl`
  - `dict_path` → `en_dict_pkl`
  - `cache_dir` → removed (no cache directory anymore)
  - `norms_pkl` (new parameter) for phonetic normalizations.
  All parameters now accept paths to compiled `.pkl` files, not source `.py` files.
- Rules are now compiled at **build time** by `scripts/build_rules.py` and shipped as `.pkl` inside the wheel. No JSON cache, no runtime compilation.
- `dsl_translator.py` moved from `src/eng_to_ru_transcriber/` to `scripts/` — it is now a build-time tool, not part of the runtime package.
- Source rule files (`transliteration_rules.py`, `eng_to_ipa_rules.py`, `phonetic_normalizations.py`) and `en_dict.txt` moved to `data_src/` in the repository. Only compiled `.pkl` files remain in the wheel.
- `Transcriber` merges `custom_vocabulary` with the built-in dictionary **once in `__init__`** instead of on every `transcribe()` call. This fixes a severe performance regression (~15 ms per call regardless of input size).
- `Transcriber` precomputes `long_keys` (dictionary keys ≥ 4 chars used for word splitting) once in `__init__`. Previously this was rebuilt from the 125k-word dictionary on every call.

### Added
- `scripts/build_rules.py` — compiles DSL rules and phonetic normalizations into `.pkl`.
- `scripts/benchmark.py` — measures cold start, per-word throughput, and lru_cache effects.

### Removed
- **Breaking:** `Transcriber.reload_rules()`, `reload_dictionary()`, `reload_all()`, and `clear_cache()` — resources are loaded once in `__init__`; create a new `Transcriber` to pick up changed files.
- **Breaking:** `Transcriber.get_vocabulary()` — access `_merged_vocabulary` directly if needed.
- `platformdirs` dependency — no more user cache directory.
- JSON rule cache logic in `Transcriber`.

### Performance
- Transcription throughput improved from ~65 words/sec to **~14,500 words/sec** on unique words (≈220× faster).
- Repeated words benefit further from `lru_cache` in `rule_based_ipa` — up to **~18,000 calls/sec**.
- Cold start remains ~100 ms (pickle loading only).


## [0.2.3] - 2026-10-31

### Changed
- `Transcriber` loads rules and dictionary in `__init__` instead of on first `transcribe()`. If bundled data is missing or corrupt, construction now fails immediately — previously the error surfaced only when `transcribe()` was called.
- `repr(Transcriber())` reports resource counts instead of load status.
- `clear_cache()` recompiles rules right after deleting the on-disk JSON caches, so in-memory and on-disk state stay in sync.

## [0.2.2] - 2026-08-02

### Documentation
- Documentation-only release, version bumped to publish updated docs on PyPI. No code changes.

## [0.2.1] - 2026-06-27

### Changed
- Replaced `gruut` library with built-in rule-based transcription engine
- Built-in dictionary converted from text format to pickle for faster loading

### Performance
- Significantly faster library startup (no external dependency loading)
- Dictionary loading time reduced from ~200-400ms to ~20-50ms
- More accurate English-to-IPA transcription with custom rules

### Removed
- `gruut` dependency (no longer needed)

## [0.2.0] - 2026-06-20

### Removed
- Dynamic vocabulary API: `add_exception()` and `remove_exception()` methods
- `custom_exceptions` parameter from `Transcriber.transcribe()` method

### Changed
- **Breaking:** `custom_exceptions` parameter renamed to `custom_vocabulary` in `Transcriber.__init__`
- Custom vocabulary is now **static** — set once at object creation, cannot be modified at runtime
- For different vocabulary overrides, create separate `Transcriber` instances

### Documentation
- Added `docs/` folder with `ARCHITECTURE.md`, `CONTRIBUTING.md`, and `DSL.md`
- Added Russian translation of README (`README.ru.md`)
- Added DSL reference guide for transliteration rules

### Migration Guide

**Before (0.1.1):**
```python
t = Transcriber()
t.transcribe("text", custom_exceptions={"kubernetes": "ˈkuːbərˌnɛtɪs"})
```

**After (0.2.0):**
```python
t = Transcriber(custom_vocabulary={"kubernetes": "ˈkuːbərˌnɛtɪs"})
t.transcribe("text")
```

## [0.1.1] - 2026-06-XX

> **Note:** Details for this release were not preserved.

## [0.1.0] - 2026-06-XX

### Added
- Initial release
- Hybrid transcription engine (built-in dictionary + `gruut` fallback)
- IPA-to-Cyrillic transliteration via compiled rules
- Built-in dictionary with 120k+ English words
- Custom vocabulary support via `custom_exceptions` parameter
- Lazy loading of `gruut` for faster startup
- Rule caching in `user_cache_dir`
