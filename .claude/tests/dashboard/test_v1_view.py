"""test_v1_view.py - V-1 Project サマリービューのテスト（W1-B5-T3）

対応仕様:
  - docs/specs/b4-dashboard/design.md §4「V-1: Project サマリービュー」
  - docs/specs/b4-dashboard/design.md §8「出力形式」
  - docs/specs/b4-dashboard/tasks.md §3「W1-B5-T3 完了条件」
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# .claude/scripts を sys.path に追加（test_base_parser.py と同じパターン）
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# ─────────────────────────────────────────────
# テスト用フィクスチャ
# ─────────────────────────────────────────────


def _make_builder(generated_at: str = "2026-06-21T12:00:00"):
    """テスト用 DashboardBuilder を生成するヘルパー。"""
    from dashboard.builder import DashboardBuilder
    from dashboard.models import DashboardData

    data = DashboardData(generated_at=generated_at)
    return DashboardBuilder(data)


# ─────────────────────────────────────────────
# V-1 セクション存在確認
# ─────────────────────────────────────────────


def test_render_contains_v1_section_id():
    """生成 HTML に <section id="v1-project-summary"> が存在すること。

    対応完了条件: W1-B5-T3「<section id="v1-project-summary"> が存在」
    """
    html = _make_builder().render()
    assert '<section id="v1-project-summary">' in html, (
        "生成 HTML に <section id=\"v1-project-summary\"> が見つかりません。\n"
        "builder.py の render() に V-1 セクションを追加してください。"
    )


# ─────────────────────────────────────────────
# Project 名「LAM」の表示確認
# ─────────────────────────────────────────────


def test_render_contains_project_name_lam():
    """生成 HTML に「LAM」という文字列が含まれること。

    対応完了条件: W1-B5-T3「Project 名「LAM」が表示される」
    設計仕様: design.md §4「Project 名: ハードコード（"LAM"）」
    """
    html = _make_builder().render()
    assert "LAM" in html, (
        "生成 HTML に「LAM」が見つかりません。\n"
        "V-1 セクション内に Project 名「LAM」を表示してください。"
    )


# ─────────────────────────────────────────────
# タイムスタンプ（YYYY-MM-DD 形式）の存在確認
# ─────────────────────────────────────────────


def test_render_contains_timestamp_in_yyyy_mm_dd_format():
    """生成 HTML にタイムスタンプ（YYYY-MM-DD 形式の文字列）が含まれること。

    対応完了条件: W1-B5-T3「タイムスタンプが表示される（datetime.now() の結果）」
    """
    generated_at = "2026-06-21T12:34:56"
    html = _make_builder(generated_at=generated_at).render()
    # YYYY-MM-DD 形式のパターンがあるか確認（時刻部分はオプション）
    pattern = r"\d{4}-\d{2}-\d{2}"
    assert re.search(pattern, html) is not None, (
        "生成 HTML に YYYY-MM-DD 形式のタイムスタンプが見つかりません。\n"
        f"generated_at='{generated_at}' が HTML に反映されているか確認してください。"
    )


# ─────────────────────────────────────────────
# HTML 基本構造の確認
# ─────────────────────────────────────────────


def test_render_starts_with_doctype():
    """HTML が <!DOCTYPE html> で始まること。

    対応仕様: design.md §8「単一 HTML ファイルの構造」
    """
    html = _make_builder().render()
    assert html.strip().startswith("<!DOCTYPE html>"), (
        "生成 HTML が <!DOCTYPE html> で始まっていません。\n"
        f"先頭 50 文字: {html[:50]!r}"
    )


def test_render_contains_html_lang_ja():
    """生成 HTML に <html lang="ja"> が存在すること。

    対応仕様: design.md §8「<html lang="ja">」
    """
    html = _make_builder().render()
    assert '<html lang="ja">' in html, (
        "生成 HTML に <html lang=\"ja\"> が見つかりません。"
    )


def test_render_contains_meta_charset_utf8():
    """生成 HTML に <meta charset="UTF-8"> が存在すること（大文字小文字問わず可）。

    対応仕様: design.md §8「<meta charset="UTF-8">」
    """
    html = _make_builder().render()
    assert re.search(r'<meta\s+charset=["\']UTF-8["\']', html, re.IGNORECASE) is not None, (
        "生成 HTML に <meta charset=\"UTF-8\"> が見つかりません。"
    )
