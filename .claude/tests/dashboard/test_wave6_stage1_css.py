"""test_wave6_stage1_css.py - CSS スタイリング基盤の smoke test（W6-B5-T33）

対応仕様:
  - docs/specs/b4-dashboard/wave6/tasks.md §6 T33
  - docs/specs/b4-dashboard/wave6/design.md §6（Radix Colors 適用設計）
  - docs/specs/b4-dashboard/wave6/design.md §7（CSS 構造設計）
"""

from __future__ import annotations

import sys
from pathlib import Path

# .claude/scripts を sys.path に追加（既存テストと同じパターン）
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from dashboard.builder import DashboardBuilder
from dashboard.models import DashboardData


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
        generated_at="2026-06-25T00:00:00",
        parser_errors=[],
    )
    return DashboardBuilder(data)


def test_render_style_method_exists() -> None:
    """DashboardBuilder._render_style が呼び出し可能であること。

    design.md §7: builder.py 内の _render_style() メソッドで返す。
    """
    builder = _make_empty_builder()
    assert callable(getattr(builder, "_render_style", None)), (
        "DashboardBuilder._render_style が定義されていない"
    )


def test_render_style_returns_style_tag() -> None:
    """_render_style() の出力に <style> と </style> が含まれること。

    design.md §7: _render_style() は <style>...</style> を含む 1 つの文字列を返す。
    """
    builder = _make_empty_builder()
    style = builder._render_style()
    assert "<style>" in style, "_render_style() の出力に <style> が含まれない"
    assert "</style>" in style, "_render_style() の出力に </style> が含まれない"


def test_render_style_size_under_10kb() -> None:
    """_render_style() の出力が 16,384 バイト（16 KiB）以下であること。

    Wave 6 NFR-W6-3「追加 CSS ≤ 10 KB」は Wave 7 NFR-W7-1 v0.2.4 で
    16,384 bytes（16 KiB）+ SHOULD に上書き継承された。テスト名は歴史的経緯のため維持。
    """
    builder = _make_empty_builder()
    style = builder._render_style()
    byte_size = len(style.encode("utf-8"))
    assert byte_size <= 16_384, (
        f"_render_style() のサイズが 16,384 バイト超過: {byte_size} バイト（NFR-W7-1 v0.2.4）"
    )


def test_render_style_contains_layer1_gray_var() -> None:
    """_render_style() の出力に Layer 1 Radix gray スケール変数が含まれること。

    design.md §6 Layer 1: gray 1〜12 の 12 変数を :root に転記する。
    """
    builder = _make_empty_builder()
    style = builder._render_style()
    assert "--gray-1:" in style, "_render_style() に Layer 1 変数 --gray-1: が含まれない"
    assert "--gray-12:" in style, "_render_style() に Layer 1 変数 --gray-12: が含まれない"


def test_render_style_contains_layer2_alias() -> None:
    """_render_style() の出力に Layer 2 意味ベースエイリアス変数が含まれること。

    design.md §6 Layer 2: --color-bg-page / --color-text-primary 等を定義する。
    """
    builder = _make_empty_builder()
    style = builder._render_style()
    assert "--color-bg-page:" in style, (
        "_render_style() に Layer 2 変数 --color-bg-page: が含まれない"
    )
    assert "--color-text-primary:" in style, (
        "_render_style() に Layer 2 変数 --color-text-primary: が含まれない"
    )


# ── 以下 T-S1-1〜T-S1-11 の正式テスト（formal / W6-B5-T35）──────────────────
# 参照: docs/specs/b4-dashboard/wave6/design.md §14「Stage 1 単体テスト」テーブル


def test_t_s1_01_layer1_gray_1() -> None:
    """T-S1-1: _render_style() の戻り値に --gray-1 が含まれること。

    design.md §14 T-S1-1: assert '--gray-1' in style
    """
    builder = _make_empty_builder()
    style = builder._render_style()
    assert "--gray-1" in style, "_render_style() に --gray-1 が含まれない"


def test_t_s1_02_layer1_gray_12() -> None:
    """T-S1-2: _render_style() の戻り値に --gray-12 が含まれること。

    design.md §14 T-S1-2: assert '--gray-12' in style
    """
    builder = _make_empty_builder()
    style = builder._render_style()
    assert "--gray-12" in style, "_render_style() に --gray-12 が含まれない"


def test_t_s1_03_layer1_blue_full_range() -> None:
    """T-S1-3: _render_style() に --blue-1 〜 --blue-12 が全て含まれること。

    design.md §14 T-S1-3: for i in range(1, 13): assert f'--blue-{i}' in style
    """
    builder = _make_empty_builder()
    style = builder._render_style()
    for i in range(1, 13):
        assert f"--blue-{i}" in style, f"_render_style() に --blue-{i} が含まれない"


def test_t_s1_04_layer1_green_full_range() -> None:
    """T-S1-4: _render_style() に --green-1 〜 --green-12 が全て含まれること。

    design.md §14 T-S1-4: for i in range(1, 13): assert f'--green-{i}' in style
    """
    builder = _make_empty_builder()
    style = builder._render_style()
    for i in range(1, 13):
        assert f"--green-{i}" in style, f"_render_style() に --green-{i} が含まれない"


def test_t_s1_05_layer1_amber_full_range() -> None:
    """T-S1-5: _render_style() に --amber-1 〜 --amber-12 が全て含まれること。

    design.md §14 T-S1-5: for i in range(1, 13): assert f'--amber-{i}' in style
    """
    builder = _make_empty_builder()
    style = builder._render_style()
    for i in range(1, 13):
        assert f"--amber-{i}" in style, f"_render_style() に --amber-{i} が含まれない"


def test_t_s1_06_dark_media_query_count() -> None:
    """T-S1-6: _render_style() に @media (prefers-color-scheme: dark) が 2 箇所以上含まれること。

    design.md §14 T-S1-6: assert style.count('@media (prefers-color-scheme: dark)') >= 2
    """
    builder = _make_empty_builder()
    style = builder._render_style()
    count = style.count("@media (prefers-color-scheme: dark)")
    assert count >= 2, (
        f"_render_style() の @media (prefers-color-scheme: dark) が {count} 箇所 / 期待: 2 以上"
    )


def test_t_s1_07_layer2_color_bg_page() -> None:
    """T-S1-7: _render_style() に --color-bg-page が含まれること（Layer 2 エイリアス存在確認）。

    design.md §14 T-S1-7: assert '--color-bg-page' in style
    """
    builder = _make_empty_builder()
    style = builder._render_style()
    assert "--color-bg-page" in style, "_render_style() に --color-bg-page が含まれない"


def test_t_s1_08_layer2_color_status_completed_bg() -> None:
    """T-S1-8: _render_style() に --color-status-completed-bg が含まれること。

    design.md §14 T-S1-8: assert '--color-status-completed-bg' in style
    """
    builder = _make_empty_builder()
    style = builder._render_style()
    assert "--color-status-completed-bg" in style, (
        "_render_style() に --color-status-completed-bg が含まれない"
    )


def test_t_s1_09_render_contains_main_landmark() -> None:
    """T-S1-9: render() 出力に <main id="main-content"> が含まれること。

    design.md §14 T-S1-9: assert '<main id="main-content">' in html
    """
    builder = _make_empty_builder()
    html = builder.render()
    assert '<main id="main-content">' in html, (
        "render() 出力に <main id=\"main-content\"> が含まれない"
    )


def test_t_s1_10_render_contains_nav_landmark() -> None:
    """T-S1-10: render() 出力に <nav id="nav-landmarks"> が含まれること。

    design.md §14 T-S1-10: assert '<nav id="nav-landmarks">' in html
    """
    builder = _make_empty_builder()
    html = builder.render()
    assert '<nav id="nav-landmarks">' in html, (
        "render() 出力に <nav id=\"nav-landmarks\"> が含まれない"
    )


def test_t_s1_11_css_size_under_10kb() -> None:
    """T-S1-11: CSS 文字列サイズが 16,384 バイト（16 KiB）以下であること。

    Wave 6 T-S1-11 起源時は 10,240 バイト（10 KB）上限。
    Wave 7 NFR-W7-1 v0.2.4 で 16,384 バイト（16 KiB）+ SHOULD に上書き継承。
    """
    builder = _make_empty_builder()
    style = builder._render_style()
    byte_size = len(style.encode("utf-8"))
    assert byte_size <= 16_384, (
        f"CSS サイズが 16,384 バイト超過: {byte_size} バイト / 上限: 16,384 バイト（NFR-W7-1 v0.2.4）"
    )
