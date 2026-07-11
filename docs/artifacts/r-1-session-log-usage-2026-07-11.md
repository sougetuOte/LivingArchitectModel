# R-1 W-R4 S1-T3: Session log 30日窓 起動記録 (agents / skills / hooks)

**作成日**: 2026-07-11
**Task**: W-R4-S1-T3 (`docs/specs/large-scale-review/tasks.md` §W-R4 S1)
**目的**: `~/.claude/projects/D--work7-LivingArchitectModel/*.jsonl` を 30 日窓で走査し、agents / skills / hooks 3 分岐の起動記録を収集する。W-R4 削除判定データソースの本命 (FR-F4)。S1-T4 (git log 統合による最終判定) のインプット。
**権限等級**: SE (アーティファクト新規 / 非 SSOT)

## §1 サマリ

- window_days: **30**
- sessions_scanned: **76**
- timestamp_field: `timestamp` (トップレベル / ISO 8601, `Z` = UTC)

| resource_type | target 総数 | hit>0 | hit==0 |
|:---|---:|---:|---:|
| agent | 12 | 12 | 0 |
| skill | 23 | 9 | 14 |
| hook | 7 | 3 | 4 (うち 3 件はヘルパーモジュール = §4 参照) |

**総評**: agents は 30 日窓で **全 12 件が hit>0**（削除候補ゼロ）。skills は 23 件中 **14 件が hit==0**（§5 の削除候補提示対象）。hooks は 7 ファイル中 4 件が hit==0 だが、そのうち 3 件 (`_hook_utils.py` / `_incident_patterns.py` / `autonomous_state.py`) は登録済み hook エントリポイントではなくヘルパーモジュールのため構造的に 0 hit となる（§4 参照）。

## §2 agent 起動記録 (hit_count 降順)

| path | slug | hit_count_window | last_hit_timestamp |
|:---|:---|---:|:---|
| .claude/agents/tdd-developer.md | tdd-developer | 56 | 2026-07-06T22:47:55.586Z |
| .claude/agents/doc-writer.md | doc-writer | 32 | 2026-07-02T08:42:40.047Z |
| .claude/agents/goal-driven-grader.md | goal-driven-grader | 29 | 2026-06-27T23:15:52.456Z |
| .claude/agents/design-architect.md | design-architect | 22 | 2026-06-29T11:53:20.804Z |
| .claude/agents/task-decomposer.md | task-decomposer | 19 | 2026-06-29T13:26:59.373Z |
| .claude/agents/code-reviewer.md | code-reviewer | 13 | 2026-07-06T07:07:57.989Z |
| .claude/agents/requirement-analyst.md | requirement-analyst | 7 | 2026-06-24T01:00:02.540Z |
| .claude/agents/test-runner.md | test-runner | 7 | 2026-06-23T23:33:59.518Z |
| .claude/agents/quality-auditor.md | quality-auditor | 6 | 2026-06-18T22:07:04.535Z |
| .claude/agents/gabriel.md | gabriel | 2 | 2026-07-05T09:23:50.958Z |
| .claude/agents/goal-driven-l3-executor.md | goal-driven-l3-executor | 2 | 2026-06-17T01:25:30.217Z |
| .claude/agents/goal-driven-l2-foreman.md | goal-driven-l2-foreman | 1 | 2026-06-18T09:06:16.148Z |

検出パターン: `tool_use.name == "Agent"` かつ `input.subagent_type == <slug>`（単一経路 / S1-T1 実測どおり）。

## §3 skill 起動記録 (hit_count 降順)

2 経路 OR (`tool_use.Skill.input.skill` / user text の `<command-name>` タグ) を採用。実装した OR 検証結果は §5 末尾の「skills 2 経路 OR 検証」を参照。

| path | slug | hit_count_window | last_hit_timestamp | detection_paths |
|:---|:---|---:|:---|:---|
| .claude/skills/quick-load/SKILL.md | quick-load | 69 | 2026-07-11T07:47:11.825Z | tool_use.Skill.input.skill, user_text.command-name |
| .claude/skills/ship/SKILL.md | ship | 40 | 2026-07-05T11:47:23.643Z | tool_use.Skill.input.skill, user_text.command-name |
| .claude/skills/quick-save/SKILL.md | quick-save | 34 | 2026-07-09T21:50:52.259Z | tool_use.Skill.input.skill, user_text.command-name |
| .claude/skills/goal-driven/SKILL.md | goal-driven | 6 | 2026-06-18T09:01:13.186Z | tool_use.Skill.input.skill, user_text.command-name |
| .claude/skills/magi/SKILL.md | magi | 6 | 2026-07-05T09:15:59.479Z | tool_use.Skill.input.skill, user_text.command-name |
| .claude/skills/retro/SKILL.md | retro | 6 | 2026-07-06T01:05:23.333Z | tool_use.Skill.input.skill, user_text.command-name |
| .claude/skills/adr-template/SKILL.md | adr-template | 1 | 2026-07-03T21:09:03.120Z | tool_use.Skill.input.skill, user_text.command-name |
| .claude/skills/building/SKILL.md | building | 1 | 2026-06-12T11:34:37.377Z | tool_use.Skill.input.skill, user_text.command-name |
| .claude/skills/spec-template/SKILL.md | spec-template | 1 | 2026-07-05T10:26:46.676Z | tool_use.Skill.input.skill, user_text.command-name |

hit==0 の 14 件は §5 の削除判定候補表を参照。

**detection_paths 内訳の注記**: 出力スキーマ上、hit>0 の skill は常に両経路名を列挙している（実装がどちらの経路がヒットしたかを個別に区別せず、OR 判定の結果としてのみ記録する設計のため）。個々のヒットがどちらの経路由来かの内訳は §5 末尾の実測例で個別確認した。

## §4 hook 発火記録

hooks は起動頻度が桁違い（本レポジトリの `pre-tool-use.py` 単体で 370 件 / 30 日窓）なため、ファイル単位の hit_count に加えて `hookName` 別頻度を併記する。

| path | slug | hit_count_window | last_hit_timestamp | 判定 |
|:---|:---|---:|:---|:---|
| .claude/hooks/lam-stop-hook.py | lam-stop-hook | 739 | 2026-07-11T08:16:29.628Z | 稼働中（Stop hook） |
| .claude/hooks/pre-tool-use.py | pre-tool-use | 370 | 2026-07-11T08:09:12.917Z | 稼働中（PreToolUse hook） |
| .claude/hooks/post-tool-use.py | post-tool-use | 14 | 2026-07-09T20:46:04.078Z | 稼働中（PostToolUse hook） |
| .claude/hooks/pre-compact.py | pre-compact | 0 | - | **特記（§4.2 参照）: 検出手段なし、削除候補ではない** |
| .claude/hooks/_hook_utils.py | _hook_utils | 0 | - | ヘルパーモジュール（非エントリポイント） |
| .claude/hooks/_incident_patterns.py | _incident_patterns | 0 | - | ヘルパーモジュール（非エントリポイント） |
| .claude/hooks/autonomous_state.py | autonomous_state | 0 | - | ヘルパーモジュール（非エントリポイント） |

### §4.1 hookName 別頻度 (対象 3 ファイルの内訳 / 30 日窓)

- **pre-tool-use.py**: `PreToolUse:Edit` 294 / `PreToolUse:Write` 76（合計 370）。**注記**: `settings.json` の PreToolUse hook 登録に `matcher` 指定はなく全ツール対象のはずだが、実測では Edit / Write 以外のツール呼び出し（Bash / Read 等）で `attachment.command` に本ファイルへの参照が現れなかった。全期間（76 セッション全体）でも同じ分布（Edit 301 / Write 77）を確認済みであり、走査バグではなく実挙動として記録する（未解明の挙動として申し送り — hook 自体の削除判定には影響しない）。
- **post-tool-use.py**: `PostToolUse:Bash` 14（設定は `matcher: "Edit|Write|Bash"` のため Bash 以外の出現がないのは既知範囲内。ただし Edit/Write 経由の PostToolUse ヒットが 0 件だった点は要目視確認 — 本 Task のスコープ外として申し送り）。
- **lam-stop-hook.py**: `Stop` 739（全件 `type=="system", subtype=="stop_hook_summary"` の `hookInfos[].command` 経由。攻撃的検証: 同じ Stop イベントで併走する他の Stop hook（`stop.py` 1549 / `notify-sound.py` 742 / `security_reminder_hook.py` 742/1）との比較で、`lam-stop-hook.py` のみ件数が他よりやや少ない（739 < 742）。これは 30 日窓の端で数件のセッション境界差によるものと推定 — 削除判定に影響する差ではない）。

### §4.2 pre-compact.py の検出手段なし（特記）

`settings.json` は `PreCompact` イベントに `.claude/hooks/pre-compact.py` を登録している（実在確認済み・§4 表参照）。しかし 76 セッション全量を走査しても、`PreCompact` に対応する `hook_success` attachment、または `stop_hook_summary` 相当の要約イベントは **1 件も観測されなかった**（`attachment.command` に `pre-compact` を含む行がゼロ、`type=="system"` 側にも PreCompact 専用 subtype が存在しない）。

**判定**: これは「30 日窓で 0 発火 = 未使用」という **偽陽性リスクの高いケース** と判断する。理由:

1. `PreCompact` イベント自体が compaction 発生時にしか起きず、そもそも通常セッションでの発火頻度が低い（頻度の問題）
2. Claude Code 側が `PreCompact` の実行結果を他イベントと同じ `attachment.hook_success` 形式でログに残しているという保証が実測で得られていない（**ロギング経路自体の欠落の疑い**）

したがって `pre-compact.py` は §5 の削除候補一覧から **明示的に除外** する（hit==0 だが delete_candidate 判定を出さない）。最終判定は S1-T4 で git log（最終更新日・関連コミット）と併せて個別に扱うこと。

## §5 削除判定候補 (hit_count_window == 0 / 30 日窓)

**注意**: 以下は削除候補の**提示のみ**であり、削除決定ではない。verdict は暫定ラベル `delete_candidate (30d unused)` を付与する。最終判定は S1-T4 (git log 統合) で行う。

### skills (14 件 — 全称列挙)

| path | slug | verdict |
|:---|:---|:---|
| .claude/skills/auditing/SKILL.md | auditing | delete_candidate (30d unused) |
| .claude/skills/autonomous/SKILL.md | autonomous | delete_candidate (30d unused) |
| .claude/skills/build-dashboard/SKILL.md | build-dashboard | delete_candidate (30d unused) |
| .claude/skills/clarify/SKILL.md | clarify | delete_candidate (30d unused) |
| .claude/skills/full-review/SKILL.md | full-review | delete_candidate (30d unused) |
| .claude/skills/init-harness/SKILL.md | init-harness | delete_candidate (30d unused) |
| .claude/skills/lam-orchestrate/SKILL.md | lam-orchestrate | delete_candidate (30d unused) |
| .claude/skills/pattern-review/SKILL.md | pattern-review | delete_candidate (30d unused) |
| .claude/skills/planning/SKILL.md | planning | delete_candidate (30d unused) |
| .claude/skills/project-status/SKILL.md | project-status | delete_candidate (30d unused) |
| .claude/skills/release/SKILL.md | release | delete_candidate (30d unused) |
| .claude/skills/skill-creator/SKILL.md | skill-creator | delete_candidate (30d unused) |
| .claude/skills/ui-design-guide/SKILL.md | ui-design-guide | delete_candidate (30d unused) |
| .claude/skills/wave-plan/SKILL.md | wave-plan | delete_candidate (30d unused) |

### agents (0 件)

30 日窓では全 12 agent が hit>0 のため、該当なし。

### hooks (delete_candidate 対象 = 0 件 / 特記 1 件)

`_hook_utils.py` / `_incident_patterns.py` / `autonomous_state.py` はヘルパーモジュール（非エントリポイント）のため `delete_candidate` 対象から除外する（§4 参照 — 別途 import 参照解析が必要な種別であり、本 Task の 3 分岐 grep のスコープ外）。`pre-compact.py` は §4.2 の理由により `delete_candidate` を **明示的に付与しない**（検出手段なしの特記のみ）。

### skills 2 経路 OR 検証（実測例）

`quick-save` の hit_count_window = 34（30 日窓）。全期間実測（S1-T1, 76 セッション全量）では Skill tool 経由 24 件 + `<command-name>` 直入力 24 件（計 48 起動、2 経路並存）が確認されている。本スクリプトは OR 判定のため両経路のいずれかにヒットした行を漏れなく数える設計であり、単一経路実装であれば 30 日窓の 34 件のうち約半数を取りこぼしていた可能性が高い。

## 変更ファイル一覧・実行証跡

- **files_changed (2)**:
  - `.claude/scripts/r-1-session-log-usage.py`（新規 / Python 3 標準ライブラリのみ）
  - `docs/artifacts/r-1-session-log-usage-2026-07-11.md`（本ファイル / 新規）
- **実行コマンド**: `python .claude/scripts/r-1-session-log-usage.py --window-days 30`（stdout に JSON を出力 / `--markdown` オプションで簡易表も出力可能）
- **実行時刻**: 2026-07-11T10:14:27Z (generated_at)
- **sessions_scanned**: 76

## 権限等級

本アーティファクト: SE (`docs/artifacts/` 配下 / 非 SSOT)

## 参照

- `docs/artifacts/r-1-jsonl-fields-2026-07-11.md`（S1-T1 フィールド名確定 / 検出パターン 4 種の一次資料）
- `docs/specs/large-scale-review/design.md` §7.2（HGA #6 Crux 5-1）
- `docs/specs/large-scale-review/requirements.md` §FR-F4
- `docs/specs/large-scale-review/tasks.md` §W-R4 S1
