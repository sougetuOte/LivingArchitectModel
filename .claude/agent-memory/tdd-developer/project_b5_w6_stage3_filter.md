---
name: project-b5-w6-stage3-filter
description: B-5 Wave 6 Stage 3 フィルタ機能実装（T40+T41）知見 — _render_filter_controls() 新設・DOMContentLoaded 単一統合・静的検証パターン
metadata:
  type: project
---

## B-5 Wave 6 Stage 3（T40+T41）フィルタ機能実装

**Why:** Stage 2 ソートに続く Stage 3 として、3フィルタ（状態/Milestone/テキスト）をAND結合するUIとJSを追加した。

### 実装構造
- `_render_filter_controls(self) -> str`: 新設メソッド。_render_v4_tasks() から内部呼び出し（W-NEW-6 責務集約）
- `_render_script()`: applyFilters / resetFilters / initFilters を追加。単一 DOMContentLoaded に統合（C-NEW-2）
- `_render_v4_tasks()`: filter_controls_html 挿入 + `<p id="filter-result-count" aria-live="polite">` 追加
- CSS Section 11（ソートUI）/ Section 12（フィルタUI）を _render_style() に追加
- Layer 2 に `--color-sort-hover` / `--color-filter-bg` / `--color-filter-border` を追加

### DOMContentLoaded 統合（C-NEW-2）
- Stage 2 では `initSortButtons()` のみを呼んでいたリスナーを Stage 3 で拡張
- `initSortButtons()` → `initFilters()` → `applyFilters()` の順序が重要（initFilters 登録後に applyFilters を呼ぶ）
- 単一リスナーは `DOMContentLoaded` が 1 箇所のみであることを grep で確認

### T-S3-10 フィクスチャ（W-NEW-3）
- `MilestoneInfo(name="B-5", current_step="BUILDING", status="in-progress")` を `DashboardData.milestones` に渡す
- `_render_filter_controls()` が `f'<option value="{html.escape(ms.name)}">'` で動的生成
- assert は部分一致 `'<option value="B-5">'` で PASS

### 空 milestones 処理
- `self.data.milestones` が空リストの場合、milestone_options 生成ループが空文字列を返す
- `<select id="filter-milestone">` には「すべて」のみが含まれる（実質無効化）

### JS 行数管理（design.md §11）
- ソート関連（sortTable + initSortButtons）: 約 45 行（コメント・空行除く）
- フィルタ関連（applyFilters + resetFilters + initFilters）: 約 48 行
- 共通初期化（定数 + DOMContentLoaded）: 約 8 行
- 合計: 約 100 行（設計目標 100-150 行の下限付近）
- T-S3 テストには JS 行数カウントを含む（design.md §11 Python 方式）

### 既存テストへの影響
- `_render_v4_tasks()` の改修により `<section id="v4-tasks">` 内部にフィルタUI が追加されるが、
  既存テストは section タグの存在確認と文字列包含チェックのみのため破損なし
- `test_wave3_integration.py` の `html.count('id="v4-')` は `id="filter-result-count"` にマッチしないため安全
- `test_parser_errors_view.py` の `<li>` カウントは parser-errors セクション内のみで安全

### ガードレール遵守
- Bash 実行禁止 → grep/Read による静的検証のみ
- テスト緩和は独自実施せず（今回は既存破損なしのため緩和不要）
- JS 行数は Python 計測スクリプトをテストに組み込む（設計書 §11 参照）

**How to apply:** Stage 4 では `_render_script()` / `_render_v4_tasks()` をさらに改修する可能性があるが、DOMContentLoaded は単一のままで追加呼び出しを末尾に足すパターンで統一する。
