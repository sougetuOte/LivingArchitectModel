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

## 依存関係（Phase 4）

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

## Phase 5: Plan E — ハイブリッド統合（将来）

### Task E-1: 全ステージ統合
### Task E-2: 自動スケール判定
### Task E-3: エンドツーエンドテスト

Phase 5 のタスク詳細は Phase 4 完了後に設計する。

### Plan E 設計ノート（Phase 4 完了時の申し送り）

#### D-5 再定義の経緯と E-3 への影響

Phase 4 Wave 3 計画時に D-5 のスコープを AoT + Three Agents Model で分析し、以下を再定義した（2026-03-16）:

**テスト責務の二層分離**:

| レイヤー | 担当 | 検証内容 | 決定性 |
|---------|------|---------|--------|
| データフロー | D-5 統合チェーンテスト | 関数チェーンの入出力整合（graph → topo → prompt → contract） | 決定的（pytest） |
| 品質・精度 | E-3 エンドツーエンドテスト | Issue 検出精度、収束イテレーション数、Green State 到達 | 非決定的（LLM 依存） |

**E-3 設計時の検討事項**:
- D-5 の `test_integration_pipeline.py` を基盤として活用可能
- Green State 到達の検証は E-3 が引き受ける（D-5 では削除）
- full-review.md の Phase 体系は Plan E で Stage 体系に再編される可能性がある。D-5 で追加した Phase 0/2.5 のステップは Stage 2 に吸収される想定
- `analyze_impact()` の「ログで確認」型検証（D-4 受け入れ条件(2)の運用検証部分）も E-3 のスコープに含めることを推奨

**Plan D で構築済みの Python 関数群**（E-1/E-3 で再利用可能）:
- `build_topo_order()` — グラフ構築 + SCC 縮約 + トポロジカルソート
- `order_chunks_by_topo()` — チャンクのトポロジカル順グループ化
- `build_review_prompt_with_contracts()` — 契約カード注入プロンプト生成
- `parse_contract()` / `merge_contracts()` — 契約カード抽出・集約
- `analyze_impact()` — 推移的影響範囲分析（D-4）
- `order_files_by_topo()` — 修正順序のトポロジカルソート

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
