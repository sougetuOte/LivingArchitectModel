"""Task A-6: パイプライン統合テスト

対応仕様: scalable-code-review-spec.md FR-1, NFR-2
対応設計: scalable-code-review-design.md Section 2.4
受け入れ条件: LAM 自体に対して Phase 0 を実行できること
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from analyzers.run_pipeline import (
    count_lines,
    run_phase0,
    should_enable_static_analysis,
)


# ── 行数カウント ───────────────────────────────────────────


class TestCountLines:
    """プロジェクトの有効コード行数をカウントする。"""

    def test_counts_python_files(self, tmp_path: Path) -> None:
        """Python ファイルの行数をカウントできること。"""
        (tmp_path / "a.py").write_text("line1\nline2\nline3\n")
        (tmp_path / "b.py").write_text("x\ny\n")
        result = count_lines(tmp_path)
        assert result >= 5

    def test_excludes_default_dirs(self, tmp_path: Path) -> None:
        """node_modules, .venv 等のデフォルト除外ディレクトリをスキップすること。"""
        (tmp_path / "app.py").write_text("line1\n")
        venv = tmp_path / ".venv" / "lib"
        venv.mkdir(parents=True)
        (venv / "pkg.py").write_text("x\n" * 1000)
        result = count_lines(tmp_path)
        assert result < 100  # .venv の 1000 行が含まれていないこと

    def test_counts_multiple_languages(self, tmp_path: Path) -> None:
        """複数言語のファイルを合算すること。"""
        (tmp_path / "app.py").write_text("a\nb\n")
        (tmp_path / "index.js").write_text("c\nd\ne\n")
        (tmp_path / "main.rs").write_text("f\n")
        result = count_lines(tmp_path)
        assert result == 6

    def test_empty_project(self, tmp_path: Path) -> None:
        """ファイルが存在しない場合は 0 を返すこと。"""
        assert count_lines(tmp_path) == 0

    def test_respects_custom_exclude_dirs(self, tmp_path: Path) -> None:
        """カスタム除外ディレクトリを指定できること。"""
        (tmp_path / "app.py").write_text("a\n")
        build = tmp_path / "build"
        build.mkdir()
        (build / "out.py").write_text("x\n" * 500)
        result = count_lines(tmp_path, exclude_dirs=["build"])
        assert result < 100


# ── 自動有効化判定 ─────────────────────────────────────────


class TestShouldEnableStaticAnalysis:
    """行数に基づく自動有効化判定。NFR-2 対応。"""

    def test_under_10k_returns_skip(self) -> None:
        """10K 行以下は skip（現行 full-review のまま）。"""
        assert should_enable_static_analysis(5000) == "skip"

    def test_10k_to_30k_returns_suggest(self) -> None:
        """10K-30K 行は suggest（ユーザーに提案）。"""
        assert should_enable_static_analysis(15000) == "suggest"

    def test_boundary_10k_returns_suggest(self) -> None:
        """ちょうど 10K 行は suggest。"""
        assert should_enable_static_analysis(10000) == "suggest"

    def test_over_30k_returns_auto(self) -> None:
        """30K 行以上は auto（自動有効化）。"""
        assert should_enable_static_analysis(50000) == "auto"

    def test_boundary_30k_returns_auto(self) -> None:
        """ちょうど 30K 行は auto。"""
        assert should_enable_static_analysis(30000) == "auto"

    def test_boundary_9999_is_skip(self) -> None:
        """9999行は skip（10K 未満）。"""
        assert should_enable_static_analysis(9999) == "skip"

    def test_boundary_29999_is_suggest(self) -> None:
        """29999行は suggest（30K 未満）。"""
        assert should_enable_static_analysis(29999) == "suggest"

    def test_custom_threshold(self) -> None:
        """カスタム閾値を指定できること。"""
        assert should_enable_static_analysis(5000, auto_threshold=5000) == "auto"


# ── Phase 0 パイプライン実行 ───────────────────────────────


class TestRunPhase0:
    """Phase 0（静的解析パイプライン）の統合テスト。"""

    # 既存テストでは gitleaks を無効化（gitleaks 固有のテストは test_gitleaks_scanner.py で実施）
    _GITLEAKS_MOCK = patch("analyzers.run_pipeline.gitleaks_run_detect", return_value=[])

    def test_returns_summary_path(self, project_root: Path) -> None:
        """実行結果の summary.md パスを返すこと。"""
        (project_root / "app.py").write_text("x = 1\n")
        (project_root / "pyproject.toml").write_text("[project]\n")
        with patch("subprocess.run", side_effect=_subprocess_side_effect()), self._GITLEAKS_MOCK:
            result = run_phase0(project_root)
        assert result.summary_path.exists()

    def test_creates_review_state_dir(self, project_root: Path) -> None:
        """review-state/ ディレクトリを作成すること。"""
        (project_root / "app.py").write_text("x = 1\n")
        (project_root / "pyproject.toml").write_text("[project]\n")
        with patch("subprocess.run", side_effect=_subprocess_side_effect()), self._GITLEAKS_MOCK:
            run_phase0(project_root)
        state_dir = project_root / ".claude" / "review-state"
        assert state_dir.is_dir()

    def test_saves_static_issues_json(self, project_root: Path) -> None:
        """static-issues.json を保存すること。"""
        (project_root / "app.py").write_text("x = 1\n")
        (project_root / "pyproject.toml").write_text("[project]\n")
        ruff_output = json.dumps([{
            "code": "F841",
            "filename": str(project_root / "app.py"),
            "location": {"row": 1, "column": 1},
            "end_location": {"row": 1, "column": 6},
            "message": "Local variable 'x' is assigned but never used",
            "fix": None,
            "noqa_row": 1,
            "url": "",
        }])
        with patch("subprocess.run", side_effect=_subprocess_side_effect(ruff_output)), self._GITLEAKS_MOCK:
            result = run_phase0(project_root)
        issues_path = project_root / ".claude" / "review-state" / "static-issues.json"
        assert issues_path.exists()
        assert len(result.issues) == 1

    def test_summary_nfr4_structure(self, project_root: Path) -> None:
        """summary.md が NFR-4 構造に準拠すること。

        - Review Instructions セクションが存在する
        - Summary（カウント）が末尾に配置される
        - Issue 0 件のセクションはスキップされる
        """
        (project_root / "app.py").write_text("x = 1\n")
        (project_root / "pyproject.toml").write_text("[project]\n")
        with patch("subprocess.run", side_effect=_subprocess_side_effect()), self._GITLEAKS_MOCK:
            result = run_phase0(project_root)
        content = result.summary_path.read_text()
        assert "## Review Instructions" in content
        assert "## Summary" in content
        assert "FR-5 リマインド" in content

    def test_returns_line_count(self, project_root: Path) -> None:
        """結果に行数カウントを含むこと。"""
        (project_root / "app.py").write_text("a\nb\nc\n")
        (project_root / "pyproject.toml").write_text("[project]\n")
        with patch("subprocess.run", side_effect=_subprocess_side_effect()), self._GITLEAKS_MOCK:
            result = run_phase0(project_root)
        assert result.line_count >= 3

    def test_returns_detected_languages(self, project_root: Path) -> None:
        """結果に検出された言語リスト（language_name ベース）を含むこと。"""
        (project_root / "app.py").write_text("x = 1\n")
        (project_root / "pyproject.toml").write_text("[project]\n")
        with patch("subprocess.run", side_effect=_subprocess_side_effect()), self._GITLEAKS_MOCK:
            result = run_phase0(project_root)
        assert "python" in result.languages

    def test_no_languages_detected(self, tmp_path: Path) -> None:
        """言語ファイルなしの空ディレクトリでも gitleaks は実行されること。"""
        empty_dir = tmp_path / "empty_project"
        empty_dir.mkdir()
        with self._GITLEAKS_MOCK:
            result = run_phase0(empty_dir)
        assert result.languages == []

    def test_tool_not_found_raises(self, project_root: Path) -> None:
        """ツール未インストール時は ToolNotFoundError を送出すること。"""
        from analyzers.base import ToolNotFoundError

        (project_root / "pyproject.toml").write_text("[project]\n")
        (project_root / "app.py").write_text("x = 1\n")
        with patch("analyzers.base.shutil.which", return_value=None), self._GITLEAKS_MOCK:
            with pytest.raises(ToolNotFoundError):
                run_phase0(project_root)


class TestRunPhase0GitleaksIntegration:
    """run_phase0() の gitleaks 統合テスト。

    対応仕様: gitleaks-integration-spec.md FR-1
    対応設計: gitleaks-integration-design.md Section 5.4, 6.2
    """

    def test_run_phase0_includes_gitleaks(self, project_root: Path) -> None:
        """run_phase0() に gitleaks 結果が含まれること。"""
        (project_root / "app.py").write_text("x = 1\n")
        (project_root / "pyproject.toml").write_text("[project]\n")

        from analyzers.base import Issue
        gitleaks_issue = Issue(
            file="secret.yaml", line=3, severity="critical",
            category="security", tool="gitleaks",
            message="Generic password detected",
            rule_id="gitleaks:generic-password",
            suggestion="test",
        )
        with (
            patch("subprocess.run", side_effect=_subprocess_side_effect()),
            patch("analyzers.run_pipeline.gitleaks_run_detect", return_value=[gitleaks_issue]),
        ):
            result = run_phase0(project_root)

        gitleaks_issues = [i for i in result.issues if i.tool == "gitleaks"]
        assert len(gitleaks_issues) == 1
        assert gitleaks_issues[0].severity == "critical"

    def test_run_phase0_without_gitleaks(self, project_root: Path) -> None:
        """gitleaks 未インストールでも run_phase0() が動作すること（not-installed Issue を含む）。"""
        (project_root / "app.py").write_text("x = 1\n")
        (project_root / "pyproject.toml").write_text("[project]\n")

        from analyzers.base import Issue
        not_installed = Issue(
            file="", line=0, severity="critical",
            category="security", tool="gitleaks",
            message="gitleaks not installed",
            rule_id="gitleaks:not-installed",
            suggestion="install guide",
        )
        with (
            patch("subprocess.run", side_effect=_subprocess_side_effect()),
            patch("analyzers.run_pipeline.gitleaks_run_detect", return_value=[not_installed]),
        ):
            result = run_phase0(project_root)

        not_installed_issues = [i for i in result.issues if i.rule_id == "gitleaks:not-installed"]
        assert len(not_installed_issues) == 1


# ── ヘルパー ───────────────────────────────────────────────


def _mock_result(returncode: int, stdout: str):
    """subprocess.run のモック戻り値を生成する。"""

    class MockResult:
        def __init__(self):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = ""

    return MockResult()


_EMPTY_BANDIT = json.dumps({"results": []})


def _subprocess_side_effect(ruff_output: str = "[]"):
    """ruff と bandit で異なるレスポンスを返す side_effect を生成する。"""

    def side_effect(cmd, **kwargs):
        if cmd[0] == "bandit":
            return _mock_result(0, _EMPTY_BANDIT)
        return _mock_result(0, ruff_output)

    return side_effect
