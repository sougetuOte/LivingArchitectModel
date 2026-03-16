---
name: magi
description: >
  MAGI System — AoT 分解 + MELCHIOR/BALTHASAR/CASPAR 合議 + Reflection による
  構造化意思決定フレームワーク。判断ポイント 2+ / 影響レイヤー 3+ / 選択肢 3+ で使用。
  Use when facing complex decisions with multiple trade-offs or architectural choices.
---

# /magi — 構造化意思決定（MAGI System）

名前の由来: エヴァンゲリオンの MAGI システム（3 つの独立した思考体による合議意思決定）

## MAGI System

**SSOT**: `docs/internal/06_DECISION_MAKING.md` を精読すること。

| MAGI | ペルソナ | フォーカス |
|:-----|:--------|:----------|
| **MELCHIOR** | 科学者（推進者）[旧: Affirmative] | Value, Speed, Innovation |
| **BALTHASAR** | 母（批判者）[旧: Critical] | Risk, Security, Debt |
| **CASPAR** | 女（調停者）[旧: Mediator] | Synthesis, Balance, Decision |

## 適用条件

以下のいずれかに該当する場合に発動する:

- 判断ポイントが 2 つ以上
- 影響するレイヤー/モジュールが 3 つ以上
- 有効な選択肢が 3 つ以上

**ユーザーが明示的に `/magi` を呼び出した場合は、条件に合致しなくても必ず実行する。**

条件に合致しないかつ明示呼出しでない場合は「従来手法で十分です」と案内する。

## 実行フロー

### Step 0: AoT Decomposition（分解）

議題を独立した Atom（判断単位）に分解し、依存 DAG を構築する。

Atom の 3 条件:
- **自己完結性**: 他の Atom に依存せず独立処理可能
- **インターフェース契約**: 入力と出力が明確
- **エラー隔離**: 失敗しても他 Atom に影響しない

```markdown
### AoT Decomposition

| Atom | 判断内容 | 依存 |
|:-----|:---------|:-----|
| A1 | [判断1] | なし |
| A2 | [判断2] | A1 |
```

### Step 1: Divergence（発散）

MELCHIOR と BALTHASAR がそれぞれの立場から意見を出し尽くす。

- **MELCHIOR**: メリット、開発効率、革新性を列挙
- **BALTHASAR**: リスク、セキュリティ懸念、保守コストを列挙

### Step 2: Debate（議論）

対立するポイントについて、具体的な解決策や緩和策を検討する。

### Step 3: Convergence（収束）

CASPAR が議論を整理し、結論を下す。

```markdown
### Atom A1: [判断内容]

**[MELCHIOR]**: ...
**[BALTHASAR]**: ...
**[CASPAR]**: 結論: ...
```

### Step 4: Reflection（振り返り）

全員で結論を検証する。**1 回限り**。

**ルール**:
- 致命的な見落とし（セキュリティ、データ損失、仕様違反）が見つかった場合のみ結論を修正する
- 「もっと良い案がある」程度では覆さない（Bikeshedding 防止）
- Reflection の Reflection は禁止

```markdown
### Reflection

致命的な見落とし: なし → 結論確定
```

### Step 5: AoT Synthesis（統合）

各 Atom の結論を統合し、最終決定と Action Items を導出する。

```markdown
### AoT Synthesis

**統合結論**: ...
**Action Items**:
1. ...
2. ...
```

## アンカーファイル

思考過程を必ず `docs/artifacts/YYYY-MM-DD-magi-{用途}.md` に書き出す。
フォーマットは `references/anchor-format.md` を参照。

- 書き込み権限: CASPAR のみ（Single-Writer）
- 読み取り権限: 全 MAGI（Multi-Reader）
- 削除: ユーザーのみ可能

## 参照

- SSOT: `docs/internal/06_DECISION_MAKING.md`
- アンカーフォーマット: `.claude/skills/magi/references/anchor-format.md`
- 仕様書: `docs/specs/magi-skill-spec.md`
- decision-making ルール: `.claude/rules/decision-making.md`
