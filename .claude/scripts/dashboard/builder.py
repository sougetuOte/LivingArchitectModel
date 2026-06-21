"""builder.py - DashboardBuilder HTML テンプレート展開（W1-B5-T2/T3, W2-B5-T9）

対応仕様: docs/specs/b4-dashboard/design.md §6「ビルドコマンド設計」
         docs/specs/b4-dashboard/design.md §8「出力形式」
         docs/specs/b4-dashboard/design.md §4「V-1: Project サマリービュー」
         docs/specs/b4-dashboard/design.md §4「V-2: Milestone 一覧ビュー」

Wave 1: V-1 Project サマリービュー実装（W1-B5-T3 完了）
Wave 2: V-2 Milestone 一覧ビュー実装（W2-B5-T9 完了）
<head> 内の inline CSS は W1-B5-T4 で追加済み（外部 CDN 参照なし・500KB 未満）。
V-3〜V-4 は Wave 3 で実装する（<body> 内の TODO コメントを参照）。
"""

from __future__ import annotations

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

    V-3〜V-4 用注記:
        <body> 内の ``<!-- TODO: V-3〜V-4 -->`` コメント箇所に
        各ビューの _render_v3_*() / _render_v4_*() を追加すること
        （Wave 3 担当）。
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

  <!-- TODO: V-3〜V-4（Wave 3 で実装）-->

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

    def _render_parser_errors(self) -> str:
        """parser_errors がある場合のエラーサマリー HTML を返す。

        エラーがない場合は空文字列を返す。
        """
        if not self.data.parser_errors:
            return ""

        error_items = "\n".join(
            f"    <li>{error}</li>" for error in self.data.parser_errors
        )
        return (
            '<section id="parser-errors">\n'
            '  <h2>データ取得エラー</h2>\n'
            '  <p>一部のデータが取得できませんでした。以下の情報をご確認ください。</p>\n'
            f"  <ul>\n{error_items}\n  </ul>\n"
            "</section>"
        )
