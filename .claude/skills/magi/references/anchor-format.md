# アンカーファイル テンプレート

lam-orchestrate の構造化思考で使用するアンカーファイルの形式。
アンカーファイル作成時は以下の構造に従う。
レベルに応じて不要なセクションは省略する。

```markdown
# Structured Thinking Anchor: {用途}

**議題**: {元の議題}
**レベル**: {1/2/3}
**開始**: {YYYY-MM-DD HH:MM}

---

## Phase 0: Grounding

**Web サーチ結果**（WebSearch 利用可能な場合のみ。不可時はスキップ）:
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

## gabriel probe（AoT 適用時のみ）

> **旧 Reflection は廃止**（gabriel probe に統合済 / Wave C 骨子 ② / ADR-0007 Accepted 2026-07-02）。
> B-4 監査（2026-06-19）実機計測: Reflection の初回変更率 0%（全 7 件「致命的な見落とし: なし → 結論確定」）で「無効な安全網」であったため、独立コンテキストの adversarial probe へ構造的に置換した。詳細は `.claude/skills/magi/SKILL.md` §Step 4 参照。

- verdict: confirmed / refuted / inconclusive
- severity: critical / warning / info
- affected_atoms: [Atom ID の配列 / verdict=refuted 時は非空必須]
- reasoning: [判定理由 / 200-1000 字]
- recommended_action: proceed / re-magi / abort
- confidence: 0.0-1.0（0.3 未満なら verdict=inconclusive 強制）
- 処理: `recommended_action` に応じた分岐（優先順位: abort > critical+re-magi > warning > info > confirmed > inconclusive）。詳細分岐は `.claude/skills/magi/SKILL.md` §Step 4.1 参照

---

## Synthesis

**統合結論**:
- {全 Atom の結論を統合した最終結論}

**Action Items**:
1. {アクション 1}
2. {アクション 2}
```
