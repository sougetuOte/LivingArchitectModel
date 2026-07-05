"""test_wave8_stage4_integration.py - Stage 4 統合テスト（W8-B5-T109）

対応仕様:
  - docs/specs/b4-dashboard/wave8/tasks.md §3 Stage 4 / §3.5 / §6 T109
  - docs/specs/b4-dashboard/wave8/design.md v0.2.3 §5-6（Merger + Builder 統合）
  - docs/specs/b4-dashboard/wave8/requirements.md v0.2.3
        FR-W8-1〜6 / FR-W8-N2 / AC-W8-1〜7 + AC-W8-N1 / NFR-W8-1〜5

実行前提:
  - Stage 1〜3 完了済み（pytest 435 PASS + 10 SKIP 想定 / 本ファイル追加後 +9 で 444 PASS + 14 SKIP）
  - Lighthouse Accessibility 計測（T-S4-2）は L1 リレー検証（T110）で実施。
    本ファイルでは skip。
  - 手動確認（T-S4-4 / AC-W8-N1 視覚確認 / chip 解消確認）は L1 + chrome-devtools-mcp
    で T110 内で実施。本ファイルでは skip。
  - 自動テスト（静的 5 件）はこのファイルで pytest により自動実行される。

テスト件数:
  - MCP skip: 4 件（T-S4-06 〜 T-S4-09）
  - 自動: 5 件（T-S4-01 〜 T-S4-05）
  - 合計: 9 件（tasks.md §6 T109 「静的 5 + MCP skip 4」に対応）

Wave 7 Stage 4（test_wave7_stage4_integration.py）踏襲パターン。
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

# .claude/scripts を sys.path に追加（既存テストと同じパターン）
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_BUILD_SCRIPT = _PROJECT_ROOT / ".claude" / "scripts" / "build_dashboard.py"
_FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "wave8"


# ─────────────────────────────────────────────
# 抽出ヘルパー（test_wave8_v2_v4_ssot_alignment.py 準拠）
# ─────────────────────────────────────────────

_V2_CARD_PATTERN = re.compile(r'<article class="milestone-card" data-milestone="([^"]*)">')
_V4_OPTION_PATTERN = re.compile(
    r'<select id="filter-milestone"[^>]*>(.*?)</select>', re.DOTALL
)
_V4_OPTION_VALUE_PATTERN = re.compile(r'<option value="([^"]*)">')


def _extract_v2_milestone_names(html: str) -> list[str]:
    return _V2_CARD_PATTERN.findall(html)


def _extract_v4_filter_milestone_values(html: str) -> list[str]:
    select_match = re.search(_V4_OPTION_PATTERN, html)
    assert select_match is not None, (
        '<select id="filter-milestone"> が HTML に見つかりません。'
    )
    select_block = select_match.group(1)
    all_values = _V4_OPTION_VALUE_PATTERN.findall(select_block)
    return [v for v in all_values if v != ""]


# ─────────────────────────────────────────────
# build_dashboard.py ロード + 制御ルート構築（test_wave8_tasks_milestone_integration.py 準拠）
# ─────────────────────────────────────────────


def _load_build_module():
    """build_dashboard.py を importlib でロードして build() 関数を取得する。"""
    spec = importlib.util.spec_from_file_location(
        "build_dashboard_w8_stage4", _BUILD_SCRIPT
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _build_controlled_root(
    tmp_path: Path, *, session_text: str, tasks_text: str
) -> Path:
    """fixture テキストから制御済みプロジェクトルートを構築する。"""
    root = tmp_path / "project"
    root.mkdir()

    dotclaude = root / ".claude"
    dotclaude.mkdir()
    (dotclaude / "current-phase.md").write_text(
        "# Current Phase\n\n**BUILDING**\n", encoding="utf-8"
    )

    (root / "SESSION_STATE.md").write_text(session_text, encoding="utf-8")

    specs_dir = root / "docs" / "specs" / "wave8-stage4-fixture"
    specs_dir.mkdir(parents=True)
    (specs_dir / "tasks.md").write_text(tasks_text, encoding="utf-8")

    return root


@pytest.fixture
def fixture_texts() -> tuple[str, str]:
    """session_minimal.txt / tasks_with_extra.txt を読み込んで返す。

    fixture 内容:
      - session_minimal.txt: B-5 のみ Task ID
      - tasks_with_extra.txt: B-4/B-5/B-6 Task ID
    """
    session_text = (_FIXTURES_DIR / "session_minimal.txt").read_text(encoding="utf-8")
    tasks_text = (_FIXTURES_DIR / "tasks_with_extra.txt").read_text(encoding="utf-8")
    return session_text, tasks_text


# ═════════════════════════════════════════════
# 自動テスト（静的 5 件 / T-S4-01 〜 T-S4-05）
# ═════════════════════════════════════════════


# ─────────────────────────────────────────────
# T-S4-01: Merger + Builder 統合生成成功（自動）
# ─────────────────────────────────────────────


def test_t_s4_01_integrated_build_via_orchestrator(tmp_path, fixture_texts) -> None:
    """build_dashboard.py の build() 経由で dashboard.html 生成が成功すること。

    種別: 自動

    設計根拠:
        tasks.md §6 T109 (1) Merger + Builder 統合
        design.md §5 build_dashboard.py オーケストレータ変更
        AC-W8-1 (Merger 動作) + AC-W8-2/-3 (V-2/V-4 統合) の統合動作保証

    検証:
        1. build() が正常終了して dashboard.html が生成されること
        2. 生成された HTML が DOCTYPE 宣言を含むこと
        3. B-4/B-5/B-6 の 3 Milestone すべてが HTML に反映されていること（Merger 動作の end-to-end 保証）
    """
    session_text, tasks_text = fixture_texts
    root = _build_controlled_root(
        tmp_path, session_text=session_text, tasks_text=tasks_text
    )
    mod = _load_build_module()

    output = tmp_path / "dashboard.html"
    mod.build(project_root=root, output_path=output)

    assert output.is_file(), "build() 経由での dashboard.html 生成に失敗しました。"

    html = output.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html, (
        "生成された dashboard.html が DOCTYPE 宣言を含みません。"
    )

    for name in ("B-4", "B-5", "B-6"):
        assert f'data-milestone="{name}"' in html, (
            f"Merger 統合結果として Milestone {name} が HTML に反映されていません。\n"
            "AC-W8-1: MilestoneSourceMerger の集合演算が正しく機能していない可能性。"
        )


# ─────────────────────────────────────────────
# T-S4-02: V-2 / V-4 SSOT 一致 (統合 build() 経由 / AC-W8-2)
# ─────────────────────────────────────────────


def test_t_s4_02_v2_v4_ssot_alignment_via_orchestrator(
    tmp_path, fixture_texts
) -> None:
    """build() 経由生成の HTML で V-2 Milestone カード名の集合と V-4 フィルタ選択肢の集合が一致すること。

    種別: 自動

    設計根拠:
        tasks.md §6 T109 (2) V-2/V-4 Milestone 集合完全一致
        requirements.md AC-W8-2 / FR-W8-2 / FR-W8-3

    T105（test_wave8_v2_v4_ssot_alignment.py）は DashboardBuilder 単体で
    data.milestones を直接構築して検証していたが、本テストは build_dashboard.py
    オーケストレータ経由（Merger + Builder 統合）で SSOT が保たれることを確認する。

    検証:
        V-2 milestone-card の data-milestone 値の集合 == V-4 filter-milestone の option value 集合
    """
    session_text, tasks_text = fixture_texts
    root = _build_controlled_root(
        tmp_path, session_text=session_text, tasks_text=tasks_text
    )
    mod = _load_build_module()

    output = tmp_path / "dashboard.html"
    mod.build(project_root=root, output_path=output)
    html = output.read_text(encoding="utf-8")

    v2_names = set(_extract_v2_milestone_names(html))
    v4_values = set(_extract_v4_filter_milestone_values(html))

    assert v2_names, "V-2 milestone-card が HTML に 1 件も見つかりません。"
    assert v4_values, "V-4 filter-milestone の option が HTML に 1 件も見つかりません。"

    assert v2_names == v4_values, (
        f"V-2 と V-4 の Milestone 集合が不一致です（AC-W8-2 違反）。\n"
        f"  V-2 のみ: {v2_names - v4_values}\n"
        f"  V-4 のみ: {v4_values - v2_names}\n"
        f"  V-2 全体: {sorted(v2_names)}\n"
        f"  V-4 全体: {sorted(v4_values)}"
    )


# ─────────────────────────────────────────────
# T-S4-03: tasks.md 由来 Milestone HTML 表示 + unknown バッジ (AC-W8-3 / AC-W8-N1)
# ─────────────────────────────────────────────


def test_t_s4_03_tasks_md_milestones_reflected_with_unknown_badge(
    tmp_path, fixture_texts
) -> None:
    """tasks.md にのみ存在する Milestone (B-4/B-6) が HTML に反映され、`data-status="unknown"` バッジが付くこと。

    種別: 自動

    設計根拠:
        tasks.md §6 T109 (3) tasks.md 由来 Milestone HTML 表示
        requirements.md AC-W8-3 / AC-W8-N1 / FR-W8-N2

    T106（test_wave8_tasks_milestone_integration.py）は単一 Milestone (B-4) を対象に
    <article> / <option> / unknown バッジを個別に検証していたが、本テストは
    Stage 4 統合レベルで tasks 由来 Milestone の反映 + unknown バッジ表示が
    同時に成立することを最終確認する。

    検証:
        1. B-4 と B-6 の両方が V-4 <option> に含まれる
        2. HTML 内に `data-status="unknown"` バッジが存在
        3. session 由来 B-5 は保持され、status="unknown" にならない
    """
    session_text, tasks_text = fixture_texts
    root = _build_controlled_root(
        tmp_path, session_text=session_text, tasks_text=tasks_text
    )
    mod = _load_build_module()

    output = tmp_path / "dashboard.html"
    mod.build(project_root=root, output_path=output)
    html = output.read_text(encoding="utf-8")

    # 検証 1: B-4/B-6 が V-4 フィルタに含まれる
    assert '<option value="B-4">' in html, (
        "tasks.md 由来のみの Milestone B-4 が V-4 フィルタ選択肢に反映されていません。"
    )
    assert '<option value="B-6">' in html, (
        "tasks.md 由来のみの Milestone B-6 が V-4 フィルタ選択肢に反映されていません。"
    )

    # 検証 2: unknown バッジが HTML に存在
    assert 'data-status="unknown"' in html, (
        'tasks.md 由来のみの Milestone に `data-status="unknown"` バッジが描画されていません。\n'
        "AC-W8-N1 違反。"
    )

    # 検証 3: session 由来 B-5 が unknown 化されていないこと（Merger の status 保持動作確認）
    # B-5 の milestone-card ブロックを抜き出して status 属性を確認
    b5_pattern = re.compile(
        r'<article class="milestone-card" data-milestone="B-5">(.*?)</article>',
        re.DOTALL,
    )
    b5_match = b5_pattern.search(html)
    assert b5_match is not None, "B-5 の milestone-card が HTML に見つかりません。"
    b5_block = b5_match.group(1)
    assert 'data-status="unknown"' not in b5_block, (
        "session 由来の B-5 が誤って status=\"unknown\" 化されています。\n"
        "AC-W8-1 違反: Merger の status 保持ロジックが機能していません。"
    )


# ─────────────────────────────────────────────
# T-S4-04: CSS 予算最終確認 (AC-W8-5 / NFR-W8-4)
# ─────────────────────────────────────────────


def test_t_s4_04_css_budget_within_limit() -> None:
    """DashboardBuilder が生成する inline CSS の utf-8 バイト数が 16,384 bytes 以下であること。

    種別: 自動

    設計根拠:
        tasks.md §6 T109 (4) CSS 予算最終確認
        requirements.md NFR-W8-4 (SHOULD) / AC-W8-5

    計測方法:
        len(_render_style().encode("utf-8"))
        （I-W8-1 統一 / T108 CSS 予算実測の恒久的 regression ガード）

    Wave 7 終端: 10,400 bytes
    Wave 8 終端目標: 10,717 bytes（+317 bytes / T104 unknown バッジ CSS 追加分）
    """
    from dashboard.builder import DashboardBuilder
    from dashboard.models import DashboardData

    builder = DashboardBuilder(DashboardData())
    css = builder._render_style()
    size = len(css.encode("utf-8"))

    BUDGET = 16_384
    assert size <= BUDGET, (
        f"CSS 予算超過（NFR-W8-4 違反）: {size} bytes > {BUDGET} bytes\n"
        f"Wave 7 終端 10,400 bytes / Wave 8 想定 10,717 bytes からの逸脱。\n"
        f"AC-W8-5 違反。"
    )


# ─────────────────────────────────────────────
# T-S4-05: Wave 7 後方互換維持（既存機能退行なし / NFR-W8-2）
# ─────────────────────────────────────────────


def test_t_s4_05_wave7_backward_compatibility_preserved(
    tmp_path, fixture_texts
) -> None:
    """Wave 7 機能（フィルタ UI / ソートボタン / V-1〜V-4 全セクション / Assignee 列）の退行なし。

    種別: 自動

    設計根拠:
        tasks.md §6 T109 (5) 既存テスト退行ゼロ
        requirements.md NFR-W8-2（既存 398 テスト PASS）
        Wave 7 T-S4-9 パターンを Wave 8 build() 経由に拡張。

    検証（build() 経由生成 HTML に以下のマーカーが全て含まれること）:
        - id="filter-status"    : Wave 6 T40 状態フィルタ
        - id="filter-text"      : Wave 6 T40 テキストフィルタ
        - id="filter-milestone" : Wave 6 T40 Milestone フィルタ（Wave 8 で SSOT 化）
        - class="sort-btn"      : Wave 6 T38 ソートボタン
        - id="v1-project-summary" : V-1 セクション
        - id="v2-milestones"    : V-2 セクション（Wave 7 T51 改修済 / Wave 8 SSOT 化）
        - id="v4-tasks"         : V-4 セクション
    """
    session_text, tasks_text = fixture_texts
    root = _build_controlled_root(
        tmp_path, session_text=session_text, tasks_text=tasks_text
    )
    mod = _load_build_module()

    output = tmp_path / "dashboard.html"
    mod.build(project_root=root, output_path=output)
    html = output.read_text(encoding="utf-8")

    # フィルタ UI マーカー
    for marker, origin in [
        ('id="filter-status"', "Wave 6 T40 状態フィルタ"),
        ('id="filter-text"', "Wave 6 T40 テキストフィルタ"),
        ('id="filter-milestone"', "Wave 6 T40 Milestone フィルタ（Wave 8 で SSOT 化）"),
        ('class="sort-btn"', "Wave 6 T38 ソートボタン"),
    ]:
        assert marker in html, (
            f"{marker} が build() 出力に存在しません。\n"
            f"{origin} が退行しています（NFR-W8-2 違反）。"
        )

    # V-1 〜 V-4 セクション
    for section_id, origin in [
        ("v1-project-summary", "V-1 セクション（Wave 3 以前）"),
        ("v2-milestones", "V-2 セクション（Wave 7 T51 改修 / Wave 8 SSOT 化）"),
        ("v4-tasks", "V-4 セクション（Wave 2）"),
    ]:
        assert f'id="{section_id}"' in html, (
            f'id="{section_id}" が build() 出力に存在しません。\n'
            f"{origin} が退行しています（NFR-W8-2 違反）。"
        )


# ═════════════════════════════════════════════
# MCP skip 4 件（T-S4-06 〜 T-S4-09 / L1 リレー検証 = T110 で実施）
# ═════════════════════════════════════════════


# ─────────────────────────────────────────────
# T-S4-06: Lighthouse Accessibility ≥ 95（skip / L1 実機計測 = T110）
# ─────────────────────────────────────────────


@pytest.mark.skip(
    reason=(
        "chrome-devtools-mcp 駆動 / L1 リレー検証で実施 / "
        "Wave 8 Stage 4 T110 完了時点で計測予定 / AC-W8-6 / NFR-W8-5"
    )
)
def test_t_s4_06_lighthouse_accessibility_95plus() -> None:
    """Lighthouse Accessibility スコアが 95 以上であること（Wave 7 終端値からの退行ゼロ）。

    種別: skip（chrome-devtools-mcp 駆動 / L1 リレー検証）

    対応仕様:
        requirements.md AC-W8-6 / NFR-W8-5 / tasks.md §3 Stage 4 T-S4-2

    将来の再活性化手順（chrome-devtools-mcp 利用可能環境）:
        1. dashboard.html をブラウザまたは MCP new_page でロード
        2. mcp__plugin_chrome-devtools-mcp_chrome-devtools__lighthouse_audit を実行
           （snapshot モード）
        3. Accessibility カテゴリのスコアを取得して assert score >= 95 を検証

    MCP 再活性化コード例（コメント形式）:
        # page = mcp.new_page(url="file:///path/to/dashboard.html")
        # result = mcp.lighthouse_audit(page_id=page.id, categories=["accessibility"])
        # score = result["categories"]["accessibility"]["score"] * 100
        # assert score >= 95, f"Accessibility score {score} < 95 (AC-W8-6)"
    """
    pytest.skip(
        "chrome-devtools-mcp 駆動 / L1 リレー検証で実施 / "
        "T110 完了時点で計測予定 / AC-W8-6"
    )


# ─────────────────────────────────────────────
# T-S4-07: V-2 / V-4 SSOT 手動視覚確認（skip / L1 実機計測 = T110）
# ─────────────────────────────────────────────


@pytest.mark.skip(
    reason=(
        "chrome-devtools-mcp 駆動 / L1 が V-2 Milestone カード名と V-4 フィルタ選択肢の "
        "視覚一致を確認 / AC-W8-2 / T-S4-4 対応"
    )
)
def test_t_s4_07_v2_v4_ssot_visual_confirmation() -> None:
    """dashboard.html をブラウザで開き、V-2 Milestone カード名と V-4 フィルタ選択肢が
    視覚的に完全一致することを確認する（AC-W8-2 の手動確認手段）。

    種別: skip（chrome-devtools-mcp 駆動 / L1 手動実行）

    対応仕様:
        requirements.md AC-W8-2 / tasks.md §3 Stage 4 T-S4-4
        自動集合比較は T-S4-02 で実施済み。本テストは視覚的な整合性の最終確認を担当。

    将来の再活性化手順（chrome-devtools-mcp 利用可能環境）:
        1. dashboard.html を MCP でロード
        2. V-2 セクションと V-4 フィルタ selectbox を並べてスクショ記録
        3. 目視で Milestone 名の集合が一致することを確認

    MCP 再活性化コード例（コメント形式）:
        # page = mcp.new_page(url="file:///path/to/dashboard.html")
        # cards = mcp.query_selector_all(page_id=page.id, selector=".milestone-card")
        # v2_names = {mcp.get_attribute(c, "data-milestone") for c in cards}
        # options = mcp.query_selector_all(page_id=page.id,
        #                                  selector="#filter-milestone > option")
        # v4_values = {mcp.get_attribute(o, "value") for o in options if
        #              mcp.get_attribute(o, "value") != ""}
        # assert v2_names == v4_values, f"視覚不一致: V-2={v2_names} V-4={v4_values}"
    """
    pytest.skip(
        "chrome-devtools-mcp 駆動 / L1 が V-2/V-4 SSOT 視覚確認 / "
        "SESSION_STATE Stage 4 記録参照"
    )


# ─────────────────────────────────────────────
# T-S4-08: "unknown" バッジ視覚確認（skip / L1 実機計測 = T110）
# ─────────────────────────────────────────────


@pytest.mark.skip(
    reason=(
        "chrome-devtools-mcp 駆動 / L1 が unknown バッジ (#9ca3af / gray-9 相当) の "
        "視覚表示を確認 / AC-W8-N1"
    )
)
def test_t_s4_08_unknown_badge_visual_confirmation() -> None:
    """tasks.md 由来のみの Milestone に "不明" バッジが gray-9 相当色で視覚表示されること。

    種別: skip（chrome-devtools-mcp 駆動 / L1 手動実行）

    対応仕様:
        requirements.md AC-W8-N1 / FR-W8-N2
        CSS ルール `.badge[data-status="unknown"]` の色（#9ca3af）が
        実際にブラウザで期待通りにレンダリングされることを視覚確認する。

    将来の再活性化手順（chrome-devtools-mcp 利用可能環境）:
        1. tasks.md 由来のみの Milestone を含む fixture で dashboard.html をロード
        2. .badge[data-status="unknown"] の computed background-color を取得
        3. 期待値 rgb(156, 163, 175) (= #9ca3af) と一致することを確認

    MCP 再活性化コード例（コメント形式）:
        # page = mcp.new_page(url="file:///path/to/dashboard.html")
        # badge = mcp.query_selector(page_id=page.id,
        #                            selector='.badge[data-status="unknown"]')
        # bg = mcp.get_computed_style(badge, "background-color")
        # assert bg in ("rgb(156, 163, 175)", "#9ca3af"), f"期待外の色: {bg}"
    """
    pytest.skip(
        "chrome-devtools-mcp 駆動 / L1 が unknown バッジ視覚確認 / "
        "SESSION_STATE Stage 4 記録参照 / AC-W8-N1"
    )


# ─────────────────────────────────────────────
# T-S4-09: chip task_68008f88 解消確認（skip / L1 記録 = T110）
# ─────────────────────────────────────────────


@pytest.mark.skip(
    reason=(
        "L1 判定 + SESSION_STATE 記録 / chip task_68008f88 (Milestone フィルタ仕様乖離) "
        "の解消宣言は T110 で実施 / AC-W8-2 / tasks.md §3 Stage 4 T-S4-5"
    )
)
def test_t_s4_09_chip_task_68008f88_resolution() -> None:
    """起源 chip task_68008f88（Milestone フィルタ仕様乖離）が Wave 8 で解消されたこと。

    種別: skip（L1 記録 / T110 で実施）

    対応仕様:
        tasks.md §3 Stage 4 T-S4-5 / requirements.md AC-W8-2
        Wave 8 の起点となった chip の解消は、以下 3 点の複合結果として判定される:
          1. T-S4-02 (V-2/V-4 SSOT 自動一致確認) PASS
          2. T-S4-07 (V-2/V-4 SSOT 視覚一致確認) PASS
          3. L1 による SESSION_STATE.md への正式解消記録

    自動判定は困難（複合状態判定 + L1 の主観的最終確認を含む）ため skip とし、
    T110 で L1 が SESSION_STATE.md に「chip task_68008f88 解消確認: <日時>」を
    追記した時点で本項目を PASS 扱いとする。

    将来の再活性化手順:
        - SESSION_STATE.md 内の chip 解消記録の存在を grep で確認する自動化は可能
          （例: `assert "chip task_68008f88 解消" in SESSION_STATE.md`）
        - ただし現行仕様では L1 承認 + 手動記録を優先し、本テストは skip 維持。
    """
    pytest.skip(
        "L1 判定 + SESSION_STATE 記録 / T110 で実施 / "
        "chip task_68008f88 解消確認 / AC-W8-2"
    )
