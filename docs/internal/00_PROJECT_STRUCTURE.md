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
│   └── memos/              # [Input] ユーザーからの生メモ・資料
├── .claude/                # Claude Code用設定・コマンド・状態管理
└── CLAUDE.md               # プロジェクト憲法
```

## 2. Asset Placement Rules (資産配置ルール)

### A. User Inputs & Intermediate Artifacts (ユーザー入力と中間成果物)

- **Raw Ideas**: ユーザーからの未加工のアイデアやチャットログは `docs/memos/YYYY-MM-DD_topic.md` に保存する。
- **Intermediate Reports**: lam-orchestrate の Wave 間で受け渡す調査結果等の中間成果物は `docs/memos/YYYY-MM-DD_intermediate_[topic].md` に保存する（Coordinator のコンテキスト圧迫を防ぐため）。
- **Reference Materials**: 参考資料（画像、PDF）は `docs/memos/assets/` に配置する。

### B. Specifications (仕様書)

- **Naming**: `docs/specs/{feature_name}.md` (ケバブケース)
- **Granularity**: 1 機能 = 1 ファイル。巨大になる場合はディレクトリを切る。

### C. ADR (Architectural Decision Records)

- **Naming**: `docs/adr/YYYY-MM-DD_{decision_title}.md`
- **Immutable**: 一度確定した ADR は原則変更せず、変更が必要な場合は新しい ADR を作成して "Supersedes" と明記する。

### D. State Management (状態管理)

- **SESSION_STATE.md** (プロジェクトルート): 現在のセッション状態。`/quick-save` で記録、`/full-load` で復元。セッション間ハンドオフ用の使い捨てファイル。
- **.claude/states/*.json**: フェーズごとの承認ゲート管理、タスク進捗の永続的な状態記録。機能開発の進行管理に使用。
- **.claude/current-phase.md**: 現在の開発フェーズ（PLANNING/BUILDING/AUDITING）。`/planning`, `/building`, `/auditing` コマンドで更新される。

## 3. File Naming Conventions (命名規則)

- **Directories**: `snake_case` (例: `user_auth`)
- **Files (Code)**: 言語標準に従う (Python: `snake_case.py`, JS/TS: `PascalCase.tsx` or `camelCase.ts`)
- **Files (Docs)**: `snake_case.md` または `kebab-case.md` (プロジェクト内で統一)
