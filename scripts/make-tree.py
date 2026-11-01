import os

# Что игнорируем при обходе (папки и файлы)
IGNORE_DIRS = {
    '__pycache__', '.git', '.hg', '.svn', '.idea', '.vscode',
    'venv', '.venv', 'env', '.env', 'build', 'dist', '.eggs',
    '.mypy_cache', '.pytest_cache', '.ruff_cache', '.tox'
}
IGNORE_EXT = {'.pyc', '.pyo', '.pyd', '.egg', '.swp', '.swo'}
IGNORE_FILES = {
    'compiled_rules.json', 'output_text.txt', 'structure.txt',
    'main.py', '.DS_Store', 'Thumbs.db'
}

def make_tree(startpath, prefix, out_file):
    try:
        items = sorted(os.listdir(startpath))
    except PermissionError:
        return

    filtered_items = []
    for item in items:
        full_path = os.path.join(startpath, item)
        if os.path.isdir(full_path):
            if item in IGNORE_DIRS or item.endswith('.egg-info'):
                continue
        else:
            if item in IGNORE_FILES or any(item.endswith(ext) for ext in IGNORE_EXT):
                continue
        filtered_items.append(item)

    dirs = [i for i in filtered_items if os.path.isdir(os.path.join(startpath, i))]
    files = [i for i in filtered_items if os.path.isfile(os.path.join(startpath, i))]
    sorted_items = dirs + files

    for i, item in enumerate(sorted_items):
        is_last = (i == len(sorted_items) - 1)
        connector = "└── " if is_last else "├── "

        full_path = os.path.join(startpath, item)
        is_dir = os.path.isdir(full_path)

        out_file.write(f"{prefix}{connector}{item}{'/' if is_dir else ''}\n")

        if is_dir:
            next_prefix = prefix + ("    " if is_last else "│   ")
            make_tree(full_path, next_prefix, out_file)

if __name__ == "__main__":
    # Скрипт лежит в scripts/, корень проекта — на уровень выше
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    output_file_path = os.path.join(project_root, "structure.txt")

    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(f"{os.path.basename(project_root)}/\n")
        make_tree(project_root, prefix="", out_file=f)

    print(f"✅ Готово! Структура сохранена в: {output_file_path}")
