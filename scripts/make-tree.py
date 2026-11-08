import os

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

# How to render specific directories (path relative to project root, forward slashes):
#   ("collapse", comment)              → `name/  # comment`
#   ("collapse_as", suffix, comment)   → `name<suffix>  # comment`
#   ("head", N, comment)               → show first N children, then `...`
#   ("inline_child",)                  → if exactly one child dir, show `name/child/`
TREE_MODES = {
    "data_src": ("collapse", "Source rules & dictionary (not shipped)"),
    "docs": ("collapse", "Documentation"),
    "examples": ("collapse", "Usage examples"),
    "tests": ("collapse", "Pytest suite"),
    "scripts": ("head", 2, "Build & release tools (not shipped)"),
    "src": ("inline_child",),
    "src/eng_to_ru_transcriber/data": ("collapse_as", "/*.pkl", "Compiled runtime data"),
}

COMMENTS = {
    "scripts/build_rules.py": "Compiles data_src/*.py → data/*.pkl",
    "scripts/convert_dict.py": "Compiles data_src/en_dict.txt → data/en_dict.pkl",
    "src/eng_to_ru_transcriber": "The library (this is what ships to PyPI)",
    "src/eng_to_ru_transcriber/__init__.py": "Public API",
    "src/eng_to_ru_transcriber/transcriber.py": "Orchestrator (entry point)",
    "src/eng_to_ru_transcriber/eng_to_ipa_hybrid.py": "EN → IPA (dictionary + rules)",
    "src/eng_to_ru_transcriber/rule_based_ipa.py": "Applies EN → IPA rules",
    "src/eng_to_ru_transcriber/ipa_to_ru.py": "Applies IPA → Cyrillic rules",
    "src/eng_to_ru_transcriber/rule_engine.py": "Shared regex/literal rule executor",
    "pyproject.toml": "Metadata, build config",
}

CUSTOM_ORDER = {
    "scripts": [
        "build_rules.py", "convert_dict.py",
        "benchmark.py", "dsl_translator.py", "make-tree.py", "pre_release.py",
    ],
    "src/eng_to_ru_transcriber": [
        "data", "__init__.py", "transcriber.py",
        "eng_to_ipa_hybrid.py", "rule_based_ipa.py", "ipa_to_ru.py", "rule_engine.py",
    ],
}

MERGES = [
    ("README.md", "README.ru.md", "README.md / README.ru.md"),
]


def collect_entries(path):
    try:
        items = sorted(os.listdir(path))
    except PermissionError:
        return [], []
    dirs, files = [], []
    for item in items:
        full = os.path.join(path, item)
        if os.path.isdir(full):
            if item in IGNORE_DIRS or item.endswith('.egg-info'):
                continue
            dirs.append(item)
        else:
            if item in IGNORE_FILES or any(item.endswith(ext) for ext in IGNORE_EXT):
                continue
            files.append(item)
    return dirs, files


def sort_items(items, relpath):
    order = CUSTOM_ORDER.get(relpath)
    if order:
        idx = {name: i for i, name in enumerate(order)}
        items.sort(key=lambda x: (idx.get(x[0], len(order)), x[2]))
    else:
        items.sort(key=lambda x: (-x[1], x[2]))


def render(startpath, prefix, relpath, lines):
    dirs, files = collect_entries(startpath)

    merge_display = {}
    for kept, merged, display in MERGES:
        if kept in files and merged in files:
            files.remove(merged)
            merge_display[kept] = display

    items = [(d, True, d) for d in dirs] + [(f, False, merge_display.get(f, f)) for f in files]
    sort_items(items, relpath)

    for i, (item, is_dir, display) in enumerate(items):
        is_last = (i == len(items) - 1)
        connector = "└── " if is_last else "├── "

        full = os.path.join(startpath, item)
        rel = f"{relpath}/{item}" if relpath else item

        mode = TREE_MODES.get(rel)

        if mode and mode[0] == "collapse":
            lines.append(f"{prefix}{connector}{display}/  # {mode[1]}")
            continue

        if mode and mode[0] == "collapse_as":
            lines.append(f"{prefix}{connector}{display}{mode[1]}  # {mode[2]}")
            continue

        if mode and mode[0] == "head":
            limit, comment = mode[1], mode[2]
            lines.append(f"{prefix}{connector}{display}/  # {comment}")
            next_prefix = prefix + ("    " if is_last else "│   ")
            sub_dirs, sub_files = collect_entries(full)
            sub_items = [(d, True, d) for d in sub_dirs] + [(f, False, f) for f in sub_files]
            sort_items(sub_items, rel)
            shown = sub_items[:limit]
            has_more = len(sub_items) > limit
            for j, (sub_item, sub_is_dir, sub_display) in enumerate(shown):
                sub_is_last = (j == len(shown) - 1) and not has_more
                sub_conn = "└── " if sub_is_last else "├── "
                sub_rel = f"{rel}/{sub_item}"
                sub_comment = COMMENTS.get(sub_rel, "")
                sub_comment_str = f"  # {sub_comment}" if sub_comment else ""
                lines.append(
                    f"{next_prefix}{sub_conn}{sub_display}"
                    f"{'/' if sub_is_dir else ''}{sub_comment_str}"
                )
            if has_more:
                lines.append(f"{next_prefix}└── ...")
            continue

        if mode and mode[0] == "inline_child":
            sub_dirs, sub_files = collect_entries(full)
            if len(sub_dirs) == 1 and not sub_files:
                child = sub_dirs[0]
                child_full = os.path.join(full, child)
                child_rel = f"{rel}/{child}"
                child_comment = COMMENTS.get(child_rel, "")
                child_comment_str = f"  # {child_comment}" if child_comment else ""
                lines.append(f"{prefix}{connector}{display}/{child}/{child_comment_str}")
                next_prefix = prefix + ("    " if is_last else "│   ")
                render(child_full, next_prefix, child_rel, lines)
                continue

        comment = COMMENTS.get(rel, "")
        comment_str = f"  # {comment}" if comment else ""

        if is_dir:
            lines.append(f"{prefix}{connector}{display}/{comment_str}")
            next_prefix = prefix + ("    " if is_last else "│   ")
            render(full, next_prefix, rel, lines)
        else:
            lines.append(f"{prefix}{connector}{display}{comment_str}")


def align_comments(lines: list[str], min_gap: int = 2) -> list[str]:
    """Pad each content before '  # ' so all comments start at the same column."""
    parsed = []
    for line in lines:
        content, sep, comment = line.partition("  # ")
        if sep:
            parsed.append((content.rstrip(), comment.rstrip()))
        else:
            parsed.append((line.rstrip(), None))

    widths = [len(c) for c, cm in parsed if cm is not None]
    if not widths:
        return [c for c, _ in parsed]

    target = max(widths) + min_gap

    return [
        f"{c.ljust(target)}# {cm}" if cm is not None else c
        for c, cm in parsed
    ]


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    output_path = os.path.join(project_root, "structure.txt")

    lines = [f"{os.path.basename(project_root)}/"]
    render(project_root, prefix="", relpath="", lines=lines)
    lines = align_comments(lines)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"✅ Готово! Структура сохранена в: {output_path}")
