"""test_wave7_stage3_milestones.py - Wave 7 Stage 3 / FR-W7-4 / T53a 対応
`_render_v2_milestones()` の section/article 構造テスト。

対応仕様:
  - docs/specs/b4-dashboard/wave7/design.md §8 HTML 構造設計
  - docs/specs/b4-dashboard/wave7/tasks.md §6 T53 フィクスチャ実装例
  - design.md §3 A3-4: Milestone 名昇順（文字列辞書順）ソート確定

TDD Red ステップ先行: T51 未完成の段階では FAIL するのが正常動作。
Step 1 完了（T51 + T53a 両方完了）時点で全件 PASS を期待する。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# .claude/scripts を sys.path に追加（既存テストと同一パターン）
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


# ─────────────────────────────────────────────
# pytest fixture — DashboardData モック構築
# ─────────────────────────────────────────────


@pytest.fixture
def multi_milestone_data():
    """複数 Milestone を含む DashboardData モック。

    出現順 B-5 → B-4 を意図的に与え、_render_v2_milestones() 内の
    ソートが機能していることを検証可能にする。
    実 SESSION_STATE.md に依存しない（gitignore 対象のため再現性なし）。
    """
    from dashboard.models import DashboardData, MilestoneInfo

    return DashboardData(
        current_phase="PLANNING",
        milestones=[
            # 出現順: B-5 が先 → ソート後 B-4 が先になることを確認
            MilestoneInfo(name="B-5", current_step="UNKNOWN", status="in-progress"),
            MilestoneInfo(name="B-4", current_step="UNKNOWN", status="in-progress"),
        ],
        waves=[],
        tasks=[],
    )


@pytest.fixture
def single_milestone_data():
    """単一 Milestone を含む DashboardData モック。"""
    from dashboard.models import DashboardData, MilestoneInfo

    return DashboardData(
        current_phase="BUILDING",
        milestones=[
            MilestoneInfo(name="B-5", current_step="UNKNOWN", status="in-progress"),
        ],
        waves=[],
        tasks=[],
    )


@pytest.fixture
def empty_milestone_data():
    """Milestone 0 件の DashboardData モック（empty state 検証用）。"""
    from dashboard.models import DashboardData

    return DashboardData(
        current_phase="PLANNING",
        milestones=[],
        waves=[],
        tasks=[],
    )


# ─────────────────────────────────────────────
# テスト #1: ソート順確認（必須）
# ─────────────────────────────────────────────


def test_v2_renders_milestones_in_alphabetical_order(multi_milestone_data):
    """V-2 で Milestone が名前昇順（文字列辞書順）で並ぶこと。

    入力 [B-5, B-4] → 出力で data-milestone="B-4" の index が
    data-milestone="B-5" より小さい（B-4 が先に出現する）。

    design.md §3 A3-4: 文字列辞書順を採用。
    """
    from dashboard.builder import DashboardBuilder

    builder = DashboardBuilder(data=multi_milestone_data)
    html = builder._render_v2_milestones()

    assert 'data-milestone="B-4"' in html, 'data-milestone="B-4" が HTML に存在しません。'
    assert 'data-milestone="B-5"' in html, 'data-milestone="B-5" が HTML に存在しません。'
    assert html.index('data-milestone="B-4"') < html.index('data-milestone="B-5"'), (
        "B-4 が B-5 より前に出現するはず（昇順ソート）。"
        "design.md §3 A3-4 の文字列辞書順に従って `sorted(..., key=lambda m: m.name)` を実装してください。"
    )


# ─────────────────────────────────────────────
# テスト #2: data-milestone 属性付与（必須）
# ─────────────────────────────────────────────


def test_v2_renders_data_milestone_attribute(multi_milestone_data):
    """各 <article> に data-milestone="{name}" 属性が付与されること。

    design.md §8: <article class="milestone-card" data-milestone="{ms.name}">
    Wave 8+ でのフィルタ JS が data-milestone 属性を識別キーとして使用する想定。
    """
    from dashboard.builder import DashboardBuilder

    builder = DashboardBuilder(data=multi_milestone_data)
    html = builder._render_v2_milestones()

    assert 'data-milestone="B-4"' in html, 'B-4 の data-milestone 属性が見つかりません。'
    assert 'data-milestone="B-5"' in html, 'B-5 の data-milestone 属性が見つかりません。'


# ─────────────────────────────────────────────
# テスト #3: .milestone-card 件数確認（必須）
# ─────────────────────────────────────────────


def test_v2_renders_milestone_card_count_matches_milestones(multi_milestone_data):
    """`.milestone-card` 件数が Milestone 件数（2 件）と一致すること。

    design.md §8: Milestone 件数分 <article class="milestone-card"> が出力される。
    """
    from dashboard.builder import DashboardBuilder

    builder = DashboardBuilder(data=multi_milestone_data)
    html = builder._render_v2_milestones()

    card_count = html.count('class="milestone-card"')
    assert card_count == 2, (
        f"milestone-card の件数が 2 件であるべきですが {card_count} 件でした。"
        "Milestone 件数と一致していないか、クラス名が正しくありません。"
    )


# ─────────────────────────────────────────────
# テスト #4: .milestones-container ラッパ確認（必須）
# ─────────────────────────────────────────────


def test_v2_renders_milestones_container_wrapper(multi_milestone_data):
    """<div class="milestones-container"> ラッパ div が存在すること。

    design.md §8:
      <div class="milestones-container">
        <article class="milestone-card" ...>...</article>
        ...
      </div>
    """
    from dashboard.builder import DashboardBuilder

    builder = DashboardBuilder(data=multi_milestone_data)
    html = builder._render_v2_milestones()

    assert 'class="milestones-container"' in html, (
        '<div class="milestones-container"> が見つかりません。'
        "design.md §8 の HTML 構造を確認してください。"
    )


# ─────────────────────────────────────────────
# テスト #5: Step 列が current_phase に統一（必須）
# ─────────────────────────────────────────────


def test_v2_step_column_uses_current_phase(multi_milestone_data):
    """Step 列が current_phase の値（全 Milestone 共通）で表示されること。

    design.md §8: <span class="step">{self.data.current_phase}</span>
    全 Milestone で同一の current_phase 値が表示される（Milestone ごとの Step 値ではない）。
    """
    from dashboard.builder import DashboardBuilder

    builder = DashboardBuilder(data=multi_milestone_data)
    html = builder._render_v2_milestones()

    # current_phase = "PLANNING" が 2 件（各 Milestone カード）に現れること
    planning_count = html.count("PLANNING")
    assert planning_count >= 2, (
        f"PLANNING が {planning_count} 回しか出現しません（期待: 2 以上）。"
        "各 milestone-card に current_phase の値が表示されているか確認してください。"
    )


# ─────────────────────────────────────────────
# テスト #6: <h3> に Milestone 名表示（必須）
# ─────────────────────────────────────────────


def test_v2_renders_h3_with_milestone_name(multi_milestone_data):
    """各 <article> 内に <h3>{name}</h3> 形式で Milestone 名が表示されること。

    design.md §8: <h3>{ms.name}</h3>
    """
    from dashboard.builder import DashboardBuilder

    builder = DashboardBuilder(data=multi_milestone_data)
    html = builder._render_v2_milestones()

    assert "<h3>B-4</h3>" in html, "<h3>B-4</h3> が見つかりません。"
    assert "<h3>B-5</h3>" in html, "<h3>B-5</h3> が見つかりません。"


# ─────────────────────────────────────────────
# テスト #7: 単一 Milestone 入力時の挙動（必須）
# ─────────────────────────────────────────────


def test_v2_renders_single_milestone(single_milestone_data):
    """単一 Milestone 入力時（1 件）に 1 つの .milestone-card が出力されること。

    空でも複数でもない「1 件」の境界ケース。
    """
    from dashboard.builder import DashboardBuilder

    builder = DashboardBuilder(data=single_milestone_data)
    html = builder._render_v2_milestones()

    card_count = html.count('class="milestone-card"')
    assert card_count == 1, (
        f"単一 Milestone 入力で milestone-card が {card_count} 件生成されました（期待: 1 件）。"
    )
    assert 'data-milestone="B-5"' in html, "B-5 の data-milestone 属性が見つかりません。"


# ─────────────────────────────────────────────
# テスト #8: empty state（Milestone 0 件）（必須）
# ─────────────────────────────────────────────


def test_v2_renders_empty_state_when_no_milestones(empty_milestone_data):
    """空 milestones 入力時に empty state（「Milestone 情報なし」等）が維持されること。

    Wave 7 での HTML 構造変更後も empty state の文言は維持される（後方互換）。
    """
    from dashboard.builder import DashboardBuilder

    builder = DashboardBuilder(data=empty_milestone_data)
    html = builder._render_v2_milestones()

    assert "Milestone 情報なし" in html, (
        "milestones が空のとき「Milestone 情報なし」が表示されていません。"
    )
    # empty state では milestone-card を生成しない
    assert 'class="milestone-card"' not in html, (
        "milestones が空のとき milestone-card が生成されるのは誤りです。"
    )


# ─────────────────────────────────────────────
# テスト #9: status テキスト表示（任意）
# ─────────────────────────────────────────────


def test_v2_renders_status_text(multi_milestone_data):
    """<span class="status">{status}</span> で status が表示されること。

    design.md §8: <p>状態: <span class="status">{ms.status}</span></p>
    バッジではなく文字列（"in-progress" 等）として表示する。
    """
    from dashboard.builder import DashboardBuilder

    builder = DashboardBuilder(data=multi_milestone_data)
    html = builder._render_v2_milestones()

    assert 'class="status"' in html, (
        '<span class="status"> が見つかりません。'
        "status 値をテキストとして表示するクラスを確認してください。"
    )
    assert "in-progress" in html, "status 値「in-progress」が HTML に見つかりません。"


# ─────────────────────────────────────────────
# テスト #10: <section> 内の <h2> 見出し（任意）
# ─────────────────────────────────────────────


def test_v2_section_has_h2_heading(multi_milestone_data):
    """<section id="v2-milestones"> 内に <h2>Milestone 一覧</h2> が存在すること。

    design.md §8: <h2>Milestone 一覧</h2>
    """
    from dashboard.builder import DashboardBuilder

    builder = DashboardBuilder(data=multi_milestone_data)
    html = builder._render_v2_milestones()

    assert '<section id="v2-milestones">' in html, (
        '<section id="v2-milestones"> が見つかりません。'
    )
    assert "<h2>Milestone 一覧</h2>" in html, (
        "<h2>Milestone 一覧</h2> が見つかりません。"
    )
