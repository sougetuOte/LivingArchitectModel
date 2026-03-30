"""モジュール間帰責ヒントのパーサー（スタンドアロン版）。

他プロジェクトの card_generator.py に追加するか、
独立モジュールとして配置して使用する。

対応仕様: cross-module-blame-spec.md FR-2c
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Blame Hint parsing (cross-module-blame FR-2c)
# ---------------------------------------------------------------------------

_BLAME_START = "---BLAME-HINT---"
_BLAME_END = "---END-BLAME-HINT---"
_BLAME_FIELDS = ("issue", "suspected_responsible", "module", "reason")
_VALID_RESPONSIBLE = frozenset({"upstream", "downstream", "spec_ambiguity", "unknown"})

BlameHint = dict[str, str]


def parse_blame_hint(agent_output: str) -> list[BlameHint]:
    """Agent 出力から BLAME-HINT マーカー間のフィールドを抽出する。

    複数の BLAME-HINT ブロックに対応。
    マーカーがない場合は空リストを返す（フォールバック）。
    """
    hints: list[BlameHint] = []
    search_start = 0

    while True:
        start_idx = agent_output.find(_BLAME_START, search_start)
        if start_idx == -1:
            break
        end_idx = agent_output.find(_BLAME_END, start_idx)
        if end_idx == -1:
            search_start = start_idx + len(_BLAME_START)
            continue  # 閉じマーカーなし → 次ブロックを探索（NFR-3）

        content = agent_output[start_idx + len(_BLAME_START) : end_idx]
        hint: BlameHint = {}
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            for field in _BLAME_FIELDS:
                prefix = field + ":"
                if line.startswith(prefix):
                    hint[field] = line[len(prefix) :].strip()
                    break

        if hint:
            responsible = hint.get("suspected_responsible", "")
            if responsible and responsible not in _VALID_RESPONSIBLE:
                hint["suspected_responsible"] = "unknown"
            hints.append(hint)

        search_start = end_idx + len(_BLAME_END)

    return hints
