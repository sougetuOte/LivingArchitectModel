---
name: b5-wave9-description-design-context
description: B-5 Wave 9 V-4 description 列追加設計の文脈。chip task_5de9563e 対応。spec-critic ラウンド3完了 (v0.2.6) / FR-W9-N1 (a)(b)(c) + sortTable() aria-sort 修正確定
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
- `docs/specs/b4-dashboard/design.md` Edit (v0.2.2 → … → v0.2.7)
- `docs/specs/b4-dashboard/wave9/requirements.md` 新規 (v0.2.3) → Edit (v0.2.7)
- `docs/specs/b4-dashboard/wave9/design.md` 新規 (v0.2.3) → Edit (v0.2.7)

**spec-critic ラウンド 2 反映 (v0.2.5 / 選択肢 A 補完)**:
Critical I-C-N1 解決: `sortTable()` が `cells[btn.dataset.col]` 経由でアクセスするため、
data-col 属性値の更新も必須と判明。JS 定数値だけでなく thead テンプレートの data-col も同期更新。
- 担当 th: data-col="1" → "2" / 状態 th: data-col="2" → "3" / Task ID th: data-col="0" 変更なし
- description th: data-col 属性なし（ソート不可設計のため）
FR-W9-N1 を (a) JS 定数値 + (b) data-col 属性値の 2段構えに拡張。
AC-W9-N1 を 5 検証手段に拡張（thead data-col 確認 / btn.dataset.col="3" 整合確認）。
colNames 配列（3要素）は Wave 9 後も変更不要（`th[aria-sort]` NodeList から description 列が除外される設計）。

**spec-critic ラウンド 4 結果 (Critical 0 / Warning 1 / Info 2)**: I-W-RR1 (§8 注記) / I-I-RR1 (-1 fallback 補足) / I-I-RR2 (ヘッダ version)。ユーザー選択肢 X で一括修正 → v0.2.7 Green State 完全達成。

**spec-critic ラウンド 3 反映 (v0.2.6 / 選択肢 A + sortTable aria-sort 修正)**:
Critical I-C-R1 解決: `sortTable()` 内 L391-408 の `ths.forEach` で `idx === columnIndex` が
Wave 9 後に担当列(1===2)・状態列(2===3)で常に false → aria-sort 属性更新が破壊される核心バグを発見。
修正: `thCol = parseInt(th.querySelector('.sort-btn')?.dataset.col ?? '-1', 10)` を計算し
`thCol === columnIndex` に判定を変更。aria-label の `colNames[idx]` は idx ベースを維持（正しく動作）。
FR-W9-N1 を (a) JS 定数値 + (b) data-col 属性値 + (c) sortTable() aria-sort 修正 の3段構えに拡張。
AC-W9-N1 に検証手段 6（aria-sort 属性更新テスト / NFR-W9-4 整合）を追加。
wave9/design.md §6 に「(c) sortTable() aria-sort 更新ロジック修正」節を新設。
§8 に FR-W9-N1 (a)(b)(c) チェックリスト3行 + aria-sort テスト行を追加。

**Wave 8 FR-W8-4 との関係**: Wave 8 の「既存4パーサ無改変 MUST NOT」は Wave 8 スコープ内の宣言。
Wave 9 は別仕様書で TasksParser の 1行変更を明示的に許可（parser ロジック追加ゼロ条件付き）。

関連: [[b5-wave8-merger-design-context]]
