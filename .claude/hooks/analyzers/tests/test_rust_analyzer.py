"""Task A-4: RustAnalyzer のテスト

対応仕様: scalable-code-review-spec.md FR-1, FR-2
対応設計: scalable-code-review-design.md Section 2.2 (Rust)
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from analyzers.base import ASTNode, Issue, ToolRequirement
from analyzers.rust_analyzer import RustAnalyzer


# ── detect ──────────────────────────────────────────────────


class TestDetect:
    """detect() のテスト。"""

    def test_detect_returns_true_when_cargo_toml_exists(self, tmp_path: Path) -> None:
        """Cargo.toml が存在するとき True を返すこと。"""
        (tmp_path / "Cargo.toml").write_text("[package]\nname = \"myapp\"\n")
        analyzer = RustAnalyzer()
        assert analyzer.detect(tmp_path) is True

    def test_detect_returns_false_when_cargo_toml_missing(self, tmp_path: Path) -> None:
        """Cargo.toml が存在しないとき False を返すこと。"""
        analyzer = RustAnalyzer()
        assert analyzer.detect(tmp_path) is False


# ── run_lint（cargo clippy） ────────────────────────────────


class TestRunLint:
    """run_lint() のテスト。cargo clippy JSON Lines 出力を扱う。"""

    def _make_clippy_line(
        self,
        *,
        level: str = "warning",
        code: str | None = "clippy::needless_return",
        msg: str = "unneeded `return` statement",
        file_name: str = "src/main.rs",
        line_start: int = 5,
        rendered: str = "warning: unneeded `return` statement\nhelp: remove this `return`",
    ) -> str:
        """compiler-message 形式の JSON 文字列を生成するヘルパー。"""
        span = {
            "file_name": file_name,
            "line_start": line_start,
            "line_end": line_start,
            "column_start": 1,
            "column_end": 10,
        }
        entry = {
            "reason": "compiler-message",
            "message": {
                "code": {"code": code} if code is not None else None,
                "level": level,
                "message": msg,
                "spans": [span],
                "rendered": rendered,
            },
        }
        return json.dumps(entry)

    def test_run_lint_returns_issue_list(self, tmp_path: Path) -> None:
        """clippy の出力から Issue リストを返すこと。"""
        line = self._make_clippy_line()
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = line + "\n"

        with patch("subprocess.run", return_value=mock_result):
            analyzer = RustAnalyzer()
            issues = analyzer.run_lint(tmp_path)

        assert len(issues) == 1
        issue = issues[0]
        assert isinstance(issue, Issue)

    def test_run_lint_severity_mapping_warning(self, tmp_path: Path) -> None:
        """clippy の level=warning は severity=warning にマップされること。"""
        line = self._make_clippy_line(level="warning")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = line + "\n"

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_lint(tmp_path)

        assert issues[0].severity == "warning"

    def test_run_lint_severity_mapping_error(self, tmp_path: Path) -> None:
        """clippy の level=error は severity=critical にマップされること。"""
        line = self._make_clippy_line(level="error")
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = line + "\n"

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_lint(tmp_path)

        assert issues[0].severity == "critical"

    def test_run_lint_severity_mapping_other(self, tmp_path: Path) -> None:
        """clippy の level=note など他の level は severity=info にマップされること。"""
        line = self._make_clippy_line(level="note")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = line + "\n"

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_lint(tmp_path)

        assert issues[0].severity == "info"

    def test_run_lint_category_is_lint(self, tmp_path: Path) -> None:
        """category は常に lint であること。"""
        line = self._make_clippy_line()
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = line + "\n"

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_lint(tmp_path)

        assert issues[0].category == "lint"

    def test_run_lint_tool_is_clippy(self, tmp_path: Path) -> None:
        """tool は clippy であること。"""
        line = self._make_clippy_line()
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = line + "\n"

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_lint(tmp_path)

        assert issues[0].tool == "clippy"

    def test_run_lint_rule_id_from_code(self, tmp_path: Path) -> None:
        """rule_id は message.code.code から取得されること。"""
        line = self._make_clippy_line(code="clippy::needless_return")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = line + "\n"

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_lint(tmp_path)

        assert issues[0].rule_id == "clippy::needless_return"

    def test_run_lint_rule_id_unknown_when_code_null(self, tmp_path: Path) -> None:
        """message.code が null のとき rule_id は unknown であること。"""
        line = self._make_clippy_line(code=None)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = line + "\n"

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_lint(tmp_path)

        assert issues[0].rule_id == "unknown"

    def test_run_lint_line_from_spans(self, tmp_path: Path) -> None:
        """line は spans[0].line_start から取得されること。"""
        line = self._make_clippy_line(line_start=42)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = line + "\n"

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_lint(tmp_path)

        assert issues[0].line == 42

    def test_run_lint_line_zero_when_spans_empty(self, tmp_path: Path) -> None:
        """spans が空のとき line は 0 であること。"""
        entry = {
            "reason": "compiler-message",
            "message": {
                "code": {"code": "clippy::test"},
                "level": "warning",
                "message": "test message",
                "spans": [],
                "rendered": "warning: test",
            },
        }
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(entry) + "\n"

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_lint(tmp_path)

        assert issues[0].line == 0

    def test_run_lint_file_from_spans(self, tmp_path: Path) -> None:
        """file は spans[0].file_name から取得されること。"""
        line = self._make_clippy_line(file_name="src/lib.rs")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = line + "\n"

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_lint(tmp_path)

        assert issues[0].file == "src/lib.rs"

    def test_run_lint_message_content(self, tmp_path: Path) -> None:
        """message は message.message の内容であること。"""
        line = self._make_clippy_line(msg="unneeded `return` statement")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = line + "\n"

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_lint(tmp_path)

        assert issues[0].message == "unneeded `return` statement"

    def test_run_lint_suggestion_from_help_in_rendered(self, tmp_path: Path) -> None:
        """rendered に help: が含まれる場合、suggestion に help 行を抽出すること。"""
        rendered = "warning: unneeded `return`\nhelp: remove this `return`\n  --> src/main.rs:5"
        line = self._make_clippy_line(rendered=rendered)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = line + "\n"

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_lint(tmp_path)

        assert "help:" in issues[0].suggestion

    def test_run_lint_suggestion_empty_when_no_help(self, tmp_path: Path) -> None:
        """rendered に help: がない場合、suggestion は空文字列であること。"""
        rendered = "warning: unneeded `return`\n  --> src/main.rs:5"
        line = self._make_clippy_line(rendered=rendered)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = line + "\n"

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_lint(tmp_path)

        assert issues[0].suggestion == ""

    def test_run_lint_ignores_non_compiler_message_lines(self, tmp_path: Path) -> None:
        """reason が compiler-message 以外の行は無視されること。"""
        artifact_line = json.dumps({"reason": "compiler-artifact", "package_id": "foo"})
        msg_line = self._make_clippy_line()
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = artifact_line + "\n" + msg_line + "\n"

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_lint(tmp_path)

        assert len(issues) == 1

    def test_run_lint_multiple_issues(self, tmp_path: Path) -> None:
        """複数の compiler-message を複数の Issue に変換すること。"""
        line1 = self._make_clippy_line(msg="issue one", line_start=10)
        line2 = self._make_clippy_line(msg="issue two", line_start=20)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = line1 + "\n" + line2 + "\n"

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_lint(tmp_path)

        assert len(issues) == 2
        assert issues[0].line == 10
        assert issues[1].line == 20

    def test_run_lint_returns_empty_on_parse_failure(self, tmp_path: Path) -> None:
        """JSON パース失敗（不正な出力）でも空リストを返し例外を出さないこと。"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "this is not json\n"

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_lint(tmp_path)

        assert issues == []

    def test_run_lint_subprocess_called_with_correct_args(self, tmp_path: Path) -> None:
        """cargo clippy が正しい引数で呼ばれること。"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            RustAnalyzer().run_lint(tmp_path)

        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert cmd[0] == "cargo"
        assert "clippy" in cmd
        assert "--message-format" in cmd
        assert "json" in cmd

    def test_run_lint_cwd_is_target(self, tmp_path: Path) -> None:
        """cargo clippy は target ディレクトリを cwd として実行されること。"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            RustAnalyzer().run_lint(tmp_path)

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get("cwd") == tmp_path


# ── run_security（cargo audit） ─────────────────────────────


class TestRunSecurity:
    """run_security() のテスト。cargo audit JSON 出力を扱う。"""

    def _make_audit_output(
        self,
        *,
        vuln_id: str = "RUSTSEC-2021-0145",
        title: str = "Potential segfault in the time crate",
        package: str = "time",
        severity: str = "HIGH",
        patched: list[str] | None = None,
    ) -> str:
        """cargo audit の JSON 出力を生成するヘルパー。"""
        if patched is None:
            patched = [">=0.3.36"]
        vuln = {
            "advisory": {
                "id": vuln_id,
                "title": title,
                "package": package,
                "severity": severity,
            },
            "versions": {
                "patched": patched,
            },
        }
        return json.dumps({
            "vulnerabilities": {
                "found": True,
                "count": 1,
                "list": [vuln],
            }
        })

    def test_run_security_returns_issue_list(self, tmp_path: Path) -> None:
        """cargo audit の出力から Issue リストを返すこと。"""
        mock_result = MagicMock()
        mock_result.returncode = 1  # 脆弱性あり = 正常終了
        mock_result.stdout = self._make_audit_output()

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_security(tmp_path)

        assert len(issues) == 1
        assert isinstance(issues[0], Issue)

    def test_run_security_severity_high_to_critical(self, tmp_path: Path) -> None:
        """severity HIGH は critical にマップされること。"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = self._make_audit_output(severity="HIGH")

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_security(tmp_path)

        assert issues[0].severity == "critical"

    def test_run_security_severity_critical_to_critical(self, tmp_path: Path) -> None:
        """severity CRITICAL は critical にマップされること。"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = self._make_audit_output(severity="CRITICAL")

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_security(tmp_path)

        assert issues[0].severity == "critical"

    def test_run_security_severity_medium_to_warning(self, tmp_path: Path) -> None:
        """severity MEDIUM は warning にマップされること。"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = self._make_audit_output(severity="MEDIUM")

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_security(tmp_path)

        assert issues[0].severity == "warning"

    def test_run_security_severity_low_to_info(self, tmp_path: Path) -> None:
        """severity LOW は info にマップされること。"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = self._make_audit_output(severity="LOW")

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_security(tmp_path)

        assert issues[0].severity == "info"

    def test_run_security_severity_unknown_to_warning(self, tmp_path: Path) -> None:
        """未指定の severity は warning にマップされること。"""
        output = json.dumps({
            "vulnerabilities": {
                "found": True,
                "count": 1,
                "list": [{
                    "advisory": {
                        "id": "RUSTSEC-2021-0001",
                        "title": "Test vuln",
                        "package": "test",
                    },
                    "versions": {"patched": []},
                }],
            }
        })
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = output

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_security(tmp_path)

        assert issues[0].severity == "warning"

    def test_run_security_category_is_security(self, tmp_path: Path) -> None:
        """category は security であること。"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = self._make_audit_output()

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_security(tmp_path)

        assert issues[0].category == "security"

    def test_run_security_tool_is_cargo_audit(self, tmp_path: Path) -> None:
        """tool は cargo-audit であること。"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = self._make_audit_output()

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_security(tmp_path)

        assert issues[0].tool == "cargo-audit"

    def test_run_security_rule_id_from_advisory_id(self, tmp_path: Path) -> None:
        """rule_id は advisory.id であること。"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = self._make_audit_output(vuln_id="RUSTSEC-2021-0145")

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_security(tmp_path)

        assert issues[0].rule_id == "RUSTSEC-2021-0145"

    def test_run_security_line_is_zero(self, tmp_path: Path) -> None:
        """line は 0（パッケージレベル）であること。"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = self._make_audit_output()

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_security(tmp_path)

        assert issues[0].line == 0

    def test_run_security_file_is_cargo_toml(self, tmp_path: Path) -> None:
        """file は Cargo.toml であること。"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = self._make_audit_output()

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_security(tmp_path)

        assert issues[0].file == "Cargo.toml"

    def test_run_security_message_from_advisory_title(self, tmp_path: Path) -> None:
        """message は advisory.title であること。"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = self._make_audit_output(title="Potential segfault in the time crate")

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_security(tmp_path)

        assert issues[0].message == "Potential segfault in the time crate"

    def test_run_security_suggestion_with_patched_versions(self, tmp_path: Path) -> None:
        """patched バージョンがある場合、suggestion に Update to が含まれること。"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = self._make_audit_output(patched=[">=0.3.36"])

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_security(tmp_path)

        assert "Update to:" in issues[0].suggestion
        assert ">=0.3.36" in issues[0].suggestion

    def test_run_security_suggestion_empty_when_no_patched(self, tmp_path: Path) -> None:
        """patched が空のとき suggestion は空文字列であること。"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = self._make_audit_output(patched=[])

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_security(tmp_path)

        assert issues[0].suggestion == ""

    def test_run_security_no_vulns_returns_empty(self, tmp_path: Path) -> None:
        """脆弱性なしの場合は空リストを返すこと。"""
        output = json.dumps({
            "vulnerabilities": {"found": False, "count": 0, "list": []}
        })
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = output

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_security(tmp_path)

        assert issues == []

    def test_run_security_returns_empty_on_parse_failure(self, tmp_path: Path) -> None:
        """JSON パース失敗時は空リストを返し例外を出さないこと。"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "not valid json"

        with patch("subprocess.run", return_value=mock_result):
            issues = RustAnalyzer().run_security(tmp_path)

        assert issues == []

    def test_run_security_subprocess_called_with_correct_args(self, tmp_path: Path) -> None:
        """cargo audit が正しい引数で呼ばれること。"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"vulnerabilities": {"found": False, "count": 0, "list": []}})

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            RustAnalyzer().run_security(tmp_path)

        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "cargo"
        assert "audit" in cmd
        assert "--json" in cmd

    def test_run_security_cwd_is_target(self, tmp_path: Path) -> None:
        """cargo audit は target ディレクトリを cwd として実行されること。"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"vulnerabilities": {"found": False, "count": 0, "list": []}})

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            RustAnalyzer().run_security(tmp_path)

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get("cwd") == tmp_path


# ── parse_ast（Phase 1 簡易実装） ───────────────────────────


class TestParseAst:
    """parse_ast() のテスト。Phase 1 では簡易実装。"""

    def test_parse_ast_returns_module_node(self, tmp_path: Path) -> None:
        """kind=module のルートノードを返すこと。"""
        rs_file = tmp_path / "main.rs"
        rs_file.write_text("fn main() {\n    println!(\"hello\");\n}\n")
        analyzer = RustAnalyzer()
        node = analyzer.parse_ast(rs_file)
        assert node.kind == "module"

    def test_parse_ast_name_is_stem(self, tmp_path: Path) -> None:
        """name はファイル名（拡張子なし）であること。"""
        rs_file = tmp_path / "lib.rs"
        rs_file.write_text("pub fn add(a: i32, b: i32) -> i32 { a + b }\n")
        node = RustAnalyzer().parse_ast(rs_file)
        assert node.name == "lib"

    def test_parse_ast_children_is_empty(self, tmp_path: Path) -> None:
        """children は空リストであること（Phase 1）。"""
        rs_file = tmp_path / "main.rs"
        rs_file.write_text("fn main() {}\n")
        node = RustAnalyzer().parse_ast(rs_file)
        assert node.children == []

    def test_parse_ast_start_line_is_one(self, tmp_path: Path) -> None:
        """start_line は 1 であること。"""
        rs_file = tmp_path / "main.rs"
        rs_file.write_text("fn main() {}\n")
        node = RustAnalyzer().parse_ast(rs_file)
        assert node.start_line == 1

    def test_parse_ast_end_line_is_file_line_count(self, tmp_path: Path) -> None:
        """end_line はファイルの行数であること。"""
        rs_file = tmp_path / "main.rs"
        content = "fn main() {\n    println!(\"hello\");\n}\n"
        rs_file.write_text(content)
        line_count = len(content.splitlines())
        node = RustAnalyzer().parse_ast(rs_file)
        assert node.end_line == line_count

    def test_parse_ast_signature_is_empty(self, tmp_path: Path) -> None:
        """signature は空文字列であること（Phase 1）。"""
        rs_file = tmp_path / "main.rs"
        rs_file.write_text("fn main() {}\n")
        node = RustAnalyzer().parse_ast(rs_file)
        assert node.signature == ""

    def test_parse_ast_returns_astnode_type(self, tmp_path: Path) -> None:
        """戻り値の型が ASTNode であること。"""
        rs_file = tmp_path / "foo.rs"
        rs_file.write_text("// empty\n")
        node = RustAnalyzer().parse_ast(rs_file)
        assert isinstance(node, ASTNode)


# ── required_tools ─────────────────────────────────────────


class TestRequiredTools:
    """required_tools() のテスト。"""

    def test_required_tools_returns_cargo_only(self) -> None:
        """cargo のみ返すこと。

        cargo-audit は cargo のサブコマンドであり shutil.which では
        検出できないため、required_tools には含めない。
        cargo audit のインストール確認は run_security() 内で行う。
        """
        tools = RustAnalyzer().required_tools()
        assert len(tools) == 1
        assert tools[0].command == "cargo"

    def test_required_tools_cargo_install_hint(self) -> None:
        """cargo の install_hint に rustup.rs が含まれること。"""
        tools = RustAnalyzer().required_tools()
        assert "rustup.rs" in tools[0].install_hint

    def test_required_tools_returns_tool_requirement_instances(self) -> None:
        """各要素が ToolRequirement のインスタンスであること。"""
        tools = RustAnalyzer().required_tools()
        for tool in tools:
            assert isinstance(tool, ToolRequirement)
