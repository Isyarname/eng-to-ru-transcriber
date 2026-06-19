# Contributing Guide

Thank you for your interest in contributing to eng-to-ru-transcriber!

## 🚀 Development Setup

```bash
git clone https://github.com/Isyarname/eng-to-ru-transcriber
cd eng-to-ru-transcriber
pip install -e ".[dev]"
```

The `-e` flag installs the package in editable mode, so changes to the source code are immediately reflected without reinstalling.

## 🧪 Running Tests

```bash
pytest tests/ -v
```

All tests must pass before submitting a PR.

## 📝 How to Add a New Transliteration Rule

1. Open `src/eng_to_ru_transcriber/data/transliteration_rules.py`
2. Add your rule in the format `source -> result`:
   ```python
   rules = """
   # Existing rules...
   θ -> с
   ð -> з
   """
   ```
3. Reload rules in your code:
   ```python
   from eng_to_ru_transcriber import Transcriber
   
   t = Transcriber()
   t.reload_rules()  # Recompiles rules and updates cache
   ```
4. Run tests:
   ```bash
   pytest
   ```
5. Create a PR with a description of the new rule and examples.

## 🔀 Git Workflow

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

## 📋 Pull Request Checklist

Before submitting your PR, make sure:

- [ ] Tests pass: `pytest`
- [ ] Code follows the existing style (4 spaces, type hints)
- [ ] Added tests for new functionality (if applicable)
- [ ] Updated documentation (if applicable)
- [ ] PR description explains what ch

## 🐛 Reporting Issues

If you find a bug or have a feature request:

1. Check existing issues to avoid duplicates
2. Create a new issue with:
   - Clear description
   - Steps to reproduce (for bugs)
   - Expected vs actual behavior
   - Python version and OS

Thank you for contributing! 🎉