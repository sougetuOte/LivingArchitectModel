# MCP Integration Guide

本ドキュメントは、**Model Context Protocol (MCP)** サーバーを活用して、Living Architect の能力を拡張するためのガイドラインである。
特に、ローカル環境で **Serena** や **Heimdall** が稼働している場合の連携方法と注意点を記述する。

## 1. Recommended MCP Servers (推奨サーバー)

### A. Serena (Coding Agent Toolkit)

- **Repository**: `oraios/serena`
- **Role**: **"The Hands" (手)**
- **Capability**: 高度なコード検索、シンボルレベルの編集、LSP (Language Server Protocol) ライクな静的解析能力を提供する。
- **Integration Rule**:
  - コードの調査・修正を行う際は、標準の `grep` や `replace` よりも **Serena のツールを優先的に使用する** こと。
  - 特に大規模なリファクタリングや、依存関係が複雑な変更において、その真価を発揮する。

### B. Heimdall (Long-Term Memory)

- **Repository**: `lcbcFoo/heimdall-mcp-server`
- **Role**: **"The Brain" (脳)**
- **Capability**: ベクトルデータベース (Qdrant) を用いた長期記憶、Git 履歴の文脈理解、プロジェクト固有の知識の永続化。
- **Integration Rule**:
  - **Context Compression の代替**: Heimdall が有効な場合、手動での `docs/memos/` への書き出し（圧縮）は必須ではなくなる。代わりに「Heimdall に記憶させる」アクションを意識する。
  - **Knowledge Retrieval**: 過去の意思決定や、類似の実装パターンを探す際は、Heimdall の検索機能を使用する。

### C. Database Visualization (Optional)

- **Tools**: `SingleStore MCP`, `ChartDB` (Self-hosted)
- **Role**: **"The Eyes" (目)**
- **Capability**: データベーススキーマの可視化、ER 図の自動生成。
- **Integration Rule**: データモデリング (Phase 0) において、ER 図を自動生成し `docs/specs/` に添付するために使用する。

## 2. Operational Precautions (運用上の注意点)

### A. Tool Conflict (ツールの競合)

- 標準のファイル操作ツールと MCP ツール（例: Serena の編集ツール）が重複する場合がある。
- **原則**: 「より高機能で、文脈を理解している方」を選ぶ。通常は MCP ツールの方が高機能である。

### B. Latency & Cost (レイテンシとコスト)

- MCP 経由の操作は、ローカルコマンド実行よりもオーバーヘッドが発生する場合がある。
- 単純な `ls` や `cat` レベルの操作なら、標準ツールの方が高速な場合がある。使い分けを意識せよ。

### C. Security (セキュリティ)

- MCP サーバーはローカルのファイルシステムや DB にアクセス権限を持つ。
- 信頼できないサードパーティ製 MCP サーバーを無闇に追加しないこと。

## 3. Workflow Integration (ワークフローへの組み込み)

### Phase 0 (Requirement)

- **Heimdall**: 過去の類似機能の仕様や、既存のドキュメントを検索し、仕様書のドラフト精度を高める。

### Phase 1 (Planning)

- **Serena**: 依存関係の調査 (Dependency Traversal) を Serena の解析機能で行い、より正確な影響範囲を特定する。
- **DB Visualization**: 現在のスキーマ構造を可視化し、変更案の妥当性を検証する。

### Phase 2 (Building)

- **Serena**: シンボル単位の置換や、LSP 機能を活用した「壊れない修正」を行う。

### Phase 3 (Auditing)

- **Heimdall**: 「過去にどのような経緯でこのコードになったか」を Git 履歴から参照し、リファクタリングの判断材料にする。

## 4. Finding More MCP Servers (MCP サーバーの探し方)

Antigravity は標準的な MCP クライアントとして動作するため、以下のリソースから用途に合ったサーバーを探して追加することができる。

- **Official MCP Registry**: [modelcontextprotocol.io](https://modelcontextprotocol.io/examples)
  - 公式および検証済みの主要サーバー（Filesystem, Git, Postgres, Slack 等）が掲載されている。
- **Awesome MCP Servers**: [github.com/punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers)
  - コミュニティベースの包括的なリスト。カテゴリ別に整理されており、新しいツールを探すのに最適。

## 5. Configuration Examples (設定例)

以下は `claude.json` (または Antigravity の設定ファイル) への記述例である。
**注意**: `serena` や `heimdall` はプロジェクトごとにパスを指定する必要があるため、新しいプロジェクトを始めるたびに設定を追加（または更新）する必要がある。

```json
{
  "mcpServers": {
    "serena": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/oraios/serena",
        "serena",
        "start-mcp-server",
        "--context",
        "ide-assistant",
        "--project",
        "/absolute/path/to/your/project"
      ]
    },
    "heimdall": {
      "type": "stdio",
      "command": "heimdall-mcp",
      "args": [],
      "env": {
        "PROJECT_PATH": "/absolute/path/to/your/project"
      }
    }
  }
}
```

※ `/absolute/path/to/your/project` は実際のプロジェクトルートに書き換えること。
