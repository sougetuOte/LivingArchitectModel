"""Task A-1a: 基盤データモデルのテスト

対応仕様: scalable-code-review-spec.md FR-1, FR-2
対応設計: scalable-code-review-design.md Section 2.1, 2.1c, 2.3
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from analyzers.base import ASTNode, Issue, LanguageAnalyzer


# ── Issue データモデル ──────────────────────────────────────


class TestIssue:
    """Issue データモデルのテスト。設計書 Section 2.3 に対応。"""

    def test_instantiation(self) -> None:
        """全フィールドを指定して Issue を生成できること。"""
        issue = Issue(
            file="src/main.py",
            line=42,
            severity="warning",
            category="lint",
            tool="ruff",
            message="Line too long",
            rule_id="E501",
            suggestion="Split the line",
        )
        assert issue.file == "src/main.py"
        assert issue.line == 42
        assert issue.severity == "warning"
        assert issue.category == "lint"
        assert issue.tool == "ruff"
        assert issue.message == "Line too long"
        assert issue.rule_id == "E501"
        assert issue.suggestion == "Split the line"

    def test_serialization_to_dict(self) -> None:
        """asdict() で辞書に変換できること。"""
        issue = Issue(
            file="src/app.py",
            line=10,
            severity="critical",
            category="security",
            tool="bandit",
            message="Hardcoded password",
            rule_id="B105",
            suggestion="Use environment variable",
        )
        d = asdict(issue)
        assert d["file"] == "src/app.py"
        assert d["severity"] == "critical"
        assert d["tool"] == "bandit"

    def test_serialization_to_json(self) -> None:
        """JSON にシリアライズ可能であること。"""
        issue = Issue(
            file="src/util.py",
            line=1,
            severity="info",
            category="lint",
            tool="ruff",
            message="Unused import",
            rule_id="F401",
            suggestion="Remove import",
        )
        json_str = json.dumps(asdict(issue))
        restored = json.loads(json_str)
        assert restored["rule_id"] == "F401"

    @pytest.mark.parametrize("sev", ("critical", "warning", "info"))
    def test_severity_values(self, sev: str) -> None:
        """severity は critical / warning / info のいずれかであること。"""
        issue = Issue(
            file="x.py", line=1, severity=sev,
            category="lint", tool="t", message="m",
            rule_id="R1", suggestion="",
        )
        assert issue.severity == sev

    @pytest.mark.parametrize("cat", ("lint", "security", "type", "dead-code"))
    def test_category_values(self, cat: str) -> None:
        """category は lint / security / type / dead-code のいずれかであること。"""
        issue = Issue(
            file="x.py", line=1, severity="info",
            category=cat, tool="t", message="m",
            rule_id="R1", suggestion="",
        )
        assert issue.category == cat


# ── ASTNode ラッパー型 ─────────────────────────────────────


class TestASTNode:
    """ASTNode ラッパー型のテスト。設計書 Section 2.1c に対応。"""

    def test_instantiation(self) -> None:
        """全フィールドを指定して ASTNode を生成できること。"""
        node = ASTNode(
            name="my_func",
            kind="function",
            start_line=10,
            end_line=20,
            signature="def my_func(x: int) -> str",
            children=[],
            docstring="A sample function.",
        )
        assert node.name == "my_func"
        assert node.kind == "function"
        assert node.start_line == 10
        assert node.end_line == 20
        assert node.signature == "def my_func(x: int) -> str"
        assert node.children == []
        assert node.docstring == "A sample function."

    def test_docstring_default_none(self) -> None:
        """docstring はデフォルトで None であること。"""
        node = ASTNode(
            name="Cls",
            kind="class",
            start_line=1,
            end_line=50,
            signature="class Cls:",
            children=[],
        )
        assert node.docstring is None

    def test_nested_children(self) -> None:
        """children に ASTNode をネストできること。"""
        child = ASTNode(
            name="method_a",
            kind="method",
            start_line=5,
            end_line=10,
            signature="def method_a(self) -> None",
            children=[],
        )
        parent = ASTNode(
            name="MyClass",
            kind="class",
            start_line=1,
            end_line=20,
            signature="class MyClass:",
            children=[child],
        )
        assert len(parent.children) == 1
        assert parent.children[0].name == "method_a"
        assert parent.children[0].kind == "method"

    def test_serialization_to_dict(self) -> None:
        """asdict() で辞書に再帰的に変換できること。"""
        child = ASTNode(
            name="inner",
            kind="function",
            start_line=3,
            end_line=8,
            signature="def inner()",
            children=[],
        )
        parent = ASTNode(
            name="outer",
            kind="module",
            start_line=1,
            end_line=10,
            signature="",
            children=[child],
        )
        d = asdict(parent)
        assert d["name"] == "outer"
        assert len(d["children"]) == 1
        assert d["children"][0]["name"] == "inner"

    def test_serialization_to_json(self) -> None:
        """JSON にシリアライズ可能であること（ネスト含む）。"""
        node = ASTNode(
            name="f",
            kind="function",
            start_line=1,
            end_line=5,
            signature="def f()",
            children=[],
        )
        json_str = json.dumps(asdict(node))
        restored = json.loads(json_str)
        assert restored["kind"] == "function"

    def test_kind_values(self) -> None:
        """kind は function / class / module / method のいずれかであること。"""
        for kind in ("function", "class", "module", "method"):
            node = ASTNode(
                name="x", kind=kind,
                start_line=1, end_line=2,
                signature="", children=[],
            )
            assert node.kind == kind


# ── LanguageAnalyzer ABC ───────────────────────────────────


class TestLanguageAnalyzer:
    """LanguageAnalyzer ABC のテスト。設計書 Section 2.1 に対応。"""

    def test_cannot_instantiate_directly(self) -> None:
        """ABC を直接インスタンス化できないこと。"""
        with pytest.raises(TypeError):
            LanguageAnalyzer()  # type: ignore[abstract]

    def test_subclass_must_implement_abstract_methods(self) -> None:
        """抽象メソッドを実装しないサブクラスはインスタンス化できないこと。"""

        class IncompleteAnalyzer(LanguageAnalyzer):
            def detect(self, project_root: Path) -> bool:
                return True
            # run_lint, run_security, parse_ast が未実装

        with pytest.raises(TypeError):
            IncompleteAnalyzer()  # type: ignore[abstract]

    def test_complete_subclass_can_instantiate(self) -> None:
        """全抽象メソッドを実装したサブクラスはインスタンス化できること。"""

        class CompleteAnalyzer(LanguageAnalyzer):
            def detect(self, project_root: Path) -> bool:
                return True

            def run_lint(self, target: Path) -> list[Issue]:
                return []

            def run_security(self, target: Path) -> list[Issue]:
                return []

            def parse_ast(self, file_path: Path) -> ASTNode:
                return ASTNode(
                    name="mod", kind="module",
                    start_line=1, end_line=1,
                    signature="", children=[],
                )

        analyzer = CompleteAnalyzer()
        assert analyzer.detect(Path("/tmp"))

    def test_run_type_check_default_returns_empty(self) -> None:
        """run_type_check() のデフォルト実装は空リストを返すこと。"""

        class MinimalAnalyzer(LanguageAnalyzer):
            def detect(self, project_root: Path) -> bool:
                return False

            def run_lint(self, target: Path) -> list[Issue]:
                return []

            def run_security(self, target: Path) -> list[Issue]:
                return []

            def parse_ast(self, file_path: Path) -> ASTNode:
                return ASTNode(
                    name="m", kind="module",
                    start_line=1, end_line=1,
                    signature="", children=[],
                )

        analyzer = MinimalAnalyzer()
        result = analyzer.run_type_check(Path("/tmp"))
        assert result == []

    def test_abstract_methods_exist(self) -> None:
        """detect, run_lint, run_security, parse_ast が抽象メソッドであること。"""
        abstract_methods = LanguageAnalyzer.__abstractmethods__
        assert "detect" in abstract_methods
        assert "run_lint" in abstract_methods
        assert "run_security" in abstract_methods
        assert "parse_ast" in abstract_methods

    def test_run_type_check_is_not_abstract(self) -> None:
        """run_type_check は抽象メソッドではないこと（オプショナル）。"""
        assert "run_type_check" not in LanguageAnalyzer.__abstractmethods__
