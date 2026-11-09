"""Бенчмарк: eng_to_ipa_hybrid vs eng_to_ipa vs g2p_en vs epitran.

Все движки приводятся к IPA:
  - eng_to_ipa_hybrid  → IPA (нативно)
  - eng_to_ipa         → IPA (нативно)
  - g2p_en             → ARPAbet → IPA (конвертер в этом файле)
  - epitran            → IPA (нативно)

Запуск:
    py benchmark_ipa_engines.py
    py benchmark_ipa_engines.py --text examples/text.txt
    py benchmark_ipa_engines.py --words skibidi rizz delulu doomscrolling
    py benchmark_ipa_engines.py --rounds 10
"""
import argparse
import re
import statistics
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_TEXT = PROJECT_ROOT / "examples" / "text.txt"


# ─────────────────────────── ARPAbet → IPA ───────────────────────────

ARPABET_TO_IPA = {
    # Гласные
    "AA": "ɑ", "AE": "æ", "AH": "ʌ", "AO": "ɔ", "AW": "aʊ",
    "AY": "aɪ", "EH": "ɛ", "ER": "ɝ", "EY": "eɪ", "IH": "ɪ",
    "IY": "i", "OW": "oʊ", "OY": "ɔɪ", "UH": "ʊ", "UW": "u",
    # Согласные
    "B": "b", "CH": "tʃ", "D": "d", "DH": "ð", "F": "f",
    "G": "ɡ", "HH": "h", "JH": "dʒ", "K": "k", "L": "l",
    "M": "m", "N": "n", "NG": "ŋ", "P": "p", "R": "ɹ",
    "S": "s", "SH": "ʃ", "T": "t", "TH": "θ", "V": "v",
    "W": "w", "Y": "j", "Z": "z", "ZH": "ʒ",
}


def arpabet_to_ipa(arpabet: str) -> str:
    """Конвертирует строку ARPAbet (с цифрами ударения) в строку IPA."""
    phones = arpabet.split()
    out = []

    for phone in phones:
        if not phone:
            continue

        stress = None
        if phone[-1].isdigit():
            stress = phone[-1]
            base = phone[:-1]
        else:
            base = phone

        ipa = ARPABET_TO_IPA.get(base, base)

        # Безударный AH редуцируется в шву
        if base == "AH" and stress == "0":
            ipa = "ə"
        # Безударный ER — тоже шва с r-окраской
        elif base == "ER" and stress == "0":
            ipa = "ɚ"

        if stress == "1":
            ipa = "ˈ" + ipa
        elif stress == "2":
            ipa = "ˌ" + ipa

        out.append(ipa)

    return "".join(out)


# ─────────────────────────── Загрузка текста ───────────────────────────

def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z']+", text)


# ─────────────────────────── Инициализация движков ───────────────────────────

def init_our_hybrid():
    """Наш движок: словарь + правила EN → IPA."""
    from eng_to_ru_transcriber import Transcriber
    from eng_to_ru_transcriber.eng_to_ipa_hybrid import transcribe as hybrid_transcribe

    t = Transcriber()

    def fn(word: str) -> str:
        return hybrid_transcribe(
            word,
            t._merged_vocabulary,
            t._long_keys,
            t._eng_to_ipa_rules,
            t._substring_norms,
            t._word_norms,
        )

    return fn


def init_eng_to_ipa():
    """Библиотека eng_to_ipa (CMUdict). Возвращает IPA."""
    import eng_to_ipa as ipa

    def fn(word: str) -> str:
        # convert() возвращает строку; OOV-слова помечает звёздочками
        return ipa.convert(word, stress_marks="both")

    return fn


def init_g2p_en():
    """Нейросетевой G2P. Возвращает ARPAbet, конвертируем в IPA."""
    from g2p_en import G2p

    g2p = G2p()

    def fn(word: str) -> str:
        phones = g2p(word)
        # g2p возвращает список строк вида ["HH", "AH0", "V"]
        return arpabet_to_ipa(" ".join(phones))

    return fn


def init_epitran():
    """Epitran через Flite. Возвращает IPA. Требует системный flite."""
    import epitran
    epi = epitran.Epitran("eng-Latn")

    def fn(word: str) -> str:
        return epi.transliterate(word)

    return fn


# ─────────────────────────── Замеры ───────────────────────────

def measure_init(factory, name: str) -> tuple[float | None, object | None]:
    """Замеряет время инициализации движка."""
    start = time.perf_counter()
    try:
        fn = factory()
        init_ms = (time.perf_counter() - start) * 1000
        return init_ms, fn
    except Exception as e:
        print(f"⚠  {name}: не удалось инициализировать — {type(e).__name__}: {e}")
        return None, None


def benchmark(fn, words: list[str], rounds: int, warmup: int = 2) -> dict:
    """Замеряет скорость на списке слов. Возвращает метрики."""
    # Прогрев
    for _ in range(warmup):
        for w in words:
            try:
                fn(w)
            except Exception:
                pass

    times = []
    errors = 0
    for _ in range(rounds):
        start = time.perf_counter()
        for w in words:
            try:
                fn(w)
            except Exception:
                errors += 1
        times.append(time.perf_counter() - start)

    median = statistics.median(times)
    return {
        "median_sec": median,
        "ms_per_word": median / len(words) * 1000,
        "words_per_sec": len(words) / median,
        "errors": errors,
    }


# ─────────────────────────── Вывод ───────────────────────────

def print_speed_table(results: dict, n_words: int, rounds: int) -> None:
    print("\n" + "=" * 100)
    print(f"СКОРОСТЬ: {n_words} слов, {rounds} раундов")
    print("=" * 100)

    header = f"{'Движок':22} {'Init':>10} {'мс/слово':>12} {'слов/сек':>12} {'ошибок':>8}"
    print(header)
    print("-" * 100)

    for name, data in results.items():
        if data.get("fn") is None:
            print(f"{name:22} {'—':>10} {'—':>12} {'—':>12} {'—':>8}  (недоступен)")
            continue

        init_ms = data.get("init_ms")
        init_str = f"{init_ms:.0f} мс" if init_ms is not None else "—"
        m = data.get("metrics", {})
        print(
            f"{name:22} {init_str:>10} "
            f"{m.get('ms_per_word', 0):>10.3f} "
            f"{m.get('words_per_sec', 0):>10.0f} "
            f"{m.get('errors', 0):>8}"
        )

    print("=" * 100)


def print_quality_table(engines: dict, words: list[str]) -> None:
    """Показывает вывод всех движков для нескольких слов."""
    print("\n" + "=" * 100)
    print("КАЧЕСТВО: как каждый движок обрабатывает слово")
    print("=" * 100)

    col_w = 22
    print(f"{'Слово':14}" + "".join(f"{name:^{col_w}}" for name in engines))
    print("-" * 100)

    for word in words:
        row = f"{word:14}"
        for name, fn in engines.items():
            if fn is None:
                row += f"{'—':^{col_w}}"
                continue
            try:
                out = fn(word)
                # OOV в eng_to_ipa помечается звёздочками — оставляем как индикатор
                row += f"{out[:col_w - 2]:^{col_w}}"
            except Exception:
                row += f"{'ERR':^{col_w}}"
        print(row)

    print("=" * 100)


def print_agreement(engines: dict, words: list[str], reference: str = "our_hybrid") -> None:
    """Считает, насколько часто движки совпадают с референсным."""
    print("\n" + "=" * 100)
    print(f"СОГЛАСИЕ с {reference} (посимвольно, на {len(words)} словах)")
    print("=" * 100)

    ref_fn = engines.get(reference)
    if ref_fn is None:
        print("Референсный движок недоступен.")
        return

    def safe(fn, w):
        try:
            return fn(w)
        except Exception:
            return None

    ref_outputs = [safe(ref_fn, w) for w in words]

    for name, fn in engines.items():
        if name == reference or fn is None:
            continue

        matches = 0
        total = 0
        for w, ref_out in zip(words, ref_outputs):
            if ref_out is None:
                continue
            out = safe(fn, w)
            if out is None:
                continue
            total += 1
            if out == ref_out:
                matches += 1

        if total == 0:
            print(f"  {name:22}: нет данных")
            continue

        pct = matches / total * 100
        print(f"  {name:22}: {matches}/{total} ({pct:.1f}%)")

    print("=" * 100)


# ─────────────────────────── Главная ───────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="IPA engines benchmark")
    parser.add_argument("--text", type=Path, default=DEFAULT_TEXT)
    parser.add_argument("--words", nargs="+", default=None,
                        help="Список слов вместо чтения из файла")
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--show", type=int, default=8,
                        help="Сколько слов показать в таблице качества")
    args = parser.parse_args()

    if args.words:
        words = args.words
    else:
        words = tokenize(load_text(args.text))

    if not words:
        print("❌ Нет слов для бенчмарка")
        return

    print(f"Загружено слов: {len(words)}")
    print(f"Первые 5: {words[:5]}")

    # Инициализация
    print("\nИнициализация движков...")
    engines: dict[str, object] = {}
    results: dict[str, dict] = {}

    for name, factory in [
        ("our_hybrid", init_our_hybrid),
        ("eng_to_ipa", init_eng_to_ipa),
        ("g2p_en", init_g2p_en),
        ("epitran", init_epitran),
    ]:
        init_ms, fn = measure_init(factory, name)
        engines[name] = fn
        results[name] = {"init_ms": init_ms, "fn": fn}

    # Замеры
    print("\nЗамеры скорости...")
    for name, data in results.items():
        if data["fn"] is None:
            continue
        data["metrics"] = benchmark(data["fn"], words, args.rounds)

    # Вывод
    print_speed_table(results, len(words), args.rounds)

    sample = words[: args.show]
    print_quality_table(engines, sample)

    # Согласие считаем на всех словах (или на первых 100, если слов много)
    agreement_words = words[:100]
    print_agreement(engines, agreement_words)


if __name__ == "__main__":
    main()
