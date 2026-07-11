# R-1 W-R4-S1-T2: git log usage scan (2026-07-11)

**目的**: `.claude/` 配下の agents / skills / hooks / commands について git log 全期間から
(a) 削除履歴 と (b) 改名履歴 を収集する。FR-F4 削除判定データソースの補助情報
(design.md §7.1 「主データソース: git log 最終 touch commit の日付 / 改名追跡: --follow で補完」)。

**スクリプト**: `.claude/scripts/r-1-git-log-usage.py`（Python 標準ライブラリのみ・依存なし）

**実行コマンド**:
```bash
python .claude/scripts/r-1-git-log-usage.py            # JSON (schema は script docstring 参照)
python .claude/scripts/r-1-git-log-usage.py --markdown # Markdown 表
```

---

## §1 サマリ

| resource_type | 現存 target_path 数 | 削除済履歴数 (orphan) | 改名済履歴数 |
|:---|---:|---:|---:|
| agent | 12 | 0 | 0 |
| skill | 23 | 3 | 11 |
| hook | 7 | 0 | 0 |
| command | **0** | 7 | 0 |
| **合計** | **42** | **11** (uniq path) | **11** |

- `command` は現存 target_path が **0 件**（`.claude/commands/` ディレクトリは存在するが追跡ファイルなし）。
  2026-05-29 の一括移行 (commit `8c83019481c7...`) で `.claude/commands/*.md` → `.claude/skills/*/SKILL.md`
  へ 11 件が改名され、その他 7 件は 2026-03-13 (commit `e1426491d686...`) に削除済み。
  結果として command 種別は「実体ゼロ・履歴のみ現存」の状態（省略せず count=0 として明示）。
- 改名 11 件は全て 2026-05-29 の単一コミット (`8c83019481c795c0f9cec1e2972fe44d2a359fac`) による
  `.claude/commands/*.md` → `.claude/skills/*/SKILL.md` 一括移行。
- 削除（orphan）11 件のうち 7 件は command 種別（2026-03-13 一括削除）、3 件は skill 種別
  （`ultimate-think` 2026-03-13 削除 / `auditing-guardrail` `building-guardrail` `planning-guardrail`
  2026-01-05 削除）。agent / hook 種別に削除履歴はなし。

---

## §2 現存 target_path 一覧

### agent (12)

| path | first_commit | last_commit | commit_count |
|:---|:---|:---|---:|
| `.claude/agents/code-reviewer.md` | 2026-02-15 | 2026-07-10 | 8 |
| `.claude/agents/design-architect.md` | 2025-12-08 | 2026-07-10 | 10 |
| `.claude/agents/doc-writer.md` | 2026-02-15 | 2026-07-10 | 9 |
| `.claude/agents/gabriel.md` | 2026-07-04 | 2026-07-07 | 2 |
| `.claude/agents/goal-driven-grader.md` | 2026-06-12 | 2026-06-12 | 1 |
| `.claude/agents/goal-driven-l2-foreman.md` | 2026-06-12 | 2026-06-12 | 1 |
| `.claude/agents/goal-driven-l3-executor.md` | 2026-06-12 | 2026-06-12 | 1 |
| `.claude/agents/quality-auditor.md` | 2025-12-08 | 2026-07-10 | 15 |
| `.claude/agents/requirement-analyst.md` | 2025-12-08 | 2026-07-10 | 11 |
| `.claude/agents/task-decomposer.md` | 2025-12-08 | 2026-07-10 | 11 |
| `.claude/agents/tdd-developer.md` | 2025-12-08 | 2026-07-10 | 8 |
| `.claude/agents/test-runner.md` | 2026-02-15 | 2026-07-10 | 4 |

### skill (23)

| path | first_commit | last_commit | commit_count | renames |
|:---|:---|:---|---:|:---|
| `.claude/skills/adr-template/SKILL.md` | 2025-12-08 | 2026-05-28 | 5 | - |
| `.claude/skills/auditing/SKILL.md` | 2025-12-08 | 2026-05-29 | 9 | ← `.claude/commands/auditing.md` (2026-05-29) |
| `.claude/skills/autonomous/SKILL.md` | 2026-06-01 | 2026-06-21 | 3 | - |
| `.claude/skills/build-dashboard/SKILL.md` | 2026-06-21 | 2026-06-21 | 1 | - |
| `.claude/skills/building/SKILL.md` | 2025-12-08 | 2026-05-29 | 9 | ← `.claude/commands/building.md` (2026-05-29) |
| `.claude/skills/clarify/SKILL.md` | 2026-03-14 | 2026-05-28 | 2 | - |
| `.claude/skills/full-review/SKILL.md` | 2026-03-06 | 2026-06-20 | 34 | ← `.claude/commands/full-review.md` (2026-05-29) |
| `.claude/skills/goal-driven/SKILL.md` | 2026-06-12 | 2026-07-10 | 7 | - |
| `.claude/skills/init-harness/SKILL.md` | 2026-06-30 | 2026-07-10 | 3 | - |
| `.claude/skills/lam-orchestrate/SKILL.md` | 2026-02-15 | 2026-06-10 | 15 | - |
| `.claude/skills/magi/SKILL.md` | 2026-03-16 | 2026-07-05 | 4 | - |
| `.claude/skills/pattern-review/SKILL.md` | 2026-03-08 | 2026-05-29 | 5 | ← `.claude/commands/pattern-review.md` (2026-05-29) |
| `.claude/skills/planning/SKILL.md` | 2025-12-08 | 2026-05-29 | 5 | ← `.claude/commands/planning.md` (2026-05-29) |
| `.claude/skills/project-status/SKILL.md` | 2025-12-09 | 2026-05-29 | 6 | ← `.claude/commands/project-status.md` (2026-05-29) |
| `.claude/skills/quick-load/SKILL.md` | 2026-02-17 | 2026-06-30 | 7 | ← `.claude/commands/quick-load.md` (2026-05-29) |
| `.claude/skills/quick-save/SKILL.md` | 2026-02-15 | 2026-06-22 | 9 | ← `.claude/commands/quick-save.md` (2026-05-29) |
| `.claude/skills/release/SKILL.md` | 2026-05-29 | 2026-06-11 | 2 | - |
| `.claude/skills/retro/SKILL.md` | 2026-03-10 | 2026-05-29 | 6 | ← `.claude/commands/retro.md` (2026-05-29) |
| `.claude/skills/ship/SKILL.md` | 2026-03-06 | 2026-07-07 | 8 | ← `.claude/commands/ship.md` (2026-05-29) |
| `.claude/skills/skill-creator/SKILL.md` | 2026-02-20 | 2026-05-28 | 3 | - |
| `.claude/skills/spec-template/SKILL.md` | 2025-12-08 | 2026-05-28 | 4 | - |
| `.claude/skills/ui-design-guide/SKILL.md` | 2026-03-08 | 2026-05-28 | 2 | - |
| `.claude/skills/wave-plan/SKILL.md` | 2026-03-10 | 2026-05-29 | 3 | ← `.claude/commands/wave-plan.md` (2026-05-29) |

### hook (7)

| path | first_commit | last_commit | commit_count |
|:---|:---|:---|---:|
| `.claude/hooks/_hook_utils.py` | 2026-03-10 | 2026-06-11 | 15 |
| `.claude/hooks/_incident_patterns.py` | 2026-06-30 | 2026-06-30 | 1 |
| `.claude/hooks/autonomous_state.py` | 2026-05-30 | 2026-05-30 | 1 |
| `.claude/hooks/lam-stop-hook.py` | 2026-03-10 | 2026-06-13 | 22 |
| `.claude/hooks/post-tool-use.py` | 2026-03-10 | 2026-06-29 | 12 |
| `.claude/hooks/pre-compact.py` | 2026-03-10 | 2026-06-10 | 6 |
| `.claude/hooks/pre-tool-use.py` | 2026-03-10 | 2026-07-06 | 15 |

### command (0)

現存 target_path なし（`.claude/commands/*.md` は 2026-05-29 に全て `.claude/skills/*/SKILL.md`
へ改名済み、または 2026-03-13 に削除済み）。

---

## §3 削除履歴 (orphan_history / deleted_at 降順)

| path | resource_type | deleted_at | deleted_by_commit | last_content_seen |
|:---|:---|:---|:---|:---|
| `.claude/commands/adr-create.md` | command | 2026-03-13 | `e1426491d686e41ecafe7e1c28ec5239d4c43251` | 2026-03-08 |
| `.claude/commands/daily.md` | command | 2026-03-13 | `e1426491d686e41ecafe7e1c28ec5239d4c43251` | 2026-03-08 |
| `.claude/commands/focus.md` | command | 2026-03-13 | `e1426491d686e41ecafe7e1c28ec5239d4c43251` | 2026-03-08 |
| `.claude/commands/full-load.md` | command | 2026-03-13 | `e1426491d686e41ecafe7e1c28ec5239d4c43251` | 2026-03-08 |
| `.claude/commands/full-save.md` | command | 2026-03-13 | `e1426491d686e41ecafe7e1c28ec5239d4c43251` | 2026-03-08 |
| `.claude/commands/impact-analysis.md` | command | 2026-03-13 | `e1426491d686e41ecafe7e1c28ec5239d4c43251` | 2026-03-08 |
| `.claude/commands/security-review.md` | command | 2026-03-13 | `e1426491d686e41ecafe7e1c28ec5239d4c43251` | 2026-03-08 |
| `.claude/skills/ultimate-think/SKILL.md` | skill | 2026-03-13 | `e1426491d686e41ecafe7e1c28ec5239d4c43251` | 2026-03-12 |
| `.claude/skills/auditing-guardrail/SKILL.md` | skill | 2026-01-05 | `e5d4aecbc25cac4964c4367f886535524c1f4baf` | 2025-12-08 |
| `.claude/skills/building-guardrail/SKILL.md` | skill | 2026-01-05 | `e5d4aecbc25cac4964c4367f886535524c1f4baf` | 2025-12-08 |
| `.claude/skills/planning-guardrail/SKILL.md` | skill | 2026-01-05 | `e5d4aecbc25cac4964c4367f886535524c1f4baf` | 2025-12-09 |

agent / hook 種別の削除履歴は 0 件（全期間を通じて削除されたリソースなし）。

---

## §4 改名履歴 (from → to / date / commit)

全 11 件が単一コミット `8c83019481c795c0f9cec1e2972fe44d2a359fac`（2026-05-29）による
`.claude/commands/*.md` → `.claude/skills/*/SKILL.md` 一括移行。

| from | to | date | commit |
|:---|:---|:---|:---|
| `.claude/commands/auditing.md` | `.claude/skills/auditing/SKILL.md` | 2026-05-29 | `8c83019481c795c0f9cec1e2972fe44d2a359fac` |
| `.claude/commands/building.md` | `.claude/skills/building/SKILL.md` | 2026-05-29 | `8c83019481c795c0f9cec1e2972fe44d2a359fac` |
| `.claude/commands/full-review.md` | `.claude/skills/full-review/SKILL.md` | 2026-05-29 | `8c83019481c795c0f9cec1e2972fe44d2a359fac` |
| `.claude/commands/pattern-review.md` | `.claude/skills/pattern-review/SKILL.md` | 2026-05-29 | `8c83019481c795c0f9cec1e2972fe44d2a359fac` |
| `.claude/commands/planning.md` | `.claude/skills/planning/SKILL.md` | 2026-05-29 | `8c83019481c795c0f9cec1e2972fe44d2a359fac` |
| `.claude/commands/project-status.md` | `.claude/skills/project-status/SKILL.md` | 2026-05-29 | `8c83019481c795c0f9cec1e2972fe44d2a359fac` |
| `.claude/commands/quick-load.md` | `.claude/skills/quick-load/SKILL.md` | 2026-05-29 | `8c83019481c795c0f9cec1e2972fe44d2a359fac` |
| `.claude/commands/quick-save.md` | `.claude/skills/quick-save/SKILL.md` | 2026-05-29 | `8c83019481c795c0f9cec1e2972fe44d2a359fac` |
| `.claude/commands/retro.md` | `.claude/skills/retro/SKILL.md` | 2026-05-29 | `8c83019481c795c0f9cec1e2972fe44d2a359fac` |
| `.claude/commands/ship.md` | `.claude/skills/ship/SKILL.md` | 2026-05-29 | `8c83019481c795c0f9cec1e2972fe44d2a359fac` |
| `.claude/commands/wave-plan.md` | `.claude/skills/wave-plan/SKILL.md` | 2026-05-29 | `8c83019481c795c0f9cec1e2972fe44d2a359fac` |

---

## 実装メモ (unverified 扱いの排除 / grounding)

- 初回実装では `fnmatch.fnmatch()` をパス全体に対して直接使用しており、`.claude/hooks/*.py`
  パターンの `*` がディレクトリ境界 (`/`) を越えてマッチしてしまい、`.claude/hooks/analyzers/`
  等のネストしたテスト用 `.py` まで hook 数に混入する不具合（7 件の想定に対し 70 件検出）を
  実行結果 (JSON の `Counter({'hook': 70, ...})`) で確認した。
  セグメント単位マッチ (`path_matches_glob()` / 各 `/` 区切りごとに `fnmatch` を適用) に修正し、
  再実行で `hook: 7` に是正されたことをスクリプト実行結果で確認済み（推測ではなく実行結果で検証）。

---

## 変更ファイル一覧 (2 files) + 実行コマンド + 実行時刻

**変更ファイル**:
1. `.claude/scripts/r-1-git-log-usage.py` (新規)
2. `docs/artifacts/r-1-git-log-usage-2026-07-11.md` (新規・本ファイル)

**実行コマンド**:
```bash
cd D:/work7/LivingArchitectModel
python .claude/scripts/r-1-git-log-usage.py > <出力先>.json
python .claude/scripts/r-1-git-log-usage.py --markdown > <出力先>.md
```

**実行時刻 (generated_at)**: `2026-07-11T11:57:23.015701+00:00` (UTC / スクリプト実行結果の JSON フィールドより)

**boundary_deviation**: なし（白リスト内 2 ファイルのみ変更 / git 操作は `git log` read-only のみ /
依存追加なし / 依頼外ファイル作成なし）
