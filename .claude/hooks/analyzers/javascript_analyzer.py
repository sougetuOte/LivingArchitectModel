"""JavaScript/TypeScript 静的解析アナライザー

Task A-3: JavaScriptAnalyzer 実装
対応仕様: scalable-code-review-spec.md FR-1, FR-2
対応設計: scalable-code-review-design.md Section 2.2 JavaScript/TypeScript

Phase 1: 簡易実装（parse_ast は正規表現ベース）
Phase 2: tree-sitter による本格的な AST 解析に置換予定
"""
from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

from analyzers.base import ASTNode, Issue, LanguageAnalyzer, ToolRequirement

logger = logging.getLogger(__name__)

_SUBPROCESS_TIMEOUT = 300  # seconds (config.static_analysis_timeout_sec のデフォルト値)

_SEVERITY_ESLINT: dict[int, str] = {
    # ESLint: 2=error, 1=warning, 0=off
    # ESLint の error はコード品質問題であり、セキュリティの critical とは異なる。
    # ruff (Python) も E/F を "warning" にマッピングしており、それに合わせる。
    2: "warning",
    1: "info",
}

_SEVERITY_NPM_AUDIT: dict[str, str] = {
    "critical": "critical",
    "high": "critical",
    "moderate": "warning",
    "low": "info",
}


class JavaScriptAnalyzer(LanguageAnalyzer):
    """JavaScript/TypeScript プロジェクトの静的解析アナライザー。

    設計書 Section 2.2 に対応。
    - detect: package.json の存在で検出
    - run_lint: npx eslint --format json
    - run_security: npm audit --json
    - parse_ast: Phase 1 は簡易実装（kind="module" のルートノードのみ）

    language_name は "javascript" だが、TypeScript も包含する。
    """

    language_name = "javascript"

    def detect(self, project_root: Path) -> bool:
        """package.json が存在する場合 True を返す。"""
        return (project_root / "package.json").exists()

    def run_lint(self, target: Path) -> list[Issue]:
        """npx eslint を実行し、Issue リストを返す。

        eslint の returncode:
        - 0: lint エラーなし（正常）
        - 1: lint エラーあり（正常終了、stdout をパース）
        - その他: eslint 自体の実行失敗 → 空リストを返す
        """
        try:
            result = subprocess.run(
                ["npx", "eslint", "--format", "json", str(target)],
                capture_output=True,
                text=True,
                check=False,
                timeout=_SUBPROCESS_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            logger.warning("eslint timed out after %d seconds", _SUBPROCESS_TIMEOUT)
            return []

        if result.returncode not in (0, 1):
            return []

        try:
            data = json.loads(result.stdout)
        except (json.JSONDecodeError, ValueError):
            return []

        issues: list[Issue] = []
        for file_result in data:
            file_path = file_result.get("filePath", "")
            try:
                relative_file = str(Path(file_path).relative_to(target))
            except ValueError:
                relative_file = file_path

            for msg in file_result.get("messages", []):
                rule_id = msg.get("ruleId") or "parse-error"
                severity_code = msg.get("severity", 1)
                severity = _SEVERITY_ESLINT.get(severity_code, "info")
                suggestion = "Auto-fixable" if msg.get("fix") else ""

                issues.append(Issue(
                    file=relative_file,
                    line=msg.get("line", 0),
                    severity=severity,
                    category="lint",
                    tool="eslint",
                    message=msg.get("message", ""),
                    rule_id=rule_id,
                    suggestion=suggestion,
                ))

        return issues

    def run_security(self, target: Path) -> list[Issue]:
        """npm audit を実行し、Issue リストを返す。

        npm audit は脆弱性がある場合に returncode != 0 を返すが、
        stdout に JSON が出力される。パースを試みて失敗した場合のみ空リストを返す。
        target ディレクトリ（package.json の場所）で実行する。
        """
        cwd = target if target.is_dir() else target.parent
        try:
            result = subprocess.run(
                ["npm", "audit", "--json"],
                capture_output=True,
                text=True,
                check=False,
                cwd=cwd,
                timeout=_SUBPROCESS_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            logger.warning("npm audit timed out after %d seconds", _SUBPROCESS_TIMEOUT)
            return []

        try:
            data = json.loads(result.stdout)
        except (json.JSONDecodeError, ValueError):
            return []

        vulnerabilities = data.get("vulnerabilities", {})
        issues: list[Issue] = []

        for pkg_name, vuln in vulnerabilities.items():
            npm_severity = vuln.get("severity", "low")
            severity = _SEVERITY_NPM_AUDIT.get(npm_severity, "info")

            via = vuln.get("via", [])
            if via:
                first_via = via[0]
                if isinstance(first_via, dict):
                    message = first_via.get("title", "")
                else:
                    message = str(first_via)
            else:
                message = ""

            fix_available = vuln.get("fixAvailable", False)
            suggestion = "Run npm audit fix" if fix_available else ""

            issues.append(Issue(
                file="package.json",
                line=0,
                severity=severity,
                category="security",
                tool="npm-audit",
                message=message,
                rule_id=pkg_name,
                suggestion=suggestion,
            ))

        return issues

    def parse_ast(self, file_path: Path) -> ASTNode:
        """AST を構築して返す。

        Phase 1 簡易実装:
        - kind="module" のルートノードのみ返す
        - children は空リスト（Phase 2 で tree-sitter による解析に置換）
        - name はファイル名（拡張子なし）
        - signature は空文字列
        - start_line=1, end_line=ファイル行数
        """
        content = file_path.read_text(encoding="utf-8")
        line_count = len(content.splitlines())

        return ASTNode(
            name=file_path.stem,
            kind="module",
            start_line=1,
            end_line=line_count,
            signature="",
            children=[],
        )

    def required_tools(self) -> list[ToolRequirement]:
        """npx と npm の ToolRequirement を返す。"""
        return [
            ToolRequirement(
                command="npx",
                install_hint="Install Node.js: https://nodejs.org/",
            ),
            ToolRequirement(
                command="npm",
                install_hint="Install Node.js: https://nodejs.org/",
            ),
        ]
