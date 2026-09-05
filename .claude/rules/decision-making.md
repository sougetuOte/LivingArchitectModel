# 意思決定プロトコル（MAGI System）

## MAGI System

> **SSOT**: `docs/internal/06_DECISION_MAKING.md`。本ファイルは実行時の要約版。

| Agent | ペルソナ | フォーカス |
|-------|---------|-----------|
| **MELCHIOR** | 科学者（Affirmative / 推進者） | Value, Speed, Innovation |
| **BALTHASAR** | 母（Critical / 批判者） | Risk, Security, Debt |
| **CASPAR** | 女（Mediator / 調停者） | Synthesis, Balance, Decision（合意に至らない場合は独断で決定を下す権限を持つ / 親 §1 参照） |

## Execution Flow

> MAGI ログ冒頭での**モード宣言**は `.claude/skills/magi/SKILL.md` §モード判定（FR-W-C-3）が担う。
> **モードの判定基準そのものは下記 §AoT 適用条件**（および `phase-rules.md` BUILDING §Self-Check）に残る。

1. **Divergence**: MELCHIOR と BALTHASAR が意見を出し尽くす
2. **Debate**: 対立ポイントについて解決策を検討
3. **Convergence**: CASPAR が最終決定を下す
4. **gabriel Adversarial Probe（AoT 適用時のみ）**: 独立コンテキストで動作する gabriel subagent が CASPAR 結論を adversarial verification。verdict={confirmed/refuted/inconclusive} + severity + confidence を返す。詳細分岐は `.claude/skills/magi/SKILL.md` §Step 4.1 参照
   > **注記**: 旧 Reflection は Wave C（骨子 ②）で gabriel に置換済（ADR-0007 Accepted 2026-07-02）。B-4 監査（2026-06-19）で Reflection 変更率 0% を実測、独立コンテキストによる adversarial probe への構造的置換で解消

## AoT（Atom of Thought）

### 適用条件（いずれか該当）

> **本節が 3 軸の値の正本である**。同じ値が `phase-rules.md` BUILDING §AoT/MAGI 適用条件 Self-Check（実務チェックリスト）と `magi/SKILL.md` §適用条件（起動判定）にもあり、**変更時は 3 箇所を同時に直す**（2026-08-27 に表記揺れ「2つ以上」/「2 つ以上」を統一 / probe 2 巡目の指摘）。

- 判断ポイントが **2 つ以上**
- 影響レイヤー/モジュールが **3 つ以上**
- 有効な選択肢が **3 つ以上**

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

> **AoT フレームワーク保存**: 上記 §Atom の定義・適用条件は無改変で保存する（**NFR-W-C-6 MUST NOT** / 詳細: 親 §6.3）。破壊は統合テスト 3 系統（`.claude/tests/wave_c/` **31+21+16 件** / 2026-08-20 に `--collect-only` で実測）が拾う設計。

## Output Format

```markdown
### AoT Decomposition
| Atom | 判断内容 | 読む状態 | 書く状態 |
|------|----------|----------|----------|
| A1 | [判断1] | [参照する事実・ファイル・前段の結論] | [この Atom が変える対象] |
| A2 | [判断2] | [同上。A1 の結論を読むならそう書く] | [同上] |

> **「依存」「並列可否」「独立」を列に持たないこと**。それらは結論であって事実ではなく、
> 宣言すると証明されないまま真として扱われる（要素 n 個で n(n−1)/2 本の暗黙の主張が立つ）。
> 読む状態・書く状態を書けば、**依存は「A の書く状態を B が読む」として、
> 並列可否は「書込集合が交わらない」として導出できる**。根拠: HGA #32（2026-09-05）。

### Atom A1: [判断内容]
**[MELCHIOR]**: ...
**[BALTHASAR]**: ...
**[CASPAR]**: 結論: ...
**採用しなかった選択肢とその理由** (**MUST**): [列挙 / §2 Step 3 準拠 / 親 §2 参照]

### gabriel probe（AoT 適用時のみ）
- verdict: confirmed / refuted / inconclusive
- severity: critical / warning / info
- affected_atoms: [Atom ID の配列 / verdict=refuted 時は非空必須]
- reasoning: [判定理由 / 200-1000 字]
- recommended_action: proceed / re-magi / abort
- confidence: 0.0-1.0（0.3 未満なら verdict=inconclusive 強制）
- 処理: `recommended_action` に応じた分岐（優先順位: **abort > critical+re-magi > warning > info > confirmed > inconclusive**）。詳細分岐は SKILL.md §Step 4.1。親 SSOT: `docs/internal/06_DECISION_MAKING.md` §6.5-6.6
- プローブ観点（rubric 5 観点）: 論理的一貫性 / 仕様整合 / リスク見落とし / 前提検証 / 境界条件（詳細: 親 §6.4）
- **opt-out**: 条件・AUTONOMOUS での扱いは SKILL.md §Step 4.2（親 §6.8）

### AoT Synthesis
**統合結論**: ...
```

## 適用場面（When to Use）

詳細は親 SSOT `docs/internal/06_DECISION_MAKING.md` §4 参照（ライブラリ選定 / DB スキーマ変更 / 大規模リファクタリング / 曖昧要件）。
