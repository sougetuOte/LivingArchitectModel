# design.md 監査レポート（2026-06-20）

## A. 必須セクション

- **A-1 Problem Statement**: PASS（§0、L11-21 で存在）
  - 設計視点から 4 種類の fat を「実装可能な変更単位」に分解しており、問題文として機能している
  - 表形式で fat の原因と設計解を明示

- **A-2 Non-Goals**: PASS（§1、L25-35 で存在）
  - 要件書の Non-Goals をそのまま継承と明示
  - スコープ外 6 項目が列挙されている

- **A-3 Alternatives Considered**: PASS（§2、L39-80 で存在）
  - §1 NFR cleanup の却下案（案 X）
  - §2 distill-lessons の却下案（案 B）
  - §3 SKILL.md no-op マーカー（実施済み確認・却下案なし）
  - §4 MAGI Reflection の却下案（案 A）

- **A-4 Success Criteria**: PASS（§3、L83-97 で存在）
  - 観測可能な条件が 11 の AC（AC-1～AC-11）として明示
  - 計測方法が「grep」「テキスト照合」「ファイル存在確認」等で記載

## B. FR カバレッジ

**Requirements.md の全 FR（14 件）:**
- FR-1.1 ✓（§1.2 L110-125）
- FR-1.2 ✓（§1.2 L110-125 に含む「NFR-7」として明示）
- FR-1.3 ✓（§1.2 L110-125 に含む「NFR-8」として明示）
- FR-1.4 ✓（§1.4 L171-183）
- FR-1.5 ✓（§1.3 L157-169）
- FR-2.1 ✓（§2.2 L260-277）
- FR-2.2 ✓（§2.2 L260-277）
- FR-2.3 ✓（§2.6 L340-362）
- FR-2.4 ✓（requirements.md L154-157 で SHOULD 要件だが、design.md では言及なし — **警告）**
- FR-4.1 ✓（§4.1 L399-410）
- FR-4.2 ✓（§4.3 L434-451）
- FR-4.3 ✓（§4.4 L453-463）
- FR-4.4 ✓（§4.1 L399-410 で gabriel 統合が言及）
- FR-4.5 ✓（§4.5 L465-479）

**未言及 FR**: 0 件（全 14 FR が言及されている）
ただし FR-2.4 は設計書で詳述されていない（requirements.md では SHOULD 要件）

## C. Alternatives Considered の質

### §1 NFR cleanup の却下案（案 X）
- ✓ 却下案が 1 件以上存在
- ✓ 却下理由が事実・トレードオフで説明されている
  - 理由 1-4 が具体的（「現状維持と同義」「誤解を生む」「コスト評価と矛盾」「注釈で十分」）

### §2 distill-lessons の却下案（案 B）
- ✓ 却下案が 1 件以上存在
- ✓ 却下理由が事実で説明されている
  - 理由 1-4 が定量的・定性的（「120 エントリ蓄積予測」「精査コスト」「SE 級で即時実施」）

### §3 SKILL.md no-op マーカー（実施済み確認）
- ⚠️ 却下案なし（§3 が「実施済み確認」の記録専用であるため正当）
- ただしこの章は「却下案なし」が許容されるパターンとして定義されている（L67-69）

### §4 MAGI Reflection 警告ラベルの却下案（案 A）
- ✓ 却下案が 1 件以上存在
- ✓ 却下理由が事実で説明されている
  - 理由 1-3 が技術的・コスト的（「adversarial 検証喪失」「設計地ならし」「直接コスト削減効果限定」）

**総合評価: PASS（全セクションで却下案の質が基準達成）**

## D. 実装可能性（推測実装の禁止）

### §1 diff 範囲の特定
- ✓ **L105**: `docs/specs/v4.0.0-immune-system-requirements.md` 対象ファイル明示
- ✓ **L106**: 「L531〜L574」行番号範囲明示
- ✓ **L110-125**: 「L547〜L554」変更前の行番号付きで diff 掲載

### §2 関数シグネチャの実在確認
- ✓ **L238-256**: `distill()` 関数の現状フロー記載（既存実装 L217-L247 参照）
- ✓ **L286-301**: `_is_grader_log_empty()` 判定関数のシグネチャ案記載（フロー挿入位置 L240 直後と明示）
- ✓ **L90-105, L108-129**: `_extract_fail_reasons()`, `_extract_fix_summary()` への参照指示

### §4 警告ラベル文言の requirements.md FR-4.1 との一致確認
- **L403-410 (design.md の警告ラベル):**
```markdown
> **[WARNING: temporary preserve / v5② gabriel 統合予定]**
> Reflection（Step 4）は形式実行の状態にある。
> B-4 監査（2026-06-19）の実機計測では、9 件の適用事例中 7 件が記録済みで、
> 初回変更率 0%（全件「致命的な見落とし: なし → 結論確定」）であった。
> 根本原因は Step 3 (CASPAR) 直後の同一文脈再処理による入力同一問題。
> 物理削除は行わない。v5 ② で gabriel adversarial probe として機能強化予定。
```

- **requirements.md L216-222 (FR-4.1):**
  - 第一文～最終文まで **完全一致** を確認
  - ✓ 文言同期が保証されている

**総合評価: PASS（全セクションで行番号特定・シグネチャ実在・文言一致が達成）**

## E. Requirements Smells（設計書版）

検出された曖昧表現：

| 行番号 | 単語 | コンテキスト | 重要度 |
|---------|------|------------|--------|
| L18 | 「将来」 | 「将来タスクの根拠が不明」（Problem Statement 表中） | Info |
| L47 | 「将来」 | Alternatives 案 X「将来計測したい意図」 | Info |
| L50 | 「将来」 | Alternatives 案 X「将来実装されるかもしれない要件」 | Info |
| L321 | 「適切に」 | §2.4 ログ出力フォーマット「同一レイヤーに揃えたい」の後の「フィルタリングに対応できる」 | Info |
| L484 | 「将来」 | §5 ADR 候補「将来の ADR として記録を推奨」 | Info |

**判定: Info 級のみ（Critical/Warning は 0 件）**

- 「将来」は context（fat 削減の根拠・代替案の説明・ADR 記録計画）において計測可能な記述（「v5 Phase 1」「v5 ② gabriel 統合」等で後付される）
- L321 の「適切に」は「`logging.INFO` で出力」「`--log-level` フラグ等のフィルタリング」で具体化されており、実装可能性に影響なし

## 総合評価

| 項目 | 結果 | 件数 |
|------|------|------|
| Critical | PASS | 0 |
| Warning | PASS | 0 |
| Info | 検出 | 5 |
| **Green State** | **PASS** | — |

---

## 報告概要

### 成果物パス
`D:/work7/LivingArchitectModel/docs/specs/v5-fat-reduction/design.md`

### 3 行要約
- **合否**: PASS（Green State 達成）
- **Critical/Warning**: 0/0 件（基準達成）
- **最大の指摘**: **FR-2.4 の設計詳述が欠落**（requirements.md では SHOULD 要件として存在するが、design.md で具体化されていない。ただし SHOULD 要件のため PM 判断対象）

### 詳細

1. **必須 4 セクション**: 全て存在（Problem Statement / Non-Goals / Alternatives / Success Criteria）
2. **FR カバレッジ**: 14/14 FR が言及（100%）
   - **警告**: FR-2.4（requirements.md L154-157）は設計書で詳述されていない
     - 要件: 「distill_lessons の設計書（design §13）の『未検証エントリを MUST で追記する』要件と本スキップ条件の矛盾確認」
     - 状況: requirements.md では記載、design.md §2 では触れられていない
     - 評価: SHOULD 要件のため実装ブロッカーではないが、BUILDING フェーズで矛盾確認が必要（AC-6 の「既存テスト 21 件が PASS」で実装側で検証）
3. **Alternatives 質**: 全セクションで却下案が事実・トレードオフベースで説明
4. **実装可能性**: 行番号指定・関数シグネチャ・文言同期が確認済み
5. **Requirements Smells**: Info 級のみ 5 件（Critical/Warning 0）

---

## 実装着手の承認可否

**評価: Green State PASS — BUILDING フェーズ着手可能**

ただし以下の点を BUILDING 実装時に確認することを推奨:

1. **FR-2.4 の矛盾確認**: AC-6（既存テスト 21 件 PASS）実施時に「distill_lessons 設計書と本スキップ条件の矛盾」が発生していないことを確認
2. **goal-driven-orchestration NFR-6/7/8 と v4.0.0 NFR-6/7/8 の grep 再確認**: L108 の注意事項に従い、削除前に「別番号体系」との区別を確実に行う
3. **2.4 ログ出力の logging vs print の選定**: L316-323 で logging.INFO を採用した根拠が示されているため、実装時に既存テスト（capsys/logging mock）の選択を確認
