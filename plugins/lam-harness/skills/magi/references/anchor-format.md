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

| Atom | 判断内容 | 読む状態 | 書く状態 |
|:---|:---|:---|:---|
| A1 | {判断 1} | {参照する事実・ファイル・前段の結論} | {この Atom が変える対象} |
| A2 | {判断 2} | {同上。A1 の結論を読むならそう書く} | {同上} |

> **「依存」「並列可否」「独立」を列に持たないこと**。それらは結論であって事実ではなく、
> 宣言すると証明されないまま真として扱われる（要素 n 個で n(n−1)/2 本の暗黙の主張が立つ）。
> 読む状態・書く状態を書けば、**依存は「A の書く状態を B が読む」として、
> 並列可否は「書込集合が交わらない」として導出できる**。根拠: HGA #32（2026-09-05）。

**依存関係 DAG**（**上表から導出する / 宣言しない**）:
（Mermaid flowchart で記載 —— **辺は「A の書く状態を B が読む」ときにのみ引く**。
上表に無い依存を図で足さないこと。図と表が食い違うなら**表が正**）

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
