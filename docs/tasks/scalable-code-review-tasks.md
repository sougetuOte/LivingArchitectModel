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

## Phase 4: Plan D — 依存グラフ駆動

### Wave 割り当て

| Wave | タスク | 規模 | 概要 |
|:----:|:-------|:----:|:-----|
| Wave 1 | D-0, D-0b, D-1 | S+S+M | シークレットスキャン統合 + 型統一 + 依存グラフ構築 |
| Wave 2 | D-2, D-3 | M+M | 契約カード生成 + トポロジカル順レビュー統合 |
| Wave 3 | D-4, D-5 | M+S | 影響範囲分析 + full-review 統合 |

### Task D-0: シークレットスキャン Phase 0 統合（FR-7e）
- `lam-stop-hook.py` から `_SECRET_PATTERN` / `_SAFE_PATTERN` を削除
- `python_analyzer.py` の bandit 設定で B105/B106 が有効であることを確認（テスト追加）
- Stop hook の G5 チェックからシークレットスキャン部分を除去
- **成果物**: `lam-stop-hook.py` 修正、`python_analyzer.py` テスト追加
- **テスト**: `password = "secret123"` を含むテストファイルに対して bandit B105 が検出されることを確認
- **受け入れ条件**: (1) Stop hook から `_SECRET_PATTERN`/`_SAFE_PATTERN` が削除されていること (2) `python_analyzer.run_security()` がハードコードパスワードを含むファイルから B105 Issue を返すこと

### Task D-0b: ReviewResult.issues 型統一（FR-7f）
- `orchestrator.py` の `ReviewResult.issues` を `list[str]` → `list[Issue]` に変更
- `build_review_prompt()` の出力パースに `Issue` dataclass 変換ロジックを追加
- 既存の `deduplicate_issues()` / `check_naming_consistency()` との整合性確認
- **成果物**: `orchestrator.py` 修正
- **テスト**: `ReviewResult` の型統一テスト、既存テストの修正
- **受け入れ条件**: `ReviewResult.issues` が `list[Issue]` 型で、既存パイプラインが壊れないこと

### Task D-1: 依存グラフ構築 + トポロジカルソート（FR-7a）
- `_condense_sccs(graph, sccs)` の実装: SCC をスーパーノードに縮約
- `build_topo_order(import_map)` の実装: `graphlib.TopologicalSorter` でソート
- `dependency-graph.json` の永続化（`state_manager.py` 拡張）
- Phase 3 の `_build_import_graph` / `_find_sccs` を内部で呼び出し
- **成果物**: `card_generator.py`（グラフ構築部分）、`state_manager.py`（永続化）
- **テスト**: SCC 縮約テスト、トポロジカルソートテスト（循環あり/なし/複数 SCC）、永続化ラウンドトリップ
- **受け入れ条件**: `dependency-graph.json` が正しいトポロジカル順序と SCC 情報を含むこと

### Task D-2: 契約カード生成（FR-7c）
- `ContractCard` dataclass の実装（設計書 Section 5.3）
- Agent プロンプトに契約フィールド出力マーカー追加（`---CONTRACT-CARD---`）
- `parse_contract()` で Agent 出力から契約フィールドを抽出
- `merge_contracts()` でモジュール単位に集約
- `save_contract_card()` / `load_contract_card()` で永続化（`review-state/contracts/` ディレクトリ作成含む）
- **成果物**: `card_generator.py`（ContractCard 部分）
- **テスト**: パーステスト（正常系 + マーカー欠落フォールバック）、集約テスト、永続化ラウンドトリップテスト
- **受け入れ条件**: (1) モック Agent 出力からの契約フィールド抽出が正しく動作すること (2) モジュール境界が存在する場合、全モジュールの契約カードが `review-state/contracts/` に生成されること (3) モジュール境界がない場合（パッケージ定義なし）、ディレクトリ単位フォールバックで生成されること

### Task D-3: トポロジカル順レビュー統合（FR-7b）
- Phase 2 の Agent 起動順序をトポロジカル順に変更
- 下流モジュールの Agent プロンプトに上流の契約カードをコンテキストとして注入
- Phase 4（修正）の修正順序もトポロジカル順に変更
- `full-review.md` Phase 2 + Phase 4 を改修
- **成果物**: `full-review.md` 改修、`orchestrator.py` 拡張、`card_generator.py`（契約カード注入ロジック）
- **テスト**: (1) トポロジカル順での Agent 起動順序テスト（モック: A→B→C の依存で A が最初にレビューされること） (2) 下流 Agent プロンプトに上流契約カード JSON が含まれることのテスト
- **受け入れ条件**: (1) Agent 起動順序が dependency-graph.json の topo_order と一致すること (2) 下流 Agent のプロンプトに上流の ContractCard が含まれていること (3) Phase 4 の修正も topo_order 順で実行されること

### Task D-4: 影響範囲分析（FR-7d）
- `analyze_impact(modified_files, graph)` の実装: 依存グラフを推移的に上流方向に辿る（深さ制限なし）
- 影響範囲内/外の分類ロジック
- 概要カードの機械的フィールド再利用判定（`state_manager.py` のファイルハッシュ比較を活用）
- Phase 5（再レビュー）での影響範囲ベーススコープ適用
- **成果物**: `card_generator.py`（影響分析部分）、`full-review.md` Phase 5 改修
- **テスト**: (1) 直接依存の影響範囲テスト (2) 間接依存（A→B→C で C 修正時に A も影響範囲） (3) SCC 内ノード修正時にSCC 全体が影響範囲 (4) 依存なしファイルの修正で影響範囲が自身のみ
- **受け入れ条件**: (1) `analyze_impact()` が推移的依存を正しく返すこと (2) 修正後の再レビューで影響範囲外ファイルの概要カード機械的フィールドのハッシュが前回と一致し再利用されること（ログで確認可能）

### Task D-5: full-review 全体統合 + 統合チェーンテスト
- Phase 0 完了後に `dependency-graph.json` 生成ステップを full-review.md に挿入
- Phase 2.5 に契約カード生成・永続化ステップを full-review.md に挿入
- **統合チェーンテスト**: モックデータで以下のパイプラインを検証:
  AST/import_map → build_topo_order → order_chunks_by_topo
  → build_review_prompt_with_contracts → parse_contract → merge_contracts
  → save_contract_card（ラウンドトリップ）
- **成果物**: `full-review.md` 最終改修 + `tests/test_integration_pipeline.py`
- **テスト**: 上記チェーンテスト（決定的、pytest で自動実行）
- **受け入れ条件**:
  - (1) full-review.md に Phase 0 後の graph 生成 + Phase 2.5 の契約カード生成が記述されていること
  - (2) 統合チェーンテストが PASSED
  - (3) 既存テスト全件が PASSED
- **旧受け入れ条件からの変更（2026-03-16 AoT 分析に基づく再定義）**:
  - 旧(4)「Green State 到達」を削除。理由: LLM 出力に依存する非決定的プロセスであり、自動テストで検証不可能。既存 full-review.md Phase 5 の Green State 判定ロジック（G1〜G5）が継続して担う
  - 旧「手動統合テスト」を「統合チェーンテスト（pytest）」に置換。手動検証は Wave 3 完了後の `/auditing` で実施
- **Plan E（E-3）との棲み分け**: D-5 は**データフローの正しさ**（関数チェーンの入出力整合）を検証。**品質・精度・収束性**の検証は E-3 の守備範囲。詳細は下記「Plan E 設計ノート」を参照

---

## 依存関係（Plan D: Phase 4）

```
D-0 → D-1（Stop hook 整理後にグラフ構築）
D-0b → D-3（ReviewResult 型統一後にレビュー統合）
D-1 → D-3（トポロジカル順が必要）
D-2 → D-3（契約カードが必要）
D-1 → D-4（グラフが必要）
D-3, D-4 → D-5（全コンポーネント統合）

注: D-2（契約カード生成）は D-1（グラフ構築）に依存しない。
契約カードの生成自体にグラフは不要。グラフが必要なのは
トポロジカル順で契約カードを注入する D-3。
D-0b と D-2 も独立しており、Wave 1 と Wave 2 で並列着手可能。
```

---

## Phase 5: Plan E — ハイブリッド統合

対応仕様: `docs/specs/scalable-code-review-phase5-spec.md`
対応設計: `docs/design/scalable-code-review-design.md` Section 6

### AoT 分解: タスク計画

| Atom | 判断内容 | 依存 |
|:-----|:---------|:-----|
| T1 | タスク粒度と分割方法 | なし |
| T2 | 依存関係と実行順序 | T1 |
| T3 | Wave 割り当て | T1, T2 |

#### Atom T1: タスク粒度

**[Affirmative]**: FR-E1（Stage 再編）は full-review.md のみの変更で 1 タスクでよい。FR-E2（scale_detector.py）はデータモデル + 判定ロジック + CLI + テストで 2 分割が適切。FR-E3 はフィクスチャ + 決定的テスト + LLM テストで 2 分割。

**[Critical]**: FR-E1 は 23 箇所の self-reference 更新を含み monolithic にすると検証が困難。Scale Detection の Stage 0 統合は FR-E1 と FR-E2 の交差点であり独立タスクにすべき。連鎖ドキュメント更新（NFR-E3）も独立タスクにしないと抜け漏れが出る。

**[Mediator]**: FR-E1 を 3 分割（見出し再編 / Scale Detection 統合 / 連鎖ドキュメント）。FR-E2 を 2 分割（コア / CLI + 前提条件）。FR-E3 を 2 分割（決定的 / 非決定的）。計 7 タスク。

#### Atom T2: 依存関係

**[Affirmative]**: E-2a と E-1a は完全独立（Python vs Document）で並列可能。E-2b は E-2a に依存。E-3a は E-2a に依存（ScaleDetectionResult をテスト）。E-1b は E-1a + E-2b の両方に依存。

**[Critical]**: E-1c（連鎖ドキュメント）は E-1a + E-1b 完了後でないと整合性を取れない。E-3b の収束テストは full-review.md の Stage 再編（E-1b）完了後でないと意味がない。

**[Mediator]**: 依存グラフを 3 層に整理。Layer 1: E-2a + E-1a（並列）。Layer 2: E-2b + E-3a（並列）。Layer 3: E-1b + E-3b + E-1c。

#### Atom T3: Wave 割り当て

**[Affirmative]**: 3 Wave で依存レイヤーと一致させるのが自然。各 Wave 内の並列タスクでスループットを最大化。

**[Critical]**: Wave 3 に 3 タスク（E-1b + E-3b + E-1c）は多すぎないか？E-1c は E-1b 完了後でないと開始できない。

**[Mediator]**: Wave 3 内は E-1b → E-1c の順序依存あり。E-3b は E-1b と並列可能だが、実際には LLM 手動実行のため軽量。Wave 3 のサイズは許容範囲。

### Wave 割り当て

| Wave | タスク | 規模 | 概要 |
|:----:|:-------|:----:|:-----|
| Wave 1 | E-2a, E-1a | M+M | scale_detector コア + Stage 見出し再編（並列可能） |
| Wave 2 | E-2b, E-3a | S+M | 前提条件チェック + CLI + フィクスチャ + 決定的テスト（並列可能） |
| Wave 3 | E-1b, E-3b, E-1c | M+S+S | Scale Detection Stage 0 統合 + LLM テスト + 連鎖ドキュメント |

### Task E-1a: full-review.md Stage 見出し再編（FR-E1, FR-E1b）

現行の 11 Phase 構造を 6 Stage 体系に再編する。設計書 Section 6.2.1 のマッピングに従う。

- full-review.md の見出し構造を Stage 0〜5 に変更
- 各 Stage 先頭に「実行条件 / 入力 / 出力」の契約セクションを追加（FR-E1b、設計書 6.2.2 テーブル）
- self-reference 23 箇所を全件更新（設計書 Section 6.5.1 テーブル R-01〜R-23）
- 参照セクション（末尾）を Stage 番号に更新
- **成果物**: `.claude/commands/full-review.md` 改修
- **テスト**: `grep -c "Phase" full-review.md` で Phase 参照が残っていないこと（歴史的記述・コメントを除く）
- **受け入れ条件**:
  - (1) Stage 0〜5 の `## Stage N:` 見出しが存在し、`## Phase` 見出しが存在しないこと
  - (2) R-01〜R-23 の全件が更新されていること
  - (3) 各 Stage 先頭に実行条件 / 入力 / 出力が記述されていること
  - (4) Python コード変更がゼロであること（NFR-E1）

### Task E-2a: scale_detector.py データモデル + 判定ロジック（FR-E2a, FR-E2d）

スケール判定の中核ロジックを実装する。設計書 Section 6.3 に従う。

- `PlanStatus` dataclass の実装（enabled, available, reason）
- `ScaleDetectionResult` dataclass の実装（line_count, recommended_plans, active_plans, plan_statuses）
- 閾値テーブル `_PLAN_THRESHOLDS` の実装（設計書 6.3.2）
- `detect_scale(project_root, config=None) -> ScaleDetectionResult` の実装
  - `run_pipeline.count_lines()` を import して行数カウント（既存関数変更なし）
  - 閾値テーブルで `recommended_plans` を決定
  - 各 Plan の前提条件チェックは E-2b で実装するため、ここではスタブ（全て available=True）
- `format_scale_detection(result) -> str` の実装（FR-E2c 出力フォーマット）
- **成果物**: `.claude/hooks/analyzers/scale_detector.py`
- **テスト**: `.claude/hooks/analyzers/tests/test_e2e_review.py` の `TestScaleDetection` クラスに閾値テストを追加
  - `test_under_10k_returns_no_plans`
  - `test_10k_to_30k_returns_plan_a`
  - `test_30k_to_100k_returns_plan_a_and_b`
  - `test_100k_to_300k_returns_plan_a_b_c`
  - `test_over_300k_returns_all_plans`
  - `test_output_format_matches_fr_e2c`
- **受け入れ条件**:
  - (1) `detect_scale()` が 5 段階の閾値（0/10K/30K/100K/300K）で正しい Plan セットを返すこと
  - (2) `format_scale_detection()` が FR-E2c 仕様のフォーマットと一致すること
  - (3) `run_pipeline.py` への変更がゼロであること（NFR-E1）
  - (4) 既存テスト（396+ 件）が全 PASSED であること

### Task E-2b: 前提条件チェック + CLI エントリポイント（FR-E2b, FR-E2c）

各 Plan の前提条件チェックと CLI 実行機能を実装する。設計書 Section 6.3.3〜6.3.4 に従う。

- Plan A チェック: `shutil.which("ruff")` + `shutil.which("bandit")`
- Plan B チェック: `importlib.util.find_spec("tree_sitter")`
- Plan C チェック: Plan B の `PlanStatus.available` を参照（auto）
- Plan D チェック: `Path(".claude/review-state/import-map.json").exists()`
- E-2a のスタブを実際のチェックロジックに置換
- CLI エントリポイント（`if __name__ == "__main__":`）:
  - `sys.argv[1]` から `project_root` を受け取る
  - stdout に `format_scale_detection()` 出力
  - `.claude/review-state/scale-detection.json` に JSON 永続化
- **成果物**: `.claude/hooks/analyzers/scale_detector.py`（E-2a の拡張）
- **テスト**: `TestScaleDetection` クラスに前提条件テストを追加
  - `test_plan_a_skipped_when_ruff_missing`（monkeypatch で `shutil.which` をモック）
  - `test_plan_a_skipped_when_bandit_missing`
  - `test_plan_b_fallback_when_tree_sitter_missing`（monkeypatch で `importlib.util.find_spec` をモック）
  - `test_plan_d_skipped_when_import_map_missing`（tmp_path で存在しないパスを指定）
- **受け入れ条件**:
  - (1) 各 Plan のツール未インストール時に `PlanStatus(available=False)` が返ること
  - (2) CLI 実行で stdout に FR-E2c フォーマットが出力されること
  - (3) `.claude/review-state/scale-detection.json` が正しく永続化されること
  - (4) 既存モジュール（`base.py`, `chunker.py`）への変更がゼロであること

### Task E-3a: E2E フィクスチャ + 決定的テスト（FR-E3b-3, FR-E3a）

E2E テストのフィクスチャと決定的テスト（CI 対象）を作成する。設計書 Section 6.4 に従う。

- フィクスチャ作成（`.claude/hooks/analyzers/tests/fixtures/e2e/`）:
  - `critical_silent_failure.py`: Silent Failure × 3 箇所（空 except, 空 dict 返却, pass でスキップ）
  - `warning_long_function.py`: Long Function × 2 箇所（51 行以上の関数、複数責務）
  - `security_hardcoded_password.py`: ハードコードパスワード × 3 箇所（bandit B105/B106 検出パターン）
  - `combined_issues.py`: 全 Issue 種別 × 各 1 箇所
  - `README.md`: フィクスチャ概要・Issue 箇所一覧
- `test_e2e_review.py` にデータモデル追加:
  - `DetectionResult` dataclass
  - `E2ERunRecord` dataclass
  - `_save_result()` ヘルパー（`docs/artifacts/e2e-results/` に保存）
- `pyproject.toml` に pytest marker 追加（`e2e_llm`, `e2e_convergence`）
  - 既存 `addopts` に `-m 'not e2e_llm and not e2e_convergence'` を追加
- `docs/artifacts/e2e-results/README.md` 作成
- **成果物**: `tests/fixtures/e2e/*.py`, `test_e2e_review.py`（E-2a で作成したファイルへの追記）, `docs/artifacts/e2e-results/README.md`
- **テスト**: `TestScaleDetection`（E-2a/E-2b で既に作成済み）が素の `pytest` で PASSED
- **受け入れ条件**:
  - (1) 4 つのフィクスチャファイルが `fixtures/e2e/` に配置されていること
  - (2) 各フィクスチャに `# FIXTURE-ISSUE-N:` コメントが付与されていること
  - (3) `pytest -m 'not e2e_llm and not e2e_convergence'` で決定的テストのみが実行されること
  - (4) 既存テスト（396+ 件）が全 PASSED であること

### Task E-1b: Stage 0 への Scale Detection 統合（FR-E1, FR-E2）

full-review.md の Stage 0 に Scale Detection 呼び出しを統合する。設計書 Section 6.3.6 に従う。

- Stage 0 に Step 3 として Scale Detection ブロックを追加:
  - `python3 .claude/hooks/analyzers/scale_detector.py $PROJECT_ROOT` の呼び出し
  - `scale-detection.json` の読み込み
  - `active_plans` に基づく後続 Stage の制御フロー記述
- Stage 1 の先頭に実行条件を追加（`Plan A 以上が有効の場合のみ実行`）
- Stage 2/3/4 の条件分岐を Active Plans に基づいて明示
- 小規模プロジェクト（~10K 行）での動作が現行と同一であることを確認（NFR-2、設計書 6.2.3）
- **成果物**: `.claude/commands/full-review.md`（E-1a の成果物への追記）
- **テスト**: `scale_detector.py` を ~10K 行相当の引数で実行し、Plan セット「なし」が返ることを確認
- **受け入れ条件**:
  - (1) Stage 0 Step 3 に scale_detector.py 呼び出しが記述されていること
  - (2) Stage 1 先頭に「Plan A 以上で実行」の条件が記述されていること
  - (3) Stage 2/3 で Plan B/C の有無による分岐が明示されていること
  - (4) Python コード変更がゼロであること

### Task E-3b: LLM 依存テスト + 結果記録（FR-E3b-1, FR-E3b-2, FR-E3c）

非決定的テスト（LLM 依存）のテストクラスと結果記録ロジックを実装する。設計書 Section 6.4.2〜6.4.4 に従う。

- `TestDetectionRate` クラス（`@pytest.mark.e2e_llm`）:
  - `test_critical_silent_failure_detection`: フィクスチャへの LLM 検出率テスト（Critical 100% 目標）
  - `test_warning_long_function_detection`: Warning 80%+ 目標（SHOULD、未達時は `improvement_triggers` に記録）
  - `test_security_hardcoded_password_detection`: bandit による決定的検出の確認
  - `test_detection_results_are_recorded`: 結果ファイルの存在確認
- `TestConvergence` クラス（`@pytest.mark.e2e_convergence`）:
  - `test_lam_reaches_green_state`: LAM 自体への静的解析 + レポート生成
- 結果記録ロジック:
  - `latest.json` + `latest-summary.md` の生成（上書き）
  - `history/YYYYMMDD_HHMMSS.json` の生成（履歴）
- **成果物**: `test_e2e_review.py`（E-3a の成果物への追記）
- **テスト**: `pytest -m e2e_llm` で LLM テストが実行可能なことを確認（実際の LLM 実行は手動）
- **受け入れ条件**:
  - (1) `TestDetectionRate` と `TestConvergence` クラスが `e2e_llm` / `e2e_convergence` marker 付きで定義されていること
  - (2) 素の `pytest` 実行で LLM テストがスキップされること（CI 安全性）
  - (3) `_save_result()` が `docs/artifacts/e2e-results/latest.json` + `history/` に正しく保存すること
  - (4) 既存テスト（396+ 件）が全 PASSED であること

### Task E-1c: 連鎖ドキュメント更新 + 最終検証（NFR-E3, NFR-E2）

Plan E の全タスク完了後に、連鎖ドキュメントの整合性を確認・更新する。

- `docs/design/scalable-code-review-design.md` Section 1 の Phase 対応表を Stage 対応表に更新
- `docs/specs/scalable-code-review-spec.md` FR-8 / Section 5 に Plan E 完了の記載を追加
- 本タスク定義ファイル内の Phase 参照を Stage 参照に更新（依存関係セクション）
- NFR-E2 段階的検証の実施:
  1. 既存テスト（396+ 件）が全 PASSED
  2. `scale_detector.py` の単体テストが PASSED
  3. `pytest -m 'not e2e_llm and not e2e_convergence'` が全 PASSED
- **成果物**: `docs/design/scalable-code-review-design.md`, `docs/specs/scalable-code-review-spec.md`, `docs/tasks/scalable-code-review-tasks.md`
- **テスト**: 全テストスイート実行
- **受け入れ条件**:
  - (1) 設計書 Section 1 が Stage 対応表に更新されていること
  - (2) 仕様書に Plan E 完了の反映があること
  - (3) 全テスト PASSED
  - (4) `/full-review` を ~10K 行プロジェクト相当で手動実行し、Stage 1〜3 がスキップされ現行動作と同一であること（手動）

### WBS 100% Rule: 仕様⇔タスク トレーサビリティ

| FR/NFR | 対応タスク | 漏れ |
|:-------|:----------|:-----|
| FR-E1（Stage 体系再編） | E-1a, E-1b | なし |
| FR-E1a（Python 変更禁止、Stage 番号安定、後方互換） | 全タスク制約 + E-1b（後方互換検証） | なし |
| FR-E1b（Stage 間データフロー明示） | E-1a（契約セクション追加） | なし |
| FR-E2a（行数ベース閾値テーブル） | E-2a | なし |
| FR-E2b（Plan 固有前提条件チェック） | E-2b | なし |
| FR-E2c（判定結果出力） | E-2a（format）+ E-2b（CLI stdout） | なし |
| FR-E2d（scale_detector.py 実装場所） | E-2a, E-2b | なし |
| FR-E3a（テスト責務棲み分け） | E-3a（marker 定義） | なし |
| FR-E3b-1（検出率テスト） | E-3b | なし |
| FR-E3b-2（収束テスト） | E-3b | なし |
| FR-E3b-3（スケール判定テスト） | E-2a（TestScaleDetection） | なし |
| FR-E3c（非決定的テスト管理） | E-3a（marker + addopts）+ E-3b | なし |
| NFR-E1（Python 変更最小化） | 全タスク制約 | なし |
| NFR-E2（段階的検証） | E-1c（最終検証ステップ） | なし |
| NFR-E3（ドキュメント整合性） | E-1c（連鎖ドキュメント更新） | なし |

**孤児タスク検証**: 全タスク（E-1a〜E-3b, E-1c）が FR/NFR にトレースでき、孤児なし。

### Plan E 設計ノート（Phase 4 完了時の申し送り）

#### D-5 再定義の経緯と E-3 への影響

Phase 4 Wave 3 計画時に D-5 のスコープを AoT + Three Agents Model で分析し、以下を再定義した（2026-03-16）:

**テスト責務の二層分離**:

| レイヤー | 担当 | 検証内容 | 決定性 |
|:--------|:-----|:--------|:------|
| データフロー | D-5 統合チェーンテスト | 関数チェーンの入出力整合（graph → topo → prompt → contract） | 決定的（pytest） |
| 品質・精度 | E-3 エンドツーエンドテスト | Issue 検出精度、収束イテレーション数、Green State 到達 | 非決定的（LLM 依存） |

**E-3 への反映状況**:
- D-5 の `test_integration_pipeline.py` → E-3a/E-3b で基盤として活用
- Green State 到達の検証 → E-3b `TestConvergence` が引き受け
- `analyze_impact()` の運用検証 → E-3b のスコープに包含
- Phase 体系の Stage 再編 → E-1a で実施済み

**Plan D で構築済みの Python 関数群**（E-1/E-3 で再利用）:
- `build_topo_order()` — グラフ構築 + SCC 縮約 + トポロジカルソート
- `order_chunks_by_topo()` — チャンクのトポロジカル順グループ化
- `build_review_prompt_with_contracts()` — 契約カード注入プロンプト生成
- `parse_contract()` / `merge_contracts()` — 契約カード抽出・集約
- `analyze_impact()` — 推移的影響範囲分析（D-4）
- `order_files_by_topo()` — 修正順序のトポロジカルソート

---

## 依存関係

```
Phase 1〜4（既存）:
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
C-3b → D-0（シークレットスキャン統合）
D-0 → D-1, D-0b → D-3, D-1 → D-3, D-2 → D-3
D-1 → D-4, D-3 + D-4 → D-5

Phase 5（Plan E）:
D-5 → E-2a, E-1a（Wave 1、並列可能）
E-2a → E-2b（データモデルが先、前提条件チェックが後）
E-2a → E-3a（ScaleDetectionResult をテスト）
E-1a → E-1b（Stage 見出しが先、Scale Detection 統合が後）
E-2b → E-1b（scale_detector.py 完成後に Stage 0 統合）
E-3a → E-3b（フィクスチャが先、LLM テストが後）
E-1b → E-1c（Stage 統合完了後に連鎖ドキュメント更新）
E-3b → E-1c（全テスト完了後に最終検証）
```
