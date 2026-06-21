"""git_history.py - GitHistoryParser 実装（W3-B5-T13）

対応仕様: docs/specs/b4-dashboard/design.md §5「GitHistoryParser」

実データパターン（git log --oneline -100 で確認済み）:
    feat(B-5): b4-dashboard Wave 2 パーサ層 + V-2 ビュー実装（W2-B5-T7〜T11・テスト 144/144 PASS）
    feat(B-5): b4-dashboard Wave 1 骨格実装 (W1-B5-T1〜T5, テスト 47/47 PASS)
    docs(B-5): B-4 Wave 1.5 波及不整合修正（W-1〜W-5）
    docs(specs): W7-T2b + PM-G3 完了チェック記入
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from dashboard.parsers.base import BaseParser

# Wave 番号を検出するパターン（例: "Wave 2", "wave 1.5", "Wave 1"）
# terminology.md §4: Wave は正整数または「整数.5」形式
_WAVE_PATTERN = re.compile(r"[Ww]ave\s+(\d+(?:\.\d+)?)")

# Task ID を検出するパターン
# 形式1: W2-B5-T7 （Wave番号-Milestone-Task番号、末尾にアルファベットも許容）
# 形式2: W7-T2b （Milestone 省略、短縮形）
_TASK_PATTERN = re.compile(r"\b(W\d+-(?:[A-Z][0-9]+-)?T\d+[a-z]?)\b")


class GitHistoryParser(BaseParser):
    """git log --oneline -100 からコミット完了情報を抽出するパーサ。

    戻り値の data キー::

        {
            "completed_waves": list[str],  # 検出された Wave 番号の文字列リスト（重複なし）
            "completed_tasks": list[str],  # 検出された Task ID の文字列リスト（重複なし）
        }

    git log 実行失敗・例外発生時は ok=False を返す（MUST NOT エラー終了）。
    例外は外に伝播させない（MUST、FR-6）。
    """

    def __init__(self, project_root: Path) -> None:
        self._project_root = Path(project_root)

    def parse(self) -> dict:
        """git log を実行し、Wave / Task 完了情報を抽出して返す。

        Returns:
            dict: ok / error / data の 3 キーを持つ dict。
                - ok=True のとき data={"completed_waves": list, "completed_tasks": list}、error=None
                - ok=False のとき data=None、error=エラーメッセージ
        """
        try:
            return self._do_parse()
        except Exception as exc:
            return {"ok": False, "error": str(exc), "data": None}

    def _do_parse(self) -> dict:
        """git log を実行して解析する内部メソッド。"""
        result = subprocess.run(
            ["git", "log", "--oneline", "-100"],
            cwd=str(self._project_root),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return {
                "ok": False,
                "error": f"git log failed: {result.stderr}",
                "data": None,
            }

        completed_waves = _extract_waves(result.stdout)
        completed_tasks = _extract_tasks(result.stdout)

        return {
            "ok": True,
            "error": None,
            "data": {
                "completed_waves": completed_waves,
                "completed_tasks": completed_tasks,
            },
        }


def _extract_waves(log_output: str) -> list[str]:
    """git log 出力から Wave 番号を抽出して重複排除済みリストを返す。

    Args:
        log_output: git log --oneline 出力の全文字列。

    Returns:
        重複なしの Wave 番号文字列リスト（例: ["1", "1.5", "2"]）。
    """
    seen: set[str] = set()
    result: list[str] = []
    for match in _WAVE_PATTERN.finditer(log_output):
        wave_num = match.group(1)
        if wave_num not in seen:
            seen.add(wave_num)
            result.append(wave_num)
    return result


def _extract_tasks(log_output: str) -> list[str]:
    """git log 出力から Task ID を抽出して重複排除済みリストを返す。

    Args:
        log_output: git log --oneline 出力の全文字列。

    Returns:
        重複なしの Task ID 文字列リスト（例: ["W2-B5-T7", "W7-T2b"]）。
    """
    seen: set[str] = set()
    result: list[str] = []
    for match in _TASK_PATTERN.finditer(log_output):
        task_id = match.group(1)
        if task_id not in seen:
            seen.add(task_id)
            result.append(task_id)
    return result
