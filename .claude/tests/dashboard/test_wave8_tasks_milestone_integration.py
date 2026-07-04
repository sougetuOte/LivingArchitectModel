"""test_wave8_tasks_milestone_integration.py - tasks.md 由来 Milestone 反映テスト（W8-B5-T106）

対応仕様:
  - docs/specs/b4-dashboard/wave8/requirements.md AC-W8-3（FR-W8-1 対応）
  - docs/specs/b4-dashboard/wave8/design.md §4「MilestoneSourceMerger 詳細設計」
  - docs/specs/b4-dashboard/wave8/tasks.md §6 T106

検証内容:
  SESSION_STATE.md に Task ID が存在しない Milestone（B-4 / B-6）が tasks.md に
  存在する場合、その Milestone が V-2 Milestone カードおよび V-4 フィルタ選択肢に
  status="unknown" で反映されること。

fixture:
  .claude/tests/dashboard/fixtures/wave8/session_minimal.txt（B-5 のみ Task ID）
  .claude/tests/dashboard/fixtures/wave8/tasks_with_extra.txt（B-4/B-5/B-6 Task ID）

責務境界（T105 との重複回避）:
  T105（test_wave8_v2_v4_ssot_alignment.py）は「V-2/V-4 の Milestone 集合が
  常に一致する」という SSOT 一致要件を検証する。
  T106（本ファイル）は「tasks.md にのみ存在する Milestone が実際に
  dashboard に表示される」という反映要件（データソース統合の実効性）を検証する。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# .claude/scripts を sys.path に追加（既存テストと同一パターン）
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_BUILD_SCRIPT = _PROJECT_ROOT / ".claude" / "scripts" / "build_dashboard.py"
_FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "wave8"


def _load_build_module():
    """build_dashboard.py を importlib でロードして build() 関数を取得する。

    既存パターン踏襲: test_wave2_integration.py::TestBuildFunctionWithParsers。
    """
    spec = importlib.util.spec_from_file_location("build_dashboard_w8", _BUILD_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _build_controlled_root(tmp_path: Path, *, session_text: str, tasks_text: str) -> Path:
    """fixture テキストから制御済みプロジェクトルートを構築する。

    構造:
      <root>/.claude/current-phase.md
      <root>/SESSION_STATE.md          ← session_text
      <root>/docs/specs/wave8-fixture/tasks.md  ← tasks_text
    """
    root = tmp_path / "project"
    root.mkdir()

    dotclaude = root / ".claude"
    dotclaude.mkdir()
    (dotclaude / "current-phase.md").write_text(
        "# Current Phase\n\n**BUILDING**\n", encoding="utf-8"
    )

    (root / "SESSION_STATE.md").write_text(session_text, encoding="utf-8")

    specs_dir = root / "docs" / "specs" / "wave8-fixture"
    specs_dir.mkdir(parents=True)
    (specs_dir / "tasks.md").write_text(tasks_text, encoding="utf-8")

    return root


@pytest.fixture
def fixture_texts() -> tuple[str, str]:
    """session_minimal.txt / tasks_with_extra.txt の内容を読み込んで返す。"""
    session_text = (_FIXTURES_DIR / "session_minimal.txt").read_text(encoding="utf-8")
    tasks_text = (_FIXTURES_DIR / "tasks_with_extra.txt").read_text(encoding="utf-8")
    return session_text, tasks_text


# ─────────────────────────────────────────────
# 単体テスト（Merger）: tasks 由来のみのエントリが status="unknown"
# ─────────────────────────────────────────────


def test_merger_unit_tasks_only_entries_are_unknown_status():
    """session=[B-5] / tasks=[B-4, B-5, B-6] のとき、B-4/B-6 が status="unknown" で
    補完されること（design.md §4 / AC-W8-3 検証手段 1）。

    T103（test_wave8_merger.py）の一般ケースとは別に、本 Wave 8 fixture が想定する
    具体的なシナリオ（B-4/B-5/B-6 3 Milestone 構成）で再現することを明示的に確認する。
    """
    from dashboard.merger import MilestoneSourceMerger
    from dashboard.models import MilestoneInfo

    session_milestones = [
        MilestoneInfo(name="B-5", current_step="UNKNOWN", status="in-progress"),
    ]
    task_milestone_names = ["B-4", "B-5", "B-6"]

    result = MilestoneSourceMerger(
        session_milestones=session_milestones,
        task_milestone_names=task_milestone_names,
    ).get_milestones()

    by_name = {ms.name: ms for ms in result}
    assert set(by_name) == {"B-4", "B-5", "B-6"}
    assert by_name["B-4"].status == "unknown"
    assert by_name["B-6"].status == "unknown"
    assert by_name["B-5"].status == "in-progress"  # session 由来は保持される


# ─────────────────────────────────────────────
# 統合テスト（dashboard.html）: B-4 が V-2 / V-4 に表示される
# ─────────────────────────────────────────────


def test_integration_html_contains_b4_milestone_card(tmp_path, fixture_texts):
    """生成 HTML に <article class="milestone-card" data-milestone="B-4"> が
    含まれること（AC-W8-3 検証手段 2 / grep パターン: r'data-milestone="B-4"'）。
    """
    session_text, tasks_text = fixture_texts
    root = _build_controlled_root(tmp_path, session_text=session_text, tasks_text=tasks_text)
    mod = _load_build_module()

    output = tmp_path / "dashboard.html"
    mod.build(project_root=root, output_path=output)
    html = output.read_text(encoding="utf-8")

    assert 'data-milestone="B-4"' in html, (
        "tasks.md にのみ存在する Milestone B-4 が V-2 カードに反映されていません。"
    )


def test_integration_html_contains_b4_filter_option(tmp_path, fixture_texts):
    """V-4 フィルタに <option value="B-4"> が含まれること
    （AC-W8-3 検証手段 2 / grep パターン: r'<option[^>]*value="B-4"'）。
    """
    session_text, tasks_text = fixture_texts
    root = _build_controlled_root(tmp_path, session_text=session_text, tasks_text=tasks_text)
    mod = _load_build_module()

    output = tmp_path / "dashboard.html"
    mod.build(project_root=root, output_path=output)
    html = output.read_text(encoding="utf-8")

    assert '<option value="B-4">' in html, (
        "tasks.md にのみ存在する Milestone B-4 が V-4 フィルタ選択肢に反映されていません。"
    )


def test_integration_html_contains_unknown_status_badge(tmp_path, fixture_texts):
    """B-4 の Milestone カードに data-status="unknown" バッジが描画されていること
    （AC-W8-3 追加期待 / I-W-N2 / grep パターン: r'data-status="unknown"'）。
    """
    session_text, tasks_text = fixture_texts
    root = _build_controlled_root(tmp_path, session_text=session_text, tasks_text=tasks_text)
    mod = _load_build_module()

    output = tmp_path / "dashboard.html"
    mod.build(project_root=root, output_path=output)
    html = output.read_text(encoding="utf-8")

    assert 'data-status="unknown"' in html, (
        "tasks.md 由来のみの Milestone に status=\"unknown\" バッジが描画されていません。"
    )


def test_integration_css_defines_unknown_badge_rule(tmp_path, fixture_texts):
    """生成 HTML の <style> ブロックに .badge[data-status="unknown"] の CSS ルールが
    存在すること（AC-W8-3 CSS 適用確認）。
    """
    session_text, tasks_text = fixture_texts
    root = _build_controlled_root(tmp_path, session_text=session_text, tasks_text=tasks_text)
    mod = _load_build_module()

    output = tmp_path / "dashboard.html"
    mod.build(project_root=root, output_path=output)
    html = output.read_text(encoding="utf-8")

    assert '.badge[data-status="unknown"]' in html, (
        "<style> 内に .badge[data-status=\"unknown\"] の CSS ルールが見つかりません。"
    )


# ─────────────────────────────────────────────
# 境界確認: T105 との重複回避（本ファイル固有の責務を明示）
# ─────────────────────────────────────────────


def test_b5_present_alongside_tasks_only_milestones(tmp_path, fixture_texts):
    """session と tasks 両方に存在する B-5 も、tasks 由来のみの B-4/B-6 と共存して
    表示されること（tasks.md 由来 Milestone の「反映」自体を検証する本ファイルの責務。
    V-2/V-4 の集合一致そのものは test_wave8_v2_v4_ssot_alignment.py が担う）。
    """
    session_text, tasks_text = fixture_texts
    root = _build_controlled_root(tmp_path, session_text=session_text, tasks_text=tasks_text)
    mod = _load_build_module()

    output = tmp_path / "dashboard.html"
    mod.build(project_root=root, output_path=output)
    html = output.read_text(encoding="utf-8")

    for name in ("B-4", "B-5", "B-6"):
        assert f'data-milestone="{name}"' in html, (
            f"Milestone {name} の data-milestone 属性が HTML に見つかりません。"
        )
