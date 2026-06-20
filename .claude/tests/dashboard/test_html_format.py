"""test_html_format.py - 単一 HTML 出力形式（CSS/JS インライン化）のテスト（W1-B5-T4）

対応仕様:
  - docs/specs/b4-dashboard/design.md §8「CSS/JS 埋め込み方針」
  - docs/specs/b4-dashboard/design.md §8「単一 HTML ファイルの構造」
  - docs/specs/b4-dashboard/requirements.md FR-5（オフライン動作 MUST）
  - docs/specs/b4-dashboard/requirements.md NFR-1（500KB 未満）
  - docs/specs/b4-dashboard/tasks.md §3「W1-B5-T4 完了条件」
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# .claude/scripts を sys.path に追加（既存テストと同じパターン）
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# プロジェクトルートの推定
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

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
# <style> タグ存在確認
# ─────────────────────────────────────────────


def test_render_contains_style_tag():
    """生成 HTML に <style> タグが存在すること。

    対応完了条件: W1-B5-T4「生成 HTML が <style> タグで inline CSS を含む」
    対応仕様: design.md §8「CSS と JavaScript は <style> / <script> タグで inline 埋め込み」
    """
    html = _make_builder().render()
    assert "<style>" in html, (
        "生成 HTML に <style> タグが見つかりません。\n"
        "builder.py の <head> 内に inline CSS を <style> タグで追加してください。"
    )


# ─────────────────────────────────────────────
# badge CSS ルール存在確認（4 状態値）
# ─────────────────────────────────────────────


def test_style_contains_badge_completed():
    """.badge[data-status="completed"] が <style> 内に含まれること。

    対応仕様: design.md §8「.badge[data-status="completed"] { background: #28a745; ... }」
    """
    html = _make_builder().render()
    assert '.badge[data-status="completed"]' in html, (
        '生成 HTML の <style> 内に .badge[data-status="completed"] が見つかりません。\n'
        "design.md §8 の badge CSS ルールを追加してください。"
    )


def test_style_contains_badge_in_progress():
    """.badge[data-status="in-progress"] が <style> 内に含まれること。

    対応仕様: design.md §8「.badge[data-status="in-progress"] { background: #007bff; ... }」
    """
    html = _make_builder().render()
    assert '.badge[data-status="in-progress"]' in html, (
        '生成 HTML の <style> 内に .badge[data-status="in-progress"] が見つかりません。\n'
        "design.md §8 の badge CSS ルールを追加してください。"
    )


def test_style_contains_badge_blocked():
    """.badge[data-status="blocked"] が <style> 内に含まれること。

    対応仕様: design.md §8「.badge[data-status="blocked"] { background: #dc3545; ... }」
    """
    html = _make_builder().render()
    assert '.badge[data-status="blocked"]' in html, (
        '生成 HTML の <style> 内に .badge[data-status="blocked"] が見つかりません。\n'
        "design.md §8 の badge CSS ルールを追加してください。"
    )


def test_style_contains_badge_not_started():
    """.badge[data-status="not-started"] が <style> 内に含まれること。

    対応仕様: design.md §8「.badge[data-status="not-started"] { background: #6c757d; ... }」
    """
    html = _make_builder().render()
    assert '.badge[data-status="not-started"]' in html, (
        '生成 HTML の <style> 内に .badge[data-status="not-started"] が見つかりません。\n'
        "design.md §8 の badge CSS ルールを追加してください。"
    )


# ─────────────────────────────────────────────
# 外部依存なし確認（FR-5 / NFR-5）
# ─────────────────────────────────────────────


def test_render_has_no_link_tag():
    """生成 HTML に <link タグが存在しないこと（外部 CDN 参照チェック）。

    対応完了条件: W1-B5-T4「外部 link / script を参照していない」
    対応仕様: design.md §8「外部 CDN（Bootstrap, jQuery 等）を参照してはならない（MUST NOT）」
    """
    html = _make_builder().render()
    assert "<link" not in html, (
        "生成 HTML に <link タグが見つかりました。\n"
        "外部スタイルシートへの参照を削除し、inline <style> タグを使用してください。\n"
        f"検出箇所: {[line for line in html.splitlines() if '<link' in line]}"
    )


def test_render_has_no_external_script_src():
    """生成 HTML に https:// を含む <script src= が存在しないこと（外部 JS CDN チェック）。

    対応完了条件: W1-B5-T4「外部 link / script を参照していない」
    対応仕様: design.md §8「外部 CDN（Bootstrap, jQuery 等）を参照してはならない（MUST NOT）」
    """
    html = _make_builder().render()
    # https:// または http:// を含む script src 属性を検出
    import re
    pattern = r'<script\s[^>]*src=["\']https?://'
    matches = re.findall(pattern, html)
    assert len(matches) == 0, (
        "生成 HTML に外部 URL を参照する <script src=...> タグが見つかりました。\n"
        "外部 JS は使用せず、inline <script> タグを使用してください。\n"
        f"検出: {matches}"
    )


# ─────────────────────────────────────────────
# ファイルサイズ確認（NFR-1: 500KB 未満）
# ─────────────────────────────────────────────


def test_generated_html_file_size_under_500kb():
    """生成 HTML ファイルのサイズが 500KB（512,000 バイト）未満であること。

    対応完了条件: W1-B5-T4「stat docs/artifacts/dashboard/dashboard.html で 500KB 未満」
    対応仕様: requirements.md NFR-1「生成 HTML のファイルサイズが 500KB 未満」
    """
    dashboard_path = _PROJECT_ROOT / "docs" / "artifacts" / "dashboard" / "dashboard.html"
    assert dashboard_path.is_file(), (
        f"ダッシュボード HTML ファイルが見つかりません: {dashboard_path}\n"
        "python .claude/scripts/build_dashboard.py を実行して HTML を生成してください。"
    )
    size_bytes = os.path.getsize(str(dashboard_path))
    limit_bytes = 512_000  # 500KB = 512,000 バイト
    assert size_bytes < limit_bytes, (
        f"ダッシュボード HTML のファイルサイズが 500KB を超えています。\n"
        f"現在のサイズ: {size_bytes:,} バイト（{size_bytes / 1024:.1f} KB）\n"
        f"上限: {limit_bytes:,} バイト（500 KB）\n"
        "inline CSS/JS を最小限に保ち、外部リソースを使用しないようにしてください。"
    )
