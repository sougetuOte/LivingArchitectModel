"""
test_loop_integration.py - ループ統合テスト

W4-T2: H4/H1/H2/H3 をまたぐループ統合テスト。
bash 版 test-loop-integration.sh の 5 シナリオ (S-1〜S-5) を pytest で再現。

対応仕様: docs/design/hooks-python-migration-design.md Section 4 (S-1〜S-5)
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path

from conftest import write_state as _write_state

# テスト対象フックのパス
STOP_HOOK_PATH = Path(__file__).resolve().parent.parent / "lam-stop-hook.py"

# 状態ファイルのデフォルト構造
DEFAULT_STATE = {
    "active": True,
    "iteration": 0,
    "max_iterations": 5,
    "command": "full-review",
    "target": "src/",
    "started_at": "2026-03-10T00:00:00Z",
    "log": [],
}

DEFAULT_INPUT = {
    "session_id": "test-integration",
    "permission_mode": "default",
    "hook_event_name": "Stop",
    "stop_hook_active": False,
    "last_assistant_message": "done",
}


def _read_state(project_root: Path) -> dict | None:
    """lam-loop-state.json を読み込む。存在しなければ None。"""
    state_file = project_root / ".claude" / "lam-loop-state.json"
    if not state_file.exists():
        return None
    return json.loads(state_file.read_text(encoding="utf-8"))


def _make_input(project_root: Path, message: str = "done", **overrides) -> dict:
    """テスト用 stdin JSON を生成する。cwd と transcript_path は project_root に設定。"""
    data = {
        **DEFAULT_INPUT,
        "cwd": str(project_root),
        "transcript_path": str(project_root / "transcript"),
        "last_assistant_message": message,
    }
    data.update(overrides)
    return data


def _create_makefile(project_root: Path, test_exit: int = 0, lint_exit: int = 0) -> None:
    """Makefile を project_root に作成する。"""
    lines = [f"test:\n\t@exit {test_exit}\n"]
    if lint_exit is not None:
        lines.append(f"lint:\n\t@exit {lint_exit}\n")
    (project_root / "Makefile").write_text("".join(lines), encoding="utf-8")


class TestNormalConvergence:
    """S-1: 安全ネット動作シミュレーション

    Stop hook は Green State 判定を行わず、アクティブなループ中は
    常に block を返す（安全ネット）。Green State 判定と状態ファイル
    削除は Claude 側（/full-review）の責務。
    """

    def test_active_loop_always_blocks(self, hook_runner, project_root):
        """S-1-1: アクティブなループ中は常に block を返すこと。"""
        state = {
            **DEFAULT_STATE,
            "iteration": 1,
            "log": [
                {"iteration": 0, "issues_found": 2, "issues_fixed": 2, "pg": 2, "se": 0, "pm": 0},
            ],
        }
        _write_state(project_root, state)

        input_data = _make_input(project_root, "修正完了。再スキャンへ。")
        result = hook_runner(STOP_HOOK_PATH, input_data)

        assert result.returncode == 0
        stdout = result.stdout.strip()
        assert stdout, "安全ネットとして block JSON が出力されるべき"
        data = json.loads(stdout)
        assert data["decision"] == "block"


class TestLoopStateVariations:
    """S-2: ループ状態バリエーション（block / active=false）"""

    def test_test_failure_blocks(self, hook_runner, project_root):
        """S-2-1: テスト失敗 → block で継続（PM級検出は Claude の責務）"""
        state = {
            **DEFAULT_STATE,
            "iteration": 1,
            "log": [
                {"iteration": 0, "issues_found": 5, "issues_fixed": 3, "pg": 2, "se": 1, "pm": 2},
            ],
        }
        _write_state(project_root, state)
        _create_makefile(project_root, test_exit=1)

        input_data = _make_input(
            project_root,
            "PM級の問題が2件検出されました。ループを停止してエスカレーションします。",
        )
        result = hook_runner(STOP_HOOK_PATH, input_data)

        assert result.returncode == 0
        stdout = result.stdout.strip()
        assert stdout, f"テスト失敗時は block JSON が出力されるべき。got: {stdout!r}"
        data = json.loads(stdout)
        assert data.get("decision") == "block"

    def test_active_false_stops(self, hook_runner, project_root):
        """S-2-2: active=false → ループ無効で停止"""
        state = {**DEFAULT_STATE, "active": False, "iteration": 1}
        _write_state(project_root, state)

        result = hook_runner(STOP_HOOK_PATH, _make_input(project_root))

        assert result.returncode == 0
        assert result.stdout.strip() == "", (
            f"active=false 時は stdout が空であるべき。got: {result.stdout!r}"
        )


class TestMaxIterationsLifecycle:
    """S-3: 上限到達ライフサイクル"""

    def test_below_max_continues(self, hook_runner, project_root):
        """S-3-1: iteration=4, max_iterations=5 → まだ継続可能"""
        state = {
            **DEFAULT_STATE,
            "iteration": 4,
            "max_iterations": 5,
            "log": [
                {"iteration": 0, "issues_found": 10, "issues_fixed": 8, "pg": 5, "se": 3, "pm": 0},
                {"iteration": 1, "issues_found": 5, "issues_fixed": 4, "pg": 3, "se": 1, "pm": 0},
                {"iteration": 2, "issues_found": 3, "issues_fixed": 2, "pg": 1, "se": 1, "pm": 0},
                {"iteration": 3, "issues_found": 2, "issues_fixed": 1, "pg": 1, "se": 0, "pm": 0},
            ],
        }
        _write_state(project_root, state)
        _create_makefile(project_root, test_exit=1)

        input_data = _make_input(project_root, "Green State 未達。残 Issue: 1件")
        result = hook_runner(STOP_HOOK_PATH, input_data)

        assert result.returncode == 0
        stdout = result.stdout.strip()
        assert stdout, "上限未到達時は block JSON が出力されるべき"
        data = json.loads(stdout)
        assert data.get("decision") == "block", "上限未到達時は block で継続"

    def test_at_max_stops(self, hook_runner, project_root):
        """S-3-2: iteration=5 == max_iterations=5 → 強制停止"""
        state = {
            **DEFAULT_STATE,
            "iteration": 5,
            "max_iterations": 5,
            "log": [
                {"iteration": 0, "issues_found": 10, "issues_fixed": 8, "pg": 5, "se": 3, "pm": 0},
                {"iteration": 1, "issues_found": 5, "issues_fixed": 4, "pg": 3, "se": 1, "pm": 0},
                {"iteration": 2, "issues_found": 3, "issues_fixed": 2, "pg": 1, "se": 1, "pm": 0},
                {"iteration": 3, "issues_found": 2, "issues_fixed": 1, "pg": 1, "se": 0, "pm": 0},
                {"iteration": 4, "issues_found": 1, "issues_fixed": 0, "pg": 0, "se": 1, "pm": 0},
            ],
        }
        state_file = _write_state(project_root, state)

        input_data = _make_input(project_root, "Green State 未達。残 Issue: 1件")
        result = hook_runner(STOP_HOOK_PATH, input_data)

        assert result.returncode == 0
        assert result.stdout.strip() == "", (
            f"上限到達時は stdout が空であるべき。got: {result.stdout!r}"
        )
        assert not state_file.exists(), "上限到達時は状態ファイルが削除されるべき"


class TestContextExhaustion:
    """S-4: コンテキスト枯渇 → ループ停止"""

    def test_precompact_recent_stops(self, hook_runner, project_root):
        """S-4-1: PreCompact フラグが直近 → ループ停止"""

        state = {**DEFAULT_STATE, "iteration": 2}
        state_file = _write_state(project_root, state)

        # 直近のタイムスタンプで pre-compact-fired フラグを作成
        now_ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        pre_compact_flag = project_root / ".claude" / "pre-compact-fired"
        pre_compact_flag.write_text(now_ts, encoding="utf-8")

        result = hook_runner(STOP_HOOK_PATH, _make_input(project_root))

        assert result.returncode == 0
        assert result.stdout.strip() == "", (
            f"PreCompact 発火直後は stdout が空であるべき。got: {result.stdout!r}"
        )
        assert not state_file.exists(), "PreCompact 発火時は状態ファイルが削除されるべき"


class TestFullLifecycle:
    """S-5: ループライフサイクル全体（初期化→複数サイクル→収束）"""

    def test_init_fail_then_converge(self, hook_runner, project_root):
        """S-5-1: Phase 0 初期化 → サイクル1(失敗) → サイクル2(成功) の流れ"""

        # Phase 0: 初期化（状態ファイル生成）
        now_ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        state = {
            **DEFAULT_STATE,
            "started_at": now_ts,
        }
        state_file = _write_state(project_root, state)
        assert state_file.exists(), "Phase 0: 状態ファイルが生成されるべき"

        # サイクル1: テスト失敗 → block で継続
        _create_makefile(project_root, test_exit=1)
        input_data = _make_input(project_root, "Green State 未達。残 Issue: 3件")
        result = hook_runner(STOP_HOOK_PATH, input_data)

        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data.get("decision") == "block", "サイクル1: テスト失敗時は block で継続"
        assert state_file.exists(), "サイクル1: 状態ファイルが残っているべき"

        # 安全ネットでは iteration をインクリメントしない（Claude 側の責務）
        updated_state = _read_state(project_root)
        assert updated_state is not None
        assert updated_state["iteration"] == 0, (
            "安全ネットは iteration を変更しない"
        )

        # サイクル2: 安全ネットとして再び block（Green State 判定は Claude 側の責務）
        input_data = _make_input(project_root, "修正完了。再スキャンへ。")
        result = hook_runner(STOP_HOOK_PATH, input_data)

        assert result.returncode == 0
        stdout = result.stdout.strip()
        assert stdout, "サイクル2: 安全ネットとして block を返すべき"
        data2 = json.loads(stdout)
        assert data2.get("decision") == "block"
        # 状態ファイルの削除は Claude 側（/full-review Phase 6）の責務
        assert state_file.exists(), "安全ネットは状態ファイルを削除しない"
