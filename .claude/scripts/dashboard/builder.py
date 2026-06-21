"""builder.py - DashboardBuilder HTML テンプレート展開（W1-B5-T2/T3, W2-B5-T9, W3-B5-T14, W3-B5-T15）

対応仕様: docs/specs/b4-dashboard/design.md §6「ビルドコマンド設計」
         docs/specs/b4-dashboard/design.md §8「出力形式」
         docs/specs/b4-dashboard/design.md §4「V-1: Project サマリービュー」
         docs/specs/b4-dashboard/design.md §4「V-2: Milestone 一覧ビュー」
         docs/specs/b4-dashboard/design.md §4「V-3: Wave 一覧ビュー」
         docs/specs/b4-dashboard/design.md §4「V-4: Task 一覧ビュー」

Wave 1: V-1 Project サマリービュー実装（W1-B5-T3 完了）
Wave 2: V-2 Milestone 一覧ビュー実装（W2-B5-T9 完了）
Wave 3: V-3 Wave 一覧ビュー実装（W3-B5-T14 完了）
Wave 3: V-4 Task 一覧ビュー実装（W3-B5-T15 完了）
<head> 内の inline CSS は W1-B5-T4 で追加済み（外部 CDN 参照なし・500KB 未満）。
"""

from __future__ import annotations

import html

from .models import DashboardData


class DashboardBuilder:
    """パーサ結果を受け取り、単一 HTML ファイルを生成するビルダー。

    Args:
        data: 全パーサの結果を統合した DashboardData オブジェクト。

    使用例::

        builder = DashboardBuilder(data)
        html = builder.render()
        output_path.write_text(html, encoding="utf-8")

    T4 完了済み:
        <head> 内の <style> タグに design.md §8 の badge CSS を埋め込み済み（W1-B5-T4）。
        外部 CDN 参照なし・500KB 未満を担保している。

    Wave 3 完了:
        V-3 Wave 一覧は _render_v3_waves() / _render_v3_milestone_section() で実装済み（W3-B5-T14）。
        V-4 Task 一覧は _render_v4_tasks() / _resolve_task_status() で実装済み（W3-B5-T15）。
    """

    def __init__(self, data: DashboardData) -> None:
        self.data = data

    def render(self) -> str:
        """DashboardData を HTML 文字列に変換する。

        Returns:
            str: 完全な HTML ドキュメント文字列。
        """
        v1_html = self._render_v1_project_summary()
        v2_html = self._render_v2_milestones()
        v3_html = self._render_v3_waves()
        v4_html = self._render_v4_tasks()
        parser_errors_html = self._render_parser_errors()

        return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LAM Dashboard</title>
  <style>
    /* --- inline CSS（最小限）--- */
    /* 配色・レイアウト詳細は PoC 後の UI フェーズで決める（design.md §8 非スコープ） */
    .badge[data-status="completed"]   {{ background: #28a745; color: #fff; }}
    .badge[data-status="in-progress"] {{ background: #007bff; color: #fff; }}
    .badge[data-status="blocked"]     {{ background: #dc3545; color: #fff; }}
    .badge[data-status="not-started"] {{ background: #6c757d; color: #fff; }}
    .badge {{ padding: 2px 8px; border-radius: 4px; font-size: 0.85em; }}
  </style>
</head>
<body>
  {v1_html}

  {v2_html}

  {v3_html}

  {v4_html}

  {parser_errors_html}
</body>
</html>"""

    def _render_v1_project_summary(self) -> str:
        """V-1 Project サマリービューの HTML を返す。

        design.md §4「V-1: Project サマリービュー」DOM 構成案に準拠。
        Project 名は "LAM" にハードコード（design.md §4 の表示ロジック: 固定文字列）。
        最終更新日時は DashboardData.generated_at から取得する。
        """
        generated_at = self.data.generated_at or ""
        return (
            '<section id="v1-project-summary">\n'
            "  <h1>LAM Dashboard</h1>\n"
            "  <dl>\n"
            "    <dt>Project</dt><dd>LAM（Living Architect Model）</dd>\n"
            f"    <dt>最終更新</dt><dd>{generated_at}</dd>\n"
            "  </dl>\n"
            "</section>"
        )

    # ─────────────────────────────────────────────
    # 状態バッジ日本語ラベル（設計判断: design.md §4 V-2 + 実装方針 L1）
    # ─────────────────────────────────────────────
    _STATUS_LABELS: dict[str, str] = {
        "completed": "完了",
        "in-progress": "進行中",
        "blocked": "ブロック中",
        "not-started": "未着手",
    }

    def _render_status_badge(self, status: str) -> str:
        """状態値を <span class="badge" data-status="..."> 形式の HTML に変換する。

        design.md §4 V-2 DOM 構成案準拠。
        未知の状態値はそのままラベルとして表示する。
        """
        label = self._STATUS_LABELS.get(status, status)
        return f'<span class="badge" data-status="{status}">{label}</span>'

    def _render_v2_milestones(self) -> str:
        """V-2 Milestone 一覧ビューの HTML を返す。

        design.md §4「V-2: Milestone 一覧ビュー」DOM 構成案に準拠。

        - Milestone が 0 件: empty state（「Milestone 情報なし」表示）
        - 1 件以上: テーブル（thead 3 列 + tbody 各行）
        - 各行の Step 列は self.data.current_phase を使用（全 Milestone 共通）
        - アンカーリンク: <a href="#v3-waves-{name}">{name}</a>
        """
        current_phase = self.data.current_phase

        if not self.data.milestones:
            return (
                '<section id="v2-milestones">\n'
                "  <h2>Milestone 一覧</h2>\n"
                "  <p>Milestone 情報なし</p>\n"
                "</section>"
            )

        rows = []
        for ms in self.data.milestones:
            badge_html = self._render_status_badge(ms.status)
            rows.append(
                f'      <tr data-milestone="{ms.name}">\n'
                f'        <td><a href="#v3-waves-{ms.name}">{ms.name}</a></td>\n'
                f"        <td>{current_phase}</td>\n"
                f"        <td>{badge_html}</td>\n"
                "      </tr>"
            )

        tbody_rows = "\n".join(rows)
        return (
            '<section id="v2-milestones">\n'
            "  <h2>Milestone 一覧</h2>\n"
            "  <table>\n"
            "    <thead>\n"
            "      <tr><th>Milestone</th><th>現在の Step</th><th>状態</th></tr>\n"
            "    </thead>\n"
            "    <tbody>\n"
            f"{tbody_rows}\n"
            "    </tbody>\n"
            "  </table>\n"
            "</section>"
        )

    def _render_v3_waves(self) -> str:
        """V-3 Wave 一覧ビューの HTML を返す。

        design.md §4「V-3: Wave 一覧ビュー」DOM 構成案に準拠。

        - Wave が 0 件: 空文字列（セクション自体を生成しない）
        - 1 件以上: Milestone ごとにセクションを生成
          - <section id="v3-waves-{milestone}">
          - <h2>Wave 一覧（{milestone}）</h2>
          - テーブル: Wave 番号 / Task 数 / 状態 の 3 列
          - <a href="#v4-tasks"> ナビゲーションリンク（design.md §4 V-3→V-4）
        - 各行: <tr data-wave="{wave_number}">
        - 状態: _render_status_badge() で共通バッジ生成
        """
        if not self.data.waves:
            return ""

        # Milestone ごとに Wave をグループ化（出現順を維持）
        milestone_order: list[str] = []
        waves_by_milestone: dict[str, list] = {}
        for wave in self.data.waves:
            ms = wave.milestone
            if ms not in waves_by_milestone:
                milestone_order.append(ms)
                waves_by_milestone[ms] = []
            waves_by_milestone[ms].append(wave)

        sections: list[str] = []
        for milestone_name in milestone_order:
            milestone_waves = waves_by_milestone[milestone_name]
            section_html = self._render_v3_milestone_section(milestone_name, milestone_waves)
            sections.append(section_html)

        return "\n\n  ".join(sections)

    def _render_v3_milestone_section(self, milestone_name: str, waves: list) -> str:
        """1 つの Milestone 分の V-3 セクション HTML を返す。

        design.md §4 V-3 DOM 構成案:
          <section id="v3-waves-{milestone}">
            <h2>Wave 一覧（{milestone}）</h2>
            <table>...</table>
            <p><a href="#v4-tasks">Task 一覧を見る</a></p>
          </section>
        """
        escaped_ms = html.escape(milestone_name)
        rows = []
        for wave in waves:
            badge_html = self._render_status_badge(wave.status)
            rows.append(
                f'      <tr data-wave="{html.escape(wave.wave_number)}">\n'
                f"        <td>Wave {html.escape(wave.wave_number)}</td>\n"
                f"        <td>{wave.task_count}</td>\n"
                f"        <td>{badge_html}</td>\n"
                "      </tr>"
            )

        tbody_rows = "\n".join(rows)
        return (
            f'<section id="v3-waves-{escaped_ms}">\n'
            f"  <h2>Wave 一覧（{escaped_ms}）</h2>\n"
            "  <table>\n"
            "    <thead>\n"
            "      <tr><th>Wave</th><th>Task 数</th><th>状態</th></tr>\n"
            "    </thead>\n"
            "    <tbody>\n"
            f"{tbody_rows}\n"
            "    </tbody>\n"
            "  </table>\n"
            '  <p><a href="#v4-tasks">Task 一覧を見る</a></p>\n'
            "</section>"
        )

    def _resolve_task_status(self, task_id: str, base_status: str) -> str:
        """design.md §5 Task 状態決定ロジックに従い、最終的な状態を返す。

        優先順位:
          1. DashboardData.completed の行に task_id が含まれる → "completed"
          2. DashboardData.in_progress の行に task_id が含まれる → "in-progress"
          3. DashboardData.blocked の行に task_id が含まれる → "blocked"
          4. base_status（TasksParser の [x]/[ ] チェックから決定済み）を使用
          5. 上記いずれにも該当しない場合は "not-started"

        Args:
            task_id: Task の識別子。例: "W1-B5-T1"
            base_status: TasksParser が返した初期状態。"completed" または "not-started"。

        Returns:
            最終的な状態値（4 値のいずれか）。
        """
        for line in self.data.completed:
            if task_id in line:
                return "completed"
        for line in self.data.in_progress:
            if task_id in line:
                return "in-progress"
        for line in self.data.blocked:
            if task_id in line:
                return "blocked"
        return base_status

    def _render_v4_tasks(self) -> str:
        """V-4 Task 一覧ビューの HTML を返す。

        design.md §4「V-4: Task 一覧ビュー」DOM 構成案に準拠。

        - Task が 0 件: empty state（「Task 情報なし」表示）
        - 1 件以上: テーブル（thead 3 列 + tbody 各行）
        - 各行の状態は _resolve_task_status() で決定（design.md §5 優先順位）
        - アンカー: <section id="v4-tasks">
        """
        if not self.data.tasks:
            return (
                '<section id="v4-tasks">\n'
                "  <h2>Task 一覧</h2>\n"
                "  <p>Task 情報なし</p>\n"
                "</section>"
            )

        rows = []
        for task in self.data.tasks:
            status = self._resolve_task_status(task.id, task.status)
            badge_html = self._render_status_badge(status)
            escaped_id = html.escape(task.id)
            escaped_assignee = html.escape(task.assignee)
            rows.append(
                f'      <tr data-task-id="{escaped_id}">\n'
                f"        <td>{escaped_id}</td>\n"
                f"        <td>{escaped_assignee}</td>\n"
                f"        <td>{badge_html}</td>\n"
                "      </tr>"
            )

        tbody_rows = "\n".join(rows)
        return (
            '<section id="v4-tasks">\n'
            "  <h2>Task 一覧</h2>\n"
            "  <table>\n"
            "    <thead>\n"
            "      <tr><th>Task ID</th><th>担当</th><th>状態</th></tr>\n"
            "    </thead>\n"
            "    <tbody>\n"
            f"{tbody_rows}\n"
            "    </tbody>\n"
            "  </table>\n"
            "</section>"
        )

    def _render_parser_errors(self) -> str:
        """parser_errors がある場合のエラーサマリー HTML を返す。

        エラーがない場合は空文字列を返す。
        """
        if not self.data.parser_errors:
            return ""

        error_items = "\n".join(
            f"    <li>{html.escape(error)}</li>" for error in self.data.parser_errors
        )
        return (
            '<section id="parser-errors">\n'
            '  <h2>データ取得エラー</h2>\n'
            '  <p>一部のデータが取得できませんでした。以下の情報をご確認ください。</p>\n'
            f"  <ul>\n{error_items}\n  </ul>\n"
            "</section>"
        )
