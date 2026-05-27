# LAM 差分マッピング: MCP / Settings / Permissions 領域

**作成日**: 2026-05-27  
**対象バージョン**: Claude Code v2.1.89 〜 v2.1.150（調査期間: 2026-03-31 〜 2026-05-27）  
**フェーズ**: PLANNING（文書分析・差分記録のみ。コード修正・生成は対象外）  
**担当**: MCP + Settings + Permissions 差分マッピング

---

## 対象範囲

本文書は、LAM（Living Architect Model）が `.claude/settings.json` および `.mcp.json`（または `~/.claude.json`）を通じて依存する以下の領域を対象とする。

- **MCP**: トランスポート設定・サーバー名制約・新規 MCP 機能
- **Settings**: `settings.json` の権限ブロック（permissions）・新規設定キー・Managed 設定パス
- **Permissions**: `allow`/`ask`/`deny` 書式・`permissionDecision` の値・Permission Modes

hooks（イベント種別・入出力スキーマ）は別文書（diff-hooks.md）の扱いとし、本文書では **hook 設定ブロックの書式**（settings.json 内 `hooks` 節）のうち Permissions に関係する部分のみ扱う。

---

## 入力資料

| 番号 | ファイル | 内容 |
|------|---------|------|
| 10 | `docs/artifacts/research/2026-05-27-cc-spec-survey/10-lam-current-dependencies.md` | LAM 現行依存インベントリ |
| 20 | `docs/artifacts/research/2026-05-27-cc-spec-survey/20-anthropic-official-spec.md` | 公式仕様（WebFetch + context7, 2026-05-27） |
| 40 | `docs/artifacts/research/2026-05-27-cc-spec-survey/40-github-releases-issues.md` | GitHub リリースノート v2.1.89–v2.1.150 |
| 50 | `docs/artifacts/research/2026-05-27-cc-spec-survey/50-verification.md` | 公式逐語確認レポート |
| 現物 | `.claude/settings.json` | LAM のプロジェクト設定現物 |
| 現物 | `docs/internal/05_MCP_INTEGRATION.md` | MCP 統合ガイド（SSOT） |
| 現物 | `docs/internal/07_SECURITY_AND_AUTOMATION.md` | セキュリティ・コマンド安全基準（SSOT） |

---

## 分類定義

| 分類 | 意味 |
|------|------|
| **現状維持で安全** | 現行 LAM の設定・書式が最新仕様と一致しており、変更不要 |
| **新機能で改善可** | 最新仕様に追加された機能を採用すれば LAM を改善できるが、必須ではない |
| **要更新** | 非推奨・破壊的変更・陳腐化・誤記・整合性欠落により、対応が推奨または必須 |

---

## 1. MCP 節

### 1.1 差分一覧表

| # | 項目 | 現行 LAM の状態 | 最新公式仕様 | 分類 | 根拠/出典 | LAM 影響箇所 |
|---|------|----------------|------------|------|-----------|-------------|
| M-1 | MCP トランスポート（SSE 非推奨） | `docs/internal/05_MCP_INTEGRATION.md` の設定例に `"type": "stdio"` のみ使用。SSE は使用していない | SSE (`type: "sse"`) は公式に非推奨。HTTP (`type: "http"` / `streamable-http`) が推奨 | **現状維持で安全** | 資料50 B-8「確認済み / SSE は非推奨」。LAM 設定例は `stdio` のみで SSE 使用なし | `docs/internal/05_MCP_INTEGRATION.md` L91–115（`type: "stdio"` のみ）|
| M-2 | MCP サーバー名 `workspace` の予約 | LAM 設定内に `workspace` 名のサーバーは存在しない（Serena / Heimdall のみ） | v2.1.128 より `workspace` が予約済みサーバー名。既存の同名サーバーは警告付きでスキップ | **現状維持で安全** | 資料40 v2.1.128「破壊的変更: workspace が予約済みサーバー名に」 | `.mcp.json`（存在する場合）。現行ドキュメント内に `workspace` 名の使用なし |
| M-3 | MCP 設定ドキュメント内の `type` フィールド明示 | `docs/internal/05_MCP_INTEGRATION.md` L91–115 の `serena` / `heimdall` 設定例は `"type": "stdio"` を明示 | 公式書式で `type` 必須（`stdio|http|sse|streamable-http`） | **現状維持で安全** | 資料20 Section 6.1 | `docs/internal/05_MCP_INTEGRATION.md` |
| M-4 | MCP `alwaysLoad` フィールド（新規） | LAM の MCP 設定例に `alwaysLoad` なし | v2.1.121 で `alwaysLoad: true` を追加。Tool Search による遅延ロード対象から外すオプション | **新機能で改善可** | 資料40 v2.1.121「alwaysLoad オプションを MCP サーバー設定に追加」。資料20 Section 6.6 | `docs/internal/05_MCP_INTEGRATION.md`（Serena, Heimdall を常時ロードしたい場合に追加可） |
| M-5 | `$CLAUDE_PROJECT_DIR` の MCP stdio 設定への展開 | 現行 `docs/internal/05_MCP_INTEGRATION.md` では `--project /absolute/path` を手動指定 | v2.1.139 より MCP stdio サーバーが `CLAUDE_PROJECT_DIR` 環境変数を受け取れる。`${CLAUDE_PROJECT_DIR}` を `args` や `env` 内で参照可能 | **新機能で改善可** | 資料40 v2.1.139「MCP stdio サーバーが CLAUDE_PROJECT_DIR を受け取れるように」。資料50 A-5 | `docs/internal/05_MCP_INTEGRATION.md` L96–116（`--project` 引数を `${CLAUDE_PROJECT_DIR}` 化できる） |
| M-6 | Elicitation（MCPサーバーからのユーザー入力要求） | LAM では未使用 | `Elicitation` / `ElicitationResult` hook イベントが正式追加。MCP サーバーが構造化ユーザー入力を要求できる | **新機能で改善可** | 資料20 Section 7.5 | 現状影響なし。将来の MCP 導入時の選択肢として記録 |
| M-7 | `headersHelper` / `oauth` フィールド（HTTP MCP） | LAM の設定例に HTTP MCP なし | HTTP MCP に `headersHelper`（動的ヘッダー）・`oauth` ブロックが追加 | **新機能で改善可** | 資料20 Section 6.2 | `docs/internal/05_MCP_INTEGRATION.md`（HTTP MCP 追加時の参照情報） |

### 1.2 小計（MCP）

| 分類 | 件数 |
|------|------|
| 現状維持で安全 | 3（M-1, M-2, M-3） |
| 新機能で改善可 | 4（M-4, M-5, M-6, M-7） |
| 要更新 | 0 |

---

## 2. Settings 節

### 2.1 差分一覧表

| # | 項目 | 現行 LAM の状態 | 最新公式仕様 | 分類 | 根拠/出典 | LAM 影響箇所 |
|---|------|----------------|------------|------|-----------|-------------|
| S-1 | Managed 設定パス（Windows） | `docs/internal/07_SECURITY_AND_AUTOMATION.md` に旧 Windows パスへの言及なし。LAM 環境は Windows 11 | v2.1.75 以降、旧 Windows パス `C:\ProgramData\ClaudeCode\managed-settings.json` は**非サポート**。現行は `C:\Program Files\ClaudeCode\managed-settings.json` | **要更新**（影響度: 中） | 資料50 B-9「Windows パスが変更されているため（v2.1.75以降）、古い C:\ProgramData\ClaudeCode\ パスを参照していると要更新」。廃止時期は資料50 が「公式 changelog で未確認」と記載（**公式未確認事項あり**） | `docs/internal/07_SECURITY_AND_AUTOMATION.md`（Managed 設定パスの記述があれば更新。現物確認では直接記述なし）。管理者配布環境向けのガイドや README があれば要確認 |
| S-2 | `settings.json` の基本構造（permissions, hooks ブロック） | `.claude/settings.json` に `permissions`・`hooks` の2ブロックのみ。他の新規キー（`model`, `worktree.*`, `sandbox`, `skillOverrides` 等）は未使用 | 現行の2ブロック構成は公式書式と完全互換。未使用キーの不在は問題なし | **現状維持で安全** | 資料20 Section 2.2、資料10 Section 4 | `.claude/settings.json` |
| S-3 | `worktree.baseRef` デフォルト変更 | LAM の `settings.json` に `worktree` ブロックなし（未設定） | v2.1.133 より `worktree.baseRef` のデフォルトが `fresh` に変更。`EnterWorktree` のベースが `origin/<default>` に（v2.1.128 では local HEAD だった）。unpushed コミット保持には `"head"` の明示設定が必要 | **要更新**（影響度: 低） | 資料40 v2.1.133「worktree.baseRef 設定追加…デフォルト変更に注意」。資料20 Section 2.4（v2.1.133） | `.claude/settings.json`（worktree 機能を使う場合は `worktree.baseRef: "head"` の明示設定を検討。現状未使用なら対応不要だが、wave-plan スキルなど worktree を活用する際に注意） |
| S-4 | `skillOverrides` キー（新規） | `settings.json` に未設定 | `skillOverrides` で特定スキルの可視性を `off`, `user-invocable-only`, `name-only` に制御可能（v2.1.129, 修正 v2.1.121） | **新機能で改善可** | 資料40 v2.1.129「skillOverrides 設定が機能するよう修正」。資料20 Section 2.4 | `.claude/settings.json`（LAM には多数のスキルがある。コンテキスト節約のため一部スキルを `name-only` 等にする用途） |
| S-5 | `skillListingBudgetFraction` / `maxSkillDescriptionChars` キー（新規） | `settings.json` に未設定 | スキルリスト用コンテキスト割り当て（`skillListingBudgetFraction`, デフォルト 0.01）・スキル説明最大文字数（`maxSkillDescriptionChars`, デフォルト 1536）が v2.1.105 で追加 | **新機能で改善可** | 資料20 Section 2.4（v2.1.105）。資料40 v2.1.105 | `.claude/settings.json`（LAM はスキル数が多いため、コンテキスト管理の観点で設定価値あり） |
| S-6 | `worktree.bgIsolation` キー（新規） | `settings.json` に未設定 | v2.1.143 で `worktree.bgIsolation: "none"` が追加。バックグラウンドセッションのワークツリー分離モード制御 | **新機能で改善可** | 資料40 v2.1.143「worktree.bgIsolation: "none" 設定」。資料20 Section 2.4（v2.1.143） | `.claude/settings.json`（EnterWorktree スキル使用時） |
| S-7 | `policyHelper` キー（新規） | `settings.json` に未設定 | v2.1.136 で `policyHelper` が追加。動的な Managed 設定計算スクリプトを指定可能 | **新機能で改善可** | 資料20 Section 2.4（v2.1.136）。資料40 v2.1.136「policyHelper 追加」（バージョン番号は収集値・**公式未確認**） | `docs/internal/07_SECURITY_AND_AUTOMATION.md`（Enterprise 管理者向け機能。小規模開発では不要） |
| S-8 | `parentSettingsBehavior` キー（新規） | `settings.json` に未設定 | v2.1.133 で `parentSettingsBehavior`（`'first-wins'`|`'merge'`）が追加。SDK `managedSettings`（親ティア）のポリシーマージを制御 | **新機能で改善可** | 資料40 v2.1.133「parentSettingsBehavior 管理者ティアキー追加」 | `docs/internal/07_SECURITY_AND_AUTOMATION.md`（Enterprise 管理者向け機能） |
| S-9 | `disableRemoteControl` キー（新規） | `settings.json` に未設定 | v2.1.128 で `disableRemoteControl` が追加。リモートコントロール機能をブロック | **新機能で改善可** | 資料20 Section 2.4（v2.1.128）。バージョン番号は収集値・**公式未確認** | `.claude/settings.json`（セキュリティ強化が必要な環境での選択肢） |
| S-10 | `autoMode.hard_deny`（新規） | `settings.json` に `autoMode` ブロックなし | v2.1.136 で `autoMode.hard_deny` が追加。ユーザー意図や allow 例外にかかわらず無条件でブロックするルール | **新機能で改善可** | 資料40 v2.1.136「settings.autoMode.hard_deny 追加」 | `.claude/settings.json`（auto モード使用時の追加安全策） |
| S-11 | `$schema` キー | `settings.json` に `$schema` なし | 公式サンプルでは `"$schema": "https://json.schemastore.org/claude-code-settings.json"` を冒頭に記述 | **新機能で改善可** | 資料20 Section 2.2 | `.claude/settings.json`（IDE での補完・バリデーション向上。機能影響なし） |
| S-12 | `disableSkillShellExecution` キー（新規） | `settings.json` に未設定 | v2.1.91 で `disableSkillShellExecution` が追加。スキル・カスタムスラッシュコマンド・プラグインコマンドでのインラインシェル実行を無効化 | **新機能で改善可** | 資料40 v2.1.91「disableSkillShellExecution 設定追加」 | `.claude/settings.json`（セキュリティポリシーに応じて設定を検討。LAM スキルの `!`コマンド実行を制限できる） |

### 2.2 小計（Settings）

| 分類 | 件数 |
|------|------|
| 現状維持で安全 | 2（S-2） ※ S-1 は別分類 |
| 新機能で改善可 | 9（S-4〜S-12） |
| 要更新 | 2（S-1, S-3） |

---

## 3. Permissions 節

### 3.1 差分一覧表

| # | 項目 | 現行 LAM の状態 | 最新公式仕様 | 分類 | 根拠/出典 | LAM 影響箇所 |
|---|------|----------------|------------|------|-----------|-------------|
| P-1 | `allow`/`ask`/`deny` 三値書式 | `.claude/settings.json` L2–66 で `allow`/`deny`/`ask` の三値ブロックを使用。各要素は `"Bash(glob_pattern)"` 書式 | 現行書式と完全互換。`allow`/`ask`/`deny` の三値書式は最新仕様でも有効 | **現状維持で安全** | 資料20 Section 3.1、資料50 A-3 | `.claude/settings.json` |
| P-2 | `permissionDecision` 出力値（hook 連携） | `pre-tool-use.py` が `hookSpecificOutput.permissionDecision: "ask"` を出力。値は `"ask"` のみ使用 | v2.1.89 で `"defer"` が4番目の値として追加。現行値 `"allow"`, `"deny"`, `"ask"` はすべて有効。`"defer"` は「通常の許可フローに委ねる」 | **現状維持で安全** | 資料50 A-3「確認済み / 書式変更あり（値の追加）。継続使用OK（既存の3値は全て有効）」。資料40 v2.1.89「PreToolUse に defer 判断追加」 | `pre-tool-use.py` L191–197（既存動作に変更不要。`defer` 値の活用は改善機会） |
| P-3 | `permissionDecision: "defer"` の活用（新規） | `pre-tool-use.py` は `"ask"` のみ出力 | `"defer"` を返すと通常の権限フロー（`settings.json` の `allow`/`ask`/`deny`）に委ねる。ヘッドレスモードでは一時停止し `--resume` で再評価 | **新機能で改善可** | 資料50 A-3、資料40 v2.1.89 | `pre-tool-use.py`（条件判定が難しいケースで `"ask"` の代わりに `"defer"` を使い、settings.json のルールに判断を委ねる設計も可能） |
| P-4 | `PermissionDenied` hook イベント（新規） | LAM は `PermissionDenied` hook を未設定 | v2.1.89 で `PermissionDenied` イベントが追加。auto モードでツール呼び出しが拒否されたときに発火。`{"hookSpecificOutput": {"retry": true}}` を返すと再試行 | **新機能で改善可** | 資料40 v2.1.89「PermissionDenied フックイベント追加」。資料20 Section 1.1 | `.claude/settings.json`（auto モード利用時に権限拒否の後処理を実装できる。現状 auto モード未使用なら対応不要） |
| P-5 | `PermissionRequest` hook イベント（新規） | LAM は `PermissionRequest` hook を未設定 | `PermissionRequest` イベントが正式追加。`PreToolUse` とは別の、権限ダイアログ表示専用 hook | **新機能で改善可** | 資料20 Section 1.1, 1.3（PermissionRequest の入出力スキーマ） | `.claude/settings.json`（権限制御の細粒化に活用可能） |
| P-6 | `permissions.defaultMode` キー | `.claude/settings.json` に `defaultMode` なし | `permissions.defaultMode` で Permission Mode（`default`/`plan`/`acceptEdits`/`auto`/`dontAsk`/`bypassPermissions`）を設定可能 | **新機能で改善可** | 資料20 Section 3.3 | `.claude/settings.json`（BUILDING フェーズで `acceptEdits` を設定すれば、ファイル編集の逐一承認を省略できる） |
| P-7 | `permissions.additionalDirectories` キー | `.claude/settings.json` に `additionalDirectories` なし | `permissions.additionalDirectories` でプロジェクト外ディレクトリへのファイルアクセスを付与できる。v2.1.97 でセッション途中での変更も即時適用されるよう改善 | **新機能で改善可** | 資料20 Section 3.4、資料40 v2.1.97 | `.claude/settings.json`（`docs/` と `src/` が分離している構成や、モノレポ構成での使用を検討） |
| P-8 | Bash allow ルールのバックスラッシュエスケープバイパス修正（セキュリティ） | `.claude/settings.json` の `deny` ルールに `Bash(rm *)` 等を設定 | v2.1.98 でバックスラッシュエスケープによる権限バイパスが修正済み。v2.1.113 で exec ラッパー（`env`, `sudo`, `watch` 等）経由のバイパスも修正。v2.1.149 で PowerShell `cd` バイパスも修正 | **現状維持で安全** | 資料40 v2.1.98, v2.1.113, v2.1.149（セキュリティ修正）。LAM の deny ルール設定は変更不要だが、**プラットフォーム側のセキュリティ強化**により従来の抜け穴が塞がれた | `.claude/settings.json` L30–46（deny ルール）|
| P-9 | `find` の deny パターン網羅性 | `.claude/settings.json` L43–46 で `find * -delete *`, `find * -exec rm *`, `find * -exec chmod *`, `find * -exec chown *` を deny | v2.1.113 で `Bash(find:*)` allow ルールが `find -exec`/`-delete` を自動承認しないよう修正。LAM は `find *` を ask に分類、特定パターンを deny で網羅 | **現状維持で安全** | 資料40 v2.1.113「Bash(find:*) allow ルールが find -exec/-delete を自動承認しないよう修正」 | `.claude/settings.json` L43–46 |
| P-10 | `Agent(name)` 書式による Sub-agent の deny 制御（新規） | `deny` ブロックに `Agent()` 書式なし | `"deny": ["Agent(Explore)", "Agent(my-custom-agent)"]` で特定サブエージェントの起動を禁止できる | **新機能で改善可** | 資料20 Section 3.2 | `.claude/settings.json`（特定の高権限サブエージェントを制限する用途） |
| P-11 | `ToolSearch` の deny 制御（新規） | `deny` ブロックに `ToolSearch` なし | `"deny": ["ToolSearch"]` でツール検索機能をブロックできる | **新機能で改善可** | 資料20 Section 3.2 | `.claude/settings.json`（MCP ツール検索を強制無効化したい場合） |
| P-12 | `permissions.disableBypassPermissionsMode` キー | `.claude/settings.json` に未設定 | `disableBypassPermissionsMode: "disable"` で `bypassPermissions` モードを無効化できる | **新機能で改善可** | 資料20 Section 2.2（permissions ブロックの構造）。資料40 v2.1.97「--dangerously-skip-permissions のバグ修正」 | `.claude/settings.json`（セキュリティポリシーとして完全禁止が必要な場合） |

### 3.2 小計（Permissions）

| 分類 | 件数 |
|------|------|
| 現状維持で安全 | 4（P-1, P-2, P-8, P-9） |
| 新機能で改善可 | 7（P-3, P-4, P-5, P-6, P-7, P-10, P-11, P-12） ※ P-12 は 8件目だが重複排除で7 |
| 要更新 | 0 |

> ※ P-3 〜 P-12 は改善可 8 件、安全 4 件の計 12 件。

---

## 4. 全体小計

| 節 | 現状維持で安全 | 新機能で改善可 | 要更新 | 合計 |
|----|--------------|-------------|------|------|
| MCP | 3 | 4 | 0 | 7 |
| Settings | 2 | 9 | 2 | 13 |
| Permissions | 4 | 8 | 0 | 12 |
| **合計** | **9** | **21** | **2** | **32** |

---

## 5. 「要更新」詳細（影響度付き）

### S-1: Managed 設定パス（Windows）旧パス廃止

**影響度**: 中

**概要**: v2.1.75 以降、Windows での Managed 設定ファイルのパスが変更された。

| 項目 | 内容 |
|------|------|
| 旧パス（非サポート） | `C:\ProgramData\ClaudeCode\managed-settings.json` |
| 新パス（現行） | `C:\Program Files\ClaudeCode\managed-settings.json` |

**LAM への影響**: LAM の現物 `settings.json`・`07_SECURITY_AND_AUTOMATION.md` には旧パスへの直接言及はないが、managed-settings を利用する管理者向けガイド文書や README がある場合は更新が必要。LAM 環境は Windows 11（作業ディレクトリ: `D:\work7\LivingArchitectModel`）のため、managed-settings を導入する際は新パスを参照すること。

**注記**: 廃止時期「v2.1.75以降」は資料50 B-9 の WebFetch 取得内容に基づく。v2.1.75 のリリース日は GitHub releases から未確認（**公式未確認**）。

**対応**: `docs/internal/05_MCP_INTEGRATION.md` または管理者向けドキュメントに「Windows managed-settings のパスは `C:\Program Files\ClaudeCode\`」を明記。

---

### S-3: `worktree.baseRef` デフォルト変更

**影響度**: 低

**概要**: v2.1.133 より `worktree.baseRef` のデフォルトが `fresh`（`origin/<default>` ブランチ）に変更。unpushed コミットがある状態で `EnterWorktree` を呼ぶと、新ワークツリーのベースが `origin/<default>` になるため、ローカルのみのコミットが取り込まれない。

| 項目 | 内容 |
|------|------|
| 変更前デフォルト（v2.1.128〜v2.1.132） | `head`（local HEAD ベース） |
| 変更後デフォルト（v2.1.133〜） | `fresh`（`origin/<default>` ベース） |

**LAM への影響**: LAM の `settings.json` に `worktree` ブロックはなく、現時点では EnterWorktree を常用しているわけではない。ただし `wave-plan` スキルや並列 worktree 機能を将来活用する際には、unpushed コミットが存在する状況でデフォルト動作が変わっている点に注意が必要。

**対応**: `wave-plan` スキルや worktree 関連手順書に「unpushed コミットを保持したい場合は `worktree.baseRef: "head"` を明示設定」という注意書きを追加。または `settings.json` に `"worktree": {"baseRef": "head"}` を先行追加（PM 級変更）。

---

## 6. 「公式未確認」として残った項目

以下の項目は先行調査（資料40）または資料50 が「公式未確認」と明記しているもの。差分評価に含めるが、採否の前に公式一次情報の再確認を推奨する。

| # | 項目 | 状況 | 出典 |
|---|------|------|------|
| U-1 | Managed 設定旧 Windows パス廃止の確定時期（v2.1.75） | 資料50 B-9 が「v2.1.75 のリリース日は公式 changelog で未確認」と明記 | 資料50 B-9 |
| U-2 | `policyHelper`（S-7）のバージョン番号 v2.1.136 | 資料20 Section 2.4 は v2.1.136 と記載。資料40 の Web 由来バージョン番号は「収集値・要裏取り」扱い | 資料20 Section 2.4 |
| U-3 | `disableRemoteControl`（S-9）のバージョン番号 v2.1.128 | 同上 | 資料20 Section 2.4 |
| U-4 | `PreCompact` hook のブロック可否（出力 `decision: "block"` による）の逐語確認 | 資料50 が「WebFetch 結果より可能と推定されるが、公式スニペットでの逐語確認は未完全」と明記 | 資料50 Section「公式で裏取りできなかった先行調査の主張」 |
| U-5 | hook `type: "mcp_tool"` の詳細スキーマ（必須フィールド一覧） | 資料50 が「動作確認は別途必要」と明記 | 資料50 Section「公式で裏取りできなかった先行調査の主張」 |

---

*文書作成: 2026-05-27。次回更新タイミング: 次回 Wave 開始時または Claude Code メジャーアップデート時。Upstream First 原則（`.claude/rules/upstream-first.md`）に従い、プラットフォーム機能実装前に必ず公式ドキュメントを再確認すること。*
