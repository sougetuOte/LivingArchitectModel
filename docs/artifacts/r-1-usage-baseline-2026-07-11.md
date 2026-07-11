# R-1 W-R4 S1-T4: usage-baseline 統合 (2026-07-11)

**Task**: W-R4-S1-T4（`docs/specs/large-scale-review/tasks.md` §W-R4 S1）
**目的**: S1-T2（git log 削除・改名履歴）と S1-T3（session log 30日窓 起動記録）を統合し、
`.claude/` 配下 agents / skills / hooks 各 target に verdict（delete_candidate /
keep_recent_modified / hold_low_confidence）を付与する。W-R4 S2/S3 の削除判定の直接インプット。
**権限等級**: SE（`docs/artifacts/` 配下 / 非 SSOT）

---

## §1 メタ

- **生成日時**: 2026-07-11（本 Task 実行時点 / 統合処理は手作業・スクリプトなし）
- **統合したデータソース 2 本**:
  1. `docs/artifacts/r-1-git-log-usage-2026-07-11.md`（S1-T2 成果物 / generated_at `2026-07-11T11:57:23.015701+00:00`）
  2. `docs/artifacts/r-1-session-log-usage-2026-07-11.md`（S1-T3 成果物 / generated_at `2026-07-11T10:14:27Z`）
- **window_days**: 30（S1-T3 実測に準拠 / 基準時刻 `2026-07-11T10:14:27Z` からの遡及。日付レベルの比較のため cutoff 日は `2026-06-11`）
- **sessions_scanned**: 76（S1-T3 実測値）
- **verdict 判定ロジック要約**: 下記 §2 の 3 分類を「hold_low_confidence → keep_recent_modified → delete_candidate」の優先順位（上から先勝）で判定。hit_count_30d と last_commit_date の 2 軸に加え、ヘルパーモジュール判定・ロギング経路不確実性（S1-T3 §4.2 の特記事項）を hold 側の追加条件として使用。
- **対象範囲の注記**: S1-T2 の `command` 種別（現存 target_path 0 件 / 全て改名済みまたは削除済み）は本 baseline の対象外（verdict 付与対象は「現存する」agent / skill / hook のみ）。

---

## §2 verdict 判定ロジック

各 target に対し、以下の順で判定する（上から先勝）。

1. **hold_low_confidence**（削除保留 / 偽陰性リスク大）:
   - condition: 「30 日窓 hit_count == 0」かつ「以下いずれかに該当」
     - (a) S1-T3 で detection_paths が特定できなかった（pre-compact.py 型 / logging coverage gap 疑い）
     - (b) hook で `attachment.hook_success` にも Stop-hook shape にも現れない（event shape 未確認）
     - (c) helper module 相当（`.claude/hooks/` 直下 .py だが entrypoint ではない可能性）
     - (d) 最終コミット（last_commit_date）が 30 日以内（cutoff `2026-06-11` 以降。同日は window 境界として「以内」扱い）
2. **keep_recent_modified**（削除不可 / 現役）:
   - condition: 「30 日窓 hit_count > 0」または「最終コミットが 30 日以内」
3. **delete_candidate**（削除候補 / S2/S3 で承認取得対象）:
   - condition: 「30 日窓 hit_count == 0」かつ「最終コミットが 30 日超前」かつ hold_low_confidence の (a)-(c) に該当しない

**注記**: 「30 日」は S1-T3 の window_days=30 実測に準拠。上記ロジックは design.md §7 の 3 条件 AND を verdict 3 分類に翻訳したもの（deferred fallback は S1-T5 判定失敗時に発火する別レイヤなので本 Task では扱わない）。

---

## §3 verdict 別集計

| verdict | agent | skill | hook | 合計 |
|:---|---:|---:|---:|---:|
| delete_candidate | 0 | 9 | 0 | **9** |
| keep_recent_modified | 12 | 14 | 3 | **29** |
| hold_low_confidence | 0 | 0 | 4 | **4** |
| **合計** | **12** | **23** | **7** | **42** |

---

## §4 全 target 一覧

### §4.1 agent (12) — 全件 keep_recent_modified（30 日窓 hit>0）

| path | resource_type | slug | exists_now | first_commit_date | last_commit_date | commit_count | rename_history | hit_count_30d | last_hit_timestamp | detection_paths | verdict | verdict_reason |
|:---|:---|:---|:---:|:---|:---|---:|:---:|---:|:---|:---|:---|:---|
| `.claude/agents/tdd-developer.md` | agent | tdd-developer | true | 2025-12-08 | 2026-07-10 | 8 | - | 56 | 2026-07-06T22:47:55.586Z | tool_use.name==Agent + input.subagent_type | keep_recent_modified | 56 hits/30d (active) |
| `.claude/agents/doc-writer.md` | agent | doc-writer | true | 2026-02-15 | 2026-07-10 | 9 | - | 32 | 2026-07-02T08:42:40.047Z | tool_use.name==Agent + input.subagent_type | keep_recent_modified | 32 hits/30d (active) |
| `.claude/agents/goal-driven-grader.md` | agent | goal-driven-grader | true | 2026-06-12 | 2026-06-12 | 1 | - | 29 | 2026-06-27T23:15:52.456Z | tool_use.name==Agent + input.subagent_type | keep_recent_modified | 29 hits/30d (active) |
| `.claude/agents/design-architect.md` | agent | design-architect | true | 2025-12-08 | 2026-07-10 | 10 | - | 22 | 2026-06-29T11:53:20.804Z | tool_use.name==Agent + input.subagent_type | keep_recent_modified | 22 hits/30d (active) |
| `.claude/agents/task-decomposer.md` | agent | task-decomposer | true | 2025-12-08 | 2026-07-10 | 11 | - | 19 | 2026-06-29T13:26:59.373Z | tool_use.name==Agent + input.subagent_type | keep_recent_modified | 19 hits/30d (active) |
| `.claude/agents/code-reviewer.md` | agent | code-reviewer | true | 2026-02-15 | 2026-07-10 | 8 | - | 13 | 2026-07-06T07:07:57.989Z | tool_use.name==Agent + input.subagent_type | keep_recent_modified | 13 hits/30d (active) |
| `.claude/agents/requirement-analyst.md` | agent | requirement-analyst | true | 2025-12-08 | 2026-07-10 | 11 | - | 7 | 2026-06-24T01:00:02.540Z | tool_use.name==Agent + input.subagent_type | keep_recent_modified | 7 hits/30d (active) |
| `.claude/agents/test-runner.md` | agent | test-runner | true | 2026-02-15 | 2026-07-10 | 4 | - | 7 | 2026-06-23T23:33:59.518Z | tool_use.name==Agent + input.subagent_type | keep_recent_modified | 7 hits/30d (active) |
| `.claude/agents/quality-auditor.md` | agent | quality-auditor | true | 2025-12-08 | 2026-07-10 | 15 | - | 6 | 2026-06-18T22:07:04.535Z | tool_use.name==Agent + input.subagent_type | keep_recent_modified | 6 hits/30d (active) |
| `.claude/agents/gabriel.md` | agent | gabriel | true | 2026-07-04 | 2026-07-07 | 2 | - | 2 | 2026-07-05T09:23:50.958Z | tool_use.name==Agent + input.subagent_type | keep_recent_modified | 2 hits/30d (active) |
| `.claude/agents/goal-driven-l3-executor.md` | agent | goal-driven-l3-executor | true | 2026-06-12 | 2026-06-12 | 1 | - | 2 | 2026-06-17T01:25:30.217Z | tool_use.name==Agent + input.subagent_type | keep_recent_modified | 2 hits/30d (active) |
| `.claude/agents/goal-driven-l2-foreman.md` | agent | goal-driven-l2-foreman | true | 2026-06-12 | 2026-06-12 | 1 | - | 1 | 2026-06-18T09:06:16.148Z | tool_use.name==Agent + input.subagent_type | keep_recent_modified | 1 hit/30d (active) |

### §4.2 skill (23)

| path | resource_type | slug | exists_now | first_commit_date | last_commit_date | commit_count | rename_history | hit_count_30d | last_hit_timestamp | detection_paths | verdict | verdict_reason |
|:---|:---|:---|:---:|:---|:---|---:|:---:|---:|:---|:---|:---|:---|
| `.claude/skills/quick-load/SKILL.md` | skill | quick-load | true | 2026-02-17 | 2026-06-30 | 7 | ← commands/quick-load.md (2026-05-29) | 69 | 2026-07-11T07:47:11.825Z | Skill.input.skill, user_text.command-name | keep_recent_modified | 69 hits/30d (active) |
| `.claude/skills/ship/SKILL.md` | skill | ship | true | 2026-03-06 | 2026-07-07 | 8 | ← commands/ship.md (2026-05-29) | 40 | 2026-07-05T11:47:23.643Z | Skill.input.skill, user_text.command-name | keep_recent_modified | 40 hits/30d (active) |
| `.claude/skills/quick-save/SKILL.md` | skill | quick-save | true | 2026-02-15 | 2026-06-22 | 9 | ← commands/quick-save.md (2026-05-29) | 34 | 2026-07-09T21:50:52.259Z | Skill.input.skill, user_text.command-name | keep_recent_modified | 34 hits/30d (active) |
| `.claude/skills/goal-driven/SKILL.md` | skill | goal-driven | true | 2026-06-12 | 2026-07-10 | 7 | - | 6 | 2026-06-18T09:01:13.186Z | Skill.input.skill, user_text.command-name | keep_recent_modified | 6 hits/30d (active) |
| `.claude/skills/magi/SKILL.md` | skill | magi | true | 2026-03-16 | 2026-07-05 | 4 | - | 6 | 2026-07-05T09:15:59.479Z | Skill.input.skill, user_text.command-name | keep_recent_modified | 6 hits/30d (active) |
| `.claude/skills/retro/SKILL.md` | skill | retro | true | 2026-03-10 | 2026-05-29 | 6 | ← commands/retro.md (2026-05-29) | 6 | 2026-07-06T01:05:23.333Z | Skill.input.skill, user_text.command-name | keep_recent_modified | 6 hits/30d (active) |
| `.claude/skills/adr-template/SKILL.md` | skill | adr-template | true | 2025-12-08 | 2026-05-28 | 5 | - | 1 | 2026-07-03T21:09:03.120Z | Skill.input.skill, user_text.command-name | keep_recent_modified | 1 hit/30d (active) |
| `.claude/skills/building/SKILL.md` | skill | building | true | 2025-12-08 | 2026-05-29 | 9 | ← commands/building.md (2026-05-29) | 1 | 2026-06-12T11:34:37.377Z | Skill.input.skill, user_text.command-name | keep_recent_modified | 1 hit/30d (active) |
| `.claude/skills/spec-template/SKILL.md` | skill | spec-template | true | 2025-12-08 | 2026-05-28 | 4 | - | 1 | 2026-07-05T10:26:46.676Z | Skill.input.skill, user_text.command-name | keep_recent_modified | 1 hit/30d (active) |
| `.claude/skills/autonomous/SKILL.md` | skill | autonomous | true | 2026-06-01 | 2026-06-21 | 3 | - | 0 | - | (0 hit / 両経路スキャン済) | keep_recent_modified | 0 hits/30d but last commit 2026-06-21 (<30d, WIP suspected) |
| `.claude/skills/build-dashboard/SKILL.md` | skill | build-dashboard | true | 2026-06-21 | 2026-06-21 | 1 | - | 0 | - | (0 hit / 両経路スキャン済) | keep_recent_modified | 0 hits/30d but last commit 2026-06-21 (<30d, WIP suspected) |
| `.claude/skills/full-review/SKILL.md` | skill | full-review | true | 2026-03-06 | 2026-06-20 | 34 | ← commands/full-review.md (2026-05-29) | 0 | - | (0 hit / 両経路スキャン済) | keep_recent_modified | 0 hits/30d but last commit 2026-06-20 (<30d, WIP suspected) |
| `.claude/skills/init-harness/SKILL.md` | skill | init-harness | true | 2026-06-30 | 2026-07-10 | 3 | - | 0 | - | (0 hit / 両経路スキャン済) | keep_recent_modified | 0 hits/30d but last commit 2026-07-10 (<30d, WIP suspected) |
| `.claude/skills/release/SKILL.md` | skill | release | true | 2026-05-29 | 2026-06-11 | 2 | - | 0 | - | (0 hit / 両経路スキャン済) | keep_recent_modified | 0 hits/30d but last commit 2026-06-11 (window boundary, treated as recent) |
| `.claude/skills/auditing/SKILL.md` | skill | auditing | true | 2025-12-08 | 2026-05-29 | 9 | ← commands/auditing.md (2026-05-29) | 0 | - | (0 hit / 両経路スキャン済) | delete_candidate | 0 hits/30d + last commit 2026-05-29 (>40d ago) |
| `.claude/skills/clarify/SKILL.md` | skill | clarify | true | 2026-03-14 | 2026-05-28 | 2 | - | 0 | - | (0 hit / 両経路スキャン済) | delete_candidate | 0 hits/30d + last commit 2026-05-28 (>40d ago) |
| `.claude/skills/lam-orchestrate/SKILL.md` | skill | lam-orchestrate | true | 2026-02-15 | 2026-06-10 | 15 | - | 0 | - | (0 hit / 両経路スキャン済) | delete_candidate | 0 hits/30d + last commit 2026-06-10 (31d ago, just outside window) |
| `.claude/skills/pattern-review/SKILL.md` | skill | pattern-review | true | 2026-03-08 | 2026-05-29 | 5 | ← commands/pattern-review.md (2026-05-29) | 0 | - | (0 hit / 両経路スキャン済) | delete_candidate | 0 hits/30d + last commit 2026-05-29 (>40d ago) |
| `.claude/skills/planning/SKILL.md` | skill | planning | true | 2025-12-08 | 2026-05-29 | 5 | ← commands/planning.md (2026-05-29) | 0 | - | (0 hit / 両経路スキャン済) | delete_candidate | 0 hits/30d + last commit 2026-05-29 (>40d ago) |
| `.claude/skills/project-status/SKILL.md` | skill | project-status | true | 2025-12-09 | 2026-05-29 | 6 | ← commands/project-status.md (2026-05-29) | 0 | - | (0 hit / 両経路スキャン済) | delete_candidate | 0 hits/30d + last commit 2026-05-29 (>40d ago) |
| `.claude/skills/skill-creator/SKILL.md` | skill | skill-creator | true | 2026-02-20 | 2026-05-28 | 3 | - | 0 | - | (0 hit / 両経路スキャン済) | delete_candidate | 0 hits/30d + last commit 2026-05-28 (>40d ago) |
| `.claude/skills/ui-design-guide/SKILL.md` | skill | ui-design-guide | true | 2026-03-08 | 2026-05-28 | 2 | - | 0 | - | (0 hit / 両経路スキャン済) | delete_candidate | 0 hits/30d + last commit 2026-05-28 (>40d ago) |
| `.claude/skills/wave-plan/SKILL.md` | skill | wave-plan | true | 2026-03-10 | 2026-05-29 | 3 | ← commands/wave-plan.md (2026-05-29) | 0 | - | (0 hit / 両経路スキャン済) | delete_candidate | 0 hits/30d + last commit 2026-05-29 (>40d ago) |

### §4.3 hook (7)

| path | resource_type | slug | exists_now | first_commit_date | last_commit_date | commit_count | rename_history | hit_count_30d | last_hit_timestamp | detection_paths | verdict | verdict_reason |
|:---|:---|:---|:---:|:---|:---|---:|:---:|---:|:---|:---|:---|:---|
| `.claude/hooks/lam-stop-hook.py` | hook | lam-stop-hook | true | 2026-03-10 | 2026-06-13 | 22 | - | 739 | 2026-07-11T08:16:29.628Z | attachment (Stop hook summary) | keep_recent_modified | 739 hits/30d (active) |
| `.claude/hooks/pre-tool-use.py` | hook | pre-tool-use | true | 2026-03-10 | 2026-07-06 | 15 | - | 370 | 2026-07-11T08:09:12.917Z | attachment.command (PreToolUse) | keep_recent_modified | 370 hits/30d (active) |
| `.claude/hooks/post-tool-use.py` | hook | post-tool-use | true | 2026-03-10 | 2026-06-29 | 12 | - | 14 | 2026-07-09T20:46:04.078Z | attachment.command (PostToolUse:Bash) | keep_recent_modified | 14 hits/30d (active) |
| `.claude/hooks/pre-compact.py` | hook | pre-compact | true | 2026-03-10 | 2026-06-10 | 6 | - | 0 | - | 検出手段なし（PreCompact 専用 attachment/subtype 未確認） | hold_low_confidence | 0 hits/30d + logging shape uncertain / PreCompact event detection unconfirmed (S1-T3 §4.2) |
| `.claude/hooks/_hook_utils.py` | hook | _hook_utils | true | 2026-03-10 | 2026-06-11 | 15 | - | 0 | - | ヘルパーモジュール（非エントリポイント） | hold_low_confidence | 0 hits/30d + helper module (non-entrypoint, import analysis needed) |
| `.claude/hooks/_incident_patterns.py` | hook | _incident_patterns | true | 2026-06-30 | 2026-06-30 | 1 | - | 0 | - | ヘルパーモジュール（非エントリポイント） | hold_low_confidence | 0 hits/30d + helper module + last commit 2026-06-30 (<30d, non-entrypoint) |
| `.claude/hooks/autonomous_state.py` | hook | autonomous_state | true | 2026-05-30 | 2026-05-30 | 1 | - | 0 | - | ヘルパーモジュール（非エントリポイント） | hold_low_confidence | 0 hits/30d + helper module (non-entrypoint, import analysis needed) |

---

## §5 delete_candidate 詳細（S2/S3 の削除承認取得用リスト）

9 件全て skill 種別。agent / hook に delete_candidate なし。

| # | path | last_commit_date | commit_count | rename_history | verdict_reason |
|---:|:---|:---|---:|:---|:---|
| 1 | `.claude/skills/auditing/SKILL.md` | 2026-05-29 | 9 | ← commands/auditing.md | 0 hits/30d + last commit 2026-05-29 (>40d ago) |
| 2 | `.claude/skills/clarify/SKILL.md` | 2026-05-28 | 2 | - | 0 hits/30d + last commit 2026-05-28 (>40d ago) |
| 3 | `.claude/skills/lam-orchestrate/SKILL.md` | 2026-06-10 | 15 | - | 0 hits/30d + last commit 2026-06-10 (31d ago, just outside window) |
| 4 | `.claude/skills/pattern-review/SKILL.md` | 2026-05-29 | 5 | ← commands/pattern-review.md | 0 hits/30d + last commit 2026-05-29 (>40d ago) |
| 5 | `.claude/skills/planning/SKILL.md` | 2026-05-29 | 5 | ← commands/planning.md | 0 hits/30d + last commit 2026-05-29 (>40d ago) |
| 6 | `.claude/skills/project-status/SKILL.md` | 2026-05-29 | 6 | ← commands/project-status.md | 0 hits/30d + last commit 2026-05-29 (>40d ago) |
| 7 | `.claude/skills/skill-creator/SKILL.md` | 2026-05-28 | 3 | - | 0 hits/30d + last commit 2026-05-28 (>40d ago) |
| 8 | `.claude/skills/ui-design-guide/SKILL.md` | 2026-05-28 | 2 | - | 0 hits/30d + last commit 2026-05-28 (>40d ago) |
| 9 | `.claude/skills/wave-plan/SKILL.md` | 2026-05-29 | 3 | ← commands/wave-plan.md | 0 hits/30d + last commit 2026-05-29 (>40d ago) |

**注意（W-R4-S2-T2 / W-R4-S3-T2 の Stage 冒頭一括宣言用）**:
- `lam-orchestrate` は window 境界に近い（cutoff 2026-06-11 に対し last_commit 2026-06-10、1 日差）。他の 8 件（>40 日前）より確信度が相対的に低いことを承認提示時に明記すること。
- `auditing` / `pattern-review` / `planning` / `project-status` / `wave-plan` の 5 件は 2026-05-29 の一括 commands→skills 改名対象でもある（S1-T2 §4 参照）。改名直後から一貫して 30 日窓 hit=0 のため、改名後未使用と判断できる。

---

## §6 hold_low_confidence 詳細（削除保留の根拠明示）

4 件全て hook 種別。agent / skill に hold_low_confidence なし。

| # | path | 保留条件 | 根拠 |
|---:|:---|:---|:---|
| 1 | `.claude/hooks/pre-compact.py` | (a) 検出経路不確実 | S1-T3 §4.2: `settings.json` に `PreCompact` イベント登録は実在確認済みだが、76 セッション全量走査でも `PreCompact` に対応する attachment / summary event が 1 件も観測されず、ロギング経路自体の欠落が疑われる。0 hit は「未使用」ではなく「観測不能」の可能性が高い |
| 2 | `.claude/hooks/_hook_utils.py` | (c) ヘルパーモジュール | `.claude/hooks/` 直下の `_` プレフィックス付きファイルは登録済み hook エントリポイントではなく、他 hook から import される共通ユーティリティと推定される（S1-T3 §4 表の判定列）。3 分岐 grep のスコープでは import 参照を追跡できないため、実使用有無は本 baseline では判定不能 |
| 3 | `.claude/hooks/_incident_patterns.py` | (c) ヘルパーモジュール + (d) 最終コミット 30 日以内 | 上記 (c) に加え、last_commit_date が 2026-06-30（cutoff 2026-06-11 以降）で二重に保留条件を満たす。直近改修されたヘルパーの可能性が高い |
| 4 | `.claude/hooks/autonomous_state.py` | (c) ヘルパーモジュール | `_hook_utils.py` と同様、非エントリポイントのため import 参照解析が別途必要 |

**共通の申し送り**: 上記 4 件は W-R4-S2/S3 の grep ベース削除フローでは判定材料が不足している。削除判定を進める場合は、対象 hook を import している箇所（`grep -r "import _hook_utils\|import _incident_patterns\|import autonomous_state"` 等）を別途走査してから個別判断すること（本 Task のスコープ外）。

---

## §7 S1-T5 データソース確定判定へのインプット

**推奨 verdict**: **success**

**理由**:
- git log（S1-T2）と session log（S1-T3）は独立した 2 系統のデータソースとして正常に走査を完了し、path をキーに矛盾なく統合できた（42 件全 target で join 成功、欠損なし）。
- agent 種別は検出パターンが単一かつ全 12 件が hit>0 で判定に迷いがなく、データソースとしての信頼性が高い。
- skill 種別は 2 経路 OR 検出（S1-T3 §5 末尾の `quick-save` 実測検証）により取りこぼしが実測で否定されており、hit==0 の 14 件は「検出漏れ」ではなく「実際に未使用」である確信度が高い。
- hook 種別のみ、pre-compact.py（ロギング経路不確実）とヘルパーモジュール 3 件（非エントリポイント）で判定材料不足が確認された。これは **データソース自体の欠陥ではなく、hook という resource_type 固有の構造的制約**（グレップベース走査では import 参照や `PreCompact` 専用 event shape を拾えない）であり、S1-T5 のデータソース確定判定（agent/skill/hook 3 分岐全体の合否）を failure とするほどの欠陥ではない。該当 4 件は本 baseline で hold_low_confidence として明示的に隔離済み（§6）であり、削除フローには進めない設計になっている。

---

## 変更ファイル一覧・実行証跡（自己申告 / Fable-Alembic L3 §5.4 ガード4）

**詰まり仮説**: 「S2/S3 で削除承認を求める読み手が、9 件の delete_candidate の中で確信度に差があることに気づかず一括承認してしまうのでは」という仮説を立てた。

**実況第1文**: 承認判断をする読み手は、まず §3 の集計表で件数を掴んだ後、§5 に飛んで「9 件全部が同じ確信度か」を確認しようとする——ここで `lam-orchestrate` だけ last_commit が cutoff の 1 日差という点に気づかず読み飛ばす可能性があったため、§5 の「注意」ブロックに明記して対処した。

**入力ファイル 2 本**:
1. `docs/artifacts/r-1-git-log-usage-2026-07-11.md`（S1-T2 成果物）
2. `docs/artifacts/r-1-session-log-usage-2026-07-11.md`（S1-T3 成果物）

**生成日時**: 2026-07-11（本 Task 実行時点）

**変更ファイル（1 件のみ・白リスト内）**:
1. `docs/artifacts/r-1-usage-baseline-2026-07-11.md`（新規・本ファイル）

**boundary_deviation**: なし（白リスト内 1 ファイルのみ変更 / S1-T2・S1-T3 成果物・S1-T1 メモ・スクリプトへの変更なし / 削除は実行していない / 依頼外 helper・スクリプト作成なし）

## 権限等級

本アーティファクト: SE（`docs/artifacts/` 配下 / 非 SSOT）

## 参照

- `docs/artifacts/r-1-git-log-usage-2026-07-11.md`（S1-T2 成果物）
- `docs/artifacts/r-1-session-log-usage-2026-07-11.md`（S1-T3 成果物）
- `docs/artifacts/r-1-jsonl-fields-2026-07-11.md`（S1-T1 フィールド名確定）
- `docs/specs/large-scale-review/design.md` §3.4（usage-baseline スキーマ）/ §7（FR-F4）/ §7.5（確定失敗の分岐条件）
- `docs/specs/large-scale-review/requirements.md` FR-F4
- `docs/specs/large-scale-review/tasks.md`（S1-T4/T5 の完了条件）
