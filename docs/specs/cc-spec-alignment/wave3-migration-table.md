# Wave 3 移行判定表: commands → skills（C-1 解消）

最終更新: 2026-05-29 / フェーズ: BUILDING / 親: [design.md](design.md) §7.5（approved）
タスク: T3-0（起動セマンティクス判定）/ 等級: PM

## 1. 決定（2026-05-29 ユーザー承認）

**全11本を「手動限定」で統一移行する。** `disable-model-invocation: true` を付与し、
移行前 commands と同じ「人間が明示起動」挙動を完全保証する（Zero-Regression 優先）。

> 唯一の自動起動候補だった `project-status`（読み取り専用・副作用なし）も、
> Wave 3 の主目的を C-1 の機械的移行に限定し、自動起動の活用は将来の別タスクへ切り出す方針で
> 手動限定に含める判断をユーザーが選択（AskUserQuestion, 2026-05-29）。

## 2. 公式フロントマター書式（裏取り済み・upstream-first）

出典: code.claude.com/docs/en/{skills, slash-commands, best-practices, claude-directory}（context7 `/websites/code_claude`, 2026-05-29）

| キー | 用途 | 本移行での扱い |
|------|------|---------------|
| `name` | スキル名 | 必須・コマンド名と同一 |
| `description` | 用途説明（自動起動判断に使用） | 必須・既存 description を踏襲 |
| `disable-model-invocation: true` | **モデル自動起動を禁止**（手動起動のみ許可） | **全11本に付与** |
| `argument-hint` | 引数ヒント | 引数を取る4本に付与 |
| `$ARGUMENTS` | 本文中の引数プレースホルダ | 引数を取る本で使用 |
| `allowed-tools` | ツール最小権限 | **付与しない**（運用系は Bash/Task/Write 等を要し、制限は回帰リスク） |
| `model` | モデル委譲 | **付与しない**（inherit 維持。Wave 2 はテンプレート系のみ sonnet 化） |
| `paths` | パス自動適用 | **付与しない**（これらは起動型であってパストリガ型ではない） |

> 設計 §7.5 が言及した `user-invocable` は独立キーではなく、`disable-model-invocation: true` が
> 「ユーザー起動のみ／モデル自動起動なし」を表現する正式書式である（裏取りで確定）。

## 3. 判定表（11本）

| # | コマンド | タスク | 性質 | 副作用 | 引数 | 判定 |
|---|---------|:------:|------|--------|------|------|
| 1 | planning | T3-1 | フェーズ切替・承認ゲート | フェーズ状態変更 | なし | 手動限定 |
| 2 | building | T3-2 | フェーズ切替・承認前提チェック | フェーズ状態変更 | なし | 手動限定 |
| 3 | auditing | T3-3 | フェーズ切替 | フェーズ状態変更 | なし | 手動限定 |
| 4 | full-review | T3-4 | ワンショット自動ループ | 状態ファイル生成・自動コード修正 | 対象パス（必須） | 手動限定 |
| 5 | pattern-review | T3-5 | TDDパターン審査 | ルール昇格・削除（PM級） | なし | 手動限定 |
| 6 | project-status | T3-6 | 進捗表示 | 読み取り専用 | なし | 手動限定 |
| 7 | quick-load | T3-7 | セッション復帰 | SESSION_STATE.md 読込 | なし | 手動限定 |
| 8 | quick-save | T3-8 | セッション保存 | ファイル書込（STATE/Daily） | なし | 手動限定 |
| 9 | retro | T3-9 | 振り返り | ルール候補生成（PM級） | wave/phase | 手動限定 |
| 10 | ship | T3-10 | コミット | git commit | dry-run | 手動限定 |
| 11 | wave-plan | T3-11 | Wave計画・承認ゲート | 計画策定 | N | 手動限定 |

### 引数を取る本（`argument-hint` 付与対象）

| コマンド | argument-hint | 既存引数仕様 |
|----------|---------------|-------------|
| full-review | `<対象ファイル or ディレクトリ>` | 対象パス（必須） |
| retro | `[wave\|phase]` | デフォルト wave |
| ship | `[dry-run]` | dry-run で Phase 4 まで |
| wave-plan | `[N]` | デフォルト次 Wave |

## 4. 同名競合チェック（T3-0 完了条件）

プロジェクト `.claude/skills/` の既存7スキル（adr-template, spec-template, ui-design-guide,
clarify, lam-orchestrate, magi, skill-creator）と移行対象11本に **名前の重複なし** ✅

> 注: User スコープ（`~/.claude/skills/`）に同名（project-status, retro, ship 等）が存在しうるが、
> Project スコープが優先されるため移行に支障なし。これは移行前の commands でも同条件で、
> 新たな競合を生まない。

## 5. 移行手順（各 T3-N 共通）

1. `.claude/skills/<name>/SKILL.md` を作成
   - フロントマター: `name` / `description` / `version` / `disable-model-invocation: true`（+ 引数本は `argument-hint`）
   - 本文: 既存 `.claude/commands/<name>.md` の本文を移植（引数本は `$ARGUMENTS` 化を検討）
2. 旧 `.claude/commands/<name>.md` の除去
   - **AI はファイル削除を実行しない**（憲法・security-commands.md deny）
   - `git rm`（ask級）でユーザー承認のうえ実施、または `/ship` 内で一括処理、または手動削除
3. 回帰確認: 手動起動が従来どおり機能 / 既存テスト無回帰

> 旧コマンドファイルを残すと同名スキルが二重登録され競合するため、除去は必須。
> 除去タイミング（各コミット内 / Wave 3 末尾一括）は実装時にユーザーと確定する。

## 6. Wave 3 完了判定

- 11本すべて `.claude/skills/<name>/SKILL.md` へ移行済み
- 旧 `.claude/commands/*.md` 11本が除去済み（同名競合の解消）
- 各起動挙動が本表と一致（全本 disable-model-invocation: true）
- SC-4 回帰なし（pytest）
