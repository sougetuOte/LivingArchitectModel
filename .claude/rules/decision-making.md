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
4. **Reflection（新規追加）**: 全員で結論を検証（1回限り）。致命的な見落としがあれば修正

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
AoT Decomposition → MAGI Debate (各Atom) → Reflection → AoT Synthesis
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

### Reflection
致命的な見落とし: なし → 結論確定

### AoT Synthesis
**統合結論**: ...
```
