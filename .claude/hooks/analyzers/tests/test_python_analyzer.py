"""Task A-2: PythonAnalyzer のテスト

TDD Red フェーズ: 実装前に全テストを定義する。

対応仕様: scalable-code-review-spec.md FR-1, FR-2
対応設計: scalable-code-review-design.md Section 2.2 Python
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch


from analyzers.base import ToolRequirement
from analyzers.python_analyzer import PythonAnalyzer


def _make_mock_result(stdout: str = "", stderr: str = "", returncode: int = 0) -> MagicMock:
    result = MagicMock()
    result.stdout = stdout
    result.stderr = stderr
    result.returncode = returncode
    return result


# ── detect ──────────────────────────────────────────────────


class TestDetect:
    """detect() が Python プロジェクトを正しく検出する。"""

    def test_detects_pyproject_toml(self, tmp_path: Path) -> None:
        """pyproject.toml が存在すれば True を返す。"""
        (tmp_path / "pyproject.toml").write_text("[tool.poetry]\n")
        analyzer = PythonAnalyzer()
        assert analyzer.detect(tmp_path) is True

    def test_detects_py_file(self, tmp_path: Path) -> None:
        """*.py ファイルが存在すれば True を返す。"""
        (tmp_path / "main.py").write_text("print('hello')\n")
        analyzer = PythonAnalyzer()
        assert analyzer.detect(tmp_path) is True

    def test_detects_nested_py_file(self, tmp_path: Path) -> None:
        """サブディレクトリに *.py ファイルがあれば True を返す。"""
        sub = tmp_path / "src" / "pkg"
        sub.mkdir(parents=True)
        (sub / "module.py").write_text("x = 1\n")
        analyzer = PythonAnalyzer()
        assert analyzer.detect(tmp_path) is True

    def test_returns_false_when_no_python(self, tmp_path: Path) -> None:
        """Python 関連ファイルが存在しなければ False を返す。"""
        (tmp_path / "index.js").write_text("console.log('hi');\n")
        analyzer = PythonAnalyzer()
        assert analyzer.detect(tmp_path) is False

    def test_returns_false_for_empty_directory(self, tmp_path: Path) -> None:
        """空のディレクトリでは False を返す。"""
        analyzer = PythonAnalyzer()
        assert analyzer.detect(tmp_path) is False


# ── required_tools ──────────────────────────────────────────


class TestRequiredTools:
    """required_tools() が正しいツール要件を返す。"""

    def test_returns_two_tools(self) -> None:
        """ruff と bandit の 2 つを返す。"""
        tools = PythonAnalyzer().required_tools()
        assert len(tools) == 2

    def test_ruff_tool(self) -> None:
        """ruff の command と install_hint が正しい。"""
        tools = PythonAnalyzer().required_tools()
        ruff = next(t for t in tools if t.command == "ruff")
        assert isinstance(ruff, ToolRequirement)
        assert ruff.install_hint == "pip install ruff"

    def test_bandit_tool(self) -> None:
        """bandit の command と install_hint が正しい。"""
        tools = PythonAnalyzer().required_tools()
        bandit = next(t for t in tools if t.command == "bandit")
        assert isinstance(bandit, ToolRequirement)
        assert bandit.install_hint == "pip install bandit"


# ── run_lint ────────────────────────────────────────────────


class TestRunLint:
    """run_lint() が ruff の JSON 出力を Issue リストに変換する。"""

    RUFF_OUTPUT = json.dumps([
        {
            "cell": None,
            "code": "F401",
            "end_location": {"column": 10, "row": 1},
            "filename": "/project/src/main.py",
            "fix": {"applicability": "safe", "edits": []},
            "location": {"column": 1, "row": 1},
            "message": "os imported but unused",
            "noqa_row": 1,
            "url": "https://docs.astral.sh/ruff/rules/unused-import",
        },
        {
            "cell": None,
            "code": "E501",
            "end_location": {"column": 120, "row": 10},
            "filename": "/project/src/main.py",
            "fix": None,
            "location": {"column": 1, "row": 10},
            "message": "Line too long (120 > 88)",
            "noqa_row": 10,
            "url": "https://docs.astral.sh/ruff/rules/line-too-long",
        },
    ])

    def test_returns_issue_list(self, tmp_path: Path) -> None:
        """ruff の出力を Issue リストに変換して返す。"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_mock_result(self.RUFF_OUTPUT)
            issues = PythonAnalyzer().run_lint(tmp_path)
        assert len(issues) == 2

    def test_issue_fields_from_ruff(self, tmp_path: Path) -> None:
        """各フィールドが ruff 出力から正しくマッピングされる。"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_mock_result(self.RUFF_OUTPUT)
            issues = PythonAnalyzer().run_lint(tmp_path)
        issue = issues[0]
        assert issue.rule_id == "F401"
        assert issue.line == 1
        assert issue.message == "os imported but unused"
        assert issue.severity == "warning"
        assert issue.category == "lint"
        assert issue.tool == "ruff"

    def test_fix_present_means_auto_fixable(self, tmp_path: Path) -> None:
        """fix フィールドが存在すれば suggestion が 'Auto-fixable'。"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_mock_result(self.RUFF_OUTPUT)
            issues = PythonAnalyzer().run_lint(tmp_path)
        # issues[0] は fix あり
        assert issues[0].suggestion == "Auto-fixable"

    def test_fix_none_means_empty_suggestion(self, tmp_path: Path) -> None:
        """fix フィールドが None なら suggestion が空文字列。"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_mock_result(self.RUFF_OUTPUT)
            issues = PythonAnalyzer().run_lint(tmp_path)
        # issues[1] は fix なし
        assert issues[1].suggestion == ""

    def test_file_is_relative_to_target(self, tmp_path: Path) -> None:
        """file フィールドは target からの相対パスになる。"""
        ruff_output = json.dumps([{
            "cell": None,
            "code": "F401",
            "end_location": {"column": 5, "row": 1},
            "filename": str(tmp_path / "src" / "main.py"),
            "fix": None,
            "location": {"column": 1, "row": 1},
            "message": "unused import",
            "noqa_row": 1,
            "url": "",
        }])
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_mock_result(ruff_output)
            issues = PythonAnalyzer().run_lint(tmp_path)
        assert issues[0].file == "src/main.py"

    def test_subprocess_called_with_correct_args(self, tmp_path: Path) -> None:
        """subprocess.run が正しい引数で呼ばれる。"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_mock_result("[]")
            PythonAnalyzer().run_lint(tmp_path)
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert cmd[0] == "ruff"
        assert "check" in cmd
        assert "--output-format" in cmd
        assert "json" in cmd
        assert str(tmp_path) in cmd

    def test_returns_empty_on_invalid_json_output(self, tmp_path: Path) -> None:
        """ruff の出力が不正な JSON の場合は空リストを返す。"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_mock_result("not json", returncode=1)
            issues = PythonAnalyzer().run_lint(tmp_path)
        assert issues == []

    def test_returns_empty_on_empty_json_array(self, tmp_path: Path) -> None:
        """ruff の出力が空配列なら空リストを返す。"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_mock_result("[]")
            issues = PythonAnalyzer().run_lint(tmp_path)
        assert issues == []


# ── run_security ────────────────────────────────────────────


class TestRunSecurity:
    """run_security() が bandit の JSON 出力を Issue リストに変換する。"""

    BANDIT_OUTPUT = json.dumps({
        "results": [
            {
                "code": "password = 'secret'",
                "filename": "/project/src/config.py",
                "issue_confidence": "HIGH",
                "issue_severity": "HIGH",
                "issue_text": "Possible hardcoded password",
                "line_number": 5,
                "line_range": [5],
                "test_id": "B105",
                "test_name": "hardcoded_password_string",
            },
            {
                "code": "import subprocess",
                "filename": "/project/src/runner.py",
                "issue_confidence": "MEDIUM",
                "issue_severity": "MEDIUM",
                "issue_text": "Consider possible security implications",
                "line_number": 10,
                "line_range": [10],
                "test_id": "B404",
                "test_name": "blacklist",
            },
            {
                "code": "x = eval(s)",
                "filename": "/project/src/eval.py",
                "issue_confidence": "LOW",
                "issue_severity": "LOW",
                "issue_text": "Use of eval",
                "line_number": 3,
                "line_range": [3],
                "test_id": "B307",
                "test_name": "blacklist",
            },
        ]
    })

    def test_returns_issue_list(self, tmp_path: Path) -> None:
        """bandit の出力を Issue リストに変換して返す。"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_mock_result(self.BANDIT_OUTPUT)
            issues = PythonAnalyzer().run_security(tmp_path)
        assert len(issues) == 3

    def test_severity_high_maps_to_critical(self, tmp_path: Path) -> None:
        """HIGH severity は 'critical' にマッピングされる。"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_mock_result(self.BANDIT_OUTPUT)
            issues = PythonAnalyzer().run_security(tmp_path)
        high_issue = next(i for i in issues if i.rule_id == "B105")
        assert high_issue.severity == "critical"

    def test_severity_medium_maps_to_warning(self, tmp_path: Path) -> None:
        """MEDIUM severity は 'warning' にマッピングされる。"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_mock_result(self.BANDIT_OUTPUT)
            issues = PythonAnalyzer().run_security(tmp_path)
        medium_issue = next(i for i in issues if i.rule_id == "B404")
        assert medium_issue.severity == "warning"

    def test_severity_low_maps_to_info(self, tmp_path: Path) -> None:
        """LOW severity は 'info' にマッピングされる。"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_mock_result(self.BANDIT_OUTPUT)
            issues = PythonAnalyzer().run_security(tmp_path)
        low_issue = next(i for i in issues if i.rule_id == "B307")
        assert low_issue.severity == "info"

    def test_issue_fields(self, tmp_path: Path) -> None:
        """各フィールドが bandit 出力から正しくマッピングされる。"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_mock_result(self.BANDIT_OUTPUT)
            issues = PythonAnalyzer().run_security(tmp_path)
        issue = next(i for i in issues if i.rule_id == "B105")
        assert issue.line == 5
        assert issue.message == "Possible hardcoded password"
        assert issue.category == "security"
        assert issue.tool == "bandit"
        assert issue.suggestion == ""

    def test_file_is_relative_to_target(self, tmp_path: Path) -> None:
        """file フィールドは target からの相対パスになる。"""
        bandit_output = json.dumps({
            "results": [{
                "code": "x",
                "filename": str(tmp_path / "src" / "config.py"),
                "issue_confidence": "HIGH",
                "issue_severity": "HIGH",
                "issue_text": "Hardcoded password",
                "line_number": 5,
                "line_range": [5],
                "test_id": "B105",
                "test_name": "hardcoded_password_string",
            }]
        })
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_mock_result(bandit_output)
            issues = PythonAnalyzer().run_security(tmp_path)
        assert issues[0].file == "src/config.py"

    def test_subprocess_called_with_correct_args(self, tmp_path: Path) -> None:
        """subprocess.run が正しい引数で呼ばれる。"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_mock_result('{"results": []}')
            PythonAnalyzer().run_security(tmp_path)
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert cmd[0] == "bandit"
        assert "-r" in cmd
        assert "-f" in cmd
        assert "json" in cmd
        assert str(tmp_path) in cmd

    def test_returns_empty_on_parse_failure(self, tmp_path: Path) -> None:
        """JSON 解析失敗時は空リストを返す。"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_mock_result("not json", returncode=1)
            issues = PythonAnalyzer().run_security(tmp_path)
        assert issues == []

    def test_returns_empty_on_no_results(self, tmp_path: Path) -> None:
        """results が空なら空リストを返す。"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_mock_result('{"results": []}')
            issues = PythonAnalyzer().run_security(tmp_path)
        assert issues == []

    def test_bandit_b105_detects_hardcoded_password(self, tmp_path: Path) -> None:
        """bandit B105 がハードコードパスワードを検出すること（FR-7e）。"""
        bandit_output = json.dumps({
            "results": [{
                "code": "password = 'my_secret_password_123'",
                "filename": str(tmp_path / "src" / "config.py"),
                "issue_confidence": "MEDIUM",
                "issue_severity": "HIGH",
                "issue_text": "Possible hardcoded password: 'my_secret_password_123'",
                "line_number": 3,
                "line_range": [3],
                "test_id": "B105",
                "test_name": "hardcoded_password_string",
            }]
        })
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_mock_result(bandit_output)
            issues = PythonAnalyzer().run_security(tmp_path)
        b105 = [i for i in issues if i.rule_id == "B105"]
        assert len(b105) >= 1, "B105 が検出されるべき"
        assert b105[0].severity == "critical"  # HIGH → critical
        assert b105[0].category == "security"


# ── parse_ast ────────────────────────────────────────────────


class TestParseAst:
    """parse_ast() が Python ファイルを ASTNode ツリーに変換する。"""

    def test_module_root_node(self, tmp_path: Path) -> None:
        """ルートノードは kind='module' で返される。"""
        py_file = tmp_path / "mod.py"
        py_file.write_text("x = 1\n")
        node = PythonAnalyzer().parse_ast(py_file)
        assert node.kind == "module"
        assert node.name == "mod"

    def test_top_level_function(self, tmp_path: Path) -> None:
        """トップレベル関数は kind='function' の子ノードになる。"""
        py_file = tmp_path / "func.py"
        py_file.write_text(
            "def greet(name: str) -> str:\n"
            "    return f'Hello {name}'\n"
        )
        node = PythonAnalyzer().parse_ast(py_file)
        assert len(node.children) == 1
        func = node.children[0]
        assert func.kind == "function"
        assert func.name == "greet"

    def test_function_signature(self, tmp_path: Path) -> None:
        """関数シグネチャが 'def name(args)' 形式で構築される。"""
        py_file = tmp_path / "sig.py"
        py_file.write_text(
            "def add(x: int, y: int) -> int:\n"
            "    return x + y\n"
        )
        node = PythonAnalyzer().parse_ast(py_file)
        func = node.children[0]
        assert func.signature.startswith("def add(")
        assert "x" in func.signature
        assert "y" in func.signature

    def test_function_with_docstring(self, tmp_path: Path) -> None:
        """ドキュメント文字列が docstring フィールドに設定される。"""
        py_file = tmp_path / "doc.py"
        py_file.write_text(
            'def documented():\n'
            '    """This is a docstring."""\n'
            '    pass\n'
        )
        node = PythonAnalyzer().parse_ast(py_file)
        func = node.children[0]
        assert func.docstring == "This is a docstring."

    def test_function_without_docstring(self, tmp_path: Path) -> None:
        """ドキュメント文字列なし関数の docstring は None。"""
        py_file = tmp_path / "nodoc.py"
        py_file.write_text(
            "def no_doc():\n"
            "    pass\n"
        )
        node = PythonAnalyzer().parse_ast(py_file)
        func = node.children[0]
        assert func.docstring is None

    def test_top_level_class(self, tmp_path: Path) -> None:
        """トップレベルクラスは kind='class' の子ノードになる。"""
        py_file = tmp_path / "cls.py"
        py_file.write_text(
            "class MyClass:\n"
            "    pass\n"
        )
        node = PythonAnalyzer().parse_ast(py_file)
        assert len(node.children) == 1
        cls_node = node.children[0]
        assert cls_node.kind == "class"
        assert cls_node.name == "MyClass"

    def test_class_with_methods(self, tmp_path: Path) -> None:
        """クラスのメソッドは children に kind='method' として追加される。"""
        py_file = tmp_path / "methods.py"
        py_file.write_text(
            "class Calculator:\n"
            "    def add(self, a: int, b: int) -> int:\n"
            "        return a + b\n"
            "    def subtract(self, a: int, b: int) -> int:\n"
            "        return a - b\n"
        )
        node = PythonAnalyzer().parse_ast(py_file)
        cls_node = node.children[0]
        assert cls_node.kind == "class"
        assert len(cls_node.children) == 2
        method_names = {c.name for c in cls_node.children}
        assert method_names == {"add", "subtract"}
        for child in cls_node.children:
            assert child.kind == "method"

    def test_async_function(self, tmp_path: Path) -> None:
        """async def は kind='function' として解析される。"""
        py_file = tmp_path / "async_func.py"
        py_file.write_text(
            "async def fetch(url: str) -> str:\n"
            "    pass\n"
        )
        node = PythonAnalyzer().parse_ast(py_file)
        assert len(node.children) == 1
        func = node.children[0]
        assert func.kind == "function"
        assert func.name == "fetch"

    def test_start_and_end_lines(self, tmp_path: Path) -> None:
        """start_line と end_line が正しく設定される。"""
        py_file = tmp_path / "lines.py"
        py_file.write_text(
            "def first():\n"     # line 1
            "    pass\n"         # line 2
            "\n"                 # line 3
            "def second():\n"    # line 4
            "    pass\n"         # line 5
        )
        node = PythonAnalyzer().parse_ast(py_file)
        first = next(c for c in node.children if c.name == "first")
        second = next(c for c in node.children if c.name == "second")
        assert first.start_line == 1
        assert second.start_line == 4

    def test_multiple_top_level_items(self, tmp_path: Path) -> None:
        """複数のトップレベル定義が全て children に含まれる。"""
        py_file = tmp_path / "multi.py"
        py_file.write_text(
            "class A:\n"
            "    pass\n"
            "\n"
            "def b():\n"
            "    pass\n"
            "\n"
            "class C:\n"
            "    pass\n"
        )
        node = PythonAnalyzer().parse_ast(py_file)
        assert len(node.children) == 3
        kinds = {c.kind for c in node.children}
        assert "class" in kinds
        assert "function" in kinds

    def test_empty_file(self, tmp_path: Path) -> None:
        """空ファイルはモジュールノード（子なし）として解析される。"""
        py_file = tmp_path / "empty.py"
        py_file.write_text("")
        node = PythonAnalyzer().parse_ast(py_file)
        assert node.kind == "module"
        assert node.children == []

    def test_module_node_lines(self, tmp_path: Path) -> None:
        """モジュールノードの start_line=1, end_line はファイル行数以上。"""
        py_file = tmp_path / "lines_mod.py"
        py_file.write_text("x = 1\ny = 2\n")
        node = PythonAnalyzer().parse_ast(py_file)
        assert node.start_line == 1
        assert node.end_line >= 2
