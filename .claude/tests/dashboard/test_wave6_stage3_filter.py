"""test_wave6_stage3_filter.py - フィルタ機能の自動テスト（W6-B5-T40 + T41 / Stage 3）

対応仕様:
  - docs/specs/b4-dashboard/wave6/design.md §10（フィルタ機能設計）
  - docs/specs/b4-dashboard/wave6/design.md §11（JS 行数管理）
  - docs/specs/b4-dashboard/wave6/design.md §14（Stage 3 単体テスト T-S3-1〜T-S3-10）
  - docs/specs/b4-dashboard/wave6/tasks.md §6 T40 / T41
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


def _make_builder_with_milestone() -> DashboardBuilder:
    """Milestone を持つ DashboardBuilder を生成する（T-S3-10 で使用）。

    design.md §14 T-S3-10 のフィクスチャ要件（W-NEW-3 対応）:
    DashboardData(milestones=[MilestoneInfo(name="B-5", current_step="BUILDING",
                                             status="in-progress")])
    を渡し、_render_filter_controls() の Milestone select に
    '<option value="B-5">' が含まれることを確認する。
    """
    milestone = MilestoneInfo(
        name="B-5",
        current_step="BUILDING",
        status="in-progress",
    )
    data = DashboardData(
        milestones=[milestone],
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
    """Task を持つ DashboardBuilder を生成する（render() 出力検証で使用）。"""
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
# T-S3-1: _render_script() に applyFilters 関数が含まれる
# ─────────────────────────────────────────────


def test_t_s3_01_render_script_apply_filters_exists() -> None:
    """_render_script() の戻り値に function applyFilters( が含まれること。

    design.md §14 T-S3-1 合格基準:
        assert 'function applyFilters(' in script
    design.md §10: applyFilters() は状態/Milestone/テキストの 3 フィルタを AND 結合して
    tbody 各行の style.display を切替え、件数表示を更新する。
    """
    builder = _make_empty_builder()
    script = builder._render_script()
    assert "function applyFilters(" in script, (
        "_render_script() に 'function applyFilters(' が見つかりません。\n"
        "design.md §10 のフィルタ関数を _render_script() に実装してください。"
    )


# ─────────────────────────────────────────────
# T-S3-2: _render_script() に resetFilters 関数が含まれる
# ─────────────────────────────────────────────


def test_t_s3_02_render_script_reset_filters_exists() -> None:
    """_render_script() の戻り値に function resetFilters( が含まれること。

    design.md §14 T-S3-2 合格基準:
        assert 'function resetFilters(' in script
    design.md §10: resetFilters() は 3 フィルタ変数を初期値にリセットし applyFilters() を呼ぶ。
    """
    builder = _make_empty_builder()
    script = builder._render_script()
    assert "function resetFilters(" in script, (
        "_render_script() に 'function resetFilters(' が見つかりません。\n"
        "design.md §10 の resetFilters 関数を _render_script() に実装してください。"
    )


# ─────────────────────────────────────────────
# T-S3-3: _render_filter_controls() に id="filter-status" が含まれる
# ─────────────────────────────────────────────


def test_t_s3_03_filter_controls_contains_filter_status() -> None:
    """_render_filter_controls() の戻り値に id="filter-status" が含まれること。

    design.md §14 T-S3-3 合格基準:
        assert 'id="filter-status"' in filter_html
    design.md §10 フィルタ UI DOM 構造:
        <select id="filter-status" aria-controls="tasks-table">
        4 状態値 + 「すべて」の計 5 オプション。
    """
    builder = _make_empty_builder()
    filter_html = builder._render_filter_controls()
    assert 'id="filter-status"' in filter_html, (
        "_render_filter_controls() に 'id=\"filter-status\"' が見つかりません。\n"
        "design.md §10 の状態フィルタ select を _render_filter_controls() に追加してください。"
    )


# ─────────────────────────────────────────────
# T-S3-4: _render_filter_controls() に id="filter-milestone" が含まれる
# ─────────────────────────────────────────────


def test_t_s3_04_filter_controls_contains_filter_milestone() -> None:
    """_render_filter_controls() の戻り値に id="filter-milestone" が含まれること。

    design.md §14 T-S3-4 合格基準:
        assert 'id="filter-milestone"' in filter_html
    design.md §10 フィルタ UI DOM 構造:
        <select id="filter-milestone" aria-controls="tasks-table">
        DashboardData.milestones から動的生成。
    """
    builder = _make_empty_builder()
    filter_html = builder._render_filter_controls()
    assert 'id="filter-milestone"' in filter_html, (
        "_render_filter_controls() に 'id=\"filter-milestone\"' が見つかりません。\n"
        "design.md §10 の Milestone フィルタ select を _render_filter_controls() に追加してください。"
    )


# ─────────────────────────────────────────────
# T-S3-5: _render_filter_controls() に id="filter-text" が含まれる
# ─────────────────────────────────────────────


def test_t_s3_05_filter_controls_contains_filter_text() -> None:
    """_render_filter_controls() の戻り値に id="filter-text" が含まれること。

    design.md §14 T-S3-5 合格基準:
        assert 'id="filter-text"' in filter_html
    design.md §10 フィルタ UI DOM 構造:
        <input type="search" id="filter-text" placeholder="Task ID / 担当..."
               aria-controls="tasks-table" aria-label="Task IDまたは担当で検索">
    """
    builder = _make_empty_builder()
    filter_html = builder._render_filter_controls()
    assert 'id="filter-text"' in filter_html, (
        "_render_filter_controls() に 'id=\"filter-text\"' が見つかりません。\n"
        "design.md §10 のテキスト検索 input を _render_filter_controls() に追加してください。"
    )


# ─────────────────────────────────────────────
# T-S3-6: _render_filter_controls() に id="filter-reset" が含まれる
# ─────────────────────────────────────────────


def test_t_s3_06_filter_controls_contains_filter_reset() -> None:
    """_render_filter_controls() の戻り値に id="filter-reset" が含まれること。

    design.md §14 T-S3-6 合格基準:
        assert 'id="filter-reset"' in filter_html
    design.md §10 フィルタ UI DOM 構造:
        <button type="button" id="filter-reset" class="filter-reset-btn">
        フィルタをクリア
        </button>
    """
    builder = _make_empty_builder()
    filter_html = builder._render_filter_controls()
    assert 'id="filter-reset"' in filter_html, (
        "_render_filter_controls() に 'id=\"filter-reset\"' が見つかりません。\n"
        "design.md §10 のリセットボタンを _render_filter_controls() に追加してください。"
    )


# ─────────────────────────────────────────────
# T-S3-7: render() 出力に aria-live="polite" が含まれる
# ─────────────────────────────────────────────


def test_t_s3_07_render_output_contains_aria_live_polite() -> None:
    """render() の出力 HTML に aria-live="polite" が含まれること。

    design.md §14 T-S3-7 合格基準:
        assert 'aria-live="polite"' in html
    design.md §10: <p id="filter-result-count" aria-live="polite"> は
    _render_v4_tasks() 内に配置（T40 完了条件）。
    WAI-ARIA: aria-live="polite" でスクリーンリーダーが件数変更を非割り込みで通知。
    """
    builder = _make_builder_with_tasks()
    html_output = builder.render()
    assert 'aria-live="polite"' in html_output, (
        "render() 出力に 'aria-live=\"polite\"' が見つかりません。\n"
        "design.md §10 の aria-live 属性付き件数表示要素を _render_v4_tasks() に追加してください。"
    )


# ─────────────────────────────────────────────
# T-S3-8: render() 出力に id="filter-result-count" が含まれる
# ─────────────────────────────────────────────


def test_t_s3_08_render_output_contains_filter_result_count() -> None:
    """render() の出力 HTML に id="filter-result-count" が含まれること。

    design.md §14 T-S3-8 合格基準:
        assert 'id="filter-result-count"' in html
    design.md §10: <p id="filter-result-count" aria-live="polite">
    は _render_v4_tasks() 内、フィルタ UI の直後に配置。
    AC-W6-7: applyFilters() がこの要素の textContent を "{n} 件表示" に更新する。
    """
    builder = _make_builder_with_tasks()
    html_output = builder.render()
    assert 'id="filter-result-count"' in html_output, (
        "render() 出力に 'id=\"filter-result-count\"' が見つかりません。\n"
        "design.md §10 の件数表示要素を _render_v4_tasks() に追加してください。"
    )


# ─────────────────────────────────────────────
# T-S3-9: _render_script() に style.display が含まれる
# ─────────────────────────────────────────────


def test_t_s3_09_render_script_contains_style_display() -> None:
    """_render_script() の戻り値に style.display が含まれること。

    design.md §14 T-S3-9 合格基準:
        assert 'style.display' in script
    design.md §10 / §3 A3-4 CASPAR 結論:
        フィルタは row.style.display 切替方式を採用（CSS クラストグルではない）。
        match ? '' : 'none' による表示制御ロジックの存在確認。
    """
    builder = _make_empty_builder()
    script = builder._render_script()
    assert "style.display" in script, (
        "_render_script() に 'style.display' が見つかりません。\n"
        "design.md §10 の row.style.display 表示制御ロジックを applyFilters() に実装してください。"
    )


# ─────────────────────────────────────────────
# T-S3-10: _render_filter_controls() の Milestone option が DashboardData.milestones と一致
# ─────────────────────────────────────────────


def test_t_s3_10_filter_milestone_option_matches_milestone_info() -> None:
    """_render_filter_controls() の Milestone option 値が DashboardData.milestones の name と一致すること。

    design.md §14 T-S3-10 合格基準（W-NEW-3 対応）:
        フィクスチャ: DashboardData(milestones=[MilestoneInfo(name="B-5",
                                   current_step="BUILDING", status="in-progress")])
        assert '<option value="B-5">' in filter_html

    design.md §10: _render_filter_controls() は DashboardData.milestones を反復し、
    ms.name を <option value="{name}">{name}</option> として動的生成する。
    MilestoneInfo オブジェクトリストを渡すことで確認（文字列リストではない）。
    """
    builder = _make_builder_with_milestone()
    filter_html = builder._render_filter_controls()
    assert '<option value="B-5">' in filter_html, (
        "_render_filter_controls() に '<option value=\"B-5\">' が見つかりません。\n"
        "design.md §10 の Milestone 動的生成ロジックを _render_filter_controls() に実装してください。\n"
        "DashboardData.milestones（MilestoneInfo オブジェクトリスト）の ms.name を参照してください。"
    )
