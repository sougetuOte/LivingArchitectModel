# Scalable Code Review 設計書

**バージョン**: 1.1
**作成日**: 2026-03-14
**ステータス**: draft
**対応仕様**: `docs/specs/scalable-code-review-spec.md`

---

## 1. アーキテクチャ概要

```
┌──────────────────────────────────────────────────────────────┐
│                    /full-review (Stage 体系)                   │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐  │
│  │ Stage 0  │→│ Stage 1  │→│ Stage 2  │→│ Stage 3-5   │  │
│  │ 初期化   │  │ 静的解析 │  │ チャンク │  │ 統合・修正  │  │
│  │ +Scale   │  │ +依存グラフ│  │ +レビュー │  │ ・検証      │  │
│  └──────────┘  └──────────┘  └──────────┘  └─────────────┘  │
│       ↓              ↓              ↓              ↓          │
│  .claude/review-state/ (外部永続化)                           │
└──────────────────────────────────────────────────────────────┘
```

### Stage 体系（Plan E で再編）

Plan E で full-review.md を 11 Phase → 6 Stage に再編した。

| Stage | 内容 | 統合元 Phase |
|:------|:-----|:-------------|
| Stage 0 | 初期化（ループ状態、context7 検出、Scale Detection） | Phase 1, 1.5 |
| Stage 1 | 静的分析 + 依存グラフ構築 | Phase 0, 0.3 |
| Stage 2 | チャンク分割 + トポロジカル順レビュー | Phase 1.7, 2 |
| Stage 3 | 階層的統合 + レポート生成 | Phase 2.5, 3 |
| Stage 4 | トポロジカル順修正 | Phase 4 |
| Stage 5 | 検証 + Green State 判定 + 完了 | Phase 5, 6 |

### Plan 別の有効化

| 規模 | 有効な Plan | 自動判定 |
|:-----|:-----------|:---------|
| ~10K | なし（従来 full-review） | scale_detector.py が Plan セット「なし」を返す |
| 10K-30K | Plan A | Stage 1 実行 |
| 30K-100K | Plan A + B | Stage 1 + Stage 2 チャンクモード |
| 100K-300K | Plan A + B + C | 全 Stage 自動 |
| 300K+ | Plan A + B + C + D | 全 Stage 自動（トポロジカル順） |

## 2. Plan A: 静的解析パイプライン設計

### 2.1 プラグインインターフェース

```python
class LanguageAnalyzer(ABC):
    """言語固有の静的解析プラグインの基底クラス。
    ユーザーが新言語を追加する際はこのクラスを継承する。"""

    language_name: str = ""  # サブクラスで必ず設定（例: "python", "rust"）
    # exclude_languages フィルタで使用。未設定だとフィルタが機能しない。

    @abstractmethod
    def detect(self, project_root: Path) -> bool:
        """プロジェクトがこの言語を使用しているか検出する。"""

    @abstractmethod
    def run_lint(self, target: Path) -> list[Issue]:
        """lint を実行し Issue リストを返す。"""

    @abstractmethod
    def run_security(self, target: Path) -> list[Issue]:
        """セキュリティスキャンを実行し Issue リストを返す。"""

    @abstractmethod
    def parse_ast(self, file_path: Path) -> "ASTNode":
        """AST を構築して返す（Plan B で使用）。"""

    def run_type_check(self, target: Path) -> list[Issue]:
        """型チェック（オプション）。"""
        return []

    def required_tools(self) -> list["ToolRequirement"]:
        """この Analyzer が必要とする外部ツールのリスト（オプション）。
        サブクラスでオーバーライドし、ToolRequirement を返す。
        デフォルトは空リスト（外部ツール不要）。"""
        return []
```

`required_tools()` は `run_type_check()` と同様のオプショナルメソッド。
`AnalyzerRegistry.verify_tools()` が各 Analyzer の `required_tools()` を収集し、
`shutil.which()` で存在確認を行う（Section 2.4 step 4）。

```python
@dataclass
class ToolRequirement:
    """外部ツールの要件。command はコマンド名、install_hint はインストール手順。"""
    command: str
    install_hint: str
```

### 2.1b AnalyzerRegistry（言語自動検出 + プラグイン管理）

```python
class AnalyzerRegistry:
    """言語 Analyzer の自動検出・管理を担う。

    プロジェクトルートをスキャンし、detect() が True を返す
    Analyzer を自動的にインスタンス化する。
    ユーザーは LanguageAnalyzer を継承したクラスを作成し、
    register() で登録するだけで新言語に対応できる。
    """

    def __init__(self):
        self._analyzer_classes: list[type[LanguageAnalyzer]] = []

    def register(self, analyzer_cls: type[LanguageAnalyzer]) -> None:
        """Analyzer クラスを登録する（重複チェック付き）。"""
        self._analyzer_classes.append(analyzer_cls)

    def detect_languages(self, project_root: Path) -> list[LanguageAnalyzer]:
        """プロジェクトで使用されている言語を検出し、
        対応する Analyzer のインスタンスリストを返す。"""
        return [cls() for cls in self._analyzer_classes if cls().detect(project_root)]

    def run_all(self, project_root: Path, target: Path) -> list[Issue]:
        """検出された全言語で lint + security を逐次実行し、Issue を統合して返す。
        Phase 2 以降で並列化を検討する。"""
        ...
```

**プラグイン探索パス**: `.claude/hooks/analyzers/` 配下の `*_analyzer.py` を自動探索。
`LanguageAnalyzer` を継承したクラスを含むモジュールを動的にインポートし、自動登録する。

### 2.1c ASTNode ラッパー型

```python
@dataclass
class ASTNode:
    """tree-sitter / Python ast の差異を吸収するラッパー型。"""
    name: str              # 関数名/クラス名
    kind: str              # "function" | "class" | "module" | "method"
    start_line: int
    end_line: int
    signature: str         # 引数・戻り値を含むシグネチャ文字列
    children: list["ASTNode"]
    docstring: str | None  # 先頭の docstring（あれば）
```

各 `LanguageAnalyzer.parse_ast()` はこの共通型に変換して返す。
tree-sitter の Node や Python ast.AST を直接公開しない。

### 2.2 初期サポート言語の実装

#### Python

```python
class PythonAnalyzer(LanguageAnalyzer):
    def detect(self, project_root):
        return (project_root / "pyproject.toml").exists() or
               any(project_root.rglob("*.py"))

    def run_lint(self, target):
        # ruff check --output-format json
        ...

    def run_security(self, target):
        # bandit -r -f json + semgrep --config auto --json
        ...

    def parse_ast(self, file_path):
        # ast.parse() または tree-sitter
        ...
```

#### JavaScript/TypeScript

```python
class JavaScriptAnalyzer(LanguageAnalyzer):
    def detect(self, project_root):
        return (project_root / "package.json").exists()

    def run_lint(self, target):
        # npx eslint --format json
        ...

    def run_security(self, target):
        # semgrep --config auto --json
        # npm audit --json
        ...

    def parse_ast(self, file_path):
        # tree-sitter (tree-sitter-javascript / tree-sitter-typescript)
        ...
```

#### Rust

```python
class RustAnalyzer(LanguageAnalyzer):
    def detect(self, project_root):
        return (project_root / "Cargo.toml").exists()

    def run_lint(self, target):
        # cargo clippy --message-format json
        ...

    def run_security(self, target):
        # cargo audit --json
        ...

    def parse_ast(self, file_path):
        # tree-sitter (tree-sitter-rust)
        ...
```

### 2.3 Issue データモデル

```python
@dataclass
class Issue:
    file: str           # 相対パス
    line: int           # 行番号
    severity: str       # "critical" | "warning" | "info"
    category: str       # "lint" | "security" | "type" | "dead-code"
    tool: str           # "ruff" | "bandit" | "semgrep" 等
    message: str        # 問題の説明
    rule_id: str        # ルール ID（E501, B101 等）
    suggestion: str     # 修正案（あれば）
```

### 2.4 パイプライン実行フロー

```
1. プロジェクトルートをスキャンし、使用言語を検出（AnalyzerRegistry.detect_languages()）
2. .claude/review-config.json の除外設定を適用
3. 該当する LanguageAnalyzer をインスタンス化
4. ツールインストール確認: shutil.which() で存在確認
   → 未インストールならエラー停止し、インストール手順を表示（FR-1）
   → --version によるバージョン互換性チェックは Phase 2 以降で追加
5. 各 Analyzer の run_lint() / run_security() を逐次実行
   - Phase 1: 逐次実行。Phase 2 以降で並列化を検討
6. Issue リストを .claude/review-state/static-issues.json に永続化
7. AST 構造マップを .claude/review-state/ast-map.json に永続化
8. サマリーレポートを生成し、LLM レビューの入力として提供
```

### 2.4b 再レビュー時のキャッシュ戦略

再レビュー時（FR-5）の静的解析:
- **変更ファイル**: 静的解析を再実行
- **未変更ファイル**: 前回の静的解析結果をキャッシュから利用
- **LLM レビュー**: ゼロベースで再実行（キャッシュなし）

キャッシュの無効化: ファイルのハッシュ値（SHA-256）で変更を検出する。

### 2.4c review-config.json スキーマ

設定ファイル `.claude/review-config.json` でパイプラインの動作を制御する。

```json
{
  "exclude_languages": [],
  "exclude_dirs": ["node_modules", ".venv", "vendor", "dist"],
  "max_parallel_agents": 4,
  "chunk_size_tokens": 3000,
  "overlap_ratio": 0.2,
  "auto_enable_threshold": 30000,
  "agent_retry_count": 2,
  "static_analysis_timeout_sec": 300,
  "file_size_limit_bytes": 1000000,
  "summary_max_tokens": 5000
}
```

全項目はオプション。未指定時は上記のデフォルト値を使用する。
ファイルが存在しない場合は全てデフォルトで動作する。

### 2.5 コンパクション対策（Phase A から組み込み）

```
.claude/review-state/
├── static-issues.json      # 静的解析の Issue リスト
├── ast-map.json            # AST 構造マップ（関数シグネチャ、クラス定義）
├── dependency-graph.json   # 依存グラフ（Plan D で追加）
├── contracts/              # 契約カード（Plan D で追加）
├── chunk-results/          # チャンクごとのレビュー結果（Plan B で追加）
└── summary.md              # LLM に渡すサマリー
```

**原則**: LLM コンテキストには判断に必要な情報のみ。事実の保管は外部ファイルに。

**ライフサイクル**: `review-state/` は `.gitignore` に追加し永続的に保持する。
次回レビューのキャッシュおよびログとして機能する。
明示的な削除が必要な場合はユーザーが手動で行う。

### 2.6 NFR-4 対応: Lost in the Middle 対策

`summary.md` および LLM に渡すプロンプトは以下の構造で配置する:

```
[先頭] Critical Issues（最重要の問題）
[先頭] レビュー指示・観点
[中間] 個別ファイル/チャンクの詳細
[末尾] Issue カウントサマリー（Critical: X / Warning: Y / Info: Z）
[末尾] 全体再レビュー原則（FR-5）のリマインド
```

重要な情報をコンテキストの先頭と末尾に配置し、Liu et al. (TACL 2024) の
Lost in the Middle 問題を軽減する。

## 3. Plan B: AST チャンキング設計

### 3.0 tree-sitter 導入方針

`chunker.py` 内で `try: import tree_sitter` し、未インストール時は Plan B をスキップして
Warning を表示する。プロジェクトの pyproject.toml に tree-sitter を必須依存として追加しない。
FR-2「tree-sitter がインストールできない環境では Plan B をスキップ」、
NFR-3（外部依存の最小化）との一貫性。ユーザーが必要に応じて pip install する方式。

インストール手順（ユーザー向け）:
```bash
pip install tree-sitter tree-sitter-python tree-sitter-javascript tree-sitter-rust
```

### 3.1 チャンク単位

| レベル | 単位 | 用途 |
|--------|------|------|
| L1 | 関数/メソッド | 最小レビュー単位 |
| L2 | クラス | クラス内の整合性チェック |
| L3 | モジュール（ファイル） | ファイル全体の構造チェック |

通常は L2（クラス単位）をベースとし、チャンク上限（デフォルト 3,000 トークン、`review-config.json` で調整可能）を
超えるクラスは L1（関数/メソッド単位）に自動分割する。
目標チャンクサイズ: 2,000-3,000 トークン（`review-config.json` の `chunk_size_tokens` で調整可能、デフォルト 3,000）。
のりしろサイズ上限: チャンクサイズの 20% 以内（最大 600 トークン、`overlap_ratio` で調整可能）。

**トークンカウント方法**: `len(text.split())` でワード数を近似トークン数として使用する。
外部トークナイザ（tiktoken 等）への依存は NFR-3 により追加しない。
コードのワード数は LLM トークン数のおおよその近似として十分実用的。

### 3.2 のりしろ設計

各チャンクに以下を付与:

```
[のりしろ: ファイルヘッダー]
- import 文全体
- モジュールレベルの定数・型定義

[チャンク本体]
- 関数/クラスの実コード

[のりしろ: シグネチャサマリー]
- 同一ファイル内の他関数/クラスのシグネチャ（本体なし）
- 直接の呼び出し先のシグネチャ（AST の Call ノードから特定、同一パッケージ内に限定）
```

**呼び出し先の特定方法**: AST の Call ノード（関数呼び出し）を走査し、
呼び出し先の関数/メソッド名を抽出する。同一パッケージ（`__init__.py` / `package.json` スコープ）内の
定義が見つかった場合、そのシグネチャ（引数・戻り値）をのりしろに含める。
パッケージ外の呼び出し先は import 文から推測可能なため、のりしろには含めない。

### 3.3 Map-Reduce フロー

```
Map（バッチ並列方式）:
  チャンクを max_parallel_agents 個ずつのバッチに分割（デフォルト 4、最大 10）
  バッチ1: チャンク1〜4 → Agent1〜4 を run_in_background で並列起動
           → 全 Agent 完了待ち
  バッチ2: チャンク5〜8 → Agent5〜8 を並列起動
           → 全 Agent 完了待ち
  ...

  エラーハンドリング:
  - Agent タイムアウト/エラー時: 最大 2回リトライ（agent_retry_count で調整）
  - リトライ後も失敗: Warning として報告し続行（未レビューチャンクとして記録）

Reduce（横断チェック — 静的解析ベース）:
  Issues1..N → 重複排除
            → API 呼び出しと定義の一致チェック（AST の Call ノード vs 関数定義）
            → 型の整合性チェック（引数の型が定義と一致するか）
            → 命名規則の統一性チェック（snake_case / camelCase の混在検出）
            → 統合レポート
```

**並列制御の設計根拠**: Claude Code の Agent ツールは `run_in_background` で非同期起動し
完了通知を受ける仕組み。「Agent 完了次第、次を投入」する動的ディスパッチは API 上不可能なため、
バッチ方式を採用する。バッチサイズ = `max_parallel_agents`。

**Reduce の実装方針**: 横断チェック（API 一致、型整合性、命名統一性）は
AST 情報と Issue リストを用いた静的解析で実現する。LLM に全チャンクを再度読ませるのではなく、
`ast-map.json` のシグネチャ情報を機械的に照合する。

**型の整合性チェック方針**:
- 型ヒントあり: シグネチャの引数型・戻り値型を照合（`def foo(x: int)` に `foo("str")` で Warning）
- 型ヒントなし: 呼び出し側の引数から型を推論してチェック
  - リテラル値（`foo(42)` → int、`foo("bar")` → str）は確定
  - 変数は代入元を AST で遡って推論（1 ホップまで、深い推論はしない）
  - 推論不可の場合はスキップ（偽陽性を避ける）
- 動的型付け言語（Python, JS）では Warning 扱い、静的型付け言語（Rust）では Critical 扱い

### 3.4 Chunk データモデル

```python
@dataclass
class Chunk:
    """チャンキングエンジンが生成するレビュー単位。"""
    file_path: str          # 対象ファイルの相対パス
    start_line: int         # チャンク本体の開始行
    end_line: int           # チャンク本体の終了行
    content: str            # チャンク本体のソースコード
    overlap_header: str     # のりしろ（ファイルヘッダー: import + 定数）
    overlap_footer: str     # のりしろ（シグネチャサマリー: 同一ファイル内 + 呼び出し先）
    token_count: int        # チャンク全体（本体 + のりしろ）の推定トークン数
    level: str              # "L1" | "L2" | "L3"（チャンク粒度）
    node_name: str          # 対象のクラス名/関数名（L3 の場合はファイル名）
```

### 3.5 チャンク分割アルゴリズム

```
入力: ファイルの ASTNode ツリー（parse_ast() の出力）

1. トップレベルノードを列挙（クラス、関数、モジュールレベルコード）
2. 各ノードのトークン数を計算（len(content.split())）
3. 分割判定:
   - クラス ≤ chunk_size_tokens → L2 チャンク（クラス全体）
   - クラス > chunk_size_tokens → L1 に分割（メソッド単位）
   - トップレベル関数 → L1 チャンク（そのまま）
   - モジュールレベルコード（import 以外）→ まとめて L3 チャンク
4. 各チャンクにのりしろを付与（Section 3.2）
5. のりしろ込みで chunk_size_tokens * (1 + overlap_ratio) を超えないよう調整
6. L1 分割後もなお chunk_size_tokens を超える巨大関数/メソッド:
   → そのまま 1 チャンクとして処理（構文的妥当性を優先）
   → Warning ログを出力
   → 「関数が大きすぎる（N tokens > chunk_size_tokens）」Issue を自動追加
```

### 3.6 full-review への統合位置

Plan B（AST チャンキング）は新しい Phase として独立させる:

| Phase | 内容 | Plan B 追加分 |
|-------|------|--------------|
| Phase 0 | 静的解析 | （変更なし） |
| Phase 1 | ループ初期化 | （変更なし） |
| Phase 1.5 | context7 MCP 検出 | （変更なし） |
| **Phase 1.7** | **AST チャンキング** | **新規: chunker.py でファイルをチャンク分割** |
| Phase 2 | 並列監査 | チャンクがある場合はチャンク単位で Agent を起動 |
| Phase 3〜6 | 統合〜完了 | Reduce の横断チェックを Phase 3 に追加 |

Phase 1.7 の動作:
- tree-sitter がインストール済み: 全対象ファイルをチャンク分割、結果を `review-state/chunks.json` に保存
- tree-sitter 未インストール: Warning 表示、Phase 2 は従来のファイル全体レビューにフォールバック

Phase 2 でのチャンク受け渡し:
- Agent にチャンクファイルのパスを渡し、Agent が自分で読み込む
- Agent プロンプトには「このファイルを読んでレビューせよ」と指示
- Agent は `overlap_header` + `content` + `overlap_footer` を結合して文脈を理解する

### 3.8 テスト戦略（B-2 Map-Reduce）

モック Agent（LLM 呼び出しなし）でバッチ並列制御ロジックを検証する:
- 50 モックチャンクを 4 並列（13 バッチ）で処理
- 各モック Agent は固定の Issue リストを返す
- バッチ間の順序制御、エラーリトライ、Reduce の重複排除を自動テストで検証

実 LLM テストは LAM 自体に対して手動で実施する（CI には含めない）。

### 3.7 チャンク結果の永続化

チャンクごとの Issue リストを個別ファイルで保存する:

```
.claude/review-state/chunk-results/
├── src-hooks-analyzers-base-py-L2-AnalyzerRegistry-42-187.json
├── src-hooks-analyzers-run_pipeline-py-L1-run_phase0-87-151.json
└── ...
```

ファイル名フォーマット: `{path_segments}-{level}-{node_name}-{start}-{end}.json`
- `path_segments`: ファイルパスの `/` を `-` に置換（検索性確保）
- `level`: L1/L2/L3
- `node_name`: クラス名/関数名
- `start`-`end`: 行番号範囲

これによりファイル名だけで「どのファイルのどの関数/クラスの結果か」が即座に判別できる。

## 4. Plan C: 階層的レビュー設計

### 4.1 レイヤー構成

```
Layer 1 (ファイル): Phase 2 の並列監査 Agent がレビュー + 概要カード生成（同時実行）
    ↓ 概要カード群（review-state/cards/file-cards/）
Layer 2 (モジュール): メインフローで逐次実行。Reduce チェック + モジュール境界固有チェック → 要約カード生成
    ↓ 要約カード群（review-state/cards/module-cards/）
Layer 3 (システム): メインフローで逐次実行。機械的チェック + LLM 仕様ドリフト検出
    ↓ 統合レポート
全体再レビュー: 修正後は Layer 1 からゼロベースで再実行（FR-5）
```

### 4.2 full-review への統合位置

Phase 2.5 として Phase 2（並列監査）と Phase 3（レポート統合）の間に挿入する。

```
Phase 0    → 静的解析
Phase 0.5  → context7 MCP 検出
Phase 1    → ループ初期化
Phase 1.7  → AST チャンキング
Phase 2    → 並列監査（Layer 1: レビュー + 概要カード生成を同時実行）
Phase 2.5  → 階層的レビュー（Layer 2: モジュール統合、Layer 3: システム統合）【新規】
Phase 3    → レポート統合
Phase 4    → 修正
Phase 5    → 検証（Green State 判定）
Phase 6    → 完了報告
```

### 4.3 概要カード仕様（Layer 1 出力）

Phase 2 の並列監査 Agent がレビューと同時に生成する（100-200 トークン）。
Agent プロンプトに「レビュー結果 + 概要カードを出力せよ」と指示する。

```markdown
## [ファイルパス]
- **責務**: [LLM が1行で生成]
- **公開 API**: [AST マップから機械的に取得]
- **依存先**: [import 文から機械的に取得]
- **依存元**: [ast-map.json の import 情報を逆引きして導出。Plan D で依存グラフに置換]
- **Issue 数**: Critical: X / Warning: Y / Info: Z
```

**フィールド生成方式**:

| フィールド | 方式 | ソース |
|-----------|------|--------|
| 責務 | LLM 生成 | Agent がコードを読んで1行サマリー |
| 公開 API | 機械的 | ast-map.json |
| 依存先 | 機械的 | import 文（ast-map.json） |
| 依存元 | 機械的 | ast-map.json の import 情報を逆引き |
| Issue 数 | 機械的 | static-issues.json + チャンク結果 |

### 4.4 要約カード仕様（Layer 2 出力）

モジュール単位（`__init__.py` / `package.json` 境界）で概要カードを集約する。
メインフローで逐次実行（Agent 不要。モジュール数は通常少なく、並列化のオーバーヘッドに見合わない）。

**Layer 2 のチェック内容**:
1. Phase 2 Reduce のチェック結果をモジュール単位に集約
2. モジュール境界固有チェック（以下3点で開始、運用しながら追加）:
   - `__init__.py` の `__all__` と実際のエクスポートの一致
   - `__init__.py` で re-export しているが実際に使われていないシンボル
   - モジュール内のファイル間で同名の関数/クラスが衝突していないか

### 4.5 システムレビュー（Layer 3）

メインフローで逐次実行。以下の2段構成:

1. **機械的チェック**: 循環依存検出、命名パターン違反（ast-map.json ベース）
2. **LLM 仕様ドリフト検出**: 全モジュールの要約カード群 + `docs/specs/` 配下の全 `.md` ファイルを
   LLM に渡し、仕様と実装の乖離を指摘させる

**仕様書の特定方法**: `docs/specs/` 配下の全 `.md` ファイルを自動で渡す。
`docs/specs/` は SSOT であり、通常は数ファイル程度でトークン量は問題にならない。
将来的にトークン量が問題になった場合は `review-config.json` に `spec_files` フィールドを追加し、
対象を明示指定する方式に移行する。

### 4.6 カードの永続化

```
.claude/review-state/
├── cards/
│   ├── file-cards/      # 概要カード（Layer 1 出力）
│   │   ├── src-analyzers-base-py.json
│   │   └── ...
│   └── module-cards/    # 要約カード（Layer 2 出力）
│       ├── src-analyzers.json
│       └── ...
```

ファイル名: パスの `/` を `-` に置換（chunk-results と同じ規則）。

### 4.7 再レビュー原則（FR-5）

修正後の再レビューは Layer 1 からの全体ゼロベース再実行とする。
部分再レビューは潜在的不具合の放置になるため禁止。

将来的に Plan D（依存グラフ駆動）が実装された後、影響範囲分析に基づく
スコープ最適化を検討する。ただしその場合でも「一度見て問題なしが確定した」
チャンクのみスキップ可能とし、未検証チャンクのスキップは禁止。

## 5. Plan D: 依存グラフ駆動設計

対応仕様: FR-7a〜FR-7f

### 5.0 設計判断の前提

#### Non-Goals（Phase 4 でやらないこと）

- **Plan E（ハイブリッド統合）**: Phase 5 に据え置き。Plan D 完了後に設計する
- **クロスリポジトリ依存解析**: 単一リポジトリ内の import 依存のみ対象
- **動的依存の解析**: 実行時の依存（DI、プラグイン）は対象外。静的 import のみ
- **言語横断依存**: Python→JS 等の言語間依存は対象外。各言語内の依存グラフを独立構築

#### Alternatives Considered（却下した代替案）

| 代替案 | 却下理由 |
|:------|:--------|
| NetworkX 導入 | 外部依存が増える。`graphlib.TopologicalSorter`（標準ライブラリ）+ Phase 3 の Tarjan で十分 |
| pydeps / pyan 導入 | 外部ツール依存。既存の `import_map`（AST ベース）で同等の情報が取得済み |
| PageRank による重要度ランキング | ユースケースが不明確。トポロジカルソートでレビュー順序は決定可能 |
| 契約カードの機械的のみ生成 | 前提条件・保証・不変条件は AST だけでは推論不可。LLM ハイブリッドが必要 |
| FR-5 完全維持（影響範囲分析なし） | 概要カードの機械的フィールド再計算は無駄。LLM はゼロベース維持で安全性を担保 |

#### Success Criteria（成功基準）

| 基準 | 計測方法 |
|:-----|:--------|
| 依存グラフが正しく構築される | LAM 自体（10K行）に対して実行し、既知の依存関係と一致することを手動検証 |
| トポロジカル順レビューで契約違反を検出できる | 意図的に契約違反するテストコードを用意し、Agent が検出することを確認 |
| 影響範囲分析で概要カード再利用が機能する | 1ファイル修正後の再レビューで、影響範囲外の概要カードが再利用されることを確認 |
| 全テストが通過 | `pytest .claude/hooks/` 全 PASSED |
| full-review が完走する | LAM 自体に対して Phase 4 対応版 full-review を手動実行し、Green State に到達 |

### 5.1 グラフ構築（FR-7a）

既存の `_build_import_graph`（card_generator.py）を拡張する。外部ライブラリは導入しない。

```
入力: import_map (dict[str, list[str]])  ← Phase 0/2 で生成済み
  ↓
_build_import_graph() → graph, all_nodes, node_to_file  ← Phase 3 実装済み
  ↓
_find_sccs(graph) → SCC リスト  ← Phase 3 実装済み（Tarjan）
  ↓
_condense_sccs(graph, sccs) → condensed_graph  ← Phase 4 新規
  ↓
graphlib.TopologicalSorter(condensed_graph) → topo_order  ← Phase 4 新規
  ↓
永続化: review-state/dependency-graph.json
```

**SCC スーパーノード化**: SCC 内の複数ノードを1つのスーパーノード（名前: `scc_{n}`）に縮約する。
スーパーノードの辺は、SCC 内の任意のノードが持つ外部辺を集約したもの。

**dependency-graph.json スキーマ**:

```json
{
  "topo_order": ["module_a", "scc_0", "module_b"],
  "sccs": [["module_x", "module_y"]],
  "node_to_file": { "module_a": "src/a.py", "module_x": "src/x.py", "module_y": "src/y.py" }
}
```

> **Note**: `sccs` は SCC メンバーリストの配列（`list[list[str]]`）。
> `node_to_file` はノード名 → 単一ファイルパスのマッピング（SCC のスーパーノード名はキーに含まない）。
> `edges` は `build_topo_order()` の戻り値には含まない（`graphlib.TopologicalSorter` が内部で使用）。

### 5.2 トポロジカル順レビュー・修正（FR-7b）

**レビュー順序（Phase 2 拡張）**:

```
topo_order: [A, B, scc_0, C]

Step 1: A をレビュー → 契約カード(A) 生成
Step 2: B をレビュー（契約カード(A) をコンテキストに含む）→ 契約カード(B) 生成
Step 3: scc_0 (X, Y) をバッチレビュー（契約カード(A,B) をコンテキストに含む）→ 契約カード(scc_0) 生成
Step 4: C をレビュー（契約カード(A,B,scc_0) をコンテキストに含む）→ 契約カード(C) 生成
```

**修正順序（Phase 4 拡張）**: 同じトポロジカル順で修正し、上流の修正が下流に波及するのを最小化する。

### 5.3 契約カード（FR-7c）

#### データモデル

```python
@dataclass
class ContractCard:
    module_name: str
    public_api: list[str]        # 機械的（FileCard から流用）
    signatures: list[str]        # 機械的（AST の signature フィールド）
    preconditions: list[str]     # LLM 推論
    postconditions: list[str]    # LLM 推論
    side_effects: list[str]      # LLM 推論
    invariants: list[str]        # LLM 推論
```

#### 生成フロー

1. Phase 2 の Agent が各ファイルをレビューする際、契約フィールドもマーカー付きで出力:
   ```
   ---CONTRACT-CARD---
   preconditions: [...]
   postconditions: [...]
   side_effects: [...]
   invariants: [...]
   ---END-CONTRACT-CARD---
   ```
2. `parse_contract()` でマーカーから抽出（`parse_responsibility()` と同パターン）
3. `merge_contracts()` でモジュール単位に集約
4. `save_contract_card()` で `review-state/contracts/{module-name}.json` に永続化

#### 下流レビューでの活用

下流モジュールの Agent プロンプトに上流の契約カードを含める:
```
以下は上流モジュールの契約です。これらの前提条件・保証に違反する呼び出しがないか確認してください。
[契約カード JSON]
```

### 5.4 影響範囲分析（FR-7d）

```
修正ファイル集合 → 依存グラフで上流方向に辿る → 影響範囲ファイル集合

影響範囲内:
  - 概要カード: 再生成
  - LLM レビュー: ゼロベース再実行

影響範囲外:
  - 概要カード: 機械的フィールド再利用可（責務フィールドは再生成）
  - LLM レビュー: ゼロベース再実行（スキップ不可）
  - 契約カード: 再生成（キャッシュなし）
```

### 5.5 D-0: シークレットスキャン Phase 0 統合（FR-7e）

- `lam-stop-hook.py` から `_SECRET_PATTERN` / `_SAFE_PATTERN` を削除
- `python_analyzer.py` の bandit 設定で B105（hardcoded password）/ B106（hardcoded SQL）が有効であることを確認
- Stop hook の G5 チェックからシークレットスキャン部分を除去

### 5.6 ReviewResult.issues 型統一（FR-7f）

`orchestrator.py` の `ReviewResult.issues` を `list[str]` → `list[Issue]` に変更。
`build_review_prompt()` の出力パースを `Issue` dataclass に変換するロジックを追加。

### 5.7 永続化構造（Phase 4 追加分）

```
.claude/review-state/
├── dependency-graph.json    # グラフ + トポロジカル順序 + SCC
├── contracts/               # 契約カード
│   ├── src-core.json
│   └── src-analyzers.json
├── cards/                   # 既存（Phase 3）
├── chunk-results/           # 既存（Phase 2）
└── ...
```

## 6. Plan E: ハイブリッドパイプライン設計

対応仕様: `docs/specs/scalable-code-review-phase5-spec.md` FR-E1〜FR-E3

### 6.0 設計判断の前提

#### Problem Statement

現行の `/full-review` は Plan A〜D の追加により Phase 番号が 11 段階
（0, 0.3, 1, 1.5, 1.7, 2, 2.5, 3, 4, 5, 6）に肥大化している。
認知負荷の増大、スケール判定の分散、E2E 検証の欠如が課題。

#### Non-Goals（Plan E でやらないこと）

- `/auditing` や CI/CD パイプラインへの統合（Plan F 以降）
- プロンプトテンプレートの内容変更（Stage 再編に伴う見出し統合・改番のみ許容）
- Plan A〜D の Python コードの変更・リファクタリング
- `_find_sccs` の反復実装化（既知制限、別途対応）
- `import_map` 生成ロジックの新規実装

#### Alternatives Considered（却下した代替案）

| 代替案 | 却下理由 |
|:------|:--------|
| Phase 番号をそのまま維持し、ドキュメント上で Stage グルーピングだけ行う | 二重管理。full-review.md 内の自己参照が Phase 番号のままとなり、認知負荷が解消されない |
| `run_pipeline.py` に `detect_scale()` を追加（scale_detector.py を作らない） | NFR-E1「既存関数群を修正してはならない」に抵触。関数追加もファイル変更として扱う |
| `should_enable_static_analysis()` を scale_detector から呼び出して結果をマッピング | 既存関数は 3 値（skip/suggest/auto）しか返さず、Plan A〜D の 4 段階区分に変換するロジックが複雑化する。独立した閾値テーブルの方がシンプル |
| `base.AnalyzerRegistry.verify_tools()` をラップして例外を握りつぶす | Error Swallowing は code-quality-guideline.md の Critical 指摘対象。`shutil.which()` による独立チェックが正しい |
| `chunker._TREE_SITTER_AVAILABLE` を直接参照 | プライベート変数の外部参照は将来のリファクタリングで無言破壊リスクあり。`importlib.util.find_spec()` の方が宣言的かつ安定 |
| E2E テストを `test_scale_detector.py` と `test_e2e_review.py` の 2 ファイルに分割 | NFR-E1「新規 Python ファイルは `scale_detector.py` と `test_e2e_review.py` に限定」に抵触 |
| Security フィクスチャを LLM 検出テスト（非決定的）として扱う | bandit B105/B106 が確実に検出できるため、静的解析の決定的テストとして扱う方が恒久的に 100% を保証できる |

#### Success Criteria

| 基準 | 計測方法 |
|:-----|:--------|
| full-review.md が Stage 体系で構成されている | Stage 0〜5 のセクションが存在し、中間 Phase 番号がないこと |
| 自動スケール判定が動作する | `scale_detector.py` の単体テストで ~10K / 30K / 100K / 300K の各閾値が正しく判定されること |
| 前提条件チェックが動作する | ruff/bandit/tree-sitter 未インストール時に Warning 表示され、対応 Plan がスキップされること |
| E2E テストフレームワークが存在する | `test_e2e_review.py` が実行可能で、3 種のフィクスチャが配置されていること |
| 既存テストが全 PASSED | 396+ テスト全 PASSED |
| NFR-2 後方互換 | ~10K 行プロジェクトで Plan セット「なし」が返り、Stage 1〜3 スキップのログが出力されること |

### 6.1 AoT 分解と Three Agents 分析

#### AoT Decomposition

| Atom | 判断内容 | 依存 |
|:-----|:---------|:-----|
| A1 | Stage 体系マッピング: Phase → Stage の再編方法 | なし |
| A2 | scale_detector.py のアーキテクチャ: 既存コードとの関係、責務分担 | A1 |
| A3 | E2E テストフレームワーク: テストアーキテクチャ、フィクスチャ設計 | なし |
| A4 | full-review.md 移行戦略: 後方互換を保ちつつ再編する方法 | A1, A2 |

#### Atom A1: Stage 体系マッピング

**[Affirmative]**: 11 段階 → 6 段階への再編は認知負荷を大幅に削減する。Stage 0〜5 の番号体系は直感的で安定的。Python コード変更なし（full-review.md のみ）は安全。

**[Critical]**: 見出し構造の変更は AI の挙動に影響する可能性がある。「Phase 1.7 の次が Phase 2」という非線形番号が消えることは良いが、「Phase 0.3 完了後、Phase 1 に進む」等の誘導文が 23 箇所存在し、全件更新しないとフロー断絶が起きる。Stage 内の Step 実行順序（特に Stage 1 内の静的解析 → 依存グラフ構築の順序）の明確化も必要。

**[Mediator]**: FR-E1 の Stage 体系を採用。Stage 0 にはループ初期化 + context7 検出 + Scale Detection を統合する。Stage 内の Step 構造は既存を維持しつつ、全 self-reference（23 箇所）を漏れなく更新する。各 Stage 先頭に「実行条件 / 入力 / 出力」の契約を明記する。

#### Atom A2: scale_detector.py のアーキテクチャ

**[Affirmative]**: `run_pipeline.count_lines()` を import して再利用し、DRY を維持すべき。判定ロジックの集約は SRP に適合。

**[Critical]**: `verify_tools()` は例外を投げる設計であり、Scale Detector の「Warning + スキップ」セマンティクスと矛盾する。`should_enable_static_analysis()` は 3 値のみで Plan A〜D の 4 段階に不十分。`chunker._TREE_SITTER_AVAILABLE` はプライベート変数。

**[Mediator]**: `count_lines()` のみ import で再利用。`should_enable_static_analysis()` は使用せず独自閾値テーブルを持つ（上位互換）。前提条件チェックは `shutil.which()` と `importlib.util.find_spec()` で独立実装。

#### Atom A3: E2E テストフレームワーク

**[Affirmative]**: フィクスチャで既知 Issue を仕込み検出率を計測する方式は有用。pytest marker でテスト分離すれば CI への影響がない。

**[Critical]**: LLM 出力は非決定的。検出率テストの結果が揺れる。Security フィクスチャは bandit が確実に検出できるため LLM に頼る必要がない。Warning 80% 基準未達でテストを fail させると CI の信頼性が失われる。

**[Mediator]**: 3 層分離（決定的 / LLM 検出率 / 収束テスト）を pytest marker で実現。Security フィクスチャは決定的テストとして扱う。Warning 基準未達は結果記録 + Issue 起票推奨とし、テスト自体は pass。

#### Atom A4: full-review.md 移行戦略

**[Affirmative]**: 一括書き換えで整合性を確保。段階的移行は中途半端な二重管理のリスクがある。

**[Critical]**: 一括書き換えは self-reference 漏れ時にフロー断絶。連鎖ドキュメント（設計書、タスク定義）の更新も必要。

**[Mediator]**: self-reference を全件棚卸し（Section 6.5 テーブル参照）した上で一括移行。移行は 6 ステップで実施し、各ステップ後に検証。

#### AoT Synthesis

**統合結論**: Stage 体系への一括移行を採用し、scale_detector.py は既存コードを import しつつ独自閾値テーブルを持つ独立モジュールとして設計する。E2E テストは pytest marker による 3 層分離で管理する。

### 6.2 Stage 体系設計（FR-E1）

#### 6.2.1 Stage-to-Phase 完全マッピング

```
Stage 0: 初期化
  Step 1: ループ状態ファイル生成        ← Phase 1
  Step 2: context7 MCP 検出            ← Phase 1.5
  Step 3: Scale Detection 判定（新規）  ← Phase 0 Step 1 から移管 + FR-E2

Stage 1: 静的分析 + 依存グラフ構築 【実行条件: Plan A 以上】
  Step 1: 静的解析実行（run_phase0）    ← Phase 0 Step 2
  Step 2: 結果の Stage 2 への接続      ← Phase 0 Step 3
  Step 3: 依存グラフ構築               ← Phase 0.3

Stage 2: チャンク分割 + トポロジカル順レビュー
  Step 1: tree-sitter 利用可否チェック  ← Phase 1.7 Step 1
  Step 2: チャンク分割（chunks.json）   ← Phase 1.7 Step 2
  Step 3: 並列監査                     ← Phase 2（全内容）
  Step 4: 概要カード + 契約カード生成   ← Phase 2 完了後フロー

Stage 3: 階層的統合 + レポート生成
  Step 1: Layer 2 — モジュール統合      ← Phase 2.5 Step 1
  Step 2: 契約カード永続化              ← Phase 2.5 Step 1.5
  Step 3: Layer 3 — 機械的チェック      ← Phase 2.5 Step 2
  Step 4: Layer 3 — LLM 仕様ドリフト検出← Phase 2.5 Step 3
  Step 5: レポート統合 + PG/SE/PM 分類  ← Phase 3

Stage 4: トポロジカル順修正
  Step 1: PG/SE 級修正（トポロジカル順）← Phase 4
  Step 2: PM 級処理フロー              ← Phase 4 PM 級処理

Stage 5: 検証 + Green State 判定 + 完了
  Step 1: G1〜G5 チェック              ← Phase 5
  Step 2: 影響範囲分析                 ← Phase 5（FR-7d）
  Step 3: ループ継続/停止判定           ← Phase 5 ループ制御
  Step 4: 完了報告 + ループログ出力     ← Phase 6
```

#### 6.2.2 Stage 間データフロー契約（FR-E1b）

**永続化成果物（Stage 間で引き継ぐファイル）**:

| Stage | 入力（前 Stage から） | 出力（次 Stage へ） |
|:------|:---------------------|:-------------------|
| **Stage 0** | 対象パス（引数） | `lam-loop-state.json`, `scale-detection.json` |
| **Stage 1** | 対象パス, `review-config.json`（任意）, `scale-detection.json` | `static-issues.json`, `ast-map.json`, `import-map.json`, `dependency-graph.json`, `summary.md` |
| **Stage 2** | `ast-map.json`, `import-map.json`, `dependency-graph.json`（任意）, `static-issues.json`（任意） | `file-cards/`, `contracts/`, `chunk-results/`（チャンクモード時） |
| **Stage 3** | `file-cards/`, `contracts/`（任意）, `ast-map.json`, `import-map.json` | 統合レポート（`audit-reports/YYYY-MM-DD-iterN.md`）, `module-cards/`, `layer3-issues.json` |
| **Stage 4** | 統合レポート, `dependency-graph.json`（任意） | 修正済みコード, 更新済み `lam-loop-state.json` |
| **Stage 5** | テスト結果, lint 結果, `lam-loop-state.json` | Green State 判定, ループログ（`logs/`） |

**ステージ制御フラグ（lam-loop-state.json 内）**:

| フラグ | セット Stage | 参照 Stage | 意味 |
|:-------|:------------|:-----------|:-----|
| `active` | Stage 0 | Stage 5 | ループ有効フラグ |
| `iteration` | Stage 5 | Stage 2, 5 | 現在イテレーション番号 |
| `fullscan_pending` | Stage 5 | Stage 2 | フルスキャン待ちフラグ |
| `pm_pending` | Stage 4 | Stage 4, Stop hook | PM級承認待ちフラグ |

#### 6.2.3 後方互換メカニズム（~10K 行プロジェクト）

Scale Detection が Plan セット「なし」を返す場合（~10K 行）の動作:

```
Stage 0: ループ初期化 + context7 検出 + Scale Detection → Plan セット「なし」
Stage 1: スキップ（Plan A 未満のため）
Stage 2: 従来モード（ファイル全体レビュー、チャンクなし、トポロジカル順なし）
Stage 3: レポート統合のみ実行（Layer 2, 3 はスキップ）
Stage 4: 従来通り修正（重要度順）
Stage 5: 従来通り検証 + 完了報告
```

各 Stage 先頭に「実行条件」を記述し、条件分岐を明示する:

| Stage | 実行条件 |
|:------|:---------|
| Stage 0 | 常に実行 |
| Stage 1 | Scale Detection で Plan A 以上が有効と判定された場合のみ |
| Stage 2 | 常に実行（チャンクモード/従来モードは Plan B の有無で分岐） |
| Stage 3 | 常に実行（Layer 2/3 は Plan C 以上の場合のみ。レポート統合は常に実行） |
| Stage 4 | 常に実行（トポロジカル順は Plan D の場合のみ） |
| Stage 5 | 常に実行 |

### 6.3 scale_detector.py 設計（FR-E2）

#### 6.3.1 データモデル

```python
@dataclass
class PlanStatus:
    """個別 Plan の判定結果。"""
    enabled: bool      # 行数閾値から有効化すべきか
    available: bool    # 前提条件が充足されているか
    reason: str        # 表示用メッセージ（例: "ruff: installed, bandit: installed"）

@dataclass
class ScaleDetectionResult:
    """Scale Detection の判定結果全体。"""
    line_count: int
    recommended_plans: list[str]                # 閾値テーブルからの推奨 ["A", "B", "C"]
    active_plans: list[str]                     # enabled=True かつ available=True のプラン
    plan_statuses: dict[str, PlanStatus]        # "A"|"B"|"C"|"D" → PlanStatus
```

#### 6.3.2 閾値テーブル

```python
_PLAN_THRESHOLDS: list[tuple[int, list[str]]] = [
    (300_000, ["A", "B", "C", "D"]),
    (100_000, ["A", "B", "C"]),
    ( 30_000, ["A", "B"]),
    ( 10_000, ["A"]),
    (      0, []),
]
```

`should_enable_static_analysis()` を利用しない理由: 既存関数は 3 値（skip/suggest/auto）を返し、Plan A 単体の有効化判定にしか使えない。scale_detector は Plan A〜D の 4 段階を区別する必要があり、独立した閾値テーブルを持つ方がシンプル。両者の閾値（10K/30K）は重複するが、scale_detector がより多くの段階を表現する上位互換として位置づける。

#### 6.3.3 前提条件チェック

| Plan | チェック方法 | 判定ロジック |
|:-----|:-----------|:-----------|
| Plan A | `shutil.which("ruff")`, `shutil.which("bandit")` | 両方インストール済みなら available=True |
| Plan B | `importlib.util.find_spec("tree_sitter")` | tree-sitter パッケージが見つかれば available=True |
| Plan C | Plan B の PlanStatus.available を参照 | Plan B が available なら自動的に available=True |
| Plan D | `Path(".claude/review-state/import-map.json").exists()` | ファイル存在で available=True |

**設計判断**: `base.AnalyzerRegistry.verify_tools()` は `ToolNotFoundError` を投げて処理を停止する設計であり、Scale Detector の「Warning 表示 + スキップ」セマンティクスと矛盾するため使用しない。`chunker._TREE_SITTER_AVAILABLE` はプライベート変数であり外部参照は設計違反のため、`importlib.util.find_spec()` で代替する。

#### 6.3.4 公開 API

```python
def detect_scale(
    project_root: Path,
    config: ReviewConfig | None = None,
) -> ScaleDetectionResult:
    """プロジェクト規模を検出し、有効化する Plan を判定する。

    1. count_lines() で行数をカウント（run_pipeline.py から import）
    2. 閾値テーブルで推奨 Plan セットを決定
    3. 各 Plan の前提条件をチェック
    4. 結果を ScaleDetectionResult として返す
    """

def format_scale_detection(result: ScaleDetectionResult) -> str:
    """FR-E2c 準拠のフォーマット済み出力を生成する。

    出力例:
    === Scale Detection ===
    Lines: 45,230
    Recommended: Plan A + B + C
    Active Plans:
      Plan A: ✓ (ruff: installed, bandit: installed)
      Plan B: ✓ (tree-sitter: installed)
      Plan C: ✓ (auto)
      Plan D: ✗ (import-map.json not found — skipping topological ordering)
    """
```

**CLI エントリポイント**: `if __name__ == "__main__":` ブロックで CLI として実行可能にし、`ScaleDetectionResult` を JSON 変換して stdout 出力 + `.claude/review-state/scale-detection.json` に永続化する。full-review.md の Stage 0 は `python3 .claude/hooks/analyzers/scale_detector.py <project_root>` を呼び出す。

#### 6.3.5 既存コードとの関係

| 既存要素 | 利用方法 | 修正の要否 |
|:---------|:---------|:---------|
| `run_pipeline.count_lines()` | `from analyzers.run_pipeline import count_lines` で直接 import | 不要 |
| `run_pipeline.should_enable_static_analysis()` | **利用しない**（独自閾値テーブルで上位互換） | 不要 |
| `base.AnalyzerRegistry.verify_tools()` | **利用しない**（例外投出設計のため不適合） | 不要 |
| `chunker._TREE_SITTER_AVAILABLE` | **利用しない**（`importlib.util.find_spec` で代替） | 不要 |
| `config.ReviewConfig` | `detect_scale()` の引数として受け取り、`exclude_dirs` を `count_lines()` に渡す | 不要 |

依存方向: `scale_detector` → `run_pipeline`（単方向）。`run_pipeline` は `scale_detector` に依存しないため循環 import のリスクなし。

#### 6.3.6 Stage 0 への統合フロー

```
Stage 0 Step 3: Scale Detection
  1. python3 .claude/hooks/analyzers/scale_detector.py $PROJECT_ROOT を実行
  2. stdout に FR-E2c フォーマットの判定結果が表示される
  3. .claude/review-state/scale-detection.json に結果が永続化される
  4. active_plans に基づいて後続 Stage の動作を決定:
     - active_plans が空    → Stage 1 スキップ、Stage 2 従来モード
     - "A" を含む           → Stage 1 実行
     - "B" を含む           → Stage 2 チャンクモード
     - "C" を含む           → Stage 3 全 Layer 実行
     - "D" を含む           → Stage 2/4 トポロジカル順
```

### 6.4 E2E テストフレームワーク設計（FR-E3）

#### 6.4.1 テスト責務の 3 層分離

| 層 | クラス | pytest marker | CI | 決定性 |
|:---|:------|:-------------|:---|:------|
| 決定的 | `TestScaleDetection` | なし | 組み込む | 決定的（pytest） |
| LLM 検出率 | `TestDetectionRate` | `@pytest.mark.e2e_llm` | 除外 | 非決定的（LLM 依存） |
| 収束 | `TestConvergence` | `@pytest.mark.e2e_convergence` | 除外 | 非決定的（LLM 依存） |

`pyproject.toml` 追記:

```toml
[tool.pytest.ini_options]
markers = [
    "e2e_llm: LLM依存テスト（CI除外）",
    "e2e_convergence: 収束テスト（CI除外・手動実行）",
]
```

既存の `addopts` に `-m 'not e2e_llm and not e2e_convergence'` を追加し、素の `pytest` 実行では決定的テストのみが走るようにする。LLM 依存テストは `pytest -m e2e_llm` で明示的に実行する。

#### 6.4.2 test_e2e_review.py インターフェース

```python
# .claude/hooks/analyzers/tests/test_e2e_review.py

@dataclass
class DetectionResult:
    """検出率テストの1回分の結果。"""
    fixture_name: str
    expected_count: int
    detected_count: int
    detection_rate: float
    meets_target: bool

@dataclass
class E2ERunRecord:
    """E2E テスト全体の実行記録。"""
    run_id: str               # YYYYMMDD_HHMMSS
    test_type: str            # "detection" | "convergence" | "scale"
    status: str               # "passed" | "failed" | "skipped"
    summary: str
    details: list[dict]
    elapsed_seconds: float


class TestScaleDetection:
    """FR-E3b-3: scale_detector.py 決定的テスト（CI 対象）。"""

    def test_under_10k_returns_no_plans(self) -> None: ...
    def test_10k_to_30k_returns_plan_a(self) -> None: ...
    def test_30k_to_100k_returns_plan_a_and_b(self) -> None: ...
    def test_100k_to_300k_returns_plan_a_b_c(self) -> None: ...
    def test_over_300k_returns_all_plans(self) -> None: ...
    def test_plan_a_skipped_when_ruff_missing(self, monkeypatch) -> None: ...
    def test_plan_a_skipped_when_bandit_missing(self, monkeypatch) -> None: ...
    def test_plan_b_fallback_when_tree_sitter_missing(self, monkeypatch) -> None: ...
    def test_plan_d_skipped_when_import_map_missing(self, tmp_path) -> None: ...
    def test_output_format_matches_fr_e2c(self) -> None: ...


@pytest.mark.e2e_llm
class TestDetectionRate:
    """FR-E3b-1: 検出率テスト（CI 除外）。"""

    def test_critical_silent_failure_detection(self) -> None: ...
    def test_warning_long_function_detection(self) -> None: ...
    def test_security_hardcoded_password_detection(self) -> None: ...
    def test_detection_results_are_recorded(self) -> None: ...


@pytest.mark.e2e_convergence
class TestConvergence:
    """FR-E3b-2: 収束テスト（CI 除外・手動実行）。"""

    def test_lam_reaches_green_state(self) -> None: ...
```

#### 6.4.3 フィクスチャ設計

**配置先**: `.claude/hooks/analyzers/tests/fixtures/e2e/`

```
fixtures/e2e/
├── README.md                        # フィクスチャ概要・Issue 箇所一覧
├── critical_silent_failure.py       # Critical: Silent Failure × 3箇所
├── warning_long_function.py         # Warning: Long Function (51行+) × 2箇所
├── security_hardcoded_password.py   # Security: ハードコードパスワード × 3箇所
└── combined_issues.py               # 複合: 全 Issue 種別 × 各1箇所
```

**フィクスチャ設計原則**:

- 各ファイルは単一の Issue 種別に特化（`combined_issues.py` を除く）
- 各 Issue 箇所に `# FIXTURE-ISSUE-N:` コメントを付与し、行番号を固定
- Security フィクスチャは bandit B105/B106 が確実に検出するパターンを使用（決定的テスト層）
- フィクスチャの変更は PM 級扱い（テスト基準の変更に相当）

**critical_silent_failure.py の構造例**:

```python
"""E2E フィクスチャ: Critical - Silent Failure (3箇所)"""

def process_payment(amount: float) -> bool:
    try:
        result = _call_payment_api(amount)
        return result.success
    except Exception:
        # FIXTURE-ISSUE-1: Silent Failure — 例外握りつぶし
        return False

def load_config(path: str) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        # FIXTURE-ISSUE-2: Silent Failure — 空 dict で隠蔽
        return {}

class DataProcessor:
    def transform(self, data: list) -> list:
        results = []
        for item in data:
            try:
                results.append(self._process_item(item))
            except ValueError:
                # FIXTURE-ISSUE-3: Silent Failure — エラースキップ
                pass
        return results
```

#### 6.4.4 結果記録フォーマット

**配置先**: `docs/artifacts/e2e-results/`

```
docs/artifacts/e2e-results/
├── README.md
├── latest.json              # 最新実行結果（上書き）
├── latest-summary.md        # 人間向けサマリー（上書き）
└── history/
    ├── 20260316_143022.json
    └── ...
```

**latest.json スキーマ（実装準拠）**:

```json
{
  "run_id": "20260316_143022",
  "executed_at": "2026-03-16T14:30:22+09:00",
  "test_type": "detection",
  "overall_status": "passed",
  "summary": "Critical 3/3 (100%), Warning 4/5 (80%), Security 3/3 (100%)",
  "details": [],
  "elapsed_seconds": 127.4
}
```

> **Note**: `details` フィールドは汎用的なリスト型。LLM 検出率テスト拡張時に
> `detection_results`（fixture 別の検出率）や `improvement_triggers`（SHOULD 基準未達フラグ）を
> `details` 内に格納する。現時点では空リスト。

Warning 基準未達時はテストを fail させず、`details` 内に改善トリガー情報を記録し `/retro` での確認対象とする（仕様: SHOULD 基準、改善トリガーとして扱う）。

### 6.5 full-review.md 移行設計

#### 6.5.1 self-reference 全件テーブル

full-review.md 内の Phase 参照を全件棚卸しした結果（23 箇所）:

| # | 現行テキスト（抜粋） | 更新後 |
|:--|:---------------------|:------|
| R-01 | `Phase 0 完了後、Phase 0.3 に進む。` | Stage 1 内部: Step 完了後 Step 3 に進む |
| R-02 | `Phase 0.3 完了後、Phase 1 に進む。` | Stage 1 完了後、Stage 2 に進む |
| R-03 | `Phase 1 完了後、Phase 1.5 に進む。` | 削除（同一 Stage 0 内） |
| R-04 | `Phase 5 完了後に自分で Phase 2 に戻る` | Stage 5 → Stage 2 に戻る |
| R-05 | `Phase 1.7 完了後、Phase 2 に進む。` | 削除（同一 Stage 2 内） |
| R-06 | `Phase 2 では従来のファイル全体レビューにフォールバック` | Stage 2 では〜 |
| R-07 | `Phase 2 への接続` | レビューへの接続 |
| R-08 | `（Phase 4: Plan D）` | （Stage 4: Plan D） |
| R-09 | `Phase 0 Step 3: 静的解析結果の Phase 2 への接続` | Stage 1: 静的解析結果の Stage 2 への接続 |
| R-10 | `Phase 2（並列監査）のエージェント` | Stage 2（並列監査）のエージェント |
| R-11 | `Phase 2.5 も含めて全 Layer をゼロベース` | Stage 3 も含めて〜 |
| R-12 | 再スキャンフロー: `Phase 0→1.7→2→2.5→3〜5` | `Stage 1→2→3→4〜5` |
| R-13 | 監査範囲テーブル: `Phase 2`, `Phase 2.5`, `Phase 5` | `Stage 2`, `Stage 3`, `Stage 5` |
| R-14 | `Phase 2 に戻って再監査` | Stage 2 に戻って〜 |
| R-15 | `再レビューループでの Phase 2.5 再実行` | Stage 3 再実行 |
| R-16 | `自分で Phase 2 に戻る` | Stage 2 に戻る |
| R-17 | `Phase 6 に進む` | Stage 5（完了報告）に進む |
| R-18 | `Phase 2 + 2.5`, `Phase 3〜5→Phase 2` | `Stage 2 + 3`, `Stage 4〜5→Stage 2` |
| R-19 | `max_iterations → Phase 6` | Stage 5（完了報告）へ |
| R-20 | 参照セクション（7 行の Phase 参照） | 全件 Stage 参照に更新 |
| R-21 | `Phase 2（並列監査）のエージェントに` | Stage 2（並列監査）のエージェントに |
| R-22 | `Phase 1 以降は静的解析なしで続行可能` | Stage 2 以降は〜 |
| R-23 | `Phase 4: Plan D` | Stage 4: Plan D |

#### 6.5.2 移行ステップ計画

| Step | 作業内容 | 検証ポイント |
|:-----|:---------|:-----------|
| M-1 | full-review.md の見出し再編（Phase → Stage） | Stage 0〜5 の見出しが存在し、中間 Phase がないこと |
| M-2 | R-01〜R-23 の self-reference 全件更新 | grep で `Phase` が残っていないこと（参照セクションの歴史的記述を除く） |
| M-3 | Stage 0 に Scale Detection Step を追加 | Stage 0 Step 3 が scale_detector.py を呼び出す記述があること |
| M-4 | 各 Stage 先頭に実行条件 / 入力 / 出力の契約を追加 | 6 Stage 全てに契約セクションがあること |
| M-5 | 連鎖ドキュメント更新（設計書 Section 1, タスク定義） | Phase 対応表が Stage 対応表に更新されていること |
| M-6 | 参照セクションの更新 | Stage 番号で整合していること |

### 6.6 永続化構造（Plan E 追加分）

```
.claude/
├── hooks/
│   └── analyzers/
│       ├── scale_detector.py          # Plan E 新規: スケール判定
│       └── tests/
│           ├── test_e2e_review.py     # Plan E 新規: E2E テスト
│           └── fixtures/
│               └── e2e/               # Plan E 新規: E2E フィクスチャ
│                   ├── README.md
│                   ├── critical_silent_failure.py
│                   ├── warning_long_function.py
│                   ├── security_hardcoded_password.py
│                   └── combined_issues.py
├── review-state/
│   ├── scale-detection.json           # Plan E 新規: スケール判定結果
│   ├── static-issues.json             # 既存（Plan A）
│   ├── ast-map.json                   # 既存（Plan A）
│   ├── import-map.json                # 既存（Plan A）
│   ├── summary.md                     # 既存（Plan A）
│   ├── chunks.json                    # 既存（Plan B）
│   ├── chunk-results/                 # 既存（Plan B）
│   ├── cards/                         # 既存（Plan C）
│   │   ├── file-cards/
│   │   └── module-cards/
│   ├── dependency-graph.json          # 既存（Plan D）
│   └── contracts/                     # 既存（Plan D）
├── review-config.json                 # 既存
└── commands/
    └── full-review.md                 # 改修: Stage 体系に再編
```

```
docs/artifacts/
└── e2e-results/                       # Plan E 新規
    ├── README.md
    ├── latest.json
    ├── latest-summary.md
    └── history/
```

## 7. ファイル構成

```
.claude/
├── hooks/
│   └── analyzers/              # 静的解析プラグイン
│       ├── __init__.py
│       ├── base.py             # LanguageAnalyzer ABC
│       ├── python_analyzer.py
│       ├── javascript_analyzer.py
│       ├── rust_analyzer.py
│       ├── chunker.py            # Plan B
│       ├── card_generator.py     # Plan C + D
│       ├── orchestrator.py       # Plan B + D
│       ├── reducer.py            # Plan B
│       ├── run_pipeline.py       # Plan A
│       ├── state_manager.py      # Plan A〜D
│       ├── config.py             # Plan A
│       ├── scale_detector.py     # Plan E: スケール判定
│       └── tests/
│           ├── conftest.py
│           ├── test_*.py         # Plan A〜D テスト群
│           ├── test_e2e_review.py  # Plan E: E2E テスト
│           └── fixtures/
│               └── e2e/          # Plan E: E2E フィクスチャ
├── review-state/               # レビュー状態の永続化
│   ├── scale-detection.json      # Plan E
│   ├── static-issues.json        # Plan A
│   ├── ast-map.json              # Plan A
│   ├── import-map.json           # Plan A
│   ├── summary.md                # Plan A
│   ├── chunks.json               # Plan B
│   ├── chunk-results/            # Plan B
│   ├── cards/                    # Plan C
│   │   ├── file-cards/
│   │   └── module-cards/
│   ├── dependency-graph.json     # Plan D
│   └── contracts/                # Plan D
├── review-config.json          # レビュー設定（Section 2.4c 参照）
└── commands/
    └── full-review.md          # Stage 体系（Plan E で再編）
```

## 8. 参照

- 要件仕様: `docs/specs/scalable-code-review-spec.md`
- Phase 5 仕様: `docs/specs/scalable-code-review-phase5-spec.md`
- 調査メモ: `docs/specs/scalable-code-review.md`
- タスク: `docs/tasks/scalable-code-review-tasks.md`
- モジュール間帰責判断: `docs/design/cross-module-blame-design.md`（契約カード帰責ヒント拡張）
