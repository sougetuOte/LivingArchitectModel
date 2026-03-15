"""
test_stop_hook.py - lam-stop-hook.py の TDD テスト

W4-T1: Red フェーズ（テストファースト）
対応仕様: docs/design/hooks-python-migration-design.md H3（lam-stop-hook）
"""
import datetime
import json
from pathlib import Path

from conftest import write_state as _write_state

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

    def test_active_loop_blocks_regardless_of_env(self, hook_runner, project_root):
        """アクティブなループ中は環境（Makefile 等）に関わらず block を返す。"""
        state = {**DEFAULT_STATE, "iteration": 0, "max_iterations": 5}
        _write_state(project_root, state)

        result = hook_runner(
            HOOK_PATH,
            {"session_id": "test-session", "cwd": str(project_root)},
        )

        assert result.returncode == 0
        stdout = result.stdout.strip()
        assert stdout, "安全ネットとして block JSON が出力されるべき"
        data = json.loads(stdout)
        assert data.get("decision") == "block"
        assert "ループ継続中" in data.get("reason", "")

    def test_precompact_stops(self, hook_runner, project_root):
        """PreCompact 発火フラグが直近 10 分以内に存在する場合、停止許可する"""
        # アクティブな状態ファイルを作成
        state_file = _write_state(project_root, DEFAULT_STATE)

        # 直近のタイムスタンプで pre-compact-fired フラグを作成
        now_ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        pre_compact_flag = project_root / ".claude" / "pre-compact-fired"
        pre_compact_flag.write_text(now_ts, encoding="utf-8")

        result = hook_runner(HOOK_PATH, {"session_id": "test-session"})

        assert result.returncode == 0
        assert result.stdout.strip() == "", (
            f"PreCompact 発火直後は stdout が空であるべき。got: {result.stdout!r}"
        )
        # 状態ファイルが削除されていること
        assert not state_file.exists(), "PreCompact 発火時は状態ファイルが削除されるべき"

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


class TestSafetyNetBlock:
    """Stop hook が安全ネットとして block する動作のテスト。

    Stop hook はループ制御を行わず、アクティブなループ中に
    Claude が止まろうとした場合に 1 回 block するだけ。
    G1-G5 の Green State 判定は Claude 側（/full-review）の責務。
    """

    def test_active_loop_blocks_with_reason(self, hook_runner, project_root):
        """アクティブなループ中は block を返すこと。"""
        _write_state(project_root, DEFAULT_STATE)

        result = hook_runner(HOOK_PATH, {"session_id": "test-session"})
        assert result.returncode == 0
        stdout = result.stdout.strip()
        assert stdout, "block JSON が出力されるべき"
        data = json.loads(stdout)
        assert data["decision"] == "block"
        assert "ループ継続中" in data["reason"]

    def test_active_loop_logs_safety_net(self, hook_runner, project_root):
        """安全ネット発動がログに記録されること。"""
        _write_state(project_root, DEFAULT_STATE)

        hook_runner(HOOK_PATH, {"session_id": "test-session"})

        log_file = project_root / ".claude" / "logs" / "loop.log"
        assert log_file.exists()
        log_content = log_file.read_text(encoding="utf-8")
        assert "safety net" in log_content
