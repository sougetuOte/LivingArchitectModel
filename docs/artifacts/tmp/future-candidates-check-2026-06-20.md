# future-candidates.md 充足チェック（2026-06-20）

**対象ファイル**: `docs/specs/v5-fat-reduction/future-candidates.md`  
**チェック日**: 2026-06-20  
**チェック基準**: requirements.md FR-4.4 / §7

---

## 充足度表

| # | 項目 | 要件内容 | 状態 | 行番号 | 記載内容 |
|---|------|---------|------|-------|---------|
| 1 | gabriel 統合対象 | 「MAGI Reflection の gabriel adversarial probe への統合」 | ✅ yes | L11-14 | FC-1セクションで gabriel エージェント導入と adversarial probe 機能強化を明記 |
| 2 | 設計根拠 | 「ADR-0005 Reflection 追補（2026-05-29）」「別セッション・独立文脈での検証が 3 catch を発見」 | ✅ yes | L15-17 | ADR-0005 引用と「別セッション・独立文脈での検証が 3 catch を発見」パターンを記載 |
| 3 | 統合方針 | 「gabriel が Convergence 後に独立文脈で adversarial probe を実行」 | ✅ yes | L18-21 | gabriel Convergence 後の独立文脈 probe 実行、MELCHIOR/BALTHASAR/CASPAR 純調停化、AoT 温存を明記 |
| 4 | 実施条件 | 「v5 ② gabriel エージェント設計・ADR 新設・MAGI SKILL.md 全面改訂との同時実施」 | ✅ yes | L22 | 実施条件で「v5 ② gabriel エージェント設計・ADR 新設・MAGI SKILL.md 全面改訂との同時実施」と明記 |
| 5 | 権限等級 | 「PM 級（アーキテクチャ変更・ADR 新設）」 | ✅ yes | L23 | 「PM 級（アーキテクチャ変更・ADR 新設）」と記載 |
| 6 | distill-lessons セマンティック重複チェック | 「プラン C・30 件超到達後」の再評価条件 | ✅ yes | L28-34 | FC-2セクション、再評価条件に「`lessons.md` エントリが 30 件を超えた時点」と明記 |
| 7 | /full-review Stage 1/3 物理撤去 | 「/full-review」の撤去予定と撤去タイミング | ✅ yes | L38-45 | FC-3セクション、no-op 4 Step 削除、Plan B/C/D 復活余地記載、再評価条件に Plan 実装決定時を明記 |
| 8 | /retro Step 4 への lessons.md 確認手順 | 「/retro」Step 4 の手順追加と実施タイミング | ✅ yes | L49-55 | FC-4セクション、Step 4 チェックリストへの未検証エントリ確認・削除手順追加、v5 PLANNING フェーズ開始時を再評価条件に明記 |

---

## 充足判定

### 仕様要件（requirements.md FR-4.4）

| 要件 | 充足状況 |
|------|---------|
| FC-1: gabriel 統合対象・根拠・統合方針・実施条件・権限等級 | ✅ **5/5** 完全充足 |
| FC-2: distill-lessons 重複チェック（再評価条件） | ✅ **1/1** 充足 |
| FC-3: /full-review Stage 1/3 撤去（再評価条件） | ✅ **1/1** 充足 |
| FC-4: /retro Step 4 lessons.md 確認（再評価条件） | ✅ **1/1** 充足 |

### 追加チェック（requirements §7）

| 項目 | 有無 | 備考 |
|------|------|------|
| 6. distill-lessons セマンティック重複 | ✅ yes | FC-2 に明記 |
| 7. /full-review Stage 1/3 物理撤去 | ✅ yes | FC-3 に明記 |
| 8. /retro Step 4 への lessons.md 確認手順 | ✅ yes | FC-4 に明記 |

---

## 不足項目

**なし** — 全要件が充足されている。

---

## 充足率

**8/8 充足 = 100%**

---

## 最終評価

- **合否**: **PASS**
- **評価**: EXCELLENT
- **理由**: 
  - FR-4.4 の 5 項目（FC-1 構成要素）を完全に網羅
  - requirements §7 の追加チェック 3 項目（6～8）もすべて明記
  - 各 FC セクションが再評価条件と権限等級を明示
  - ドキュメント構造が明確で、トレーサビリティが高い

---

## 記載品質評価

| 側面 | 評価 | 根拠 |
|------|------|------|
| **明確性** | A | ADR 引用、条件記載、権限等級が具体的 |
| **完全性** | A | 全要件項目を網羅、再評価条件が実装可能 |
| **トレーサビリティ** | A | requirements.md との双方向リンク可能 |
| **実行可能性** | A | 実施条件・再評価条件が明確で意思決定可能 |

---

## 次ステップ（提案）

1. 本チェック結果を PM タスク記録に追加（e.g., TASK_REGISTER.md）
2. FC-1 から v5 ② タスク群の起票準備
3. FC-2～FC-5 の各再評価条件を v5 以降 roadmap へ登録
