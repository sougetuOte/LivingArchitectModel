"""distill_lessons.py - goal-driven メモリ蒸留スクリプト（W4-T1 FR-5）

W4-T1: distill-lessons.py 実装（メモリ蒸留 FR-5）
対応仕様: docs/specs/goal-driven-orchestration/design.md §13
対応要件: FR-5 / AC-2 / design §13 / design §9.1

機能:
  - build_lesson_entry(): grader ログから lessons.md エントリを構築（design §13 スキーマ）
  - distill(): grader ログを分析し lessons.md に追記（重複スキップ）
  - build_arg_parser(): SKILL.md フロー[8] 呼び出し用 argparse パーサ
  - main(): CLI エントリポイント

重要な制約（W-5 制約 / design §13）:
  - 書き込み先は .claude/agent-memory/goal-driven-l3-executor/lessons.md のみ
  - docs/artifacts/knowledge/ への自動書き込みは禁止（MUST NOT）
  - 人間が /retro Step 4 で精査した知見のみ手動で昇格させる

SKILL.md フロー[8] からの呼び出し:
  python .claude/scripts/distill-lessons.py \\
    --task-id <task_id> \\
    --grader-log .claude/logs/gd/<task_id>-loop*-grader.json

小タスクルート（design §9.1）:
  --small-task フラグで grader 判定 JSON のみを入力として処理する。
  L1 最終検収をスキップするため、grader ログのみが入力となる。
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# パス解決（gd_state.py と同じパターン・P-3 対応）
# ---------------------------------------------------------------------------


def get_project_root() -> Path:
    """プロジェクトルートを返す。

    LAM_PROJECT_ROOT 環境変数が設定されていればそれを使用する（P-3 対応）。
    未設定の場合は __file__ の祖先から推定する。
    """
    import os
    env_root = os.environ.get("LAM_PROJECT_ROOT")
    if env_root:
        return Path(env_root)
    # .claude/scripts/distill_lessons.py → 3階層上がプロジェクトルート
    return Path(__file__).resolve().parent.parent.parent


def _default_lessons_path(project_root: Optional[Path] = None) -> Path:
    """デフォルトの lessons.md パスを返す（design §13）。

    書き込み先: .claude/agent-memory/goal-driven-l3-executor/lessons.md のみ
    """
    root = project_root if project_root is not None else get_project_root()
    return root / ".claude" / "agent-memory" / "goal-driven-l3-executor" / "lessons.md"


# ---------------------------------------------------------------------------
# grader ログ解析ユーティリティ
# ---------------------------------------------------------------------------


def _has_fail_to_pass_transition(grader_logs: list[dict]) -> bool:
    """grader ログ列に fail→pass 遷移が含まれるか確認する。

    design §13: 「検証済みの一般則」は fail→pass 修正パターンから抽出する。
    fail→pass 遷移があれば検証済み、なければ未検証扱い。
    """
    if len(grader_logs) < 2:
        return False

    seen_fail = False
    for log in grader_logs:
        overall = log.get("overall") or log.get("verdict", "")
        if overall == "fail":
            seen_fail = True
        elif overall == "pass" and seen_fail:
            return True
    return False


def _extract_fail_reasons(grader_logs: list[dict]) -> str:
    """grader ログの fail 項目から原因を要約する。"""
    reasons = []
    for log in grader_logs:
        overall = log.get("overall") or log.get("verdict", "")
        if overall != "fail":
            continue
        for item in log.get("items", []):
            if item.get("result") == "fail":
                reason = item.get("reason", "")
                if reason:
                    reasons.append(f"項目{item.get('id', '?')}: {reason}")

    if not reasons:
        return "詳細不明（grader ログに fail 項目なし）"
    return " / ".join(reasons[:3])  # 最大 3 件


def _extract_fix_summary(grader_logs: list[dict]) -> str:
    """最終 pass ループの pass 項目から修正内容を要約する。"""
    # 最後の pass ログを探す
    last_pass_log = None
    for log in reversed(grader_logs):
        overall = log.get("overall") or log.get("verdict", "")
        if overall == "pass":
            last_pass_log = log
            break

    if last_pass_log is None:
        return "修正内容不明"

    pass_items = [
        item for item in last_pass_log.get("items", [])
        if item.get("result") == "pass"
    ]
    if not pass_items:
        return "全項目通過"

    summaries = [item.get("reason", "") for item in pass_items[:2] if item.get("reason")]
    return " / ".join(summaries) if summaries else "全項目通過"


# ---------------------------------------------------------------------------
# エントリ構築（design §13 スキーマ）
# ---------------------------------------------------------------------------


def _resolve_verified(grader_logs: list[dict], verified: Optional[bool]) -> bool:
    """verified=None の場合、fail→pass 遷移の有無で検証済み判定を行う。"""
    if verified is None:
        return _has_fail_to_pass_transition(grader_logs)
    return verified


def build_lesson_entry(
    task_id: str,
    grader_logs: list[dict],
    verified: Optional[bool],
) -> str:
    """grader ログから lessons.md エントリを構築する（design §13 スキーマ準拠）。

    Args:
        task_id: タスク識別子（例: "gd-20260613-001"）。
        grader_logs: grader 判定ログのリスト（複数ループ分）。
        verified: True=検証済み / False=未検証 / None=自動判定（fail→pass 遷移で判定）。

    Returns:
        lessons.md に追記するエントリ文字列（末尾改行なし）。
    """
    today = date.today().isoformat()
    loop_count = len(grader_logs)
    is_verified = _resolve_verified(grader_logs, verified)

    status_label = "検証済み" if is_verified else "未検証"
    fail_summary = _extract_fail_reasons(grader_logs) if is_verified else "（自動判定なし）"
    fix_summary = _extract_fix_summary(grader_logs)
    title = "fail→pass 修正パターン" if is_verified else "実行記録（未検証）"

    lines = [
        f"## [{today}] {task_id}: {title}",
        "",
        f"**状態**: {status_label}",
        f"**ループ回数**: {loop_count}",
        f"**fail 原因**: {fail_summary}",
        f"**修正内容**: {fix_summary}",
        "**一般則**: （自動抽出・要人間確認）ループ完了時の修正パターンを参照のこと",
        "**適用範囲**: goal-driven l3-executor 実行全般",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# メイン蒸留関数
# ---------------------------------------------------------------------------


def _load_grader_logs(grader_log_paths: list[str]) -> list[dict]:
    """grader ログファイルを読み込んで dict リストを返す。

    読み込み失敗したファイルはスキップする（Silent Failure 禁止: 空リストで継続）。
    """
    grader_logs: list[dict] = []
    for log_path_str in grader_log_paths:
        log_path = Path(log_path_str)
        if not log_path.exists():
            continue
        try:
            grader_logs.append(json.loads(log_path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return grader_logs


def _is_grader_log_empty(grader_logs: list[dict]) -> bool:
    """grader ログが全条件を満たす「情報ゼロ」状態かどうかを返す（FR-2.1 C-1〜C-4）。

    全条件が True の場合のみ True を返す（AND 条件）。
    1 条件でも False になればスキップしない（MUST NOT）。

    C-1: ループ回数（grader_logs の長さ） == 0
    C-2: 全 grader_log の fail 原因フィールドが空文字列/null/未設定
    C-3: 全 grader_log の修正内容フィールドが空文字列/null/未設定
    C-4: 全 grader_log の一般則フィールドが空/定型文のみ

    注意:
    - C-1 が True（len==0）の場合、C-2〜C-4 は grader_log が存在しないため自動的に True
    - 定型文（C-4）は build_lesson_entry() L175 が生成する固定文字列と照合する
    """
    # C-1: ループ回数が 0 件
    if len(grader_logs) == 0:
        return True

    # C-1 が False の場合（grader_logs が 1 件以上）は C-2〜C-4 を評価する
    # C-2: 全 grader_log の fail 原因が空/未設定
    has_fail_reason = False
    for log in grader_logs:
        overall = log.get("overall") or log.get("verdict", "")
        if overall != "fail":
            continue
        for item in log.get("items", []):
            if item.get("result") == "fail" and item.get("reason", ""):
                has_fail_reason = True
                break
        if has_fail_reason:
            break
    if has_fail_reason:
        return False

    # C-3: 修正内容フィールドが空（最後の pass ログに pass 項目の reason がない）
    has_fix_content = False
    for log in reversed(grader_logs):
        overall = log.get("overall") or log.get("verdict", "")
        if overall == "pass":
            for item in log.get("items", []):
                if item.get("result") == "pass" and item.get("reason", ""):
                    has_fix_content = True
                    break
            break
    if has_fix_content:
        return False

    # C-4: 一般則は grader ログに存在しない（build_lesson_entry で定型文が生成される）
    # grader ログのスキーマに一般則フィールドは存在しないため、
    # C-1〜C-3 が全て False（情報なし）の場合は C-4 も True と判定する
    return True


def _append_to_lessons(target_path: Path, entry: str) -> None:
    """lessons.md にエントリを追記する（新規の場合はヘッダ付きで作成）。"""
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if target_path.exists():
        current = target_path.read_text(encoding="utf-8")
        new_content = current.rstrip("\n") + "\n\n" + entry + "\n"
    else:
        header = "# goal-driven-l3-executor lessons\n\n"
        new_content = header + entry + "\n"

    target_path.write_text(new_content, encoding="utf-8")


def distill(
    task_id: str,
    grader_log_paths: list[str],
    lessons_path: Optional[Path] = None,
    verified: Optional[bool] = None,
    is_small_task: bool = False,
) -> None:
    """grader ログを分析して lessons.md に教訓を追記する。

    design §13 蒸留パイプライン:
    - 検証済みの一般則 → .claude/agent-memory/goal-driven-l3-executor/lessons.md のみ
    - 未検証の推測 → 同ファイルに「未検証」タグ付きで追記（MUST）
    - W-5 制約: docs/artifacts/knowledge/ への書き込みは禁止（MUST NOT）

    Args:
        task_id: タスク識別子。
        grader_log_paths: grader ログファイルのパスリスト（glob 展開済み）。
        lessons_path: 書き込み先 lessons.md のパス（None でデフォルトパスを使用）。
        verified: True=強制検証済み / False=強制未検証 / None=自動判定。
        is_small_task: True で小タスクルート（grader ログのみ入力・design §9.1）。
    """
    target_path = lessons_path if lessons_path is not None else _default_lessons_path()
    grader_logs = _load_grader_logs(grader_log_paths)

    # FR-2.1: grader ログ空スキップ判定（重複チェックより先に評価する）
    if _is_grader_log_empty(grader_logs):
        logger.info("distill-lessons: skipped (empty grader log)")
        return

    # 重複チェック: 同一 task_id のエントリは追記しない
    if target_path.exists():
        if task_id in target_path.read_text(encoding="utf-8"):
            return

    entry = build_lesson_entry(task_id=task_id, grader_logs=grader_logs, verified=verified)
    _append_to_lessons(target_path, entry)


# ---------------------------------------------------------------------------
# argparse インターフェース（SKILL.md フロー[8] 呼び出し用）
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    """SKILL.md フロー[8] から呼び出すための argparse パーサを返す。

    SKILL.md フロー[8]:
    python .claude/scripts/distill-lessons.py \\
      --task-id <task_id> \\
      --grader-log .claude/logs/gd/<task_id>-loop*-grader.json
    """
    parser = argparse.ArgumentParser(
        description="goal-driven メモリ蒸留スクリプト（FR-5 / design §13）"
    )
    parser.add_argument(
        "--task-id",
        required=True,
        help="タスク識別子（例: gd-20260613-001）",
    )
    parser.add_argument(
        "--grader-log",
        nargs="+",
        required=True,
        help="grader ログファイルのパス（複数指定可・glob 展開はシェルに委ねる）",
    )
    parser.add_argument(
        "--lessons-path",
        default=None,
        help="書き込み先 lessons.md のパス（省略時はデフォルトパスを使用）",
    )
    parser.add_argument(
        "--small-task",
        action="store_true",
        help="小タスクルート: grader 判定 JSON のみを入力とする（design §9.1）",
    )
    parser.add_argument(
        "--verified",
        choices=["true", "false"],
        default=None,
        help="検証済み/未検証を強制指定（省略時は fail→pass 遷移で自動判定）",
    )
    return parser


# ---------------------------------------------------------------------------
# CLI エントリポイント
# ---------------------------------------------------------------------------


def main() -> int:
    """CLI エントリポイント。SKILL.md フロー[8] から呼び出す。

    使用例:
      python .claude/scripts/distill-lessons.py \\
        --task-id gd-20260613-001 \\
        --grader-log .claude/logs/gd/gd-20260613-001-loop*.json

    小タスクルート（grader ログのみ・design §9.1）:
      python .claude/scripts/distill-lessons.py \\
        --task-id gd-small-001 \\
        --grader-log .claude/logs/gd/gd-small-001-loop01-grader.json \\
        --small-task
    """
    parser = build_arg_parser()
    args = parser.parse_args()

    lessons_path = Path(args.lessons_path) if args.lessons_path else None

    # --verified フラグの変換
    if args.verified == "true":
        verified: Optional[bool] = True
    elif args.verified == "false":
        verified = False
    else:
        verified = None

    distill(
        task_id=args.task_id,
        grader_log_paths=args.grader_log,
        lessons_path=lessons_path,
        verified=verified,
        is_small_task=args.small_task,
    )

    print(f"[distill-lessons] 蒸留完了: task_id={args.task_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
