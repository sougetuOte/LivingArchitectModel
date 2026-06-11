"""
test_post_tool_use.py - post-tool-use.py の TDD テスト

対応仕様:
  - docs/design/hooks-python-migration-design.md H2（post-tool-use）
  - docs/specs/tdd-introspection-v2.md Section 4（JUnit XML 方式）
"""
import json
from pathlib import Path

# テスト対象フックのパス
HOOK_PATH = Path(__file__).resolve().parent.parent / "post-tool-use.py"

# JUnit XML テンプレート
_JUNIT_PASS = """\
<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" tests="{tests}" failures="0" errors="0">
{testcases}
</testsuite>
"""

_JUNIT_FAIL = """\
<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" tests="{tests}" failures="{failures}" errors="0">
{testcases}
</testsuite>
"""


def _write_junit_xml(project_root: Path, tests: int, failures: int = 0,
                     failed_names: list[str] | None = None) -> None:
    """テスト用の JUnit XML 結果ファイルを生成する。"""
    xml_path = project_root / ".claude" / "test-results.xml"
    testcases = []
    for i in range(tests):
        name = f"test_{i}"
        if failed_names and i < len(failed_names):
            name = failed_names[i]
        if i < failures:
            testcases.append(
                f'  <testcase name="{name}"><failure message="assert failed"/></testcase>'
            )
        else:
            testcases.append(f'  <testcase name="{name}"/>')
    tc_str = "\n".join(testcases)
    if failures > 0:
        content = _JUNIT_FAIL.format(tests=tests, failures=failures, testcases=tc_str)
    else:
        content = _JUNIT_PASS.format(tests=tests, testcases=tc_str)
    xml_path.write_text(content, encoding="utf-8")


class TestTDDPatternDetection:
    """TDD パターン検出テスト（責務1: JUnit XML 方式）"""

    def test_pytest_fail_recorded(self, hook_runner, project_root):
        """pytest 失敗 + JUnit XML あり → tdd-patterns.log に FAIL 記録"""
        _write_junit_xml(project_root, tests=5, failures=2,
                         failed_names=["test_bar", "test_baz"])
        input_json = {
            "tool_name": "Bash",
            "tool_input": {"command": "pytest tests/ -v"},
            "tool_response": {"stdout": "2 failed, 3 passed", "stderr": ""},
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0

        tdd_log = project_root / ".claude" / "tdd-patterns.log"
        assert tdd_log.exists(), "tdd-patterns.log が作成されるべき"
        content = tdd_log.read_text(encoding="utf-8")
        assert "FAIL" in content
        assert "pytest" in content
        assert "failures=2" in content

    def test_pytest_pass_after_fail(self, hook_runner, project_root):
        """失敗後成功 → PASS 記録 + systemMessage 出力"""
        # まず失敗を記録
        _write_junit_xml(project_root, tests=5, failures=1,
                         failed_names=["test_bar"])
        fail_input = {
            "tool_name": "Bash",
            "tool_input": {"command": "pytest tests/ -v"},
            "tool_response": {"stdout": "1 failed", "stderr": ""},
        }
        hook_runner(HOOK_PATH, fail_input)

        # 次に成功を記録
        _write_junit_xml(project_root, tests=5, failures=0)
        pass_input = {
            "tool_name": "Bash",
            "tool_input": {"command": "pytest tests/ -v"},
            "tool_response": {"stdout": "5 passed", "stderr": ""},
        }
        result = hook_runner(HOOK_PATH, pass_input)
        assert result.returncode == 0

        tdd_log = project_root / ".claude" / "tdd-patterns.log"
        assert tdd_log.exists()
        content = tdd_log.read_text(encoding="utf-8")
        assert "PASS" in content, "失敗→成功パターンが PASS として記録されるべき"

        # 通知A: systemMessage が出力される（仕様必須）
        stdout = result.stdout.strip()
        assert stdout, "FAIL→PASS 遷移時は systemMessage が出力されるべき"
        data = json.loads(stdout)
        assert "systemMessage" in data
        assert "/retro" in data["systemMessage"]

    def test_non_integer_xml_attribute_returns_none(self, tmp_path):
        """数値属性が非整数（tests="abc"）でも raise せず None を返す（iter2 W2-2）。

        _parse_junit_xml の docstring 契約は「パース失敗時 None」。
        非整数属性は ValueError で main() の広域 except に吸収されていたが、
        契約どおり関数自身が None を返すべき。
        """
        import importlib.util

        xml_path = tmp_path / "test-results.xml"
        xml_path.write_text(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<testsuite name="pytest" tests="abc" failures="0" errors="0">\n'
            '  <testcase name="test_a"/>\n'
            "</testsuite>\n",
            encoding="utf-8",
        )
        spec = importlib.util.spec_from_file_location("post_tool_use", HOOK_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module._parse_junit_xml(xml_path) is None

    def test_testsuites_root_aggregates_multiple_suites(self, tmp_path):
        """<testsuites> ルート（Jest/Maven 等の複数スイート形式）で
        tests/failures/errors が全スイート合算される（iter4 W4-7）。"""
        import importlib.util

        xml_path = tmp_path / "test-results.xml"
        xml_path.write_text(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            "<testsuites>\n"
            '  <testsuite name="suite1" tests="3" failures="1" errors="0">\n'
            '    <testcase name="test_a"><failure message="boom"/></testcase>\n'
            '    <testcase name="test_b"/>\n'
            '    <testcase name="test_c"/>\n'
            "  </testsuite>\n"
            '  <testsuite name="suite2" tests="2" failures="0" errors="1">\n'
            '    <testcase name="test_d"/>\n'
            '    <testcase name="test_e"><error message="crash"/></testcase>\n'
            "  </testsuite>\n"
            "</testsuites>\n",
            encoding="utf-8",
        )
        spec = importlib.util.spec_from_file_location("post_tool_use", HOOK_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module._parse_junit_xml(xml_path)

        assert result is not None
        assert result["tests"] == 5, "全スイートの tests が合算されるべき"
        assert result["failures"] == 2, "failures + errors が全スイート合算されるべき"
        assert result["failed_names"] == ["test_a", "test_e"]

    def test_no_junit_xml_warns(self, hook_runner, project_root):
        """JUnit XML なし → WARN ログのみ、tdd-patterns.log には FAIL/PASS 記録なし"""
        input_json = {
            "tool_name": "Bash",
            "tool_input": {"command": "pytest tests/ -v"},
            "tool_response": {"stdout": "5 passed", "stderr": ""},
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0

        tdd_log = project_root / ".claude" / "tdd-patterns.log"
        # JUnit XML なし時は tdd-patterns.log が作成されてはいけない
        assert not tdd_log.exists(), "JUnit XML なし時は tdd-patterns.log が作成されないべき"

    def test_npm_test_fail_recorded(self, hook_runner, project_root):
        """npm test 失敗 + JUnit XML → FAIL 記録"""
        _write_junit_xml(project_root, tests=10, failures=3,
                         failed_names=["should render", "should validate", "should submit"])
        input_json = {
            "tool_name": "Bash",
            "tool_input": {"command": "npm test"},
            "tool_response": {"stdout": "3 failed", "stderr": ""},
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0

        tdd_log = project_root / ".claude" / "tdd-patterns.log"
        assert tdd_log.exists()
        content = tdd_log.read_text(encoding="utf-8")
        assert "FAIL" in content
        assert "npm test" in content

    def test_go_test_fail_recorded(self, hook_runner, project_root):
        """go test 失敗 + JUnit XML → FAIL 記録"""
        _write_junit_xml(project_root, tests=8, failures=2,
                         failed_names=["TestAdd", "TestSub"])
        input_json = {
            "tool_name": "Bash",
            "tool_input": {"command": "go test ./..."},
            "tool_response": {"stdout": "FAIL", "stderr": ""},
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0

        tdd_log = project_root / ".claude" / "tdd-patterns.log"
        assert tdd_log.exists()
        content = tdd_log.read_text(encoding="utf-8")
        assert "FAIL" in content
        assert "go test" in content

    def test_non_test_command_no_record(self, hook_runner, project_root):
        """テスト以外のコマンド（ls）→ 記録なし"""
        input_json = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls -la"},
            "tool_response": {"stdout": "total 8", "stderr": ""},
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0

        tdd_log = project_root / ".claude" / "tdd-patterns.log"
        assert not tdd_log.exists(), "非テストコマンドで tdd-patterns.log が作成されてはいけない"

    def test_pass_without_prior_fail_no_pattern(self, hook_runner, project_root):
        """前回失敗なしでの成功 → PASS パターン記録なし"""
        _write_junit_xml(project_root, tests=5, failures=0)
        input_json = {
            "tool_name": "Bash",
            "tool_input": {"command": "pytest tests/ -v"},
            "tool_response": {"stdout": "5 passed", "stderr": ""},
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0
        assert result.stdout.strip() == "", "前回失敗なしでは systemMessage 不要"

        tdd_log = project_root / ".claude" / "tdd-patterns.log"
        assert not tdd_log.exists(), "前回失敗なしでの成功時は tdd-patterns.log が作成されてはいけない"


class TestPostToolUseFailure:
    """PostToolUseFailure イベント分岐テスト（監査 B4）。

    ツール実行自体が非ゼロ exit で失敗したイベント。古い XML による誤判定を防ぐため、
    XML を読まず直接 FAIL を記録する（post-tool-use.py: is_failure_event 分岐）。
    """

    def _failure_input(self, command: str) -> dict:
        return {
            "hook_event_name": "PostToolUseFailure",
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "tool_response": {"stdout": "", "stderr": "error"},
        }

    def test_failure_event_records_fail_directly(self, hook_runner, project_root):
        """PostToolUseFailure + テストコマンド → XML 無しでも直接 FAIL 記録。"""
        result = hook_runner(HOOK_PATH, self._failure_input("pytest tests/ -v"))
        assert result.returncode == 0

        tdd_log = project_root / ".claude" / "tdd-patterns.log"
        assert tdd_log.exists(), "PostToolUseFailure 時に tdd-patterns.log が作成されるべき"
        content = tdd_log.read_text(encoding="utf-8")
        assert "FAIL" in content
        assert "PostToolUseFailure event" in content, (
            "失敗イベント由来であることがマーカーで記録されるべき"
        )

        last_result = project_root / ".claude" / "last-test-result"
        assert last_result.read_text(encoding="utf-8").startswith("fail")

    def test_failure_event_ignores_stale_pass_xml(self, hook_runner, project_root):
        """古い PASS XML が残っていても PostToolUseFailure は FAIL を記録（XML 不読）。"""
        # 直前実行の PASS XML を残置
        _write_junit_xml(project_root, tests=5, failures=0)

        result = hook_runner(HOOK_PATH, self._failure_input("pytest tests/ -v"))
        assert result.returncode == 0

        tdd_log = project_root / ".claude" / "tdd-patterns.log"
        content = tdd_log.read_text(encoding="utf-8")
        assert "FAIL" in content, "古い PASS XML に惑わされず FAIL を記録すべき"
        assert "PASS" not in content

    def test_failure_event_non_test_command_no_record(self, hook_runner, project_root):
        """PostToolUseFailure でもテストコマンドでなければ記録しない（ls 失敗等）。"""
        result = hook_runner(HOOK_PATH, self._failure_input("ls -la"))
        assert result.returncode == 0

        tdd_log = project_root / ".claude" / "tdd-patterns.log"
        assert not tdd_log.exists(), "非テストコマンドの失敗では記録されないべき"


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
        assert not doc_sync_flag.exists() or "docs/readme.md" not in doc_sync_flag.read_text(encoding="utf-8")


class TestLoopLog:
    """ループログテスト（責務3）"""

    def test_loop_state_tool_events(self, hook_runner, project_root):
        """lam-loop-state.json 存在時 → tool_events に追記"""
        loop_state_path = project_root / ".claude" / "lam-loop-state.json"
        initial_state = {"iteration": 1, "tool_events": []}
        loop_state_path.write_text(
            json.dumps(initial_state, ensure_ascii=False),
            encoding="utf-8",
        )

        input_json = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls -la"},
            "tool_response": {"stdout": "total 8", "stderr": ""},
        }
        result = hook_runner(HOOK_PATH, input_json)
        assert result.returncode == 0

        updated = json.loads(loop_state_path.read_text(encoding="utf-8"))
        assert "tool_events" in updated
        assert len(updated["tool_events"]) > 0
        event = updated["tool_events"][0]
        assert "timestamp" in event
        assert event["tool_name"] == "Bash"


class TestAtomicWriteSafety:
    """アトミック書き込みの安全性テスト（責務3）"""

    def test_atomic_write_safety(self, hook_runner, project_root):
        """lam-loop-state.json への追記がアトミックに行われる"""
        loop_state_path = project_root / ".claude" / "lam-loop-state.json"
        initial_state = {"iteration": 1, "tool_events": []}
        loop_state_path.write_text(
            json.dumps(initial_state, ensure_ascii=False),
            encoding="utf-8",
        )

        for i in range(3):
            input_json = {
                "tool_name": "Edit",
                "tool_input": {"file_path": f"src/file{i}.py", "old_string": "a", "new_string": "b"},
            }
            result = hook_runner(HOOK_PATH, input_json)
            assert result.returncode == 0

        content = loop_state_path.read_text(encoding="utf-8")
        data = json.loads(content)
        assert "tool_events" in data
        assert len(data["tool_events"]) == 3

    def test_max_tool_events_truncation(self, tmp_path):
        """tool_events が _MAX_TOOL_EVENTS(500) 件超過時、古いイベントを切り捨てる（W6-2）。

        ちょうど _MAX_TOOL_EVENTS(500) 件のイベントを持つ lam-loop-state.json を作成し
        _handle_loop_log を1回呼ぶと、append→切り捨てにより 501件→500件になる。
        つまり最古の1件（cmd_0）が消え、末尾に新イベントが追記されて計 500 件のまま。
        importlib 方式で直接呼び出す（test_non_integer_xml_attribute_returns_none と同型）。
        """
        import importlib.util

        spec = importlib.util.spec_from_file_location("post_tool_use", HOOK_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        max_events = module._MAX_TOOL_EVENTS  # 500

        # ちょうど max_events 件のイベントを持つ loop state を作成
        # 追加後 max_events + 1 件 → 切り捨てで後ろ max_events 件を保持
        initial_events = [
            {"timestamp": "2026-01-01T00:00:00Z", "tool_name": "Bash",
             "command": f"cmd_{i}", "file_path": "", "exit_code": ""}
            for i in range(max_events)
        ]
        loop_state_path = tmp_path / "lam-loop-state.json"
        loop_state_path.write_text(
            json.dumps({"iteration": 1, "tool_events": initial_events}),
            encoding="utf-8",
        )
        log_file = tmp_path / "post-tool-use.log"

        # 1 件追加呼び出し（501件 → 切り捨て後 500件）
        module._handle_loop_log(
            "Edit", "new_cmd", "src/new.py", "", loop_state_path, "2026-06-11T00:00:00Z", log_file
        )

        updated = json.loads(loop_state_path.read_text(encoding="utf-8"))
        events = updated["tool_events"]

        # 件数は max_events のまま（切り捨てで上限を維持）
        assert len(events) == max_events, (
            f"切り捨て後は {max_events} 件のままのはず、実際: {len(events)}"
        )
        # 最古の1件（cmd_0）が消えていること
        assert events[0]["command"] == "cmd_1", (
            f"最古イベントが切り捨てられるべき、実際の先頭: {events[0]['command']}"
        )
        # 末尾に新イベントが追記されていること
        assert events[-1]["command"] == "new_cmd", (
            f"新イベントが末尾に追記されるべき、実際の末尾: {events[-1]}"
        )
        assert events[-1]["tool_name"] == "Edit"
