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

### Task B-1: チャンキングエンジン実装
- tree-sitter ベースの AST チャンキング
- チャンクサイズ制御（デフォルト 3,000 トークン、`chunk_size_tokens` で調整）
- 4,000 トークン超のクラスを L1（関数/メソッド単位）に自動分割
- のりしろ付与（import、シグネチャ、20% 以内、`overlap_ratio` で調整）
- tree-sitter 未インストール時は Plan B をスキップし Warning 表示
- **成果物**: `.claude/hooks/analyzers/chunker.py`
- **受け入れ条件**: 各チャンクが構文的に妥当であること、のりしろにより周辺コンテキストが保持されること

### Task B-2: Map-Reduce オーケストレーション
- 動的ディスパッチ: Agent 完了次第、次のチャンクを投入
- デフォルト 4 並列（`max_parallel_agents` で調整、最大 10）
- Agent タイムアウト/エラー時: 最大リトライ（`agent_retry_count` で調整）、失敗なら Warning 続行
- Reduce: 重複排除 + API 整合性 + 型整合性 + 命名統一性の横断チェック
- **成果物**: full-review Phase 2 改修
- **テスト**: モックチャンク生成ヘルパーでオーケストレーションロジックを検証（LLM 呼び出しなし）。実プロジェクトでの手動検証も並行して実施
- **受け入れ条件**: 50モックチャンクを 4 並列で処理し、全チャンクの結果が統合されること
- **Phase 完了検証**: 統合テストで自動検証

### Task B-3: チャンク結果の永続化
- `.claude/review-state/chunk-results/` への結果保存
- チャンク間の依存関係の記録
- **成果物**: state_manager.py 拡張
- **受け入れ条件**: 次回レビュー時にキャッシュが機能すること

---

## Phase 3: Plan C — 階層的レビュー

### Task C-1: 概要カード生成
- ファイルレビュー結果からの概要カード自動生成（100-200 トークン）
- 概要カードに「依存元」を grep ベース逆引きで取得
- 概要カードのフォーマット定義（設計書 Section 4.2 準拠）
- **成果物**: `.claude/hooks/analyzers/card_generator.py`
- **受け入れ条件**: 各ファイルから概要カードが生成され、責務・公開API・依存先/元・Issue数が含まれること

### Task C-2: 3レイヤーレビュー実装
- Layer 1（ファイル）→ Layer 2（モジュール: `__init__.py` / `package.json` 単位）→ Layer 3（システム）
- レイヤー間の情報伝達（概要カード → 要約カード）
- 仕様ドリフトチェックの Layer 3 統合
- **成果物**: full-review 改修
- **受け入れ条件**: 3レイヤーの段階的レビューが動作し、各レイヤーで適切な粒度の問題が検出されること

### Task C-3: 全体再レビューループ
- 修正後の Layer 1 からのゼロベース再実行（FR-5）
- 静的解析は変更ファイルのみ再実行、LLM はゼロベース
- Green State 判定の拡張
- **成果物**: full-review Phase 5 改修
- **受け入れ条件**: 修正後の再レビューで全体がスキャンされ、部分スキップが発生しないこと
- **Phase 完了検証**: 統合テストで自動検証

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
A-6 → B-1
B-1 → B-2
B-2 → B-3
A-5 → B-3（state_manager.py 拡張のため）
B-3 → C-1
C-1 → C-2
C-2 → C-3
C-3 → D-1（将来）
D-4 → E-1（将来）
```
