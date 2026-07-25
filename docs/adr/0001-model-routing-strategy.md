# ADR-0001: モデルルーティング戦略

**日付**: 2026-03-08
**ステータス**: **Accepted** (2026-07-10 / R1-047 W-R3 S4 で正式遷移)
**関連要件**: NFR-1〜5, DP-4, DP-6

## 改訂履歴

- **2026-07-25** (M-1 W0-M1-T6 / PM 級承認済): 下記 2026-07-10 の記述および「決定」§注記に **3 点の誤り**があることを実測で確定し、**「決定」§注記 2 として訂正を追記**（過去の決定文は書き換えない）。要旨: (1)(2) `command` は本 ADR 自身が定義する **hooks 第 1 層の handler type** であり `.claude/agents/*.md` の `model:` 値ではない（**同一文書内のレイヤー混同**）/ `fable` は実ファイル・hook のいずれにも不在、(3) `goal-driven-l3-executor` は実測 **`sonnet`**（`haiku` ではない）。全 12 agents の実測は **sonnet 9 / haiku 3 / 不明 0**。**実ファイル側は一貫しており修正不要**。

- **2026-07-10** (W-R3 S4 R1-047 消化): Proposed → **Accepted**。同時に「第2層 (prompt/haiku ハンドラ) は不採用」を明示 (下記「決定」§注記参照)。実装は `.claude/agents/*.md` frontmatter の `model:` 個別指定 (12 agents で `command|sonnet|haiku|fable` 混在指定) で決定 B の意図 (Opus 枠温存 + 分類精度確保 + コスト最小化) を達成しているため、3 層構造の第 2 層 (prompt/haiku) は「未実装のまま不要」として結論。

---

## コンテキスト

LAM v4.0.0 では hooks（PreToolUse, PostToolUse, Stop, PreCompact）と subagents でモデルを使用する。Claude Code Max 契約では Opus にフォールバック閾値があり、hooks で Opus を消費するとメインセッションの Opus 枠を圧迫するリスクがある。

## 判断対象

hooks と subagents でどのモデルを使用するか。

## 選択肢

### A: 等級に応じてモデルを上げる（PG=なし, SE=Haiku, PM=Opus）

- **[Affirmative]**: PM級判定に Opus を使えば精度が最も高い
- **[Critical]**: Opus 枠を hooks が消費し、メインセッションで Opus が使えなくなるリスク。PM級の hook は「この変更は PM 級か？」の分類判定であり、Opus の推論力は不要

### B: 3層アプローチ（command → Haiku → Sonnet）— **採用**

- **[Affirmative]**: Haiku は hooks のデフォルト（公式設計意図と一致）。Sonnet は agent 型で十分な精度。Opus 枠をメインセッションに温存
- **[Critical]**: Sonnet での PM 級判定精度が不十分な場合、誤分類リスク。ただし「迷ったら SE」原則で安全側に倒せる

### C: 全て command 型（LLM 不使用）

- **[Affirmative]**: コストゼロ、レイテンシ最小
- **[Critical]**: ファイルパス・ツール名のパターンマッチだけでは SE/PM の判定が不十分。変更内容の意味理解が必要なケースに対応できない

## 決定

**選択肢 B を採用。**

| レイヤー | handler type | model | 用途 |
|---------|-------------|-------|------|
| 第1層: パスベース | `command` | なし | ファイルパス・ツール名で PG/SE/PM を粗分類 |
| 第2層: 内容ベース | `prompt` | `haiku` | 第1層で判定不能なグレーゾーンを LLM で判定 |
| 第3層: 深い検証 | `agent` | `sonnet` | ファイル内容を読む必要がある場合（agent は tool access あり） |

**Opus は hooks/subagents で使用しない。** メインセッション専用。

### 注記 (2026-07-10 Accepted 遷移時追加 / R1-047)

第 2 層 (prompt/haiku ハンドラ) は**不採用**とする。実装は `.claude/agents/*.md` frontmatter の `model:` 個別指定 (subagent 別に `command|sonnet|haiku|fable` を明示) で決定 B の意図 (Opus 枠温存 + 分類精度確保 + コスト最小化) を達成しているため、hooks 内 3 層カスケードは第 1 層 (`.claude/hooks/pre-tool-use.py` パスベース) + 第 3 層 (subagent frontmatter model 指定) の 2 段構成で足りる。従って以下のように読み替える:

- **hooks (第 1 層)**: 全 5 件 `type: command` = 純粋 Python 実装 = 追加 LLM コストなし
- **第 2 層 (グレーゾーン LLM 判定)**: 不採用 = subagent 個別指定で代替 (実運用で判定不能ケース未観測)
- **subagents (第 3 層)**: `model:` フィールドで agent 毎に指定 (12 agents 実測 / gabriel = sonnet / goal-driven-l3-executor = haiku / 等)

### 注記 2 (2026-07-25 追加 / M-1 W0-M1-T6 実測 / 上記記述の訂正)

`grep -n "^model:" .claude/agents/*.md` による全 12 ファイルの実測 (2026-07-25) は **sonnet 9 / haiku 3 / 不明 0** であり、上記および §改訂履歴の記述に **3 点の誤り**がある。ADR の慣習に従い過去の決定文は書き換えず、本注記で訂正する。

| # | 誤っている記述 | 実測 (2026-07-25) | 種別 |
|:-:|:--------------|:------------------|:-----|
| 1 | §改訂履歴「12 agents で `command\|sonnet\|haiku\|fable` 混在指定」 | `command` **0 件** / `fable` **0 件** | **レイヤー混同** |
| 2 | 上記「決定」§注記「subagent 別に `command\|sonnet\|haiku\|fable` を明示」 | 同上 | **レイヤー混同** |
| 3 | 直上の行「goal-driven-l3-executor = haiku」 | **`model: sonnet`** | **事実誤記** |

**#1・#2 は drift ではなく本 ADR 内部の自己矛盾である**: 本 ADR の「決定」§表は `command` を「**第 1 層: パスベース / handler type = `command` / model = なし**」と定義している。すなわち `command` は **hooks の handler type** であって `.claude/agents/*.md` の `model:` frontmatter の値ではない。両記述はこれを agents の model 値として列挙しており、**同一文書内で層を取り違えている**。`fable` は実ファイル・hook のいずれにも存在しない。

**#3 について（2026-07-26 追記 / git 実測で確定）**: **2026-07-10 の注記追加時点で既に誤っていた。** 実ファイルは一度も `haiku` だったことがない。

- `.claude/agents/goal-driven-l3-executor.md` の `model:` 行の全変更履歴は **`+model: sonnet` の 1 回のみ**（`ce4acc7` / 2026-06-12 / 新規作成時）
- 上記注記を追加した commit（`80d8c8c` / 2026-07-10）時点の同ファイルの値も `model: sonnet`

```bash
git log --follow -p --date=short --pretty=format:"COMMIT %h %ad %s" -- .claude/agents/goal-driven-l3-executor.md | grep -E "^(COMMIT|[+-]model:)"
git show 80d8c8c:.claude/agents/goal-driven-l3-executor.md | head -8
```

したがって **#3 も #1・#2 と同じく drift ではなく、注記が書かれた時点からの誤記である**。実ファイル側は一貫しており修正不要という結論は変わらない。

**実ファイル側は一貫しており修正不要**。訂正は本 ADR 側のみで完結する。

**2026-07-25 時点の実測値**:

| model 値 | 件数 | 該当 agent |
|:---------|-----:|:-----------|
| `sonnet` | 9 | code-reviewer / design-architect / doc-writer / gabriel / goal-driven-l2-foreman / **goal-driven-l3-executor** / quality-auditor / requirement-analyst / tdd-developer |
| `haiku` | 3 | goal-driven-grader / task-decomposer / test-runner |
| 未設定 | 0 | — |

実測記録: `docs/artifacts/m-1-baseline-w0.md` §W0-M1-T6。本注記に伴い `docs/specs/m-1-opus5-migration/requirements.md` FR-20 の説明文も同日訂正済み。

## 補足事項

- `model` フィールドのエイリアス（`haiku`, `sonnet`, `opus`）は公式ドキュメント（model-config, sub-agents）に記載あり。実機検証は Wave 1 実装時に実施
- 環境変数 `ANTHROPIC_DEFAULT_HAIKU_MODEL` 等で解決先を上書き可能
- `opusplan` エイリアス（planning 時 Opus、execution 時 Sonnet）はメインセッションのモデルとして検討に値する

## 結果

- hooks のコスト影響を最小化
- メインセッションの Opus 枠を保護
- 「迷ったら SE」原則により、分類精度不足時も安全側に倒れる
