"""失敗時挙動 3 段階 + 統合テスト (Wave C Stage 3 T6)

MAGI v2 の gabriel probe 失敗時挙動 (design.md §5) を、magi_dispatch.py の
resolve_action() + render_log_entry() で検証する。

対応仕様:
    - docs/specs/magi-v2-gabriel/design.md §5 (失敗時挙動 3 段階 + abort/timeout/format_error)
    - docs/specs/magi-v2-gabriel/requirements.md AC-W-C-5 / AC-W-C-6 / AC-W-C-7
    - docs/specs/magi-v2-gabriel/tasks.md §6 WC-B5-T6 (テストケース 8 件)
    - .claude/skills/magi/SKILL.md §Step 4.1 (verdict 別分岐処理)
    - .claude/scripts/magi_dispatch.py (実行時 SSOT)

テストケース (tasks.md §6 T6 準拠):
    1. critical (初回) → 再 MAGI 指示 (re_magi)
    2. critical (2 回目) → escalation (escalate_critical_max)
    3. warning → 結論併記 (annotate_warning)
    4. info → 記録のみ (record_only)
    5. abort → escalation (escalate_abort / verdict/severity 問わず)
    6. inconclusive → 結論確定 (proceed_inconclusive)
    7. timeout > 60s → inconclusive 同等 (handle_timeout)
    8. format_error → inconclusive 同等 (handle_format_error)

追加テスト:
    - confirmed → 結論確定 (proceed_confirmed) [パターン 0]
    - 優先順位テスト (abort が critical より優先されること)
    - render_log_entry() の design §5 テンプレート一致確認
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from magi_dispatch import (  # noqa: E402
    ResolvedAction,
    render_log_entry,
    resolve_action,
)


# ---------------------------------------------------------------------------
# fixture 群 (design.md §3 スキーマに準拠した gabriel 出力 stub)
# ---------------------------------------------------------------------------


def _make_gabriel_output(
    verdict: str,
    severity: str,
    affected_atoms: list[str],
    recommended_action: str,
    confidence: float,
    reasoning: str = None,
) -> dict:
    """テスト用の gabriel 出力 dict を生成する。

    reasoning は design.md §3 の minLength=200 を満たすデフォルト値を持たせる。
    """
    if reasoning is None:
        reasoning = (
            "This is a stub reasoning string used for MAGI v2 integration testing. "
            "It contains sufficient content to satisfy the design.md §3 minLength=200 "
            "constraint while remaining under the maxLength=1000 upper bound. "
            "The test verifies that verdict dispatch logic operates correctly regardless "
            "of the specific reasoning text content."
        )
    return {
        "verdict": verdict,
        "severity": severity,
        "affected_atoms": affected_atoms,
        "reasoning": reasoning,
        "recommended_action": recommended_action,
        "confidence": confidence,
    }


# ---------------------------------------------------------------------------
# 1. critical (初回) → re_magi (AC-W-C-5)
# ---------------------------------------------------------------------------
def test_critical_first_round_triggers_re_magi():
    output = _make_gabriel_output(
        verdict="refuted",
        severity="critical",
        affected_atoms=["A1", "A2"],
        recommended_action="re-magi",
        confidence=0.85,
    )
    resolved = resolve_action(output, retry_count=0)

    assert resolved.action == "re_magi"
    assert resolved.re_magi_next is True
    assert resolved.escalate_human is False
    assert resolved.conclusion_state == "pending"


# ---------------------------------------------------------------------------
# 2. critical (2 回目) → escalation (AC-W-C-7)
# ---------------------------------------------------------------------------
def test_critical_second_round_triggers_escalation():
    output = _make_gabriel_output(
        verdict="refuted",
        severity="critical",
        affected_atoms=["A1"],
        recommended_action="re-magi",
        confidence=0.85,
    )
    resolved = resolve_action(output, retry_count=1)

    assert resolved.action == "escalate_critical_max"
    assert resolved.re_magi_next is False
    assert resolved.escalate_human is True
    assert resolved.conclusion_state == "pending"


# ---------------------------------------------------------------------------
# 3. warning → annotate_warning (AC-W-C-6)
# ---------------------------------------------------------------------------
def test_warning_annotates_conclusion():
    output = _make_gabriel_output(
        verdict="refuted",
        severity="warning",
        affected_atoms=["A2"],
        recommended_action="proceed",
        confidence=0.7,
    )
    resolved = resolve_action(output, retry_count=0)

    assert resolved.action == "annotate_warning"
    assert resolved.re_magi_next is False
    assert resolved.escalate_human is False
    assert resolved.conclusion_state == "annotated"


# ---------------------------------------------------------------------------
# 4. info → record_only
# ---------------------------------------------------------------------------
def test_info_records_only():
    output = _make_gabriel_output(
        verdict="refuted",
        severity="info",
        affected_atoms=["A3"],
        recommended_action="proceed",
        confidence=0.5,
    )
    resolved = resolve_action(output, retry_count=0)

    assert resolved.action == "record_only"
    assert resolved.re_magi_next is False
    assert resolved.escalate_human is False
    assert resolved.conclusion_state == "confirmed"


# ---------------------------------------------------------------------------
# 5. abort (verdict/severity 問わず) → escalate_abort
# ---------------------------------------------------------------------------
def test_abort_triggers_immediate_escalation_regardless_of_verdict():
    """recommended_action=abort は verdict や severity に関わらず即時 escalation。

    SKILL.md §Step 4.1: 優先順位 abort > critical > warning > info > confirmed > inconclusive
    """
    # abort は severity=critical と共に返される場合もあれば、verdict=confirmed 時も可能
    for verdict, severity in [
        ("refuted", "critical"),
        ("refuted", "warning"),
        ("refuted", "info"),
        ("confirmed", "info"),
        ("inconclusive", "info"),
    ]:
        output = _make_gabriel_output(
            verdict=verdict,
            severity=severity,
            affected_atoms=["A1"] if verdict == "refuted" else [],
            recommended_action="abort",
            confidence=0.9,
        )
        resolved = resolve_action(output, retry_count=0)

        assert resolved.action == "escalate_abort", (
            f"abort が verdict={verdict}, severity={severity} で escalation 未発火"
        )
        assert resolved.escalate_human is True
        assert resolved.re_magi_next is False
        assert resolved.conclusion_state == "pending"


# ---------------------------------------------------------------------------
# 6. inconclusive → proceed_inconclusive
# ---------------------------------------------------------------------------
def test_inconclusive_proceeds_with_caspar_conclusion():
    output = _make_gabriel_output(
        verdict="inconclusive",
        severity="info",
        affected_atoms=[],
        recommended_action="proceed",
        confidence=0.25,  # < 0.3 だが verdict=inconclusive なのでスキーマ違反ではない
    )
    resolved = resolve_action(output, retry_count=0)

    assert resolved.action == "proceed_inconclusive"
    assert resolved.re_magi_next is False
    assert resolved.escalate_human is False
    assert resolved.conclusion_state == "confirmed"


# ---------------------------------------------------------------------------
# 7. timeout (> 60 秒) → handle_timeout / inconclusive 同等 (NFR-W-C-1)
# ---------------------------------------------------------------------------
def test_timeout_falls_back_to_inconclusive():
    """gabriel が 60 秒制限を超過した場合、gabriel_output の内容に関わらず timeout 処理。"""
    resolved = resolve_action(gabriel_output=None, retry_count=0, is_timeout=True)

    assert resolved.action == "handle_timeout"
    assert resolved.re_magi_next is False
    assert resolved.escalate_human is False
    assert resolved.conclusion_state == "confirmed"


def test_timeout_takes_precedence_over_gabriel_output():
    """is_timeout=True は gabriel_output の中身より優先される (defensive)。"""
    # gabriel が critical refute を返したように見えても、timeout ならば timeout 扱い
    output = _make_gabriel_output(
        verdict="refuted",
        severity="critical",
        affected_atoms=["A1"],
        recommended_action="abort",
        confidence=0.9,
    )
    resolved = resolve_action(output, retry_count=0, is_timeout=True)

    assert resolved.action == "handle_timeout"


# ---------------------------------------------------------------------------
# 8. format_error → handle_format_error / inconclusive 同等 (NFR-W-C-2)
# ---------------------------------------------------------------------------
def test_format_error_falls_back_to_inconclusive():
    """gabriel の出力が None (JSON 欠損 / 型不一致相当) の場合、format_error 処理。"""
    resolved = resolve_action(gabriel_output=None, retry_count=0)

    assert resolved.action == "handle_format_error"
    assert resolved.re_magi_next is False
    assert resolved.escalate_human is False
    assert resolved.conclusion_state == "confirmed"


# ---------------------------------------------------------------------------
# 追加: confirmed → proceed_confirmed
# ---------------------------------------------------------------------------
def test_confirmed_proceeds_with_reinforcement():
    output = _make_gabriel_output(
        verdict="confirmed",
        severity="info",
        affected_atoms=[],
        recommended_action="proceed",
        confidence=0.85,
    )
    resolved = resolve_action(output, retry_count=0)

    assert resolved.action == "proceed_confirmed"
    assert resolved.re_magi_next is False
    assert resolved.escalate_human is False
    assert resolved.conclusion_state == "confirmed"


# ---------------------------------------------------------------------------
# 優先順位: abort > critical (どちらも成立するケースで abort が勝つ)
# ---------------------------------------------------------------------------
def test_abort_takes_precedence_over_critical():
    """recommended_action=abort が verdict=refuted+severity=critical より優先されること。

    SKILL.md §Step 4.1 分岐優先順位の実装検証。
    """
    output = _make_gabriel_output(
        verdict="refuted",
        severity="critical",
        affected_atoms=["A1"],
        recommended_action="abort",
        confidence=0.9,
    )
    resolved = resolve_action(output, retry_count=0)

    assert resolved.action == "escalate_abort"
    # 「critical で retry_count=0 → re_magi」の分岐に落ちてはならない
    assert resolved.action != "re_magi"
    assert resolved.escalate_human is True


# ---------------------------------------------------------------------------
# render_log_entry() の design §5 テンプレート一致検証
# ---------------------------------------------------------------------------
class TestLogEntryTemplates:
    """render_log_entry() が design.md §5 の 8 テンプレートに準拠することを確認。"""

    def test_render_re_magi_contains_critical_by_gabriel_marker(self):
        output = _make_gabriel_output(
            verdict="refuted",
            severity="critical",
            affected_atoms=["A1"],
            recommended_action="re-magi",
            confidence=0.9,
        )
        resolved = resolve_action(output, retry_count=0)
        log = render_log_entry(output, resolved)

        assert "### gabriel probe" in log
        assert "verdict: refuted" in log
        assert "severity: critical" in log
        assert "[CRITICAL by gabriel]" in log
        assert "gabriel.reasoning を新入力として再 MAGI を実施" in log

    def test_render_escalate_critical_max_contains_upper_limit_marker(self):
        output = _make_gabriel_output(
            verdict="refuted",
            severity="critical",
            affected_atoms=["A1"],
            recommended_action="re-magi",
            confidence=0.9,
        )
        resolved = resolve_action(output, retry_count=1)
        log = render_log_entry(output, resolved)

        assert "再 MAGI 上限" in log or "上限" in log
        assert "人間" in log

    def test_render_annotate_warning_contains_warning_marker(self):
        output = _make_gabriel_output(
            verdict="refuted",
            severity="warning",
            affected_atoms=["A1"],
            recommended_action="proceed",
            confidence=0.7,
        )
        resolved = resolve_action(output, retry_count=0)
        log = render_log_entry(output, resolved)

        assert "[WARNING by gabriel]" in log
        assert "L1 統括" in log

    def test_render_record_only_contains_info_marker(self):
        output = _make_gabriel_output(
            verdict="refuted",
            severity="info",
            affected_atoms=["A1"],
            recommended_action="proceed",
            confidence=0.5,
        )
        resolved = resolve_action(output, retry_count=0)
        log = render_log_entry(output, resolved)

        assert "[INFO by gabriel]" in log
        assert "記録するのみ" in log

    def test_render_escalate_abort_contains_abort_marker(self):
        output = _make_gabriel_output(
            verdict="refuted",
            severity="critical",
            affected_atoms=["A1"],
            recommended_action="abort",
            confidence=0.95,
        )
        resolved = resolve_action(output, retry_count=0)
        log = render_log_entry(output, resolved)

        assert "[ABORT by gabriel]" in log
        assert "即時人間判断必須" in log

    def test_render_confirmed_contains_reinforcement_marker(self):
        output = _make_gabriel_output(
            verdict="confirmed",
            severity="info",
            affected_atoms=[],
            recommended_action="proceed",
            confidence=0.85,
        )
        resolved = resolve_action(output, retry_count=0)
        log = render_log_entry(output, resolved)

        assert "verdict: confirmed" in log
        assert "gabriel 補強" in log

    def test_render_inconclusive_contains_note_marker(self):
        output = _make_gabriel_output(
            verdict="inconclusive",
            severity="info",
            affected_atoms=[],
            recommended_action="proceed",
            confidence=0.25,
        )
        resolved = resolve_action(output, retry_count=0)
        log = render_log_entry(output, resolved)

        assert "verdict: inconclusive" in log
        assert "[NOTE]" in log
        assert "CASPAR の判断を維持" in log

    def test_render_timeout_contains_timeout_marker(self):
        resolved = resolve_action(gabriel_output=None, retry_count=0, is_timeout=True)
        log = render_log_entry(None, resolved)

        assert "(timeout 注記)" in log
        assert "60 秒" in log
        assert "再 MAGI は実施しません" in log

    def test_render_format_error_contains_format_error_marker(self):
        resolved = resolve_action(gabriel_output=None, retry_count=0)
        log = render_log_entry(None, resolved)

        assert "(format_error 注記)" in log
        assert "フォーマット不備" in log
        assert "再 MAGI は実施しません" in log

    def test_render_raises_when_output_missing_for_non_fallback_action(self):
        """timeout/format_error 以外の action で gabriel_output=None を渡すとエラー。

        Silent Failure 禁止 (LAM code-quality-guideline.md § Error Swallowing) の実装確認。
        """
        # confirmed action だが gabriel_output なし → 例外
        resolved = ResolvedAction(
            action="proceed_confirmed",
            re_magi_next=False,
            escalate_human=False,
            conclusion_state="confirmed",
        )
        with pytest.raises(ValueError, match="gabriel_output must be provided"):
            render_log_entry(None, resolved)


# ---------------------------------------------------------------------------
# SKILL.md との整合性確認 (静的テスト / SSOT drift ガード)
# ---------------------------------------------------------------------------
class TestSkillMdConsistency:
    """SKILL.md の verdict 別分岐テーブルと magi_dispatch.py の実装が乖離していないか確認。

    静的検査であり、SKILL.md がリファクタで変更された際にドリフトを検出する。
    """

    SKILL_MD_PATH = (
        Path(__file__).resolve().parent.parent.parent
        / "skills"
        / "magi"
        / "SKILL.md"
    )

    def test_skill_md_exists(self):
        assert self.SKILL_MD_PATH.is_file(), (
            f"SKILL.md が見つかりません: {self.SKILL_MD_PATH}"
        )

    def test_skill_md_declares_gabriel_probe(self):
        content = self.SKILL_MD_PATH.read_text(encoding="utf-8")
        assert "gabriel adversarial probe" in content
        assert "Step 4.1" in content or "verdict 別分岐" in content

    def test_skill_md_lists_all_verdict_branches(self):
        content = self.SKILL_MD_PATH.read_text(encoding="utf-8")
        # 全 9 分岐 (再 MAGI 初回 / 2 回目 / warning / info / confirmed / inconclusive
        # / abort / timeout / format_error) が SKILL.md に文言として存在すること
        required_markers = [
            "recommended_action=abort",
            "severity=critical",
            "severity=warning",
            "severity=info",
            "verdict=confirmed",
            "verdict=inconclusive",
            "timeout",
            "format_error",
        ]
        for marker in required_markers:
            assert marker in content, (
                f"SKILL.md に verdict 分岐マーカー {marker!r} が欠落しています。"
            )

    def test_skill_md_declares_re_magi_upper_bound(self):
        content = self.SKILL_MD_PATH.read_text(encoding="utf-8")
        assert "1 ラウンド上限" in content or "上限 1 回" in content, (
            "SKILL.md に再 MAGI 1 ラウンド上限 (AC-W-C-7) の記述が欠落しています。"
        )

    def test_skill_md_references_magi_dispatch_module(self):
        content = self.SKILL_MD_PATH.read_text(encoding="utf-8")
        assert "magi_dispatch.py" in content, (
            "SKILL.md が実装 SSOT である magi_dispatch.py を参照していません。"
        )
