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
