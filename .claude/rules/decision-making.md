# 意思決定プロトコル（MAGI System）

## MAGI System

> **SSOT**: `docs/internal/06_DECISION_MAKING.md`。本ファイルは実行時の要約版。

| Agent | ペルソナ | フォーカス |
|-------|---------|-----------|
| **MELCHIOR** | 科学者（Affirmative / 推進者） | Value, Speed, Innovation |
| **BALTHASAR** | 母（Critical / 批判者） | Risk, Security, Debt |
| **CASPAR** | 女（Mediator / 調停者） | Synthesis, Balance, Decision |

## Execution Flow

1. **Divergence**: MELCHIOR と BALTHASAR が意見を出し尽くす
2. **Debate**: 対立ポイントについて解決策を検討
3. **Convergence**: CASPAR が最終決定を下す
4. **gabriel Adversarial Probe（AoT 適用時のみ）**: 独立コンテキストで動作する gabriel subagent が CASPAR 結論を adversarial verification。verdict={confirmed/refuted/inconclusive} + severity + confidence を返す。詳細分岐は `.claude/skills/magi/SKILL.md` §Step 4.1 参照
   > **注記**: 旧 Reflection は Wave C（骨子 ②）で gabriel に置換済（ADR-0007 Accepted 2026-07-02）。B-4 監査（2026-06-19）で Reflection 変更率 0% を実測、独立コンテキストによる adversarial probe への構造的置換で解消

## AoT（Atom of Thought）

### 適用条件（いずれか該当）

- 判断ポイントが **2つ以上**
- 影響レイヤー/モジュールが **3つ以上**
- 有効な選択肢が **3つ以上**

### Atom の定義

| 条件 | 説明 |
|------|------|
| 自己完結性 | 他の Atom に依存せず独立処理可能 |
| インターフェース契約 | 入力と出力が明確 |
| エラー隔離 | 失敗しても他 Atom に影響しない |

### ワークフロー

```
AoT Decomposition → MAGI Debate (各Atom) → gabriel probe → AoT Synthesis

（軽量モード / 非 AoT: MAGI Debate のみで完結 / gabriel は起動しない）
```

## Output Format

```markdown
### AoT Decomposition
| Atom | 判断内容 | 依存 |
|------|----------|------|
| A1 | [判断1] | なし |
| A2 | [判断2] | A1 |

### Atom A1: [判断内容]
**[MELCHIOR]**: ...
**[BALTHASAR]**: ...
**[CASPAR]**: 結論: ...

### gabriel probe（AoT 適用時のみ）
- verdict: confirmed / refuted / inconclusive
- severity: critical / warning / info
- affected_atoms: [Atom ID の配列 / verdict=refuted 時は非空必須]
- reasoning: [判定理由 / 200-1000 字]
- recommended_action: proceed / re-magi / abort
- confidence: 0.0-1.0（0.3 未満なら verdict=inconclusive 強制）
- 処理: `recommended_action` に応じた分岐（優先順位: **abort > critical+re-magi > warning > info > confirmed > inconclusive**）。詳細分岐は SKILL.md §Step 4.1。親 SSOT: `docs/internal/06_DECISION_MAKING.md` §6.5-6.6

### AoT Synthesis
**統合結論**: ...
```
