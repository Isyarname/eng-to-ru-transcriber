# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
