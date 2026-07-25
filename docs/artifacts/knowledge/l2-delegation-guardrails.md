# L2 委譲ガードレール（§2-4 = prompt 4 点 / §8 = 振り分け判定）

**初出**: B-5 Wave 6 Stage 3 委譲 prompt（2026-06-26）
**拡張**: 2026-07-26（§8 委譲の振り分け判定 = BUILDING 以外での失敗集中への回答）
**実証**: B-5 Wave 6 Stage 3 — L2 (tdd-developer / Sonnet) の **報告と実測の乖離 50% → 5%** を達成
**retro**: [retro-W6-B5-2026-06-27.md](../retro-W6-B5-2026-06-27.md)
**権限**: SE 級（knowledge 蓄積） / 昇格時は PM 級

---

## 1. 背景

L2 (tdd-developer / Sonnet) は実装能力に問題はないが、以下の「手順面の前提」を委譲時に明示しないと
報告精度が落ちる。B-5 Wave 6 Stage 1 + Stage 2 で同種の問題が連続発生し、Stage 3 で本ガードレールを
委譲 prompt 冒頭に組み込んだところ報告品質が大幅向上した（実測乖離 50% → 5%）。

---

## 2. ガードレール 4 点

```
1. Bash 制限前提
   権限のない Bash コマンドは試行せず、L1 に依頼すること。
   特に Windows + Git Bash 環境で pytest 全件実行・git 操作・複雑なファイル走査は L1 リレー検証で行う。

2. 緩和事前承認必須
   既存テスト・規約からの緩和（assert 文の書き換え、テスト削除、規約逸脱等）は、
   実施前に L1 へ承認依頼すること。実施後の事後報告は不可。

3. JS 行数計測法明示
   JavaScript の行数計測は 4 区分で行うこと:
     - 実装行（コード行）
     - コメント行
     - 空行
     - 合計
   SHOULD 100-150 範囲との突合は「実装行」で評価する（合計ではない）。

4. 既存テスト影響事前分析
   改修対象（HTML/CSS/JS/Python）の波及範囲を事前に列挙し、
   既存テスト破損予測を委譲時に L1 と共有すること。
```

---

## 3. 委譲 prompt テンプレ（冒頭挿入用）

L2 (tdd-developer 等) に委譲する際、prompt 冒頭に以下を挿入する:

```markdown
## 委譲ガードレール（事前合意）

実装着手前に以下 4 点を必ず確認してください:

1. **Bash 制限前提**: 権限のない Bash コマンドは試行せず、L1 に依頼する
2. **緩和事前承認必須**: 既存テスト・規約からの緩和は実施前に L1 へ承認依頼
3. **JS 行数計測法明示**: 実装行 / コメント行 / 空行 / 合計 の 4 区分で計測
4. **既存テスト影響事前分析**: 改修対象の波及範囲を事前に列挙し、破損予測を共有

完了報告時は上記 4 点の遵守状況を明示してください。
```

---

## 4. 実証メトリクス（Wave 6 Stage 別）

| Stage | 委譲構成 | L2 報告と L1 実測の乖離 | ガードレール適用 |
|:------|:--------|:---------------------|:----------------|
| Stage 1 | 単独タスク委譲 | 計測対象外 | なし |
| Stage 2 | T37+T38+T39 統合 | **50%（過大評価）** | なし |
| Stage 3 | T40+T41 統合 | **5%（破損予測完全的中）** | **本 4 点適用** |
| Stage 4 | T42 統合 | 5% 水準維持 | 本 4 点適用 |

---

## 5. 適用条件

- L2 (Sonnet 系 / tdd-developer 等) への委譲時
- 複数タスクの統合委譲時（T37+T38+T39 のような直列依存）
- BUILDING フェーズの Stage 委譲（PLANNING / AUDITING は **§8 で回答済**（2026-07-26）= 本 4 点の前に**振り分け判定**を行う）

### 適用しない場合

- L3 (Haiku / goal-driven-grader 等) の採点委譲 — 採点対象が静的で乖離リスクが低い
- L1 直作業 — 自己評価のため乖離が発生しない
- 単発の極小タスク（10 行未満の編集等） — overhead が利得を上回る

---

## 6. 関連知見

- [project_b5_w6_stage2_sort.md](../../../.claude/agent-memory/tdd-developer/project_b5_w6_stage2_sort.md) — Stage 2 の Bash 制限実態
- [project_b5_w6_stage3_filter.md](../../../.claude/agent-memory/tdd-developer/project_b5_w6_stage3_filter.md) — Stage 3 ガードレール適用後の改善実証
- [retro-W6-B5-2026-06-27.md](../retro-W6-B5-2026-06-27.md) — Wave 6 retro 全体

---

## 7. 昇格候補

本ガイドラインは knowledge 層（SE 級）で開始。以下の場合は `.claude/rules/` への昇格を検討する（PM 級）:

- Wave 7+ で 2 回以上適用され、再現性が確認された場合
- 他の subagent（design-architect / quality-auditor 等）への委譲でも同様の問題が発生し、汎用化の必要性が出た場合 → **2026-07-26 充足**（§8.1 / R-1・R-2・M-1 で design-architect / code-reviewer / 汎用 Sonnet に同型の失敗）
- 委譲 prompt テンプレが恒久的なプロセスとして定着した場合

> 昇格の受け皿は `.claude/rules/model-delegation-prompting.md`。M-1 の閉集合制約により条項化は M-1 完了後の別 Milestone で行う（`retro-M1-W1-2026-07-25.md` §6.2 の A2 / A4）。

---

## 8. 委譲の振り分け判定（2026-07-26 追記 / §5「PLANNING / AUDITING には別途検討」への回答）

§2-4 は「委譲するとき**どう書くか**」。本節は「そもそも**何を委譲するか**」を扱う。

### 8.1 実測 — 成功と失敗は BUILDING / それ以外で分かれる

| 委譲 | 結果 | 出典 |
|:--|:--|:--|
| tdd-developer ×7 / grader ×4（B-5 W7） | 全 Stage 完走 | `retro-W7-B5-2026-06-28.md` |
| L2 実装（B-5 W6 / 本ガードレール適用） | 乖離 **50% → 5%** | §4 |
| 2 段 Sonnet（grep triage → rewriter） | 82 hits / 20 files を **L1 手作業ゼロ**で完遂 | `retro-R1-W4-S3-2026-07-13.md` |
| 条項抽出（M-1 W1-T1） | 5 種の適用漏れ / 92 → 106 に L1 補修 | `retro-M1-W1-2026-07-25.md` P2 |
| 設計書執筆（R-2 W1-T5） | 実行すれば必ず落ちるコードを設計書に埋込 | `retro-R2-W1-M1-PLANNING-2026-07-25.md` K1 / P2 |
| 監査（R-1 W1 S1S2） | 生指摘の **25〜50%** が棄却・降格 | `retro-R1-W1-S1S2-2026-07-06.md` |
| skill 仕様判定（R1-016）/ テスト有無（R1-I10） | ローカル文書を公式スキーマと誤認 / 片側しか探さず誤報 | 同上 |

### 8.2 分岐軸 = 成果物の外に不動点があるか

「実装 vs 調査」でも「Sonnet vs Haiku」でもない。**完了条件を外形的に検証できる不動点が成果物の外にあるか**で分かれる。

- テストが落ちる（TDD）/ 件数が合わない（一括書換）/ rubric がある（採点）→ **漏れは必ず捕まる**
- 抽出・判定・設計・監査 → **正解が外にない**。何が漏れているかは、漏れを知っている人にしか分からない

memory `self-verification-scope-limit`（自己検証は自分の理解の内側でしか働かない）の**委譲版**。subagent の自己検証も自分の理解の内側でしか働かないため、brief に不動点がなければ漏れは誰にも検出されずに成果物となる。

### 8.3 なぜそうなるか

1. **委譲は文脈の切断**。L1 が積んだセッション経緯は渡らず、subagent は「知らないことを知らない」ので質問も警告も出ない。R-2 のスキーマ誤りでは、参照すべき文書は**同日に自分たちが更新したファイル**だった（L1 に自明すぎて brief に書かれなかった）
2. **LAM は判断が本体で手数が少ない**。委譲が最も効く「判断は済み・手数だけ膨大」という形の仕事が構造的に少なく、M-1 W1 に至っては Wave まるごと判定
3. **Sonnet 5 のリテラル解釈**（`model-delegation-prompting.md` §1 デルタ 1）。M-1 P5 の条項再採番は「同一列挙内で一部だけ抽出しない」を書かなかった結果

### 8.4 処方

1. **F0 の「検証方法」を委譲可否の判定に流用する**（`phase-rules.md` BUILDING §F0）。実コマンドが 1 行書けたら委譲可、書けなければ L1 直。**新しい判定軸を作らない**
2. **不動点がなければ人工的に作って渡す**。期待件数 / spec が名指しする ID の全列挙 / 突合 grep コマンド。M-1 T1 なら「design §5.2 が名指す候補 ID が表に全部あるか」を boundaries に入れれば、最重要の漏れは subagent 側で自己検出できた
3. **検収を工程として計上する**。委譲は**検収込みで 1 工程**。所要見込みに含めて提示する

### 8.5 誤診への注意

- 失敗率が高く見える主因は、検収込みで 1 工程のものを**委譲単体で完成すると期待している**こと。M-1 K3・R-1 の監督工程はいずれも実際に穴を捕捉しており、設計どおりに動いている
- **3.5 層構造は壊れていない**（§8.1 上段が実証）。壊れているのは**振り分けと見積り**
- 観測不能性（M-1 P1 / transcript 22 分 0 バイト → `TaskStop` の 10 秒後に成果物）は subagent の品質問題ではない。混ぜて評価しないこと。ただし **2026-07-26 訂正 = harness 側の制約で終わりではなく回避策がある**: transcript を監視するのが誤りで、**進捗を成果物側に書かせれば外形観測できる**（N 件ごとの追記 / 逐次 commit）。次回の委譲から boundaries に「N 件ごとに進捗を追記せよ」を入れる（§8.6 / Anthropic「Effective harnesses」の実装と同型）

### 8.6 外部知見との突合（2026-07-26 調査）

| 出典 | LAM への含意 |
|:--|:--|
| **MAST**（arXiv 2503.13657 / NeurIPS 2025 / 7 フレームワーク・1,600+ トレース・14 failure mode） | Verification 系が全失敗の **28%**。LAM 実測がそのまま該当 → **FM-10** Missing Required Information（R-2 スキーマ未添付）/ **FM-11** Premature Termination（92 条項で完了報告・`TaskStop` 誤爆）/ **FM-12** Incorrect Verification（R1-I10 片側探索で誤報）/ **FM-13** Incomplete Verification（5 種の適用漏れ）。決定的な知見は「**プロンプト強化とエージェント構成の改善では失敗は解消しなかった**」= §2-4 型の対策には天井がある。§8.4 処方 1（振り分けを変える）を優先する根拠 |
| **Cognition「Don't Build Multi-Agents」** | 原理 (1) full agent trace を共有せよ（individual message では不足）/ (2) 行動は暗黙の決定を運び、決定が食い違えば結果も壊れる。§8.3-1 と同診断だが処方はより厳しく、**brief 主義そのものへの異論**。「Claude Code の並列サブタスクが成立するのは質問に答えるだけで並列にコードを書かないから」= LAM の失敗例が全て「書込を伴い検証が外にない」委譲だったことと整合 |
| **Anthropic「multi-agent research system」** | 既引用（+90.2% / tight brief）だが**未引用部が重要** — 「全エージェントが同一コンテキストを共有する領域・エージェント間依存が多い領域は不向き」「**コーディングは research より真に並列化できるタスクが少ないため不向き**」。一方 LAM の成功例（grep triage → rewriter / module 分割監査）は公式が best fit とする breadth-first 並列探索と一致 → **3.5 層は「並列探索に効き逐次判断に効かない」で首尾一貫**（構造の否定ではない） |
| **Anthropic「Effective harnesses for long-running agents」** | 「完了の自己申告は信用できない（進捗を少し観測しただけで **declare the job done** する）」→ 対策は **pass/fail 状態を持つ明示的な feature list ファイル**でエージェント判断に依存しない = §8.4 処方 2 と同一結論に公式実装が到達。進捗記録と git 履歴は「**エージェントではなく harness が**」レビューする |

**引用の偏りに注意**: `hga-summoning.md` は Anthropic 推進側のみを引用している。Cognition と Anthropic は 24 時間差で正反対の立場を公開した対であり、MAST は両者に対する実証的な第三の視点。片側だけを根拠にしないこと。

**URL**: `arxiv.org/abs/2503.13657` / `cognition.com/blog/dont-build-multi-agents` / `anthropic.com/engineering/multi-agent-research-system` / `anthropic.com/engineering/effective-harnesses-for-long-running-agents`
