"""
test_pre_tool_use.py - pre-tool-use.py の TDD テスト

W2-T2: Red フェーズ（テストファースト）
対応仕様: docs/design/hooks-python-migration-design.md H1（pre-tool-use）
"""
import json
from pathlib import Path

import pytest

# テスト対象フックのパス
HOOK_PATH = Path(__file__).resolve().parent.parent / "pre-tool-use.py"


class TestPreToolUse:
    """pre-tool-use.py の権限等級判定テスト"""

    def test_read_tool_pg_allow(self, hook_runner):
        """Read ツールは PG 級として許可される（exit 0、stdout 空）"""
        input_json = {
            "tool_name": "Read",
            "tool_input": {
                "file_path": "src/main.py",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        # PG 許可: stdout は空（hookSpecificOutput を出力しない）
        assert result.stdout.strip() == "", f"PG 許可時は stdout が空であるべき。got: {result.stdout!r}"

    def test_edit_specs_pm_ask(self, hook_runner):
        """Edit で docs/specs/*.md を編集すると PM ask が返る"""
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
        assert stdout, "PM ask 時は stdout に JSON が出力されるべき"
        data = json.loads(stdout)
        assert "hookSpecificOutput" in data
        hook_output = data["hookSpecificOutput"]
        assert hook_output["permissionDecision"] == "ask"
        assert isinstance(hook_output["permissionDecisionReason"], str)
        assert len(hook_output["permissionDecisionReason"]) > 0

    def test_edit_rules_auto_generated_pm_ask(self, hook_runner):
        """Edit で .claude/rules/auto-generated/ 配下のファイルを編集すると PM ask が返る"""
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
        assert stdout, "PM ask 時は stdout に JSON が出力されるべき"
        data = json.loads(stdout)
        assert "hookSpecificOutput" in data
        hook_output = data["hookSpecificOutput"]
        assert hook_output["permissionDecision"] == "ask"
        assert isinstance(hook_output["permissionDecisionReason"], str)
        assert len(hook_output["permissionDecisionReason"]) > 0

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
        # SE 級: stdout は空（ask/deny を出力しない）
        assert result.stdout.strip() == "", f"SE 許可時は stdout が空であるべき。got: {result.stdout!r}"

    def test_edit_src_se_allow(self, hook_runner):
        """Edit で src/main.py を編集すると SE 許可（exit 0、stdout 空）"""
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
        # SE 許可: stdout は空
        assert result.stdout.strip() == "", f"SE 許可時は stdout が空であるべき。got: {result.stdout!r}"

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
        lines = [line for line in log_content.strip().split("\n") if "Edit" in line and "aaa" in line]
        assert lines, "Edit のログが記録されるべき"
        last_line = lines[-1]
        fields = last_line.split("\t")
        # target フィールドは 4番目（0-indexed: 3）
        assert len(fields) >= 4, f"ログフィールドが4つ以上あるべき。got: {len(fields)} fields"
        target = fields[3]
        # trunc 後は 100 文字以内
        assert len(target) <= 100, f"target が 100 文字を超えている: {len(target)}"

    def test_glob_tool_pg_allow(self, hook_runner):
        """Glob ツールは PG 級として許可される（exit 0、stdout 空）"""
        input_json = {
            "tool_name": "Glob",
            "tool_input": {
                "pattern": "**/*.py",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        assert result.stdout.strip() == "", f"PG 許可時は stdout が空であるべき。got: {result.stdout!r}"

    def test_grep_tool_pg_allow(self, hook_runner):
        """Grep ツールは PG 級として許可される（exit 0、stdout 空）"""
        input_json = {
            "tool_name": "Grep",
            "tool_input": {
                "pattern": "def main",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        assert result.stdout.strip() == "", f"PG 許可時は stdout が空であるべき。got: {result.stdout!r}"

    @pytest.mark.parametrize("blacklisted_arg", [
        "--config",
        "--settings",
        "--ruleset",
        "--rule-dir",
        "--rulesdir",
        "--plugin",
        "--resolve-plugins-relative-to",
        "--stdin-filename",
        "--ignore-path",
        "--ext",
    ])
    def test_auditing_pg_command_with_blacklisted_arg_pm(self, hook_runner, project_root, blacklisted_arg):
        """AUDITING フェーズで PG コマンドにブラックリスト引数があると PM に昇格する"""
        phase_file = project_root / ".claude" / "current-phase.md"
        phase_file.parent.mkdir(parents=True, exist_ok=True)
        phase_file.write_text("**AUDITING**\n", encoding="utf-8")

        input_json = {
            "tool_name": "Bash",
            "tool_input": {
                "command": f"ruff check --fix {blacklisted_arg} /etc/evil.toml src/",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        stdout = result.stdout.strip()
        assert stdout, f"ブラックリスト引数 {blacklisted_arg} 付き PG コマンドは PM ask を返すべき"
        data = json.loads(stdout)
        assert data["hookSpecificOutput"]["permissionDecision"] == "ask"

    def test_auditing_pg_command_normal_args_allowed(self, hook_runner, project_root):
        """AUDITING フェーズで PG コマンドに正常な引数は PG 許可される"""
        phase_file = project_root / ".claude" / "current-phase.md"
        phase_file.parent.mkdir(parents=True, exist_ok=True)
        phase_file.write_text("**AUDITING**\n", encoding="utf-8")

        input_json = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "ruff check --fix src/main.py",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        assert result.stdout.strip() == "", f"正常引数の PG コマンドは許可されるべき。got: {result.stdout!r}"

    def test_non_auditing_pg_command_se(self, hook_runner, project_root):
        """非 AUDITING フェーズでは PG コマンドも SE として扱われる"""
        # フェーズファイルを作成しない（非 AUDITING）
        input_json = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "ruff check --fix src/main.py",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        assert result.stdout.strip() == "", f"非 AUDITING では SE 許可されるべき。got: {result.stdout!r}"
