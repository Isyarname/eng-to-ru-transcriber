"""Бенчмарк: eng-to-ru-transcriber vs ru-normalizr.

Читает examples/text.txt, прогоняет через оба движка и сравнивает результаты.
Для честного сравнения из вывода ru-normalizr удаляются маркеры ударения (+).
"""
import argparse
import statistics
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

from eng_to_ru_transcriber import Transcriber

try:
    from ru_normalizr import Normalizer, NormalizeOptions
    HAS_RU_NORMALIZR = True
except ImportError:
    HAS_RU_NORMALIZR = False

PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_TEXT = PROJECT_ROOT / "examples" / "text.txt"


def benchmark(fn, text: str, rounds: int = 5) -> float:
    """Замеряет время выполнения функции (медиана в мс)."""
    # Прогрев
    for _ in range(2):
        fn(text)

    times = []
    for _ in range(rounds):
        start = time.perf_counter()
        fn(text)
        times.append(time.perf_counter() - start)

    return statistics.median(times) * 1000


def clean_normalizr(text: str) -> str:
    """Убирает маркеры ударения из вывода ru-normalizr для наглядности."""
    return text.replace("+", "").replace("\u0301", "")


def main() -> None:
    parser = argparse.ArgumentParser(description="Text comparison benchmark")
    parser.add_argument("--text", type=Path, default=DEFAULT_TEXT, help="Путь к тексту")
    args = parser.parse_args()

    if not args.text.exists():
        print(f"❌ Файл не найден: {args.text}")
        return

    raw_text = args.text.read_text(encoding="utf-8").strip()
    print(f"Загружен текст ({len(raw_text)} символов).\n")

    # --- 1. Инициализация ---
    print("Инициализация...")
    t_our = Transcriber()

    t_ru = None
    if HAS_RU_NORMALIZR:
        try:
            t_ru = Normalizer(NormalizeOptions.tts(
                latinization_backend="ipa",
                enable_latinization_stress_marks=True,
            ))
        except Exception as e:
            print(f"⚠ Ошибка инициализации ru-normalizr: {e}")

    # --- 2. Замеры скорости ---
    print("\n" + "=" * 60)
    print("СКОРОСТЬ")
    print("=" * 60)

    ms_our = benchmark(t_our.transcribe, raw_text)
    print(f"eng-to-ru-transcriber : {ms_our:.3f} мс")

    if t_ru:
        ms_ru = benchmark(t_ru.normalize, raw_text)
        print(f"ru-normalizr          : {ms_ru:.3f} мс")
        print(f"Ускорение             : {ms_ru / ms_our:.1f}x")

    # --- 3. Сравнение текста ---
    print("\n" + "=" * 60)
    print("СРАВНЕНИЕ ТЕКСТА")
    print("=" * 60)

    res_our = t_our.transcribe(raw_text)
    print("\n[eng-to-ru-transcriber]:")
    print(res_our)

    if t_ru:
        try:
            res_ru = t_ru.normalize(raw_text)
            print("\n[ru-normalizr] (с удаленными '+', но сохраненными ударениями):")
            print(clean_normalizr(res_ru))
        except Exception as e:
            print(f"\n❌ Ошибка выполнения ru-normalizr: {e}")


if __name__ == "__main__":
    main()
