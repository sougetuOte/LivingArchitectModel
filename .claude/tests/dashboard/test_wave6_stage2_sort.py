"""test_wave6_stage2_sort.py - ソート機能の自動テスト（W6-B5-T39 / Stage 2）

対応仕様:
  - docs/specs/b4-dashboard/wave6/design.md §9（ソート機能設計）
  - docs/specs/b4-dashboard/wave6/design.md §14（Stage 2 単体テスト T-S2-1〜T-S2-8）
  - docs/specs/b4-dashboard/wave6/tasks.md §6 T39
"""

from __future__ import annotations

import sys
from pathlib import Path

# .claude/scripts を sys.path に追加（既存テストと同じパターン）
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from dashboard.builder import DashboardBuilder
from dashboard.models import DashboardData, MilestoneInfo, TaskInfo


# ─────────────────────────────────────────────
# テスト用フィクスチャヘルパー
# ─────────────────────────────────────────────


def _make_empty_builder() -> DashboardBuilder:
    """テスト用の空 DashboardData から DashboardBuilder を生成する。"""
    data = DashboardData(
        milestones=[],
        waves=[],
        tasks=[],
        completed=[],
        in_progress=[],
        blocked=[],
        current_phase="BUILDING",
        generated_at="2026-06-26T00:00:00",
        parser_errors=[],
    )
    return DashboardBuilder(data)


def _make_builder_with_tasks() -> DashboardBuilder:
    """Task を持つ DashboardBuilder を生成する（T-S2-7 等で使用）。

    design.md §14 T-S2-7 のフィクスチャ要件:
    「非空 tasks リスト」で _render_v4_tasks() が data-milestone= を出力することを確認。
    """
    milestone = MilestoneInfo(
        name="B-5",
        current_step="BUILDING",
        status="in-progress",
    )
    task = TaskInfo(
        id="W1-B5-T1",
        milestone="B-5",
        assignee="Sonnet",
        status="completed",
    )
    data = DashboardData(
        milestones=[milestone],
        waves=[],
        tasks=[task],
        completed=[],
        in_progress=[],
        blocked=[],
        current_phase="BUILDING",
        generated_at="2026-06-26T00:00:00",
        parser_errors=[],
    )
    return DashboardBuilder(data)


# ─────────────────────────────────────────────
# T-S2-1: _render_script() に sortTable 関数が含まれる
# ─────────────────────────────────────────────


def test_t_s2_01_render_script_sort_table_exists() -> None:
    """_render_script() の戻り値に function sortTable( が含まれること。

    design.md §14 T-S2-1 合格基準:
        assert 'function sortTable(' in script
    design.md §9: sortTable(tableId, columnIndex) 関数シグネチャ。
    """
    builder = _make_empty_builder()
    script = builder._render_script()
    assert "function sortTable(" in script, (
        "_render_script() に 'function sortTable(' が見つかりません。\n"
        "design.md §9 のソート関数を実装してください。"
    )


# ─────────────────────────────────────────────
# T-S2-2: _render_script() に initSortButtons 関数が含まれる
# ─────────────────────────────────────────────


def test_t_s2_02_render_script_init_sort_buttons_exists() -> None:
    """_render_script() の戻り値に function initSortButtons( が含まれること。

    design.md §14 T-S2-2 合格基準:
        assert 'function initSortButtons(' in script
    design.md §9: .sort-btn 全件に click listener を追加する初期化関数。
    """
    builder = _make_empty_builder()
    script = builder._render_script()
    assert "function initSortButtons(" in script, (
        "_render_script() に 'function initSortButtons(' が見つかりません。\n"
        "design.md §9 の initSortButtons 関数を実装してください。"
    )


# ─────────────────────────────────────────────
# T-S2-3: render() 出力に class="sort-btn" が含まれる
# ─────────────────────────────────────────────


def test_t_s2_03_render_output_contains_sort_btn_class() -> None:
    """render() の出力 HTML に class="sort-btn" が含まれること。

    design.md §14 T-S2-3 合格基準:
        assert 'class="sort-btn"' in html
    design.md §9 DOM 構造: <button class="sort-btn" data-col="N">
    """
    builder = _make_builder_with_tasks()
    html_output = builder.render()
    assert 'class="sort-btn"' in html_output, (
        "render() 出力に 'class=\"sort-btn\"' が見つかりません。\n"
        "design.md §9 のソートボタン DOM 構造を _render_v4_tasks() に実装してください。"
    )


# ─────────────────────────────────────────────
# T-S2-4: render() 出力に aria-sort="none" が含まれる
# ─────────────────────────────────────────────


def test_t_s2_04_render_output_contains_aria_sort_none() -> None:
    """render() の出力 HTML に aria-sort="none" が含まれること。

    design.md §14 T-S2-4 合格基準:
        assert 'aria-sort="none"' in html
    design.md §9 DOM 構造: <th id="th-task-id" aria-sort="none">
    WAI-ARIA 1.1: aria-sort 初期値は "none"。
    """
    builder = _make_builder_with_tasks()
    html_output = builder.render()
    assert 'aria-sort="none"' in html_output, (
        "render() 出力に 'aria-sort=\"none\"' が見つかりません。\n"
        "design.md §9 の aria-sort 属性を <th> に追加してください。"
    )


# ─────────────────────────────────────────────
# T-S2-5: render() 出力に id="tasks-table" が含まれる
# ─────────────────────────────────────────────


def test_t_s2_05_render_output_contains_tasks_table_id() -> None:
    """render() の出力 HTML に id="tasks-table" が含まれること。

    design.md §14 T-S2-5 合格基準:
        assert 'id="tasks-table"' in html
    design.md §9: テーブル ID は 'tasks-table'（Wave 6 で新規付与）。
    """
    builder = _make_builder_with_tasks()
    html_output = builder.render()
    assert 'id="tasks-table"' in html_output, (
        "render() 出力に 'id=\"tasks-table\"' が見つかりません。\n"
        "design.md §9 の tasks-table ID を <table> 要素に付与してください。"
    )


# ─────────────────────────────────────────────
# T-S2-6: _render_script() に aria-sort 文字列が含まれる
# ─────────────────────────────────────────────


def test_t_s2_06_render_script_contains_aria_sort_update() -> None:
    """_render_script() の戻り値に aria-sort 文字列が含まれること。

    design.md §14 T-S2-6 合格基準:
        assert 'aria-sort' in script
    design.md §9 アルゴリズム: ソート中の <th> に aria-sort="ascending" 等を設定。
    """
    builder = _make_empty_builder()
    script = builder._render_script()
    assert "aria-sort" in script, (
        "_render_script() に 'aria-sort' が見つかりません。\n"
        "design.md §9 の aria-sort 更新ロジックを sortTable() 内に実装してください。"
    )


# ─────────────────────────────────────────────
# T-S2-7: _render_v4_tasks() タスク行に data-milestone= が含まれる
# ─────────────────────────────────────────────


def test_t_s2_07_render_v4_tasks_row_has_data_milestone() -> None:
    """_render_v4_tasks() の行に data-milestone= 属性が含まれること（非空 tasks データ）。

    design.md §14 T-S2-7 合格基準:
        assert 'data-milestone=' in v4_html
    design.md §9 / §13: _render_v4_tasks() は各 <tr> に data-milestone="{task.milestone}" を付与。
    Stage 3 フィルタ機能（applyFilters）で row.dataset.milestone を参照する際に使用。
    """
    builder = _make_builder_with_tasks()
    v4_html = builder._render_v4_tasks()
    assert "data-milestone=" in v4_html, (
        "_render_v4_tasks() 出力に 'data-milestone=' が見つかりません。\n"
        "design.md §13 の data-milestone 属性を <tr> に追加してください。"
    )


# ─────────────────────────────────────────────
# T-S2-8: _render_script() に STATUS_ORDER 定数が含まれる
# ─────────────────────────────────────────────


def test_t_s2_08_render_script_contains_status_order() -> None:
    """_render_script() の戻り値に STATUS_ORDER 定数が含まれること。

    design.md §14 T-S2-8 合格基準:
        assert 'STATUS_ORDER' in script
    design.md §9: STATUS_ORDER = {'not-started': 0, 'in-progress': 1, 'blocked': 2, 'completed': 3}
    状態列（列 2）のソートに固定順序を使用するための定数（文字列辞書順を使わない理由も §9 に記載）。
    """
    builder = _make_empty_builder()
    script = builder._render_script()
    assert "STATUS_ORDER" in script, (
        "_render_script() に 'STATUS_ORDER' が見つかりません。\n"
        "design.md §9 の STATUS_ORDER 定数を <script> 先頭に定義してください。"
    )
