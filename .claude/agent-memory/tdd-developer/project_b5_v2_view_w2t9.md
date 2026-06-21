---
name: project_b5_v2_view_w2t9
description: B-5 W2-T9 V-2 Milestone 一覧ビュー実装の設計判断と実装パターン
metadata:
  type: project
---

B-5 W2-B5-T9「V-2 Milestone 一覧ビュー」実装完了（2026-06-21）。

## 実装場所

- 実装: `.claude/scripts/dashboard/builder.py`
  - `_render_v2_milestones() -> str` 追加
  - `_render_status_badge(status: str) -> str` 追加
  - `_STATUS_LABELS: dict[str, str]` クラス変数追加
  - `render()` の `<!-- TODO: V-2〜V-4 -->` を `{v2_html}` + `<!-- TODO: V-3〜V-4 -->` に差し替え
- テスト: `.claude/tests/dashboard/test_v2_view.py`（24 件）

## 設計判断

1. **Step 列の値**: `DashboardData.current_phase` を使用（全 Milestone 共通・T7 引き継ぎ方針通り）
   - `MilestoneInfo.current_step` は `"UNKNOWN"` デフォルトのため使わない
2. **empty state 文言**: 「Milestone 情報なし」（`<p>` タグ内）+ テーブルは生成しない
3. **日本語ラベル**: クラス変数 `_STATUS_LABELS` dict で管理
   - completed=完了 / in-progress=進行中 / blocked=ブロック中 / not-started=未着手
4. **未知 status**: `_STATUS_LABELS.get(status, status)` でフォールバック（ラベルとして status 文字列をそのまま表示）
5. **アンカーリンク**: `<a href="#v3-waves-{ms.name}">{ms.name}</a>` 形式

## テストパターン

- `_make_builder(milestones, current_phase)` + `_make_milestone(name, status, current_step)` ヘルパーで DashboardData 直接組み立て
- パーサを呼ばない（T9 完了条件「テストでは MilestoneInfo を直接組み立てた DashboardData を builder に渡す」準拠）
- 既存 89 テスト + 24 テスト = 113 テスト全 PASS

## 次タスクへの引き渡し

- T10（パーサエラー検証）: `_render_parser_errors()` は T9 時点で既存実装済み。テストで `parser_errors=[...]` を DashboardData に直接セットすることで検証可能
- T11（Wave 2 統合テスト）: `<!-- TODO: V-3〜V-4 -->` プレースホルダーが残存。T14/T15（V-3/V-4）実装後に差し替え予定
- T14（V-3）: `_render_v3_waves()` を追加する際、`data.waves: list[WaveInfo]` を使用。アンカー `id="v3-waves-{milestone}"` で V-2 からのリンクと一致させること

**Why:** デザイン §4 V-2 の「複数 Milestone が存在する場合は全 Milestone に同じ Step を表示する」仕様に従い、CurrentPhaseParser 由来の `current_phase` を統一ソースとした。
**How to apply:** V-3/V-4 実装でも `DashboardData.current_phase` を参照する場合は同じパターンを踏襲する。
