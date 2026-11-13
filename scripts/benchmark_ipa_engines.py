"""Бенчмарк: сравнение EN -> IPA движков и их транслитерации в кириллицу.

Все движки приводятся к IPA, затем пропускаются через правила трансляции
из основного пакета (ipa_to_ru).

Запуск:
    py scripts/benchmark_ipa_engines.py
    py scripts/benchmark_ipa_engines.py --rounds 10
"""
import argparse
import re
import statistics
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

from eng_to_ru_transcriber import Transcriber, ipa_to_ru

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


def arpabet_tokens_to_ipa(tokens: list[str]) -> str:
    """Конвертирует список токенов ARPAbet (от g2p_en) в строку IPA, сохраняя пробелы и пунктуацию."""
    out = []
    for token in tokens:
        if token == " ":
            out.append(" ")
        elif not token.isalnum():  # пунктуация (запятые, точки и т.д.)
            out.append(token)
        else:
            # Это фонема, например 'AH0' или 'K'
            stress = None
            if token[-1].isdigit():
                stress = token[-1]
                base = token[:-1]
            else:
                base = token

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



# ─────────────────────────── Инициализация движков ───────────────────────────

def init_our_hybrid():
    """Наш движок: словарь + правила EN → IPA."""
    from eng_to_ru_transcriber.eng_to_ipa_hybrid import transcribe as hybrid_transcribe
    t = Transcriber()

    def fn(text: str) -> str:
        return hybrid_transcribe(
            text,
            t._merged_vocabulary,
            t._long_keys,
            t._eng_to_ipa_rules,
        )

    return fn


def init_eng_to_ipa():
    """Библиотека eng_to_ipa (CMUdict). Возвращает IPA."""
    import eng_to_ipa as ipa

    def fn(text: str) -> str:
        return ipa.convert(text, stress_marks="both")

    return fn


def init_g2p_en():
    """Нейросетевой G2P. Возвращает ARPAbet, конвертируем в IPA."""
    from g2p_en import G2p
    g2p = G2p()

    def fn(text: str) -> str:
        # Передаем строку целиком, чтобы сохранить контекст для омографов
        tokens = g2p(text)
        return arpabet_tokens_to_ipa(tokens)

    return fn


def init_gruut():
    """Gruut: словарь + нейросетевой fallback. Возвращает IPA."""
    from gruut import sentences

    def fn(text: str) -> str:
        words = []
        for sent in sentences(text, lang="en-us"):
            for word in sent:
                if word.phonemes:
                    # Это слово. Убираем лигатуру t͡ʃ -> tʃ и добавляем в список
                    clean = "".join(word.phonemes).replace("͡", "")
                    words.append(clean)
                else:
                    # Это знак препинания (запятая, точка и т.д.)
                    if words:
                        # Приклеиваем пунктуацию прямо к предыдущему слову
                        words[-1] += word.text

        # Теперь у нас список слов (некоторые с запятыми на конце).
        # Склеиваем их через пробел!
        return " ".join(words).strip().replace(" |",",").replace(" ‖",".")

    return fn


def init_epitran():
    """Epitran через Flite. Возвращает IPA. Требует системный flite."""
    import epitran
    epi = epitran.Epitran("eng-Latn")

    def fn(text: str) -> str:
        return epi.transliterate(text)

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


def benchmark(fn, text: str, rounds: int, warmup: int = 2) -> dict:
    """Замеряет скорость на тексте. Возвращает метрики."""
    for _ in range(warmup):
        try:
            fn(text)
        except Exception:
            pass

    times = []
    errors = 0
    for _ in range(rounds):
        start = time.perf_counter()
        try:
            fn(text)
        except Exception:
            errors += 1
        times.append(time.perf_counter() - start)

    median = statistics.median(times)
    return {
        "median_sec": median,
        "ms_per_call": median * 1000,
        "calls_per_sec": 1 / median,
        "errors": errors,
    }


# ─────────────────────────── Вывод ───────────────────────────

def print_speed_table(results: dict, rounds: int) -> None:
    print("\n" + "=" * 100)
    print(f"СКОРОСТЬ: обработка текста ({rounds} раундов)")
    print("=" * 100)

    header = f"{'Движок':22} {'Init':>10} {'мс/текст':>12} {'текстов/сек':>12} {'ошибок':>8}"
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
            f"{m.get('ms_per_call', 0):>10.1f} "
            f"{m.get('calls_per_sec', 0):>12.2f} "
            f"{m.get('errors', 0):>8}"
        )

    print("=" * 100)


def print_results(engines: dict, translit_rules: list, text: str) -> None:
    """Выводит IPA и Кириллицу для каждого движка."""
    print("\n" + "=" * 100)
    print("РЕЗУЛЬТАТЫ (IPA и Транслитерация)")
    print("=" * 100)

    print(f"Входной текст:\n{text}\n")
    print("-" * 100)

    for name, fn in engines.items():
        if fn is None:
            print(f"\n--- {name} ---")
            print("(движок недоступен)\n")
            continue

        try:
            ipa_text = fn(text)
            # Транслитерируем IPA в кириллицу
            cyr_text = ipa_to_ru.convert(ipa_text, translit_rules)

            print(f"\n--- {name} ---")
            print(f"[IPA]:\n{ipa_text}\n")
            print(f"[Кириллица]:\n{cyr_text}\n")

        except Exception as e:
            print(f"\n--- {name} ---")
            print(f"Ошибка при выполнении: {type(e).__name__}: {e}\n")

    print("=" * 100)


# ─────────────────────────── Главная ───────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="IPA engines and transliteration benchmark")
    parser.add_argument("--text", type=Path, default=DEFAULT_TEXT)
    parser.add_argument("--rounds", type=int, default=5)
    args = parser.parse_args()

    if not args.text.exists():
        print(f"❌ Файл не найден: {args.text}")
        return

    raw_text = args.text.read_text(encoding="utf-8").strip()
    print(f"Загружен текст ({len(raw_text)} символов).")

    # Получаем правила транслитерации для дальнейшего использования
    t = Transcriber()
    translit_rules = t._transliteration_rules

    # Инициализация
    print("\nИнициализация движков...")
    engines: dict[str, object] = {}
    results: dict[str, dict] = {}

    for name, factory in [
        ("our_hybrid", init_our_hybrid),
        ("eng_to_ipa", init_eng_to_ipa),
        ("g2p_en", init_g2p_en),
        ("gruut", init_gruut),
        ("epitran", init_epitran),
    ]:
        init_ms, fn = measure_init(factory, name)
        engines[name] = fn
        results[name] = {"init_ms": init_ms, "fn": fn}

    # Замеры скорости
    print("\nЗамеры скорости...")
    for name, data in results.items():
        if data["fn"] is None:
            continue
        data["metrics"] = benchmark(data["fn"], raw_text, args.rounds)

    # Вывод
    print_speed_table(results, args.rounds)
    print_results(engines, translit_rules, raw_text)


if __name__ == "__main__":
    main()
