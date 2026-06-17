import sys
import json
import importlib.util
from pathlib import Path

# Константы путей относительно корня проекта
BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"

# Добавляем папку с исходным кодом в пути поиска модулей Python
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

import compiler
import eng_to_ru

def load_text_file(path: Path) -> str:
    """Безопасно читает текстовый файл с диска."""
    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {path.name}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def parse_ipa_dictionary(content: str) -> dict:
    """Парсит сырой текст словаря en_US.txt в хэш-таблицу dict."""
    ipa_dict = {}
    for line in content.splitlines():
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

def build_rules_infrastructure(py_path: Path, json_path: Path) -> bool:
    """Динамически загружает исходный файл правил и компилирует его в JSON-сsnapshot."""
    if not py_path.exists():
        print(f"❌ Ошибка: Файл исходных правил не найден по пути: {py_path}")
        return False
        
    try:
        # Динамическая загрузка модуля с правилами из папки data/
        spec = importlib.util.spec_from_file_location("rules_module", str(py_path))
        rules_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rules_module)
        
        raw_contractions = getattr(rules_module, "contractions", {})
        raw_rules_string = getattr(rules_module, "rules", "")
        
        # Вызов чистой функции компилятора
        prepared_rules = compiler.compile(raw_rules_string, raw_contractions)
        
        # Сохранение промежуточного представления (IR)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(prepared_rules, f, ensure_ascii=False, indent=4)
            
        print(f"✅ Инфраструктура готова! Правила скомпилированы в {json_path.name}")
        return True
    except Exception as e:
        print(f"❌ Критическая ошибка сборки инфраструктуры правил: {e}")
        return False

def save_output_result(result_text: str, output_path: Path) -> None:
    """Записывает итоговый транскрибированный текст в файл."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result_text)
    print(f"💾 Результат успешно сохранен в файл: {output_path.name}")

def run_pipeline() -> None:
    """Оркестратор верхнего уровня: координирует ввод-вывод и логику работы."""
    TEXT_PATH = BASE_DIR / "data" / "text.txt"
    DICT_PATH = BASE_DIR / "data" / "en_US.txt"
    RULES_JSON_PATH = BASE_DIR / "compiled_rules.json"
    RULES_PY_PATH = BASE_DIR / "data" / "ipa_to_ru_rules.py"
    OUTPUT_PATH = BASE_DIR / "output_text.txt"
    
    # 1. Сборка и валидация инфраструктуры правил
    if not RULES_JSON_PATH.exists():
        print(f"⚠️ Файл {RULES_JSON_PATH.name} не найден. Запуск компиляции...")
        if not build_rules_infrastructure(RULES_PY_PATH, RULES_JSON_PATH):
            return

    try:
        # 2. Поэтапное чтение сырых ресурсов
        raw_text = load_text_file(TEXT_PATH)
        raw_dict_content = load_text_file(DICT_PATH)
        
        with open(RULES_JSON_PATH, "r", encoding="utf-8") as f:
            compiled_rules = json.load(f)
            
        # 3. Преобразование сырых строк в рабочие структуры данных
        custom_exceptions = parse_ipa_dictionary(raw_dict_content)
        
        # 4. Запуск чистого вычислительного ядра пайплайна
        result = eng_to_ru.transcribe(raw_text, custom_exceptions, compiled_rules)
        
        print("\n✅ Результат транслитерации (RU):")
        print(result)
        
        # 5. Экспорт результатов
        save_output_result(result, OUTPUT_PATH)
            
    except FileNotFoundError as e:
        print(f"❌ Ошибка ввода-вывода: {e}")
    except Exception as e:
        print(f"❌ Произошла непредвиденная ошибка в главном цикле: {e}")

if __name__ == "__main__":
    run_pipeline()
