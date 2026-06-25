---
name: project_b5_w6_stage2_sort
description: B-5 Wave 6 Stage 2 ソート機能実装（T37+T38+T39）の知見・実装パターン・注意点
metadata:
  type: project
---

## 実装完了（2026-06-26）

T37: `_render_script()` 新設、T38: `_render_v4_tasks()` 改修、T39: テスト 8 件（`test_wave6_stage2_sort.py`）

## 既存 assert 緩和が必要だった箇所（SE 級）

`<th>Task ID</th>` を直接 assert するテストが 2 か所あり、`<button>` 内包後に FAIL する:
- `test_v4_view.py:107-109`: `_render_v4_tasks()` のヘッダ直書き assert → 文字列包含チェックに緩和
- `test_wave3_integration.py:308`: 同上

**Why:** V-4 ヘッダに `<button class="sort-btn">` を内包すると `<th>Task ID</th>` が `<th aria-sort="none"><button>Task ID</button></th>` になるため直書き assert が FAIL する。

**How to apply:** V-4 テーブルヘッダ構造変更を行う場合は、同様の直書き assert 緩和が必要。grep パターン: `<th>Task ID</th>|<th>担当</th>|<th>状態</th>` を `.claude/tests/dashboard/` で確認する。

## _render_script() の JS 行数

コメント・空行除く実質 JS: 約 41 行（design.md §11 目標 40-55 行を充足）。
Stage 3 で initFilters / applyFilters / resetFilters を追加した後に 100-150 行になる予定。

## ソート状態保持の実装パターン

`table.dataset.sortCol` / `table.dataset.sortDir` を `<table>` 要素自身に保持（data 属性）。
初回クリック時は `prevCol` が `null` → `null === String(columnIndex)` が false → `dir = 'asc'`。
同列 2 回目: `prevDir === 'asc'` → `dir = 'desc'`。3 回目: `dir = 'asc'` に戻る。

## STATUS_ORDER フォールバック（design.md §9 W-NEW-5）

`STATUS_ORDER[va] ?? 99` で未知 status 値を末尾（昇順時）に集約。
`undefined ?? 99` が機能する（Nullish coalescing）。NaN での sort 挙動不定を回避。

## render() への script_html 配置

design.md §3 A3-5 に従い `</body>` 直前（`{parser_errors_html}` の後）に配置。
inline script に `defer` は無効（MDN 仕様）のため `<head>` に置かない。

## テストフィクスチャのパターン

T-S2-7 など `_render_v4_tasks()` が tasks データを要求するテストでは:
```python
task = TaskInfo(id="W1-B5-T1", milestone="B-5", assignee="Sonnet", status="completed")
```
DashboardData の tasks=[] では `data-milestone=` が出力されないため必ず非空 tasks を用意すること。

## Bash 権限制限（L1 リレー依頼パターン）

このセッションでも Bash が制限されており pytest を直接実行できない。
静的検証（read/grep）で assert 充足を確認し、L1 に実行を委ねる形で完了報告する。
