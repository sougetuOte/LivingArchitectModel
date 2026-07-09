# ADR-0001: モデルルーティング戦略

**日付**: 2026-03-08
**ステータス**: **Accepted** (2026-07-10 / R1-047 W-R3 S4 で正式遷移)
**関連要件**: NFR-1〜5, DP-4, DP-6

## 改訂履歴

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

## 補足事項

- `model` フィールドのエイリアス（`haiku`, `sonnet`, `opus`）は公式ドキュメント（model-config, sub-agents）に記載あり。実機検証は Wave 1 実装時に実施
- 環境変数 `ANTHROPIC_DEFAULT_HAIKU_MODEL` 等で解決先を上書き可能
- `opusplan` エイリアス（planning 時 Opus、execution 時 Sonnet）はメインセッションのモデルとして検討に値する

## 結果

- hooks のコスト影響を最小化
- メインセッションの Opus 枠を保護
- 「迷ったら SE」原則により、分類精度不足時も安全側に倒れる
