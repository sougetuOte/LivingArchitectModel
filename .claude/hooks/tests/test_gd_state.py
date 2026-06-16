"""test_gd_state.py - gd_state.py の TDD テスト

W2-T2: bound スクリプト第一防衛線実装
対応仕様: docs/specs/goal-driven-orchestration/design.md §10
対応要件: FR-4 / AC-8 / AC-9
対応タスク: tasks.md W2-T2 完了条件 1〜8

テスト構成:
  TestInitializeState       - gd-session-state.json の初期化（完了条件 1）
  TestAccumulateTokens      - tokens_used 累積処理（完了条件 2）
  TestSpawnTimeCheck        - spawn 前残予算チェック（完了条件 3・4・AC-8）
  TestEscalationOutput      - エスカレーション出力内容の検証
  TestMaxLoopEscalation     - loop_count >= max_loop_count エスカレーション（完了条件 4・AC-9）
  TestParallelSpawnCheck    - 並列起動サブ予算チェック（完了条件 7）
  TestDistillHookPoint      - distill-lessons.py 向け hook 点の存在確認（完了条件 8）
  TestStateFileIO           - 読み書き・get_project_root() によるパス解決（完了条件 1・P-3）
  TestSchemaFields          - スキーマフィールド（fallback フィールド・status 値域）
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

# scripts ディレクトリを sys.path に追加（test_gd_guard.py と同じパターン）
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------


def _make_running_state(
    total_tokens: int = 0,
    loop_count: int = 0,
    max_loop_count: int = 3,
    global_token_bound: int = 150_000,
    global_time_bound: int = 3600,
    start_time: float | None = None,
    status: str = "running",
    fallback: object = None,
) -> dict:
    """テスト用の gd-session-state.json 内容を生成する。"""
    return {
        "task_id": "gd-test-001",
        "task_slug": "test-task",
        "route": "medium",
        "nest_depth_limit": 5,
        "global_token_bound": global_token_bound,
        "global_time_bound": global_time_bound,
        "total_tokens": total_tokens,
        "loop_count": loop_count,
        "max_loop_count": max_loop_count,
        "start_time": start_time if start_time is not None else time.time(),
        "status": status,
        "fallback": fallback,
    }


def _write_state(project_root: Path, state: dict) -> Path:
    """gd-session-state.json を書き込んで Path を返す。"""
    state_file = project_root / ".claude" / "gd-session-state.json"
    state_file.write_text(json.dumps(state), encoding="utf-8")
    return state_file


# ---------------------------------------------------------------------------
# TestStateFileIO: 読み書き・P-3 パス解決（完了条件 1）
# ---------------------------------------------------------------------------


class TestStateFileIO:
    """gd-session-state.json の読み書きと get_project_root() によるパス解決（P-3 対応）。"""

    def test_initialize_state_creates_file(self, tmp_path: Path, monkeypatch):
        """initialize_state() が gd-session-state.json を生成する。"""
        monkeypatch.setenv("LAM_PROJECT_ROOT", str(tmp_path))
        (tmp_path / ".claude").mkdir(exist_ok=True)

        import gd_state

        gd_state.initialize_state(
            project_root=tmp_path,
            task_id="gd-20260613-001",
            task_slug="test-task",
            route="medium",
        )

        state_file = tmp_path / ".claude" / "gd-session-state.json"
        assert state_file.is_file(), "initialize_state() が state ファイルを作成すること"

    def test_initialize_state_schema_fields(self, tmp_path: Path, monkeypatch):
        """initialize_state() が完全スキーマを持つ state ファイルを生成する。

        config.md §5 完全スキーマ: task_id / task_slug / route / nest_depth_limit /
        global_token_bound / global_time_bound / total_tokens / loop_count /
        max_loop_count / start_time / status / fallback
        """
        monkeypatch.setenv("LAM_PROJECT_ROOT", str(tmp_path))
        (tmp_path / ".claude").mkdir(exist_ok=True)

        import gd_state

        gd_state.initialize_state(
            project_root=tmp_path,
            task_id="gd-20260613-001",
            task_slug="test-task",
            route="medium",
        )

        state_file = tmp_path / ".claude" / "gd-session-state.json"
        state = json.loads(state_file.read_text(encoding="utf-8"))

        required_fields = [
            "task_id", "task_slug", "route", "nest_depth_limit",
            "global_token_bound", "global_time_bound", "total_tokens",
            "loop_count", "max_loop_count", "start_time", "status", "fallback",
        ]
        for field in required_fields:
            assert field in state, f"スキーマに必須フィールド {field!r} が欠落"

    def test_initialize_state_default_values(self, tmp_path: Path, monkeypatch):
        """initialize_state() が正しい初期値を設定する。

        config.md §5: total_tokens=0 / loop_count=0 / status="running" / fallback=null
        """
        monkeypatch.setenv("LAM_PROJECT_ROOT", str(tmp_path))
        (tmp_path / ".claude").mkdir(exist_ok=True)

        import gd_state

        gd_state.initialize_state(
            project_root=tmp_path,
            task_id="gd-20260613-001",
            task_slug="test-task",
            route="medium",
        )

        state_file = tmp_path / ".claude" / "gd-session-state.json"
        state = json.loads(state_file.read_text(encoding="utf-8"))

        assert state["total_tokens"] == 0, "初期 total_tokens は 0"
        assert state["loop_count"] == 0, "初期 loop_count は 0"
        assert state["status"] == "running", "初期 status は 'running'"
        assert state["fallback"] is None, "初期 fallback は null"

    def test_initialize_route_medium_token_bound(self, tmp_path: Path, monkeypatch):
        """medium ルートの global_token_bound は 150,000（config.md §2）。"""
        monkeypatch.setenv("LAM_PROJECT_ROOT", str(tmp_path))
        (tmp_path / ".claude").mkdir(exist_ok=True)

        import gd_state

        gd_state.initialize_state(
            project_root=tmp_path,
            task_id="gd-20260613-001",
            task_slug="test-task",
            route="medium",
        )

        state = json.loads(
            (tmp_path / ".claude" / "gd-session-state.json").read_text(encoding="utf-8")
        )
        assert state["global_token_bound"] == 150_000, (
            f"medium ルートの global_token_bound は 150000。got: {state['global_token_bound']}"
        )

    def test_initialize_route_small_token_bound(self, tmp_path: Path, monkeypatch):
        """small ルートの global_token_bound は 50,000（config.md §2）。"""
        monkeypatch.setenv("LAM_PROJECT_ROOT", str(tmp_path))
        (tmp_path / ".claude").mkdir(exist_ok=True)

        import gd_state

        gd_state.initialize_state(
            project_root=tmp_path,
            task_id="gd-20260613-002",
            task_slug="test-task-small",
            route="small",
        )

        state = json.loads(
            (tmp_path / ".claude" / "gd-session-state.json").read_text(encoding="utf-8")
        )
        assert state["global_token_bound"] == 50_000, (
            f"small ルートの global_token_bound は 50000。got: {state['global_token_bound']}"
        )

    def test_initialize_route_large_token_bound(self, tmp_path: Path, monkeypatch):
        """large ルートの global_token_bound は 400,000（config.md §2）。"""
        monkeypatch.setenv("LAM_PROJECT_ROOT", str(tmp_path))
        (tmp_path / ".claude").mkdir(exist_ok=True)

        import gd_state

        gd_state.initialize_state(
            project_root=tmp_path,
            task_id="gd-20260613-003",
            task_slug="test-task-large",
            route="large",
        )

        state = json.loads(
            (tmp_path / ".claude" / "gd-session-state.json").read_text(encoding="utf-8")
        )
        assert state["global_token_bound"] == 400_000, (
            f"large ルートの global_token_bound は 400000。got: {state['global_token_bound']}"
        )

    def test_read_state_returns_dict(self, tmp_path: Path):
        """read_state() が dict を返す。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)
        state = _make_running_state()
        _write_state(tmp_path, state)

        import gd_state

        result = gd_state.read_state(tmp_path)
        assert isinstance(result, dict), f"read_state() は dict を返すべき。got: {type(result)}"
        assert result["task_id"] == "gd-test-001"

    def test_read_state_raises_when_no_file(self, tmp_path: Path):
        """read_state() がファイルなしで FileNotFoundError を送出する。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)

        import gd_state

        with pytest.raises(FileNotFoundError):
            gd_state.read_state(tmp_path)

    def test_write_state_persists_changes(self, tmp_path: Path):
        """write_state() が変更を永続化する。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)
        state = _make_running_state(total_tokens=1000)
        _write_state(tmp_path, state)

        import gd_state

        state["total_tokens"] = 2000
        gd_state.write_state(tmp_path, state)

        updated = json.loads(
            (tmp_path / ".claude" / "gd-session-state.json").read_text(encoding="utf-8")
        )
        assert updated["total_tokens"] == 2000, "write_state() の変更が永続化されること"

    def test_path_resolved_via_get_project_root(self, tmp_path: Path, monkeypatch):
        """gd-session-state.json のパスは LAM_PROJECT_ROOT 経由で解決される（P-3 対応）。

        サブエージェント内で cwd が変動しても、LAM_PROJECT_ROOT が正しければ
        ファイルが見つかることを確認する。
        """
        monkeypatch.setenv("LAM_PROJECT_ROOT", str(tmp_path))
        (tmp_path / ".claude").mkdir(exist_ok=True)
        state = _make_running_state()
        _write_state(tmp_path, state)

        import gd_state

        # project_root を明示せずに LAM_PROJECT_ROOT から解決させる
        result = gd_state.read_state()
        assert result is not None, "LAM_PROJECT_ROOT 経由でファイルが読めること"


# ---------------------------------------------------------------------------
# TestAccumulateTokens: tokens_used 累積処理（完了条件 2）
# ---------------------------------------------------------------------------


class TestAccumulateTokens:
    """各 Agent 呼び出し後に tokens_used を total_tokens に累積する処理。

    config.md §5: total_tokens はグローバル bound 判定の正規フィールド。
    各 Agent 呼び出し後に更新（MUST）。
    """

    def test_accumulate_tokens_adds_to_total(self, tmp_path: Path):
        """accumulate_tokens() が total_tokens に加算する。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)
        state = _make_running_state(total_tokens=10_000)
        _write_state(tmp_path, state)

        import gd_state

        gd_state.accumulate_tokens(project_root=tmp_path, tokens_used=5_000)

        updated = gd_state.read_state(tmp_path)
        assert updated["total_tokens"] == 15_000, (
            f"10000 + 5000 = 15000 になるべき。got: {updated['total_tokens']}"
        )

    def test_accumulate_tokens_from_zero(self, tmp_path: Path):
        """初期値 0 から tokens_used を累積する。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)
        state = _make_running_state(total_tokens=0)
        _write_state(tmp_path, state)

        import gd_state

        gd_state.accumulate_tokens(project_root=tmp_path, tokens_used=3_000)

        updated = gd_state.read_state(tmp_path)
        assert updated["total_tokens"] == 3_000, (
            f"0 + 3000 = 3000 になるべき。got: {updated['total_tokens']}"
        )

    def test_accumulate_tokens_multiple_calls(self, tmp_path: Path):
        """複数回の累積が正しく加算される。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)
        state = _make_running_state(total_tokens=0)
        _write_state(tmp_path, state)

        import gd_state

        gd_state.accumulate_tokens(project_root=tmp_path, tokens_used=1_000)
        gd_state.accumulate_tokens(project_root=tmp_path, tokens_used=2_000)
        gd_state.accumulate_tokens(project_root=tmp_path, tokens_used=3_000)

        updated = gd_state.read_state(tmp_path)
        assert updated["total_tokens"] == 6_000, (
            f"1000 + 2000 + 3000 = 6000 になるべき。got: {updated['total_tokens']}"
        )


# ---------------------------------------------------------------------------
# TestSpawnTimeCheck: spawn 前残予算チェック（完了条件 3・4・AC-8）
# ---------------------------------------------------------------------------


class TestSpawnTimeCheck:
    """spawn 前の残予算チェック（spawn-time enforcement）。

    AC-8: total_tokens が global_token_bound 以上のとき、
    check_spawn_budget() がエスカレーション経路に到達する。
    """

    def test_check_spawn_budget_within_bound_returns_ok(self, tmp_path: Path):
        """total_tokens < global_token_bound → spawn 許可（"ok" を返す）。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)
        state = _make_running_state(
            total_tokens=100_000,
            global_token_bound=150_000,
        )
        _write_state(tmp_path, state)

        import gd_state

        result = gd_state.check_spawn_budget(project_root=tmp_path)
        assert result == "ok", f"予算内なら 'ok' を返すべき。got: {result!r}"

    def test_ac8_total_tokens_at_bound_triggers_escalation(self, tmp_path: Path):
        """AC-8: total_tokens == global_token_bound（境界値）→ エスカレーション経路。

        design §10: OR 条件 - いずれか早く到達した方で打ち切り。
        境界値（==）もエスカレーション対象。
        """
        (tmp_path / ".claude").mkdir(exist_ok=True)
        state = _make_running_state(
            total_tokens=150_000,
            global_token_bound=150_000,
        )
        _write_state(tmp_path, state)

        import gd_state

        result = gd_state.check_spawn_budget(project_root=tmp_path)
        assert result == "escalate", (
            f"total_tokens(150000) >= global_token_bound(150000) → 'escalate' を返すべき。got: {result!r}"
        )

    def test_ac8_total_tokens_exceeds_bound_triggers_escalation(self, tmp_path: Path):
        """AC-8: total_tokens > global_token_bound → エスカレーション経路。

        tasks.md W2-T2 AC-8: total_tokens 閾値超の状態ファイルで spawn-time チェックが
        エスカレーション経路に到達することを pytest で確認。
        """
        (tmp_path / ".claude").mkdir(exist_ok=True)
        state = _make_running_state(
            total_tokens=200_000,
            global_token_bound=150_000,
        )
        _write_state(tmp_path, state)

        import gd_state

        result = gd_state.check_spawn_budget(project_root=tmp_path)
        assert result == "escalate", (
            f"total_tokens(200000) > global_token_bound(150000) → 'escalate' を返すべき。got: {result!r}"
        )

    def test_check_spawn_budget_time_exceeded_triggers_escalation(self, tmp_path: Path):
        """経過時間 >= global_time_bound → エスカレーション経路（OR 条件）。

        design §10 層別 bound: OR セマンティクス。
        start_time を過去に設定し、経過時間が time_bound を超えるケース。
        """
        (tmp_path / ".claude").mkdir(exist_ok=True)
        # start_time を 7200 秒前に設定（time_bound=3600 を超過）
        state = _make_running_state(
            total_tokens=0,
            global_token_bound=150_000,
            global_time_bound=3600,
            start_time=time.time() - 7200,
        )
        _write_state(tmp_path, state)

        import gd_state

        result = gd_state.check_spawn_budget(project_root=tmp_path)
        assert result == "escalate", (
            f"経過時間(7200s) >= global_time_bound(3600s) → 'escalate' を返すべき。got: {result!r}"
        )

    def test_check_spawn_budget_sets_escalated_status(self, tmp_path: Path):
        """check_spawn_budget() がエスカレーション時に status を 'escalated' に更新する。

        design §10 エスカレーション経路:
        gd-session-state.json: status = "escalated"
        """
        (tmp_path / ".claude").mkdir(exist_ok=True)
        state = _make_running_state(
            total_tokens=200_000,
            global_token_bound=150_000,
        )
        _write_state(tmp_path, state)

        import gd_state

        gd_state.check_spawn_budget(project_root=tmp_path)

        updated = gd_state.read_state(tmp_path)
        assert updated["status"] == "escalated", (
            f"エスカレーション時に status が 'escalated' に更新されること。got: {updated['status']!r}"
        )


# ---------------------------------------------------------------------------
# TestEscalationOutput: エスカレーション出力内容の検証（完了条件 4）
# ---------------------------------------------------------------------------


class TestEscalationOutput:
    """エスカレーション時の出力内容検証。

    design §10 エスカレーション経路:
    L1 コンテキストが構造化報告の unresolved リストを PM に提示して終了。
    """

    def test_build_escalation_report_contains_reason(self, tmp_path: Path):
        """build_escalation_report() が理由を含む文字列を返す。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)
        state = _make_running_state(
            total_tokens=200_000,
            global_token_bound=150_000,
        )
        _write_state(tmp_path, state)

        import gd_state

        report = gd_state.build_escalation_report(
            project_root=tmp_path,
            reason="token_bound_exceeded",
        )
        assert isinstance(report, str), "build_escalation_report() は str を返すべき"
        assert len(report) > 0, "エスカレーション報告は空であってはならない"

    def test_build_escalation_report_includes_task_id(self, tmp_path: Path):
        """エスカレーション報告に task_id が含まれる。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)
        state = _make_running_state(
            total_tokens=200_000,
            global_token_bound=150_000,
        )
        _write_state(tmp_path, state)

        import gd_state

        report = gd_state.build_escalation_report(
            project_root=tmp_path,
            reason="token_bound_exceeded",
        )
        assert "gd-test-001" in report, (
            f"エスカレーション報告に task_id が含まれること。report={report!r}"
        )

    def test_build_escalation_report_includes_token_info(self, tmp_path: Path):
        """エスカレーション報告にトークン使用量と上限が含まれる。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)
        state = _make_running_state(
            total_tokens=200_000,
            global_token_bound=150_000,
        )
        _write_state(tmp_path, state)

        import gd_state

        report = gd_state.build_escalation_report(
            project_root=tmp_path,
            reason="token_bound_exceeded",
        )
        assert "200000" in report or "200,000" in report, (
            "エスカレーション報告に total_tokens 値が含まれること"
        )


# ---------------------------------------------------------------------------
# TestMaxLoopEscalation: loop_count >= max_loop_count エスカレーション（AC-9）
# ---------------------------------------------------------------------------


class TestMaxLoopEscalation:
    """AC-9: 常に fail を返す grader スタブ + loop_count == max_loop_count の状態で
    エスカレーション報告が出力されること（骨格レベル）。

    tasks.md W2-T2 AC-9:
    常に fail を返す grader スタブ + loop_count=max_loop_count（max_loop_count フィールドの値に
    到達した状態）の状態ファイルで、エスカレーション報告が出力されることを pytest で確認。
    """

    def test_ac9_loop_count_at_max_triggers_escalation(self, tmp_path: Path):
        """AC-9: loop_count == max_loop_count → エスカレーション経路。

        loop_count=3, max_loop_count=3 の状態で check_loop_bound() がエスカレーション返却。
        """
        (tmp_path / ".claude").mkdir(exist_ok=True)
        state = _make_running_state(loop_count=3, max_loop_count=3)
        _write_state(tmp_path, state)

        import gd_state

        result = gd_state.check_loop_bound(project_root=tmp_path)
        assert result == "escalate", (
            f"loop_count(3) >= max_loop_count(3) → 'escalate' を返すべき。got: {result!r}"
        )

    def test_ac9_loop_count_exceeds_max_triggers_escalation(self, tmp_path: Path):
        """loop_count > max_loop_count → エスカレーション経路。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)
        state = _make_running_state(loop_count=5, max_loop_count=3)
        _write_state(tmp_path, state)

        import gd_state

        result = gd_state.check_loop_bound(project_root=tmp_path)
        assert result == "escalate", (
            f"loop_count(5) > max_loop_count(3) → 'escalate' を返すべき。got: {result!r}"
        )

    def test_loop_count_below_max_returns_ok(self, tmp_path: Path):
        """loop_count < max_loop_count → spawn 許可（"ok" を返す）。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)
        state = _make_running_state(loop_count=1, max_loop_count=3)
        _write_state(tmp_path, state)

        import gd_state

        result = gd_state.check_loop_bound(project_root=tmp_path)
        assert result == "ok", (
            f"loop_count(1) < max_loop_count(3) → 'ok' を返すべき。got: {result!r}"
        )

    def test_ac9_grader_fail_stub_and_max_loop_produces_escalation_report(
        self, tmp_path: Path, capsys
    ):
        """AC-9 統合: grader fail スタブ + loop_count=max_loop_count でエスカレーション報告が出力。

        SKILL.md フロー [4] step 5:
        loop_count >= max_loop_count → エスカレーション（bound 超過）
        """
        (tmp_path / ".claude").mkdir(exist_ok=True)
        # max_loop_count=3 の上限に到達した状態
        state = _make_running_state(loop_count=3, max_loop_count=3)
        _write_state(tmp_path, state)

        # grader スタブ: 常に fail を返す
        grader_result = {"overall": "fail", "escalate": False, "escalate_reason": ""}

        import gd_state

        # loop_count が max_loop_count に達しているため、エスカレーション処理を実行
        loop_result = gd_state.check_loop_bound(project_root=tmp_path)
        assert loop_result == "escalate", "loop 上限到達はエスカレーション"

        # エスカレーション報告を生成・出力
        report = gd_state.build_escalation_report(
            project_root=tmp_path,
            reason="max_loop_count_reached",
        )
        print(report)  # stdout に出力

        captured = capsys.readouterr()
        assert len(captured.out) > 0, "エスカレーション報告が stdout に出力されること"

    def test_increment_loop_count(self, tmp_path: Path):
        """increment_loop_count() が loop_count を 1 増やす。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)
        state = _make_running_state(loop_count=1)
        _write_state(tmp_path, state)

        import gd_state

        gd_state.increment_loop_count(project_root=tmp_path)

        updated = gd_state.read_state(tmp_path)
        assert updated["loop_count"] == 2, (
            f"loop_count が 1 → 2 に増えること。got: {updated['loop_count']}"
        )


# ---------------------------------------------------------------------------
# TestParallelSpawnCheck: 並列起動サブ予算チェック（完了条件 7）
# ---------------------------------------------------------------------------


class TestParallelSpawnCheck:
    """並列起動チェック: 並列グループの各サブ予算合計が残予算以下か確認。

    design §10 MUST:
    L2 が複数の l3-executor を並列起動する場合、並列グループの各サブ予算の合計が
    残予算以下であることを spawn 前に確認する。
    確認できない場合は順次起動に退避する。
    """

    def test_parallel_spawn_within_budget_returns_parallel(self, tmp_path: Path):
        """サブ予算合計 < 残予算 → 並列起動許可（"parallel" を返す）。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)
        # 残予算: 150000 - 50000 = 100000
        state = _make_running_state(
            total_tokens=50_000,
            global_token_bound=150_000,
        )
        _write_state(tmp_path, state)

        import gd_state

        # サブ予算: [30000, 40000] = 70000 < 残予算 100000
        result = gd_state.check_parallel_spawn_budget(
            project_root=tmp_path,
            sub_budgets=[30_000, 40_000],
        )
        assert result == "parallel", (
            f"サブ予算合計(70000) <= 残予算(100000) → 'parallel' を返すべき。got: {result!r}"
        )

    def test_parallel_spawn_exceeds_budget_returns_sequential(self, tmp_path: Path):
        """サブ予算合計 > 残予算 → 順次起動に退避（"sequential" を返す）。

        design §10: 確認できない場合は順次起動に退避する。
        """
        (tmp_path / ".claude").mkdir(exist_ok=True)
        # 残予算: 150000 - 100000 = 50000
        state = _make_running_state(
            total_tokens=100_000,
            global_token_bound=150_000,
        )
        _write_state(tmp_path, state)

        import gd_state

        # サブ予算: [30000, 40000] = 70000 > 残予算 50000
        result = gd_state.check_parallel_spawn_budget(
            project_root=tmp_path,
            sub_budgets=[30_000, 40_000],
        )
        assert result == "sequential", (
            f"サブ予算合計(70000) > 残予算(50000) → 'sequential'（順次起動）を返すべき。got: {result!r}"
        )

    def test_parallel_spawn_equal_budget_returns_parallel(self, tmp_path: Path):
        """サブ予算合計 == 残予算（境界値）→ 並列起動許可（"parallel" を返す）。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)
        # 残予算: 150000 - 80000 = 70000
        state = _make_running_state(
            total_tokens=80_000,
            global_token_bound=150_000,
        )
        _write_state(tmp_path, state)

        import gd_state

        # サブ予算: [30000, 40000] = 70000 == 残予算 70000
        result = gd_state.check_parallel_spawn_budget(
            project_root=tmp_path,
            sub_budgets=[30_000, 40_000],
        )
        assert result == "parallel", (
            f"サブ予算合計(70000) == 残予算(70000) → 'parallel' を返すべき。got: {result!r}"
        )

    def test_parallel_spawn_empty_budgets_returns_parallel(self, tmp_path: Path):
        """サブ予算リストが空 → 並列起動許可（"parallel" を返す）。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)
        state = _make_running_state(total_tokens=50_000, global_token_bound=150_000)
        _write_state(tmp_path, state)

        import gd_state

        result = gd_state.check_parallel_spawn_budget(
            project_root=tmp_path,
            sub_budgets=[],
        )
        assert result == "parallel", (
            f"サブ予算リストが空 → 'parallel' を返すべき。got: {result!r}"
        )


# ---------------------------------------------------------------------------
# TestDistillHookPoint: distill-lessons.py 向け hook 点（完了条件 8）
# ---------------------------------------------------------------------------


class TestDistillHookPoint:
    """distill-lessons.py 向けメモリ蒸留 hook 点の存在確認。

    完了条件 8: distill-lessons.py 向けのメモリ蒸留 hook 点（呼び出しポイントの用意。
    蒸留本体は対象外）。
    gd_state モジュールが distill_hook_point() 関数を公開していること。
    """

    def test_distill_hook_point_function_exists(self):
        """gd_state モジュールが distill_hook_point() を公開している。"""
        import gd_state

        assert hasattr(gd_state, "distill_hook_point"), (
            "gd_state に distill_hook_point() 関数が必要（完了条件 8）"
        )
        assert callable(gd_state.distill_hook_point), (
            "distill_hook_point は callable である必要がある"
        )

    def test_distill_hook_point_callable_without_error(self, tmp_path: Path):
        """distill_hook_point() が例外なく呼び出せる。

        蒸留本体は W4-T1 の範囲。本タスクでは呼び出しポイントの骨格のみ確認する。
        """
        (tmp_path / ".claude").mkdir(exist_ok=True)
        state = _make_running_state(status="completed")
        _write_state(tmp_path, state)

        import gd_state

        # 例外なしで完了すること
        gd_state.distill_hook_point(
            project_root=tmp_path,
            task_id="gd-test-001",
        )


# ---------------------------------------------------------------------------
# TestSchemaFields: スキーマフィールド検証（fallback フィールド・status 値域）
# ---------------------------------------------------------------------------


class TestSchemaFields:
    """gd-session-state.json スキーマフィールドの検証。

    PM 承認済み追加フィールド:
    - fallback: null（初期値）/ "two_layer"（二層フォールバック発動時）
    - status: "running" / "escalated" / "completed" の 3 値
    """

    def test_set_fallback_two_layer(self, tmp_path: Path):
        """set_fallback() が fallback フィールドを "two_layer" に更新する。

        SKILL.md [4]: 大タスクルートでネスト失敗時に fallback: "two_layer" をセット。
        """
        (tmp_path / ".claude").mkdir(exist_ok=True)
        state = _make_running_state(fallback=None)
        _write_state(tmp_path, state)

        import gd_state

        gd_state.set_fallback(project_root=tmp_path, fallback_mode="two_layer")

        updated = gd_state.read_state(tmp_path)
        assert updated["fallback"] == "two_layer", (
            f"fallback フィールドが 'two_layer' に更新されること。got: {updated['fallback']!r}"
        )

    def test_initial_fallback_is_null(self, tmp_path: Path, monkeypatch):
        """initialize_state() の初期 fallback は null（None）。"""
        monkeypatch.setenv("LAM_PROJECT_ROOT", str(tmp_path))
        (tmp_path / ".claude").mkdir(exist_ok=True)

        import gd_state

        gd_state.initialize_state(
            project_root=tmp_path,
            task_id="gd-test-schema-001",
            task_slug="schema-test",
            route="medium",
        )

        state = gd_state.read_state(tmp_path)
        assert state.get("fallback") is None, (
            f"初期 fallback は null（None）であること。got: {state.get('fallback')!r}"
        )

    def test_set_status_escalated(self, tmp_path: Path):
        """set_status() が status を 'escalated' に更新する。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)
        state = _make_running_state(status="running")
        _write_state(tmp_path, state)

        import gd_state

        gd_state.set_status(project_root=tmp_path, new_status="escalated")

        updated = gd_state.read_state(tmp_path)
        assert updated["status"] == "escalated", (
            f"status が 'escalated' に更新されること。got: {updated['status']!r}"
        )

    def test_set_status_completed(self, tmp_path: Path):
        """set_status() が status を 'completed' に更新する。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)
        state = _make_running_state(status="running")
        _write_state(tmp_path, state)

        import gd_state

        gd_state.set_status(project_root=tmp_path, new_status="completed")

        updated = gd_state.read_state(tmp_path)
        assert updated["status"] == "completed", (
            f"status が 'completed' に更新されること。got: {updated['status']!r}"
        )

    def test_cost_log_not_duplicated_in_total_tokens(self, tmp_path: Path):
        """cost_log は層別内訳のみ保持し、total_tokens を重複保持しない。

        config.md §5: cost_log は層別内訳のみを保持する。
        合計値を重複保持してはならない（design §14 MUST NOT）。
        """
        (tmp_path / ".claude").mkdir(exist_ok=True)
        state = _make_running_state(total_tokens=70_000)
        # cost_log を追加
        state["cost_log"] = {
            "l1_tokens": 12_000,
            "l2_tokens": 5_000,
            "l3_tokens": 45_000,
            "grader_tokens": 8_000,
        }
        _write_state(tmp_path, state)

        import gd_state

        loaded = gd_state.read_state(tmp_path)
        cost_log = loaded.get("cost_log", {})

        # cost_log に total_tokens の重複保持がないこと
        assert "total_tokens" not in cost_log, (
            "cost_log に total_tokens を重複保持してはならない（design §14 MUST NOT）"
        )


# ---------------------------------------------------------------------------
# TestAccumulateSubagentTokens: 層別トークン累積（W4-T2 Phase 1+2）
# ---------------------------------------------------------------------------


class TestAccumulateSubagentTokens:
    """accumulate_subagent_tokens() の層別正常系テスト（W4-T2 Phase 1）。

    design §14: cost_log は層別内訳のみ保持。
    total_tokens は cost_log と二重保持せず、トップレベルで正規ソースとして管理。
    """

    def test_accumulate_subagent_tokens_l1(self, tmp_path: Path):
        """layer='l1' のトークンが cost_log['l1_tokens'] に加算される。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)
        _write_state(tmp_path, _make_running_state(total_tokens=0))

        import gd_state

        gd_state.accumulate_subagent_tokens(layer="l1", tokens=3000, project_root=tmp_path)

        state = gd_state.read_state(tmp_path)
        assert state["cost_log"]["l1_tokens"] == 3000, (
            f"l1 tokens=3000 が cost_log['l1_tokens'] に加算されるべき。got: {state['cost_log']['l1_tokens']}"
        )

    def test_accumulate_subagent_tokens_l2(self, tmp_path: Path):
        """layer='l2' のトークンが cost_log['l2_tokens'] に加算される。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)
        _write_state(tmp_path, _make_running_state(total_tokens=0))

        import gd_state

        gd_state.accumulate_subagent_tokens(layer="l2", tokens=1500, project_root=tmp_path)

        state = gd_state.read_state(tmp_path)
        assert state["cost_log"]["l2_tokens"] == 1500, (
            f"l2 tokens=1500 が cost_log['l2_tokens'] に加算されるべき。got: {state['cost_log']['l2_tokens']}"
        )

    def test_accumulate_subagent_tokens_l3(self, tmp_path: Path):
        """layer='l3' のトークンが cost_log['l3_tokens'] に加算される。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)
        _write_state(tmp_path, _make_running_state(total_tokens=0))

        import gd_state

        gd_state.accumulate_subagent_tokens(layer="l3", tokens=8000, project_root=tmp_path)

        state = gd_state.read_state(tmp_path)
        assert state["cost_log"]["l3_tokens"] == 8000, (
            f"l3 tokens=8000 が cost_log['l3_tokens'] に加算されるべき。got: {state['cost_log']['l3_tokens']}"
        )

    def test_accumulate_subagent_tokens_grader(self, tmp_path: Path):
        """layer='grader' のトークンが cost_log['grader_tokens'] に加算される。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)
        _write_state(tmp_path, _make_running_state(total_tokens=0))

        import gd_state

        gd_state.accumulate_subagent_tokens(layer="grader", tokens=2000, project_root=tmp_path)

        state = gd_state.read_state(tmp_path)
        assert state["cost_log"]["grader_tokens"] == 2000, (
            f"grader tokens=2000 が cost_log['grader_tokens'] に加算されるべき。"
            f"got: {state['cost_log']['grader_tokens']}"
        )

    def test_accumulate_subagent_tokens_also_adds_to_total_tokens(self, tmp_path: Path):
        """accumulate_subagent_tokens() が同時に total_tokens も加算する。

        design §14 L764: total_tokens は §10 で正規ソース。
        cost_log は層別内訳のみ（二重保持禁止）。
        """
        (tmp_path / ".claude").mkdir(exist_ok=True)
        _write_state(tmp_path, _make_running_state(total_tokens=10_000))

        import gd_state

        gd_state.accumulate_subagent_tokens(layer="l3", tokens=5000, project_root=tmp_path)

        state = gd_state.read_state(tmp_path)
        assert state["total_tokens"] == 15_000, (
            f"total_tokens: 10000 + 5000 = 15000 になるべき。got: {state['total_tokens']}"
        )

    def test_accumulate_subagent_tokens_initializes_cost_log_if_missing(self, tmp_path: Path):
        """cost_log が存在しない場合、初期化してから加算する。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)
        state = _make_running_state(total_tokens=0)
        # cost_log なしで書き込む
        assert "cost_log" not in state
        _write_state(tmp_path, state)

        import gd_state

        gd_state.accumulate_subagent_tokens(layer="l1", tokens=1000, project_root=tmp_path)

        updated = gd_state.read_state(tmp_path)
        assert "cost_log" in updated, "cost_log が初期化されるべき"
        assert updated["cost_log"]["l1_tokens"] == 1000

    def test_accumulate_subagent_tokens_cost_log_not_duplicated(self, tmp_path: Path):
        """累積後も cost_log に total_tokens が含まれない（二重保持禁止）。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)
        _write_state(tmp_path, _make_running_state(total_tokens=0))

        import gd_state

        gd_state.accumulate_subagent_tokens(layer="l3", tokens=5000, project_root=tmp_path)

        state = gd_state.read_state(tmp_path)
        assert "total_tokens" not in state["cost_log"], (
            "cost_log に total_tokens を保持してはならない（design §14 MUST NOT）"
        )


# ---------------------------------------------------------------------------
# TestBuildCostSummary: コスト集計文字列生成（W4-T2 Phase 1）
# ---------------------------------------------------------------------------


class TestBuildCostSummary:
    """build_cost_summary() と compute_l1_ratio() のテスト。

    design §14 L767-778: 層別 tokens / l1_ratio / 合計を含む文字列を生成。
    """

    def _setup_with_cost_log(
        self,
        tmp_path: Path,
        l1: int = 12_000,
        l2: int = 5_000,
        l3: int = 45_000,
        grader: int = 8_000,
    ) -> "gd_state":
        """cost_log を持つ state を作成して gd_state モジュールを返す。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)
        total = l1 + l2 + l3 + grader
        state = _make_running_state(total_tokens=total)
        state["cost_log"] = {
            "l1_tokens": l1,
            "l2_tokens": l2,
            "l3_tokens": l3,
            "grader_tokens": grader,
        }
        _write_state(tmp_path, state)
        import gd_state
        return gd_state

    def test_build_cost_summary_contains_layer_fields(self, tmp_path: Path):
        """build_cost_summary() が層別 tokens フィールドを含む文字列を返す。"""
        gd_state = self._setup_with_cost_log(tmp_path)

        summary = gd_state.build_cost_summary(project_root=tmp_path)

        assert isinstance(summary, str), "build_cost_summary() は str を返すべき"
        assert "l1" in summary.lower() or "l1_tokens" in summary, "l1 情報が含まれるべき"
        assert "l3" in summary.lower() or "l3_tokens" in summary, "l3 情報が含まれるべき"
        assert "grader" in summary.lower(), "grader 情報が含まれるべき"

    def test_build_cost_summary_contains_total(self, tmp_path: Path):
        """build_cost_summary() が合計トークンを含む。"""
        gd_state = self._setup_with_cost_log(
            tmp_path, l1=12_000, l2=5_000, l3=45_000, grader=8_000
        )

        summary = gd_state.build_cost_summary(project_root=tmp_path)

        # 合計 70000 が含まれること
        assert "70000" in summary or "70,000" in summary, (
            f"合計 tokens=70000 が summary に含まれるべき。got: {summary!r}"
        )

    def test_build_cost_summary_contains_l1_ratio(self, tmp_path: Path):
        """build_cost_summary() が l1_ratio を含む。"""
        gd_state = self._setup_with_cost_log(tmp_path)

        summary = gd_state.build_cost_summary(project_root=tmp_path)

        assert "l1_ratio" in summary or "ratio" in summary.lower(), (
            f"l1_ratio が summary に含まれるべき。got: {summary!r}"
        )

    def test_compute_l1_ratio_nonzero_total(self, tmp_path: Path):
        """compute_l1_ratio() が l1_tokens / total_tokens を正確に返す。"""
        gd_state = self._setup_with_cost_log(
            tmp_path, l1=20_000, l2=0, l3=60_000, grader=20_000
        )

        ratio = gd_state.compute_l1_ratio(project_root=tmp_path)

        # l1=20000, total=100000 → ratio=0.2
        assert abs(ratio - 0.2) < 1e-9, (
            f"l1_tokens=20000, total=100000 → ratio=0.2 であるべき。got: {ratio}"
        )

    def test_compute_l1_ratio_zero_total(self, tmp_path: Path):
        """compute_l1_ratio() が total=0 のとき 0.0 を返す（ゼロ除算回避）。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)
        state = _make_running_state(total_tokens=0)
        state["cost_log"] = {
            "l1_tokens": 0,
            "l2_tokens": 0,
            "l3_tokens": 0,
            "grader_tokens": 0,
        }
        _write_state(tmp_path, state)

        import gd_state

        ratio = gd_state.compute_l1_ratio(project_root=tmp_path)

        assert ratio == 0.0, f"total=0 のとき ratio=0.0 であるべき。got: {ratio}"


# ---------------------------------------------------------------------------
# TestRecordTokenDivergence: トークン乖離記録（W4-T2 Phase 1）
# ---------------------------------------------------------------------------


class TestRecordTokenDivergence:
    """record_token_divergence() のテスト。

    ±20% 超で WARN ログ出力 + cost_log['_divergences'] に記録。
    ±20% 以内では WARN なし。
    """

    def test_divergence_over_20pct_emits_warn(self, tmp_path: Path, capsys):
        """乖離率 > 20% で WARN ログが stdout に出力される。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)
        state = _make_running_state(total_tokens=0)
        state["cost_log"] = {
            "l1_tokens": 0, "l2_tokens": 0, "l3_tokens": 0, "grader_tokens": 0
        }
        _write_state(tmp_path, state)

        import gd_state

        # self_reported=1000, measured=1300 → ratio=(300/1300)≒23% > 20%
        gd_state.record_token_divergence(
            layer="l3", self_reported=1000, measured=1300, project_root=tmp_path
        )

        captured = capsys.readouterr()
        assert "[gd-warn]" in captured.out, (
            f"乖離率 23% > 20% → [gd-warn] が出力されるべき。got: {captured.out!r}"
        )
        assert "token divergence" in captured.out.lower(), (
            "WARN メッセージに 'token divergence' が含まれるべき"
        )

    def test_divergence_over_20pct_records_to_divergences(self, tmp_path: Path):
        """乖離率 > 20% で cost_log['_divergences'] に記録される。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)
        state = _make_running_state(total_tokens=0)
        state["cost_log"] = {
            "l1_tokens": 0, "l2_tokens": 0, "l3_tokens": 0, "grader_tokens": 0
        }
        _write_state(tmp_path, state)

        import gd_state

        gd_state.record_token_divergence(
            layer="l3", self_reported=1000, measured=1300, project_root=tmp_path
        )

        updated = gd_state.read_state(tmp_path)
        divergences = updated["cost_log"].get("_divergences", [])
        assert len(divergences) == 1, (
            f"乖離記録が 1 件 _divergences に追加されるべき。got: {divergences}"
        )
        assert divergences[0]["layer"] == "l3"
        assert divergences[0]["self_reported"] == 1000
        assert divergences[0]["measured"] == 1300

    def test_divergence_within_20pct_no_warn(self, tmp_path: Path, capsys):
        """乖離率 <= 20% では WARN ログを出力しない。"""
        (tmp_path / ".claude").mkdir(exist_ok=True)
        state = _make_running_state(total_tokens=0)
        state["cost_log"] = {
            "l1_tokens": 0, "l2_tokens": 0, "l3_tokens": 0, "grader_tokens": 0
        }
        _write_state(tmp_path, state)

        import gd_state

        # self_reported=1000, measured=1100 → ratio=(100/1100)≒9.1% <= 20%
        gd_state.record_token_divergence(
            layer="l3", self_reported=1000, measured=1100, project_root=tmp_path
        )

        captured = capsys.readouterr()
        assert "[gd-warn]" not in captured.out, (
            f"乖離率 9.1% <= 20% → [gd-warn] は出力されないべき。got: {captured.out!r}"
        )
