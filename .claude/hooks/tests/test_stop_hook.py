"""
test_stop_hook.py - lam-stop-hook.py の TDD テスト

W4-T1: Red フェーズ（テストファースト）
対応仕様: docs/specs/hooks-python-migration/design.md Section 3.4
"""
import json
import time
from pathlib import Path

import pytest

# テスト対象フックのパス
HOOK_PATH = Path(__file__).resolve().parent.parent / "lam-stop-hook.py"

# 状態ファイルのデフォルト構造
DEFAULT_STATE = {
    "active": True,
    "iteration": 0,
    "max_iterations": 5,
    "command": "test_command",
    "target": "test_target",
    "started_at": "2026-03-10T00:00:00Z",
    "log": [],
}


def _write_state(project_root: Path, state: dict) -> Path:
    """lam-loop-state.json を書き込む。"""
    state_file = project_root / ".claude" / "lam-loop-state.json"
    state_file.write_text(json.dumps(state), encoding="utf-8")
    return state_file


class TestStopHook:
    """lam-stop-hook.py の自律ループ収束判定テスト"""

    def test_no_state_file_stops(self, hook_runner, project_root):
        """状態ファイルが存在しない場合は停止許可する（exit 0、stdout 空）"""
        # 状態ファイルを作成しない
        state_file = project_root / ".claude" / "lam-loop-state.json"
        assert not state_file.exists()

        result = hook_runner(HOOK_PATH, {"session_id": "test-session"})

        assert result.returncode == 0
        assert result.stdout.strip() == "", (
            f"状態ファイルなし時は stdout が空であるべき。got: {result.stdout!r}"
        )

    def test_max_iterations_stops(self, hook_runner, project_root):
        """iteration >= max_iterations の場合、停止許可し状態ファイルを削除する"""
        state = {**DEFAULT_STATE, "iteration": 5, "max_iterations": 5}
        state_file = _write_state(project_root, state)
        assert state_file.exists()

        result = hook_runner(HOOK_PATH, {"session_id": "test-session"})

        assert result.returncode == 0
        assert result.stdout.strip() == "", (
            f"上限到達時は stdout が空であるべき。got: {result.stdout!r}"
        )
        # 状態ファイルが削除されていること
        assert not state_file.exists(), "上限到達時は状態ファイルが削除されるべき"

    def test_recursion_guard(self, hook_runner, project_root):
        """stop_hook_active=true の場合、再帰防止のため即座に停止する"""
        # 状態ファイルをアクティブ状態で作成
        _write_state(project_root, DEFAULT_STATE)

        result = hook_runner(HOOK_PATH, {"stop_hook_active": True})

        assert result.returncode == 0
        assert result.stdout.strip() == "", (
            f"再帰防止時は stdout が空であるべき。got: {result.stdout!r}"
        )

    def test_test_fail_blocks(self, hook_runner, project_root, tmp_path):
        """テスト失敗時は block JSON を出力して継続指示を出す"""
        # アクティブな状態ファイルを作成（まだ上限に達していない）
        state = {**DEFAULT_STATE, "iteration": 0, "max_iterations": 5}
        _write_state(project_root, state)

        # テストが失敗する Makefile を project_root に配置
        makefile = project_root / "Makefile"
        makefile.write_text("test:\n\texit 1\n", encoding="utf-8")

        # cwd に project_root を渡す（テストフレームワーク検出のため）
        result = hook_runner(
            HOOK_PATH,
            {"session_id": "test-session", "cwd": str(project_root)},
        )

        assert result.returncode == 0
        stdout = result.stdout.strip()
        assert stdout, (
            f"テスト失敗時は block JSON が出力されるべき。got: {stdout!r}"
        )
        data = json.loads(stdout)
        assert data.get("decision") == "block", (
            f"decision が 'block' であるべき。got: {data}"
        )
        assert "reason" in data, "reason フィールドが含まれるべき"

    def test_precompact_stops(self, hook_runner, project_root):
        """PreCompact 発火フラグが直近 10 分以内に存在する場合、停止許可する"""
        # アクティブな状態ファイルを作成
        _write_state(project_root, DEFAULT_STATE)

        # 直近のタイムスタンプで pre-compact-fired フラグを作成
        now_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        pre_compact_flag = project_root / ".claude" / "pre-compact-fired"
        pre_compact_flag.write_text(now_ts, encoding="utf-8")

        result = hook_runner(HOOK_PATH, {"session_id": "test-session"})

        assert result.returncode == 0
        assert result.stdout.strip() == "", (
            f"PreCompact 発火直後は stdout が空であるべき。got: {result.stdout!r}"
        )

    def test_state_schema_valid(self, project_root):
        """lam-loop-state.json の必須フィールドが正しく書き込み・読み込みできる"""
        state = {
            "active": True,
            "iteration": 2,
            "max_iterations": 5,
            "command": "full-review",
            "target": "src/",
            "started_at": "2026-03-10T12:00:00Z",
            "log": [
                {
                    "iteration": 1,
                    "issues_found": 3,
                    "issues_fixed": 3,
                    "pg": 2,
                    "se": 1,
                    "pm": 0,
                    "test_count": 42,
                }
            ],
            "fullscan_pending": False,
        }
        state_file = _write_state(project_root, state)

        # 読み込んで検証
        loaded = json.loads(state_file.read_text(encoding="utf-8"))

        # 必須フィールドの存在確認
        assert loaded["active"] is True
        assert loaded["iteration"] == 2
        assert loaded["max_iterations"] == 5
        assert loaded["command"] == "full-review"
        assert loaded["target"] == "src/"
        assert isinstance(loaded["log"], list)
        assert len(loaded["log"]) == 1
        assert loaded["log"][0]["test_count"] == 42
