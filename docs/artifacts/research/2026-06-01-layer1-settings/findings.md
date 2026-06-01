# 裏取り結果: T1-4 層1（permissions.deny を autonomous 専用 settings に注入）

調査日: 2026-06-01 / 担当: Living Architect(Opus) + リサーチ subagent×3 / フェーズ: BUILDING（Wave 1 / T1-4 層1）
対象: design D7 層1（`permissions.deny` を FR9_PATTERNS に上書き不可で固定）の**注入手段**
手段: context7（`/websites/code_claude`）×3 + WebFetch（settings ページ全文）+ WebSearch（subagent 経由）。多重クロスチェック。
前回の保留: SESSION_STATE「層1 注入書式が未裏取り」を本調査でクローズ。

> upstream-first 二段構え（planning-quality-guideline §7）に従い、段階1（実在性）/段階2（LAM 適合性）を分けて評価する。

---

## 結論（先出し）

**選択肢2（autonomous 専用 settings）を `claude --settings <file>` で注入する案が成立**。
- `--settings <file|inline-json>` は実在（cli-reference）。読み込まれた値は **precedence 第2位「command line arguments」**（settings ページ直 fetch で確定）。
- deny は **deny-first・any-scope の deny が any-scope の allow に優先**（cannot be overridden except by managed）。
- ⇒ 専用 settings の deny は autonomous 起動セッションでのみ効き、**人間の通常セッションは無縛り＝自己ロック回避**。共有 `.claude/settings.json` には FR9 deny を置かない（前回決定を裏取りで追認）。

---

## 段階1: 実在性

### A. settings precedence（RQ-A）

**[確認済]** 出典: WebFetch `code.claude.com/docs/en/settings`（全文）原文:
> 1. **Managed** (highest) - can't be overridden by anything
> 2. **Command line arguments** - temporary session overrides
> 3. **Local** - overrides project and user settings
> 4. **Project** - overrides user settings
> 5. **User** (lowest)

### B. deny の評価順・override 不可性（RQ-C precedence / RQ-D）

**[確認済]** 出典: `code.claude.com/docs/en/permissions`（subagent R2 全文取得）原文:
> "Rules are evaluated in order: **deny -> ask -> allow**. The first matching rule wins, so deny rules always take precedence."
> "If a tool is denied at any level, no other level can allow it."
> "a user-level deny blocks a project-level allow, because deny rules from any scope are evaluated before allow rules."

managed の最強性（同・"Settings precedence" 節）:
> "Managed settings: cannot be overridden by any other level, **including command line arguments**"

**含意**: `--settings`（=command line arguments・第2位）の deny は Local/Project/User の allow を上回り、**managed（無し）以外では覆らない**。autonomous セッション内で FR-9.1 を決定的に強制できる。

### C. 注入手段（RQ-B / RQ-F）

**[確認済]** 出典: context7 `cli-reference` 原文:
> "**`--settings`**: Pass a path to a settings JSON file **or inline JSON string** to override settings for the session." 例: `claude --settings ./settings.json`
> "**`--setting-sources`**: Specify comma-separated list of setting sources to load (user, project, local)." 例: `claude --setting-sources user,project`
> "**`--disallowedTools`**: Deny rules. ... A scoped rule such as `Bash(rm *)` leaves the tool available and denies only matching calls." 例: `"Edit"`／`"Bash(git log *)"`

→ 注入の選択肢は3つ:
| 手段 | 形態 | 評価 |
|------|------|------|
| **`--settings <file>`** | 専用 JSON ファイル | ◎ 推奨（deny + auto mode + disableBypass を一括・版管理可） |
| `--settings '<inline json>'` | インライン JSON | ○ 起動コマンドが長大化 |
| `--disallowedTools "Edit(...)" ...` | CLI 直 deny | △ エントリ数だけ冗長・auto mode 同梱不可 |

### D. permissions.deny の書式（RQ-C）

**[確認済]** 出典: R2（permissions ページ全文）+ context7（server-managed-settings / settings 例）:
- **`Edit(<path>)` 1本で `Write`・`MultiEdit` を含むファイル編集系ビルトイン全てをカバー**（原文 "Edit rules apply to all built-in tools that edit files."）。`Write(...)` 別記は不要（ただし `NotebookEdit` のカバーは未確認）。
- パスパターンは **gitignore 仕様**:
  | 書式 | 意味 |
  |------|------|
  | `//path` | FS ルート絶対 |
  | `~/path` | ホーム |
  | `/path` | **プロジェクトルート相対** |
  | `path` / `./path` | cwd 相対 |
  - `*`=単一ディレクトリ / `**`=再帰。`/Users/x` は**絶対でなくプロジェクト相対**（注意）。
  - Windows: POSIX 正規化（`C:\Users\alice`→`/c/Users/alice`）。
- deny の公式例（settings ページ）: `"deny": ["Bash(curl *)", "Read(./.env)", "Read(./secrets/**)"]`
- subagent deny も可: `"deny": ["Agent(Explore)"]`。

### E. protected paths（新発見・FR-9 設計に直結）

**[確認済]** 出典: R3（permission-modes / auto-mode-config）原文:
> "In every mode except `bypassPermissions`, writes to protected paths are never auto-approved ... Protected directories: `.git`, `.vscode`, `.idea`, `.husky`, `.cargo`, `.claude`, **except for `.claude/commands`, `.claude/agents`, `.claude/skills`, and `.claude/worktrees`**"
> auto mode では protected paths は "route to the classifier"。

**🔴 重要な含意**:
- `.claude/skills` は **protected の例外**＝デフォルト保護されない。よって **`.claude/skills/autonomous/**` は明示 deny が必須**（classifier 任せにできない＝層1 の存在意義）。
- `.claude/rules` / `.claude/hooks` / `.claude/settings*.json` はデフォルト protected だが、auto mode では **classifier（非決定的・soft）にルーティング**。決定的保証には明示 deny が必要。
- `docs/adr/**` は `.claude` 外＝完全に無保護。明示 deny 必須。

### F. auto mode と permissions.deny の前段関係（RQ-E）

**[確認済]** 出典: R3（auto-mode-config）原文:
> "The classifier is a second gate that runs after the permissions system. For actions that must never run regardless of user intent or classifier configuration, use `permissions.deny` in managed settings, **which blocks the action before the classifier is consulted and cannot be overridden**."

hook との独立性（permissions ページ）:
> "Hook decisions do not bypass permission rules. Deny and ask rules are evaluated regardless of what a PreToolUse hook returns ... This preserves the deny-first precedence ... including deny rules set in managed settings."

→ **層1（permissions.deny）は層2（PreToolUse hook）と独立**。hook の戻り値に関係なく deny が効く＝二重防御が成立。

### G. auto mode / 専用 settings の制約

**[確認済]** 出典: R3 + WebFetch settings:
- `autoMode` ブロック・`defaultMode:"auto"`（v2.1.142+）は **共有 project/local settings からは読まれない**。`~/.claude/settings.json` / managed / **`--settings`（CLI scope）** で指定。
- auto mode は **Anthropic API のみ**（Bedrock/Vertex/Foundry 不可）/ Model Opus 4.6+ or Sonnet 4.6+。本環境（Max 5x = Anthropic API）は可（findings 2026-05-30 §E で確認済）。
- `disableBypassPermissionsMode: "disable"`（**any scope で有効**・`--dangerously-skip-permissions` を無効化）/ `disableAutoMode`（auto を拒否＝今回は付けない）。
- `allowManagedPermissionRulesOnly`（managed のみ・user/project/local の allow/ask/deny を全無効化）。

### H. block cap / /goal 前提（既裏取りの再確認）

**[確認済]**（findings 2026-05-30 P-2a と一致）: `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`（既定8 / `0` 無効化 / 8連続 block で override / `stop_hook_active` 早期 exit）。`/goal` は trust dialog 必須・`disableAllHooks`/`allowManagedHooksOnly` 時不可。

---

## 段階2: LAM 適合性（選択肢2 = `--settings` 専用 deny の評価）

| 観点 | 評価 |
|------|------|
| **決定的境界**（FR-9.1 MUST NOT）| ◎ permissions.deny は classifier・hook 前段で決定的・any-scope allow を覆す。autonomous セッション内で確実に効く |
| **自己ロック回避** | ◎ 専用 settings は `--settings` 起動時のみ。人間の通常 `claude` は無縛り。共有 settings.json に常時 deny を置かない（前回決定を追認）|
| **承認ゲート維持** | ◎ 人間が意図的に autonomous セッションを起動。統治ファイル変更はループ外の人間ゲートに残る |
| **フェイルセーフ** | △ `--settings` を付け忘れると層1 が無効（層2=phase 条件 deny は残る）。→ **`/autonomous` 起動時に層1 有効性を自己点検し、無ければ warn/中止**する fail-safe を MVP に追加すべき |
| **Zero-Regression** | ◎ 共有 settings 不変＝既存フロー無回帰。専用 settings は追加ファイル |

**段階2 結論**: 選択肢2 は LAM 思想と整合。**採用可**。ただしフェイルセーフ（起動自己点検）を実装で補う。

---

## 推奨実装（公式書式準拠）

### 専用 settings ファイル `.claude/settings.autonomous.json`

> 命名を `settings.autonomous.json` とすると、既存 FR9_PATTERN `.claude/settings*.json`（層2 pre-tool-use.py）と層1 deny の**両方で自己保護**される（`settings*.json` glob にマッチ）。

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "defaultMode": "auto",
    "disableBypassPermissionsMode": "disable",
    "deny": [
      "Edit(/.claude/rules/**)",
      "Edit(/.claude/hooks/**)",
      "Edit(/.claude/skills/autonomous/**)",
      "Edit(/.claude/settings.json)",
      "Edit(/.claude/settings.local.json)",
      "Edit(/.claude/settings.autonomous.json)",
      "Edit(/docs/adr/**)"
    ]
  }
}
```
- `Edit(...)` で Write/MultiEdit もカバー（公式）。**MUST NOT 境界なので belt-and-suspenders で `Write(...)` 同型も併記するか**は実装判断（NotebookEdit 未確認のため安全側で併記も可）。
- `/path` はプロジェクトルート相対。`**` 再帰。
- `disableBypassPermissionsMode:"disable"` で `--dangerously-skip-permissions` 経由の deny 回避を封鎖。

### 起動コマンド（autonomous セッション）

```bash
claude --permission-mode auto --settings .claude/settings.autonomous.json
# 中で /autonomous <spec> → /goal "..."
```
- `--permission-mode auto` を明示（settings の defaultMode と二重で確実化）。
- 共有 project settings（hooks: lam-stop-hook / pre-tool-use 等）は通常どおりロードされ、専用 deny が CLI scope で上乗せされる（merge）。

---

## 未確認・残リスク（推測実装禁止・要実機 or 追加調査）

1. **`--settings` の merge vs replace**: project settings（hooks）がロードされ続けるか、置換されないかは**初回実機起動で要確認**（precedence 記述上は merge＝上乗せと解釈。低リスク）。
2. **`--settings` の `--resume`/`--continue` 持続**: resume 時に専用 settings が残るか未文書。→ **設計で回避**: 起動・再開とも常に `--settings` を付与する運用契約にする（FR-7.1）。
3. **エンジンの脱獄**: 自律エンジンが `--settings` 無しで `claude` を再起動 / bypassPermissions へ切替えて deny を回避する経路。→ `disableBypassPermissionsMode` + auto mode の bypass/"Create Unsafe Agents" 既定ブロック + **MVP は人間監視下**で緩和。完全封鎖は将来課題。
4. **`NotebookEdit` の Edit カバー**: 未確認。統治ファイルは notebook でないため実害なしだが、安全側なら `Write(...)` 併記。
5. **Self-Modification 既定ルール原文**: engineering blog が auto mode classifier にブロックされ全文未取得。ただし**本設計は明示 deny に依存**するため非ブロッカー。

---

## 反映先（PM ゲートを要する変更）

| 対象 | 等級 | 内容 |
|------|------|------|
| `.claude/settings.autonomous.json`（新規）| **PM**（settings）| 上記 deny + auto mode |
| `docs/specs/autonomous-mode/design.md` D7 | **PM**（spec）| 「共有→専用 settings via `--settings`・CLI scope・自己ロック回避」へ精緻化 |
| `docs/specs/autonomous-mode/tasks.md` T1-4(b) | **PM**（spec）| 完了条件を専用 settings 注入へ更新 |
| `.claude/skills/autonomous/SKILL.md` 前提条件 | **PM**（mode 定義）| 起動フラグ + 層1 自己点検 fail-safe を追記 |
| （任意）層1 内容テスト | SE | settings.autonomous.json の JSON 妥当性 + FR9 deny 網羅を検証 |

## 出典一覧

- `code.claude.com/docs/en/settings`（precedence / autoMode / disableBypass / disableAutoMode / allowManagedPermissionRulesOnly）
- `code.claude.com/docs/en/permissions`（deny-first / any-scope / Edit カバー / gitignore glob / symlink / Windows 正規化 / managed override 不可）
- `code.claude.com/docs/en/cli-reference`（`--settings` file|inline / `--setting-sources` / `--disallowedTools` / `--permission-mode auto`）
- `code.claude.com/docs/en/permission-modes` + `auto-mode-config`（classifier 4-tier / permissions.deny 前段・override 不可 / protected paths / API 限定 / モデル要件）
- `code.claude.com/docs/en/goal`（/goal=prompt Stop hook ラッパー / hooks 前提 / auto mode 補完）
- `code.claude.com/docs/en/hooks-guide` + `env-vars`（block cap=8 / `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`）
