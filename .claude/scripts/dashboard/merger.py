"""merger.py - MilestoneSourceMerger 実装（W8-B5-T101）

対応仕様:
  - docs/specs/b4-dashboard/wave8/requirements.md FR-W8-1 / FR-W8-5 / FR-W8-6
  - docs/specs/b4-dashboard/wave8/design.md §4「MilestoneSourceMerger 詳細設計」
  - docs/specs/b4-dashboard/wave8/design.md §10「Registry 昇格契約」

責務:
  SessionStateParser 由来の Milestone 集合（list[MilestoneInfo]）と
  TasksParser 由来の Milestone 名集合（list[str]）を集合演算（和集合）で統合し、
  build_dashboard.py が DashboardData.milestones に直接代入できる単一の SSOT を提供する。

パーサ独立性原則（design.md §3）を維持するため、Merger は各パーサの結果を
受け取るのみで、パーサそのものやファイルシステムには依存しない（read-only 集約レイヤ）。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from dashboard.models import MilestoneInfo


@runtime_checkable
class MilestoneProvider(Protocol):
    """Milestone 一覧を提供するコンポーネントの契約（将来 Registry 差し替え用）。

    MilestoneSourceMerger（Wave 8）も将来の MilestoneRegistry（⑥ A 設計時）も
    このプロトコルを実装することで、build_dashboard.py の変更なしに差し替え可能にする
    （design.md §10 Registry 昇格契約 / FR-W8-5 MUST）。
    """

    def get_milestones(self) -> list[MilestoneInfo]:
        """統合済みの Milestone リストを返す。"""
        ...


class MilestoneSourceMerger:
    """SessionState 由来と tasks.md 由来の Milestone 集合を統合する集約レイヤ。

    MilestoneProvider Protocol を実装する（FR-W8-5 MUST）。

    Args:
        session_milestones: SessionStateParser.parse()["data"]["milestones"] 由来。
            ok=False 時は呼び出し側（build_dashboard.py）が空リストに正規化して渡す
            責務を持つ（I-W-6 / Merger は None を受け取らない）。
        task_milestone_names: TasksParser.parse()["data"]["tasks"] の milestone
            フィールドを集合化した名前リスト。同様に ok=False 時は空リストを渡す。
    """

    def __init__(
        self,
        session_milestones: list[MilestoneInfo],
        task_milestone_names: list[str],
    ) -> None:
        self._session_milestones = session_milestones
        self._task_milestone_names = task_milestone_names

    def get_milestones(self) -> list[MilestoneInfo]:
        """MilestoneProvider Protocol 実装。統合後 Milestone リストを返す（MUST）。"""
        return self._merge()

    def _merge(self) -> list[MilestoneInfo]:
        """内部統合ロジック（design.md §4 アルゴリズム）。

        1. session_milestones を dict[name -> MilestoneInfo] に変換（重複排除・後勝ち）
        2. task_milestone_names を走査し、session dict に存在しない name を補完追加
        3. 全エントリを name 昇順ソートして返す

        エラー耐障害性（FR-W8-6 MUST）:
          - 片方が空リストでも継続する
          - 両方が空なら空リストを返す
        """
        session_dict: dict[str, MilestoneInfo] = {
            ms.name: ms for ms in self._session_milestones
        }

        for name in self._task_milestone_names:
            if name not in session_dict:
                session_dict[name] = self._make_milestone_from_name(name)

        return sorted(session_dict.values(), key=lambda ms: ms.name)

    def _make_milestone_from_name(self, name: str) -> MilestoneInfo:
        """tasks.md 由来のみのエントリを補完生成する。

        status="unknown": SESSION_STATE.md は gitignore 対象かつセッション切替で
        変動する揮発的ファイルであるため、「記録なし = 未着手」とは限らない。
        完了済み Milestone が誤って "not-started" 表示されるリスクを回避するため、
        中立な "unknown" を補完値とする（design.md §4 重複排除ルール / I-W-2）。
        """
        return MilestoneInfo(name=name, current_step="UNKNOWN", status="unknown")
