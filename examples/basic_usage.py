"""Пример использования библиотеки."""
from __future__ import annotations

from pathlib import Path

from eng_to_ru_transcriber import Transcriber


EXAMPLES_DIR = Path(__file__).parent
TEXT_PATH = EXAMPLES_DIR / "text.txt"
OUTPUT_PATH = Path.cwd() / "output_text.txt"


def run_pipeline() -> None:
    if not TEXT_PATH.exists():
        print(f"❌ Файл не найден: {TEXT_PATH}")
        return

    raw_text = TEXT_PATH.read_text(encoding="utf-8")

    # Создаём объект с пользовательскими исключениями
    custom = {
        "python": "ˈpaɪθɑn",
        "docker": "ˈdɑkər",
    }
    t = Transcriber(custom_exceptions=custom)
    print(f"📦 Создан: {t}")

    t.reload_transliteration()
    result = t.transcribe(raw_text)
    print(f"📦 После транслитерации: {t}")

    print("\n✅ Результат (RU):")
    print(result)

    OUTPUT_PATH.write_text(result, encoding="utf-8")
    print(f"\n💾 Сохранено в: {OUTPUT_PATH}")


if __name__ == "__main__":
    run_pipeline()