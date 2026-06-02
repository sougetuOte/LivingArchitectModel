"""test_autonomous_state.py - autonomous_state.py の TDD テスト

T1-1: autonomous-state.json 最小スキーマ（design D1）
対応仕様: docs/specs/autonomous-mode/design.md D1 / tasks.md T1-1 / FR-1.1
"""

from __future__ import annotations

from pathlib import Path


class TestBuildInitialState:
    """build_initial_state が design D1 スキーマと文字単位で一致することを検証。"""

    def test_initial_state_matches_design_d1(self, hooks_on_syspath):
        """build_initial_state が design D1 の全フィールド・初期値と一致する。"""
        import autonomous_state

        state = autonomous_state.build_initial_state(
            "docs/specs/foo/requirements.md",
            started_at="2026-05-30T00:00:00Z",
        )
        expected = {
            "active": True,
            "mode": "autonomous",
            "spec_target": "docs/specs/foo/requirements.md",
            "phase": "building",
            "iteration": 0,
            "max_iterations": 20,
            "started_at": "2026-05-30T00:00:00Z",
            "checker_results": {
                "g1_exit": None,
                "g2_exit": None,
                "g5_exit": None,
                "checked_at": None,
            },
            "pm_queue": [],
            "pm_queue_limit": 5,
            "se_log": [],
            "escalation_budget": {
                "magi_count": 0,
                "magi_limit": 3,
                "full_review_count": 0,
                "full_review_limit": 1,
            },
            "consecutive_clean_runs": 0,
            "tripwire_n": 3,
            "tripwire_level": 0,
            "log": [],
        }
        assert state == expected

    def test_started_at_defaults_to_utc_now(self, hooks_on_syspath):
        """started_at 未指定時は UTC ISO 8601（Z 終端）で補完される。"""
        import autonomous_state

        state = autonomous_state.build_initial_state("docs/specs/foo/requirements.md")
        assert state["started_at"].endswith("Z")
        assert state["iteration"] == 0

    def test_max_iterations_8_override(self, hooks_on_syspath):
        """max_iterations=8 を渡すと state に 8 が反映される（外部化・調整可）。"""
        import autonomous_state

        state = autonomous_state.build_initial_state(
            "docs/specs/foo/requirements.md", max_iterations=8
        )
        assert state["max_iterations"] == 8

    def test_state_file_path_is_independent_from_loop_state(
        self, hooks_on_syspath, tmp_path
    ):
        """autonomous-state.json は lam-loop-state.json と独立（design D1 分離理由）。"""
        import autonomous_state

        p = autonomous_state.state_file_path(tmp_path)
        assert isinstance(p, Path)
        assert p.name == "autonomous-state.json"
        assert p.name != "lam-loop-state.json"
        assert p.parent.name == ".claude"
