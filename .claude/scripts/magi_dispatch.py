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
        is_timeout: gabriel が 60 秒制限 (NFR-W-C-1) を超過した場合 True

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
            "> [NOTE]: gabriel がタイムアウト（> 60 秒）しました。inconclusive として処理します。\n"
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
