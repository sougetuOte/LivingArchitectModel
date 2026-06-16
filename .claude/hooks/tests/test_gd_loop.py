"""test_gd_loop.py - gd_loop.py の TDD テスト（Plan B 実行ループ）

W3-T2: 実行ループ実装（Plan B: 自前ループ）
対応仕様: docs/specs/goal-driven-orchestration/design.md §8 Plan B
対応要件: FR-1 / FR-2 / FR-3 / FR-4 / NFR-6 / AC-5 / design §8 / §11b

テスト構成:
  TestGraderResultParsing      - grader 判定 JSON のパースと分類（pass/fail/escalate/error）
  TestGraderRetryLogic         - grader エラー時の 1 回のみ再試行とエスカレーション
  TestLoopControlFlow          - Plan B 制御ループのフロー（合格・差し戻し・bound 超過）
  TestNestFailureFallback      - §11b ネスト失敗フォールバック（三層→二層退避）
  TestGraderLogPersistence     - grader 判定 JSON のログ保存（NFR-3）
  TestBuildL3Prompt            - l3-executor 向けプロンプト生成
  TestBuildGraderPrompt        - grader 向けプロンプト生成
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import pytest

# scripts ディレクトリを sys.path に追加（test_gd_state.py と同じパターン）
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------


def _make_state(
    tmp_path: Path,
    total_tokens: int = 0,
    loop_count: int = 0,
    max_loop_count: int = 3,
    global_token_bound: int = 150_000,
    global_time_bound: int = 3600,
    status: str = "running",
    fallback: object = None,
    route: str = "medium",
) -> Path:
    """gd-session-state.json を tmp_path に作成し、パスを返す。"""
    import time

    (tmp_path / ".claude").mkdir(exist_ok=True)
    state = {
        "task_id": "gd-test-001",
        "task_slug": "test-task",
        "route": route,
        "nest_depth_limit": 5,
        "global_token_bound": global_token_bound,
        "global_time_bound": global_time_bound,
        "total_tokens": total_tokens,
        "loop_count": loop_count,
        "max_loop_count": max_loop_count,
        "start_time": time.time(),
        "status": status,
        "fallback": fallback,
    }
    state_path = tmp_path / ".claude" / "gd-session-state.json"
    state_path.write_text(json.dumps(state), encoding="utf-8")
    return state_path


def _valid_grader_pass() -> dict:
    """grader が返す合格判定 JSON（design §11 スキーマ）。"""
    return {
        "rubric_version": "2026-06-13",
        "overall": "pass",
        "items": [
            {"id": 1, "result": "pass", "reason": "all tests passed"},
        ],
        "escalate": False,
        "escalate_reason": "",
    }


def _valid_grader_fail() -> dict:
    """grader が返す不合格判定 JSON（design §11 スキーマ）。"""
    return {
        "rubric_version": "2026-06-13",
        "overall": "fail",
        "items": [
            {"id": 1, "result": "fail", "reason": "field name mismatch"},
        ],
        "escalate": False,
        "escalate_reason": "",
    }


def _valid_grader_escalate() -> dict:
    """grader が返すエスカレーション判定 JSON（design §11 スキーマ）。"""
    return {
        "rubric_version": "2026-06-13",
        "overall": "fail",
        "items": [],
        "escalate": True,
        "escalate_reason": "rubric description is ambiguous",
    }


def _mock_executor_report(tokens_used: int = 5000) -> dict:
    """l3-executor が返す構造化報告 JSON（design §7 スキーマ）。"""
    return {
        "$schema": "goal-driven-report/v1",
        "task_id": "gd-test-001",
        "rubric_version": "2026-06-13",
        "changes": [{"file": "src/foo.py", "summary": "add function"}],
        "test_results": {
            "command": "pytest --tb=short",
            "passed": 5,
            "failed": 0,
            "skipped": 0,
            "exit_code": 0,
        },
        "unresolved": [],
        "next_suggestion": "",
        "tokens_used": tokens_used,
    }


def _make_executor_fn(tokens_used: int = 5000, subagent_tokens: Optional[int] = None):
    """invoke_executor_fn のモックを生成する。

    新シグネチャ: Callable[[str], tuple[str, Optional[int]]]
    第2要素が None なら P-2 フォールバック（自己申告値を使用）。
    """
    from typing import Optional as _Opt
    report_json = json.dumps(_mock_executor_report(tokens_used=tokens_used))
    return lambda prompt: (report_json, subagent_tokens)


def _make_grader_fn(grader_dict: dict, subagent_tokens: Optional[int] = None):
    """invoke_grader_fn のモックを生成する。

    新シグネチャ: Callable[[str], tuple[str, Optional[int]]]
    """
    grader_json = json.dumps(grader_dict)
    return lambda prompt: (grader_json, subagent_tokens)


# ---------------------------------------------------------------------------
# TestGraderResultParsing: grader 判定 JSON のパースと分類
# ---------------------------------------------------------------------------


class TestGraderResultParsing:
    """grader が返す JSON を合格/不合格/エスカレーション/エラーに分類する。

    design §8 Plan B [5]:
      - 合格 (overall: "pass") → ループ終了
      - エスカレーション (escalate: true) → エスカレーション処理
      - grader エラー / 不正 JSON → 1 回のみ再試行
      - 不合格 (overall: "fail") → loop_count++ → 差し戻し
    """

    def test_parse_grader_output_pass(self):
        """overall='pass' → 'pass' に分類される。"""
        import gd_loop

        grader_json = json.dumps(_valid_grader_pass())
        result = gd_loop.parse_grader_output(grader_json)
        assert result["verdict"] == "pass", (
            f"overall='pass' → verdict='pass' であるべき。got: {result['verdict']!r}"
        )

    def test_parse_grader_output_fail(self):
        """overall='fail' かつ escalate=False → 'fail' に分類される。"""
        import gd_loop

        grader_json = json.dumps(_valid_grader_fail())
        result = gd_loop.parse_grader_output(grader_json)
        assert result["verdict"] == "fail", (
            f"overall='fail', escalate=False → verdict='fail' であるべき。got: {result['verdict']!r}"
        )

    def test_parse_grader_output_escalate(self):
        """escalate=True → 'escalate' に分類される。

        design §11: 判定不能時は escalate=True + escalate_reason を設定。
        """
        import gd_loop

        grader_json = json.dumps(_valid_grader_escalate())
        result = gd_loop.parse_grader_output(grader_json)
        assert result["verdict"] == "escalate", (
            f"escalate=True → verdict='escalate' であるべき。got: {result['verdict']!r}"
        )

    def test_parse_grader_output_escalate_reason_preserved(self):
        """エスカレーション時の理由が保持される。"""
        import gd_loop

        grader_data = _valid_grader_escalate()
        grader_json = json.dumps(grader_data)
        result = gd_loop.parse_grader_output(grader_json)
        assert result["escalate_reason"] == grader_data["escalate_reason"], (
            "escalate_reason が保持されるべき"
        )

    def test_parse_grader_output_invalid_json_returns_error(self):
        """不正 JSON → 'error' に分類される（MUST NOT 合格扱い）。

        design §8 Plan B MUST NOT: grader 失敗を合格として扱ってはならない。
        """
        import gd_loop

        result = gd_loop.parse_grader_output("{ this is not json }")
        assert result["verdict"] == "error", (
            f"不正 JSON → verdict='error' であるべき（合格扱い禁止）。got: {result['verdict']!r}"
        )

    def test_parse_grader_output_empty_string_returns_error(self):
        """空文字列 → 'error' に分類される。"""
        import gd_loop

        result = gd_loop.parse_grader_output("")
        assert result["verdict"] == "error", (
            f"空文字列 → verdict='error' であるべき。got: {result['verdict']!r}"
        )

    def test_parse_grader_output_missing_overall_returns_error(self):
        """overall フィールドが欠落した JSON → 'error' に分類される。"""
        import gd_loop

        incomplete = {"rubric_version": "2026-06-13", "items": []}
        result = gd_loop.parse_grader_output(json.dumps(incomplete))
        assert result["verdict"] == "error", (
            f"overall 欠落 → verdict='error' であるべき。got: {result['verdict']!r}"
        )

    def test_parse_grader_output_pass_has_items(self):
        """合格時の items フィールドが保持される。"""
        import gd_loop

        grader_data = _valid_grader_pass()
        result = gd_loop.parse_grader_output(json.dumps(grader_data))
        assert result["items"] == grader_data["items"], (
            "items フィールドが保持されるべき"
        )


# ---------------------------------------------------------------------------
# TestGraderRetryLogic: grader エラー時の再試行とエスカレーション
# ---------------------------------------------------------------------------


class TestGraderRetryLogic:
    """grader エラー時: 1 回のみ再試行し、再試行失敗でエスカレーション。

    design §8 Plan B [5]:
      grader エラー / 不正 JSON → 1 回のみ再試行してよい（MAY）。
      再試行も失敗した場合はエスカレーション（MUST）。
      grader 失敗を合格として扱ってはならない（MUST NOT）。
    """

    def test_run_grader_with_retry_success_on_retry(self, tmp_path: Path, monkeypatch):
        """1 回目エラー → 2 回目成功 → 'pass' を返す。

        再試行が成功した場合は合格として扱う（正常ケース）。
        新シグネチャ: invoke_grader_fn は tuple[str, Optional[int]] を返す。
        run_grader_with_retry も (dict, Optional[int]) を返す。
        """
        import gd_loop

        call_count = 0

        def mock_invoke_grader(prompt: str) -> tuple:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return ("{ invalid json }", None)
            return (json.dumps(_valid_grader_pass()), 500)

        result, subagent_tokens = gd_loop.run_grader_with_retry(
            invoke_grader_fn=mock_invoke_grader,
            prompt="test prompt",
        )
        assert result["verdict"] == "pass", (
            f"再試行成功 → verdict='pass' であるべき。got: {result['verdict']!r}"
        )
        assert call_count == 2, (
            f"1 回エラー後に再試行（合計 2 回）されるべき。got: {call_count}"
        )

    def test_run_grader_with_retry_escalate_on_both_failures(self, tmp_path: Path):
        """1 回目エラー → 2 回目もエラー → 'escalate' を返す（MUST NOT 合格扱い）。

        design §8 MUST: 再試行も失敗した場合はエスカレーション。
        MUST NOT: grader 失敗を合格として扱ってはならない。
        新シグネチャ: invoke_grader_fn は tuple[str, Optional[int]] を返す。
        """
        import gd_loop

        def mock_invoke_grader_always_fails(prompt: str) -> tuple:
            return ("{ always invalid json }", None)

        result, _ = gd_loop.run_grader_with_retry(
            invoke_grader_fn=mock_invoke_grader_always_fails,
            prompt="test prompt",
        )
        assert result["verdict"] == "escalate", (
            f"1 回目・2 回目ともにエラー → verdict='escalate' であるべき（合格扱い禁止）。"
            f"got: {result['verdict']!r}"
        )

    def test_run_grader_with_retry_exactly_one_retry(self, tmp_path: Path):
        """エラー時の再試行は 1 回のみ（3 回目を呼ばない）。

        design §8: 1 回のみ再試行してよい（MAY）。
        新シグネチャ: invoke_grader_fn は tuple[str, Optional[int]] を返す。
        """
        import gd_loop

        call_count = 0

        def mock_invoke_grader_always_fails(prompt: str) -> tuple:
            nonlocal call_count
            call_count += 1
            return ("{ always invalid }", None)

        gd_loop.run_grader_with_retry(
            invoke_grader_fn=mock_invoke_grader_always_fails,
            prompt="test prompt",
        )
        assert call_count == 2, (
            f"再試行は 1 回のみ（合計 2 回）であるべき。got: {call_count}"
        )

    def test_run_grader_with_retry_no_retry_on_pass(self, tmp_path: Path):
        """1 回目が成功 → 再試行なしで 'pass' を返す。

        新シグネチャ: invoke_grader_fn は tuple[str, Optional[int]] を返す。
        run_grader_with_retry も (dict, Optional[int]) を返す。
        """
        import gd_loop

        call_count = 0

        def mock_invoke_grader_success(prompt: str) -> tuple:
            nonlocal call_count
            call_count += 1
            return (json.dumps(_valid_grader_pass()), 400)

        result, subagent_tokens = gd_loop.run_grader_with_retry(
            invoke_grader_fn=mock_invoke_grader_success,
            prompt="test prompt",
        )
        assert result["verdict"] == "pass", f"got: {result['verdict']!r}"
        assert call_count == 1, (
            f"1 回目成功なら再試行なし（1 回のみ）であるべき。got: {call_count}"
        )

    def test_run_grader_with_retry_no_retry_on_fail(self, tmp_path: Path):
        """1 回目が 'fail' → 再試行なしで 'fail' を返す（エラーと混同しない）。

        エラー（不正 JSON）と不合格（valid JSON で overall='fail'）は別物。
        不合格は再試行せずにそのまま返す。
        新シグネチャ: invoke_grader_fn は tuple[str, Optional[int]] を返す。
        """
        import gd_loop

        call_count = 0

        def mock_invoke_grader_fail(prompt: str) -> tuple:
            nonlocal call_count
            call_count += 1
            return (json.dumps(_valid_grader_fail()), 300)

        result, _ = gd_loop.run_grader_with_retry(
            invoke_grader_fn=mock_invoke_grader_fail,
            prompt="test prompt",
        )
        assert result["verdict"] == "fail", f"got: {result['verdict']!r}"
        assert call_count == 1, (
            f"不合格（valid fail）は再試行なし（1 回のみ）であるべき。got: {call_count}"
        )


# ---------------------------------------------------------------------------
# TestLoopControlFlow: Plan B 制御ループのフロー
# ---------------------------------------------------------------------------


class TestLoopControlFlow:
    """Plan B 制御ループの主要フロー検証。

    design §8 Plan B:
    while loop_count < max_loop_count AND total_tokens < global_token_bound:
      [1] bound チェック → 不足ならエスカレーション
      [2] Agent(l3-executor) 起動 → 構造化報告 JSON
      [3] tokens_used を累積
      [4] Agent(grader) 起動 → grader 判定 JSON
      [5] 判定処理（合格/不合格/エスカレーション）
    """

    def test_run_plan_b_loop_pass_on_first_attempt(self, tmp_path: Path):
        """1 回目の grader 判定で合格 → 'completed' でループ終了。

        design §8 Plan B [5]: 合格 → ループ終了。
        invoke_executor_fn / invoke_grader_fn は新シグネチャ: tuple[str, Optional[int]]。
        """
        import gd_loop

        _make_state(tmp_path)
        logs_dir = tmp_path / ".claude" / "logs" / "gd"
        logs_dir.mkdir(parents=True, exist_ok=True)

        result = gd_loop.run_plan_b_loop(
            project_root=tmp_path,
            task_id="gd-test-001",
            rubric_path=tmp_path / "rubric.md",
            invoke_executor_fn=_make_executor_fn(tokens_used=5000, subagent_tokens=5200),
            invoke_grader_fn=_make_grader_fn(_valid_grader_pass(), subagent_tokens=800),
        )

        assert result["outcome"] == "completed", (
            f"合格 → outcome='completed' であるべき。got: {result['outcome']!r}"
        )

    def test_run_plan_b_loop_fail_then_pass(self, tmp_path: Path):
        """1 回目不合格 → 2 回目合格 → 'completed' でループ終了。

        invoke_grader_fn は新シグネチャ: tuple[str, Optional[int]]。
        """
        import gd_loop

        _make_state(tmp_path, max_loop_count=3)
        logs_dir = tmp_path / ".claude" / "logs" / "gd"
        logs_dir.mkdir(parents=True, exist_ok=True)

        call_count = 0

        def mock_grader(prompt: str) -> tuple:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return (json.dumps(_valid_grader_fail()), 600)
            return (json.dumps(_valid_grader_pass()), 600)

        result = gd_loop.run_plan_b_loop(
            project_root=tmp_path,
            task_id="gd-test-001",
            rubric_path=tmp_path / "rubric.md",
            invoke_executor_fn=_make_executor_fn(tokens_used=3000, subagent_tokens=3100),
            invoke_grader_fn=mock_grader,
        )

        assert result["outcome"] == "completed", (
            f"1 回差し戻し後に合格 → outcome='completed' であるべき。got: {result['outcome']!r}"
        )

    def test_run_plan_b_loop_max_loop_count_reached_escalates(self, tmp_path: Path):
        """max_loop_count 到達 → 'escalated' でループ終了。

        design §8: loop_count >= max_loop_count → エスカレーション。
        invoke_grader_fn は新シグネチャ: tuple[str, Optional[int]]。
        """
        import gd_loop

        _make_state(tmp_path, max_loop_count=2)
        logs_dir = tmp_path / ".claude" / "logs" / "gd"
        logs_dir.mkdir(parents=True, exist_ok=True)

        def mock_grader_always_fail(prompt: str) -> tuple:
            return (json.dumps(_valid_grader_fail()), 500)

        result = gd_loop.run_plan_b_loop(
            project_root=tmp_path,
            task_id="gd-test-001",
            rubric_path=tmp_path / "rubric.md",
            invoke_executor_fn=_make_executor_fn(tokens_used=1000, subagent_tokens=1000),
            invoke_grader_fn=mock_grader_always_fail,
        )

        assert result["outcome"] == "escalated", (
            f"max_loop_count 到達 → outcome='escalated' であるべき。got: {result['outcome']!r}"
        )

    def test_run_plan_b_loop_grader_escalate_triggers_escalation(self, tmp_path: Path):
        """grader が escalate=True → 'escalated' でループ終了。

        design §11: 判定不能時は escalate=True を設定 → スクリプトがエスカレーション。
        invoke_executor_fn / invoke_grader_fn は新シグネチャ: tuple[str, Optional[int]]。
        """
        import gd_loop

        _make_state(tmp_path)
        logs_dir = tmp_path / ".claude" / "logs" / "gd"
        logs_dir.mkdir(parents=True, exist_ok=True)

        result = gd_loop.run_plan_b_loop(
            project_root=tmp_path,
            task_id="gd-test-001",
            rubric_path=tmp_path / "rubric.md",
            invoke_executor_fn=_make_executor_fn(tokens_used=2000, subagent_tokens=2000),
            invoke_grader_fn=_make_grader_fn(_valid_grader_escalate(), subagent_tokens=700),
        )

        assert result["outcome"] == "escalated", (
            f"grader escalate=True → outcome='escalated' であるべき。got: {result['outcome']!r}"
        )

    def test_run_plan_b_loop_token_bound_exceeded_before_loop_escalates(
        self, tmp_path: Path
    ):
        """ループ前の spawn-time チェックで token bound 超過 → 'escalated'。

        design §8 Plan B [1]: bound 残量チェック → 残量不足ならエスカレーション。
        invoke_executor_fn は新シグネチャ: tuple[str, Optional[int]]。
        """
        import gd_loop

        # すでに bound を超えた状態で初期化
        _make_state(tmp_path, total_tokens=150_000, global_token_bound=150_000)
        logs_dir = tmp_path / ".claude" / "logs" / "gd"
        logs_dir.mkdir(parents=True, exist_ok=True)

        call_count = 0

        def mock_executor(prompt: str) -> tuple:
            nonlocal call_count
            call_count += 1
            return (json.dumps(_mock_executor_report(tokens_used=1000)), 1000)

        result = gd_loop.run_plan_b_loop(
            project_root=tmp_path,
            task_id="gd-test-001",
            rubric_path=tmp_path / "rubric.md",
            invoke_executor_fn=mock_executor,
            invoke_grader_fn=_make_grader_fn(_valid_grader_pass()),
        )

        assert result["outcome"] == "escalated", (
            f"事前 bound 超過 → outcome='escalated' であるべき。got: {result['outcome']!r}"
        )
        assert call_count == 0, (
            f"bound 超過時は executor を呼ばないべき（spawn-time enforcement）。"
            f"got call_count={call_count}"
        )

    def test_run_plan_b_loop_accumulates_tokens(self, tmp_path: Path):
        """実測 subagent_tokens がトップレベル total_tokens を加算する（P-2 経由でなく）。

        新シグネチャ: invoke_executor_fn は (json_str, subagent_tokens) を返す。
        実測値（第2要素）が total_tokens に累積されること。
        """
        import gd_loop
        import gd_state

        _make_state(tmp_path)
        logs_dir = tmp_path / ".claude" / "logs" / "gd"
        logs_dir.mkdir(parents=True, exist_ok=True)

        # 実測 subagent_tokens=9000、自己申告 tokens_used=8000
        # → 実測値 9000 が total_tokens に累積されるべき
        gd_loop.run_plan_b_loop(
            project_root=tmp_path,
            task_id="gd-test-001",
            rubric_path=tmp_path / "rubric.md",
            invoke_executor_fn=_make_executor_fn(tokens_used=8000, subagent_tokens=9000),
            invoke_grader_fn=_make_grader_fn(_valid_grader_pass(), subagent_tokens=500),
        )

        state = gd_state.read_state(tmp_path)
        # executor 実測 9000 + grader 実測 500 = 9500 が累積される
        assert state["total_tokens"] >= 9000, (
            f"実測 subagent_tokens=9000 が total_tokens に累積されるべき。"
            f"got total_tokens={state['total_tokens']}"
        )

    def test_run_plan_b_loop_sets_status_completed_on_pass(self, tmp_path: Path):
        """合格時に gd-session-state.json の status が 'completed' になる。

        design §10: grader 合格 → status = 'completed'。
        invoke_executor_fn / invoke_grader_fn は新シグネチャ: tuple[str, Optional[int]]。
        """
        import gd_loop
        import gd_state

        _make_state(tmp_path)
        logs_dir = tmp_path / ".claude" / "logs" / "gd"
        logs_dir.mkdir(parents=True, exist_ok=True)

        gd_loop.run_plan_b_loop(
            project_root=tmp_path,
            task_id="gd-test-001",
            rubric_path=tmp_path / "rubric.md",
            invoke_executor_fn=_make_executor_fn(),
            invoke_grader_fn=_make_grader_fn(_valid_grader_pass()),
        )

        state = gd_state.read_state(tmp_path)
        assert state["status"] == "completed", (
            f"合格時は status='completed' であるべき。got: {state['status']!r}"
        )

    def test_run_plan_b_loop_sets_status_escalated_on_max_loop(self, tmp_path: Path):
        """max_loop_count 到達時に gd-session-state.json の status が 'escalated' になる。

        invoke_executor_fn / invoke_grader_fn は新シグネチャ: tuple[str, Optional[int]]。
        """
        import gd_loop
        import gd_state

        _make_state(tmp_path, max_loop_count=1)
        logs_dir = tmp_path / ".claude" / "logs" / "gd"
        logs_dir.mkdir(parents=True, exist_ok=True)

        result = gd_loop.run_plan_b_loop(
            project_root=tmp_path,
            task_id="gd-test-001",
            rubric_path=tmp_path / "rubric.md",
            invoke_executor_fn=_make_executor_fn(),
            invoke_grader_fn=_make_grader_fn(_valid_grader_fail()),
        )

        state = gd_state.read_state(tmp_path)
        assert state["status"] == "escalated", (
            f"max_loop_count 到達時は status='escalated' であるべき。got: {state['status']!r}"
        )

    def test_run_plan_b_loop_increments_loop_count_on_fail(self, tmp_path: Path):
        """不合格時に loop_count が増加する。

        design §8 Plan B: 不合格 → loop_count++
        invoke_grader_fn は新シグネチャ: tuple[str, Optional[int]]。
        """
        import gd_loop
        import gd_state

        _make_state(tmp_path, max_loop_count=3)
        logs_dir = tmp_path / ".claude" / "logs" / "gd"
        logs_dir.mkdir(parents=True, exist_ok=True)

        call_count = 0

        def mock_grader(prompt: str) -> tuple:
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return (json.dumps(_valid_grader_fail()), 400)
            return (json.dumps(_valid_grader_pass()), 400)

        gd_loop.run_plan_b_loop(
            project_root=tmp_path,
            task_id="gd-test-001",
            rubric_path=tmp_path / "rubric.md",
            invoke_executor_fn=_make_executor_fn(),
            invoke_grader_fn=mock_grader,
        )

        state = gd_state.read_state(tmp_path)
        # 2 回 fail の後に pass → loop_count = 2
        assert state["loop_count"] == 2, (
            f"2 回差し戻しで loop_count=2 であるべき。got: {state['loop_count']}"
        )

    def test_run_plan_b_loop_grader_error_then_escalate_not_pass(self, tmp_path: Path):
        """grader が両回エラー → 'escalated'（MUST NOT: 合格扱い禁止）。

        design §8 MUST NOT: grader 失敗を合格として扱ってはならない。
        invoke_grader_fn は新シグネチャ: tuple[str, Optional[int]]。
        """
        import gd_loop

        _make_state(tmp_path)
        logs_dir = tmp_path / ".claude" / "logs" / "gd"
        logs_dir.mkdir(parents=True, exist_ok=True)

        def mock_grader_always_error(prompt: str) -> tuple:
            return ("{ broken json always }", None)

        result = gd_loop.run_plan_b_loop(
            project_root=tmp_path,
            task_id="gd-test-001",
            rubric_path=tmp_path / "rubric.md",
            invoke_executor_fn=_make_executor_fn(),
            invoke_grader_fn=mock_grader_always_error,
        )

        assert result["outcome"] != "completed", (
            f"grader エラー時は outcome='completed' であってはならない（MUST NOT）。"
            f"got: {result['outcome']!r}"
        )
        assert result["outcome"] == "escalated", (
            f"grader 両回エラー → outcome='escalated' であるべき。got: {result['outcome']!r}"
        )


# ---------------------------------------------------------------------------
# TestNestFailureFallback: §11b ネスト失敗フォールバック（三層→二層退避）
# ---------------------------------------------------------------------------


class TestNestFailureFallback:
    """design §11b: ネスト失敗フォールバック（三層→二層退避）。

    L2 からの Agent(l3-executor) 呼び出しがエラーを返した場合:
    - gd-session-state.json: "fallback": "two_layer" をセット
    - 以後 L1 が l3-executor を直接制御
    """

    def test_detect_nest_failure_error_field(self):
        """Agent ツール結果の error フィールドが非空 → ネスト失敗と判定。

        design §11b 検知方法: Agent ツール結果の error フィールドが非空。
        """
        import gd_loop

        agent_result = {
            "error": "sub-agent nesting not supported at this depth",
            "output": "",
        }
        assert gd_loop.is_nest_failure(agent_result) is True, (
            "error フィールドが非空 → ネスト失敗と判定されるべき"
        )

    def test_detect_nest_failure_nesting_keyword(self):
        """エラーメッセージに 'nesting' → ネスト失敗と判定。

        design §11b: エラーメッセージに 'sub-agent' / 'nesting' / 'not supported' が含まれる。
        """
        import gd_loop

        agent_result = {
            "error": "nesting level exceeded maximum allowed",
            "output": "",
        }
        assert gd_loop.is_nest_failure(agent_result) is True, (
            "'nesting' キーワードを含む error → ネスト失敗と判定されるべき"
        )

    def test_detect_nest_failure_not_supported_keyword(self):
        """エラーメッセージに 'not supported' → ネスト失敗と判定。"""
        import gd_loop

        agent_result = {
            "error": "sub-agent invocation not supported in this context",
            "output": "",
        }
        assert gd_loop.is_nest_failure(agent_result) is True, (
            "'not supported' を含む error → ネスト失敗と判定されるべき"
        )

    def test_detect_no_nest_failure_empty_error(self):
        """error フィールドが空文字列 → ネスト失敗でない。"""
        import gd_loop

        agent_result = {
            "error": "",
            "output": "{ ... }",
        }
        assert gd_loop.is_nest_failure(agent_result) is False, (
            "error 空文字列 → ネスト失敗でないと判定されるべき"
        )

    def test_detect_no_nest_failure_no_error_field(self):
        """error フィールドなし → ネスト失敗でない。"""
        import gd_loop

        agent_result = {"output": "some output"}
        assert gd_loop.is_nest_failure(agent_result) is False, (
            "error フィールドなし → ネスト失敗でないと判定されるべき"
        )

    def test_set_two_layer_fallback_updates_state(self, tmp_path: Path):
        """ネスト失敗時に gd-session-state.json の fallback が 'two_layer' になる。

        design §11b: gd-session-state.json: "fallback": "two_layer" をセット。
        """
        import gd_loop
        import gd_state

        _make_state(tmp_path, route="large")

        gd_loop.activate_two_layer_fallback(project_root=tmp_path)

        state = gd_state.read_state(tmp_path)
        assert state["fallback"] == "two_layer", (
            f"ネスト失敗フォールバック発動後は fallback='two_layer' であるべき。"
            f"got: {state['fallback']!r}"
        )

    def test_set_two_layer_fallback_preserves_other_fields(self, tmp_path: Path):
        """fallback セット時に他のフィールドが保持される。"""
        import gd_loop
        import gd_state

        _make_state(tmp_path, total_tokens=5000, loop_count=1, route="large")

        gd_loop.activate_two_layer_fallback(project_root=tmp_path)

        state = gd_state.read_state(tmp_path)
        assert state["total_tokens"] == 5000, "total_tokens が保持されるべき"
        assert state["loop_count"] == 1, "loop_count が保持されるべき"
        assert state["status"] == "running", "status が変更されないべき"


# ---------------------------------------------------------------------------
# TestGraderLogPersistence: grader 判定ログの保存（NFR-3）
# ---------------------------------------------------------------------------


class TestGraderLogPersistence:
    """NFR-3: grader の判定結果を .claude/logs/gd/ に保存する。

    design §11 NFR-3:
    ファイル命名: gd-<task_id>-loop<N>-grader.json
    """

    def test_save_grader_log_creates_file(self, tmp_path: Path):
        """save_grader_log() が .claude/logs/gd/ にファイルを作成する。"""
        import gd_loop

        logs_dir = tmp_path / ".claude" / "logs" / "gd"
        logs_dir.mkdir(parents=True, exist_ok=True)

        grader_result = _valid_grader_pass()
        gd_loop.save_grader_log(
            project_root=tmp_path,
            task_id="gd-20260613-001",
            loop_num=1,
            grader_result=grader_result,
        )

        expected_path = logs_dir / "gd-20260613-001-loop01-grader.json"
        assert expected_path.is_file(), (
            f"grader ログファイルが作成されるべき: {expected_path}"
        )

    def test_save_grader_log_filename_format(self, tmp_path: Path):
        """grader ログのファイル名が design §11 の命名規則に従う。

        命名規則: gd-<task_id>-loop<N 2桁>-grader.json
        """
        import gd_loop

        logs_dir = tmp_path / ".claude" / "logs" / "gd"
        logs_dir.mkdir(parents=True, exist_ok=True)

        gd_loop.save_grader_log(
            project_root=tmp_path,
            task_id="gd-20260613-001",
            loop_num=3,
            grader_result=_valid_grader_fail(),
        )

        expected_path = logs_dir / "gd-20260613-001-loop03-grader.json"
        assert expected_path.is_file(), (
            f"loop_num=3 → ループ番号は 2 桁ゼロパディング。got: {expected_path}"
        )

    def test_save_grader_log_content_is_valid_json(self, tmp_path: Path):
        """保存されたファイルが有効な JSON である。"""
        import gd_loop

        logs_dir = tmp_path / ".claude" / "logs" / "gd"
        logs_dir.mkdir(parents=True, exist_ok=True)

        grader_result = _valid_grader_pass()
        gd_loop.save_grader_log(
            project_root=tmp_path,
            task_id="gd-20260613-001",
            loop_num=1,
            grader_result=grader_result,
        )

        log_file = logs_dir / "gd-20260613-001-loop01-grader.json"
        content = json.loads(log_file.read_text(encoding="utf-8"))
        assert content["overall"] == "pass", (
            f"保存内容が正しいべき。got: {content}"
        )

    def test_run_plan_b_loop_saves_grader_log(self, tmp_path: Path):
        """run_plan_b_loop() 実行後に grader ログが .claude/logs/gd/ に保存される。

        design §11 NFR-3: grader の判定結果を .claude/logs/gd/ に保存する。
        invoke_executor_fn / invoke_grader_fn は新シグネチャ: tuple[str, Optional[int]]。
        """
        import gd_loop

        _make_state(tmp_path)
        logs_dir = tmp_path / ".claude" / "logs" / "gd"
        logs_dir.mkdir(parents=True, exist_ok=True)

        gd_loop.run_plan_b_loop(
            project_root=tmp_path,
            task_id="gd-20260613-001",
            rubric_path=tmp_path / "rubric.md",
            invoke_executor_fn=_make_executor_fn(),
            invoke_grader_fn=_make_grader_fn(_valid_grader_pass()),
        )

        log_files = list(logs_dir.glob("gd-20260613-001-loop*-grader.json"))
        assert len(log_files) >= 1, (
            f"grader ログが 1 件以上保存されるべき。got: {log_files}"
        )


# ---------------------------------------------------------------------------
# TestBuildL3Prompt: l3-executor 向けプロンプト生成
# ---------------------------------------------------------------------------


class TestBuildL3Prompt:
    """build_l3_executor_prompt() のテスト。

    design §8 Plan B [2]: prompt にタスク内容 + rubric.md パス + 前回の差し戻し情報を含む。
    """

    def test_build_l3_prompt_contains_rubric_path(self, tmp_path: Path):
        """プロンプトに rubric_path が含まれる。"""
        import gd_loop

        rubric_path = tmp_path / "rubric.md"
        prompt = gd_loop.build_l3_executor_prompt(
            task_description="implement feature X",
            rubric_path=rubric_path,
            previous_feedback=None,
        )
        assert str(rubric_path) in prompt, (
            f"rubric_path が prompt に含まれるべき。got prompt:\n{prompt}"
        )

    def test_build_l3_prompt_contains_task_description(self, tmp_path: Path):
        """プロンプトにタスク説明が含まれる。"""
        import gd_loop

        rubric_path = tmp_path / "rubric.md"
        task_desc = "implement the authentication module"
        prompt = gd_loop.build_l3_executor_prompt(
            task_description=task_desc,
            rubric_path=rubric_path,
            previous_feedback=None,
        )
        assert task_desc in prompt, (
            f"タスク説明が prompt に含まれるべき。got prompt:\n{prompt}"
        )

    def test_build_l3_prompt_contains_feedback_on_retry(self, tmp_path: Path):
        """差し戻し時（previous_feedback あり）にフィードバックが含まれる。

        design §8 Plan B [5]: 不合格 → l3-executor に差し戻し情報を注入してループ継続。
        """
        import gd_loop

        rubric_path = tmp_path / "rubric.md"
        feedback = "field name mismatch: expected 'user_id', got 'userId'"
        prompt = gd_loop.build_l3_executor_prompt(
            task_description="implement feature X",
            rubric_path=rubric_path,
            previous_feedback=feedback,
        )
        assert feedback in prompt, (
            f"差し戻しフィードバックが prompt に含まれるべき。got prompt:\n{prompt}"
        )

    def test_build_l3_prompt_no_feedback_section_on_first_run(self, tmp_path: Path):
        """初回実行（previous_feedback=None）では差し戻し情報セクションが最小限。"""
        import gd_loop

        rubric_path = tmp_path / "rubric.md"
        prompt = gd_loop.build_l3_executor_prompt(
            task_description="implement feature X",
            rubric_path=rubric_path,
            previous_feedback=None,
        )
        assert isinstance(prompt, str), "prompt は文字列であるべき"
        assert len(prompt) > 0, "prompt は空でないべき"


# ---------------------------------------------------------------------------
# TestBuildGraderPrompt: grader 向けプロンプト生成
# ---------------------------------------------------------------------------


class TestBuildGraderPrompt:
    """build_grader_prompt() のテスト。

    design §8 Plan B [4]: grader に 構造化報告 JSON + rubric.md を渡す。
    design [5] §11: grader は rubric.md と構造化報告を照合。
    """

    def test_build_grader_prompt_contains_rubric_path(self, tmp_path: Path):
        """プロンプトに rubric_path が含まれる。"""
        import gd_loop

        rubric_path = tmp_path / "rubric.md"
        report = _mock_executor_report()
        prompt = gd_loop.build_grader_prompt(
            rubric_path=rubric_path,
            executor_report=report,
        )
        assert str(rubric_path) in prompt, (
            f"rubric_path が grader prompt に含まれるべき。got prompt:\n{prompt}"
        )

    def test_build_grader_prompt_contains_report_json(self, tmp_path: Path):
        """プロンプトに executor_report が JSON 形式で含まれる。"""
        import gd_loop

        rubric_path = tmp_path / "rubric.md"
        report = _mock_executor_report(tokens_used=7777)
        prompt = gd_loop.build_grader_prompt(
            rubric_path=rubric_path,
            executor_report=report,
        )
        assert "7777" in prompt, (
            f"executor_report の tokens_used=7777 が prompt に含まれるべき。"
            f"got prompt:\n{prompt}"
        )

    def test_build_grader_prompt_requests_json_output(self, tmp_path: Path):
        """プロンプトが JSON 形式での出力を要求する。

        design §11 grader 出力スキーマ: overall / items / escalate を含む JSON を返す。
        """
        import gd_loop

        rubric_path = tmp_path / "rubric.md"
        report = _mock_executor_report()
        prompt = gd_loop.build_grader_prompt(
            rubric_path=rubric_path,
            executor_report=report,
        )
        # JSON 出力を要求するキーワードがプロンプトに含まれるべき
        prompt_lower = prompt.lower()
        assert "json" in prompt_lower, (
            f"grader prompt は JSON 出力を要求すべき。got prompt:\n{prompt}"
        )


# ---------------------------------------------------------------------------
# TestSubagentTokenAccumulation: subagent_tokens 実測値による累積（W4-T2 Phase 2）
# ---------------------------------------------------------------------------


class TestSubagentTokenAccumulation:
    """W4-T2 Phase 2: 実測 subagent_tokens による累積ロジックのテスト。

    新シグネチャ: invoke_executor_fn / invoke_grader_fn が
    tuple[str, Optional[int]] を返す。
    第2要素（subagent_tokens）が None の場合、P-2 フォールバックで自己申告値を使用する。
    """

    def test_measured_subagent_tokens_accumulated_as_total(self, tmp_path: Path):
        """実測 subagent_tokens が total_tokens に累積される（P-2 経由ではない）。

        invoke_executor_fn が (json_str, 9000) を返す場合、
        自己申告 tokens_used=8000 ではなく実測 9000 が累積されるべき。
        """
        import gd_loop
        import gd_state

        _make_state(tmp_path)
        logs_dir = tmp_path / ".claude" / "logs" / "gd"
        logs_dir.mkdir(parents=True, exist_ok=True)

        # 実測=9000、自己申告=8000 → 実測値が優先されること
        gd_loop.run_plan_b_loop(
            project_root=tmp_path,
            task_id="gd-test-001",
            rubric_path=tmp_path / "rubric.md",
            invoke_executor_fn=_make_executor_fn(tokens_used=8000, subagent_tokens=9000),
            invoke_grader_fn=_make_grader_fn(_valid_grader_pass(), subagent_tokens=0),
        )

        state = gd_state.read_state(tmp_path)
        # executor 実測 9000 が累積される
        assert state["total_tokens"] >= 9000, (
            f"実測 subagent_tokens=9000 が累積されるべき。got: {state['total_tokens']}"
        )

    def test_none_subagent_tokens_falls_back_to_self_reported(self, tmp_path: Path, capsys):
        """subagent_tokens=None → P-2 フォールバックで自己申告値が累積される。

        invoke_executor_fn が (json_str, None) を返す場合:
        - [gd-warn] ログで P-2 フォールバックを通知
        - 自己申告 tokens_used が total_tokens に累積される
        """
        import gd_loop
        import gd_state

        _make_state(tmp_path)
        logs_dir = tmp_path / ".claude" / "logs" / "gd"
        logs_dir.mkdir(parents=True, exist_ok=True)

        # subagent_tokens=None → フォールバック
        gd_loop.run_plan_b_loop(
            project_root=tmp_path,
            task_id="gd-test-001",
            rubric_path=tmp_path / "rubric.md",
            invoke_executor_fn=_make_executor_fn(tokens_used=7000, subagent_tokens=None),
            invoke_grader_fn=_make_grader_fn(_valid_grader_pass(), subagent_tokens=0),
        )

        state = gd_state.read_state(tmp_path)
        # 自己申告 7000 が累積される
        assert state["total_tokens"] >= 7000, (
            f"P-2 フォールバック: 自己申告 tokens_used=7000 が累積されるべき。"
            f"got: {state['total_tokens']}"
        )

        captured = capsys.readouterr()
        assert "[gd-warn]" in captured.out, (
            "P-2 フォールバック時に [gd-warn] ログが出力されるべき"
        )

    def test_grader_subagent_tokens_accumulated(self, tmp_path: Path):
        """grader 側の subagent_tokens も total_tokens に累積される。

        grader の invoke_grader_fn が (json_str, 800) を返す場合、
        grader の実測 800 が total_tokens に加算されるべき。
        """
        import gd_loop
        import gd_state

        _make_state(tmp_path)
        logs_dir = tmp_path / ".claude" / "logs" / "gd"
        logs_dir.mkdir(parents=True, exist_ok=True)

        gd_loop.run_plan_b_loop(
            project_root=tmp_path,
            task_id="gd-test-001",
            rubric_path=tmp_path / "rubric.md",
            # executor 実測 5000
            invoke_executor_fn=_make_executor_fn(tokens_used=5000, subagent_tokens=5000),
            # grader 実測 800
            invoke_grader_fn=_make_grader_fn(_valid_grader_pass(), subagent_tokens=800),
        )

        state = gd_state.read_state(tmp_path)
        # executor 5000 + grader 800 = 5800 以上
        assert state["total_tokens"] >= 5800, (
            f"executor(5000) + grader(800) = 5800 以上が累積されるべき。"
            f"got: {state['total_tokens']}"
        )
