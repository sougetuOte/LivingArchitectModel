"""conftest.py - dashboard テスト共通 fixture（R1-031 対応）

対応 issue: docs/artifacts/r-1-audit-tracker.md #R1-031
  「MilestoneInfo / WaveInfo / TaskInfo 手動構築が 10+ テストファイルに散在
   (Rule of Three 違反 / fixture 未共通化)」

MilestoneInfo / WaveInfo / TaskInfo（dashboard.models）の手動構築を
factory fixture に集約し、Wave 追加のたびに増える重複を防ぐ。

各 fixture はキーワード引数で上書き可能な既定値を持つ factory 関数を返す
（`@pytest.fixture` → 内部 `_make(**kwargs)` を return する形式）。
既定値は dashboard.models のフィールド定義（必須引数のみで既定値なし）に
準拠しつつ、テストで頻出する値（B-5 / in-progress 等）を採用する。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# .claude/scripts を sys.path に追加（既存テストと同じパターン）
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


@pytest.fixture
def make_milestone():
    """MilestoneInfo を生成する factory を返す fixture。

    既定値: name="B-5", current_step="BUILDING", status="in-progress"
    """
    from dashboard.models import MilestoneInfo

    def _make(
        name: str = "B-5",
        current_step: str = "BUILDING",
        status: str = "in-progress",
    ) -> MilestoneInfo:
        return MilestoneInfo(name=name, current_step=current_step, status=status)

    return _make


@pytest.fixture
def make_wave():
    """WaveInfo を生成する factory を返す fixture。

    既定値: milestone="B-5", wave_number="1", task_count=5, status="in-progress"
    """
    from dashboard.models import WaveInfo

    def _make(
        milestone: str = "B-5",
        wave_number: str = "1",
        task_count: int = 5,
        status: str = "in-progress",
    ) -> WaveInfo:
        return WaveInfo(
            milestone=milestone,
            wave_number=wave_number,
            task_count=task_count,
            status=status,
        )

    return _make


@pytest.fixture
def make_task():
    """TaskInfo を生成する factory を返す fixture。

    既定値: id="W1-B5-T1", milestone="B-5", status="not-started", assignee="-"
    引数名は `id`（models.TaskInfo のフィールド名と一致）。
    """
    from dashboard.models import TaskInfo

    def _make(
        id: str = "W1-B5-T1",
        milestone: str = "B-5",
        status: str = "not-started",
        assignee: str = "-",
    ) -> TaskInfo:
        return TaskInfo(id=id, milestone=milestone, status=status, assignee=assignee)

    return _make
