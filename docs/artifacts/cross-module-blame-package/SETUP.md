# Cross-Module Blame — セットアップガイド

モジュール間帰責判断機能を他の LAM プロジェクトに導入する手順。

## 前提条件

- LAM v4.5.0 以上（Scalable Code Review 機能が必要）
- `.claude/hooks/analyzers/card_generator.py` に `parse_contract()` が存在すること
- `.claude/hooks/analyzers/orchestrator.py` に `build_review_prompt_with_contracts()` が存在すること
- `.claude/commands/full-review.md` が存在すること

## パッケージ内容

```
cross-module-blame-package/
├── SETUP.md                          # 本ファイル
├── blame_hint_parser.py              # スタンドアロン版 parse_blame_hint()
├── blame_guide_prompt.txt            # Agent プロンプトに追加する帰責ガイドテキスト
├── blame_flowchart.md                # code-quality-guideline.md に追加するフローチャート
├── cross-module-blame-spec.md        # 仕様書（参考）
├── cross-module-blame-design.md      # 設計書（参考）
├── card_generator.patch              # card_generator.py への差分パッチ
├── orchestrator.patch                # orchestrator.py への差分パッチ
├── code-quality-guideline.patch      # code-quality-guideline.md への差分パッチ
├── full-review.patch                 # full-review.md への差分パッチ
├── agents.patch                      # Agent 定義への差分パッチ
└── tests.patch                       # テストへの差分パッチ
```

## セットアップ手順

### 方法 A: パッチ適用（推奨）

LAM の構成が本プロジェクトと同一の場合、パッチで一括適用できる。

```bash
# プロジェクトルートで実行
cd /path/to/your-project

# 1. 実装コード
git apply /path/to/cross-module-blame-package/card_generator.patch
git apply /path/to/cross-module-blame-package/orchestrator.patch

# 2. ルール
git apply /path/to/cross-module-blame-package/code-quality-guideline.patch

# 3. full-review コマンド
git apply /path/to/cross-module-blame-package/full-review.patch

# 4. Agent 定義
git apply /path/to/cross-module-blame-package/agents.patch

# 5. テスト
git apply /path/to/cross-module-blame-package/tests.patch

# 6. テスト実行で確認
python -m pytest .claude/hooks/analyzers/tests/test_card_generator.py::TestParseBlameHint -v
python -m pytest .claude/hooks/analyzers/tests/test_orchestrator.py::TestBuildReviewPromptWithContracts -v
```

パッチが適用できない場合（ファイル構造が異なる場合）は方法 B を使用。

### 方法 B: 手動適用

#### Step 1: parse_blame_hint() の追加

`blame_hint_parser.py` の内容を `.claude/hooks/analyzers/card_generator.py` の
`parse_contract()` 関数の直後にコピーする。

追加するもの:
- `_BLAME_START`, `_BLAME_END`, `_BLAME_FIELDS`, `_VALID_RESPONSIBLE` 定数
- `BlameHint` 型エイリアス
- `parse_blame_hint()` 関数

#### Step 2: プロンプト拡張

`.claude/hooks/analyzers/orchestrator.py` の `build_review_prompt_with_contracts()` 関数で、
`contracts_text` の前に帰責ガイドを挿入する。

`blame_guide_prompt.txt` の内容を header 文字列に追加する。

変更前:
```python
header = (
    "以下は上流モジュールの契約です。"
    "これらの前提条件・保証に違反する呼び出しがないか確認してください。\n\n"
    + contracts_text
    + "\n\n"
)
```

変更後:
```python
header = (
    "以下は上流モジュールの契約です。"
    "これらの前提条件・保証に違反する呼び出しがないか確認してください。\n\n"
    + BLAME_GUIDE_TEXT  # blame_guide_prompt.txt の内容
    + "\n\n"
    + contracts_text
    + "\n\n"
)
```

#### Step 3: フローチャート追加

`blame_flowchart.md` の内容を `.claude/rules/code-quality-guideline.md` の
「判断に迷った場合 > アンチパターン」セクションの後、
「BUILDING フェーズでの適用」セクションの前に挿入する。

#### Step 4: Agent 定義更新

以下の内容を各 Agent のレビュー観点セクションに追加:

```markdown
### N. モジュール間帰責（契約カード注入時のみ）
- 上流モジュールの契約に違反する呼び出しがないか
- 帰責判断が必要な場合は BLAME-HINT マーカーで出力
- 詳細な指示はレビュープロンプト内の【帰責判断ガイド】に従う
```

対象ファイル:
- `.claude/agents/quality-auditor.md`
- `.claude/agents/code-reviewer.md`

#### Step 5: full-review.md 更新

`.claude/commands/full-review.md` に以下の 3 箇所を追加:

1. **Stage 2 Step 3**: Agent 出力パース手順に `parse_blame_hint()` を追加
2. **Stage 3 Step 5**: レポート形式に `** 帰責判断求む **` マーカーと帰責サマリーテーブルを追加
3. **Stage 4**: 修正前に帰責ヒントのガードを追加（`spec_ambiguity` は自動修正禁止）

詳細は `full-review.patch` を参照。

#### Step 6: テスト追加・実行

`tests.patch` のテスト内容を対応するテストファイルに追加し、実行して Green を確認する。

## 動作確認

セットアップ後、以下で動作を確認:

```bash
# 1. parse_blame_hint のテスト
python -m pytest .claude/hooks/analyzers/tests/test_card_generator.py::TestParseBlameHint -v

# 2. プロンプト拡張のテスト
python -m pytest .claude/hooks/analyzers/tests/test_orchestrator.py::TestBuildReviewPromptWithContracts -v

# 3. 全テスト回帰確認
python -m pytest .claude/hooks/analyzers/tests/ -v
```

## 機能の使い方

セットアップ後は通常通り `/full-review` を実行するだけでよい。

- 契約カードが注入される（モジュール間依存がある）場合、Agent プロンプトに帰責ガイドが自動挿入される
- Agent がモジュール間 Issue を検出すると `BLAME-HINT` マーカーを出力する
- Stage 3 レポートに `** 帰責判断求む **` マーカーと帰責サマリーが表示される
- `spec_ambiguity` の Issue は Stage 4 で自動修正されない

## 注意事項

- 帰責ヒントは**参考情報**であり、重要度分類（Critical/Warning/Info）には影響しない
- 最終的な帰責判断は人間が行う
- 帰責マーカーが出力されなくても、既存のレビューフローは正常に動作する（フォールバック）
