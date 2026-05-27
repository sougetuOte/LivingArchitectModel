# LAM 現行依存インベントリ — Claude Code プラットフォーム仕様との突き合わせ用

**作成日**: 2026-05-27
**作成目的**: 約2ヶ月後の Claude Code 最新仕様すり合わせに向け、LAM が依存する全プラットフォーム書式・キー・イベント名を網羅的に記録する。

---

## 1. hooks — イベント種別と登録書式（settings.json）

### 1.1 登録されているイベント種別

| イベント名 | 対応 hook スクリプト | matcher | file:line |
|-----------|---------------------|---------|-----------|
| `PreToolUse` | `pre-tool-use.py` | なし（全ツール対象） | `.claude/settings.json` L69–72 |
| `PostToolUse` | `post-tool-use.py` | `"Edit\|Write\|Bash"` | `.claude/settings.json` L74–78 |
| `PostToolUseFailure` | `post-tool-use.py` | `"Bash"` | `.claude/settings.json` L79–83 |
| `Stop` | `lam-stop-hook.py` | なし（全ツール対象） | `.claude/settings.json` L84–88 |
| `PreCompact` | `pre-compact.py` | なし | `.claude/settings.json` L89–93 |

> **注意**: `PreCompact` は「公式ドキュメント未掲載だが動作確認済み（2026-03時点）」と pre-compact.py L8 のコメントに明記されている。最も陳腐化リスクが高い。

### 1.2 hooks ブロックのキー構造

```json
{
  "hooks": {
    "<EventName>": [
      {
        "matcher": "<ToolNameRegex>",     // 省略可（全ツール対象になる）
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/<script>.py"
          }
        ]
      }
    ]
  }
}
```

依存キー: `type`（"command" 固定）、`command`、`matcher`、環境変数 `$CLAUDE_PROJECT_DIR`

file:line: `.claude/settings.json` L68–95

---

## 2. hooks — 入力 JSON のキー名

### 2.1 共通ユーティリティ（_hook_utils.py）

| キー | 取得関数 | 用途 | file:line |
|------|---------|------|-----------|
| `tool_name` | `get_tool_name(data)` | ツール種別識別 | `_hook_utils.py` L65–67 |
| `tool_input` | `get_tool_input(data, key)` | ツール引数取得（辞書） | `_hook_utils.py` L70–78 |
| `tool_input.file_path` | `get_tool_input(data, "file_path")` | 対象ファイルパス | `_hook_utils.py` L70–78 |
| `tool_input.command` | `get_tool_input(data, "command")` | Bash コマンド文字列 | `_hook_utils.py` L70–78 |
| `tool_response` | `get_tool_response(data, key, default)` | ツール実行結果 | `_hook_utils.py` L81–89 |

### 2.2 pre-tool-use.py が読む入力キー

| キー | 取得方法 | 用途 | file:line |
|------|---------|------|-----------|
| `tool_name` | `get_tool_name(data)` | 読取専用ツール判定 / ログ | `pre-tool-use.py` L163 |
| `tool_input.file_path` | `get_tool_input(data, "file_path")` | PM/SE/PG パス判定 | `pre-tool-use.py` L174 |
| `tool_input.command` | `get_tool_input(data, "command")` | AUDITING PG コマンド判定 | `pre-tool-use.py` L175 |

### 2.3 post-tool-use.py が読む入力キー

| キー | 取得方法 | 用途 | file:line |
|------|---------|------|-----------|
| `tool_name` | `get_tool_name(data)` | Bash / Edit / Write 分岐 | `post-tool-use.py` L304 |
| `tool_input.command` | `get_tool_input(data, "command")` | テストコマンド検出 | `post-tool-use.py` L305 |
| `tool_input.file_path` | `get_tool_input(data, "file_path")` | doc-sync-flag / loop-log 記録 | `post-tool-use.py` L306 |
| `hook_event_name` | `data.get("hook_event_name", "")` | PostToolUseFailure 判定 | `post-tool-use.py` L307 |

> **陳腐化リスク**: post-tool-use.py L324 のコメントに「exit_code は空文字: PostToolUse/PostToolUseFailure の入力データに exit code が含まれないため」と明記。これは 2026-03-13 に判明した仕様（trust-model.md 参照）。将来バージョンで exitCode が追加される可能性があり、動作変更につながりうる。

### 2.4 lam-stop-hook.py が読む入力キー

| キー | 取得方法 | 用途 | file:line |
|------|---------|------|-----------|
| `stop_hook_active` | `input_data.get("stop_hook_active")` | 再帰防止チェック | `lam-stop-hook.py` L130 |

> `stop_hook_active` が `True` の場合は即 exit 0。このキーが Claude Code により自動セットされることを前提とする。

### 2.5 pre-compact.py が読む入力キー

pre-compact.py は stdin JSON を読み込まない（`read_stdin_json` を import していない）。
フラグファイル（`.claude/pre-compact-fired`）とセッション状態ファイルへのファイルシステム操作のみ行う。

---

## 3. hooks — 出力 JSON のキー名

### 3.1 pre-tool-use.py の出力

| イベント | 出力 JSON | キー | 値 | file:line |
|---------|----------|------|----|-----------|
| PM 級の場合 | `hookSpecificOutput` | `hookSpecificOutput.permissionDecision` | `"ask"` | `pre-tool-use.py` L191–197 |
| PM 級の場合 | `hookSpecificOutput` | `hookSpecificOutput.permissionDecisionReason` | 説明文字列 | `pre-tool-use.py` L191–197 |
| PG/SE 級 | （出力なし） | — | — | `pre-tool-use.py` L198–199 |

出力例:
```json
{
  "hookSpecificOutput": {
    "permissionDecision": "ask",
    "permissionDecisionReason": "PM級変更です。承認してください: <target>"
  }
}
```

> **重要依存**: `hookSpecificOutput.permissionDecision` の値として `"ask"` が Claude Code のネイティブ許可ダイアログを呼び出すことを前提としている。このキー名・値の書式は公式仕様への強依存。

### 3.2 post-tool-use.py の出力

| 条件 | 出力 JSON | キー | 値 | file:line |
|------|----------|------|----|-----------|
| FAIL→PASS 遷移 | `{"systemMessage": "..."}` | `systemMessage` | 推奨メッセージ文字列 | `post-tool-use.py` L329 |
| それ以外 | （出力なし） | — | — | — |

> `systemMessage` キーが Claude Code に Claude へのシステムメッセージ注入として機能することを前提とする。

### 3.3 lam-stop-hook.py の出力

| 条件 | 出力 JSON | キー | 値 | file:line |
|------|----------|------|----|-----------|
| ループ継続 | `{"decision": "block", "reason": "..."}` | `decision` | `"block"` | `lam-stop-hook.py` L71 |
| ループ停止 | （出力なし + exit 0） | — | — | `lam-stop-hook.py` L65 |

> **重要依存**: `decision: "block"` が Stop hook からの「ブロック（継続指示）」として Claude Code に解釈されることを前提とする。

---

## 4. permissions — settings.json の書式

### 4.1 permissions ブロック構造

```json
{
  "permissions": {
    "allow": ["Bash(ls *)", "Bash(cat *)", ...],
    "deny":  ["Bash(rm *)", "Bash(rm -rf *)", ...],
    "ask":   ["Bash(find *)", "Bash(git push *)", ...]
  }
}
```

依存キー: `allow` / `deny` / `ask` の三択リスト、各要素は `"ToolName(glob_pattern)"` 書式

file:line: `.claude/settings.json` L2–67

### 4.2 パターン書式

| 書式 | 例 | 用途 |
|------|-----|------|
| `Bash(command *)` | `"Bash(ls *)"` | Bash ツールのコマンドプレフィックス一致 |
| `Bash(exact-command)` | `"Bash(pwd)"` | 完全一致 |
| `Edit\|Write\|Bash` | matchers 内 | 複数ツールの OR マッチ（settings.json hooks.matcher） |

> pre-tool-use.py L44–46 のコメント：「Claude Code は allow マッチ時に hook をスキップする場合があるため、このブラックリストチェックは二重防御として機能する」。allow 優先の挙動が変わった場合に hook の二重防御が無効化されるリスクあり。

---

## 5. sub-agents — フロントマターのキー

`.claude/agents/*.md` の全ファイルで共通して使用されるキー:

| キー | 型 | 使用例 | file:line（代表） |
|------|-----|--------|-----------------|
| `name` | string | `code-reviewer` | `agents/code-reviewer.md` L2 |
| `description` | string (multiline) | エージェント説明 | `agents/code-reviewer.md` L3–7 |
| `model` | string | `"sonnet"` | `agents/code-reviewer.md` L9 |
| `tools` | カンマ区切り string | `"Read, Grep, Glob, Bash"` | `agents/code-reviewer.md` L10 |

> `# permission-level: SE` はコメント行（L8）であり、正式なフロントマターキーではない。（推測）LAM 独自の慣習的メタデータとして記録されているが、Claude Code には解釈されない可能性がある。

確認した全エージェントのフロントマターキー一覧:

| ファイル | name | model | tools |
|---------|------|-------|-------|
| `code-reviewer.md` | code-reviewer | sonnet | Read, Grep, Glob, Bash |
| `tdd-developer.md` | tdd-developer | sonnet | Read, Glob, Grep, Write, Edit, Bash |
| `quality-auditor.md` | quality-auditor | sonnet | Read, Glob, Grep, Bash |

---

## 6. skills — フロントマターのキー

`.claude/skills/*/SKILL.md` で使用されるキー:

| キー | 型 | 使用例 | file:line（代表） |
|------|-----|--------|-----------------|
| `name` | string | `lam-orchestrate` | `skills/lam-orchestrate/SKILL.md` L2 |
| `description` | string (multiline) | スキル説明 | `skills/lam-orchestrate/SKILL.md` L3–6 |
| `version` | string | `"1.0.0"` | `skills/lam-orchestrate/SKILL.md` L7 |

> `magi/SKILL.md` と `code-reviewer.md` 等のエージェントでは `version` キーを持たないものもある。必須キーの定義が公式仕様と一致しているか要確認。

---

## 7. 環境変数

| 変数名 | 使用箇所 | 用途 | file:line |
|--------|---------|------|-----------|
| `$CLAUDE_PROJECT_DIR` | `settings.json` hooks.command | hook スクリプトへの絶対パス解決 | `settings.json` L71, 77, 82, 86, 92 |
| `LAM_PROJECT_ROOT` | `_hook_utils.py` L39 | テスト用プロジェクトルート上書き | `_hook_utils.py` L38–43 |

> `$CLAUDE_PROJECT_DIR` が Claude Code から hooks の command 文字列内で展開されることを前提とする。この変数名が変更された場合、全 hook が機能不全になる。

---

## 8. LAM が前提とする Claude Code バージョン/日付の記述

| 記述内容 | 場所 | 日付 |
|---------|------|------|
| `PreCompact` は「公式ドキュメント未掲載だが動作確認済み」 | `pre-compact.py` L8 | 2026-03時点 |
| `PostToolUse の入力に exitCode が存在しない` ことを確認 | `trust-model.md` | 2026-03-13 判明 |
| v1 hook（bash 版）から Python 移植 | `pre-tool-use.py` L5, `post-tool-use.py` L5 | 記載なし |
| `find` を v4.3.1 で ask に移動 | `docs/internal/07_SECURITY_AND_AUTOMATION.md` L17 | v4.3.1（LAM 内部バージョン） |

---

## 9. 最新仕様と突き合わせる際に特に確認すべき箇所

以下を「差分が出やすい依存ポイント」として優先的に確認すること。

### 高リスク（書式変更でLAMが即座に機能不全になる箇所）

- **PreCompact イベント**: 公式未掲載のまま使用（`pre-compact.py` L8）。正式化されたか、廃止されたか、イベント名が変わったか確認必須。

- **Stop hook の出力キー `decision: "block"`**: Claude Code が `{"decision": "block"}` を Stop hook からのブロック指示として解釈することを前提とする（`lam-stop-hook.py` L71）。このキー名/値が変更された場合、自律ループが機能しなくなる。

- **PreToolUse 出力の `hookSpecificOutput.permissionDecision: "ask"`**: PM 級ファイルへのアクセス制御の要。このキー構造が変わると権限ガードが完全に失効する（`pre-tool-use.py` L191–197）。

- **PostToolUse の `systemMessage` 出力キー**: FAIL→PASS 遷移通知に使用（`post-tool-use.py` L329）。キー名変更でTDD内省パイプラインの通知機能が失われる。

- **`stop_hook_active` 入力キー**: 再帰防止の根幹（`lam-stop-hook.py` L130）。Claude Code が自動セットしない/キー名が変わると無限再帰リスク。

- **`$CLAUDE_PROJECT_DIR` 環境変数**: 全 hook の command 文字列内で使用（`settings.json` L71, 77, 82, 86, 92）。変数名変更で全 hook が起動不能になる。

### 中リスク（動作に影響するが代替手段がある箇所）

- **`hook_event_name` フィールド**: `PostToolUseFailure` イベント判定に使用（`post-tool-use.py` L307）。存在しない場合は空文字扱いで処理が変わる（`is_failure_event=False` になりXML読取を試みる）。

- **permissions の `allow`/`deny`/`ask` 三値書式**: 他の値（例: `"prompt"` 等）への変更、または新しいキーの追加に対応できていない（`settings.json` L3–66）。

- **hooks.matcher の正規表現書式**: `"Edit|Write|Bash"` がパイプ区切りORとして解釈されることを前提とする（`settings.json` L75, 81）。

- **sub-agents フロントマターの `tools` キー**: カンマ区切りの文字列として記述されているが、リスト形式が正式書式の可能性がある（要確認）。

### 低リスク（変更しても一定期間は動作し続ける箇所）

- **`tool_name`・`tool_input`・`tool_response` の入力 JSON 構造**: これらが変わると全 hook に影響するが、Claude Code コアの後方互換性が比較的高いと思われる（推測）。

- **JUnit XML の読取（`.claude/test-results.xml`）**: プラットフォーム仕様ではなくファイル形式依存のため、Claude Code 更新の影響を受けにくい。ただし pytest 等のテストフレームワーク側の変更には注意。

---

## 付録: 依存ファイル一覧

| ファイル | プラットフォーム依存の概要 |
|---------|--------------------------|
| `.claude/settings.json` | permissions 書式・hooks ブロック書式・matcher・type: "command"・$CLAUDE_PROJECT_DIR |
| `.claude/hooks/pre-tool-use.py` | 入力: tool_name / tool_input.file_path / tool_input.command。出力: hookSpecificOutput.permissionDecision / permissionDecisionReason |
| `.claude/hooks/post-tool-use.py` | 入力: hook_event_name / tool_name / tool_input.command / tool_input.file_path。出力: systemMessage |
| `.claude/hooks/lam-stop-hook.py` | 入力: stop_hook_active。出力: decision: "block" |
| `.claude/hooks/pre-compact.py` | PreCompact イベント（公式未掲載）への依存。入力 JSON 未使用。 |
| `.claude/hooks/_hook_utils.py` | tool_name / tool_input / tool_response の入力 JSON スキーマ |
| `.claude/agents/*.md` | フロントマター: name / description / model / tools |
| `.claude/skills/*/SKILL.md` | フロントマター: name / description / version |
