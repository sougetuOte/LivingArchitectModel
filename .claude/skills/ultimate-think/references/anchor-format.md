# アンカーファイル テンプレート

アンカーファイル作成時は以下の構造に従う。
レベルに応じて不要なセクションは省略する。

```markdown
# ultimate-think Anchor: {用途}

**議題**: {元の議題}
**レベル**: {1/2/3}
**開始**: {YYYY-MM-DD HH:MM}

---

## Phase 0: Grounding

**Web サーチ結果**:
- {検索結果のサマリ 1}
- {検索結果のサマリ 2}

**複雑度判定**: Level {N} — {判定理由}

---

## AoT Decomposition

| Atom | 判断内容 | 依存 |
|:---|:---|:---|
| A1 | {判断 1} | なし |
| A2 | {判断 2} | A1 |

**依存関係 DAG**:
（Mermaid flowchart で記載）

---

## Atom A1: {判断内容}

### Three Agents Debate（Level 2+）

**[Mediator 結論]**:
- {結論}
- **Action**: {アクション}

（Atom ごとに繰り返す）

---

## Reflection（Level 3）

### Iteration 1

**検出事項**:
- {矛盾/見落とし}

**修正**:
- {Mediator による修正内容}

### Iteration 2（該当する場合）

**検出事項**: ...
**修正**: ...

**打ち切り理由**: stable / max_iterations_reached

---

## Synthesis

**統合結論**:
- {全 Atom の結論を統合した最終結論}

**Action Items**:
1. {アクション 1}
2. {アクション 2}
```
