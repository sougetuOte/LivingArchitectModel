"""test_wave8_merger.py - MilestoneSourceMerger 単体テスト（W8-B5-T103）

対応仕様:
  - docs/specs/b4-dashboard/wave8/requirements.md FR-W8-1 / FR-W8-5 / FR-W8-6 / NFR-W8-1
  - docs/specs/b4-dashboard/wave8/design.md §4「MilestoneSourceMerger 詳細設計」
  - docs/specs/b4-dashboard/wave8/tasks.md §6 T103

検証内容:
  - 正常系: 和集合・重複排除・昇順ソート
  - 異常系: 片方/両方が空リスト
  - status 補完: tasks 由来のみのエントリは status="unknown"
  - NFR-W8-1 MUST: 30 件以上の Milestone 入力で 1 秒以内に完了すること
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

# .claude/scripts を sys.path に追加（既存テストと同一パターン）
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


# ─────────────────────────────────────────────
# 正常系: 両方にエントリあり、重複あり
# ─────────────────────────────────────────────


def test_merge_union_with_duplicate():
    """session=[B-4, B-5] / tasks=[B-5, B-6] → 結果 [B-4, B-5, B-6]（AC-W8-1 シナリオ 1）。"""
    from dashboard.merger import MilestoneSourceMerger
    from dashboard.models import MilestoneInfo

    session_milestones = [
        MilestoneInfo(name="B-4", current_step="UNKNOWN", status="in-progress"),
        MilestoneInfo(name="B-5", current_step="UNKNOWN", status="in-progress"),
    ]
    task_milestone_names = ["B-5", "B-6"]

    result = MilestoneSourceMerger(
        session_milestones=session_milestones,
        task_milestone_names=task_milestone_names,
    ).get_milestones()

    names = [ms.name for ms in result]
    assert names == ["B-4", "B-5", "B-6"]


# ─────────────────────────────────────────────
# 正常系: session のみ
# ─────────────────────────────────────────────


def test_merge_session_only():
    """session=[B-5] / tasks=[] → 結果 [B-5]（AC-W8-1 シナリオ 2）。"""
    from dashboard.merger import MilestoneSourceMerger
    from dashboard.models import MilestoneInfo

    session_milestones = [
        MilestoneInfo(name="B-5", current_step="UNKNOWN", status="in-progress"),
    ]

    result = MilestoneSourceMerger(
        session_milestones=session_milestones,
        task_milestone_names=[],
    ).get_milestones()

    assert len(result) == 1
    assert result[0].name == "B-5"
    assert result[0].status == "in-progress"


# ─────────────────────────────────────────────
# 正常系: tasks のみ → status="unknown" 補完
# ─────────────────────────────────────────────


def test_merge_tasks_only_completes_unknown_status():
    """session=[] / tasks=[B-5] → 結果 [MilestoneInfo(name="B-5", status="unknown")]（AC-W8-1 シナリオ 3）。"""
    from dashboard.merger import MilestoneSourceMerger

    result = MilestoneSourceMerger(
        session_milestones=[],
        task_milestone_names=["B-5"],
    ).get_milestones()

    assert len(result) == 1
    assert result[0].name == "B-5"
    assert result[0].status == "unknown"


# ─────────────────────────────────────────────
# 正常系: 両方空 → 空リスト
# ─────────────────────────────────────────────


def test_merge_both_empty_returns_empty_list():
    """session=[] / tasks=[] → 結果 []（AC-W8-1 シナリオ 4 / FR-W8-6 両方空）。"""
    from dashboard.merger import MilestoneSourceMerger

    result = MilestoneSourceMerger(
        session_milestones=[],
        task_milestone_names=[],
    ).get_milestones()

    assert result == []


# ─────────────────────────────────────────────
# 異常系: session_milestones が空（ok=False 相当）
# ─────────────────────────────────────────────


def test_merge_empty_session_milestones_continues_with_tasks():
    """session_milestones=[] でも tasks のみで継続動作すること（FR-W8-6 MUST）。"""
    from dashboard.merger import MilestoneSourceMerger

    result = MilestoneSourceMerger(
        session_milestones=[],
        task_milestone_names=["B-4", "B-6"],
    ).get_milestones()

    names = [ms.name for ms in result]
    assert names == ["B-4", "B-6"]
    assert all(ms.status == "unknown" for ms in result)


# ─────────────────────────────────────────────
# 異常系: task_milestone_names が空（ok=False 相当）
# ─────────────────────────────────────────────


def test_merge_empty_task_names_continues_with_session():
    """task_milestone_names=[] でも session のみで継続動作すること（FR-W8-6 MUST）。"""
    from dashboard.merger import MilestoneSourceMerger
    from dashboard.models import MilestoneInfo

    session_milestones = [
        MilestoneInfo(name="B-4", current_step="UNKNOWN", status="blocked"),
    ]

    result = MilestoneSourceMerger(
        session_milestones=session_milestones,
        task_milestone_names=[],
    ).get_milestones()

    assert len(result) == 1
    assert result[0].name == "B-4"
    assert result[0].status == "blocked"


# ─────────────────────────────────────────────
# status 補完: 重複時は session 側の status を優先
# ─────────────────────────────────────────────


def test_merge_duplicate_name_prefers_session_status():
    """同名 Milestone が session/tasks 両方に存在する場合、session 側の status を優先する（design.md §4 重複排除ルール）。"""
    from dashboard.merger import MilestoneSourceMerger
    from dashboard.models import MilestoneInfo

    session_milestones = [
        MilestoneInfo(name="B-5", current_step="UNKNOWN", status="completed"),
    ]

    result = MilestoneSourceMerger(
        session_milestones=session_milestones,
        task_milestone_names=["B-5"],
    ).get_milestones()

    assert len(result) == 1
    assert result[0].status == "completed"


# ─────────────────────────────────────────────
# ソート: name 昇順確認
# ─────────────────────────────────────────────


def test_merge_sorts_by_name_ascending():
    """出力が name 昇順（文字列辞書順）でソートされること（design.md §4 出力契約）。"""
    from dashboard.merger import MilestoneSourceMerger
    from dashboard.models import MilestoneInfo

    session_milestones = [
        MilestoneInfo(name="B-9", current_step="UNKNOWN", status="in-progress"),
        MilestoneInfo(name="B-10", current_step="UNKNOWN", status="in-progress"),
    ]
    task_milestone_names = ["B-2"]

    result = MilestoneSourceMerger(
        session_milestones=session_milestones,
        task_milestone_names=task_milestone_names,
    ).get_milestones()

    names = [ms.name for ms in result]
    # 文字列辞書順: "B-10" < "B-2" < "B-9"
    assert names == sorted(names)


# ─────────────────────────────────────────────
# MilestoneProvider Protocol 実装確認
# ─────────────────────────────────────────────


def test_merger_implements_milestone_provider_protocol():
    """MilestoneSourceMerger が MilestoneProvider Protocol を実装していること（FR-W8-5 MUST）。"""
    from dashboard.merger import MilestoneProvider, MilestoneSourceMerger

    merger = MilestoneSourceMerger(session_milestones=[], task_milestone_names=[])
    assert isinstance(merger, MilestoneProvider)


# ─────────────────────────────────────────────
# NFR-W8-1 MUST 保証: 30 件以上の Milestone で 1 秒以内
# ─────────────────────────────────────────────


def test_merge_performance_within_1_second_for_30_plus_milestones():
    """30 件以上の Milestone 入力に対して 1 秒以内に完了すること（NFR-W8-1 MUST）。"""
    from dashboard.merger import MilestoneSourceMerger
    from dashboard.models import MilestoneInfo

    session_milestones = [
        MilestoneInfo(name=f"B-{i}", current_step="UNKNOWN", status="in-progress")
        for i in range(30)
    ]
    task_milestone_names = [f"B-{i}" for i in range(15, 45)]

    start = time.perf_counter()
    result = MilestoneSourceMerger(
        session_milestones=session_milestones,
        task_milestone_names=task_milestone_names,
    ).get_milestones()
    elapsed = time.perf_counter() - start

    assert elapsed < 1.0, f"Merger 処理が 1 秒を超過しました: {elapsed:.4f}s"
    assert len(result) == 45  # B-0..B-44 の和集合
