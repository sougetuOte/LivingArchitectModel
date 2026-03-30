# モジュール間帰責判断 仕様書

**バージョン**: 0.2
**作成日**: 2026-03-31
**フェーズ**: PLANNING
**関連仕様**:
- `docs/specs/scalable-code-review-spec.md`（Scalable Code Review）
- `docs/specs/green-state-definition.md`（Green State 定義）
- `.claude/rules/code-quality-guideline.md`（品質判断基準）
- `.claude/commands/full-review.md`（/full-review コマンド）

---

## 1. Problem Statement

### 1.1 現状の課題

`/full-review` は単一の対象パスに対する「深さ方向の自動ループ」に特化しているが、
**複数 Wave で構築されたモジュール間の境界に曖昧な不具合が存在する場合の帰責判断基準がない**。

典型的なシナリオ:

- Wave 1 で Module A を実装し、`/full-review` で Green State を達成
- Wave 2 で Module Z を実装。Z は A の関数を呼び出す
- Wave 1+2 をまとめて `/full-review` した際、A と Z の境界に不具合を発見
- A が悪いのか、Z が悪いのか、仕様が曖昧なのかを判断する基準がない

### 1.2 解決後の理想状態

- `/full-review` がモジュール間境界の Issue を検出した際、**帰責のヒント**が Issue に付与される
- 人間が帰責判断を行うための**フローチャート**が品質基準に明記されている
- 帰責判断が必要な Issue は**視認性の高いマーカー**で表示され、見落としにくい

### 1.3 Non-Goals（非スコープ）

- Issue の重要度分類（Critical/Warning/Info）への帰責の組み込み — 帰責は参考情報であり、重要度判定ロジックには影響しない
- 自動帰責による修正先の自動決定 — 最終判断は人間が行う
- `Issue` dataclass へのフィールド追加 — 帰責ヒントは Agent 出力のマーカーとレポート表示で実現し、データモデル変更は行わない
- Green State 判定条件の変更 — G1〜G5 の判定ロジックは変更しない

---

## 2. User Story

**誰が**: `/full-review` を実行する開発者（LAM ユーザー）
**何をしたいか**: モジュール間境界の Issue を発見した際に、どのモジュールに修正責任があるかの判断材料を得たい
**なぜなら**: 帰責が曖昧なまま修正すると、根本原因ではなく症状を修正してしまい、再発するから

---

## 3. 機能要件

### FR-1: 帰責判断フローチャート（Plan B）

`code-quality-guideline.md` に**モジュール間帰責判断**セクションを追加する。

フローチャートの判断ロジック:

```
モジュール間境界に Issue を発見
  │
  ├─ 仕様書（docs/specs/）に該当 API/インターフェースの定義がある？
  │    ├─ Yes → 仕様と乖離している側が修正対象（仕様ドリフト帰責）
  │    └─ No  → 仕様の欠落が根本原因 → PM級（仕様明確化が先決）
  │
  ├─ 上流モジュールの契約カードと下流の呼び出しに矛盾がある？
  │    ├─ 下流が契約違反 → 下流モジュールを修正
  │    └─ 上流の契約自体が不十分/不正確 → 上流の契約（≒仕様）を更新 → PM級
  │
  └─ 単体では問題なく、組み合わせで初めて顕在化する？
       → 上流の Green State は「単体での Green State」であり、結合時の再審査で
         Issue が出ることは正常動作
       → 修正は「変更コストが小さい側」に寄せる（Postel's Law 的判断）
       → 判断が困難な場合は PM級にエスカレーション
```

**義務レベル**:

- FR-1a: `/full-review` の Stage 3 レポートおよび Stage 4 修正時に、モジュール間 Issue に対しては本フローチャートを参照して帰責を判断すること — **SHOULD**
- FR-1b: モジュール間 Issue が検出された場合、帰責判断の結果（フローチャートの適用有無を問わず）を監査レポートに記録すること — **MUST**

### FR-2: 契約カード帰責ヒント（Plan C）

#### FR-2a: 契約カードへの帰責コンテキスト追加

`ContractCard` の `format_contract_cards_for_prompt()` が生成するプロンプトテキストに、
帰責判断のヒントを追加する。

追加する指示テキスト（`build_review_prompt_with_contracts()` の header 部分）:

```
以下は上流モジュールの契約です。
これらの前提条件・保証に違反する呼び出しがないか確認してください。

【帰責判断ガイド】
違反を発見した場合、以下の基準で帰責先を判定してください:
1. 仕様書に定義がある場合 → 仕様と乖離している側が修正対象
2. 仕様書に定義がない場合 → 仕様の欠落として PM級にエスカレーション
3. 下流が上流の契約に違反している場合 → 下流が修正対象
4. 上流の契約自体が不十分な場合 → 上流の契約更新が必要（PM級）
```

**変更対象**: `orchestrator.py` の `build_review_prompt_with_contracts()` 関数の header 文字列のみ。

**義務レベル**: Agent プロンプトに帰責ガイドを含めること — **MUST**

#### FR-2b: Agent 出力の帰責マーカー

帰責マーカーの出力指示は、`build_review_prompt_with_contracts()` のプロンプトに集約する（FR-2a と同一箇所）。
契約カードが注入される場合（＝モジュール間依存がある場合）のみ帰責マーカー指示がプロンプトに含まれるため、
Agent 定義ファイル（quality-auditor.md, code-reviewer.md）への変更は「帰責観点がある」ことの認知のみに留める。

出力マーカー形式:

```
---BLAME-HINT---
issue: [Issue の要約]
suspected_responsible: upstream | downstream | spec_ambiguity | unknown
module: [帰責先モジュール名]
reason: [判断理由の1行要約]
---END-BLAME-HINT---
```

**義務レベル**:

- FR-2b-i: Agent は**モジュール間境界の Issue を検出した場合のみ**、帰責マーカーを出力すること — **SHOULD**
- FR-2b-ii: マーカーがない場合はフォールバック（帰責ヒントなしで従来通り処理）すること — **MUST**（ロバスト性）

#### FR-2c: 帰責マーカーのパース

`card_generator.py` に `parse_blame_hint()` 関数を追加する。

- 入力: Agent 出力文字列
- 出力: `list[BlameHint]`（0個以上）
- `BlameHint` は辞書型（`dict[str, str]`）で、`issue`, `suspected_responsible`, `module`, `reason` をキーとする。全フィールドが存在しない場合も、抽出されたフィールドのみで有効な `BlameHint` とする
- マーカーが存在しない場合は空リストを返す
- `suspected_responsible` の値が `upstream`, `downstream`, `spec_ambiguity`, `unknown` のいずれにも該当しない場合、`unknown` に正規化すること — **MUST**

**義務レベル**: パース関数はマーカー不在時にエラーを発生させないこと — **MUST**

### FR-3: 監査レポートの帰責表示

#### FR-3a: 帰責判断要求マーカー

Stage 3 の統合レポートにおいて、帰責ヒントが付与された Issue には以下のマーカーを付与する:

```
[W-3] Warning [SE]: Module Z が Module A の validate() を未検証の引数で呼び出し (z.py:42)
      ** 帰責判断求む ** → 下流(Z)の契約違反の疑い（理由: A の precondition に型チェック要求あり）
```

**表示ルール**:

- `** 帰責判断求む **` は帰責ヒントが存在する全ての Issue に付与する — **MUST**
- `→` 以降に `suspected_responsible` と `reason` を表示する — **MUST**
- 帰責ヒントがない Issue には付与しない — **MUST**

#### FR-3b: レポート末尾の帰責サマリー

統合レポートの末尾に帰責判断が必要な Issue の一覧を集約する:

```
=== 帰責判断が必要な Issue ===
| # | Issue | 帰責候補 | モジュール | 理由 |
|---|-------|---------|-----------|------|
| 1 | [W-3] | downstream | Module Z | A の precondition に型チェック要求あり |
| 2 | [C-1] | spec_ambiguity | - | 該当 API の仕様定義なし |

上記 Issue は自動修正の対象外です。帰責判断後に修正方針を指示してください。
PM級の仕様明確化が必要な Issue: 1件
```

**義務レベル**: 帰責判断が必要な Issue が 1 件以上ある場合、サマリーを出力すること — **MUST**

### FR-4: Stage 4 修正時の帰責考慮

Stage 4（修正フェーズ）において、帰責ヒントが付与された Issue は以下のように扱う:

- `suspected_responsible` が `spec_ambiguity` → **自動修正しない**。PM級としてユーザーに提示
- `suspected_responsible` が `upstream` または `downstream` → 帰責ヒントを添えてユーザーに提示し、修正方針の確認を求める。ただし `.claude/rules/permission-levels.md` の PG 級に該当する修正（フォーマット、typo、lint 違反等）は帰責ヒントに関わらず自動修正可
- `suspected_responsible` が `unknown` → 従来通りの重要度ベース修正

**義務レベル**: `spec_ambiguity` の Issue を自動修正してはならない — **MUST NOT**

---

## 4. 非機能要件

### NFR-1: 後方互換性

- `ContractCard` dataclass のフィールド追加は行わない（Non-Goals）
- 既存の `parse_contract()` の動作を変更しない
- 帰責マーカーを含まない Agent 出力を `/full-review` に与えた場合、Stage 2〜5 が従来と同一のフォーマットで完了すること — **MUST**

### NFR-2: プロンプトサイズ

- FR-2a で追加するプロンプトテキストは **200 トークン以下** であること — **MUST**（AC-9 で検証）
- `build_review_prompt_with_contracts()` が生成するプロンプト全体に対する増加率は 10% 以下であること — **SHOULD**。ただし AC-9（絶対量 200 トークン以下）を常に優先する
- トークン数の計測: 追加テキストの文字数を 4 で除算した近似値を用いる（手動確認）

### NFR-3: パース堅牢性

- `parse_blame_hint()` は不正な形式のマーカーに対してエラーを発生させず、空リストを返すこと
- 部分的に壊れたマーカー（`---BLAME-HINT---` はあるが `---END-BLAME-HINT---` がない等）も安全に処理すること

---

## 5. 変更対象ファイル一覧

| ファイル | 変更内容 | 権限等級 |
|---------|---------|---------|
| `.claude/rules/code-quality-guideline.md` | 帰責判断フローチャート追加（FR-1） | **PM** |
| `.claude/hooks/analyzers/orchestrator.py` | `build_review_prompt_with_contracts()` の header 拡張（FR-2a） | SE |
| `.claude/hooks/analyzers/card_generator.py` | `parse_blame_hint()` 関数追加（FR-2c） | SE |
| `.claude/commands/full-review.md` | Stage 2/3/4 の帰責関連手順追加（FR-3a/3b, FR-4） | SE |
| `.claude/agents/quality-auditor.md` | レビュー観点に帰責項目を参照追加（FR-2b） | SE |
| `.claude/agents/code-reviewer.md` | レビュー観点に帰責項目を参照追加（FR-2b） | SE |
| `.claude/hooks/analyzers/tests/test_card_generator.py` | `parse_blame_hint()` のテスト追加 | SE |
| `.claude/hooks/analyzers/tests/test_orchestrator.py` | プロンプト帰責ガイドのテスト追加 | SE |

> **注**: `.claude/agents/` への変更は SE 級とする。帰責の具体的な指示はプロンプト（`orchestrator.py`）に集約されており、Agent 定義への変更は「帰責観点がある」ことの認知追加のみであるため、Agent の振る舞いを根本的に変えるものではない。

---

## 6. Acceptance Criteria（完了条件）

- [ ] AC-1: `code-quality-guideline.md` にモジュール間帰責判断フローチャートが存在する
- [ ] AC-2: `build_review_prompt_with_contracts()` のプロンプトに帰責ガイドが含まれる
- [ ] AC-3: `parse_blame_hint()` が正常なマーカーから `BlameHint` を抽出できる
- [ ] AC-4: `parse_blame_hint()` がマーカー不在時に空リストを返す
- [ ] AC-5: `parse_blame_hint()` が不正形式のマーカーに対してエラーを発生させない
- [ ] AC-6: `/full-review` の Stage 3 レポートに `** 帰責判断求む **` マーカーが表示される（帰責ヒントがある場合）
- [ ] AC-7: `/full-review` の Stage 3 レポート末尾に帰責サマリーテーブルが出力される（帰責 Issue が 1 件以上の場合）
- [ ] AC-8: `spec_ambiguity` の Issue が Stage 4 で自動修正されない
- [ ] AC-9: Agent プロンプトの帰責ガイド追加によるトークン増加が 200 トークン以下（文字数/4 の近似値で計測）
- [ ] AC-10: 帰責マーカーを含まない Agent 出力で `/full-review` が Stage 2〜5 を従来通り完了する（FR-2b-ii フォールバック検証）
- [ ] AC-11: `upstream` または `downstream` の帰責ヒント付き Issue に対し、修正方針確認プロンプトが表示される（PG 級を除く）
- [ ] AC-12: `parse_blame_hint()` が無効な `suspected_responsible` 値を `unknown` に正規化する

---

## 7. Alternatives Considered

| 選択肢 | 概要 | 却下理由 |
|--------|------|---------|
| A: フル帰責システム | `Issue` dataclass にフィールド追加、全 analyzer 改修（14 ファイル・3800 行） | LLM 帰責精度が未検証のまま大規模改修はリスクが高い |
| B のみ | フローチャートだけ追加 | 人間の判断基準は整うが、Agent からの判断材料が増えない |

**採用**: B+C（フローチャート + 契約カード強化）。既存インフラを活かし、最小変更で判断材料を増やす。

---

## 8. MAGI Review

### [MELCHIOR]（推進者）

- B+C は既存インフラ（契約カード、トポロジカル順レビュー）を活かす効率的なアプローチ
- `Issue` dataclass を変更しないことで、全 analyzer への波及を完全に回避
- 帰責ヒントは「参考情報」としての位置づけにより、精度問題があっても被害なし

### [BALTHASAR]（批判者）

- Agent が帰責マーカーを出し忘れるリスクあり — ただし FR-2c でフォールバック済み
- `full-review.md` が既に 14K+ tokens で、さらに指示を追加する負荷 — NFR-2 で上限を設定
- 帰責ヒントの精度が低い場合、かえってノイズになる可能性 — `** 帰責判断求む **` マーカーで「最終判断は人間」と明示しており、ミスリード耐性あり

### [CASPAR]（調停者）

- **結論**: B+C で進める。リスクは全て許容範囲内。
- 帰責を「強制力のある判定」に組み込まない設計判断が、安全マージンを確保している
- 唯一の注意点: FR-1 の `code-quality-guideline.md` 変更は PM 級。BUILDING フェーズ開始前に承認を得ること

### [Reflection]

致命的な見落とし: なし。B+C の設計判断は、帰責を「参考情報」に留めることでリスクを封じ込めており、結論を修正する必要はない。
