# LAM Orchestrate 設計書

**バージョン**: 2.0.0
**作成日**: 2026-01-29
**改訂日**: 2026-02-15
**ステータス**: Active (Revision - Public API Aligned)
**前バージョン**: 1.0.0 (On Hold)
**参照 Claude Code バージョン**: 2.1.42
**関連文書**: `_reference/2026-01-29.md`

> **改訂履歴**:
> - v1.0.0 (2026-01-29): 初版。Anthropic Swarm 機能リリース待ちで On Hold。
> - v2.0.0 (2026-02-15): Claude Code 公式 Subagent/Skills API に準拠して全面改訂。Agent Teams は将来拡張パスとして記載。

---

## 1. 概要

### 1.1 目的

Claude Code の Subagent 制約（Subagent が他の Subagent を起動できない）を回避し、
**擬似的な3層構造**による自律的なタスク実行を実現する。

### 1.2 背景

```
┌─────────────────────────────────────────────────────────────────┐
│ 課題: Subagent の階層制限                                       │
│                                                                 │
│   Main ──┬── Subagent A                                        │
│          ├── Subagent B     ← ここまでは可能                   │
│          └── Subagent C                                        │
│                   │                                             │
│                   └── Sub-Subagent ← これは不可能              │
│                                                                 │
│ 解決策: Skill + Main + Subagent の役割分離で擬似3層を実現      │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 スコープ

| 含む | 含まない |
|------|----------|
| Skill による戦略定義 | 外部オーケストレーター（claude-flow 等） |
| 並列 Subagent 実行 | taskqueue-mcp 統合（将来拡張） |
| Agent 定義テンプレート | Swarm 機能（Anthropic 実装待ち） |
| | Tier 定義の変更（SSOT で管理） |

---

## 2. アーキテクチャ

### 2.1 全体構成図

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        LAM Orchestrate Architecture                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Layer 1: Coordinator (Strategy)                                  │   │
│  │ ┌─────────────────────────────────────────────────────────────┐ │   │
│  │ │  /lam-orchestrate Skill                                     │ │   │
│  │ │  ・タスク分解ルール                                         │ │   │
│  │ │  ・並列化判断基準                                           │ │   │
│  │ │  ・Agent 選択ロジック                                       │ │   │
│  │ └─────────────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────┬──────────────────────────────────┘   │
│                                 │                                       │
│                                 ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Layer 2: Dispatcher (Coordination)                               │   │
│  │ ┌─────────────────────────────────────────────────────────────┐ │   │
│  │ │  Main Claude Process                                        │ │   │
│  │ │  ・Skill の指示を実行                                       │ │   │
│  │ │  ・Task tool で Subagent を起動                             │ │   │
│  │ │  ・結果の集約と報告                                         │ │   │
│  │ └─────────────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────┬──────────────────────────────────┘   │
│                                 │                                       │
│              ┌──────────────────┼──────────────────┐                   │
│              ▼                  ▼                  ▼                   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Layer 3: Workers (Execution)                                     │   │
│  │ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐           │   │
│  │ │  Subagent A   │ │  Subagent B   │ │  Subagent C   │           │   │
│  │ │  (並列実行)   │ │  (並列実行)   │ │  (並列実行)   │           │   │
│  │ └───────────────┘ └───────────────┘ └───────────────┘           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 シーケンス図

```mermaid
sequenceDiagram
    participant U as User
    participant S as Skill<br>(Coordinator)
    participant M as Main<br>(Dispatcher)
    participant A as Subagent A<br>(Worker)
    participant B as Subagent B<br>(Worker)
    participant C as Subagent C<br>(Worker)

    U->>S: /lam-orchestrate タスク説明
    activate S

    Note over S: タスク分析<br>・独立性判定<br>・Agent 選択

    S->>M: 分解されたタスクリスト
    deactivate S
    activate M

    Note over M: 並列実行準備<br>1メッセージで複数 Task

    par 並列実行
        M->>A: Task({ subagent_type: "agent-a", ... })
        activate A
        A-->>M: 結果 A
        deactivate A
    and
        M->>B: Task({ subagent_type: "agent-b", ... })
        activate B
        B-->>M: 結果 B
        deactivate B
    and
        M->>C: Task({ subagent_type: "agent-c", ... })
        activate C
        C-->>M: 結果 C
        deactivate C
    end

    Note over M: 結果統合

    M->>U: 統合レポート
    deactivate M
```

### 2.3 状態遷移図

```mermaid
stateDiagram-v2
    [*] --> Idle: 初期状態

    Idle --> Analyzing: /lam-orchestrate 実行

    Analyzing --> Planning: タスク分解完了
    Analyzing --> Idle: 分解不可（単一タスク）

    Planning --> Executing: 並列実行開始
    Planning --> Idle: キャンセル

    Executing --> Aggregating: 全 Worker 完了
    Executing --> Error: Worker 失敗

    Aggregating --> Reporting: 結果統合完了

    Reporting --> Idle: レポート出力

    Error --> Idle: エラーレポート
    Error --> Executing: リトライ（手動）
```

---

## 3. コンポーネント詳細

### 3.1 Skill: `/lam-orchestrate`

#### 3.1.1 ファイル配置

```
.claude/
└── skills/
    └── lam-orchestrate/
        ├── SKILL.md           # メイン指示（必須）
        └── examples/
            └── execution-plan-sample.md  # 出力例
```

> **Note**: Claude Code 2.x 以降、Skills は `SKILL.md` をエントリポイントとするディレクトリ構造。
> `.claude/commands/` との互換性は維持されるが、Skills 形式を推奨。

#### 3.1.2 Skill 定義（公式 SKILL.md 形式準拠）

```yaml
# .claude/skills/lam-orchestrate/SKILL.md
---
name: lam-orchestrate
description: >
  LAM Coordinator - タスクを分解し、適切な Subagent で並列実行する。
  複数ファイル/モジュールにまたがる作業の自動分解・並列実行に使用。
  Use proactively when the user requests multi-file operations.
disable-model-invocation: true
allowed-tools: Task, Read, Glob, Grep
---

# LAM Orchestrate Coordinator

あなたは LAM プロジェクトの **Coordinator**（調整者）です。
ユーザーから与えられたタスクを分析し、最適な実行計画を立案・実行します。

## 実行フロー

### Phase 1: 分析
1. タスクの全体像を把握
2. 独立して実行可能な単位に分解
3. 各単位に最適な Subagent を割り当て

### Phase 2: 実行
1. 並列実行可能なタスクを特定
2. **1メッセージで複数の Task を呼び出し**（並列実行）
3. 依存関係があるタスクは Wave を分けて逐次実行

### Phase 3: 統合
1. 各 Worker の結果を収集
2. 整合性を確認
3. 統合レポートを作成

## 並列実行ルール

```
最大並列数: 5（デフォルト）
引数 --parallel=N で上書き可能

並列化の条件:
  ✓ 異なるファイル/ディレクトリを対象
  ✓ 相互に依存しないタスク
  ✗ 同一ファイルへの書き込み → 直列化
  ✗ 出力が次の入力になる → Wave 分離
```

## Subagent 選択ルール

| ファイルパターン | 推奨 Subagent |
|------------------|---------------|
| `*.rs`, `Cargo.toml` | rust-specialist |
| `*.ts`, `*.tsx`, `*.vue` | frontend-dev |
| `*test*`, `*spec*` | test-runner |
| `*.md`, `docs/` | doc-writer |
| その他 | general-purpose（ビルトイン） |

> **Note**: `general-purpose` は Claude Code ビルトイン Subagent。
> カスタム Subagent が未定義のパターンではビルトインにフォールバックする。

## 禁止事項

- Subagent からの Subagent 起動（技術的に不可 — Claude Code の制約）
- 未分析でのタスク実行

## 出力フォーマット

タスク分解後、以下を表示してから実行:

```
## 実行計画

| # | タスク | Subagent | 並列 |
|---|--------|----------|:----:|
| 1 | ... | rust-specialist | Wave 1 |
| 2 | ... | frontend-dev | Wave 1 |
| 3 | ... | test-runner | Wave 2 |

続行しますか？ [Y/n]
```
```

#### 3.1.3 引数仕様

| 引数 | 説明 | デフォルト |
|------|------|-----------|
| `--parallel=N` | 最大並列数 | 5 |
| `--dry-run` | 実行計画のみ表示 | false |
| `--no-confirm` | 確認スキップ | false |
| `--wave=N` | 特定 Wave のみ実行 | all |

### 3.2 Agent 定義

#### 3.2.1 ディレクトリ構造

```
.claude/
└── agents/
    ├── rust-specialist.md
    ├── frontend-dev.md
    ├── test-runner.md
    ├── code-reviewer.md
    ├── doc-writer.md
    └── explorer.md
```

#### 3.2.2 Subagent テンプレート（公式仕様準拠）

```yaml
# .claude/agents/{agent-name}.md
---
name: {agent-name}
description: >
  {役割の簡潔な説明}。
  {どのような場面で使用されるかの説明}。
  Use proactively when {自動起動の条件}。
model: sonnet  # haiku | sonnet | opus | inherit
tools: Read, Write, Edit, Bash, Grep, Glob
# disallowedTools: Task  # Subagent は Task を使用不可（制約）
# permissionMode: default  # default | acceptEdits | dontAsk | plan
# maxTurns: 20  # 最大ターン数
# memory: project  # user | project | local（永続メモリ）
# hooks:  # Subagent 固有のライフサイクルフック
#   PreToolUse:
#     - matcher: "Bash"
#       hooks:
#         - type: command
#           command: "./scripts/validate.sh"
# skills:  # プリロードする Skill（Subagent 起動時に注入）
#   - api-conventions
---

# {Agent 名}

あなたは {専門分野} の専門家です。

## 担当範囲
- {担当するファイル/ディレクトリ}
- {担当する作業種別}

## 制約
- {守るべきルール}
- {禁止事項}

## 出力形式
- {期待される出力フォーマット}
```

> **公式仕様との対応**（Claude Code 2.1.42 時点）:
>
> | フィールド | 必須 | 説明 |
> |-----------|:----:|------|
> | `name` | Yes | 一意識別子（小文字+ハイフン） |
> | `description` | Yes | Claude が委任判断に使用する説明文 |
> | `tools` | No | 使用可能ツール（省略時は全ツール継承） |
> | `disallowedTools` | No | 拒否ツールリスト |
> | `model` | No | `sonnet`, `opus`, `haiku`, `inherit`（デフォルト: `inherit`） |
> | `permissionMode` | No | 権限モード |
> | `maxTurns` | No | 最大ターン数 |
> | `memory` | No | 永続メモリスコープ（セッション横断学習） |
> | `hooks` | No | ライフサイクルフック |
> | `skills` | No | プリロード Skill |
> | `mcpServers` | No | 使用可能 MCP サーバー |

#### 3.2.3 標準 Agent 一覧

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Standard Agents                                  │
├─────────────────┬───────────────────────────────────────────────────────┤
│ rust-specialist │ Rust / Tauri / Cargo 専門                             │
│                 │ 対象: src-tauri/, *.rs, Cargo.toml                    │
│                 │ モデル: sonnet                                        │
├─────────────────┼───────────────────────────────────────────────────────┤
│ frontend-dev    │ フロントエンド開発（React/Vue/TS）                    │
│                 │ 対象: src/, *.ts, *.tsx, *.vue, *.css                 │
│                 │ モデル: sonnet                                        │
├─────────────────┼───────────────────────────────────────────────────────┤
│ test-runner     │ テスト実行・分析                                      │
│                 │ 対象: *test*, *spec*, __tests__/                      │
│                 │ モデル: haiku（高速）                                 │
├─────────────────┼───────────────────────────────────────────────────────┤
│ code-reviewer   │ コードレビュー・品質チェック                          │
│                 │ 対象: 全ソースコード                                  │
│                 │ モデル: opus（深い分析）                              │
├─────────────────┼───────────────────────────────────────────────────────┤
│ doc-writer      │ ドキュメント作成・更新                                │
│                 │ 対象: docs/, *.md, README                             │
│                 │ モデル: sonnet                                        │
├─────────────────┼───────────────────────────────────────────────────────┤
│ explorer        │ コードベース調査・分析                                │
│                 │ 対象: 全体（読み取り専用）                            │
│                 │ モデル: haiku（広範囲探索）                           │
└─────────────────┴───────────────────────────────────────────────────────┘
```

---

## 4. 実行フロー詳細

### 4.1 基本フロー

```
┌─────────────────────────────────────────────────────────────────────────┐
│ User Input                                                              │
│ > /lam-orchestrate src/ をリファクタリング                              │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Phase 1: Analysis (Skill)                                               │
├─────────────────────────────────────────────────────────────────────────┤
│ 1. src/ の構造を調査                                                    │
│    └── Glob("src/**/*") で対象ファイル列挙                             │
│                                                                         │
│ 2. 独立性を分析                                                         │
│    ├── src/auth/     → 独立（認証モジュール）                          │
│    ├── src/api/      → 独立（API エンドポイント）                      │
│    └── src/utils/    → 独立（ユーティリティ）                          │
│                                                                         │
│ 3. Agent を割り当て                                                     │
│    └── すべて frontend-dev（TypeScript）                               │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Phase 2: Execution (Main → Workers)                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Main Process (1メッセージで3つの Task を発行)                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Task({                                                           │  │
│  │   subagent_type: "frontend-dev",                                 │  │
│  │   prompt: "src/auth/ をリファクタリング..."                      │  │
│  │ })                                                               │  │
│  │                                                                  │  │
│  │ Task({                                                           │  │
│  │   subagent_type: "frontend-dev",                                 │  │
│  │   prompt: "src/api/ をリファクタリング..."                       │  │
│  │ })                                                               │  │
│  │                                                                  │  │
│  │ Task({                                                           │  │
│  │   subagent_type: "frontend-dev",                                 │  │
│  │   prompt: "src/utils/ をリファクタリング..."                     │  │
│  │ })                                                               │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                              │                                          │
│              ┌───────────────┼───────────────┐                          │
│              ▼               ▼               ▼                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                    │
│  │ Worker A     │ │ Worker B     │ │ Worker C     │                    │
│  │ src/auth/    │ │ src/api/     │ │ src/utils/   │                    │
│  │ 実行中...    │ │ 実行中...    │ │ 実行中...    │   ← 並列実行      │
│  └──────────────┘ └──────────────┘ └──────────────┘                    │
│              │               │               │                          │
│              └───────────────┼───────────────┘                          │
│                              ▼                                          │
│                     結果を Main に返却                                  │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Phase 3: Aggregation                                                    │
├─────────────────────────────────────────────────────────────────────────┤
│ 1. 各 Worker の結果を収集                                               │
│ 2. 変更ファイル一覧を統合                                               │
│ 3. 整合性チェック（インポートの競合等）                                │
│ 4. レポート生成                                                         │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Output                                                                  │
├─────────────────────────────────────────────────────────────────────────┤
│ ## 実行結果                                                             │
│                                                                         │
│ | タスク | 状態 | 変更ファイル |                                        │
│ |--------|------|--------------|                                        │
│ | src/auth/ | ✅ | 3 files |                                            │
│ | src/api/  | ✅ | 5 files |                                            │
│ | src/utils/| ✅ | 2 files |                                            │
│                                                                         │
│ **合計**: 10 ファイル変更                                               │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Wave 実行フロー（依存関係あり）

```mermaid
flowchart TB
    subgraph Wave1["Wave 1: 調査"]
        A1[Explorer A<br>依存関係調査]
        A2[Explorer B<br>影響範囲調査]
    end

    subgraph Wave2["Wave 2: 実装"]
        B1[Developer A<br>コア実装]
        B2[Developer B<br>UI 実装]
    end

    subgraph Wave3["Wave 3: 検証"]
        C1[Tester<br>テスト実行]
        C2[Reviewer<br>コードレビュー]
    end

    A1 --> B1
    A2 --> B2
    B1 --> C1
    B2 --> C1
    B1 --> C2
    B2 --> C2
```

```
Wave 1 (並列) ──完了──→ Wave 2 (並列) ──完了──→ Wave 3 (並列)

┌─────────────────────────────────────────────────────────────────────────┐
│ Wave 実行の制御                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ Main:                                                                   │
│   # Wave 1                                                              │
│   results_1 = [                                                         │
│     Task(explorer, "依存関係調査"),                                     │
│     Task(explorer, "影響範囲調査")                                      │
│   ]  # 並列実行                                                         │
│                                                                         │
│   # Wave 1 完了を待機（自動）                                           │
│                                                                         │
│   # Wave 2（Wave 1 の結果を使用）                                       │
│   results_2 = [                                                         │
│     Task(developer, f"コア実装。参考: {results_1}"),                    │
│     Task(developer, f"UI実装。参考: {results_1}")                       │
│   ]  # 並列実行                                                         │
│                                                                         │
│   # Wave 3                                                              │
│   results_3 = [                                                         │
│     Task(tester, f"テスト。対象: {results_2}"),                         │
│     Task(reviewer, f"レビュー。対象: {results_2}")                      │
│   ]  # 並列実行                                                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. エラーハンドリング

### 5.1 エラー種別

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Error Classification                                                    │
├─────────────────┬───────────────────────────────────────────────────────┤
│ RECOVERABLE     │ リトライまたは代替処理で継続可能                      │
│                 │ ・Subagent タイムアウト → リトライ                    │
│                 │ ・ファイル競合 → 直列化して再実行                     │
├─────────────────┼───────────────────────────────────────────────────────┤
│ PARTIAL_FAILURE │ 一部タスクのみ失敗、他は成功                          │
│                 │ ・成功結果は保持                                      │
│                 │ ・失敗タスクのみ報告                                  │
├─────────────────┼───────────────────────────────────────────────────────┤
│ FATAL           │ 全体停止が必要                                        │
│                 │ ・前提条件エラー（ファイル不在等）                    │
│                 │ ・Claude Code 自体のエラー                            │
└─────────────────┴───────────────────────────────────────────────────────┘
```

### 5.2 エラー処理フロー

```mermaid
flowchart TD
    E[エラー発生] --> C{エラー種別?}

    C -->|RECOVERABLE| R1[リトライ判定]
    R1 -->|リトライ可| R2[最大3回リトライ]
    R2 -->|成功| S[継続]
    R2 -->|失敗| P[PARTIAL_FAILURE へ]
    R1 -->|リトライ不可| P

    C -->|PARTIAL_FAILURE| P1[成功結果を保存]
    P1 --> P2[失敗タスクをログ]
    P2 --> P3[ユーザーに報告]
    P3 --> P4{継続?}
    P4 -->|Yes| S
    P4 -->|No| F

    C -->|FATAL| F[全体停止]
    F --> F1[エラーレポート出力]
```

---

## 6. 設定・カスタマイズ

### 6.1 設定ファイル構造

```
.claude/
├── skills/
│   └── lam-orchestrate.md      # Coordinator Skill
├── agents/
│   ├── rust-specialist.md      # カスタム Agent
│   ├── frontend-dev.md
│   └── ...
└── settings.json               # グローバル設定（将来）
```

### 6.2 Agent の追加手順

```
1. ファイル作成
   $ touch .claude/agents/my-agent.md

2. テンプレートに従って記述
   ---
   name: my-agent
   description: 新しいエージェント
   model: sonnet
   tools: [Read, Write, ...]
   ---

   # My Agent
   ...

3. 即座に使用可能（再起動不要）
   /lam-orchestrate で自動認識
```

### 6.3 Skill のカスタマイズ

```yaml
# .claude/skills/lam-orchestrate.md の編集

# 並列数変更
最大並列数: 3  # デフォルト 5 → 3

# Agent マッピング追加
| ファイルパターン | 推奨 Agent |
|------------------|------------|
| `*.py` | python-expert |  # 新規追加
```

---

## 7. 制限事項と将来計画

### 7.1 現在の制限

| 制限 | 説明 | 回避策 |
|------|------|--------|
| 2階層のみ | Subagent → Subagent 不可 | Wave パターンで擬似3層 |
| 最大10並列 | Claude Code の制限 | Wave 分割 |
| Background Subagent | MCP ツール使用不可、権限の事前承認必要 | Foreground 実行を基本とする |
| Subagent 間通信なし | 直接通信不可 | Main 経由で中継（Agent Teams で解消予定） |

### 7.2 将来拡張: Agent Teams（Experimental → Stable 後に移行検討）

> **旧称**: Swarm 機能。Opus 4.6 (2026-02) と同時に **Agent Teams** としてリリース。
> 現在は **Experimental**（`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` で有効化）。

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 将来: Agent Teams が Stable になった場合                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ 現在 (v2.0 - Subagent ベース):                                         │
│   Skill → Main → Subagents (Task tool)                                 │
│   ・安定 API、低コスト (1.5-2x)                                        │
│   ・Subagent 間通信なし（Main 経由）                                   │
│                                                                         │
│ 将来 (Agent Teams ベース):                                              │
│   Team Lead → Teammates (TeammateTool)                                  │
│   ・Teammate 間直接通信                                                 │
│   ・共有タスクリスト + 自動依存解決                                     │
│   ・高コスト (3-4x、plan mode 時 7x)                                   │
│                                                                         │
│ 移行判断基準:                                                           │
│   ✓ Agent Teams が Experimental を脱した                               │
│   ✓ セッション再開 (/resume) が Teammate に対応                        │
│   ✓ Windows Terminal での split-pane サポート                          │
│   ✓ トークンコストの改善（または許容範囲に）                           │
│                                                                         │
│ マイグレーション:                                                       │
│   - .claude/agents/ の定義はそのまま再利用可能                         │
│   - Skill は Team Lead への指示に変換                                   │
│   - 呼び出し方法は変更なし（/lam-orchestrate 維持）                    │
│                                                                         │
│ 現時点で Agent Teams を採用しない理由:                                  │
│   ✗ セッション再開不可（LAM の save/load と非互換）                    │
│   ✗ タスクステータスのドリフト（信頼性不足）                           │
│   ✗ Lead が委任せず自分で実装を始める問題                              │
│   ✗ トークンコスト 3-7x（個人〜小規模チームには過大）                  │
│   ✗ Windows Terminal で split-pane 非対応                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.3 taskqueue-mcp 統合（オプション）

```mermaid
flowchart LR
    subgraph Current["現在の構成（v2.0）"]
        S1[Skill] --> M1[Main]
        M1 --> W1[Subagents]
    end

    subgraph Future["将来の構成（Agent Teams）"]
        S2[Skill] --> TL[Team Lead]
        TL <--> TM[Teammates]
        TL --> |共有タスクリスト| TQ[(~/.claude/tasks/)]
    end

    Current -.->|Stable 後に移行| Future
```

---

## 8. 使用例

### 8.1 基本的な使用

```bash
# 単純なタスク分解・並列実行
/lam-orchestrate src/ をリファクタリング

# 並列数を制限
/lam-orchestrate --parallel=2 全ファイルにドキュメントを追加

# ドライラン（計画のみ）
/lam-orchestrate --dry-run 大規模な変更を計画
```

### 8.2 Tegetege-dice での使用例

```bash
# フロントエンドとバックエンド同時開発
/lam-orchestrate 新しいダイス機能を追加（UI とロジック両方）

# レビューとテスト並列
/lam-orchestrate --parallel=3 PR の品質チェック

# 調査タスク
/lam-orchestrate --dry-run 依存関係を全て洗い出し
```

### 8.3 期待される出力

```markdown
## 実行計画

| # | タスク | Agent | Wave |
|---|--------|-------|:----:|
| 1 | src-tauri/ にダイスロジック追加 | rust-specialist | 1 |
| 2 | src/ に UI コンポーネント追加 | frontend-dev | 1 |
| 3 | 統合テスト | test-runner | 2 |

続行しますか？ [Y/n] y

---

## 実行中...

Wave 1: [========================================] 2/2 完了
Wave 2: [========================================] 1/1 完了

---

## 実行結果

| タスク | 状態 | 変更 | 詳細 |
|--------|:----:|------|------|
| Rust ロジック | ✅ | 3 files | src-tauri/src/dice.rs 等 |
| UI コンポーネント | ✅ | 4 files | src/components/Dice.tsx 等 |
| 統合テスト | ✅ | 1 file | tests/integration.test.ts |

**合計**: 8 ファイル変更、0 エラー
```

---

## 9. チェックリスト

### 9.1 実装チェックリスト

- [ ] `.claude/skills/lam-orchestrate/SKILL.md` 作成（公式 SKILL.md 形式）
- [ ] `.claude/agents/` に Subagent 定義作成（公式 frontmatter 形式）
  - [ ] rust-specialist.md
  - [ ] frontend-dev.md
  - [ ] test-runner.md
  - [ ] code-reviewer.md（ビルトインとの差別化を検討）
  - [ ] doc-writer.md
  - [ ] ~~explorer.md~~（ビルトイン `Explore` で代替）
- [ ] ビルトイン Subagent との重複確認（Explore, Plan, general-purpose）
- [ ] 動作確認（ドライラン: `--dry-run`）
- [ ] 動作確認（実行）
- [ ] ドキュメント更新（CHANGELOG, README）
- [ ] 参照 Claude Code バージョンの記録

### 9.2 レビューチェックリスト

- [ ] Skill の指示が明確か（`description` が委任判断に十分か）
- [ ] Subagent の役割がビルトインと重複していないか
- [ ] `tools` フィールドが最小権限原則に従っているか
- [ ] エラーハンドリングが適切か
- [ ] 並列実行の安全性が担保されているか（同一ファイル書き込みの排除）
- [ ] `memory` 設定の適切性（不要な永続化を避ける）

---

## 10. 参考資料

- [_reference/2026-01-29.md](../../_reference/2026-01-29.md) - 調査結果
- [_reference/2026-01-28-02.md](../../_reference/2026-01-28-02.md) - 要求仕様

---

*本設計書は LAM v4.0 の一部として作成された。*
*v2.0 改訂: Claude Code 公式 Subagent/Skills API (v2.1.42) に準拠。*
*Agent Teams (旧 Swarm) が Stable になった段階で、Section 7.2 の移行基準に基づき再評価する。*
