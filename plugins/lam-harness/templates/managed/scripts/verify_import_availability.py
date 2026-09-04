#!/usr/bin/env python3
"""verify_import_availability.py — R-2 W1 T20.

hooks/scripts/tests の第三者 import 全数走査 と `.venv` importability の突合。
retro T20 の原意 (2026-07-20 の PyYAML 検出事例 = ある script が `import yaml`
するが `.venv` に未インストールで初回実行時に失敗した drift) を検出する。

判定ロジック (design.md §4.1 C1 反映版):
1. `.claude/hooks/**/*.py` / `.claude/scripts/**/*.py` / `.claude/tests/**/*.py`
   を AST 解析し、import 文のトップレベルモジュール名を抽出する
2. 3.8 互換のフォールバック手段で stdlib モジュール名集合を導出し、抽出結果から除外する
   (stdlib は `.venv` でも常に import 可能なため drift になり得ない)
3. 残った第三者モジュール名について `.venv` インタプリタ上で `import <name>` を
   subprocess 実行し、失敗するものを drift として報告する

Usage:
    python .claude/scripts/verify_import_availability.py

Exit code:
    0: drift なし
    1: drift あり
    2: 実行時エラー

Refs:
    docs/specs/r-2-consolidation/design.md §4.1 (T20 / C1 反映)
    docs/specs/r-2-consolidation/requirements.md FR-7 / FR-9 / NFR-2
"""
from __future__ import annotations

import ast
import glob
import os
import subprocess
import sys
import sysconfig
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[2]

_SCAN_PATTERNS = [
    ".claude/hooks/**/*.py",
    ".claude/scripts/**/*.py",
    ".claude/tests/**/*.py",
]


def resolve_venv_python(repo_root: Path = REPO_ROOT) -> str:
    """`.venv` の python interpreter パスを解決する.

    `.venv/Scripts/python.exe` (Windows) → `.venv/bin/python` (POSIX) の順に
    探索し、見つからない場合は現行インタプリタ (`sys.executable`) にフォールバックする。
    テストで monkeypatch / repo_root 差し替え可能にするため関数化している
    (py_invoke.sh の venv-first fallback chain と同じ考え方)。
    """
    candidates = [
        repo_root / ".venv" / "Scripts" / "python.exe",
        repo_root / ".venv" / "bin" / "python",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return sys.executable


def _iter_scan_files(repo_root: Path = REPO_ROOT) -> list[Path]:
    """走査対象 (.claude/hooks|scripts|tests 配下 .py) を一意に列挙する."""
    files: set[str] = set()
    for pattern in _SCAN_PATTERNS:
        for found in glob.glob(str(repo_root / pattern), recursive=True):
            files.add(found)
    return sorted(Path(f) for f in files)


def extract_toplevel_imports(source: str) -> set[str]:
    """AST 解析で import 文からトップレベルモジュール名を抽出する.

    `import X.Y.Z` / `from X.Y import Z` のいずれも X のみを抽出する
    (中間モジュール Y や Z は含まない)。相対 import (`from . import x`) は
    トップレベルモジュールを持たないため対象外とする。
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()

    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue  # 相対 import: トップレベルモジュールなし
            if node.module:
                modules.add(node.module.split(".")[0])
    return modules


def _build_stdlib_module_names() -> set[str]:
    """3.8 互換の stdlib モジュール名集合を導出する.

    `sys.stdlib_module_names` は 3.10+ 専用 API のため使用しない (NFR-2)。
    代わりに `sysconfig.get_paths()['stdlib']` 配下を走査し、
    パッケージ (サブディレクトリ + `__init__.py`) とモジュール (`*.py`) の
    トップレベル名を収集する。組込みモジュール (`sys.builtin_module_names`) も合わせる。
    """
    names: set[str] = set(sys.builtin_module_names)
    stdlib_path = sysconfig.get_paths().get("stdlib")
    if stdlib_path and os.path.isdir(stdlib_path):
        for entry in os.listdir(stdlib_path):
            full = os.path.join(stdlib_path, entry)
            if os.path.isdir(full):
                if os.path.isfile(os.path.join(full, "__init__.py")):
                    names.add(entry)
            elif entry.endswith(".py"):
                names.add(entry[: -len(".py")])
    return names


def is_importable(module_name: str, python_executable: str) -> bool:
    """指定した python interpreter 上で module_name が import 可能か検証する."""
    result = subprocess.run(
        [python_executable, "-c", "import " + module_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.returncode == 0


def find_drift(
    repo_root: Path = REPO_ROOT,
    python_executable: Optional[str] = None,
) -> list[str]:
    """走査対象を解析し、importability drift (第三者 import かつ import 不能) を返す."""
    if python_executable is None:
        python_executable = resolve_venv_python(repo_root)

    stdlib_names = _build_stdlib_module_names()

    all_modules: set[str] = set()
    for path in _iter_scan_files(repo_root):
        source = path.read_text(encoding="utf-8", errors="replace")
        all_modules.update(extract_toplevel_imports(source))

    third_party = sorted(name for name in all_modules if name not in stdlib_names)

    drift = [name for name in third_party if not is_importable(name, python_executable)]
    return sorted(drift)


def main() -> int:
    try:
        drift = find_drift()
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"drift count: {len(drift)}")
    for module_name in drift:
        print(module_name)

    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(main())
