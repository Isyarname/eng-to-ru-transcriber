"""Бенчмарк скорости транскрипции: eng-to-ru-transcriber.

Замеряет:
- время холодного старта (инициализация Transcriber)
- пропускную способность на одном слове
- пропускную способность на реалистичном тексте
- пропускную способность на повторяющихся словах (эффект lru_cache)
"""
import statistics
import time
from dataclasses import dataclass

from eng_to_ru_transcriber import Transcriber


# Реалистичный текст для замера (микс словарных слов, сленга и ников)
SAMPLE_TEXT = """Yesterday my boy read an amazing book about history and today he reads it again.
He usually says that the wind is blowing hard outside but it is impossible to wind up this old clock anyway.
Live and learn! People who live in London like to drink hot tea every day.
hawk tuah ChatGPT cringe vibe ghosting doomscrolling gaslighting rizz skibidi clickbait
microdosing pregame hatewatch unfollow photobomb slowburn standard softlaunch
glowup shadowban brainrot delulu ship textneck overthinker clout neurodivergent
myURL and MacBook software white"""

# Слова для замера по одному
WORDS = [
    "hello", "computer", "London", "Shakespeare", "music",
    "skibidi", "rizz", "delulu", "doomscrolling", "myURL",
]

# Повторяющиеся слова (имитация TTS-диалога с персонажем)
REPEATED_WORDS = ["hello", "the", "you", "friend"] * 100


@dataclass
class SpeedStats:
    """Статистика времени выполнения."""
    times: list[float]
    count: int

    @property
    def median(self) -> float:
        return statistics.median(self.times)

    @property
    def mean(self) -> float:
        return statistics.mean(self.times)

    @property
    def min(self) -> float:
        return min(self.times)

    @property
    def max(self) -> float:
        return max(self.times)


def benchmark(fn, args: list, rounds: int = 10, warmup: int = 3) -> SpeedStats:
    """Замеряет время вызова fn(*args) несколько раз."""
    # Прогрев (наполняем lru_cache)
    for _ in range(warmup):
        for a in args:
            fn(a)

    times = []
    for _ in range(rounds):
        start = time.perf_counter()
        for a in args:
            fn(a)
        times.append(time.perf_counter() - start)
    return SpeedStats(times, len(args))


def report(name: str, stats: SpeedStats) -> None:
    print(f"\n{name}")
    print(f"  раундов            : {len(stats.times)}")
    print(f"  всего вызовов      : {len(stats.times) * stats.count}")
    print(f"  время, сек         : min={stats.min:.4f}  median={stats.median:.4f}  mean={stats.mean:.4f}  max={stats.max:.4f}")
    print(f"  на вызов (median)  : {stats.median / stats.count * 1000:.3f} мс")
    print(f"  пропускная способн.: {stats.count / stats.median:.0f} вызовов/сек")


def main() -> None:
    # --- Холодный старт ---
    print("=" * 60)
    print("ХОЛОДНЫЙ СТАРТ")
    print("=" * 60)

    start = time.perf_counter()
    t = Transcriber()
    cold_start_ms = (time.perf_counter() - start) * 1000
    print(f"  Transcriber()      : {cold_start_ms:.1f} мс")
    print(f"  {t!r}")

    # --- Пропускная способность на отдельных словах ---
    print("\n" + "=" * 60)
    print("СКОРОСТЬ: ОТДЕЛЬНЫЕ СЛОВА")
    print("=" * 60)

    stats_words = benchmark(t.transcribe, WORDS)
    report(f"уникальные слова ({len(WORDS)} шт.)", stats_words)

    # --- Пропускная способность на связном тексте ---
    print("\n" + "=" * 60)
    print("СКОРОСТЬ: СВЯЗНЫЙ ТЕКСТ")
    print("=" * 60)

    stats_text = benchmark(t.transcribe, [SAMPLE_TEXT])
    report(f"текст ({len(SAMPLE_TEXT)} символов)", stats_text)

    # --- Эффект lru_cache на повторяющихся словах ---
    print("\n" + "=" * 60)
    print("СКОРОСТЬ: ПОВТОРЯЮЩИЕСЯ СЛОВА (эффект lru_cache)")
    print("=" * 60)

    stats_repeated = benchmark(t.transcribe, REPEATED_WORDS)
    report(f"повторяющиеся слова ({len(REPEATED_WORDS)} вызовов)", stats_repeated)

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
