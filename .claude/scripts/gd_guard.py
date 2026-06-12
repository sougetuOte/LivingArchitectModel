"""gd_guard.py - goal-driven スキルの排他ガード・残留検知・rubric-tmp 削除

W1-T1: SKILL.md 骨格実装 - ガード系スクリプト
対応仕様: docs/specs/goal-driven-orchestration/design.md §6 / §10
対応要件: FR-4 / AC-7 / AC-10

このスクリプトは SKILL.md から呼び出される。
W2-T2（gd-state.py 本体・bound 累積）は対象外。ガード系のみ実装する。

CLI 使用例:
  python .claude/scripts/gd_guard.py --check-exclusion
  python .claude/scripts/gd_guard.py --check-residual
  python .claude/scripts/gd_guard.py --cleanup-rubric-tmp
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional


def get_project_root() -> Path:
    """プロジェクトルートを返す。

    LAM_PROJECT_ROOT 環境変数が設定されていればそれを使用する（P-3 対応）。
    未設定の場合は __file__ の祖先から推定する。
    """
    env_root = os.environ.get("LAM_PROJECT_ROOT")
    if env_root:
        return Path(env_root)
    # .claude/scripts/gd_guard.py → 3階層上がプロジェクトルート
    return Path(__file__).resolve().parent.parent.parent


def check_exclusion_guard(project_root: Optional[Path] = None) -> Optional[str]:
    """排他ガード: 競合する state ファイルの存在を確認する。

    autonomous-state.json または lam-loop-state.json が存在する場合、
    goal-driven スキルの同時起動を拒否するメッセージを返す。
    競合なしの場合は None を返す。

    design §10: gd-session-state.json は autonomous-state.json および
    lam-loop-state.json と同時実行禁止。

    Args:
        project_root: プロジェクトルートのパス。None の場合は get_project_root() を使用。

    Returns:
        競合がある場合は拒否理由の文字列、ない場合は None。
    """
    if project_root is None:
        project_root = get_project_root()

    claude_dir = project_root / ".claude"
    conflicting = []

    auto_state = claude_dir / "autonomous-state.json"
    if auto_state.exists():
        conflicting.append("autonomous-state.json")

    lam_loop_state = claude_dir / "lam-loop-state.json"
    if lam_loop_state.exists():
        conflicting.append("lam-loop-state.json")

    if not conflicting:
        return None

    files_str = " / ".join(conflicting)
    return (
        f"[goal-driven] 起動拒否: 競合する state ファイルが存在します: {files_str}\n"
        "goal-driven スキルは autonomous / lam-orchestrate と同時実行できません。\n"
        "競合するセッションが終了してから再起動してください。"
    )


def cleanup_rubric_tmp(project_root: Optional[Path] = None) -> None:
    """rubric-tmp.md を削除する。

    小タスクルートの .claude/rubric-tmp.md はタスク終了時
    （合格・エスカレーションを問わず）に削除する（design §6 MUST）。
    ファイルが存在しない場合はエラーなしで完了する。

    docs/tasks/ 配下の rubric.md は削除しない。

    Args:
        project_root: プロジェクトルートのパス。None の場合は get_project_root() を使用。
    """
    if project_root is None:
        project_root = get_project_root()

    rubric_tmp = project_root / ".claude" / "rubric-tmp.md"
    if rubric_tmp.exists():
        rubric_tmp.unlink()


def detect_residual_session(project_root: Optional[Path] = None) -> Optional[dict]:
    """残留セッション検知: gd-session-state.json が status: "running" のまま残留しているか確認。

    design §10: スキル起動時に gd-session-state.json が status: "running" のまま
    存在する場合（前回セッションの異常終了による残留）、自動削除はせず PM に提示し、
    明示承認後に削除して新規開始する（フェイルセーフ）。

    本関数は検知のみを行い、状態ファイルの削除は行わない。

    Args:
        project_root: プロジェクトルートのパス。None の場合は get_project_root() を使用。

    Returns:
        残留セッションがある場合は gd-session-state.json の内容 dict、
        ない場合は None。ファイルが壊れている場合も None（fail-close）。
    """
    if project_root is None:
        project_root = get_project_root()

    state_file = project_root / ".claude" / "gd-session-state.json"
    if not state_file.exists():
        return None

    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # 壊れた state ファイルは fail-close（None を返す）
        return None

    if state.get("status") == "running":
        return state

    return None


def _main() -> int:
    """CLI エントリポイント。SKILL.md から直接呼び出す用途。

    使用例:
      python .claude/scripts/gd_guard.py --check-exclusion   # 排他ガード確認
      python .claude/scripts/gd_guard.py --check-residual    # 残留検知
      python .claude/scripts/gd_guard.py --cleanup-rubric-tmp  # rubric-tmp 削除
    """
    if len(sys.argv) < 2:
        print("使用法: gd_guard.py --check-exclusion | --check-residual | --cleanup-rubric-tmp")
        return 1

    command = sys.argv[1]
    root = get_project_root()

    if command == "--check-exclusion":
        result = check_exclusion_guard(root)
        if result is not None:
            print(result, file=sys.stderr)
            return 1
        print("[goal-driven] 排他ガード: 競合なし。起動可能。")
        return 0

    if command == "--check-residual":
        state = detect_residual_session(root)
        if state is not None:
            task_id = state.get("task_id", "不明")
            print(
                f"[goal-driven] 残留セッション検知: task_id={task_id} が status: running のまま残留しています。\n"
                "自動削除せず PM に提示します。明示承認後に削除して新規開始してください。",
                file=sys.stderr,
            )
            return 2
        print("[goal-driven] 残留セッション: なし。")
        return 0

    if command == "--cleanup-rubric-tmp":
        cleanup_rubric_tmp(root)
        print("[goal-driven] rubric-tmp.md を削除しました（存在しない場合はスキップ）。")
        return 0

    print(f"不明なコマンド: {command}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(_main())
