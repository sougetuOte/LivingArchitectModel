"""
test_subagent_boundary.py - ADR-0008 Phase B-4 / B-2b subagent 境界判定テスト

pre-tool-use.py の Task/Agent 検知 + AUTONOMOUS フェーズ ask 動作 + 通常フェーズ log_only 動作を検証。
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

HOOK_PATH = Path(__file__).resolve().parent.parent / "pre-tool-use.py"


def _write_phase(project_root: Path, phase: str) -> None:
    phase_file = project_root / ".claude" / "current-phase.md"
    phase_file.parent.mkdir(parents=True, exist_ok=True)
    phase_file.write_text(f"**{phase}**\n", encoding="utf-8")


class TestSubagentBoundaryNonAutonomous:
    """通常フェーズ（PLANNING/BUILDING/AUDITING）の subagent 起動は log_only"""

    @pytest.mark.parametrize("phase", ["PLANNING", "BUILDING", "AUDITING"])
    def test_task_tool_non_autonomous_log_only(self, hook_runner, project_root, phase):
        """Task ツール起動は通常フェーズで素通し（stdout 空 / ログ記録のみ）"""
        _write_phase(project_root, phase)
        result = hook_runner(
            HOOK_PATH,
            {
                "tool_name": "Task",
                "tool_input": {
                    "subagent_type": "Explore",
                    "description": "Test exploration",
                    "prompt": "Find files",
                },
            },
        )
        assert result.returncode == 0
        # log_only 相当 → stdout は空（PM ask を出さない）
        assert result.stdout.strip() == "", (
            f"通常フェーズの Task 起動は素通しのはず: stdout={result.stdout!r}"
        )
        # permission.log には "subagent launch" が LOG レベルで記録される
        log_file = project_root / ".claude" / "logs" / "permission.log"
        assert log_file.exists()
        assert "subagent launch" in log_file.read_text(encoding="utf-8")

    def test_agent_tool_non_autonomous_log_only(self, hook_runner, project_root):
        """Agent ツール（Task の旧称）も同様に log_only"""
        _write_phase(project_root, "BUILDING")
        result = hook_runner(
            HOOK_PATH,
            {
                "tool_name": "Agent",
                "tool_input": {"subagent_type": "code-reviewer"},
            },
        )
        assert result.returncode == 0
        assert result.stdout.strip() == ""


class TestSubagentBoundaryAutonomous:
    """AUTONOMOUS フェーズの subagent 起動は ask（classifier 重ね掛け二重防御）"""

    def test_task_tool_autonomous_pm_ask(self, hook_runner, project_root):
        """AUTONOMOUS + Task 起動は PM ask 応答"""
        _write_phase(project_root, "AUTONOMOUS")
        result = hook_runner(
            HOOK_PATH,
            {
                "tool_name": "Task",
                "tool_input": {
                    "subagent_type": "autonomous-engine",
                    "description": "Self-loop step",
                },
            },
        )
        assert result.returncode == 0
        stdout = result.stdout.strip()
        assert stdout, f"AUTONOMOUS の Task 起動は ask が出るはず: stderr={result.stderr!r}"
        data = json.loads(stdout)
        hsp = data["hookSpecificOutput"]
        assert hsp["permissionDecision"] == "ask"
        assert "AUTONOMOUS subagent launch" in hsp["permissionDecisionReason"]
        assert "autonomous-engine" in hsp["permissionDecisionReason"]

    def test_agent_tool_autonomous_pm_ask(self, hook_runner, project_root):
        """AUTONOMOUS + Agent 起動も同様に ask"""
        _write_phase(project_root, "AUTONOMOUS")
        result = hook_runner(
            HOOK_PATH,
            {
                "tool_name": "Agent",
                "tool_input": {"subagent_type": "general-purpose"},
            },
        )
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["hookSpecificOutput"]["permissionDecision"] == "ask"


class TestNonSubagentToolsUntouched:
    """subagent 以外のツールには影響しない（既存挙動維持）"""

    def test_bash_in_autonomous_not_treated_as_subagent(self, hook_runner, project_root):
        """AUTONOMOUS でも Bash は subagent 境界判定対象外（既存 deny/SE 経路）"""
        _write_phase(project_root, "AUTONOMOUS")
        result = hook_runner(
            HOOK_PATH,
            {
                "tool_name": "Bash",
                "tool_input": {"command": "echo hello"},
            },
        )
        assert result.returncode == 0
        # AUTONOMOUS でも Bash 単体は subagent 境界経路に乗らない（SE 級素通し or 既存判定）
        stdout = result.stdout.strip()
        if stdout:
            # 何か応答が出る場合は ask か deny のどちらかだが、
            # 少なくとも reason に "subagent" が含まれていないことを確認
            data = json.loads(stdout)
            reason = data.get("hookSpecificOutput", {}).get("permissionDecisionReason", "")
            assert "subagent" not in reason.lower()

    def test_edit_normal_path_untouched(self, hook_runner, project_root):
        """Edit on src/ は subagent 境界判定対象外（既存 SE 級判定）"""
        _write_phase(project_root, "AUTONOMOUS")
        result = hook_runner(
            HOOK_PATH,
            {
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": "src/main.py",
                    "old_string": "old",
                    "new_string": "new",
                },
            },
        )
        assert result.returncode == 0
        # SE 級素通し（stdout 空）
        assert result.stdout.strip() == ""
