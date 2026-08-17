"""session_state.py - SessionStateParser 実装（W2-B5-T7）

対応仕様: docs/specs/b4-dashboard/design.md §5「SessionStateParser」
         docs/specs/b4-dashboard/tasks.md §3 W2-B5-T7
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple, Optional

from dashboard.models import MilestoneInfo, WaveInfo
from dashboard.parsers.base import BaseParser

# SESSION_STATE.md 内のタスク ID パターン: W<wave>-<LETTER><num>-T<num>
# 例: W1-B5-T1 (Milestone=B-5), W7-B4-T9 (Milestone=B-4)
# ※ タスク ID 内の Milestone 表記はハイフンなし（B5）。抽出後に B-5 形式に変換する
_TASK_ID_RE = re.compile(r"W(\d+(?:\.\d+)?)-([A-Z])(\d+)-T(\d+)")

# フォールバック抽出パターン（タスク ID が存在しない書式の SESSION_STATE.md 対応）
# Milestone: B-5, R-1 等（大文字 1 文字 + ハイフン + 数字 / R-1 W-R1 S1 T6 で B → [A-Z] に拡張）
# 拡張根拠: rule-001 パターン発火 3 回目 (2026-07-06) 対策 / Fable→Opus 実装ギャップ #1 恒久解
_FALLBACK_MILESTONE_RE = re.compile(r"\b([A-Z]-\d+)\b")
# Wave: "Wave 7", "Wave 1.5" 等（既存）
_FALLBACK_WAVE_RE = re.compile(r"\bWave\s+(\d+(?:\.\d+)?)\b")
# Wave (ハイフン記法): "W-R1", "W-R2" 等（R-1 W-R1 S1 T6 で追加 / W-<Letter><Num> 形式）
_FALLBACK_WAVE_HYPHEN_RE = re.compile(r"\bW-([A-Z]\d+(?:\.\d+)?)\b")

# セクション見出しパターン（## または ###）
_SECTION_RE = re.compile(r"^#{2,3}\s+(.+)$", re.MULTILINE)

# --- 宣言欄の解析（2026-08-17 / rule-001 §構造的論点の恒久解 (c)）--------------
#
# 現在の Milestone は SESSION_STATE.md ヘッダの宣言欄を**正本**とする。散文からの
# 推論は宣言欄が無い旧書式のための fallback に降格した。
#
# 根拠（2026-08-17 の実測）: 旧実装は `参考: 直近実績` に残るセッション 18 の記録
# `W1-D1-T1` 1 箇所から `D-1 / in-progress` を導出していた。D-1 は 2026-08-13 に
# クローズ済であり、ダッシュボードはクローズ済 Milestone を進行中と表示していた。
# retention 検査は緑のままだったため、**壊れても静かな計器**になっていた。
_DECLARED_MILESTONE_RE = re.compile(
    r"^\*\*現在の\s*Milestone\*\*\s*[:：]\s*(.+?)\s*$", re.MULTILINE
)
# 「Milestone は存在しない」を表す明示値。**「なし」は正当な値であり欠落ではない。**
_NONE_MARKERS = frozenset({"なし", "無し", "none", "n/a", "-", "—", "ー", ""})


class DeclaredMilestone(NamedTuple):
    """SESSION_STATE.md ヘッダで宣言された Milestone 状態。

    Attributes:
        raw:      宣言欄の生の値（診断メッセージ用）
        name:     Milestone 名（例 'B-5'）。「なし」または解釈不能なら None
        is_none:  明示的に「なし」と宣言されている
    """

    raw: str
    name: Optional[str]
    is_none: bool

    @property
    def interpretable(self) -> bool:
        """「なし」か Milestone 名のどちらかとして読めるか。

        どちらでもない値（典型: 誤字）を「なし」と同一視すると、宣言欄が黙って
        無効化される。呼び出し側はこの述語で不正な宣言を検出すること。
        """
        return self.name is not None or self.is_none


def _scan_wave_numbers(content: str) -> list:
    """本文から Wave 番号を重複排除して列挙する（旧記法 + ハイフン記法）。

    宣言経路と旧書式 fallback の双方から使う共通部品。
    """
    seen: set = set()
    nums: list = []
    for regex in (_FALLBACK_WAVE_RE, _FALLBACK_WAVE_HYPHEN_RE):
        for match in regex.finditer(content):
            num = match.group(1)
            if num not in seen:
                seen.add(num)
                nums.append(num)
    return nums


def _strip_annotation(value: str) -> str:
    """宣言値から markdown 強調と注釈（括弧以降）を取り除く。

    ハイフンは Milestone 名（`B-5`）の構成要素なので区切り文字に含めない。
    """
    cleaned = value.replace("**", "").replace("`", "").strip()
    for sep in ("（", "(", "/", "—", "…"):
        idx = cleaned.find(sep)
        if idx != -1:
            cleaned = cleaned[:idx]
    return cleaned.strip()


def parse_declared_milestone(content: str) -> Optional[DeclaredMilestone]:
    """SESSION_STATE.md 本文から Milestone 宣言欄を読む。

    Returns:
        宣言欄が無ければ None（= 旧書式 / 呼び出し側は散文推論へ落とす）。
    """
    match = _DECLARED_MILESTONE_RE.search(content)
    if match is None:
        return None

    raw = match.group(1).strip()
    cleaned = _strip_annotation(raw)
    if cleaned.lower() in _NONE_MARKERS:
        return DeclaredMilestone(raw=raw, name=None, is_none=True)

    name_match = _FALLBACK_MILESTONE_RE.search(cleaned)
    if name_match is not None:
        return DeclaredMilestone(raw=raw, name=name_match.group(1), is_none=False)
    return DeclaredMilestone(raw=raw, name=None, is_none=False)


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

        milestones, waves = self._resolve_milestone_wave(content)

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

    def _resolve_milestone_wave(
        self, content: str
    ) -> tuple[list[MilestoneInfo], list[WaveInfo]]:
        """Milestone / Wave を決定する。**宣言欄が正本、散文推論は fallback。**

        判定順:
          1. 宣言欄あり かつ 解釈可能 → 宣言を採用（散文は見ない）
             - 「なし」 → 空リスト（不在は正常であり、痕跡テキストを要求しない）
             - Milestone 名 → その Milestone。Wave は散文から拾うが**当該 Milestone
               に属するものだけ**に絞る（他 Milestone の履歴を現在状態にしない）
          2. 宣言欄なし / 解釈不能 → 旧書式として散文推論（後方互換）
        """
        declared = parse_declared_milestone(content)
        if declared is not None and declared.interpretable:
            if declared.is_none:
                return [], []
            _, inferred_waves = self._build_milestone_wave_lists(
                _extract_task_ids_from_text(content)
            )
            waves = [w for w in inferred_waves if w.milestone == declared.name]
            if not waves:
                # タスク ID 形式が無い書式（例: `W-R1 S1 T6`）向け。Wave 番号だけを
                # 拾い、**宣言された Milestone とだけ**組む（クロス積を作らない）
                waves = [
                    WaveInfo(
                        milestone=declared.name,
                        wave_number=num,
                        task_count=0,
                        status="in-progress",
                    )
                    for num in _scan_wave_numbers(content)
                ]
            return (
                [
                    MilestoneInfo(
                        name=declared.name,
                        current_step="UNKNOWN",
                        status="in-progress",
                    )
                ],
                waves,
            )

        # 旧書式: タスク ID ベース → 直接スキャンの順でフォールバック
        milestones, waves = self._build_milestone_wave_lists(
            _extract_task_ids_from_text(content)
        )
        if not milestones:
            milestones, waves = self._extract_milestones_waves_fallback(content)
        return milestones, waves

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

        wave_nums = _scan_wave_numbers(content)
        seen_wave_nums = set(wave_nums)

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
