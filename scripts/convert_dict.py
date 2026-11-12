"""Конвертер словаря IPA-исключений из txt в pickle."""
import pickle
import time
from pathlib import Path

# Пути относительно корня проекта
PROJECT_ROOT = Path(__file__).parent.parent
DICT_TXT = PROJECT_ROOT / "data_src" / "en_dict.txt"
DICT_PKL = PROJECT_ROOT / "src" / "eng_to_ru_transcriber" / "data" / "en_dict.pkl"


def convert():
    if not DICT_TXT.exists():
        print(f"❌ Файл не найден: {DICT_TXT}")
        return

    print(f"📖 Читаю {DICT_TXT}...")
    start = time.perf_counter()

    ipa_dict: dict[str, str] = {}
    with open(DICT_TXT, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line[0] == "#":
                continue
            parts = line.split("\t", 1)
            if len(parts) == 2:
                word = parts[0].strip()
                ipa_val = parts[1].replace("/", "").split(",")[0].strip()
                if word not in ipa_dict:
                    ipa_dict[word] = ipa_val

    print(f"✅ Распарсено слов: {len(ipa_dict)} за {(time.perf_counter() - start)*1000:.1f} мс")

    with open(DICT_PKL, "wb") as f:
        pickle.dump(ipa_dict, f, protocol=pickle.HIGHEST_PROTOCOL)

    size_kb = DICT_PKL.stat().st_size / 1024
    print(f"💾 Сохранено: {DICT_PKL} ({size_kb:.1f} КБ)")

    # Проверка скорости загрузки
    start = time.perf_counter()
    with open(DICT_PKL, "rb") as f:
        test_dict = pickle.load(f)
    elapsed = time.perf_counter() - start
    print(f"⚡ Загрузка pkl: {elapsed*1000:.1f} мс")


if __name__ == "__main__":
    convert()
