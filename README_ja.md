# The Living Architect Model

**"AI は単なるツールではない。パートナーだ。"**

このリポジトリは、大規模言語モデル（特に Gemini 3 Pro/Ultra）が中〜大規模ソフトウェア開発プロジェクトにおいて、自律的な「アーキテクト」兼「ゲートキーパー」として振る舞うためのプロトコルセット **"Living Architect Model"** を定義します。

これらの定義ファイルをプロジェクトルートに配置することで、標準的なコーディングアシスタントを、プロジェクトの整合性と健全性を守る「能動的な守護者」へと変貌させることができます。

## 🌟 コアコンセプト

- **Active Retrieval (能動的検索)**: AI は受動的な記憶に頼るのではなく、能動的にコンテキストを検索・ロードしなければならない。
- **Gatekeeper Role (門番の役割)**: AI は低品質なコードや曖昧な仕様がコードベースに混入するのを阻止する。
- **Zero-Regression (退行ゼロ)**: 厳格な影響分析と TDD サイクルにより、リグレッション（先祖返り）を防ぐ。
- **Living Documentation (生きたドキュメント)**: ドキュメントをコードと同様に扱い、すべてのサイクルで動的に更新する。

## 📦 収録内容

- **`GEMINI.md`**: 憲法。AI のアイデンティティ、基本原則、権限を定義。
- **`docs/internal/`**: 運用プロトコル。
  - `00_PROJECT_STRUCTURE.md`: 物理構成と命名規則。
  - `01_REQUIREMENT_MANAGEMENT.md`: アイデアから仕様へ (Definition of Ready)。
  - `02_DEVELOPMENT_FLOW.md`: 影響分析、TDD、レビューサイクル。
  - `03_QUALITY_STANDARDS.md`: コーディング規約と品質ゲート。
  - `04_RELEASE_OPS.md`: デプロイと緊急対応プロトコル。
  - `05_MCP_INTEGRATION.md`: MCP サーバー連携ガイド (Serena, Heimdall)。

## 🚀 使い方

### Option A: テンプレートとして使用 (推奨)

リポジトリ上部の **"Use this template"** ボタンをクリックし、この構成済み構造で新しいリポジトリを作成してください。

### Option B: 手動インストール

1. `GEMINI.md` をプロジェクトルートにコピーする。
2. `docs/internal/` ディレクトリをプロジェクトの `docs/` フォルダにコピーする。
3. AI アシスタントに指示する: _"GEMINI.md を読み込み、Living Architect として初期化してください。"_

## 🤖 推奨モデル

| Role                              | Model                                                   |
| :-------------------------------- | :------------------------------------------------------ |
| **Architect (Planning/Auditing)** | **Gemini 3 Pro / Ultra**                                |
| **Builder (Coding)**              | **Gemini 3 Pro** (単純作業なら **Gemini 3 Flash** も可) |

## 📄 ライセンス

MIT License
