"""scale_detector のテスト（監査 B4: 全関数カバレッジ）。

対象: .claude/hooks/analyzers/scale_detector.py
対応仕様: scalable-code-review-phase5-spec.md FR-E2a〜FR-E2d
対応設計: scalable-code-review-design.md Section 6.3

環境依存（shutil.which / importlib.util.find_spec / count_lines）は monkeypatch で
決定化し、判定ロジックと表示・永続化を網羅する。
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from analyzers import scale_detector
from analyzers.scale_detector import (
    PlanStatus,
    ScaleDetectionResult,
    _build_plan_status,
    _check_plan_a,
    _check_plan_b,
    _check_plan_c,
    _check_plan_d,
    _determine_recommended_plans,
    _format_plan_line,
    _format_recommended,
    _persist_result,
    _result_to_dict,
    detect_scale,
    format_scale_detection,
)


# ---------------------------------------------------------------------------
# _determine_recommended_plans: 閾値テーブルの境界
# ---------------------------------------------------------------------------


class TestDetermineRecommendedPlans:
    @pytest.mark.parametrize(
        ("line_count", "expected"),
        [
            (0, []),
            (9_999, []),
            (10_000, ["A"]),            # 10K 境界（下限ちょうど）
            (29_999, ["A"]),
            (30_000, ["A", "B"]),       # 30K 境界
            (99_999, ["A", "B"]),
            (100_000, ["A", "B", "C"]),  # 100K 境界
            (299_999, ["A", "B", "C"]),
            (300_000, ["A", "B", "C", "D"]),  # 300K 境界
            (1_000_000, ["A", "B", "C", "D"]),
        ],
    )
    def test_thresholds(self, line_count: int, expected: list[str]) -> None:
        assert _determine_recommended_plans(line_count) == expected


# ---------------------------------------------------------------------------
# 各 Plan の前提条件チェック
# ---------------------------------------------------------------------------


class TestCheckPlanA:
    def test_all_tools_installed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(scale_detector.shutil, "which", lambda tool: f"/usr/bin/{tool}")
        status = _check_plan_a()
        assert status.enabled is True
        assert status.available is True

    def test_one_tool_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # bandit のみ未インストール
        monkeypatch.setattr(
            scale_detector.shutil,
            "which",
            lambda tool: "/usr/bin/ruff" if tool == "ruff" else None,
        )
        status = _check_plan_a()
        assert status.enabled is True
        assert status.available is False
        assert "bandit" in status.reason

    def test_all_tools_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(scale_detector.shutil, "which", lambda tool: None)
        status = _check_plan_a()
        assert status.available is False
        assert "ruff" in status.reason and "bandit" in status.reason


class TestCheckPlanB:
    def test_tree_sitter_installed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("importlib.util.find_spec", lambda name: object())
        status = _check_plan_b()
        assert status.available is True

    def test_tree_sitter_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("importlib.util.find_spec", lambda name: None)
        status = _check_plan_b()
        assert status.available is False
        assert "tree-sitter" in status.reason


class TestCheckPlanC:
    def test_enabled_when_plan_b_available(self) -> None:
        plan_b = PlanStatus(enabled=True, available=True, reason="tree-sitter: installed")
        status = _check_plan_c(plan_b)
        assert status.available is True
        assert status.reason == "auto"

    def test_disabled_when_plan_b_unavailable(self) -> None:
        plan_b = PlanStatus(enabled=True, available=False, reason="tree-sitter: not installed")
        status = _check_plan_c(plan_b)
        assert status.available is False
        assert "Plan B" in status.reason


class TestCheckPlanD:
    def test_import_map_found(self, tmp_path: Path) -> None:
        review_state = tmp_path / ".claude" / "review-state"
        review_state.mkdir(parents=True)
        (review_state / "import-map.json").write_text("{}", encoding="utf-8")
        status = _check_plan_d(tmp_path)
        assert status.available is True

    def test_import_map_missing(self, tmp_path: Path) -> None:
        status = _check_plan_d(tmp_path)
        assert status.available is False
        assert "import-map.json" in status.reason


# ---------------------------------------------------------------------------
# _build_plan_status: ディスパッチ
# ---------------------------------------------------------------------------


class TestBuildPlanStatus:
    def test_not_recommended(self, tmp_path: Path) -> None:
        status = _build_plan_status("D", recommended_plans=["A"], project_root=tmp_path)
        assert status.enabled is False
        assert status.available is False
        assert status.reason == "not recommended"

    def test_dispatches_to_plan_a(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(scale_detector.shutil, "which", lambda tool: f"/x/{tool}")
        status = _build_plan_status("A", recommended_plans=["A"], project_root=tmp_path)
        assert status.available is True

    def test_plan_c_reuses_given_plan_b_status(self, tmp_path: Path) -> None:
        plan_b = PlanStatus(enabled=True, available=True, reason="tree-sitter: installed")
        status = _build_plan_status(
            "C", recommended_plans=["A", "B", "C"], project_root=tmp_path,
            plan_b_status=plan_b,
        )
        assert status.available is True
        assert status.reason == "auto"


# ---------------------------------------------------------------------------
# detect_scale: 統合（count_lines / ツール有無を決定化）
# ---------------------------------------------------------------------------


def _patch_env(
    monkeypatch: pytest.MonkeyPatch,
    *,
    line_count: int,
    plan_a_ok: bool,
    tree_sitter_ok: bool,
) -> None:
    monkeypatch.setattr(scale_detector, "count_lines", lambda root, exclude: line_count)
    monkeypatch.setattr(
        scale_detector.shutil,
        "which",
        lambda tool: f"/x/{tool}" if plan_a_ok else None,
    )
    monkeypatch.setattr(
        "importlib.util.find_spec",
        lambda name: object() if tree_sitter_ok else None,
    )


class TestDetectScale:
    def test_small_project_no_plans(
        self, project_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_env(monkeypatch, line_count=5_000, plan_a_ok=True, tree_sitter_ok=True)
        result = detect_scale(project_root)
        assert result.line_count == 5_000
        assert result.recommended_plans == []
        assert result.active_plans == []

    def test_medium_project_plan_a_b_active(
        self, project_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_env(monkeypatch, line_count=50_000, plan_a_ok=True, tree_sitter_ok=True)
        result = detect_scale(project_root)
        assert result.recommended_plans == ["A", "B"]
        assert result.active_plans == ["A", "B"]

    def test_recommended_but_unavailable_excluded_from_active(
        self, project_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # 100K 推奨 [A,B,C] だが tree-sitter 欠如 → B/C は available=False
        _patch_env(monkeypatch, line_count=100_000, plan_a_ok=True, tree_sitter_ok=False)
        result = detect_scale(project_root)
        assert result.recommended_plans == ["A", "B", "C"]
        assert result.active_plans == ["A"]  # B/C は前提条件未充足で除外
        assert result.plan_statuses["B"].available is False
        assert result.plan_statuses["C"].available is False

    def test_loads_default_config_when_none(
        self, project_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """config=None の経路（ReviewConfig.load）を通る。"""
        _patch_env(monkeypatch, line_count=10_000, plan_a_ok=True, tree_sitter_ok=True)
        result = detect_scale(project_root, config=None)
        assert result.recommended_plans == ["A"]


# ---------------------------------------------------------------------------
# 表示・シリアライズ・永続化
# ---------------------------------------------------------------------------


class TestFormatting:
    def test_format_recommended_empty(self) -> None:
        assert _format_recommended([]) == "None"

    def test_format_recommended_list(self) -> None:
        assert _format_recommended(["A", "B", "C"]) == "Plan A + B + C"

    def test_format_plan_line_available(self) -> None:
        status = PlanStatus(enabled=True, available=True, reason="ok")
        line = _format_plan_line("A", status)
        assert "Plan A" in line and "✓" in line and "ok" in line

    def test_format_plan_line_unavailable(self) -> None:
        status = PlanStatus(enabled=True, available=False, reason="missing")
        line = _format_plan_line("D", status)
        assert "Plan D" in line and "✗" in line

    def test_format_scale_detection_full(self) -> None:
        result = ScaleDetectionResult(
            line_count=45_230,
            recommended_plans=["A", "B", "C"],
            active_plans=["A", "B", "C"],
            plan_statuses={
                "A": PlanStatus(True, True, "ruff: installed, bandit: installed"),
                "B": PlanStatus(True, True, "tree-sitter: installed"),
                "C": PlanStatus(True, True, "auto"),
                "D": PlanStatus(True, False, "import-map.json not found"),
            },
        )
        text = format_scale_detection(result)
        assert "=== Scale Detection ===" in text
        assert "Lines: 45,230" in text          # 桁区切り
        assert "Recommended: Plan A + B + C" in text
        assert "Active Plans:" in text
        # 4 Plan すべての行が出る
        for plan in ("Plan A", "Plan B", "Plan C", "Plan D"):
            assert plan in text


class TestResultToDict:
    def test_structure(self) -> None:
        result = ScaleDetectionResult(
            line_count=12_345,
            recommended_plans=["A"],
            active_plans=["A"],
            plan_statuses={"A": PlanStatus(True, True, "ok")},
        )
        d = _result_to_dict(result)
        assert d["line_count"] == 12_345
        assert d["recommended_plans"] == ["A"]
        assert d["active_plans"] == ["A"]
        assert d["plan_statuses"]["A"] == {
            "enabled": True,
            "available": True,
            "reason": "ok",
        }
        # JSON シリアライズ可能であること
        json.dumps(d)


class TestPersistResult:
    def test_writes_scale_detection_json(self, project_root: Path) -> None:
        result = ScaleDetectionResult(
            line_count=100,
            recommended_plans=[],
            active_plans=[],
            plan_statuses={},
        )
        out = _persist_result(project_root, result)
        assert out == project_root / ".claude" / "review-state" / "scale-detection.json"
        assert out.is_file()
        loaded = json.loads(out.read_text(encoding="utf-8"))
        assert loaded["line_count"] == 100

    def test_creates_review_state_dir_if_missing(self, tmp_path: Path) -> None:
        # .claude/review-state が無くても mkdir される
        result = ScaleDetectionResult(0, [], [], {})
        out = _persist_result(tmp_path, result)
        assert out.parent.is_dir()


# ---------------------------------------------------------------------------
# W-12: state_dir パス不整合バグの回帰テスト
# ---------------------------------------------------------------------------


from analyzers.scale_detector import _find_project_root  # noqa: E402


class TestFindProjectRoot:
    """_find_project_root() のテスト。"""

    def test_returns_root_when_git_at_path(self, tmp_path: Path) -> None:
        """ターゲット自体に .git がある場合、そのパスを返す。"""
        (tmp_path / ".git").mkdir()
        result = _find_project_root(tmp_path)
        assert result == tmp_path

    def test_returns_root_from_subdir(self, tmp_path: Path) -> None:
        """サブディレクトリをターゲットにしても祖先の .git を見つける。"""
        (tmp_path / ".git").mkdir()
        subdir = tmp_path / ".claude" / "hooks"
        subdir.mkdir(parents=True)
        result = _find_project_root(subdir)
        assert result == tmp_path

    def test_fallback_when_no_git(self, tmp_path: Path) -> None:
        """.git が見つからない場合はターゲット自身を返す（フォールバック）。"""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        result = _find_project_root(subdir)
        assert result == subdir


class TestMainBlockPersistToProjectRoot:
    """__main__ 相当の永続化経路が正しいプロジェクトルートに書き込むことを検証する。

    バグ再現: ターゲットが <project>/.claude/hooks のとき、
    旧実装では <project>/.claude/hooks/.claude/review-state/ に書き込んでいた。
    修正後はプロジェクトルート（.git がある祖先）側に書き込まれるべき。
    """

    def test_persist_uses_project_root_not_subdir_target(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # プロジェクトルート（.git あり）とサブディレクトリターゲットを構成
        project_root = tmp_path / "myproject"
        project_root.mkdir()
        (project_root / ".git").mkdir()

        subdir_target = project_root / ".claude" / "hooks"
        subdir_target.mkdir(parents=True)

        # detect_scale の外部依存を決定化
        monkeypatch.setattr(scale_detector, "count_lines", lambda root, exclude: 1_000)
        monkeypatch.setattr(scale_detector.shutil, "which", lambda tool: f"/x/{tool}")
        monkeypatch.setattr("importlib.util.find_spec", lambda name: object())

        # __main__ と同じ経路: ターゲット（サブディレクトリ）で detect_scale → _persist_result
        detection_result = detect_scale(subdir_target)
        resolved_root = _find_project_root(subdir_target)
        out = _persist_result(resolved_root, detection_result)

        # ジャンクパス（<subdir>/.claude/review-state/）ではなく
        # プロジェクトルートに書き込まれること
        expected = project_root / ".claude" / "review-state" / "scale-detection.json"
        assert out == expected, (
            f"期待: {expected}\n実際: {out}\n"
            "サブディレクトリをターゲットにしたとき、永続化先がプロジェクトルート基準でなかった"
        )

        # ジャンクディレクトリが生成されていないこと
        junk_dir = subdir_target / ".claude" / "review-state"
        assert not junk_dir.exists(), f"ジャンクディレクトリが生成された: {junk_dir}"
