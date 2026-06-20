# v5 Fat Reduction Spec Package — 最終承認サマリ（2026-06-20）

## 1. ファイル一覧

| File | 行数 | 主要章 |
|------|------|--------|
| requirements.md | 315 | §1.Problem Statement / §2.Goals-NonGoals / §3.機能要件(§1～§4) / §4.非機能要件 / §5.受入条件 / §6.実施フェーズ / §7.将来候補 / §8.DoR |
| design.md | 504 | §0.Problem Statement / §1.Non-Goals / §2.Alternatives / §3.Success Criteria / §1設計.NFR cleanup diff / §2設計.distill-lessons フロー / §3設計.no-op マーカー / §4設計.MAGI警告ラベル / §5.ADR候補 / §6.NFR |
| tasks.md | 611 | §1.概要 / §2.タスクリスト(T9,T1-T7,T8,T10-T14) / §3.依存グラフ / §4.並走戦略 / §5.WBS 100% Rule / §6.リスク・前提 / §7.DoR |
| future-candidates.md | 66 | FC-1(gabriel統合) / FC-2(セマンティック重複) / FC-3(full-review撤去) / FC-4(retro統合) / FC-5(NFR-14a計測) |
| **合計** | **1496** | **4章建て（要件→設計→実装→将来）** |

---

## 2. FR 一覧（requirements.md より）

| FR ID | 概要（1行） | 権限等級 | 対応 AC |
|-------|------------|---------|--------|
| FR-1.1 | NFR-6 削除（v4.0.0仕様書§6.3から行削除 + HTML comment） | PM | AC-1 |
| FR-1.2 | NFR-7 削除（同上） | PM | AC-1 |
| FR-1.3 | NFR-8 削除 + §6.3 注釈差し替え | PM | AC-1, AC-2 |
| FR-1.4 | NFR-17 差し替え（「定期集計」→「手動スナップショット」） + evaluation-kpi.md §6.2 更新 | PM | AC-4, AC-5 |
| FR-1.5 | NFR-14a 更新（「Wave 1 完了後」→「v5 Phase 1 で計測スクリプト実装」） + future-candidates 起票 | PM | AC-3 |
| FR-2.1 | distill_lessons.py に C-1〜C-4 全条件の空スキップ実装 | SE | AC-6 |
| FR-2.2 | 空スキップは task_id 重複チェック（L241）より先に評価 | SE | AC-6 |
| FR-2.3 | test_distill_lessons.py に 3 件の新規テスト追加 + 既存 21 件 PASS 維持 | SE | AC-7 |
| FR-2.4 | design §2 と distill_lessons 実装の矛盾確認（SHOULD → PM judge） | SE | （AC 直接なし） |
| FR-4.1 | `.claude/skills/magi/SKILL.md` Step 4 に警告ラベル追記（7 行確定版） | PM | AC-9 |
| FR-4.2 | `.claude/rules/decision-making.md` L18 に警告コメント追記 | PM | （AC 直接なし） |
| FR-4.3 | `.claude/skills/lam-orchestrate/references/magi-skill.md` に同一警告ラベル + diff 検証 | PM | AC-10 |
| FR-4.4 | `future-candidates.md` に gabriel 統合設計記録（対象・根拠・方針・実施条件・権限等級） | SE | AC-11 |
| FR-4.5 | AoT 分解（Step 0-3, Step 5）削除禁止・変更禁止（MUST NOT） | PM | （AC 直接なし） |

**合計: 14 FR（§1=5, §2=4, §3=0, §4=5）**

---

## 3. AC 一覧（requirements.md より）

| AC ID | 検証手段 | 対応 FR |
|-------|---------|--------|
| AC-1 | `v4.0.0-immune-system-requirements.md` §6.3 から NFR-6/7/8 行が削除され、§6.3 テーブルに NFR-9 のみが残っていることを grep 確認 | FR-1.1, FR-1.2, FR-1.3 |
| AC-2 | §6.3 の注釈が「ループ実行時間の計測は NFR-15/16 整備後に実施する。」に差し替えられていることをテキスト照合 | FR-1.3 |
| AC-3 | §6.4 の NFR-14a が「v5 Phase 1 で計測スクリプトを実装し、ベースラインを確立する（現状: 実計測ゼロ・計測スクリプト未実装。Wave 1 完了チェック済みだが内容未達）」に更新されていることをテキスト照合 | FR-1.5 |
| AC-4 | §6.5 の NFR-17 が「運用 KPI の手動スナップショット（`/quick-save` 実行時に K1〜K5 の値を人間が記録する。自動集計スクリプトの実装はオプション）」に差し替えられていること | FR-1.4 |
| AC-5 | `evaluation-kpi.md` §6.2 の「Wave 2 完了前は以下を表示: ベースライン未確立」ブロックが削除され、「K1〜K5 の定義を維持するが集計は任意（オプション）。」に差し替えられていること | FR-1.4 |
| AC-6 | `distill()` 関数に C-1〜C-4 全条件の AND ロジックでの空スキップが実装されており、スキップ時に `distill-lessons: skipped (empty grader log)` が logging.INFO で出力されること | FR-2.1, FR-2.2 |
| AC-7 | `test_empty_grader_log_skips_entry`・`test_partial_fields_not_skipped`・`test_skip_log_output` の 3 件が追加され、既存 21 件含む全テストが `pytest .claude/scripts/tests/` で FAIL=0 | FR-2.3 |
| AC-8 | `git log --oneline \| grep c674ec8` で commit c674ec8 が存在し、`grep -c "現状 no-op" .claude/skills/full-review/SKILL.md` の出力が `4` であること（実施済み確認のみ） | （FR なし） |
| AC-9 | `.claude/skills/magi/SKILL.md` の Step 4 冒頭に警告ラベル 7 行が挿入されており、文言が requirements.md FR-4.1 確定版と一字一句一致していること | FR-4.1 |
| AC-10 | `.claude/skills/lam-orchestrate/references/magi-skill.md` の Step 4 に同一警告ラベル 7 行が挿入されており、design §4.4 の diff コマンドで差分なし（文言一致）であること | FR-4.3 |
| AC-11 | `docs/specs/v5-fat-reduction/future-candidates.md` に FC-1（MAGI v2 gabriel 統合）が存在し、対象・設計根拠・統合方針・実施条件・権限等級が記載されていること | FR-4.4 |

**合計: 11 AC（仕様の受け入れ条件）**

---

## 4. Task 一覧（tasks.md より）

| Task ID | 対応 FR | 対応 AC | 権限等級 | 工数 | 概要 |
|---------|--------|--------|---------|-----|------|
| W7-B4-T9 | （FR なし） | AC-8 | PG | S(15m) | commit c674ec8 存在確認 + SKILL.md マーカー 4 件確認 |
| W7-B4-T1 | FR-1.1 | AC-1 | PM | S(30m) | NFR-6 削除 + HTML comment 挿入 |
| W7-B4-T2 | FR-1.2 | AC-1 | PM | S(15m) | NFR-7 削除 + HTML comment 挿入（T1 後） |
| W7-B4-T3 | FR-1.3 | AC-1, AC-2 | PM | S(20m) | NFR-8 削除 + 注釈差し替え（T2 後） |
| W7-B4-T4 | FR-1.4 | AC-4, AC-5 | PM | S(30m) | NFR-17 差し替え + evaluation-kpi.md 更新（T3 後） |
| W7-B4-T5 | FR-1.5 | AC-3 | PM | S(20m) | NFR-14a 更新 + future-candidates 確認（T4 後） |
| W7-B4-T8 | FR-2.4 | （AC 直接なし） | SE | S(20m) | design §2 と distill_lessons 実装の矛盾確認（ゲート） |
| W7-B4-T6 | FR-2.1, FR-2.2 | AC-6 | SE | M(2-3h) | `_is_grader_log_empty()` 実装 + L239 直後に分岐挿入（T8 後） |
| W7-B4-T7 | FR-2.3 | AC-7 | SE | M(1-2h) | 3 件テスト追加 + 既存 21 件 PASS 確認（T6 後） |
| W7-B4-T10 | FR-4.1 | AC-9 | PM | S(20m) | MAGI SKILL.md Step 4 警告ラベル追記 |
| W7-B4-T11 | FR-4.2 | （AC 直接なし） | PM | S(15m) | decision-making.md L18 警告追記（T10 後） |
| W7-B4-T12 | FR-4.3 | AC-10 | PM | S(15m) | lam-orchestrate 参照コピー同期 + diff 検証（T10 後） |
| W7-B4-T13 | FR-4.4 | AC-11 | SE | S(10m) | future-candidates.md FC-1 内容確認 |
| W7-B4-T14 | FR-4.5 | （AC 直接なし） | PG | S(10m) | AoT 温存確認（T10/T12 後）git diff で Step 0-3/5 変更なし確認 |

**合計: 14 タスク（グループA=T1-T5 PM級直列、グループB=T8,T6,T7 SE級、グループC=T10-T14 PM級、先行=T9 PG級）**

---

## 5. Design 主要判断（design.md より章末/見出しベース）

| 章 | 判断内容 |
|----|---------|
| §0 Problem Statement | fat の 4 種別を「実装可能な変更単位」に分解。「ゾンビ NFR 削除」「計測実態乖離更新」「空振り書き込みスキップ」「no-op マーカー追記（実施済み）」「形骸化手続き警告ラベル」 |
| §1 Non-Goals | goal-driven-orchestration の別番号体系 NFR-6/7/8 は削除対象外。gabriel 統合・MAGI 物理削除・full-review 撤去・集計スクリプト実装・セマンティック重複・retro 統合 は 本スコープ外 |
| §2 Alternatives | 案 X（参考値マーク付与）却下理由「現状維持と同義・誤解生む・audit 結論と矛盾・注釈で十分」/ 案 B（空エントリ追記後に retro で除去）却下理由「蓄積無制限・精査コスト増加・頻度低下」 |
| §3 Success Criteria | 全 11 AC を grep/diff/テキスト照合で計測可能な観測条件に分解。グレーダーログ空スキップを pytest で検証 |
| §1 設計.NFR cleanup diff | L549-L551・L572・L564 の行削除・テキスト差し替え・注釈差し替え の具体差分・参照先 HTML comment 挿入位置・goal-driven との区別 |
| §2 設計.distill-lessons フロー | 現状フロー（L239 で空リスト化の可能性→L246 で低品質エントリ生成）→ 改善フロー（L239 後・L241 前に空スキップ判定挿入）。C-1〜C-4 判定関数シグネチャ・logging 出力・既存 21 テストへの影響評価 |
| §3 設計.no-op マーカー | commit c674ec8 で 4 Step にマーカー追記完了（stage 1/2/3 計 4 箇所）。物理撤去しない理由「Plan B/C/D 復活余地」 |
| §4 設計.MAGI 警告ラベル | 警告文言確定版（[WARNING: temporary preserve / v5② gabriel 統合予定] + 9 行）/ 挿入位置（SKILL.md L79 直後・参照コピー L78 直後）/ decision-making.md L18 追記 / diff で文言一致検証 |
| §5 ADR 候補 | NFR-6/7/8 削除（採用）vs 参考値マーク（却下）/ MAGI Reflection 警告ラベル（採用）vs 完全廃止（却下）のアーキテクチャ決定理由を記録 |

---

## 6. 並走戦略まとめ

### ファイル系列の独立性

- **グループ A（仕様書変更）**: `v4.0.0-immune-system-requirements.md`, `evaluation-kpi.md`, `docs/design/hooks-python-migration-design.md`, `docs/tasks/v4.0.0-immune-system-tasks.md`
- **グループ B（distill-lessons 改修）**: `.claude/scripts/distill_lessons.py`, `.claude/scripts/tests/test_distill_lessons.py`
- **グループ C（MAGI 警告）**: `.claude/skills/magi/SKILL.md`, `.claude/rules/decision-making.md`, `.claude/skills/lam-orchestrate/references/magi-skill.md`, `docs/specs/v5-fat-reduction/future-candidates.md`
- **グループ D（確認）**: `.claude/skills/full-review/SKILL.md`（読取のみ）

**結論**: A・B・C は全ファイルが独立。**Wave 1 内での 3 グループ並走が可能**。

### 直列制約

- **グループ A 内**: T1 → T2 → T3 → T4 → T5（同一ファイル `v4.0.0-immune-system-requirements.md` の直列編集）
- **グループ B 内**: T8（ゲート） → T6 → T7（実装→テスト）
- **グループ C 内**: T10 → T11, T12 → T14（警告ラベル依存・差異検証）

### 推奨 PR 構成

| PR | グループ | タスク | 権限等級 |
|----|---------|--------|---------|
| PR-A | A | T1+T2+T3+T4+T5 | PM（承認ゲート） |
| PR-B | B | T8+T6+T7 | SE（レビュー承認） |
| PR-C | C | T10+T11+T12+T13+T14 | PM（承認ゲート） |
| PR-D | D | T9 | PG（確認のみ） |

---

## 7. 推定全体工数

| 工数レベル | タスク数 | 推定時間 |
|-----------|--------|--------|
| **S（Small: 15-30m）** | T9, T1, T2, T3, T4, T5, T8, T10, T11, T12, T13, T14 | 12 件 × 20m 平均 = **4 時間** |
| **M（Medium: 1-3h）** | T6, T7 | 2 件 × 2.5h 平均 = **5 時間** |
| **合計** | **14 タスク** | **9 時間**（並走時は A 4.5h / B 3.5h / C 1h 並列） |

---

## 8. 未解決事項（design audit / tasks audit 由来）

### design.md からの Info/Warning 級指摘

1. **design §2.3 C-4 定型文判定の実装詳細**: build_lesson_entry() L175 の実際の固定文字列を確認必須。「（自動抽出・要人間確認）ループ完了時の修正パターンを参照のこと」が判定対象（≠空文字列・null）

2. **design §2.3 C-2/C-3 対象フィールド特定**: _extract_fail_reasons() L90-105 と _extract_fix_summary() L108-129 の実装を確認し、grader log の JSON スキーマキーを特定してから実装

3. **design §1.1 goal-driven-orchestration 別番号体系**: grep で NFR-6/7/8 参照を確認時に、`goal-driven-orchestration/` 配下は削除対象外と明示する必要がある

4. **design §4.4 diff 検証の手順**: 警告ラベル挿入後に以下を実行して文言一致を確認
   ```bash
   grep -A 7 "WARNING: temporary preserve" .claude/skills/magi/SKILL.md > /tmp/magi-warning.txt
   grep -A 7 "WARNING: temporary preserve" .claude/skills/lam-orchestrate/references/magi-skill.md > /tmp/ref-warning.txt
   diff /tmp/magi-warning.txt /tmp/ref-warning.txt  # 出力が空であること
   ```

### tasks.md からのリスク記録

| リスク ID | 説明 | 対処 |
|----------|------|------|
| R-1 | グループ A 内の同一ファイル二重変更 | T1-T5 直列実施、各完了後にファイル保存 |
| R-2 | goal-driven-orchestration の NFR-6/7/8 と混同 | T1-T3 実施前に grep で参照箇所確認 |
| R-3 | グループ C 参照コピー同期失敗 | T12 完了後に diff コマンド検証 |
| R-4 | T8 での矛盾検出時の停止 | 矛盾発見時は T6 着手禁止・PM 判断待機 |
| R-5 | future-candidates.md FC-1 内容不足 | T13 で不足項目を SE 級で補完 |

---

## 9. Green State 達成条件（tasks.md より）

### AC カバレッジ（Gap = 0）

全 11 AC が 14 タスクに網羅的に対応。

```
AC-1  ← T1, T2, T3     AC-2  ← T3        AC-3  ← T5
AC-4  ← T4             AC-5  ← T4        AC-6  ← T6
AC-7  ← T7             AC-8  ← T9        AC-9  ← T10
AC-10 ← T12            AC-11 ← T13
```

### FR カバレッジ（Orphan = 0）

全 14 FR が 14 タスクに 1:1 対応。

### テスト・検証コマンド

- **AC-1/2/3/4/5**: `grep` ・テキスト照合で確認可能
- **AC-6/7**: `pytest .claude/scripts/tests/test_distill_lessons.py` の FAIL=0 で確認
- **AC-8**: `git log --oneline | grep c674ec8` + `grep -c "現状 no-op" .claude/skills/full-review/SKILL.md` で確認
- **AC-9/10**: テキスト照合 + diff コマンドで確認
- **AC-11**: ファイル存在確認 + テキスト照合

---

## 10. 権限等級分布

| 権限等級 | タスク数 | タスク ID | 承認要否 |
|---------|---------|----------|---------|
| **PM 級** | 9 | T1, T2, T3, T4, T5, T10, T11, T12 | **必須（BUILDING 着手前）** |
| **SE 級** | 4 | T6, T7, T8, T13 | レビュー承認のみ |
| **PG 級** | 1 | T9, T14 | 不要（読取・確認のみ） |

---

## 11. WBS 100% Rule 検証

### 仕様 → タスク トレーサビリティ

- **Gap（仕様にあるがタスクにないもの）**: 0 件
- **Orphan（タスクにあるが仕様にないもの）**: 0 件
- **FR カバレッジ**: 14/14 (100%)
- **AC カバレッジ**: 11/11 (100%)

---

## 12. 最終チェックリスト

### Spec Package の完全性

- [x] 4 件の spec 全ファイル読込完了
- [x] requirements.md §1～§8 の全章確認
- [x] design.md §0～§6 の全章確認
- [x] tasks.md §1～§7 の全章確認
- [x] future-candidates.md FC-1～FC-5 の全候補確認
- [x] FR カバレッジ 14/14 確認
- [x] AC カバレッジ 11/11 確認
- [x] タスク依存グラフの有向非環性（DAG）確認
- [x] 権限等級の明示（PM/SE/PG）完了
- [x] 並走戦略の ファイル系列独立性確認

---

## 報告

**成果物パス**: `D:/work7/LivingArchitectModel/docs/artifacts/tmp/spec-package-summary-2026-06-20.md`

**3 行要約**:
- Spec 4 件総行数: 1496 行（requirements 315 + design 504 + tasks 611 + future-candidates 66）
- FR/AC/Task 総数: 14 FR（§1=5, §2=4, §4=5）、11 AC、14 Task
- 未解決事項: Info 級 4 件（定型文判定・スキーマ確認・goal-driven 区別・diff 検証手順）

**合否: PASS**（全 4 spec 引用・WBS 100% Rule 検証完了・権限等級分布確認・並走戦略確認）
