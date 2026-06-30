"""
test_incident_patterns.py - ADR-0008 Phase B-4 / B-2a 動的 deny テスト

_incident_patterns.py の単体テスト + pre-tool-use.py への統合テスト。
yaml fail-open / 3 演算子マッチ / log_only ログ記録 / additionalContext 出力検証。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HOOK_PATH = Path(__file__).resolve().parent.parent / "pre-tool-use.py"
HOOKS_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# 単体テスト: _incident_patterns モジュール
# ============================================================


@pytest.fixture()
def incident_module(monkeypatch):
    """_incident_patterns モジュールを sys.path 経由で import する。"""
    monkeypatch.syspath_prepend(str(HOOKS_DIR))
    import _incident_patterns

    return _incident_patterns


def _write_yaml(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestLoadPatterns:
    """load_patterns() の fail-open 仕様検証"""

    def test_missing_file_returns_none(self, incident_module, tmp_path):
        """yaml 不在時は None を返す（fail-open）"""
        result = incident_module.load_patterns(tmp_path / "nonexistent.yaml")
        assert result is None

    def test_parse_error_returns_none(self, incident_module, tmp_path):
        """yaml パース失敗時は None を返す（fail-open）"""
        bad = tmp_path / "bad.yaml"
        bad.write_text("not: valid: yaml: [unclosed", encoding="utf-8")
        result = incident_module.load_patterns(bad)
        assert result is None

    def test_missing_patterns_key_returns_none(self, incident_module, tmp_path):
        """patterns キーがない yaml は None"""
        yaml_file = tmp_path / "x.yaml"
        _write_yaml(yaml_file, "version: 1\nlast_updated: 2026-06-30\n")
        result = incident_module.load_patterns(yaml_file)
        assert result is None

    def test_filters_inactive_patterns(self, incident_module, tmp_path):
        """active: false は除外される"""
        yaml_file = tmp_path / "x.yaml"
        _write_yaml(yaml_file, """
version: 1
patterns:
  - id: P-1
    source_md: x.md
    trigger_type: tool_set
    trigger_pattern: [Bash]
    action: log_only
    severity: low
    description: active
    active: true
  - id: P-2
    source_md: x.md
    trigger_type: tool_set
    trigger_pattern: [Bash]
    action: log_only
    severity: low
    description: inactive
    active: false
""")
        result = incident_module.load_patterns(yaml_file)
        assert result is not None
        assert len(result) == 1
        assert result[0]["id"] == "P-1"

    def test_filters_invalid_trigger_type(self, incident_module, tmp_path):
        """trigger_type が許容外なら除外"""
        yaml_file = tmp_path / "x.yaml"
        _write_yaml(yaml_file, """
version: 1
patterns:
  - id: P-bad
    source_md: x.md
    trigger_type: regex_unsupported
    trigger_pattern: ".*"
    action: deny
    severity: low
    description: bad
    active: true
""")
        result = incident_module.load_patterns(yaml_file)
        assert result == []

    def test_filters_invalid_action(self, incident_module, tmp_path):
        """action が許容外なら除外"""
        yaml_file = tmp_path / "x.yaml"
        _write_yaml(yaml_file, """
version: 1
patterns:
  - id: P-bad
    source_md: x.md
    trigger_type: tool_set
    trigger_pattern: [Bash]
    action: warn
    severity: low
    description: bad
    active: true
""")
        result = incident_module.load_patterns(yaml_file)
        assert result == []


class TestMatchInput:
    """match_input() の 3 演算子マッチング検証"""

    def _patterns(self) -> list[dict]:
        return [
            {
                "id": "P-glob",
                "source_md": "x.md",
                "trigger_type": "path_glob",
                "trigger_pattern": ".claude/grep_*.txt",
                "action": "ask",
                "severity": "mid",
                "description": "glob test",
                "active": True,
            },
            {
                "id": "P-lit",
                "source_md": "x.md",
                "trigger_type": "command_literal",
                "trigger_pattern": "rm -rf /",
                "action": "deny",
                "severity": "critical",
                "description": "literal test",
                "active": True,
            },
            {
                "id": "P-set",
                "source_md": "x.md",
                "trigger_type": "tool_set",
                "trigger_pattern": ["Bash", "Edit"],
                "action": "log_only",
                "severity": "low",
                "description": "set test",
                "active": True,
            },
        ]

    def test_path_glob_match(self, incident_module):
        result = incident_module.match_input(
            self._patterns(), "Write", ".claude/grep_results.txt", ""
        )
        assert result is not None
        assert result.incident_id == "P-glob"
        assert result.action == "ask"

    def test_path_glob_backslash_normalized(self, incident_module):
        """Windows パス区切り \\ も / に正規化されてマッチする"""
        result = incident_module.match_input(
            self._patterns(), "Write", ".claude\\grep_results.txt", ""
        )
        assert result is not None
        assert result.incident_id == "P-glob"

    def test_command_literal_match(self, incident_module):
        result = incident_module.match_input(
            self._patterns(), "Bash", "", "rm -rf /"
        )
        # command が複数演算子に同時マッチするので最初のマッチが返る。
        # _patterns 順序は path_glob → command_literal → tool_set だが、
        # path_glob は file_path 空で不発、command_literal が成立。
        assert result is not None
        assert result.incident_id == "P-lit"
        assert result.action == "deny"
        assert result.severity == "critical"

    def test_command_literal_no_match_with_extra_args(self, incident_module):
        """完全一致のみ。引数違いはマッチしない"""
        result = incident_module.match_input(
            self._patterns(), "Bash", "", "rm -rf / --no-preserve-root"
        )
        # P-set (tool_set) が Bash でマッチするので log_only が返る
        assert result is not None
        assert result.incident_id == "P-set"
        assert result.action == "log_only"

    def test_tool_set_match(self, incident_module):
        result = incident_module.match_input(
            self._patterns(), "Edit", "src/main.py", ""
        )
        assert result is not None
        assert result.incident_id == "P-set"

    def test_no_match_returns_none(self, incident_module):
        result = incident_module.match_input(
            self._patterns(), "Read", "src/main.py", ""
        )
        # Read は tool_set リストにない / path_glob は src/main.py に当たらない
        assert result is None

    def test_empty_patterns_returns_none(self, incident_module):
        assert incident_module.match_input(None, "Bash", "", "ls") is None
        assert incident_module.match_input([], "Bash", "", "ls") is None


# ============================================================
# 統合テスト: pre-tool-use.py 経由（incident-patterns.yaml ベース）
# ============================================================


def _setup_incident_yaml(project_root: Path, yaml_body: str) -> None:
    target = project_root / "docs" / "artifacts" / "incident-patterns.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(yaml_body, encoding="utf-8")


class TestPreToolUseIncidentIntegration:
    """pre-tool-use.py への incident pattern 統合動作"""

    def test_ask_action_emits_ask_with_additional_context(
        self, hook_runner, project_root
    ):
        """action=ask のパターンマッチ時、ask 応答 + additionalContext が出力される"""
        _setup_incident_yaml(project_root, """
version: 1
patterns:
  - id: P-3-temp-file-pre-push-leak
    source_md: docs/artifacts/retro-B4-W1-W15.md
    trigger_type: path_glob
    trigger_pattern: ".claude/grep_*.txt"
    action: ask
    severity: mid
    description: temp file leak guard
    active: true
""")
        result = hook_runner(
            HOOK_PATH,
            {
                "tool_name": "Write",
                "tool_input": {"file_path": ".claude/grep_results.txt", "content": "x"},
            },
        )
        assert result.returncode == 0
        stdout = result.stdout.strip()
        assert stdout, f"incident ask 時は stdout に JSON が出力されるべき: stderr={result.stderr!r}"
        data = json.loads(stdout)
        hsp = data["hookSpecificOutput"]
        assert hsp["permissionDecision"] == "ask"
        assert "P-3-temp-file-pre-push-leak" in hsp["permissionDecisionReason"]
        # B-2c: additionalContext で Claude 側に検知文言を残す
        assert "additionalContext" in hsp
        assert "P-3-temp-file-pre-push-leak" in hsp["additionalContext"]
        assert len(hsp["additionalContext"]) <= 10000

    def test_deny_action_emits_deny(self, hook_runner, project_root):
        """action=deny のパターンマッチ時、deny 応答が出力される"""
        _setup_incident_yaml(project_root, """
version: 1
patterns:
  - id: P-X-deny-sample
    source_md: x.md
    trigger_type: command_literal
    trigger_pattern: "danger-cmd --execute"
    action: deny
    severity: high
    description: deny test
    active: true
""")
        result = hook_runner(
            HOOK_PATH,
            {
                "tool_name": "Bash",
                "tool_input": {"command": "danger-cmd --execute"},
            },
        )
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        hsp = data["hookSpecificOutput"]
        assert hsp["permissionDecision"] == "deny"
        assert "P-X-deny-sample" in hsp["permissionDecisionReason"]

    def test_log_only_action_does_not_block(self, hook_runner, project_root):
        """action=log_only はブロックせず通常 flow を継続する（Bash → 既存 SE 判定）"""
        _setup_incident_yaml(project_root, """
version: 1
patterns:
  - id: P-2-log-only-sample
    source_md: x.md
    trigger_type: tool_set
    trigger_pattern: [Bash]
    action: log_only
    severity: low
    description: log only test
    active: true
""")
        result = hook_runner(
            HOOK_PATH,
            {
                "tool_name": "Bash",
                "tool_input": {"command": "ls -la"},
            },
        )
        assert result.returncode == 0
        # log_only なので hookSpecificOutput は出力されない（SE 級素通し）
        # ただし permission.log には incident_id が記録される
        log_file = project_root / ".claude" / "logs" / "permission.log"
        assert log_file.exists()
        log_content = log_file.read_text(encoding="utf-8")
        assert "P-2-log-only-sample" in log_content

    def test_yaml_missing_does_not_block(self, hook_runner, project_root):
        """incident-patterns.yaml 不在でも hook はブロックしない（fail-open）"""
        # yaml を意図的に作らない
        result = hook_runner(
            HOOK_PATH,
            {
                "tool_name": "Write",
                "tool_input": {"file_path": "src/main.py", "content": "x"},
            },
        )
        assert result.returncode == 0
        # SE 級素通し（stdout 空）
        assert result.stdout.strip() == ""

    def test_yaml_corrupted_does_not_block(self, hook_runner, project_root):
        """incident-patterns.yaml がパース失敗でも fail-open"""
        _setup_incident_yaml(project_root, "not: valid: yaml: [unclosed")
        result = hook_runner(
            HOOK_PATH,
            {
                "tool_name": "Write",
                "tool_input": {"file_path": "src/main.py", "content": "x"},
            },
        )
        assert result.returncode == 0
        assert result.stdout.strip() == ""
