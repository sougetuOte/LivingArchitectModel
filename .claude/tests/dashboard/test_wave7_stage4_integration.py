"""test_wave7_stage4_integration.py - Stage 4 統合テスト（W7-B5-T54）

対応仕様:
  - docs/specs/b4-dashboard/wave7/tasks.md §3 Stage 4 / §3.5 / §6 T54
  - docs/specs/b4-dashboard/wave7/design.md v0.2.4 §8（V-2 セクション化）
  - docs/specs/b4-dashboard/wave7/requirements.md v0.2.4
        FR-W7-1〜4 / AC-W7-3〜9 / NFR-W7-1

実行前提:
  - Stage 1〜3 完了済み（pytest 394 PASS + 5 SKIP 想定）
  - Lighthouse Accessibility 計測（T-S4-1 / T-S4-2）は L1 リレー検証で実施。
    本ファイルでは skip。
  - 手動確認（T-S4-3〜T-S4-5）は L1 + chrome-devtools-mcp で実施。本ファイルでは skip。
  - 自動テスト（T-S4-6〜T-S4-9）はこのファイルで pytest により自動実行される。

テスト件数:
  - MCP skip: 5 件（T-S4-1〜T-S4-5）
  - 自動: 4 件（T-S4-6〜T-S4-9）
  - 合計: 9 件
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# .claude/scripts を sys.path に追加（既存テストと同じパターン）
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from dashboard.builder import DashboardBuilder
from dashboard.models import DashboardData, MilestoneInfo, TaskInfo


# ─────────────────────────────────────────────
# テスト用フィクスチャヘルパー
# ─────────────────────────────────────────────


def _make_builder_with_full_data() -> DashboardBuilder:
    """統合テスト用の現実的なデータを持つ DashboardBuilder を生成する。

    Wave 6 Stage 4 踏襲元（test_wave6_stage4_integration.py）から継承し、
    Wave 7 機能（Assignee タグ）付き Tasks を追加した単一 Milestone B-5 版。
    複数テスト（T-S4-7 / T-S4-8 / T-S4-9）で再利用する。
    """
    milestone = MilestoneInfo(
        name="B-5",
        current_step="BUILDING",
        status="in-progress",
    )
    tasks = [
        TaskInfo(id="W1-B5-T1", milestone="B-5", assignee="Sonnet", status="completed"),
        TaskInfo(id="W2-B5-T9", milestone="B-5", assignee="Sonnet", status="completed"),
        TaskInfo(id="W3-B5-T14", milestone="B-5", assignee="Sonnet", status="completed"),
        TaskInfo(id="W3-B5-T15", milestone="B-5", assignee="Sonnet", status="completed"),
        TaskInfo(id="W6-B5-T31", milestone="B-5", assignee="Sonnet", status="completed"),
        TaskInfo(id="W6-B5-T32", milestone="B-5", assignee="Sonnet", status="completed"),
        TaskInfo(id="W6-B5-T33", milestone="B-5", assignee="Sonnet", status="completed"),
        TaskInfo(id="W6-B5-T34", milestone="B-5", assignee="Sonnet", status="completed"),
        TaskInfo(id="W6-B5-T35", milestone="B-5", assignee="Sonnet", status="completed"),
        TaskInfo(id="W6-B5-T36", milestone="B-5", assignee="Sonnet", status="completed"),
        TaskInfo(id="W6-B5-T37", milestone="B-5", assignee="Sonnet", status="completed"),
        TaskInfo(id="W6-B5-T38", milestone="B-5", assignee="Sonnet", status="completed"),
        TaskInfo(id="W6-B5-T39", milestone="B-5", assignee="Sonnet", status="completed"),
        TaskInfo(id="W6-B5-T40", milestone="B-5", assignee="Sonnet", status="completed"),
        TaskInfo(id="W6-B5-T41", milestone="B-5", assignee="Sonnet", status="completed"),
        TaskInfo(id="W6-B5-T42", milestone="B-5", assignee="Sonnet", status="completed"),
        TaskInfo(id="W7-B5-T44", milestone="B-5", assignee="Sonnet", status="completed"),
        TaskInfo(id="W7-B5-T45", milestone="B-5", assignee="Sonnet", status="completed"),
        TaskInfo(id="W7-B5-T46", milestone="B-5", assignee="Sonnet", status="completed"),
        TaskInfo(id="W7-B5-T47", milestone="B-5", assignee="Sonnet", status="completed"),
        TaskInfo(id="W7-B5-T48", milestone="B-5", assignee="Sonnet", status="completed"),
        TaskInfo(id="W7-B5-T49", milestone="B-5", assignee="Sonnet", status="completed"),
        TaskInfo(id="W7-B5-T50", milestone="B-5", assignee="Sonnet", status="completed"),
        TaskInfo(id="W7-B5-T51", milestone="B-5", assignee="Sonnet", status="completed"),
        TaskInfo(id="W7-B5-T52", milestone="B-5", assignee="Sonnet", status="completed"),
        TaskInfo(id="W7-B5-T53", milestone="B-5", assignee="Sonnet", status="completed"),
        TaskInfo(id="W7-B5-T54", milestone="B-5", assignee="Sonnet", status="in-progress"),
        TaskInfo(id="W7-B5-T55", milestone="B-5", assignee="-", status="not-started"),
    ]
    data = DashboardData(
        milestones=[milestone],
        waves=[],
        tasks=tasks,
        completed=[t.id for t in tasks if t.status == "completed"],
        in_progress=[t.id for t in tasks if t.status == "in-progress"],
        blocked=[],
        current_phase="BUILDING",
        generated_at="2026-06-28T00:00:00",
        parser_errors=[],
    )
    return DashboardBuilder(data)


def _make_builder_with_multi_milestone_data() -> DashboardBuilder:
    """Wave 7 統合テスト用 — 複数 Milestone（B-4 + B-5）+ Assignee タグ付き DashboardBuilder。

    T-S4-6 / T-S4-7 で使用する Wave 7 固有の拡張フィクスチャ。
    B-5 が先に記述されているが、render() 内で B-4 が昇順ソートで先に来ることを確認できる。
    各 Milestone に assignee="Sonnet" 付き TaskInfo を 2 件以上配置。
    """
    milestone_b4 = MilestoneInfo(
        name="B-4",
        current_step="AUDITING",
        status="completed",
    )
    milestone_b5 = MilestoneInfo(
        name="B-5",
        current_step="BUILDING",
        status="in-progress",
    )
    tasks = [
        # B-4 タスク（Assignee 付き）
        TaskInfo(id="W1-B4-T1", milestone="B-4", assignee="Sonnet", status="completed"),
        TaskInfo(id="W2-B4-T2", milestone="B-4", assignee="Sonnet", status="completed"),
        # B-5 タスク（Assignee 付き）
        TaskInfo(id="W1-B5-T1", milestone="B-5", assignee="Sonnet", status="completed"),
        TaskInfo(id="W7-B5-T47", milestone="B-5", assignee="Sonnet", status="completed"),
        TaskInfo(id="W7-B5-T48", milestone="B-5", assignee="Sonnet", status="completed"),
        TaskInfo(id="W7-B5-T54", milestone="B-5", assignee="Sonnet", status="in-progress"),
    ]
    data = DashboardData(
        # 意図的に B-5 を先に渡す（ソート検証のため）
        milestones=[milestone_b5, milestone_b4],
        waves=[],
        tasks=tasks,
        completed=[t.id for t in tasks if t.status == "completed"],
        in_progress=[t.id for t in tasks if t.status == "in-progress"],
        blocked=[],
        current_phase="BUILDING",
        generated_at="2026-06-28T00:00:00",
        parser_errors=[],
    )
    return DashboardBuilder(data)


# ─────────────────────────────────────────────
# T-S4-1: Lighthouse Accessibility ≥ 95（skip / L1 実機計測待ち）
# ─────────────────────────────────────────────


@pytest.mark.skip(
    reason=(
        "chrome-devtools-mcp 駆動 / L1 リレー検証で実施 / "
        "Wave 7 Stage 4 完了時点で計測予定 / AC-W7-6"
    )
)
def test_t_s4_01_lighthouse_accessibility_95plus() -> None:
    """Lighthouse Accessibility スコアが 95 以上であること（Wave 6 終端値 97 からの退行ゼロ）。

    種別: skip（chrome-devtools-mcp 駆動 / L1 リレー検証）

    対応仕様:
        requirements.md AC-W7-6 / NFR-W7-2 / design.md §4 Success Criteria
        tasks.md §3 Stage 4 T-S4-1 / §6 T55

    将来の再活性化手順（chrome-devtools-mcp 利用可能環境）:
        1. dashboard.html をブラウザで開く（または MCP new_page でロード）
        2. mcp__plugin_chrome-devtools-mcp_chrome-devtools__lighthouse_audit を実行
           （snapshot モード / AC-W7-6 の計測方法）
        3. Accessibility カテゴリのスコアを取得して assert score >= 95 を検証
        4. Wave 6 終端値 97 から退行していないことを確認
        5. 95 未達時は Wave 6 T43 相当の調整ループを参照
           （aria-* 再検証 → Lighthouse 修正サイクル）

    MCP 再活性化コード例（コメント形式）:
        # page = mcp.new_page(url="file:///path/to/dashboard.html")
        # result = mcp.lighthouse_audit(page_id=page.id, categories=["accessibility"])
        # score = result["categories"]["accessibility"]["score"] * 100
        # assert score >= 95, f"Accessibility score {score} < 95 (AC-W7-6)"
    """
    pytest.skip(
        "chrome-devtools-mcp 駆動 / L1 リレー検証で実施 / "
        "Wave 7 Stage 4 完了時点で計測予定 / AC-W7-6"
    )


# ─────────────────────────────────────────────
# T-S4-2: Lighthouse 全項目記録（skip / chrome-devtools-mcp 駆動）
# ─────────────────────────────────────────────


@pytest.mark.skip(
    reason=(
        "chrome-devtools-mcp 駆動 / L1 が Accessibility / Best Practices / SEO / "
        "Agentic Browsing を記録 / SESSION_STATE に結果記録"
    )
)
def test_t_s4_02_lighthouse_all_categories_recorded() -> None:
    """Lighthouse 全カテゴリ（Accessibility / Best Practices / SEO / Agentic Browsing）が記録されること。

    種別: skip（chrome-devtools-mcp 駆動 / L1 手動実行）

    対応仕様:
        requirements.md NFR-W7-2（MAY 項目）/ tasks.md §3 Stage 4 T-S4-2
        Lighthouse 全項目記録は NFR-W7-2 の任意要件。
        SESSION_STATE.md Stage 4 記録参照。

    将来の再活性化手順（chrome-devtools-mcp 利用可能環境）:
        1. dashboard.html を MCP でロード
        2. lighthouse_audit（全カテゴリモード）を実行
        3. 4 カテゴリすべてのスコアを SESSION_STATE.md に記録
        4. Accessibility は AC-W7-6 基準（≥ 95）を確認

    MCP 再活性化コード例（コメント形式）:
        # result = mcp.lighthouse_audit(page_id=..., categories=[
        #     "accessibility", "best-practices", "seo", "agentic-browsing"
        # ])
        # for cat in ["accessibility", "best-practices", "seo"]:
        #     score = result["categories"][cat]["score"] * 100
        #     print(f"{cat}: {score}")
        # assert result["categories"]["accessibility"]["score"] * 100 >= 95
    """
    pytest.skip(
        "chrome-devtools-mcp 駆動 / L1 が全カテゴリ記録 / "
        "SESSION_STATE Stage 4 記録参照"
    )


# ─────────────────────────────────────────────
# T-S4-3: V-2 複数 Milestone カード視覚確認（skip / chrome-devtools-mcp 駆動）
# ─────────────────────────────────────────────


@pytest.mark.skip(
    reason=(
        "chrome-devtools-mcp 駆動 / L1 が V-2 複数 Milestone カード縦並び表示を視覚確認 / "
        "AC-W7-4 / SESSION_STATE に結果記録"
    )
)
def test_t_s4_03_v2_multiple_milestone_cards_visible() -> None:
    """V-2 ビューで複数 Milestone カードが視覚的に縦並びで表示されること。

    種別: skip（chrome-devtools-mcp 駆動 / L1 手動実行）

    対応仕様:
        requirements.md AC-W7-4 / FR-W7-4 / tasks.md §3 Stage 4 T-S4-7 一部
        V-2 section に 2 件以上の .milestone-card が縦に並んで表示されること。
        静的 HTML 検証は test_wave7_stage3_milestones.py で実施済み。
        本テストは「視覚的に縦並びで表示されること」のブラウザ確認を担当。

    将来の再活性化手順（chrome-devtools-mcp 利用可能環境）:
        1. dashboard.html を MCP でロード（SESSION_STATE.md に B-4 / B-5 両方が存在する状態）
        2. V-2 セクションを目視確認またはスクショ記録
        3. .milestone-card が 2 件以上縦並びで表示されていることを確認
        4. Milestone 名昇順（B-4 → B-5）で並んでいることを確認

    MCP 再活性化コード例（コメント形式）:
        # page = mcp.new_page(url="file:///path/to/dashboard.html")
        # cards = mcp.query_selector_all(page_id=page.id, selector=".milestone-card")
        # assert len(cards) >= 2, f"milestone-card が {len(cards)} 件（期待: ≥ 2 件）"
        # names = [mcp.get_attribute(c, "data-milestone") for c in cards]
        # assert names == sorted(names), f"Milestone 名が昇順でない: {names}"
    """
    pytest.skip(
        "chrome-devtools-mcp 駆動 / L1 が V-2 複数 Milestone カード縦並び表示確認 / "
        "SESSION_STATE Stage 4 記録参照"
    )


# ─────────────────────────────────────────────
# T-S4-4: V-4 Assignee 列に意味データ表示確認（skip / chrome-devtools-mcp 駆動）
# ─────────────────────────────────────────────


@pytest.mark.skip(
    reason=(
        "chrome-devtools-mcp 駆動 / L1 が V-4 Assignee 列に - 以外の値表示を視覚確認 / "
        "AC-W7-3 / SESSION_STATE に結果記録"
    )
)
def test_t_s4_04_v4_assignee_column_displays_meaningful_values() -> None:
    """V-4 ビューの Assignee 列に「-」以外の意味ある値が ≥ 1 件表示されること。

    種別: skip（chrome-devtools-mcp 駆動 / L1 手動実行）

    対応仕様:
        requirements.md AC-W7-3 / FR-W7-2 / FR-W7-3 / tasks.md §3 Stage 4 T-S4-7 一部
        dashboard.html 上で V-4 担当列に「Sonnet」等の意味値が ≥ 1 件表示されること。
        静的 HTML 検証は test_wave7_stage2_assignee.py / T-S4-8 で実施済み。

    将来の再活性化手順（chrome-devtools-mcp 利用可能環境）:
        1. dashboard.html を MCP でロード
        2. V-4 テーブルの tbody 行を走査
        3. 担当列（cells[1]）に「-」以外の値が 1 件以上あることを確認

    MCP 再活性化コード例（コメント形式）:
        # page = mcp.new_page(url="file:///path/to/dashboard.html")
        # rows = mcp.query_selector_all(page_id=page.id,
        #                               selector="#tasks-table tbody tr")
        # assignees = [
        #     mcp.get_text(mcp.query_selector(row, "td:nth-child(2)"))
        #     for row in rows
        # ]
        # meaningful = [a for a in assignees if a != "-"]
        # assert len(meaningful) >= 1, f"意味ある Assignee 値が 0 件（AC-W7-3）"
    """
    pytest.skip(
        "chrome-devtools-mcp 駆動 / L1 が V-4 Assignee 列の意味値確認 / "
        "SESSION_STATE Stage 4 記録参照"
    )


# ─────────────────────────────────────────────
# T-S4-5: Milestone 名昇順視覚確認（skip / chrome-devtools-mcp 駆動）
# ─────────────────────────────────────────────


@pytest.mark.skip(
    reason=(
        "chrome-devtools-mcp 駆動 / L1 が Milestone 名昇順の視覚確認（スクショ）を実施 / "
        "T-S3-4 延長 + T-S4-7 統合 / SESSION_STATE に結果記録"
    )
)
def test_t_s4_05_milestone_name_ascending_order_visual() -> None:
    """dashboard.html 上で Milestone 名昇順が視覚的に確認できること。

    種別: skip（chrome-devtools-mcp 駆動 / L1 手動実行）

    対応仕様:
        tasks.md §3 T-S3-4（手動確認）延長 + tasks.md §3 Stage 4 T-S4-7 統合
        T-S3-4 は Stage 3 完了時の条件付き PASS（実データが 1 件の場合は猶予）。
        本テストは Stage 4 で SESSION_STATE.md に複数 Milestone が存在する状態での
        最終視覚確認（スクショ記録）を担当。

    将来の再活性化手順（chrome-devtools-mcp 利用可能環境）:
        1. SESSION_STATE.md に B-4 / B-5 の両 Milestone が記録されていることを事前確認
        2. dashboard.html を MCP でロード
        3. V-2 セクションのスクショを記録（SESSION_STATE Stage 4 に添付）
        4. Milestone 名が B-4 → B-5 の昇順で縦並びになっていることを目視確認

    MCP 再活性化コード例（コメント形式）:
        # page = mcp.new_page(url="file:///path/to/dashboard.html")
        # cards = mcp.query_selector_all(page_id=page.id, selector=".milestone-card")
        # names = [mcp.get_attribute(c, "data-milestone") for c in cards]
        # assert names == sorted(names), f"Milestone 名が昇順でない: {names}"
        # mcp.screenshot(page_id=page.id, path="v2-milestone-order.png")
    """
    pytest.skip(
        "chrome-devtools-mcp 駆動 / L1 が Milestone 名昇順の視覚確認（スクショ）を実施 / "
        "SESSION_STATE Stage 4 記録参照"
    )


# ─────────────────────────────────────────────
# T-S4-6: 複数 Milestone + Assignee 統合 render() 確認（自動）
# ─────────────────────────────────────────────


def test_t_s4_06_integrated_render_multi_milestone_assignee() -> None:
    """複数 Milestone + Assignee + 厳格 Task ID が組み合わさった統合 render() が成立すること。

    種別: 自動

    設計根拠:
        tasks.md §6 T54 / requirements.md FR-W7-1〜4 / design.md §8
        B-4 / B-5 を含む DashboardData + 各 Milestone に assignee="Sonnet" 付き
        TaskInfo を 2 件以上配置した状態で builder.render() を実行する。

    検証:
        1. render() が例外なく完了すること（統合動作の基本保証）
        2. data-milestone="B-4" と data-milestone="B-5" が共存すること（FR-W7-4 / AC-W7-4）
        3. V-4 テーブルに Assignee セル "Sonnet" が ≥ 1 件含まれること（FR-W7-2 / AC-W7-3）
    """
    builder = _make_builder_with_multi_milestone_data()
    html_output = builder.render()

    # 検証 1: render() が有効な HTML を返すこと
    assert html_output, "render() が空文字列を返しました（統合動作に失敗）"
    assert "<!DOCTYPE html>" in html_output, (
        "render() の出力が有効な HTML ドキュメントではありません。"
    )

    # 検証 2: B-4 / B-5 両方の data-milestone 属性が共存すること
    assert 'data-milestone="B-4"' in html_output, (
        'data-milestone="B-4" が render() 出力に存在しません。\n'
        "requirements.md FR-W7-4 / AC-W7-4: 複数 Milestone の同時表示（MUST）"
    )
    assert 'data-milestone="B-5"' in html_output, (
        'data-milestone="B-5" が render() 出力に存在しません。\n'
        "requirements.md FR-W7-4 / AC-W7-4: 複数 Milestone の同時表示（MUST）"
    )

    # 検証 3: V-4 に Assignee "Sonnet" が ≥ 1 件含まれること
    assert "Sonnet" in html_output, (
        "render() 出力に Assignee 値「Sonnet」が見つかりません。\n"
        "requirements.md FR-W7-2 / AC-W7-3: Assignee 列の意味化（MUST）"
    )


# ─────────────────────────────────────────────
# T-S4-7: 統合 render() で Milestone 名昇順維持（自動）
# ─────────────────────────────────────────────


def test_t_s4_07_milestones_alphabetical_order_in_full_render() -> None:
    """統合 render() で Milestone 名昇順（B-3 < B-4 < B-5）が維持されること。

    種別: 自動

    設計根拠:
        design.md §3 A3-4: 文字列辞書順を採用（文字列 str 比較 / Python sorted() 相当）
        tasks.md §6 T51 完了条件 / requirements.md FR-W7-4

    フィクスチャ:
        B-5 / B-4 / B-3 を意図的に逆順で DashboardData に渡す。
        render() 内の V-2 セクションで昇順ソートが適用されることを確認する。

    検証:
        render() 結果文字列で data-milestone="B-3" の位置 < B-4 < B-5 の位置。
    """
    milestone_b3 = MilestoneInfo(name="B-3", current_step="AUDITING", status="completed")
    milestone_b4 = MilestoneInfo(name="B-4", current_step="AUDITING", status="completed")
    milestone_b5 = MilestoneInfo(name="B-5", current_step="BUILDING", status="in-progress")

    data = DashboardData(
        # 意図的に逆順（B-5 → B-4 → B-3）で渡す
        milestones=[milestone_b5, milestone_b4, milestone_b3],
        waves=[],
        tasks=[],
        current_phase="BUILDING",
        generated_at="2026-06-28T00:00:00",
        parser_errors=[],
    )
    builder = DashboardBuilder(data)
    html_output = builder.render()

    pos_b3 = html_output.index('data-milestone="B-3"')
    pos_b4 = html_output.index('data-milestone="B-4"')
    pos_b5 = html_output.index('data-milestone="B-5"')

    assert pos_b3 < pos_b4, (
        f"B-3 (pos={pos_b3}) が B-4 (pos={pos_b4}) より後に出現しています。\n"
        "design.md §3 A3-4: Milestone 名昇順ソート（文字列辞書順）が機能していません。"
    )
    assert pos_b4 < pos_b5, (
        f"B-4 (pos={pos_b4}) が B-5 (pos={pos_b5}) より後に出現しています。\n"
        "design.md §3 A3-4: Milestone 名昇順ソート（文字列辞書順）が機能していません。"
    )


# ─────────────────────────────────────────────
# T-S4-8: 統合 render() で V-4 Assignee 列に意味値 ≥ 1 件（自動）
# ─────────────────────────────────────────────


def test_t_s4_08_v4_assignee_meaningful_values_in_full_render() -> None:
    """統合 render() で V-4 Assignee 列に「-」以外の値が ≥ 1 件表示されること。

    種別: 自動

    設計根拠:
        requirements.md AC-W7-3 / FR-W7-2 / FR-W7-3
        tasks.md §3 Stage 4 T-S4-7 一部 / §6 T54

    フィクスチャ:
        _make_builder_with_full_data() で assignee="Sonnet" を含む Task を複数配置。

    検証:
        render() 全体に "Sonnet" が出現すること（V-4 テーブルの担当セル由来）。
        V-4 セクションは <section id="v4-tasks"> 内に配置されるため、
        substring 検索で "Sonnet" の存在を確認する。
    """
    builder = _make_builder_with_full_data()
    html_output = builder.render()

    # V-4 セクションが存在することを事前確認
    assert '<section id="v4-tasks">' in html_output, (
        '<section id="v4-tasks"> が render() 出力に存在しません。\n'
        "V-4 Task 一覧セクションが生成されていない可能性があります。"
    )

    # V-4 セクション内に "Sonnet" が出現すること
    v4_start = html_output.index('<section id="v4-tasks">')
    v4_section = html_output[v4_start:]

    assert "Sonnet" in v4_section, (
        "V-4 セクション内に Assignee 値「Sonnet」が見つかりません。\n"
        "requirements.md AC-W7-3: V-4 Assignee 列に「-」以外の意味値が ≥ 1 件必要（MUST）\n"
        "requirements.md FR-W7-2 / FR-W7-3: TasksParser による Assignee 抽出 + V-4 表示"
    )


# ─────────────────────────────────────────────
# T-S4-9: Wave 6 機能の退行なし確認（自動）
# ─────────────────────────────────────────────


def test_t_s4_09_wave6_backward_compatibility_preserved() -> None:
    """Wave 6 機能（フィルタ UI / ソートボタン / V-1〜V-4 全セクション）の退行なし。

    種別: 自動

    設計根拠:
        requirements.md NFR-W7-4（後方互換 MUST）/ AC-W7-7（pytest 全件 PASS）
        tasks.md §5 WBS「既存要件（FR-1〜FR-11）対応」/ NFR-W7-3

    フィクスチャ:
        _make_builder_with_full_data() で Wave 6 実績データ相当の現実的データを使用。

    検証（render() 結果に以下のマーカーが全て含まれること）:
        - id="filter-status"  : Wave 6 状態フィルタ（T40 実装）
        - id="filter-text"    : Wave 6 テキストフィルタ（T40 実装）
        - class="sort-btn"    : Wave 6 ソートボタン（T38 実装）
        - id="v1-project-summary" : V-1 セクション（Wave 3 以前）
        - id="v2-milestones"  : V-2 セクション（T51 Wave 7 改修済）
        - id="v4-tasks"       : V-4 セクション（Wave 2）
    """
    builder = _make_builder_with_full_data()
    html_output = builder.render()

    # Wave 6 フィルタ UI マーカー
    assert 'id="filter-status"' in html_output, (
        'id="filter-status" が render() 出力に存在しません。\n'
        "Wave 6 T40 実装の状態フィルタが退行しています。"
    )
    assert 'id="filter-text"' in html_output, (
        'id="filter-text" が render() 出力に存在しません。\n'
        "Wave 6 T40 実装のテキストフィルタが退行しています。"
    )

    # Wave 6 ソートボタン
    assert 'class="sort-btn"' in html_output, (
        'class="sort-btn" が render() 出力に存在しません。\n'
        "Wave 6 T38 実装のソートボタンが退行しています。"
    )

    # V-1〜V-4 全セクションヘッダー
    for section_id, wave_origin in [
        ("v1-project-summary", "V-1 セクション（Wave 3 以前）"),
        ("v2-milestones", "V-2 セクション（Wave 7 T51 改修済）"),
        ("v4-tasks", "V-4 セクション（Wave 2）"),
    ]:
        assert f'id="{section_id}"' in html_output, (
            f'id="{section_id}" が render() 出力に存在しません。\n'
            f"{wave_origin} が退行しています。\n"
            "requirements.md NFR-W7-4: 後方互換 MUST"
        )
