---
name: b5-wave9-description-design-context
description: B-5 Wave 9 V-4 description 列追加設計の文脈。chip task_5de9563e 対応。3成果物起草済み（design.md v0.2.3 Edit + wave9/requirements.md + wave9/design.md）
metadata:
  type: project
---

Wave 9 = chip task_5de9563e（V-4 description 列なし / Wave 7 PoC レビュー指摘）対応。
Wave 7 retro A10 高優先 → Wave 8 スコープ外 → Wave 9 として 2026-06-28 に設計完了。

**Why:** TasksParser の `_extract_assignee()` は既に `(description_clean, assignee)` を返すが、
呼び出し元 L154 で `_, assignee = ...` と第1要素を捨てていた。parser ロジック追加ゼロで解決可能。

**How to apply:** 次の BUILDING 着手前に以下を確認する:
- `test_v4_view.py` の HTML 期待値更新件数を Grep で確定（2〜6件想定）
- 既存 applySort() JS と description 列（data-col なし）の干渉確認（AC-W9-4）
- TaskInfo への `description=""` 追加が位置引数テストに影響しないか確認

**MAGI 合議確定事項 (B1/B2/B3)**:
- B1: description 列 = V-4 の 2列目（Task ID 右隣）
- B2: ソート不可（MUST NOT）/ `sort-btn` なし / `aria-sort` なし
- B3: TaskInfo に `description: str = ""` + TasksParser で `description_clean, assignee = _extract_assignee(raw_description)` に変更 + `TaskInfo(description=description_clean)` を追加

**成果物**:
- `docs/specs/b4-dashboard/design.md` Edit (v0.2.2 → v0.2.3)
- `docs/specs/b4-dashboard/wave9/requirements.md` 新規 (v0.2.3)
- `docs/specs/b4-dashboard/wave9/design.md` 新規 (v0.2.3)

**Wave 8 FR-W8-4 との関係**: Wave 8 の「既存4パーサ無改変 MUST NOT」は Wave 8 スコープ内の宣言。
Wave 9 は別仕様書で TasksParser の 1行変更を明示的に許可（parser ロジック追加ゼロ条件付き）。

関連: [[b5-wave8-merger-design-context]]
