# Claude Code GitHub リリース調査レポート

**調査期間**: 2026-03-31 〜 2026-05-27  
**調査日**: 2026-05-27  
**調査手法**: `gh release view --repo anthropics/claude-code` (gh CLI 直接取得)  
**対象バージョン**: v2.1.89 〜 v2.1.150  

---

## 1. バージョン別変更点（時系列）

### v2.1.89 (2026-04-01)

| カテゴリ | 変更内容 |
|---------|---------|
| Hooks | `PreToolUse` フックに `"defer"` 判断を追加。ヘッドレスセッションがツール呼び出しで一時停止し、`-p --resume` で再評価 |
| Hooks | `PermissionDenied` フック追加：auto モードの分類拒否後に発火。`{retry: true}` を返すと再試行指示 |
| Hooks | `PreToolUse` フックが stdout に JSON を出力してコード2で終了するとツール呼び出しを正しくブロックしない問題を修正 |
| Permissions | `Edit(//path/**)` / `Read(//path/**)` の allow ルールがシンボリックリンクの解決先を確認するよう修正 |
| MCP | `MCP_CONNECTION_NONBLOCKING=true` で `-p` モード時 MCP 接続待ちをスキップ、`--mcp-config` のサーバー接続を最大5秒に制限 |
| MCP | MCP ツールエラーがマルチ要素エラーコンテンツの最初のブロックのみに切り詰められる問題を修正 |
| Sub-agents | 名前付きサブエージェントが `@` メンション先読みに表示 |

**出典**: https://github.com/anthropics/claude-code/releases/tag/v2.1.89

---

### v2.1.90 (2026-04-02)

| カテゴリ | 変更内容 |
|---------|---------|
| Hooks | `PreToolUse` フックが JSON を stdout に出力してコード2で終了してもブロックされない問題を修正 |
| Settings | `permissions.defaultMode: "auto"` の JSON スキーマ検証を修正 (v2.1.91) |
| Settings | `.husky` を保護ディレクトリに追加 |

**出典**: https://github.com/anthropics/claude-code/releases/tag/v2.1.90

---

### v2.1.91 (2026-04-03)

| カテゴリ | 変更内容 |
|---------|---------|
| MCP | MCP ツール結果の永続化オーバーライド：`_meta["anthropic/maxResultSizeChars"]` アノテーション（最大500K）で大きな結果（DBスキーマ等）を切り詰めなしに通過 |
| Settings | `disableSkillShellExecution` 設定追加：スキル・カスタムスラッシュコマンド・プラグインコマンドでのインラインシェル実行を無効化 |
| Skills | スキル/プラグインのシェル実行を制御する新設定 |

**出典**: https://github.com/anthropics/claude-code/releases/tag/v2.1.91

---

### v2.1.92 (2026-04-04)

| カテゴリ | 変更内容 |
|---------|---------|
| Settings | `forceRemoteSettingsRefresh` ポリシー設定追加：設定でリモートマネージド設定の新鮮取得を強制（フェイルクローズ） |
| Hooks | Stop フックが小型高速モデルの `ok:false` 返却で誤って失敗する問題を修正。`preventContinuation:true` のセマンティクスを復元 |

**出典**: https://github.com/anthropics/claude-code/releases/tag/v2.1.92

---

### v2.1.94 (2026-04-08)

| カテゴリ | 変更内容 |
|---------|---------|
| Hooks | プラグインスキルフックの YAML フロントマター定義が黙って無視される問題を修正 |
| Hooks | `CLAUDE_PLUGIN_ROOT` 未設定時にプラグインフックが失敗する問題を修正 |
| Skills | `hookSpecificOutput.sessionTitle` を `UserPromptSubmit` フックに追加（セッションタイトル設定） |
| Skills | `"skills": ["./"]` で宣言したプラグインスキルがディレクトリ名ではなくスキルのフロントマター `name` を使用するよう変更 |
| Skills | `keep-coding-instructions` フロントマターフィールドサポート追加 |

**出典**: https://github.com/anthropics/claude-code/releases/tag/v2.1.94

---

### v2.1.97 (2026-04-09)

| カテゴリ | 変更内容 |
|---------|---------|
| Settings | `refreshInterval` ステータスライン設定追加：N秒ごとにステータスラインコマンドを再実行 |
| Settings | `workspace.git_worktree` をステータスラインの JSON 入力に追加 |
| Settings | `permissions.additionalDirectories` の変更がセッション途中で適用されるよう修正 |
| Permissions | `--dangerously-skip-permissions` が保護パスへの書き込みを承認後に accept-edits モードに静かにダウングレードされる問題を修正 |
| Permissions | マネージドセッション allow ルールがプロセス再起動まで有効なまま残る問題を修正 |
| MCP | MCP HTTP/SSE 接続が再接続時に ~50 MB/hr のバッファを解放しないメモリリーク修正 |
| MCP | MCP OAuth `oauth.authServerMetadataUrl` がトークンリフレッシュ後に尊重されない問題を修正 |

**出典**: https://github.com/anthropics/claude-code/releases/tag/v2.1.97

---

### v2.1.98 (2026-04-09)

| カテゴリ | 変更内容 |
|---------|---------|
| Settings | `CLAUDE_CODE_PERFORCE_MODE` 環境変数追加：読み取り専用ファイルへの Edit/Write/NotebookEdit で `p4 edit` ヒントを出して失敗 |
| Hooks | `CLAUDE_PROJECT_DIR` が Bash ツールサブプロセスに渡されるよう（OTEL トレーシング有効時） |
| Permissions | Bash ツールのバックスラッシュエスケープフラグによる権限バイパスを修正 |
| Permissions | 複合 Bash コマンドが強制権限プロンプトをバイパスする問題を修正 |
| Permissions | `/dev/tcp/...` や `/dev/udp/...` へのリダイレクトが自動承認される問題を修正 |
| MCP | LSP: `clientInfo` を初期化リクエストで言語サーバーに送信するよう変更 |

**出典**: https://github.com/anthropics/claude-code/releases/tag/v2.1.98

---

### v2.1.101 (2026-04-11)

| カテゴリ | 変更内容 |
|---------|---------|
| Settings | Hooks: 不認識のフックイベント名が `settings.json` 全体を無視させる問題を修正（設定ファイルの弾力性向上） |
| Settings | マネージド設定で強制有効化されたプラグインのフックが `allowManagedHooksOnly` 設定時に動作するよう改善 |

**出典**: https://github.com/anthropics/claude-code/releases/tag/v2.1.101

---

### v2.1.105 (2026-04-14)

| カテゴリ | 変更内容 |
|---------|---------|
| Hooks | **PreCompact フック対応追加**: フックがコード2で終了または `{"decision":"block"}` を返すことでコンパクションをブロック可能 |
| Sub-agents | プラグインのバックグラウンドモニター対応：トップレベルの `monitors` マニフェストキーでセッション開始時に自動アーム |
| MCP | `EnterWorktree` ツールに `path` パラメータ追加（既存ワークツリーに切り替え） |

**出典**: https://github.com/anthropics/claude-code/releases/tag/v2.1.105

---

### v2.1.108 (2026-04-14)

| カテゴリ | 変更内容 |
|---------|---------|
| Settings | `ENABLE_PROMPT_CACHING_1H` 環境変数追加：1時間プロンプトキャッシュ TTL にオプトイン。`ENABLE_PROMPT_CACHING_1H_BEDROCK` は**非推奨**（後方互換あり） |
| Skills | モデルが `/init`, `/review`, `/security-review` などの組み込みスラッシュコマンドを Skill ツール経由で実行可能に |

**出典**: https://github.com/anthropics/claude-code/releases/tag/v2.1.108

---

### v2.1.111 (2026-04-16)

| カテゴリ | 変更内容 |
|---------|---------|
| Settings | Auto モードが `--enable-auto-mode` なしで利用可能（フラグ廃止） |
| Skills | `/less-permission-prompts` スキル追加（後の `fewer-permission-prompts` に相当）：transcript からの読み取り専用 Bash/MCP コールをスキャンして allowlist 候補を `.claude/settings.json` に提案 |
| Permissions | 読み取り専用 bash コマンドのグロブパターン（`ls *.ts`）と `cd <project-dir> &&` 始まりのコマンドが権限プロンプトを出さないよう変更 |

**出典**: https://github.com/anthropics/claude-code/releases/tag/v2.1.111

---

### v2.1.113 (2026-04-17)

| カテゴリ | 変更内容 |
|---------|---------|
| Settings | `sandbox.network.deniedDomains` 設定追加：広範な `allowedDomains` ワイルドカードが許可する場合でも特定ドメインをブロック |
| Permissions | **セキュリティ**: Bash deny ルールが `env`/`sudo`/`watch`/`ionice`/`setsid` などの exec ラッパーでラップされたコマンドにマッチするよう強化 |
| Permissions | **セキュリティ**: `Bash(find:*)` allow ルールが `find -exec`/`-delete` を自動承認しないよう修正 |
| Permissions | **セキュリティ**: macOS で `/private/{etc,var,tmp,home}` パスが `Bash(rm:*)` allow ルール下の危険な削除ターゲットとして扱われるよう変更 |
| MCP | ネイティブビルド（macOS/Linux）で `Glob` と `Grep` ツールが組み込みの `bfs` と `ugrep` で置換（Bash ツール経由） |

**出典**: https://github.com/anthropics/claude-code/releases/tag/v2.1.113

---

### v2.1.116 (2026-04-21)

| カテゴリ | 変更内容 |
|---------|---------|
| Sub-agents | Agent フロントマター `hooks:` が `--agent` での main-thread agent 実行時にも発火するよう修正 |
| Permissions | **セキュリティ**: サンドボックスの自動許可が `rm`/`rmdir` を `/`, `$HOME` などのクリティカルディレクトリに向けた場合に危険パス安全チェックをバイパスしないよう修正 |

**出典**: https://github.com/anthropics/claude-code/releases/tag/v2.1.116

---

### v2.1.117 (2026-04-22)

| カテゴリ | 変更内容 |
|---------|---------|
| MCP | Agent フロントマター `mcpServers` が `--agent` での main-thread agent セッションで読み込まれるよう修正 |
| Sub-agents | フォーク型サブエージェントを外部ビルドで `CLAUDE_CODE_FORK_SUBAGENT=1` で有効化可能 |

**出典**: https://github.com/anthropics/claude-code/releases/tag/v2.1.117

---

### v2.1.118 (2026-04-23)

| カテゴリ | 変更内容 |
|---------|---------|
| Hooks | **Hooks から MCP ツール直接呼び出し可能**: `type: "mcp_tool"` で MCP ツールを呼び出し可能 |
| Settings | `DISABLE_UPDATES` 環境変数追加：手動 `claude update` を含む全アップデートパスをブロック（`DISABLE_AUTOUPDATER` より厳格） |
| Settings | WSL が `wslInheritsWindowsSettings` ポリシーキーで Windows 側のマネージド設定を継承可能 |
| Settings | Auto mode: `autoMode.allow`, `autoMode.soft_deny`, `autoMode.environment` に `"$defaults"` を含めることで組み込みリストに追加（置換でなく） |

**出典**: https://github.com/anthropics/claude-code/releases/tag/v2.1.118

---

### v2.1.119 (2026-04-24)

| カテゴリ | 変更内容 |
|---------|---------|
| Settings | `/config` の設定（テーマ、エディタモード等）が `~/.claude/settings.json` に永続化され、プロジェクト/ローカル/ポリシーの上書き優先順位に参加 |
| Settings | `prUrlTemplate` 設定追加：フッター PR バッジのカスタム URL |
| Hooks | **`PostToolUse` と `PostToolUseFailure` フック入力に `duration_ms` 追加**（ツール実行時間、権限プロンプトと PreToolUse フックを除く） |
| Permissions | `--print` モードが agent の `tools:` と `disallowedTools:` フロントマターを尊重 |
| Permissions | `--agent <name>` が agent 定義の `permissionMode` を尊重 |

**出典**: https://github.com/anthropics/claude-code/releases/tag/v2.1.119

---

### v2.1.121 (2026-04-28)

| カテゴリ | 変更内容 |
|---------|---------|
| MCP | `alwaysLoad` オプションを MCP サーバー設定に追加：`true` のとき全ツールがツール検索の遅延をスキップして常時利用可能 |
| Hooks | `PostToolUse` フックが全ツールに対して `hookSpecificOutput.updatedToolOutput` でツール出力を置換可能（以前は MCP のみ） |
| Skills | `skillOverrides` 設定が機能するよう修正：`off`, `user-invocable-only`, `name-only` |

**出典**: https://github.com/anthropics/claude-code/releases/tag/v2.1.121

---

### v2.1.128 (2026-05-05)

| カテゴリ | 変更内容 |
|---------|---------|
| MCP | `workspace` が MCP の予約済みサーバー名に。既存の同名サーバーは警告付きでスキップ |
| MCP | 再接続する MCP サーバーが毎回全ツール名リストをフラッドしないよう変更（サーバープレフィックスでサマリー化） |

**出典**: https://github.com/anthropics/claude-code/releases/tag/v2.1.128

---

### v2.1.129 (2026-05-06)

| カテゴリ | 変更内容 |
|---------|---------|
| Skills | `skillOverrides` 設定が機能するよう修正 |
| Plugins | プラグインマニフェスト: `themes` と `monitors` は `"experimental": { ... }` 下に宣言すべきに変更（トップレベルは動作するが `claude plugin validate` が警告） |
| Settings | Gateway `/v1/models` 探索が opt-in に変更（`CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1`、v2.1.126-128 は自動だった） |

**出典**: https://github.com/anthropics/claude-code/releases/tag/v2.1.129

---

### v2.1.132 (2026-05-07)

| カテゴリ | 変更内容 |
|---------|---------|
| Hooks | `CLAUDE_CODE_SESSION_ID` 環境変数を Bash ツールのサブプロセス環境に追加（フックに渡される `session_id` と一致） |

**出典**: https://github.com/anthropics/claude-code/releases/tag/v2.1.132

---

### v2.1.133 (2026-05-08)

| カテゴリ | 変更内容 |
|---------|---------|
| Settings | `worktree.baseRef` 設定追加（`fresh` | `head`）：`--worktree`, `EnterWorktree`, エージェント隔離ワークツリーのブランチ元を選択。**デフォルト `fresh` が `EnterWorktree` のベースを `origin/<default>` に変更**（v2.1.128 から local HEAD だったものを戻す。unpushed コミットを保持するには `head` を設定） |
| Settings | `sandbox.bwrapPath` と `sandbox.socatPath` マネージド設定追加（Linux/WSL） |
| Settings | `parentSettingsBehavior` 管理者ティアキー追加（`'first-wins' | 'merge'`）：SDK `managedSettings`（親ティア）のポリシーマージをオプトイン |
| Hooks | **フック入力に `effort.level` フィールドと `$CLAUDE_EFFORT` 環境変数を追加**（アクティブな effort レベルを受信） |

**出典**: https://github.com/anthropics/claude-code/releases/tag/v2.1.133

---

### v2.1.136 (2026-05-09)

| カテゴリ | 変更内容 |
|---------|---------|
| Settings | `settings.autoMode.hard_deny` 追加：ユーザー意図や allow 例外にかかわらず無条件でブロックする auto mode 分類ルール |
| MCP | `.mcp.json`、プラグイン、claude.ai コネクタで設定された MCP サーバーが VS Code 拡張・JetBrains プラグイン・Agent SDK で `/clear` 後に消える問題を修正 |
| MCP | MCP OAuth リフレッシュトークンが複数サーバーの同時リフレッシュ時に失われる問題を修正 |
| Permissions | `allowManagedDomainsOnly` / `allowManagedReadPathsOnly` が上位優先度のマネージド設定ソースに `sandbox` ブロックがない場合に無視される問題を修正（**セキュリティ修正**） |

**出典**: https://github.com/anthropics/claude-code/releases/tag/v2.1.136

---

### v2.1.139 (2026-05-12)

| カテゴリ | 変更内容 |
|---------|---------|
| Hooks | **フック `args: string[]` フィールド追加**（exec 形式）：シェルなしでコマンドを直接起動するためパスのプレースホルダーをクォートする必要がない |
| Hooks | **`PostToolUse` の `continueOnBlock` オプション追加**：`true` の場合フックの拒否理由を Claude にフィードバックしてターンを継続 |
| MCP | MCP stdio サーバーが `CLAUDE_PROJECT_DIR` を環境変数で受け取れるように（フックと同様）。プラグイン設定でコマンド内に `${CLAUDE_PROJECT_DIR}` を参照可能 |

**出典**: https://github.com/anthropics/claude-code/releases/tag/v2.1.139

---

### v2.1.140 (2026-05-13)

| カテゴリ | 変更内容 |
|---------|---------|
| Settings | シンボリックリンクされた設定ファイルが変更イベントを誤帰属させて偽の `ConfigChange` フックを発火させるリグレッションを修正 |

**出典**: https://github.com/anthropics/claude-code/releases/tag/v2.1.140

---

### v2.1.141 (2026-05-14)

| カテゴリ | 変更内容 |
|---------|---------|
| Hooks | `terminalSequence` フィールドをフック JSON 出力に追加：制御端末なしでデスクトップ通知、ウィンドウタイトル、ベルを送信可能 |

**出典**: https://github.com/anthropics/claude-code/releases/tag/v2.1.141

---

### v2.1.145 (2026-05-20)

| カテゴリ | 変更内容 |
|---------|---------|
| Hooks | Stop と SubagentStop フック入力に `background_tasks` と `session_crons` フィールドを追加 |
| Permissions | Bash コマンドでの非許可リスト環境変数への単純変数代入が自動承認されるバイパスを修正（**セキュリティ修正**） |

**出典**: https://github.com/anthropics/claude-code/releases/tag/v2.1.145

---

### v2.1.146 (2026-05-21)

| カテゴリ | 変更内容 |
|---------|---------|
| MCP | `resources/list`, `resources/templates/list`, `prompts/list` がページネーションする場合に2ページ目以降がドロップされる問題を修正 |
| Settings | `allowAllClaudeAiMcps` マネージド設定追加：`managed-mcp.json` と並行して claude.ai クラウド MCP コネクタを読み込む（v2.1.149） |

**出典**: https://github.com/anthropics/claude-code/releases/tag/v2.1.146

---

### v2.1.149 (2026-05-22)

| カテゴリ | 変更内容 |
|---------|---------|
| Settings | `allowAllClaudeAiMcps` マネージド設定追加（Enterprise 向け） |
| Permissions | PowerShell: 組み込み `cd` 関数（`cd..`, `cd\`, `cd~`, `X:`）が検出されずにワーキングディレクトリを変更できたバイパスを修正（**セキュリティ修正**） |
| Permissions | PowerShell: サンドボックス書き込み許可リストが git worktree 内でメインリポジトリルート全体をカバーしていた問題を修正（`hooks/` と `config` はdeny） |
| Permissions | PowerShell プレフィックス/ワイルドカード allow ルール（例：`PowerShell(dotnet.exe build *)`）がネイティブ実行可能ファイルとスクリプトを事前承認しない問題を修正 |

**出典**: https://github.com/anthropics/claude-code/releases/tag/v2.1.149

---

## 2. プラットフォーム機能に影響する変更（強調セクション）

### Hooks（フック）

| バージョン | 変更種別 | 詳細 |
|-----------|---------|------|
| v2.1.89 | **新機能** | `PreToolUse` に `"defer"` 判断追加 |
| v2.1.89 | **新機能** | `PermissionDenied` フックイベント追加 |
| v2.1.94 | **新機能** | `hookSpecificOutput.sessionTitle` を `UserPromptSubmit` に追加 |
| v2.1.105 | **新機能** | **PreCompact フック** 追加（`{"decision":"block"}` でコンパクションブロック） |
| v2.1.118 | **新機能** | フックが `type: "mcp_tool"` で MCP ツールを直接呼び出し可能 |
| v2.1.119 | **拡張** | `PostToolUse` / `PostToolUseFailure` 入力に `duration_ms` 追加 |
| v2.1.121 | **拡張** | `PostToolUse` フックが全ツールで `updatedToolOutput` によるツール出力置換をサポート（以前は MCP のみ） |
| v2.1.133 | **拡張** | フック入力に `effort.level` フィールドと `$CLAUDE_EFFORT` 環境変数を追加 |
| v2.1.132 | **拡張** | Bash ツールサブプロセスに `CLAUDE_CODE_SESSION_ID` 環境変数を追加 |
| v2.1.139 | **新機能** | フック `args: string[]` フィールド（exec 形式、シェル不要） |
| v2.1.139 | **新機能** | `PostToolUse` の `continueOnBlock` オプション |
| v2.1.141 | **新機能** | フック出力に `terminalSequence` フィールド追加 |
| v2.1.145 | **拡張** | Stop/SubagentStop フック入力に `background_tasks`, `session_crons` フィールド追加 |

### Settings（設定）

| バージョン | 変更種別 | 詳細 |
|-----------|---------|------|
| v2.1.91 | **新機能** | `disableSkillShellExecution` 設定 |
| v2.1.92 | **新機能** | `forceRemoteSettingsRefresh` ポリシー設定 |
| v2.1.97 | **新機能** | `refreshInterval` ステータスライン設定 |
| v2.1.113 | **新機能** | `sandbox.network.deniedDomains` 設定 |
| v2.1.118 | **新機能** | `wslInheritsWindowsSettings` ポリシーキー |
| v2.1.119 | **変更** | `/config` の設定が `~/.claude/settings.json` に永続化されるよう変更 |
| v2.1.119 | **新機能** | `prUrlTemplate` 設定 |
| v2.1.129 | **変更** | Gateway モデル探索が opt-in に変更（`CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1`） |
| v2.1.133 | **新機能** | `worktree.baseRef` 設定（`fresh`|`head`）。**デフォルト変更に注意** |
| v2.1.133 | **新機能** | `sandbox.bwrapPath`, `sandbox.socatPath` マネージド設定（Linux/WSL） |
| v2.1.133 | **新機能** | `parentSettingsBehavior` 管理者ティアキー |
| v2.1.136 | **新機能** | `settings.autoMode.hard_deny` |
| v2.1.143 | **新機能** | `worktree.bgIsolation: "none"` 設定 |
| v2.1.149 | **新機能** | `allowAllClaudeAiMcps` マネージド設定（Enterprise） |

### MCP

| バージョン | 変更種別 | 詳細 |
|-----------|---------|------|
| v2.1.89 | **新機能** | `MCP_CONNECTION_NONBLOCKING=true`、`--mcp-config` の接続を5秒に制限 |
| v2.1.91 | **新機能** | `_meta["anthropic/maxResultSizeChars"]` アノテーション（最大500K） |
| v2.1.121 | **新機能** | `alwaysLoad` オプションを MCP サーバー設定に追加 |
| v2.1.128 | **破壊的** | `workspace` が MCP の予約済みサーバー名に（既存の同名サーバーは警告付きでスキップ） |
| v2.1.139 | **新機能** | MCP stdio サーバーが `CLAUDE_PROJECT_DIR` 環境変数を受け取れるように |
| v2.1.146 | **修正** | ページネーション対応サーバーで2ページ目以降がドロップされる問題を修正 |

### Skills / Sub-agents / Plugins

| バージョン | 変更種別 | 詳細 |
|-----------|---------|------|
| v2.1.94 | **変更** | プラグインスキルの呼び出し名がフロントマター `name` を使用 |
| v2.1.94 | **新機能** | `keep-coding-instructions` フロントマターフィールド |
| v2.1.105 | **新機能** | プラグインの `monitors` マニフェストキー |
| v2.1.117 | **修正** | Agent フロントマター `mcpServers` が `--agent` での main-thread agent セッションで読み込まれるよう修正 |
| v2.1.129 | **変更** | `themes` と `monitors` は `"experimental": { ... }` 下に宣言推奨 |
| v2.1.129 | **新機能** | `skillOverrides` 設定（`off`, `user-invocable-only`, `name-only`） |

---

## 3. 破壊的変更（Breaking Changes）・非推奨化

| バージョン | 種別 | 詳細 |
|-----------|------|------|
| v2.1.108 | **非推奨** | `ENABLE_PROMPT_CACHING_1H_BEDROCK` 環境変数が非推奨に（後方互換あり、`ENABLE_PROMPT_CACHING_1H` を使用） |
| v2.1.111 | **変更** | Auto モードが `--enable-auto-mode` フラグなしで利用可能（フラグ不要になった） |
| v2.1.113 | **変更（移行）** | CLI がバンドルされた JavaScript の代わりにプラットフォームネイティブバイナリを起動するよう変更 |
| v2.1.128 | **破壊的** | MCP サーバー名 `workspace` が予約済みに。既存サーバーは警告付きでスキップされる |
| v2.1.129 | **変更（非推奨化）** | プラグインマニフェストのトップレベル `themes` / `monitors` キーが `"experimental"` 下での宣言を推奨（動作はするが `validate` が警告） |
| v2.1.129 | **変更（opt-in 化）** | Gateway `/v1/models` 探索が `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1` によるオプトインに変更（v2.1.126-128 では自動だった） |
| v2.1.133 | **動作変更** | `worktree.baseRef` のデフォルトが `fresh` になり、`EnterWorktree` のベースが `origin/<default>` に戻った（v2.1.128 以降は local HEAD だった）。unpushed コミットを保持するには `worktree.baseRef: "head"` に明示設定が必要 |

---

## 4. セキュリティ修正（プラットフォーム機能関連）

| バージョン | 詳細 |
|-----------|------|
| v2.1.97 | `--dangerously-skip-permissions` が保護パスへの書き込み承認後に静かにダウングレードされる問題を修正 |
| v2.1.98 | Bash ツールのバックスラッシュエスケープによる権限バイパスを修正 |
| v2.1.98 | 複合 Bash コマンドが強制権限プロンプトをバイパスする問題を修正 |
| v2.1.113 | Bash deny ルールが exec ラッパー（`env`, `sudo`, `watch` 等）でラップされたコマンドにマッチするよう強化 |
| v2.1.113 | `Bash(find:*)` allow ルールが `find -exec`/`-delete` を自動承認しないよう修正 |
| v2.1.116 | サンドボックスの自動許可がクリティカルディレクトリへの `rm`/`rmdir` で危険パス安全チェックをバイパスしないよう修正 |
| v2.1.136 | `allowManagedDomainsOnly` / `allowManagedReadPathsOnly` が上位の `sandbox` ブロックがない場合に無視される問題を修正 |
| v2.1.145 | Bash コマンドでの非許可リスト環境変数への単純変数代入が自動承認されるバイパスを修正 |
| v2.1.149 | PowerShell 組み込み `cd` 関数がワーキングディレクトリを検出されずに変更できたバイパスを修正 |

---

## 5. 調査上の注意事項・欠落情報

- v2.1.100, v2.1.104 は `gh release view` でリリースノートが空（内容なし）。実際は v2.1.98 の内容が含まれると推測されるが、推測での補完は行わない
- v2.1.138 は "Internal fixes" のみで詳細不明
- Issue 検索は今回未実施（`gh search issues` は公開リポジトリのみアクセス可能）
- 2026-05-27 時点での最新は v2.1.150（内部インフラ改善のみ）

---

## 6. 出典一覧

- `gh release list --repo anthropics/claude-code --limit 100`
- `gh release view <tag> --repo anthropics/claude-code`
- 各リリースページ: `https://github.com/anthropics/claude-code/releases/tag/<tag>`
