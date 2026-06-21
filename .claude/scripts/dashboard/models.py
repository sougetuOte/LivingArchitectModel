"""models.py - ダッシュボード用データクラス定義（W1-B5-T1）

対応仕様: docs/specs/b4-dashboard/design.md §5「データモデル」
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MilestoneInfo:
    """Milestone の状態情報。

    Attributes:
        name: Milestone 名。例: "B-5"
        current_step: 現在の Step 名。例: "PLANNING"（CurrentPhaseParser から補完）
        status: 状態値。"not-started" / "in-progress" / "blocked" / "completed" のいずれか
    """

    name: str
    current_step: str
    status: str


@dataclass
class WaveInfo:
    """Wave の状態情報。

    Attributes:
        milestone: 属する Milestone 名。例: "B-5"
        wave_number: Wave 番号の文字列表現。例: "1", "1.5"
        task_count: この Wave に属する Task 数（TasksParser から補完）
        status: 状態値。"not-started" / "in-progress" / "blocked" / "completed" のいずれか
    """

    milestone: str
    wave_number: str
    task_count: int
    status: str


@dataclass
class TaskInfo:
    """Task の状態情報。

    Attributes:
        id: Task 識別子。例: "W1-B5-T1"
        milestone: 属する Milestone 名。例: "B-5"
        assignee: 担当者名。例: "Sonnet", "-"
        status: 状態値。"not-started" / "in-progress" / "blocked" / "completed" のいずれか
    """

    id: str
    milestone: str
    assignee: str
    status: str


@dataclass
class DashboardData:
    """全パーサの結果を統合するダッシュボードデータ。

    DashboardBuilder がこのオブジェクトを受け取り HTML を生成する。
    parser_errors に 1 件以上ある場合、HTML 末尾にエラーサマリーを表示する。

    Attributes:
        milestones: Milestone 一覧（V-2 ビュー用）
        waves: Wave 一覧（V-3 ビュー用）
        tasks: Task 一覧（V-4 ビュー用）
        current_phase: 現在の Phase 文字列（CurrentPhaseParser から取得）
        generated_at: HTML 生成日時（ISO 8601 形式）
        parser_errors: パーサエラーのサマリーリスト（エラーがない場合は空リスト）
    """

    milestones: list[MilestoneInfo] = field(default_factory=list)
    waves: list[WaveInfo] = field(default_factory=list)
    tasks: list[TaskInfo] = field(default_factory=list)
    current_phase: str = "UNKNOWN"
    generated_at: str = ""
    parser_errors: list[str] = field(default_factory=list)
    # SessionStateParser 由来の補完データ（V-4 Task 状態決定ロジックで使用）
    in_progress: list[str] = field(default_factory=list)   # 進行中タスクのテキスト行
    blocked: list[str] = field(default_factory=list)       # ブロック中タスクのテキスト行
    completed: list[str] = field(default_factory=list)     # 完了タスクのテキスト行
