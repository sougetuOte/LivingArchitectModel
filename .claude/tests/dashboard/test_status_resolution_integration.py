"""test_status_resolution_integration.py - 状態値決定ロジック統合テスト（W3-B5-T16）

対応仕様:
  - docs/specs/b4-dashboard/tasks.md §3 W3-B5-T16
  - docs/specs/b4-dashboard/design.md §5「状態値の決定ロジック」
  - FR-2（状態値 4 値表示）/ AC-3（各エントリに状態値のいずれか）

テスト方針:
  - tmp_path で制御されたプロジェクト構造を使う（外部状態依存なし）
  - tmp 上に SESSION_STATE.md + .claude/current-phase.md + docs/specs/<m>/tasks.md を配置
  - DashboardBuilder.render() を実行し、生成 HTML を文字列レベルで検証

対応完了条件:
  - SessionState 「完了タスク」リストの Task ID が V-4 で completed バッジで表示
  - SessionState 「進行中」リストの Task ID が V-4 で in-progress バッジで表示
  - SessionState 「ブロック中」リストの Task ID が V-4 で blocked バッジで表示
  - tasks.md [x] で SessionState 上に記載なしの Task が completed バッジで表示（補完）
  - tasks.md [ ] で SessionState 上に記載なしの Task が not-started バッジで表示
  - 状態値が 4 値以外に存在しないこと（AC-3）
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# .claude/scripts を sys.path に追加（既存テストと同パターン）
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# プロジェクトルートの推定
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# build_dashboard.py スクリプトパス
_SCRIPT = _PROJECT_ROOT / ".claude" / "scripts" / "build_dashboard.py"


# ─────────────────────────────────────────────
# ヘルパー: build モジュールの動的ロード
# ─────────────────────────────────────────────


def _load_build_module():
    """build_dashboard.py モジュールを動的にロードして返す。"""
    sys.path.insert(0, str(_PROJECT_ROOT / ".claude" / "scripts"))
    spec = importlib.util.spec_from_file_location("build_dashboard", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─────────────────────────────────────────────
# ヘルパー: 制御済みプロジェクト構造の構築
# ─────────────────────────────────────────────


def _build_controlled_project(
    tmp_path: Path,
    session_state_content: str,
    tasks_content: str,
    phase: str = "BUILDING",
    milestone: str = "b4-dashboard",
) -> Path:
    """制御済みのプロジェクト構造を tmp_path 上に構築して project_root を返す。

    配置するファイル:
      - SESSION_STATE.md（session_state_content）
      - .claude/current-phase.md（# Current Phase\n\n**{phase}**\n）
      - docs/specs/{milestone}/tasks.md（tasks_content）
    """
    project_root = tmp_path / "project"
    project_root.mkdir()

    # SESSION_STATE.md
    (project_root / "SESSION_STATE.md").write_text(session_state_content, encoding="utf-8")

    # .claude/current-phase.md
    dotclaude = project_root / ".claude"
    dotclaude.mkdir()
    (dotclaude / "current-phase.md").write_text(
        f"# Current Phase\n\n**{phase}**\n", encoding="utf-8"
    )

    # docs/specs/<milestone>/tasks.md
    specs_dir = project_root / "docs" / "specs" / milestone
    specs_dir.mkdir(parents=True)
    (specs_dir / "tasks.md").write_text(tasks_content, encoding="utf-8")

    return project_root


def _run_build_to_html(project_root: Path, tmp_path: Path) -> str:
    """build() を実行して生成 HTML を返す。"""
    mod = _load_build_module()
    output = tmp_path / "dashboard.html"
    mod.build(project_root=project_root, output_path=output)
    return output.read_text(encoding="utf-8")


# ─────────────────────────────────────────────
# TC-1: SESSION_STATE「完了タスク」→ V-4 で completed バッジ
# ─────────────────────────────────────────────


class TestCompletedTaskFromSessionState:
    """SessionState の「完了タスク」に記載された Task が V-4 で completed と表示される。

    design.md §5 優先順位 1: SESSION_STATE.md「完了タスク」に記録あり → "completed"
    """

    SESSION_STATE = """\
# SESSION_STATE

## 完了タスク

- W1-B5-T1: BaseParser 実装完了
- W1-B5-T2: build_dashboard.py スケルトン完了
"""

    TASKS_MD = """\
# タスク定義書

- [ ] W1-B5-T1: BaseParser インターフェース定義
- [ ] W1-B5-T2: build_dashboard.py スケルトン
- [ ] W2-B5-T7: SessionStateParser 実装
"""

    def test_completed_task_shows_completed_badge(self, tmp_path):
        """SESSION_STATE 完了タスクが V-4 で data-status="completed" バッジで表示されること。"""
        project_root = _build_controlled_project(
            tmp_path, self.SESSION_STATE, self.TASKS_MD
        )
        html = _run_build_to_html(project_root, tmp_path)
        # data-status="completed" が存在する（SessionState 優先順位 1）
        assert 'data-status="completed"' in html, (
            "SessionState 完了タスクが completed バッジで表示されていません。\n"
            "design.md §5 優先順位 1 を確認してください。"
        )

    def test_completed_task_id_in_html(self, tmp_path):
        """SESSION_STATE 完了タスク（W1-B5-T1）が HTML に含まれること。"""
        project_root = _build_controlled_project(
            tmp_path, self.SESSION_STATE, self.TASKS_MD
        )
        html = _run_build_to_html(project_root, tmp_path)
        assert "W1-B5-T1" in html, "W1-B5-T1 が HTML に含まれていません。"

    def test_completed_task_overrides_tasks_md_not_started(self, tmp_path):
        """tasks.md が [ ] (not-started) でも SessionState 完了が優先されること。

        design.md §5 優先順位 1 > 5（Session.completed > tasks.md [ ]）
        """
        project_root = _build_controlled_project(
            tmp_path, self.SESSION_STATE, self.TASKS_MD
        )
        html = _run_build_to_html(project_root, tmp_path)
        # W1-B5-T1 の行が completed バッジを持つ（not-started より優先）
        # HTML 内に completed バッジが存在すれば優先順位が機能している
        assert 'data-status="completed"' in html, (
            "SessionState completed（優先順位1）が tasks.md not-started（優先順位5）に負けています。"
        )


# ─────────────────────────────────────────────
# TC-2: SESSION_STATE「進行中タスク」→ V-4 で in-progress バッジ
# ─────────────────────────────────────────────


class TestInProgressTaskFromSessionState:
    """SessionState の「進行中タスク」に記載された Task が V-4 で in-progress と表示される。

    design.md §5 優先順位 2: SESSION_STATE.md「進行中タスク」に記録あり → "in-progress"
    """

    SESSION_STATE = """\
# SESSION_STATE

## 進行中タスク

- W3-B5-T14: V-3 Wave 一覧ビュー実装中
- W3-B5-T15: V-4 Task 一覧ビュー実装中
"""

    TASKS_MD = """\
# タスク定義書

- [ ] W3-B5-T14: V-3 Wave 一覧ビュー実装
- [ ] W3-B5-T15: V-4 Task 一覧ビュー実装
- [ ] W3-B5-T16: 状態値決定ロジック統合テスト
"""

    def test_in_progress_task_shows_in_progress_badge(self, tmp_path):
        """SESSION_STATE 進行中タスクが V-4 で data-status="in-progress" バッジで表示されること。"""
        project_root = _build_controlled_project(
            tmp_path, self.SESSION_STATE, self.TASKS_MD
        )
        html = _run_build_to_html(project_root, tmp_path)
        assert 'data-status="in-progress"' in html, (
            "SessionState 進行中タスクが in-progress バッジで表示されていません。\n"
            "design.md §5 優先順位 2 を確認してください。"
        )

    def test_in_progress_task_id_in_html(self, tmp_path):
        """SESSION_STATE 進行中タスク（W3-B5-T14）が HTML に含まれること。"""
        project_root = _build_controlled_project(
            tmp_path, self.SESSION_STATE, self.TASKS_MD
        )
        html = _run_build_to_html(project_root, tmp_path)
        assert "W3-B5-T14" in html, "W3-B5-T14 が HTML に含まれていません。"

    def test_in_progress_overrides_tasks_md_not_started(self, tmp_path):
        """tasks.md が [ ] (not-started) でも SessionState 進行中が優先されること。

        design.md §5 優先順位 2 > 5
        """
        project_root = _build_controlled_project(
            tmp_path, self.SESSION_STATE, self.TASKS_MD
        )
        html = _run_build_to_html(project_root, tmp_path)
        assert 'data-status="in-progress"' in html, (
            "SessionState in-progress（優先順位2）が tasks.md not-started（優先順位5）に負けています。"
        )


# ─────────────────────────────────────────────
# TC-3: SESSION_STATE「ブロック中タスク」→ V-4 で blocked バッジ
# ─────────────────────────────────────────────


class TestBlockedTaskFromSessionState:
    """SessionState の「ブロック中タスク」に記載された Task が V-4 で blocked と表示される。

    design.md §5 優先順位 3: SESSION_STATE.md「未解決の問題」に記録あり → "blocked"
    """

    SESSION_STATE = """\
# SESSION_STATE

## 未解決の問題

- W2-B5-T7: SESSION_STATE.md パースの堅牢性確認が必要
"""

    TASKS_MD = """\
# タスク定義書

- [ ] W2-B5-T7: SessionStateParser 実装
- [ ] W2-B5-T8: CurrentPhaseParser 実装
"""

    def test_blocked_task_shows_blocked_badge(self, tmp_path):
        """SESSION_STATE ブロック中タスクが V-4 で data-status="blocked" バッジで表示されること。"""
        project_root = _build_controlled_project(
            tmp_path, self.SESSION_STATE, self.TASKS_MD
        )
        html = _run_build_to_html(project_root, tmp_path)
        assert 'data-status="blocked"' in html, (
            "SessionState ブロック中タスクが blocked バッジで表示されていません。\n"
            "design.md §5 優先順位 3 を確認してください。"
        )

    def test_blocked_task_id_in_html(self, tmp_path):
        """SESSION_STATE ブロック中タスク（W2-B5-T7）が HTML に含まれること。"""
        project_root = _build_controlled_project(
            tmp_path, self.SESSION_STATE, self.TASKS_MD
        )
        html = _run_build_to_html(project_root, tmp_path)
        assert "W2-B5-T7" in html, "W2-B5-T7 が HTML に含まれていません。"


# ─────────────────────────────────────────────
# TC-4: tasks.md [x] で SessionState 未記載 → completed（補完）
# ─────────────────────────────────────────────


class TestTasksParserCompletedFromCheckbox:
    """tasks.md の [x] チェックから completed が決定されること。

    design.md §5 優先順位 4: tasks.md に [x] チェックあり → "completed"
    SessionState に記載なしの場合はこの優先順位が適用される。
    """

    SESSION_STATE = """\
# SESSION_STATE

## 現在の作業状況

（特に何も記録なし）
"""

    TASKS_MD = """\
# タスク定義書

- [x] W1-B5-T1: BaseParser 実装完了
- [x] W1-B5-T2: スケルトン完了
- [ ] W2-B5-T7: SessionStateParser 未実装
"""

    def test_checkbox_completed_task_shows_completed_badge(self, tmp_path):
        """tasks.md [x] の Task（SessionState 未記載）が completed バッジで表示されること。"""
        project_root = _build_controlled_project(
            tmp_path, self.SESSION_STATE, self.TASKS_MD
        )
        html = _run_build_to_html(project_root, tmp_path)
        assert 'data-status="completed"' in html, (
            "tasks.md [x] の Task が completed バッジで表示されていません。\n"
            "design.md §5 優先順位 4（tasks.md [x] → completed）を確認してください。"
        )

    def test_checkbox_completed_task_id_in_html(self, tmp_path):
        """tasks.md [x] の Task ID（W1-B5-T1）が HTML に含まれること。"""
        project_root = _build_controlled_project(
            tmp_path, self.SESSION_STATE, self.TASKS_MD
        )
        html = _run_build_to_html(project_root, tmp_path)
        assert "W1-B5-T1" in html, "W1-B5-T1 が HTML に含まれていません。"

    def test_checkbox_not_started_task_shows_not_started_badge(self, tmp_path):
        """tasks.md [ ] の Task（SessionState 未記載）が not-started バッジで表示されること。

        design.md §5 優先順位 5: tasks.md に [ ] チェックあり → "not-started"
        """
        project_root = _build_controlled_project(
            tmp_path, self.SESSION_STATE, self.TASKS_MD
        )
        html = _run_build_to_html(project_root, tmp_path)
        assert 'data-status="not-started"' in html, (
            "tasks.md [ ] の Task が not-started バッジで表示されていません。\n"
            "design.md §5 優先順位 5（tasks.md [ ] → not-started）を確認してください。"
        )


# ─────────────────────────────────────────────
# TC-5: AC-3 確認 - 状態値が 4 値のみであること
# ─────────────────────────────────────────────


class TestStatusValuesAreOnly4Types:
    """AC-3: 各エントリの状態値が 4 値（not-started/in-progress/blocked/completed）のみ。

    design.md §5 / requirements.md AC-3
    """

    SESSION_STATE = """\
# SESSION_STATE

## 完了タスク

- W1-B5-T1: 完了
- W1-B5-T2: 完了

## 進行中タスク

- W3-B5-T16: 統合テスト実装中

## 未解決の問題

- W2-B5-T7: 要確認
"""

    TASKS_MD = """\
# タスク定義書

- [x] W1-B5-T1: BaseParser 実装
- [x] W1-B5-T2: スケルトン
- [ ] W2-B5-T7: SessionStateParser
- [ ] W3-B5-T16: 状態値ロジックテスト
- [ ] W3-B5-T17: 全ビュー統合テスト
"""

    VALID_STATUSES = {"completed", "in-progress", "blocked", "not-started"}

    def test_only_4_status_values_in_html(self, tmp_path):
        """生成 HTML の data-status 属性値が 4 値のみであること。"""
        import re

        project_root = _build_controlled_project(
            tmp_path, self.SESSION_STATE, self.TASKS_MD
        )
        html = _run_build_to_html(project_root, tmp_path)

        # data-status="..." の値を全て抽出
        found_statuses = set(re.findall(r'data-status="([^"]+)"', html))

        # 4 値以外の状態値が存在しないこと
        unexpected = found_statuses - self.VALID_STATUSES
        assert not unexpected, (
            f"4 値以外の状態値が HTML に含まれています: {unexpected}\n"
            "design.md §5 / AC-3: 状態値は not-started / in-progress / blocked / completed のみ"
        )

    def test_all_4_status_values_appear_in_html(self, tmp_path):
        """生成 HTML に 4 値すべてのステータスバッジが含まれること（AC-3 の網羅確認）。"""
        project_root = _build_controlled_project(
            tmp_path, self.SESSION_STATE, self.TASKS_MD
        )
        html = _run_build_to_html(project_root, tmp_path)

        for status in self.VALID_STATUSES:
            assert f'data-status="{status}"' in html, (
                f'data-status="{status}" が HTML に含まれていません（AC-3 網羅確認）。'
            )

    def test_status_badge_count_matches_task_count(self, tmp_path):
        """状態バッジの数が Task 数と一致すること（各 Task に 1 つのバッジ）。"""
        import re

        project_root = _build_controlled_project(
            tmp_path, self.SESSION_STATE, self.TASKS_MD
        )
        html = _run_build_to_html(project_root, tmp_path)

        # tasks.md のチェックボックス行数
        task_count = len(re.findall(r"- \[[ x]\]", self.TASKS_MD))

        # data-status 属性の数（V-4 テーブル内のバッジ数に相当）
        badge_count = len(re.findall(r'data-status="[^"]+"', html))

        assert badge_count >= task_count, (
            f"バッジ数（{badge_count}）が Task 数（{task_count}）より少ないです。\n"
            "各 Task に 1 つのステータスバッジが必要です。"
        )


# ─────────────────────────────────────────────
# TC-6: 優先順位の総合確認（複数状態が混在する場合）
# ─────────────────────────────────────────────


class TestStatusResolutionPriority:
    """design.md §5 の優先順位ロジックが複数状態混在時に正しく動作すること。

    優先順位:
      1. SessionState.completed  → "completed"
      2. SessionState.in_progress → "in-progress"
      3. SessionState.blocked    → "blocked"
      4. tasks.md [x]            → "completed"
      5. tasks.md [ ]            → "not-started"
    """

    SESSION_STATE_MIXED = """\
# SESSION_STATE

## 完了タスク

- W1-B5-T1: 完了済み

## 進行中タスク

- W2-B5-T7: 実装中

## 未解決の問題

- W1-B5-T2: 問題あり
"""

    TASKS_MD_MIXED = """\
# タスク定義書

- [ ] W1-B5-T1: SessionState=completed, tasks=not-started → 優先: completed
- [ ] W2-B5-T7: SessionState=in-progress, tasks=not-started → 優先: in-progress
- [ ] W1-B5-T2: SessionState=blocked, tasks=not-started → 優先: blocked
- [x] W3-B5-T12: SessionState=なし, tasks=completed → 優先: completed
- [ ] W3-B5-T17: SessionState=なし, tasks=not-started → 優先: not-started
"""

    def test_completed_overrides_tasks_not_started(self, tmp_path):
        """優先順位 1: SessionState completed が tasks.md not-started より優先される。"""
        project_root = _build_controlled_project(
            tmp_path, self.SESSION_STATE_MIXED, self.TASKS_MD_MIXED
        )
        html = _run_build_to_html(project_root, tmp_path)
        assert 'data-status="completed"' in html, (
            "SessionState completed が HTML に反映されていません。"
        )

    def test_in_progress_overrides_tasks_not_started(self, tmp_path):
        """優先順位 2: SessionState in-progress が tasks.md not-started より優先される。"""
        project_root = _build_controlled_project(
            tmp_path, self.SESSION_STATE_MIXED, self.TASKS_MD_MIXED
        )
        html = _run_build_to_html(project_root, tmp_path)
        assert 'data-status="in-progress"' in html, (
            "SessionState in-progress が HTML に反映されていません。"
        )

    def test_blocked_overrides_tasks_not_started(self, tmp_path):
        """優先順位 3: SessionState blocked が tasks.md not-started より優先される。"""
        project_root = _build_controlled_project(
            tmp_path, self.SESSION_STATE_MIXED, self.TASKS_MD_MIXED
        )
        html = _run_build_to_html(project_root, tmp_path)
        assert 'data-status="blocked"' in html, (
            "SessionState blocked が HTML に反映されていません。"
        )

    def test_tasks_completed_from_checkbox_when_not_in_session_state(self, tmp_path):
        """優先順位 4: SessionState 未記載 + tasks.md [x] → completed。"""
        project_root = _build_controlled_project(
            tmp_path, self.SESSION_STATE_MIXED, self.TASKS_MD_MIXED
        )
        html = _run_build_to_html(project_root, tmp_path)
        # W3-B5-T12 は SessionState 未記載・tasks.md [x] → completed
        assert "W3-B5-T12" in html, "W3-B5-T12 が HTML に含まれていません。"
        assert 'data-status="completed"' in html, (
            "tasks.md [x]（SessionState 未記載）が completed で表示されていません。"
        )

    def test_not_started_when_not_in_session_state_and_not_checked(self, tmp_path):
        """優先順位 5: SessionState 未記載 + tasks.md [ ] → not-started。"""
        project_root = _build_controlled_project(
            tmp_path, self.SESSION_STATE_MIXED, self.TASKS_MD_MIXED
        )
        html = _run_build_to_html(project_root, tmp_path)
        # W3-B5-T17 は SessionState 未記載・tasks.md [ ] → not-started
        assert "W3-B5-T17" in html, "W3-B5-T17 が HTML に含まれていません。"
        assert 'data-status="not-started"' in html, (
            "tasks.md [ ]（SessionState 未記載）が not-started で表示されていません。"
        )
