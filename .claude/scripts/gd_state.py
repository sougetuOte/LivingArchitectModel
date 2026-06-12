"""gd_state.py - goal-driven セッション状態管理・第一防衛線（spawn-time enforcement）

W2-T2: bound スクリプト第一防衛線実装
対応仕様: docs/specs/goal-driven-orchestration/design.md §10
対応要件: FR-4 / AC-8 / AC-9
対応設定: docs/specs/goal-driven-orchestration/config.md §5

機能:
  - gd-session-state.json の読み書き（get_project_root() によるパス解決・P-3 対応）
  - 各 Agent 呼び出し後の tokens_used 累積処理
  - 次の spawn 前の残予算チェック（spawn-time enforcement）
  - bound 超過時の status="escalated" 更新とエスカレーション報告出力
  - 並列起動チェック（並列グループのサブ予算合計が残予算以下か確認）
  - distill-lessons.py 向けメモリ蒸留 hook 点

CLI 使用例（SKILL.md から呼び出す場合）:
  python .claude/scripts/gd_state.py --init --task-id gd-20260613-001 \\
      --task-slug my-task --route medium
  python .claude/scripts/gd_state.py --accumulate 5000
  python .claude/scripts/gd_state.py --check-spawn-budget
  python .claude/scripts/gd_state.py --check-loop-bound
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# パス解決（P-3 対応）
# ---------------------------------------------------------------------------


def get_project_root() -> Path:
    """プロジェクトルートを返す。

    LAM_PROJECT_ROOT 環境変数が設定されていればそれを使用する（P-3 対応）。
    サブエージェント内で cwd が変動しても、この関数でパスが安定して解決される。
    未設定の場合は __file__ の祖先から推定する。
    """
    env_root = os.environ.get("LAM_PROJECT_ROOT")
    if env_root:
        return Path(env_root)
    # .claude/scripts/gd_state.py → 3階層上がプロジェクトルート
    return Path(__file__).resolve().parent.parent.parent


def _state_path(project_root: Optional[Path]) -> Path:
    """gd-session-state.json の絶対パスを返す。

    project_root が None の場合は get_project_root() で解決する（P-3 対応）。
    """
    root = project_root if project_root is not None else get_project_root()
    return root / ".claude" / "gd-session-state.json"


# ---------------------------------------------------------------------------
# ルート別初期値（config.md §2）
# ---------------------------------------------------------------------------


_ROUTE_TOKEN_BOUNDS: dict[str, int] = {
    "small": 50_000,
    "medium": 150_000,
    "large": 400_000,
}

_ROUTE_TIME_BOUNDS: dict[str, int] = {
    "small": 3600,
    "medium": 3600,
    "large": 7200,
}

_DEFAULT_MAX_LOOP_COUNT: int = 3
_DEFAULT_NEST_DEPTH_LIMIT: int = 5


# ---------------------------------------------------------------------------
# 読み書き（完了条件 1）
# ---------------------------------------------------------------------------


def read_state(project_root: Optional[Path] = None) -> dict:
    """gd-session-state.json を読み取って dict を返す。

    ファイルが存在しない場合は FileNotFoundError を送出する。
    JSON が壊れている場合は json.JSONDecodeError を送出する（握りつぶさない）。

    Args:
        project_root: プロジェクトルートのパス。None の場合は get_project_root() を使用。

    Returns:
        gd-session-state.json の内容を dict として返す。

    Raises:
        FileNotFoundError: gd-session-state.json が存在しない場合。
        json.JSONDecodeError: JSON が不正な場合。
    """
    path = _state_path(project_root)
    if not path.exists():
        raise FileNotFoundError(
            f"gd-session-state.json が見つかりません: {path}\n"
            "initialize_state() でセッションを初期化してください。"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def write_state(project_root: Optional[Path], state: dict) -> None:
    """gd-session-state.json に state を書き込む。

    Args:
        project_root: プロジェクトルートのパス。None の場合は get_project_root() を使用。
        state: 書き込む状態 dict。
    """
    path = _state_path(project_root)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def initialize_state(
    task_id: str,
    task_slug: str,
    route: str,
    project_root: Optional[Path] = None,
    nest_depth_limit: int = _DEFAULT_NEST_DEPTH_LIMIT,
    max_loop_count: int = _DEFAULT_MAX_LOOP_COUNT,
    global_token_bound: Optional[int] = None,
    global_time_bound: Optional[int] = None,
) -> dict:
    """gd-session-state.json を初期状態で生成する。

    config.md §5 完全スキーマに準拠した状態ファイルを作成する。
    ルート別のデフォルト bound 値を設定し、外部化パラメータが渡された場合はそれを優先する。

    Args:
        task_id: タスク識別子（例: "gd-20260613-001"）。
        task_slug: タスクのスラッグ（docs/tasks/<slug>/ に対応）。
        route: ルート種別。"small" / "medium" / "large" のいずれか。
        project_root: プロジェクトルートのパス。None の場合は get_project_root() を使用。
        nest_depth_limit: ネスト深さ上限（NFR-5 外部化）。
        max_loop_count: grader 差し戻し回数上限（NFR-5 外部化）。
        global_token_bound: グローバルトークン bound。None でルート別デフォルト値を使用。
        global_time_bound: グローバル時間 bound（秒）。None でルート別デフォルト値を使用。

    Returns:
        作成した state dict。
    """
    if route not in _ROUTE_TOKEN_BOUNDS:
        raise ValueError(
            f"不正なルート: {route!r}。'small' / 'medium' / 'large' のいずれかを指定してください。"
        )

    state: dict = {
        "task_id": task_id,
        "task_slug": task_slug,
        "route": route,
        "nest_depth_limit": nest_depth_limit,
        "global_token_bound": (
            global_token_bound
            if global_token_bound is not None
            else _ROUTE_TOKEN_BOUNDS[route]
        ),
        "global_time_bound": (
            global_time_bound
            if global_time_bound is not None
            else _ROUTE_TIME_BOUNDS[route]
        ),
        "total_tokens": 0,
        "loop_count": 0,
        "max_loop_count": max_loop_count,
        "start_time": time.time(),
        "status": "running",
        "fallback": None,
    }

    write_state(project_root, state)
    return state


# ---------------------------------------------------------------------------
# tokens_used 累積処理（完了条件 2）
# ---------------------------------------------------------------------------


def accumulate_tokens(tokens_used: int, project_root: Optional[Path] = None) -> dict:
    """各 Agent 呼び出し後に tokens_used を total_tokens に累積する。

    config.md §5: total_tokens はグローバル bound 判定の正規フィールド。
    各 Agent 呼び出し後に更新（MUST）。

    Args:
        tokens_used: 今回の Agent 呼び出しで使用したトークン数。
        project_root: プロジェクトルートのパス。None の場合は get_project_root() を使用。

    Returns:
        更新後の state dict。
    """
    state = read_state(project_root)
    state["total_tokens"] = state.get("total_tokens", 0) + tokens_used
    write_state(project_root, state)
    return state


# ---------------------------------------------------------------------------
# spawn 前残予算チェック（完了条件 3・4・AC-8）
# ---------------------------------------------------------------------------


def check_spawn_budget(project_root: Optional[Path] = None) -> str:
    """次の spawn 前に残予算チェックを実施する（spawn-time enforcement）。

    design §10 bound 機構（OR 条件）:
    - total_tokens >= global_token_bound → エスカレーション
    - 経過時間 >= global_time_bound → エスカレーション
    いずれか早く到達した方で打ち切る（OR セマンティクス）。

    bound 超過時は status を "escalated" に更新する（design §10 エスカレーション経路）。

    Args:
        project_root: プロジェクトルートのパス。None の場合は get_project_root() を使用。

    Returns:
        "ok": spawn 許可。
        "escalate": bound 超過によりエスカレーション経路へ進む。
    """
    state = read_state(project_root)

    total_tokens = state.get("total_tokens", 0)
    global_token_bound = state.get("global_token_bound", 200_000)
    start_time = state.get("start_time", time.time())
    global_time_bound = state.get("global_time_bound", 3600)
    elapsed_s = time.time() - start_time

    if total_tokens >= global_token_bound or elapsed_s >= global_time_bound:
        state["status"] = "escalated"
        write_state(project_root, state)
        return "escalate"

    return "ok"


# ---------------------------------------------------------------------------
# エスカレーション報告（完了条件 4）
# ---------------------------------------------------------------------------


def build_escalation_report(reason: str, project_root: Optional[Path] = None) -> str:
    """エスカレーション報告文字列を生成する。

    design §10 エスカレーション経路:
    L1 コンテキストが構造化報告の unresolved リストを PM に提示して終了。

    Args:
        reason: エスカレーション理由（例: "token_bound_exceeded" / "max_loop_count_reached"）。
        project_root: プロジェクトルートのパス。None の場合は get_project_root() を使用。

    Returns:
        PM に提示するエスカレーション報告文字列。
    """
    state = read_state(project_root)

    task_id = state.get("task_id", "不明")
    task_slug = state.get("task_slug", "不明")
    total_tokens = state.get("total_tokens", 0)
    global_token_bound = state.get("global_token_bound", 0)
    loop_count = state.get("loop_count", 0)
    max_loop_count = state.get("max_loop_count", 0)
    route = state.get("route", "不明")

    lines = [
        "[goal-driven] エスカレーション報告",
        f"  task_id    : {task_id}",
        f"  task_slug  : {task_slug}",
        f"  route      : {route}",
        f"  reason     : {reason}",
        f"  total_tokens: {total_tokens} / {global_token_bound}",
        f"  loop_count : {loop_count} / {max_loop_count}",
        "PM による確認・判断が必要です。gd-session-state.json を参照してください。",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# loop_count 管理・loop_bound チェック（完了条件 4・AC-9）
# ---------------------------------------------------------------------------


def check_loop_bound(project_root: Optional[Path] = None) -> str:
    """loop_count が max_loop_count 以上か確認する（AC-9 対応）。

    tasks.md W2-T2 AC-9:
    loop_count == max_loop_count の状態ファイルでエスカレーション経路に到達すること。

    Args:
        project_root: プロジェクトルートのパス。None の場合は get_project_root() を使用。

    Returns:
        "ok": ループ継続可能。
        "escalate": loop_count が max_loop_count に到達したためエスカレーション。
    """
    state = read_state(project_root)

    loop_count = state.get("loop_count", 0)
    max_loop_count = state.get("max_loop_count", _DEFAULT_MAX_LOOP_COUNT)

    if loop_count >= max_loop_count:
        return "escalate"

    return "ok"


def increment_loop_count(project_root: Optional[Path] = None) -> dict:
    """loop_count を 1 増やして state を更新する。

    grader が "fail" を返したとき（差し戻し時）に呼び出す。

    Args:
        project_root: プロジェクトルートのパス。None の場合は get_project_root() を使用。

    Returns:
        更新後の state dict。
    """
    state = read_state(project_root)
    state["loop_count"] = state.get("loop_count", 0) + 1
    write_state(project_root, state)
    return state


# ---------------------------------------------------------------------------
# status・fallback 更新（完了条件 4）
# ---------------------------------------------------------------------------


def set_status(new_status: str, project_root: Optional[Path] = None) -> dict:
    """gd-session-state.json の status フィールドを更新する。

    取りうる値: "running" / "escalated" / "completed"（config.md §5 status フィールド定義）

    Args:
        new_status: 新しい status 値。
        project_root: プロジェクトルートのパス。None の場合は get_project_root() を使用。

    Returns:
        更新後の state dict。
    """
    valid_statuses = {"running", "escalated", "completed"}
    if new_status not in valid_statuses:
        raise ValueError(
            f"不正な status: {new_status!r}。"
            f"取りうる値: {valid_statuses}"
        )

    state = read_state(project_root)
    state["status"] = new_status
    write_state(project_root, state)
    return state


def set_fallback(fallback_mode: str, project_root: Optional[Path] = None) -> dict:
    """gd-session-state.json の fallback フィールドを更新する。

    SKILL.md [4]: 大タスクルートでネスト失敗時に fallback: "two_layer" をセット。
    design §11b: 三層→二層退避のフォールバック記録。

    Args:
        fallback_mode: フォールバックモード。現時点の有効値は "two_layer"。
        project_root: プロジェクトルートのパス。None の場合は get_project_root() を使用。

    Returns:
        更新後の state dict。
    """
    state = read_state(project_root)
    state["fallback"] = fallback_mode
    write_state(project_root, state)
    return state


# ---------------------------------------------------------------------------
# 並列起動チェック（完了条件 7）
# ---------------------------------------------------------------------------


def check_parallel_spawn_budget(
    sub_budgets: list[int],
    project_root: Optional[Path] = None,
) -> str:
    """並列グループのサブ予算合計が残予算以下か確認する（design §10 MUST）。

    L2 が複数の l3-executor を並列起動する場合、各サブ予算の合計が
    残予算（global_token_bound - total_tokens）以下であることを spawn 前に確認する。
    確認できない（合計 > 残予算）場合は順次起動に退避する。

    Args:
        sub_budgets: 各 l3-executor に割り当てるサブ予算のリスト（トークン数）。
        project_root: プロジェクトルートのパス。None の場合は get_project_root() を使用。

    Returns:
        "parallel": サブ予算合計 <= 残予算。並列起動許可。
        "sequential": サブ予算合計 > 残予算。順次起動に退避。
    """
    if not sub_budgets:
        return "parallel"

    state = read_state(project_root)
    total_tokens = state.get("total_tokens", 0)
    global_token_bound = state.get("global_token_bound", 200_000)

    remaining_budget = global_token_bound - total_tokens
    total_sub_budget = sum(sub_budgets)

    if total_sub_budget > remaining_budget:
        return "sequential"

    return "parallel"


# ---------------------------------------------------------------------------
# distill-lessons.py 向け hook 点（完了条件 8）
# ---------------------------------------------------------------------------


def distill_hook_point(task_id: str, project_root: Optional[Path] = None) -> None:
    """distill-lessons.py 向けメモリ蒸留 hook 点（呼び出しポイントの骨格）。

    SKILL.md [8] メモリ蒸留（W4-T1 の範囲）:
        python .claude/scripts/distill-lessons.py \\
          --task-id <task_id> \\
          --grader-log .claude/logs/gd/<task_id>-loop*-grader.json

    本関数は W4-T1 実装のフック点として用意する。
    現時点では呼び出しポイントの存在を保証するのみ（蒸留本体は対象外）。
    W4-T1 で実装を追加する際はこの関数を拡張するか、
    本関数から distill-lessons.py を subprocess.run で呼び出す。

    Args:
        task_id: タスク識別子（grader ログの命名に使用）。
        project_root: プロジェクトルートのパス。None の場合は get_project_root() を使用。
    """
    # W4-T1 実装プレースホルダ
    # 将来の実装: subprocess.run([
    #     sys.executable, str(root / ".claude/scripts/distill-lessons.py"),
    #     "--task-id", task_id,
    #     "--grader-log", str(root / f".claude/logs/gd/{task_id}-loop*-grader.json"),
    # ])
    pass


# ---------------------------------------------------------------------------
# CLI エントリポイント（SKILL.md から直接呼び出す用途）
# ---------------------------------------------------------------------------


def _build_arg_parser():
    """argparse パーサを生成する（_main から分離して単体テスト可能にする）。"""
    import argparse

    parser = argparse.ArgumentParser(
        description="gd-session-state.json 管理ツール（goal-driven 第一防衛線）"
    )
    parser.add_argument("--init", action="store_true", help="state ファイルを初期化")
    parser.add_argument("--task-id", help="タスク識別子（--init 時必須）")
    parser.add_argument("--task-slug", help="タスクスラッグ（--init 時必須）")
    parser.add_argument("--route", choices=["small", "medium", "large"],
                        help="ルート種別（--init 時必須）")
    parser.add_argument("--accumulate", type=int, metavar="TOKENS",
                        help="tokens_used を total_tokens に累積")
    parser.add_argument("--check-spawn-budget", action="store_true",
                        help="spawn 前残予算チェック")
    parser.add_argument("--check-loop-bound", action="store_true",
                        help="loop_count が max_loop_count 以上か確認")
    parser.add_argument("--increment-loop-count", action="store_true",
                        help="loop_count を 1 増やす")
    parser.add_argument("--set-status", metavar="STATUS",
                        help="status を更新（running / escalated / completed）")
    parser.add_argument("--set-fallback", metavar="MODE",
                        help="fallback を更新（例: two_layer）")
    parser.add_argument("--build-escalation-report", metavar="REASON",
                        help="エスカレーション報告を生成・出力")
    parser.add_argument("--check-parallel-budget", type=int, nargs="+",
                        metavar="SUB_BUDGET", help="並列サブ予算チェック（予算リストを渡す）")
    return parser


def _dispatch_command(args, root: Path) -> int:
    """解析済み引数を受け取り、対応する処理を実行して終了コードを返す。"""
    if args.init:
        if not all([args.task_id, args.task_slug, args.route]):
            print("--init には --task-id / --task-slug / --route が必要です。",
                  file=sys.stderr)
            return 1
        initialize_state(
            project_root=root,
            task_id=args.task_id,
            task_slug=args.task_slug,
            route=args.route,
        )
        print(f"[goal-driven] state 初期化完了: {_state_path(root)}")
        return 0

    if args.accumulate is not None:
        state = accumulate_tokens(project_root=root, tokens_used=args.accumulate)
        print(f"[goal-driven] total_tokens: {state['total_tokens']}")
        return 0

    if args.check_spawn_budget:
        result = check_spawn_budget(project_root=root)
        print(f"[goal-driven] spawn_budget_check: {result}")
        return 0 if result == "ok" else 2

    if args.check_loop_bound:
        result = check_loop_bound(project_root=root)
        print(f"[goal-driven] loop_bound_check: {result}")
        return 0 if result == "ok" else 2

    if args.increment_loop_count:
        state = increment_loop_count(project_root=root)
        print(f"[goal-driven] loop_count: {state['loop_count']} / {state['max_loop_count']}")
        return 0

    if args.set_status:
        set_status(project_root=root, new_status=args.set_status)
        print(f"[goal-driven] status を {args.set_status!r} に更新しました。")
        return 0

    if args.set_fallback:
        set_fallback(project_root=root, fallback_mode=args.set_fallback)
        print(f"[goal-driven] fallback を {args.set_fallback!r} に更新しました。")
        return 0

    if args.build_escalation_report:
        report = build_escalation_report(
            project_root=root, reason=args.build_escalation_report
        )
        print(report)
        return 0

    if args.check_parallel_budget is not None:
        result = check_parallel_spawn_budget(
            project_root=root, sub_budgets=args.check_parallel_budget
        )
        print(f"[goal-driven] parallel_budget_check: {result}")
        return 0 if result == "parallel" else 2

    return None  # 呼び出し元でヘルプ表示


def _main() -> int:
    """CLI エントリポイント。SKILL.md スクリプトから使用する。

    使用例:
      python .claude/scripts/gd_state.py --init --task-id gd-001 \\
          --task-slug my-task --route medium
      python .claude/scripts/gd_state.py --accumulate 5000
      python .claude/scripts/gd_state.py --check-spawn-budget
      python .claude/scripts/gd_state.py --set-status escalated
    """
    parser = _build_arg_parser()
    args = parser.parse_args()
    root = get_project_root()

    result = _dispatch_command(args, root)
    if result is None:
        parser.print_help()
        return 1
    return result


if __name__ == "__main__":
    sys.exit(_main())
