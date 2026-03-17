"""gitleaks_scanner モジュールのユニットテスト。

対応仕様: docs/specs/gitleaks-integration-spec.md
対応設計: docs/design/gitleaks-integration-design.md Section 5.2, 5.3, 6.1
対応タスク: Task 1-1, 1-3
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from analyzers.gitleaks_scanner import (
    get_install_guide,
    is_available,
    run_detect,
    run_protect_staged,
)
from analyzers.base import Issue


class TestIsAvailable:
    """is_available() のテスト。"""

    def test_available_when_gitleaks_in_path(self) -> None:
        """PATH に gitleaks がある場合 True を返す。"""
        with patch("analyzers.gitleaks_scanner.shutil.which", return_value="/usr/bin/gitleaks"):
            assert is_available() is True

    def test_not_available_when_gitleaks_missing(self) -> None:
        """PATH に gitleaks がない場合 False を返す。"""
        with patch("analyzers.gitleaks_scanner.shutil.which", return_value=None):
            assert is_available() is False


class TestParseGitleaksJson:
    """_parse_gitleaks_json() の変換テスト。"""

    def test_parse_gitleaks_json_converts_correctly(self, tmp_path: Path) -> None:
        """gitleaks JSON → Issue dataclass の変換が設計 5.3 に準拠すること。"""
        gitleaks_output = [
            {
                "RuleID": "generic-api-key",
                "Description": "Generic API Key detected",
                "File": "src/config.py",
                "StartLine": 10,
                "Match": "AKIAIOSFODNN7EXAMPLE",
                "Secret": "AKIAIOSFODNN7EXAMPLE",
            }
        ]
        json_path = tmp_path / "report.json"
        json_path.write_text(json.dumps(gitleaks_output), encoding="utf-8")

        from analyzers.gitleaks_scanner import _parse_gitleaks_json

        issues = _parse_gitleaks_json(json_path)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.file == "src/config.py"
        assert issue.line == 10
        assert issue.rule_id == "gitleaks:generic-api-key"
        assert issue.message == "Generic API Key detected"
        assert issue.severity == "critical"
        assert issue.category == "security"
        assert issue.tool == "gitleaks"
        assert "環境変数" in issue.suggestion or "secret manager" in issue.suggestion
        # セキュリティ保証: Match/Secret の生値が Issue に含まれないこと
        assert "AKIAIOSFODNN7EXAMPLE" not in issue.suggestion
        assert "AKIAIOSFODNN7EXAMPLE" not in issue.message

    def test_parse_empty_json(self, tmp_path: Path) -> None:
        """検出なしの場合、空リストを返す。"""
        json_path = tmp_path / "report.json"
        json_path.write_text("[]", encoding="utf-8")

        from analyzers.gitleaks_scanner import _parse_gitleaks_json

        issues = _parse_gitleaks_json(json_path)
        assert issues == []

    def test_parse_nonexistent_file(self, tmp_path: Path) -> None:
        """ファイルが存在しない場合、空リストを返す。"""
        from analyzers.gitleaks_scanner import _parse_gitleaks_json

        issues = _parse_gitleaks_json(tmp_path / "nonexistent.json")
        assert issues == []


class TestRunDetect:
    """run_detect() のテスト。"""

    def test_run_detect_not_installed(self, tmp_path: Path) -> None:
        """未インストール時に rule_id='gitleaks:not-installed' の Critical Issue を返す。"""
        with patch("analyzers.gitleaks_scanner.is_available", return_value=False):
            issues = run_detect(tmp_path)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "gitleaks:not-installed"
        assert issue.severity == "critical"
        assert issue.category == "security"
        assert issue.tool == "gitleaks"

    def test_run_detect_no_findings(self, tmp_path: Path) -> None:
        """検出なし時に空リストを返す。"""
        mock_result = MagicMock()
        mock_result.returncode = 0

        def mock_run(cmd, **kwargs):
            for i, arg in enumerate(cmd):
                if arg == "--report-path" and i + 1 < len(cmd):
                    Path(cmd[i + 1]).write_text("[]", encoding="utf-8")
            return mock_result

        with (
            patch("analyzers.gitleaks_scanner.is_available", return_value=True),
            patch("analyzers.gitleaks_scanner.subprocess.run", side_effect=mock_run),
        ):
            issues = run_detect(tmp_path)

        assert issues == []

    def test_run_detect_with_findings(self, tmp_path: Path) -> None:
        """検出あり時に Issue リストが返る。"""
        gitleaks_output = [
            {
                "RuleID": "aws-access-key",
                "Description": "AWS Access Key detected",
                "File": "config.yaml",
                "StartLine": 5,
                "Match": "AKIAIOSFODNN7EXAMPLE",
                "Secret": "AKIAIOSFODNN7EXAMPLE",
            }
        ]
        mock_result = MagicMock()
        mock_result.returncode = 1

        def mock_run(cmd, **kwargs):
            for i, arg in enumerate(cmd):
                if arg == "--report-path" and i + 1 < len(cmd):
                    Path(cmd[i + 1]).write_text(
                        json.dumps(gitleaks_output), encoding="utf-8"
                    )
            return mock_result

        with (
            patch("analyzers.gitleaks_scanner.is_available", return_value=True),
            patch("analyzers.gitleaks_scanner.subprocess.run", side_effect=mock_run),
        ):
            issues = run_detect(tmp_path)

        assert len(issues) == 1
        assert issues[0].file == "config.yaml"
        assert issues[0].severity == "critical"

    def test_run_detect_uses_gitleaks_toml(self, tmp_path: Path) -> None:
        """プロジェクトルートの .gitleaks.toml を自動検出して --config に渡す。"""
        toml_path = tmp_path / ".gitleaks.toml"
        toml_path.write_text("[extend]\n", encoding="utf-8")

        mock_result = MagicMock()
        mock_result.returncode = 0
        captured_cmd: list[str] = []

        def mock_run(cmd, **kwargs):
            captured_cmd.extend(cmd)
            for i, arg in enumerate(cmd):
                if arg == "--report-path" and i + 1 < len(cmd):
                    Path(cmd[i + 1]).write_text("[]", encoding="utf-8")
            return mock_result

        with (
            patch("analyzers.gitleaks_scanner.is_available", return_value=True),
            patch("analyzers.gitleaks_scanner.subprocess.run", side_effect=mock_run),
        ):
            run_detect(tmp_path)

        assert "--config" in captured_cmd
        config_idx = captured_cmd.index("--config")
        assert captured_cmd[config_idx + 1] == str(toml_path)


class TestRunProtectStaged:
    """run_protect_staged() のテスト。"""

    def test_run_protect_staged_not_installed(self) -> None:
        """未インストール時に空リストを返す（WARNING は呼び出し側で表示）。"""
        with patch("analyzers.gitleaks_scanner.is_available", return_value=False):
            issues = run_protect_staged()
        assert issues == []

    def test_run_protect_staged_with_findings(self, tmp_path: Path) -> None:
        """staged 差分にシークレットがある場合 Issue リストを返す。"""
        gitleaks_output = [
            {
                "RuleID": "generic-password",
                "Description": "Generic password detected",
                "File": "app.yaml",
                "StartLine": 3,
                "Match": "password: secret123",
                "Secret": "secret123",
            }
        ]
        mock_result = MagicMock()
        mock_result.returncode = 1

        def mock_run(cmd, **kwargs):
            for i, arg in enumerate(cmd):
                if arg == "--report-path" and i + 1 < len(cmd):
                    Path(cmd[i + 1]).write_text(
                        json.dumps(gitleaks_output), encoding="utf-8"
                    )
            assert "--staged" in cmd
            return mock_result

        with (
            patch("analyzers.gitleaks_scanner.is_available", return_value=True),
            patch("analyzers.gitleaks_scanner.subprocess.run", side_effect=mock_run),
        ):
            issues = run_protect_staged()

        assert len(issues) == 1
        assert issues[0].severity == "critical"


class TestRunDetectScanFailed:
    """run_detect() の実行失敗テスト（C-2 対応）。"""

    def test_run_detect_scan_failed_returns_critical(self, tmp_path: Path) -> None:
        """gitleaks 実行失敗時に scan-failed Critical Issue を返す。"""
        with (
            patch("analyzers.gitleaks_scanner.is_available", return_value=True),
            patch(
                "analyzers.gitleaks_scanner.subprocess.run",
                side_effect=OSError("gitleaks binary crashed"),
            ),
        ):
            issues = run_detect(tmp_path)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "gitleaks:scan-failed"
        assert issue.severity == "critical"
        assert issue.category == "security"

    def test_run_protect_scan_failed_returns_critical(self) -> None:
        """gitleaks protect 実行失敗時に scan-failed Critical Issue を返す。"""
        with (
            patch("analyzers.gitleaks_scanner.is_available", return_value=True),
            patch(
                "analyzers.gitleaks_scanner.subprocess.run",
                side_effect=OSError("gitleaks binary crashed"),
            ),
        ):
            issues = run_protect_staged()

        assert len(issues) == 1
        assert issues[0].rule_id == "gitleaks:scan-failed"


class TestScanTimeout:
    """タイムアウト時の scan-timeout Issue テスト（C-1 対応）。"""

    def test_run_detect_timeout_returns_scan_timeout(self, tmp_path: Path) -> None:
        """gitleaks detect タイムアウト時に scan-timeout Critical Issue を返す。"""
        with (
            patch("analyzers.gitleaks_scanner.is_available", return_value=True),
            patch(
                "analyzers.gitleaks_scanner.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd=["gitleaks"], timeout=120),
            ),
        ):
            issues = run_detect(tmp_path)

        assert len(issues) == 1
        assert issues[0].rule_id == "gitleaks:scan-timeout"
        assert issues[0].severity == "critical"
        assert "120" in issues[0].message

    def test_run_protect_timeout_returns_scan_timeout(self) -> None:
        """gitleaks protect タイムアウト時に scan-timeout Critical Issue を返す。"""
        with (
            patch("analyzers.gitleaks_scanner.is_available", return_value=True),
            patch(
                "analyzers.gitleaks_scanner.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd=["gitleaks"], timeout=60),
            ),
        ):
            issues = run_protect_staged()

        assert len(issues) == 1
        assert issues[0].rule_id == "gitleaks:scan-timeout"


class TestOptOut:
    """明示的オプトアウト機構のテスト。"""

    def test_run_detect_disabled_returns_empty(self, tmp_path: Path) -> None:
        """enabled=False で空リストを返す（G5 PASS）。"""
        issues = run_detect(tmp_path, enabled=False)
        assert issues == []

    def test_run_protect_disabled_returns_empty(self) -> None:
        """enabled=False で空リストを返す。"""
        issues = run_protect_staged(enabled=False)
        assert issues == []

    def test_run_detect_disabled_does_not_call_subprocess(self, tmp_path: Path) -> None:
        """enabled=False 時に subprocess.run を呼ばない。"""
        with patch("analyzers.gitleaks_scanner.subprocess.run") as mock_sub:
            run_detect(tmp_path, enabled=False)
        mock_sub.assert_not_called()

    def test_install_guide_mentions_opt_out(self) -> None:
        """インストールガイドにオプトアウト方法が含まれる。"""
        guide = get_install_guide()
        assert "gitleaks_enabled" in guide


class TestIssueSeverity:
    """全 Issue が Critical/security であることのテスト。"""

    def test_issue_severity_is_critical(self, tmp_path: Path) -> None:
        """gitleaks が検出した全 Issue の severity が critical であること。"""
        gitleaks_output = [
            {
                "RuleID": "aws-access-key",
                "Description": "AWS key",
                "File": "a.py",
                "StartLine": 1,
                "Match": "x",
                "Secret": "x",
            },
            {
                "RuleID": "generic-password",
                "Description": "Password",
                "File": "b.yaml",
                "StartLine": 2,
                "Match": "y",
                "Secret": "y",
            },
        ]
        json_path = tmp_path / "report.json"
        json_path.write_text(json.dumps(gitleaks_output), encoding="utf-8")

        from analyzers.gitleaks_scanner import _parse_gitleaks_json

        issues = _parse_gitleaks_json(json_path)
        for issue in issues:
            assert issue.severity == "critical"
            assert issue.category == "security"
            assert issue.tool == "gitleaks"


class TestGetInstallGuide:
    """get_install_guide() のテスト。"""

    def test_get_install_guide_contains_url(self) -> None:
        """インストールガイドに公式 URL が含まれる。"""
        guide = get_install_guide()
        assert "github.com/gitleaks/gitleaks" in guide

    def test_get_install_guide_contains_commands(self) -> None:
        """インストールガイドにインストールコマンドが含まれる。"""
        guide = get_install_guide()
        assert "brew install gitleaks" in guide
        assert "scoop install gitleaks" in guide

    def test_get_install_guide_contains_g5_impact(self) -> None:
        """インストールガイドに G5 FAIL の影響説明が含まれる。"""
        guide = get_install_guide()
        assert "Green State" in guide
        assert "G5" in guide
        assert "FAIL" in guide


class TestGitleaksTomlAllowlist:
    """除外設定のテスト。"""

    def test_gitleaks_toml_excludes_fixtures(self) -> None:
        """テストフィクスチャが除外パスに含まれること。"""
        toml_path = Path(__file__).resolve().parents[4] / ".gitleaks.toml"
        if not toml_path.exists():
            pytest.skip(".gitleaks.toml not yet created (Task 1-2)")
        content = toml_path.read_text(encoding="utf-8")
        assert "fixtures" in content

    def test_gitleaks_toml_has_extend_section(self) -> None:
        """[extend] セクションが存在すること（デフォルトルール継承）。"""
        toml_path = Path(__file__).resolve().parents[4] / ".gitleaks.toml"
        if not toml_path.exists():
            pytest.skip(".gitleaks.toml not yet created (Task 1-2)")
        content = toml_path.read_text(encoding="utf-8")
        assert "[extend]" in content

    def test_gitleaks_toml_does_not_exclude_memos(self) -> None:
        """docs/memos/ が除外されていないこと（設計意図: 認知の網の外を防ぐ）。"""
        toml_path = Path(__file__).resolve().parents[4] / ".gitleaks.toml"
        if not toml_path.exists():
            pytest.skip(".gitleaks.toml not yet created (Task 1-2)")
        content = toml_path.read_text(encoding="utf-8")
        assert "docs/memos" not in content
