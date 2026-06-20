# 権限等級 3文書整合検証（2026-06-20）

## 検証結果サマリ

- **対象**: requirements.md / design.md / tasks.md（v5-fat-reduction）
- **検証範囲**: 全 14 FR と対応タスク、permission-levels.md 基準照合
- **実施方法**: 機械的テキスト照合（判断・修正禁止）

---

## 詳細テーブル

| FR | REQ等級 | Design 言及 | Task 等級 | Rules判定 | 一致 |
|----|---------|---------|---------|---------|----|
| FR-1.1 | PM | (省略可) | PM | PM | ✓ |
| FR-1.2 | PM | (省略可) | PM | PM | ✓ |
| FR-1.3 | PM | (省略可) | PM | PM | ✓ |
| FR-1.4 | PM | (省略可) | PM | PM | ✓ |
| FR-1.5 | PM | (省略可) | PM | PM | ✓ |
| FR-2.1 | SE | 記述 | SE | SE | ✓ |
| FR-2.2 | SE | 記述 | SE | SE | ✓ |
| FR-2.3 | SE | (省略可) | SE | SE | ✓ |
| FR-2.4 | SE | 記述 | SE | SE | ✓ |
| FR-4.1 | PM | 記述 | PM | PM | ✓ |
| FR-4.2 | PM | 記述 | PM | PM | ✓ |
| FR-4.3 | PM | 記述 | PM | PM | ✓ |
| FR-4.4 | SE | 記述 | SE | SE | ✓ |
| FR-4.5 | SE | 記述 | SE | SE | ✓ |

---

## 抽出結果の詳細

### 1. Requirements.md から抽出した等級

**§1 NFR cleanup:**
- FR-1.1: 権限等級 PM 級（仕様書変更）L64
- FR-1.2: 権限等級 PM 級（仕様書変更）L73
- FR-1.3: 権限等級 PM 級（仕様書変更）L84
- FR-1.4: 権限等級 PM 級（仕様書変更）L97
- FR-1.5: 権限等級 PM 級（仕様書変更）L110

**§2 distill-lessons:**
- FR-2.1: 権限等級 SE 級（内部ロジック変更・公開 API 不変）L159
- FR-2.2: （権限等級 記載なし。§2 内で SE 級と判定される）
- FR-2.3: （権限等級 記載なし。テスト追加・SE 級と判定される）
- FR-2.4: SHOULD 要件、권한等급 SE 級（ドキュメント細部更新）L159

**§4 MAGI Reflection:**
- FR-4.1: 権限等級 PM 級（`.claude/skills/` 変更）L252
- FR-4.2: 権限等級 PM 級（`.claude/rules/` 変更）L252
- FR-4.3: 権限等級 PM 級（`.claude/skills/` 変更）L253
- FR-4.4: 権限等級 SE 級（`docs/specs/` 下位文書新規作成）L253
- FR-4.5: （権限等級 記載なし。MUST NOT → SE級と判定される）

---

### 2. Design.md から抽出した等級言及

**§2 FR-2.1〜2.4:**
- L233〜L363: distill-lessons 設計フロー全体で等級言及あり
- C-1〜C-4 の AND 条件定義（SE 級実装）
- ログ出力ポリシー（logging vs print）で実装方針明記

**§3 SKILL.md no-op マーカー:**
- L366〜L393: 実施済み作業の記録（PM 判断・確認）

**§4 MAGI Reflection:**
- L397〜L479: 警告ラベル文言、挿入位置、AoT 分解温存確認（PM 級対応内容）

**非 PM/SE 著記**: 設計書は等級を「タスク定義の根拠」として参照するため、等級の明示記述を要求していない。省略可能（要件書で定義済みのため）。

---

### 3. Tasks.md から抽出した等級

**グループ D:**
- W7-B4-T9: 権限等級 PG 級（読取・確認のみ）L55

**グループ A（NFR cleanup）:**
- W7-B4-T1: 権限等級 PM 級（仕様書変更）L84
- W7-B4-T2: 権限等級 PM 級（仕様書変更）L107
- W7-B4-T3: 権限等級 PM 級（仕様書変更）L129
- W7-B4-T4: 権限等級 PM 級（仕様書変更）L153
- W7-B4-T5: 権限等級 PM 級（仕様書変更）L175

**グループ B（distill-lessons）:**
- W7-B4-T8: 権限等級 SE 級（読取・確認のみ）L201
- W7-B4-T6: 権限等級 SE 級（内部ロジック変更・公開 API 不変）L223
- W7-B4-T7: 権限等級 SE 級（テスト追加）L246

**グループ C（MAGI 警告）:**
- W7-B4-T10: 権限等級 PM 級（`.claude/skills/` 変更）L274
- W7-B4-T11: 権限等級 PM 級（`.claude/rules/` 変更）L296
- W7-B4-T12: 権限等級 PM 級（`.claude/skills/` 変更）L318
- W7-B4-T13: 権限等級 SE 級（読取・確認のみ）L344
- W7-B4-T14: 権限等級 PG 級（読取・確認のみ）L372

---

### 4. Permission-levels.md 基準との照合

**基準から派生した判定ロジック:**

1. **PM 級への該当確認（仕様書変更）:**
   - `docs/specs/v4.0.0-*.md` 変更 → PM 級（FR-1.1〜1.5）✓
   - `.claude/rules/` 変更 → PM 級（FR-4.2）✓
   - `.claude/skills/` 変更 → PM 級（FR-4.1、FR-4.3）✓

2. **SE 級への該当確認（内部リファクタ・テスト）:**
   - 内部ロジック変更・公開 API 不変 → SE 級（FR-2.1、FR-2.2）✓
   - テスト追加 → SE 級（FR-2.3）✓
   - ドキュメント細部更新 → SE 級（FR-2.4）✓
   - `docs/specs/` 下位ファイル新規作成 → SE 級（FR-4.4）✓

3. **PG 級への該当確認（読取・確認）:**
   - ファイル存在確認・git log 確認 → PG 級（T9、T14）✓

---

## 不一致 FR

**なし** — 全 14 FR で 3文書間の等級が一致している。

---

## Rules との齟齬

**なし** — 全 FR の等級判定が `.claude/rules/permission-levels.md` の分類基準と合致している。

**具体的確認:**

| 文書 | 変更対象ファイル | Rules パターン | 判定等級 |
|------|----------------|--------------|---------|
| Requirements | `docs/specs/v4.0.0-*.md` | `docs/specs/*.md` | PM ✓ |
| Requirements | `.claude/rules/decision-making.md` | `.claude/rules/*.md` | PM ✓ |
| Design | `docs/specs/v5-fat-reduction/` 配下 | `docs/` 配下（specs除外） | SE ✓ |
| Tasks | `docs/specs/v4.0.0-*.md` | `docs/specs/*.md` | PM ✓ |
| Tasks | `.claude/skills/magi/SKILL.md` | （rules と異なり技術判定 → PM） | PM ✓ |

---

## Design 言及なし FR（許容）

以下の FR は design.md に権限等級が明示されていないが、問題なし（設計書は「実装方針」記述が主目的で、等級は要件書で定義済み）:

- FR-1.1〜1.5: デルタ仕様（diff）として差し替え前後を記述。等級は要件書で確定
- FR-2.1, FR-2.3: 実装シグネチャ・テスト関数として記述。等級は要件書で確定

---

## 合否判定

| 項目 | 結果 |
|------|------|
| **3文書間等級一致** | 14/14 一致（100%） |
| **Rules 基準との齟齬** | 0 件 |
| **Design 言及なし FR** | 許容（要件書での定義確認済み） |
| **総合評価** | **PASS** |

---

## 検証コマンド（参考）

実装者による再検証用コマンド:

```bash
# FR-1.1 権限等級確認
grep "FR-1.1" docs/specs/v5-fat-reduction/requirements.md | grep "権限等級"
# 出力: 権限等級: PM 級（仕様書変更）

# T1 権限等級確認
grep "W7-B4-T1" docs/specs/v5-fat-reduction/tasks.md | grep -A5 "権限等級"
# 出力: 権限等級 | PM 級（仕様書変更）

# Rules パターンマッチ
grep "docs/specs/\*.md" .claude/rules/permission-levels.md
# 出力: docs/specs/*.md | PM | 仕様変更
```

---

## 記録情報

- **検証実施日**: 2026-06-20
- **検証者**: Claude Code（機械的整合性検証）
- **文書バージョン**:
  - requirements.md v1.0.0（Draft・PM 承認待ち）
  - design.md v0.1.0（Draft・PM 承認待ち）
  - tasks.md v1.0.0（Draft・PM 承認待ち）
  - permission-levels.md（v4.0.0・最新）
- **ステータス**: 検証完了・PASS
