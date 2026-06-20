# artifact PM 採用案 ↔ requirements 突合（2026-06-20）

## 実施概要

- **artifact 原典**: `docs/artifacts/v5-fat-audit-2026-06-19.md`（2026-06-19 B-4 監査）
- **仕様書対象**: `docs/specs/v5-fat-reduction/requirements.md`（2026-06-20 起草）
- **検証範囲**: 4 つの PM 採用プランと対応する requirements の FR（機能要件）が文字単位で一致しているか

---

## §1 NFR 仕分け（候補 ④）

### artifact 側の PM 采用案（§1.3 + JSON）

| NFR ID | artifact 採用案 | PM 決定 | 実施フェーズ |
|--------|---------------|--------|-----------|
| NFR-6 | 削除候補 | 削除 | B-4 後の PLANNING/BUILDING |
| NFR-7 | 削除候補 | 削除 | B-4 後の PLANNING/BUILDING |
| NFR-8 | 削除候補 | 削除 | B-4 後の PLANNING/BUILDING |
| NFR-17 | 削除候補（A 採用） | 縮小（手動スナップショット化） | B-4 後の PLANNING/BUILDING |
| NFR-14a | 要追加調査 | 再起票（v5 Phase 1） | B-4 後の PLANNING/BUILDING |

### requirements.md 側の対応内容（§1 / §3 / §4）

#### FR-1.1: NFR-6 削除

- **requirements 記述**（L57-64）:
  ```
  #### FR-1.1 NFR-6 削除（MUST）
  
  `docs/specs/v4.0.0-immune-system-requirements.md` §6.3 から NFR-6 の行を削除しなければならない。
  削除後、NFR-6 への参照が残るドキュメントには HTML コメント...を挿入しなければならない。
  
  - 削除対象: 「NFR-6 | PG 権限フックの応答時間 | 数秒程度（command 型） | 努力目標」
  - 根拠: audit §1.2 NFR-6「使用頻度 low / 失敗時影響 low / 計測実装なし」
  ```

- **artifact 側**（§1.2 NFR-6）:
  ```
  **マトリクス分類**: 削除候補
  **削減プラン**: 仕様書から独立した NFR 行を削除し、NFR-9 の注釈内に...一行吸収
  ```

- **一致判定**: ✓ **YES** — artifact は「削除」、requirements も「削除」で文言完全一致

#### FR-1.2: NFR-7 削除

- **requirements 記述**（L66-73）:
  ```
  #### FR-1.2 NFR-7 削除（MUST）
  
  `docs/specs/v4.0.0-immune-system-requirements.md` §6.3 から NFR-7 の行を削除しなければならない。
  削除後の参照への対応は FR-1.1 と同様とする。
  
  - 削除対象: 「NFR-7 | SE 権限フックの応答時間 | 体感で待てる範囲（prompt 型） | 努力目標」
  - 根拠: audit §1.2 NFR-7「使用頻度 low / 失敗時影響 low / 計測実装なし」
  ```

- **artifact 側**（§1.2 NFR-7）:
  ```
  **マトリクス分類**: 削除候補
  **削減プラン**: NFR-6 と同様。削除または一行吸収
  ```

- **一致判定**: ✓ **YES** — artifact は「削除」、requirements も「削除」で一致

#### FR-1.3: NFR-8 削除

- **requirements 記述**（L75-84）:
  ```
  #### FR-1.3 NFR-8 削除（MUST）
  
  `docs/specs/v4.0.0-immune-system-requirements.md` §6.3 から NFR-8 の行を削除しなければならない。
  削除後、§6.3 の注釈（「NFR-6〜8 は厳密な制約ではなく…」）も合わせて削除し、
  「ループ実行時間の計測は NFR-15/16 の可観測性基盤が整備された後に実施する」
  という一文に差し替えなければならない。
  
  - 削除対象: 「NFR-8 | 1ループサイクルの実行時間 | プロジェクト規模に依存...」
  ```

- **artifact 側**（§1.2 NFR-8）:
  ```
  **マトリクス分類**: 削除候補
  **削減プラン**: 削除。仕様書に「ループ実行時間の計測は NFR-15/16 の可観測性基盤が整備されてから実施する」
  一行で代替
  ```

- **一致判定**: ✓ **YES** — artifact は「削除」＋「注釈一行代替」、requirements も同一

#### FR-1.4: NFR-17 縮小

- **requirements 記述**（L86-97）:
  ```
  #### FR-1.4 NFR-17 縮小（MUST）
  
  `docs/specs/v4.0.0-immune-system-requirements.md` §6.5 の NFR-17 を以下の内容に差し替えなければならない:
  
  - 差し替え前: 「NFR-17 | 運用KPI の定期集計（`/daily` コマンドとの連携）」
  - 差し替え後: 「NFR-17 | 運用 KPI の手動スナップショット（`/quick-save` 実行時に K1〜K5 の値を人間が記録する。
    自動集計スクリプトの実装はオプション）」
  ```

- **artifact 側**（§1.2 NFR-17）:
  ```
  **PM 査定（2026-06-19）**:
  - NFR-17 削減プラン **A 採用**（自動集計要件を削除し、手動スナップショットに再定義）
  
  **削減プラン**:
  - A（推奨）: NFR-17 の「自動集計」要件を削除し、「手動スナップショット」として再定義。
    `evaluation-kpi.md §6.2` の Wave 2 前後条件分岐は削除し、「K1〜K5 の定義を維持するが集計はオプション」に変更
  ```

- **一致判定**: ✓ **YES** — artifact は「自動集計要件を削除し、手動スナップショット化」、requirements も「手動スナップショット」で一致

#### FR-1.5: NFR-14a 再起票

- **requirements 記述**（L99-110）:
  ```
  #### FR-1.5 NFR-14a 再起票（MUST）
  
  `docs/specs/v4.0.0-immune-system-requirements.md` §6.4 の NFR-14a を以下の内容に更新しなければならない:
  
  - 更新前: 「NFR-14a | フック分類の誤判定率を Wave 1 完了後に計測し、ベースラインを確立する」
  - 更新後: 「NFR-14a | フック分類の誤判定率を v5 Phase 1 で計測スクリプトを実装し、ベースラインを確立する
    （現状: 実計測ゼロ・計測スクリプト未実装。Wave 1 完了チェック済みだが内容未達）」
  
  この更新に対応する v5 タスク起票（計測スクリプトの実装タスク）を 
  `docs/specs/v5-fat-reduction/future-candidates.md` に記録しなければならない。
  ```

- **artifact 側**（§1.2 NFR-14a）:
  ```
  **マトリクス分類**: 要追加調査（Opus 査定で降格・元 Sonnet 判定: 削除候補）
  **削減プラン**: NFR-14a の定義を「Wave 1 完了後」から「v5 Phase 1」へ更新し、
  計測スクリプト実装タスクを v5 タスクとして再起票（PM 級）。
  現 NFR-14a はフラグとして温存しつつ「未達成」を明記
  ```

- **一致判定**: ✓ **YES** — artifact は「Phase を Wave 1 → v5 Phase 1 へ更新」＋「v5 タスク再起票」、requirements も「v5 Phase 1 で計測スクリプト実装」＋「v5 タスク起票」で一致

### 結論（§1）

| FR | artifact 採用案 | requirements 記述 | 一致度 |
|----|---------------|-----------------|-------|
| FR-1.1 (NFR-6) | 削除 | 削除 | ✓ YES |
| FR-1.2 (NFR-7) | 削除 | 削除 | ✓ YES |
| FR-1.3 (NFR-8) | 削除 + 注釈代替 | 削除 + 注釈代替 | ✓ YES |
| FR-1.4 (NFR-17) | 手動スナップショット化 | 手動スナップショット | ✓ YES |
| FR-1.5 (NFR-14a) | Phase 更新 + v5 再起票 | Phase 更新 + v5 タスク起票 | ✓ YES |

**齟齬なし**

---

## §2 distill-lessons grader ログ空スキップ（候補 ②）

### artifact 側の PM 采用案（§2.6 + JSON）

| プラン | artifact 采用 | 判定基準 |
|--------|------------|---------|
| プラン A | **採用** | grader ログ空スキップ機構を追加（SE 級） |
| プラン B | 後送り | /retro Step 4 への lessons.md 確認手順追加は v5 PLANNING 時に併せて検討 |
| プラン C | 棚上げ | セマンティック重複チェックは lessons.md エントリ 30 件超え後に再評価 |

#### 判定基準の詳細（artifact §2.6）

```
判定基準は 【全フィールドが空 / 定型文のみ】
（ループ回数 0、fail 原因なし、修正内容なし、一般則が定型文のみの全条件を満たす場合のみスキップ）
```

### requirements.md 側の対応内容（§2 / §3）

#### FR-2.1: 空スキップ条件の実装

- **requirements 記述**（L121-133）:
  ```
  #### FR-2.1 空スキップ条件の実装（MUST）
  
  `distill()` 関数は、以下の全条件を同時に満たす場合にエントリ追記をスキップし、
  `distill-lessons: skipped (empty grader log)` をログ出力した後、戻らなければならない（MUST）:
  
  | 条件 ID | 判定対象 | 判定基準 |
  |---------|---------|---------|
  | C-1 | ループ回数（grader ログ内の pass/fail イベント数） | 0 件 |
  | C-2 | fail 原因フィールド | 空文字列、`null`、または未設定 |
  | C-3 | 修正内容フィールド | 空文字列、`null`、または未設定 |
  | C-4 | 一般則フィールド | 空文字列、`null`、「（自動抽出・要人間確認）」定型文のみ、またはそれらの組み合わせ |
  
  C-1〜C-4 の全条件が成立する場合のみスキップする。
  ```

- **artifact 側**（§2.6）:
  ```
  判定基準は 【全フィールドが空 / 定型文のみ】
  （ループ回数 0、fail 原因なし、修正内容なし、一般則が定型文のみの全条件を満たす場合のみスキップ）
  ```

- **一致判定**: ✓ **YES** — artifact の「ループ回数 0、fail 原因なし、修正内容なし、一般則が定型文のみ」と requirements の「C-1, C-2, C-3, C-4 全条件」が対応

#### FR-2.2: 既存実装との整合

- **requirements 記述**（L135-144）:
  ```
  #### FR-2.2 既存実装との整合（MUST）
  
  空スキップは `.claude/scripts/distill_lessons.py` L241-244 の既存 `task_id` 重複チェック（idempotency）より
  先に評価しなければならない。処理順序は以下の通りとする:
  
  ```
  1. grader ログ空スキップ判定（FR-2.1）← 本要件で追加
  2. task_id 重複チェック（既存 L241-244）← 変更なし
  3. エントリ構築・追記（既存処理）← 変更なし
  ```
  ```

- **artifact 側**（§2.6）:
  ```
  プラン A 採用: grader ログ空スキップ機構を追加（SE 級）
  判定基準は...の全条件を満たす場合のみスキップ
  ```

  artifact は詳細な処理順序を明記していないが、監査レポート本体（§2.4）に「既存重複スキップはあるが、新規性チェック機構は無し」と記載

- **一致判定**: ✓ **YES** — artifact は「既存 idempotency と別に新規スキップを追加」と示唆、requirements は「処理順序: 空スキップ→既存チェック」で詳細化

#### FR-2.3: テスト追加

- **requirements 記述**（L146-152）:
  ```
  #### FR-2.3 テスト追加（MUST）
  
  以下のテストケースを `.claude/scripts/tests/test_distill_lessons.py` に追加しなければならない:
  
  - `test_empty_grader_log_skips_entry`: grader ログが空リストのとき distill() がスキップすること
  - `test_partial_fields_not_skipped`: C-1〜C-4 のうち 1 条件が成立しない場合（ループ回数 1 件以上）はスキップしないこと
  - `test_skip_log_output`: スキップ時に `distill-lessons: skipped (empty grader log)` がログ出力されること
  ```

- **artifact 側**: テスト追加の言及なし（§2.4 プラン A の記述には「効果」のみ記載）

- **一致判定**: ✗ **NO（見落とし）** — artifact は テスト追加要件を明示しておらず、requirements で初めて出現

  **評価**: これは artifact の漏落、requirements での追加仕様。PM 級以上の判断が必要（実装時のテスト漏れは SE 級だが、ここは新規要件追加）

#### FR-2.4: design との整合確認

- **requirements 記述**（L154-159）:
  ```
  #### FR-2.4 design との整合確認（SHOULD）
  
  本機構の実装前に、`distill_lessons` の設計書（design §13）の「未検証エントリを MUST で追記する」要件と
  本スキップ条件が矛盾しないことを確認すべきである。
  ```

- **artifact 側**（§2.6 副次所見）:
  ```
  プラン A で症状は吸収可能だが、別タスクとしては起票せず本記録のみで残す。
  将来同様パターンが頻発した場合に再調査する
  ```

  artifact は「design §13 の『未検証エントリを MUST で追記』と矛盾の可能性」を指摘しているが、確認の実施は明示していない

- **一致判定**: ✓ **YES（SHOULD）** — artifact は「PM 判断が必要」と示唆、requirements は「確認すべき」と SHOULD で柔らかく規定

### 結論（§2）

| FR | artifact 採用案 | requirements 記述 | 一致度 |
|----|---------------|-----------------|-------|
| FR-2.1 | C-1〜C-4 全条件スキップ | C-1〜C-4 全条件スキップ | ✓ YES |
| FR-2.2 | 既存 idempotency と別に追加 | 処理順序: 空スキップ→既存チェック | ✓ YES（詳細化） |
| FR-2.3 | テスト言及なし | 3 つのテストケース追加 | ✗ NO（漏落） |
| FR-2.4 | PM 判断が必要と示唆 | design §13 との整合確認（SHOULD） | ✓ YES |

**齟齬 1 件**: FR-2.3 テスト追加が artifact で明示されていない

---

## §3 /full-review SKILL.md no-op マーカー（候補 ③）

### artifact 側の PM 采用案（§3.6 + JSON）

```
**方針 X 采用（現状温存・文書化のみ）**: 
プラン A を採用。SKILL.md に「現状 no-op（前提条件未充足）」マーカーを追記する SE 級修正のみ実施。
Stage 1/3 の物理撤去は行わない（Plan B/C/D の v5 復活余地を残す）
```

### requirements.md 側の対応内容（§3 実施済み）

- **requirements 記述**（L163-196）:
  ```
  ### §3: /full-review SKILL.md no-op マーカー（実施済み）
  
  > 根拠: 監査レポート §3（...§3.4 プラン A 方針 X）
  > 実施状況: commit c674ec8 で完了済み（2026-06-19）
  
  本セクションは実施済み作業の記録である。新規実装タスクは発生しない。
  
  #### 背景
  
  `/full-review` SKILL.md（v1.2.0・944 行）の以下 4 Step は...
  
  #### 実施内容
  
  commit c674ec8 により、上記 4 Step の各 Step 冒頭に以下形式のマーカーが追記された:
  
  ```
  > **現状 no-op（前提条件未充足）**: [理由]。[充足条件] が実装された時点で有効化される。
  ```
  
  #### 受け入れ条件（確認のみ）
  
  - commit c674ec8 が master に存在し、4 Step のマーカー追記が確認できること
  - SKILL.md の Stage 1/3 が物理削除されていないこと
  ```

- **artifact 側**（§3.6）:
  ```
  **方針 X 采用（現状温存・文書化のみ）**: 
  プラン A を采用。SKILL.md に「現状 no-op（前提条件未充足）」マーカーを追記する SE 級修正のみ実施。
  Stage 1/3 の物理撤去は行わない
  ```

### 一致判定

- artifact の「プラン A を采用。SKILL.md に『現状 no-op』マーカーを追記」と requirements の「commit c674ec8 で完了済み・マーカー追記」が対応

- **一致判定**: ✓ **YES** — artifact は「プラン A = マーカー追記」と規定、requirements は「実施済み（c674ec8）」と確認

**特記**: 本セクションは「実施済み作業の記録」であり、新規実装タスクは発生しない（§3 Non-Goals での除外）

### 結論（§3）

| フェーズ | 内容 | 一致度 |
|---------|------|-------|
| 実施内容 | SKILL.md に現状 no-op マーカー追記 | ✓ YES（実施済み確認） |
| 物理削除 | Stage 1/3 は削除しない（温存） | ✓ YES |

**齟齬なし**

---

## §4 MAGI Reflection 警告ラベル付き温存（候補 ①）

### artifact 側の PM 采用案（§4.6 + JSON）

```
**プラン B 采用 + 暫定「警告ラベル付き温存」**: 
v5 構想 ② gabriel 統合を長期方針として正式採用。
暫定対応として MAGI Reflection ステップに「形式実行・効果 0%」警告ラベルを付与しつつ機構を残す
（物理削除・コメントアウトは不採用）
```

### requirements.md 側の対応内容（§4）

#### FR-4.1: SKILL.md への警告ラベル追記

- **requirements 記述**（L211-222）:
  ```
  #### FR-4.1 MAGI SKILL.md への警告ラベル追記（MUST）
  
  `.claude/skills/magi/SKILL.md` の Step 4（Reflection）冒頭に以下の警告ラベルを追記しなければならない:
  
  ```markdown
  > **[WARNING: temporary preserve / v5② gabriel 統合予定]**
  > Reflection（Step 4）は形式実行の状態にある。
  > B-4 監査（2026-06-19）の実機計測では、9 件の適用事例中 7 件が記録済みで、
  > 初回変更率 0%（全件「致命的な見落とし: なし → 結論確定」）であった。
  > ...
  ```
  ```

- **artifact 側**（§4.6）:
  ```
  **プラン B 采用 + 暫定「警告ラベル付き温存」**: 
  v5 構想 ② gabriel 統合を長期方針として正式採用。
  暫定対応として MAGI Reflection ステップに「形式実行・効果 0%」警告ラベルを付与しつつ機構を残す
  ```

- **一致判定**: ✓ **YES** — artifact は「警告ラベル付き温存」、requirements は「[WARNING] ラベル追記 + gabriel 統合予定との明示」で一致

#### FR-4.2: decision-making ルールへの警告追記

- **requirements 記述**（L224-228）:
  ```
  #### FR-4.2 decision-making ルールへの警告追記（MUST）
  
  `.claude/rules/decision-making.md` の「Reflection（新規追加）」行（Step 4 該当箇所）に、
  FR-4.1 と同趣旨の警告コメントを追記しなければならない。
  ただし `rules/` 配下の変更は PM 級であるため、実装前に人間の承認を得なければならない（MUST）。
  ```

- **artifact 側**: rules 変更への言及なし

- **一致判定**: ✗ **NO（見落とし）** — requirements で rules/ 変更として初めて出現

#### FR-4.3: lam-orchestrate 参照コピーの同期

- **requirements 記述**（L230-233）:
  ```
  #### FR-4.3 lam-orchestrate 参照コピーの同期（MUST）
  
  `.claude/skills/lam-orchestrate/references/magi-skill.md` に FR-4.1 と同内容の警告ラベルを
  追記しなければならない。SKILL.md と参照コピーの警告ラベル文言を同一に保たなければならない（MUST）。
  ```

- **artifact 側**: lam-orchestrate 参照コピーへの言及なし

- **一致判定**: ✗ **NO（見落とし）** — requirements で参照コピー同期として初めて出現

#### FR-4.4: future-candidates への gabriel 統合設計記録

- **requirements 記述**（L235-244）:
  ```
  #### FR-4.4 future-candidates への gabriel 統合設計記録（MUST）
  
  以下の情報を `docs/specs/v5-fat-reduction/future-candidates.md` に記録しなければならない:
  
  - 対象: MAGI Reflection の gabriel adversarial probe への統合
  - 設計根拠: ADR-0005 Reflection 追補（2026-05-29）が示した「別セッション・独立文脈での検証が 3 catch を発見」パターン
  - 統合方針: gabriel（出題・決断者）が Convergence 後に独立文脈で adversarial probe を実行し、
    Reflection の「入力同一問題」を構造的に解消する
  ```

- **artifact 側**（§4.6）:
  ```
  **v5 構想 ② への統合**: 
  ADR-0005 別セッション DW catch パターンを gabriel 設計根拠として明示追記。
  SESSION_STATE.md の v5 ② 骨子に補強記述として追記
  ```

  artifact は「SESSION_STATE.md v5 ② への追記」と記述しているが、requirements は「future-candidates.md への記録」と指定

- **一致判定**: ✗ **PARTIAL** — artifact は SESSION_STATE.md への記録を指示、requirements は future-candidates.md への記録を指示（保存先の差異）

#### FR-4.5: AoT 分解の温存確認

- **requirements 記述**（L246-250）:
  ```
  #### FR-4.5 AoT 分解の温存確認（MUST NOT）
  
  本要件の実装において、AoT 分解（Step 1-3）を削除または変更してはならない。
  AoT 分解は Reflection と独立した別機構であり、W5-T2 で 6 件の隠れリスクを顕在化した実績を持つ
  （audit §4.6 PM 決定「AoT 分解は温存」）。
  ```

- **artifact 側**（§4.6）:
  ```
  **AoT 分解は温存**: 
  Reflection と AoT 分解は別機構。W5-T2 で 6 件の隠れリスクを顕在化したのは AoT 分解の貢献であり、
  Reflection の貢献ではない。AoT 分解は v5 ② でも温存する
  ```

- **一致判定**: ✓ **YES** — artifact は「AoT 分解温存・v5 ② でも維持」、requirements も「AoT 分解は削除または変更してはならない」で一致

### 結論（§4）

| FR | artifact 采用案 | requirements 記述 | 一致度 |
|----|---------------|-----------------|-------|
| FR-4.1 | SKILL.md に警告ラベル | 警告ラベル追記 | ✓ YES |
| FR-4.2 | rules/ 変更への言及なし | decision-making.md に警告追記 | ✗ NO（漏落） |
| FR-4.3 | lam-orchestrate 言及なし | 参照コピーの同期 | ✗ NO（漏落） |
| FR-4.4 | SESSION_STATE.md v5 ② への記録 | future-candidates.md への記録 | ✗ PARTIAL（保存先差異） |
| FR-4.5 | AoT 分解温存・v5 ② で維持 | AoT 分解は削除変更禁止 | ✓ YES |

**齟齬 3 件**: FR-4.2 / FR-4.3 / FR-4.4（保存先）

---

## 齟齬サマリ

### 齟齬一覧

| # | 章 | FR | 内容 | 重要度 |
|----|----|----|------|--------|
| 1 | §2 | FR-2.3 | テスト追加が artifact で明示されていない | **中** |
| 2 | §4 | FR-4.2 | rules/ 変更（decision-making.md）が artifact で明示されていない | **中** |
| 3 | §4 | FR-4.3 | lam-orchestrate 参照コピー同期が artifact で明示されていない | **中** |
| 4 | §4 | FR-4.4 | 保存先差異: artifact は SESSION_STATE.md、requirements は future-candidates.md | **高** |

### 義務レベル変動（artifact → requirements）

| 件 | 項目 | artifact 側 | requirements 側 | 方向 |
|----|------|-----------|----------------|------|
| 1 | FR-2.4 design 整合確認 | PM 判断が必要（暗示） | SHOULD（明示） | 弱化（SHOULD へ緩和） |

---

## 所見・指摘

### 1. 重要な齟齬: FR-4.4 の保存先差異

**artifact の記述**（§4.6）:
```
**v5 構想 ② への統合**: 
ADR-0005 別セッション DW catch パターンを gabriel 設計根拠として明示追記。
SESSION_STATE.md の v5 ② 骨子に補強記述として追記
```

**requirements の記述**（FR-4.4）:
```
#### FR-4.4 future-candidates への gabriel 統合設計記録（MUST）

以下の情報を `docs/specs/v5-fat-reduction/future-candidates.md` に記録しなければならない:
```

**判定**: これは要件の **強化・변경** ではなく、**저장 경로 명시화** の문제다. requirements가 artifact의 「v5 ② 骨子への補강」를 더 구체적으로 「future-candidates.md」라는 파일명으로 지정한 것.

**評価**: artifact は「SESSION_STATE.md 원본 업데이트」를 지시했지만, requirements는 「future-candidates.md (분리된 문서)」를 새로운 저장처로 지정. 이것은 **문서 구조의 의도적 변경** (非스코프 변경).

**PM 판断 필요**: requirements §7 에서 `docs/specs/v5-fat-reduction/future-candidates.md` 가 新규생성 될 문서인지, 기존 문서인지 명확화 필요.

### 2. 누락: 테스트 및 규칙 파일 변경 (FR-2.3, FR-4.2, FR-4.3)

artifact는 PM采用案이 명시되었지만:
- **FR-2.3 테스트**: SE 급 추가(PM이 아님)이지만, artifact에서는 「테스트」에 대한 언급이 완전히 부재
- **FR-4.2 decision-making.md**: PM 급 변경(`.claude/rules/` 수정)이므로 artifact에서 명시되어야 함. 누락된 것으로 보임
- **FR-4.3 lam-orchestrate**: 참조 코피 동기화. artifact § 4.6에서 「副次所見」 수준으로는 언급되지 않음

### 3. 강화된 요건: requirements가 artifact의 의도를 더 명확화

| 경우 | artifact | requirements | 평가 |
|------|---------|-------------|------|
| FR-2.1 | 「조건 명시」 | 「C-1〜C-4 표로 명시」 | 요건 강화 (좋음) |
| FR-2.4 | 「PM 판단 필요 암시」 | 「SHOULD로 명시」 | 요건 강화 (좋음) |

---

## 최종 판정

### PASS / FAIL

**FAIL** — 다음 齟齬 존재:

1. **§4 FR-4.4**: 보존 위치 명시화 (artifact SESSION_STATE.md → requirements future-candidates.md)
2. **§2 FR-2.3**: 테스트 요건 누락
3. **§4 FR-4.2/FR-4.3**: 규칙 및 참조 코피 변경 누락

### 齟齬 분류

| 齟齬 | 타입 | 심각도 | PM 판단 필요 |
|-----|------|--------|------------|
| FR-4.4 | 保存처 명시화 | **높음** | ✓ **필수** |
| FR-2.3 | 테스트 누락 | 중간 | 선택 (SE 급) |
| FR-4.2 | rules/ 변경 누락 | 높음 | ✓ **필수** |
| FR-4.3 | 참조코피 동기화 누락 | 중간 | 선택 |

---

## 結論

**artifact PM 采用案과 requirements의 FR은 문자 단위 완전 일치하지 않음**.

- **§1 NFR 仕分け**: 완전 일치 ✓
- **§2 distill-lessons**: 部分 일치 (FR-2.3 테스트 누락)
- **§3 /full-review**: 完全 일치 (실시 완료)
- **§4 MAGI Reflection**: 부분 일치 (FR-4.2/4.3/4.4 편차)

requirements는 artifact를 基礎로 하되, **PM 판단 필요사항**을 추가로 명시한 것으로 보임. 특히:
- FR-4.4의 「future-candidates.md」 명시는 artifact의 모호함을 강화한 것
- FR-2.3 테스트는 artifact에서 완전 누락
- FR-4.2/4.3은 rules/ 변경이므로 PM 급이어야 하나 artifact에서 누락

**다음 단계**: PM이 以下 항목 승인 필수:
1. FR-4.4 저장처: SESSION_STATE.md vs future-candidates.md 중선택
2. FR-2.3 테스트: 신규요건 추가인지 원래 포함이었는지 명확화
3. FR-4.2/4.3: rules/ 및 참조코피 변경 추가 여부

