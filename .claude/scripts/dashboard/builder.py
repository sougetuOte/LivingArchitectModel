"""builder.py - DashboardBuilder HTML テンプレート展開（W1-B5-T2/T3, W2-B5-T9, W3-B5-T14, W3-B5-T15, W6-B5-T34, W6-B5-T33, W6-B5-T37, W6-B5-T38, W6-B5-T40, W6-B5-T41）

対応仕様: docs/specs/b4-dashboard/design.md §6「ビルドコマンド設計」
         docs/specs/b4-dashboard/design.md §8「出力形式」
         docs/specs/b4-dashboard/design.md §4「V-1: Project サマリービュー」
         docs/specs/b4-dashboard/design.md §4「V-2: Milestone 一覧ビュー」
         docs/specs/b4-dashboard/design.md §4「V-3: Wave 一覧ビュー」
         docs/specs/b4-dashboard/design.md §4「V-4: Task 一覧ビュー」
         docs/specs/b4-dashboard/wave6/design.md §5「全体アーキテクチャ」
         docs/specs/b4-dashboard/wave6/design.md §6「Radix Colors 適用設計」
         docs/specs/b4-dashboard/wave6/design.md §7「CSS 構造設計」
         docs/specs/b4-dashboard/wave6/design.md §8「アクセシビリティ実装設計」
         docs/specs/b4-dashboard/wave6/design.md §9「ソート機能設計」
         docs/specs/b4-dashboard/wave6/design.md §10「フィルタ機能設計」
         docs/specs/b4-dashboard/wave6/design.md §11「JS 行数管理」
         docs/specs/b4-dashboard/wave6/design.md §13「builder.py 改修方針」

Wave 1: V-1 Project サマリービュー実装（W1-B5-T3 完了）
Wave 2: V-2 Milestone 一覧ビュー実装（W2-B5-T9 完了）
Wave 3: V-3 Wave 一覧ビュー実装（W3-B5-T14 完了）
Wave 3: V-4 Task 一覧ビュー実装（W3-B5-T15 完了）
Wave 6: セマンティック HTML + <main> / <nav> ランドマーク追加（W6-B5-T34 完了）
Wave 6: CSS スタイリング基盤（Radix Colors Layer 1/2 + フルスタック）（W6-B5-T33 完了）
Wave 6: ソート JS 実装（_render_script() 新設）（W6-B5-T37 完了）
Wave 6: V-4 テーブルヘッダ改修（ソート UI / data-milestone 追加）（W6-B5-T38 完了）
Wave 6: フィルタ UI HTML + _render_filter_controls() 新設（W6-B5-T40 完了）
Wave 6: フィルタ JS 実装 + DOMContentLoaded 統合（W6-B5-T41 完了）
"""

from __future__ import annotations

import html

from ._radix_colors import RADIX_DARK, RADIX_LIGHT
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

    def _render_style(self) -> str:
        """CSS スタイルブロックを返す。

        Wave 6 新設（W6-B5-T33）。design.md wave6 §6/§7/§8 に準拠。

        出力セクション（design.md §7 番号体系）:
          1. Reset / base
          2. Layer 1: Radix Colors スケール転記（ライト / :root）
          3. Layer 1: Radix Colors スケール転記（ダーク / @media）
          4. Layer 2: 意味ベースエイリアス（ライト / :root 末尾）
          5. Layer 2: 意味ベースエイリアス（ダーク / @media 末尾）— no-op プレースホルダー
          6. レイアウト（body / main / nav）
          7. タイポグラフィ（h1-h3 / .task-id 等幅フォント）
          8. テーブル共通（table / th / td / hover）
          9. 状態バッジ（.badge / 4 種 data-status）
         10. フォーカス可視化（:focus-visible）
         11. ソート UI（th button.sort-btn / sorted-asc / sorted-desc）
         12. フィルタ UI（#filter-controls / .filter-control / #filter-result-count）
         13. nav / スキップリンク
         14. パーサエラー

        Returns:
            str: <style>...</style> を含む CSS ブロック文字列。
        """
        # ── Section 2: Layer 1 ライト変数を生成 ──────────────────────────
        light_vars = []
        for color in ("gray", "blue", "green", "amber"):
            for step in range(1, 13):
                light_vars.append(f"  --{color}-{step}: {RADIX_LIGHT[color][step]};")
        light_vars_css = "\n".join(light_vars)

        # ── Section 3: Layer 1 ダーク変数を生成 ──────────────────────────
        dark_vars = []
        for color in ("gray", "blue", "green", "amber"):
            for step in range(1, 13):
                dark_vars.append(f"    --{color}-{step}: {RADIX_DARK[color][step]};")
        dark_vars_css = "\n".join(dark_vars)

        return f"""<style>
/* ─── 1. Reset / base ─────────────────────────────────────────── */
*, *::before, *::after {{ box-sizing: border-box; }}
body {{ margin: 0; }}

/* ─── 2. Layer 1: Radix Colors スケール転記（ライト）─────────── */
:root {{
{light_vars_css}

/* ─── 4. Layer 2: 意味ベースエイリアス（ライト）─────────────── */
  --color-bg-page:        var(--gray-1);
  --color-bg-surface:     var(--gray-2);
  --color-bg-header:      var(--blue-3);
  --color-text-primary:   var(--gray-12);
  --color-text-secondary: var(--gray-11);
  --color-text-muted:     var(--gray-9);
  --color-border:         var(--gray-6);
  --color-border-table:   var(--gray-5);
  --color-focus-ring:     var(--blue-8);
  --color-status-completed-bg:   var(--green-4);
  --color-status-completed-text: var(--green-11);
  --color-status-progress-bg:    var(--blue-4);
  --color-status-progress-text:  var(--blue-11);
  --color-status-blocked-bg:     var(--amber-4);
  --color-status-blocked-text:   var(--amber-11);
  --color-status-notstarted-bg:  var(--gray-3);
  --color-status-notstarted-text:var(--gray-11);

  /* ソート UI */
  --color-sort-indicator:        var(--blue-9);
  --color-sort-hover:            var(--blue-2);

  /* フィルタ UI */
  --color-filter-bg:             var(--gray-2);
  --color-filter-border:         var(--gray-6);
}}

/* ─── 3. Layer 1: Radix Colors スケール転記（ダーク）──────────── */
@media (prefers-color-scheme: dark) {{
  :root {{
{dark_vars_css}
  }}
}}

/* ─── 5. Layer 2: 意味ベースエイリアス（ダーク）──────────────── */
@media (prefers-color-scheme: dark) {{
  :root {{
    --color-bg-page:        var(--gray-1);
    --color-bg-surface:     var(--gray-2);
    --color-bg-header:      var(--blue-3);
    --color-text-primary:   var(--gray-12);
    --color-text-secondary: var(--gray-11);
    --color-text-muted:     var(--gray-9);
    --color-border:         var(--gray-6);
    --color-border-table:   var(--gray-5);
    --color-focus-ring:     var(--blue-8);
    --color-status-completed-bg:   var(--green-4);
    --color-status-completed-text: var(--green-11);
    --color-status-progress-bg:    var(--blue-4);
    --color-status-progress-text:  var(--blue-11);
    --color-status-blocked-bg:     var(--amber-4);
    --color-status-blocked-text:   var(--amber-11);
    --color-status-notstarted-bg:  var(--gray-3);
    --color-status-notstarted-text:var(--gray-11);
    --color-sort-indicator:        var(--blue-9);
    --color-sort-hover:            var(--blue-2);
    --color-filter-bg:             var(--gray-2);
    --color-filter-border:         var(--gray-6);
  }}
}}

/* ─── 6. レイアウト ───────────────────────────────────────────── */
body {{
  font-family: system-ui, -apple-system, "Segoe UI", "Hiragino Sans",
               "Noto Sans JP", sans-serif;
  background-color: var(--color-bg-page);
  color: var(--color-text-primary);
}}
main {{ max-width: 1200px; margin: 0 auto; padding: 1rem 2rem; }}
nav {{ position: sticky; top: 0; background: var(--color-bg-surface); padding: 0.5rem 1rem; }}

/* ─── 7. タイポグラフィ ──────────────────────────────────────── */
h1 {{ font-size: 1.75rem; font-weight: 700; line-height: 1.3; }}
h2 {{ font-size: 1.375rem; font-weight: 600; line-height: 1.4; }}
h3 {{ font-size: 1.125rem; font-weight: 600; line-height: 1.4; }}
td.task-id, th.col-task-id {{
  font-family: ui-monospace, "SF Mono", Consolas, monospace;
}}

/* ─── 8. テーブル共通 ────────────────────────────────────────── */
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ padding: 0.5rem 0.75rem; border: 1px solid var(--color-border-table); text-align: left; }}
th {{ background-color: var(--color-bg-header); }}
tbody tr:hover {{ background-color: var(--color-bg-surface); }}

/* ─── 9. 状態バッジ ──────────────────────────────────────────── */
.badge {{ padding: 2px 8px; border-radius: 4px; font-size: 0.85em; font-weight: 600; }}
.badge[data-status="completed"]   {{ background: var(--color-status-completed-bg); color: var(--color-status-completed-text); }}
.badge[data-status="in-progress"] {{ background: var(--color-status-progress-bg);  color: var(--color-status-progress-text);  }}
.badge[data-status="blocked"]     {{ background: var(--color-status-blocked-bg);    color: var(--color-status-blocked-text);    }}
.badge[data-status="not-started"] {{ background: var(--color-status-notstarted-bg); color: var(--color-status-notstarted-text); }}

/* ─── 10. フォーカス可視化 ───────────────────────────────────── */
:focus-visible {{
  outline: 2px solid var(--color-focus-ring);
  outline-offset: 2px;
  border-radius: 2px;
}}

/* ─── 11. ソート UI ──────────────────────────────────────────── */
th button.sort-btn {{
  appearance: none;
  border: none;
  background: transparent;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
  color: var(--color-text-primary);
  width: 100%;
  text-align: left;
}}
th button.sort-btn:hover {{
  background-color: var(--color-sort-hover);
}}

/* ─── 12. フィルタ UI ────────────────────────────────────────── */
#filter-controls {{
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  padding: 0.75rem 1rem;
  background: var(--color-filter-bg);
  border: 1px solid var(--color-filter-border);
  border-radius: 4px;
  margin-bottom: 0.5rem;
}}
.filter-control {{
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}}
.filter-control label {{
  font-size: 0.85em;
  color: var(--color-text-secondary);
  font-weight: 600;
}}
.filter-control select,
.filter-control input {{
  padding: 0.35rem 0.5rem;
  border: 1px solid var(--color-filter-border);
  border-radius: 3px;
  background: var(--color-bg-page);
  color: var(--color-text-primary);
  font: inherit;
  font-size: 0.9em;
}}
.filter-reset-btn {{
  align-self: flex-end;
  padding: 0.35rem 0.75rem;
  border: 1px solid var(--color-filter-border);
  border-radius: 3px;
  background: var(--color-bg-surface);
  color: var(--color-text-primary);
  font: inherit;
  font-size: 0.9em;
  cursor: pointer;
}}
#filter-result-count {{
  font-size: 0.9em;
  color: var(--color-text-secondary);
  margin: 0 0 0.5rem 0;
}}

/* ─── 13. nav / スキップリンク ──────────────────────────────── */
nav ul {{ list-style: none; margin: 0; padding: 0; display: flex; gap: 1rem; flex-wrap: wrap; }}
nav ul li a {{ text-decoration: none; color: var(--color-text-primary); }}
.skip-link {{
  position: absolute;
  left: -9999px;
  top: auto;
  width: 1px;
  height: 1px;
  overflow: hidden;
}}
.skip-link:focus {{
  position: static;
  width: auto;
  height: auto;
}}

/* ─── 14. パーサエラー ───────────────────────────────────────── */
#parser-errors {{
  border-left: 3px solid var(--amber-9);
  padding: 0.75rem 1rem;
  background: var(--color-bg-surface);
}}
</style>"""

    def _render_script(self) -> str:
        """JavaScript ブロックを返す（ソート機能 + フィルタ機能 / Stage 2 + Stage 3）。

        Wave 6 新設（W6-B5-T37）。Stage 3 拡張（W6-B5-T41）。
        design.md wave6 §9 / §10 / §11 に準拠。

        含まれる関数:
          - sortTable(tableId, columnIndex): テーブルソート（DOM 再挿入方式）
          - initSortButtons(): .sort-btn 全件に click listener を追加
          - applyFilters(): 状態/Milestone/テキスト AND 結合フィルタ + aria-live 件数更新
          - resetFilters(): 3 フィルタを初期値にリセットして applyFilters() を呼ぶ
          - initFilters(): フィルタ要素に input/change listener + リセットボタン listener を登録

        単一 DOMContentLoaded（C-NEW-2 対応）:
          initSortButtons() → initFilters() → applyFilters() の順序で実行。
          initFilters() 登録後に applyFilters() を呼ぶことで初期件数が確実に表示される。

        ソート状態保持:
          data-sort-col / data-sort-dir を <table> 要素自身に保持（design.md §9）。
          初回クリック: null → asc、asc → desc、desc → asc（3 回目で asc に戻る）。

        STATUS_ORDER: 状態列の固定優先順位（not-started=0, in-progress=1, blocked=2, completed=3）。
          未知 status 値は 99 にフォールバックして末尾に集約（design.md §9 W-NEW-5 対応）。

        フィルタロジック（design.md §10）:
          row.style.display = match ? '' : 'none' 方式（A3-4 CASPAR 採用）。
          件数表示: display !== 'none' の行数を filter-result-count に "{n} 件表示" で更新。
          ソート×フィルタ併用: display 切替のみでソート順序を維持（design.md §10）。

        Returns:
            str: <script>...</script> タグ全体の文字列。
        """
        return """<script>
const STATUS_ORDER = {'not-started': 0, 'in-progress': 1, 'blocked': 2, 'completed': 3};
const COL_TASK_ID = 0;
const COL_ASSIGNEE = 1;
const COL_STATUS = 2;

function sortTable(tableId, columnIndex) {
  const table = document.getElementById(tableId);
  if (!table) return;
  const tbody = table.tBodies[0];
  const rows = Array.from(tbody.rows);

  const prevCol = table.dataset.sortCol;
  const prevDir = table.dataset.sortDir;

  let dir;
  if (prevCol === String(columnIndex)) {
    dir = prevDir === 'asc' ? 'desc' : 'asc';
  } else {
    dir = 'asc';
  }

  rows.sort((a, b) => {
    if (columnIndex === COL_STATUS) {
      const va = a.cells[COL_STATUS].querySelector('.badge').dataset.status;
      const vb = b.cells[COL_STATUS].querySelector('.badge').dataset.status;
      const oa = STATUS_ORDER[va] ?? 99;
      const ob = STATUS_ORDER[vb] ?? 99;
      const diff = oa - ob;
      return dir === 'asc' ? diff : -diff;
    }
    const va = a.cells[columnIndex].textContent.trim();
    const vb = b.cells[columnIndex].textContent.trim();
    return dir === 'asc' ? va.localeCompare(vb, 'ja') : vb.localeCompare(va, 'ja');
  });

  tbody.append(...rows);

  table.dataset.sortCol = String(columnIndex);
  table.dataset.sortDir = dir;

  const ths = table.querySelectorAll('th[aria-sort]');
  const colNames = ['Task ID', '担当', '状態'];
  ths.forEach((th, idx) => {
    if (idx === columnIndex) {
      th.setAttribute('aria-sort', dir === 'asc' ? 'ascending' : 'descending');
      const btn = th.querySelector('.sort-btn');
      if (btn) {
        const opposite = dir === 'asc' ? '降順' : '昇順';
        btn.setAttribute('aria-label', colNames[idx] + 'で' + opposite + 'にソート');
      }
    } else {
      th.setAttribute('aria-sort', 'none');
      const btn = th.querySelector('.sort-btn');
      if (btn) {
        btn.setAttribute('aria-label', colNames[idx] + 'で昇順にソート');
      }
    }
  });
}

function initSortButtons() {
  document.querySelectorAll('.sort-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const col = parseInt(btn.dataset.col, 10);
      sortTable('tasks-table', col);
    });
  });
}

function applyFilters() {
  const statusFilter = document.getElementById('filter-status').value;
  const msFilter = document.getElementById('filter-milestone').value;
  const textFilter = document.getElementById('filter-text').value.trim().toLowerCase();

  const table = document.getElementById('tasks-table');
  if (!table) return;
  const rows = Array.from(table.tBodies[0].rows);

  rows.forEach(row => {
    const badge = row.cells[COL_STATUS].querySelector('.badge');
    const status = badge ? badge.dataset.status : '';
    const ms = row.dataset.milestone || '';
    const taskId = row.cells[COL_TASK_ID].textContent.toLowerCase();
    const assignee = row.cells[COL_ASSIGNEE].textContent.toLowerCase();

    const match = (statusFilter === '' || status === statusFilter)
               && (msFilter === '' || ms === msFilter)
               && (textFilter === '' || taskId.includes(textFilter) || assignee.includes(textFilter));

    row.style.display = match ? '' : 'none';
  });

  const count = rows.filter(r => r.style.display !== 'none').length;
  const countEl = document.getElementById('filter-result-count');
  if (countEl) {
    countEl.textContent = count + ' 件表示';
  }
}

function resetFilters() {
  const statusEl = document.getElementById('filter-status');
  const msEl = document.getElementById('filter-milestone');
  const textEl = document.getElementById('filter-text');
  if (statusEl) statusEl.value = '';
  if (msEl) msEl.value = '';
  if (textEl) textEl.value = '';
  applyFilters();
}

function initFilters() {
  const statusEl = document.getElementById('filter-status');
  const msEl = document.getElementById('filter-milestone');
  const textEl = document.getElementById('filter-text');
  const resetBtn = document.getElementById('filter-reset');

  if (statusEl) statusEl.addEventListener('change', applyFilters);
  if (msEl) msEl.addEventListener('change', applyFilters);
  if (textEl) textEl.addEventListener('input', applyFilters);
  if (resetBtn) resetBtn.addEventListener('click', resetFilters);
}

document.addEventListener('DOMContentLoaded', () => {
  initSortButtons();
  initFilters();
  applyFilters();
});
</script>"""

    def render(self) -> str:
        """DashboardData を HTML 文字列に変換する。

        Wave 6 改修（W6-B5-T34）: セマンティック HTML 構造に改修済み。
        Wave 6 改修（W6-B5-T33）: _render_style() で CSS スタイリング基盤を注入。
        Wave 6 改修（W6-B5-T37）: _render_script() で JS ブロックを </body> 直前に配置。
        - <nav id="nav-landmarks"> ランドマークナビを <body> 直下に追加
        - <main id="main-content"> で V-1〜V-4 セクションを包含
        - <section id="parser-errors"> は <main> の外側に配置（既存位置維持）
        - <script> は </body> 直前（design.md wave6 §3 A3-5 確定）
        design.md wave6 §5 構造図 / §7 CSS 構造設計 / §8 セマンティック HTML 実装 に準拠。

        Returns:
            str: 完全な HTML ドキュメント文字列。
        """
        style_html = self._render_style()
        script_html = self._render_script()
        nav_html = self._render_nav()
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
  {style_html}
</head>
<body>
  {nav_html}
  <main id="main-content">
    {v1_html}

    {v2_html}

    {v3_html}

    {v4_html}
  </main>

  {parser_errors_html}
  {script_html}
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
        Wave 6 改修（W6-B5-T38）: ソート UI 追加・data-milestone 属性追加。
        Wave 6 改修（W6-B5-T40）: フィルタ UI を section 先頭に内部呼び出し（W-NEW-6 責務集約）。
                                   filter-result-count 要素を追加（T40 完了条件）。

        - Task が 0 件: empty state（「Task 情報なし」表示）
        - 1 件以上: フィルタ UI + 件数表示 + テーブル（id="tasks-table" / thead 3 列 + tbody 各行）
        - 各列ヘッダ: aria-sort="none" + <button class="sort-btn" data-col="N"> を内包
        - 各行: data-task-id に加え data-milestone="{task.milestone}" を追加（Stage 3 フィルタ用）
        - 各行の状態は _resolve_task_status() で決定（design.md §5 優先順位）
        - アンカー: <section id="v4-tasks">

        フィルタ UI は _render_filter_controls() を呼び出して section 先頭に挿入。
        filter-result-count はフィルタ UI の直後に配置。applyFilters() が件数更新を担当。
        """
        filter_controls_html = self._render_filter_controls()

        if not self.data.tasks:
            return (
                '<section id="v4-tasks">\n'
                "  <h2>Task 一覧</h2>\n"
                f"  {filter_controls_html}\n"
                '  <p id="filter-result-count" aria-live="polite"></p>\n'
                "  <p>Task 情報なし</p>\n"
                "</section>"
            )

        rows = []
        for task in self.data.tasks:
            status = self._resolve_task_status(task.id, task.status)
            badge_html = self._render_status_badge(status)
            escaped_id = html.escape(task.id)
            escaped_assignee = html.escape(task.assignee)
            escaped_milestone = html.escape(task.milestone)
            rows.append(
                f'      <tr data-task-id="{escaped_id}" data-milestone="{escaped_milestone}">\n'
                f"        <td>{escaped_id}</td>\n"
                f"        <td>{escaped_assignee}</td>\n"
                f"        <td>{badge_html}</td>\n"
                "      </tr>"
            )

        tbody_rows = "\n".join(rows)
        return (
            '<section id="v4-tasks">\n'
            "  <h2>Task 一覧</h2>\n"
            f"  {filter_controls_html}\n"
            '  <p id="filter-result-count" aria-live="polite"></p>\n'
            '  <table id="tasks-table">\n'
            "    <thead>\n"
            "      <tr>\n"
            '        <th id="th-task-id" aria-sort="none">\n'
            '          <button class="sort-btn" data-col="0" aria-label="Task IDで昇順にソート">Task ID</button>\n'
            "        </th>\n"
            '        <th id="th-assignee" aria-sort="none">\n'
            '          <button class="sort-btn" data-col="1" aria-label="担当で昇順にソート">担当</button>\n'
            "        </th>\n"
            '        <th id="th-status" aria-sort="none">\n'
            '          <button class="sort-btn" data-col="2" aria-label="状態で昇順にソート">状態</button>\n'
            "        </th>\n"
            "      </tr>\n"
            "    </thead>\n"
            "    <tbody>\n"
            f"{tbody_rows}\n"
            "    </tbody>\n"
            "  </table>\n"
            "</section>"
        )

    def _render_filter_controls(self) -> str:
        """フィルタ UI コンテナ HTML を返す（W6-B5-T40）。

        design.md wave6 §10「フィルタ機能設計」DOM 構造に準拠。
        _render_v4_tasks() から内部呼び出しされる（W-NEW-6 責務集約）。

        出力構造:
          <div id="filter-controls" role="search" aria-label="タスクフィルタ">
            <div class="filter-control">
              <label for="filter-status">状態</label>
              <select id="filter-status" aria-controls="tasks-table">
                <option value="">すべて</option>
                <option value="not-started">未着手</option>
                <option value="in-progress">進行中</option>
                <option value="blocked">ブロック中</option>
                <option value="completed">完了</option>
              </select>
            </div>
            <div class="filter-control">
              <label for="filter-milestone">Milestone</label>
              <select id="filter-milestone" aria-controls="tasks-table">
                <option value="">すべて</option>
                {DashboardData.milestones から動的生成}
              </select>
            </div>
            <div class="filter-control">
              <label for="filter-text">テキスト検索</label>
              <input type="search" id="filter-text" ...>
            </div>
            <button type="button" id="filter-reset" class="filter-reset-btn">
              フィルタをクリア
            </button>
          </div>

        Milestone select 動的生成（design.md §10）:
          self.data.milestones が空リストの場合は「すべて」のみ（実質無効化）。
          各 MilestoneInfo の name フィールドを <option value="{name}">{name}</option> に変換。
          html.escape() で XSS 対策（既存パターン継承）。

        Returns:
            str: <div id="filter-controls"> HTML 文字列。
        """
        milestone_options = "\n".join(
            f'      <option value="{html.escape(ms.name)}">{html.escape(ms.name)}</option>'
            for ms in self.data.milestones
        )
        milestone_options_block = f"\n{milestone_options}" if milestone_options else ""

        return (
            '<div id="filter-controls" role="search" aria-label="タスクフィルタ">\n'
            '  <div class="filter-control">\n'
            '    <label for="filter-status">状態</label>\n'
            '    <select id="filter-status" aria-controls="tasks-table">\n'
            '      <option value="">すべて</option>\n'
            '      <option value="not-started">未着手</option>\n'
            '      <option value="in-progress">進行中</option>\n'
            '      <option value="blocked">ブロック中</option>\n'
            '      <option value="completed">完了</option>\n'
            "    </select>\n"
            "  </div>\n"
            '  <div class="filter-control">\n'
            '    <label for="filter-milestone">Milestone</label>\n'
            '    <select id="filter-milestone" aria-controls="tasks-table">\n'
            '      <option value="">すべて</option>'
            f"{milestone_options_block}\n"
            "    </select>\n"
            "  </div>\n"
            '  <div class="filter-control">\n'
            '    <label for="filter-text">テキスト検索</label>\n'
            '    <input type="search" id="filter-text" placeholder="Task ID / 担当..."\n'
            '           aria-controls="tasks-table" aria-label="Task IDまたは担当で検索">\n'
            "  </div>\n"
            '  <button type="button" id="filter-reset" class="filter-reset-btn">\n'
            "    フィルタをクリア\n"
            "  </button>\n"
            "</div>"
        )

    def _render_nav(self) -> str:
        """ページ内ナビゲーション <nav> ランドマークの HTML を返す。

        Wave 6 新設（W6-B5-T34）。design.md wave6 §5 構造図 / §8 セマンティック HTML に準拠。

        出力構造:
          <nav id="nav-landmarks">
            <a href="#main-content" class="skip-link">メインコンテンツへスキップ</a>
            <ul>
              <li><a href="#v1-project-summary">Project サマリー</a></li>
              <li><a href="#v2-milestones">Milestone 一覧</a></li>
              {V-3 リンク（Milestone 数だけ動的生成）}
              <li><a href="#v4-tasks">Task 一覧</a></li>
            </ul>
          </nav>

        V-3 リンクは self.data.milestones を反復して動的生成する。
        milestones が空の場合は V-3 リンクなし（空文字列を join）。
        html.escape() で XSS 対策（既存パターン継承）。

        Returns:
            str: <nav> ランドマーク HTML 文字列。
        """
        v3_links = "\n".join(
            f'      <li><a href="#v3-waves-{html.escape(ms.name)}">Wave 一覧（{html.escape(ms.name)}）</a></li>'
            for ms in self.data.milestones
        )
        v3_block = f"\n{v3_links}" if v3_links else ""
        return (
            '<nav id="nav-landmarks">\n'
            '  <a href="#main-content" class="skip-link">メインコンテンツへスキップ</a>\n'
            "  <ul>\n"
            '    <li><a href="#v1-project-summary">Project サマリー</a></li>\n'
            '    <li><a href="#v2-milestones">Milestone 一覧</a></li>'
            f"{v3_block}\n"
            '    <li><a href="#v4-tasks">Task 一覧</a></li>\n'
            "  </ul>\n"
            "</nav>"
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
