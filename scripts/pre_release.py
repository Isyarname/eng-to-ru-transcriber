"""Pre-release check: проверка и подготовка к сборке пакета.

Запуск:
    py scripts/pre_release.py
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
PACKAGE_DIR = PROJECT_ROOT / "src" / "eng_to_ru_transcriber"
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
CHANGELOG = PROJECT_ROOT / "docs" / "CHANGELOG.md"
DIST_DIR = PROJECT_ROOT / "dist"

# Модули, без которых импорт transcriber.py не работает.
REQUIRED_MODULES = (
    "transcriber.py",
    "rule_engine.py",
    "dsl_compiler.py",
    "default_adaptation_rules.py",
)

README_FILES = ("README.md", "README.en.md")


def _ok(msg: str) -> None:
    print(f"✅ {msg}")


def _warn(msg: str) -> None:
    print(f"⚠  {msg}")


def _err(msg: str) -> None:
    print(f"❌ {msg}")


def _run(cmd: list[str], cwd: Path = PROJECT_ROOT) -> int:
    return subprocess.run(cmd, cwd=cwd).returncode


def get_version_from_pyproject() -> str:
    content = PYPROJECT.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if not match:
        raise ValueError("version not found in pyproject.toml")
    return match.group(1)


def get_version_from_init() -> str:
    src = PROJECT_ROOT / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

    for key in list(sys.modules.keys()):
        if key == "eng_to_ru_transcriber" or key.startswith("eng_to_ru_transcriber."):
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


def check_rules_source() -> bool:
    """Проверяет, что правила и компилятор на месте и непустые.

    Правила компилируются при импорте transcriber.py, поэтому отсутствие
    любого из этих файлов ломает импорт пакета, а не сборку.
    """
    ok = True
    for name in REQUIRED_MODULES:
        path = PACKAGE_DIR / name
        if not path.exists():
            _err(f"Нет модуля: {path}")
            ok = False
        elif path.stat().st_size == 0:
            _err(f"Пустой модуль: {path}")
            ok = False
    if ok:
        _ok(f"Модули на месте ({len(REQUIRED_MODULES)} шт.)")
    return ok


def check_changelog(version: str) -> bool:
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


def clean_dist() -> None:
    targets = [DIST_DIR, PROJECT_ROOT / "build", *PROJECT_ROOT.rglob("*.egg-info")]
    removed = []

    for path in targets:
        if path.exists():
            shutil.rmtree(path)
            removed.append(path.relative_to(PROJECT_ROOT).as_posix())

    if removed:
        _ok(f"Удалено: {', '.join(removed)}")
    else:
        _ok("Артефакты сборки не найдены")


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


def reinstall_editable() -> bool:
    print("📦 Переустановка в editable-режиме...")
    return _run([sys.executable, "-m", "pip", "install", "-e", ".", "--quiet"]) == 0


def run_example() -> bool:
    print("🚀 Проверка examples/basic_usage.py...")

    example_path = PROJECT_ROOT / "examples" / "basic_usage.py"
    if not example_path.exists():
        _err("Не найден examples/basic_usage.py")
        return False

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    result = subprocess.run(
        [sys.executable, str(example_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=env,
        encoding="utf-8",
    )

    if result.returncode == 0:
        _ok("Пример отработал успешно")
        return True

    _err("Пример упал с ошибкой:")
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return False


def main() -> None:
    print("=" * 60)
    print("PRE-RELEASE CHECK")
    print("=" * 60)

    clean_dist()
    clean_cache()

    if not reinstall_editable():
        _err("Не удалось переустановить пакет")
        sys.exit(1)
    _ok("Пакет переустановлен")

    ok, version = check_versions()
    if not ok or version is None:
        sys.exit(1)

    if not check_rules_source():
        sys.exit(1)

    if not check_changelog(version):
        sys.exit(1)

    check_readme()

    if not check_git_clean():
        print("   ⚠️  Сборка возможна, но код в git не совпадает с тем, что уйдёт на PyPI.")

    if not run_example():
        _err("Пример упал")
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
