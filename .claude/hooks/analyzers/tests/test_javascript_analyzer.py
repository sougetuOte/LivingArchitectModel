"""Task A-3: JavaScriptAnalyzer のテスト

対応仕様: scalable-code-review-spec.md FR-1, FR-2
対応設計: scalable-code-review-design.md Section 2.2 JavaScript/TypeScript
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from analyzers.base import ASTNode, Issue, ToolRequirement
from analyzers.javascript_analyzer import JavaScriptAnalyzer


def _make_mock_result(stdout: str = "", stderr: str = "", returncode: int = 0) -> MagicMock:
    result = MagicMock()
    result.stdout = stdout
    result.stderr = stderr
    result.returncode = returncode
    return result


# ── detect ─────────────────────────────────────────────────


class TestDetect:
    """detect: package.json の有無でプロジェクト検出。"""

    def test_detect_returns_true_when_package_json_exists(self, tmp_path: Path) -> None:
        """package.json が存在する場合 True を返す。"""
        (tmp_path / "package.json").write_text("{}")
        analyzer = JavaScriptAnalyzer()
        assert analyzer.detect(tmp_path) is True

    def test_detect_returns_false_when_package_json_missing(self, tmp_path: Path) -> None:
        """package.json が存在しない場合 False を返す。"""
        analyzer = JavaScriptAnalyzer()
        assert analyzer.detect(tmp_path) is False


# ── required_tools ─────────────────────────────────────────


class TestRequiredTools:
    """required_tools: npx と npm の ToolRequirement を返す。"""

    def test_returns_two_tools(self) -> None:
        """npx と npm の 2 つを返すこと。"""
        analyzer = JavaScriptAnalyzer()
        tools = analyzer.required_tools()
        assert len(tools) == 2

    def test_contains_npx(self) -> None:
        """npx の ToolRequirement が含まれること。"""
        analyzer = JavaScriptAnalyzer()
        tools = analyzer.required_tools()
        commands = [t.command for t in tools]
        assert "npx" in commands

    def test_contains_npm(self) -> None:
        """npm の ToolRequirement が含まれること。"""
        analyzer = JavaScriptAnalyzer()
        tools = analyzer.required_tools()
        commands = [t.command for t in tools]
        assert "npm" in commands

    def test_all_are_tool_requirement_instances(self) -> None:
        """全要素が ToolRequirement のインスタンスであること。"""
        analyzer = JavaScriptAnalyzer()
        for tool in analyzer.required_tools():
            assert isinstance(tool, ToolRequirement)

    def test_install_hint_not_empty(self) -> None:
        """install_hint が空でないこと。"""
        analyzer = JavaScriptAnalyzer()
        for tool in analyzer.required_tools():
            assert tool.install_hint


# ── run_lint ───────────────────────────────────────────────


ESLINT_OUTPUT_SINGLE_ERROR = json.dumps([
    {
        "filePath": "/project/src/app.js",
        "messages": [
            {
                "ruleId": "no-unused-vars",
                "severity": 2,
                "message": "'x' is defined but never used.",
                "line": 3,
                "column": 7,
                "fix": {"range": [10, 20], "text": ""},
            }
        ],
        "errorCount": 1,
        "warningCount": 0,
    }
])

ESLINT_OUTPUT_WARNING = json.dumps([
    {
        "filePath": "/project/src/util.js",
        "messages": [
            {
                "ruleId": "no-console",
                "severity": 1,
                "message": "Unexpected console statement.",
                "line": 10,
                "column": 1,
            }
        ],
        "errorCount": 0,
        "warningCount": 1,
    }
])

ESLINT_OUTPUT_NULL_RULE = json.dumps([
    {
        "filePath": "/project/src/broken.js",
        "messages": [
            {
                "ruleId": None,
                "severity": 2,
                "message": "Parsing error: Unexpected token",
                "line": 1,
                "column": 1,
            }
        ],
        "errorCount": 1,
        "warningCount": 0,
    }
])


class TestRunLint:
    """run_lint: eslint JSON 出力を Issue リストに変換。"""

    def test_severity_2_maps_to_warning(self, tmp_path: Path) -> None:
        """eslint severity=2 は Issue.severity="warning" に変換される。"""
        with patch("subprocess.run", return_value=_make_mock_result(ESLINT_OUTPUT_SINGLE_ERROR, returncode=1)):
            analyzer = JavaScriptAnalyzer()
            issues = analyzer.run_lint(tmp_path)

        assert len(issues) == 1
        assert issues[0].severity == "warning"

    def test_severity_1_maps_to_info(self, tmp_path: Path) -> None:
        """eslint severity=1 は Issue.severity="info" に変換される。"""
        with patch("subprocess.run", return_value=_make_mock_result(ESLINT_OUTPUT_WARNING, returncode=1)):
            analyzer = JavaScriptAnalyzer()
            issues = analyzer.run_lint(tmp_path)

        assert len(issues) == 1
        assert issues[0].severity == "info"

    def test_category_is_lint(self, tmp_path: Path) -> None:
        """category は "lint" であること。"""
        with patch("subprocess.run", return_value=_make_mock_result(ESLINT_OUTPUT_SINGLE_ERROR, returncode=1)):
            analyzer = JavaScriptAnalyzer()
            issues = analyzer.run_lint(tmp_path)

        assert issues[0].category == "lint"

    def test_tool_is_eslint(self, tmp_path: Path) -> None:
        """tool は "eslint" であること。"""
        with patch("subprocess.run", return_value=_make_mock_result(ESLINT_OUTPUT_SINGLE_ERROR, returncode=1)):
            analyzer = JavaScriptAnalyzer()
            issues = analyzer.run_lint(tmp_path)

        assert issues[0].tool == "eslint"

    def test_rule_id_from_eslint(self, tmp_path: Path) -> None:
        """rule_id は eslint の ruleId から取得すること。"""
        with patch("subprocess.run", return_value=_make_mock_result(ESLINT_OUTPUT_SINGLE_ERROR, returncode=1)):
            analyzer = JavaScriptAnalyzer()
            issues = analyzer.run_lint(tmp_path)

        assert issues[0].rule_id == "no-unused-vars"

    def test_null_rule_id_becomes_parse_error(self, tmp_path: Path) -> None:
        """ruleId が null の場合 rule_id は "parse-error" になること。"""
        with patch("subprocess.run", return_value=_make_mock_result(ESLINT_OUTPUT_NULL_RULE, returncode=1)):
            analyzer = JavaScriptAnalyzer()
            issues = analyzer.run_lint(tmp_path)

        assert issues[0].rule_id == "parse-error"

    def test_fix_present_sets_suggestion(self, tmp_path: Path) -> None:
        """fix が存在する場合 suggestion は "Auto-fixable" であること。"""
        with patch("subprocess.run", return_value=_make_mock_result(ESLINT_OUTPUT_SINGLE_ERROR, returncode=1)):
            analyzer = JavaScriptAnalyzer()
            issues = analyzer.run_lint(tmp_path)

        assert issues[0].suggestion == "Auto-fixable"

    def test_no_fix_gives_empty_suggestion(self, tmp_path: Path) -> None:
        """fix がない場合 suggestion は空文字列であること。"""
        with patch("subprocess.run", return_value=_make_mock_result(ESLINT_OUTPUT_WARNING, returncode=1)):
            analyzer = JavaScriptAnalyzer()
            issues = analyzer.run_lint(tmp_path)

        assert issues[0].suggestion == ""

    def test_line_number_preserved(self, tmp_path: Path) -> None:
        """line 番号が保持されること。"""
        with patch("subprocess.run", return_value=_make_mock_result(ESLINT_OUTPUT_SINGLE_ERROR, returncode=1)):
            analyzer = JavaScriptAnalyzer()
            issues = analyzer.run_lint(tmp_path)

        assert issues[0].line == 3

    def test_returncode_other_than_0_or_1_returns_empty(self, tmp_path: Path) -> None:
        """returncode が 0 でも 1 でもない場合（eslint 実行失敗）は空リストを返す。"""
        with patch("subprocess.run", return_value=_make_mock_result("", returncode=2)):
            analyzer = JavaScriptAnalyzer()
            issues = analyzer.run_lint(tmp_path)

        assert issues == []

    def test_returncode_0_returns_empty_issues(self, tmp_path: Path) -> None:
        """eslint returncode=0 はエラーなし（空リスト）。"""
        stdout = json.dumps([
            {"filePath": "/project/src/app.js", "messages": [], "errorCount": 0, "warningCount": 0}
        ])
        with patch("subprocess.run", return_value=_make_mock_result(stdout, returncode=0)):
            analyzer = JavaScriptAnalyzer()
            issues = analyzer.run_lint(tmp_path)

        assert issues == []

    def test_file_path_is_relative(self, tmp_path: Path) -> None:
        """file は target に対する相対パスに変換されること。"""
        stdout = json.dumps([
            {
                "filePath": str(tmp_path / "src" / "app.js"),
                "messages": [
                    {
                        "ruleId": "no-unused-vars",
                        "severity": 2,
                        "message": "'x' is defined but never used.",
                        "line": 3,
                        "column": 7,
                    }
                ],
                "errorCount": 1,
                "warningCount": 0,
            }
        ])
        with patch("subprocess.run", return_value=_make_mock_result(stdout, returncode=1)):
            analyzer = JavaScriptAnalyzer()
            issues = analyzer.run_lint(tmp_path)

        assert issues[0].file == "src/app.js"

    def test_all_issues_are_issue_instances(self, tmp_path: Path) -> None:
        """返り値の全要素が Issue のインスタンスであること。"""
        with patch("subprocess.run", return_value=_make_mock_result(ESLINT_OUTPUT_SINGLE_ERROR, returncode=1)):
            analyzer = JavaScriptAnalyzer()
            issues = analyzer.run_lint(tmp_path)

        for issue in issues:
            assert isinstance(issue, Issue)


# ── run_security ───────────────────────────────────────────


NPM_AUDIT_OUTPUT = json.dumps({
    "vulnerabilities": {
        "lodash": {
            "name": "lodash",
            "severity": "high",
            "via": [{"title": "Prototype Pollution", "url": "https://example.com"}],
            "effects": [],
            "range": "<4.17.21",
            "fixAvailable": True,
        }
    }
})

NPM_AUDIT_MODERATE = json.dumps({
    "vulnerabilities": {
        "express": {
            "name": "express",
            "severity": "moderate",
            "via": [{"title": "ReDoS vulnerability", "url": "https://example.com"}],
            "effects": [],
            "range": "<4.18.0",
            "fixAvailable": False,
        }
    }
})

NPM_AUDIT_STRING_VIA = json.dumps({
    "vulnerabilities": {
        "semver": {
            "name": "semver",
            "severity": "low",
            "via": ["semver-vuln"],
            "effects": [],
            "range": "<7.5.2",
            "fixAvailable": False,
        }
    }
})

NPM_AUDIT_CRITICAL = json.dumps({
    "vulnerabilities": {
        "shelljs": {
            "name": "shelljs",
            "severity": "critical",
            "via": [{"title": "Command Injection", "url": "https://example.com"}],
            "effects": [],
            "range": "<0.8.5",
            "fixAvailable": True,
        }
    }
})


class TestRunSecurity:
    """run_security: npm audit JSON 出力を Issue リストに変換。"""

    def test_high_severity_maps_to_critical(self, tmp_path: Path) -> None:
        """severity="high" は Issue.severity="critical" に変換される。"""
        with patch("subprocess.run", return_value=_make_mock_result(NPM_AUDIT_OUTPUT, returncode=1)):
            analyzer = JavaScriptAnalyzer()
            issues = analyzer.run_security(tmp_path)

        assert len(issues) == 1
        assert issues[0].severity == "critical"

    def test_critical_severity_maps_to_critical(self, tmp_path: Path) -> None:
        """severity="critical" は Issue.severity="critical" に変換される。"""
        with patch("subprocess.run", return_value=_make_mock_result(NPM_AUDIT_CRITICAL, returncode=1)):
            analyzer = JavaScriptAnalyzer()
            issues = analyzer.run_security(tmp_path)

        assert issues[0].severity == "critical"

    def test_moderate_severity_maps_to_warning(self, tmp_path: Path) -> None:
        """severity="moderate" は Issue.severity="warning" に変換される。"""
        with patch("subprocess.run", return_value=_make_mock_result(NPM_AUDIT_MODERATE, returncode=1)):
            analyzer = JavaScriptAnalyzer()
            issues = analyzer.run_security(tmp_path)

        assert issues[0].severity == "warning"

    def test_low_severity_maps_to_info(self, tmp_path: Path) -> None:
        """severity="low" は Issue.severity="info" に変換される。"""
        with patch("subprocess.run", return_value=_make_mock_result(NPM_AUDIT_STRING_VIA, returncode=1)):
            analyzer = JavaScriptAnalyzer()
            issues = analyzer.run_security(tmp_path)

        assert issues[0].severity == "info"

    def test_category_is_security(self, tmp_path: Path) -> None:
        """category は "security" であること。"""
        with patch("subprocess.run", return_value=_make_mock_result(NPM_AUDIT_OUTPUT, returncode=1)):
            analyzer = JavaScriptAnalyzer()
            issues = analyzer.run_security(tmp_path)

        assert issues[0].category == "security"

    def test_tool_is_npm_audit(self, tmp_path: Path) -> None:
        """tool は "npm-audit" であること。"""
        with patch("subprocess.run", return_value=_make_mock_result(NPM_AUDIT_OUTPUT, returncode=1)):
            analyzer = JavaScriptAnalyzer()
            issues = analyzer.run_security(tmp_path)

        assert issues[0].tool == "npm-audit"

    def test_rule_id_is_package_name(self, tmp_path: Path) -> None:
        """rule_id はパッケージ名であること。"""
        with patch("subprocess.run", return_value=_make_mock_result(NPM_AUDIT_OUTPUT, returncode=1)):
            analyzer = JavaScriptAnalyzer()
            issues = analyzer.run_security(tmp_path)

        assert issues[0].rule_id == "lodash"

    def test_line_is_zero(self, tmp_path: Path) -> None:
        """line は 0 であること（パッケージレベルの問題）。"""
        with patch("subprocess.run", return_value=_make_mock_result(NPM_AUDIT_OUTPUT, returncode=1)):
            analyzer = JavaScriptAnalyzer()
            issues = analyzer.run_security(tmp_path)

        assert issues[0].line == 0

    def test_file_is_package_json(self, tmp_path: Path) -> None:
        """file は "package.json" であること。"""
        with patch("subprocess.run", return_value=_make_mock_result(NPM_AUDIT_OUTPUT, returncode=1)):
            analyzer = JavaScriptAnalyzer()
            issues = analyzer.run_security(tmp_path)

        assert issues[0].file == "package.json"

    def test_message_from_via_dict_title(self, tmp_path: Path) -> None:
        """via の最初の要素が辞書の場合 title を message に使用する。"""
        with patch("subprocess.run", return_value=_make_mock_result(NPM_AUDIT_OUTPUT, returncode=1)):
            analyzer = JavaScriptAnalyzer()
            issues = analyzer.run_security(tmp_path)

        assert issues[0].message == "Prototype Pollution"

    def test_message_from_via_string(self, tmp_path: Path) -> None:
        """via の最初の要素が文字列の場合はそのまま message に使用する。"""
        with patch("subprocess.run", return_value=_make_mock_result(NPM_AUDIT_STRING_VIA, returncode=1)):
            analyzer = JavaScriptAnalyzer()
            issues = analyzer.run_security(tmp_path)

        assert issues[0].message == "semver-vuln"

    def test_fix_available_true_sets_suggestion(self, tmp_path: Path) -> None:
        """fixAvailable=True の場合 suggestion は "Run npm audit fix" であること。"""
        with patch("subprocess.run", return_value=_make_mock_result(NPM_AUDIT_OUTPUT, returncode=1)):
            analyzer = JavaScriptAnalyzer()
            issues = analyzer.run_security(tmp_path)

        assert issues[0].suggestion == "Run npm audit fix"

    def test_fix_available_false_gives_empty_suggestion(self, tmp_path: Path) -> None:
        """fixAvailable=False の場合 suggestion は空文字列であること。"""
        with patch("subprocess.run", return_value=_make_mock_result(NPM_AUDIT_MODERATE, returncode=1)):
            analyzer = JavaScriptAnalyzer()
            issues = analyzer.run_security(tmp_path)

        assert issues[0].suggestion == ""

    def test_invalid_json_returns_empty(self, tmp_path: Path) -> None:
        """stdout が JSON でない場合は空リストを返す。"""
        with patch("subprocess.run", return_value=_make_mock_result("not json", returncode=1)):
            analyzer = JavaScriptAnalyzer()
            issues = analyzer.run_security(tmp_path)

        assert issues == []

    def test_npm_executed_in_target_directory(self, tmp_path: Path) -> None:
        """npm audit は target ディレクトリで実行されること。"""
        stdout = json.dumps({"vulnerabilities": {}})
        with patch("subprocess.run", return_value=_make_mock_result(stdout, returncode=0)) as mock_run:
            analyzer = JavaScriptAnalyzer()
            analyzer.run_security(tmp_path)

        assert mock_run.call_args.kwargs.get("cwd") == tmp_path

    def test_all_issues_are_issue_instances(self, tmp_path: Path) -> None:
        """返り値の全要素が Issue のインスタンスであること。"""
        with patch("subprocess.run", return_value=_make_mock_result(NPM_AUDIT_OUTPUT, returncode=1)):
            analyzer = JavaScriptAnalyzer()
            issues = analyzer.run_security(tmp_path)

        for issue in issues:
            assert isinstance(issue, Issue)


# ── parse_ast ──────────────────────────────────────────────


class TestParseAst:
    """parse_ast: Phase 1 簡易実装 — kind="module" のルートノードを返す。"""

    def test_returns_astnode(self, tmp_path: Path) -> None:
        """ASTNode のインスタンスを返すこと。"""
        js_file = tmp_path / "app.js"
        js_file.write_text("console.log('hello');\n")

        analyzer = JavaScriptAnalyzer()
        node = analyzer.parse_ast(js_file)

        assert isinstance(node, ASTNode)

    def test_kind_is_module(self, tmp_path: Path) -> None:
        """kind は "module" であること。"""
        js_file = tmp_path / "app.js"
        js_file.write_text("const x = 1;\n")

        analyzer = JavaScriptAnalyzer()
        node = analyzer.parse_ast(js_file)

        assert node.kind == "module"

    def test_name_is_filename_without_extension(self, tmp_path: Path) -> None:
        """name はファイル名（拡張子なし）であること。"""
        js_file = tmp_path / "my_module.js"
        js_file.write_text("export default {};\n")

        analyzer = JavaScriptAnalyzer()
        node = analyzer.parse_ast(js_file)

        assert node.name == "my_module"

    def test_start_line_is_1(self, tmp_path: Path) -> None:
        """start_line は 1 であること。"""
        js_file = tmp_path / "app.js"
        js_file.write_text("const x = 1;\n")

        analyzer = JavaScriptAnalyzer()
        node = analyzer.parse_ast(js_file)

        assert node.start_line == 1

    def test_end_line_is_file_line_count(self, tmp_path: Path) -> None:
        """end_line はファイルの行数であること。"""
        js_file = tmp_path / "app.js"
        content = "line1\nline2\nline3\n"
        js_file.write_text(content)

        analyzer = JavaScriptAnalyzer()
        node = analyzer.parse_ast(js_file)

        assert node.end_line == 3

    def test_children_is_empty_list(self, tmp_path: Path) -> None:
        """children は空リストであること（Phase 2 で tree-sitter に置換）。"""
        js_file = tmp_path / "app.js"
        js_file.write_text("function hello() { return 1; }\n")

        analyzer = JavaScriptAnalyzer()
        node = analyzer.parse_ast(js_file)

        assert node.children == []

    def test_signature_is_empty_string(self, tmp_path: Path) -> None:
        """signature は空文字列であること。"""
        js_file = tmp_path / "app.js"
        js_file.write_text("const x = 1;\n")

        analyzer = JavaScriptAnalyzer()
        node = analyzer.parse_ast(js_file)

        assert node.signature == ""

    def test_typescript_file(self, tmp_path: Path) -> None:
        """TypeScript ファイルも同様に処理できること。"""
        ts_file = tmp_path / "component.ts"
        ts_file.write_text("interface Foo { bar: string; }\n")

        analyzer = JavaScriptAnalyzer()
        node = analyzer.parse_ast(ts_file)

        assert node.name == "component"
        assert node.kind == "module"

    def test_multiline_file_end_line(self, tmp_path: Path) -> None:
        """複数行ファイルの end_line が正確であること。"""
        js_file = tmp_path / "large.js"
        lines = "\n".join(f"// line {i}" for i in range(1, 51))
        js_file.write_text(lines)

        analyzer = JavaScriptAnalyzer()
        node = analyzer.parse_ast(js_file)

        assert node.end_line == 50
