# Claude Code 公式仕様 逐語引用検証レポート

**作成日**: 2026-05-27  
**調査担当**: Claude Code (Sonnet 4.6)  
**調査手法**: context7 MCP (`/websites/code_claude`) + WebFetch (`code.claude.com/docs/en/*`)  
**目的**: LAM プロジェクトの hook 実装が依存するキー・書式の現行仕様での有効性を確認

---

## A. 高リスク依存5点の検証

### A-1: PreCompact イベント

**判定: 【確認済み / 正式掲載あり】**

**逐語引用:**

```
Source: https://code.claude.com/docs/en/hooks  (WebFetch 2026-05-27)

"All 29 official hook events:
...
25. PreCompact
26. PostCompact
..."

PreCompact input schema (公式サンプル):
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf.jsonl",
  "cwd": "/Users/...",
  "hook_event_name": "PreCompact",
  "trigger": "manual",
  "custom_instructions": ""
}
```

Source: https://code.claude.com/docs/en/hooks (context7 クエリ結果より)

```
"JSON input structure for PreCompact hooks, which receive trigger type and custom
instructions. For manual triggers, custom_instructions contains user input;
for auto triggers, it is empty."
```

**LAMへの影響**: 継続使用OK。「公式未掲載だが動作確認済み」という従来の注記は**更新が必要**。現在は29の公式フックイベントの一つとして正式掲載されている。

マッチャー値: `"manual"` または `"auto"`（compactionのトリガー種別）

---

### A-2: Stop hook の出力書式 `{"decision": "block", "reason": ...}`

**判定: 【確認済み / 書式変更なし】**

**逐語引用:**

```
Source: https://code.claude.com/docs/en/hooks (context7 クエリ結果より)

"Stop Decision Control JSON Response
Return this JSON from Stop or SubagentStop hooks to block Claude from stopping.
The decision field must be 'block' and reason is required to explain why Claude
should continue.

{
  'decision': 'block',
  'reason': 'Must be provided when Claude is blocked from stopping'
}"
```

また、汎用ブロックとして:

```
"Block Decision Control for Hooks
Use this JSON output to block an action for hooks like UserPromptSubmit,
PostToolUse, and others.

{
  'decision': 'block',
  'reason': 'Test suite must pass before proceeding'
}"
```

`decision` の取り得る値: `"block"` のみ（省略または exit 0 でアクションを許可）。  
exit code 2 でも同様のブロック効果あり。

**LAMへの影響**: 継続使用OK。書式は現行仕様と完全一致。

---

### A-3: PreToolUse 出力 `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask"|"allow"|"deny", ...}}`

**判定: 【確認済み / 書式変更あり（値の追加）】**

**逐語引用:**

```
Source: https://code.claude.com/docs/en/hooks (WebFetch 2026-05-27)

"Controls tool execution with structured decisions:
{
  'hookSpecificOutput': {
    'hookEventName': 'PreToolUse',
    'permissionDecision': 'deny|allow|ask|defer',
    'permissionDecisionReason': 'Explanation text',
    'updatedInput': { /* modified tool input */ },
    'additionalContext': 'Context for Claude'
  }
}"
```

公式サンプル (context7より、Source: https://code.claude.com/docs/en/hooks):

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Destructive command blocked by hook"
  }
}
```

`permissionDecision` の取り得る値: `"allow"`, `"deny"`, `"ask"`, **`"defer"`**（先行調査では3値だったが `defer` が追加されている）

`defer` の意味: "Let normal permission flow decide"（通常の許可フローに委ねる）

**LAMへの影響**: 継続使用OK（既存の3値は全て有効）。ただし `defer` という4番目の値が追加されていることに注意。書式のキー名は現行仕様と一致。

---

### A-4: 入力キー `stop_hook_active`

**判定: 【確認済み / 書式変更なし】**

**逐語引用:**

Stop イベントの入力 JSON 公式サンプル (Source: https://code.claude.com/docs/en/hooks, context7より):

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../00893aaf.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "Stop",
  "stop_hook_active": true,
  ...
}
```

Python SDK の型定義 (Source: https://code.claude.com/docs/en/agent-sdk/python, context7より):

```python
class StopHookInput(BaseHookInput):
    hook_event_name: Literal["Stop"]
    stop_hook_active: bool
```

Bash での使用例 (Source: https://code.claude.com/docs/en/hooks-guide, context7より):

```bash
INPUT=$(cat)
if [ "$(echo "$INPUT" | jq -r '.stop_hook_active')" = "true" ]; then
  exit 0  # Allow Claude to stop
fi
```

**LAMへの影響**: 継続使用OK。`stop_hook_active` は現行仕様で明示的に定義されている。`SubagentStop` イベントにも同フィールドが存在する。

---

### A-5: 環境変数 `$CLAUDE_PROJECT_DIR`

**判定: 【確認済み / 書式変更なし】**

**逐語引用:**

hook コマンド内での使用例 (Source: https://code.claude.com/docs/en/claude-code-on-the-web, context7より):

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/install_pkgs.sh"
          }
        ]
      }
    ]
  }
}
```

PreToolUse hook での使用例 (Source: https://code.claude.com/docs/en/hooks-guide, context7より):

```json
{
  "type": "command",
  "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect-files.sh"
}
```

環境変数一覧表 (Source: https://code.claude.com/docs/en/hooks, WebFetch 2026-05-27):

| Variable | Description | Example |
|----------|-------------|---------|
| `CLAUDE_PROJECT_DIR` | Project root directory | `/home/user/my-project` |

MCP ドキュメントでも追記確認 (Source: https://code.claude.com/docs/en/mcp, WebFetch 2026-05-27):

```
"Claude Code sets CLAUDE_PROJECT_DIR in the spawned server's environment to the
project root, so your server can resolve project-relative paths without depending
on the working directory. This is the same directory hooks receive in their
CLAUDE_PROJECT_DIR variable."
```

**LAMへの影響**: 継続使用OK。公式に明示されている変数名であり、hooks・MCP の両文脈で有効。

---

## B. 追加確認点(6-10)

### B-6: Skills のディレクトリ構造

**判定: 【確認済み / 変更あり（commands 統合を公式確認）】**

**逐語引用:**

```
Source: https://code.claude.com/docs/en/skills (WebFetch 2026-05-27)

"Custom commands have been merged into skills. A file at .claude/commands/deploy.md
and a skill at .claude/skills/deploy/SKILL.md both create /deploy and work the same
way. Your existing .claude/commands/ files keep working. Skills add optional features:
a directory for supporting files, frontmatter to control whether you or Claude invokes
them, and the ability for Claude to load them automatically when relevant."
```

ディレクトリ構造 (Source: https://code.claude.com/docs/en/skills, context7より):

```
my-skill/
├── SKILL.md           # Main instructions (required)
├── template.md        # (optional)
├── examples/
│   └── sample.md      # (optional)
└── scripts/
    └── validate.sh    # (optional)
```

SKILL.md フロントマター必須/任意キー (Source: https://code.claude.com/docs/en/skills, context7より):

```yaml
---
name: my-skill                    # optional
description: What this skill does # recommended (auto-invoke に必要)
disable-model-invocation: true    # optional (ユーザー専用呼び出し)
allowed-tools: Read Grep          # optional
---
```

`agent: Explore`、`context: fork`、`argument-hint`、`model` キーも使用例に見られる（Source: https://code.claude.com/docs/en/slash-commands, context7より）。

**LAMへの影響**: 継続使用OK。`.claude/commands/` は後方互換あり。Skills はより豊富な機能を持つ上位互換。`allowed-tools` キー名の確認が完了。

---

### B-7: Sub-agents のフロントマター拡張

**判定: 【確認済み】**

**逐語引用:**

公式サポートフィールド一覧 (Source: https://code.claude.com/docs/en/sub-agents, WebFetch 2026-05-27 保存ファイルより):

```
"The --agents flag accepts JSON with the same frontmatter fields as file-based
subagents: description, prompt, tools, disallowedTools, model, permissionMode,
mcpServers, hooks, maxTurns, skills, initialPrompt, memory, effort, background,
isolation, and color."
```

各キーの定義 (Source: https://code.claude.com/docs/en/sub-agents):

| キー | 必須 | 説明 |
|-----|------|------|
| `name` | No | エージェント識別子 |
| `description` | No | クロードが使用するタイミングを決定するための説明 |
| `tools` | No | 許可ツールのallowlist |
| `disallowedTools` | No | 拒否ツールのdenylist |
| `model` | No | 使用モデル（例: `sonnet`, `haiku`, `inherit`） |
| `permissionMode` | No | 許可モード |
| `mcpServers` | No | MCPサーバー設定 |
| `hooks` | No | フック設定 |
| `maxTurns` | No | 最大ターン数 |
| `skills` | No | プリロードするスキル |
| `initialPrompt` | No | 初期プロンプト |
| `memory` | No | `user`, `project`, `local` のいずれか |
| `effort` | No | 努力レベル |
| `background` | No | `true` でバックグラウンドタスクとして常時実行 |
| `isolation` | No | `worktree` でgitワークツリー分離 |
| `color` | No | `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan` |

**メモリスコープ** (Source: https://code.claude.com/docs/en/sub-agents):
- `user`: `~/.claude/agent-memory/<name>/`（全プロジェクト共有）
- `project`: `.claude/agent-memory/<name>/`（プロジェクト固有、バージョン管理可）
- `local`: `.claude/agent-memory-local/<name>/`（プロジェクト固有、バージョン管理外）

**LAMへの影響**: 継続使用OK。LAMが使用する `memory` キーは公式確認済み。`isolation: worktree` も正式サポート。

---

### B-8: MCP のトランスポート変更

**判定: 【確認済み / SSE は非推奨】**

**逐語引用:**

```
Source: https://code.claude.com/docs/en/mcp (WebFetch 2026-05-27)

"Option 1: Add a remote HTTP server
HTTP servers are the recommended option for connecting to remote MCP servers.
This is the most widely supported transport for cloud-based services."

"Option 2: Add a remote SSE server
[WARNING] The SSE (Server-Sent Events) transport is deprecated.
Use HTTP servers instead, where available."
```

コメント例 (context7より、Source: https://code.claude.com/docs/en/mcp):

```bash
# Note that SSE transport is deprecated.
claude mcp add --transport sse asana https://mcp.asana.com/sse
```

現行推奨トランスポートの設定書式 (Source: https://code.claude.com/docs/en/mcp, WebFetch):

```json
{
  "mcpServers": {
    "notion": {
      "type": "http",
      "url": "https://mcp.notion.com/mcp"
    }
  }
}
```

`type` フィールドのエイリアス:

```
"When configuring MCP servers via JSON in .mcp.json, ~/.claude.json, or
claude mcp add-json, the type field accepts streamable-http as an alias for http.
The MCP specification uses the name streamable-http for this transport,
so configurations copied from server documentation work without modification."
```

型は `McpStdioServerConfig | McpSSEServerConfig | McpHttpServerConfig | McpSdkServerConfig` の4種類が現行サポート。

**LAMへの影響**: LAMがSSEを使用している場合は要更新。HTTPトランスポートへの移行を推奨。SSEは引き続き動作するが非推奨。

---

### B-9: Settings の "Managed" 設定（managed-settings.json 等）

**判定: 【確認済み / 正式機能として存在】**

**逐語引用:**

ファイル名と場所 (Source: https://code.claude.com/docs/en/settings, WebFetch 2026-05-27):

```
"File name: managed-settings.json
Storage locations by platform:
- macOS: /Library/Application Support/ClaudeCode/
- Linux and WSL: /etc/claude-code/
- Windows: C:\Program Files\ClaudeCode\

Note: The legacy Windows path C:\ProgramData\ClaudeCode\managed-settings.json
is no longer supported as of v2.1.75."
```

設定の優先順位:
```
1. Managed（最高優先）— 上書き不可
2. Command line arguments
3. Local (.claude/settings.local.json)
4. Project (.claude/settings.json)
5. User (~/.claude/settings.json)（最低優先）
```

サーバー管理設定 (Source: https://code.claude.com/docs/en/server-managed-settings, WebFetch 2026-05-27):

```
"Server-managed settings allow administrators to centrally configure Claude Code
through a web-based interface on Claude.ai. Claude Code clients automatically receive
these settings when users authenticate with their organization credentials."
```

両方式の関係:

```
"Within the managed tier, the first source that delivers a non-empty configuration
wins. Server-managed settings are checked first, then endpoint-managed settings.
Sources do not merge: if server-managed settings deliver any keys at all,
endpoint-managed settings are ignored entirely."
```

**LAMへの影響**: LAM が managed-settings.json を使用する場合は正常に機能する。Windows パスが変更されているため（v2.1.75以降）、古い `C:\ProgramData\ClaudeCode\` パスを参照していると要更新。

---

### B-10: hooks の `type: "mcp_tool"` / `type: "agent"` / `type: "prompt"` と `effort.level` 入力

**判定: 【確認済み / 全て正式掲載】**

**逐語引用:**

hook の type 値 (Source: https://code.claude.com/docs/en/hooks, WebFetch 2026-05-27):

```
"There are five types:
- Command hooks (type: "command"): run a shell command
- HTTP hooks (type: "http"): send the event's JSON input as an HTTP POST request
- MCP tool hooks (type: "mcp_tool"): call a tool on an already-connected MCP server
- Prompt hooks (type: "prompt"): send a prompt to a Claude model for single-turn evaluation
- Agent hooks (type: "agent"): spawn a subagent that can use tools"
```

`effort.level` 入力フィールド (Source: https://code.claude.com/docs/en/hooks, WebFetch 2026-05-27):

```
"The effort field is available in the common input fields for events that fire within
a tool-use context: Present for events that fire within a tool-use context, such as
PreToolUse, PostToolUse, Stop, and SubagentStop, when the current model supports
the effort parameter."

"The effort object structure:
{
  'effort': {
    'level': 'low|medium|high|xhigh|max'
  }
}"
```

環境変数 `CLAUDE_EFFORT` (Source: https://code.claude.com/docs/en/hooks, WebFetch 2026-05-27):

```
| CLAUDE_EFFORT | Current effort level: "low", "medium", "high", "xhigh", "max"
```

`type: "prompt"` の使用例 (context7より、Source: https://code.claude.com/docs/en/hooks-guide):

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Check if all tasks are complete. If not, respond with {\"ok\": false, \"reason\": \"what remains to be done\"}."
          }
        ]
      }
    ]
  }
}
```

`type: "agent"` の使用例 (context7より、Source: https://code.claude.com/docs/en/hooks-guide):

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "agent",
            "prompt": "Verify that all unit tests pass. $ARGUMENTS",
            "timeout": 120
          }
        ]
      }
    ]
  }
}
```

**LAMへの影響**: 継続使用OK。`mcp_tool`、`agent`、`prompt` の3つは全て正式サポートされている（計5種類）。`effort.level` も公式入力フィールドとして確認済み。

---

## 判定サマリー表

| 項目 | 判定 | LAMへの影響 |
|------|------|------------|
| A-1: PreCompact イベント | ✅ 確認済み（正式掲載あり） | 継続使用OK / 「未掲載」注記の**更新必要** |
| A-2: Stop hook `{"decision": "block", "reason": ...}` | ✅ 確認済み | 継続使用OK |
| A-3: PreToolUse `hookSpecificOutput / permissionDecision` | ✅ 確認済み（値追加あり） | 継続使用OK / `"defer"` 値が追加（既存値は全て有効） |
| A-4: `stop_hook_active` 入力キー | ✅ 確認済み | 継続使用OK |
| A-5: `$CLAUDE_PROJECT_DIR` 環境変数 | ✅ 確認済み | 継続使用OK |
| B-6: Skills ディレクトリ構造 / commands 統合 | ✅ 確認済み（統合を公式確認） | 継続使用OK / `.claude/commands/` 後方互換あり |
| B-7: Sub-agents フロントマター拡張 | ✅ 確認済み | 継続使用OK（`memory`、`isolation`、`color` 等は全て正式） |
| B-8: MCP SSE 非推奨 / HTTP 推奨 | ✅ 確認済み（SSE は非推奨） | SSE使用中なら**要更新**（HTTPへの移行を推奨） |
| B-9: managed-settings.json | ✅ 確認済み（正式機能） | 継続使用OK / Windows パス変更に注意（v2.1.75以降） |
| B-10: hook type: mcp_tool / agent / prompt / effort.level | ✅ 確認済み | 継続使用OK |

---

## 公式で裏取りできなかった先行調査の主張

以下の項目は、今回の調査で公式一次情報を確認できなかった、または先行調査が主張していたものの公式文書への記載が見つからなかった項目：

1. **バージョン番号の詳細** — 「v4.6.2」等のLAM側のバージョン番号は調査対象外（Claude Codeの公式バージョン番号ではない）。

2. **PreCompact フックが「ブロック可能」かどうかの明示的確認** — WebFetch結果では「exit 2 または JSON `decision: "block"` でブロック可能」と記述されていたが、context7の公式スニペットには PreCompact 固有のブロック出力サンプルが見当たらなかった。PostCompact は「ブロック不可能（compaction 完了後のため）」と明記されている。PreCompact のブロック可否は WebFetch 結果より「可能」と推定されるが、公式スニペットでの逐語確認は未完全。

3. **`managed-settings.json` の旧 Windows パス廃止時期** — 「v2.1.75以降、`C:\ProgramData\ClaudeCode\` は非サポート」という記述は WebFetch の Settings ページから取得したものだが、v2.1.75のリリース日は公式 changelog で確認していない。

4. **`effort.level` の `"xhigh"` 値** — `"xhigh"` という値が公式にリストアップされていることは確認できたが、これがどのモデルで利用可能かの対応表は逐語確認できなかった。環境変数 `CLAUDE_EFFORT` の説明に `"xhigh"` が含まれていることは確認済み。

5. **hook `type: "mcp_tool"` の詳細スキーマ** — `type: "mcp_tool"` が公式に存在することは確認済みだが、必須フィールド（サーバー名、ツール名など）の完全なスキーマは今回のクエリで取得できなかった。動作確認は別途必要。

---

*調査実施: 2026-05-27*  
*情報ソース: code.claude.com/docs (context7 MCP経由) および code.claude.com/docs (WebFetch直接取得)*
