# 意思決定プロトコル

## Purpose

重要な意思決定において「3 つの視点」と AoT を適用するプロトコル。

## Three Agents Model

| Agent | ペルソナ | フォーカス |
|-------|---------|-----------|
| **Affirmative** | 推進者 | Value, Speed, Innovation |
| **Critical** | 批判者 | Risk, Security, Debt |
| **Mediator** | 調停者 | Synthesis, Balance, Decision |

## Execution Flow

1. **Divergence**: Affirmative と Critical が意見を出し尽くす
2. **Debate**: 対立ポイントについて解決策を検討
3. **Convergence**: Mediator が最終決定を下す

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
AoT Decomposition → Three Agents Debate (各Atom) → AoT Synthesis
```

## Output Format

```markdown
### AoT Decomposition
| Atom | 判断内容 | 依存 |
|------|----------|------|
| A1 | [判断1] | なし |
| A2 | [判断2] | A1 |

### Atom A1: [判断内容]
**[Affirmative]**: ...
**[Critical]**: ...
**[Mediator]**: 結論: ...

### AoT Synthesis
**統合結論**: ...
```

## References

- `docs/internal/06_DECISION_MAKING.md`（SSOT）
