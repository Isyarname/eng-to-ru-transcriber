import json
import importlib.util
from pathlib import Path
import eng_to_ipa_hybrid as eng_to_ipa
import ipa_to_ru

# Вычисляем корень проекта относительно папки src/
BASE_DIR = Path(__file__).resolve().parent.parent

def _build_rules_infrastructure(py_path: Path, json_path: Path) -> list:
    """Внутренняя функция для динамической сборки инфраструктуры правил."""
    import compiler
    if not py_path.exists():
        raise FileNotFoundError(f"Файл исходных правил не найден: {py_path}")
        
    spec = importlib.util.spec_from_file_location("rules_module", str(py_path))
    rules_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rules_module)
    
    raw_contractions = getattr(rules_module, "contractions", {})
    raw_rules_string = getattr(rules_module, "rules", "")
    
    prepared_rules = compiler.compile(raw_rules_string, raw_contractions)
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(prepared_rules, f, ensure_ascii=False, indent=4)
        
    return prepared_rules


def _parse_ipa_dictionary(dict_path: Path) -> dict:
    """Внутренняя функция для парсинга сырого словаря в хэш-таблицу."""
    if not dict_path.exists():
        raise FileNotFoundError(f"Локальный словарь не найден: {dict_path}")
        
    ipa_dict = {}
    with open(dict_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
                
            parts = line.split("\t")
            if len(parts) == 2:
                word, ipa_val = parts
                word = word.strip()
                ipa_val = ipa_val.strip().strip("/")
                
                if "," in ipa_val:
                    ipa_val = ipa_val.split(",")[0].strip()
                
                if word not in ipa_dict:
                    ipa_dict[word] = ipa_val
    return ipa_dict


def convert(text: str, custom_exceptions: dict = None, compiled_rules: list = None) -> str:
    """
    Универсальная функция транслитерации английского текста в кириллицу.
    
    Выполняет чистые вычисления в памяти, если переданы готовые структуры.
    Если параметры равны None, лениво собирает инфраструктуру и читает файлы с диска.
    """
    # === Подготовка правил (Ленивая инициализация и кэширование) ===
    if compiled_rules is None:
        RULES_JSON_PATH = BASE_DIR / "compiled_rules.json"
        RULES_PY_PATH = BASE_DIR / "data" / "ipa_to_ru_rules.py"
        
        if not RULES_JSON_PATH.exists():
            compiled_rules = _build_rules_infrastructure(RULES_PY_PATH, RULES_JSON_PATH)
        else:
            with open(RULES_JSON_PATH, "r", encoding="utf-8") as f:
                compiled_rules = json.load(f)

    # === Подготовка словаря исключений ===
    if custom_exceptions is None:
        DICT_PATH = BASE_DIR / "data" / "en_US.txt"
        custom_exceptions = _parse_ipa_dictionary(DICT_PATH)

    # === Вычислительное ядро ===
    # 1. English -> IPA
    ipa_text = eng_to_ipa.transcribe(text, custom_exceptions)
    print("🔊 IPA транскрипция:\n", ipa_text, "\n")
    
    # 2. IPA -> RU
    ru_text = ipa_to_ru.convert(ipa_text, compiled_rules)
    
    return ru_text
