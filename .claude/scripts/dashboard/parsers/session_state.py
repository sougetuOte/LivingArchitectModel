"""session_state.py - SessionStateParser 実装（W2-B5-T7）

対応仕様: docs/specs/b4-dashboard/design.md §5「SessionStateParser」
         docs/specs/b4-dashboard/tasks.md §3 W2-B5-T7
"""

from __future__ import annotations

import re
from pathlib import Path

from dashboard.models import MilestoneInfo, WaveInfo
from dashboard.parsers.base import BaseParser

# SESSION_STATE.md 内のタスク ID パターン: W<wave>-<LETTER><num>-T<num>
# 例: W1-B5-T1 (Milestone=B-5), W7-B4-T9 (Milestone=B-4)
# ※ タスク ID 内の Milestone 表記はハイフンなし（B5）。抽出後に B-5 形式に変換する
_TASK_ID_RE = re.compile(r"W(\d+(?:\.\d+)?)-([A-Z])(\d+)-T(\d+)")

# フォールバック抽出パターン（タスク ID が存在しない書式の SESSION_STATE.md 対応）
# Milestone: B-5, B-4 等（大文字 1 文字 + ハイフン + 数字）
_FALLBACK_MILESTONE_RE = re.compile(r"\b(B-\d+)\b")
# Wave: "Wave 7", "Wave 1.5" 等
_FALLBACK_WAVE_RE = re.compile(r"\bWave\s+(\d+(?:\.\d+)?)\b")

# セクション見出しパターン（## または ###）
_SECTION_RE = re.compile(r"^#{2,3}\s+(.+)$", re.MULTILINE)


def _is_completed_section(title: str) -> bool:
    """見出しが「完了タスク」セクションか判定する。"""
    lower = title.lower()
    return "完了タスク" in title or "completed" in lower


def _is_in_progress_section(title: str) -> bool:
    """見出しが「進行中タスク」セクションか判定する。"""
    return "進行中タスク" in title or "in progress" in title.lower() or "in_progress" in title.lower()


def _is_blocked_section(title: str) -> bool:
    """見出しが「未解決の問題」セクションか判定する。"""
    return "未解決" in title or "問題" in title or "blocked" in title.lower()


def _extract_bullet_lines(text: str) -> list[str]:
    """テキストから箇条書き行（- で始まる行）を抽出する。

    「なし」で始まるコンテンツ行は除外する（進行中タスクなし等の記述に対応）。
    """
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("-"):
            continue
        content = stripped.lstrip("-").strip()
        # 「なし」で始まる行を除外（「なし（...）」「なし。」等も含む）
        if content.startswith("なし"):
            continue
        if content:
            lines.append(content)
    return lines


def _extract_task_ids_from_text(text: str) -> list[tuple[str, str, str]]:
    """テキスト全体からタスク ID を抽出する。

    タスク ID 形式: W<wave>-<LETTER><num>-T<tasknum>
    例: W1-B5-T1 → wave="1", milestone="B-5"（ハイフンあり形式に変換）

    Returns:
        list of (wave_number, milestone_name, full_task_id)
    """
    found = []
    for m in _TASK_ID_RE.finditer(text):
        wave_number = m.group(1)
        ms_letter = m.group(2)
        ms_num = m.group(3)
        milestone = f"{ms_letter}-{ms_num}"  # B5 → B-5 形式に変換
        found.append((wave_number, milestone, m.group(0)))
    return found


class SessionStateParser(BaseParser):
    """SESSION_STATE.md から進捗データを抽出するパーサ。

    入力: SESSION_STATE.md（プロジェクトルート直下）
    責務: 進行中タスク・完了タスク・未解決問題・Milestone・Wave を抽出

    戻り値の data キー:
        milestones: list[MilestoneInfo]  Milestone 一覧（重複排除済み）
        waves:      list[WaveInfo]       Wave 一覧（重複排除済み）
        in_progress: list[str]           進行中タスクのテキスト行
        blocked:    list[str]            未解決問題のテキスト行
        completed:  list[str]            完了タスクのテキスト行
    """

    def __init__(self, project_root: Path) -> None:
        self._project_root = Path(project_root)

    def parse(self) -> dict:
        """SESSION_STATE.md を解析して正規化されたデータを返す。

        失敗条件:
          - SESSION_STATE.md が存在しない
          - ファイル読み込みエラー

        パース結果が空でも ok=True で空リストを返す（仕様準拠）。
        """
        try:
            return self._do_parse()
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": str(e), "data": None}

    def _do_parse(self) -> dict:
        """実際のパース処理。例外はそのまま上位に伝播させる。"""
        session_file = self._project_root / "SESSION_STATE.md"
        if not session_file.exists():
            raise FileNotFoundError(f"SESSION_STATE.md が見つかりません: {session_file}")

        content = session_file.read_text(encoding="utf-8")
        sections = self._split_sections(content)

        in_progress = self._extract_in_progress(sections)
        completed = self._extract_completed(sections)
        blocked = self._extract_blocked(sections)

        # Milestone / Wave を全テキストから抽出（タスク ID ベース）
        task_tuples = _extract_task_ids_from_text(content)
        milestones, waves = self._build_milestone_wave_lists(task_tuples)

        # タスク ID が存在しない場合（書式変化対応）: テキスト直接スキャンでフォールバック
        if not milestones:
            milestones, waves = self._extract_milestones_waves_fallback(content)

        return {
            "ok": True,
            "error": None,
            "data": {
                "milestones": milestones,
                "waves": waves,
                "in_progress": in_progress,
                "blocked": blocked,
                "completed": completed,
            },
        }

    def _split_sections(self, content: str) -> dict[str, str]:
        """見出し（## / ###）でコンテンツをセクションに分割する。

        Returns:
            dict mapping section_title -> section_body
        """
        sections: dict[str, str] = {}
        matches = list(_SECTION_RE.finditer(content))

        for i, match in enumerate(matches):
            title = match.group(1).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            body = content[start:end]
            sections[title] = body

        return sections

    def _extract_in_progress(self, sections: dict[str, str]) -> list[str]:
        """進行中タスクのセクションから箇条書き行を取得する。"""
        for title, body in sections.items():
            if _is_in_progress_section(title):
                return _extract_bullet_lines(body)
        return []

    def _extract_completed(self, sections: dict[str, str]) -> list[str]:
        """完了タスクのセクションから箇条書き行を取得する。"""
        for title, body in sections.items():
            if _is_completed_section(title):
                return _extract_bullet_lines(body)
        return []

    def _extract_blocked(self, sections: dict[str, str]) -> list[str]:
        """未解決の問題セクションから箇条書き行を取得する。"""
        for title, body in sections.items():
            if _is_blocked_section(title):
                return _extract_bullet_lines(body)
        return []

    def _build_milestone_wave_lists(
        self,
        task_tuples: list[tuple[str, str, str]],
    ) -> tuple[list[MilestoneInfo], list[WaveInfo]]:
        """タスク ID 群から MilestoneInfo / WaveInfo リストを構築する。

        重複排除を行い、それぞれユニークなエントリのみ返す。
        """
        seen_milestones: set[str] = set()
        seen_waves: set[tuple[str, str]] = set()  # (milestone, wave_number)
        milestones: list[MilestoneInfo] = []
        waves: list[WaveInfo] = []

        for wave_number, milestone_name, _full_id in task_tuples:
            if milestone_name not in seen_milestones:
                seen_milestones.add(milestone_name)
                milestones.append(
                    MilestoneInfo(
                        name=milestone_name,
                        current_step="UNKNOWN",  # CurrentPhaseParser で補完
                        status="in-progress",    # 状態決定ロジックは V-3/V-4 ビュー側
                    )
                )

            wave_key = (milestone_name, wave_number)
            if wave_key not in seen_waves:
                seen_waves.add(wave_key)
                waves.append(
                    WaveInfo(
                        milestone=milestone_name,
                        wave_number=wave_number,
                        task_count=0,   # TasksParser で補完
                        status="in-progress",  # 状態決定ロジックは V-3 ビュー側
                    )
                )

        return milestones, waves

    def _extract_milestones_waves_fallback(
        self,
        content: str,
    ) -> tuple[list[MilestoneInfo], list[WaveInfo]]:
        """タスク ID が存在しない書式向けのフォールバック抽出。

        B-N パターンで Milestone を、Wave N パターンで Wave 番号を取得する。
        Wave は各 Milestone に関連付ける（全 Milestone x 全 Wave のクロス）。
        重複排除済みのリストを返す。
        """
        seen_milestones: set[str] = set()
        milestones: list[MilestoneInfo] = []
        for m in _FALLBACK_MILESTONE_RE.finditer(content):
            name = m.group(1)
            if name not in seen_milestones:
                seen_milestones.add(name)
                milestones.append(
                    MilestoneInfo(
                        name=name,
                        current_step="UNKNOWN",
                        status="in-progress",
                    )
                )

        seen_wave_nums: set[str] = set()
        wave_nums: list[str] = []
        for m in _FALLBACK_WAVE_RE.finditer(content):
            num = m.group(1)
            if num not in seen_wave_nums:
                seen_wave_nums.add(num)
                wave_nums.append(num)

        waves: list[WaveInfo] = []
        seen_waves: set[tuple[str, str]] = set()
        for milestone_name in seen_milestones:
            for wave_number in wave_nums:
                key = (milestone_name, wave_number)
                if key not in seen_waves:
                    seen_waves.add(key)
                    waves.append(
                        WaveInfo(
                            milestone=milestone_name,
                            wave_number=wave_number,
                            task_count=0,
                            status="in-progress",
                        )
                    )

        return milestones, waves
