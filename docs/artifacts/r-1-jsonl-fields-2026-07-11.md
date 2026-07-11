# R-1 W-R4 S1-T1: jsonl 起動記録フィールド名確定

**作成日**: 2026-07-11
**Task**: W-R4-S1-T1 (`docs/specs/large-scale-review/tasks.md` L212)
**目的**: HGA #6 Crux 5-1 の要検証仮定「skills も subagent_type で grep できるか」を実測で解消し、W-R4 S1-T3 (session log 30 日窓 grep スクリプト) の実装対象フィールド名を確定する
**権限等級**: SE (アーティファクト新規 / SSOT ではない)

## 1. 実測条件

- **対象**: `~/.claude/projects/D--work7-LivingArchitectModel/*.jsonl` 全 76 セッション
- **走査スクリプト**: `<scratchpad>/jsonl_probe_all.py`
- **Claude Code バージョン範囲**: 2.1.205 前後 (直近セッション実測)

## 2. 検出パターン確定表 (HGA #6 Crux 5-1 解消)

W-R4 S1-T3 session log grep の 3 分岐に対応。

| リソース種別 | 起動判定パターン (jsonl 内) | 実測件数 (76 sessions) | 補足 |
|:------|:--------|---:|:-----|
| **skills (Skill tool 経由)** | `tool_use.name == "Skill"` かつ `input.skill == <slug>` | 76 起動 / `input.skill` 全件必須 / `input.args` は 23 件のみ (任意) | 例: `{"name":"Skill","input":{"skill":"quick-save"}}` |
| **slash commands (`/name` 直入力)** | user message 内テキストの `<command-name>/([^<]+)</command-name>` タグ | 117 出現 / 実測 slug: `/quick-load` 72, `/quick-save` 24, `/ship` 10, `/goal-driven` 6, `/model` 1, `/building` 1, `/build-mode` 1, `/magi` 1, `/retro` 1 | Skill tool を挟まず直接コマンド化されるルートで発火 |
| **agents (subagent)** | `tool_use.name == "Agent"` かつ `input.subagent_type == <agent-name>` | 532 起動 / `input.subagent_type` 全件必須 / `input.description` `input.prompt` も全件必須 / `input.model` 320 / `input.run_in_background` 72 | 従来通り subagent_type で判定可 |
| **hooks** | `attachment.type == "hook_success"` かつ `hookName` (`PreToolUse:<Tool>` 等) + `hookEvent` (`PreToolUse` / `PostToolUse` / `Stop`) | 12,421 発火 / hookName + hookEvent 全件必須 | 3 分岐は判定粒度が違う (skills 系は起動、hooks 系は発火頻度) |

## 3. Crux 5-1 の実測反証・追認

design.md §7.2 の主張「skills も subagent_type で grep すると全 skills が hit 0 で偽陽性削除の直行便になる」は **実測で追認**:

- 全 76 セッション横断で **skills が subagent_type フィールドに現れた実例は 0 件** (subagent_type は Agent tool 専用フィールド)
- skills 起動 76 件は全て `tool_use.name == "Skill"` 経由であり、独立の判定パスが必要

**結論**: HGA #6 Crux 5-1 の懸念は正当。W-R4 S1-T3 は 3 分岐 (agents / skills / hooks) それぞれ独立パターンで実装する必要がある。

## 4. skills 検出の完全性ノート (S1-T3 実装者向け)

`tool_use.name == "Skill"` だけでは **`<command-name>` 直入力ルートの skill 起動が漏れる**:

- 実測: `/quick-save` は Skill tool 経由 24 件 + `<command-name>` 直入力 24 件 (合計 48 起動) — 2 経路が並存
- 30 日窓 grep で「skill 起動 = 0」判定を出す前に、**両経路の OR** を取ること
- pseudo: `(tool_use.name == "Skill" && input.skill == <slug>) || <command-name>/<slug></command-name> in user text`

同様に slash command 化した skill (`.claude/commands/` にラッパーがあるもの) は tool_use を経由しない発火経路がある。tier=utility の skill でこの経路を持つものは W-R4 S3-T1 (skills 削除候補確定) で個別に確認。

## 4.5 hooks の第 2 event shape 追補 (S1-T3 実装中に発見 / 2026-07-11 追記)

S1-T3 (session log 30 日窓 grep) 実装中、L2 Sonnet subagent が本メモ §2 に **未記載の第 2 event shape** を発見:

- **Stop-hook** は `attachment.type == "hook_success"` ではなく、**top-level イベント** として記録される:
  - `type == "system"` かつ `subtype == "stop_hook_summary"`
  - hook 名は `hookInfos[].command` に格納 (`hookName` ではない)
- §2 のパターン (`attachment.hook_success` + `hookName` + `hookEvent`) は **PreToolUse / PostToolUse 系のみ** カバーする
- Stop-hook 検出は独立実装が必要

**影響範囲**: `.claude/hooks/lam-stop-hook.py` 等の Stop 系 hook の起動記録は §2 の単一パターンだけでは取り逃す。S1-T3 スクリプトは両パターン実装済 (`docs/artifacts/r-1-session-log-usage-2026-07-11.md` §4 参照)。

**未確認**: `PreCompact` hook (`.claude/hooks/pre-compact.py`) は 76 セッション全期間で 0 hit / 対応 event shape 特定不能 (両パターンでも捕捉されず)。**logging-coverage gap の可能性が高く** (実装上は稼働しているはず)、S1-T4 usage-baseline では **hold_low_confidence verdict** を付与予定。

## 5. hooks 判定粒度の注意

hooks は起動頻度が桁違い (12,421 発火 vs skills 76 起動) のため、「90 日窓で 0 発火 = 削除候補」判定は skills / commands / agents と同じ閾値では使えない。W-R4 S3-T4 (hooks 重複統合) の判定基準は別途設計するべき (本 Task の scope 外だが申し送り)。

## 6. データソース確定判定 (S1-T5 用インプット)

| 判定軸 (design §7.5) | 結果 |
|:------|:-----|
| フィールド名確定 (S1-T1 完了条件) | **成功** (skills / commands / agents / hooks 4 種別すべて実測ベースで確定) |
| 種別別パターン分岐 (Crux 5-1) | **確定** (3 分岐実装可能) |
| 30 日窓 grep 実装可能性 | **成功** (jsonl 直読 + タイムスタンプ `timestamp` フィールド既存 + 76 セッション分の実データあり) |

→ S1-T5 データソース確定判定 = **成功 verdict の見込み** (S1-T2/T3/T4 の実装で最終確定)

## 7. S1-T2/T3 実装者への引継ぎ事項

- **S1-T2 git log スクリプト**: `git log --diff-filter=D --name-only` で削除履歴、`git log --follow` で改名履歴。フィールド名は git 側のため本メモの対象外
- **S1-T3 session log 30 日窓 grep**: 上表 §2 の 4 パターンをそのまま実装。skills 分岐は §4 の 2 経路 OR が必須
- **S1-T4 usage-baseline.md**: 各 target_path に対し `hit_count` (30 日窓) + `last_hit_timestamp` + `verdict` (delete_candidate / keep_recent_modified / hold_low_confidence) を付与

## 8. 実測補助データ (参考)

76 セッション横断の tool_use 分布 (top 10):

```
1331 Bash        738 Read       486 TaskCreate    238 Write     138 Glob
1001 Edit        532 Agent      238 Write         225 Grep       89 ToolSearch
854 TaskUpdate                                                    76 Skill
```

attachment.type 分布 (skills / hooks / agent 関連の代表):

```
12421 hook_success       90 skill_listing      65 agent_listing_delta
185 command_permissions  39 auto_mode          14 hook_system_message
```

## 権限等級

本アーティファクト: SE (`docs/artifacts/` 配下 / 非 SSOT)

## 参照

- `docs/specs/large-scale-review/tasks.md` §W-R4 S1-T1 (L212)
- `docs/specs/large-scale-review/design.md` §7.2 §7.5 (HGA #6 Crux 5-1 出典)
- `docs/specs/large-scale-review/requirements.md` FR-F4 (2026-07-05 再定義)
- `docs/artifacts/hga-summon-log.md` #6 (Crux 5-1 原記録)
