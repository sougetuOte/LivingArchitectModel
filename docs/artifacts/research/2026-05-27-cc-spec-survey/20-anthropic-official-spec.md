# Claude Code 公式仕様サーベイ（2026-05-27）

> 出典: WebFetch（https://code.claude.com/docs/en/hooks, /settings, /skills, /sub-agents, /mcp）  
> および context7 MCP（/websites/code_claude, Trust Score 9.9）  
> 調査日: 2026-05-27

---

## 目次

1. [Hooks](#1-hooks)
2. [Settings](#2-settings)
3. [Permissions](#3-permissions)
4. [Skills](#4-skills)
5. [Sub-agents](#5-sub-agents)
6. [MCP](#6-mcp)
7. [2026年頃に追加・変更された新機能（要注意）](#7-2026年頃に追加変更された新機能要注意)
8. [取得不可項目](#8-取得不可項目)

---

## 1. Hooks

**出典**: https://code.claude.com/docs/en/hooks

### 1.1 対応イベント一覧（27種類）

#### セッションライフサイクル
| イベント | 説明 |
|----------|------|
| `SessionStart` | セッション開始・再開時 |
| `Setup` | 一回限りの初期化（--init-only, --init, --maintenance）|
| `SessionEnd` | セッション終了時（ブロック不可） |

#### ターンごとのイベント
| イベント | 説明 |
|----------|------|
| `UserPromptSubmit` | Claudeがユーザープロンプトを処理する前 |
| `UserPromptExpansion` | スラッシュコマンド展開時 |
| `Stop` | Claudeが応答を完了した時 |
| `StopFailure` | APIエラーでターンが終了した時 |

#### エージェントループ（ツール実行）
| イベント | 説明 |
|----------|------|
| `PreToolUse` | ツール呼び出し実行前（ブロック可能） |
| `PostToolUse` | ツール呼び出し成功後 |
| `PostToolUseFailure` | ツール呼び出し失敗後 |
| `PostToolBatch` | 並列ツール呼び出しの全バッチ完了後 |
| `PermissionRequest` | 権限ダイアログ表示時 |
| `PermissionDenied` | autoモードでツール呼び出しが拒否された時 |

#### Subagents & Tasks
| イベント | 説明 |
|----------|------|
| `SubagentStart` | サブエージェント生成時 |
| `SubagentStop` | サブエージェント終了時 |
| `TaskCreated` | タスク作成時 |
| `TaskCompleted` | タスク完了マーク時 |
| `TeammateIdle` | エージェントチームメンバーがアイドルになる前 |

#### ファイル・設定
| イベント | 説明 |
|----------|------|
| `FileChanged` | ウォッチ中のファイルが変更された時 |
| `ConfigChange` | 設定ファイルが変更された時 |
| `CwdChanged` | カレントディレクトリが変更された時 |
| `InstructionsLoaded` | CLAUDE.md / .claude/rules/*.md がロードされた時 |

#### コンテキスト管理
| イベント | 説明 |
|----------|------|
| `PreCompact` | コンテキスト圧縮の前 |
| `PostCompact` | コンテキスト圧縮の完了後 |

#### MCP統合
| イベント | 説明 |
|----------|------|
| `Elicitation` | MCPサーバーがユーザー入力を要求した時 |
| `ElicitationResult` | ユーザーがMCP Elicitationに応答した後 |

#### 通知
| イベント | 説明 |
|----------|------|
| `Notification` | Claude Codeが通知を送信する時 |

#### Worktree（新規）
| イベント | 説明 |
|----------|------|
| `WorktreeCreate` | ワークツリー作成時 |
| `WorktreeRemove` | ワークツリー削除時 |

---

### 1.2 入力 JSON スキーマ

#### 全イベント共通フィールド

```json
{
  "session_id": "string",
  "transcript_path": "string",
  "cwd": "string",
  "permission_mode": "default|plan|acceptEdits|auto|dontAsk|bypassPermissions",
  "effort": {
    "level": "low|medium|high|xhigh|max"
  },
  "hook_event_name": "string",
  "agent_id": "string (optional, subagent only)",
  "agent_type": "string (optional)"
}
```

#### SessionStart 入力

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/path/to/project",
  "hook_event_name": "SessionStart",
  "source": "startup|resume|clear|compact",
  "model": "claude-sonnet-4-6"
}
```

#### Setup 入力

```json
{
  "session_id": "abc123",
  "cwd": "/path/to/project",
  "hook_event_name": "Setup",
  "trigger": "init|maintenance"
}
```

#### UserPromptSubmit 入力

```json
{
  "session_id": "abc123",
  "transcript_path": "...",
  "cwd": "...",
  "permission_mode": "default",
  "hook_event_name": "UserPromptSubmit",
  "prompt": "string"
}
```

#### UserPromptExpansion 入力

```json
{
  "session_id": "abc123",
  "cwd": "...",
  "permission_mode": "default",
  "hook_event_name": "UserPromptExpansion",
  "expansion_type": "slash_command|mcp_prompt",
  "command_name": "string",
  "command_args": "string",
  "command_source": "string",
  "prompt": "string"
}
```

#### PreToolUse 入力

```json
{
  "session_id": "abc123",
  "cwd": "...",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash|Write|Edit|Read|Glob|Grep|Agent|WebFetch|WebSearch|mcp__*",
  "tool_input": {},
  "tool_use_id": "toolu_01ABC123...",
  "effort": { "level": "high" }
}
```

ツール別 `tool_input` の主要フィールド:
- `Bash`: `{ "command": "str", "description": "str?", "timeout": 60000, "run_in_background": false }`
- `Write`: `{ "file_path": "str", "content": "str" }`
- `Edit`: `{ "file_path": "str", "old_string": "str", "new_string": "str", "replace_all": false }`
- `Read`: `{ "file_path": "str" }`

#### PostToolUse 入力

```json
{
  "session_id": "abc123",
  "cwd": "...",
  "permission_mode": "default",
  "hook_event_name": "PostToolUse",
  "tool_name": "string",
  "tool_input": {},
  "tool_result": "string",
  "tool_use_id": "toolu_01ABC123..."
}
```

#### PermissionRequest 入力

```json
{
  "session_id": "abc123",
  "transcript_path": "...",
  "cwd": "...",
  "permission_mode": "default",
  "hook_event_name": "PermissionRequest",
  "tool_name": "Bash",
  "tool_input": {
    "command": "rm -rf node_modules",
    "description": "Remove node_modules directory"
  },
  "permission_suggestions": [
    {
      "type": "addRules",
      "rules": [{ "toolName": "Bash", "ruleContent": "rm -rf node_modules" }],
      "behavior": "allow",
      "destination": "localSettings"
    }
  ]
}
```

#### PermissionDenied 入力

```json
{
  "session_id": "abc123",
  "transcript_path": "...",
  "cwd": "...",
  "permission_mode": "auto",
  "hook_event_name": "PermissionDenied",
  "tool_name": "Bash",
  "tool_input": { "command": "...", "description": "..." },
  "tool_use_id": "toolu_01ABC123...",
  "reason": "Auto mode denied: command targets a path outside the project"
}
```

#### Stop 入力

```json
{
  "session_id": "abc123",
  "transcript_path": "...",
  "cwd": "...",
  "permission_mode": "default",
  "hook_event_name": "Stop",
  "stop_hook_active": true,
  "last_assistant_message": "...",
  "background_tasks": [
    {
      "id": "task-001",
      "type": "shell",
      "status": "running",
      "description": "tail logs",
      "command": "tail -f /var/log/syslog"
    }
  ],
  "session_crons": [
    {
      "id": "cron-001",
      "schedule": "0 9 * * 1-5",
      "recurring": true,
      "prompt": "check the build"
    }
  ]
}
```

#### StopFailure 入力

```json
{
  "session_id": "abc123",
  "hook_event_name": "StopFailure",
  "error_type": "rate_limit|authentication_failed|oauth_org_not_allowed|billing_error|invalid_request|model_not_found|server_error|max_output_tokens|unknown",
  "error_message": "string"
}
```

#### SubagentStart 入力

```json
{
  "session_id": "abc123",
  "hook_event_name": "SubagentStart",
  "agent_id": "string",
  "agent_type": "general-purpose|Explore|Plan|custom-name"
}
```

#### InstructionsLoaded 入力

```json
{
  "session_id": "abc123",
  "cwd": "...",
  "hook_event_name": "InstructionsLoaded",
  "file_path": "string",
  "memory_type": "User|Project|Local|Managed",
  "load_reason": "session_start|nested_traversal|path_glob_match|include|compact",
  "globs": ["string"]
}
```

#### PreCompact 入力

```json
{
  "session_id": "abc123",
  "transcript_path": "...",
  "cwd": "...",
  "hook_event_name": "PreCompact",
  "trigger": "manual|auto",
  "custom_instructions": ""
}
```

#### PostCompact 入力

```json
{
  "session_id": "abc123",
  "transcript_path": "...",
  "cwd": "...",
  "hook_event_name": "PostCompact",
  "trigger": "manual",
  "compact_summary": "Summary of the compacted conversation..."
}
```

#### SessionEnd 入力

```json
{
  "session_id": "abc123",
  "transcript_path": "...",
  "cwd": "...",
  "hook_event_name": "SessionEnd",
  "reason": "clear|resume|logout|prompt_input_exit|bypass_permissions_disabled|other"
}
```

#### ConfigChange 入力

```json
{
  "session_id": "abc123",
  "transcript_path": "...",
  "cwd": "...",
  "hook_event_name": "ConfigChange",
  "source": "project_settings",
  "file_path": "/path/to/.claude/settings.json"
}
```

#### FileChanged 入力

```json
{
  "session_id": "abc123",
  "transcript_path": "...",
  "cwd": "/Users/my-project",
  "hook_event_name": "FileChanged",
  "file_path": "/Users/my-project/.envrc",
  "event": "change"
}
```

#### CwdChanged 入力

```json
{
  "session_id": "abc123",
  "transcript_path": "...",
  "cwd": "/Users/my-project/src",
  "hook_event_name": "CwdChanged",
  "old_cwd": "/Users/my-project",
  "new_cwd": "/Users/my-project/src"
}
```

#### WorktreeCreate 入力

```json
{
  "session_id": "abc123",
  "transcript_path": "...",
  "cwd": "...",
  "hook_event_name": "WorktreeCreate",
  "name": "feature-auth"
}
```

#### WorktreeRemove 入力

```json
{
  "session_id": "abc123",
  "transcript_path": "...",
  "cwd": "...",
  "hook_event_name": "WorktreeRemove",
  "worktree_path": "/Users/.../my-project/.claude/worktrees/feature-auth"
}
```

---

### 1.3 出力 JSON スキーマ

#### 全イベント共通出力フィールド

```json
{
  "continue": true,
  "stopReason": "string",
  "suppressOutput": false,
  "systemMessage": "string",
  "terminalSequence": "string"
}
```

> **注意**: `terminalSequence` は OSC 0/1/2/9/99/777, BEL などのターミナル通知シーケンスを出力できる新フィールド。

#### PreToolUse 決定出力

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow|deny|ask|defer",
    "permissionDecisionReason": "string",
    "additionalContext": "string",
    "updatedInput": {}
  }
}
```

#### PostToolUse 出力

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "string",
    "updatedToolOutput": "any",
    "updatedMCPToolOutput": "any (deprecated: use updatedToolOutput)"
  }
}
```

#### PermissionRequest 決定出力

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "allow|deny",
      "updatedInput": {},
      "updatedPermissions": [
        { "type": "setMode", "mode": "acceptEdits", "destination": "session" }
      ]
    }
  }
}
```

#### PermissionDenied 出力

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionDenied",
    "retry": true
  }
}
```

#### SessionStart 出力

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "string",
    "initialUserMessage": "string",
    "watchPaths": ["/path/to/watch"]
  }
}
```

#### UserPromptSubmit 出力

```json
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "string"
  }
}
```

#### Elicitation 出力

```json
{
  "hookSpecificOutput": {
    "hookEventName": "Elicitation",
    "action": "accept|decline|cancel",
    "content": {}
  }
}
```

#### WorktreeCreate 出力

```json
{
  "hookSpecificOutput": {
    "hookEventName": "WorktreeCreate",
    "worktreePath": "string"
  }
}
```

---

### 1.4 settings.json での Hooks 設定ブロック書式

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "string",
            "args": ["string"],
            "async": false,
            "asyncRewake": false,
            "shell": "bash|powershell",
            "timeout": 600,
            "statusMessage": "string",
            "if": "permission_rule",
            "once": false
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "http",
            "url": "http://localhost:8080/hooks",
            "headers": { "Authorization": "Bearer $MY_TOKEN" },
            "allowedEnvVars": ["MY_TOKEN"],
            "timeout": 600,
            "statusMessage": "string"
          }
        ]
      },
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "mcp_tool",
            "server": "my_server",
            "tool": "security_scan",
            "input": { "file_path": "${tool_input.file_path}" },
            "timeout": 600
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Evaluate if Claude should stop: $ARGUMENTS.",
            "model": "string",
            "timeout": 30,
            "statusMessage": "string"
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "agent",
            "prompt": "string",
            "timeout": 60,
            "statusMessage": "string"
          }
        ]
      }
    ]
  },
  "disableAllHooks": false
}
```

#### Matcher パターン記法

```
"" or "*"           - 全マッチ
"exact"             - 完全一致（英数字・_・|のみ）
"exact|exact2"      - 複数の完全一致
"^regex.*pattern"   - JavaScriptの正規表現（その他の文字で始まる）
```

#### Hook ハンドラタイプ一覧

| タイプ | 説明 |
|--------|------|
| `command` | シェルコマンド実行 |
| `http` | HTTP POSTリクエスト |
| `mcp_tool` | MCPサーバーのツール呼び出し |
| `prompt` | LLMによるhook評価 |
| `agent` | サブエージェントによるhook評価 |

#### 終了コードと動作

| 終了コード | 意味 | 動作 |
|-----------|------|------|
| 0 | 成功 | stdoutをJSONとして解析 |
| 2 | ブロッキングエラー | stdoutを無視、stderrをClaudeに渡す、アクションをブロック |
| その他 | 非ブロッキングエラー | stderrの最初の行を表示して実行継続 |

#### Hookの配置場所とスコープ

| 場所 | スコープ | 共有可 |
|------|----------|--------|
| `~/.claude/settings.json` | 全プロジェクト | No |
| `.claude/settings.json` | 単一プロジェクト | Yes |
| `.claude/settings.local.json` | 単一プロジェクト | No（gitignore） |
| `hooks/hooks.json`（プラグイン） | プラグイン有効時 | Yes |
| Skill/Agentフロントマター | コンポーネントアクティブ時 | Yes |

---

## 2. Settings

**出典**: https://code.claude.com/docs/en/settings

### 2.1 設定ファイルの階層

優先度（高→低）:

1. **Managed**（MDM/システムレベル、上書き不可）
   - macOS: `/Library/Application Support/ClaudeCode/`
   - Linux/WSL: `/etc/claude-code/`
   - Windows: `C:\Program Files\ClaudeCode\`
2. **コマンドライン引数**（一時的なセッション上書き）
3. **Local**: `.claude/settings.local.json`（個人用、gitignore）
4. **Project**: `.claude/settings.json`（チーム共有、git管理）
5. **User**: `~/.claude/settings.json`（個人用、全プロジェクト）

### 2.2 settings.json の主要構造

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",

  // モデル・動作
  "model": "claude-sonnet-4-6",
  "effortLevel": "xhigh",
  "alwaysThinkingEnabled": true,
  "showThinkingSummaries": true,

  // 権限・セキュリティ
  "permissions": {
    "allow": ["Bash(npm run lint)", "Bash(npm run test *)", "Read(~/.zshrc)"],
    "ask": ["Bash(git push *)"],
    "deny": ["Bash(curl *)", "Read(./.env)"],
    "additionalDirectories": ["../docs/"],
    "defaultMode": "acceptEdits",
    "disableBypassPermissionsMode": "disable",
    "skipDangerousModePermissionPrompt": false
  },

  // サンドボックス
  "sandbox": {
    "enabled": true,
    "failIfUnavailable": false,
    "autoAllowBashIfSandboxed": true,
    "excludedCommands": ["docker *"],
    "filesystem": {
      "allowWrite": ["/tmp/build"],
      "denyWrite": ["/etc"],
      "denyRead": ["~/.aws/credentials"],
      "allowRead": ["."]
    },
    "network": {
      "allowedDomains": ["github.com", "*.npmjs.org"],
      "deniedDomains": ["sensitive.cloud.example.com"]
    }
  },

  // MCP
  "allowedMcpServers": [{ "serverName": "github" }],
  "deniedMcpServers": [{ "serverName": "filesystem" }],
  "enableAllProjectMcpServers": true,
  "enabledMcpjsonServers": ["memory", "github"],
  "disabledMcpjsonServers": ["filesystem"],

  // Hooks
  "hooks": { /* 1章参照 */ },
  "disableAllHooks": false,
  "allowedHttpHookUrls": ["https://hooks.example.com/*"],
  "httpHookAllowedEnvVars": ["MY_TOKEN"],

  // 環境変数・認証
  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1"
  },
  "apiKeyHelper": "/bin/generate_temp_api_key.sh",

  // UI・表示
  "language": "japanese",
  "editorMode": "vim",
  "autoScrollEnabled": true,
  "showTurnDuration": true,

  // メモリ・コンテキスト
  "autoMemoryEnabled": true,
  "claudeMd": "Always run make lint before committing.",
  "claudeMdExcludes": ["**/vendor/**/CLAUDE.md"],

  // Skills
  "skillListingBudgetFraction": 0.01,
  "maxSkillDescriptionChars": 1536,
  "skillOverrides": {
    "legacy-context": "name-only",
    "deploy": "off"
  },

  // Git
  "attribution": {
    "commit": "🤖 Generated with Claude Code",
    "pr": ""
  },
  "includeGitInstructions": true,
  "respectGitignore": true,

  // Worktrees（新規）
  "worktree": {
    "baseRef": "fresh",
    "symlinkDirectories": ["node_modules", ".cache"],
    "sparsePaths": ["packages/my-app"],
    "bgIsolation": "worktree"
  },

  // Agents・Subagents
  "agent": "code-reviewer",
  "disableAgentView": false,
  "disableAutoMode": false,
  "autoMode": {
    "environment": [],
    "allow": [],
    "soft_deny": ["$defaults"],
    "hard_deny": []
  },

  // チーム・チャンネル
  "channelsEnabled": true,
  "teammateMode": "in-process|auto|tmux",

  // アップデート
  "autoUpdatesChannel": "stable",
  "minimumVersion": "2.1.100",

  // ステータスライン
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.sh"
  },
  "subagentStatusLine": {
    "type": "command",
    "command": "~/.claude/subagent-statusline.sh"
  }
}
```

### 2.3 settings.local.json との関係

- gitignore される個人設定ファイル
- `.claude/settings.json`（プロジェクト）より高優先度
- `~/.claude/settings.json`（ユーザー）より**低**優先度
- 用途: 個人の好み、テスト用、マシン固有設定

### 2.4 最近追加された設定キー

| 設定キー | 追加バージョン | 目的 |
|---------|--------------|------|
| `disableRemoteControl` | v2.1.128 | リモートコントロール機能のブロック |
| `maxSkillDescriptionChars` | v2.1.105 | スキル説明の最大文字数（デフォルト: 1536） |
| `skillListingBudgetFraction` | v2.1.105 | スキルリスト用コンテキスト割り当て（デフォルト: 0.01） |
| `skillOverrides` | v2.1.129 | スキルごとの可視性制御 |
| `worktree.bgIsolation` | v2.1.143 | バックグラウンドセッションの分離モード |
| `policyHelper` | v2.1.136 | 動的なManaged設定計算 |
| `parentSettingsBehavior` | v2.1.133 | 親提供設定のマージ動作 |

---

## 3. Permissions

**出典**: https://code.claude.com/docs/en/settings（permissions セクション）

### 3.1 allow/ask/deny の書式

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run lint)",
      "Bash(npm run test *)",
      "Bash(git log *)",
      "Bash(git diff *)",
      "Read(~/.zshrc)",
      "Read",
      "Glob",
      "Grep"
    ],
    "ask": [
      "Bash(git push *)"
    ],
    "deny": [
      "Bash(curl *)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "ToolSearch",
      "Agent(Explore)",
      "Agent(my-custom-agent)"
    ]
  }
}
```

### 3.2 ツール名のマッチング記法

```
"Read"              - ツール全体を許可
"Bash(git log *)"   - Bashの特定コマンドパターン（glob）
"Bash(git diff *)"  - ワイルドカードマッチ
"mcp__server__tool" - MCPツールの指定
"Agent(Explore)"    - 特定サブエージェントの制限
"ToolSearch"        - ツール検索機能のブロック
```

### 3.3 Permission Modes

| モード | 説明 |
|--------|------|
| `default` | 標準の権限確認動作 |
| `plan` | 計画モード（実行前に計画を提示） |
| `acceptEdits` | ファイル編集を自動承認 |
| `auto` | 自動モード（安全と判断したものを自動承認） |
| `dontAsk` | 確認なしで実行 |
| `bypassPermissions` | 全権限チェックをバイパス（危険） |

### 3.4 追加ディレクトリ設定

```json
{
  "permissions": {
    "additionalDirectories": ["../docs/", "/shared/libs/"],
    "defaultMode": "acceptEdits"
  }
}
```

> **注意**: `--add-dir` フラグとは異なり、`permissions.additionalDirectories` はファイルアクセスのみを付与する（Skillsなどの設定はロードされない）。

---

## 4. Skills

**出典**: https://code.claude.com/docs/en/skills

### 4.1 配置場所

| 場所 | パス | 適用範囲 |
|------|------|----------|
| Enterprise | Managed設定ディレクトリ配下 | 組織の全ユーザー |
| Personal | `~/.claude/skills/<skill-name>/SKILL.md` | 全プロジェクト |
| Project | `.claude/skills/<skill-name>/SKILL.md` | このプロジェクトのみ |
| Plugin | `<plugin>/skills/<skill-name>/SKILL.md` | プラグイン有効時 |

> **互換性**: `.claude/commands/<name>.md` も引き続き動作する（スキルに統合済み）。スキルと同名のコマンドがある場合、スキルが優先される。

### 4.2 SKILL.md フロントマター（完全リファレンス）

```yaml
---
name: my-skill              # 表示名。ディレクトリ名がデフォルト。コマンド名はディレクトリ名から決まる（例外あり）
description: "What this skill does and when to use it"  # 推奨（1536文字まで）
when_to_use: "Additional trigger context"               # descriptionに追記される
argument-hint: "<issue-number>"                         # オートコンプリート表示
arguments: "issue branch"                               # 名前付き引数の宣言（スペース区切りまたはYAMLリスト）
disable-model-invocation: true                          # Claudeによる自動起動を禁止
user-invocable: false                                   # /メニューから非表示
allowed-tools: "Read Grep Bash(git *)"                  # このスキル使用中に自動許可するツール
model: "sonnet"                                         # このスキル使用中のモデル上書き
effort: "high"                                          # このスキル使用中のエフォートレベル
context: fork                                           # forkでサブエージェントとして実行
agent: "code-reviewer"                                  # context: fork時に使うサブエージェント
hooks:                                                  # このスキルのライフサイクルhooks
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/security-check.sh"
paths: "src/**/*.py, tests/**/*.py"                    # このスキルを自動適用するファイルパターン
shell: "bash|powershell"                                # !`command` ブロックに使うシェル
---

Your skill instructions here...
```

**必須**: なし（`description` は強く推奨）

### 4.3 文字列置換変数

| 変数 | 説明 |
|------|------|
| `$ARGUMENTS` | 全引数文字列 |
| `$ARGUMENTS[N]` | N番目の引数（0ベース） |
| `$N` | `$ARGUMENTS[N]` の短縮形 |
| `$name` | `arguments` フロントマターで宣言した名前付き引数 |
| `${CLAUDE_SESSION_ID}` | 現在のセッションID |
| `${CLAUDE_EFFORT}` | 現在のエフォートレベル |
| `${CLAUDE_SKILL_DIR}` | このSKILL.mdのディレクトリ絶対パス |

### 4.4 動的コンテキストインジェクション

```markdown
## Current changes

!`git diff HEAD`
```

バッククォートで囲んだコマンドが実行され、その出力でこの行が置換される。

### 4.5 ディレクトリ構造

```text
my-skill/
├── SKILL.md           # メイン手順（必須）
├── template.md        # テンプレート
├── examples/
│   └── sample.md      # サンプル出力
└── scripts/
    └── validate.sh    # Claudeが実行できるスクリプト
```

### 4.6 invocation制御

| フロントマター | ユーザー起動 | Claude自動起動 | コンテキスト |
|--------------|------------|--------------|------------|
| （デフォルト） | Yes | Yes | 説明が常時ロード、本文は起動時 |
| `disable-model-invocation: true` | Yes | No | 説明がコンテキストに入らない |
| `user-invocable: false` | No | Yes | 説明が常時ロード |

### 4.7 コンテキストライフサイクル

- 起動後、SKILL.md の内容はセッション中維持される（再ロードなし）
- 自動圧縮時: 最近起動したスキルが優先、先頭5,000トークン保持
- 複数スキル合計25,000トークンの共有バジェット

### 4.8 skillOverrides 設定

```json
{
  "skillOverrides": {
    "legacy-context": "name-only",
    "deploy": "off"
  }
}
```

---

## 5. Sub-agents

**出典**: https://code.claude.com/docs/en/sub-agents

### 5.1 配置場所と優先度

| 場所 | スコープ | 優先度 |
|------|----------|--------|
| Managed設定 | 組織全体 | 1（最高） |
| `--agents` CLIフラグ | 現在のセッションのみ | 2 |
| `.claude/agents/` | 現在のプロジェクト | 3 |
| `~/.claude/agents/` | 全プロジェクト | 4 |
| Plugin `agents/` | プラグイン有効時 | 5（最低） |

> **注意**: プロジェクト`.claude/agents/`はカレントディレクトリから上位へ再帰的に探索される。`--add-dir`ではサブエージェントはロードされない。

### 5.2 サブエージェントファイルの書式

```markdown
---
name: code-reviewer          # 必須: 小文字・ハイフン
description: "When Claude should delegate to this subagent"  # 必須
tools: Read, Glob, Grep      # 許可ツール（省略=全ツール継承）
disallowedTools: Write, Edit # 拒否ツール（toolsより優先適用）
model: sonnet                # sonnet|opus|haiku|フルID|inherit
permissionMode: acceptEdits  # default|acceptEdits|auto|dontAsk|bypassPermissions|plan
maxTurns: 20                 # 最大ターン数
skills:                      # 起動時に事前ロードするスキル
  - api-conventions
  - error-handling-patterns
mcpServers:                  # サブエージェント専用MCPサーバー
  - playwright:
      type: stdio
      command: npx
      args: ["-y", "@playwright/mcp@latest"]
  - github                   # 既存設定サーバーの参照
hooks:                       # ライフサイクルhooks（プラグインサブエージェントでは無効）
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-command.sh"
memory: user                 # user|project|local（永続メモリ）
background: false            # trueでバックグラウンドタスクとして実行
effort: high                 # low|medium|high|xhigh|max
isolation: worktree          # worktreeで分離リポジトリを使用
color: blue                  # red|blue|green|yellow|purple|orange|pink|cyan
initialPrompt: "..."         # メインセッションとして実行時の初期プロンプト
---

You are a code reviewer. When invoked, analyze the code and provide
specific, actionable feedback on quality, security, and best practices.
```

### 5.3 必須フィールド

- `name`: 必須
- `description`: 必須

### 5.4 利用不可ツール（サブエージェント内）

以下のツールはサブエージェントでは使用不可:
- `Agent`
- `AskUserQuestion`
- `EnterPlanMode`
- `ExitPlanMode`（permissionModeがplanの場合を除く）
- `ScheduleWakeup`
- `WaitForMcpServers`

### 5.5 ビルトインサブエージェント

| エージェント | モデル | 用途 |
|-------------|--------|------|
| `Explore` | Haiku | 読み取り専用、高速コードベース探索 |
| `Plan` | 継承 | プランモード用リサーチ |
| `general-purpose` | 継承 | 複合タスク、全ツール |
| `statusline-setup` | Sonnet | `/statusline`設定 |
| `claude-code-guide` | Haiku | Claude Code機能の質問応答 |

### 5.6 CLIでの動的定義

```bash
claude --agents '{
  "code-reviewer": {
    "description": "Expert code reviewer.",
    "prompt": "You are a senior code reviewer.",
    "tools": ["Read", "Grep", "Glob", "Bash"],
    "model": "sonnet"
  }
}'
```

`--agents`フラグで使えるフィールド: `description`, `prompt`, `tools`, `disallowedTools`, `model`, `permissionMode`, `mcpServers`, `hooks`, `maxTurns`, `skills`, `initialPrompt`, `memory`, `effort`, `background`, `isolation`, `color`

### 5.7 永続メモリ

```yaml
---
name: code-reviewer
memory: user   # ~/.claude/agent-memory/ に蓄積
---
```

`memory: user` で `~/.claude/agent-memory/<agent-name>/` にセッション横断の学習を保存。

### 5.8 注意: プラグインサブエージェントの制限

プラグイン由来のサブエージェントでは以下のフィールドが**無視される**:
- `hooks`
- `mcpServers`
- `permissionMode`

---

## 6. MCP

**出典**: https://code.claude.com/docs/en/mcp

### 6.1 .mcp.json の書式（プロジェクトスコープ）

```json
{
  "mcpServers": {
    "server-name": {
      "type": "stdio|http|sse|streamable-http",
      "command": "npx",
      "args": ["-y", "some-mcp-server"],
      "env": {
        "API_KEY": "${API_KEY:-default}"
      },
      "timeout": 600000,
      "alwaysLoad": false
    }
  }
}
```

> **注意**: `streamable-http` は `http` の alias（MCPスペックの名称）。SSEは**非推奨**。

### 6.2 サーバータイプ別の設定

#### Stdio（ローカルプロセス）

```json
{
  "mcpServers": {
    "local-tools": {
      "type": "stdio",
      "command": "node",
      "args": ["/path/to/server.js", "--port", "8080"],
      "env": {
        "DB_URL": "${DB_URL}"
      }
    }
  }
}
```

#### HTTP（リモート、推奨）

```json
{
  "mcpServers": {
    "remote-api": {
      "type": "http",
      "url": "https://mcp.example.com/mcp",
      "headers": {
        "Authorization": "Bearer ${API_TOKEN}"
      },
      "oauth": {
        "clientId": "your-client-id",
        "callbackPort": 8080,
        "scopes": "read write",
        "authServerMetadataUrl": "https://auth.example.com/.well-known/openid-configuration"
      },
      "headersHelper": "/opt/bin/get-mcp-auth-headers.sh",
      "alwaysLoad": true,
      "timeout": 600000
    }
  }
}
```

#### SSE（非推奨、移行推奨）

```json
{
  "mcpServers": {
    "sse-server": {
      "type": "sse",
      "url": "https://api.example.com/sse",
      "headers": {
        "X-API-Key": "${API_KEY}"
      }
    }
  }
}
```

### 6.3 スコープと保存先

| スコープ | 保存先 | チーム共有 |
|---------|--------|----------|
| Local（デフォルト） | `~/.claude.json`（プロジェクトパスで管理） | No |
| Project | `.mcp.json`（プロジェクトルート） | Yes（git管理） |
| User | `~/.claude.json` | No |

### 6.4 CLIコマンド

```bash
# HTTPサーバーを追加
claude mcp add --transport http <name> <url>

# SSEサーバーを追加（非推奨）
claude mcp add --transport sse <name> <url>

# Stdioサーバーを追加
claude mcp add -- <name> <command> [args...]

# ヘッダー付き
claude mcp add --transport http github https://api.githubcopilot.com/mcp/ \
  --header "Authorization: Bearer YOUR_GITHUB_PAT"

# スコープ指定
claude mcp add --transport http stripe --scope project https://mcp.stripe.com

# JSON設定で追加
claude mcp add-json <name> '<json>'

# 一覧表示
claude mcp list

# 詳細確認
claude mcp get github

# 削除
claude mcp remove github
```

### 6.5 環境変数展開（.mcp.json）

サポート構文:
- `${VAR}` - 環境変数を展開
- `${VAR:-default}` - 未設定時のデフォルト値

展開可能な場所: `command`, `args`, `env`, `url`, `headers`

### 6.6 MCP Tool Search（デフォルト有効）

```bash
# デフォルト（全MCPツールを遅延ロード）
# 環境変数なし

# 閾値モード（コンテキストの10%以下なら先行ロード）
ENABLE_TOOL_SEARCH=auto

# カスタム閾値
ENABLE_TOOL_SEARCH=auto:5

# 無効化（全ツールを起動時ロード）
ENABLE_TOOL_SEARCH=false
```

特定サーバーの遅延を無効化:
```json
{
  "mcpServers": {
    "core-tools": {
      "type": "http",
      "url": "https://mcp.example.com/mcp",
      "alwaysLoad": true
    }
  }
}
```

### 6.7 サブエージェントでのMCP設定

```yaml
---
name: browser-tester
mcpServers:
  - playwright:
      type: stdio
      command: npx
      args: ["-y", "@playwright/mcp@latest"]
  - github
---
```

---

## 7. 2026年頃に追加・変更された新機能（要注意）

### 7.1 Hooks（大幅拡張）

| 新機能 | 詳細 |
|--------|------|
| **27種類のイベント** | 旧来の7種類から大幅拡張（WorktreeCreate/Remove, Elicitation, PostToolBatch, StopFailure, InstructionsLoaded, UserPromptExpansion 等） |
| **`terminalSequence` 出力フィールド** | OSC/BELシーケンスでターミナル通知 |
| **`asyncRewake` フィールド** | バックグラウンドhookが終了コード2で再起動トリガー |
| **`effort` 入力フィールド** | hookからエフォートレベルにアクセス可能 |
| **`agent` hook タイプ** | サブエージェントをhookとして実行 |
| **`prompt` hook タイプ** | LLMによるhook判定 |
| **`mcp_tool` hook タイプ** | MCPツールをhookから呼び出し |
| **スキル/エージェントのフロントマターhooks** | コンポーネント定義にhooksを直接記述 |
| **`PermissionRequest` イベント** | `PreToolUse`とは別の権限要求専用hook |
| **`watchPaths` in SessionStart出力** | 特定パスのファイル変更監視設定 |
| **`/hooks` メニュー** | セッション内でhooks設定を確認 |
| **`CLAUDE_ENV_FILE`** | hookをまたぐ環境変数の永続化 |

### 7.2 Settings（新規キー）

| 新規キー | バージョン |
|---------|----------|
| `skillOverrides` | v2.1.129 |
| `maxSkillDescriptionChars` | v2.1.105 |
| `skillListingBudgetFraction` | v2.1.105 |
| `worktree.bgIsolation` | v2.1.143 |
| `policyHelper` | v2.1.136 |
| `parentSettingsBehavior` | v2.1.133 |
| `disableRemoteControl` | v2.1.128 |
| `subagentStatusLine` | 最近追加 |
| `teammateMode` | 最近追加 |
| `channelsEnabled` | 最近追加 |

### 7.3 Skills（新機能）

| 新機能 | 詳細 |
|--------|------|
| **コマンドとの統合** | `.claude/commands/`はSkillsに統合。既存ファイルは引き続き動作 |
| **Agent Skills Open Standard** | agentskills.io に準拠 |
| **`paths` フロントマター** | 特定ファイルパターンで自動適用 |
| **`shell` フロントマター** | PowerShell対応（Windows） |
| **`when_to_use` フロントマター** | トリガー条件の追加記述 |
| **`${CLAUDE_SKILL_DIR}` 変数** | スキルディレクトリの絶対パス |
| **`${CLAUDE_EFFORT}` 変数** | 現在のエフォートレベル |
| **`hooks` フロントマター** | スキル固有のhooks定義 |
| **`context: fork`** | サブエージェントとして実行 |
| **`model`/`effort` フロントマター** | スキル実行中のモデル・エフォート上書き |
| **Live change detection** | スキルファイル変更がセッション内即反映 |
| **ネストディレクトリ自動発見** | モノレポ対応、サブディレクトリのskillsも自動ロード |
| **5000/25000トークン圧縮ルール** | 圧縮時のスキル保持ルール明確化 |
| **バンドルスキル** | `/run`, `/verify`, `/run-skill-generator`, `/code-review`, `/debug`, `/batch`, `/loop`, `/claude-api` |

### 7.4 Sub-agents（新機能）

| 新機能 | 詳細 |
|--------|------|
| **`memory` フロントマター** | `user|project|local` で永続メモリを有効化 |
| **`isolation: worktree`** | サブエージェントが独立したgit worktreeで実行 |
| **`background: true`** | 常にバックグラウンドタスクとして実行 |
| **`effort` フロントマター** | サブエージェントのエフォートレベル設定 |
| **`color` フロントマター** | UIでのサブエージェント識別色 |
| **`initialPrompt` フロントマター** | メインセッション起動時の初期プロンプト |
| **`skills` フロントマター** | 事前ロードするスキルの指定 |
| **`hooks` フロントマター** | サブエージェント固有のhooks |
| **`Agent(worker, researcher)`** | Agentツールで起動可能サブエージェントを制限 |
| **`/agents` コマンド** | インタラクティブなサブエージェント管理UI |
| **Task → Agent リネーム** | v2.1.63でTaskツールがAgentに改名（旧名は引き続き動作） |
| **サブエージェントの再帰探索** | `.claude/agents/`配下のサブフォルダも探索 |

### 7.5 MCP（新機能）

| 新機能 | 詳細 |
|--------|------|
| **Tool Search（デフォルト有効）** | MCPツールを遅延ロード、コンテキスト節約 |
| **`alwaysLoad` フィールド** | 特定サーバーの遅延ロード無効化 |
| **`headersHelper`** | 動的ヘッダー生成スクリプト |
| **`oauth.scopes`** | OAuthスコープの固定 |
| **`oauth.authServerMetadataUrl`** | OAuthメタデータ検索URL指定 |
| **`--channels` フラグ** | MCPサーバーからのメッセージプッシュ |
| **`anthropic/maxResultSizeChars`** | ツールごとの出力サイズ上限設定 |
| **`anthropic/alwaysLoad`** | ツールごとの遅延ロード無効化 |
| **自動再接続** | HTTP/SSEサーバーの指数バックオフ再接続 |
| **`list_changed`通知** | ツール一覧の動的更新対応 |
| **Elicitation** | MCPサーバーからの構造化ユーザー入力要求 |
| **SSEの非推奨化** | HTTP（streamable-http）への移行を推奨 |
| **Claude.ai connectors統合** | claude.aiで設定したMCPサーバーをCC内で自動利用 |

---

## 8. 取得不可項目

以下の情報は今回の調査では取得できなかった（推測で埋めていない）:

- `Setup` hookイベントの完全な出力スキーマ
- `TaskCreated`/`TaskCompleted`/`TeammateIdle` hookの詳細な入力スキーマ
- `PostToolBatch` hookの詳細な入力スキーマ
- `ElicitationResult` hookの詳細な入力スキーマ
- `UserPromptExpansion` hookの出力スキーマ
- Managed設定（`/etc/claude-code/` 等）の詳細フォーマット
- Plugins（`plugin.json`）の完全フォーマット
- Agent Teams の詳細設定書式
- Channels の詳細設定書式
- `fastModePerSessionOptIn` の詳細動作
- 各hookイベントの `statusMessage` フィールドのデフォルト値

---

*このドキュメントは 2026-05-27 時点の公式ドキュメントに基づく。Claude Code は活発に開発中のため、次回調査では Upstream First 原則に従い必ず再取得すること。*
