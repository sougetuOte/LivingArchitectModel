"""test_wave8_v2_v4_ssot_alignment.py - V-2/V-4 SSOT 一致確認テスト（W8-B5-T105）

対応仕様:
  - docs/specs/b4-dashboard/wave8/requirements.md AC-W8-2（FR-W8-2 / FR-W8-3 対応）
  - docs/specs/b4-dashboard/wave8/design.md §6「V-2 / V-4 描画ロジック整合化」
  - docs/specs/b4-dashboard/wave8/tasks.md §6 T105

検証内容:
  DashboardBuilder(data).render() を呼び出し、V-2 Milestone カード名（
  <article class="milestone-card" data-milestone="...">）と
  V-4 フィルタ選択肢（<select id="filter-milestone"> 内の <option value="...">）の
  Milestone 集合が完全一致すること。

  data.milestones は MilestoneSourceMerger 確定済みリストを想定した状態で
  DashboardData に直接設定する（design.md §5 の「Builder は data.milestones が
  Merger 由来か否かを知る必要がない」という設計に基づき、Builder 単体テストとして
  Merger 呼び出しを経由せず data.milestones を直接構築する）。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# .claude/scripts を sys.path に追加（既存テストと同一パターン）
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


# ─────────────────────────────────────────────
# 抽出ヘルパー
# ─────────────────────────────────────────────

_V2_CARD_PATTERN = re.compile(r'<article class="milestone-card" data-milestone="([^"]*)">')
_V4_OPTION_PATTERN = re.compile(
    r'<select id="filter-milestone"[^>]*>(.*?)</select>', re.DOTALL
)
_V4_OPTION_VALUE_PATTERN = re.compile(r'<option value="([^"]*)">')


def _extract_v2_milestone_names(html: str) -> list[str]:
    """V-2 Milestone カードの data-milestone 値をリストで抽出する（出現順維持）。"""
    return _V2_CARD_PATTERN.findall(html)


def _extract_v4_filter_milestone_values(html: str) -> list[str]:
    """V-4 フィルタの Milestone <select> 内 <option value> をリストで抽出する（出現順維持）。

    先頭の `<option value="">すべて</option>` は除外し、Milestone 名の option のみ抽出する。
    """
    select_match = re.search(_V4_OPTION_PATTERN, html)
    assert select_match is not None, (
        '<select id="filter-milestone"> が HTML に見つかりません。'
    )
    select_block = select_match.group(1)
    all_values = _V4_OPTION_VALUE_PATTERN.findall(select_block)
    # 先頭の空値（"すべて"）を除外
    return [v for v in all_values if v != ""]


def _make_builder(milestones):
    """テスト用 DashboardBuilder を生成するヘルパー（既存 V-2/V-4 テストと同パターン）。"""
    from dashboard.builder import DashboardBuilder
    from dashboard.models import DashboardData

    data = DashboardData(
        milestones=milestones,
        current_phase="BUILDING",
        generated_at="2026-06-29T00:00:00",
    )
    return DashboardBuilder(data)


def _make_milestone(name: str, status: str = "in-progress"):
    from dashboard.models import MilestoneInfo

    return MilestoneInfo(name=name, current_step="UNKNOWN", status=status)


# ─────────────────────────────────────────────
# テストケース 1: 単一 Milestone
# ─────────────────────────────────────────────


def test_single_milestone_v2_v4_match():
    """単一 Milestone のとき V-2 と V-4 で同じ 1 件が表示されること（AC-W8-2）。"""
    milestones = [_make_milestone("B-5")]
    html = _make_builder(milestones).render()

    v2_names = _extract_v2_milestone_names(html)
    v4_values = _extract_v4_filter_milestone_values(html)

    assert v2_names == ["B-5"]
    assert v4_values == ["B-5"]
    assert set(v2_names) == set(v4_values)


# ─────────────────────────────────────────────
# テストケース 2: 複数 Milestone（順序含む一致）
# ─────────────────────────────────────────────


def test_multiple_milestones_v2_v4_match_with_order():
    """複数 Milestone のとき V-2 と V-4 で同じセット・同じ順序が表示されること（AC-W8-2）。"""
    milestones = [
        _make_milestone("B-4", status="completed"),
        _make_milestone("B-5", status="in-progress"),
        _make_milestone("B-6", status="unknown"),
    ]
    html = _make_builder(milestones).render()

    v2_names = _extract_v2_milestone_names(html)
    v4_values = _extract_v4_filter_milestone_values(html)

    assert v2_names == ["B-4", "B-5", "B-6"]
    assert v4_values == ["B-4", "B-5", "B-6"]
    assert v2_names == v4_values, (
        "V-2 と V-4 の Milestone 出現順が一致していません（SSOT 一致要件 / AC-W8-2）。"
    )


# ─────────────────────────────────────────────
# テストケース 3: 空 Milestone
# ─────────────────────────────────────────────


def test_empty_milestones_v2_v4_both_empty():
    """Milestone が 0 件のとき V-2 は empty state・V-4 フィルタは「すべて」のみであること。"""
    html = _make_builder([]).render()

    v2_names = _extract_v2_milestone_names(html)
    v4_values = _extract_v4_filter_milestone_values(html)

    assert v2_names == []
    assert v4_values == []
    assert "Milestone 情報なし" in html


# ─────────────────────────────────────────────
# テストケース 4: 重複排除確認
# ─────────────────────────────────────────────


def test_no_duplicate_milestone_entries_in_v2_and_v4():
    """data.milestones に重複がない前提（Merger が処理済み）で、
    V-2 / V-4 双方とも同名エントリが 1 件のみ表示されること。

    Merger の重複排除（session と tasks の同名統合）は test_wave8_merger.py で検証済み。
    本テストは Builder 側が Merger 確定済みリストをそのまま重複なく描画することを確認する。
    """
    milestones = [_make_milestone("B-5")]  # Merger 確定済み: 重複排除後は 1 件
    html = _make_builder(milestones).render()

    v2_names = _extract_v2_milestone_names(html)
    v4_values = _extract_v4_filter_milestone_values(html)

    assert v2_names.count("B-5") == 1, "V-2 に B-5 が重複して表示されています。"
    assert v4_values.count("B-5") == 1, "V-4 に B-5 が重複して表示されています。"


# ─────────────────────────────────────────────
# テストケース 5: 昇順ソート確認
# ─────────────────────────────────────────────


def test_v2_and_v4_both_ascending_sorted():
    """V-2 と V-4 のリストが同じ昇順で並ぶこと（design.md §3 A3-4 踏襲）。

    実運用では data.milestones は MilestoneSourceMerger.get_milestones() が
    name 昇順ソート済みで返した結果を build_dashboard.py が代入する
    （design.md §4 出力契約 / §5 正規スケッチ）。本テストはその前提を踏襲し、
    昇順ソート済みの data.milestones を Builder に与えたとき、
    V-2（builder 内部で再ソートする実装）・V-4（data.milestones の順序をそのまま使う実装）
    の双方が同一の昇順を維持することを確認する。

    参考: _render_filter_controls() は data.milestones を再ソートしない実装のため、
    順序保証は呼び出し元（Merger の出力契約）に依存する。この依存関係自体が
    AC-W8-2 の SSOT 一致要件の前提であり、Merger 単体のソート保証は
    test_wave8_merger.py::test_merge_sorts_by_name_ascending で別途検証済み。
    """
    # 文字列辞書順: "B-10" < "B-2" < "B-9" → Merger 確定済みとして昇順で構築
    milestones = [
        _make_milestone("B-10"),
        _make_milestone("B-2"),
        _make_milestone("B-9"),
    ]
    html = _make_builder(milestones).render()

    v2_names = _extract_v2_milestone_names(html)
    v4_values = _extract_v4_filter_milestone_values(html)

    expected_order = ["B-10", "B-2", "B-9"]
    assert v2_names == expected_order, (
        f"V-2 の並び順が期待値と不一致: {v2_names} != {expected_order}"
    )
    assert v4_values == expected_order, (
        f"V-4 の並び順が期待値と不一致: {v4_values} != {expected_order}"
    )
    assert v4_values == v2_names, (
        "V-4 フィルタの並び順が V-2 と一致していません（AC-W8-2 SSOT 一致要件）。\n"
        f"V-2: {v2_names} / V-4: {v4_values}"
    )
