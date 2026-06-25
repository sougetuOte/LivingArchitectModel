"""test_v4_view.py - V-4 Task 一覧ビューのテスト（W3-B5-T15）

対応仕様:
  - docs/specs/b4-dashboard/design.md §4「V-4: Task 一覧ビュー」
  - docs/specs/b4-dashboard/design.md §5「Task の状態決定ロジック」
  - docs/specs/b4-dashboard/tasks.md §3 W3-B5-T15
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# .claude/scripts を sys.path に追加（test_v2_view.py と同じパターン）
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


# ─────────────────────────────────────────────
# テスト用フィクスチャヘルパー
# ─────────────────────────────────────────────


def _make_builder(tasks=None, in_progress=None, blocked=None, completed=None):
    """テスト用 DashboardBuilder を生成するヘルパー。

    パーサを呼ばず DashboardData を直接組み立てる（V-2 テストと同パターン）。

    Args:
        tasks: TaskInfo リスト（TasksParser 由来のベースデータ）
        in_progress: 進行中タスクの文字列リスト（SessionStateParser 由来）
        blocked: ブロック中タスクの文字列リスト（SessionStateParser 由来）
        completed: 完了タスクの文字列リスト（SessionStateParser 由来）
    """
    from dashboard.builder import DashboardBuilder
    from dashboard.models import DashboardData

    task_list = tasks if tasks is not None else []
    data = DashboardData(
        tasks=task_list,
        in_progress=in_progress if in_progress is not None else [],
        blocked=blocked if blocked is not None else [],
        completed=completed if completed is not None else [],
        generated_at="2026-06-21T12:00:00",
    )
    return DashboardBuilder(data)


def _make_task(
    task_id: str = "W1-B5-T1",
    milestone: str = "b4-dashboard",
    assignee: str = "-",
    status: str = "not-started",
):
    """テスト用 TaskInfo を生成するヘルパー。"""
    from dashboard.models import TaskInfo

    return TaskInfo(id=task_id, milestone=milestone, assignee=assignee, status=status)


# ─────────────────────────────────────────────
# R-6: <section id="v4-tasks"> の存在確認（設計書出力ファイルからのアサーション）
# ─────────────────────────────────────────────


def test_render_contains_v4_section_id():
    """生成 HTML に <section id="v4-tasks"> が存在すること。

    対応完了条件: W3-B5-T15「<section id="v4-tasks"> が存在」
    設計仕様: design.md §4 V-4 DOM 構成案
    R-6: design.md に「<section id="v4-tasks">」出力が明記されているため必須
    """
    builder = _make_builder()
    result_html = builder.render()
    assert '<section id="v4-tasks">' in result_html, (
        '生成 HTML に <section id="v4-tasks"> が見つかりません。\n'
        "builder.py の render() に V-4 セクションを追加してください。"
    )


# ─────────────────────────────────────────────
# テーブル構造確認
# ─────────────────────────────────────────────


def test_render_v4_contains_table_with_tasks():
    """Task が 1 件以上のとき <table> 要素が存在すること。

    対応完了条件: W3-B5-T15「テーブルに Task ID・担当・状態カラムが表示される」
    Wave 6 T38 緩和: `<table>` に `id="tasks-table"` 属性が付与されたため、
    開きタグの部分一致（`<table`）で検査する（SE 級）。
    """
    task = _make_task()
    result_html = _make_builder(tasks=[task]).render()
    assert "<table" in result_html, (
        "生成 HTML に <table 要素が見つかりません（Task 1 件以上のケース）。"
    )


def test_render_v4_thead_has_three_columns():
    """V-4 テーブルのヘッダに「Task ID」「担当」「状態」の 3 列が存在すること。

    対応完了条件: W3-B5-T15「テーブルに Task ID・担当・状態カラムが表示される」
    設計仕様: design.md §4 V-4 DOM 構成案「<th>Task ID</th><th>担当</th><th>状態</th>」
    Wave 6 T38 緩和: ヘッダ内に <button> が内包されるため文字列包含チェックに緩和（SE 級）。
    """
    task = _make_task()
    result_html = _make_builder(tasks=[task]).render()
    assert "Task ID" in result_html, "ヘッダに「Task ID」が見つかりません。"
    assert "担当" in result_html, "ヘッダに「担当」が見つかりません。"
    assert "状態" in result_html, "ヘッダに「状態」が見つかりません。"


def test_render_v4_contains_tbody():
    """V-4 テーブルに <tbody> が存在すること。"""
    task = _make_task()
    result_html = _make_builder(tasks=[task]).render()
    assert "<tbody>" in result_html, "生成 HTML に <tbody> が見つかりません。"


def test_render_v4_section_has_h2_heading():
    """V-4 セクションに <h2> 見出しが存在すること。"""
    task = _make_task()
    result_html = _make_builder(tasks=[task]).render()
    assert "<h2>" in result_html, "V-4 セクションに <h2> 見出しが見つかりません。"


# ─────────────────────────────────────────────
# Task ID 表示確認
# ─────────────────────────────────────────────


def test_render_v4_task_id_in_row():
    """Task ID が tbody 行に表示されること。

    対応完了条件: W3-B5-T15「テーブルに Task ID カラムが表示される」
    """
    task = _make_task(task_id="W1-B5-T1")
    result_html = _make_builder(tasks=[task]).render()
    assert "W1-B5-T1" in result_html, "Task ID「W1-B5-T1」が HTML に見つかりません。"


def test_render_v4_task_id_row_has_data_attribute():
    """<tr data-task-id="{id}"> 属性が各行に存在すること。

    設計仕様: design.md §4 V-4 DOM 構成案「<tr data-task-id="W1-B5-T1">」
    """
    task = _make_task(task_id="W1-B5-T1")
    result_html = _make_builder(tasks=[task]).render()
    assert 'data-task-id="W1-B5-T1"' in result_html, (
        'data-task-id="W1-B5-T1" 属性が <tr> タグに見つかりません。'
    )


def test_render_v4_multiple_tasks_all_shown():
    """複数 Task がある場合、全 Task が表示されること。

    対応完了条件: W3-B5-T15「全 Task が表示される（Orphan Task 検出用）」
    """
    task1 = _make_task(task_id="W1-B5-T1")
    task2 = _make_task(task_id="W2-B5-T7")
    task3 = _make_task(task_id="W3-B5-T12")
    result_html = _make_builder(tasks=[task1, task2, task3]).render()
    assert "W1-B5-T1" in result_html, "Task W1-B5-T1 が HTML に見つかりません。"
    assert "W2-B5-T7" in result_html, "Task W2-B5-T7 が HTML に見つかりません。"
    assert "W3-B5-T12" in result_html, "Task W3-B5-T12 が HTML に見つかりません。"


# ─────────────────────────────────────────────
# 担当列確認
# ─────────────────────────────────────────────


def test_render_v4_assignee_shown():
    """担当列が表示されること。"""
    task = _make_task(assignee="Sonnet")
    result_html = _make_builder(tasks=[task]).render()
    assert "Sonnet" in result_html, "担当「Sonnet」が HTML に見つかりません。"


def test_render_v4_assignee_dash_when_empty():
    """担当が '-' のとき '-' が表示されること。"""
    task = _make_task(assignee="-")
    result_html = _make_builder(tasks=[task]).render()
    # '-' はハイフン。HTML内に含まれているか確認（他のコンテキストとの区別は不要）
    assert "-" in result_html, "担当が '-' のとき '-' が HTML に見つかりません。"


# ─────────────────────────────────────────────
# 状態バッジ確認（design.md §4 V-4 DOM 構成案）
# ─────────────────────────────────────────────


def test_render_v4_status_badge_not_started():
    """not-started Task に状態バッジ（data-status="not-started"）と「未着手」が表示されること。

    設計仕様: design.md §4 V-4 + §5 Task 状態決定ロジック step 5
    """
    task = _make_task(status="not-started")
    result_html = _make_builder(tasks=[task]).render()
    assert 'data-status="not-started"' in result_html, (
        'data-status="not-started" が見つかりません。'
    )
    assert "未着手" in result_html, "状態バッジの日本語ラベル「未着手」が見つかりません。"


def test_render_v4_status_badge_completed():
    """completed Task に状態バッジ（data-status="completed"）と「完了」が表示されること。

    設計仕様: design.md §5 Task 状態決定ロジック step 4
    """
    task = _make_task(status="completed")
    result_html = _make_builder(tasks=[task]).render()
    assert 'data-status="completed"' in result_html, (
        'data-status="completed" が見つかりません。'
    )
    assert "完了" in result_html, "状態バッジの日本語ラベル「完了」が見つかりません。"


def test_render_v4_status_badge_in_progress():
    """in-progress Task に状態バッジ（data-status="in-progress"）と「進行中」が表示されること。

    設計仕様: design.md §5 Task 状態決定ロジック step 2（SessionState 補完）
    """
    task = _make_task(status="in-progress")
    result_html = _make_builder(tasks=[task]).render()
    assert 'data-status="in-progress"' in result_html, (
        'data-status="in-progress" が見つかりません。'
    )
    assert "進行中" in result_html, "状態バッジの日本語ラベル「進行中」が見つかりません。"


def test_render_v4_status_badge_blocked():
    """blocked Task に状態バッジ（data-status="blocked"）と「ブロック中」が表示されること。

    設計仕様: design.md §5 Task 状態決定ロジック step 3（SessionState 補完）
    """
    task = _make_task(status="blocked")
    result_html = _make_builder(tasks=[task]).render()
    assert 'data-status="blocked"' in result_html, (
        'data-status="blocked" が見つかりません。'
    )
    assert "ブロック中" in result_html, "状態バッジの日本語ラベル「ブロック中」が見つかりません。"


def test_render_v4_badge_has_span_class():
    """状態バッジが <span class="badge" data-status="..."> 形式であること。"""
    task = _make_task(status="in-progress")
    result_html = _make_builder(tasks=[task]).render()
    assert '<span class="badge" data-status=' in result_html, (
        '<span class="badge" data-status=...> 形式のバッジが見つかりません。'
    )


# ─────────────────────────────────────────────
# 状態決定ロジック: SessionState 補完（design.md §5 優先順位）
# ─────────────────────────────────────────────


def test_render_v4_task_status_override_in_progress_from_session_state():
    """TasksParser が not-started を返しても、SessionState の in_progress に含まれる Task は
    in-progress として表示されること。

    設計仕様: design.md §5 Task 状態決定ロジック
      優先順位 2: SESSION_STATE.md「進行中タスク」に記録あり → "in-progress"
      優先順位 5: tasks.md に [ ] チェック → "not-started"
    R-1: 状態値フィールド名が design.md §5 と文字単位で一致すること
    """
    # TasksParser では not-started、SessionState では進行中
    task = _make_task(task_id="W1-B5-T1", status="not-started")
    result_html = _make_builder(
        tasks=[task],
        in_progress=["W1-B5-T1: BaseParser 実装"],
    ).render()
    # in-progress バッジが表示されること
    assert 'data-status="in-progress"' in result_html, (
        "SessionState の in_progress に含まれる Task が in-progress として表示されていません。\n"
        "design.md §5 優先順位 2 が未実装の可能性があります。"
    )


def test_render_v4_task_status_override_blocked_from_session_state():
    """TasksParser が not-started を返しても、SessionState の blocked に含まれる Task は
    blocked として表示されること。

    設計仕様: design.md §5 Task 状態決定ロジック 優先順位 3
    """
    task = _make_task(task_id="W2-B5-T7", status="not-started")
    result_html = _make_builder(
        tasks=[task],
        blocked=["W2-B5-T7: ブロック中の問題"],
    ).render()
    assert 'data-status="blocked"' in result_html, (
        "SessionState の blocked に含まれる Task が blocked として表示されていません。\n"
        "design.md §5 優先順位 3 が未実装の可能性があります。"
    )


def test_render_v4_task_status_override_completed_from_session_state():
    """TasksParser が not-started を返しても、SessionState の completed に含まれる Task は
    completed として表示されること。

    設計仕様: design.md §5 Task 状態決定ロジック 優先順位 1
    """
    task = _make_task(task_id="W1-B5-T1", status="not-started")
    result_html = _make_builder(
        tasks=[task],
        completed=["W1-B5-T1: 完了済み"],
    ).render()
    assert 'data-status="completed"' in result_html, (
        "SessionState の completed に含まれる Task が completed として表示されていません。\n"
        "design.md §5 優先順位 1 が未実装の可能性があります。"
    )


def test_render_v4_session_state_completed_overrides_tasks_parser_not_started():
    """SessionState 優先順位 1（completed）が tasks.md not-started より優先されること。

    design.md §5 優先順位テスト: 1 > 5
    """
    task = _make_task(task_id="W1-B5-T1", status="not-started")
    result_html = _make_builder(
        tasks=[task],
        completed=["W1-B5-T1: 完了"],
        in_progress=["W2-B5-T9: 進行中"],  # 別タスクは影響なし
    ).render()
    # W1-B5-T1 は completed になるはず
    assert 'data-status="completed"' in result_html, (
        "SessionState completed（優先順位1）が tasks.md not-started（優先順位5）に負けています。"
    )


def test_render_v4_tasks_parser_completed_status_retained():
    """TasksParser が completed を返した Task は completed のまま表示されること。

    設計仕様: design.md §5 Task 状態決定ロジック step 4（tasks.md の [x]）
    """
    task = _make_task(task_id="W1-B5-T1", status="completed")
    result_html = _make_builder(tasks=[task]).render()
    assert 'data-status="completed"' in result_html, (
        "TasksParser が completed を返した Task が completed で表示されていません。"
    )


# ─────────────────────────────────────────────
# Empty State（Task 0 件）
# ─────────────────────────────────────────────


def test_render_v4_empty_state_when_no_tasks():
    """Task が 0 件のとき「Task 情報なし」または同等の文言が表示されること（empty state）。

    対応完了条件: W3-B5-T15「全 Task が表示される」の逆ケース（0 件時の graceful degradation）
    """
    result_html = _make_builder(tasks=[]).render()
    assert "Task 情報なし" in result_html, (
        "tasks が空のとき「Task 情報なし」が表示されていません。\n"
        "empty state の実装を確認してください。"
    )


def test_render_v4_section_exists_even_when_no_tasks():
    """Task が 0 件でも <section id="v4-tasks"> は存在すること。"""
    result_html = _make_builder(tasks=[]).render()
    assert '<section id="v4-tasks">' in result_html, (
        'Task 0 件でも <section id="v4-tasks"> は表示される必要があります。'
    )


# ─────────────────────────────────────────────
# HTML エスケープ確認（既存パターン踏襲）
# ─────────────────────────────────────────────


def test_render_v4_html_escape_in_task_id():
    """Task ID に HTML 特殊文字が含まれる場合、エスケープされて出力されること。

    既存パターン: builder.py の _render_parser_errors() で html.escape() を使用済み
    Wave 6 T37 緩和: builder.py が自前 `<script>` ブロックを挿入するようになったため、
    自前 script を除去した後の文字列に Task ID 起源の `<script>` が残っていないことを検証する
    二段検証（SE 級）。`&lt;script&gt;` の存在検証は元の HTML に対して行う。
    """
    task = _make_task(task_id="<script>alert('xss')</script>")
    result_html = _make_builder(tasks=[task]).render()
    stripped = re.sub(r"<script\b[^>]*>.*?</script>", "", result_html, flags=re.DOTALL)
    assert "<script>" not in stripped, (
        "Task ID の HTML エスケープが行われていません（XSS リスク / 自前 script 除外後検査）。"
    )
    assert "&lt;script&gt;" in result_html, (
        "HTML エスケープ後の &lt;script&gt; が見つかりません。"
    )


def test_render_v4_html_escape_in_assignee():
    """担当列に HTML 特殊文字が含まれる場合、エスケープされること。"""
    task = _make_task(assignee='<b>hack"er</b>')
    result_html = _make_builder(tasks=[task]).render()
    assert "<b>" not in result_html, "担当列の HTML エスケープが行われていません。"


# ─────────────────────────────────────────────
# 回帰テスト: V-1 / V-2 / parser_errors が壊れていないこと
# ─────────────────────────────────────────────


def test_v1_section_not_broken_by_v4():
    """V-4 実装後も V-1 セクションが正常に生成されること（回帰テスト）。"""
    task = _make_task()
    result_html = _make_builder(tasks=[task]).render()
    assert '<section id="v1-project-summary">' in result_html, (
        "V-4 追加後に V-1 セクションが消えています。回帰テスト失敗。"
    )
    assert "LAM Dashboard" in result_html, "LAM Dashboard タイトルが消えています。"


def test_v2_section_not_broken_by_v4():
    """V-4 実装後も V-2 セクションが正常に生成されること（回帰テスト）。"""
    task = _make_task()
    result_html = _make_builder(tasks=[task]).render()
    assert '<section id="v2-milestones">' in result_html, (
        "V-4 追加後に V-2 セクションが消えています。回帰テスト失敗。"
    )


def test_parser_errors_not_broken_by_v4():
    """V-4 実装後も parser_errors セクションが正常に動作すること（回帰テスト）。"""
    from dashboard.builder import DashboardBuilder
    from dashboard.models import DashboardData

    data = DashboardData(parser_errors=["Tasks: ファイル不在"])
    builder = DashboardBuilder(data)
    result_html = builder.render()
    assert '<section id="parser-errors">' in result_html, (
        "V-4 追加後に parser-errors セクションが壊れています。"
    )
