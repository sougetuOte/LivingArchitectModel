# モジュール間帰責判断 設計書

**バージョン**: 0.2
**作成日**: 2026-03-31
**対応仕様**: `docs/specs/cross-module-blame-spec.md`

---

## 0. Problem Statement

`/full-review` で複数 Wave のモジュールをまとめてレビューした際、モジュール間境界の Issue について「どのモジュールに修正責任があるか」の判断基準がない。本設計は、既存の契約カードインフラを活かして帰責ヒントを提供し、人間の判断を支援することで解決する。

---

## 1. 設計方針

### 1.1 Alternatives Considered（却下した選択肢）

| 選択肢 | 概要 | 却下理由 |
|--------|------|---------|
| A: フル帰責システム | `Issue` dataclass にフィールド追加、全 analyzer 改修 | 14 ファイル・3800 行の大規模改修。LLM 帰責精度が未検証のままリスクが高い |
| B のみ | フローチャートだけ追加 | 人間の判断基準は整うが、Agent からの判断材料が増えない |

**採用**: B+C（フローチャート + 契約カード強化）。既存インフラを活かし、最小変更で判断材料を増やす。

### 1.2 Success Criteria

- 帰責判断が必要な Issue が `/full-review` レポートで `** 帰責判断求む **` 付きで表示される（AC-6）
- 帰責 Issue が 1 件以上の場合、レポート末尾に帰責サマリーテーブルが出力される（AC-7）
- `spec_ambiguity` の Issue が Stage 4 で自動修正されない（AC-8）
- `parse_blame_hint()` のテストが全パスする（AC-3, AC-4, AC-5）
- 帰責マーカーなしの Agent 出力で `/full-review` が従来通り完了する（AC-10）
- 既存テスト（435 件）が全パスする（回帰なし）
- `scalable-code-review-design.md` にクロスリファレンスが追加されている

---

## 2. 変更設計

### 2.1 FR-1: `code-quality-guideline.md` 帰責フローチャート

**変更箇所**: `.claude/rules/code-quality-guideline.md`

既存の「判断に迷った場合 > フローチャート」セクションの後に、新セクション「モジュール間帰責判断」を追加する。

```markdown
### モジュール間帰責判断

複数モジュールにまたがる Issue で、修正責任が曖昧な場合の判断基準。

#### フローチャート

[仕様書 FR-1 のフローチャートをそのまま記載]

#### 帰責の分類

| 分類 | 意味 | 対応 |
|------|------|------|
| upstream | 上流モジュールの契約/実装に問題 | 上流を修正 |
| downstream | 下流モジュールが契約に違反 | 下流を修正 |
| spec_ambiguity | 仕様の欠落/曖昧さが根本原因 | PM級（仕様明確化が先決） |
| unknown | 判断不能 | PM級にエスカレーション |
```

**権限等級**: PM（`.claude/rules/` 配下）

### 2.2 FR-2a: `orchestrator.py` プロンプト拡張

**変更箇所**: `.claude/hooks/analyzers/orchestrator.py` L292-297

現在の header:

```python
header = (
    "以下は上流モジュールの契約です。"
    "これらの前提条件・保証に違反する呼び出しがないか確認してください。\n\n"
    + contracts_text
    + "\n\n"
)
```

変更後の header:

```python
header = (
    "以下は上流モジュールの契約です。"
    "これらの前提条件・保証に違反する呼び出しがないか確認してください。\n\n"
    "【帰責判断ガイド】\n"
    "違反を発見した場合、以下の基準で帰責先を判定してください:\n"
    "1. 仕様書に定義がある → 仕様と乖離している側が修正対象\n"
    "2. 仕様書に定義がない → 仕様の欠落として PM級エスカレーション\n"
    "3. 下流が上流の契約に違反 → 下流が修正対象\n"
    "4. 上流の契約自体が不十分 → 上流の契約更新が必要（PM級）\n\n"
    "帰責判断が必要な Issue には以下のマーカーで出力してください:\n"
    "---BLAME-HINT---\n"
    "issue: [Issue の要約]\n"
    "suspected_responsible: upstream | downstream | spec_ambiguity | unknown\n"
    "module: [帰責先モジュール名]\n"
    "reason: [判断理由の1行要約]\n"
    "---END-BLAME-HINT---\n\n"
    + contracts_text
    + "\n\n"
)
```

**設計判断**: 帰責マーカーの出力指示を `build_review_prompt_with_contracts()` に集約する。理由:
- 契約カードが注入される場合（＝モジュール間依存がある場合）のみ帰責判断が必要
- 契約カードがない場合（単一モジュール/依存なし）は帰責マーカーの指示自体が不要
- Agent 定義ファイル（quality-auditor.md, code-reviewer.md）の変更を最小化できる

**トークン見積もり**: 追加テキストは約 150 トークン（NFR-2 の 200 トークン上限内）。

### 2.3 FR-2b: Agent 定義ファイルの変更

**変更箇所**: `.claude/agents/quality-auditor.md`, `.claude/agents/code-reviewer.md`

FR-2a でプロンプトに帰責指示を集約するため、Agent 定義ファイル自体への変更は**最小限**とする。

追加内容（両 Agent 共通、レビュー観点セクションに 1 項目追加）:

```markdown
### N. モジュール間帰責（契約カード注入時のみ）
- 上流モジュールの契約に違反する呼び出しがないか
- 帰責判断が必要な場合は BLAME-HINT マーカーで出力
- 詳細な指示はレビュープロンプト内の【帰責判断ガイド】に従う
```

**設計判断**: 帰責の具体的な指示はプロンプト（FR-2a）に委ね、Agent 定義には「帰責観点がある」ことの認知だけを追加する。これにより:
- Agent 定義の肥大化を防ぐ
- 帰責指示の一元管理が可能（`orchestrator.py` のみ変更すればよい）

### 2.4 FR-2c: `parse_blame_hint()` 関数

**追加箇所**: `.claude/hooks/analyzers/card_generator.py`

既存の `parse_contract()` と同じパターンで実装する。

```python
# マーカー定数
_BLAME_START = "---BLAME-HINT---"
_BLAME_END = "---END-BLAME-HINT---"
_BLAME_FIELDS = ("issue", "suspected_responsible", "module", "reason")

BlameHint = dict[str, str]


def parse_blame_hint(agent_output: str) -> list[BlameHint]:
    """Agent 出力から BLAME-HINT マーカー間のフィールドを抽出する。

    複数の BLAME-HINT ブロックに対応。
    マーカーがない場合は空リストを返す（フォールバック）。
    """
    hints: list[BlameHint] = []
    search_start = 0

    while True:
        start_idx = agent_output.find(_BLAME_START, search_start)
        if start_idx == -1:
            break
        end_idx = agent_output.find(_BLAME_END, start_idx)
        if end_idx == -1:
            search_start = start_idx + len(_BLAME_START)
            continue  # 閉じマーカーなし → 次ブロックを探索（NFR-3）

        content = agent_output[start_idx + len(_BLAME_START):end_idx]
        hint: BlameHint = {}
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            for field in _BLAME_FIELDS:
                prefix = field + ":"
                if line.startswith(prefix):
                    hint[field] = line[len(prefix):].strip()
                    break

        if hint:  # 空でなければ追加
            hints.append(hint)

        search_start = end_idx + len(_BLAME_END)

    return hints
```

**設計判断**:
- `parse_contract()` と同じマーカーベースパース方式を採用（一貫性）
- 複数ブロック対応: `parse_contract()` は単数対応（モジュールに契約カードは 1 枚のみ）だが、1 回のレビューで複数の帰責 Issue が出うるため `parse_blame_hint()` は複数対応とする
- `BlameHint` は `dict[str, str]` 型エイリアスとし、dataclass にしない（Non-Goals: データモデル追加なし）
- `suspected_responsible` の値バリデーション: `_VALID_RESPONSIBLE = frozenset({"upstream", "downstream", "spec_ambiguity", "unknown"})` で検証し、範囲外の値は `unknown` に正規化する（仕様書 FR-2c）

### 2.5 FR-3: `full-review.md` レポート形式拡張

**変更箇所**: `.claude/commands/full-review.md`

#### Stage 2 Step 3（並列監査）への追加

Agent 出力から `parse_blame_hint()` で帰責ヒントを抽出する手順を追加:

```
各 Agent 完了後:
1. parse_responsibility() で責務フィールドを抽出（既存）
2. parse_contract() で契約フィールドを抽出（既存）
3. parse_blame_hint() で帰責ヒントを抽出（新規）
4. 帰責ヒントを Issue ID と紐付けてレポート統合に渡す
```

#### Stage 3 Step 5（レポート統合）への追加

統合レポートの Issue 表示に帰責マーカーを追加:

```
通常の Issue:
[W-1] Warning [PG]: <内容> (file:line)

帰責ヒント付き Issue:
[W-3] Warning [SE]: <内容> (file:line)
      ** 帰責判断求む ** → downstream(Module Z): A の precondition に型チェック要求あり
```

帰責ヒント付き Issue が **1 件以上の場合のみ**、レポート末尾に帰責サマリーテーブルを追加（仕様書 FR-3b のフォーマット）。0 件の場合はサマリーを出力しない。

#### Stage 4 への追加

`spec_ambiguity` の Issue を自動修正対象から除外するガードを追加:

```
修正前チェック:
- 帰責ヒントが spec_ambiguity → 自動修正スキップ、PM級として提示
- 帰責ヒントが upstream/downstream → ヒントを添えてユーザーに確認を求める
  （ただし PG 級の修正（フォーマット、typo、lint 違反等）は帰責ヒントに関わらず自動修正可）
- 帰責ヒントが unknown または帰責ヒントなし → 従来通り
```

> **注**: このセクションは仕様書の FR-2b（full-review.md 部分）・FR-3a・FR-3b・FR-4 に対応する。

### 2.6 データフロー全体図

```
Stage 1: 依存グラフ構築（既存）
  ↓
Stage 2: トポロジカル順レビュー
  ├─ build_review_prompt_with_contracts()
  │   └─ 帰責判断ガイド + BLAME-HINT マーカー指示を注入（FR-2a 新規）
  ├─ Agent 実行（quality-auditor / code-reviewer）
  │   └─ 帰責が必要な Issue に BLAME-HINT マーカーを出力（FR-2b）
  └─ parse_blame_hint() で帰責ヒントを抽出（FR-2c 新規）
  ↓
Stage 3: レポート統合
  ├─ Issue に ** 帰責判断求む ** マーカーを付与（FR-3a 新規）
  └─ レポート末尾に帰責サマリーテーブル出力（FR-3b 新規）
  ↓
Stage 4: 修正
  └─ spec_ambiguity は自動修正スキップ（FR-4 新規）
```

---

## 3. テスト方針

### 3.1 `parse_blame_hint()` のユニットテスト

| テストケース | 入力 | 期待出力 |
|-------------|------|---------|
| 正常: 単一マーカー | 正常形式の BLAME-HINT ブロック 1 つ | `[{issue: ..., suspected_responsible: ..., module: ..., reason: ...}]` |
| 正常: 複数マーカー | BLAME-HINT ブロック 2 つ | 2 要素のリスト |
| マーカーなし | 通常の Agent 出力 | `[]` |
| 閉じマーカーなし | `---BLAME-HINT---` のみ | `[]` |
| 空コンテンツ | マーカーはあるが中身が空 | `[]` |
| 部分フィールド | `issue` と `reason` のみ | `[{issue: ..., reason: ...}]`（部分的に抽出） |
| 既存 parse_contract と共存 | CONTRACT-CARD + BLAME-HINT 混在 | 各パーサーが独立に動作 |

### 3.2 `build_review_prompt_with_contracts()` のテスト

| テストケース | 確認内容 |
|-------------|---------|
| 契約カードあり | header に「帰責判断ガイド」と「BLAME-HINT マーカー指示」が含まれる |
| 契約カードなし（空リスト） | 従来の `build_review_prompt()` と同一出力（帰責指示なし） |
| トークン数 | 帰責ガイド追加分が 200 トークン以下（追加テキストの文字数/4 の近似値で計測） |

### 3.3 回帰テスト

既存テスト（435 件）が全パスすること。

---

## 4. 影響範囲と依存関係

```
orchestrator.py (FR-2a)
  └─ card_generator.py の format_contract_cards_for_prompt() を呼び出し（既存、変更なし）
  （parse_blame_hint() は full-review.md の手順書に従い LLM が直接呼び出す。orchestrator.py への import は不要）

card_generator.py (FR-2c)
  └─ parse_blame_hint() を新規追加。既存関数への変更なし

full-review.md (FR-3, FR-4)
  └─ Stage 2/3/4 の指示テキスト変更。実装コードへの影響なし

code-quality-guideline.md (FR-1)
  └─ 独立。他ファイルへの影響なし

quality-auditor.md / code-reviewer.md (FR-2b)
  └─ レビュー観点に 1 項目追加。既存観点への影響なし
```

**循環依存**: なし
**破壊的変更**: なし（全て追加のみ）
