"""test_visualize_skill.py - /build-dashboard スキルのテスト（W1-B5-T5）

対応仕様:
  docs/specs/b4-dashboard/design.md §6「/visualize スキル（FR-10 SHOULD）」
  docs/specs/b4-dashboard/tasks.md §3「W1-B5-T5 完了条件」
  設計 §13 UQ-3（スキル名確定・disable-model-invocation 書式）

確定スキル名: build-dashboard
  選定理由: 動詞+名詞型ケバブケース（full-review / wave-plan と同パターン）。
  /visualize より実際の動作（ダッシュボードをビルドする）が明確。
"""

from __future__ import annotations

from pathlib import Path

import pytest

# ─────────────────────────────────────────────
# パス定数
# ─────────────────────────────────────────────

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_SKILL_DIR = _REPO_ROOT / ".claude" / "skills" / "build-dashboard"
_SKILL_FILE = _SKILL_DIR / "SKILL.md"


# ─────────────────────────────────────────────
# ファイル存在テスト
# ─────────────────────────────────────────────


def test_skill_file_exists():
    """`.claude/skills/build-dashboard/SKILL.md` が存在すること。"""
    assert _SKILL_FILE.is_file(), (
        f"SKILL.md が存在しません: {_SKILL_FILE}\n"
        "Green フェーズで `.claude/skills/build-dashboard/SKILL.md` を作成してください。"
    )


# ─────────────────────────────────────────────
# フロントマター検証テスト
# ─────────────────────────────────────────────


def _read_skill_content() -> str:
    """SKILL.md の内容を読み込む（ファイルが存在しない場合は空文字）。"""
    if not _SKILL_FILE.is_file():
        return ""
    return _SKILL_FILE.read_text(encoding="utf-8")


def test_frontmatter_has_disable_model_invocation():
    """`disable-model-invocation: true` がフロントマターに含まれること（UQ-3 解決）。"""
    content = _read_skill_content()
    assert "disable-model-invocation: true" in content, (
        "フロントマターに `disable-model-invocation: true` が含まれていません。\n"
        "既存スキル（quick-save, ship, project-status）と書式を統一してください。"
    )


def test_frontmatter_name_matches_skill_name():
    """`name:` フィールドが `build-dashboard` と一致すること。"""
    content = _read_skill_content()
    # フロントマター内の name: フィールドを確認
    assert "name: build-dashboard" in content, (
        "フロントマターの `name:` フィールドが `build-dashboard` ではありません。\n"
        "UQ-3 で確定したスキル名と一致させてください。"
    )


def test_frontmatter_has_version():
    """`version:` フィールドがフロントマターに含まれること（既存スキルとの書式統一）。"""
    content = _read_skill_content()
    assert "version:" in content, (
        "フロントマターに `version:` フィールドが含まれていません。\n"
        "既存スキル（quick-save: 1.0.0 等）に準拠してください。"
    )


def test_frontmatter_has_description():
    """`description:` フィールドがフロントマターに含まれること。"""
    content = _read_skill_content()
    assert "description:" in content, (
        "フロントマターに `description:` フィールドが含まれていません。"
    )


# ─────────────────────────────────────────────
# build_dashboard.py への参照テスト
# ─────────────────────────────────────────────


def test_skill_references_build_dashboard_script():
    """`build_dashboard.py` への参照が SKILL.md に含まれること。"""
    content = _read_skill_content()
    assert "build_dashboard.py" in content, (
        "SKILL.md に `build_dashboard.py` への参照が含まれていません。\n"
        "スキルのフローで `build_dashboard.py` を呼び出す手順を記述してください。"
    )


def test_skill_describes_success_path():
    """成功時の出力パスが SKILL.md に記述されていること。"""
    content = _read_skill_content()
    # dashboard.html への参照または docs/artifacts への参照
    has_html_ref = "dashboard.html" in content or "docs/artifacts/dashboard" in content
    assert has_html_ref, (
        "SKILL.md に成功時の出力パス（dashboard.html または docs/artifacts/dashboard）が\n"
        "記述されていません。design.md §6 のフロー step 3 を参照してください。"
    )


def test_skill_describes_failure_path():
    """失敗時の対応が SKILL.md に記述されていること（エラー終了しない旨）。"""
    content = _read_skill_content()
    # 「失敗」「エラー」「error」のいずれかが本文に存在すること
    has_failure_desc = any(
        keyword in content
        for keyword in ("失敗", "エラー", "error", "Error", "警告", "warn")
    )
    assert has_failure_desc, (
        "SKILL.md に失敗時の対応が記述されていません。\n"
        "design.md §6 では「失敗: エラーメッセージを表示（スキル自体はエラー終了しない）」\n"
        "とされています。"
    )
