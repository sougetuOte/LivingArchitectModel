"""R-2 W1 T20: verify_import_availability.py テスト.

FR-9 / FR-7 対応 (design.md §4.1 C1 反映版)。
hooks/scripts/tests の第三者 import 全数走査 と .venv importability の
突合 (drift) を検証する。
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import verify_import_availability  # noqa: E402
from verify_import_availability import (  # noqa: E402
    _build_stdlib_module_names,
    extract_toplevel_imports,
    find_drift,
    resolve_venv_python,
)


def _write(tmp_path: Path, rel_path: str, content: str) -> None:
    target = tmp_path / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def test_ast_extracts_toplevel_only():
    """design.md §4.1: from X.Y import Z のトップレベルモジュール名のみ抽出."""
    modules = extract_toplevel_imports("from foo.bar.baz import qux\n")
    assert modules == {"foo"}


def test_ast_extracts_import_statement_toplevel_only():
    """import X.Y.Z の場合もトップレベル X のみ抽出."""
    modules = extract_toplevel_imports("import foo.bar.baz\n")
    assert modules == {"foo"}


def test_ast_ignores_relative_imports():
    """from . import x / from .. import y は相対 import でありトップレベル対象外."""
    modules = extract_toplevel_imports("from . import x\nfrom ..pkg import y\n")
    assert modules == set()


def test_stdlib_excluded():
    """os / sys / json は stdlib 集合に含まれる (drift 除外対象 / NFR-2: 3.10+ 専用 API 不使用)."""
    stdlib_names = _build_stdlib_module_names()
    assert {"os", "sys", "json"}.issubset(stdlib_names)


def test_no_drift_with_stdlib_and_installed(tmp_path: Path):
    """正例: stdlib + 実在パッケージ (pytest) のみの import は drift 0."""
    _write(tmp_path, ".claude/scripts/dummy_ok.py", "import sys\nimport pytest\n")
    drift = find_drift(repo_root=tmp_path)
    assert drift == []


def test_drift_detected_with_nonexistent_pkg(tmp_path: Path):
    """誤例: 実在しない架空パッケージは drift として検出される (FR-7 誤例列挙)."""
    _write(
        tmp_path,
        ".claude/hooks/dummy_bad.py",
        "import nonexistent_pkg_xyz_20260721\n",
    )
    drift = find_drift(repo_root=tmp_path)
    assert drift == ["nonexistent_pkg_xyz_20260721"]


def test_resolve_venv_python_falls_back_to_sys_executable(tmp_path: Path):
    """.venv が存在しない repo_root では sys.executable にフォールバックする (monkeypatch 対応設計)."""
    result = resolve_venv_python(repo_root=tmp_path)
    assert result == sys.executable


def test_baseline_measurement_records_actual_count():
    """grep baseline: 現行 LAM リポジトリの drift 実測件数を取得可能 (FR-7 grep baseline)."""
    drift = find_drift()
    assert isinstance(drift, list)
    assert all(isinstance(module_name, str) for module_name in drift)
    assert len(drift) >= 0
