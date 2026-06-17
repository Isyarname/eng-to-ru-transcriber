import sys
from pathlib import Path

# Константы путей относительно корня проекта
BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"

# Добавляем папку с исходным кодом в пути поиска модулей Python
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

import eng_to_ru

def run_pipeline() -> None:
    """Оркестратор верхнего уровня для консольного запуска."""
    TEXT_PATH = BASE_DIR / "data" / "text.txt"
    OUTPUT_PATH = BASE_DIR / "output_text.txt"
    
    if not TEXT_PATH.exists():
        print(f"❌ Ошибка: Входной файл не найден по пути: {TEXT_PATH}")
        return

    try:
        # Чтение исходного текста
        with open(TEXT_PATH, "r", encoding="utf-8") as f:
            raw_text = f.read()
        
        # Вызов универсальной функции. Она сама лениво загрузит всё необходимое!
        result = eng_to_ru.convert(raw_text)
        
        print("\n✅ Результат транслитерации (RU):")
        print(result)
        
        # Экспорт результатов
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"💾 Результат успешно сохранен в файл: {OUTPUT_PATH.name}")
            
    except Exception as e:
        print(f"❌ Произошла непредвиденная ошибка в главном цикле: {e}")

if __name__ == "__main__":
    run_pipeline()
