# MAGI 合議記録 — R-1 PLANNING 冒頭 4 Atom

- 日付: 2026-07-05
- モード: **AoT 適用モード**（判断ポイント 4 / 影響レイヤー 4+ / 選択肢 3）
- 議題: R-1 Milestone (大規模レビュー & リファクタリング) の PLANNING 冒頭方針確定
- 実施者: L1 (Opus 4.7 / セッション `84742b87`)
- 参照計画書: `docs/artifacts/future-large-scale-review-plan-2026-07-05.md`
- 単独書込者 (CASPAR): L1
- gabriel probe: **世界初 real-world 発火機会** — メトリクス収集開始点

---

## Step 0: AoT Decomposition

| Atom | 判断内容 | 依存 |
|:-----|:---------|:-----|
| A1 | 監査スコープ形式 (widescan / layered / hybrid) | なし |
| A2 | リファクタリング実施形態 (in-place / fork-then-merge / worktree) | なし |
| A3 | 破壊的変更許容範囲 (strict / moderate / aggressive) | A1 (監査結果で「未使用検知」が判定材料になる) |
| A4 | W-R1 監査粒度 (ファイル / モジュール / 責務) | A1 (スコープ形式が粒度を規定する) |

依存 DAG: A1 → A4, A1 → A3, A2 は独立。

---

## Atom A1: 監査スコープ形式

### Step 1-2: Divergence + Debate

**[MELCHIOR]** (推進 / Value・Speed・Innovation):
- (a) widescan は全体最適で refactor 優先度を全体視点で決定できる。layered だと後段 Wave で発見した問題で前段 refactor がやり直し
- (c) hybrid: W-R1 で widescan 監査 + W-R2 以降で layered 実装 → 「早くリスト化 + 手堅く実装」で両立
- Speed 最速は (c) hybrid。widescan で問題可視化 → dependency map で並列化余地
- **推奨**: (c) hybrid

**[BALTHASAR]** (批判 / Risk・Security・Debt):
- (a) widescan は認知過負荷リスク: 問題リストが数百件になれば L1 判断限界を超える
- (b) layered は「規律更新 → コード修正 → テスト更新」の依存が層方向に逆流するケース (rules 変更が dashboard 実装制約を変える)
- (c) hybrid リスク: widescan 監査後の問題「消化率」追跡が難しい (進捗計測不明瞭)
- 特に W-R3 (規律 SSOT 統合) は全 rules × 全 internal × 全 adr の相互矛盾 widescan 必須
- **推奨**: (c) hybrid だが監査アウトプットに 3 段階重要度 + 帰責先必須化

### Step 3: Convergence

**[CASPAR]** (調停): 両者 (c) hybrid で一致。BALTHASAR の認知過負荷 + 消化率追跡懸念は監査アウトプット様式で吸収。
- **結論**: **(c) hybrid** — W-R1 で widescan 監査 (問題リスト + 重要度 + 帰責先グループ化)、W-R2〜W-R4 で layered 実装、W-R5 で最終監査
- **追加条件**: W-R1 監査アウトプットは Critical/Warning/Info 分類 + 帰責先 (upstream/downstream/spec_ambiguity/unknown) 必須 (`code-quality-guideline.md` §モジュール間帰責判断 準拠)

---

## Atom A2: リファクタリング実施形態

### Step 1-2: Divergence + Debate

**[MELCHIOR]**:
- (a) in-place: master 直で ship 頻度高 → 各 Wave 末で Green State 毎回確認可 (B-5 パターン継続)
- (b) fork-then-merge: R-1 全体一括 merge → 途中の緊急作業を blocker 化
- (c) worktree isolation: 領域別並列 → W-R2 (dashboard) と W-R3 (rules) 分離で時短
- LAM は master 単独ワークフロー慣行 → (a) が習慣整合
- **推奨**: (a) in-place

**[BALTHASAR]**:
- (a) in-place リスク: refactor 中 master で dashboard 生成が壊れると SESSION_STATE.md 破損 → セッション復帰不可
- (b) fork-then-merge: 一括 merge は conflict 解消コスト大 (規律 SSOT 統合の変更が多 module 波及)
- (c) worktree: LAM は Windows + Git Bash 環境 → worktree の実運用実績少 (副作用リスク未検証)
- **推奨**: (a) in-place + 各 Stage 末で `python -m pytest .claude/tests/dashboard/` smoke test 義務化

### Step 3: Convergence

**[CASPAR]**: 両者 (a) in-place で一致 (BALTHASAR 条件付き)。worktree は LAM 習熟なしのため保留。
- **結論**: **(a) in-place** — master 直改修、Stage 末で ship + push、Stage 冒頭でテスト smoke pass 確認
- **追加条件**: dashboard 生成周辺の refactor では特に `test_session_state_parser.py` smoke test 必須化 (rule-001.md 発動)

---

## Atom A3: 破壊的変更許容範囲

### Step 1-2: Divergence + Debate

**[MELCHIOR]**:
- (a) strict は R-1 目的 (資産整理) と矛盾。deprecation warning 経由削除は「延命」でしかない
- (b) moderate: 未使用 agent/rule 削除は monotonic 判断で可 (使用検知が確実なら)
- (c) aggressive: R-1 は resurfacing の機会 → 破壊的変更 free で最短経路
- 特に `.claude/agents/` の未使用 agent は 3-5 個推定 → 削除で保守コスト減
- **推奨**: (b) moderate または (c) aggressive

**[BALTHASAR]**:
- (c) aggressive リスク: R-1 破壊後 B-6+ で「あの機能どこ行った?」発生 → 履歴追跡コスト
- (b) moderate は「公開 API 相当」の定義が曖昧: LAM は library ではないので公開 API がない
- (a) strict は保守的すぎ (deprecation warning はコスト対効果薄)
- 破壊対象は (i) 未使用検知済み agent (ii) 使われていない rule (iii) 冗長な hook → (b) moderate で十分
- CRITICAL: 削除判断は PM 級 (`permission-levels.md` 準拠) → 削除前に必ず承認取得
- **推奨**: (b) moderate + 削除 PM 級承認必須 + 削除履歴を `docs/artifacts/r-1-deletions.md` に記録

### Step 3: Convergence

**[CASPAR]**: 両者 (b) moderate で妥協点。BALTHASAR の削除履歴記録は Zero-Regression Policy との整合上必要。
- **結論**: **(b) moderate** — 未使用検知済み agent/rule/hook は直接削除許容、削除前に PM 級承認 + 削除履歴を artifact に記録
- **追加条件**: 削除判定基準は「grep で参照ゼロ + import 参照ゼロ + セッション履歴で 90 日以上未使用」の 3 条件 AND

---

## Atom A4: W-R1 監査粒度

### Step 1-2: Divergence + Debate

**[MELCHIOR]**:
- (a) ファイル単位: 網羅性 100% だが問題リストが肥大化 (dashboard/ だけで数十ファイル)
- (b) モジュール単位: 責務単位で問題まとめ → refactor 実装計画に直結
- (c) 責務単位 (SRP/DRY 等): クロスカッティング分類は視点独立 → 実装計画に落としづらい
- refactor 直結性から (b) モジュール単位が最適
- **推奨**: (b) モジュール単位

**[BALTHASAR]**:
- (b) モジュール単位リスク: ファイル間相互依存問題を「モジュール内」に閉じ込めるバイアス → cross-module blame の見落とし
- (c) 責務単位は認知複雑度・重複コード等の `code-quality-guideline.md` と直結
- (a) ファイル単位は網羅性重視だが listing 疲労で本質見落とし
- 実運用では「モジュール単位 listing + 責務観点タグ付け」の合わせ技必要
- **推奨**: (b) モジュール単位 + 責務タグ (SRP/DRY/凝集度/認知複雑度) 付与

### Step 3: Convergence

**[CASPAR]**: 両者 (b) モジュール単位で一致 (BALTHASAR は責務タグ追加)。
- **結論**: **(b) モジュール単位** — 8 モジュール分類 (dashboard/scripts, dashboard/tests, hooks, agents, rules, internal, adr, specs)
- **追加条件**: 各 issue に責務タグ (SRP/DRY/凝集度/認知複雑度/仕様ドリフト/セキュリティ) + 重要度 (Critical/Warning/Info) + 帰責先 (upstream/downstream/spec_ambiguity/unknown) 必須付与

---

## 統合結論 (gabriel probe 前 / CASPAR)

| Atom | 結論 | 追加条件 |
|:-----|:-----|:--------|
| A1 | hybrid (widescan 監査 + layered 実装) | Critical/Warning/Info + 帰責先必須 |
| A2 | in-place (master 直改修) | Stage 末 smoke test + rule-001.md 発動 |
| A3 | moderate (未使用検知済み削除許容) | PM 級承認 + 削除履歴 artifact + 3 条件 AND |
| A4 | モジュール単位 (8 モジュール) | 責務タグ + 重要度 + 帰責先 |

依存関係の整合:
- A1 → A4: hybrid スコープ → W-R1 粒度は自然にモジュール単位で成立 ✓
- A3 → A2: moderate 削除許容 + in-place → 削除は独立 Stage で単独 ship 推奨 ✓
- A1/A4 → A3: widescan 監査で「未使用検知済み」判定 → A3 削除判断根拠 ✓

## gabriel probe (Step 4) — 世界初 real-world 発火

**発火日時**: 2026-07-05 / **経過**: 81,096 ms / **subagent_tokens**: 74,139 / **tool_uses**: 12

### gabriel 出力 (6 フィールド JSON / `docs/artifacts/2026-07-05-gabriel-probe-r1-planning.json`)

| フィールド | 値 |
|:----------|:---|
| verdict | **refuted** |
| severity | **warning** |
| affected_atoms | [A1, A4] |
| recommended_action | re-magi |
| confidence | 0.72 |

### reasoning (gabriel)

4 Atom 間の依存整合 (A1→A4, A1/A4→A3, A3→A2) 自体は論理的に妥当で、仕様 (`permission-levels.md` / `code-quality-guideline.md`) との明確な矛盾もない。しかし **2 点の前提検証漏れ** を確認:

1. **A4「8 モジュール分類」の網羅性不足**: 計画書 §2.1-2.2 のスコープ実体を網羅できていない
   - `.claude/scripts/` には dashboard 以外に `gd_guard.py` / `magi_dispatch.py` / `hga_usage.py` 等の独立スクリプト群が実在
   - `.claude/skills/` (27+ SKILL.md / magi・full-review 等の中核オーケストレータ含む) が 8 分類のどこにも属さない
2. **HGA envelope 週枠期限 (2026-07-07) が A2/Phase 2 未反映**: 現在 2026-07-05 → Phase 2 (HGA 召喚) が **クレジット従量移行境界を跨ぐ可能性が高い** が制約として反映されていない

加えて BALTHASAR が A1 で指摘した「消化率追跡」懸念は CASPAR が「監査アウトプット様式で吸収」としたのみで、追加条件は **静的分類にとどまり進捗追跡機構を持たず実質未回収**。

severity=critical のバグ・データ損失リスクではないため **warning**。

### Step 4.1 dispatch 判定

- 適用行: `verdict=refuted & severity=warning` → **「MAGI 結論に gabriel 指摘を併記 + 警告ラベル」**
- ただし gabriel の `recommended_action=re-magi` は積極的採用が妥当 (user 方針: MAGI/HGA 積極活用)
- **暫定処理**: gabriel 指摘を併記 + 警告ラベル貼付 → 次段判断はユーザーエスカレーション

### 併記された警告ラベル

> **[WARNING by gabriel]**: A4 の 8 モジュール分類は `.claude/scripts/` (dashboard 以外) と `.claude/skills/` を欠く。A2/Phase 2 は HGA envelope 週枠期限 (2026-07-07) を制約として明記していない。BALTHASAR の「消化率追跡」は静的分類のみで進捗機構を欠く。最終判断はユーザー (L1 統括) に委ねる。

### メトリクス記録

`.claude/gabriel-metrics.log` に JSONL 1 エントリー追記済 (実運用初発火 / gate_decision=run / resolved_action=annotate_warning)。

---

## Step 5-alt: re-MAGI 1 ラウンド (Path β / ユーザー承認 2026-07-05)

gabriel warning を Divergence 入力として A1/A2/A4 のみ再収束。retry_count=1。

### Atom A4 re-MAGI: 監査粒度の網羅性拡張

**[MELCHIOR]**: gabriel 指摘は妥当。10 モジュール分類に拡張:
1. `.claude/scripts/dashboard/` (dashboard 生成一式)
2. `.claude/scripts/` (dashboard 以外の独立スクリプト群 / gd_*/magi_dispatch/hga_usage/scan_nfr_refs/distill-lessons)
3. `.claude/skills/` (SKILL.md 27+ / magi / full-review / lam-orchestrate 等の中核オーケストレータ)
4. `.claude/tests/`
5. `.claude/hooks/`
6. `.claude/agents/`
7. `.claude/rules/`
8. `docs/internal/`
9. `docs/specs/`
10. `docs/adr/`

**[BALTHASAR]**: 10 モジュールで単純にコスト 25% 増 (元 8 → 10)。SKILL.md 27+ を 1 節に押し込むと個別 skill の drift 見落としリスク。ただし集約案 (6-7 分類) は中核オーケストレータの独立監査性を犠牲にする。10 分割 + 各 issue へのモジュール別問題数ヒートマップ添付で認知負荷は緩和可能。

**[CASPAR]**: **10 モジュール分類** で確定。W-R1 監査アウトプットに「モジュール別問題数ヒートマップ」を添えて認知負荷管理。

### Atom A2 re-MAGI: HGA 週枠期限の設計制約反映

**[MELCHIOR]**: 7/7 期限は運用条件だが Phase 2 スケジューリングに影響。追加条件で対応可能。

**[BALTHASAR]**: 7/7 跨ぎでコスト構造 (Pro/Max 50% 枠 → クレジット従量) が変わる。「7/7 以前に無条件召喚ゾーン (spec/design 初期の設計軸確定 = W-R1 スコープ最終確定) を集中消化」を A2 追加条件に明示すべき。7/8 以降は `hga-summon-log.md` envelope monitoring 必須化。

**[CASPAR]**: A2 **(a) in-place** の結論は不変。追加条件強化:
- Stage 末 smoke test (既定)
- rule-001.md 発動 (既定)
- **NEW**: HGA 召喚は 2026-07-07 以前に W-R1 スコープ確定 (spec/design 初期 = 無条件召喚ゾーン) を集中消化
- **NEW**: 7/8 以降の HGA 召喚は `hga-summon-log.md` envelope monitoring (実 $10-40 / weekly cap 20%) 必須

### Atom A1 re-MAGI: 消化率追跡機構の追加

**[MELCHIOR]**: 静的リストのみでは進捗計測不能。W-R1 監査アウトプットを Markdown table 化 + `status` 列 (open/wip/closed) 付与 → 各 Stage 末で更新。tracker ファイルを分離。

**[BALTHASAR]**: tracker 手動更新は負担。dashboard 組込は SESSION_STATE.md parser 複雑化で却下。妥協: `docs/artifacts/r-1-audit-tracker.md` 手動運用 + 各 Wave/Stage 末 ship の commit message に「closed issue IDs」列挙 → git log で消化率追跡可能。

**[CASPAR]**: A1 **(c) hybrid** の結論は不変。追加条件強化:
- Critical/Warning/Info + 帰責先 (既定)
- **NEW**: 監査アウトプットは `docs/artifacts/r-1-audit-tracker.md` (Markdown table / status 列 open/wip/closed 付き)
- **NEW**: 各 Wave/Stage 末で tracker 更新 (SE 級) / commit message に「closed issue IDs」列挙 (git log 経由の消化率追跡)

### re-MAGI 統合結論 (retry_count=1)

| Atom | 結論 | 追加条件 (差分) |
|:-----|:-----|:----------------|
| A1 | hybrid (不変) | **NEW**: r-1-audit-tracker.md (status 列) + commit message に closed issue IDs 列挙 |
| A2 | in-place (不変) | **NEW**: 7/7 以前 HGA 集中消化 + 7/8 以降 envelope monitoring |
| A3 | moderate (不変 / 対象外) | — |
| A4 | 10 モジュール (拡張) | scripts/skills 独立追加 + モジュール別問題数ヒートマップ |

## gabriel probe 2nd (Step 4 / retry_count=1)

**発火日時**: 2026-07-05 / **経過**: 73,719 ms / **subagent_tokens**: 74,523 / **tool_uses**: 10

### gabriel 出力 (6 フィールド JSON / `docs/artifacts/2026-07-05-gabriel-probe-r1-planning-2nd.json`)

| フィールド | 値 |
|:----------|:---|
| verdict | **refuted** |
| severity | **warning** |
| affected_atoms | [A2] |
| recommended_action | **proceed** |
| confidence | 0.68 |

### reasoning (gabriel)

前回 3 指摘のうち **A4 網羅性 (10 モジュール分類拡張) + A1 tracker 導入 (消化率追跡機構)** は実質解消。A2 のみ「7/7 以前に HGA 集中消化」が方向性明記に留まり、実現可能性未検証。計画書 §5 の前提残務 (B-5 Wave 8 T110 / gabriel Wave C Stage 4-5) 完了時期が本 re-MAGI 記録内で確認されておらず、PLANNING 未開始状態から 2 日以内の完走可能性が未検証のまま結論に組み込まれている。

**軽微な追加指摘**:
- SKILL.md 実測 22 件 (見積 27+ から下方修正)
- BALTHASAR の「tracker 手動更新は負担」提案が同じく手動運用 (tracker + commit message 併用) → 運用継続性リスク未評価 (rule 化等の予防機構)
- A1 tracker と A3 削除の連動 (削除実施時に該当 issue → closed 手順) 未明記

severity=critical に至るバグ・データ損失リスクではないため **warning**。`recommended_action=proceed` (re-magi 再要求は致命度に見合わない)。

### Step 4.1 dispatch 判定 (2nd)

- 適用行: `verdict=refuted & severity=warning` → 併記 + 進む
- `recommended_action=proceed` により再 MAGI なし
- **判定**: annotate + proceed → **Step 5 AoT Synthesis 実行可**

### メトリクス記録 (2nd)

`.claude/gabriel-metrics.log` に JSONL 追記済 (retry_count=1 / resolved_action=annotate_warning)。

### CASPAR による gabriel 残存懸念の annotation

以下 4 点を統合結論に併記警告として付す:

1. **A2 前提残務の実状**: 計画書 §5 の前提残務 (B-5 Wave 8 T110 / gabriel Wave C Stage 4-5) は **本セッション 2026-07-05 時点で全て完了済**（SESSION_STATE.md HEAD `93032da` 参照 / B-5 Milestone COMPLETE 判定済）。したがって「7/7 以前の HGA 集中消化」は W-R1 スコープ確定作業のみが残タスクであり、実現可能性は高い。gabriel の懸念は「MAGI 記録内で明示されていない」点は妥当だが、事実として障害はない。
2. **SKILL.md 件数**: 22 件 (実測) → A4 の説明文を「27+」から「22 件」に下方修正
3. **tracker 手動運用リスク**: rule 化予防機構は本 R-1 内で PM 級 draft-002 候補として起票検討 (次 Wave 議題)
4. **A3 × A1 連動**: 削除実施 (A3 Stage) 時に tracker の該当 issue を closed にする手順を design.md §削除フロー で明記 (追加 SSOT 差分)

---

## Step 5: AoT Synthesis (最終)

### 統合結論

| Atom | 最終結論 | 追加条件 (統合) |
|:-----|:---------|:----------------|
| A1 | hybrid (widescan 監査 + layered 実装) | Critical/Warning/Info + 帰責先 (upstream/downstream/spec_ambiguity/unknown) / **NEW**: `docs/artifacts/r-1-audit-tracker.md` (Markdown table / status open/wip/closed) + 各 Stage 末 ship の commit message に closed issue IDs 列挙 |
| A2 | in-place (master 直改修) | Stage 末 smoke test / rule-001.md 発動 / **NEW**: 7/7 以前 HGA 集中消化 (残タスク = W-R1 スコープ確定のみ / B-5 前提残務は既完了) / **NEW**: 7/8 以降 envelope monitoring (実 $10-40 / weekly cap 20%) |
| A3 | moderate (未使用検知済み削除許容) | 削除前 PM 級承認 + 削除履歴 artifact (`docs/artifacts/r-1-deletions.md`) + 3 条件 AND (grep ゼロ + import ゼロ + 90 日未使用) / **NEW**: 削除時に tracker の該当 issue を closed にする手順を design.md §削除フローで明記 |
| A4 | モジュール単位 (10 モジュール分類 / SKILL.md 22 件) | 責務タグ + 重要度 + 帰責先必須 / モジュール別問題数ヒートマップ添付 |

### gabriel 併記警告 (final)

> **[WARNING by gabriel 1st, resolved by re-MAGI]**: A4 網羅性 (scripts/skills 追加) と A1 消化率追跡機構は re-MAGI で解消。
> **[WARNING by gabriel 2nd, annotated]**: A2「7/7 以前 HGA 集中消化」の実現可能性は前提残務完了確認 (SESSION_STATE.md HEAD `93032da`) により障害なし。tracker 手動運用 rule 化は次 Wave 議題として起票候補。A3 削除 × A1 tracker 連動は design.md で明記予定。

### Action Items (R-1 PLANNING 進行方針として requirements.md へ反映)

1. **requirements.md**: A1-A4 結論を FR/NFR 化 (RFC 2119 準拠) + gabriel 併記警告を Non-Goals セクションと Success Criteria に反映
2. **design.md**: 5 Wave (W-R1 〜 W-R5) 分割 + A3 削除フロー明記 (tracker 連動) + A4 の 10 モジュール監査アウトプット様式 (Markdown table / status 列 / モジュール別ヒートマップ)
3. **tasks.md**: SPIDR 垂直分割 + WBS 100% Rule + 各 Task に closed issue ID 対応付け機構
4. **`.claude/rules/auto-generated/`**: rule-002 起票候補 (tracker 手動更新の忘却予防 / 次 Wave 議題)
5. **HGA スケジュール**: 7/7 以前に W-R1 スコープ確定 = HGA 無条件召喚ゾーン (spec/design 初期の設計軸確定) を集中消化 → 具体的日程は次アクション

---

## Step 6: HGA #5 統合 (Fable スポット召喚 / 2026-07-05)

Fable HGA #5 が **crux 5 件全て命中 + unknown-unknown 5 件追加検出**。CASPAR は Fable 提案を統合し以下に反映:

### Fable 反映内容

#### Crux 1 (Green State 追加条件) → 採用

Green State 5 条件に **追加 3 二値条件** を Milestone R-1 完了条件として組み込む (連続量指標は棄却 / 観測に降格):

- **R-G6: tracker 全閉塞** — `r-1-audit-tracker.md` の全 issue が closed または deferred (理由付き / green-state-definition §4 準拠)
- **R-G7: SKILL.md / rules 参照解決 = 0 drift** — 23 SKILL.md + rules が参照するパス・rule 名・verdict フィールド名が grep で全て実在解決 (prose 資産の「テスト」等価物)
- **R-G8: Python モジュール循環依存 = 0** — dashboard / scripts の import グラフ循環ゼロ (`phase-rules` AUDITING チェックリスト既存項目の機械判定化)

**棄却指標**: 認知複雑度平均 (Goodhart 化 / G3 既存より弱い) / 結合度低下率 (ベースライン不在) → **W-R1 では観測値として記録するが Green State ゲートには入れない**

#### Crux 2 (10 モジュール粒度) → 修正採用

- `.claude/skills/` は単一モジュール維持 + **`tier=orchestrator / utility` タグ** で分離 (orchestrator 5 件 = magi/full-review/lam-orchestrate/autonomous/goal-driven のみ R-G7 強度必須)
- `.claude/scripts/` 内外分離は **「テスト保護下 vs 保護外」の実質境界** として維持 (module 2 の issue は多くが module 3/6 への upstream 帰責になる予測)
- `docs/internal/` / `docs/specs/` / `.claude/rules/` の 3 分類は独立だが **設計された重複が存在** (`decision-making.md` が「06_DECISION_MAKING.md の実行時要約」を宣言) → **W-R3 に横断監査軸「規範文の重複ペア検査」を明示的に立てる** (SSOT 親を宣言している rules/*.md 全件について親との差分検査必須化)
- **11 番目のモジュール = ルート統治文書** (`CLAUDE.md` + `CHEATSHEET.md`) 追加 (blast radius 最大 / 現分類では監査漏れ)
- `.claude/settings*.json` は独立させず **module 5 を「hooks + settings 配線」に改称して吸収**
- `SESSION_STATE.md` (gitignore 済揮発資産) + `docs/artifacts/` (歴史記録) は **明示的 Non-Goals** (scope creep 湧き口の予防)

**最終モジュール分類 (11 モジュール)**:

1. `.claude/scripts/dashboard/` — Wave 2-8 累積 / 424 テスト保護
2. `.claude/scripts/` (dashboard 外) — gd_*/magi_dispatch/hga_usage/scan_nfr_refs/distill-lessons / 保護薄
3. `.claude/skills/` — 23 SKILL.md (実測) / **tier=orchestrator 5 件のみ強度**
4. `.claude/tests/` — 424 + 63 PASS / 14 SKIP
5. `.claude/hooks/` + `.claude/settings*.json` — hooks + settings 配線 (改称)
6. `.claude/agents/` — 12 件 (実測 / plugin 由来は out of scope)
7. `.claude/rules/` — 11 files + auto-generated/
8. `docs/internal/` — 憲法 SSOT 00-07
9. `docs/specs/` — 全 spec directories
10. `docs/adr/` — 0005-0009
11. **`CLAUDE.md` + `CHEATSHEET.md`** — ルート統治文書 (NEW / blast radius 最大)

**明示的 Non-Goals**: `SESSION_STATE.md` / `docs/artifacts/`

#### Crux 3 (scope creep 予防) → (d) 採用 = (a)+(b) 合成 + 客観的昇格基準 1 本

- **既存憲法の適用のみ** (新機構ゼロ): planning-quality-guideline §3 (Non-Goals 節) + green-state-definition §4 (deferred フォーマット / 理由必須) の合成
- 接続する追加ルール **1 本のみ**: 「Wave 途中で湧いた項目は無条件で tracker に deferred として記録する。R-1 の Wave 内へ昇格できるのは **『in-scope モジュールの Green State 条件 (Critical / Warning) を block する場合』のみ**」 (二値・機械判定 → MAGI 呼ぶ余地を消す)
- **Wave 数 5 は固定**。Wave 追加 = Milestone 再計画 = PM 級承認 (terminology.md ペア 5 と同思想 / クローズ済 Milestone の再開禁止)

#### Crux 4 (7/7 前 HGA スケジュール) → (i)+(ii) 合成 = 3 回構成 (カレンダー駆動 → ゲート駆動)

| 召喚 | 時期 | 対象 |
|:----|:----|:----|
| #5 (本件) | 済 (2026-07-05) | スコープ crux |
| **#6** | **7/7 前・必須消化** | 第一候補: W-R1 監査結果の妥当性検証 / 第二候補 (スライド): W-R1 監査 rubric / チェックリスト事前検証 |
| **#7** | W-R3 設計時 (7/8 後 / 従量 ~$2-3) | 規律 SSOT 統合の設計軸 (hga-summoning.md「不可逆な設計コミット = 無条件召喚」に該当 / 従量でも実施) |
| W-R5 | **召喚しない** | 検証は gabriel 実運用初日 refute 2/2 で実証済領域 |

**原則**: 召喚はカレンダーではなくゲートで決める。7/7 期限が動かすのは「どの作業を前倒すか」であり「ゲートに該当しない召喚を追加するか」ではない

#### Crux 5 (unknown-unknown 5 件) → 全採用

**すべて requirements/design/tasks に反映すること**:

1. **W-R1 冒頭タスク: ファイルシステム インベントリ再生成必須** — 記憶・ブリーフ由来の件数を信用しない。SKILL.md 数 (実測 23) と agents 数 (実測 12) の drift を Fable が検出済
2. **W-R4 に `.claude/agent-memory/` 無効化・更新パス タスク追加** — 現 10 モジュール分類に不在 / 削除・改名時に古い memory が改名後 agent を誤誘導するリスク
3. **W-R3/W-R4 は R-G7 を Stage 末 smoke test の必須部品に組み込む** — prose 資産 (rules/skills/agents) は回帰網なしで G1 が無内容 PASS → A2 in-place 前提が崩れる懸念
4. **A3 「90 日未使用」判定データソース確定** — hga_usage.py は HGA 専用 / skills/agents 台帳不在 → W-R4 着手前に「未使用の判定データソース」を明文化 (git log 上の最終参照更新日で代用等)
5. **rule-001 (SESSION_STATE fallback) を tracker 認識に拡張** — セッション断絶時の復旧チェックリストに tracker 状態確認を 1 行追加 (SESSION_STATE.md 復旧手順への追記)

### Fable 反映後の最終 CASPAR 統合結論

上記 5 crux 反映後の最終結論を **R-1 PLANNING requirements.md 起稿の SSOT** として確定 → 起稿へ移行 (Task #3)

### メトリクス補足

- HGA #5 コスト実測: subagent_tokens 83,890 / tool_uses 4 / 経過 171,330 ms
- envelope 消費: $2-5 圏想定 (jsonl 直読み実測は次日以降 / #4 型パターン準拠)
- 判定: **envelope 内で高価値情報を取得** (Fable 実質貢献 = 明確 / L1+MAGI+gabriel では検出不可の 5 unknown-unknown を独立検出)

### メトリクス集計 (R-1 PLANNING 冒頭 gabriel probe / 実運用初日)

- 起動回数: 2 (1st + 2nd probe)
- refute 率: **100% (2/2)** ← 実運用初日として高い / 品質基準の緩さと過剰厳しさのバランスに要注意
- warning 率: 100% (2/2 / critical/info はゼロ)
- inconclusive 率: 0%
- 平均経過時間: 77,407 ms (81,096 + 73,719) / 2
- proceed 到達回数: 1 (2nd probe)
- re-magi 発動回数: 1 (1st probe)
- confidence 平均: 0.70 (0.72 + 0.68) / 2

**運用初日所感**: gabriel の実質貢献 = 明確 (A4 網羅性 / A2 期限制約 / A1 追跡機構の 3 点は L1 単独では見逃していた可能性が高い)。retry_count=1 上限で自動収束。人間エスカレーション不要。設計妥当性の裏付けを実運用初日で得た。
