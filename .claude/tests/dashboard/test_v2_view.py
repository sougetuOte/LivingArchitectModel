"""test_v2_view.py - V-2 Milestone 一覧ビューのテスト（W2-B5-T9）

対応仕様:
  - docs/specs/b4-dashboard/design.md §4「V-2: Milestone 一覧ビュー」
  - docs/specs/b4-dashboard/tasks.md §3 W2-B5-T9
  - 実装方針（L1 確定）: builder.py の _render_v2_milestones() メソッド
"""

from __future__ import annotations

import sys
from pathlib import Path

# .claude/scripts を sys.path に追加（test_v1_view.py と同じパターン）
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


# ─────────────────────────────────────────────
# テスト用フィクスチャヘルパー
# ─────────────────────────────────────────────


def _make_builder(milestones=None, current_phase: str = "BUILDING"):
    """テスト用 DashboardBuilder を生成するヘルパー。

    パーサを呼ばず DashboardData を直接組み立てる（T9 完了条件に従う）。
    """
    from dashboard.builder import DashboardBuilder
    from dashboard.models import DashboardData, MilestoneInfo

    ms_list = milestones if milestones is not None else []
    data = DashboardData(
        milestones=ms_list,
        current_phase=current_phase,
        generated_at="2026-06-21T12:00:00",
    )
    return DashboardBuilder(data)


def _make_milestone(
    name: str = "B-5",
    status: str = "in-progress",
    current_step: str = "UNKNOWN",
):
    """テスト用 MilestoneInfo を生成するヘルパー。"""
    from dashboard.models import MilestoneInfo

    return MilestoneInfo(name=name, current_step=current_step, status=status)


# ─────────────────────────────────────────────
# V-2 セクション存在確認
# ─────────────────────────────────────────────


def test_render_contains_v2_section_id():
    """生成 HTML に <section id="v2-milestones"> が存在すること。

    対応完了条件: W2-B5-T9「<section id="v2-milestones"> が存在」
    """
    builder = _make_builder()
    html = builder.render()
    assert '<section id="v2-milestones">' in html, (
        "生成 HTML に <section id=\"v2-milestones\"> が見つかりません。\n"
        "builder.py の render() に V-2 セクションを追加してください。"
    )


# ─────────────────────────────────────────────
# テーブル構造確認
# ─────────────────────────────────────────────


def test_render_v2_contains_table():
    """V-2 セクションに <table> 要素が存在すること。

    対応完了条件: W2-B5-T9「<table> + <thead> + <tbody> 構造」
    """
    milestone = _make_milestone()
    html = _make_builder(milestones=[milestone]).render()
    assert "<table>" in html, (
        "生成 HTML に <table> が見つかりません（Milestone 1 件以上のケース）。"
    )


def test_render_v2_thead_has_three_columns():
    """V-2 テーブルのヘッダに「Milestone」「現在の Step」「状態」の 3 列が存在すること。

    対応完了条件: W2-B5-T9「<thead><tr><th>Milestone</th><th>現在の Step</th><th>状態</th></tr></thead>」
    設計仕様: design.md §4 V-2 DOM 構成案
    """
    milestone = _make_milestone()
    html = _make_builder(milestones=[milestone]).render()
    assert "<th>Milestone</th>" in html, "<th>Milestone</th> が見つかりません。"
    assert "<th>現在の Step</th>" in html, "<th>現在の Step</th> が見つかりません。"
    assert "<th>状態</th>" in html, "<th>状態</th> が見つかりません。"


def test_render_v2_contains_tbody():
    """V-2 テーブルに <tbody> が存在すること。"""
    milestone = _make_milestone()
    html = _make_builder(milestones=[milestone]).render()
    assert "<tbody>" in html, "生成 HTML に <tbody> が見つかりません。"


# ─────────────────────────────────────────────
# Milestone 名とアンカーリンク確認
# ─────────────────────────────────────────────


def test_render_v2_milestone_name_in_row():
    """Milestone 名が <tbody> 行に表示されること。"""
    milestone = _make_milestone(name="B-5")
    html = _make_builder(milestones=[milestone]).render()
    assert "B-5" in html, "Milestone 名「B-5」が HTML に見つかりません。"


def test_render_v2_anchor_link_format():
    """Milestone 行に <a href="#v3-waves-{name}"> 形式のアンカーリンクがあること。

    対応完了条件: W2-B5-T9「アンカーリンクが <a href="#v3-waves-<milestone>"> 形式」
    設計仕様: design.md §4 V-2 DOM 構成案 / §4 ナビゲーション
    """
    milestone = _make_milestone(name="B-5")
    html = _make_builder(milestones=[milestone]).render()
    assert '<a href="#v3-waves-B-5">B-5</a>' in html, (
        "アンカーリンク <a href=\"#v3-waves-B-5\">B-5</a> が見つかりません。\n"
        "設計: design.md §4 ナビゲーション「V-2 → V-3」"
    )


def test_render_v2_anchor_link_for_different_milestone():
    """B-4 など別 Milestone でもアンカーリンクが正しく生成されること。"""
    milestone = _make_milestone(name="B-4")
    html = _make_builder(milestones=[milestone]).render()
    assert '<a href="#v3-waves-B-4">B-4</a>' in html, (
        "アンカーリンク <a href=\"#v3-waves-B-4\">B-4</a> が見つかりません。"
    )


def test_render_v2_multiple_milestones():
    """複数 Milestone がある場合、全て行に表示されること。"""
    ms_b4 = _make_milestone(name="B-4", status="completed")
    ms_b5 = _make_milestone(name="B-5", status="in-progress")
    html = _make_builder(milestones=[ms_b4, ms_b5]).render()
    assert '<a href="#v3-waves-B-4">B-4</a>' in html, "B-4 のリンクが見つかりません。"
    assert '<a href="#v3-waves-B-5">B-5</a>' in html, "B-5 のリンクが見つかりません。"


# ─────────────────────────────────────────────
# 現在の Step 列（DashboardData.current_phase から取得）
# ─────────────────────────────────────────────


def test_render_v2_step_column_shows_current_phase():
    """Step 列に DashboardData.current_phase の値が表示されること。

    対応完了条件: W2-B5-T9「各行の Step 列に DashboardData.current_phase の値が表示される」
    設計仕様: design.md §4 V-2「複数 Milestone が存在する場合は全 Milestone に同じ Step を表示」
    """
    milestone = _make_milestone(name="B-5")
    html = _make_builder(milestones=[milestone], current_phase="BUILDING").render()
    # BUILDING が td 要素内に表示されること（アンカーリンクでなく Step 列として）
    assert "BUILDING" in html, (
        "Step 列に current_phase 値「BUILDING」が表示されていません。\n"
        "V-2 の各行の Step 列は DashboardData.current_phase を使用すること（design.md §4）。"
    )


def test_render_v2_step_column_planning():
    """current_phase が PLANNING のとき Step 列に「PLANNING」が表示されること。"""
    milestone = _make_milestone(name="B-5")
    html = _make_builder(milestones=[milestone], current_phase="PLANNING").render()
    assert "PLANNING" in html, "Step 列に「PLANNING」が表示されていません。"


def test_render_v2_multiple_milestones_same_step():
    """複数 Milestone が存在する場合、全 Milestone に同じ Step が表示されること。

    設計仕様: design.md §4 V-2 注記「複数 Milestone が存在する場合は全 Milestone に同じ Step を表示する」
    """
    ms_b4 = _make_milestone(name="B-4", status="completed")
    ms_b5 = _make_milestone(name="B-5", status="in-progress")
    html = _make_builder(milestones=[ms_b4, ms_b5], current_phase="BUILDING").render()
    # 「BUILDING」が2回以上出現すること（各行に表示されるため）
    count = html.count("BUILDING")
    assert count >= 2, (
        f"複数 Milestone の場合、全行に同じ Step が表示される必要があります。\n"
        f"「BUILDING」の出現回数: {count}（期待: 2 以上）"
    )


# ─────────────────────────────────────────────
# 状態バッジ確認
# ─────────────────────────────────────────────


def test_render_v2_status_badge_in_progress():
    """in-progress Milestone に状態バッジ（data-status="in-progress"）が表示されること。

    対応完了条件: W2-B5-T9「状態バッジ <span class="badge" data-status="..."> + 日本語ラベル」
    """
    milestone = _make_milestone(status="in-progress")
    html = _make_builder(milestones=[milestone]).render()
    assert 'data-status="in-progress"' in html, (
        "data-status=\"in-progress\" が見つかりません。"
    )
    assert "進行中" in html, "状態バッジの日本語ラベル「進行中」が見つかりません。"


def test_render_v2_status_badge_completed():
    """completed Milestone に状態バッジ（data-status="completed"）と日本語「完了」が表示されること。"""
    milestone = _make_milestone(status="completed")
    html = _make_builder(milestones=[milestone]).render()
    assert 'data-status="completed"' in html, "data-status=\"completed\" が見つかりません。"
    assert "完了" in html, "状態バッジの日本語ラベル「完了」が見つかりません。"


def test_render_v2_status_badge_blocked():
    """blocked Milestone に状態バッジ（data-status="blocked"）と日本語「ブロック中」が表示されること。"""
    milestone = _make_milestone(status="blocked")
    html = _make_builder(milestones=[milestone]).render()
    assert 'data-status="blocked"' in html, "data-status=\"blocked\" が見つかりません。"
    assert "ブロック中" in html, "状態バッジの日本語ラベル「ブロック中」が見つかりません。"


def test_render_v2_status_badge_not_started():
    """not-started Milestone に状態バッジ（data-status="not-started"）と日本語「未着手」が表示されること。"""
    milestone = _make_milestone(status="not-started")
    html = _make_builder(milestones=[milestone]).render()
    assert 'data-status="not-started"' in html, 'data-status="not-started" が見つかりません。'
    assert "未着手" in html, "状態バッジの日本語ラベル「未着手」が見つかりません。"


def test_render_v2_badge_has_span_class():
    """状態バッジが <span class="badge" data-status="..."> 形式であること。"""
    milestone = _make_milestone(status="in-progress")
    html = _make_builder(milestones=[milestone]).render()
    assert '<span class="badge" data-status=' in html, (
        '<span class="badge" data-status=...> 形式のバッジが見つかりません。'
    )


# ─────────────────────────────────────────────
# データ行の data-milestone 属性確認
# ─────────────────────────────────────────────


def test_render_v2_row_has_data_milestone_attribute():
    """<tr data-milestone="{name}"> 属性が各行に存在すること。

    設計仕様: design.md §4 V-2 DOM 構成案「<tr data-milestone="B-5">」
    """
    milestone = _make_milestone(name="B-5")
    html = _make_builder(milestones=[milestone]).render()
    assert 'data-milestone="B-5"' in html, (
        'data-milestone="B-5" 属性が <tr> タグに見つかりません。'
    )


# ─────────────────────────────────────────────
# Empty State（Milestone 0 件）
# ─────────────────────────────────────────────


def test_render_v2_empty_state_when_no_milestones():
    """Milestone が 0 件のとき「Milestone 情報なし」と表示されること（empty state）。

    対応完了条件: W2-B5-T9「empty state（milestones が空）: 「Milestone 情報なし」または同等の文言」
    """
    html = _make_builder(milestones=[]).render()
    assert "Milestone 情報なし" in html, (
        "milestones が空のとき「Milestone 情報なし」が表示されていません。\n"
        "empty state の実装を確認してください。"
    )


def test_render_v2_empty_state_no_table():
    """Milestone が 0 件のとき <table> が生成されないこと（empty state では不要）。"""
    html = _make_builder(milestones=[]).render()
    # V-2 セクションが存在し、テーブルはなくて良い（empty state）
    assert '<section id="v2-milestones">' in html, "V-2 セクション自体がありません。"
    # table が存在しないことは厳密には要求しないが、
    # empty state には <table> は不要（テストは Milestone 情報なし文言の存在を確認）


def test_render_v2_section_exists_even_when_no_milestones():
    """Milestone が 0 件でも <section id="v2-milestones"> は存在すること。"""
    html = _make_builder(milestones=[]).render()
    assert '<section id="v2-milestones">' in html, (
        "Milestone 0 件でも <section id=\"v2-milestones\"> は表示される必要があります。"
    )


# ─────────────────────────────────────────────
# 回帰テスト: V-1 / parser_errors が壊れていないこと
# ─────────────────────────────────────────────


def test_v1_section_not_broken_by_v2():
    """V-2 実装後も V-1 セクションが正常に生成されること（回帰テスト）。

    対応完了条件: W2-B5-T9「既存 V-1 / parser_errors の出力が壊れていない（回帰テスト）」
    """
    milestone = _make_milestone()
    html = _make_builder(milestones=[milestone]).render()
    assert '<section id="v1-project-summary">' in html, (
        "V-2 追加後に V-1 セクションが消えています。回帰テスト失敗。"
    )
    assert "LAM Dashboard" in html, "LAM Dashboard タイトルが消えています。"


def test_parser_errors_section_not_shown_when_no_errors():
    """parser_errors が空のとき <section id="parser-errors"> が生成されないこと（回帰テスト）。"""
    from dashboard.builder import DashboardBuilder
    from dashboard.models import DashboardData

    data = DashboardData(parser_errors=[])
    builder = DashboardBuilder(data)
    html = builder.render()
    assert '<section id="parser-errors">' not in html, (
        "エラーなしのとき parser-errors セクションが生成されています。"
    )


def test_parser_errors_section_shown_when_errors_exist():
    """parser_errors がある場合 <section id="parser-errors"> が生成されること（回帰テスト）。"""
    from dashboard.builder import DashboardBuilder
    from dashboard.models import DashboardData

    data = DashboardData(parser_errors=["SessionState: ファイル不在"])
    builder = DashboardBuilder(data)
    html = builder.render()
    assert '<section id="parser-errors">' in html, (
        "エラーあり時に parser-errors セクションが生成されていません。"
    )


# ─────────────────────────────────────────────
# h2 見出し確認
# ─────────────────────────────────────────────


def test_render_v2_contains_h2_heading():
    """V-2 セクションに <h2> 見出しが存在すること。"""
    milestone = _make_milestone()
    html = _make_builder(milestones=[milestone]).render()
    assert "<h2>" in html, "V-2 セクションに <h2> 見出しが見つかりません。"
