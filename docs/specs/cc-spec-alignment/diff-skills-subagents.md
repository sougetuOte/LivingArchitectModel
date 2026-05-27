# LAM 差分マッピング — Skills / Sub-agents 領域

**作成日**: 2026-05-27  
**フェーズ**: PLANNING（文書突き合わせ分析のみ。コード修正禁止）  
**作成目的**: LAM の Skills 群・Sub-agents 群について、現行依存と最新公式仕様の差分を3分類に振り分け、今後の意思決定の入力資料とする。

---

## 対象範囲

| 対象 | 現行ファイル |
|------|------------|
| Skills | `.claude/skills/*/SKILL.md`（7スキル）: adr-template, clarify, lam-orchestrate, magi, skill-creator, spec-template, ui-design-guide |
| Commands（Skills統合） | `.claude/commands/*.md`（11ファイル）: auditing, building, full-review, pattern-review, planning, project-status, quick-load, quick-save, retro, ship, wave-plan |
| Sub-agents | `.claude/agents/*.md`（8エージェント）: code-reviewer, design-architect, doc-writer, quality-auditor, requirement-analyst, task-decomposer, tdd-developer, test-runner |

## 入力資料

| 資料 | パス |
|-----|------|
| LAM 現行依存インベントリ | `docs/artifacts/research/2026-05-27-cc-spec-survey/10-lam-current-dependencies.md` |
| 公式仕様サーベイ | `docs/artifacts/research/2026-05-27-cc-spec-survey/20-anthropic-official-spec.md` |
| 裏取り検証レポート | `docs/artifacts/research/2026-05-27-cc-spec-survey/50-verification.md` |
| 現物確認 | `.claude/agents/*.md`、`.claude/skills/*/SKILL.md`、`.claude/commands/*.md` |

---

## 1. Skills 差分表

### 凡例

- **分類A**: 現状維持で安全（公式と乖離なく変更不要）
- **分類B**: 新機能で改善可（公式の新フィールド/新機構を未活用、列挙のみ）
- **分類C**: 要更新（非推奨・破壊的・記述陳腐化）

### 1.1 SKILL.md フロントマター キー差分

| 項目 | 現行 LAM の状態 | 最新公式仕様 | 分類 | 根拠/出典 | LAM 影響箇所(file) |
|------|--------------|------------|------|---------|------------------|
| `name` キー | 全 SKILL.md に存在。lam-orchestrate, adr-template, clarify, spec-template, skill-creator は明示あり。magi は未記載（ディレクトリ名が代替） | オプション（省略時はディレクトリ名がデフォルト）。必須ではない | A: 現状維持で安全 | 20-anthropic-official-spec.md §4.2「ディレクトリ名がデフォルト」 | `.claude/skills/*/SKILL.md` |
| `description` キー | 全 SKILL.md に存在し、多行または単行で記述 | 強く推奨（auto-invoke に必要）。上限1536文字 | A: 現状維持で安全 | 20-anthropic-official-spec.md §4.2 | `.claude/skills/*/SKILL.md` |
| `version` キー | lam-orchestrate, adr-template, clarify, spec-template, skill-creator, ui-design-guide に存在。magi は未記載 | 公式フロントマターに `version` キーの定義なし。LAM 独自のメタデータ | A: 現状維持で安全（Claude Code に解釈されないが害もない） | 20-anthropic-official-spec.md §4.2（version キーの記載なし）; 50-verification.md B-6 | `.claude/skills/lam-orchestrate/SKILL.md` 他 |
| `allowed-tools` キー | **全 SKILL.md に存在しない** | 公式キー名は `allowed-tools`（スペース区切り文字列）。このスキル使用中に自動許可するツールを指定できる | B: 新機能で改善可 | 20-anthropic-official-spec.md §4.2 | `.claude/skills/*/SKILL.md`（全7スキル） |
| `when_to_use` キー | **全 SKILL.md に存在しない** | `description` に追記されるトリガー条件記述フィールド。auto-invoke のトリガー精度向上に寄与 | B: 新機能で改善可 | 20-anthropic-official-spec.md §4.2, §7.3 | `.claude/skills/*/SKILL.md`（全7スキル） |
| `model` キー | **全 SKILL.md に存在しない** | スキル実行中のモデル上書きが可能。`"sonnet"`, `"haiku"` 等 | B: 新機能で改善可 | 20-anthropic-official-spec.md §4.2 | `.claude/skills/*/SKILL.md`（全7スキル） |
| `effort` キー | **全 SKILL.md に存在しない** | スキル実行中のエフォートレベル上書きが可能。`"high"`, `"low"` 等 | B: 新機能で改善可 | 20-anthropic-official-spec.md §4.2 | `.claude/skills/*/SKILL.md`（全7スキル） |
| `paths` キー | **全 SKILL.md に存在しない** | 特定ファイルパターンでスキルを自動適用できる（例: `"docs/specs/*.md"` で spec-template を自動起動） | B: 新機能で改善可 | 20-anthropic-official-spec.md §4.2, §7.3 | `.claude/skills/*/SKILL.md`（adr-template, spec-template 等が有力候補） |
| `hooks` キー（フロントマター内） | **全 SKILL.md に存在しない** | スキル固有の PreToolUse/PostToolUse 等をフロントマター内に直接記述できる | B: 新機能で改善可 | 20-anthropic-official-spec.md §4.2 | `.claude/skills/*/SKILL.md` |
| `context: fork` キー | **全 SKILL.md に存在しない** | サブエージェントとして実行する指定。`agent:` キーと組み合わせて使用可 | B: 新機能で改善可 | 20-anthropic-official-spec.md §4.2 | `.claude/skills/lam-orchestrate/SKILL.md`（オーケストレーター系が候補） |
| `disable-model-invocation` キー | **全 SKILL.md に存在しない** | Claude による自動起動を禁止（ユーザー手動起動専用にする） | B: 新機能で改善可 | 20-anthropic-official-spec.md §4.2, §4.6 | `.claude/skills/*/SKILL.md`（ship, retro 等の手動運用スキルが候補） |
| `user-invocable: false` キー | **全 SKILL.md に存在しない** | /メニューから非表示にする。Claude が自動起動するが人間は直接呼べない | B: 新機能で改善可 | 20-anthropic-official-spec.md §4.2, §4.6 | `.claude/skills/*/SKILL.md` |
| `shell` キー | **全 SKILL.md に存在しない** | PowerShell 対応（Windowsプロジェクト）。`!` コマンドブロックで使うシェルを指定 | B: 新機能で改善可 | 20-anthropic-official-spec.md §4.2, §7.3 | `.claude/skills/*/SKILL.md`（LAM は Windows 環境で動作確認あり） |
| `argument-hint` / `arguments` キー | **全 SKILL.md に存在しない** | オートコンプリート表示と名前付き引数の宣言。`$ARGUMENTS[N]` や `$name` 変数と組み合わせ | B: 新機能で改善可 | 20-anthropic-official-spec.md §4.2, §4.3 | `.claude/skills/*/SKILL.md` |

### 1.2 .claude/commands/ との統合状況

| 項目 | 現行 LAM の状態 | 最新公式仕様 | 分類 | 根拠/出典 | LAM 影響箇所(file) |
|------|--------------|------------|------|---------|------------------|
| `.claude/commands/*.md` の継続動作 | 11 ファイルが `.claude/commands/` に存在（auditing, building, full-review, pattern-review, planning, project-status, quick-load, quick-save, retro, ship, wave-plan） | `.claude/commands/` ファイルは Skills に統合済み。後方互換あり。既存ファイルはそのまま動作。スキルと同名のコマンドが存在する場合はスキルが優先 | A: 現状維持で安全 | 50-verification.md B-6「後方互換あり」; 20-anthropic-official-spec.md §4.1 | `.claude/commands/*.md`（全11ファイル） |
| `commands/` と `skills/` の重複 | `skills/` には 7 スキルが存在。命名上の重複（例: magi スキルと `commands/` 側での同名コマンド）は現状なし | 同名の場合はスキル（`skills/`）が優先される | A: 現状維持で安全 | 20-anthropic-official-spec.md §4.1「スキルと同名のコマンドがある場合、スキルが優先」 | `.claude/skills/`, `.claude/commands/` |
| `commands/` ファイルのフロントマター欠如 | `commands/` 配下のファイルにフロントマターなし（マークダウン本文のみ） | Skills の新機能（`paths`, `allowed-tools`, `model` 等）を活用するには SKILL.md 形式への移行が必要。後方互換動作ではフロントマター機能は使えない | C: 要更新（影響度:低） | 20-anthropic-official-spec.md §4.1「Skillsはより豊富な機能を持つ上位互換」; 50-verification.md B-6 | `.claude/commands/*.md`（全11ファイル）。動作は継続するが機能拡張不可 |
| 動的コンテキストインジェクション（`!` ブロック） | `commands/` ファイルに `!`ブロック未使用 | SKILL.md 内で `` !`command` `` 形式でコマンド出力を動的挿入できる | B: 新機能で改善可 | 20-anthropic-official-spec.md §4.4 | `.claude/commands/*.md`, `.claude/skills/*/SKILL.md` |
| `${CLAUDE_SKILL_DIR}` / `${CLAUDE_EFFORT}` 変数 | SKILL.md, commands/ ともに未使用 | スキルディレクトリ絶対パスとエフォートレベルを参照できる組み込み変数 | B: 新機能で改善可 | 20-anthropic-official-spec.md §4.3 | `.claude/skills/*/SKILL.md` |

### 1.3 コンテキスト管理（Skills 圧縮ルール）

| 項目 | 現行 LAM の状態 | 最新公式仕様 | 分類 | 根拠/出典 | LAM 影響箇所(file) |
|------|--------------|------------|------|---------|------------------|
| コンテキスト圧縮ルール | 明示的な考慮なし（SKILL.md のサイズ制約に関する記述なし） | 複数スキル合計25,000トークン共有バジェット。圧縮時は最近起動したスキルが優先、先頭5,000トークン保持 | A: 現状維持で安全（知識として持っておく） | 20-anthropic-official-spec.md §4.7 | `.claude/skills/*/SKILL.md`（特に長大な lam-orchestrate, quality-auditor 相当のスキル） |
| スキル説明の上限1536文字 | description の文字数について制限の意識なし | `maxSkillDescriptionChars`（デフォルト1536文字）で切り詰められる可能性 | A: 現状維持で安全（description は全て1536文字未満と推定） | 20-anthropic-official-spec.md §2.2「maxSkillDescriptionChars: v2.1.105」 | `.claude/skills/*/SKILL.md` |

---

**Skills 分類小計**

| 分類 | 件数 |
|------|-----|
| A: 現状維持で安全 | 7 |
| B: 新機能で改善可 | 12 |
| C: 要更新 | 1 |

---

## 2. Sub-agents 差分表

### 2.1 フロントマター キー差分（全8エージェント共通）

LAM の全 Sub-agents（code-reviewer, design-architect, doc-writer, quality-auditor, requirement-analyst, task-decomposer, tdd-developer, test-runner）で使用中のキーと公式仕様の対照。

| 項目 | 現行 LAM の状態 | 最新公式仕様 | 分類 | 根拠/出典 | LAM 影響箇所(file) |
|------|--------------|------------|------|---------|------------------|
| `name` キー | 全8エージェントに存在 | 必須（小文字・ハイフン推奨） | A: 現状維持で安全 | 20-anthropic-official-spec.md §5.2「name: 必須」 | `.claude/agents/*.md`（全8ファイル） |
| `description` キー | 全8エージェントに存在（単行または複数行） | 必須。Claude がエージェントを選択するタイミングを決定する | A: 現状維持で安全 | 20-anthropic-official-spec.md §5.2, §5.3 | `.claude/agents/*.md`（全8ファイル） |
| `model` キー | 全エージェントに存在。sonnet（6体）・haiku（task-decomposer, test-runner の2体） | `sonnet`, `opus`, `haiku`, フルID, `inherit` のいずれか | A: 現状維持で安全 | 20-anthropic-official-spec.md §5.2 | `.claude/agents/*.md`（全8ファイル） |
| `tools` キー | 全8エージェントに存在（カンマ区切り文字列形式） | カンマ区切り文字列形式で有効。省略時は全ツール継承 | A: 現状維持で安全 | 10-lam-current-dependencies.md §5「カンマ区切り文字列」; 20-anthropic-official-spec.md §5.2 | `.claude/agents/*.md`（全8ファイル） |
| `# permission-level: XX` コメント行 | 全8エージェントで使用。SE（design-architect, doc-writer, quality-auditor, task-decomposer, tdd-developer, code-reviewer）、PM（requirement-analyst）、PG（test-runner） | 公式フロントマターキーとして定義なし。コメント行は Claude Code に解釈されない。LAM 独自の慣習メタデータ | A: 現状維持で安全（LAM 内部での可読性メタデータとして機能。実害なし） | 10-lam-current-dependencies.md §5「推測：Claude Code には解釈されない可能性」; 20-anthropic-official-spec.md §5.2（該当キーなし） | `.claude/agents/*.md`（全8ファイル） |
| `disallowedTools` キー | **全エージェントに存在しない** | 拒否ツールの denylist。`tools` より優先適用 | B: 新機能で改善可 | 20-anthropic-official-spec.md §5.2 | `.claude/agents/*.md` |
| `permissionMode` キー | **全エージェントに存在しない** | `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan` を設定可能。エージェントごとに許可モードを変えられる | B: 新機能で改善可 | 20-anthropic-official-spec.md §5.2 | `.claude/agents/*.md` |
| `maxTurns` キー | **全エージェントに存在しない** | エージェントの最大ターン数制限（無限ループ防止） | B: 新機能で改善可 | 20-anthropic-official-spec.md §5.2 | `.claude/agents/*.md` |
| `skills` キー | **全エージェントに存在しない** | エージェント起動時に事前ロードするスキルを指定できる。例: code-reviewer に `code-quality-guideline` スキルを注入 | B: 新機能で改善可 | 20-anthropic-official-spec.md §5.2; 50-verification.md B-7 | `.claude/agents/*.md`（code-reviewer, quality-auditor 等が有力候補） |
| `hooks` キー（フロントマター内） | **全エージェントに存在しない** | エージェント固有の PreToolUse/PostToolUse 等をフロントマター内に直接記述できる | B: 新機能で改善可 | 20-anthropic-official-spec.md §5.2; 50-verification.md B-7 | `.claude/agents/*.md` |
| `memory` キー | **全エージェントに存在しない** | `user`/`project`/`local` で永続メモリを有効化。`user` は `~/.claude/agent-memory/<name>/` に蓄積 | B: 新機能で改善可（後述の LAM 自前運用との関係を要整理） | 20-anthropic-official-spec.md §5.2, §5.7; 50-verification.md B-7 | `.claude/agents/*.md`（全8ファイル） |
| `background` キー | **全エージェントに存在しない** | `true` でバックグラウンドタスクとして常時実行 | B: 新機能で改善可 | 20-anthropic-official-spec.md §5.2 | `.claude/agents/*.md` |
| `effort` キー | **全エージェントに存在しない** | エージェントのエフォートレベルを設定できる | B: 新機能で改善可 | 20-anthropic-official-spec.md §5.2 | `.claude/agents/*.md` |
| `isolation: worktree` キー | **全エージェントに存在しない** | サブエージェントが独立した git worktree で実行される。並列エージェントの衝突防止に有効 | B: 新機能で改善可 | 20-anthropic-official-spec.md §5.2; 50-verification.md B-7 | `.claude/agents/*.md` |
| `color` キー | **全エージェントに存在しない** | UI でのエージェント識別色。`red`/`blue`/`green`/`yellow`/`purple`/`orange`/`pink`/`cyan` | B: 新機能で改善可 | 20-anthropic-official-spec.md §5.2 | `.claude/agents/*.md`（全8ファイル） |
| `mcpServers` キー | **全エージェントに存在しない** | エージェント専用の MCP サーバーを定義できる | B: 新機能で改善可 | 20-anthropic-official-spec.md §5.2, §6.7 | `.claude/agents/*.md` |

### 2.2 LAM 独自 agent-memory 運用と公式 memory 機構の関係

| 項目 | 現行 LAM の状態 | 最新公式仕様 | 分類 | 根拠/出典 | LAM 影響箇所(file) |
|------|--------------|------------|------|---------|------------------|
| agent-memory 運用方針 | CLAUDE.md に「Subagent は `.claude/agent-memory/<agent-name>/` に知見を蓄積できる」と記述。ただし現状エージェントの `memory` キーは未設定。プロジェクト自前運用の形式的な宣言のみ | 公式の `memory: project` は `.claude/agent-memory/<name>/` に永続保存。パスが **LAM の自前運用先と一致** | C: 要更新（影響度:中）。公式 `memory: project` を設定すれば自前記述との意図が合致するが、現状は「宣言あり・未実装」の状態。エージェントに `memory: project` を加えることで公式機構と一致させられる | 10-lam-current-dependencies.md §5; CLAUDE.md「Subagent Persistent Memory」; 20-anthropic-official-spec.md §5.7「memory: project → .claude/agent-memory/<name>/」; 50-verification.md B-7 | `CLAUDE.md`, `.claude/agents/*.md` |

### 2.3 Task → Agent ツールリネームの影響

| 項目 | 現行 LAM の状態 | 最新公式仕様 | 分類 | 根拠/出典 | LAM 影響箇所(file) |
|------|--------------|------------|------|---------|------------------|
| Task ツール → Agent ツール リネーム | `.claude/skills/lam-orchestrate/SKILL.md` のスキル本文内で `Task` ツール呼び出しへの明示的な言及があるかは本調査では確認しきれていない（コメント系は非フロントマター）。hooks の `tool_name` 等では直接参照なし | v2.1.63 で `Task` ツールが `Agent` に改名。旧名 `Task` は引き続き動作（後方互換あり） | A: 現状維持で安全（後方互換あり。ただし SKILL.md 本文に `Task(` の記述があれば将来のため `Agent(` への更新を推奨） | 20-anthropic-official-spec.md §7.4「Task → Agent リネーム（旧名は引き続き動作）」 | `.claude/skills/lam-orchestrate/SKILL.md`（要目視確認） |
| `permissions.deny` の `Agent(agent-name)` 記法 | `settings.json` の deny リストに `Agent()` 形式の記述なし | `"Agent(Explore)"` や `"Agent(my-custom-agent)"` でサブエージェント単位の制限が可能 | B: 新機能で改善可 | 20-anthropic-official-spec.md §3.1 | `.claude/settings.json` |

### 2.4 CLAUDE.md 記述陳腐化

| 項目 | 現行 LAM の状態 | 最新公式仕様 | 分類 | 根拠/出典 | LAM 影響箇所(file) |
|------|--------------|------------|------|---------|------------------|
| CLAUDE.md の agent-memory 注記「Claude Code の公式フロントマター機能ではない」 | CLAUDE.md に「Subagent が自発的に書き込む仕組みであり、Claude Code の公式フロントマター機能ではない」と記述 | 公式の `memory` キーが正式対応し、`memory: project` でパス `.claude/agent-memory/<name>/` が使用可能になっている。「公式フロントマター機能ではない」という記述は陳腐化 | C: 要更新（影響度:低）。動作に影響はないが、記述が事実と乖離している | 50-verification.md B-7; 20-anthropic-official-spec.md §5.7 | `CLAUDE.md`（Subagent Persistent Memory セクション） |

---

**Sub-agents 分類小計**

| 分類 | 件数 |
|------|-----|
| A: 現状維持で安全 | 6 |
| B: 新機能で改善可 | 16 |
| C: 要更新 | 2 |

---

## 3. 全体小計

| 領域 | A: 現状維持 | B: 改善可 | C: 要更新 | 合計 |
|------|------------|---------|---------|-----|
| Skills（フロントマター） | 4 | 10 | 1 | 15 |
| Skills（commands 統合） | 2 | 2 | 1 | 5 |
| Sub-agents（フロントマター） | 5 | 15 | 0 | 20 |
| Sub-agents（memory / 記述） | 0 | 0 | 2 | 2 |
| **合計** | **11** | **27** | **4** | **42** |

---

## 4. 「要更新（C）」項目の影響度メモ

| # | 項目 | 影響度 | 説明 |
|---|------|:------:|-----|
| C-1 | `.claude/commands/*.md` のフロントマター欠如 | 低 | 動作継続するが、Skills の新機能（`paths`, `allowed-tools`, `model` 等）を活用できない。緊急性なし。移行は任意。 |
| C-2 | CLAUDE.md の `agent-memory` 注記陳腐化 | 低 | 「公式フロントマター機能ではない」という記述が事実と乖離。誤った情報を提供しうる。動作への影響はない。 |
| C-3 | Sub-agents の `memory` キー未設定（宣言と実装の乖離） | 中 | CLAUDE.md に agent-memory 運用の意図が記述されているが、エージェントに `memory: project` キーが存在しない。意図的に書き込む仕組みを有効化するには `memory: project` 追加が必要。PM級判断（エージェント定義の変更）。 |
| C-4 | 対象外（hooks 領域は別文書） | — | — |

> C-3 は機能不全ではなく「意図の宣言と実装の乖離」であり、緊急修正は不要。次 Wave の設計検討課題として扱うことを推奨。

---

## 5. 「新機能で改善可（B）」の優先グループ整理

採否の議論はスコープ外のため事実ベースの列挙のみ。参照時の便宜として件数が多い領域をグループ化する。

| グループ | 代表キー | 件数 | 主な活用候補 |
|---------|---------|-----|------------|
| エージェント強化系 | `maxTurns`, `permissionMode`, `disallowedTools`, `effort`, `color` | 5 | 全エージェント |
| エージェント分離/バックグラウンド系 | `isolation: worktree`, `background`, `mcpServers`（エージェント内） | 3 | tdd-developer, lam-orchestrate 相当 |
| エージェントメモリ活用系 | `memory: user`, `skills`（プリロード）, `hooks`（エージェント内） | 3 | code-reviewer, quality-auditor |
| スキル起動制御系 | `disable-model-invocation`, `user-invocable`, `paths`, `when_to_use` | 4 | commands 群移行後の管理 |
| スキル実行環境系 | `allowed-tools`, `model`, `effort`（スキル内）, `shell`（PowerShell） | 4 | lam-orchestrate, magi 等 |
| スキル動的コンテキスト系 | `!`ブロック, `${CLAUDE_SKILL_DIR}`, `${CLAUDE_EFFORT}`, `argument-hint`/`arguments` | 4 | skill-creator, clarify, spec-template |
| hooks 拡張系 | `hooks` フロントマター（スキル内）, `hooks` フロントマター（エージェント内） | 2 | lam-orchestrate, pre-tool-use 相当 |
| permissions 拡張系 | `Agent(name)` deny 記法 | 1 | `.claude/settings.json` |

---

*本文書は PLANNING フェーズの成果物（文書突き合わせのみ）。実装・コード修正は一切含まない。*  
*採否の意思決定は `/planning` または別途の MAGI 合議フローで行うこと。*
