---
name: project-b4-fat-reduction-requirements
description: B-4 v5 fat削減 要件定義起草で確立した構造パターン・注意点
metadata:
  type: project
---

B-4「v5 fat 削減リファクタ」の要件定義書を起草した（2026-06-20）。
成果物: `docs/specs/v5-fat-reduction/requirements.md`（4 章構成）
副産物: `docs/specs/v5-fat-reduction/future-candidates.md`（Non-Goals の記録）

**Why:** 監査レポート（1085 行・5 章）の PM 採用プランを忠実に要件化する作業。MAGI 合議で 3 Atom が確定済みだったため、独自解釈を一切加えない変換が重要。

**How to apply:** 同様の「監査レポート → 要件定義書」変換タスクでは以下のパターンを適用する:

1. **根拠引用を必ず入れる**: 各章冒頭に「根拠: 監査レポート §X（パス §Y.Z）」を明記する。独自解釈と PM 判断の区別がつく
2. **「実施済み」章は記録セクションとして残す**: commit 番号を引用し、受け入れ条件を「確認のみ」として記述する（§3 の c674ec8 パターン）
3. **物理削除 vs 警告ラベルの判断は PM に帰属する**: 「削除しない理由」を Non-Goals に明示し、仕様書から消えた NFR への参照対策（HTML コメント）も要件に含める
4. **future-candidates.md は requirements.md と同時作成する**: FR から参照するため、ファイル自体が存在しないと要件が宙に浮く
5. **AC（受け入れ条件）は章ごとではなくサマリテーブルにまとめる**: レビュー時のチェックが容易になる
