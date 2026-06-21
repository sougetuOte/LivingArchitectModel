"""test_v3_view.py - V-3 Wave 一覧ビューのテスト（W3-B5-T14）

対応仕様:
  - docs/specs/b4-dashboard/design.md §4「V-3: Wave 一覧ビュー」
  - docs/specs/b4-dashboard/design.md §5「Wave の状態決定ロジック」
  - docs/specs/b4-dashboard/tasks.md §3 W3-B5-T14
  - 実装方針: builder.py の _render_v3_waves() メソッド

完了条件（仕様 W3-B5-T14）:
  - <section id="v3-waves-<milestone>"> が Milestone ごとに生成される
  - テーブルに Wave 番号・Task 数・状態カラムが表示される
  - 状態値が design.md §5「Wave の状態決定」ロジックに従う
  - <a href="#v4-tasks"> リンクが張られている
"""

from __future__ import annotations

import sys
from pathlib import Path

# .claude/scripts を sys.path に追加（test_v2_view.py と同じパターン）
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


# ─────────────────────────────────────────────
# テスト用フィクスチャヘルパー
# ─────────────────────────────────────────────


def _make_builder(waves=None, milestones=None, current_phase: str = "BUILDING"):
    """テスト用 DashboardBuilder を生成するヘルパー。

    パーサを呼ばず DashboardData を直接組み立てる（V-2 と同じパターン）。
    """
    from dashboard.builder import DashboardBuilder
    from dashboard.models import DashboardData

    wave_list = waves if waves is not None else []
    ms_list = milestones if milestones is not None else []
    data = DashboardData(
        milestones=ms_list,
        waves=wave_list,
        current_phase=current_phase,
        generated_at="2026-06-21T12:00:00",
    )
    return DashboardBuilder(data)


def _make_wave(
    milestone: str = "B-5",
    wave_number: str = "1",
    task_count: int = 5,
    status: str = "in-progress",
):
    """テスト用 WaveInfo を生成するヘルパー。"""
    from dashboard.models import WaveInfo

    return WaveInfo(
        milestone=milestone,
        wave_number=wave_number,
        task_count=task_count,
        status=status,
    )


def _make_milestone(name: str = "B-5", status: str = "in-progress"):
    """テスト用 MilestoneInfo を生成するヘルパー。"""
    from dashboard.models import MilestoneInfo

    return MilestoneInfo(name=name, current_step="BUILDING", status=status)


# ─────────────────────────────────────────────
# V-3 セクション存在確認（R-6: <section id="v3-waves-<milestone>"> を生成）
# ─────────────────────────────────────────────


def test_v3_section_id_contains_milestone_name():
    """<section id="v3-waves-B-5"> が存在すること（R-6）。

    対応完了条件: W3-B5-T14「<section id="v3-waves-<milestone>"> が Milestone ごとに生成される」
    仕様: design.md §4 V-3 DOM 構成案「<section id="v3-waves-B-5">」
    """
    wave = _make_wave(milestone="B-5")
    html = _make_builder(waves=[wave]).render()
    assert '<section id="v3-waves-B-5">' in html, (
        'HTML に <section id="v3-waves-B-5"> が見つかりません。\n'
        "builder.py の _render_v3_waves() を実装してください。"
    )


def test_v3_section_per_milestone_b4():
    """B-4 Milestone の Wave も <section id="v3-waves-B-4"> で生成されること。"""
    wave = _make_wave(milestone="B-4")
    html = _make_builder(waves=[wave]).render()
    assert '<section id="v3-waves-B-4">' in html, (
        'HTML に <section id="v3-waves-B-4"> が見つかりません。'
    )


def test_v3_separate_sections_for_different_milestones():
    """B-4 と B-5 の Wave がある場合、両方のセクションが生成されること。"""
    wave_b4 = _make_wave(milestone="B-4", wave_number="7")
    wave_b5 = _make_wave(milestone="B-5", wave_number="1")
    html = _make_builder(waves=[wave_b4, wave_b5]).render()
    assert '<section id="v3-waves-B-4">' in html, "B-4 セクションが見つかりません。"
    assert '<section id="v3-waves-B-5">' in html, "B-5 セクションが見つかりません。"


# ─────────────────────────────────────────────
# テーブル構造確認（R-4: Wave 番号・Task 数・状態カラム）
# ─────────────────────────────────────────────


def test_v3_contains_table():
    """V-3 セクションに <table> が存在すること。"""
    wave = _make_wave()
    html = _make_builder(waves=[wave]).render()
    assert "<table>" in html, "V-3 に <table> が見つかりません。"


def test_v3_thead_has_three_columns():
    """V-3 テーブルのヘッダに「Wave」「Task 数」「状態」の 3 列が存在すること。

    対応完了条件: W3-B5-T14「テーブルに Wave 番号・Task 数・状態カラムが表示される」
    仕様: design.md §4 V-3 DOM 構成案 thead
    """
    wave = _make_wave()
    html = _make_builder(waves=[wave]).render()
    assert "<th>Wave</th>" in html, "<th>Wave</th> が見つかりません。"
    assert "<th>Task 数</th>" in html, "<th>Task 数</th> が見つかりません。"
    assert "<th>状態</th>" in html, "<th>状態</th> が見つかりません。"


def test_v3_contains_tbody():
    """V-3 テーブルに <tbody> が存在すること。"""
    wave = _make_wave()
    html = _make_builder(waves=[wave]).render()
    assert "<tbody>" in html, "<tbody> が見つかりません。"


# ─────────────────────────────────────────────
# Wave 番号の表示確認
# ─────────────────────────────────────────────


def test_v3_wave_number_displayed():
    """Wave 番号「Wave 1」が行に表示されること。

    仕様: design.md §4 V-3 DOM 構成案「<td>Wave 1</td>」
    """
    wave = _make_wave(wave_number="1")
    html = _make_builder(waves=[wave]).render()
    assert "Wave 1" in html, "「Wave 1」が HTML に見つかりません。"


def test_v3_wave_number_15_displayed():
    """Wave 番号「Wave 1.5」が行に表示されること（小数点形式）。"""
    wave = _make_wave(wave_number="1.5")
    html = _make_builder(waves=[wave]).render()
    assert "Wave 1.5" in html, "「Wave 1.5」が HTML に見つかりません。"


def test_v3_wave_number_3_displayed():
    """Wave 番号「Wave 3」が行に表示されること。"""
    wave = _make_wave(wave_number="3")
    html = _make_builder(waves=[wave]).render()
    assert "Wave 3" in html, "「Wave 3」が HTML に見つかりません。"


# ─────────────────────────────────────────────
# Task 数の表示確認
# ─────────────────────────────────────────────


def test_v3_task_count_displayed():
    """Task 数が行に表示されること。

    仕様: design.md §4 V-3 DOM 構成案「<td>5</td>」（task_count の値）
    """
    wave = _make_wave(task_count=5)
    html = _make_builder(waves=[wave]).render()
    assert ">5<" in html, "Task 数「5」が HTML に見つかりません。"


def test_v3_task_count_zero_displayed():
    """Task 数 0 が行に表示されること（境界値テスト）。"""
    wave = _make_wave(task_count=0)
    html = _make_builder(waves=[wave]).render()
    assert ">0<" in html, "Task 数「0」が HTML に見つかりません。"


def test_v3_task_count_large_displayed():
    """Task 数が大きい場合も正しく表示されること。"""
    wave = _make_wave(task_count=12)
    html = _make_builder(waves=[wave]).render()
    assert ">12<" in html, "Task 数「12」が HTML に見つかりません。"


# ─────────────────────────────────────────────
# 状態バッジ確認（R-4: 状態値 4 値）
# ─────────────────────────────────────────────


def test_v3_status_badge_in_progress():
    """in-progress Wave に状態バッジ（data-status="in-progress"）が表示されること。

    対応完了条件: W3-B5-T14「状態値が design.md §5 Wave の状態決定ロジックに従う」
    """
    wave = _make_wave(status="in-progress")
    html = _make_builder(waves=[wave]).render()
    assert 'data-status="in-progress"' in html, 'data-status="in-progress" が見つかりません。'
    assert "進行中" in html, "状態バッジの日本語ラベル「進行中」が見つかりません。"


def test_v3_status_badge_completed():
    """completed Wave に状態バッジ（data-status="completed"）と「完了」が表示されること。"""
    wave = _make_wave(status="completed")
    html = _make_builder(waves=[wave]).render()
    assert 'data-status="completed"' in html, 'data-status="completed" が見つかりません。'
    assert "完了" in html, "状態バッジの日本語ラベル「完了」が見つかりません。"


def test_v3_status_badge_blocked():
    """blocked Wave に状態バッジ（data-status="blocked"）と「ブロック中」が表示されること。"""
    wave = _make_wave(status="blocked")
    html = _make_builder(waves=[wave]).render()
    assert 'data-status="blocked"' in html, 'data-status="blocked" が見つかりません。'
    assert "ブロック中" in html, "状態バッジの日本語ラベル「ブロック中」が見つかりません。"


def test_v3_status_badge_not_started():
    """not-started Wave に状態バッジ（data-status="not-started"）と「未着手」が表示されること。"""
    wave = _make_wave(status="not-started")
    html = _make_builder(waves=[wave]).render()
    assert 'data-status="not-started"' in html, 'data-status="not-started" が見つかりません。'
    assert "未着手" in html, "状態バッジの日本語ラベル「未着手」が見つかりません。"


def test_v3_badge_has_span_class():
    """状態バッジが <span class="badge" data-status="..."> 形式であること。"""
    wave = _make_wave(status="in-progress")
    html = _make_builder(waves=[wave]).render()
    assert '<span class="badge" data-status=' in html, (
        '<span class="badge" data-status=...> 形式のバッジが見つかりません。'
    )


# ─────────────────────────────────────────────
# アンカーリンク確認（R-6: <a href="#v4-tasks">）
# ─────────────────────────────────────────────


def test_v3_anchor_link_to_v4_tasks():
    """V-3 セクションに <a href="#v4-tasks"> リンクが存在すること。

    対応完了条件: W3-B5-T14「<a href="#v4-tasks"> リンクが張られている」
    仕様: design.md §4 ナビゲーション「V-3 → V-4」
    """
    wave = _make_wave()
    html = _make_builder(waves=[wave]).render()
    assert 'href="#v4-tasks"' in html, (
        'href="#v4-tasks" が見つかりません。\n'
        "V-3 から V-4 へのアンカーリンクが必要です（design.md §4 ナビゲーション）。"
    )


# ─────────────────────────────────────────────
# <tr data-wave> 属性確認
# ─────────────────────────────────────────────


def test_v3_row_has_data_wave_attribute():
    """<tr data-wave="1"> 属性が各行に存在すること。

    仕様: design.md §4 V-3 DOM 構成案「<tr data-wave="1">」
    """
    wave = _make_wave(wave_number="1")
    html = _make_builder(waves=[wave]).render()
    assert 'data-wave="1"' in html, (
        'data-wave="1" 属性が <tr> タグに見つかりません。'
    )


def test_v3_row_data_wave_attribute_15():
    """Wave 1.5 の場合 <tr data-wave="1.5"> 属性が存在すること。"""
    wave = _make_wave(wave_number="1.5")
    html = _make_builder(waves=[wave]).render()
    assert 'data-wave="1.5"' in html, (
        'data-wave="1.5" 属性が見つかりません。'
    )


# ─────────────────────────────────────────────
# h2 見出し確認
# ─────────────────────────────────────────────


def test_v3_section_has_h2_heading():
    """V-3 セクションに <h2> 見出しが存在すること。

    仕様: design.md §4 V-3 DOM 構成案「<h2>Wave 一覧（B-5）</h2>」
    """
    wave = _make_wave(milestone="B-5")
    html = _make_builder(waves=[wave]).render()
    assert "<h2>" in html, "V-3 セクションに <h2> が見つかりません。"
    assert "B-5" in html, "<h2> の見出しに Milestone 名「B-5」が含まれていません。"


def test_v3_h2_heading_contains_wave_list_label():
    """V-3 セクションの <h2> に「Wave 一覧」が含まれること。

    仕様: design.md §4 V-3 DOM 構成案「<h2>Wave 一覧（B-5）</h2>」
    """
    wave = _make_wave(milestone="B-5")
    html = _make_builder(waves=[wave]).render()
    assert "Wave 一覧" in html, "V-3 の見出しに「Wave 一覧」が見つかりません。"


# ─────────────────────────────────────────────
# 複数 Wave の表示
# ─────────────────────────────────────────────


def test_v3_multiple_waves_same_milestone():
    """同じ Milestone の複数 Wave が全て表示されること。"""
    wave1 = _make_wave(milestone="B-5", wave_number="1", status="completed")
    wave2 = _make_wave(milestone="B-5", wave_number="2", status="in-progress")
    wave3 = _make_wave(milestone="B-5", wave_number="3", status="not-started")
    html = _make_builder(waves=[wave1, wave2, wave3]).render()
    assert "Wave 1" in html, "Wave 1 が表示されていません。"
    assert "Wave 2" in html, "Wave 2 が表示されていません。"
    assert "Wave 3" in html, "Wave 3 が表示されていません。"


def test_v3_waves_grouped_by_milestone():
    """異なる Milestone の Wave がそれぞれのセクションに表示されること。

    B-4 の Wave は v3-waves-B-4 に、B-5 の Wave は v3-waves-B-5 にグループ化される。
    """
    wave_b4 = _make_wave(milestone="B-4", wave_number="7")
    wave_b5 = _make_wave(milestone="B-5", wave_number="1")
    html = _make_builder(waves=[wave_b4, wave_b5]).render()

    # B-4 セクション内に Wave 7 が表示されること
    assert '<section id="v3-waves-B-4">' in html, "B-4 セクションが見つかりません。"
    # B-5 セクション内に Wave 1 が表示されること
    assert '<section id="v3-waves-B-5">' in html, "B-5 セクションが見つかりません。"
    assert "Wave 7" in html, "Wave 7 が表示されていません。"
    assert "Wave 1" in html, "Wave 1 が表示されていません。"


# ─────────────────────────────────────────────
# Empty State（Wave 0 件）
# ─────────────────────────────────────────────


def test_v3_no_section_when_no_waves():
    """Wave が 0 件のとき V-3 セクションが生成されないこと。

    V-2 が empty state でセクションを出力するのとは異なり、
    V-3 は Wave データがない場合はセクション自体を生成しない（Milestone ごと生成のため）。
    """
    html = _make_builder(waves=[]).render()
    assert '<section id="v3-waves-' not in html, (
        "Wave が 0 件のとき V-3 セクションが生成されています。"
    )


# ─────────────────────────────────────────────
# HTML エスケープ確認
# ─────────────────────────────────────────────


def test_v3_milestone_name_html_escaped():
    """Milestone 名に HTML 特殊文字が含まれる場合にエスケープされること。"""
    from dashboard.models import WaveInfo

    # 特殊文字を含む Milestone 名（実際には起きないが安全性確認）
    wave = WaveInfo(
        milestone="B&5",
        wave_number="1",
        task_count=3,
        status="not-started",
    )
    html = _make_builder(waves=[wave]).render()
    # & がエスケープされていること（そのまま & が HTML に出力されない）
    # セクション id は属性値なのでエスケープ必要
    # Wave 一覧の見出し・テーブル行のテキストにも & が生データで出ないこと
    assert "&amp;" in html or "B&amp;5" in html or "B&5" not in html.split('id="v3-waves-')[0].split('<section')[-1], (
        "Milestone 名の HTML エスケープが行われていない可能性があります。"
    )


# ─────────────────────────────────────────────
# 回帰テスト: V-1 / V-2 / parser_errors が壊れていないこと
# ─────────────────────────────────────────────


def test_v1_section_not_broken_by_v3():
    """V-3 実装後も V-1 セクションが正常に生成されること（回帰テスト）。"""
    wave = _make_wave()
    html = _make_builder(waves=[wave]).render()
    assert '<section id="v1-project-summary">' in html, (
        "V-3 追加後に V-1 セクションが消えています。回帰テスト失敗。"
    )


def test_v2_section_not_broken_by_v3():
    """V-3 実装後も V-2 セクションが正常に生成されること（回帰テスト）。"""
    from dashboard.models import MilestoneInfo, WaveInfo

    ms = MilestoneInfo(name="B-5", current_step="BUILDING", status="in-progress")
    wave = WaveInfo(milestone="B-5", wave_number="1", task_count=5, status="in-progress")
    from dashboard.builder import DashboardBuilder
    from dashboard.models import DashboardData

    data = DashboardData(milestones=[ms], waves=[wave])
    html = DashboardBuilder(data).render()
    assert '<section id="v2-milestones">' in html, (
        "V-3 追加後に V-2 セクションが消えています。回帰テスト失敗。"
    )


def test_parser_errors_not_broken_by_v3():
    """V-3 実装後もパーサエラーセクションが正常に機能すること（回帰テスト）。"""
    from dashboard.builder import DashboardBuilder
    from dashboard.models import DashboardData

    data = DashboardData(parser_errors=["GitHistory: git command not found"])
    html = DashboardBuilder(data).render()
    assert '<section id="parser-errors">' in html, (
        "V-3 追加後に parser-errors セクションが壊れています。"
    )


def test_v3_position_before_parser_errors():
    """V-3 セクションが parser-errors セクションより前に配置されること。

    仕様: design.md §8 HTML 構造「V-3 → V-4 → parser-errors の順」
    """
    from dashboard.builder import DashboardBuilder
    from dashboard.models import DashboardData, WaveInfo

    wave = WaveInfo(milestone="B-5", wave_number="1", task_count=5, status="in-progress")
    data = DashboardData(
        waves=[wave],
        parser_errors=["test error"],
    )
    html = DashboardBuilder(data).render()
    v3_pos = html.find('<section id="v3-waves-B-5">')
    errors_pos = html.find('<section id="parser-errors">')
    assert v3_pos != -1, "V-3 セクションが見つかりません。"
    assert errors_pos != -1, "parser-errors セクションが見つかりません。"
    assert v3_pos < errors_pos, (
        f"V-3（位置 {v3_pos}）が parser-errors（位置 {errors_pos}）より後ろにあります。\n"
        "V-3 は parser-errors より前に配置してください（design.md §8）。"
    )
