"""analyzers テスト用 conftest.py

analyzers パッケージを sys.path に追加し、import を解決する。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# .claude/hooks を sys.path に追加（analyzers パッケージの import 解決）
_HOOKS_DIR = Path(__file__).resolve().parent.parent.parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))


@pytest.fixture()
def project_root(tmp_path: Path) -> Path:
    """テスト用の仮プロジェクトルートを作成する。"""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    return tmp_path
