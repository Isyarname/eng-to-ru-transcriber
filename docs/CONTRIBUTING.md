# Contributing Guide

Thank you for your interest in contributing to eng-to-ru-transcriber!

## 🚀 Development setup

```bash
git clone https://github.com/Isyarname/eng-to-ru-transcriber
cd eng-to-ru-transcriber
pip install -e ".[dev]"
```

The `-e` flag installs the package in editable mode, so changes to Python source files are immediately visible without reinstalling.

## 🧪 Running tests

```bash
python -m pytest tests/ -v
```

All tests must pass before submitting a PR.

## 📝 Changing rules

Runtime rule data is compiled ahead of time into `.pkl` files. Source rules are stored in `data_src/` and are not used directly at runtime.

To change transliteration or transcription rules:

1. Edit the relevant source file under `data_src/`, for example `data_src/transliteration_rules.py`.
2. Rebuild the compiled rule data:

```bash
python scripts/build_rules.py
```

3. Create a new `Transcriber` instance or restart your process so the updated compiled data is loaded.

With an editable installation, reinstalling the package after rebuilding is not required.

4. Run the tests:

```bash
python -m pytest
```

Do not edit generated `.pkl` files by hand. If the repository tracks the generated files, commit them together with the source changes.

## 📖 Updating the dictionary

The source dictionary is stored as a plain text file and compiled into a pickle for faster loading.

1. Edit `data_src/en_dict.txt` using the existing format:

```text
word<TAB>IPA_transcription
```

2. Regenerate the dictionary data:

```bash
python scripts/convert_dict.py
```

3. Create a new `Transcriber` instance or restart your process.
4. Run the tests:

```bash
python -m pytest
```

## 🔀 Git workflow

1. Create a branch for your changes:

```bash
git checkout -b feature/add-th-rule
```

2. Make your changes and commit:

```bash
git add .
git commit -m "Add θ → с transliteration rule"
```

3. Push to your fork:

```bash
git push origin feature/add-th-rule
```

4. Open a Pull Request on GitHub.

## 📋 Pull request checklist

Before submitting your PR, make sure:

- [ ] Tests pass: `python -m pytest`
- [ ] Code follows the existing style
- [ ] Compiled data is regenerated if source rules or dictionary data changed
- [ ] Added tests for new functionality (if applicable)
- [ ] Updated documentation (if applicable)
- [ ] PR description explains what changed and why

## 🐛 Reporting issues

If you find a bug or have a feature request:

1. Check existing issues to avoid duplicates.
2. Create a new issue with:
   - a clear description;
   - steps to reproduce (for bugs);
   - expected vs actual behavior;
   - Python version and OS.

Thank you for contributing! 🎉