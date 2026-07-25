#!/usr/bin/env python3
"""r1_inventory.py — R-1 W-R1 S1 T1.

11 モジュール横断のファイル inventory + Python AST 情報 (T3 循環依存グラフ用) を生成する。

Usage:
    python .claude/scripts/r1_inventory.py [--dry-run] [--output PATH]

Refs:
    docs/specs/large-scale-review/design.md §4.1
    docs/specs/large-scale-review/requirements.md FR-F1
"""
from __future__ import annotations

import argparse
import ast
import glob
import json
import os
import subprocess
import sys
from datetime import date
from typing import Optional, Union

# 11 モジュール分類 (design.md §4.1 MODULES dict 準拠)
MODULES: dict[int, Union[str, list[str]]] = {
    1: ".claude/scripts/dashboard/**/*.py",
    2: ".claude/scripts/*.py",  # module 2 は dashboard/ を post-filter で除外 (module 1 と重複回避)
    3: ".claude/skills/**/SKILL.md",
    4: ".claude/tests/**/*.py",
    5: [".claude/hooks/**/*.py", ".claude/settings*.json"],
    6: ".claude/agents/*.md",
    7: [".claude/rules/*.md", ".claude/rules/**/*.md"],
    8: "docs/internal/*.md",
    9: "docs/specs/**/*.md",
    10: "docs/adr/*.md",
    11: ["CLAUDE.md", "CHEATSHEET.md"],
}

MODULE_2_EXCLUDE_PREFIX = ".claude/scripts/dashboard/"


def _normalize(p: str) -> str:
    return p.replace("\\", "/")


_TRACKED_FILES_CACHE: Optional[set[str]] = None


def _tracked_files() -> set[str]:
    """`git ls-files` の結果を正規化 (/ 区切り) した set で返す (R1-008 対応).

    glob.glob() は .gitignore を関知しないため、gitignore 済みファイル
    (例: .claude/scripts/scan_nfr_refs*.py) が inventory に混入する問題への対処。
    プロセス内でキャッシュし、複数モジュール走査での重複呼び出しを避ける。
    """
    global _TRACKED_FILES_CACHE
    if _TRACKED_FILES_CACHE is None:
        result = subprocess.run(
            ["git", "ls-files"],
            capture_output=True, text=True, check=True,
            encoding="utf-8", errors="replace",
        )
        _TRACKED_FILES_CACHE = {_normalize(line) for line in result.stdout.splitlines()}
    return _TRACKED_FILES_CACHE


def _glob_module(pattern: Union[str, list[str]], module_id: int) -> list[str]:
    patterns = pattern if isinstance(pattern, list) else [pattern]
    tracked = _tracked_files()
    files: set[str] = set()
    for p in patterns:
        for f in glob.glob(p, recursive=True):
            fn = _normalize(f)
            if module_id == 2 and fn.startswith(MODULE_2_EXCLUDE_PREFIX):
                continue
            if fn not in tracked:
                continue
            files.add(fn)
    return sorted(files)


def _parse_ast(path: str) -> dict:
    """Python ファイルから imports + top_level_defs を抽出 (T3 用)."""
    try:
        with open(path, encoding="utf-8") as f:
            source = f.read()
    except (OSError, UnicodeDecodeError) as e:
        return {"parse_error": str(e)}

    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as e:
        return {"parse_error": f"SyntaxError: {e}"}

    imports: list[str] = []
    from_imports: list[dict] = []
    defs: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            from_imports.append({
                "module": node.module or "",
                "names": [a.name for a in node.names],
                "level": node.level,
            })
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.col_offset == 0:
                defs.append(node.name)

    return {
        "imports": imports,
        "from_imports": from_imports,
        "top_level_defs": defs,
    }


def build_inventory() -> dict:
    """全モジュールを走査し inventory dict を構築する."""
    inventory: dict = {}
    for module_id, pattern in MODULES.items():
        files = _glob_module(pattern, module_id)
        inventory[str(module_id)] = {
            "count": len(files),
            "files": files,
            "python_ast": {
                f: _parse_ast(f) for f in files if f.endswith(".py")
            },
        }
    inventory["_meta"] = {
        "generated_at": date.today().isoformat(),
        "module_count": len(MODULES),
        "total_files": sum(inventory[str(m)]["count"] for m in MODULES),
    }
    return inventory


def main(argv: Union[list[str], None] = None) -> int:
    parser = argparse.ArgumentParser(description="R-1 W-R1 S1 T1 inventory generator")
    parser.add_argument("--dry-run", action="store_true",
                        help="Build inventory in memory only; do not write JSON output")
    parser.add_argument("--output", type=str, default=None,
                        help="Output JSON path (default: docs/artifacts/r-1-inventory-<today>.json)")
    args = parser.parse_args(argv)

    inv = build_inventory()

    if args.dry_run:
        print(f"[dry-run] modules={inv['_meta']['module_count']} "
              f"total_files={inv['_meta']['total_files']}")
        for module_id in MODULES:
            print(f"  module {module_id:>2}: {inv[str(module_id)]['count']:>4} files")
        return 0

    output_path = args.output or f"docs/artifacts/r-1-inventory-{date.today().isoformat()}.json"
    parent = os.path.dirname(output_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(inv, f, indent=2, ensure_ascii=False)
    print(f"inventory written: {output_path}")
    print(f"  modules={inv['_meta']['module_count']} "
          f"total_files={inv['_meta']['total_files']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
