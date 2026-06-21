"""tasks.py - TasksParser 実装（W3-B5-T12）

対応仕様: docs/specs/b4-dashboard/design.md §5「TasksParser」
         docs/specs/b4-dashboard/tasks.md §3 W3-B5-T12
"""

from __future__ import annotations

import re
from pathlib import Path

from dashboard.models import TaskInfo
from dashboard.parsers.base import BaseParser

# チェックボックス行のパターン: ^-\s\[( |x)\]\s(.+)$
# 例: "- [x] W1-B5-T1: BaseParser 実装完了"
#     "- [ ] W2-B5-T7: SessionStateParser 実装予定"
_CHECKBOX_RE = re.compile(r"^-\s\[( |x)\]\s(.+)$")

# チェックボックス状態から status 値へのマッピング
_STATUS_MAP = {
    "x": "completed",
    " ": "not-started",
}

# Task ID パターン: W<wave>-<MILESTONE_SLUG>-T<num>
# 例: W1-B5-T1, W2-B5-T7, W1.5-B4-T9
_TASK_ID_PREFIX_RE = re.compile(r"^(W\d+(?:\.\d+)?-[A-Za-z0-9]+-T\d+)")


class TasksParser(BaseParser):
    """docs/specs/ 配下の tasks.md からタスク情報を抽出するパーサ。

    入力: docs/specs/<milestone>/tasks.md（存在するすべての Milestone 分）
    責務: チェックボックス行（- [ ] / - [x]）をスキャンし TaskInfo エントリを構築

    戻り値の data キー:
        tasks: list[TaskInfo]  全 Milestone の Task 一覧
    """

    def __init__(self, project_root: Path) -> None:
        self._project_root = Path(project_root)

    def parse(self) -> dict:
        """docs/specs/ を走査してチェックボックス行から Task を抽出する。

        失敗条件:
          - 予期しない例外（通常は発生しない）

        docs/specs/ が存在しない場合も ok=True / tasks=[] を返す（仕様準拠）。
        個別 Milestone の失敗は他の処理を止めない。
        """
        try:
            return self._do_parse()
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": str(e), "data": None}

    def _do_parse(self) -> dict:
        """実際のパース処理。例外はそのまま上位に伝播させる。"""
        specs_dir = self._project_root / "docs" / "specs"

        if not specs_dir.exists():
            return {"ok": True, "error": None, "data": {"tasks": []}}

        tasks: list[TaskInfo] = []
        for milestone_dir in sorted(specs_dir.iterdir()):
            if not milestone_dir.is_dir():
                continue
            tasks_file = milestone_dir / "tasks.md"
            if not tasks_file.exists():
                continue
            milestone_tasks = self._parse_tasks_file(tasks_file, milestone_dir.name)
            tasks.extend(milestone_tasks)

        return {"ok": True, "error": None, "data": {"tasks": tasks}}

    def _parse_tasks_file(self, tasks_file: Path, milestone_name: str) -> list[TaskInfo]:
        """tasks.md ファイルからチェックボックス行を抽出し TaskInfo リストを返す。

        個別ファイルのエラーは空リストで吸収し、上位処理を止めない。
        """
        try:
            content = tasks_file.read_text(encoding="utf-8")
            return self._extract_tasks(content, milestone_name)
        except Exception:  # noqa: BLE001
            return []

    def _extract_tasks(self, content: str, milestone_name: str) -> list[TaskInfo]:
        """テキストコンテンツからチェックボックス行を抽出して TaskInfo リストを構築する。"""
        tasks: list[TaskInfo] = []
        for line in content.splitlines():
            match = _CHECKBOX_RE.match(line)
            if match is None:
                continue
            checkbox_value = match.group(1)
            description = match.group(2).strip()
            status = _STATUS_MAP[checkbox_value]
            task_id = self._extract_task_id(description)
            tasks.append(
                TaskInfo(
                    id=task_id,
                    milestone=milestone_name,
                    assignee="-",
                    status=status,
                )
            )
        return tasks

    def _extract_task_id(self, description: str) -> str:
        """チェックボックス行の説明文から Task ID を抽出する。

        説明文の先頭が "W<num>-<LETTER><num>-T<num>:" 形式であれば Task ID を返す。
        該当しない場合は説明文全体を ID として使用する。

        例:
            "W1-B5-T1: BaseParser 実装完了" → "W1-B5-T1"
            "対応する仕様書が存在する" → "対応する仕様書が存在する"
        """
        task_id_match = _TASK_ID_PREFIX_RE.match(description)
        if task_id_match:
            return task_id_match.group(1)
        # Task ID が見つからない場合は説明文をそのまま ID として使用
        return description
