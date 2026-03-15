"""Scalable Code Review 基盤データモデル + プラグイン管理

Task A-1a: LanguageAnalyzer ABC, ASTNode, Issue
Task A-1b: AnalyzerRegistry, ToolRequirement, ToolNotFoundError

対応仕様: scalable-code-review-spec.md FR-1, FR-2
対応設計: scalable-code-review-design.md Section 2.1, 2.1b, 2.1c, 2.3, 2.4
"""
from __future__ import annotations

import importlib.util
import inspect
import logging
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Issue:
    """静的解析が検出した問題を表すデータモデル。

    設計書 Section 2.3 に対応。各 LanguageAnalyzer の
    run_lint() / run_security() が返す共通型。
    """

    file: str
    line: int
    severity: str  # "critical" | "warning" | "info"
    category: str  # "lint" | "security" | "type" | "dead-code"
    tool: str
    message: str
    rule_id: str
    suggestion: str


@dataclass
class ASTNode:
    """tree-sitter / Python ast の差異を吸収するラッパー型。

    設計書 Section 2.1c に対応。各 LanguageAnalyzer の
    parse_ast() がこの共通型に変換して返す。
    """

    name: str
    kind: str  # "function" | "class" | "module" | "method"
    start_line: int
    end_line: int
    signature: str
    children: list[ASTNode]
    docstring: str | None = None


class LanguageAnalyzer(ABC):
    """言語固有の静的解析プラグインの基底クラス。

    設計書 Section 2.1 に対応。ユーザーが新言語を追加する際は
    このクラスを継承し、language_name と4つの抽象メソッドを実装する。
    """

    language_name: str = ""  # サブクラスで必ずオーバーライド

    @abstractmethod
    def detect(self, project_root: Path) -> bool:
        """プロジェクトがこの言語を使用しているか検出する。"""

    @abstractmethod
    def run_lint(self, target: Path) -> list[Issue]:
        """lint を実行し Issue リストを返す。"""

    @abstractmethod
    def run_security(self, target: Path) -> list[Issue]:
        """セキュリティスキャンを実行し Issue リストを返す。"""

    @abstractmethod
    def parse_ast(self, file_path: Path) -> ASTNode:
        """AST を構築して返す。"""

    def run_type_check(self, target: Path) -> list[Issue]:
        """型チェック（オプション）。デフォルトは空リスト。"""
        return []

    def required_tools(self) -> list[ToolRequirement]:
        """この Analyzer が必要とする外部ツールのリスト。

        サブクラスでオーバーライドし、必要なツールとインストール手順を返す。
        デフォルトは空リスト（外部ツール不要）。
        """
        return []


@dataclass
class ToolRequirement:
    """外部ツールの要件を表すデータモデル。"""

    command: str
    install_hint: str


class ToolNotFoundError(Exception):
    """必要なツールが見つからない場合のエラー。

    設計書 Section 2.4 step 4: 未インストール時はエラー停止し、
    インストール手順を表示する（FR-1）。
    """

    def __init__(self, missing: list[tuple[str, str]]) -> None:
        self.missing = missing
        lines = ["Required tools not found:"]
        for cmd, hint in missing:
            lines.append(f"  - {cmd}: {hint}")
        super().__init__("\n".join(lines))


class AnalyzerRegistry:
    """言語 Analyzer の自動検出・管理を担う。

    設計書 Section 2.1b に対応。
    *_analyzer.py を自動探索し、LanguageAnalyzer サブクラスを登録する。
    """

    def __init__(self) -> None:
        self._analyzer_classes: list[type[LanguageAnalyzer]] = []

    def register(self, analyzer_cls: type[LanguageAnalyzer]) -> None:
        """Analyzer クラスを手動登録する。"""
        self._analyzer_classes.append(analyzer_cls)

    def auto_discover(self, search_dir: Path) -> None:
        """search_dir 内の *_analyzer.py を探索し、
        LanguageAnalyzer サブクラスを自動登録する。"""
        for module_path in sorted(search_dir.glob("*_analyzer.py")):
            self._load_module(module_path)

    def _load_module(self, module_path: Path) -> None:
        """モジュールを動的にインポートし、LanguageAnalyzer の
        具象サブクラスを発見して登録する。"""
        spec = importlib.util.spec_from_file_location(
            module_path.stem, module_path,
        )
        if spec is None or spec.loader is None:
            return
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except SyntaxError as e:
            logger.error(
                "SyntaxError in analyzer %s (likely a code bug): %s",
                module_path, e,
            )
            return
        except (ImportError, OSError, AttributeError, ValueError) as e:
            logger.warning(
                "Failed to load analyzer %s: %s: %s",
                module_path, type(e).__name__, e,
            )
            return

        # クラス名ベースで重複チェック（動的ロードされたクラスと
        # register() で登録されたクラスはオブジェクト同一性が異なるため）
        registered_names = {cls.__name__ for cls in self._analyzer_classes}
        for _name, obj in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(obj, LanguageAnalyzer)
                and obj is not LanguageAnalyzer
                and not inspect.isabstract(obj)
                and obj.__name__ not in registered_names
            ):
                self._analyzer_classes.append(obj)

    def detect_languages(self, project_root: Path) -> list[LanguageAnalyzer]:
        """プロジェクトで使用されている言語を検出し、
        対応する Analyzer のインスタンスリストを返す。"""
        result: list[LanguageAnalyzer] = []
        for cls in self._analyzer_classes:
            instance = cls()
            if instance.detect(project_root):
                result.append(instance)
        return result

    def verify_tools(self, analyzers: list[LanguageAnalyzer]) -> None:
        """全 Analyzer の required_tools を検証する。

        未インストールのツールがあれば ToolNotFoundError を送出する。
        """
        missing: list[tuple[str, str]] = []
        for analyzer in analyzers:
            for tool in analyzer.required_tools():
                if shutil.which(tool.command) is None:
                    missing.append((tool.command, tool.install_hint))
        if missing:
            raise ToolNotFoundError(missing)

    def run_all(self, project_root: Path, target: Path) -> list[Issue]:
        """検出された全言語で lint + security を実行し、Issue を統合して返す。

        実行前にツール検証を行い、未インストール時はエラー停止する。
        """
        analyzers = self.detect_languages(project_root)
        self.verify_tools(analyzers)
        issues: list[Issue] = []
        for analyzer in analyzers:
            issues.extend(analyzer.run_lint(target))
            issues.extend(analyzer.run_security(target))
        return issues
