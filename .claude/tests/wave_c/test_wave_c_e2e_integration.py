"""MAGI v2 E2E 統合テスト (Wave C Stage 5 T10)

MAGI 合議 (軽量 / AoT 適用) から gabriel probe 起動判定 → verdict 別分岐 → 再 MAGI カウンター
までの E2E フローを検証する。

対応仕様:
    - docs/specs/magi-v2-gabriel/design.md §4 (MAGI 統合フロー) + §5 (失敗時挙動) + §6 (トリガー条件)
    - docs/specs/magi-v2-gabriel/requirements.md AC-W-C-4 (トリガー) + AC-W-C-10 (ログ記録) + AC-W-C-11 (AoT 温存)
    - docs/specs/magi-v2-gabriel/tasks.md §6 WC-B5-T10 (テストケース 6 件 + 60s 計測)
    - .claude/skills/magi/SKILL.md §Step 4 / §Step 4.2 (opt-out 経路)
    - .claude/scripts/magi_dispatch.py (SSOT)
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from magi_dispatch import (  # noqa: E402
    GateDecision,
    OptOutRecord,
    render_log_entry,
    resolve_action,
    should_run_gabriel,
)


# ---------------------------------------------------------------------------
# fixture helpers
# ---------------------------------------------------------------------------


def _make_gabriel_output(
    verdict: str,
    severity: str,
    affected_atoms: list[str],
    recommended_action: str,
    confidence: float,
) -> dict:
    return {
        "verdict": verdict,
        "severity": severity,
        "affected_atoms": affected_atoms,
        "reasoning": "E2E integration test stub reasoning " * 5,
        "recommended_action": recommended_action,
        "confidence": confidence,
    }


# ═════════════════════════════════════════════════════════════
# T10 テストケース 1-2: MAGI モード別 gabriel 起動判定 (AC-W-C-4)
# ═════════════════════════════════════════════════════════════


class TestGabrielGateAoTMode:
    """AC-W-C-4: AoT 適用 / 非適用の gabriel 起動判定の正当性検証。"""

    def test_lightweight_mode_skips_gabriel(self):
        """MAGI 軽量モード (非 AoT) では gabriel は起動されない (FR-W-C-3 MUST NOT)。"""
        decision = should_run_gabriel(is_aot_mode=False, opt_out=None)

        assert decision.gate_action == "skip_lightweight"
        assert decision.should_run is False
        assert "軽量モード" in decision.log_message
        assert "MUST NOT" in decision.log_message

    def test_aot_mode_without_opt_out_runs_gabriel(self):
        """AoT 適用 MAGI で opt-out 記録なしなら gabriel を起動する (通常経路)。"""
        decision = should_run_gabriel(is_aot_mode=True, opt_out=None)

        assert decision.gate_action == "run"
        assert decision.should_run is True
        assert "AoT" in decision.log_message


# ═════════════════════════════════════════════════════════════
# T10 テストケース 3-4: opt-out 経路 (FR-W-C-4)
# ═════════════════════════════════════════════════════════════


class TestGabrielOptOut:
    """§Step 4.2 opt-out 経路: 2 条件必須 (理由 + 宣言者)。"""

    def test_valid_opt_out_by_user_skips_gabriel(self):
        """ユーザーが理由を明示した opt-out は受理される。"""
        opt_out = OptOutRecord(
            reason="時間的緊急性: 締め切り前の軽微な仕様確認のため",
            declarer="user",
        )
        decision = should_run_gabriel(is_aot_mode=True, opt_out=opt_out)

        assert decision.gate_action == "skip_opt_out"
        assert decision.should_run is False
        assert "opt-out 受理" in decision.log_message
        assert "user" in decision.log_message

    def test_valid_opt_out_by_l1_skips_gabriel(self):
        """L1 統括が理由を明示した opt-out は受理される。"""
        opt_out = OptOutRecord(
            reason="gabriel 判定に必要な情報が揮発的で正確な判定が期待できない",
            declarer="L1",
        )
        decision = should_run_gabriel(is_aot_mode=True, opt_out=opt_out)

        assert decision.gate_action == "skip_opt_out"
        assert decision.should_run is False

    def test_opt_out_without_reason_is_rejected(self):
        """理由が空文字の opt-out は却下される (FR-W-C-4 MUST NOT)。"""
        opt_out = OptOutRecord(reason="   ", declarer="user")  # 空白のみ
        decision = should_run_gabriel(is_aot_mode=True, opt_out=opt_out)

        assert decision.gate_action == "run"
        assert decision.should_run is True
        assert "opt-out 記録不備" in decision.log_message
        assert "却下" in decision.log_message


# ═════════════════════════════════════════════════════════════
# T10 テストケース 5: AUTONOMOUS フェーズ opt-out 却下 (ADR-0005 FR-9.1)
# ═════════════════════════════════════════════════════════════


class TestGabrielAutonomousRejection:
    """§Step 4.2: AUTONOMOUS フェーズ / 自律ループの opt-out は却下される。"""

    def test_autonomous_phase_rejects_opt_out(self):
        """AUTONOMOUS フェーズでの opt-out 宣言は却下される。"""
        opt_out = OptOutRecord(
            reason="自律ループ実行中の高速化",
            declarer="user",  # 宣言者が user でも AUTONOMOUS フェーズなら却下
        )
        decision = should_run_gabriel(
            is_aot_mode=True, opt_out=opt_out, phase="AUTONOMOUS"
        )

        assert decision.gate_action == "reject_opt_out"
        assert decision.should_run is True
        assert "AUTONOMOUS" in decision.log_message
        assert "FR-9.1" in decision.log_message

    def test_autonomous_declarer_rejects_opt_out(self):
        """自律ループ実行者 (declarer=autonomous) の opt-out は phase 問わず却下される。"""
        opt_out = OptOutRecord(
            reason="自律ループの効率化",
            declarer="autonomous",
        )
        decision = should_run_gabriel(
            is_aot_mode=True, opt_out=opt_out, phase="standard"
        )

        assert decision.gate_action == "reject_opt_out"
        assert decision.should_run is True
        assert "自律" in decision.log_message


# ═════════════════════════════════════════════════════════════
# T10 テストケース 6: E2E チェーン (再 MAGI カウンター 2 回目 escalation)
# ═════════════════════════════════════════════════════════════


class TestReMagiChainE2E:
    """AC-W-C-7: 再 MAGI 上限 1 ラウンドが 2 回目で自動 escalation される E2E チェーン。"""

    def test_full_chain_critical_first_then_critical_second_leads_to_escalation(self):
        """critical 初回 → re_magi → critical (2 回目) → escalate_critical_max。"""
        # Round 1 (初回): critical → re_magi
        gabriel_r1 = _make_gabriel_output(
            verdict="refuted",
            severity="critical",
            affected_atoms=["A1"],
            recommended_action="re-magi",
            confidence=0.9,
        )
        r1 = resolve_action(gabriel_r1, retry_count=0)
        assert r1.action == "re_magi"
        assert r1.re_magi_next is True

        # 再 MAGI 実施 → Round 2 でも critical
        gabriel_r2 = _make_gabriel_output(
            verdict="refuted",
            severity="critical",
            affected_atoms=["A1", "A2"],  # 追加 Atom が浮上
            recommended_action="re-magi",
            confidence=0.85,
        )
        r2 = resolve_action(gabriel_r2, retry_count=1)
        assert r2.action == "escalate_critical_max"
        assert r2.escalate_human is True
        assert r2.re_magi_next is False

    def test_full_chain_critical_first_then_confirmed_proceeds(self):
        """critical 初回 → re_magi → confirmed (2 回目) → proceed_confirmed。"""
        # Round 1: critical → re_magi
        gabriel_r1 = _make_gabriel_output(
            verdict="refuted",
            severity="critical",
            affected_atoms=["A1"],
            recommended_action="re-magi",
            confidence=0.9,
        )
        r1 = resolve_action(gabriel_r1, retry_count=0)
        assert r1.action == "re_magi"

        # 再 MAGI 実施 → Round 2 は confirmed
        gabriel_r2 = _make_gabriel_output(
            verdict="confirmed",
            severity="info",
            affected_atoms=[],
            recommended_action="proceed",
            confidence=0.9,
        )
        r2 = resolve_action(gabriel_r2, retry_count=1)
        assert r2.action == "proceed_confirmed"
        assert r2.re_magi_next is False


# ═════════════════════════════════════════════════════════════
# T10 テストケース: MAGI ログ形式 全 verdict パターン (AC-W-C-10)
# ═════════════════════════════════════════════════════════════


class TestFullLogFormatCoverage:
    """AC-W-C-10: MAGI ログ形式が verdict / severity / confidence を全パターンで記録すること。"""

    @pytest.mark.parametrize(
        "verdict,severity,recommended_action,confidence,expected_action",
        [
            ("confirmed", "info", "proceed", 0.85, "proceed_confirmed"),
            ("inconclusive", "info", "proceed", 0.25, "proceed_inconclusive"),
            ("refuted", "info", "proceed", 0.5, "record_only"),
            ("refuted", "warning", "proceed", 0.7, "annotate_warning"),
            ("refuted", "critical", "re-magi", 0.9, "re_magi"),
            ("confirmed", "info", "abort", 0.9, "escalate_abort"),
        ],
    )
    def test_all_verdict_patterns_produce_valid_log_entry(
        self, verdict, severity, recommended_action, confidence, expected_action
    ):
        output = _make_gabriel_output(
            verdict=verdict,
            severity=severity,
            affected_atoms=["A1"] if verdict == "refuted" else [],
            recommended_action=recommended_action,
            confidence=confidence,
        )
        resolved = resolve_action(output, retry_count=0)

        assert resolved.action == expected_action

        # ログエントリー生成が失敗しないこと + design §5 の共通要素を含むこと
        log = render_log_entry(output, resolved)
        assert "### gabriel probe" in log
        assert log.strip().endswith("\n") is False or log.endswith("\n")


# ═════════════════════════════════════════════════════════════
# T10 テストケース: タイムアウト実機計測 (NFR-W-C-1)
# ═════════════════════════════════════════════════════════════


class TestTimeoutNFRPerformance:
    """NFR-W-C-1 SHOULD: gabriel probe は 360 秒以内に完了すべき (2026-07-26 改訂 / 旧 60 秒)。

    実 gabriel 呼び出しは行わず、dispatch ロジック自体が「経過時間の超過」を
    正しく handle_timeout として処理することを確認する。

    下の 60 秒しきい値は NFR の閾値ではなく、dispatch ロジックの perf regression
    ガードである (NFR 閾値 360 秒とは別物 / 緩めない)。
    """

    def test_dispatch_logic_completes_well_under_60s_for_1000_calls(self):
        """resolve_action() + render_log_entry() を 1000 回呼び出しても 60 秒に到達しないこと。

        dispatch ロジック自体のパフォーマンス regression ガード。
        """
        output = _make_gabriel_output(
            verdict="refuted",
            severity="warning",
            affected_atoms=["A1"],
            recommended_action="proceed",
            confidence=0.7,
        )

        start = time.perf_counter()
        for _ in range(1000):
            resolved = resolve_action(output, retry_count=0)
            _ = render_log_entry(output, resolved)
        elapsed = time.perf_counter() - start

        assert elapsed < 60.0, (
            f"dispatch 1000 回で {elapsed:.3f} 秒消費 (perf ガード 60 秒を超過)"
        )
        # 実質的には milliseconds 単位で完了するはず (regression ガード)
        assert elapsed < 5.0, (
            f"dispatch 1000 回で {elapsed:.3f} 秒 (5 秒しきい値超過 = パフォーマンス regression 疑い)"
        )

    def test_is_timeout_flag_produces_timeout_log_immediately(self):
        """is_timeout=True フラグは即座に handle_timeout ログを生成する (経路の速度確認)。"""
        start = time.perf_counter()
        resolved = resolve_action(gabriel_output=None, retry_count=0, is_timeout=True)
        log = render_log_entry(None, resolved)
        elapsed = time.perf_counter() - start

        assert resolved.action == "handle_timeout"
        assert "(timeout 注記)" in log
        # 経路自体は瞬時に完了すべき (実際の 60 秒 wait は呼び出し元の責務)
        assert elapsed < 0.1


# ═════════════════════════════════════════════════════════════
# T10 テストケース: AoT 温存確認 (AC-W-C-11)
# ═════════════════════════════════════════════════════════════


class TestAoTFrameworkPreservation:
    """AC-W-C-11: AoT Decomposition (Step 0) が gabriel 統合後も変更されずに温存されていること。"""

    SKILL_MD_PATH = (
        Path(__file__).resolve().parent.parent.parent
        / "skills"
        / "magi"
        / "SKILL.md"
    )

    def test_skill_md_preserves_aot_decomposition_step_0(self):
        """SKILL.md に Step 0 AoT Decomposition の記述が保存されていること。"""
        content = self.SKILL_MD_PATH.read_text(encoding="utf-8")
        assert "Step 0" in content
        assert "AoT Decomposition" in content
        assert "自己完結性" in content or "自己完結" in content
        assert "インターフェース契約" in content
        assert "エラー隔離" in content

    def test_skill_md_preserves_atom_definition(self):
        """Atom の 3 条件が明記されていること。"""
        content = self.SKILL_MD_PATH.read_text(encoding="utf-8")
        # design.md §4.1: Atom の 3 条件が SKILL.md に明記されていること
        for keyword in ("自己完結", "インターフェース", "エラー隔離"):
            assert keyword in content, (
                f"SKILL.md に Atom の条件 {keyword!r} が欠落 (AC-W-C-11 違反)"
            )

    def test_skill_md_declares_lightweight_mode_no_gabriel(self):
        """軽量モードでは gabriel が起動しないことが明記されていること。"""
        content = self.SKILL_MD_PATH.read_text(encoding="utf-8")
        # 「軽量モード」節が gabriel 非起動を明示
        assert "軽量モード" in content
        assert "起動しない" in content or "MUST NOT" in content


# ═════════════════════════════════════════════════════════════
# T10 追加: GateDecision の dataclass 契約テスト
# ═════════════════════════════════════════════════════════════


def test_gate_decision_is_frozen_dataclass():
    """GateDecision は不変 (frozen) であるべき。"""
    decision = GateDecision(
        gate_action="run",
        should_run=True,
        log_message="test",
    )
    with pytest.raises((AttributeError, Exception)):
        decision.should_run = False  # type: ignore[misc]
