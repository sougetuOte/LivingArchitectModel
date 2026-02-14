# MCP Integration Guide

本ドキュメントは、**Model Context Protocol (MCP)** サーバーを活用して、Living Architect の能力を拡張するためのガイドラインである。
プロジェクト規模やチーム構成に応じて、適切な MCP サーバーを選択・導入する。

> **Note**: MCP サーバーはすべてオプションである。Living Architect Model のコア機能は MCP なしで動作する。
> 個人開発や小〜中規模プロジェクトでは、Claude Code 標準のツール（grep, find, Read 等）で十分な場合が多い。

## 1. MCP Servers (サーバー一覧)

### A. Serena (Coding Agent Toolkit) — Optional

- **Repository**: `oraios/serena`
- **Role**: **"The Hands" (手)**
- **Capability**: 高度なコード検索、シンボルレベルの編集、LSP (Language Server Protocol) ライクな静的解析能力を提供する。
- **推奨規模**: 数万行以上のコードベース、複数人開発
- **注意**: コンテキストコスト（MCP 定義で 5-10K トークン）を消費する。小規模プロジェクトでは grep/find で代替可能。
- **Integration Rule**:
  - CLAUDE.md に「Serena を優先使用する」旨を明記しないと、Claude Code は grep に流れる傾向がある。
  - 導入する場合は、CLAUDE.md のツール使用ルールに明示的に記載すること。

### B. Heimdall (Long-Term Memory) — Optional

- **Repository**: `lcbcFoo/heimdall-mcp-server`
- **Role**: **"The Brain" (脳)**
- **Capability**: ベクトルデータベース (Qdrant) を用いた長期記憶、Git 履歴の文脈理解、プロジェクト固有の知識の永続化。
- **Integration Rule**:
  - **Context Compression の代替**: Heimdall が有効な場合、手動での `docs/memos/` への書き出し（圧縮）は必須ではなくなる。代わりに「Heimdall に記憶させる」アクションを意識する。
  - **Knowledge Retrieval**: 過去の意思決定や、類似の実装パターンを探す際は、Heimdall の検索機能を使用する。


### C. Database Visualization — Optional

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

Claude Code は標準的な MCP クライアントとして動作するため、以下のリソースから用途に合ったサーバーを探して追加することができる。

- **Official MCP Registry**: [modelcontextprotocol.io](https://modelcontextprotocol.io/examples)
  - 公式および検証済みの主要サーバー（Filesystem, Git, Postgres, Slack 等）が掲載されている。
- **Awesome MCP Servers**: [github.com/punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers)
  - コミュニティベースの包括的なリスト。カテゴリ別に整理されており、新しいツールを探すのに最適。

## 5. Configuration Examples (設定例)

以下は `.mcp.json` (または Claude Code の設定ファイル) への記述例である。
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

## 6. MEMORY.md Policy (auto memory 運用ポリシー)

Claude Code の auto memory 機能（`MEMORY.md`）の運用方針を定義する。

### 禁止事項
- メインセッションで MEMORY.md にプロジェクト固有情報（仕様、設計判断、タスク状態）を記録しないこと
- SESSION_STATE.md の代替として使用しないこと
- `docs/internal/`, `docs/specs/`, `docs/adr/` に記録すべき情報を MEMORY.md に書かないこと

### 許可事項
- Subagent が役割ノウハウ（レビューパターン、TDD報告フォーマット等）を蓄積する用途で使用可
- プロジェクト横断で有用な一般的知見の記録

### 記憶メカニズムの棲み分け

| メカニズム | 用途 | 時間軸 | 管理 |
|-----------|------|--------|------|
| `docs/internal/`, `docs/specs/`, `docs/adr/` | プロジェクトの真実（SSOT） | 永続 | git 管理 |
| `SESSION_STATE.md` | セッション状態のハンドオフ | 使い捨て | 手動（/quick-save） |
| `MEMORY.md` (auto memory) | Subagent の役割ノウハウ蓄積 | 永続（累積） | 自動 |
| Heimdall | ベクトル検索による過去の意思決定検索 | 永続 | MCP サーバー |
