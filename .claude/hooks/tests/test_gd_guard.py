"""test_gd_guard.py - gd-guard.py の TDD テスト

W1-T1: SKILL.md 骨格実装 - 排他ガード・残留検知・rubric-tmp 削除
対応仕様: docs/specs/goal-driven-orchestration/design.md §10 / §6
対応要件: FR-4 / FR-6 / FR-8 / AC-1 / AC-7 / AC-10 / NFR-4
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# scripts ディレクトリを sys.path に追加
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


# ---------------------------------------------------------------------------
# SKILL.md 存在確認テスト（AC-1）
# ---------------------------------------------------------------------------


class TestSkillMdExists:
    """AC-1: .claude/skills/goal-driven/SKILL.md が存在すること。"""

    def test_skill_md_exists(self):
        """SKILL.md が配置されていること。"""
        skill_path = (
            Path(__file__).resolve().parent.parent.parent
            / "skills"
            / "goal-driven"
            / "SKILL.md"
        )
        assert skill_path.is_file(), (
            f"SKILL.md が存在しない: {skill_path}\n"
            "W1-T1 の完了条件 AC-1 を満たすために SKILL.md を作成すること"
        )


# ---------------------------------------------------------------------------
# 排他ガードテスト（design §10 / tasks.md W1-T1 完了条件）
# ---------------------------------------------------------------------------


class TestExclusionGuard:
    """排他ガード: autonomous-state.json / lam-loop-state.json 存在時に起動拒否を返す。

    design §10: gd-session-state.json は autonomous-state.json および
    lam-loop-state.json と同時実行禁止。スキル起動時に他 state ファイルの
    存在を確認し、存在すれば起動を拒否する。
    """

    def _make_guard(self, project_root: Path):
        """gd_guard モジュールをインポートし、project_root を注入して返す。"""
        import importlib
        import gd_guard

        importlib.reload(gd_guard)
        return gd_guard

    def test_no_conflict_allows_start(self, tmp_path: Path, monkeypatch):
        """競合ファイルがない → 起動許可（None を返す）。"""
        monkeypatch.setenv("LAM_PROJECT_ROOT", str(tmp_path))
        (tmp_path / ".claude").mkdir(exist_ok=True)

        import gd_guard
        result = gd_guard.check_exclusion_guard(tmp_path)
        assert result is None, f"競合なしなら None を返すべき。got: {result!r}"

    def test_autonomous_state_blocks_start(self, tmp_path: Path, monkeypatch):
        """autonomous-state.json が存在 → 起動拒否メッセージを返す。"""
        monkeypatch.setenv("LAM_PROJECT_ROOT", str(tmp_path))
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(exist_ok=True)
        (claude_dir / "autonomous-state.json").write_text(
            json.dumps({"active": True}), encoding="utf-8"
        )

        import gd_guard
        result = gd_guard.check_exclusion_guard(tmp_path)
        assert result is not None, "autonomous-state.json 存在時は拒否すべき"
        assert "autonomous-state.json" in result, (
            f"拒否理由に autonomous-state.json が含まれるべき。got: {result!r}"
        )

    def test_lam_loop_state_blocks_start(self, tmp_path: Path, monkeypatch):
        """lam-loop-state.json が存在 → 起動拒否メッセージを返す。"""
        monkeypatch.setenv("LAM_PROJECT_ROOT", str(tmp_path))
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(exist_ok=True)
        (claude_dir / "lam-loop-state.json").write_text(
            json.dumps({"active": True}), encoding="utf-8"
        )

        import gd_guard
        result = gd_guard.check_exclusion_guard(tmp_path)
        assert result is not None, "lam-loop-state.json 存在時は拒否すべき"
        assert "lam-loop-state.json" in result, (
            f"拒否理由に lam-loop-state.json が含まれるべき。got: {result!r}"
        )

    def test_both_conflict_files_blocks_start(self, tmp_path: Path, monkeypatch):
        """両方の競合ファイルが存在 → 起動拒否メッセージを返す。"""
        monkeypatch.setenv("LAM_PROJECT_ROOT", str(tmp_path))
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(exist_ok=True)
        (claude_dir / "autonomous-state.json").write_text("{}", encoding="utf-8")
        (claude_dir / "lam-loop-state.json").write_text("{}", encoding="utf-8")

        import gd_guard
        result = gd_guard.check_exclusion_guard(tmp_path)
        assert result is not None, "両競合ファイル存在時は拒否すべき"


# ---------------------------------------------------------------------------
# rubric-tmp.md 削除処理テスト（design §6 MUST）
# ---------------------------------------------------------------------------


class TestRubricTmpCleanup:
    """rubric-tmp.md 削除: タスク終了時にスクリプトが削除する（design §6 MUST）。

    小タスクルートの .claude/rubric-tmp.md はタスク終了時
    （合格・エスカレーションを問わず）にスキルスクリプトが削除する。
    """

    def test_delete_rubric_tmp_when_exists(self, tmp_path: Path):
        """.claude/rubric-tmp.md が存在する場合、削除する。"""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(exist_ok=True)
        rubric_tmp = claude_dir / "rubric-tmp.md"
        rubric_tmp.write_text("# rubric-tmp\n", encoding="utf-8")

        import gd_guard
        gd_guard.cleanup_rubric_tmp(tmp_path)

        assert not rubric_tmp.exists(), (
            "rubric-tmp.md は削除されるべき"
        )

    def test_no_error_when_rubric_tmp_absent(self, tmp_path: Path):
        """.claude/rubric-tmp.md が存在しない場合、エラーなしで完了する。"""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(exist_ok=True)

        import gd_guard
        # 例外が発生しないことを確認
        gd_guard.cleanup_rubric_tmp(tmp_path)

    def test_cleanup_does_not_delete_rubric_md(self, tmp_path: Path):
        """通常の rubric.md（tasks/ 配下）は削除しない。"""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(exist_ok=True)
        tasks_dir = tmp_path / "docs" / "tasks" / "my-task"
        tasks_dir.mkdir(parents=True, exist_ok=True)
        rubric_md = tasks_dir / "rubric.md"
        rubric_md.write_text("# rubric\n", encoding="utf-8")

        import gd_guard
        gd_guard.cleanup_rubric_tmp(tmp_path)

        assert rubric_md.exists(), "docs/tasks/ 配下の rubric.md は削除しない"


# ---------------------------------------------------------------------------
# 残留リカバリ検知テスト（design §10 フェイルセーフ）
# ---------------------------------------------------------------------------


class TestResidualRecoveryDetection:
    """残留リカバリ: gd-session-state.json が status: "running" のまま残留している場合の検知。

    design §10: 自動削除はせず PM に提示して明示承認後に削除する（フェイルセーフ）。
    テストは「自動削除しないこと」の確認を含む。
    """

    def _write_gd_state(self, project_root: Path, state: dict) -> Path:
        """gd-session-state.json を書き込む。"""
        claude_dir = project_root / ".claude"
        claude_dir.mkdir(exist_ok=True)
        state_file = claude_dir / "gd-session-state.json"
        state_file.write_text(json.dumps(state), encoding="utf-8")
        return state_file

    def test_no_residual_when_no_state_file(self, tmp_path: Path):
        """gd-session-state.json が存在しない → 残留なし（None を返す）。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)

        import gd_guard
        result = gd_guard.detect_residual_session(tmp_path)
        assert result is None, f"ファイルなしなら None を返すべき。got: {result!r}"

    def test_no_residual_when_status_completed(self, tmp_path: Path):
        """gd-session-state.json が status: "completed" → 残留なし（None を返す）。"""
        self._write_gd_state(tmp_path, {
            "task_id": "gd-test-001",
            "status": "completed",
        })

        import gd_guard
        result = gd_guard.detect_residual_session(tmp_path)
        assert result is None, f"status: completed は残留なし。got: {result!r}"

    def test_detect_residual_when_status_running(self, tmp_path: Path):
        """gd-session-state.json が status: "running" → 残留検知（dict を返す）。"""
        state = {
            "task_id": "gd-test-001",
            "status": "running",
            "task_slug": "example-task",
        }
        self._write_gd_state(tmp_path, state)

        import gd_guard
        result = gd_guard.detect_residual_session(tmp_path)
        assert result is not None, "status: running は残留検知すべき"
        assert isinstance(result, dict), f"残留検知時は dict を返すべき。got: {type(result)}"
        assert result.get("task_id") == "gd-test-001", (
            f"task_id が含まれるべき。got: {result!r}"
        )

    def test_residual_state_is_not_auto_deleted(self, tmp_path: Path):
        """残留検知後、gd-session-state.json は自動削除されない（フェイルセーフ）。

        design §10: 自動削除はせず PM に提示して明示承認後に削除する。
        """
        self._write_gd_state(tmp_path, {
            "task_id": "gd-test-001",
            "status": "running",
        })
        state_file = tmp_path / ".claude" / "gd-session-state.json"

        import gd_guard
        gd_guard.detect_residual_session(tmp_path)

        assert state_file.exists(), (
            "detect_residual_session は gd-session-state.json を自動削除してはならない"
        )

    def test_no_residual_when_status_escalated(self, tmp_path: Path):
        """gd-session-state.json が status: "escalated" → 残留なし（None を返す）。"""
        self._write_gd_state(tmp_path, {
            "task_id": "gd-test-001",
            "status": "escalated",
        })

        import gd_guard
        result = gd_guard.detect_residual_session(tmp_path)
        assert result is None, f"status: escalated は残留なし（終了済み）。got: {result!r}"

    def test_corrupted_state_returns_none(self, tmp_path: Path):
        """壊れた gd-session-state.json → 残留なし（None を返す・fail-close）。

        バックストップが壊れた状態ファイルによってパニックしないこと。
        """
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(exist_ok=True)
        (claude_dir / "gd-session-state.json").write_text(
            "{ not json }", encoding="utf-8"
        )

        import gd_guard
        result = gd_guard.detect_residual_session(tmp_path)
        assert result is None, f"壊れた state は None（fail-close）を返すべき。got: {result!r}"
