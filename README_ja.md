# The Living Architect Model

**"AI は単なるツールではない。パートナーだ。"**

このリポジトリは、大規模言語モデル（特に Claude）が中〜大規模ソフトウェア開発プロジェクトにおいて、自律的な「アーキテクト」兼「ゲートキーパー」として振る舞うためのプロトコルセット **"Living Architect Model"** を定義します。

これらの定義ファイルをプロジェクトルートに配置することで、標準的なコーディングアシスタントを、プロジェクトの整合性と健全性を守る「能動的な守護者」へと変貌させることができます。

## コアコンセプト

- **Active Retrieval (能動的検索)**: AI は受動的な記憶に頼るのではなく、能動的にコンテキストを検索・ロードしなければならない。
- **Gatekeeper Role (門番の役割)**: AI は低品質なコードや曖昧な仕様がコードベースに混入するのを阻止する。
- **Zero-Regression (退行ゼロ)**: 厳格な影響分析と TDD サイクルにより、リグレッション（先祖返り）を防ぐ。
- **Multi-Perspective Decisions (多角的意志決定)**: "Three Agents" モデル（肯定・批判・調停）を用いた堅牢な意思決定プロセス。
- **Command Safety (コマンド安全性)**: 厳格な Allow/Deny リストによる、偶発的な事故の防止。
- **Living Documentation (生きたドキュメント)**: ドキュメントをコードと同様に扱い、すべてのサイクルで動的に更新する。

## 収録内容

- **`CLAUDE.md`**: 憲法。AI のアイデンティティ、基本原則、権限を定義。
- **`docs/internal/`**: 運用プロトコル。
  - `00_PROJECT_STRUCTURE.md`: 物理構成と命名規則。
  - `01_REQUIREMENT_MANAGEMENT.md`: アイデアから仕様へ (Definition of Ready)。
  - `02_DEVELOPMENT_FLOW.md`: 影響分析、TDD、レビューサイクル。
  - `03_QUALITY_STANDARDS.md`: コーディング規約と品質ゲート。
  - `04_RELEASE_OPS.md`: デプロイと緊急対応プロトコル。
  - `05_MCP_INTEGRATION.md`: MCP サーバー連携ガイド (Serena, Heimdall)。
  - `06_DECISION_MAKING.md`: 意思決定プロトコル (3 Agents Model)。
  - `07_SECURITY_AND_AUTOMATION.md`: コマンド実行の安全基準 (Allow/Deny List)。
  - `99_reference_generic.md`: 一般的な助言とベストプラクティス (Non-SSOT)。

## 使い方

### Option A: テンプレートとして使用 (推奨)

リポジトリ上部の **"Use this template"** ボタンをクリックし、この構成済み構造で新しいリポジトリを作成してください。

### Option B: 手動インストール

1. `CLAUDE.md` をプロジェクトルートにコピーする。
2. `docs/internal/` ディレクトリをプロジェクトの `docs/` フォルダにコピーする。
3. AI アシスタントに指示する: _"CLAUDE.md を読み込み、Living Architect として初期化してください。"_

## 推奨モデル

| Role                              | Model                                                     |
| :-------------------------------- | :-------------------------------------------------------- |
| **Architect (Planning/Auditing)** | **Claude Opus / Sonnet**                                  |
| **Builder (Coding)**              | **Claude Sonnet** (単純作業なら **Claude Haiku** も可)    |

## スラッシュコマンド (オプション)

Claude Code 用のオプションコマンドを提供しています:

| コマンド | 用途 |
|:--------|:--------|
| `/focus` | 現在のタスクに集中 - 必要最小限の情報に絞る |
| `/daily` | 日次振り返り - 3分間のステータス更新 |
| `/adr-create` | 新しい Architecture Decision Record を作成 |
| `/security-review` | セキュリティレビュー - 変更内容の安全性を検証 |
| `/impact-analysis` | 影響分析 - 変更の波及範囲を事前に特定 |

詳細は `.claude/commands/` を参照してください。

## ライセンス

MIT License
