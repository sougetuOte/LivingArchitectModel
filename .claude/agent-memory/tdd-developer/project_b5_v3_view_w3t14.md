---
name: project_b5_v3_view_w3t14
description: B-5 Wave 3 W3-B5-T14 V-3 Wave 一覧ビュー実装の知見
metadata:
  type: project
---

# B-5 W3-T14 V-3 Wave 一覧ビュー実装

Wave 3 で実装した V-3 Wave 一覧ビューの設計判断と実装パターン。

## 実装判断

- Wave 0 件の場合はセクション自体を生成しない（V-2 の empty state 戦略とは異なる）
- Milestone ごとのグループ化は `milestone_order` list + `waves_by_milestone` dict で出現順維持
- 状態決定ロジックは builder.py ではなく呼び出し元（build_dashboard.py）の責務
  - builder は DashboardData.waves に既セットされた status をそのまま表示
  - パーサ独立性の原則（design.md §3）に従う
- `<a href="#v4-tasks">` は各 Milestone セクション末尾の `<p>` に配置

## メソッド構成

- `_render_v3_waves()`: グループ化と各セクション呼び出し（33 行）
- `_render_v3_milestone_section(milestone_name, waves)`: 1 Milestone 分の HTML（37 行）

## 兄弟協調実績

- 兄弟 L2（W3-B5-T15）が同時並列で `_render_v4_tasks()` を追加
- 兄弟は `render()` の `v3_html` 直後に `v4_html` を挿入し、TODO コメントを削除
- 衝突なし（兄弟が先に render() を更新済み・追記のみのルール遵守）

## テスト（30 件追加 / 計 253 件）

- セクション id（Milestone 別）、テーブル列（Wave/Task 数/状態）、状態バッジ 4 値
- data-wave 属性、アンカーリンク、h2 見出し、Milestone グループ化
- 空データ Empty State、HTML エスケープ、V-1/V-2/parser_errors 回帰

**Why:** V-3 は Milestone ごとにセクションを分離する必要があるため、グループ化ロジックが必要。
**How to apply:** 次回同様の「エンティティごとにセクション分割」パターンでは同じ `order + dict` 手法を使う。
