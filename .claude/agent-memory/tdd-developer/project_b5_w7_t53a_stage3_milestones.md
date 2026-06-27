---
name: project_b5_w7_t53a_stage3_milestones
description: B-5 W7 T53a — test_wave7_stage3_milestones.py 新規作成・mock fixture 駆動・10 件 PASS
metadata:
  type: project
---

## B-5 Wave 7 Stage 3 T53a: test_wave7_stage3_milestones.py 新規作成

Wave 7 Stage 3 / T53a で `_render_v2_milestones()` の section/article 構造テストを新規作成。

**Why:** T51 が並列実装中だったため TDD Red 先行ポリシーで作成。実際には T51 が先に完成していたため全件即 PASS。

**How to apply:** design.md §8 の HTML 構造（`<article class="milestone-card" data-milestone="{name}">` / `.milestones-container`）を直接テスト対象とする。

### 実装ポイント

- **呼び出し方式**: `DashboardBuilder(data=mock_data)._render_v2_milestones()` を直接呼ぶ（build() 全体は使わない）
- **fixture**: `DashboardData(current_phase=..., milestones=[MilestoneInfo(...)], waves=[], tasks=[])` — 全フィールドにデフォルト値あり
- **ソートテスト**: 入力 [B-5, B-4] → 出力で `html.index('data-milestone="B-4"') < html.index('data-milestone="B-5"')` を確認
- **Empty state**: `class="milestone-card"` が出現しないことも確認（バグ予防）

### テストファイル

`.claude/tests/dashboard/test_wave7_stage3_milestones.py` — 10 件（必須 8 + 任意 2）

| # | テスト名 | カテゴリ |
|---|---------|---------|
| 1 | test_v2_renders_milestones_in_alphabetical_order | 必須 |
| 2 | test_v2_renders_data_milestone_attribute | 必須 |
| 3 | test_v2_renders_milestone_card_count_matches_milestones | 必須 |
| 4 | test_v2_renders_milestones_container_wrapper | 必須 |
| 5 | test_v2_step_column_uses_current_phase | 必須 |
| 6 | test_v2_renders_h3_with_milestone_name | 必須 |
| 7 | test_v2_renders_single_milestone | 必須 |
| 8 | test_v2_renders_empty_state_when_no_milestones | 必須 |
| 9 | test_v2_renders_status_text | 任意 |
| 10 | test_v2_section_has_h2_heading | 任意 |

### 既存テスト破損（T53a 起因ではない）

T51 の builder.py 変更（テーブル→カード構造）により `test_v2_view.py` 7 件が FAIL。
これは design.md §10 で予告済み。T53b（別 Step）で期待値更新が必要（L1 事前承認必須）。

### 行数計測

実装行: 154 / コメント行: 63 / 空行: 89 / 合計: 306
