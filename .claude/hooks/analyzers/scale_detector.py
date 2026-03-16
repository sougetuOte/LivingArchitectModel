"""Scalable Code Review Phase E: スケール判定モジュール

Task E-2a/E-2b: scale_detector.py データモデル + 判定ロジック + 前提条件チェック
対応仕様: scalable-code-review-phase5-spec.md FR-E2a, FR-E2b, FR-E2c, FR-E2d
対応設計: scalable-code-review-design.md Section 6.3
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

from analyzers.config import ReviewConfig
from analyzers.run_pipeline import count_lines

# 閾値テーブル: (最小行数, 推奨 Plan リスト)
# 降順に並んでいる。最初に条件を満たした行を採用する。
_PLAN_THRESHOLDS: list[tuple[int, list[str]]] = [
    (300_000, ["A", "B", "C", "D"]),
    (100_000, ["A", "B", "C"]),
    (30_000, ["A", "B"]),
    (10_000, ["A"]),
    (0, []),
]

_ALL_PLANS: list[str] = ["A", "B", "C", "D"]


@dataclass
class PlanStatus:
    """個別 Plan の判定結果。"""

    enabled: bool       # 行数閾値から有効化すべきか
    available: bool     # 前提条件が充足されているか
    reason: str         # 表示用メッセージ


@dataclass
class ScaleDetectionResult:
    """Scale Detection の判定結果全体。"""

    line_count: int
    recommended_plans: list[str]            # 閾値テーブルからの推奨
    active_plans: list[str]                 # enabled=True かつ available=True
    plan_statuses: dict[str, PlanStatus] = field(default_factory=dict)


def _determine_recommended_plans(line_count: int) -> list[str]:
    """行数から推奨 Plan リストを決定する。

    _PLAN_THRESHOLDS の末尾 (0, []) により line_count >= 0 で必ずマッチする。
    末尾の return は負値への防御（count_lines は非負を返すが型安全のため残置）。
    """
    for threshold, plans in _PLAN_THRESHOLDS:
        if line_count >= threshold:
            return plans
    return []  # pragma: no cover — 防御的コード


def _check_plan_a() -> PlanStatus:
    """Plan A: ruff + bandit がインストール済みか確認する。"""
    missing = [tool for tool in ["ruff", "bandit"] if not shutil.which(tool)]
    if missing:
        return PlanStatus(
            enabled=True,
            available=False,
            reason=f"{', '.join(missing)}: not installed",
        )
    return PlanStatus(
        enabled=True,
        available=True,
        reason="ruff: installed, bandit: installed",
    )


def _check_plan_b() -> PlanStatus:
    """Plan B: tree-sitter パッケージが見つかるか確認する。"""
    if importlib.util.find_spec("tree_sitter") is None:
        return PlanStatus(
            enabled=True,
            available=False,
            reason="tree-sitter: not installed",
        )
    return PlanStatus(
        enabled=True,
        available=True,
        reason="tree-sitter: installed",
    )


def _check_plan_c(plan_b: PlanStatus) -> PlanStatus:
    """Plan C: Plan B が available なら auto で有効化する。"""
    if plan_b.available:
        return PlanStatus(enabled=True, available=True, reason="auto")
    return PlanStatus(
        enabled=True,
        available=False,
        reason="requires Plan B (tree-sitter)",
    )


def _check_plan_d(project_root: Path) -> PlanStatus:
    """Plan D: import-map.json が存在するか確認する。"""
    import_map = project_root / ".claude" / "review-state" / "import-map.json"
    if not import_map.exists():
        return PlanStatus(
            enabled=True,
            available=False,
            reason="import-map.json not found — skipping topological ordering",
        )
    return PlanStatus(
        enabled=True,
        available=True,
        reason="import-map.json: found",
    )


def _build_plan_status(
    plan: str,
    recommended_plans: list[str],
    project_root: Path,
    plan_b_status: PlanStatus | None = None,
) -> PlanStatus:
    """Plan の有効化・前提条件チェックを行い PlanStatus を返す。"""
    if plan not in recommended_plans:
        return PlanStatus(enabled=False, available=False, reason="not recommended")

    if plan == "A":
        return _check_plan_a()
    if plan == "B":
        return _check_plan_b()
    if plan == "C":
        b_status = plan_b_status if plan_b_status is not None else _check_plan_b()
        return _check_plan_c(b_status)
    if plan == "D":
        return _check_plan_d(project_root)

    return PlanStatus(enabled=True, available=True, reason="available")


def detect_scale(
    project_root: Path,
    config: ReviewConfig | None = None,
) -> ScaleDetectionResult:
    """プロジェクト規模を検出し、有効化する Plan を判定する。

    1. count_lines() で行数をカウント
    2. 閾値テーブルで推奨 Plan セットを決定
    3. 各 Plan の前提条件をチェック（shutil.which / importlib.util.find_spec 等）
    4. active_plans = enabled かつ available な Plan
    """
    if config is None:
        config = ReviewConfig.load(project_root)

    line_count = count_lines(project_root, config.exclude_dirs)
    recommended_plans = _determine_recommended_plans(line_count)

    # Plan B の結果を Plan C に渡すため、B を先に評価する
    plan_b_status = _build_plan_status("B", recommended_plans, project_root)

    plan_statuses: dict[str, PlanStatus] = {}
    for plan in _ALL_PLANS:
        if plan == "B":
            plan_statuses[plan] = plan_b_status
        elif plan == "C":
            plan_statuses[plan] = _build_plan_status(
                plan, recommended_plans, project_root, plan_b_status=plan_b_status
            )
        else:
            plan_statuses[plan] = _build_plan_status(
                plan, recommended_plans, project_root
            )

    active_plans = [
        plan
        for plan in recommended_plans
        if plan_statuses[plan].available
    ]

    return ScaleDetectionResult(
        line_count=line_count,
        recommended_plans=recommended_plans,
        active_plans=active_plans,
        plan_statuses=plan_statuses,
    )


def _format_recommended(recommended_plans: list[str]) -> str:
    """推奨 Plan を "Plan A + B + C" 形式に変換する。"""
    if not recommended_plans:
        return "None"
    return "Plan " + " + ".join(recommended_plans)


def _format_plan_line(plan: str, status: PlanStatus) -> str:
    """Plan 1 行分の表示文字列を生成する。"""
    mark = "\u2713" if status.available else "\u2717"
    return f"  Plan {plan}: {mark} ({status.reason})"


def format_scale_detection(result: ScaleDetectionResult) -> str:
    """FR-E2c 準拠のフォーマット済み出力を生成する。

    出力例:
    === Scale Detection ===
    Lines: 45,230
    Recommended: Plan A + B + C
    Active Plans:
      Plan A: ✓ (ruff: installed, bandit: installed)
      Plan B: ✓ (tree-sitter: installed)
      Plan C: ✓ (auto)
      Plan D: ✗ (import-map.json not found — skipping topological ordering)
    """
    lines = [
        "=== Scale Detection ===",
        f"Lines: {result.line_count:,}",
        f"Recommended: {_format_recommended(result.recommended_plans)}",
        "Active Plans:",
    ]

    for plan in _ALL_PLANS:
        status = result.plan_statuses.get(plan)
        if status is not None:
            lines.append(_format_plan_line(plan, status))

    return "\n".join(lines)


def _result_to_dict(result: ScaleDetectionResult) -> dict:
    """ScaleDetectionResult を JSON シリアライズ可能な dict に変換する。"""
    return {
        "line_count": result.line_count,
        "recommended_plans": result.recommended_plans,
        "active_plans": result.active_plans,
        "plan_statuses": {
            plan: {
                "enabled": status.enabled,
                "available": status.available,
                "reason": status.reason,
            }
            for plan, status in result.plan_statuses.items()
        },
    }


def _persist_result(project_root: Path, result: ScaleDetectionResult) -> Path:
    """判定結果を .claude/review-state/scale-detection.json に永続化する。"""
    state_dir = project_root / ".claude" / "review-state"
    state_dir.mkdir(parents=True, exist_ok=True)
    output_path = state_dir / "scale-detection.json"
    output_path.write_text(
        json.dumps(_result_to_dict(result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: scale_detector.py <project_root>", file=sys.stderr)
        sys.exit(1)

    root = Path(sys.argv[1]).resolve()
    if not root.is_dir():
        print(f"Error: not a directory: {root}", file=sys.stderr)
        sys.exit(1)
    detection_result = detect_scale(root)
    print(format_scale_detection(detection_result))
    _persist_result(root, detection_result)
