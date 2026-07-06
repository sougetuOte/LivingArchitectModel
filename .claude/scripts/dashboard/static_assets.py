"""static_assets.py - CSS/JS 静的合成ロジック（R1-003 第一歩）

対応 issue: docs/artifacts/r-1-audit-tracker.md #R1-003
  「DashboardBuilder が God Class 傾向（921 行 / 15 メソッド）」の第一歩として、
  builder.py の CSS/JS 静的合成部分（_render_style / _render_script）を
  モジュールレベル関数として切出したもの。

  ロジックは builder.py から一切改変せずそのまま移動している
  （文字列・整形・変数名を含め byte-identical な出力を維持すること）。

  ビュー分割（V1-V4）はスコープ外（W-R5 retro 議題）。本モジュールは
  CSS/JS 合成のみを扱う。
"""

from __future__ import annotations

from ._radix_colors import RADIX_DARK, RADIX_LIGHT


def render_style() -> str:
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
     15. Milestone カード (Wave 7 T52 / V-2 セクション化 / design.md §8)

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
  --color-status-unknown-bg:     #9ca3af;
  --color-status-unknown-text:   var(--gray-12);

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
    --color-status-unknown-bg:     #9ca3af;
    --color-status-unknown-text:   var(--gray-12);
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
.badge[data-status="unknown"]     {{ background: var(--color-status-unknown-bg);     color: var(--color-status-unknown-text);     }}

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

/* ─── 15. Milestone カード (V-2) ─────────────────────────────── */
.milestones-container {{
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}}
.milestone-card {{
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 0.75rem 1rem;
  background: var(--color-bg-surface);
}}
.milestone-card h3 {{
  margin: 0 0 0.25rem 0;
  font-size: 1.1rem;
  color: var(--color-text-primary);
}}
</style>"""


def render_script() -> str:
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
