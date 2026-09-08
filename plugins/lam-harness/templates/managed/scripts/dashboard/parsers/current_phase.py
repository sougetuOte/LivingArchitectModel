"""current_phase.py - CurrentPhaseParser 実装（W2-B5-T8）

対応仕様: docs/specs/b4-dashboard/design.md §5「CurrentPhaseParser」

設計判断（L1 確定）:
    仕様の「1 行目を strip() して返す」ではなく、実際の .claude/current-phase.md の
    構造（1 行目が "# Current Phase"、Phase 名は "**BUILDING**" 形式で本文中に記載）に
    合わせて、全文 regex スキャンで Phase 名を抽出する。
    次セッション AUDITING で design.md §5 に反映予定（PM 級判断）。
"""

from __future__ import annotations

import re
from pathlib import Path

from dashboard.parsers.base import BaseParser

# 有効な Phase 値
_VALID_PHASES = ("PLANNING", "BUILDING", "AUDITING", "AUTONOMOUS")

# Phase 名を bold 記法で囲んだパターン: **BUILDING** など
_PHASE_PATTERN = re.compile(r"\*\*(" + "|".join(_VALID_PHASES) + r")\*\*")


class CurrentPhaseParser(BaseParser):
    """`.claude/current-phase.md` から現在の Phase 文字列を抽出するパーサ。

    戻り値の data キー::

        {"phase": str}  # "PLANNING" / "BUILDING" / "AUDITING" / "AUTONOMOUS" / "UNKNOWN"

    マッチしない場合・空ファイルの場合は phase: "UNKNOWN" を返す（ok=True）。
    ファイル不在・読み込みエラー時は ok=False を返す。
    例外は外に伝播させない（MUST）。
    """

    def __init__(self, project_root: Path) -> None:
        self._phase_file = Path(project_root) / ".claude" / "current-phase.md"

    def parse(self) -> dict:
        """current-phase.md を読み込み、Phase 文字列を抽出して返す。

        Returns:
            dict: ok / error / data の 3 キーを持つ dict。
                - ok=True のとき data={"phase": str}、error=None
                - ok=False のとき data=None、error=エラーメッセージ
        """
        try:
            content = self._phase_file.read_text(encoding="utf-8")
        except OSError as exc:
            return {"ok": False, "error": str(exc), "data": None}

        match = _PHASE_PATTERN.search(content)
        phase = match.group(1) if match else "UNKNOWN"

        return {"ok": True, "error": None, "data": {"phase": phase}}
