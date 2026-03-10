"""
test_pre_tool_use.py - pre-tool-use.py の TDD テスト

W2-T2: Red フェーズ（テストファースト）
対応仕様: docs/specs/hooks-python-migration/design.md Section 3.2
"""
import json
from pathlib import Path

import pytest

# テスト対象フックのパス
HOOK_PATH = Path(__file__).resolve().parent.parent / "pre-tool-use.py"


class TestPreToolUse:
    """pre-tool-use.py の権限等級判定テスト"""

    def test_read_tool_pg_allow(self, hook_runner):
        """Read ツールは PG 級として許可される（exit 0、stdout なし）"""
        input_json = {
            "tool_name": "Read",
            "tool_input": {
                "file_path": "src/main.py",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        # PG 許可: stdout に hookSpecificOutput が出力されない
        stdout = result.stdout.strip()
        if stdout:
            data = json.loads(stdout)
            assert "hookSpecificOutput" not in data or data.get("hookSpecificOutput", {}).get("permissionDecision") != "deny"

    def test_edit_specs_pm_deny(self, hook_runner):
        """Edit で docs/specs/*.md を編集すると PM deny が返る"""
        input_json = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "docs/specs/test.md",
                "old_string": "old",
                "new_string": "new",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        stdout = result.stdout.strip()
        assert stdout, "PM deny 時は stdout に JSON が出力されるべき"
        data = json.loads(stdout)
        assert "hookSpecificOutput" in data
        hook_output = data["hookSpecificOutput"]
        assert hook_output["permissionDecision"] == "deny"
        assert "docs/specs/test.md" in hook_output["permissionDecisionReason"]
        assert "PM" in hook_output["permissionDecisionReason"]

    def test_edit_rules_auto_generated_pm_deny(self, hook_runner):
        """Edit で .claude/rules/auto-generated/ 配下のファイルを編集すると PM deny が返る"""
        input_json = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": ".claude/rules/auto-generated/rule.md",
                "old_string": "old",
                "new_string": "new",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        stdout = result.stdout.strip()
        assert stdout, "PM deny 時は stdout に JSON が出力されるべき"
        data = json.loads(stdout)
        assert "hookSpecificOutput" in data
        hook_output = data["hookSpecificOutput"]
        assert hook_output["permissionDecision"] == "deny"
        assert "PM" in hook_output["permissionDecisionReason"]

    def test_absolute_path_normalization(self, hook_runner, project_root):
        """絶対パスが project_root からの相対パスに正規化されて SE 判定される"""
        abs_path = str(project_root / "src" / "main.py")
        input_json = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": abs_path,
                "old_string": "old",
                "new_string": "new",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        # SE 級: stdout には deny JSON が出力されない
        stdout = result.stdout.strip()
        if stdout:
            data = json.loads(stdout)
            if "hookSpecificOutput" in data:
                assert data["hookSpecificOutput"].get("permissionDecision") != "deny"

    def test_edit_src_se_allow(self, hook_runner):
        """Edit で src/main.py を編集すると SE 許可（exit 0）"""
        input_json = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "src/main.py",
                "old_string": "old",
                "new_string": "new",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        stdout = result.stdout.strip()
        # SE 許可: PM deny が出力されない
        if stdout:
            data = json.loads(stdout)
            if "hookSpecificOutput" in data:
                assert data["hookSpecificOutput"].get("permissionDecision") != "deny"

    def test_log_truncation(self, hook_runner, project_root):
        """ログのターゲットフィールドが 100 文字でトランケートされる"""
        # 150 文字のパスを生成
        long_path = "src/" + "a" * 150 + ".py"
        input_json = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": long_path,
                "old_string": "old",
                "new_string": "new",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        # ログファイルを確認
        log_file = project_root / ".claude" / "logs" / "permission.log"
        assert log_file.exists(), "ログファイルが作成されるべき"
        log_content = log_file.read_text(encoding="utf-8")
        # ログの各フィールドを確認: timestamp, level, tool_name, target(100文字)
        lines = [l for l in log_content.strip().split("\n") if "Edit" in l and "aaa" in l]
        assert lines, "Edit のログが記録されるべき"
        last_line = lines[-1]
        fields = last_line.split("\t")
        # target フィールドは 4番目（0-indexed: 3）
        if len(fields) >= 4:
            target = fields[3]
            # trunc 後は 100 文字以内
            assert len(target) <= 100, f"target が 100 文字を超えている: {len(target)}"

    def test_glob_tool_pg_allow(self, hook_runner):
        """Glob ツールは PG 級として許可される（exit 0、deny なし）"""
        input_json = {
            "tool_name": "Glob",
            "tool_input": {
                "pattern": "**/*.py",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        stdout = result.stdout.strip()
        if stdout:
            data = json.loads(stdout)
            assert "hookSpecificOutput" not in data or data.get("hookSpecificOutput", {}).get("permissionDecision") != "deny"

    def test_grep_tool_pg_allow(self, hook_runner):
        """Grep ツールは PG 級として許可される（exit 0、deny なし）"""
        input_json = {
            "tool_name": "Grep",
            "tool_input": {
                "pattern": "def main",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        stdout = result.stdout.strip()
        if stdout:
            data = json.loads(stdout)
            assert "hookSpecificOutput" not in data or data.get("hookSpecificOutput", {}).get("permissionDecision") != "deny"
