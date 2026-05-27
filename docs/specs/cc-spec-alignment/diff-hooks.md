# Hooks 差分マッピング — LAM 現行実装 vs 公式最新仕様

**作成日**: 2026-05-27  
**フェーズ**: PLANNING（文書作成のみ。コード修正・コード生成を含まない）  
**担当**: 差分マッピング担当（Hooks 領域）

---

## 対象範囲

LAM の Hooks 実装全体（5スクリプト + settings.json の hooks ブロック）を対象とする。

- `.claude/hooks/pre-tool-use.py`
- `.claude/hooks/post-tool-use.py`
- `.claude/hooks/lam-stop-hook.py`
- `.claude/hooks/pre-compact.py`
- `.claude/hooks/_hook_utils.py`
- `.claude/settings.json`（hooks ブロック）

サブエージェント・スキル・permissions・MCP は別文書の管轄とし、本文書では扱わない。

---

## 入力資料

| 番号 | ファイル | 役割 |
|------|---------|------|
| 10 | `docs/artifacts/research/2026-05-27-cc-spec-survey/10-lam-current-dependencies.md` | LAM 現行依存インベントリ |
| 20 | `docs/artifacts/research/2026-05-27-cc-spec-survey/20-anthropic-official-spec.md` | Claude Code 公式仕様サーベイ（2026-05-27 取得） |
| 50 | `docs/artifacts/research/2026-05-27-cc-spec-survey/50-verification.md` | 高リスク依存の公式逐語引用検証 |
| — | `.claude/hooks/*.py` / `.claude/settings.json` | 現物確認 |

---

## 差分分類表

### 凡例

| 分類記号 | 意味 |
|---------|------|
| ◎ 現状維持で安全 | 公式仕様と乖離なし。変更不要。 |
| ○ 新機能で改善可 | 公式に新機能/新フィールドがあり LAM が未活用。採用是非は後続の requirements フェーズで判断。 |
| △ 要更新 | 非推奨・破壊的変更・記述陳腐化など、放置するとリスクまたは不正確な箇所。 |

---

### 分類表

| # | 項目 | 現行 LAM の状態 | 最新公式仕様（2026-05-27） | 分類 | 根拠/出典 | LAM 影響箇所 |
|---|------|---------------|--------------------------|------|----------|-------------|
| H-01 | PreCompact イベント登録 | `settings.json` L91–94 に登録済み。動作中。 | 公式 27 イベントの一つとして正式掲載。入力スキーマ（`trigger`, `custom_instructions`）も公式定義済み。 | ◎ 現状維持で安全 | 50-verification.md A-1 | `.claude/settings.json` L91–94 |
| H-02 | `pre-compact.py` L8 の「公式未掲載」注記 | `# NOTE: PreCompact は公式ドキュメント未掲載だが動作確認済み（2026-03時点）` というコメントが残存。 | PreCompact は公式 27 イベントの一つとして明示掲載済み（50-verification.md A-1）。注記内容が事実と相違している。 | △ 要更新 | 50-verification.md A-1 | `.claude/hooks/pre-compact.py` L8 |
| H-03 | PreCompact 入力 JSON の読み込み | `pre-compact.py` は stdin JSON を一切読み込まない（`read_stdin_json` 未 import）。フラグファイル操作のみ。 | 公式入力スキーマに `trigger: "manual\|auto"` と `custom_instructions` が存在し、活用可能。現状の非読み込みは動作的には問題なし。 | ○ 新機能で改善可 | 20-spec.md §1.2 PreCompact 入力スキーマ | `.claude/hooks/pre-compact.py` |
| H-04 | Stop hook 出力 `{"decision": "block", "reason": ...}` | `lam-stop-hook.py` L71 で使用中。 | `decision: "block"` は現行仕様で明示定義。書式変更なし。 | ◎ 現状維持で安全 | 50-verification.md A-2 | `.claude/hooks/lam-stop-hook.py` L71 |
| H-05 | Stop hook 入力 `stop_hook_active` | `lam-stop-hook.py` L130 で読み込み、再帰防止に使用。 | 公式 Stop 入力スキーマに `stop_hook_active: bool` として明示定義。Python SDK 型定義でも確認済み。 | ◎ 現状維持で安全 | 50-verification.md A-4 | `.claude/hooks/lam-stop-hook.py` L130 |
| H-06 | Stop hook 入力の `background_tasks` / `session_crons` フィールド | 現行 LAM では読み込んでいない。 | 公式 Stop 入力スキーマに `background_tasks[]` / `session_crons[]` が追加されている（各要素に id, type, status, description 等）。 | ○ 新機能で改善可 | 20-spec.md §1.2 Stop 入力スキーマ | `.claude/hooks/lam-stop-hook.py` |
| H-07 | PreToolUse 出力 `hookSpecificOutput.permissionDecision` の値 | `pre-tool-use.py` L191–197 で `"ask"` のみを使用。 | `permissionDecision` の有効値が `"allow"\|"deny"\|"ask"\|"defer"` の4値。既存の `"ask"` は引き続き有効。`"defer"`（通常許可フローに委ねる）が追加された。 | ◎ 現状維持で安全（注記あり） | 50-verification.md A-3 | `.claude/hooks/pre-tool-use.py` L191–197 |
| H-08 | PreToolUse 出力の `additionalContext` / `updatedInput` フィールド | 現行 LAM では出力していない。 | 公式 PreToolUse hookSpecificOutput に `additionalContext: string`（Claude へのコンテキスト追加）と `updatedInput: {}`（ツール入力の書き換え）が定義されている。 | ○ 新機能で改善可 | 20-spec.md §1.3 PreToolUse 決定出力 | `.claude/hooks/pre-tool-use.py` |
| H-09 | PostToolUse 出力 `systemMessage` | `post-tool-use.py` L329 で使用。FAIL→PASS 遷移通知に使用中。 | 全イベント共通出力フィールドに `systemMessage: string` が明示定義。書式変更なし。 | ◎ 現状維持で安全 | 20-spec.md §1.3 全イベント共通出力 | `.claude/hooks/post-tool-use.py` L329 |
| H-10 | PostToolUse 出力の `hookSpecificOutput.updatedToolOutput` / `additionalContext` | 現行 LAM では出力していない。 | 公式 PostToolUse hookSpecificOutput に `additionalContext` と `updatedToolOutput`（旧 `updatedMCPToolOutput` は deprecated）が定義されている。 | ○ 新機能で改善可 | 20-spec.md §1.3 PostToolUse 出力 | `.claude/hooks/post-tool-use.py` |
| H-11 | `$CLAUDE_PROJECT_DIR` 環境変数 | `settings.json` L71, 77, 82, 86, 92 の全 hook command で使用。 | 公式環境変数一覧表に `CLAUDE_PROJECT_DIR: Project root directory` として明示掲載。MCP ドキュメントでも同一変数名を確認。 | ◎ 現状維持で安全 | 50-verification.md A-5 | `.claude/settings.json` L71, 77, 82, 86, 92 |
| H-12 | hooks の `type: "command"` ハンドラ | 全 hook で `type: "command"` を使用。 | 5種類のハンドラタイプ（`command` / `http` / `mcp_tool` / `prompt` / `agent`）のうち `command` は引き続き有効。 | ◎ 現状維持で安全 | 20-spec.md §1.4 Hook ハンドラタイプ一覧 | `.claude/settings.json` L71, 77, 82, 86, 92 |
| H-13 | hooks ハンドラの `type: "http"` | LAM 未使用。 | 公式に `type: "http"`（HTTP POST リクエスト）が正式サポート。`allowedHttpHookUrls` / `httpHookAllowedEnvVars` で制御可能。 | ○ 新機能で改善可 | 20-spec.md §1.4 Hook ハンドラタイプ / settings §2.2 | — |
| H-14 | hooks ハンドラの `type: "mcp_tool"` | LAM 未使用。 | 公式に `type: "mcp_tool"`（接続済み MCP サーバーのツール呼び出し）が正式サポート。`server` / `tool` / `input` フィールドで設定。 | ○ 新機能で改善可 | 50-verification.md B-10 / 20-spec.md §1.4 | — |
| H-15 | hooks ハンドラの `type: "prompt"` | LAM 未使用。 | 公式に `type: "prompt"`（LLM による hook 評価）が正式サポート。`prompt` / `model` / `timeout` で設定。Stop hook での利用例が公式ガイドに掲載。 | ○ 新機能で改善可 | 50-verification.md B-10 / 20-spec.md §1.4 | — |
| H-16 | hooks ハンドラの `type: "agent"` | LAM 未使用。 | 公式に `type: "agent"`（サブエージェントによる hook 評価）が正式サポート。`prompt` / `timeout` / `statusMessage` で設定。 | ○ 新機能で改善可 | 50-verification.md B-10 / 20-spec.md §1.4 | — |
| H-17 | 入力 JSON の `effort.level` フィールド | 現行 LAM では読み込んでいない。 | `PreToolUse` / `PostToolUse` / `Stop` 等のツール実行コンテキストイベントの共通入力に `effort.level: "low\|medium\|high\|xhigh\|max"` が存在。環境変数 `CLAUDE_EFFORT` でもアクセス可能。 | ○ 新機能で改善可 | 50-verification.md B-10 / 20-spec.md §1.2 PreToolUse 入力 | `.claude/hooks/pre-tool-use.py` / `post-tool-use.py` / `lam-stop-hook.py` |
| H-18 | 入力 JSON の `tool_use_id` フィールド | 現行 LAM では読み込んでいない。 | `PreToolUse` / `PostToolUse` 等に `tool_use_id: string` が存在。ツール呼び出しの一意識別に使用可能。 | ○ 新機能で改善可 | 20-spec.md §1.2 PreToolUse 入力 / PostToolUse 入力 | `.claude/hooks/_hook_utils.py` |
| H-19 | `hook_event_name` 入力フィールド | `post-tool-use.py` L307 で `data.get("hook_event_name", "")` として読み込み、`PostToolUseFailure` 判定に使用。 | 全イベント共通入力フィールドに `hook_event_name: string` として定義済み。書式変更なし。 | ◎ 現状維持で安全 | 20-spec.md §1.2 全イベント共通フィールド | `.claude/hooks/post-tool-use.py` L307 |
| H-20 | `tool_name` / `tool_input` / `tool_response` 入力キー構造 | `_hook_utils.py` L65–89 で `tool_name` / `tool_input` を読み込み。`tool_response` も定義済み。 | `tool_name` / `tool_input` は PreToolUse・PostToolUse の公式スキーマに定義。PostToolUse の `tool_result` は `tool_response` ではなく `tool_result` キー名で掲載されている点に注意（現行は `get_tool_response` 関数が `tool_response` キーを参照）。 | △ 要更新（調査要） | 20-spec.md §1.2 PostToolUse 入力（`"tool_result"` キー名を掲載） | `.claude/hooks/_hook_utils.py` L81–89 |
| H-21 | settings.json hooks ブロックの基本書式 | `hooks > EventName > [{matcher, hooks: [{type, command}]}]` 構造を使用。 | 公式書式と完全一致（matcher, type, command 全て有効）。 | ◎ 現状維持で安全 | 20-spec.md §1.4 | `.claude/settings.json` L68–95 |
| H-22 | hooks コマンドの追加フィールド（`args`, `async`, `shell`, `timeout`, `statusMessage`, `if`, `once`） | LAM では使用していない（`type` と `command` のみ指定）。 | 公式で `args: []` / `async: bool` / `asyncRewake: bool` / `shell: bash\|powershell` / `timeout: int` / `statusMessage: string` / `if: permission_rule` / `once: bool` が定義済み。 | ○ 新機能で改善可 | 20-spec.md §1.4 settings.json での Hooks 設定ブロック書式 | `.claude/settings.json` L68–95 |
| H-23 | `disableAllHooks` 設定キー | LAM の settings.json に未設定（デフォルト動作）。 | 公式に `"disableAllHooks": false` が定義されており、全 hook を一括無効化するトグルとして機能。 | ○ 新機能で改善可 | 20-spec.md §1.4 | `.claude/settings.json` |
| H-24 | 全イベント共通出力の `terminalSequence` フィールド | 現行 LAM では使用していない。 | 全イベント共通出力に `terminalSequence: string` が追加。OSC 0/1/2/9/99/777, BEL 等のターミナル通知シーケンスを出力できる新フィールド。 | ○ 新機能で改善可 | 20-spec.md §1.3 全イベント共通出力 / §7.1 | — |
| H-25 | 全イベント共通出力の `suppressOutput` / `continue` フィールド | 現行 LAM では使用していない。 | 全イベント共通出力に `continue: bool` / `suppressOutput: bool` / `stopReason: string` が定義済み。 | ○ 新機能で改善可 | 20-spec.md §1.3 全イベント共通出力 | — |
| H-26 | 新イベント群（LAM 未登録）— `SessionStart`, `SessionEnd`, `UserPromptSubmit` 等 | 27 イベントのうち LAM が登録しているのは 5 つのみ（`PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `Stop`, `PreCompact`）。 | 22 イベントが未使用。代表的な未使用イベント: `SessionStart`, `SessionEnd`, `StopFailure`, `UserPromptSubmit`, `PostToolBatch`, `PermissionRequest`, `PermissionDenied`, `SubagentStart`, `SubagentStop`, `InstructionsLoaded`, `PostCompact`, `Elicitation`, `WorktreeCreate`, `WorktreeRemove`, `FileChanged`, `ConfigChange`, `CwdChanged`, `TaskCreated`, `TaskCompleted`, `TeammateIdle`, `Notification`, `Setup`, `UserPromptExpansion` | ○ 新機能で改善可 | 20-spec.md §1.1 対応イベント一覧 | `.claude/settings.json` |
| H-27 | `CLAUDE_ENV_FILE` 環境変数（hook 間永続化） | LAM では未使用。 | 公式に `CLAUDE_ENV_FILE` が追加。hook をまたぐ環境変数の永続化が可能。 | ○ 新機能で改善可 | 20-spec.md §7.1 | — |
| H-28 | `asyncRewake` フィールド | LAM では未使用。 | `asyncRewake: bool` — バックグラウンド hook が終了コード 2 を返したとき Claude を再起動するトリガー。 | ○ 新機能で改善可 | 20-spec.md §7.1 / §1.4 | — |

---

## 分類ごとの小計

| 分類 | 件数 |
|------|------|
| ◎ 現状維持で安全 | 10 件（H-01, H-04, H-05, H-07, H-09, H-11, H-12, H-19, H-20 注, H-21） |
| ○ 新機能で改善可 | 16 件（H-03, H-06, H-08, H-10, H-13, H-14, H-15, H-16, H-17, H-18, H-22, H-23, H-24, H-25, H-26, H-27, H-28） |
| △ 要更新 | 2 件（H-02, H-20） |

> H-07（`permissionDecision` の値）は `"ask"` が引き続き有効なため「現状維持で安全」とした。ただし `"defer"` 追加という仕様拡張を知った上で意図的に選択しているか確認することを推奨する。

---

## 「要更新」項目の詳細

### △ H-02: `pre-compact.py` L8 の「公式未掲載」注記

**影響度: 低**

**現状**: `pre-compact.py` L8 に以下のコメントが存在する。
```python
# NOTE: PreCompact は公式ドキュメント未掲載だが動作確認済み（2026-03時点）
```

**最新公式仕様**: PreCompact は 2026-05-27 時点の公式ドキュメントにおいて 27 イベントのうちの 1 つとして正式掲載済み。公式入力スキーマ（`trigger: "manual|auto"`, `custom_instructions`）も定義されている。

**なぜ更新が必要か**: コメントの記述が事実と相違しており、将来の開発者（または Claude Code 自身）がこのファイルを読んだ際に誤解を生む。動作への影響はないが、設計ドキュメントとしての正確性を損なう。

**推奨対応**: L8 の注記を「正式サポートのイベントであり、入力スキーマには `trigger`・`custom_instructions` が存在する（現在は未使用）」に書き換える。

---

### △ H-20: `_hook_utils.py` の `tool_response` キー名と公式の `tool_result` の不一致（要調査）

**影響度: 中**

**現状**: `_hook_utils.py` L81–89 の `get_tool_response` 関数は入力 JSON から `tool_response` キーを読み込んでいる。

**最新公式仕様**: 公式 PostToolUse 入力スキーマのサンプルには `"tool_result": "string"` として掲載されている（20-spec.md §1.2 PostToolUse 入力）。

**懸念点**: `tool_response`（LAM）と `tool_result`（公式サンプル）のどちらが正式なキー名か確定的な公式一次情報が確認できていない（50-verification.md では当該項目の逐語検証が実施されていない）。現在の LAM では PostToolUse 処理で `tool_response` は主要なフローに使われておらず、現時点では動作影響は低いと推定される。しかし、将来的に tool の出力を参照する機能を追加する場合に問題となる。

**推奨対応**: 次回の公式仕様確認時（Upstream First 原則に基づく）に `tool_result` が正式キー名であることを逐語確認する。確定後、`_hook_utils.py` の `get_tool_response` 関数と関連呼び出し箇所を修正する。

---

## 補足: 「改善可」の主な新機能カテゴリ

本表は採否を判断せず、「こういう機能がある」という事実列挙に留める。採否は後続の requirements フェーズで扱う。

### 1. Stop hook への新しい入力情報（H-06）
`background_tasks[]` / `session_crons[]` により、バックグラウンドタスクやセッション内クローンの状態を Stop 時に参照できる。

### 2. PreToolUse の入力書き換え能力（H-08）
`hookSpecificOutput.updatedInput` でツールへの入力を hook が書き換えて渡せる。

### 3. 3種の新しい hook ハンドラタイプ（H-13, H-14, H-15, H-16）
- `http`: 外部 webhook 連携
- `mcp_tool`: 接続済み MCP サーバーのツール呼び出し
- `prompt`: LLM による hook 判定
- `agent`: サブエージェントによる hook 判定

### 4. エフォートレベルへのアクセス（H-17）
`effort.level` / 環境変数 `CLAUDE_EFFORT` で現在のエフォートレベルを参照でき、処理の軽重を動的に切り替えられる。

### 5. ターミナル通知（H-24）
`terminalSequence` で OSC シーケンスを出力し、ターミナルのタイトルバー変更・ベル通知等が可能。

### 6. 22 の未登録イベント群（H-26）
`StopFailure`（API エラー種別）、`PermissionRequest`/`PermissionDenied`（権限制御の精細化）、`SubagentStart`/`SubagentStop`（サブエージェントライフサイクル）、`PostCompact`（圧縮後処理）などが新たに利用可能。

---

*本文書は PLANNING フェーズの成果物。コード修正・テストコードを含まない。*  
*次工程: 各「要更新」・「改善可」項目について requirements フェーズで採否を決定すること。*
