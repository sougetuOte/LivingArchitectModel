# FR-3 裏取り結果（V-1〜V-8）

実施日: 2026-05-28 / 実施者: Living Architect（BUILDING フェーズ T1-0）
手段: 公式 Claude Code ドキュメント直接取得（WebFetch）＋ claude-code-guide サブエージェント補助
対象URL: `https://code.claude.com/docs/en/{hooks,sub-agents,skills,settings,model-config}`

## サマリー

| ID | 項目 | 結果 | 後続タスクへの影響 |
|---:|------|:----:|-------------------|
| V-1 | PostToolUse 入力キー | **❌ LAM が誤キー** | **T1-2 実行確定** |
| V-2 | PreCompact 公式掲載・ブロック可否 | ✅ 公式掲載・ブロック可 | T1-1 文言確定 |
| V-3 | mcp_tool hook スキーマ | ✅ 完全確認 | Wave 2 で採用候補 |
| V-4 | Windows managed-settings 廃止 | ✅ v2.1.75 で廃止（LAM 影響なし） | 影響なしを記録 |
| V-5 | xhigh effort 対応モデル | ✅ Opus 4.7 のみ | 記録のみ |
| V-6 | 公式 `memory:` 挙動 | ✅ LAM 現運用と完全一致 | **分岐(b) 採用支持** |
| V-7 | isolation: worktree / background | ✅ 採用可 | **昇格判断: 採用推奨** |
| V-8 | effort.level + 新ハンドラ | ✅ 5種類のハンドラ確認 | **昇格判断: 採用推奨** |

---

## V-1: PostToolUse 入力キー（最重要）

- **正キー**: `tool_result`（出典: hooks ドキュメント PostToolUse セクション）
- **公式スキーマ表**: `| tool_result | The result returned by the tool |`
- **公式例 JSON**（逐語引用）:
  ```json
  {
    "hook_event_name": "PostToolUse",
    "tool_name": "Bash",
    "tool_input": { "command": "npm test" },
    "tool_result": { "type": "text", "text": "✓ All tests passed (42 tests)" }
  }
  ```
- **`tool_response` は公式ドキュメントに存在しない**。リネーム履歴の明記もなし
- **LAM 現状**: [.claude/hooks/_hook_utils.py:81-89](../../../../.claude/hooks/_hook_utils.py) の `get_tool_response` が `data["tool_response"]` を参照 → **誤キー**
- **是正方針（T1-2）**: 両キー併存フォールバック（新コード優先で `tool_result`、無ければ `tool_response` を fallback。後方互換も確保）

## V-2: PreCompact

- **公式掲載済み**: hooks イベント一覧に存在「`PreCompact` — Before context compaction」
- **ブロック可否**: **可**。exit code 表に「Yes (can block) | Blocks compaction」。decision control 表にも `decision: "block"` 対応イベントとして列挙
- **LAM 現状**: [.claude/hooks/pre-compact.py:8](../../../../.claude/hooks/pre-compact.py) の「公式未掲載」注記は陳腐化
- **是正方針（T1-1）**: 「PreCompact は正式イベント（ブロック可能だが LAM は exit 0 で意図的にブロックしない）」へ書換

## V-3: mcp_tool hook スキーマ

- **type**: `"mcp_tool"`（5種類のハンドラ: `command` / `http` / `mcp_tool` / `prompt` / `agent`）
- **フィールド**:
  | Field | Required | Description |
  |-------|----------|-------------|
  | `server` | Yes | 接続済 MCP サーバー名（OAuth/接続フローは起こさない） |
  | `tool` | Yes | サーバー上のツール名 |
  | `input` | No | ツール引数。`${tool_input.file_path}` 等の substitution 可 |
- **matcher**: `mcp__<server>__<tool>` 命名規則

## V-4: Windows managed-settings パス廃止

- **廃止バージョン**: **v2.1.75**
- **逐語引用**: 「The legacy Windows path `C:\ProgramData\ClaudeCode\managed-settings.json` is no longer supported as of v2.1.75. Administrators who deployed settings to that location must migrate files to `C:\Program Files\ClaudeCode\managed-settings.json`.」
- **LAM 影響**: `.claude/settings.json` から旧パスへの直接参照なし（diff-mcp-settings.md と一致）→ **影響なし**

## V-5: xhigh effort 対応モデル

- **Opus 4.7**: `low`, `medium`, `high`, **`xhigh`**, `max`
- **Opus 4.6 / Sonnet 4.6**: `low`, `medium`, `high`, `max`（xhigh 非対応）
- **フォールバック**: xhigh を Opus 4.6 に指定 → high として実行
- **デフォルト effort**: Opus 4.7 = xhigh / Opus 4.6・Sonnet 4.6 = high（v2.1.117 以降）
- **policyHelper**: v2.1.136 で導入 / **disableRemoteControl**: v2.1.128 で導入
- **worktree.baseRef**: default = `"fresh"`（branches from `origin/<default-branch>`）

## V-6: 公式 `memory:` 挙動（Memory Policy 分岐の核）

- **frontmatter キー**: `memory: user | project | local`
- **保存パス**:
  - `user` → `~/.claude/agent-memory/<name>/`
  - **`project` → `.claude/agent-memory/<name>/`** ← **LAM 現運用パスと完全一致**
  - `local` → `.claude/agent-memory-local/<name>/`
- **挙動**:
  - サブエージェントの system prompt に memory directory への読み書き指示が自動注入される
  - `MEMORY.md` の先頭 200行 or 25KB が system prompt に含まれる（超過時は subagent がキュレーション）
  - Read/Write/Edit ツールが自動有効化
- **既存ファイルの扱い**: プラットフォームが自動上書き/追記する仕組みは無く、**subagent 自身が読み書きをキュレーションする**（LAM の自前運用と同じセマンティクス）
- **公式推奨**: 「`project` is the recommended default scope」
- **結論**: LAM 想定と一致。**分岐(b) = 公式機構への移行を採用** することを推奨

## V-7: isolation: worktree / background

- **`isolation: worktree`**:
  - 一時的な git worktree でサブエージェントを実行（隔離されたリポジトリのコピー）
  - デフォルトで **parent の HEAD ではなく default branch から分岐**
  - サブエージェントが変更を加えなかった場合は worktree を自動クリーンアップ
- **`background: true`**:
  - サブエージェントを常にバックグラウンド実行
  - 既にセッション内で付与された権限で実行、プロンプトが必要なツール呼び出しは**自動拒否**
  - clarifying question が必要な場合、その tool 呼び出しは失敗するが subagent は続行
- **採用判断**: 並列レビュー系エージェント（code-reviewer 等）で有用。**RQ-2 低 → 採用推奨に昇格**

## V-8: effort.level + 新 hook ハンドラ

- **effort.level**:
  - 入力フィールド: `effort` オブジェクトの `level` フィールドに `"low"|"medium"|"high"|"xhigh"|"max"` が入る
  - **対応イベント**: `PreToolUse`, `PostToolUse`, `Stop`, `SubagentStop`
  - 要求 effort > モデル対応 effort の場合は実際にダウングレードされた値が入る
- **新ハンドラ 5種類**: `command` / `http` / `mcp_tool` / `prompt`（LLM 判定）/ `agent`（subagent 検証、experimental）
- **総イベント数**: 30種類（SessionStart, Setup, UserPromptSubmit, UserPromptExpansion, PreToolUse, PermissionRequest, PermissionDenied, PostToolUse, PostToolUseFailure, PostToolBatch, Notification, MessageDisplay, SubagentStart, SubagentStop, TaskCreated, TaskCompleted, Stop, StopFailure, TeammateIdle, InstructionsLoaded, ConfigChange, CwdChanged, FileChanged, WorktreeCreate, WorktreeRemove, PreCompact, PostCompact, Elicitation, ElicitationResult, SessionEnd）
- **採用判断**: effort.level は PG コマンド判定や TDD 内省パイプラインに統合する価値あり。**RQ-2 低 → 採用推奨に昇格**

---

## T1-0 完了判定

- ✅ SC-2 達成（V-1〜V-8 全件にラベル付与済み）
- ✅ V-1・V-2・V-6 が確定（後続 T1-* のブロック解除）
- ✅ FR-3.2 順守（未確認項目なし、推測実装なし）

## 後続タスクへの引き継ぎ

- **T1-1（PG）**: V-2 確定済 → 即実行可能
- **T1-2（SE）**: V-1 = `tool_result` 正 → **両キー併存フォールバック実装**を採用（FR-2.2 発動）
- **T1-3（PM承認ゲート）**: V-6 結果 = LAM 想定と一致 → **分岐(b) を推奨**としてユーザーに提示
- **T2-5 / T2-6（昇格判断）**: V-7・V-8 ともに採用可・効果大 → **優先度を「中」へ昇格** を推奨
