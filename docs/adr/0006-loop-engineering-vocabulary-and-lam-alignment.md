# ADR-0006: Loop Engineering 観点からの LAM 構成再評価と統一語彙

## メタ情報
| 項目 | 内容 |
|------|------|
| ステータス | **Proposed**（2026-06-21 起草） |
| 日付 | 2026-06-21 |
| 意思決定者 | sougetuOte（最終承認）/ Living Architect（起草・合議） |
| 関連ADR | [ADR-0005](./0005-thin-harness-autonomous-governance.md)（ハーネス減量と自律統治モード） |
| 関連資産 | `.claude/skills/autonomous/SKILL.md`, `.claude/skills/goal-driven/`, `.claude/rules/decision-making.md`, `CLAUDE.md`「作業体制（3.5 層委譲モデル）」節 |

---

## コンテキスト

### 背景

2026 年 6 月 7 日頃、Addy Osmani（Google Chrome）/ Boris Cherny（Anthropic）/ Peter Steinberger の議論を起点に「Loop Engineering」という用語と 3 段階モデルが提唱された。概要は以下のとおり。

- **Stage 1 Prompt**: 単発・人間ドリブンの指示実行
- **Stage 2 Loop**: research → draft → evaluate → improve の自律ループ、独立 verifier による termination 判定
- **Stage 3 Orchestrated Teams**: coordinator が parallel specialists を分配し、evaluator gate が合格判定

2026-06-21 セッションでの Web 調査により、**LAM の既存資産がこの 3 段階モデルを先取りする形で構築されていた**ことが判明した。とりわけ同日に `CLAUDE.md` へ「3.5 層委譲モデル」節を新設・明文化（commit `daa50e1`）したタイミングと重なる。

### 問題

用語の統一と概念整理が未着手のままだと、後続 Milestone（①②③⑥）の起案時に以下の手戻りが繰り返し発生する。

- 「司令塔」「grader」「verifier」「coordinator」「班長」「協議者」等の呼称が文書ごとに異なり、同一概念を指しているか判断できない
- Loop Engineering の文脈で LAM を説明する際に、対応表を各担当者が再発見しなければならない
- 後続 Milestone の起案書において LAM 固有語と Loop Eng 語が混在し、設計の一貫性が失われる

### 制約条件

- 本 ADR 自体はドキュメント確定のみ。個別スキルの実装変更は対象外
- 各 Milestone の実装判断は後続の設計・タスク段階に委ねる
- Loop Engineering 用語は Addy Osmani 等による造語であり、今後変化する可能性がある

---

## LAM 既存資産と Loop Engineering 3 段階モデルの照合

| Loop Eng Stage | 文献定義 | LAM 既存資産 | 状態 |
|---|---|---|---|
| Stage 1: Prompt | 単発・人間ドリブン | 個別 Skill 直接呼び出し / 直接 Tool 使用 | 完成 |
| Stage 2: Loop | research-draft-evaluate-improve の自律ループ + verifier | `/autonomous`（spec → Green State 自律実装）/ `/goal-driven`（rubric 駆動 + 独立 grader）| 実装済 / 部分展開 |
| Stage 3: Orchestrated Teams | coordinator + parallel specialists + evaluator gate | 3.5 層委譲モデル（CLAUDE.md 明文化）/ `lam-orchestrate` / `full-review` | 雛形あり / 自動化未完 |

### LAM 固有の追加観点（文献に明示されていない部分）

文献の 3 段階モデルには含まれないが、LAM が独自に備える統治レイヤーが 3 点ある。

- **三フェーズ規律（PLANNING / BUILDING / AUDITING）**: Stage 別ループの境界条件として機能し、ループが無制限に継続することを防ぐ承認ゲートを構成する
- **権限等級（PG/SE/PM）**: verifier 判定後にどこまでを自動適用し、どこを人間承認に委ねるかの粒度制御レイヤー
- **context engineering の多層化**: `CLAUDE.md` / `.claude/rules/` / `MEMORY.md` / `SESSION_STATE.md` の重層構成が、文献における "context engineering" 教科書例に相当する。LAM は文献が示す以上に手厚い構成を既に持つ

---

## 識別されたギャップ

本 ADR 起草時点での LAM と Loop Engineering 理想状態のギャップを 3 点特定した。

1. **Stage 2 → 3 の橋渡しが手動**: 3.5 層委譲モデルが概念として存在するが、coordinator が自律的にループを実行する機構がなく、現状は人間が各 Milestone を手動起動している
2. **verifier 分離の範囲が狭い**: `goal-driven-grader` は Stage 2 向けの独立 verifier として機能するが、`/full-review` への展開が不足しており Stage 3 の evaluator gate が自動化されていない
3. **用語の散在**: 「司令塔」「grader」「verifier」「coordinator」「班長」「協議者」等が文書ごとに異なる呼称で登場し、同一概念を指すかどうかを都度確認しなければならない

---

## Glossary（Loop Engineering 語 → LAM 語の対応）

新規読者および後続 Milestone の起案者が両語彙を同時に参照できるよう、以下に統一対照表を置く。

| Loop Eng 用語 | LAM 用語 | 備考 |
|---|---|---|
| coordinator / dispatcher | L1.5 司令塔 | parallel specialists への分配を担う |
| specialist / worker | L2 実行 | parallel specialists に相当 |
| verifier / evaluator gate | L3 採点（`goal-driven-grader` 等） | termination 判定者 |
| termination condition + verifier rubric | `rubric.md` | 文献の「完了条件」に相当する LAM 独自の構造化定義 |
| context engineering | `CLAUDE.md` / `.claude/rules/` / `MEMORY.md` 重層 | LAM 固有の多層化による実装 |
| debate among specialists | 3 Agents Model（MAGI） | Reflection を gabriel に統合予定（②） |
| （文献に該当なし・人間との接面） | L1 統括 | LAM 固有のレイヤー。最終承認権と方向性維持を人間が担う |

> **注意**: 本 Glossary は 2026-06-21 時点の対応関係である。Loop Engineering 用語は造語・流動的であり、今後改訂される場合は本 ADR を更新するか後続 ADR で差分を記録すること。

---

## 後続 Milestone への推奨改善方針

| Milestone | 改善方針 | Loop Eng 文脈 |
|---|---|---|
| ③ `lam-orchestrate` / `full-review` の `goal-driven` 化（既存骨子） | Stage 2 化（rubric + 独立 verifier）として位置づけを強化 | 「触り心地」の最大変化点 |
| ⑥ プロジェクト俯瞰オーケストレータ（既存骨子） | Stage 3 Team の典型設計として再定義。coordinator 層の常駐化 | Stage 3 Orchestrated Teams の実装 |
| ② MAGI v2（gabriel 導入・既存骨子） | gabriel = verifier 分離の核心として再強調 | Loop Eng の verifier 分離観そのもの |
| 新規・軽量 | `/autonomous` / `/goal-driven` の `SKILL.md` に Loop Eng 観点の補足追記。termination 条件と verifier の対応を 1 段落明記 | 既存資産への語彙統一（最小コスト） |

上記は優先順位の参考であり、最終的な Milestone 起案時に実態に合わせて調整する。

---

## 検討した選択肢

### 案 A: 却下 — 全 SKILL.md を Loop Eng 用語に一括リライト

**概要**: LAM の全ドキュメントを Loop Engineering 用語で書き直す。

**却下理由**: スコープが過剰。既存資産の文脈が失われ、LAM 固有の概念（三フェーズ規律・権限等級等）が Loop Eng 語に吸収されて消える。LAM の独自性が損なわれる。

### 案 B: 却下 — ⑥ プロジェクト俯瞰オーケストレータから先に実装

**概要**: ADR・Glossary の確定を待たず、最も Stage 3 に近い ⑥ を先行実装する。

**却下理由**: 統一視点なしに個別 Milestone が起案されると、用語の散在問題（ギャップ 3）が温存される。基準 ADR を先に固定し、各 Milestone が参照する順序が正しい。

### 案 C: 採用 — ADR で基準を固定し、各 Milestone 起案時に参照する

**概要**: 本 ADR を「Loop Engineering との対応基準」として確定し、後続 Milestone（①②③⑥）が起案時に本 ADR を参照することで用語と視点を統一する。個別スキルの実装変更は各 Milestone の判断に委ねる。

**採用理由**: 最小コストで用語散在問題を解消し、後続起案の一貫性を担保できる。既存資産への変更を最小化しつつ、Loop Engineering の文脈で価値を言語化できる。

---

## 影響

### ポジティブな影響

- 後続 Milestone（①②③⑥）起案時の用語が本 ADR の Glossary で統一される
- 既存資産（`/autonomous`, `/goal-driven` 等）の価値が文献用語で説明可能になり、外部発信・新規メンバー説明が容易になる
- 「触り心地」改善方向（③⑥②）の優先順位が本 ADR で参照基準として固定される
- ADR-0005 で確立した「autonomy with a constitution」方針が Loop Engineering 文脈で再言語化され、方向性の一貫性が可視化される

### ネガティブな影響

- Loop Engineering 語と LAM 語の二重定義期間が発生する（Glossary で吸収、一括リライトは非スコープ）
- Loop Engineering 用語が今後変化した場合、本 ADR の Glossary に追跡コストが発生する

### 影響を受けるコンポーネント

本 ADR はドキュメント確定のみを対象とし、以下には直接変更を加えない。後続 Milestone の起案時に参照基準として機能する。

- `.claude/skills/autonomous/SKILL.md`, `.claude/skills/goal-driven/`（Milestone 新規・軽量で補足追記）
- `lam-orchestrate`（③ の設計・タスクで扱う）
- `CLAUDE.md`「作業体制（3.5 層委譲モデル）」節（参照のみ）

---

## 参考資料

- Addy Osmani "Loop Engineering" blog（2026 年 6 月）
- Peter Steinberger ツイート（2026-06-07 付近）
- Boris Cherny / Anthropic 議論
- LangChain "The Art of Loop Engineering"
- explainx.ai "What Is Loop Engineering? Beyond Prompt Engineering in 2026"
- 本セッション `SESSION_STATE.md`（2026-06-21）「Loop Engineering とは」議論ログ
- [ADR-0005](./0005-thin-harness-autonomous-governance.md)（ハーネス減量と自律統治モード）
- `docs/internal/06_DECISION_MAKING.md`（MAGI System）
- `.claude/rules/decision-making.md`, `.claude/rules/terminology.md`
- `CLAUDE.md`「作業体制（3.5 層委譲モデル）」節（commit `daa50e1`）
