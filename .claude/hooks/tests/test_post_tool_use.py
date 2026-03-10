"""
test_post_tool_use.py - post-tool-use.py の TDD テスト

W3-T1: Red フェーズ（テストファースト）
対応仕様: docs/specs/hooks-python-migration/design.md H2（post-tool-use）
"""
import json
from pathlib import Path

# テスト対象フックのパス
HOOK_PATH = Path(__file__).resolve().parent.parent / "post-tool-use.py"


class TestTDDPatternDetection:
    """TDD パターン検出テスト（責務1）"""

    def test_pytest_fail_recorded(self, hook_runner, project_root):
        """Bash + pytest 失敗（exit_code=1）→ tdd-patterns.log に FAIL 記録"""
        input_json = {
            "tool_name": "Bash",
            "tool_input": {"command": "pytest tests/ -v"},
            "tool_response": {
                "exitCode": 1,
                "stdout": "FAILED tests/test_foo.py::test_bar\nAssertionError: assert 1 == 2",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0

        tdd_log = project_root / ".claude" / "tdd-patterns.log"
        assert tdd_log.exists(), "tdd-patterns.log が作成されるべき"
        content = tdd_log.read_text(encoding="utf-8")
        assert "FAIL" in content
        assert "pytest" in content

    def test_pytest_pass_after_fail(self, hook_runner, project_root):
        """失敗後成功 → PASS 記録（last-test-result ファイル経由）"""
        # まず失敗を記録
        fail_input = {
            "tool_name": "Bash",
            "tool_input": {"command": "pytest tests/ -v"},
            "tool_response": {
                "exitCode": 1,
                "stdout": "FAILED tests/test_foo.py::test_bar",
            },
        }
        hook_runner(HOOK_PATH, fail_input)

        # 次に成功を記録
        pass_input = {
            "tool_name": "Bash",
            "tool_input": {"command": "pytest tests/ -v"},
            "tool_response": {
                "exitCode": 0,
                "stdout": "1 passed in 0.12s",
            },
        }
        result = hook_runner(HOOK_PATH, pass_input)
        assert result.returncode == 0

        tdd_log = project_root / ".claude" / "tdd-patterns.log"
        assert tdd_log.exists(), "tdd-patterns.log が作成されるべき"
        content = tdd_log.read_text(encoding="utf-8")
        assert "PASS" in content, "失敗→成功パターンが PASS として記録されるべき"

    def test_npm_test_fail_recorded(self, hook_runner, project_root):
        """npm test 失敗 → FAIL 記録"""
        input_json = {
            "tool_name": "Bash",
            "tool_input": {"command": "npm test"},
            "tool_response": {
                "exitCode": 1,
                "stdout": "FAIL src/app.test.js\n  ● test › should render correctly",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0

        tdd_log = project_root / ".claude" / "tdd-patterns.log"
        assert tdd_log.exists(), "tdd-patterns.log が作成されるべき"
        content = tdd_log.read_text(encoding="utf-8")
        assert "FAIL" in content
        assert "npm test" in content

    def test_go_test_fail_recorded(self, hook_runner, project_root):
        """go test 失敗 → FAIL 記録"""
        input_json = {
            "tool_name": "Bash",
            "tool_input": {"command": "go test ./..."},
            "tool_response": {
                "exitCode": 1,
                "stdout": "--- FAIL: TestFoo (0.00s)\nFAIL\tgithub.com/example/pkg",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0

        tdd_log = project_root / ".claude" / "tdd-patterns.log"
        assert tdd_log.exists(), "tdd-patterns.log が作成されるべき"
        content = tdd_log.read_text(encoding="utf-8")
        assert "FAIL" in content
        assert "go test" in content

    def test_non_test_command_no_record(self, hook_runner, project_root):
        """テスト以外のコマンド（ls）→ 記録なし"""
        input_json = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls -la"},
            "tool_response": {
                "exitCode": 0,
                "stdout": "total 8\ndrwxr-xr-x 2 user user 4096",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0

        tdd_log = project_root / ".claude" / "tdd-patterns.log"
        # 非テストコマンドでは tdd-patterns.log が作成されない
        assert not tdd_log.exists(), "非テストコマンドで tdd-patterns.log が作成されてはいけない"


class TestDocSyncFlag:
    """doc-sync-flag テスト（責務2）"""

    def test_edit_src_doc_sync_flag(self, hook_runner, project_root):
        """Edit + src/main.py → doc-sync-flag に追記"""
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

        doc_sync_flag = project_root / ".claude" / "doc-sync-flag"
        assert doc_sync_flag.exists(), "doc-sync-flag が作成されるべき"
        content = doc_sync_flag.read_text(encoding="utf-8")
        assert "src/main.py" in content

    def test_write_src_doc_sync_flag(self, hook_runner, project_root):
        """Write + src/main.py → doc-sync-flag に追記"""
        input_json = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": "src/main.py",
                "content": "print('hello')",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0

        doc_sync_flag = project_root / ".claude" / "doc-sync-flag"
        assert doc_sync_flag.exists(), "doc-sync-flag が作成されるべき"
        content = doc_sync_flag.read_text(encoding="utf-8")
        assert "src/main.py" in content

    def test_edit_docs_no_sync_flag(self, hook_runner, project_root):
        """Edit + docs/readme.md → doc-sync-flag に追記なし"""
        input_json = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "docs/readme.md",
                "old_string": "old",
                "new_string": "new",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0

        doc_sync_flag = project_root / ".claude" / "doc-sync-flag"
        # doc-sync-flag が存在しないか、存在しても docs/readme.md が記録されていない
        if doc_sync_flag.exists():
            content = doc_sync_flag.read_text(encoding="utf-8")
            assert "docs/readme.md" not in content


class TestLoopLog:
    """ループログテスト（責務3）"""

    def test_loop_state_tool_events(self, hook_runner, project_root):
        """lam-loop-state.json 存在時 → tool_events に追記"""
        # lam-loop-state.json を事前に作成
        loop_state_path = project_root / ".claude" / "lam-loop-state.json"
        initial_state = {"iteration": 1, "tool_events": []}
        loop_state_path.write_text(
            json.dumps(initial_state, ensure_ascii=False),
            encoding="utf-8",
        )

        input_json = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls -la"},
            "tool_response": {
                "exitCode": 0,
                "stdout": "total 8",
            },
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0

        # tool_events に追記されていることを確認
        updated = json.loads(loop_state_path.read_text(encoding="utf-8"))
        assert "tool_events" in updated, "tool_events キーが存在するべき"
        assert len(updated["tool_events"]) > 0, "tool_events にエントリが追加されるべき"
        event = updated["tool_events"][0]
        assert "timestamp" in event
        assert event["tool_name"] == "Bash"


class TestAtomicWriteSafety:
    """アトミック書き込みの安全性テスト（責務3）"""

    def test_atomic_write_safety(self, hook_runner, project_root):
        """lam-loop-state.json への追記がアトミックに行われる"""
        # lam-loop-state.json を事前に作成
        loop_state_path = project_root / ".claude" / "lam-loop-state.json"
        initial_state = {"iteration": 1, "tool_events": []}
        loop_state_path.write_text(
            json.dumps(initial_state, ensure_ascii=False),
            encoding="utf-8",
        )

        # 複数回実行してアトミック書き込みが正常に動作することを確認
        for i in range(3):
            input_json = {
                "tool_name": "Edit",
                "tool_input": {"file_path": f"src/file{i}.py", "old_string": "a", "new_string": "b"},
                "tool_response": {"exitCode": 0, "stdout": ""},
            }
            result = hook_runner(HOOK_PATH, input_json)
            assert result.returncode == 0

        # JSON が壊れていないことを確認
        content = loop_state_path.read_text(encoding="utf-8")
        data = json.loads(content)  # JSON パースが成功すれば OK
        assert "tool_events" in data
        assert len(data["tool_events"]) == 3
