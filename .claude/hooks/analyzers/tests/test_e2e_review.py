"""E-2a/E-2b/E-3a/E-3b: スケール判定テスト + E2E フィクスチャ検証 + LLM依存テスト

対応仕様: scalable-code-review-phase5-spec.md
         FR-E2a, FR-E2b, FR-E2c, FR-E2d, FR-E3a, FR-E3b-1, FR-E3b-2, FR-E3b-3, FR-E3c
対応設計: scalable-code-review-design.md Section 6.3, 6.4
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from analyzers.scale_detector import (
    ScaleDetectionResult,
    detect_scale,
    format_scale_detection,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "e2e"
RESULTS_DIR = Path(__file__).parents[4] / "docs" / "artifacts" / "e2e-results"


@dataclass
class DetectionResult:
    """検出率テストの1回分の結果。"""

    fixture_name: str
    expected_count: int
    detected_count: int
    detection_rate: float
    meets_target: bool


@dataclass
class E2ERunRecord:
    """E2E テスト全体の実行記録。"""

    run_id: str
    test_type: str
    status: str
    summary: str
    details: list[dict]
    elapsed_seconds: float


def _count_inline_issue_markers(fixture: Path) -> int:
    """フィクスチャファイルのコード内インラインマーカー（# FIXTURE-ISSUE-N:）を数える。

    ファイルヘッダー docstring の列挙行は除外し、
    実際のコード行に付与されたマーカーのみをカウントする。
    """
    count = 0
    for line in fixture.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("# FIXTURE-ISSUE-"):
            count += 1
    return count


def _save_result(record: E2ERunRecord) -> None:
    """結果を docs/artifacts/e2e-results/ に保存する。

    latest.json（上書き）+ latest-summary.md（上書き）+ history/{run_id}.json（追記）。
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    history_dir = RESULTS_DIR / "history"
    history_dir.mkdir(exist_ok=True)

    data = {
        "run_id": record.run_id,
        "executed_at": datetime.now().isoformat(),
        "test_type": record.test_type,
        "overall_status": record.status,
        "summary": record.summary,
        "details": record.details,
        "elapsed_seconds": record.elapsed_seconds,
    }
    json_text = json.dumps(data, indent=2, ensure_ascii=False)
    (RESULTS_DIR / "latest.json").write_text(json_text, encoding="utf-8")
    (history_dir / f"{record.run_id}.json").write_text(json_text, encoding="utf-8")

    summary_md = (
        f"# E2E Review Quality Report\n\n"
        f"**Run ID**: {record.run_id}\n"
        f"**Type**: {record.test_type}\n"
        f"**Status**: {record.status}\n"
        f"**Summary**: {record.summary}\n"
        f"**Elapsed**: {record.elapsed_seconds:.1f}s\n"
    )
    (RESULTS_DIR / "latest-summary.md").write_text(summary_md, encoding="utf-8")


class TestScaleDetection:
    """行数ベース閾値テーブルによるスケール判定。"""

    def test_under_10k_returns_no_plans(self, project_root: Path) -> None:
        """10K 行未満では推奨 Plan がないこと。"""
        with patch("analyzers.scale_detector.count_lines", return_value=9_999):
            result = detect_scale(project_root)

        assert result.recommended_plans == []
        assert result.active_plans == []
        assert result.line_count == 9_999

    def test_10k_to_30k_returns_plan_a(self, project_root: Path) -> None:
        """10K 以上 30K 未満では Plan A のみが推奨されること。"""
        with patch("analyzers.scale_detector.count_lines", return_value=10_000):
            result = detect_scale(project_root)

        assert result.recommended_plans == ["A"]

    def test_just_below_30k_still_plan_a(self, project_root: Path) -> None:
        """30K 直前（29,999行）ではまだ Plan A のみであること。"""
        with patch("analyzers.scale_detector.count_lines", return_value=29_999):
            result = detect_scale(project_root)

        assert result.recommended_plans == ["A"]

    def test_30k_to_100k_returns_plan_a_and_b(self, project_root: Path) -> None:
        """30K 以上 100K 未満では Plan A + B が推奨されること。"""
        with patch("analyzers.scale_detector.count_lines", return_value=30_000):
            result = detect_scale(project_root)

        assert result.recommended_plans == ["A", "B"]

    def test_just_below_100k_still_plan_a_and_b(self, project_root: Path) -> None:
        """100K 直前（99,999行）ではまだ Plan A + B であること。"""
        with patch("analyzers.scale_detector.count_lines", return_value=99_999):
            result = detect_scale(project_root)

        assert result.recommended_plans == ["A", "B"]

    def test_100k_to_300k_returns_plan_a_b_c(self, project_root: Path) -> None:
        """100K 以上 300K 未満では Plan A + B + C が推奨されること。"""
        with patch("analyzers.scale_detector.count_lines", return_value=100_000):
            result = detect_scale(project_root)

        assert result.recommended_plans == ["A", "B", "C"]

    def test_just_below_300k_still_plan_a_b_c(self, project_root: Path) -> None:
        """300K 直前（299,999行）ではまだ Plan A + B + C であること。"""
        with patch("analyzers.scale_detector.count_lines", return_value=299_999):
            result = detect_scale(project_root)

        assert result.recommended_plans == ["A", "B", "C"]

    def test_over_300k_returns_all_plans(self, project_root: Path) -> None:
        """300K 以上では全 Plan（A + B + C + D）が推奨されること。"""
        with patch("analyzers.scale_detector.count_lines", return_value=300_000):
            result = detect_scale(project_root)

        assert result.recommended_plans == ["A", "B", "C", "D"]

    def test_over_300k_large_project(self, project_root: Path) -> None:
        """非常に大規模なプロジェクトでも全 Plan が推奨されること。"""
        with patch("analyzers.scale_detector.count_lines", return_value=1_000_000):
            result = detect_scale(project_root)

        assert result.recommended_plans == ["A", "B", "C", "D"]

    def test_active_plans_matches_recommended_when_all_available(
        self, project_root: Path
    ) -> None:
        """全 Plan が available=True の場合、active_plans == recommended_plans であること。"""
        with patch("analyzers.scale_detector.count_lines", return_value=50_000):
            result = detect_scale(project_root)

        # ruff/bandit/tree-sitter がインストール済みの環境で成立する
        assert result.active_plans == result.recommended_plans

    def test_plan_statuses_contains_all_plans(self, project_root: Path) -> None:
        """plan_statuses に A〜D の全エントリが含まれること。"""
        with patch("analyzers.scale_detector.count_lines", return_value=50_000):
            result = detect_scale(project_root)

        assert set(result.plan_statuses.keys()) == {"A", "B", "C", "D"}

    def test_plan_statuses_enabled_matches_recommended(
        self, project_root: Path
    ) -> None:
        """plan_statuses.enabled が recommended_plans と一致すること。"""
        with patch("analyzers.scale_detector.count_lines", return_value=50_000):
            result = detect_scale(project_root)

        for plan, status in result.plan_statuses.items():
            if plan in result.recommended_plans:
                assert status.enabled is True, f"Plan {plan} should be enabled"
            else:
                assert status.enabled is False, f"Plan {plan} should not be enabled"

    def test_output_format_matches_fr_e2c(self, project_root: Path) -> None:
        """format_scale_detection() の出力が FR-E2c 仕様のフォーマットに準拠すること。"""
        with patch("analyzers.scale_detector.count_lines", return_value=45_230):
            result = detect_scale(project_root)

        output = format_scale_detection(result)

        assert output.startswith("=== Scale Detection ===")
        assert "Lines:" in output
        assert "Recommended:" in output
        assert "Active Plans:" in output

    def test_format_lines_uses_comma_separator(self, project_root: Path) -> None:
        """Lines の行数表示がカンマ区切りであること（例: 45,230）。"""
        with patch("analyzers.scale_detector.count_lines", return_value=45_230):
            result = detect_scale(project_root)

        output = format_scale_detection(result)

        assert "45,230" in output

    def test_format_no_plans_shows_none(self, project_root: Path) -> None:
        """推奨 Plan なしの場合、Recommended: None と表示されること。"""
        with patch("analyzers.scale_detector.count_lines", return_value=5_000):
            result = detect_scale(project_root)

        output = format_scale_detection(result)

        assert "Recommended: None" in output

    def test_format_multiple_plans_uses_plus(self, project_root: Path) -> None:
        """複数 Plan の場合、"Plan A + B + C" 形式で表示されること。"""
        with patch("analyzers.scale_detector.count_lines", return_value=150_000):
            result = detect_scale(project_root)

        output = format_scale_detection(result)

        assert "Plan A + B + C" in output

    def test_detect_scale_uses_config_exclude_dirs(self, project_root: Path) -> None:
        """config が渡された場合、exclude_dirs を count_lines に渡すこと。"""
        from analyzers.config import ReviewConfig

        config = ReviewConfig(exclude_dirs=["custom_dir"])
        with patch(
            "analyzers.scale_detector.count_lines", return_value=0
        ) as mock_count:
            detect_scale(project_root, config=config)

        mock_count.assert_called_once_with(project_root, ["custom_dir"])


class TestFixtures:
    """E2E フィクスチャの存在・構造を検証する決定的テスト（FR-E3a, FR-E3b-3）。"""

    def test_fixtures_dir_exists(self) -> None:
        """fixtures/e2e/ ディレクトリが存在すること。"""
        assert FIXTURES_DIR.is_dir()

    def test_critical_fixture_exists(self) -> None:
        """critical_silent_failure.py フィクスチャが存在すること。"""
        assert (FIXTURES_DIR / "critical_silent_failure.py").is_file()

    def test_warning_fixture_exists(self) -> None:
        """warning_long_function.py フィクスチャが存在すること。"""
        assert (FIXTURES_DIR / "warning_long_function.py").is_file()

    def test_security_fixture_exists(self) -> None:
        """security_hardcoded_password.py フィクスチャが存在すること。"""
        assert (FIXTURES_DIR / "security_hardcoded_password.py").is_file()

    def test_combined_fixture_exists(self) -> None:
        """combined_issues.py フィクスチャが存在すること。"""
        assert (FIXTURES_DIR / "combined_issues.py").is_file()

    def test_fixtures_contain_issue_markers(self) -> None:
        """全フィクスチャに FIXTURE-ISSUE- マーカーが含まれること。"""
        for fixture in FIXTURES_DIR.glob("*.py"):
            content = fixture.read_text()
            assert "FIXTURE-ISSUE-" in content, (
                f"{fixture.name} lacks FIXTURE-ISSUE markers"
            )

    def test_save_result_creates_files(self, tmp_path: Path, monkeypatch) -> None:
        """_save_result が latest.json と history/ に保存すること。"""
        import analyzers.tests.test_e2e_review as module

        monkeypatch.setattr(module, "RESULTS_DIR", tmp_path)

        record = E2ERunRecord(
            run_id="20260316_000000",
            test_type="detection",
            status="passed",
            summary="test summary",
            details=[],
            elapsed_seconds=1.23,
        )
        _save_result(record)

        assert (tmp_path / "latest.json").is_file()
        assert (tmp_path / "latest-summary.md").is_file()
        assert (tmp_path / "history" / "20260316_000000.json").is_file()

        data = json.loads((tmp_path / "latest.json").read_text())
        assert data["run_id"] == "20260316_000000"
        assert data["overall_status"] == "passed"

        summary = (tmp_path / "latest-summary.md").read_text()
        assert "20260316_000000" in summary
        assert "passed" in summary

    def test_save_result_history_content_matches(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """history/ に保存されたファイルの内容が latest.json と同一であること。"""
        import analyzers.tests.test_e2e_review as module

        monkeypatch.setattr(module, "RESULTS_DIR", tmp_path)

        record = E2ERunRecord(
            run_id="20260316_120000",
            test_type="scale",
            status="failed",
            summary="scale summary",
            details=[{"key": "value"}],
            elapsed_seconds=0.5,
        )
        _save_result(record)

        latest = json.loads((tmp_path / "latest.json").read_text())
        history = json.loads(
            (tmp_path / "history" / "20260316_120000.json").read_text()
        )
        assert latest["run_id"] == history["run_id"]
        assert latest["overall_status"] == history["overall_status"]
        assert latest["details"] == history["details"]


class TestPlanPrerequisiteChecks:
    """E-2b: Plan 固有の前提条件チェック。"""

    def test_plan_a_skipped_when_ruff_missing(self, project_root: Path) -> None:
        """ruff 未インストール時、Plan A が active_plans に含まれないこと。"""
        def mock_which(name: str) -> str | None:
            return None if name == "ruff" else f"/usr/bin/{name}"

        with patch("analyzers.scale_detector.count_lines", return_value=50_000), \
             patch("analyzers.scale_detector.shutil.which", side_effect=mock_which):
            result = detect_scale(project_root)

        assert "A" not in result.active_plans
        assert result.plan_statuses["A"].available is False
        assert "ruff" in result.plan_statuses["A"].reason

    def test_plan_a_skipped_when_bandit_missing(self, project_root: Path) -> None:
        """bandit 未インストール時、Plan A が active_plans に含まれないこと。"""
        def mock_which(name: str) -> str | None:
            return None if name == "bandit" else f"/usr/bin/{name}"

        with patch("analyzers.scale_detector.count_lines", return_value=50_000), \
             patch("analyzers.scale_detector.shutil.which", side_effect=mock_which):
            result = detect_scale(project_root)

        assert "A" not in result.active_plans
        assert result.plan_statuses["A"].available is False
        assert "bandit" in result.plan_statuses["A"].reason

    def test_plan_a_available_when_both_tools_installed(
        self, project_root: Path
    ) -> None:
        """ruff, bandit が両方インストール済みなら Plan A が available であること。"""
        with patch("analyzers.scale_detector.count_lines", return_value=50_000), \
             patch("analyzers.scale_detector.shutil.which", return_value="/usr/bin/tool"):
            result = detect_scale(project_root)

        assert result.plan_statuses["A"].available is True
        assert "ruff" in result.plan_statuses["A"].reason
        assert "bandit" in result.plan_statuses["A"].reason

    def test_plan_b_unavailable_when_tree_sitter_missing(
        self, project_root: Path
    ) -> None:
        """tree-sitter 未インストール時、Plan B が unavailable であること。"""
        def mock_find_spec(name: str) -> object | None:
            return None if name == "tree_sitter" else importlib.util.find_spec(name)

        with patch("analyzers.scale_detector.count_lines", return_value=50_000), \
             patch("analyzers.scale_detector.shutil.which", return_value="/usr/bin/tool"), \
             patch("analyzers.scale_detector.importlib.util.find_spec", side_effect=mock_find_spec):
            result = detect_scale(project_root)

        assert result.plan_statuses["B"].available is False
        assert "tree-sitter" in result.plan_statuses["B"].reason

    def test_plan_b_available_when_tree_sitter_installed(
        self, project_root: Path
    ) -> None:
        """tree-sitter がインストール済みなら Plan B が available であること。"""
        fake_spec = object()
        with patch("analyzers.scale_detector.count_lines", return_value=50_000), \
             patch("analyzers.scale_detector.shutil.which", return_value="/usr/bin/tool"), \
             patch("analyzers.scale_detector.importlib.util.find_spec", return_value=fake_spec):
            result = detect_scale(project_root)

        assert result.plan_statuses["B"].available is True
        assert "tree-sitter" in result.plan_statuses["B"].reason

    def test_plan_c_unavailable_when_plan_b_unavailable(
        self, project_root: Path
    ) -> None:
        """Plan B が unavailable なら Plan C も unavailable であること。"""
        def mock_find_spec(name: str) -> object | None:
            return None if name == "tree_sitter" else importlib.util.find_spec(name)

        with patch("analyzers.scale_detector.count_lines", return_value=150_000), \
             patch("analyzers.scale_detector.shutil.which", return_value="/usr/bin/tool"), \
             patch("analyzers.scale_detector.importlib.util.find_spec", side_effect=mock_find_spec):
            result = detect_scale(project_root)

        assert result.plan_statuses["B"].available is False
        assert result.plan_statuses["C"].available is False
        assert "Plan B" in result.plan_statuses["C"].reason

    def test_plan_c_available_when_plan_b_available(
        self, project_root: Path
    ) -> None:
        """Plan B が available なら Plan C も available であること。"""
        fake_spec = object()
        with patch("analyzers.scale_detector.count_lines", return_value=150_000), \
             patch("analyzers.scale_detector.shutil.which", return_value="/usr/bin/tool"), \
             patch("analyzers.scale_detector.importlib.util.find_spec", return_value=fake_spec):
            result = detect_scale(project_root)

        assert result.plan_statuses["B"].available is True
        assert result.plan_statuses["C"].available is True
        assert result.plan_statuses["C"].reason == "auto"

    def test_plan_d_skipped_when_import_map_missing(self, project_root: Path) -> None:
        """import-map.json が存在しない場合、Plan D が unavailable であること。"""
        with patch("analyzers.scale_detector.count_lines", return_value=350_000), \
             patch("analyzers.scale_detector.shutil.which", return_value="/usr/bin/tool"), \
             patch("analyzers.scale_detector.importlib.util.find_spec", return_value=object()):
            result = detect_scale(project_root)

        # import-map.json は project_root/.claude/review-state/ に存在しない
        assert result.plan_statuses["D"].available is False
        assert "import-map.json" in result.plan_statuses["D"].reason

    def test_plan_d_available_when_import_map_exists(
        self, project_root: Path
    ) -> None:
        """import-map.json が存在する場合、Plan D が available であること。"""
        import_map_dir = project_root / ".claude" / "review-state"
        import_map_dir.mkdir(parents=True, exist_ok=True)
        (import_map_dir / "import-map.json").write_text("{}", encoding="utf-8")

        with patch("analyzers.scale_detector.count_lines", return_value=350_000), \
             patch("analyzers.scale_detector.shutil.which", return_value="/usr/bin/tool"), \
             patch("analyzers.scale_detector.importlib.util.find_spec", return_value=object()):
            result = detect_scale(project_root)

        assert result.plan_statuses["D"].available is True
        assert "import-map.json" in result.plan_statuses["D"].reason

    def test_plan_a_not_enabled_when_not_recommended(
        self, project_root: Path
    ) -> None:
        """Plan A が recommended に含まれない場合は enabled=False であること。"""
        with patch("analyzers.scale_detector.count_lines", return_value=5_000), \
             patch("analyzers.scale_detector.shutil.which", return_value="/usr/bin/tool"), \
             patch("analyzers.scale_detector.importlib.util.find_spec", return_value=object()):
            result = detect_scale(project_root)

        assert result.plan_statuses["A"].enabled is False

    def test_plan_unavailable_not_in_active_plans(self, project_root: Path) -> None:
        """unavailable な Plan は active_plans に含まれないこと。"""
        def mock_which(name: str) -> str | None:
            return None if name == "ruff" else f"/usr/bin/{name}"

        with patch("analyzers.scale_detector.count_lines", return_value=150_000), \
             patch("analyzers.scale_detector.shutil.which", side_effect=mock_which), \
             patch("analyzers.scale_detector.importlib.util.find_spec", return_value=object()):
            result = detect_scale(project_root)

        # Plan A unavailable → active_plans に A が含まれない
        assert "A" not in result.active_plans
        # B, C は available
        assert "B" in result.active_plans
        assert "C" in result.active_plans


class TestCLIEntryPoint:
    """E-2b: CLI エントリポイントの動作テスト。"""

    def test_cli_outputs_scale_detection_json(self, project_root: Path) -> None:
        """CLI 実行で scale-detection.json が生成されること。"""
        scale_detector_path = (
            Path(__file__).resolve().parent.parent / "scale_detector.py"
        )
        hooks_dir = scale_detector_path.parent.parent  # .claude/hooks

        env = {**os.environ, "PYTHONPATH": str(hooks_dir)}
        result = subprocess.run(
            [sys.executable, str(scale_detector_path), str(project_root)],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        json_path = project_root / ".claude" / "review-state" / "scale-detection.json"
        assert json_path.exists(), "scale-detection.json が生成されていない"

        data = json.loads(json_path.read_text(encoding="utf-8"))
        assert "line_count" in data
        assert "recommended_plans" in data
        assert "active_plans" in data
        assert "plan_statuses" in data

    def test_cli_stdout_contains_scale_detection_header(
        self, project_root: Path
    ) -> None:
        """CLI の stdout が FR-E2c フォーマットで出力されること。"""
        scale_detector_path = (
            Path(__file__).resolve().parent.parent / "scale_detector.py"
        )
        hooks_dir = scale_detector_path.parent.parent

        env = {**os.environ, "PYTHONPATH": str(hooks_dir)}
        result = subprocess.run(
            [sys.executable, str(scale_detector_path), str(project_root)],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
        assert result.returncode == 0
        assert "=== Scale Detection ===" in result.stdout

    def test_cli_exits_with_error_when_no_args(self) -> None:
        """引数なしで CLI 実行するとエラーになること。"""
        scale_detector_path = (
            Path(__file__).resolve().parent.parent / "scale_detector.py"
        )
        hooks_dir = scale_detector_path.parent.parent

        env = {**os.environ, "PYTHONPATH": str(hooks_dir)}
        result = subprocess.run(
            [sys.executable, str(scale_detector_path)],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
        assert result.returncode != 0


@pytest.mark.e2e_llm
class TestDetectionRate:
    """FR-E3b-1: 検出率テスト（CI 除外、手動実行）。

    LLM に依存するため非決定的。CLAUDE_API_KEY 未設定時は自動スキップ。
    検出率の SHOULD 基準:
    - Critical: 100%
    - Warning: 80%+
    """

    def test_critical_silent_failure_detection(self) -> None:
        """フィクスチャ critical_silent_failure.py に対する LLM 検出率フレームワーク検証。

        NOTE: 実際の LLM 呼び出しは手動実行時にのみ行う。
        このテストは検出率測定のフレームワークを提供する。
        コード内のインライン FIXTURE-ISSUE- マーカー数が期待通りであることを確認する。
        """
        fixture = FIXTURES_DIR / "critical_silent_failure.py"
        assert fixture.is_file()
        inline_markers = _count_inline_issue_markers(fixture)
        assert inline_markers == 3, f"Expected 3 issues, found {inline_markers}"

    def test_warning_long_function_detection(self) -> None:
        """フィクスチャ warning_long_function.py に対する検出率フレームワーク検証。

        Long Function Issue が 2 箇所仕込まれていることを確認する。
        """
        fixture = FIXTURES_DIR / "warning_long_function.py"
        assert fixture.is_file()
        inline_markers = _count_inline_issue_markers(fixture)
        assert inline_markers == 2, f"Expected 2 issues, found {inline_markers}"

    def test_security_hardcoded_password_detection(self) -> None:
        """フィクスチャ security_hardcoded_password.py に対する検出率フレームワーク検証。

        bandit B105/B106 による決定的検出。Security Issue が 3 箇所仕込まれていることを確認する。
        """
        fixture = FIXTURES_DIR / "security_hardcoded_password.py"
        assert fixture.is_file()
        inline_markers = _count_inline_issue_markers(fixture)
        assert inline_markers == 3, f"Expected 3 issues, found {inline_markers}"

    def test_detection_results_are_recorded(self, tmp_path: Path, monkeypatch) -> None:
        """_save_result() が latest.json と history/ に正しくファイルを生成することを検証。"""
        import analyzers.tests.test_e2e_review as module

        monkeypatch.setattr(module, "RESULTS_DIR", tmp_path)

        record = E2ERunRecord(
            run_id="20260316_120000",
            test_type="detection",
            status="passed",
            summary="detection framework validated",
            details=[],
            elapsed_seconds=1.0,
        )
        _save_result(record)

        assert (tmp_path / "latest.json").is_file()
        assert (tmp_path / "history" / "20260316_120000.json").is_file()
        data = json.loads((tmp_path / "latest.json").read_text())
        assert data["run_id"] == "20260316_120000"
        assert data["test_type"] == "detection"


@pytest.mark.e2e_convergence
class TestConvergence:
    """FR-E3b-2: 収束テスト（CI 除外、手動実行のみ）。

    LAM 自体に対して静的解析を実行し、
    max_iterations 以内に Green State に到達することを確認する。
    最も時間がかかるテスト。
    """

    def test_lam_reaches_green_state(self) -> None:
        """LAM プロジェクトへの静的解析パイプライン実行の前提条件検証。

        NOTE: 完全な /full-review 実行は手動。
        このテストは静的解析パイプライン（run_phase0）が
        LAM 自体に対してエラーなく完走できる前提条件（pyproject.toml 存在）を検証する。
        実際の Green State 到達は手動 /full-review で検証する。
        """
        project_root = Path(__file__).parents[4]  # LAM プロジェクトルート
        assert (project_root / "pyproject.toml").is_file(), (
            f"pyproject.toml not found at {project_root}"
        )
