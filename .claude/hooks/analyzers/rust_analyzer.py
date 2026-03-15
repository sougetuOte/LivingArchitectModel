"""RustAnalyzer: Rust プロジェクトの静的解析プラグイン

Task A-4: RustAnalyzer 実装

対応仕様: scalable-code-review-spec.md FR-1, FR-2
対応設計: scalable-code-review-design.md Section 2.2 (Rust)
"""
from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

from analyzers.base import ASTNode, Issue, LanguageAnalyzer, ToolRequirement

logger = logging.getLogger(__name__)

_SUBPROCESS_TIMEOUT = 300  # seconds (config.static_analysis_timeout_sec のデフォルト値)


class RustAnalyzer(LanguageAnalyzer):
    """Rust プロジェクト向け静的解析プラグイン。

    cargo clippy で lint を、cargo audit でセキュリティスキャンを実行する。
    AST 解析は Phase 1 では簡易実装（kind=module のルートノードのみ）。
    """

    language_name = "rust"

    def detect(self, project_root: Path) -> bool:
        """Cargo.toml が存在するとき True を返す。"""
        return (project_root / "Cargo.toml").exists()

    def run_lint(self, target: Path) -> list[Issue]:
        """cargo clippy --message-format json を実行し Issue リストを返す。

        clippy は JSON Lines（1行1JSON）形式で出力する。
        reason="compiler-message" の行のみを Issue に変換する。
        returncode != 0 でも stdout にメッセージが出力されるのでパースを試みる。
        """
        try:
            result = subprocess.run(
                ["cargo", "clippy", "--message-format", "json", "--", "-W", "clippy::all"],
                capture_output=True,
                text=True,
                check=False,
                cwd=target,
                timeout=_SUBPROCESS_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            logger.warning("cargo clippy timed out after %d seconds", _SUBPROCESS_TIMEOUT)
            return []

        issues: list[Issue] = []
        for raw_line in result.stdout.splitlines():
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                entry = json.loads(raw_line)
            except json.JSONDecodeError:
                continue

            if entry.get("reason") != "compiler-message":
                continue

            msg = entry.get("message", {})
            issue = self._parse_clippy_message(msg)
            if issue is not None:
                issues.append(issue)

        return issues

    def _parse_clippy_message(self, msg: dict) -> Issue | None:
        """compiler-message の message フィールドを Issue に変換する。"""
        level = msg.get("level", "")
        severity = self._map_clippy_severity(level)

        code = msg.get("code") or {}
        rule_id = code.get("code") if code else None
        if not rule_id:
            rule_id = "unknown"

        spans = msg.get("spans", [])
        if spans:
            line = spans[0].get("line_start", 0)
            file = spans[0].get("file_name", "")
        else:
            line = 0
            file = ""

        message = msg.get("message", "")
        rendered = msg.get("rendered", "")
        suggestion = self._extract_help_from_rendered(rendered)

        return Issue(
            file=file,
            line=line,
            severity=severity,
            category="lint",
            tool="clippy",
            message=message,
            rule_id=rule_id,
            suggestion=suggestion,
        )

    @staticmethod
    def _map_clippy_severity(level: str) -> str:
        if level == "error":
            return "critical"
        if level == "warning":
            return "warning"
        return "info"

    @staticmethod
    def _extract_help_from_rendered(rendered: str) -> str:
        """rendered テキストから help: を含む行を抽出する。"""
        for line in rendered.splitlines():
            if "help:" in line:
                return line.strip()
        return ""

    def run_security(self, target: Path) -> list[Issue]:
        """cargo audit --json を実行し Issue リストを返す。

        returncode != 0 は脆弱性あり（正常終了）。stdout をパースする。
        パース失敗時や cargo-audit 未インストール時は空リストを返す。
        """

        try:
            result = subprocess.run(
                ["cargo", "audit", "--json"],
                capture_output=True,
                text=True,
                check=False,
                cwd=target,
                timeout=_SUBPROCESS_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            logger.warning("cargo audit timed out after %d seconds", _SUBPROCESS_TIMEOUT)
            return []

        # cargo audit 未インストール時（stderr にエラー、stdout が空）
        if not result.stdout.strip() and result.returncode != 0:
            logger.warning(
                "cargo audit not available. Install with: cargo install cargo-audit"
            )
            return []

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            return []

        vulns = data.get("vulnerabilities", {})
        vuln_list = vulns.get("list", [])

        issues: list[Issue] = []
        for vuln in vuln_list:
            issue = self._parse_audit_vuln(vuln)
            if issue is not None:
                issues.append(issue)

        return issues

    def _parse_audit_vuln(self, vuln: dict) -> Issue | None:
        """cargo audit の脆弱性エントリを Issue に変換する。"""
        advisory = vuln.get("advisory", {})
        severity_str = advisory.get("severity", "")
        severity = self._map_audit_severity(severity_str)

        rule_id = advisory.get("id", "unknown")
        message = advisory.get("title", "")

        versions = vuln.get("versions", {})
        patched = versions.get("patched", [])
        if patched:
            suggestion = f"Update to: {patched[0]}"
        else:
            suggestion = ""

        return Issue(
            file="Cargo.toml",
            line=0,
            severity=severity,
            category="security",
            tool="cargo-audit",
            message=message,
            rule_id=rule_id,
            suggestion=suggestion,
        )

    @staticmethod
    def _map_audit_severity(severity: str) -> str:
        if severity in ("HIGH", "CRITICAL"):
            return "critical"
        if severity == "MEDIUM":
            return "warning"
        if severity == "LOW":
            return "info"
        return "warning"

    def parse_ast(self, file_path: Path) -> ASTNode:
        """Phase 1 簡易実装: kind=module のルートノードを返す。

        children は空リスト。Phase 2 で tree-sitter による解析に置換する。
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
        """この Analyzer が必要とする外部ツールのリスト。

        cargo-audit は cargo のサブコマンドであり shutil.which では
        検出できないため、cargo のみを必須ツールとして検証する。
        cargo audit のインストール確認は run_security() 内で行う。
        """
        return [
            ToolRequirement(
                command="cargo",
                install_hint="Install Rust: https://rustup.rs/",
            ),
        ]
