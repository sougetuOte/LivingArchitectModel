"""magi_dispatch.py - MAGI v2 gabriel probe verdict 別分岐処理 (Wave C Stage 3 T6)

design.md §5 の失敗時挙動 3 段階 (+ abort / timeout / format_error) を Python 純関数として実装する。
SKILL.md (skill 定義 / L1 向け宣言的仕様) と本モジュール (実行時 SSOT) の 2 系統で
MAGI v2 gabriel probe の verdict 別分岐を管理する。

分岐優先順位 (SKILL.md §Step 4.1 と一致 MUST):
    recommended_action=abort > severity=critical > warning > info > confirmed > inconclusive

再 MAGI カウンター (AC-W-C-7): 上限 1 ラウンド。retry_count >= 1 の critical で自動 escalation。

対応仕様:
    - docs/specs/magi-v2-gabriel/design.md §5 (失敗時挙動 3 段階)
    - docs/specs/magi-v2-gabriel/requirements.md AC-W-C-5 / AC-W-C-6 / AC-W-C-7
    - .claude/skills/magi/SKILL.md §Step 4.1 (verdict 別分岐処理)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Action = Literal[
    "proceed_confirmed",
    "proceed_inconclusive",
    "record_only",
    "annotate_warning",
    "re_magi",
    "escalate_critical_max",
    "escalate_abort",
    "handle_timeout",
    "handle_format_error",
]

ConclusionState = Literal["confirmed", "annotated", "pending"]


@dataclass(frozen=True)
class ResolvedAction:
    """gabriel probe の返り値から確定した次のアクション。

    Attributes:
        action: 実行すべき Action コード
        re_magi_next: True の場合、Divergence step に gabriel.reasoning を追加して再起動する
        escalate_human: True の場合、人間 escalation 必須 (再 MAGI なし / MAGI 結論保留)
        conclusion_state: MAGI 結論の状態 (confirmed / annotated=warning 併記 / pending=保留)
    """

    action: Action
    re_magi_next: bool
    escalate_human: bool
    conclusion_state: ConclusionState


def resolve_action(
    gabriel_output: dict | None,
    retry_count: int,
    is_timeout: bool = False,
) -> ResolvedAction:
    """gabriel の出力と現在の再 MAGI カウンターから次のアクションを決定する。

    分岐優先順位 (SKILL.md §Step 4.1 と一致 MUST):
        1. is_timeout=True         → handle_timeout
        2. gabriel_output is None  → handle_format_error
        3. recommended_action=abort → escalate_abort
        4. verdict=refuted & severity=critical
           - retry_count=0         → re_magi
           - retry_count>=1        → escalate_critical_max (AC-W-C-7)
        5. verdict=refuted & severity=warning → annotate_warning
        6. verdict=refuted & severity=info    → record_only
        7. verdict=confirmed                  → proceed_confirmed
        8. verdict=inconclusive               → proceed_inconclusive
        9. 予期せぬ状態 → handle_format_error (defensive fallback)

    Args:
        gabriel_output: gabriel が返した 6 フィールド JSON dict / format_error 時は None
        retry_count: 現在の再 MAGI ラウンド数 (0=初回 gabriel 呼出し, 1=1 回リトライ後の 2 回目)
        is_timeout: gabriel が 360 秒制限 (NFR-W-C-1 / 2026-07-26 改訂) を超過した場合 True

    Returns:
        ResolvedAction
    """
    if is_timeout:
        return ResolvedAction(
            action="handle_timeout",
            re_magi_next=False,
            escalate_human=False,
            conclusion_state="confirmed",
        )

    if gabriel_output is None:
        return ResolvedAction(
            action="handle_format_error",
            re_magi_next=False,
            escalate_human=False,
            conclusion_state="confirmed",
        )

    if gabriel_output.get("recommended_action") == "abort":
        return ResolvedAction(
            action="escalate_abort",
            re_magi_next=False,
            escalate_human=True,
            conclusion_state="pending",
        )

    verdict = gabriel_output.get("verdict")
    severity = gabriel_output.get("severity")

    if verdict == "refuted" and severity == "critical":
        if retry_count >= 1:
            return ResolvedAction(
                action="escalate_critical_max",
                re_magi_next=False,
                escalate_human=True,
                conclusion_state="pending",
            )
        return ResolvedAction(
            action="re_magi",
            re_magi_next=True,
            escalate_human=False,
            conclusion_state="pending",
        )

    if verdict == "refuted" and severity == "warning":
        return ResolvedAction(
            action="annotate_warning",
            re_magi_next=False,
            escalate_human=False,
            conclusion_state="annotated",
        )

    if verdict == "refuted" and severity == "info":
        return ResolvedAction(
            action="record_only",
            re_magi_next=False,
            escalate_human=False,
            conclusion_state="confirmed",
        )

    if verdict == "confirmed":
        return ResolvedAction(
            action="proceed_confirmed",
            re_magi_next=False,
            escalate_human=False,
            conclusion_state="confirmed",
        )

    if verdict == "inconclusive":
        return ResolvedAction(
            action="proceed_inconclusive",
            re_magi_next=False,
            escalate_human=False,
            conclusion_state="confirmed",
        )

    return ResolvedAction(
        action="handle_format_error",
        re_magi_next=False,
        escalate_human=False,
        conclusion_state="confirmed",
    )


def _reasoning_summary(reasoning: str, max_chars: int = 80) -> str:
    """reasoning を指定文字数以内の要約に切り詰める (log summary 用)。"""
    if len(reasoning) <= max_chars:
        return reasoning
    return reasoning[:max_chars] + "..."


def render_log_entry(
    gabriel_output: dict | None,
    resolved: ResolvedAction,
) -> str:
    """resolved action + gabriel output からログエントリー markdown を生成する。

    design.md §5 各テンプレートに準拠。SKILL.md の verdict 別ログテンプレート節と
    整合すること。

    Args:
        gabriel_output: gabriel の出力 dict / timeout・format_error 時は None
        resolved: resolve_action() の返り値

    Returns:
        design §5 に準拠した markdown ログエントリー
    """
    action = resolved.action

    if action == "handle_timeout":
        return (
            "### gabriel probe\n\n"
            "- verdict: inconclusive\n"
            "- (timeout 注記)\n"
            "- 処理: タイムアウトにより inconclusive として扱う。MAGI 結論を確定。\n\n"
            "> [NOTE]: gabriel がタイムアウト（> 360 秒）しました。inconclusive として処理します。\n"
            "> 結論は CASPAR の判断を維持します。再 MAGI は実施しません。\n"
        )

    if action == "handle_format_error":
        return (
            "### gabriel probe\n\n"
            "- verdict: inconclusive\n"
            "- (format_error 注記)\n"
            "- 処理: フォーマット不備により inconclusive として扱う。MAGI 結論を確定。\n\n"
            "> [NOTE]: gabriel の出力にフォーマット不備"
            "（必須フィールド欠損 / 型不一致）が検出されました。\n"
            "> inconclusive として処理します。結論は CASPAR の判断を維持します。"
            "再 MAGI は実施しません。\n"
        )

    if gabriel_output is None:
        raise ValueError(
            f"gabriel_output must be provided for action={action!r} "
            "(only handle_timeout / handle_format_error accept None)"
        )

    verdict = gabriel_output["verdict"]
    severity = gabriel_output["severity"]
    affected = gabriel_output.get("affected_atoms", [])
    reasoning = gabriel_output.get("reasoning", "")
    confidence = gabriel_output.get("confidence", 0.0)
    summary = _reasoning_summary(reasoning)

    if action == "escalate_abort":
        return (
            "### gabriel probe\n\n"
            f"- verdict: {verdict}\n"
            f"- severity: {severity}\n"
            "- recommended_action: abort\n"
            f"- reasoning: {reasoning}\n"
            "- 処理: MAGI 結論を保留し、人間エスカレーションを直ちに行う（再 MAGI なし）\n\n"
            "> [ABORT by gabriel]: 即時人間判断必須。\n"
            "> MAGI 結論を「保留」として記録し、人間（L1 統括）の対応を待ちます。\n"
        )

    if action == "re_magi":
        return (
            "### gabriel probe\n\n"
            "- verdict: refuted\n"
            "- severity: critical\n"
            f"- affected_atoms: {affected}\n"
            f"- reasoning: {reasoning}\n"
            "- 処理: MAGI 結論を破棄し、再 MAGI 1 ラウンドを指示する"
            "（初回のみ / 上限 1 回）\n\n"
            f"> [CRITICAL by gabriel]: {summary}\n"
            "> MAGI 結論を破棄します。"
            "gabriel.reasoning を新入力として再 MAGI を実施してください。\n"
        )

    if action == "escalate_critical_max":
        return (
            "### gabriel probe (2 回目 / 再 MAGI 上限)\n\n"
            "- verdict: refuted\n"
            "- severity: critical\n"
            f"- affected_atoms: {affected}\n"
            f"- reasoning: {reasoning}\n"
            "- 処理: 再 MAGI 上限到達（AC-W-C-7）。人間エスカレーションを行う。\n\n"
            "> [CRITICAL by gabriel]: 再 MAGI 後も critical refute。人間判断必須。\n"
            "> MAGI 結論を「保留」として記録し、人間（L1 統括）の対応を待ちます。\n"
        )

    if action == "annotate_warning":
        return (
            "### gabriel probe\n\n"
            "- verdict: refuted\n"
            "- severity: warning\n"
            f"- affected_atoms: {affected}\n"
            f"- reasoning: {reasoning}\n"
            "- 処理: 以下の指摘を MAGI 結論に併記して進む\n\n"
            f"> [WARNING by gabriel]: {summary}\n"
            "> 最終判断はユーザー（L1 統括）に委ねます。\n"
        )

    if action == "record_only":
        return (
            "### gabriel probe\n\n"
            "- verdict: refuted\n"
            "- severity: info\n"
            f"- affected_atoms: {affected}\n"
            f"- reasoning: {reasoning}\n"
            "- 処理: 以下の指摘を記録するのみ。MAGI 結論は変更しない\n\n"
            f"> [INFO by gabriel]: {summary}\n"
            "> 指摘を記録するのみ、結論は変更されない。\n"
        )

    if action == "proceed_confirmed":
        return (
            "### gabriel probe\n\n"
            "- verdict: confirmed\n"
            f"- confidence: {confidence:.2f}\n"
            f"- reasoning: {reasoning}\n"
            "- 処理: MAGI 結論を確定（gabriel 補強として記録）\n"
        )

    if action == "proceed_inconclusive":
        return (
            "### gabriel probe\n\n"
            "- verdict: inconclusive\n"
            f"- confidence: {confidence:.2f}\n"
            f"- reasoning: {reasoning}\n"
            "- 処理: MAGI 結論を確定（inconclusive 注記を添付）\n\n"
            f"> [NOTE]: gabriel は確信をもって判定できませんでした"
            f"（confidence={confidence:.2f}）。\n"
            "> 結論は CASPAR の判断を維持します。\n"
        )

    raise ValueError(f"Unknown action: {action!r}")


# ═════════════════════════════════════════════════════════════
# gabriel probe 起動判定 (opt-out gate / Wave C Stage 5 T10)
# ═════════════════════════════════════════════════════════════

Phase = Literal["standard", "AUTONOMOUS"]

GateAction = Literal["run", "skip_lightweight", "skip_opt_out", "reject_opt_out"]


@dataclass(frozen=True)
class OptOutRecord:
    """gabriel probe の opt-out 宣言記録。

    Attributes:
        reason: opt-out の理由 (1 文以上必須 / SKILL.md §Step 4.2)
        declarer: opt-out 宣言者 ("user" / "L1" / "autonomous")
    """

    reason: str
    declarer: Literal["user", "L1", "autonomous"]


@dataclass(frozen=True)
class GateDecision:
    """should_run_gabriel() の判定結果。

    Attributes:
        gate_action: 起動判定コード
        should_run: True の場合 gabriel を起動 / False の場合スキップ
        log_message: MAGI ログに記録すべきメッセージ (1 行)
    """

    gate_action: GateAction
    should_run: bool
    log_message: str


def should_run_gabriel(
    is_aot_mode: bool,
    opt_out: OptOutRecord | None,
    phase: Phase = "standard",
) -> GateDecision:
    """gabriel probe を起動すべきかを判定する。

    起動判定 (SKILL.md §Step 4 + §Step 4.2 準拠):
        1. 非 AoT (軽量モード) → skip (FR-W-C-3 MUST NOT / gabriel は AoT 適用時のみ起動)
        2. AoT + opt_out=None → run (通常経路)
        3. AoT + opt_out (declarer=user/L1 + reason 非空) → skip (§Step 4.2 opt-out 経路)
        4. AoT + opt_out (declarer=autonomous / AUTONOMOUS フェーズ) → reject (ADR-0005 FR-9.1)
        5. AoT + opt_out (reason 空) → run (opt-out 記録不備 / FR-W-C-4 MUST NOT)

    Args:
        is_aot_mode: AoT 適用モードなら True / 軽量モードなら False
        opt_out: opt-out 宣言記録 / なしの場合は None
        phase: 実行フェーズ ("standard" or "AUTONOMOUS")

    Returns:
        GateDecision
    """
    if not is_aot_mode:
        return GateDecision(
            gate_action="skip_lightweight",
            should_run=False,
            log_message="MAGI 軽量モード: gabriel probe は起動しない (FR-W-C-3 MUST NOT)。",
        )

    if opt_out is None:
        return GateDecision(
            gate_action="run",
            should_run=True,
            log_message="AoT 適用 MAGI: gabriel probe を起動する。",
        )

    if not opt_out.reason.strip():
        return GateDecision(
            gate_action="run",
            should_run=True,
            log_message=(
                "opt-out 記録不備 (reason 空): FR-W-C-4 MUST NOT により却下 / "
                "gabriel probe を通常通り起動する。"
            ),
        )

    if phase == "AUTONOMOUS" or opt_out.declarer == "autonomous":
        return GateDecision(
            gate_action="reject_opt_out",
            should_run=True,
            log_message=(
                "opt-out 試行 / 却下: AUTONOMOUS フェーズまたは自律ループ実行者の "
                "opt-out 宣言は ADR-0005 FR-9.1 により無効 / "
                "gabriel probe を通常通り起動する。"
            ),
        )

    return GateDecision(
        gate_action="skip_opt_out",
        should_run=False,
        log_message=(
            f"gabriel opt-out 受理 (宣言者: {opt_out.declarer} / "
            f"理由: {opt_out.reason[:80]}): "
            "gabriel probe をスキップする。"
        ),
    )


# ---------------------------------------------------------------------------
# gabriel 出力契約（2026-09-05 移設 / /full-review iter0 C-5）
#
# 経緯: このスキーマと検証関数は `.claude/tests/wave_c/test_wave_c_gabriel_output.py`
# の**内部にのみ**存在し、本番側から import される箇所が 0 件だった。テスト自身は
# 「実 LLM 呼び出しは行わない / fixtures は stub」と明記しており虚偽ではなかったが、
# 契約の定義が検査側にしか無いため、実運用の記録を検証する経路が作れなかった。
# 正本をここ（本番モジュール）へ移し、テストは import して使う。
#
# `jsonschema` は関数内で import する。本モジュールは managed scripts として配布され、
# 利用者環境に jsonschema があるとは限らないため、import 時に落とさない。
# ---------------------------------------------------------------------------

#: design.md §3 の JSON スキーマ完全定義。
#: additionalProperties: false により、未定義フィールドの混入も検出する。
GABRIEL_OUTPUT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GabrielOutput",
    "type": "object",
    "required": [
        "verdict",
        "severity",
        "affected_atoms",
        "reasoning",
        "recommended_action",
        "confidence",
    ],
    "additionalProperties": False,
    "properties": {
        "verdict": {
            "type": "string",
            "enum": ["confirmed", "refuted", "inconclusive"],
        },
        "severity": {
            "type": "string",
            "enum": ["critical", "warning", "info"],
        },
        "affected_atoms": {
            "type": "array",
            "items": {"type": "string"},
        },
        "reasoning": {
            "type": "string",
            "minLength": 200,
            "maxLength": 1000,
        },
        "recommended_action": {
            "type": "string",
            "enum": ["proceed", "re-magi", "abort"],
        },
        "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
        },
    },
}


class CrossFieldConstraintError(ValueError):
    """クロスフィールド制約違反を表す例外（JSON schema だけでは表現できない制約）。"""


def validate_gabriel_output(data: dict) -> None:
    """gabriel 出力の完全な契約検証を行う。

    1. JSON schema（draft-07）検証（design.md §3）
    2. クロスフィールド制約検証（FR-W-C-6 / design.md §3 フィールド制約テーブル）

    いずれかに違反する場合は例外を送出する。
    Silent Failure を避けるため、違反時は必ず例外を投げる（None 等での握りつぶし禁止）。

    Raises:
        ImportError: jsonschema が利用できない場合（握りつぶさない / 検証できないことを
            「検証に通った」と誤読させないため）
    """
    import jsonschema  # noqa: PLC0415 — 配布先に無い可能性があるため関数内 import

    jsonschema.validate(instance=data, schema=GABRIEL_OUTPUT_SCHEMA)
    _validate_cross_field_constraints(data)


def _validate_cross_field_constraints(data: dict) -> None:
    """FR-W-C-6 / design.md §3 のクロスフィールド制約を検証する。"""
    verdict = data["verdict"]
    severity = data["severity"]
    affected_atoms = data["affected_atoms"]
    recommended_action = data["recommended_action"]
    confidence = data["confidence"]

    # AC-W-C-8: confidence < 0.3 の場合、verdict は inconclusive でなければならない
    if confidence < 0.3 and verdict != "inconclusive":
        raise CrossFieldConstraintError(
            f"confidence={confidence} (<0.3) requires verdict=inconclusive, "
            f"got verdict={verdict!r}"
        )

    # AC-W-C-9: affected_atoms=[] の場合、verdict は refuted であってはならない
    if verdict == "refuted" and not affected_atoms:
        raise CrossFieldConstraintError(
            "verdict=refuted requires non-empty affected_atoms, got []"
        )

    # design.md §3: verdict=confirmed または inconclusive の場合、severity は info
    if verdict in ("confirmed", "inconclusive") and severity != "info":
        raise CrossFieldConstraintError(
            f"verdict={verdict!r} requires severity=info, got severity={severity!r}"
        )

    # design.md §3: severity=critical の場合、recommended_action は re-magi または abort
    if severity == "critical" and recommended_action not in ("re-magi", "abort"):
        raise CrossFieldConstraintError(
            "severity=critical requires recommended_action in "
            f"{{'re-magi', 'abort'}}, got {recommended_action!r}"
        )
