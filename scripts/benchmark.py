"""Бенчмарк скорости транскрипции: eng-to-ru-transcriber vs ru-normalizr.

Замеряет:
- время холодного старта (инициализация)
- пропускную способность на уникальных словах
- пропускную способность на реалистичном тексте
- пропускную способность на повторяющихся словах (эффект lru_cache)
- визуальное сравнение результатов

Запуск:
    py scripts/benchmark.py
"""
import argparse
import statistics
import time
import warnings
from dataclasses import dataclass
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

# Реалистичный текст для замера (микс словарных слов, сленга и ников)
SAMPLE_TEXT = """Yesterday my boy read an amazing book about history and today he reads it again.
He usually says that the wind is blowing hard outside but it is impossible to wind up this old clock anyway.
Live and learn! People who live in London like to drink hot tea every day.
hawk tuah ChatGPT cringe vibe ghosting doomscrolling gaslighting rizz skibidi clickbait
microdosing pregame hatewatch unfollow photobomb slowburn standard softlaunch
glowup shadowban brainrot delulu ship textneck overthinker clout neurodivergent
myURL and MacBook software white"""

# Слова для сравнения качества (включая омографы и сленг)
WORDS = [
    "hello", "computer", "London", "Shakespeare", "music",
    "skibidi", "rizz", "delulu", "doomscrolling", "myURL",
    "read", "use", "software", "white"
]

# Повторяющиеся слова (имитация TTS-диалога)
REPEATED_WORDS = ["hello", "the", "you", "friend"] * 100


@dataclass
class SpeedStats:
    times: list[float]
    count: int

    @property
    def median(self) -> float:
        return statistics.median(self.times)

    @property
    def ms_per_call(self) -> float:
        return self.median / self.count * 1000

    @property
    def calls_per_sec(self) -> float:
        return self.count / self.median


def benchmark(fn, args: list, rounds: int = 10, warmup: int = 3) -> SpeedStats:
    """Замеряет время вызова fn(*args) несколько раз."""
    for _ in range(warmup):
        for a in args:
            try:
                fn(a)
            except Exception:
                pass

    times = []
    for _ in range(rounds):
        start = time.perf_counter()
        for a in args:
            try:
                fn(a)
            except Exception:
                pass
        times.append(time.perf_counter() - start)
    return SpeedStats(times, len(args))


def print_speed_comparison(name: str, stats_ours: SpeedStats, stats_ru: SpeedStats | None) -> None:
    print(f"\n--- {name} ({stats_ours.count} вызовов) ---")
    print(f"{'Движок':20} | {'мс/вызов':>10} | {'вызовов/сек':>12}")
    print("-" * 50)
    print(f"{'eng-to-ru':20} | {stats_ours.ms_per_call:>10.3f} | {stats_ours.calls_per_sec:>12.0f}")

    if stats_ru:
        # Считаем ускорение
        speedup = stats_ru.ms_per_call / stats_ours.ms_per_call
        print(f"{'ru-normalizr':20} | {stats_ru.ms_per_call:>10.3f} | {stats_ru.calls_per_sec:>12.0f}")
        print(f"-> eng-to-ru быстрее в {speedup:.1f} раз")


def main() -> None:
    parser = argparse.ArgumentParser(description="Transcription benchmark")
    parser.add_argument("--text", type=Path, default=DEFAULT_TEXT)
    args = parser.parse_args()

    print("=" * 60)
    print("ХОЛОДНЫЙ СТАРТ")
    print("=" * 60)

    # 1. Наш движок
    start = time.perf_counter()
    t_our = Transcriber()
    ms_our = (time.perf_counter() - start) * 1000
    print(f"  eng-to-ru-transcriber : {ms_our:>6.1f} мс   {t_our!r}")

    # 2. ru-normalizr
    t_ru = None
    if HAS_RU_NORMALIZR:
        start = time.perf_counter()
        t_ru = Normalizer(NormalizeOptions.tts(
            latinization_backend="ipa",
            enable_latinization_stress_marks=True,
        ))
        ms_ru = (time.perf_counter() - start) * 1000
        print(f"  ru-normalizr          : {ms_ru:>6.1f} мс")
    else:
        print("  ru-normalizr          : (не установлен)")

    # --- Замеры скорости ---
    stats_our_words = benchmark(t_our.transcribe, WORDS)
    stats_our_text = benchmark(t_our.transcribe, [SAMPLE_TEXT], rounds=5)
    stats_our_rep = benchmark(t_our.transcribe, REPEATED_WORDS)

    if t_ru:
        def norm_ru(text: str) -> str:
            return t_ru.normalize(text)

        stats_ru_words = benchmark(norm_ru, WORDS)
        stats_ru_text = benchmark(norm_ru, [SAMPLE_TEXT], rounds=5)
        stats_ru_rep = benchmark(norm_ru, REPEATED_WORDS)
    else:
        stats_ru_words = stats_ru_text = stats_ru_rep = None

    print("\n" + "=" * 60)
    print("СКОРОСТЬ РАБОТЫ")
    print("=" * 60)

    print_speed_comparison("Уникальные слова", stats_our_words, stats_ru_words)
    print_speed_comparison("Связный текст", stats_our_text, stats_ru_text)
    print_speed_comparison("Повторяющиеся слова (lru_cache)", stats_our_rep, stats_ru_rep)

    # --- Сравнение качества ---
    print("\n" + "=" * 60)
    print("СРАВНЕНИЕ КАЧЕСТВА (на уникальных словах)")
    print("=" * 60)

    if t_ru:
        print(f"{'Слово':15} | {'eng-to-ru':25} | {'ru-normalizr':25}")
        print("-" * 72)
        for w in WORDS:
            res_our = t_our.transcribe(w)
            try:
                res_ru = t_ru.normalize(w)
            except Exception as e:
                res_ru = f"ERR: {e}"

            print(f"{w:15} | {res_our:25} | {res_ru:25}")
    else:
        print("Для сравнения качества установите: pip install ru-normalizr")


if __name__ == "__main__":
    main()
