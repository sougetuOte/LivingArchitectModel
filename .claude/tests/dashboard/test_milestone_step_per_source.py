"""Milestone カードの Step を出所別に描き分ける（wave7/design.md §8 の将来候補の実装）

## 背景

2026-08-20 の実測: Milestone が不在（`SESSION_STATE.md` の宣言欄が「なし」）の状態で
ダッシュボードを開くと、**クローズ済の B-5 が `Step: BUILDING` と表示されていた**。

原因は 2 つの合成:

1. `MilestoneSourceMerger` は SessionState ∪ tasks.md の**和集合**を返す。SessionState 側が
   空でも、`docs/specs/b4-dashboard/tasks.md` に残る B-5 のタスクが Milestone を立てる
2. `builder._render_v2_milestones()` が **全カードにグローバルの `current_phase` を一律で刻む**
   （`ms.current_step` は計算されるが描画で使われない = dead field）

2 は事故ではなく `wave7/design.md` §8 が明記した仕様であり、同節は
「**Milestone 別 Step 管理は将来候補**」とも書いていた。本テストはその将来候補を確定させる。

## 決める規則

| Milestone の出所 | `current_step` |
|:---|:---|
| SessionState が宣言した（= 現に進行中） | **グローバルの現在フェーズ** |
| tasks.md にしか現れない（= 過去の Milestone の残骸） | **`"UNKNOWN"`** |

これは `merger._make_milestone_from_name` の docstring が既に持っている意図
（「完了済み Milestone が誤って not-started 表示されるリスクを回避するため中立な
`unknown` を補完値とする」）を Step にも広げたものである。`SessionStateParser` が
`current_step="UNKNOWN"  # CurrentPhaseParser で補完` と書きながら補完実装が存在しなかった
穴も、これで塞がる。
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from dashboard.builder import DashboardBuilder  # noqa: E402
from dashboard.merger import MilestoneSourceMerger  # noqa: E402
from dashboard.models import DashboardData, MilestoneInfo  # noqa: E402


# --------------------------------------------------------------------------
# merger: 出所によって current_step を決める
# --------------------------------------------------------------------------


def test_session_declared_milestone_receives_current_phase() -> None:
    """SessionState が宣言した Milestone には現在フェーズが入る。

    `SessionStateParser` の `# CurrentPhaseParser で補完` が指していた補完である。
    """
    result = MilestoneSourceMerger(
        session_milestones=[
            MilestoneInfo(name="B-5", current_step="UNKNOWN", status="in-progress")
        ],
        task_milestone_names=[],
        current_phase="BUILDING",
    ).get_milestones()

    assert len(result) == 1
    assert result[0].current_step == "BUILDING"


def test_tasks_only_milestone_stays_unknown() -> None:
    """tasks.md にしか現れない Milestone は UNKNOWN のまま。

    これが本テストの主眼。過去の Milestone の残骸に現在フェーズを刻まない。
    """
    result = MilestoneSourceMerger(
        session_milestones=[],
        task_milestone_names=["B-5"],
        current_phase="BUILDING",
    ).get_milestones()

    assert len(result) == 1
    assert result[0].current_step == "UNKNOWN", (
        "tasks.md 由来のみの Milestone に現在フェーズを刻んではならない"
        "（クローズ済 Milestone が進行中に見える）"
    )


def test_mixed_sources_are_labelled_independently() -> None:
    """両方の出所が混ざっても、それぞれ別の値を持つ。"""
    result = MilestoneSourceMerger(
        session_milestones=[
            MilestoneInfo(name="D-1", current_step="UNKNOWN", status="in-progress")
        ],
        task_milestone_names=["B-5"],
        current_phase="AUDITING",
    ).get_milestones()

    by_name = {ms.name: ms for ms in result}
    assert by_name["D-1"].current_step == "AUDITING"
    assert by_name["B-5"].current_step == "UNKNOWN"


def test_current_phase_is_optional_for_backward_compatibility() -> None:
    """`current_phase` を省略しても壊れない（既存 11 箇所の呼び出しを守る）。"""
    result = MilestoneSourceMerger(
        session_milestones=[
            MilestoneInfo(name="B-5", current_step="UNKNOWN", status="in-progress")
        ],
        task_milestone_names=[],
    ).get_milestones()

    assert result[0].current_step == "UNKNOWN"


def test_status_is_not_touched_by_the_step_rule() -> None:
    """Step の描き分けは status に影響しない（帳簿を混ぜない）。"""
    result = MilestoneSourceMerger(
        session_milestones=[
            MilestoneInfo(name="B-5", current_step="UNKNOWN", status="completed")
        ],
        task_milestone_names=["B-4"],
        current_phase="BUILDING",
    ).get_milestones()

    by_name = {ms.name: ms for ms in result}
    assert by_name["B-5"].status == "completed"
    assert by_name["B-4"].status == "unknown"


# --------------------------------------------------------------------------
# builder: ms.current_step を描く（グローバル phase を刻まない）
# --------------------------------------------------------------------------


def _render(milestones: list[MilestoneInfo], current_phase: str) -> str:
    data = DashboardData()
    data.milestones = list(milestones)
    data.current_phase = current_phase
    return DashboardBuilder(data).render()


def test_builder_renders_per_milestone_step() -> None:
    """カードの Step は `ms.current_step` であり、グローバルの現在フェーズではない。"""
    html = _render(
        [MilestoneInfo(name="B-5", current_step="UNKNOWN", status="unknown")],
        current_phase="BUILDING",
    )
    assert '<span class="step">UNKNOWN</span>' in html
    assert '<span class="step">BUILDING</span>' not in html, (
        "tasks.md 由来のみの Milestone にグローバルフェーズが刻まれている"
    )


def test_builder_still_shows_phase_for_declared_milestone() -> None:
    """宣言された Milestone には現在フェーズが出る（表示機能自体は失わない）。"""
    html = _render(
        [MilestoneInfo(name="D-1", current_step="AUDITING", status="in-progress")],
        current_phase="AUDITING",
    )
    assert '<span class="step">AUDITING</span>' in html


def test_builder_renders_mixed_cards_independently() -> None:
    """混在時、カードごとに違う Step が出る（全 Milestone 共通ではない）。"""
    html = _render(
        [
            MilestoneInfo(name="B-5", current_step="UNKNOWN", status="unknown"),
            MilestoneInfo(name="D-1", current_step="BUILDING", status="in-progress"),
        ],
        current_phase="BUILDING",
    )
    assert '<span class="step">UNKNOWN</span>' in html
    assert '<span class="step">BUILDING</span>' in html


def test_step_value_is_escaped() -> None:
    """Step 値も HTML エスケープされる（name / status と同じ扱い）。

    ページ自体が埋め込み JS のため `<script>` を正当に含む。よって「文字列が
    現れないこと」ではなく **step span の中身**を直接検査する。
    """
    html = _render(
        [MilestoneInfo(name="X", current_step="<script>alert(1)</script>", status="unknown")],
        current_phase="BUILDING",
    )
    assert '<span class="step">&lt;script&gt;alert(1)&lt;/script&gt;</span>' in html
    assert '<span class="step"><script>' not in html


# --------------------------------------------------------------------------
# 回帰: 2026-08-20 に実測した表示そのもの
# --------------------------------------------------------------------------


def test_regression_closed_milestone_is_not_shown_as_current_phase() -> None:
    """Milestone 不在期に、tasks.md の残骸が「BUILDING 中」に見えない。

    2026-08-20 の実測そのもの: 宣言欄が「なし」なのにダッシュボードは
    `B-5 / Step: BUILDING / 状態: unknown` を表示していた。
    """
    milestones = MilestoneSourceMerger(
        session_milestones=[],
        task_milestone_names=["B-5"],
        current_phase="BUILDING",
    ).get_milestones()

    html = _render(milestones, current_phase="BUILDING")

    assert "B-5" in html
    assert '<span class="step">BUILDING</span>' not in html
    assert '<span class="step">UNKNOWN</span>' in html
    assert '<span class="status">unknown</span>' in html
