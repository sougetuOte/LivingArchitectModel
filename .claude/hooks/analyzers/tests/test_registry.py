"""Task A-1b: AnalyzerRegistry + ツール検証のテスト

対応仕様: scalable-code-review-spec.md FR-1
対応設計: scalable-code-review-design.md Section 2.1b, 2.4
"""
from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from analyzers.base import (
    ASTNode,
    AnalyzerRegistry,
    Issue,
    LanguageAnalyzer,
    ToolNotFoundError,
    ToolRequirement,
)


# ── テスト用の具象 Analyzer ───────────────────────────────


def _make_dummy_node() -> ASTNode:
    return ASTNode(name="m", kind="module", start_line=1, end_line=1,
                   signature="", children=[])


class _AlwaysDetectAnalyzer(LanguageAnalyzer):
    """常に detect=True を返すダミー Analyzer。"""

    def detect(self, project_root: Path) -> bool:
        return True

    def run_lint(self, target: Path) -> list[Issue]:
        return [Issue(file="a.py", line=1, severity="info", category="lint",
                      tool="dummy", message="dummy lint", rule_id="D001",
                      suggestion="")]

    def run_security(self, target: Path) -> list[Issue]:
        return [Issue(file="a.py", line=2, severity="warning", category="security",
                      tool="dummy", message="dummy sec", rule_id="D002",
                      suggestion="")]

    def parse_ast(self, file_path: Path) -> ASTNode:
        return _make_dummy_node()


class _NeverDetectAnalyzer(LanguageAnalyzer):
    """常に detect=False を返すダミー Analyzer。"""

    def detect(self, project_root: Path) -> bool:
        return False

    def run_lint(self, target: Path) -> list[Issue]:
        return []

    def run_security(self, target: Path) -> list[Issue]:
        return []

    def parse_ast(self, file_path: Path) -> ASTNode:
        return _make_dummy_node()


class _ToolRequiringAnalyzer(LanguageAnalyzer):
    """required_tools を宣言するダミー Analyzer。"""

    def detect(self, project_root: Path) -> bool:
        return True

    def run_lint(self, target: Path) -> list[Issue]:
        return []

    def run_security(self, target: Path) -> list[Issue]:
        return []

    def parse_ast(self, file_path: Path) -> ASTNode:
        return _make_dummy_node()

    def required_tools(self) -> list[ToolRequirement]:
        return [
            ToolRequirement(command="ruff", install_hint="pip install ruff"),
            ToolRequirement(command="bandit", install_hint="pip install bandit"),
        ]


# ── ToolRequirement ────────────────────────────────────────


class TestToolRequirement:
    """ToolRequirement データモデルのテスト。"""

    def test_instantiation(self) -> None:
        tr = ToolRequirement(command="ruff", install_hint="pip install ruff")
        assert tr.command == "ruff"
        assert tr.install_hint == "pip install ruff"


# ── AnalyzerRegistry: 手動登録 ─────────────────────────────


class TestRegistryManual:
    """AnalyzerRegistry の手動登録・検出テスト。"""

    def test_register_and_detect(self, project_root: Path) -> None:
        """register() したクラスが detect_languages() で返ること。"""
        reg = AnalyzerRegistry()
        reg.register(_AlwaysDetectAnalyzer)
        detected = reg.detect_languages(project_root)
        assert len(detected) == 1
        assert isinstance(detected[0], _AlwaysDetectAnalyzer)

    def test_detect_filters_by_detect_method(self, project_root: Path) -> None:
        """detect() が False を返す Analyzer は除外されること。"""
        reg = AnalyzerRegistry()
        reg.register(_AlwaysDetectAnalyzer)
        reg.register(_NeverDetectAnalyzer)
        detected = reg.detect_languages(project_root)
        assert len(detected) == 1
        assert isinstance(detected[0], _AlwaysDetectAnalyzer)

    def test_empty_registry(self, project_root: Path) -> None:
        """未登録時は空リストを返すこと。"""
        reg = AnalyzerRegistry()
        assert reg.detect_languages(project_root) == []

    def test_run_all_collects_issues(self, project_root: Path) -> None:
        """run_all() が全 Analyzer の lint + security Issue を統合すること。"""
        reg = AnalyzerRegistry()
        reg.register(_AlwaysDetectAnalyzer)
        issues = reg.run_all(project_root, project_root)
        assert len(issues) == 2
        assert issues[0].category == "lint"
        assert issues[1].category == "security"

    def test_run_all_skips_undetected(self, project_root: Path) -> None:
        """detect=False の Analyzer はスキップされること。"""
        reg = AnalyzerRegistry()
        reg.register(_NeverDetectAnalyzer)
        issues = reg.run_all(project_root, project_root)
        assert issues == []


# ── AnalyzerRegistry: 自動探索 ─────────────────────────────


class TestRegistryAutoDiscover:
    """AnalyzerRegistry の *_analyzer.py 自動探索テスト。"""

    @staticmethod
    def _write_analyzer_module(directory: Path, filename: str,
                               code: str) -> Path:
        """テスト用の analyzer モジュールを書き出す。"""
        filepath = directory / filename
        filepath.write_text(textwrap.dedent(code))
        return filepath

    def test_discovers_analyzer_py(self, tmp_path: Path,
                                   project_root: Path) -> None:
        """*_analyzer.py から LanguageAnalyzer サブクラスを検出すること。"""
        self._write_analyzer_module(tmp_path, "test_lang_analyzer.py", """\
            from pathlib import Path
            from analyzers.base import LanguageAnalyzer, Issue, ASTNode

            class TestLangAnalyzer(LanguageAnalyzer):
                def detect(self, project_root: Path) -> bool:
                    return True
                def run_lint(self, target: Path) -> list[Issue]:
                    return []
                def run_security(self, target: Path) -> list[Issue]:
                    return []
                def parse_ast(self, file_path: Path) -> ASTNode:
                    return ASTNode(name="m", kind="module",
                                   start_line=1, end_line=1,
                                   signature="", children=[])
        """)
        reg = AnalyzerRegistry()
        reg.auto_discover(tmp_path)
        detected = reg.detect_languages(project_root)
        assert len(detected) == 1

    def test_ignores_non_analyzer_files(self, tmp_path: Path,
                                        project_root: Path) -> None:
        """*_analyzer.py パターンに合致しないファイルは無視すること。"""
        self._write_analyzer_module(tmp_path, "helper.py", """\
            from pathlib import Path
            from analyzers.base import LanguageAnalyzer, Issue, ASTNode

            class HelperAnalyzer(LanguageAnalyzer):
                def detect(self, project_root: Path) -> bool:
                    return True
                def run_lint(self, target: Path) -> list[Issue]:
                    return []
                def run_security(self, target: Path) -> list[Issue]:
                    return []
                def parse_ast(self, file_path: Path) -> ASTNode:
                    return ASTNode(name="m", kind="module",
                                   start_line=1, end_line=1,
                                   signature="", children=[])
        """)
        reg = AnalyzerRegistry()
        reg.auto_discover(tmp_path)
        detected = reg.detect_languages(project_root)
        assert len(detected) == 0

    def test_ignores_module_without_subclass(self, tmp_path: Path,
                                             project_root: Path) -> None:
        """LanguageAnalyzer サブクラスを含まないモジュールは無視すること。"""
        self._write_analyzer_module(tmp_path, "empty_analyzer.py", """\
            # No LanguageAnalyzer subclass here
            class NotAnAnalyzer:
                pass
        """)
        reg = AnalyzerRegistry()
        reg.auto_discover(tmp_path)
        detected = reg.detect_languages(project_root)
        assert len(detected) == 0

    def test_does_not_register_abc_itself(self, tmp_path: Path,
                                          project_root: Path) -> None:
        """LanguageAnalyzer ABC 自体は登録しないこと。"""
        self._write_analyzer_module(tmp_path, "base_analyzer.py", """\
            from analyzers.base import LanguageAnalyzer
            # Only imports the ABC, no concrete subclass
        """)
        reg = AnalyzerRegistry()
        reg.auto_discover(tmp_path)
        detected = reg.detect_languages(project_root)
        assert len(detected) == 0


# ── ツール検証 ─────────────────────────────────────────────


class TestToolVerification:
    """ツールインストール確認ロジックのテスト。設計書 Section 2.4 step 4。"""

    def test_all_tools_present(self, project_root: Path) -> None:
        """全ツールがインストール済みならエラーなし。"""
        reg = AnalyzerRegistry()
        reg.register(_ToolRequiringAnalyzer)
        analyzers = reg.detect_languages(project_root)
        with patch("analyzers.base.shutil.which", return_value="/usr/bin/tool"):
            reg.verify_tools(analyzers)  # should not raise

    def test_missing_tool_raises_error(self, project_root: Path) -> None:
        """未インストールのツールがあれば ToolNotFoundError。"""
        reg = AnalyzerRegistry()
        reg.register(_ToolRequiringAnalyzer)
        analyzers = reg.detect_languages(project_root)

        def mock_which(cmd: str) -> str | None:
            return "/usr/bin/ruff" if cmd == "ruff" else None

        with patch("analyzers.base.shutil.which", side_effect=mock_which):
            with pytest.raises(ToolNotFoundError) as exc_info:
                reg.verify_tools(analyzers)
            assert "bandit" in str(exc_info.value)
            assert "pip install bandit" in str(exc_info.value)

    def test_error_lists_all_missing(self, project_root: Path) -> None:
        """複数ツール未インストール時は全て列挙すること。"""
        reg = AnalyzerRegistry()
        reg.register(_ToolRequiringAnalyzer)
        analyzers = reg.detect_languages(project_root)
        with patch("analyzers.base.shutil.which", return_value=None):
            with pytest.raises(ToolNotFoundError) as exc_info:
                reg.verify_tools(analyzers)
            err = exc_info.value
            assert len(err.missing) == 2

    def test_no_required_tools_passes(self, project_root: Path) -> None:
        """required_tools が空なら検証パス。"""
        reg = AnalyzerRegistry()
        reg.register(_AlwaysDetectAnalyzer)
        analyzers = reg.detect_languages(project_root)
        reg.verify_tools(analyzers)  # should not raise

    def test_run_all_verifies_tools_first(self, project_root: Path) -> None:
        """run_all() はツール検証を先に行うこと。"""
        reg = AnalyzerRegistry()
        reg.register(_ToolRequiringAnalyzer)
        with patch("analyzers.base.shutil.which", return_value=None):
            with pytest.raises(ToolNotFoundError):
                reg.run_all(project_root, project_root)


# ── LanguageAnalyzer.required_tools デフォルト ──────────────


class TestRequiredToolsDefault:
    """required_tools() のデフォルト実装テスト。"""

    def test_default_returns_empty(self) -> None:
        """デフォルト実装は空リストを返すこと。"""
        analyzer = _AlwaysDetectAnalyzer()
        assert analyzer.required_tools() == []
