# Project Structure & Naming Conventions

本ドキュメントは、プロジェクトの物理的な構成（ディレクトリ構造）と、資産の配置ルールを定義する。
"Living Architect" は、この地図に従って情報を格納・検索しなければならない。

## 1. Directory Structure (ディレクトリ構成)

```
/
├── src/                    # ソースコード (実装)
│   ├── backend/            # バックエンド (Python/FastAPI)
│   └── frontend/           # フロントエンド (React/Vite)
├── tests/                  # テストコード
├── docs/                   # ドキュメント資産
│   ├── specs/              # 要求仕様書 (Source of Truth)
│   ├── adr/                # アーキテクチャ決定記録 (Why)
│   ├── tasks/              # タスク管理 (Kanban/List)
│   ├── internal/           # プロジェクト運用ルール (本フォルダ)
│   ├── artifacts/          # 中間成果物・監査レポート・知見
│   │   ├── knowledge/      # /retro Step4 で整理した知見
│   │   ├── audit-reports/  # 監査レポート
│   │   └── tdd-patterns/   # TDD パターン詳細記録（v2 のログは .claude/tdd-patterns.log）
│   ├── slides/             # 概念説明スライド
│   ├── daily/              # /quick-save Daily 記録
│   └── memos/              # [Input] ユーザーからの生メモ・資料
├── .claude/                # Claude Code用設定・コマンド・状態管理
│   ├── commands/           # ワークフローコマンド（/ship, /full-review, /wave-plan 等）
│   ├── rules/              # ガードレール（自動ロード）
│   ├── hooks/              # PreToolUse/PostToolUse/Stop/PreCompact hooks
│   ├── skills/             # スキル定義（テンプレート、思考フレームワーク等）
│   ├── agents/             # カスタムサブエージェント定義
│   ├── agent-memory/       # サブエージェントの永続メモリ
│   ├── states/             # フェーズ承認ゲート状態（*.json）
│   ├── logs/               # 権限ログ、ループログ等
│   └── settings.json       # 権限・hooks 設定
└── CLAUDE.md               # プロジェクト憲法
```

## 2. Asset Placement Rules (資産配置ルール)

### A. User Inputs & Intermediate Artifacts (ユーザー入力と中間成果物)

- **Raw Ideas**: ユーザーからの未加工のアイデアやチャットログは `docs/memos/YYYY-MM-DD_topic.md` に保存する。
- **Intermediate Reports**: lam-orchestrate の Wave 間で受け渡す調査結果等の中間成果物は `docs/artifacts/YYYY-MM-DD_intermediate_[topic].md` に保存する（Coordinator のコンテキスト圧迫を防ぐため）。
- **Knowledge**: `/retro` Step 4 で整理した知見は `docs/artifacts/knowledge/` に蓄積する。
- **Audit Reports**: `/full-review` の監査レポートは `docs/artifacts/audit-reports/` に保存する。
- **TDD Patterns**: テスト失敗/成功パターンの詳細記録は `docs/artifacts/tdd-patterns/` に保存する。
- **Reference Materials**: 参考資料（画像、PDF）は `docs/memos/assets/` に配置する。

### B. Specifications (仕様書)

- **Naming**: `docs/specs/{feature_name}.md` (ケバブケース)
- **Granularity**: 1 機能 = 1 ファイル。巨大になる場合はディレクトリを切る。

### C. ADR (Architectural Decision Records)

- **Naming**: `docs/adr/NNNN-kebab-case-title.md`（NNNN: 4桁連番、0001から）
- **Immutable**: 一度確定した ADR は原則変更せず、変更が必要な場合は新しい ADR を作成して "Supersedes" と明記する。

### D. Subagent Persistent Memory

- **Path**: `.claude/agent-memory/<agent-name>/`
- **用途**: サブエージェントがレビュー時に学んだプロジェクト固有知見を蓄積する領域。CLAUDE.md の指示に従いサブエージェントが自発的に書き込む。

### E. State Management (状態管理)

- **SESSION_STATE.md** (プロジェクトルート): 現在のセッション状態。`/quick-save` で記録、`/quick-load` で復元。セッション間ハンドオフ用の使い捨てファイル。
- **.claude/states/*.json**: フェーズごとの承認ゲート管理、タスク進捗の永続的な状態記録。機能開発の進行管理に使用。
- **.claude/current-phase.md**: 現在の開発フェーズ（PLANNING/BUILDING/AUDITING）。`/planning`, `/building`, `/auditing` コマンドで更新される。

## 3. SSOT 3層アーキテクチャ

> **用語注意**: 本セクションの「情報層」は SSOT の情報階層を指す。
> `07_SECURITY_AND_AUTOMATION.md` Section 5 の「Permission Layer 0/1/2」（権限制御の多層モデル）とは別の概念である。

```
情報層 1: docs/internal/ — プロセス SSOT（What & Why）
  |
  v 参照・実装
情報層 2: .claude/rules/    — ガードレール（自動ロード）
          .claude/commands/ — ワークフロー（手動実行）
          .claude/hooks/    — 自動化 hooks（PreToolUse/PostToolUse/Stop/PreCompact）
          .claude/agents/   — エージェント定義
          .claude/skills/   — スキル定義
  |
  v 要約
情報層 3: CHEATSHEET.md — クイックリファレンス
```

- 情報層 1 が最高権限。情報層 2 は情報層 1 の「実装」
- 情報層 2 に新機能を追加したら、情報層 1 への反映を確認する
- 情報層 3 は情報層 1-2 の要約であり、独自情報を持たない

## 4. File Naming Conventions (命名規則)

- **Directories**: `snake_case` (例: `user_auth`)
- **Files (Code)**: 言語標準に従う (Python: `snake_case.py`, JS/TS: `PascalCase.tsx` or `camelCase.ts`)
- **Files (Docs)**: `snake_case.md` または `kebab-case.md` (プロジェクト内で統一)
