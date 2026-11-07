"""Общие fixtures для всех тестов."""
import sys
from pathlib import Path

import pytest

# Добавляем папку scripts в sys.path, чтобы тесты могли импортировать dsl_translator
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


@pytest.fixture
def sample_rules():
    """Простой набор правил для тестов."""
    return [
        ("a", "x"),
        ("b", "y"),
        ("c", "z"),
    ]


@pytest.fixture
def sample_ipa_text():
    """Пример IPA-текста."""
    return "hɛˈloʊ wɝːld"
