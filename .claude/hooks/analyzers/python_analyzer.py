"""Task A-2: Python 言語 Analyzer

対応仕様: scalable-code-review-spec.md FR-1, FR-2
対応設計: scalable-code-review-design.md Section 2.2 Python
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

from analyzers.base import ASTNode, Issue, LanguageAnalyzer, ToolRequirement

_SEVERITY_MAP = {
    "HIGH": "critical",
    "MEDIUM": "warning",
    "LOW": "info",
}


class PythonAnalyzer(LanguageAnalyzer):
    """Python プロジェクト用の静的解析プラグイン。

    設計書 Section 2.2 Python に対応。
    lint に ruff、セキュリティスキャンに bandit、
    AST 解析に Python 標準 ast モジュールを使用する。
    """

    def detect(self, project_root: Path) -> bool:
        """pyproject.toml または *.py ファイルが存在すれば True を返す。"""
        if (project_root / "pyproject.toml").exists():
            return True
        return any(project_root.rglob("*.py"))

    def required_tools(self) -> list[ToolRequirement]:
        """ruff と bandit の ToolRequirement を返す。"""
        return [
            ToolRequirement(command="ruff", install_hint="pip install ruff"),
            ToolRequirement(command="bandit", install_hint="pip install bandit"),
        ]

    def run_lint(self, target: Path) -> list[Issue]:
        """ruff check を実行して Issue リストに変換して返す。"""
        result = subprocess.run(
            ["ruff", "check", "--output-format", "json", str(target)],
            capture_output=True,
            text=True,
            check=False,
        )
        try:
            raw_issues = json.loads(result.stdout)
        except json.JSONDecodeError:
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return []

        issues: list[Issue] = []
        for item in raw_issues:
            filename = item.get("filename", "")
            try:
                file_rel = str(Path(filename).relative_to(target))
            except ValueError:
                file_rel = filename

            fix = item.get("fix")
            suggestion = "Auto-fixable" if fix is not None else ""

            issues.append(Issue(
                file=file_rel,
                line=item["location"]["row"],
                severity="warning",
                category="lint",
                tool="ruff",
                message=item["message"],
                rule_id=item["code"],
                suggestion=suggestion,
            ))

        return issues

    def run_security(self, target: Path) -> list[Issue]:
        """bandit を実行して Issue リストに変換して返す。"""
        result = subprocess.run(
            ["bandit", "-r", "-f", "json", str(target)],
            capture_output=True,
            text=True,
            check=False,
        )
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return []

        issues: list[Issue] = []
        for item in data.get("results", []):
            filename = item.get("filename", "")
            try:
                file_rel = str(Path(filename).relative_to(target))
            except ValueError:
                file_rel = filename

            raw_severity = item.get("issue_severity", "LOW").upper()
            severity = _SEVERITY_MAP.get(raw_severity, "info")

            issues.append(Issue(
                file=file_rel,
                line=item["line_number"],
                severity=severity,
                category="security",
                tool="bandit",
                message=item["issue_text"],
                rule_id=item["test_id"],
                suggestion="",
            ))

        return issues

    def parse_ast(self, file_path: Path) -> ASTNode:
        """Python 標準 ast モジュールを使用して ASTNode ツリーを構築する。"""
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))

        lines = source.splitlines()
        end_line = len(lines) if lines else 1

        children = [
            self._visit_top_level(node)
            for node in ast.iter_child_nodes(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        ]

        return ASTNode(
            name=file_path.stem,
            kind="module",
            start_line=1,
            end_line=max(end_line, 1),
            signature="",
            children=children,
            docstring=ast.get_docstring(tree),
        )

    def _visit_top_level(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
    ) -> ASTNode:
        """トップレベルの関数またはクラスを ASTNode に変換する。"""
        if isinstance(node, ast.ClassDef):
            return self._build_class_node(node)
        return self._build_function_node(node, kind="function")

    def _build_function_node(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        kind: str = "function",
    ) -> ASTNode:
        """FunctionDef / AsyncFunctionDef を ASTNode に変換する。"""
        return ASTNode(
            name=node.name,
            kind=kind,
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            signature=self._build_signature(node),
            children=[],
            docstring=ast.get_docstring(node),
        )

    def _build_class_node(self, node: ast.ClassDef) -> ASTNode:
        """ClassDef を ASTNode に変換し、メソッドを children として追加する。"""
        methods = [
            self._build_function_node(child, kind="method")
            for child in ast.iter_child_nodes(node)
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        return ASTNode(
            name=node.name,
            kind="class",
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            signature=f"class {node.name}:",
            children=methods,
            docstring=ast.get_docstring(node),
        )

    def _build_signature(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> str:
        """関数ノードから 'def name(args)' 形式のシグネチャを構築する。"""
        args = node.args
        arg_names: list[str] = []

        for arg in args.args:
            arg_names.append(arg.arg)
        if args.vararg:
            arg_names.append(f"*{args.vararg.arg}")
        for arg in args.kwonlyargs:
            arg_names.append(arg.arg)
        if args.kwarg:
            arg_names.append(f"**{args.kwarg.arg}")

        prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
        return f"{prefix} {node.name}({', '.join(arg_names)})"
