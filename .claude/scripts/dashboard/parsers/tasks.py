"""tasks.py - TasksParser 実装（W3-B5-T12 / T56 再帰走査対応 / T48 Assignee 抽出対応）

対応仕様: docs/specs/b4-dashboard/design.md §5「TasksParser」
         docs/specs/b4-dashboard/tasks.md §3 W3-B5-T12
         docs/specs/b4-dashboard/wave7/design.md §6「実装の追加要件」（T56）
         docs/specs/b4-dashboard/wave7/design.md §7「Stage 2: Assignee タグ規約の実装」（T48）
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

# Task ID パターン（Wave 7 厳格化 / FR-W7-1）:
#   W<wave>-<MILESTONE>-T<num> 形式 または T<num> 単独形式
#   Milestone 名は大文字アルファベット + 数字のみ（小文字混在は不正）
#   Wave 番号は整数（W1, W7）と整数.5（W1.5）の両方を許容（terminology.md §2 準拠）
#   行頭固定・コロン直後まで。それ以外の行は Task として抽出しない。
# 例: W1-B5-T1: → "W1-B5-T1"
#     W1.5-B4-T9: → "W1.5-B4-T9"
#     T99: → "T99"
#     詳細: → None（抽出しない）
_TASK_ID_PREFIX_RE = re.compile(r"^(W\d+(?:\.\d+)?-[A-Z]\d+-T\d+|T\d+):")

# 完全形 Task ID から Milestone 名を逆引きするパターン
# 例: W7-B5-T44 → B5 → "B-5"
#     W1.5-B4-T9 → B4 → "B-4"
_MILESTONE_FROM_TASK_ID_RE = re.compile(r"^W\d+(?:\.\d+)?-([A-Z])(\d+)-T\d+")

# description 末尾の @<assignee> タグを抽出するパターン（Wave 7 FR-W7-2 / design.md §7）
# - \s+: タグ前の空白（必須）
# - @([A-Za-z0-9_-]+): @ 接頭辞 + 英数字・アンダースコア・ハイフンからなる担当者名
# - \s*$: タグ後の空白（任意）+ 末尾固定
# 注: re.MULTILINE なし（Python 3 標準で $ は文字列末尾にマッチ）
# 例: "Task 説明 @Sonnet" → "Sonnet"
#     "メール @example.com を更新 @Sonnet" → "Sonnet"（末尾の @Sonnet のみ）
ASSIGNEE_REGEX = r"\s+@([A-Za-z0-9_-]+)\s*$"


def _extract_assignee(description: str) -> tuple[str, str]:
    """description 末尾から @<assignee> タグを抽出する（Wave 7 FR-W7-2 / design.md §7）。

    戻り値: (clean_description, assignee)
      - clean_description: @<assignee> タグを除去し末尾空白を strip した description
      - assignee: タグの担当者名（"Sonnet" 等）/ 未マッチ時は "-"

    中間の @ は除去されない:
      "メール @example.com を更新 @Sonnet" → ("メール @example.com を更新", "Sonnet")
    """
    match = re.search(ASSIGNEE_REGEX, description)
    if match:
        assignee = match.group(1)
        clean = description[: match.start()].rstrip()
        return clean, assignee
    return description, "-"


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
        """実際のパース処理。例外はそのまま上位に伝播させる。

        T56: specs_dir.glob("**/tasks.md") による再帰走査に変更。
        直下の tasks.md（例: b4-dashboard/tasks.md）も引き続き走査対象。
        """
        specs_dir = self._project_root / "docs" / "specs"

        if not specs_dir.exists():
            return {"ok": True, "error": None, "data": {"tasks": []}}

        tasks: list[TaskInfo] = []
        for tasks_file in sorted(specs_dir.glob("**/tasks.md")):
            milestone_tasks = self._parse_tasks_file(tasks_file, tasks_file.parent.name)
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

    def _extract_tasks(self, content: str, fallback_milestone: str) -> list[TaskInfo]:
        """テキストコンテンツからチェックボックス行を抽出して TaskInfo リストを構築する。

        Wave 7 厳格化（FR-W7-1）: _extract_task_id() が None を返す行は Task として
        登録しない（旧: description 全体を ID にしてフォールバック登録 → 誤抽出）。

        T56: milestone 名を Task ID から逆引きする。
          - 完全形 W{n}-B{n}-T{n}: `B{n}` → `B-{n}` 形式（例: B5 → "B-5"）
          - 短縮形 T{n}: fallback_milestone（tasks.md の直近親ディレクトリ名）を使用
        """
        tasks: list[TaskInfo] = []
        for line in content.splitlines():
            match = _CHECKBOX_RE.match(line)
            if match is None:
                continue
            checkbox_value = match.group(1)
            description = match.group(2).strip()
            status = _STATUS_MAP[checkbox_value]
            task_id = self._extract_task_id(description)
            if task_id is None:
                continue  # Task ID 形式でない行はスキップ（AC-W7-1 誤抽出ゼロ化）
            milestone = self._resolve_milestone(task_id, fallback_milestone)
            # description から Task ID 部分（"W7-B5-T44: "）を除いた残りを取得
            # _extract_task_id() は先頭の ID 部分のみを返すので、":"以降が実際の説明文
            id_prefix = task_id + ":"
            raw_description = description[len(id_prefix):].strip()
            _, assignee = _extract_assignee(raw_description)
            tasks.append(
                TaskInfo(
                    id=task_id,
                    milestone=milestone,
                    assignee=assignee,
                    status=status,
                )
            )
        return tasks

    def _resolve_milestone(self, task_id: str, fallback: str) -> str:
        """Task ID から Milestone 名を逆引きする（T56）。

        完全形 W{n}-B{letter}{num}-T{n} の場合: `B{letter}{num}` → `{letter}-{num}` 形式
          例: W7-B5-T44 → "B-5"
              W1.5-B4-T9 → "B-4"
        短縮形 T{n} の場合: fallback（tasks.md の親ディレクトリ名）を使用
          例: T31 → "goal-driven-orchestration"（引数で渡された値）
        """
        milestone_match = _MILESTONE_FROM_TASK_ID_RE.match(task_id)
        if milestone_match:
            letter = milestone_match.group(1)
            num = milestone_match.group(2)
            return f"{letter}-{num}"
        return fallback

    def _extract_task_id(self, description: str) -> str | None:
        """チェックボックス行の説明文から Task ID を抽出する（Wave 7 厳格化 / FR-W7-1）。

        説明文の先頭が "W<num>-<MILESTONE>-T<num>:" または "T<num>:" 形式であれば
        Task ID 文字列を返す。該当しない場合は None を返す（Task として登録しない）。

        旧実装との差分:
          旧: マッチしない場合 description 全体を ID として返す（誤抽出の根本原因）
          新: マッチしない場合 None を返し、呼び出し側でスキップ（AC-W7-1 誤抽出ゼロ化）

        例:
            "W1-B5-T1: BaseParser 実装完了" → "W1-B5-T1"
            "W1.5-B4-T9: 波及修正" → "W1.5-B4-T9"
            "T99: 単発タスク" → "T99"
            "詳細: parser 強化" → None
            "さらに具体的な手順を: ..." → None
        """
        task_id_match = _TASK_ID_PREFIX_RE.match(description)
        if task_id_match:
            return task_id_match.group(1)
        return None
