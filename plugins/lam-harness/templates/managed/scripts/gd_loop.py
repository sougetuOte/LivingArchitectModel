"""gd_loop.py - goal-driven Plan B 制御ループ（W3-T2 実装）

W3-T2: 実行ループ実装（Plan B: 自前ループ）
対応仕様: docs/specs/goal-driven-orchestration/design.md §8 Plan B / §11 / §11b
対応要件: FR-1 / FR-2 / FR-3 / FR-4 / NFR-6 / AC-5

機能:
  - parse_grader_output(): grader 判定 JSON のパースと verdict 分類（pass/fail/escalate/error）
  - run_grader_with_retry(): grader エラー時 1 回のみ再試行・再失敗でエスカレーション
  - run_plan_b_loop(): Plan B 制御ループ本体（bound チェック・executor・grader の直列制御）
  - is_nest_failure(): Agent ツール結果のネスト失敗検知（design §11b）
  - activate_two_layer_fallback(): 三層→二層退避（fallback: "two_layer" セット）
  - save_grader_log(): grader 判定結果を .claude/logs/gd/ に保存（NFR-3）
  - build_l3_executor_prompt(): l3-executor 向けプロンプト生成
  - build_grader_prompt(): grader 向けプロンプト生成

重要な制約（design §8 MUST NOT）:
  grader 失敗を合格として扱ってはならない。
  grader エラー時は 1 回のみ再試行し、再試行失敗でエスカレーション（MUST）。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Callable, Optional, Tuple

import gd_state


# ---------------------------------------------------------------------------
# grader 判定 JSON のパースと分類
# ---------------------------------------------------------------------------


def parse_grader_output(raw_output: str) -> dict:
    """grader が返す raw 文字列を解析し、verdict を分類して返す。

    design §8 Plan B [5] の分岐:
      - overall="pass"  → verdict="pass"
      - escalate=True   → verdict="escalate"
      - overall="fail"  → verdict="fail"
      - 不正 JSON / 欠落フィールド → verdict="error"（MUST NOT 合格扱い）

    Args:
        raw_output: grader が返した文字列（JSON 形式を期待）。

    Returns:
        {
            "verdict": "pass" | "fail" | "escalate" | "error",
            "overall": str | None,
            "items": list,
            "escalate": bool,
            "escalate_reason": str,
            "raw": str,
            "parse_error": str | None,
        }
    """
    base: dict = {
        "verdict": "error",
        "overall": None,
        "items": [],
        "escalate": False,
        "escalate_reason": "",
        "raw": raw_output,
        "parse_error": None,
    }

    if not raw_output or not raw_output.strip():
        base["parse_error"] = "grader が空の出力を返した"
        return base

    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        base["parse_error"] = str(exc)
        return base

    if "overall" not in data:
        base["parse_error"] = "overall フィールドが欠落"
        return base

    overall = data.get("overall", "")
    escalate = data.get("escalate", False)
    items = data.get("items", [])
    escalate_reason = data.get("escalate_reason", "")

    base["overall"] = overall
    base["items"] = items
    base["escalate"] = escalate
    base["escalate_reason"] = escalate_reason

    if escalate:
        base["verdict"] = "escalate"
    elif overall == "pass":
        base["verdict"] = "pass"
    elif overall == "fail":
        base["verdict"] = "fail"
    else:
        base["parse_error"] = f"不明な overall 値: {overall!r}"
        base["verdict"] = "error"

    return base


# ---------------------------------------------------------------------------
# grader エラー時の再試行ロジック
# ---------------------------------------------------------------------------


def run_grader_with_retry(
    invoke_grader_fn: Callable[[str], Tuple[str, Optional[int]]],
    prompt: str,
) -> Tuple[dict, Optional[int]]:
    """grader を呼び出し、エラー時は 1 回のみ再試行する。

    design §8 Plan B MUST:
      grader エラー / 不正 JSON → 1 回のみ再試行してよい（MAY）。
      再試行も失敗 → エスカレーション（MUST）。
      grader 失敗を合格として扱ってはならない（MUST NOT）。

    Args:
        invoke_grader_fn: grader を呼び出す関数
            (prompt: str → (raw_output: str, subagent_tokens: Optional[int]))。
        prompt: grader に渡すプロンプト。

    Returns:
        (parse_grader_output() と同じ構造の dict, subagent_tokens または None)。
        verdict は "pass" / "fail" / "escalate" / "error" のいずれか。
        両回失敗時は verdict="escalate" を返す（MUST NOT 合格扱い）。
    """
    raw_first, subagent_tokens_first = invoke_grader_fn(prompt)
    result_first = parse_grader_output(raw_first)

    if result_first["verdict"] != "error":
        return result_first, subagent_tokens_first

    # 1 回のみ再試行（MAY）
    raw_retry, subagent_tokens_retry = invoke_grader_fn(prompt)
    result_retry = parse_grader_output(raw_retry)

    if result_retry["verdict"] != "error":
        return result_retry, subagent_tokens_retry

    # 再試行も失敗 → エスカレーション（MUST）
    # grader 失敗を合格として扱ってはならない（MUST NOT）
    escalate_result = {
        "verdict": "escalate",
        "overall": None,
        "items": [],
        "escalate": True,
        "escalate_reason": (
            "grader が 2 回連続でエラーを返した。"
            f"1 回目: {result_first.get('parse_error')} "
            f"2 回目: {result_retry.get('parse_error')}"
        ),
        "raw": raw_retry,
        "parse_error": result_retry.get("parse_error"),
    }
    return escalate_result, None


# ---------------------------------------------------------------------------
# grader ログ永続化（NFR-3）
# ---------------------------------------------------------------------------


def save_grader_log(
    project_root: Path,
    task_id: str,
    loop_num: int,
    grader_result: dict,
) -> Path:
    """grader 判定結果を .claude/logs/gd/ に保存する（NFR-3）。

    design §11 NFR-3:
    ファイル命名: gd-<task_id>-loop<N 2桁>-grader.json

    Args:
        project_root: プロジェクトルートのパス。
        task_id: タスク識別子（例: "gd-20260613-001"）。
        loop_num: ループ番号（1 始まり）。
        grader_result: parse_grader_output() が返す dict 全体。

    Returns:
        保存したファイルのパス。
    """
    logs_dir = project_root / ".claude" / "logs" / "gd"
    logs_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{task_id}-loop{loop_num:02d}-grader.json"
    log_path = logs_dir / filename
    log_path.write_text(
        json.dumps(grader_result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return log_path


# ---------------------------------------------------------------------------
# プロンプト生成
# ---------------------------------------------------------------------------


def build_l3_executor_prompt(
    task_description: str,
    rubric_path: Path,
    previous_feedback: Optional[str],
) -> str:
    """l3-executor 向けのプロンプトを生成する。

    design §8 Plan B [2]:
    prompt: タスク内容 + rubric.md パス + 前回の差し戻し情報

    Args:
        task_description: タスクの説明文。
        rubric_path: rubric.md の絶対パス。
        previous_feedback: 前回の差し戻しフィードバック（初回は None）。

    Returns:
        l3-executor に渡すプロンプト文字列。
    """
    lines = [
        "# goal-driven l3-executor タスク",
        "",
        "## タスク内容",
        task_description,
        "",
        "## rubric ファイル",
        f"rubric_path={rubric_path}",
        "",
        "rubric.md を Read ツールで読み込み、全項目を満たす実装を行ってください。",
        "実装完了後は design §7 の構造化報告スキーマに従って JSON を出力してください。",
        "",
    ]

    if previous_feedback is not None:
        lines.extend([
            "## 前回の差し戻しフィードバック（必ず対応してください）",
            previous_feedback,
            "",
        ])

    lines.extend([
        "## 出力形式",
        "以下の JSON スキーマで構造化報告を返してください:",
        '{"$schema": "goal-driven-report/v1", "task_id": "...", "rubric_version": "...",',
        ' "changes": [...], "test_results": {...}, "unresolved": [...],',
        ' "next_suggestion": "...", "tokens_used": <integer>}',
    ])

    return "\n".join(lines)


def build_grader_prompt(
    rubric_path: Path,
    executor_report: dict,
) -> str:
    """grader 向けのプロンプトを生成する。

    design §8 Plan B [4] / §11:
    grader に rubric.md と 構造化報告 JSON を渡す。

    Args:
        rubric_path: rubric.md の絶対パス。
        executor_report: l3-executor が返した構造化報告 dict（design §7 スキーマ）。

    Returns:
        grader に渡すプロンプト文字列（rubric_path= 形式を含む）。
    """
    report_json = json.dumps(executor_report, ensure_ascii=False, indent=2)

    lines = [
        "# goal-driven grader 評価タスク",
        "",
        "## rubric ファイル",
        f"rubric_path={rubric_path}",
        "",
        "rubric.md を Read ツールで読み込み、以下の構造化報告と照合してください。",
        "",
        "## l3-executor 構造化報告（JSON）",
        report_json,
        "",
        "## 出力形式（必ず JSON で返すこと）",
        "以下の JSON スキーマで判定結果を返してください:",
        '{"rubric_version": "YYYY-MM-DD", "overall": "pass|fail",',
        ' "items": [{"id": <int>, "result": "pass|fail", "reason": "..."},...],',
        ' "escalate": <bool>, "escalate_reason": "..."}',
        "",
        "注意: overall が判定不能な場合は escalate=true を設定し、",
        "overall='fail' にせず escalate_reason に rubric の不明確箇所を記載してください。",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ネスト失敗検知（design §11b）
# ---------------------------------------------------------------------------


def is_nest_failure(agent_result: dict) -> bool:
    """Agent ツール結果がネスト失敗を示しているか判定する。

    design §11b 検知方法:
    - Agent ツール結果の error フィールドが非空
    - エラーメッセージに "sub-agent" / "nesting" / "not supported" 等が含まれる

    Args:
        agent_result: Agent ツール呼び出し結果の dict。

    Returns:
        True: ネスト失敗と判定。False: 正常または別の種類のエラー。
    """
    error_msg = agent_result.get("error", "")
    if not error_msg:
        return False

    nest_failure_keywords = {"sub-agent", "nesting", "not supported"}
    error_lower = error_msg.lower()
    return any(kw in error_lower for kw in nest_failure_keywords)


# ---------------------------------------------------------------------------
# 三層→二層退避（design §11b）
# ---------------------------------------------------------------------------


def activate_two_layer_fallback(project_root: Optional[Path] = None) -> dict:
    """ネスト失敗時に gd-session-state.json の fallback を "two_layer" にセットする。

    design §11b フォールバック後フロー:
    gd-session-state.json: "fallback": "two_layer" を設定
    → l2-foreman を廃し、SKILL.md スクリプト（L1 コンテキスト）が
      l3-executor を直接制御（大タスクルートが中タスクルートと同等に）

    Args:
        project_root: プロジェクトルートのパス。None の場合は get_project_root() を使用。

    Returns:
        更新後の state dict。
    """
    return gd_state.set_fallback(fallback_mode="two_layer", project_root=project_root)


# ---------------------------------------------------------------------------
# 内部ヘルパー: フィードバック構築・executor 報告解析
# ---------------------------------------------------------------------------


def _build_fail_feedback(grader_result: dict) -> str:
    """grader の不合格結果から差し戻しフィードバック文字列を生成する。

    Args:
        grader_result: parse_grader_output() / run_grader_with_retry() が返す dict。

    Returns:
        l3-executor に注入する差し戻しフィードバック文字列。
    """
    fail_items = [
        item for item in grader_result.get("items", [])
        if item.get("result") == "fail"
    ]
    if not fail_items:
        return "grader が不合格と判定しました。rubric.md を再確認してください。"

    lines = ["grader が以下の問題を指摘しました:"]
    for item in fail_items:
        lines.append(f"  - 項目 {item.get('id', '?')}: {item.get('reason', '不明')}")
    return "\n".join(lines)


def _parse_executor_report(raw: str) -> dict:
    """executor の生出力を構造化報告 dict に変換する。

    JSON パース失敗時は tokens_used=0 の最小 dict を返す（Silent Failure 回避）。

    Args:
        raw: invoke_executor_fn が返した生文字列。

    Returns:
        構造化報告 dict（design §7 スキーマ準拠または最小フォールバック）。
    """
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {"tokens_used": 0, "raw_output": raw}


def _check_bounds(project_root: Path) -> Optional[dict]:
    """loop_count と spawn budget を確認し、超過時はエスカレーション結果を返す。

    Args:
        project_root: プロジェクトルートのパス。

    Returns:
        超過あり: エスカレーション結果 dict（run_plan_b_loop の戻り値形式）。
        超過なし: None。
    """
    loop_check = gd_state.check_loop_bound(project_root=project_root)
    spawn_check = gd_state.check_spawn_budget(project_root=project_root)

    if loop_check != "escalate" and spawn_check != "escalate":
        return None

    reason = (
        "loop_bound_exceeded"
        if loop_check == "escalate"
        else "token_or_time_bound_exceeded"
    )
    gd_state.set_status(new_status="escalated", project_root=project_root)
    state = gd_state.read_state(project_root=project_root)
    return {
        "outcome": "escalated",
        "reason": reason,
        "loop_count": state.get("loop_count", 0),
        "final_grader_result": None,
    }


# ---------------------------------------------------------------------------
# Plan B 制御ループ本体（design §8）
# ---------------------------------------------------------------------------


def _accumulate_agent_tokens(
    layer: str,
    self_reported: int,
    subagent_tokens: Optional[int],
    project_root: Path,
) -> None:
    """実測 subagent_tokens を優先して累積し、None の場合は P-2 フォールバックを行う。

    P-2 フォールバック: subagent_tokens が None の場合、自己申告値を累積し WARN を出力。
    silent failure 禁止: フォールバック時も WARN ログで通知する（Critical 回避）。

    Args:
        layer: 累積対象の層（"l3" / "grader" 等）。
        self_reported: executor / grader の自己申告 tokens_used。
        subagent_tokens: Agent ツール結果から取得した実測値。None なら P-2 フォールバック。
        project_root: プロジェクトルートのパス。
    """
    if subagent_tokens is not None:
        gd_state.accumulate_subagent_tokens(
            layer=layer, tokens=subagent_tokens, project_root=project_root
        )
        if self_reported > 0:
            gd_state.record_token_divergence(
                layer=layer,
                self_reported=self_reported,
                measured=subagent_tokens,
                project_root=project_root,
            )
    else:
        # P-2 フォールバック: 自己申告値を採用
        print(
            f"[gd-warn] subagent_tokens unavailable, "
            f"falling back to self-reported tokens_used ({self_reported})",
            file=sys.stdout,
        )
        if self_reported > 0:
            gd_state.accumulate_subagent_tokens(
                layer=layer, tokens=self_reported, project_root=project_root
            )


def run_plan_b_loop(
    project_root: Path,
    task_id: str,
    rubric_path: Path,
    invoke_executor_fn: Callable[[str], Tuple[str, Optional[int]]],
    invoke_grader_fn: Callable[[str], Tuple[str, Optional[int]]],
    task_description: str = "",
) -> dict:
    """Plan B 制御ループを実行する。

    design §8 Plan B:
    while loop_count < max_loop_count AND total_tokens < global_token_bound:
      [1] bound 残量チェック → 超過ならエスカレーション（spawn-time enforcement）
      [2] Agent(l3-executor) 起動 → 構造化報告 JSON（AC-5: 独立呼び出し）
      [3] subagent_tokens 実測値を累積（None の場合は P-2 フォールバックで自己申告値）
      [4] Agent(grader) 起動 → grader 判定 JSON（AC-5: 独立呼び出し・別コンテキスト FR-2）
      [5] grader 判定処理（合格/不合格/エスカレーション）

    MUST NOT: grader 失敗を合格として扱ってはならない。
    MUST: grader エラー時は 1 回のみ再試行し、再失敗でエスカレーション。

    Args:
        project_root: プロジェクトルートのパス。
        task_id: タスク識別子（grader ログ命名に使用）。
        rubric_path: rubric.md の絶対パス。
        invoke_executor_fn: l3-executor を呼び出す関数
            (prompt → (raw JSON 文字列, subagent_tokens または None))。
        invoke_grader_fn: grader を呼び出す関数
            (prompt → (raw JSON 文字列, subagent_tokens または None))。
        task_description: タスクの説明文（l3-executor プロンプトに埋め込む）。

    Returns:
        {
            "outcome": "completed" | "escalated",
            "reason": str,
            "loop_count": int,
            "final_grader_result": dict | None,
        }
    """
    previous_feedback: Optional[str] = None

    while True:
        # [1] bound 残量チェック（spawn-time enforcement）
        bound_result = _check_bounds(project_root=project_root)
        if bound_result is not None:
            return bound_result

        # [2] l3-executor 起動（AC-5: 独立した Agent 呼び出し）
        executor_prompt = build_l3_executor_prompt(
            task_description=task_description,
            rubric_path=rubric_path,
            previous_feedback=previous_feedback,
        )
        executor_raw, executor_subagent_tokens = invoke_executor_fn(executor_prompt)
        executor_report = _parse_executor_report(executor_raw)

        # [3] subagent_tokens 実測値を優先して累積（None なら P-2 フォールバック）
        executor_self_reported = executor_report.get("tokens_used", 0)
        if not isinstance(executor_self_reported, int):
            executor_self_reported = 0
        _accumulate_agent_tokens(
            layer="l3",
            self_reported=executor_self_reported,
            subagent_tokens=executor_subagent_tokens,
            project_root=project_root,
        )

        # [4] grader 起動（AC-5: 独立した Agent 呼び出し・別コンテキスト FR-2）
        grader_prompt = build_grader_prompt(
            rubric_path=rubric_path,
            executor_report=executor_report,
        )
        state = gd_state.read_state(project_root=project_root)
        current_loop = state.get("loop_count", 0) + 1  # ログ番号（1 始まり）

        # [5] grader 判定処理（エラー時 1 回のみ再試行・MUST NOT 合格扱い）
        grader_result, grader_subagent_tokens = run_grader_with_retry(
            invoke_grader_fn=invoke_grader_fn,
            prompt=grader_prompt,
        )

        # grader トークン累積（実測優先・None なら P-2 フォールバック）
        _accumulate_agent_tokens(
            layer="grader",
            self_reported=0,  # grader は tokens_used を自己申告しない設計
            subagent_tokens=grader_subagent_tokens,
            project_root=project_root,
        )

        # grader ログ保存（NFR-3）
        save_grader_log(
            project_root=project_root,
            task_id=task_id,
            loop_num=current_loop,
            grader_result=grader_result,
        )

        verdict = grader_result["verdict"]

        if verdict == "pass":
            gd_state.set_status(new_status="completed", project_root=project_root)
            final_state = gd_state.read_state(project_root=project_root)
            return {
                "outcome": "completed",
                "reason": "grader_pass",
                "loop_count": final_state.get("loop_count", 0),
                "final_grader_result": grader_result,
            }

        if verdict == "escalate":
            gd_state.set_status(new_status="escalated", project_root=project_root)
            final_state = gd_state.read_state(project_root=project_root)
            return {
                "outcome": "escalated",
                "reason": f"grader_escalate: {grader_result.get('escalate_reason', '')}",
                "loop_count": final_state.get("loop_count", 0),
                "final_grader_result": grader_result,
            }

        # 不合格 → loop_count++ → 差し戻し情報生成 → ループ継続
        gd_state.increment_loop_count(project_root=project_root)
        previous_feedback = _build_fail_feedback(grader_result)
