# Scalable Code Review タスク定義

**作成日**: 2026-03-14
**バージョン**: 1.2
**対応仕様**: `docs/specs/scalable-code-review-spec.md`
**設計書**: `docs/design/scalable-code-review-design.md`

---

## Phase 1: Plan A — 静的解析パイプライン

### Task A-1a: 基盤データモデル実装
- `LanguageAnalyzer` ABC の実装（detect, run_lint, run_security, parse_ast, run_type_check）
- `ASTNode` ラッパー型の実装（tree-sitter / Python ast の差異を吸収）
- `Issue` データモデルの実装
- **成果物**: `.claude/hooks/analyzers/base.py`
- **テスト**: `.claude/hooks/analyzers/tests/` にユニットテスト
- **受け入れ条件**: ABC を継承したクラスが定義でき、ASTNode / Issue が正しくシリアライズ可能であること

### Task A-1b: プラグイン管理・ツール検証実装
- `AnalyzerRegistry`（`*_analyzer.py` 自動探索、動的 import、言語検出）の実装
- ツールインストール確認ロジック（`shutil.which()` + 初回 `--version` チェック）
- 未インストール時のエラー停止 + インストール手順表示（全 Analyzer 共通処理）
- **成果物**: `.claude/hooks/analyzers/base.py`（Registry 部分）
- **テスト**: `.claude/hooks/analyzers/tests/` にユニットテスト
- **受け入れ条件**: `*_analyzer.py` を配置すれば自動検出されること、ツール未インストール時にエラー停止すること

### Task A-2: Python Analyzer 実装
- ruff lint 統合（`ruff check --output-format json`）
- bandit + semgrep セキュリティスキャン統合（JSON 出力パーサー）
- ast / tree-sitter による AST 解析 → `ASTNode` 変換
- **成果物**: `.claude/hooks/analyzers/python_analyzer.py`
- **テスト**: 実プロジェクト（LAM 自体）での動作確認
- **受け入れ条件**: `pyproject.toml` 存在時に自動検出、lint + security の Issue が JSON で出力されること

### Task A-3: JavaScript/TypeScript Analyzer 実装
- eslint lint 統合（`npx eslint --format json`）
- semgrep + npm audit セキュリティスキャン統合
- tree-sitter による AST 解析 → `ASTNode` 変換
- **成果物**: `.claude/hooks/analyzers/javascript_analyzer.py`
- **テスト**: サンプル JS/TS プロジェクトでの動作確認
- **受け入れ条件**: `package.json` 存在時に自動検出

### Task A-4: Rust Analyzer 実装
- cargo clippy lint 統合（`cargo clippy --message-format json`）
- cargo audit セキュリティスキャン統合（`cargo audit --json`）
- tree-sitter による AST 解析 → `ASTNode` 変換
- **成果物**: `.claude/hooks/analyzers/rust_analyzer.py`
- **テスト**: サンプル Rust プロジェクトでの動作確認
- **受け入れ条件**: `Cargo.toml` 存在時に自動検出

### Task A-5: コンパクション対策 — 外部永続化
- `.claude/review-state/` ディレクトリ構造の実装
- `static-issues.json` の読み書きユーティリティ
- `ast-map.json` の読み書きユーティリティ
- `summary.md` 生成ロジック（NFR-4: Critical を先頭、カウントを末尾に配置）
- SHA-256 ベースのファイルキャッシュ（変更検出 + 未変更ファイルのキャッシュ利用）
- `.gitignore` に `.claude/review-state/` を追加
- **成果物**: `.claude/hooks/analyzers/state_manager.py`
- **受け入れ条件**: レビュー結果が永続化され、次回レビューでキャッシュが機能すること

### Task A-5b: review-config.json 実装
- `.claude/review-config.json` のスキーマ定義と読み込みロジック
- デフォルト値の管理（ファイル未存在時は全デフォルト）
- 設定項目: `exclude_languages`, `exclude_dirs`, `max_parallel_agents`, `chunk_size_tokens`, `overlap_ratio`, `auto_enable_threshold`, `agent_retry_count`, `static_analysis_timeout_sec`, `file_size_limit_bytes`, `summary_max_tokens`
- **成果物**: `.claude/hooks/analyzers/config.py`
- **受け入れ条件**: 設定ファイルの有無に関わらず動作すること

### Task A-6: full-review Phase 0 統合
- `/full-review` コマンドに Phase 0（静的解析）を挿入
- 既存 Phase を +1 してリナンバリング（Phase 0→1, 1→2, ...）
- 行数カウントによる自動有効化判定（10K: 提案、30K: 自動有効化）
  - カウント方法: AST 解析で有効コード行をカウント（Plan A の AST を流用）
  - AST 解析が失敗/未対応の場合は `wc -l` 相当の全行数にフォールバック
- 複数言語混在時の並列実行 + 除外設定の適用
- 静的解析結果を Phase 2（LLM レビュー）の入力として接続
- 既存の小規模プロジェクト（~10K行）向け動作に影響がないこと（NFR-2）
- **成果物**: `.claude/commands/full-review.md` 改修
- **受け入れ条件**: 10K行以下のプロジェクトで現行と同一動作、30K行以上で自動有効化
- **Phase 完了検証**: LAM 自体に対して Phase 0 を実行する統合テストで自動検証

---

## Phase 2: Plan B — AST チャンキング

### Task B-1a: Chunk データモデル + トークンカウント
- `Chunk` dataclass の実装（設計書 Section 3.4）
  - `file_path`, `start_line`, `end_line`, `content`, `overlap_header`, `overlap_footer`, `token_count`, `level`, `node_name`
- トークンカウント関数: `count_tokens(text) -> int` = `len(text.split())`
- **成果物**: `.claude/hooks/analyzers/chunker.py`（データモデル部分）
- **テスト**: Chunk 生成・シリアライズ、トークンカウントのユニットテスト
- **受け入れ条件**: Chunk が正しくインスタンス化でき、トークンカウントがワード数と一致すること

### Task B-1b: tree-sitter 統合 + チャンク分割エンジン
- tree-sitter の try/import（未インストール時は `TreeSitterNotAvailable` 例外 → スキップ）
- AST からトップレベルノード（クラス、関数）を列挙
- チャンク分割アルゴリズム（設計書 Section 3.5）:
  - クラス ≤ chunk_size_tokens → L2 チャンク
  - クラス > chunk_size_tokens → L1 分割（メソッド単位）
  - トップレベル関数 → L1 チャンク
  - L1 でもなお超過する巨大関数 → Warning + 自動 Issue 追加
- Python 向け実装を先行（tree-sitter-python）。JS/Rust は後続タスクで追加
- **成果物**: `.claude/hooks/analyzers/chunker.py`（分割ロジック部分）
- **テスト**: サンプル Python ファイルに対するチャンク分割結果の検証（L1/L2/L3 の判定、巨大関数の Warning）
- **受け入れ条件**: Python ファイルが正しくチャンク分割され、各チャンクのトークン数が `chunk_size_tokens` 以内であること（巨大関数を除く）

### Task B-1c: のりしろ付与
- ファイルヘッダーのりしろ: import 文 + モジュールレベル定数・型定義
- シグネチャサマリーのりしろ: 同一ファイル内の他関数/クラスのシグネチャ
- 呼び出し先シグネチャ: AST の Call ノードから同一パッケージ内の定義を特定
- のりしろ込みで `chunk_size_tokens * (1 + overlap_ratio)` を超えないよう調整
- **成果物**: `.claude/hooks/analyzers/chunker.py`（のりしろ付与部分）
- **テスト**: のりしろが正しく付与されること、サイズ制限を超えないこと
- **受け入れ条件**: 各チャンクに import + シグネチャのりしろが付与され、上限トークン数内であること

### Task B-2a: バッチ並列オーケストレーション
- チャンクを `max_parallel_agents` 個ずつのバッチに分割
- バッチ内の Agent を `run_in_background` で並列起動 → 全完了待ち → 次バッチ
- Agent プロンプト: チャンクファイルのパスを渡し、Agent が自分で読み込む
- エラーハンドリング: タイムアウト/エラー時に最大 `agent_retry_count` 回リトライ、失敗は Warning 続行
- **成果物**: `.claude/hooks/analyzers/orchestrator.py` または `full-review.md` Phase 1.7 + Phase 2 改修
- **テスト**: モック Agent（固定 Issue リストを返す）で 50 チャンク × 4 並列（13 バッチ）を検証
- **受け入れ条件**: 全バッチが順序通り処理され、全チャンクの結果が収集されること

### Task B-2b: Reduce（横断チェック + 重複排除）
- 全チャンクの Issue リストを統合
- 重複排除（同一ファイル・行・ルールの Issue を統合）
- 横断チェック（静的解析ベース、設計書 Section 3.3）:
  - API 呼び出しと定義の一致（AST の Call ノード vs 関数定義）
  - 型の整合性（型ヒントあり: シグネチャ照合、型ヒントなし: リテラル/1ホップ推論）
  - 命名規則の統一性（snake_case / camelCase 混在検出）
- **成果物**: `.claude/hooks/analyzers/reducer.py`
- **テスト**: モック Issue リストに対する重複排除・横断チェックのユニットテスト
- **受け入れ条件**: 重複が排除され、API 不一致・型不整合が検出されること

### Task B-3: チャンク結果の永続化 + full-review 統合
- `.claude/review-state/chunk-results/` への結果保存
  - ファイル名: `{path_segments}-{level}-{node_name}-{start}-{end}.json`
- `chunks.json`（チャンク一覧）の保存・読み込み
- `full-review.md` に Phase 1.7（AST チャンキング）を追加
- Phase 2 をチャンクモード対応に改修（チャンクあり → チャンク単位 Agent、なし → 従来）
- **成果物**: `state_manager.py` 拡張 + `full-review.md` 改修
- **テスト**: チャンク結果の保存・読み込みラウンドトリップ
- **受け入れ条件**: チャンク結果が永続化され、full-review がチャンクモードで動作すること
- **Phase 完了検証**: LAM 自体に対して Phase 2 を実行する手動統合テスト

---

## Phase 3: Plan C — 階層的レビュー

### Wave 割り当て

| Wave | タスク | 規模 | 概要 |
|:----:|:-------|:----:|:-----|
| Wave 1 | C-1a, C-1b, C-2a | M+S+M | 概要カード生成 + Layer 2 モジュール統合 |
| Wave 2 | C-2b, C-3a, C-3b | M+S+S | Layer 3 システムレビュー + full-review 統合 + 再レビューループ |

全タスクが直列依存のため、各 Wave 内も順序実行。

### Task C-1a: 概要カード生成エンジン（機械的フィールド）
- `card_generator.py` に概要カード生成ロジックを実装
- 機械的フィールドの生成:
  - **公開 API**: `ast-map.json` からトップレベル関数/クラス名を取得
  - **依存先**: `ast-map.json` の import 情報から取得
  - **依存元**: `ast-map.json` の import 情報を逆引き（全ファイルの import を走査し、対象ファイルを参照しているものを収集）
  - **Issue 数**: `static-issues.json` + `chunk-results/` からファイル単位で集計
- 概要カードの永続化: `review-state/cards/file-cards/{path-segments}.md`
- **成果物**: `.claude/hooks/analyzers/card_generator.py`
- **テスト**: モック ast-map / issues データから概要カード生成、逆引き依存元の正確性検証
- **受け入れ条件**: 公開API・依存先・依存元・Issue数が正しく生成・永続化されること

### Task C-1b: Phase 2 Agent プロンプト拡張（責務フィールド生成）
- Phase 2 並列監査の Agent プロンプトに「概要カードの責務フィールドを1行で出力せよ」を追加
- Agent 出力から責務フィールドをパースし、C-1a の概要カードにマージ
- Agent 出力フォーマット定義（レビュー結果 + 概要カード責務を分離可能な形式）
- **成果物**: `full-review.md` Phase 2 改修 + `card_generator.py`（マージロジック）
- **テスト**: Agent 出力のパーステスト（正常系 + 責務フィールド欠落時のフォールバック）
- **受け入れ条件**: Phase 2 完了後に全ファイルの概要カードが責務フィールド付きで生成されること

### Task C-2a: Layer 2 モジュール統合（要約カード生成）
- モジュール境界の検出: `__init__.py`（Python）/ `package.json`（JS/TS）の存在で判定、なければディレクトリ単位
- モジュール単位で概要カードを集約し、要約カードを生成
- モジュール境界固有チェック（メインフローで逐次実行、Agent 不要）:
  - `__init__.py` の `__all__` と実際のエクスポートの一致
  - `__init__.py` で re-export しているが実際に使われていないシンボル
  - モジュール内のファイル間で同名の関数/クラスが衝突していないか
- Phase 2 Reduce のチェック結果をモジュール単位に集約
- 要約カードの永続化: `review-state/cards/module-cards/{module-name}.md`
- **成果物**: `.claude/hooks/analyzers/card_generator.py`（Layer 2 部分）
- **テスト**: モック概要カード群からモジュール境界検出・要約カード生成・境界チェックのユニットテスト
- **受け入れ条件**: モジュール境界が正しく検出され、3種のチェックが動作し、要約カードが永続化されること

### Task C-2b: Layer 3 システムレビュー
- 機械的チェック（メインフローで逐次実行、Agent 不要）:
  - 循環依存検出（ast-map.json の import 情報からグラフ構築 → SCC 検出）
  - 命名パターン違反（snake_case / camelCase の混在をモジュール横断で検出）
- LLM 仕様ドリフト検出:
  - 全モジュールの要約カード群 + `docs/specs/` 配下の全 `.md` ファイルを LLM に渡す
  - 仕様と実装の乖離を Issue として出力させる
- **成果物**: `.claude/hooks/analyzers/card_generator.py`（Layer 3 部分）+ `full-review.md` 改修
- **テスト**: 循環依存検出のユニットテスト（循環あり/なしケース）、命名パターン検出テスト
- **受け入れ条件**: 循環依存・命名違反が検出され、仕様ドリフトチェックが動作すること

### Task C-3a: full-review Phase 2.5 統合
- full-review.md に Phase 2.5（階層的レビュー）を挿入
- Phase 2 完了後に Layer 2 → Layer 3 を逐次実行するフロー
- Layer 2/3 の Issue を Phase 3（レポート統合）に合流させる
- **成果物**: `full-review.md` Phase 2.5 追加
- **テスト**: full-review フロー全体の手動統合テスト（LAM 自体に対して実行）
- **受け入れ条件**: Phase 2 → 2.5 → 3 が正しい順序で実行され、全 Layer の Issue が統合レポートに含まれること

### Task C-3b: 全体再レビューループ
- 修正後の Layer 1 からのゼロベース再実行（FR-5）
- 静的解析は変更ファイルのみ再実行（キャッシュ利用）、LLM はゼロベース
- 概要カード・要約カードも再生成（キャッシュしない）
- Green State 判定の拡張: 全 Layer の Issue がゼロであること
- **成果物**: `full-review.md` Phase 5 改修
- **テスト**: 修正 → 再レビューの手動統合テスト
- **受け入れ条件**: 修正後の再レビューで全 Layer がゼロベース再実行され、部分スキップが発生しないこと
- **Phase 完了検証**: LAM 自体に対して Phase 3 全体を実行する手動統合テスト

---

## Phase 4: Plan D — 依存グラフ駆動（将来）

### Task D-1: 依存グラフ構築
### Task D-2: トポロジカルソート + 契約カード
### Task D-3: 変更影響分析
### Task D-4: full-review 統合

---

## Phase 5: Plan E — ハイブリッド統合（将来）

### Task E-1: 全ステージ統合
### Task E-2: 自動スケール判定
### Task E-3: エンドツーエンドテスト

Phase 4/5 のタスク詳細は将来の設計・着手時にこのファイルを拡張する。
現時点ではタイトルのみ記載し、設計書の Section 5/6 を参照すること。

---

## 依存関係

```
A-1a → A-1b
A-1a → A-2, A-3, A-4（並列可能）
A-1b → A-2, A-3, A-4
A-1a → A-5
A-1a → A-5b
A-5b → A-2, A-3, A-4（config 参照のため）
A-2, A-3, A-4, A-5, A-5b → A-6
A-6 → B-1a
B-1a → B-1b
B-1b → B-1c
B-1a → B-2a（Chunk データモデルが必要）
B-1c → B-2a（のりしろ付きチャンクが必要）
B-2a → B-2b（全チャンク結果が必要）
B-1a → B-3（Chunk データモデルが必要）
B-2b → B-3（Reduce 結果の永続化）
A-5 → B-3（state_manager.py 拡張のため）
B-3 → C-1a（chunk-results + ast-map が必要）
B-3 → C-1b（Phase 2 Agent プロンプト改修のため）
C-1a → C-1b（機械的フィールドが先、責務マージが後）
C-1a, C-1b → C-2a（概要カードが必要）
B-2b → C-2a（Reduce 結果の集約のため）
C-2a → C-2b（要約カードが必要）
C-2b → C-3a（全 Layer の統合）
C-3a → C-3b（Phase 2.5 が組み込まれてから再レビューループ）
C-3b → D-1（将来）
D-4 → E-1（将来）
```
