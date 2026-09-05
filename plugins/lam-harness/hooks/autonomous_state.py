#!/usr/bin/env python3
"""autonomous_state.py - AUTONOMOUS モードの状態スキーマ（design D1）。

autonomous-state.json の初期状態を生成する。状態ファイルは実行時生成・.gitignore
対象であり、lam-loop-state.json（/full-review が使用）とは独立（design D1 の分離理由:
full-review が last-line として内側から起動するネスト競合を避ける）。

MVP（Wave 1）で使用するフィールド:
  active / mode / spec_target / phase / iteration / max_iterations /
  started_at / checker_results / log
後続 Wave 用に空で確保するフィールド:
  pm_queue / pm_queue_limit / se_log / escalation_budget /
  consecutive_clean_runs / tripwire_n / tripwire_level

数値（max_iterations / pm_queue_limit / escalation_budget / tripwire_n）は
すべて状態ファイルに外部化し、ハードコードしない方針（FR-5.5 の観測可能な昇格に対応）。
ここでは既定値のみ定義し、実値は autonomous-state.json が保持する。

対応仕様: docs/specs/autonomous-mode/design.md D1 / tasks.md T1-1 / FR-1.1
"""

from __future__ import annotations

import sys
from pathlib import Path

# sys.path に hooks ディレクトリを追加（_hook_utils を import するため）
_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from _hook_utils import now_utc_iso8601  # noqa: E402

# 既定値（design D1 の暫定値）。実値は autonomous-state.json に外部化する。
DEFAULT_MAX_ITERATIONS = 20
DEFAULT_PM_QUEUE_LIMIT = 5
DEFAULT_MAGI_LIMIT = 3
DEFAULT_FULL_REVIEW_LIMIT = 1
DEFAULT_TRIPWIRE_N = 3


def state_file_path(project_root: Path) -> Path:
    """autonomous-state.json のパスを返す（lam-loop-state.json と独立: design D1）。"""
    return project_root / ".claude" / "autonomous-state.json"


def build_initial_state(
    spec_target: str,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    started_at: str | None = None,
) -> dict:
    """AUTONOMOUS モードの初期状態を生成する（design D1 スキーマ）。

    Args:
        spec_target: 対象 spec のパス（例: docs/specs/<target>/requirements.md）
        max_iterations: 無限ループ防止の上限。到達で active=false 停止（既定 20）
        started_at: ISO 8601 開始時刻。None なら現在時刻（UTC・Z 終端）で補完

    Returns:
        design D1 のスキーマに文字単位で一致する dict。
        起動時は active=True / phase="building"（起動承認後 Building へ）。
    """
    return {
        "active": True,
        "mode": "autonomous",
        "spec_target": spec_target,
        "phase": "building",
        "iteration": 0,
        "max_iterations": max_iterations,
        "started_at": started_at if started_at is not None else now_utc_iso8601(),
        "checker_results": {
            "g1_exit": None,
            "g2_exit": None,
            "g5_exit": None,
            "checked_at": None,
        },
        "pm_queue": [],
        "pm_queue_limit": DEFAULT_PM_QUEUE_LIMIT,
        "se_log": [],
        "escalation_budget": {
            "magi_count": 0,
            "magi_limit": DEFAULT_MAGI_LIMIT,
            "full_review_count": 0,
            "full_review_limit": DEFAULT_FULL_REVIEW_LIMIT,
        },
        "consecutive_clean_runs": 0,
        "tripwire_n": DEFAULT_TRIPWIRE_N,
        "tripwire_level": 0,
        "log": [],
    }
