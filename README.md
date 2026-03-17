# The Living Architect Model

**"AI は単なるツールではない。パートナーだ。"**

このリポジトリは、大規模言語モデル（特に Claude）が中〜大規模ソフトウェア開発プロジェクトにおいて、自律的な「アーキテクト」兼「ゲートキーパー」として振る舞うためのプロトコルセット **"Living Architect Model"** を定義します。

これらの定義ファイルをプロジェクトルートに配置することで、標準的なコーディングアシスタントを、プロジェクトの整合性と健全性を守る「能動的な守護者」へと変貌させることができます。

## 初めての方へ

| ステップ | リソース | 所要時間 |
|---------|---------|---------|
| 1. 概念を理解する | [スライド](docs/slides/index.html) | 5分 |
| 2. 環境を構築する | [クイックスタート](QUICKSTART.md) | 10分 |
| 3. 日常の使い方を知る | [チートシート](CHEATSHEET.md) | 参照用 |

## コアコンセプト

- **Active Retrieval (能動的検索)**: AI は受動的な記憶に頼るのではなく、能動的にコンテキストを検索・ロードしなければならない。
- **Gatekeeper Role (門番の役割)**: AI は低品質なコードや曖昧な仕様がコードベースに混入するのを阻止する。
- **Zero-Regression (退行ゼロ)**: 厳格な影響分析と TDD サイクルにより、リグレッション（先祖返り）を防ぐ。
- **Multi-Perspective Decisions (多角的意志決定)**: MAGI System（MELCHIOR・BALTHASAR・CASPAR）+ Reflection を用いた堅牢な構造化意思決定プロセス。
- **Command Safety (コマンド安全性)**: 厳格な Allow/Deny リストによる、偶発的な事故の防止。
- **Living Documentation (生きたドキュメント)**: ドキュメントをコードと同様に扱い、すべてのサイクルで動的に更新する。
- **Phase Control (フェーズ制御)**: PLANNING/BUILDING/AUDITING の明示的な切り替えにより、「つい実装してしまう」問題を防止。
- **Approval Gates (承認ゲート)**: サブフェーズ間の明示的な承認により、不完全な成果物での先走りを防止。

## 収録内容

### 憲法・チートシート

| ファイル | 説明 |
|---------|------|
| `CLAUDE.md` | 憲法。AI のアイデンティティ、基本原則、権限を定義 |
| `CHEATSHEET.md` | クイックリファレンス。コマンド・エージェント一覧 |

### 運用プロトコル (`docs/internal/`)

| ファイル | 説明 |
|---------|------|
| `00_PROJECT_STRUCTURE.md` | 物理構成と命名規則 |
| `01_REQUIREMENT_MANAGEMENT.md` | アイデアから仕様へ (Definition of Ready) |
| `02_DEVELOPMENT_FLOW.md` | 影響分析、TDD、レビューサイクル |
| `03_QUALITY_STANDARDS.md` | コーディング規約と品質ゲート |
| `04_RELEASE_OPS.md` | デプロイと緊急対応プロトコル |
| `05_MCP_INTEGRATION.md` | MCP サーバー連携・MEMORY.md 運用ポリシー（オプション） |
| `06_DECISION_MAKING.md` | 意思決定プロトコル (MAGI System + AoT + Reflection) |
| `07_SECURITY_AND_AUTOMATION.md` | コマンド実行の安全基準 (Allow/Deny List) |
| `99_reference_generic.md` | 一般的な助言とベストプラクティス (Non-SSOT) |

### Claude Code 拡張 (`.claude/`)

| ディレクトリ | 説明 |
|-------------|------|
| `rules/` | 行動規範・ガードレール（自動ロード） |
| `commands/` | スラッシュコマンド（フェーズ制御 + 補助） |
| `agents/` | 専門サブエージェント（要件分析、設計、TDD等） |
| `skills/` | スキル（タスクオーケストレーション、テンプレート出力） |

## 使い方

### Option A: テンプレートとして使用 (推奨)

GitHub 上でリポジトリページ上部の **"Use this template"** ボタンをクリックし、この構成済み構造で新しいリポジトリを作成してください。

**参考ドキュメント:**
- [テンプレートからリポジトリを作成する - GitHub Docs (日本語)](https://docs.github.com/ja/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template)
- [Creating a repository from a template - GitHub Docs (English)](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template)

### Option B: git clone

```bash
git clone https://github.com/sougetuOte/LivingArchitectModel.git my-project
cd my-project
rm -rf .git && git init
```

LAM は `.claude/`、`docs/internal/`、`CLAUDE.md` が連携して動作するため、一式をそのまま使うことを推奨します。

### Option C: 既存プロジェクトへの導入

既に開発が進んでいるプロジェクトに LAM を導入する場合:

1. プロジェクト内に作業用ディレクトリを作り、LAM リポジトリの ZIP をそこに展開する

```bash
mkdir _lam_source
cd _lam_source
# ZIP をダウンロードして展開
```

2. Claude Code を起動し、以下のように指示する:

```
_lam_source/ にある Living Architect Model をこのプロジェクトに配置してください。
```

3. 既存の要件定義や仕様書がある場合は、それを参照させて適応を指示する:

```
<要件定義ファイル> を参照して、LAM の全ファイルを確認し必要な部分を適応させてください。
```

既存の要件がない場合は、適応せずそのまま使い始めてよい。`/planning` で要件定義を行った後に適応すればよい。

## フェーズコマンド

| コマンド | 用途 | 禁止事項 |
|---------|------|---------|
| `/planning` | 要件定義・設計・タスク分解 | コード生成禁止 |
| `/building` | TDD実装 | 仕様なし実装禁止 |
| `/auditing` | レビュー・監査・リファクタ | PM級の修正禁止（PG/SE級は許可） |
| `/project-status` | 進捗状況の表示 | - |

### 承認ゲート

```
requirements → [承認] → design → [承認] → tasks → [承認] → BUILDING → [承認] → AUDITING
```

各サブフェーズ完了時にユーザー承認が必要。未承認のまま次に進むことは禁止。

## コマンドを覚える必要はありません

以下にコマンドやエージェントの一覧が続きますが、暗記する必要はありません。AI に「今の状況で使えるコマンドは？」と聞けば、適切なものを提案してくれます。まずは `/planning` から始めてみてください。

## サブエージェント

| エージェント | 用途 | 推奨フェーズ |
|-------------|------|-------------|
| `requirement-analyst` | 要件分析・ユーザーストーリー | PLANNING |
| `design-architect` | API設計・アーキテクチャ | PLANNING |
| `task-decomposer` | タスク分割・依存関係整理 | PLANNING |
| `tdd-developer` | Red-Green-Refactor 実装 | BUILDING |
| `quality-auditor` | 品質監査・セキュリティ | AUDITING |
| `doc-writer` | ドキュメント作成・仕様策定・更新 | ALL |
| `test-runner` | テスト実行・分析 | BUILDING |
| `code-reviewer` | コードレビュー（LAM品質基準） | AUDITING |

## セッション管理コマンド

| コマンド | 用途 |
|---------|------|
| `/quick-save` | セーブ（SESSION_STATE.md + ループログ + Daily） |
| `/quick-load` | ロード（SESSION_STATE.md + 関連ドキュメント特定） |

## ワークフローコマンド

| コマンド | 用途 |
|---------|------|
| `/ship` | 論理グループ分けコミット（棚卸し -> 分類 -> コミット） |
| `/full-review <対象>` | 並列監査 + 全修正 + 検証（一気通貫） |
| `/release <version>` | リリース（CHANGELOG -> commit -> push -> tag） |
| `/wave-plan [N]` | Wave 計画（次 Wave のタスク選定と実行順序を策定） |
| `/retro [wave\|phase]` | 振り返り（Wave/Phase 完了時の学習サイクル） |

## 補助コマンド

| コマンド | 用途 |
|---------|------|
| `/pattern-review` | TDD パターン審査 |
| `/project-status` | プロジェクト進捗表示 |

## 推奨モデル

| フェーズ | 推奨モデル |
|---------|----------|
| **PLANNING** | Claude Opus / Sonnet |
| **BUILDING** | Claude Sonnet (単純作業なら Haiku) |
| **AUDITING** | Claude Opus (Long Context) |

## 環境要件

| 要件 | 用途 | 必須/任意 |
|------|------|----------|
| [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) | AI アシスタント実行環境 | 必須 |
| Python 3.8+ | フック・StatusLine に必要 | 必須 |
| Git | バージョン管理 | 必須 |
| [gitleaks](https://github.com/gitleaks/gitleaks) | シークレットスキャン（`/full-review` の G5 チェック） | 推奨 |

gitleaks が未インストールの場合、`/full-review` で Green State G5 が FAIL になります。不要な場合は `review-config.json` で `"gitleaks_enabled": false` を設定してください。

## ライセンス

MIT License
