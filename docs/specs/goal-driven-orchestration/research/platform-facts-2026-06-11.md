# Claude Code プラットフォーム仕様 裏取りファクトシート

**調査日**: 2026-06-11（claude-code-guide / Sonnet による upstream-first 裏取り）
**参照**: code.claude.com/docs（docs map 最終更新 2026-06-09）、changelog v2.1.173 時点
**用途**: B-3 ゴール駆動オーケストレーション design.md の根拠資料（requirements.md OQ-1/OQ-2 関連）

> 「確認済み」の項目は設計書に書式を転記してよい。
> 「未確認」の項目は設計書に「要裏取り」と明記し、実装フェーズ前に再確認すること。

## 1. /goal コマンド

| 観点 | 確認結果 | 確度 |
|------|---------|------|
| 存在 | v2.1.139 (2026-05-11) で追加 | 確認済み |
| 書式 | `/goal` + 自由文（最大 4,000 文字）。上限は条件文中に自然言語で記述。例: `/goal all tests pass or stop after 20 turns` | 確認済み |
| 判定の独立性 | session-scoped な prompt-based Stop hook のラッパー。各ターン終了後に条件文+会話履歴を別コンテキストの small fast model に送信し yes/no + 理由を返す。既定 = **Haiku**（"configured small fast model"） | 確認済み |
| ネイティブ上限 | **数値パラメータは存在しない**。「or stop after 20 turns」等の打ち切り句が必須。`/goal` 単体実行でターン数・経過時間・トークン消費のステータス表示あり | 確認済み |
| サブエージェント内動作 | 公式記述なし。v2.1.154 changelog に「evaluator が background shells / delegated subagents 実行中に firing する不具合修正」とあり、メインセッション専用設計の可能性が高い | **未確認（要裏取り）** |
| Stop hook との関係 | `disableAllHooks` / `allowManagedHooksOnly` 設定時は使用不可 | 確認済み |

出典: https://code.claude.com/docs/en/goal.md

## 2. ネストサブエージェント

| 観点 | 確認結果 | 確度 |
|------|---------|------|
| 解禁 | v2.1.172 (2026-06-10)。"Sub-agents can now spawn their own sub-agents (up to 5 levels deep)" | 確認済み |
| 実験的フラグ | changelog に有効化設定の記述なし。sub-agents.md には旧記述「Subagents cannot spawn other subagents」が残存（docs が未追従の可能性） | **部分確認** |
| 深さ上限 5 の確定性 | 暫定値か確定値かの明示なし | **未確認（要裏取り）** |

出典: changelog v2.1.172、https://code.claude.com/docs/en/sub-agents.md

## 3. エージェント定義フロントマター（.claude/agents/*.md）

| フィールド | 確認結果 | 確度 |
|-----------|---------|------|
| `model:` | エイリアス `sonnet`/`opus`/`haiku`/`fable`、フル ID（`claude-opus-4-8` 等）、`inherit`（省略時デフォルト）。解決優先順位: (1) `CLAUDE_CODE_SUBAGENT_MODEL` env (2) per-invocation `model` (3) frontmatter (4) メインセッション | 確認済み |
| `tools:` | **allowlist 方式**（記載ツールのみ許可）。`disallowedTools:` は denylist。両方指定時は denylist 先適用。Task は v2.1.63 で `Agent` にリネーム（`Task` はエイリアス）。特定タイプのみ許可: `tools: Agent(worker, researcher), Read, Bash`。spawn 全面禁止 = `tools` から `Agent` を除く | 確認済み |
| `memory:` | `user` / `project` / `local` の 3 スコープ。先頭 200 行 or 25KB を system prompt に自動注入 | 確認済み |
| その他 | `maxTurns`(int) / `effort`(low〜max) / `isolation: worktree` / `background`(bool) / `permissionMode` / `initialPrompt` / `color` | 確認済み |

出典: https://code.claude.com/docs/en/sub-agents.md

## 4. ワークフロー（Dynamic Workflows / 保存済み）

| 観点 | 確認結果 | 確度 |
|------|---------|------|
| 保存・再利用 | 保存先 `.claude/workflows/`（プロジェクト）or `~/.claude/workflows/`（個人）。`/workflows` → `s` キーで保存。`/<name>` で呼び出し。`args` グローバル変数で引数受け渡し | 確認済み |
| トークン消費の公式注意 | あり。"a single run can use meaningfully more tokens than working through the same task in conversation"。Desktop の approval card にも caution 表示 | 確認済み |
| ultracode との関係 | ultracode = xhigh effort + 自動 workflow orchestration。`/effort ultracode`（セッション全体）またはプロンプト内 `ultracode` キーワード（単発）で起動。"use a workflow" 等の自然言語でも起動 | 確認済み |
| 無効化手段 | ① `/config` の "Dynamic workflows" トグル ② `settings.json` の `"disableWorkflows": true` ③ env `CLAUDE_CODE_DISABLE_WORKFLOWS=1` ④ "Ultracode keyword trigger" トグル ⑤ `Alt+W` でキーワードハイライト解除 | 確認済み |
| 制約 | 最大同時 16 エージェント（CPU 依存）/ 1 run 最大 1,000 / mid-run ユーザー入力不可 / スクリプトから FS・shell 直接アクセス不可 / v2.1.154 以降・有料プラン | 確認済み |

出典: https://code.claude.com/docs/en/workflows.md

## 5. コスト・トークン計測

| 手段 | 粒度 | 確度 |
|------|------|------|
| `/usage` | サブエージェント種別・skill・plugin・MCP 単位の消費割合（24h/7d、ローカル推計） | 確認済み |
| `/workflows` ビュー | フェーズ・エージェント単位のトークン数（実行中のみ） | 確認済み |
| Console API | 正確な請求情報（platform.claude.com/usage） | 確認済み |
| Agent ツールの結果 | task-notification / ツール結果に `subagent_tokens` 等の usage が含まれる（本セッションでも実測） | 確認済み（実測） |
| OTEL メトリクス | 公式ドキュメントに言及なし | **未確認（要裏取り）** |

出典: https://code.claude.com/docs/en/costs.md

## 6. Stop hook によるループ制御

**入力（共通フィールド）**: `session_id` / `transcript_path` / `cwd` / `permission_mode` / `hook_event_name` / `effort.level` / `agent_id`・`agent_type`（サブエージェント時のみ）

**出力（Stop 固有）**:

| パターン | 方法 | 効果 |
|---------|------|------|
| 続行強制 | `{"decision": "block", "reason": "..."}` or exit code 2 | 停止を阻止し次ターン継続 |
| 非ブロック注入 | `hookSpecificOutput.additionalContext` | system reminder として注入 |
| 通常停止 | exit 0 + 空 JSON | そのまま停止 |

**暴走防止**: `stop_hook_active` のような公式カウンターは**存在しない**。防止手段は hook の `timeout`（既定 600s）、Stop は 1 ターン 1 回発火、打ち切り句の条件文埋め込み。

**ループ制御に使えるイベント**: Stop / PostToolBatch / PreToolUse / SubagentStop / TaskCreated / TaskCompleted / TeammateIdle / UserPromptSubmit（いずれもブロック可）

## 設計に影響する未確認事項（要裏取りリスト）

| # | 項目 | 現状 | 推奨アクション |
|---|------|------|--------------|
| 1 | `/goal` のサブエージェント内発行可否 | 未確認（メインセッション専用の可能性大） | **実測確認が最確実**（OQ-1 の検証タスク） |
| 2 | ネストサブエージェントのデフォルト有効性・フラグ | 部分確認 | v2.1.172 以降で実測 |
| 3 | 深さ上限 5 の確定性 | 未確認 | 設計書には「現時点の上限 5（変更可能性あり・設定値として外部化）」と記載 |
| 4 | OTEL によるエージェント別トークン計測 | 未確認 | costs/observability ドキュメント再確認 |
| 5 | workflow スクリプト内モデル切替の正確な書式 | 未確認 | workflows.md スクリプト例 / Agent SDK 仕様で確認 |
| 6 | `/goal` evaluator が provider 非依存で Haiku か | 部分確認 | provider 固定なら追加確認不要 |
