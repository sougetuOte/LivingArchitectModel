"""R-1 W-R1 S1 T1: r1_inventory.py テスト.

FR-F1 (W-R1 冒頭 inventory 再生成) 対応。
design.md §4.1 (MODULES dict 11 モジュール) 準拠。
"""
from __future__ import annotations

import sys
from pathlib import Path

# scripts/ を import path に追加
SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import r1_inventory  # noqa: E402
from r1_inventory import MODULES, build_inventory, main  # noqa: E402


def test_modules_dict_has_11_entries():
    """FR-F1: 11 モジュール分類が MODULES に定義されている."""
    assert len(MODULES) == 11
    assert set(MODULES.keys()) == set(range(1, 12))


def test_module_2_excludes_dashboard_prefix():
    """module 1 (dashboard) と module 2 (scripts) の重複を post-filter で解消."""
    inv = build_inventory()
    module_2_files = inv["2"]["files"]
    leaks = [f for f in module_2_files if f.startswith(".claude/scripts/dashboard/")]
    assert not leaks, f"module 2 に dashboard/ 配下が混入: {leaks}"


def test_dry_run_returns_zero(capsys):
    """T1 完了条件: r1_inventory.py --dry-run が rc=0 で成功."""
    rc = main(["--dry-run"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "modules=11" in captured.out


def test_inventory_has_meta():
    """_meta フィールドに generated_at / module_count / total_files が含まれる."""
    inv = build_inventory()
    assert "_meta" in inv
    assert inv["_meta"]["module_count"] == 11
    assert isinstance(inv["_meta"]["total_files"], int)
    assert inv["_meta"]["total_files"] > 0


def test_python_ast_extracts_imports():
    """FR-F1 + T3 用: .py ファイルの imports が AST 抽出されている."""
    inv = build_inventory()
    all_py_ast: dict = {}
    for m in ["1", "2", "4", "5"]:
        all_py_ast.update(inv[m]["python_ast"])
    assert len(all_py_ast) > 0, "AST 対象の .py ファイルが 1 つも収集されていない"
    with_imports = [a for a in all_py_ast.values() if "imports" in a]
    assert len(with_imports) > 0, "imports キーを持つ AST エントリが存在しない"


def test_paths_use_forward_slash():
    """Windows/Git Bash 環境でパスは / 区切りで統一される."""
    inv = build_inventory()
    for module_id in range(1, 12):
        for f in inv[str(module_id)]["files"]:
            assert "\\" not in f, f"バックスラッシュを含むパス: {f}"


def test_output_file_written(tmp_path):
    """--output で指定したパスに JSON が書き出される."""
    out = tmp_path / "test-inventory.json"
    rc = main(["--output", str(out)])
    assert rc == 0
    assert out.is_file()
    import json
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["_meta"]["module_count"] == 11


def test_module_2_excludes_gitignored_files():
    """R1-008: module 2 の inventory に gitignore 済みファイルが混入しない.

    .claude/scripts/scan_nfr_refs.py / scan_nfr_refs2.py は
    .gitignore (`.claude/scripts/scan_nfr_refs*.py`) の対象だが、
    glob.glob() は gitignore を関知しないため inventory に混入していた。
    """
    inv = build_inventory()
    module_2_files = inv["2"]["files"]
    gitignored_leaks = [
        f for f in module_2_files
        if f.endswith("scan_nfr_refs.py") or f.endswith("scan_nfr_refs2.py")
    ]
    assert not gitignored_leaks, (
        f"module 2 に gitignore 済みファイルが混入: {gitignored_leaks}"
    )


def test_module_2_file_count_matches_tracked_files():
    """R1-008: module 2 のファイル数が `git ls-files` の tracked 件数と一致する."""
    import subprocess
    tracked = subprocess.run(
        ["git", "ls-files", ".claude/scripts/*.py"],
        cwd=str(SCRIPTS_DIR.parent.parent),
        capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    tracked_module_2 = [
        t.replace("\\", "/") for t in tracked
        if not t.replace("\\", "/").startswith(".claude/scripts/dashboard/")
    ]

    inv = build_inventory()
    module_2_files = inv["2"]["files"]

    assert len(module_2_files) == len(tracked_module_2), (
        f"module 2 count mismatch: inventory={len(module_2_files)} "
        f"tracked={len(tracked_module_2)}"
    )
