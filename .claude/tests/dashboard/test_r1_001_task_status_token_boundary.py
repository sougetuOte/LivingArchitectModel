"""test_r1_001_task_status_token_boundary.py - R1-001 トークン境界修正の Red-Green テスト

対応:
  - docs/artifacts/r-1-audit-tracker.md §R1-001 (module 1 issue 一覧)
  - .claude/scripts/dashboard/builder.py `_resolve_task_status()` (symbol 参照 / 行番号は保守困難なため symbol のみ)

背景:
  `_resolve_task_status` は `if task_id in line:` という素の部分文字列マッチを用いており、
  task_id="W1-B5-T1" が line="- W1-B5-T10: ..." にも一致してしまう（接頭辞衝突）。
  HGA #8 crux 反映後の推奨修正:
    re.search(r"(?<![A-Za-z0-9-])" + re.escape(task_id) + r"(?![A-Za-z0-9])", line)
  （negative lookbehind + lookahead 両方 / trailing に "-" を含めないのは
   SESSION_STATE 実物の "T1-T5" 範囲記法を保護するため）

テスト方針:
  `DashboardBuilder._resolve_task_status` を直接呼び出す（build フルパイプラインを介さない）。
  DashboardData を最小限に構築し、completed / in_progress / blocked の各リストを個別に検証する。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from dashboard.builder import DashboardBuilder  # noqa: E402
from dashboard.models import DashboardData  # noqa: E402


def _make_builder(completed=None, in_progress=None, blocked=None) -> DashboardBuilder:
    """completed/in_progress/blocked の生行リストのみを指定した DashboardData で
    DashboardBuilder を構築するヘルパー。他フィールドは空/既定値で埋める。
    """
    data = DashboardData(
        milestones=[],
        waves=[],
        tasks=[],
        current_phase="BUILDING",
        completed=completed or [],
        in_progress=in_progress or [],
        blocked=blocked or [],
        parser_errors=[],
    )
    return DashboardBuilder(data)


# ─────────────────────────────────────────────
# Case 1: 接頭辞衝突本体（Red の主役）
# ─────────────────────────────────────────────


class TestPrefixCollisionCore:
    """W1-B5-T10 のみ completed の行に存在する場合、W1-B5-T1 は completed に誤伝播しない。"""

    COMPLETED = ["W1-B5-T10: done"]

    def test_longer_id_present_resolves_completed(self):
        builder = _make_builder(completed=self.COMPLETED)
        assert builder._resolve_task_status("W1-B5-T10", "not-started") == "completed"

    def test_prefix_of_longer_id_does_not_resolve_completed(self):
        """W1-B5-T1 は W1-B5-T10 の接頭辞だが、completed に誤伝播してはならない。"""
        builder = _make_builder(completed=self.COMPLETED)
        assert builder._resolve_task_status("W1-B5-T1", "not-started") == "not-started"


# ─────────────────────────────────────────────
# Case 2: 3 ループ全網羅（1 ループだけ修正漏れ検出）
# ─────────────────────────────────────────────


class TestAllThreeLoopsTokenBoundary:
    """completed / in_progress / blocked の 3 ループ全てでトークン境界が機能すること。"""

    def test_in_progress_loop_prefix_collision(self):
        builder = _make_builder(in_progress=["W1-B5-T10: 進行中"])
        assert builder._resolve_task_status("W1-B5-T10", "not-started") == "in-progress"
        assert builder._resolve_task_status("W1-B5-T1", "not-started") == "not-started"

    def test_blocked_loop_prefix_collision(self):
        builder = _make_builder(blocked=["W1-B5-T10: ブロック中"])
        assert builder._resolve_task_status("W1-B5-T10", "not-started") == "blocked"
        assert builder._resolve_task_status("W1-B5-T1", "not-started") == "not-started"


# ─────────────────────────────────────────────
# Case 3: 短縮形衝突（T4 vs T40 / T2 vs T20）
# ─────────────────────────────────────────────


class TestShortFormCollision:
    def test_t40_present_t4_not_resolved(self):
        builder = _make_builder(completed=["W1-B5-T40: done"])
        assert builder._resolve_task_status("W1-B5-T40", "not-started") == "completed"
        assert builder._resolve_task_status("W1-B5-T4", "not-started") == "not-started"

    def test_t20_present_t2_not_resolved(self):
        builder = _make_builder(completed=["W1-B5-T20: done"])
        assert builder._resolve_task_status("W1-B5-T20", "not-started") == "completed"
        assert builder._resolve_task_status("W1-B5-T2", "not-started") == "not-started"


# ─────────────────────────────────────────────
# Case 4: trailing 装飾網羅
# ─────────────────────────────────────────────


class TestTrailingDecorationCoverage:
    """様々な装飾文字が後続してもトークン境界一致で completed 判定されること。"""

    @pytest.mark.parametrize(
        "line",
        [
            "W1-B5-T1: x",
            "W1-B5-T1 完了",
            "... W1-B5-T1",
            "(W1-B5-T1)",
            "**W1-B5-T1**: x",
            "`W1-B5-T1` 完了",
            "（W1-B5-T1）",  # 全角括弧
        ],
    )
    def test_decorated_task_id_resolves_completed(self, line):
        builder = _make_builder(completed=[line])
        assert builder._resolve_task_status("W1-B5-T1", "not-started") == "completed", (
            f"装飾行で completed 判定に失敗: {line!r}"
        )


# ─────────────────────────────────────────────
# Case 5: leading 境界（短縮形が途中にマッチしない）
# ─────────────────────────────────────────────


class TestLeadingBoundary:
    def test_t31_does_not_match_inside_w3_b5_t31(self):
        """task_id='T31' は完全形 'W3-B5-T31' の一部であってはならない
        （leading 境界がないと 'T31' が末尾一致してしまう可能性を検証）。

        本ケースは「'T31' 単独 ID が別の行に存在しない」ことの確認ではなく、
        'W3-B5-T31: done' という行に対し task_id='T31' を渡した場合に
        誤って completed 判定されないことを確認する（leading 境界検証）。
        """
        builder = _make_builder(completed=["W3-B5-T31: done"])
        assert builder._resolve_task_status("T31", "not-started") == "not-started"

    def test_t1_does_not_match_inside_s3_t1(self):
        builder = _make_builder(completed=["S3-T1: done"])
        assert builder._resolve_task_status("T1", "not-started") == "not-started"


# ─────────────────────────────────────────────
# Case 6: Wave 小数形式
# ─────────────────────────────────────────────


class TestWaveDecimalFormat:
    r"""TasksParser が生成する W1.5-B4-T9 形式の Task ID がトークン境界一致で機能すること。

    根拠: .claude/scripts/dashboard/parsers/tasks.py L37
    _TASK_ID_PREFIX_RE = r"^(W\d+(?:\.\d+)?-[A-Z]\d+-T\d+|T\d+):"
    """

    def test_wave_decimal_task_id_resolves_completed(self):
        builder = _make_builder(completed=["W1.5-B4-T9: done"])
        assert builder._resolve_task_status("W1.5-B4-T9", "not-started") == "completed"

    def test_wave_decimal_prefix_collision_avoided(self):
        """W1.5-B4-T9 のみ存在する場合、W1.5-B4-T90 のような長い ID は無関係
        （逆方向: 短い ID が存在する行に長い ID を渡しても誤一致しない）。
        """
        builder = _make_builder(completed=["W1.5-B4-T9: done"])
        assert builder._resolve_task_status("W1.5-B4-T90", "not-started") == "not-started"


# ─────────────────────────────────────────────
# Case 7: regression 用 base_status フォールバック
# ─────────────────────────────────────────────


class TestBaseStatusFallback:
    """いずれのリストにも一致しない場合は base_status がそのまま返ること（既存契約維持）。"""

    def test_no_match_returns_base_status(self):
        builder = _make_builder(
            completed=["W1-B5-T10: done"],
            in_progress=["W2-B5-T20: 進行中"],
            blocked=["W3-B5-T30: ブロック"],
        )
        assert builder._resolve_task_status("W1-B5-T1", "not-started") == "not-started"
        assert builder._resolve_task_status("W9-B5-T99", "completed") == "completed"


# ─────────────────────────────────────────────
# Case 8: 範囲記法エンドポイント（HGA #9 refute C-N2 対応）
# ─────────────────────────────────────────────


class TestRangeNotationEndpointSemantics:
    """SESSION_STATE.md L97 の "T1-T5" のような範囲記法に対するマッチ semantics を
    仕様として固定する (HGA #9 verdict C-N2 対応 / fix_before_ship)。

    仕様 (docs/specs/large-scale-review/tasks.md §Stage S1 意図的挙動変更):
    - 範囲は展開しない（"T1-T5" は "T1" だけを含み、"T5" のエンドポイントは含まない）
    - 左端 (T1): trailing ハイフン許容の lookahead 設計により completed 判定される
    - 右端 (T5): leading ハイフン非許容の lookbehind 設計により completed 判定されない
    - 旧 substring 実装は両端マッチしていたが、旧実装は接頭辞衝突 (R1-001) を含む欠陥のため
      旧挙動は仕様ではない (未文書化の副産物であった)。
    """

    def test_range_left_endpoint_matches(self):
        """範囲記法の左端 (T1) は completed 判定される (trailing "-" 許容の副産物)。"""
        builder = _make_builder(completed=["T1-T5: 範囲説明"])
        assert builder._resolve_task_status("T1", "not-started") == "completed"

    def test_range_right_endpoint_does_not_match(self):
        """範囲記法の右端 (T5) は completed 判定されない (leading "-" 非許容による意図的挙動)。

        HGA #9 で発覚した仕様曖昧性の確定: 範囲は展開しない。
        呼び出し側で範囲を扱う必要があれば個別 ID (T1, T2, T3, T4, T5) を
        completed リストに列挙する運用とする。
        """
        builder = _make_builder(completed=["T1-T5: 範囲説明"])
        assert builder._resolve_task_status("T5", "not-started") == "not-started"

    def test_range_middle_endpoints_do_not_match(self):
        """範囲の中間 ID (T2, T3, T4) は当然マッチしない (regression 防止)。"""
        builder = _make_builder(completed=["T1-T5: 範囲説明"])
        for tid in ("T2", "T3", "T4"):
            assert builder._resolve_task_status(tid, "not-started") == "not-started"
