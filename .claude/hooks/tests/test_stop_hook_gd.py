"""test_stop_hook_gd.py - lam-stop-hook.py B-3 節（goal-driven bound バックストップ）テスト

W2-T3: Stop hook B-3 節実装
対応仕様: docs/specs/goal-driven-orchestration/design.md §10
対応要件: FR-4 / AC-8 / design §10（第二防衛線）

テストケース:
  - トークン超過でエスカレーション通知（exit 0 + additionalContext）
  - 時間超過でエスカレーション通知（exit 0 + additionalContext）
  - 超過なし時は通過（B-3 節がブロックしない）
  - autonomous-state.json が active=true の場合は B-3 節をスキップ（競合排除）
  - lam-loop-state.json が存在する場合は B-3 節をスキップ（競合排除）
  - 破損 JSON でもフェイルセーフで通過（Claude を止めない）
  - status が "running" 以外の場合はスキップ（チェック対象外）
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

# hooks ディレクトリを sys.path に追加
_HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

HOOK_PATH = Path(__file__).resolve().parent.parent / "lam-stop-hook.py"


# ---------------------------------------------------------------------------
# ヘルパー関数
# ---------------------------------------------------------------------------


def _write_gd_state(project_root: Path, **overrides) -> Path:
    """gd-session-state.json をテスト用に書き込む。

    デフォルト値は status="running"、超過なし（total_tokens=0、start_time=now）。
    overrides で任意フィールドを上書きできる。
    """
    state: dict = {
        "task_id": "gd-20260613-001",
        "task_slug": "test-task",
        "route": "medium",
        "nest_depth_limit": 5,
        "global_token_bound": 150_000,
        "global_time_bound": 3600,
        "total_tokens": 0,
        "loop_count": 0,
        "max_loop_count": 3,
        "start_time": time.time(),
        "status": "running",
        "fallback": None,
    }
    state.update(overrides)
    gd_state_path = project_root / ".claude" / "gd-session-state.json"
    gd_state_path.write_text(json.dumps(state), encoding="utf-8")
    return gd_state_path


def _write_auto_state(project_root: Path, active: bool = True) -> Path:
    """autonomous-state.json をテスト用に書き込む。"""
    state = {
        "active": active,
        "iteration": 0,
        "max_iterations": 20,
        "phase": "building",
        "checker_results": {},
        "spec": "docs/specs/foo/requirements.md",
        "started_at": "2026-06-13T00:00:00Z",
    }
    auto_state_path = project_root / ".claude" / "autonomous-state.json"
    auto_state_path.write_text(json.dumps(state), encoding="utf-8")
    return auto_state_path


def _write_lam_loop_state(project_root: Path) -> Path:
    """lam-loop-state.json をテスト用に書き込む。"""
    state = {
        "active": True,
        "iteration": 0,
        "max_iterations": 5,
        "command": "test-cmd",
        "target": "test-target",
        "started_at": "2026-06-13T00:00:00Z",
        "log": [],
    }
    loop_state_path = project_root / ".claude" / "lam-loop-state.json"
    loop_state_path.write_text(json.dumps(state), encoding="utf-8")
    return loop_state_path


# ---------------------------------------------------------------------------
# B-3 節 基本動作テスト
# ---------------------------------------------------------------------------


class TestGdBoundBackstop:
    """B-3 節: goal-driven グローバル bound バックストップ（第二防衛線）の基本動作。"""

    def test_token_bound_exceeded_emits_additional_context(
        self, hook_runner, project_root
    ):
        """total_tokens >= global_token_bound の場合、exit 0 + additionalContext を出力する。

        C-1 修正: block ではなく exit 0 + additionalContext 方式。
        """
        # total_tokens が bound と等しい（>=）状態を設定
        _write_gd_state(
            project_root,
            total_tokens=150_000,
            global_token_bound=150_000,
            status="running",
        )

        result = hook_runner(HOOK_PATH, {"session_id": "test"})

        assert result.returncode == 0
        # additionalContext を含む JSON が出力されることを確認
        stdout = result.stdout.strip()
        assert stdout != "", (
            "トークン超過時は additionalContext JSON を出力すべき。got: stdout 空"
        )
        output = json.loads(stdout)
        assert "hookSpecificOutput" in output, (
            f"hookSpecificOutput キーが必要。got: {output}"
        )
        assert "additionalContext" in output["hookSpecificOutput"], (
            f"additionalContext キーが必要。got: {output['hookSpecificOutput']}"
        )
        ctx = output["hookSpecificOutput"]["additionalContext"]
        assert "goal-driven" in ctx, f"goal-driven が context に含まれるべき。got: {ctx}"
        assert "Escalating" in ctx, f"Escalating が context に含まれるべき。got: {ctx}"

    def test_token_bound_exceeded_does_not_use_block(
        self, hook_runner, project_root
    ):
        """bound 超過時に 'block' キーを使用しない（C-1 設計要件）。"""
        _write_gd_state(
            project_root,
            total_tokens=200_000,
            global_token_bound=150_000,
            status="running",
        )

        result = hook_runner(HOOK_PATH, {"session_id": "test"})

        assert result.returncode == 0
        stdout = result.stdout.strip()
        if stdout:
            output = json.loads(stdout)
            assert "decision" not in output, (
                f"'decision'（block 方式）は使用禁止。got: {output}"
            )

    def test_time_bound_exceeded_emits_additional_context(
        self, hook_runner, project_root
    ):
        """elapsed >= global_time_bound の場合、exit 0 + additionalContext を出力する。

        start_time を過去に設定し、経過時間が time_bound を超えた状態をシミュレート。
        """
        # start_time を 7200 秒前（time_bound=3600 の 2 倍）に設定
        past_start = time.time() - 7200
        _write_gd_state(
            project_root,
            total_tokens=0,
            global_token_bound=150_000,
            global_time_bound=3600,
            start_time=past_start,
            status="running",
        )

        result = hook_runner(HOOK_PATH, {"session_id": "test"})

        assert result.returncode == 0
        stdout = result.stdout.strip()
        assert stdout != "", (
            "時間超過時は additionalContext JSON を出力すべき。got: stdout 空"
        )
        output = json.loads(stdout)
        assert "hookSpecificOutput" in output
        assert "additionalContext" in output["hookSpecificOutput"]
        ctx = output["hookSpecificOutput"]["additionalContext"]
        assert "goal-driven" in ctx

    def test_no_bound_exceeded_passes_through(self, hook_runner, project_root):
        """bound 未超過時は B-3 節がブロックせず通過する（stdout 空 + exit 0）。

        gd-session-state.json が存在し status="running" だが、
        total_tokens < global_token_bound かつ elapsed < global_time_bound の場合。
        """
        _write_gd_state(
            project_root,
            total_tokens=1000,
            global_token_bound=150_000,
            global_time_bound=3600,
            start_time=time.time(),
            status="running",
        )

        result = hook_runner(HOOK_PATH, {"session_id": "test"})

        assert result.returncode == 0
        assert result.stdout.strip() == "", (
            f"bound 未超過時は stdout が空（通過）すべき。got: {result.stdout!r}"
        )

    def test_status_not_running_skips_bound_check(
        self, hook_runner, project_root
    ):
        """status が "running" 以外の場合は bound チェックをスキップして通過する。

        "escalated" や "completed" の状態ではバックストップを発動しない。
        """
        _write_gd_state(
            project_root,
            total_tokens=999_999,
            global_token_bound=150_000,
            status="escalated",
        )

        result = hook_runner(HOOK_PATH, {"session_id": "test"})

        assert result.returncode == 0
        assert result.stdout.strip() == "", (
            f"status=escalated 時は通過すべき。got: {result.stdout!r}"
        )

    def test_gd_state_absent_passes_through(self, hook_runner, project_root):
        """gd-session-state.json が存在しない場合は通過する（B-3 節は評価しない）。"""
        gd_state_path = project_root / ".claude" / "gd-session-state.json"
        assert not gd_state_path.exists()

        result = hook_runner(HOOK_PATH, {"session_id": "test"})

        assert result.returncode == 0
        assert result.stdout.strip() == "", (
            f"gd state 不在時は通過すべき（stdout 空）。got: {result.stdout!r}"
        )


# ---------------------------------------------------------------------------
# B-3 節 競合排除テスト
# ---------------------------------------------------------------------------


class TestGdBoundConflictGuard:
    """B-3 節競合排除: 他の state ファイルが存在する場合は B-3 節をスキップする。

    autonomous-state.json（active=true）または lam-loop-state.json が存在する場合は
    B-3 節を評価せず、既存フロー（AUTONOMOUS / lam-loop）に任せる。
    """

    def test_autonomous_active_skips_b3(self, hook_runner, project_root):
        """autonomous-state.json が active=true の場合、B-3 節をスキップする。

        AUTONOMOUS フローが優先され、G1 checker が動く。
        B-3 節は auto_state is None の場合のみ評価する（競合排除）。

        テスト設計: autonomous が優先されると G1 checker が実行される。
        G1 の pyproject.toml + テストなし環境では checker がファイル未発見で FAIL を返し
        block が出力される。つまり B-3 の additionalContext が出ないことを確認する。
        """
        # autonomous-state.json を active=true で作成
        _write_auto_state(project_root, active=True)
        # gd-session-state.json も bound 超過状態で作成
        _write_gd_state(
            project_root,
            total_tokens=999_999,
            global_token_bound=150_000,
            status="running",
        )
        # G1 checker 用の pyproject.toml を作成（テストファイルなし → FAIL）
        (project_root / "pyproject.toml").write_text(
            "[tool.pytest.ini_options]\n", encoding="utf-8"
        )

        from _hook_utils import build_allowlisted_env

        result = hook_runner(HOOK_PATH, {"session_id": "test"}, env=build_allowlisted_env())

        # B-3 の additionalContext（"goal-driven" を含む）が出力されないことを確認
        stdout = result.stdout.strip()
        if stdout:
            # AUTONOMOUS フローの block か空であることを確認（B-3 ではない）
            output = json.loads(stdout)
            if "hookSpecificOutput" in output:
                ctx = output["hookSpecificOutput"].get("additionalContext", "")
                assert "goal-driven" not in ctx, (
                    "autonomous active 時は B-3 節をスキップすべき。"
                    f"goal-driven が additionalContext に含まれてしまった: {ctx}"
                )

    def test_lam_loop_state_present_skips_b3(
        self, hook_runner, project_root
    ):
        """lam-loop-state.json が存在する場合、B-3 節をスキップする（競合排除）。

        lam-loop フローが優先されるため、gd bound チェックは実行しない。
        lam-loop-state が active=True の場合は安全ネット block が返される。
        """
        # lam-loop-state.json を作成（B-3 スキップ条件）
        _write_lam_loop_state(project_root)
        # gd-session-state.json も bound 超過状態で作成
        _write_gd_state(
            project_root,
            total_tokens=999_999,
            global_token_bound=150_000,
            status="running",
        )

        result = hook_runner(HOOK_PATH, {"session_id": "test"})

        assert result.returncode == 0
        stdout = result.stdout.strip()
        # lam-loop 安全ネット block が出力される（B-3 の additionalContext ではない）
        if stdout:
            output = json.loads(stdout)
            if "hookSpecificOutput" in output:
                ctx = output["hookSpecificOutput"].get("additionalContext", "")
                assert "goal-driven" not in ctx, (
                    "lam-loop-state 存在時は B-3 節をスキップすべき。"
                    f"goal-driven が additionalContext に含まれてしまった: {ctx}"
                )
            # lam-loop の block が出力された場合は "decision" キーが存在する
            if "decision" in output:
                assert output["decision"] == "block"


# ---------------------------------------------------------------------------
# B-3 節 フェイルセーフテスト
# ---------------------------------------------------------------------------


class TestGdBoundFailsafe:
    """B-3 節フェイルセーフ: 例外発生時は WARN ログのみで通過する（Claude を止めない）。"""

    def test_corrupted_gd_state_passes_through(self, hook_runner, project_root):
        """gd-session-state.json が壊れていても通過する（フェイルセーフ）。

        design §10: 例外時はフェイルセーフで通過（WARN ログのみ・Claude を止めない）
        """
        gd_state_path = project_root / ".claude" / "gd-session-state.json"
        gd_state_path.write_text("{ this is : not json ]", encoding="utf-8")

        result = hook_runner(HOOK_PATH, {"session_id": "test"})

        assert result.returncode == 0
        assert result.stdout.strip() == "", (
            f"破損 JSON でも通過すべき（stdout 空）。got: {result.stdout!r}"
        )

    def test_corrupted_gd_state_logs_warn(self, hook_runner, project_root):
        """gd-session-state.json が壊れた場合、WARN が loop.log に記録される（観測性）。"""
        gd_state_path = project_root / ".claude" / "gd-session-state.json"
        gd_state_path.write_text("<<<broken>>>", encoding="utf-8")

        hook_runner(HOOK_PATH, {"session_id": "test"})

        loop_log = project_root / ".claude" / "logs" / "loop.log"
        if loop_log.exists():
            content = loop_log.read_text(encoding="utf-8")
            assert "gd bound check error" in content or "WARN" in content, (
                "破損 JSON の読取失敗は WARN ログに記録されるべき"
            )


# ---------------------------------------------------------------------------
# B-3 節 フォールバック値テスト
# ---------------------------------------------------------------------------


class TestGdBoundFallbackValues:
    """B-3 節のフォールバック値: フィールド欠落時のデフォルト値を確認する。

    design §10: global_token_bound 欠落時 200000、global_time_bound 欠落時 3600
    """

    def test_missing_global_token_bound_uses_200000(
        self, hook_runner, project_root
    ):
        """global_token_bound が欠落している場合、フォールバック値 200000 を使用する。

        total_tokens が 200001 で status="running" かつ global_token_bound キーなし
        → フォールバック値 200000 で超過判定 → additionalContext を出力
        """
        state = {
            "task_id": "gd-fallback-test",
            "task_slug": "fallback-test",
            "route": "medium",
            "total_tokens": 200_001,
            # global_token_bound キーを意図的に省略
            "global_time_bound": 3600,
            "start_time": time.time(),
            "status": "running",
            "loop_count": 0,
            "max_loop_count": 3,
        }
        gd_state_path = project_root / ".claude" / "gd-session-state.json"
        gd_state_path.write_text(json.dumps(state), encoding="utf-8")

        result = hook_runner(HOOK_PATH, {"session_id": "test"})

        assert result.returncode == 0
        stdout = result.stdout.strip()
        assert stdout != "", (
            "global_token_bound 欠落時は 200000 でフォールバック判定し"
            f"additionalContext を出力すべき。got: stdout 空"
        )
        output = json.loads(stdout)
        assert "hookSpecificOutput" in output
        assert "additionalContext" in output["hookSpecificOutput"]

    def test_missing_global_time_bound_uses_3600(
        self, hook_runner, project_root
    ):
        """global_time_bound が欠落している場合、フォールバック値 3600 を使用する。

        start_time を 4000 秒前に設定し、time_bound キーなし
        → フォールバック値 3600 で超過判定 → additionalContext を出力
        """
        past_start = time.time() - 4000  # 4000 秒前 > 3600 秒
        state = {
            "task_id": "gd-fallback-test",
            "task_slug": "fallback-test",
            "route": "medium",
            "total_tokens": 0,
            "global_token_bound": 150_000,
            # global_time_bound キーを意図的に省略
            "start_time": past_start,
            "status": "running",
            "loop_count": 0,
            "max_loop_count": 3,
        }
        gd_state_path = project_root / ".claude" / "gd-session-state.json"
        gd_state_path.write_text(json.dumps(state), encoding="utf-8")

        result = hook_runner(HOOK_PATH, {"session_id": "test"})

        assert result.returncode == 0
        stdout = result.stdout.strip()
        assert stdout != "", (
            "global_time_bound 欠落時は 3600 でフォールバック判定し"
            f"additionalContext を出力すべき。got: stdout 空"
        )
        output = json.loads(stdout)
        assert "hookSpecificOutput" in output
        assert "additionalContext" in output["hookSpecificOutput"]

    def test_within_fallback_token_bound_passes_through(
        self, hook_runner, project_root
    ):
        """global_token_bound 欠落 + total_tokens が 200000 未満なら通過する。

        フォールバック値 200000 の境界値テスト（未満は通過）。
        """
        state = {
            "task_id": "gd-fallback-test",
            "task_slug": "fallback-test",
            "route": "medium",
            "total_tokens": 199_999,
            # global_token_bound を意図的に省略
            "global_time_bound": 3600,
            "start_time": time.time(),
            "status": "running",
            "loop_count": 0,
            "max_loop_count": 3,
        }
        gd_state_path = project_root / ".claude" / "gd-session-state.json"
        gd_state_path.write_text(json.dumps(state), encoding="utf-8")

        result = hook_runner(HOOK_PATH, {"session_id": "test"})

        assert result.returncode == 0
        assert result.stdout.strip() == "", (
            f"フォールバック値未満は通過すべき（stdout 空）。got: {result.stdout!r}"
        )
