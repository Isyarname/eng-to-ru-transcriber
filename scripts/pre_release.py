"""Pre-release check: проверка и подготовка к сборке пакета.

Запуск:
    py scripts/pre_release.py                 # стандартная проверка + очистка + тесты
    py scripts/pre_release.py --rebuild       # + пересобрать .pkl из data_src/
    py scripts/pre_release.py --no-test       # пропустить тесты
    py scripts/pre_release.py --no-clean      # не чистить dist/ и кэш
    py scripts/pre_release.py --no-reinstall  # не переустанавливать пакет
    py scripts/pre_release.py --strict        # предупреждения становятся ошибками
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_SRC = PROJECT_ROOT / "data_src"
DATA_PKL = PROJECT_ROOT / "src" / "eng_to_ru_transcriber" / "data"
INIT_FILE = PROJECT_ROOT / "src" / "eng_to_ru_transcriber" / "__init__.py"
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
CHANGELOG = PROJECT_ROOT / "docs" / "CHANGELOG.md"
DIST_DIR = PROJECT_ROOT / "dist"

# Источник в data_src/ → артефакт в src/.../data/
RULES_MAP = {
    "en_dict.txt": "en_dict.pkl",
    "transliteration_rules.py": "transliteration_rules.pkl",
    "eng_to_ipa_rules.py": "eng_to_ipa_rules.pkl",
    "phonetic_normalizations.py": "phonetic_normalizations.pkl",
}

README_FILES = ["README.md", "README.ru.md"]


# ─────────────────────────── Утилиты ───────────────────────────

def _ok(msg: str) -> None:
    print(f"✅ {msg}")


def _warn(msg: str) -> None:
    print(f"⚠  {msg}")


def _err(msg: str) -> None:
    print(f"❌ {msg}")


def _run(cmd: list[str], cwd: Path = PROJECT_ROOT) -> int:
    return subprocess.run(cmd, cwd=cwd).returncode


# ─────────────────────────── Проверки ───────────────────────────

def get_version_from_pyproject() -> str:
    content = PYPROJECT.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if not match:
        raise ValueError("version not found in pyproject.toml")
    return match.group(1)


def get_version_from_init() -> str:
    """Читает __version__ через реальный импорт (учитывает importlib.metadata)."""
    src = PROJECT_ROOT / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

    # Сбрасываем закэшированный модуль, чтобы подхватить свежий __init__.py
    if "eng_to_ru_transcriber" in sys.modules:
        del sys.modules["eng_to_ru_transcriber"]
    for key in list(sys.modules.keys()):
        if key.startswith("eng_to_ru_transcriber."):
            del sys.modules[key]

    import eng_to_ru_transcriber
    return eng_to_ru_transcriber.__version__


def check_versions() -> tuple[bool, str | None]:
    try:
        pyproject_v = get_version_from_pyproject()
        init_v = get_version_from_init()
    except (ValueError, FileNotFoundError) as e:
        _err(f"Не удалось прочитать версию: {e}")
        return False, None
    if pyproject_v != init_v:
        _err(f"Версии не совпадают: pyproject.toml={pyproject_v}, __init__.py={init_v}")
        return False, None
    _ok(f"Версия: {pyproject_v}")
    return True, pyproject_v


def check_rules_compiled() -> bool:
    """Проверяет, что .pkl существуют и новее своих источников."""
    ok = True
    for src_name, pkl_name in RULES_MAP.items():
        src = DATA_SRC / src_name
        pkl = DATA_PKL / pkl_name
        if not src.exists():
            _err(f"Нет источника: {src}")
            ok = False
            continue
        if not pkl.exists():
            _err(f"Нет .pkl: {pkl}")
            ok = False
            continue
        if pkl.stat().st_mtime < src.stat().st_mtime:
            _warn(f"{pkl_name} старше {src_name} — .pkl устарел")
            ok = False
    if ok:
        _ok(f"Все .pkl актуальны ({len(RULES_MAP)} шт.)")
    return ok


def check_changelog(version: str) -> bool:
    """CHANGELOG.md должен содержать запись для текущей версии."""
    if not CHANGELOG.exists():
        _err(f"Нет файла: {CHANGELOG}")
        return False
    content = CHANGELOG.read_text(encoding="utf-8")
    pattern = rf"^##\s*\[{re.escape(version)}\]"
    if not re.search(pattern, content, re.MULTILINE):
        _err(f"В CHANGELOG.md нет записи для версии {version}")
        print(f"   Добавь блок: ## [{version}] - YYYY-MM-DD")
        return False
    _ok(f"CHANGELOG содержит запись для {version}")
    return True


def check_readme() -> bool:
    """README файлы существуют и не пустые."""
    ok = True
    for name in README_FILES:
        path = PROJECT_ROOT / name
        if not path.exists():
            _warn(f"Нет файла: {name}")
            ok = False
        elif path.stat().st_size < 100:
            _warn(f"{name} подозрительно короткий ({path.stat().st_size} байт)")
            ok = False
    if ok:
        _ok("README файлы на месте")
    return ok


def check_git_clean() -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=PROJECT_ROOT, capture_output=True, text=True
    )
    dirty = result.stdout.strip()
    if dirty:
        _warn("Незакоммиченные изменения:")
        for line in dirty.splitlines():
            print(f"    {line}")
        return False
    _ok("Git чист")
    return True


# ─────────────────────────── Действия ───────────────────────────

def clean_dist() -> None:
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
        _ok("Удалено: dist/")
    else:
        _ok("dist/ не существовал")


def clean_cache() -> None:
    count = 0
    for p in PROJECT_ROOT.rglob("__pycache__"):
        shutil.rmtree(p, ignore_errors=True)
        count += 1
    for p in PROJECT_ROOT.rglob("*.pyc"):
        try:
            p.unlink()
            count += 1
        except FileNotFoundError:
            pass
    _ok(f"Удалено кэш-файлов: {count}")


def rebuild_rules() -> bool:
    print("🔨 Пересборка .pkl из data_src/...")
    for script in ["build_rules.py", "convert_dict.py"]:
        print(f"   → scripts/{script}")
        if _run([sys.executable, f"scripts/{script}"]) != 0:
            _err(f"{script} упал")
            return False
    return True


def reinstall_editable() -> bool:
    """Обновляет метаданные пакета (чтобы importlib.metadata видел новую версию)."""
    print("📦 Переустановка в editable-режиме...")
    return _run([sys.executable, "-m", "pip", "install", "-e", ".", "--quiet"]) == 0


def run_tests() -> bool:
    print("🧪 Запуск тестов...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        # Вытаскиваем "N passed" из последней непустой строки
        summary = ""
        for line in reversed(result.stdout.strip().splitlines()):
            if "passed" in line or "failed" in line:
                summary = line.strip()
                break
        _ok(f"Тесты прошли: {summary}" if summary else "Тесты прошли")
        return True

    # Упали — показываем всё, что pytest напечатал
    _err("Тесты упали:")
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return False


# ─────────────────────────── Главная ───────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Pre-release check")
    parser.add_argument("--rebuild", action="store_true", help="Пересобрать .pkl из data_src/")
    parser.add_argument("--no-clean", action="store_true", help="Не чистить dist/ и кэш")
    parser.add_argument("--no-test", action="store_true", help="Не запускать тесты")
    parser.add_argument("--no-reinstall", action="store_true", help="Не переустанавливать пакет")
    parser.add_argument("--strict", action="store_true", help="Предупреждения становятся ошибками")
    args = parser.parse_args()

    print("=" * 60)
    print("PRE-RELEASE CHECK")
    print("=" * 60)

    # 1. (Опционально) пересборка .pkl
    if args.rebuild:
        if not rebuild_rules():
            sys.exit(1)

    # 2. Очистка кэша и dist
    if not args.no_clean:
        clean_dist()
        clean_cache()

    # 3. Переустановка пакета (чтобы importlib.metadata / кэш подхватили новую версию)
    if not args.no_reinstall:
        if not reinstall_editable():
            _err("Не удалось переустановить пакет")
            sys.exit(1)
        _ok("Пакет переустановлен")

    # 4. Проверка версий (теперь они точно синхронизированы)
    ok, version = check_versions()
    if not ok or version is None:
        sys.exit(1)

    # 5. .pkl актуальны
    if not check_rules_compiled():
        print("\nПодсказка: запусти с --rebuild, чтобы пересобрать .pkl автоматически")
        sys.exit(1)

    # 6. CHANGELOG содержит запись для версии
    if not check_changelog(version):
        sys.exit(1)

    # 7. README (warn или fail в strict)
    readme_ok = check_readme()
    if not readme_ok and args.strict:
        _err("README проверка упала (--strict)")
        sys.exit(1)

    # 8. Git status (warn или fail в strict)
    git_ok = check_git_clean()
    if not git_ok and args.strict:
        _err("Git содержит незакоммиченные изменения (--strict)")
        sys.exit(1)
    if not git_ok:
        print("   ⚠️  Сборка возможна, но код в git не совпадает с тем, что уйдёт на PyPI.")

    # 9. Тесты
    if not args.no_test:
        if not run_tests():
            _err("Тесты упали")
            sys.exit(1)

    print()
    print("=" * 60)
    print("✅ ГОТОВО К СБОРКЕ")
    print("=" * 60)
    print("Следующие шаги:")
    print("  py -m build")
    print("  py -m twine check dist/*")
    print("  py -m twine upload dist/*")


if __name__ == "__main__":
    main()
