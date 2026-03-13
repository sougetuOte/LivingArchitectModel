"""
conftest.py - tests/ 共通 fixtures
"""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def project_root(tmp_path: Path) -> Path:
    """一時ディレクトリをプロジェクトルートとして設定する。"""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    (claude_dir / "logs").mkdir()
    return tmp_path


@pytest.fixture(autouse=True)
def _set_project_root(project_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LAM_PROJECT_ROOT", str(project_root))
