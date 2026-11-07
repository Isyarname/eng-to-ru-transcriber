"""Компилятор DSL-правил и фонетических нормализаций в pickle."""
import pickle
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec

# Прямой импорт: файл лежит в этой же папке (scripts/)
from dsl_translator import build_rules

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_SRC = PROJECT_ROOT / "data_src"
DATA_DIR = PROJECT_ROOT / "src" / "eng_to_ru_transcriber" / "data"


def compile_dsl_rules(source_file: Path, output_file: Path) -> None:
    if not source_file.exists():
        print(f"❌ Исходник не найден: {source_file}")
        return

    spec = spec_from_file_location("rules_module", str(source_file))
    module = module_from_spec(spec)
    spec.loader.exec_module(module)

    raw_macros = getattr(module, "macros", {})
    raw_rules = getattr(module, "rules", "")

    compiled = build_rules(raw_rules, raw_macros)

    with open(output_file, "wb") as f:
        pickle.dump(compiled, f, protocol=pickle.HIGHEST_PROTOCOL)

    print(f"✅ {source_file.name} → {output_file.name} ({len(compiled)} правил)")


def compile_normalizations(source_file: Path, output_file: Path) -> None:
    if not source_file.exists():
        print(f"❌ Исходник не найден: {source_file}")
        return

    spec = spec_from_file_location("norm_module", str(source_file))
    module = module_from_spec(spec)
    spec.loader.exec_module(module)

    substring_norms = getattr(module, "SUBSTRING_NORMALIZATIONS", [])
    word_norms = getattr(module, "WORD_NORMALIZATIONS", {})

    data = (substring_norms, word_norms)

    with open(output_file, "wb") as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

    print(
        f"✅ {source_file.name} → {output_file.name} "
        f"({len(substring_norms)} подстрочных, {len(word_norms)} словарных)"
    )


if __name__ == "__main__":
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    compile_dsl_rules(
        DATA_SRC / "transliteration_rules.py",
        DATA_DIR / "transliteration_rules.pkl",
    )
    compile_dsl_rules(
        DATA_SRC / "eng_to_ipa_rules.py",
        DATA_DIR / "eng_to_ipa_rules.pkl",
    )
    compile_normalizations(
        DATA_SRC / "phonetic_normalizations.py",
        DATA_DIR / "phonetic_normalizations.pkl",
    )
