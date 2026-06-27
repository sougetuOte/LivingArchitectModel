# MAGI 議事録 — Wave 7 Stage 1 構造的乖離 Pivot 判断

- 日付: 2026-06-27
- セッション: B-5 Wave 7 BUILDING Stage 1（T45 完了直後）
- 起動契機: T45 pytest 実行で `test_parse_real_specs_directory_returns_at_least_one_task` 想定外 FAIL → 実 tasks.md と新 regex の構造的乖離を発見
- 出席: MELCHIOR / BALTHASAR / CASPAR（書記）
- 関連: [2026-06-27 Wave 7 PLANNING MAGI 議事録](2026-06-27-magi-wave7-planning.md)
- 補追対象: requirements.md / design.md / tasks.md v0.2.1 → v0.2.2

---

## 1. 議題

design.md §6 新 regex 仕様 `^(W\d+(?:\.\d+)?-[A-Z]\d+-T\d+|T\d+):` と、実 docs/specs/ 配下 tasks.md の運用実態が乖離しており、新 regex 適用後に V-4 Task 一覧が空になることが判明。Wave 7 BUILDING を継続するかどうかの方針判断。

### 発覚した事実（Grep + pytest 実測）

| パターン | 件数 | 例 |
|:---|:---:|:---|
| `- [x] W{n}-T{n} ...`（コロンなし / Milestone 部分なし） | 4 | goal-driven-orchestration/tasks.md L640-L641, L642, L751 |
| `- [ ] T{n} ...`（コロンなし） | 2 | b4-dashboard/wave6/tasks.md L240-L241 |
| `- [ ] **...**:`（太字記法） | 46 | Wave 7 tasks.md 含む 5 ファイル |
| その他文章チェックボックス | 548 | — |
| **新 regex マッチ可能** | **0** | — |

→ Wave 7 PLANNING で確定した「誤抽出 378 件 → 0 件」目標は、実態としては「**V-4 Task 一覧も同時に空になる**」副作用を持つ。spec-critic 3 回独立レビュー（C → B → B → A 想定）でも検出されなかった盲点。

---

## 2. AoT Decomposition

| Atom | 判断内容 | 依存 |
|:-----|:---------|:-----|
| A1 | 仕様と運用の収束方式 | なし |
| A2 | 太字記法 `**ID**:` の扱い | A1 |
| A3 | T45 実装の扱い | A1 |
| A4 | Wave 7 残スコープ + tasks.md 運用 | A1〜A3 |

### 提示された選択肢

- A: スコープ縮小（regex 厳格化のみ完結 / V-4 有用性 Wave 8+ 送り）
- B: tasks.md 運用変更（既存 600 行を新規格に書き直し）
- C: regex 緩和（コロン optional + Milestone optional + 太字記法対応）
- D: V-4 廃止（Task ID 抽出機能再設計）
- E: 太字記法のみ許容（`^(?:\*+\s*)?(W\d+...)`）

---

## 3. Atom A1: 仕様と運用の収束方式

**[MELCHIOR]**:
- B 案で実 tasks.md を terminology.md §2 規約に統一すれば、プロジェクト全体の規約適用が一気に進む
- C/E 案の regex 緩和なら 1 セッション内完結
- 規約と実装が一致した状態で初めて V-4 が意味を持つ

**[BALTHASAR]**:
- B 案は **terminology.md §5 移行猶予条項（2026-06-20 前のファイル旧表記維持可）に違反**
- C/E 案は「過去の旧形式を取り込む」ことになり、将来の統一を阻害する技術的負債
- 根本原因は「実 tasks.md の現状を確認せず仕様を立てたこと」— spec-critic 3 回でも検出できなかった構造的盲点
- 仕様再読: requirements.md FR-W7-1 / AC-W7-1 を読み直すと **「誤抽出ゼロ化」は目標化されているが、「V-4 が意味のある Task ID を表示する」は目標化されていない**

**[CASPAR]**: 結論: **A 案（スコープ縮小）寄り** で確定。
1. Wave 7 の正式目標（FR-W7-1 / AC-W7-1）は「誤抽出ゼロ化」のみ。V-4 表示有用性は仕様外
2. terminology.md §5 移行猶予条項を遵守（B 案は条項違反で却下）
3. C/E 案の regex 緩和は技術的負債を増やすため却下
4. 「V-4 が空になる」事実は知見として記録し、Wave 8+ で別途設計

→ **A1 結論: A 案 / 現 T45 regex 維持 / V-4 有用性は Wave 8+ 送り**

---

## 4. Atom A2: 太字記法の扱い

**[MELCHIOR]**:
- 太字記法 `**T-S1-1**:` を許容すれば Wave 7 自身の T-S* 検証タスクも V-4 表示できる
- regex 微調整で対応可能

**[BALTHASAR]**:
- design.md §2 で「T-S* は TasksParser 抽出対象外」明示済（spec-critic 指摘 #I-4 への対応）。太字許容はこれを無効化
- T-S* と T-N* の区別ロジックは現実装で意図的仕様（`T-S` で 2 文字目が `-` → 不一致）。太字許容なら別弁別ルールが必要 → 仕様複雑化
- A1 で A 案を選んだ以上、A2 で太字許容は **A1 結論を骨抜きにする矛盾**

**[CASPAR]**: 結論: **太字記法は許容しない**。
1. A1 と一貫性維持
2. design.md §2 / spec-critic #I-4 と整合
3. T-S* 検証タスクは tasks.md チェックボックス管理に閉じる（現仕様維持）

→ **A2 結論: 太字記法非対応 / 現 regex 維持**

---

## 5. Atom A3: T45 実装の扱い

**[MELCHIOR]**:
- T45 実装は design.md §6 仕様通り完璧（新 regex + フォールバック削除 + テスト 4 件 = pytest 26 PASS / 新規 4 件全 PASS）
- A1 で A 案を選んだ → T45 実装はそのまま使える / 破棄は無駄

**[BALTHASAR]**:
- T45 適用後 V-4 が空。Wave 6 では誤抽出 378 件で埋まっていた → **ユーザー体験的に「機能後退」と捉えられるリスク**
- `test_parse_real_specs_directory_returns_at_least_one_task` (L508) は実 specs が変わらない限り FAIL のまま
- 「Wave 7 で V-4 が機能しなくなった」と誤解されないよう SESSION_STATE / retro / CHANGELOG で明示必要

**[CASPAR]**: 結論: **T45 実装は保持**。ただし以下を T46 に含める:
1. L508 を「0 件返却を許容」仕様に書き換え（または skip + reason）
2. L275 fixture を `W1-B5-T1` 形式に統一（T44 質問 1 既定承認）
3. design.md §6 に補足セクション追加: 「実 tasks.md マッチ 0 件は Wave 7 仕様通り。V-4 表示は Wave 8+ 再設計予定」
4. SESSION_STATE.md / retro で「V-4 機能後退」リスクを明示

→ **A3 結論: T45 実装保持 / T46 拡張（L275 fixture + L508 仕様調整 + design.md §6 補足）**

---

## 6. Atom A4: Wave 7 残スコープ + tasks.md 運用

**[MELCHIOR]**:
- Stage 2（Assignee）/ Stage 3（複数 Milestone）は Stage 1 と独立。計画通り進行可能
- Wave 7 全体価値は維持

**[BALTHASAR]**:
- V-4 が空のまま Stage 2 を実装しても **AC-W7-3（`-` 以外の Assignee 値 ≥ 1 件表示）が達成不能**
- Wave 7 全体の DoD が「V-4 機能後退状態で完了」となる

**[CASPAR]**: 結論: **Stage 2/3/4 継続 + Wave 7 tasks.md パイロット運用**。
- Stage 2 の AC-W7-3 達成のため、**Wave 7 tasks.md 自身を新規格に書き直すパイロット運用** を導入
- 具体: 表内 T44-T55 → `- [ ] W7-B5-T44: 既存テスト構造変更影響分析 @sonnet` 形式に変換（表形式と並存も可）
- T-S* 検証タスクは現仕様通り（太字記法 / 抽出対象外）
- terminology.md §5 移行猶予条項に従い、Wave 6 以前は旧表記維持
- これにより V-4 に Wave 7 Task ID 行が表示 → AC-W7-3 検証可能

→ **A4 結論: Stage 2/3/4 継続 / Wave 7 tasks.md のみパイロット運用で新規格化 / Wave 6 以前は猶予条項で旧表記維持**

---

## 7. Reflection

致命的な見落とし確認:

| 観点 | 判定 |
|:----|:----|
| terminology.md §5 違反 | A1/A2 で対処済（移行猶予条項遵守） |
| データ損失 | 該当なし（T45 実装保持 + 旧 regex 復元可能） |
| 仕様違反 | A4 の運用変更は requirements/design/tasks v0.2.2 補追が必要（PM 級 1 回承認で済む / Wave 7 内完結） |
| セキュリティ | 該当なし |
| 未確認事項 | v0.2.2 補追を spec-critic 4 回目レビューに掛けるか（盲点検証の価値あり） — これは PM 級判断、本 MAGI 結論には影響しない |

**致命的な見落とし**: **なし** → 結論確定

---

## 8. AoT Synthesis（統合結論）

| 項目 | 決定 |
|:-----|:-----|
| regex 仕様 | 現 T45 実装維持（厳格化 + フォールバック削除） |
| 太字記法 | 非対応（design.md §2 維持） |
| T45 実装 | 保持 |
| 既存テスト緩和 | L275 fixture 統一 + L508 仕様調整 + design.md §6 補足追加 |
| Wave 7 tasks.md | パイロット運用で新規格チェックボックス化（T44-T55 のみ） |
| Wave 6 以前 tasks.md | 移行猶予条項に従い旧表記維持 |
| Stage 2/3/4 | 継続（Wave 7 パイロットにより AC-W7-3 検証可能化） |
| Wave 8+ 候補 | 既存 tasks.md の新規格統一 + V-4 表示有用性の本格設計 |

### Action Items

1. **A-1 (PM)**: ユーザーに本 MAGI 結論を提示し、v0.2.2 補追の承認を仰ぐ ✅ 承認済（2026-06-27）
2. **A-2 (PM)**: v0.2.2 補追内容:
   - requirements.md: NFR-W7-5「Wave 7 tasks.md は新規格チェックボックス形式を採用（パイロット運用）」追加
   - design.md: §10「tasks.md パイロット運用ルール」追加 + §6 補足「実 tasks.md マッチ 0 件は仕様通り / Wave 8+ 本格設計予定」
   - tasks.md: 表内 T44-T55 をチェックボックス形式に変換 + Assignee `@sonnet` 等付与 + 改訂履歴 v0.2.2 追記
3. **A-3 (PM 判断)**: v0.2.2 補追を spec-critic 4 回目レビューに掛けるか（推奨: 盲点検証）
4. **A-4 (SE)**: T46 着手（L275 fixture 統一 + L508 仕様調整 + design.md §6 補足追記）
5. **A-5 (PG)**: 本議事録保存 ✅ 完了（2026-06-27）
6. **A-6 (PG)**: SESSION_STATE.md 更新（次セッション引継ぎ）

---

## 9. 次の判断ポイント

- spec-critic 4 回目レビューを起動するか（A-3）
- T46 着手前に v0.2.2 補追を完了するか / T46 → 補追の順か（補追 → T46 を推奨）

## 10. 教訓（Wave 7 retro 起票用）

- **spec-critic の限界**: 文書内整合性は検出するが、**実データとの整合性は検出しない**。今後は PLANNING フェーズで「実データ照合」ステップを追加すべき（Wave 7 retro Try 候補）
- **upstream-first の拡張案**: 設計段階で「実 tasks.md の現状サンプリング」を必須化する upstream-first の派生ルール検討（PM 級候補）
- **MAGI Reflection の有効性**: 本セッションの MAGI 合議で「V-4 表示有用性は requirements に目標化されていない」を BALTHASAR が指摘 → A1 結論を A 案に確定できた。Reflection なしなら C 案（regex 緩和）に流れ込み技術的負債を抱えた可能性
