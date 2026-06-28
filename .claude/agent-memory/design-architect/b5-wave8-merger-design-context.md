---
name: b5-wave8-merger-design-context
description: Wave 8 MilestoneSourceMerger 設計の文脈。chip task_68008f88 対応。MAGI 案5採用。パーサ独立性原則と Registry 昇格契約の両立。
metadata:
  type: project
---

Wave 8 = chip `task_68008f88`「Milestone フィルタ仕様乖離」の正式解決 Wave。

**Why:** Wave 7 では SessionStateParser 逆引きを「実装ベース SSOT」として暫定維持していた（wave7/design.md §8）。tasks.md 由来の Milestone が V-2 と V-4 フィルタに欠落するリスクがあるため、Wave 8 で `MilestoneSourceMerger`（集約レイヤ）を新設して解決する。

**MAGI 合議 7 項目（2026-06-28 確定）**:
1. `MilestoneSourceMerger` を b4-dashboard 内に新設（SessionState + tasks.md Milestone 集合の merge）
2. MilestoneRegistry 化は Wave 8 では行わない（将来 ⑥ A 昇格用 Protocol 契約のみ切る）
3. 元 design.md を §2 Non-Goals / §3 アーキ図 / §4 V-2・V-4 / §5 Merger 仕様 / §6 配置 / §13 UQ-8〜10 で更新（v0.1.0 → v0.2.0）
4. Wave 番号は Wave 8（確定）
5. 既存 4 パーサ無改変（FR-W8-4 MUST NOT）
6. 新規テスト（merger 単体 + integration）。既存 398 テスト改変なし or 最小
7. Merger は「上位集約レイヤ」= パーサ独立性原則に違反しない（build_dashboard.py がパーサ結果を Merger に渡す）

**アーキ設計の核心**:
- `merger.py` を `dashboard/` 直下に新設（parsers/ 配下ではない）
- `build_dashboard.py` オーケストレータが全パーサ完了後に `MilestoneSourceMerger().merge()` を呼び `data.milestones` を上書き
- Builder（`_render_v2_milestones()` / `_render_filter_controls()`）は変更不要
- `MilestoneProvider` Protocol を定義して将来 Registry 差し替えを可能に

**成果物**:
- `docs/specs/b4-dashboard/design.md` v0.2.0（Edit 済み）
- `docs/specs/b4-dashboard/wave8/requirements.md` v0.2.0（新規）
- `docs/specs/b4-dashboard/wave8/design.md` v0.2.0（新規）

**How to apply:** Wave 8 BUILDING 委譲時は wave8/design.md §4〜§5 の merge ロジックと Builder 注入差替方針を L2 ガードレールに含める。既存パーサ無改変の確認を Stage 末の必須チェックに設定すること。
