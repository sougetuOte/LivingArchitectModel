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
- 直接の呼び出し先のシグネチャ
```

### 3.3 Map-Reduce フロー

```
Map（デフォルト並列数: 4、最大: 10、review-config.json で調整可能）:
  動的ディスパッチ: Agent 完了次第、次のチャンクを投入
  チャンク1 → Agent1 → Issues1
  チャンク2 → Agent2 → Issues2
  ...
  チャンクN → AgentN → IssuesN

  エラーハンドリング:
  - Agent タイムアウト/エラー時: 最大 2回リトライ（agent_retry_count で調整）
  - リトライ後も失敗: Warning として報告し続行（未レビューチャンクとして記録）

Reduce（横断チェック）:
  Issues1..N → 重複排除
            → API 呼び出しと定義の一致チェック
            → 型の整合性チェック
            → 命名規則の統一性チェック
            → 統合レポート
```

## 4. Plan C: 階層的レビュー設計

### 4.1 レイヤー構成

```
Layer 1 (ファイル): 各ファイルを個別レビュー → 概要カード生成
    ↓ 概要カード群
Layer 2 (モジュール): パッケージ定義単位（__init__.py / package.json）で API 整合性チェック → 要約カード生成
    ↓ 要約カード群
Layer 3 (システム): 全モジュールの要約 + 仕様書で アーキテクチャチェック
    ↓ 統合レポート
全体再レビュー: 修正後は Layer 1 からゼロベースで再実行（FR-5）
```

### 4.2 概要カード仕様

各ファイルから生成する概要カード（100-200 トークン）:

```markdown
## [ファイルパス]
- **責務**: [1行で説明]
- **公開 API**: [関数/クラス名のリスト]
- **依存先**: [import しているモジュール]
- **依存元**: [grep ベースの逆引き検索で取得。Plan D で依存グラフに置換]
- **Issue 数**: Critical: X / Warning: Y / Info: Z
```

### 4.3 再レビュー原則（FR-5）

修正後の再レビューは Layer 1 からの全体ゼロベース再実行とする。
部分再レビューは潜在的不具合の放置になるため禁止。

将来的に Plan D（依存グラフ駆動）が実装された後、影響範囲分析に基づく
スコープ最適化を検討する。ただしその場合でも「一度見て問題なしが確定した」
チャンクのみスキップ可能とし、未検証チャンクのスキップは禁止。

## 5. Plan D: 依存グラフ駆動設計（将来）

### 5.1 グラフ構築

```python
# pydeps / pyan で依存グラフを構築
# NetworkX の DiGraph で表現
# トポロジカルソートで処理順序を決定
# 強連結成分（循環依存）を検出・マーク
```

### 5.2 契約カード

各モジュールのレビュー後に「契約カード」を生成:

```markdown
## [モジュール名]
- **公開 API**: [シグネチャリスト]
- **前提条件**: [入力の制約]
- **保証**: [出力の保証]
- **副作用**: [状態変更]
- **不変条件**: [維持すべき条件]
```

上流モジュールのレビュー時に、下流の契約カードを参照して違反を検出する。

### 5.3 影響範囲分析

修正対象ノードから依存グラフを上流方向に辿り、影響を受けるモジュールを特定する。
FR-5（全体再レビュー原則）に従いつつ、影響範囲外のモジュールについては
前回の概要カードを再利用することで効率化する。

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
