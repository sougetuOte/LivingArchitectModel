"""test_build_dashboard.py - build_dashboard.py スケルトン + DashboardBuilder テスト（W1-B5-T2）

対応仕様:
  - docs/specs/b4-dashboard/design.md §6「ビルドコマンド設計」
  - docs/specs/b4-dashboard/design.md §9「エラー耐障害性設計」
  - docs/specs/b4-dashboard/tasks.md §3「W1-B5-T2 完了条件」
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

# .claude/scripts を sys.path に追加（test_base_parser.py と同じパターン）
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# プロジェクトルートの推定
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# ─────────────────────────────────────────────
# DashboardBuilder インポートテスト
# ─────────────────────────────────────────────


def test_dashboard_builder_importable():
    """DashboardBuilder を dashboard.builder からインポートできること。"""
    from dashboard.builder import DashboardBuilder  # noqa: F401


def test_dashboard_builder_render_returns_str():
    """DashboardBuilder(data).render() が str を返すこと。"""
    from dashboard.builder import DashboardBuilder
    from dashboard.models import DashboardData

    data = DashboardData(generated_at="2026-06-21T00:00:00")
    builder = DashboardBuilder(data)
    result = builder.render()
    assert isinstance(result, str)


def test_dashboard_builder_render_not_empty():
    """DashboardBuilder.render() が空文字列でないこと。"""
    from dashboard.builder import DashboardBuilder
    from dashboard.models import DashboardData

    data = DashboardData(generated_at="2026-06-21T00:00:00")
    result = DashboardBuilder(data).render()
    assert len(result) > 0


def test_dashboard_builder_render_contains_html_doctype():
    """render() の出力が DOCTYPE 宣言を含む HTML であること。"""
    from dashboard.builder import DashboardBuilder
    from dashboard.models import DashboardData

    data = DashboardData(generated_at="2026-06-21T00:00:00")
    html = DashboardBuilder(data).render()
    assert "<!DOCTYPE html>" in html or "<!doctype html>" in html.lower()


def test_dashboard_builder_render_contains_v1_placeholder():
    """render() の出力が T3 用の V-1 プレースホルダーを含むこと（<!-- V-1 placeholder -->）。"""
    from dashboard.builder import DashboardBuilder
    from dashboard.models import DashboardData

    data = DashboardData(generated_at="2026-06-21T00:00:00")
    html = DashboardBuilder(data).render()
    assert "V-1" in html or "v1-project-summary" in html


def test_dashboard_builder_data_attribute():
    """DashboardBuilder が data 属性を持つこと（T3 が data パラメータを利用できること）。"""
    from dashboard.builder import DashboardBuilder
    from dashboard.models import DashboardData

    data = DashboardData(generated_at="2026-06-21T00:00:00")
    builder = DashboardBuilder(data)
    assert builder.data is data


# ─────────────────────────────────────────────
# build_dashboard.py subprocess 実行テスト
# ─────────────────────────────────────────────


def test_build_dashboard_exits_with_0_or_1():
    """--project-root 付きで build_dashboard.py を実行すると exit code が 0 または 1 であること。

    exit code 2 は致命的エラー（HTML 未生成）を意味するため、許容しない。
    design.md §9 参照: 0=成功, 1=部分失敗（警告あり・HTML 生成は完了）, 2=致命的エラー
    """
    script = _PROJECT_ROOT / ".claude" / "scripts" / "build_dashboard.py"
    result = subprocess.run(
        [sys.executable, str(script), "--project-root", str(_PROJECT_ROOT)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode in (0, 1), (
        f"Expected exit code 0 or 1, got {result.returncode}\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )


def test_build_dashboard_generates_html_file():
    """build_dashboard.py 実行後に docs/artifacts/dashboard/dashboard.html が生成されること。"""
    script = _PROJECT_ROOT / ".claude" / "scripts" / "build_dashboard.py"
    subprocess.run(
        [sys.executable, str(script), "--project-root", str(_PROJECT_ROOT)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    output_html = _PROJECT_ROOT / "docs" / "artifacts" / "dashboard" / "dashboard.html"
    assert output_html.exists(), (
        f"Expected {output_html} to exist after running build_dashboard.py"
    )


def test_build_dashboard_stdout_contains_generated_message():
    """stdout に 'HTML generated at' または 'dashboard.html' の文字列が含まれること。"""
    script = _PROJECT_ROOT / ".claude" / "scripts" / "build_dashboard.py"
    result = subprocess.run(
        [sys.executable, str(script), "--project-root", str(_PROJECT_ROOT)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    combined_output = result.stdout + result.stderr
    assert "HTML generated at" in combined_output or "dashboard.html" in combined_output, (
        f"Expected 'HTML generated at' or 'dashboard.html' in output.\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )


def test_build_dashboard_creates_output_directory():
    """build_dashboard.py が docs/artifacts/dashboard/ ディレクトリを自動作成すること。"""
    output_dir = _PROJECT_ROOT / "docs" / "artifacts" / "dashboard"
    script = _PROJECT_ROOT / ".claude" / "scripts" / "build_dashboard.py"
    subprocess.run(
        [sys.executable, str(script), "--project-root", str(_PROJECT_ROOT)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert output_dir.is_dir(), (
        f"Expected directory {output_dir} to exist after running build_dashboard.py"
    )
