"""test_stop_hook_autonomous.py - lam-stop-hook.py の AUTONOMOUS フロー TDD テスト

T1-3: Stop hook に autonomous 検出 + checker(G1) 厳密実行
対応仕様: docs/specs/autonomous-mode/design.md D3 / FR-4.1a / FR-4.1b
"""

from __future__ import annotations

import json
import os
from pathlib import Path

HOOK_PATH = Path(__file__).resolve().parent.parent / "lam-stop-hook.py"


def _write_auto_state(project_root: Path, **overrides) -> Path:
    """autonomous-state.json を tmp プロジェクトに書く（build_initial_state ベース）。"""
    import autonomous_state

    state = autonomous_state.build_initial_state("docs/specs/foo/requirements.md")
    state.update(overrides)
    p = project_root / ".claude" / "autonomous-state.json"
    p.write_text(json.dumps(state), encoding="utf-8")
    return p


def _read_auto_state(project_root: Path) -> dict:
    p = project_root / ".claude" / "autonomous-state.json"
    return json.loads(p.read_text(encoding="utf-8"))


def _full_env() -> dict:
    """実運用の Stop hook は full env で起動される。ネスト実行される checker→pytest が
    Windows のシステム環境変数を要するため full env を渡す（LAM_PROJECT_ROOT は autouse
    fixture 経由で tmp に維持され実プロジェクトは汚染しない）。"""
    return dict(os.environ)


class TestAutonomousStopHook:
    """design D3: Stop hook が checker(G1) を厳密実行し completion を gate する。"""

    def test_g1_pass_completion_stops(
        self, hook_runner, project_root, hooks_on_syspath
    ):
        """G1 PASS → completion 許可（停止・active=false・phase=done・g1_exit=0）。"""
        _write_auto_state(project_root, active=True, iteration=0, max_iterations=20)
        (project_root / "pyproject.toml").write_text(
            "[tool.pytest.ini_options]\n", encoding="utf-8"
        )
        (project_root / "test_p.py").write_text(
            "def test_ok():\n    assert True\n", encoding="utf-8"
        )

        result = hook_runner(HOOK_PATH, {"session_id": "x"}, env=_full_env())

        assert result.returncode == 0
        assert result.stdout.strip() == "", (
            f"G1 PASS は停止許可（stdout 空）であるべき。got: {result.stdout!r}"
        )
        state = _read_auto_state(project_root)
        assert state["active"] is False
        assert state["phase"] == "done"
        assert state["checker_results"]["g1_exit"] == 0

    def test_g1_fail_blocks(self, hook_runner, project_root, hooks_on_syspath):
        """G1 FAIL → block（継続・iteration++・phase=building・g1_exit!=0）。"""
        _write_auto_state(project_root, active=True, iteration=0, max_iterations=20)
        (project_root / "pyproject.toml").write_text(
            "[tool.pytest.ini_options]\n", encoding="utf-8"
        )
        (project_root / "test_f.py").write_text(
            "def test_ng():\n    assert False\n", encoding="utf-8"
        )

        result = hook_runner(HOOK_PATH, {"session_id": "x"}, env=_full_env())

        assert result.returncode == 0
        assert '"decision": "block"' in result.stdout, (
            f"G1 FAIL は block すべき。got: {result.stdout!r}"
        )
        state = _read_auto_state(project_root)
        assert state["iteration"] == 1
        assert state["phase"] == "building"
        assert state["checker_results"]["g1_exit"] != 0

    def test_max_iterations_stops(self, hook_runner, project_root, hooks_on_syspath):
        """iteration >= max_iterations → 停止（active=false・主 bound）。"""
        _write_auto_state(project_root, active=True, iteration=20, max_iterations=20)

        result = hook_runner(HOOK_PATH, {"session_id": "x"}, env=_full_env())

        assert result.returncode == 0
        assert result.stdout.strip() == ""
        state = _read_auto_state(project_root)
        assert state["active"] is False

    def test_inactive_falls_through_to_loop_state(
        self, hook_runner, project_root, hooks_on_syspath
    ):
        """autonomous 非active時は既存 lam-loop-state.json フローが不変（回帰防止の要）。"""
        from conftest import write_state

        _write_auto_state(project_root, active=False)
        write_state(project_root, {"active": True, "iteration": 0, "max_iterations": 5})

        result = hook_runner(HOOK_PATH, {"session_id": "x"}, env=_full_env())

        assert result.returncode == 0
        assert '"decision": "block"' in result.stdout, (
            "autonomous 非active時は既存安全ネットが block すべき（回帰なし）"
        )


class TestAutonomousFailClose:
    """監査 B1 回帰: 状態二度読み廃止後の fail-close 経路。

    _load_active_autonomous_state は単一読込で active=true の state のみ返し、
    非存在 / 読取失敗 / active≠True は None（fail-close）。autonomous フローへ
    分岐しないため、旧「二度読み」fail-open(TOCTOU) 経路を持たない。
    """

    def _write_raw_auto_state(self, project_root: Path, content: str) -> Path:
        p = project_root / ".claude" / "autonomous-state.json"
        p.write_text(content, encoding="utf-8")
        return p

    def test_corrupted_state_graceful_stop(
        self, hook_runner, project_root, hooks_on_syspath
    ):
        """壊れた autonomous-state.json → None → 通常停止（stdout 空・exit 0）。

        lam-loop-state.json も無いため、fall-through 先でも「no state file → 通常停止」。
        旧コードのように _handle_autonomous へ入って fail-open することはない。
        """
        self._write_raw_auto_state(project_root, "{ this is : not json ]")

        result = hook_runner(HOOK_PATH, {"session_id": "x"}, env=_full_env())

        assert result.returncode == 0
        assert result.stdout.strip() == "", (
            f"壊れ state は通常停止（stdout 空）すべき。got: {result.stdout!r}"
        )

    def test_corrupted_state_is_logged_observability(
        self, hook_runner, project_root, hooks_on_syspath
    ):
        """壊れた state の読取失敗は黙殺せず WARN ログに残る（B1 観測性）。"""
        self._write_raw_auto_state(project_root, "<<<broken>>>")

        hook_runner(HOOK_PATH, {"session_id": "x"}, env=_full_env())

        loop_log = project_root / ".claude" / "logs" / "loop.log"
        assert loop_log.exists(), "loop.log が作成されるべき"
        content = loop_log.read_text(encoding="utf-8")
        assert "autonomous state read/parse error" in content, (
            "読取失敗は WARN ログに記録されるべき（黙殺禁止）"
        )

    def test_corrupted_state_does_not_hijack_active_loop(
        self, hook_runner, project_root, hooks_on_syspath
    ):
        """壊れた autonomous-state.json + active な lam-loop-state → 既存安全ネットへ
        決定的に fall-through し block する（autonomous フローへ誤って入らない）。"""
        from conftest import write_state

        self._write_raw_auto_state(project_root, "not-json")
        write_state(project_root, {"active": True, "iteration": 0, "max_iterations": 5})

        result = hook_runner(HOOK_PATH, {"session_id": "x"}, env=_full_env())

        assert result.returncode == 0
        assert '"decision": "block"' in result.stdout, (
            "壊れ autonomous state は非autonomous 扱いとなり既存フローが block すべき"
        )

    def test_active_non_bool_true_is_fail_close(
        self, hook_runner, project_root, hooks_on_syspath
    ):
        """active が真偽 True 以外（文字列 "true" 等）は fail-close（autonomous 非該当）。

        strict な `is True` 判定により、改竄・型崩れ state では autonomous gate に
        入らず通常フローへ落ちる。active な lam-loop-state で fall-through を観測する。
        """
        from conftest import write_state

        self._write_raw_auto_state(project_root, json.dumps({"active": "true"}))
        write_state(project_root, {"active": True, "iteration": 0, "max_iterations": 5})

        result = hook_runner(HOOK_PATH, {"session_id": "x"}, env=_full_env())

        assert result.returncode == 0
        assert '"decision": "block"' in result.stdout, (
            'active="true"（文字列）は autonomous 非該当として fall-through すべき'
        )
