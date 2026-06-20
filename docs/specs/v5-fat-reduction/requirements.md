# 要件定義書: v5 fat 削減リファクタ

- バージョン: 1.0.0
- 作成日: 2026-06-20
- ステータス: Draft（PM 承認待ち）
- 対応フェーズ: PLANNING → BUILDING
- 根拠文書: `docs/artifacts/v5-fat-audit-2026-06-19.md`（B-4 監査レポート・全 5 章）

---

## 1. Problem Statement

B-4 監査（2026-06-19）により、LAM の「文書と実装の乖離」に起因する 4 種類の fat が特定された。
fat の共通構造は以下のいずれかである:

1. **ゾンビ NFR**: 仕様書にのみ定義が残り、計測実装・計測結果が存在しない要件
2. **空振りスキップ欠如**: 追記する情報が物理的に存在しないにもかかわらず書き込みが発生するロジック
3. **no-op Step 無表示**: 前提条件未充足で実質稼働しない Step が SKILL.md に未明示のまま残る
4. **形骸化ステップ**: 全適用事例で効果ゼロが実測された手続きが MUST 要件として残る

本要件定義書は上記 4 点を解消するための実装要件を定義する。

---

## 2. Goals / Non-Goals

### Goals

- NFR-6、NFR-7、NFR-8、NFR-17 を仕様書から削除し、「定義と実態の乖離」を解消する
- NFR-14a の Phase 対象を v5 Phase 1 に更新し、「完了チェック済み・実計測ゼロ」の乖離を解消する
- `distill-lessons.py` に grader ログ空スキップ機構を追加し、情報ゼロエントリの蓄積を防ぐ
- `/full-review` SKILL.md の no-op Step に現状マーカーを付与し、実行者の混乱を防ぐ（実施済み: commit c674ec8）
- MAGI Reflection ステップに警告ラベルを付与し、形式実行の実態を明示する（v5 ② gabriel 統合の暫定対応）

### Non-Goals（非スコープ）

- gabriel エージェントの設計・実装（v5 ② 別マイルストーンで対応）
- MAGI Reflection の物理削除またはコメントアウト
- `/full-review` Stage 1/3 の物理撤去（Plan B/C/D 復活余地を残す）
- NFR-17 の「集計スクリプト実装」（B 案は不採用）
- distill-lessons の セマンティック重複チェック（プラン C・30 件超到達後に再評価）
- `/retro` Step 4 への lessons.md 確認手順追加（プラン B・v5 PLANNING 時に統合）

---

## 3. 機能要件（RFC 2119）

### §1: NFR cleanup

> 根拠: 監査レポート §1（`docs/artifacts/v5-fat-audit-2026-06-19.md` §1.2 / §1.3）

NFR-6、NFR-7、NFR-8 は仕様書本文が自ら「努力目標」「参考値」と宣言しており、
計測コード・計測結果の実装が存在しない（audit §1.2: 使用頻度 low / 失敗時影響 low）。
NFR-17 は集計スクリプトが未実装のまま稼働実績ゼロであり、実態との乖離が最大の fat と判定された
（audit §1.2: PM 決定 A 採用）。

#### FR-1.1 NFR-6 削除（MUST）

`docs/specs/v4.0.0-immune-system-requirements.md` §6.3 から NFR-6 の行を削除しなければならない。
削除後、NFR-6 への参照が残るドキュメントには HTML コメント `<!-- NFR-6 は v5 fat 削減で削除済み (2026-06-20) -->` を挿入しなければならない。

- 削除対象: 「NFR-6 | PG 権限フックの応答時間 | 数秒程度（command 型） | 努力目標」
- 根拠: audit §1.2 NFR-6「使用頻度 low / 失敗時影響 low / 計測実装なし」
- 権限等級: PM 級（仕様書変更）

#### FR-1.2 NFR-7 削除（MUST）

`docs/specs/v4.0.0-immune-system-requirements.md` §6.3 から NFR-7 の行を削除しなければならない。
削除後の参照への対応は FR-1.1 と同様とする。

- 削除対象: 「NFR-7 | SE 権限フックの応答時間 | 体感で待てる範囲（prompt 型） | 努力目標」
- 根拠: audit §1.2 NFR-7「使用頻度 low / 失敗時影響 low / 計測実装なし」
- 権限等級: PM 級（仕様書変更）

#### FR-1.3 NFR-8 削除（MUST）

`docs/specs/v4.0.0-immune-system-requirements.md` §6.3 から NFR-8 の行を削除しなければならない。
削除後、§6.3 の注釈（「NFR-6〜8 は厳密な制約ではなく…」）も合わせて削除し、
「ループ実行時間の計測は NFR-15/16 の可観測性基盤が整備された後に実施する」
という一文に差し替えなければならない。

- 削除対象: 「NFR-8 | 1ループサイクルの実行時間 | プロジェクト規模に依存。計測・可視化を優先 | 参考値」
- 根拠: audit §1.2 NFR-8「使用頻度 low / 失敗時影響 low / 参考値 / 計測実装なし」
- 権限等級: PM 級（仕様書変更）

#### FR-1.4 NFR-17 縮小（MUST）

`docs/specs/v4.0.0-immune-system-requirements.md` §6.5 の NFR-17 を以下の内容に差し替えなければならない:

- 差し替え前: 「NFR-17 | 運用KPI の定期集計（`/daily` コマンドとの連携）」
- 差し替え後: 「NFR-17 | 運用 KPI の手動スナップショット（`/quick-save` 実行時に K1〜K5 の値を人間が記録する。自動集計スクリプトの実装はオプション）」

関連する `docs/specs/evaluation-kpi.md` §6.2 の「Wave 2 完了前は以下を表示: ベースライン未確立」という
条件分岐記述を削除し、「K1〜K5 の定義を維持するが集計は任意（オプション）」に差し替えなければならない。

- 根拠: audit §1.2 NFR-17「集計スクリプト未実装 / 稼働実績 0 件 / PM 決定 A 採用」
- 権限等級: PM 級（仕様書変更）

#### FR-1.5 NFR-14a 再起票（MUST）

`docs/specs/v4.0.0-immune-system-requirements.md` §6.4 の NFR-14a を以下の内容に更新しなければならない:

- 更新前: 「NFR-14a | フック分類の誤判定率を Wave 1 完了後に計測し、ベースラインを確立する」
- 更新後: 「NFR-14a | フック分類の誤判定率を v5 Phase 1 で計測スクリプトを実装し、ベースラインを確立する（現状: 実計測ゼロ・計測スクリプト未実装。Wave 1 完了チェック済みだが内容未達）」

この更新に対応する v5 タスク起票（計測スクリプトの実装タスク）を `docs/specs/v5-fat-reduction/future-candidates.md` に記録しなければならない。

- 根拠: audit §1.2 NFR-14a「要追加調査 / Opus 降格 / tasks 完了チェック済み実計測ゼロ」
  および `docs/adr/0005-thin-harness-autonomous-governance.md`（NFR-14a の設計根拠として ADR-0005 §Mediator 判断が参照可能）
- 権限等級: PM 級（仕様書変更）

---

### §2: distill-lessons grader ログ空スキップ追加

> 根拠: 監査レポート §2（`docs/artifacts/v5-fat-audit-2026-06-19.md` §2.6 / §2.4 プラン A）

`.claude/scripts/distill_lessons.py` の `distill()` 関数に、grader ログが空の場合に
書き込みをスキップする機構を追加する。

#### FR-2.1 空スキップ条件の実装（MUST）

`distill()` 関数は、以下の全条件を同時に満たす場合にエントリ追記をスキップし、
`distill-lessons: skipped (empty grader log)` をログ出力した後、戻らなければならない（MUST）:

| 条件 ID | 判定対象 | 判定基準 |
|---------|---------|---------|
| C-1 | ループ回数（grader ログ内の pass/fail イベント数） | 0 件 |
| C-2 | fail 原因フィールド | 空文字列、`null`、または未設定 |
| C-3 | 修正内容フィールド | 空文字列、`null`、または未設定 |
| C-4 | 一般則フィールド | 空文字列、`null`、「（自動抽出・要人間確認）」定型文のみ、またはそれらの組み合わせ |

C-1〜C-4 の全条件が成立する場合のみスキップする。1 件でも成立しない条件がある場合はスキップしてはならない（MUST NOT）。

#### FR-2.2 既存実装との整合（MUST）

空スキップは `.claude/scripts/distill_lessons.py` L241-244 の既存 `task_id` 重複チェック（idempotency）より
先に評価しなければならない。処理順序は以下の通りとする:

```
1. grader ログ空スキップ判定（FR-2.1）← 本要件で追加
2. task_id 重複チェック（既存 L241-244）← 変更なし
3. エントリ構築・追記（既存処理）← 変更なし
```

#### FR-2.3 テスト追加（MUST）

以下のテストケースを `.claude/scripts/tests/test_distill_lessons.py` に追加しなければならない:

- `test_empty_grader_log_skips_entry`: grader ログが空リストのとき distill() がスキップすること
- `test_partial_fields_not_skipped`: C-1〜C-4 のうち 1 条件が成立しない場合（ループ回数 1 件以上）はスキップしないこと
- `test_skip_log_output`: スキップ時に `distill-lessons: skipped (empty grader log)` がログ出力されること

#### FR-2.4 design との整合確認（SHOULD）

本機構の実装前に、`distill_lessons` の設計書（design §13）の「未検証エントリを MUST で追記する」要件と
本スキップ条件が矛盾しないことを確認すべきである。矛盾が発生した場合は PM 判断を求めなければならない（MUST）。

- 権限等級: SE 級（内部ロジック変更・公開 API 不変）

---

### §3: /full-review SKILL.md no-op マーカー（実施済み）

> 根拠: 監査レポート §3（`docs/artifacts/v5-fat-audit-2026-06-19.md` §3.6 / §3.4 プラン A 方針 X）
> 実施状況: commit c674ec8 で完了済み（2026-06-19）

本セクションは実施済み作業の記録である。新規実装タスクは発生しない。

#### 背景

`/full-review` SKILL.md（v1.2.0・944 行）の以下 4 Step は、前提条件未充足のため 19 Run 全件で
実質稼働ゼロであったにもかかわらず、SKILL.md にその旨が記載されていなかった:

| Step | no-op の原因 |
|------|------------|
| Stage 1 Step 3（依存グラフ構築） | `import-map.json` 未生成 |
| Stage 2 Step 1-2（チャンク分割） | `tree-sitter` 未インストール |
| Stage 3 Step 1（Layer 2 モジュール統合） | `ast_map = {}` 縮退 |
| Stage 3 Step 3（Layer 3 機械的チェック） | `import_map = {}` 縮退 |

#### 実施内容

commit c674ec8 により、上記 4 Step の各 Step 冒頭に以下形式のマーカーが追記された:

```
> **現状 no-op（前提条件未充足）**: [理由]。[充足条件] が実装された時点で有効化される。
```

Stage 1/3 の物理撤去は行わない。Plan B/C/D 復活時の足場として温存する（PM 決定・方針 X）。

#### 受け入れ条件（確認のみ）

- commit c674ec8 が master に存在し、4 Step のマーカー追記が確認できること
- SKILL.md の Stage 1/3 が物理削除されていないこと

---

### §4: MAGI Reflection 警告ラベル付き温存

> 根拠: 監査レポート §4（`docs/artifacts/v5-fat-audit-2026-06-19.md` §4.6 / §4.5）

MAGI Reflection は 9 件の適用事例において初回変更率 0%（7 件記録・7 件「致命的な見落とし: なし」）
であり、機能していない実態が実機データで裏付けられた。
長期方針はプラン B（v5 ② gabriel 統合・adversarial probe への昇格）とし、
暫定対応として Reflection ステップを物理削除せず、警告ラベルを付与して機構を残す。

物理削除・コメントアウトは採用しない理由: v5 ② gabriel 統合への設計地ならしのため、
Reflection の構造と位置を保持する必要がある。

#### FR-4.1 MAGI SKILL.md への警告ラベル追記（MUST）

`.claude/skills/magi/SKILL.md` の Step 4（Reflection）冒頭に以下の警告ラベルを追記しなければならない:

```markdown
> **[WARNING: temporary preserve / v5② gabriel 統合予定]**
> Reflection（Step 4）は形式実行の状態にある。
> B-4 監査（2026-06-19）の実機計測では、9 件の適用事例中 7 件が記録済みで、
> 初回変更率 0%（全件「致命的な見落とし: なし → 結論確定」）であった。
> 根本原因は Step 3 (CASPAR) 直後の同一文脈再処理による入力同一問題。
> 物理削除は行わない。v5 ② で gabriel adversarial probe として機能強化予定。
```

#### FR-4.2 decision-making ルールへの警告追記（MUST）

`.claude/rules/decision-making.md` の「Reflection（新規追加）」行（Step 4 該当箇所）に、
FR-4.1 と同趣旨の警告コメントを追記しなければならない。
ただし `rules/` 配下の変更は PM 級であるため、実装前に人間の承認を得なければならない（MUST）。

#### FR-4.3 lam-orchestrate 参照コピーの同期（MUST）

`.claude/skills/lam-orchestrate/references/magi-skill.md` に FR-4.1 と同内容の警告ラベルを
追記しなければならない。SKILL.md と参照コピーの警告ラベル文言を同一に保たなければならない（MUST）。

#### FR-4.4 future-candidates への gabriel 統合設計記録（MUST）

以下の情報を `docs/specs/v5-fat-reduction/future-candidates.md` に記録しなければならない:

- 対象: MAGI Reflection の gabriel adversarial probe への統合
- 設計根拠: ADR-0005 Reflection 追補（2026-05-29）が示した「別セッション・独立文脈での検証が 3 catch を発見」パターン
- 統合方針: gabriel（出題・決断者）が Convergence 後に独立文脈で adversarial probe を実行し、
  Reflection の「入力同一問題」を構造的に解消する
- 実施条件: v5 ② gabriel エージェント設計・ADR 新設・MAGI SKILL.md 全面改訂との同時実施
- 権限等級（将来）: PM 級（アーキテクチャ変更・ADR 新設）

#### FR-4.5 AoT 分解の温存確認（MUST NOT）

本要件の実装において、AoT 分解（Step 1-3）を削除または変更してはならない。
AoT 分解は Reflection と独立した別機構であり、W5-T2 で 6 件の隠れリスクを顕在化した実績を持つ
（audit §4.6 PM 決定「AoT 分解は温存」）。

- 権限等級: FR-4.1 は PM 級（`.claude/skills/` 変更）、FR-4.2 は PM 級（`.claude/rules/` 変更）
  FR-4.3 は PM 級（`.claude/skills/` 変更）、FR-4.4 は SE 級（`docs/specs/` 下位文書の新規作成）

---

## 4. 非機能要件

| ID | 要件 | 基準 |
|----|------|------|
| NFR-V1 | §1 の仕様書変更は削除箇所に HTML コメントを残す | 削除した NFR の参照先で「見つからない」状態が起きないこと |
| NFR-V2 | §2 の新規テスト追加後、既存テスト 21 件がすべて PASS を維持する | `pytest .claude/scripts/tests/` で FAIL=0 |
| NFR-V3 | §4 の警告ラベルは SKILL.md と参照コピーで文言が一致する | 差分チェックで同一文字列を確認 |

---

## 5. 受け入れ条件サマリ（Definition of Done）

| ID | 章 | 条件 |
|----|-------|------|
| AC-1 | §1 | `v4.0.0-immune-system-requirements.md` §6.3 から NFR-6/7/8 の行が削除されている |
| AC-2 | §1 | §6.3 の注釈が「ループ実行時間の計測は NFR-15/16 整備後に実施する」に差し替えられている |
| AC-3 | §1 | §6.4 の NFR-14a が「v5 Phase 1 で計測スクリプトを実装」に更新されている |
| AC-4 | §1 | §6.5 の NFR-17 が「手動スナップショット（自動集計はオプション）」に差し替えられている |
| AC-5 | §1 | `evaluation-kpi.md` §6.2 の「Wave 2 完了前」条件分岐が削除されている |
| AC-6 | §2 | `distill()` に C-1〜C-4 全条件の空スキップが実装されている |
| AC-7 | §2 | 3 件の新規テストが追加され、既存 21 件含む全テストが PASS |
| AC-8 | §3 | commit c674ec8 の存在確認（実施済み・再実装不要） |
| AC-9 | §4 | SKILL.md Step 4 に警告ラベルが追記されている |
| AC-10 | §4 | `magi-skill.md` 参照コピーに同一文言の警告ラベルが追記されている |
| AC-11 | §4 | `future-candidates.md` に gabriel 統合設計記録が作成されている |

---

## 6. 実施フェーズと優先順

| 優先順 | 章 | 権限等級 | 実施タイミング |
|-------|----|---------|--------------|
| 1 | §1 FR-1.1〜1.5 | PM 級 | B-4 後 PLANNING 承認後・BUILDING Wave 1 |
| 2 | §2 FR-2.1〜2.4 | SE 級 | BUILDING Wave 1（§1 と並行可） |
| 3 | §3 | — | 実施済み（確認のみ） |
| 4 | §4 FR-4.1〜4.5 | PM 級 | BUILDING Wave 1（§1 と並行可） |

---

## 7. 将来候補（future-candidates）

以下は本仕様のスコープ外とし、`docs/specs/v5-fat-reduction/future-candidates.md` に記録する:

- MAGI v2（gabriel エージェント設計・ADR 新設・SKILL.md 全面改訂）: v5 ② 別マイルストーン
- distill-lessons セマンティック重複チェック（プラン C）: lessons.md エントリ 30 件超到達後に再評価
- `/full-review` Stage 1/3 の物理撤去: Plan B/C/D 復活時に判断
- `/retro` Step 4 への lessons.md 確認手順追加: v5 PLANNING 時に統合

---

## 8. Definition of Ready チェックリスト

- [x] Problem Statement が明確（fat の 4 構造パターンを定義）
- [x] Goals / Non-Goals が明記されている
- [x] 全機能要件に RFC 2119 キーワードが付与されている
- [x] 各要件に根拠（audit §章番号）が引用されている
- [x] Requirements Smells（曖昧形容詞・計測不能用語）が排除されている
- [x] 受け入れ条件（AC-1〜AC-11）がテスト可能な形式で定義されている
- [ ] タスク分解（1 PR 単位への分割）→ design/tasks フェーズで対応
