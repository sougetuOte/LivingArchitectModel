# Scalable Code Review 設計書

**バージョン**: 1.1
**作成日**: 2026-03-14
**ステータス**: draft
**対応仕様**: `docs/specs/scalable-code-review-spec.md`

---

## 1. アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────┐
│                    /full-review (拡張版)                      │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │ Phase 0  │→│ Phase 1  │→│ Phase 2  │→│ Phase 3-5  │  │
│  │ 静的解析 │  │ チャンク │  │ 並列     │  │ 統合・修正 │  │
│  │ (Python) │  │ 分割     │  │ LLMレビュー│  │ ・検証     │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘  │
│       ↓              ↓              ↓              ↓         │
│  .claude/review-state/ (外部永続化)                          │
└─────────────────────────────────────────────────────────────┘
```

### 既存 full-review との Phase 対応

既存 full-review の Phase 番号を +1 してリナンバリングし、新 Phase 0 に静的解析を挿入する。

| 新 Phase | 旧 Phase | 内容 |
|----------|----------|------|
| Phase 0 | （新規） | 静的解析パイプライン（Plan A） |
| Phase 0.5 | Phase 0.5 | context7 MCP 検出（変更なし） |
| Phase 1 | Phase 0 | ループ初期化 |
| Phase 2 | Phase 1 | 並列監査（チャンク分割適用時は Map-Reduce） |
| Phase 3 | Phase 2 | レポート統合 |
| Phase 4 | Phase 3 | 修正 |
| Phase 5 | Phase 4 | 検証（Green State 判定） |
| Phase 6 | Phase 5 | 完了報告 |

### Plan 別の有効化

| 規模 | 有効な Plan | Phase | 有効化 |
|------|-----------|-------|--------|
| ~10K | 現行 full-review（変更なし） | — | — |
| 10K-30K | Plan A（提案） | Phase 0 | ユーザーが選択 |
| 30K-100K | Plan A + B | Phase 0-2 | 自動有効化 |
| 100K-300K | Plan A + B + C | Phase 0 全て | 自動有効化 |
| 300K+ | Plan A + B + C + D + E | 全 Phase | 自動有効化 |

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

## 6. Plan E: ハイブリッドパイプライン設計（将来）

Plan A〜D の統合。詳細は Plan D 実装後に設計する。

```
Stage 1: 静的事前分析（Plan A）→ static-issues.json
Stage 2: AST チャンク分割 + 依存グラフ活用（Plan B + D）
Stage 3: 並列 Map レビュー + 階層的 Reduce（Plan B + C）
Stage 4: 修正 + 全体再レビュー（FR-5）
Stage 5: Green State 判定
```

## 7. ファイル構成

```
.claude/
├── hooks/
│   └── analyzers/              # 静的解析プラグイン（新規）
│       ├── __init__.py
│       ├── base.py             # LanguageAnalyzer ABC
│       ├── python_analyzer.py
│       ├── javascript_analyzer.py
│       ├── rust_analyzer.py
│       ├── chunker.py            # Plan B
│       ├── card_generator.py     # Plan C
│       └── tests/               # analyzers 専用テスト（conftest.py で hooks/tests と fixture 共有）
├── review-state/               # レビュー状態の永続化（新規）
│   ├── static-issues.json
│   ├── ast-map.json
│   ├── summary.md
│   ├── chunk-results/
│   ├── cards/                    # Plan C で追加
│   │   ├── file-cards/           # 概要カード（Layer 1）
│   │   └── module-cards/         # 要約カード（Layer 2）
│   ├── dependency-graph.json   # Plan D で追加
│   └── contracts/              # Plan D で追加
├── review-config.json          # レビュー設定（Section 2.4c 参照）
└── commands/
    └── full-review.md          # 拡張（Phase 0 追加、Phase リナンバリング）
```

## 8. 参照

- 要件仕様: `docs/specs/scalable-code-review-spec.md`
- 調査メモ: `docs/specs/scalable-code-review.md`
- タスク: `docs/tasks/scalable-code-review-tasks.md`
