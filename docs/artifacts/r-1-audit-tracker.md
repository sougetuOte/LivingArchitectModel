# R-1 Audit Tracker

**単一 SSOT**: 本ファイル (`docs/artifacts/r-1-audit-tracker.md`)
**生成日**: 2026-07-06 (W-R1 S2 T1 / 骨組作成)
**Milestone**: R-1 (大規模レビュー & リファクタリング)
**Wave 数**: 5 固定 (FR-8)
**ライフサイクル**:
- W-R1: 全 issue 起票 (status = `open`)
- W-R2/R3/R4: 消化 (status = `wip` → `closed` / commit message に `closed issue IDs` 列挙)
- W-R5 S1: 全閉塞確認 (R-G6 / `wip` 残存 = Green State 不成立)

**破損時復旧**: requirements.md §4.1 手順で git log から復元 (rule-001 R-1 期チェックリスト対象)

---

## 1. NFR-3 Critical 件数閾値

| 項目 | 値 | 出典 |
|:----|:---|:-----|
| 初期閾値 (暫定) | 10 件 | requirements.md NFR-3 |
| 確定閾値 | **W-R1 S5-T4 で実測に基づき確定** | tasks.md W-R1 S5 T4 |
| 超過時アクション | 優先順位付けサブタスクを tracker に起票 | spec-critic Warning W5 |

---

## 2. モジュール別問題数ヒートマップ (11 × 3)

**実測値埋め予定**: W-R1 S4 T4 (11 モジュール監査完了後)

| モジュール | Critical | Warning | Info |
|:----------|:--------:|:-------:|:----:|
| 1. `.claude/scripts/dashboard/` | - | - | - |
| 2. `.claude/scripts/` (外) | - | - | - |
| 3. `.claude/skills/` (23 SKILL.md) | - | - | - |
| 4. `.claude/tests/` | - | - | - |
| 5. `.claude/hooks/` + `settings*.json` | - | - | - |
| 6. `.claude/agents/` (12 件) | - | - | - |
| 7. `.claude/rules/` (11 files + auto-generated/) | - | - | - |
| 8. `docs/internal/` (00-07) | - | - | - |
| 9. `docs/specs/` | - | - | - |
| 10. `docs/adr/` | - | - | - |
| 11. `CLAUDE.md` + `CHEATSHEET.md` | - | - | - |
| **合計** | **-** | **-** | **-** |

**W-R1 S2 進行中** (module 1-4 埋め / T2-T5 完了ごとに更新):

| モジュール | Critical | Warning | Info |
|:----------|:--------:|:-------:|:----:|
| 1. `.claude/scripts/dashboard/` | **1** | **2** | **5** |
| 2. `.claude/scripts/` (外) | **0** | **3** | **5** |
| 3. `.claude/skills/` | **0** | **3** | **2** |
| 4. `.claude/tests/` | **0** | **2** | **3** |

---

## 3. issue スキーマ

各 issue は以下 11 属性を持つ:

| 属性 | 意味 | 必須 |
|:----|:-----|:----:|
| `issue_id` | R1-NNN 形式 (通し番号) | ✅ |
| `module` | 1-11 (§2 モジュール ID) | ✅ |
| `severity` | Critical / Warning / Info | ✅ |
| `responsibility_tag` | 責務タグ (例: `parser`, `dashboard-ui`, `hook`, `spec-drift` 等) | ✅ |
| `attribution` | 帰責先 (`upstream` / `downstream` / `spec_ambiguity` / `unknown` / **単一モジュール完結時は `self`**) | ✅ |
| `status` | `open` / `wip` / `closed` / `deferred` | ✅ |
| `opened_at` | 起票日 (ISO 8601) | ✅ |
| `closed_at` | 消化日 (ISO 8601) | closed/deferred 時 |
| `closed_by_commit` | 消化コミット SHA (短縮 7 桁) | closed 時 |
| `evidence_file` | 該当ファイル (repo-relative) | Critical/Warning 必須 / Info 任意 |
| `evidence_line` | 該当行番号 | Critical/Warning 必須 (可能な場合) / Info 任意 |
| `evidence_summary` | 根拠 1 文 (L2 が再調査不要となる程度) | Critical/Warning 必須 / Info 任意 |

**deferred 時の追加要件**:
- `deferred_reason`: 保留理由 (例: `FR-F4 data source undetermined`)
- `deferred_from` → `open` 昇格条件: 「in-scope モジュールの Green State 条件 (Critical / Warning) を block する場合」のみ (FR-2 二値判定 / 昇格判定に MAGI を呼ばない)

**責務タグの用途** (FR-5): モジュール横断で「同種の責務が複数モジュールに散らばっているか」を W-R5 retro で集計する材料。

---

## 4. issue 一覧

### module 1: `.claude/scripts/dashboard/`

**監査完了**: 2026-07-06 (W-R1 S2 T2 / code-reviewer subagent + L1 監督)
**集計**: Critical 1 / Warning 2 / Info 5

#### R1-001: `_resolve_task_status` の部分文字列マッチで Task ID の接頭辞衝突
- **severity**: **Critical**
- **responsibility_tag**: `dashboard-ui`
- **attribution**: `self`
- **status**: `open`
- **opened_at**: 2026-07-06
- **evidence_file**: `.claude/scripts/dashboard/builder.py`
- **evidence_line**: 703-711
- **evidence_summary**: `if task_id in line:` は素の部分文字列マッチ。`task_id="W1-B5-T1"` は `line="- W1-B5-T10: ..."` に一致するため、T1/T10, T2/T20 等の接頭辞衝突で誤ステータス伝播。既存テストは接頭辞衝突をカバーせず。design.md §5 「完全一致前提」との黙示的仕様不一致。
- **推奨修正方針**: Red で W1-B5-T10 のみ完了・W1-B5-T1 未完了の合成 fixture で接頭辞衝突テストを追加。Green で `re.search(re.escape(task_id) + r"(?:[:\s]|$)", line)` 相当のトークン境界チェックに置換 (task ID 直後がコロン/空白/行末なら一致 / 数字が続くなら不一致)。

#### R1-002: `_render_v2_milestones` が html.escape() を漏らしている (同ファイル内一貫性欠落)
- **severity**: Warning
- **responsibility_tag**: `dashboard-ui`
- **attribution**: `self`
- **status**: `open`
- **opened_at**: 2026-07-06
- **evidence_file**: `.claude/scripts/dashboard/builder.py`
- **evidence_line**: 596-599
- **evidence_summary**: 同ファイル内の他 render メソッド (v3_milestone_section L658 / v4_tasks L748-750 / filter_controls L829 / nav L888 / parser_errors L913) は全て `html.escape()` 適用済だが v2_milestones のみが `ms.name` / `current_phase` / `ms.status` を素通し。現状は Milestone 名の入力元が正規表現由来のため実害小だが、将来入力元が拡張された場合の XSS 窓。一貫性欠落は意図的除外ではなく単純漏れと判断。
- **推奨修正方針**: Red で Milestone 名に `<script>` 等を含む合成テストケースを追加し escape 出力を assert。Green で該当 3 箇所に `html.escape()` を適用。

#### R1-003: `DashboardBuilder` の God Class 傾向 (921 行 / 15 メソッド)
- **severity**: Warning
- **responsibility_tag**: `dashboard-ui`
- **attribution**: `self`
- **status**: `open`
- **opened_at**: 2026-07-06
- **evidence_file**: `.claude/scripts/dashboard/builder.py`
- **evidence_line**: 39-922 (クラス全体)
- **evidence_summary**: DashboardBuilder が CSS 生成 + JS 生成 + V1-V4 の 4 ビュー + nav + filter + status badge + parser-errors を単一クラスに集約。個々のメソッドは責務明確で読みやすいが、Wave 毎の追加で肥大化 (コメント Wave 1-8 変遷履歴が示唆)。SRP 逸脱として Warning。**subagent 判断: 即時 Refactor は Zero-Regression Policy 上リスク大 → 次期 Wave (W-R2 S1) で `_render_style` / `_render_script` を独立モジュール切出しが第一歩**。
- **推奨修正方針**: W-R2 S1 で対応。まず CSS/JS 静的合成部分 (計 422 行) を独立モジュール化。ビュー分割は Wave をまたぐ課題として retro 議題化。

#### R1-I01: BaseParser の broad catch は契約通り (Error Swallowing ではない)
- **severity**: Info
- **evidence_summary**: `tasks.py` L96/L125 / `session_state.py` L115 の `except Exception as e:  # noqa: BLE001` は BaseParser 契約 (例外を外に伝播させず ok=False 返却 / base.py L24, L34-35) に忠実。Critical 対象外の記録。

#### R1-I02: `git_history.py` の subprocess 実行はセキュリティ Green
- **severity**: Info
- **evidence_summary**: `subprocess.run(["git", "log", ...], shell=True 不使用)` を確認。引数リスト形式でコマンドインジェクションリスクなし (G5 Green 材料)。

#### R1-I03: builder.py `_render_style` / `_render_script` は行数超過だがロジック複雑度低 (Warning 対象外)
- **severity**: Info
- **evidence_summary**: L63-322 (261 行) と L324-483 (161 行) は静的 CSS/JS 文字列合成。行数のみ Warning 起票せず (code-quality-guideline アンチパターン「読みやすさを犠牲にした行数削減」回避)。

#### R1-I04: `.claude/tests/dashboard/` の debug スクリプト残置 (module 4 で拾う予定)
- **severity**: Info
- **evidence_file**: `.claude/tests/dashboard/debug_regex.py`, `debug_regex2.py`, `debug_regex3.py`, `verify_git_history.py`, `_check_tasks.py`
- **evidence_summary**: 一時調査用スクリプトが常駐 (pytest 収集対象外の命名)。module 1 スコープ外だが module 4 (tests/) 監査 (S2-T5) で dead code 候補として拾う。

#### R1-I05: `CurrentPhaseParser` の `_VALID_PHASES` に "UNKNOWN" が含まれない (命名と実体の乖離 / 実害なし)
- **severity**: Info (旧 subagent 判断 Warning → L1 監督で降格 / docstring 明示済 / 保守困難ではない)
- **evidence_file**: `.claude/scripts/dashboard/parsers/current_phase.py`
- **evidence_line**: 20, 54-55
- **evidence_summary**: `_VALID_PHASES = ("PLANNING", "BUILDING", "AUDITING", "AUTONOMOUS")` に "UNKNOWN" は含まれないが、fallback 時 phase="UNKNOWN" を返す (L55)。docstring L31 で明示のため実害なし。次回 Refactor 時に `_PHASE_PATTERN_CANDIDATES` 等への改名検討推奨。

### module 2: `.claude/scripts/` (外)

**監査完了**: 2026-07-06 (W-R1 S2 T3 / code-reviewer subagent + L1 監督)
**集計**: Critical 0 / Warning 3 / Info 4
**特記**: 3 件全てが **本監査シリーズで作成した self コード** の Warning (Fable→Opus gap 事例 #2 = Opus 自身の T1/T4 実装漏れを subagent が発見)

#### R1-006: `verify_reference_resolution.py` の rules パス正規表現が大文字始まりファイル名を検出漏れ (自己コード)
- **severity**: **Warning**
- **responsibility_tag**: `audit-script`
- **attribution**: `self`
- **status**: `open`
- **opened_at**: 2026-07-06
- **evidence_file**: `.claude/scripts/verify_reference_resolution.py`
- **evidence_line**: 37-39
- **evidence_summary**: `_W_R3_PAT_RULES_PATH = re.compile(r"\.claude/rules/(?:auto-generated/)?([a-z0-9-]+\.md)")` は文字クラスが `[a-z0-9-]+` のみ。**実測**: rule-001.md L76 が `.claude/rules/auto-generated/README.md` を参照しているが正規表現 unmatched (`re.search()` returns None)。false negative = 実 drift があっても drift=0 と誤報告する監査ツール自体の信頼性欠陥。
- **推奨修正方針**: 正規表現を `[A-Za-z0-9_-]+` に拡張。Red で `test_w_r3_pat_rules_path_matches_uppercase_filename` を追加 (README.md 等の入力で match)。既存 test_reference_resolution.py (`.claude/tests/rules/`) に追加。**Fable→Opus gap 恒久対策 memo §事例 #2** として記録推奨。

#### R1-007: `distill_lessons.py` の `is_small_task` パラメータが未使用のままシグネチャに残存 (dead code)
- **severity**: Warning
- **responsibility_tag**: `cli-entrypoint`
- **attribution**: `self`
- **status**: `open`
- **opened_at**: 2026-07-06
- **evidence_file**: `.claude/scripts/distill_lessons.py`
- **evidence_line**: 279, 293 (docstring), 395 (caller)
- **evidence_summary**: `distill()` は `is_small_task: bool = False` を受け取り docstring で「小タスクルート (grader ログのみ / design §9.1)」を説明するが、関数本体 (274-309 行) 内で **一度も参照されない**。`grep -c "is_small_task"` の結果は 3 のみ (シグネチャ + docstring + caller)。設計意図が実装未反映か既に別ロジックで代替されて docs 未追随のいずれか。
- **推奨修正方針**: (a) 小タスクルート特有分岐 (previous_feedback 生成省略 / L1 検収 skip 等) を実装 or (b) 不要なら docstring とパラメータ削除。Red で `is_small_task=True/False` の出力差異 assert テスト追加 (現状 Red)。

#### R1-008: `r1_inventory.py` の module 2 glob が gitignore 済みファイルを inventory に混入 (自己コード)
- **severity**: Warning
- **responsibility_tag**: `audit-script`
- **attribution**: `self`
- **status**: `open`
- **opened_at**: 2026-07-06
- **evidence_file**: `.claude/scripts/r1_inventory.py`
- **evidence_line**: 27 (`2: ".claude/scripts/*.py"`), 46-55 (`_glob_module`)
- **evidence_summary**: `glob.glob()` は `.gitignore` を関知しない。`git check-ignore` 実測で `.claude/scripts/scan_nfr_refs.py` / `scan_nfr_refs2.py` は gitignore 対象と確認済だが、inventory JSON の module 2 に混入 (実測 14 files ≠ tracked 12 files)。後続の R-G8 / 監査集計が gitignore 済 ad-hoc スクリプトを「本番コード」誤認するリスク。
- **推奨修正方針**: `_glob_module` に `git ls-files` ベースの filter 追加 or `.gitignore` パターン照合。Red で gitignore 済ダミーファイル配置 → inventory 出力に含まれないこと assert。**W-R2 S2 で対応推奨** (inventory 再生成が R-G8 baseline の前提)。

#### R1-I06: `gd_state.py` (727 行 / 最大) は SRP 維持 / 分割不要 (Warning 対象外)
- **severity**: Info
- **evidence_summary**: 21 個の独立小関数 (各 10-40 行 / 単一責務: read/write, bound チェック, status 更新, コスト集計等) に整理済。God Module 兆候なし (複数責務癒着・巨大関数なし)。個別関数はいずれも Cognitive Complexity 15 以下と推定。code-quality-guideline アンチパターン「読みやすさを犠牲にした行数削減」を回避 → 指摘対象外。

#### R1-I07: `gd_state.py` `_dispatch_command` の None sentinel 戻り値 (型ヒント曖昧)
- **severity**: Info
- **evidence_file**: `.claude/scripts/gd_state.py`
- **evidence_line**: 642-723
- **evidence_summary**: 未 match 時に None 返却、成功時 int (0/2) 返却の混在。現状は `is None` チェックで正しく判定できるため実害なし。次回 Refactor で `Optional[int]` 型ヒント明示 or `NO_MATCH sentinel` に改善候補。

#### R1-I08: `hga_usage.py` の `HGA_CALLS` ハードコード (ad-hoc 集計スクリプトとして妥当)
- **severity**: Info
- **evidence_file**: `.claude/scripts/hga_usage.py`
- **evidence_line**: 36-41
- **evidence_summary**: 召喚記録が手動 append 前提 (docstring L18-20 で明示)。ad-hoc 集計として妥当。将来 `docs/artifacts/hga-summon-log.md` からの自動抽出方式への発展余地はあるが現時点指摘対象外。

#### R1-I09: `distill-lessons.py` / `detect-permission-mode.py` の hyphen 名は意図的 CLI wrapper
- **severity**: Info
- **evidence_summary**: distill-lessons.py (29 行) は distill_lessons.py への thin wrapper (docstring 明示 / import 制約と CLI 命名慣習の両立)。detect-permission-mode.py (117 行) は「本体を持たない単独 CLI」設計 (importable モジュール化想定なし / `if __name__ == "__main__"` で完結)。SRP 違反ではない。

#### R1-I10: subagent 監督訂正 — verify_reference_resolution.py のテストは `.claude/tests/rules/test_reference_resolution.py` に存在
- **severity**: Info (メタ記録 / issue ではない)
- **evidence_summary**: subagent が「テストファイルが存在しない」と報告したが、実際は `.claude/tests/rules/test_reference_resolution.py` (T4 output / 15 テスト) が存在。subagent が `.claude/tests/scripts/` のみ探索した見落とし。R1-006 の推奨修正方針は当該ファイルに追加テストを書き加える形。

### module 3: `.claude/skills/`

**監査完了**: 2026-07-06 (W-R1 S2 T4 / code-reviewer subagent + L1 監督 + context7 upstream 裏取り)
**集計**: Critical 0 / Warning 3 / Info 2 (R1-016 を subagent 4 件 → 監督修正 3 件に変更)
**特記**: **R1-016 は context7 で upstream 裏取り → subagent 誤判定を訂正** (subagent 側の knowledge gap 事例 / Fable→Opus gap の変種 = 委譲層の情報鮮度リスク)

#### tier タグ一覧 (全 23 件)

| # | skill 名 | tier | 備考 |
|:--|:--------|:-----|:-----|
| 1 | adr-template | utility | R1-016 参照 (`model:` 未文書化) |
| 2 | auditing | utility | - |
| 3 | autonomous | **orchestrator** | R-G7 保護対象 |
| 4 | build-dashboard | utility | - |
| 5 | building | utility | - |
| 6 | clarify | utility | - |
| 7 | full-review | **orchestrator** | R-G7 保護対象 / 951 行と最大規模 |
| 8 | goal-driven | **orchestrator** | R-G7 保護対象 / R1-018 参照 |
| 9 | init-harness | utility | R1-017 参照 (dead reference cluster) |
| 10 | lam-orchestrate | **orchestrator** | R-G7 保護対象 / R1-019 参照 |
| 11 | magi | **orchestrator** | R-G7 保護対象 / 全参照実在確認済 |
| 12 | pattern-review | utility | - |
| 13 | planning | utility | - |
| 14 | project-status | utility | - |
| 15 | quick-load | utility | - |
| 16 | quick-save | utility | - |
| 17 | release | utility | - |
| 18 | retro | utility | - |
| 19 | ship | utility | - |
| 20 | skill-creator | utility | Anthropic 公式ガイド (SKILL.md 公式スキーマ一次情報源) |
| 21 | spec-template | utility | R1-016 参照 |
| 22 | ui-design-guide | utility | R1-016 参照 |
| 23 | wave-plan | utility | - |

#### R1-016: SKILL.md の `model:` フィールドが非文書化 (skill では ignored / `allowed-tools:` は正当)
- **severity**: Warning (subagent 誤: `allowed-tools:` も非公式 → 監督訂正: `model:` のみが問題)
- **responsibility_tag**: `frontmatter`
- **attribution**: `self`
- **status**: `open`
- **opened_at**: 2026-07-06
- **evidence_file**: `.claude/skills/adr-template/SKILL.md`, `spec-template/SKILL.md`, `ui-design-guide/SKILL.md`
- **evidence_line**: 各ファイル 12-13 行付近
- **evidence_summary**: **context7 upstream 検証** (`/websites/code_claude` / topic: skill frontmatter allowed-tools model / 2026-07-06 取得):
  - `allowed-tools:` は Skills frontmatter で**正当** (docs `/docs/en/skills` / 例: `allowed-tools: Read Grep`) ✅
  - `disable-model-invocation:` も正当 ✅
  - `model: sonnet` は Slash Commands frontmatter (`/docs/en/agent-sdk/slash-commands`) では正当だが、**Skills 側では未文書化** — 該当 3 skill の実行時に ignored 疑い (機能不全ではないが effective dead config)
- **推奨修正方針**: 3 skill の `model: sonnet` を削除。もしくは skill の意図 (推奨モデル明示) を本文中の prose 記述に移す。`allowed-tools:` は削除不要 (正当 / むしろ他 skill にも展開すべき候補)。

#### R1-017: `init-harness/SKILL.md` の dead skill/command 参照 cluster (旧 user-global テンプレート残骸)
- **severity**: Warning
- **responsibility_tag**: `spec-drift`
- **attribution**: `self`
- **status**: `open`
- **opened_at**: 2026-07-06
- **evidence_file**: `.claude/skills/init-harness/SKILL.md`
- **evidence_line**: 17, 172 (harness.json 内 enabled_skills), 191, 236, 291-293
- **evidence_summary**: 本文 + 生成する harness.json + CHEATSHEET テンプレートが存在しない skill 群 (`design-mode`, `build-mode`, `audit-mode`, `session-save`, `session-load`) と存在しない spec (`docs/specs/init-harness/spec.md` / 該当ディレクトリ自体不在) を参照。実在は `planning` / `building` / `auditing` / `quick-save` / `quick-load` (`ls .claude/skills/` 確認済)。旧 user-global テンプレートを project-local に複製時の用語同期漏れ。
- **推奨修正方針**: 用語統一 (`design-mode`→`planning`, `build-mode`→`building`, `audit-mode`→`auditing`, `session-save`→`quick-save`, `session-load`→`quick-load`) or 本 skill 廃止/凍結 (本 project は既にハーネス適用済のため実行見込み低)。W-R3 S1-S3 (規律 SSOT 統合) で対応。

#### R1-018: `goal-driven/SKILL.md` 実装ステータス表が stale (「未実装」→ 実在確認)
- **severity**: Warning
- **responsibility_tag**: `spec-drift`
- **attribution**: `self`
- **status**: `open`
- **opened_at**: 2026-07-06
- **evidence_file**: `.claude/skills/goal-driven/SKILL.md`
- **evidence_line**: 389 (`| エージェント定義 3 件 | 未実装 | W2-T1 |`)
- **evidence_summary**: ステータス表が「エージェント定義 3 件」を「未実装」と記載するが、`.claude/agents/goal-driven-grader.md` / `goal-driven-l2-foreman.md` / `goal-driven-l3-executor.md` は実在 (`ls .claude/agents/` 確認済)。SKILL.md 本文の他セクション ([4] 実行ループ, [5] grader 呼び出し) はこれら 3 agent を実装済み前提で記述済 → 本文と表が矛盾。
- **推奨修正方針**: 表の該当行を「完了」に更新 or 実装済タスク番号 (W2-T1 実施済等) 追記。W-R3 S3 (rules 相互矛盾解消) で対応。

#### R1-I14: `lam-orchestrate` と `magi` の bundled resource (`anchor-format.md`) 重複配置
- **severity**: Info
- **evidence_file**: `.claude/skills/lam-orchestrate/references/anchor-format.md`, `.claude/skills/magi/references/anchor-format.md`
- **evidence_summary**: `lam-orchestrate/SKILL.md` L141 は正しく `magi/references/anchor-format.md` を参照するが、`lam-orchestrate/references/` にも同名・同一内容 (diff ゼロ確認済) のファイルが重複。将来 magi 側のみ更新すると即 drift の構造リスク。W-R2 S1 (module 1 相当の軽微整理) 候補。

#### R1-I15: `when_to_use:` フィールドの粒度不統一 (7 skills 使用 / 16 未使用)
- **severity**: Info
- **evidence_summary**: `when_to_use:` を持つ skill (magi, lam-orchestrate, clarify, ui-design-guide, adr-template, spec-template, skill-creator の 7 件) と持たない skill が混在。公式必須フィールドではなく実害はない。将来一貫性のため整理候補。

### module 4: `.claude/tests/`

**監査完了**: 2026-07-06 (W-R1 S2 T5 / L1 直監査)
**集計**: Critical 0 / Warning 2 / Info 3
**注記**: R1-014 (module 4 subagent 差替え) — 本モジュールは L1 直監査 (subagent 委譲せず)。module 3 と並行進行のため。番号採番は R1-030 から (module 3 subagent が R1-016..R1-029 を使用予定 / 空き番号を module 3 用に予約)。

#### R1-030: `.claude/tests/dashboard/` に debug/temp スクリプト 5 件残置 (Dead Code cluster)
- **severity**: Warning
- **responsibility_tag**: `test-hygiene`
- **attribution**: `self`
- **status**: `open`
- **opened_at**: 2026-07-06
- **evidence_file**: `.claude/tests/dashboard/debug_regex.py`, `debug_regex2.py`, `debug_regex3.py`, `verify_git_history.py`, `_check_tasks.py`
- **evidence_line**: 全ファイル (5 件)
- **evidence_summary**: `debug_regex*.py` は docstring も import 文もない一時ヒューリスティック調査スクリプト。`verify_git_history.py` / `_check_tasks.py` は docstring に「一時使用」「一時利用」と明記済 (実測 `head -3`)。pytest 収集対象外の命名だが同ディレクトリに常駐 = テスト資産の見通しを悪くする Dead Code cluster。**module 1 監査 R1-I04 で言及済 (module 4 スコープに正式移送)**。
- **推奨修正方針**: W-R4 S2 (agents 削除 Stage) と同一 Wave で `git rm` 束ね実施。deletions.md 追記対象。

#### R1-031: MilestoneInfo / WaveInfo / TaskInfo 手動構築が 10+ テストファイルに散在 (Rule of Three 違反 / fixture 未共通化)
- **severity**: Warning
- **responsibility_tag**: `test-hygiene`
- **attribution**: `self`
- **status**: `open`
- **opened_at**: 2026-07-06
- **evidence_file**: `.claude/tests/dashboard/test_base_parser.py` (12 参照), `test_session_state_parser.py` (9), `test_tasks_parser.py` (10), `test_v2_view.py` (4), `test_v3_view.py` (13), `test_v4_view.py` (4), `test_wave6_stage2_sort.py` (3), `test_wave6_stage3_filter.py` (8), `test_wave6_stage4_integration.py` (19), `test_wave7_stage3_milestones.py` (5)
- **evidence_line**: 分散 (grep -c 実測)
- **evidence_summary**: MilestoneInfo/WaveInfo/TaskInfo 手動構築が 10 ファイル・計 87 箇所に散在。conftest.py での fixture 共通化がされておらず、Wave 追加のたびに `make_milestone()` 等の重複が増える構造。W-R2 S3 (module 4 Warning 消化 / fixture 重複除去) の主対象。
- **推奨修正方針**: W-R2 S3 で `.claude/tests/dashboard/conftest.py` に `make_milestone(name, status, ...)` / `make_wave(...)` / `make_task(...)` の pytest fixture を集約。既存テストは順次移行。

#### R1-I11: test_session_state_parser.py (789 行) / test_tasks_parser.py (720 行) の大きさは対象パーサ複雑度反映で妥当
- **severity**: Info
- **evidence_summary**: 対象 SessionStateParser (277 行) / TasksParser (201 行) の分岐網羅を目指した結果の行数増大。Split すると parser API の内部境界が曖昧になり保守性劣化のリスク → 現状維持推奨。

#### R1-I12: 統合テスト (test_wave8_stage4_integration.py 534 行 / 9 tests) は 1 test 平均 59 行だが integration test として妥当
- **severity**: Info
- **evidence_file**: `.claude/tests/dashboard/test_wave8_stage4_integration.py`
- **evidence_line**: 129/172/220/285/321/392/429/471/510 (各 test 開始行)
- **evidence_summary**: 各 test は setup (data 構築) + orchestrator 呼び出し + 多点 assertion の 3 段構成。整合性検証が本質のため setup を短縮すると再現性を損なう → Warning 対象外。

#### R1-I13: `test_r1_cycle_detect.py` / `test_reference_resolution.py` が inventory JSON から欠落 (inventory 生成時系列の副作用)
- **severity**: Info (メタ記録)
- **evidence_summary**: inventory JSON 生成は T2 (2026-07-06 前半) で、T3 の test_r1_cycle_detect.py + T4 の test_reference_resolution.py はそれ以降作成。R-G8 baseline 再計測時 (W-R5 S2 T2) に inventory 再生成で解消予定。**R1-008 (gitignore filter) と共に W-R5 S2 baseline 再計測ゲートで吸収**。

### module 5: `.claude/hooks/` + `settings*.json`

_W-R1 S3 T1 (module 5 監査) で起票予定_

### module 6: `.claude/agents/`

_W-R1 S3 T2 (module 6 監査 / 12 件実測) で起票予定_

### module 7: `.claude/rules/` + `auto-generated/`

_W-R1 S3 T3 (module 7 監査 / 11 files + auto-generated) で起票予定_

### module 8: `docs/internal/` (00-07)

_W-R1 S3 T4 (module 8 監査) で起票予定_

### module 9: `docs/specs/`

_W-R1 S4 T1 (module 9 監査) で起票予定_

### module 10: `docs/adr/`

_W-R1 S4 T2 (module 10 監査) で起票予定_

### module 11: `CLAUDE.md` + `CHEATSHEET.md`

_W-R1 S4 T3 (module 11 監査) で起票予定_

---

## 5. 変更履歴

| 日付 | 変更者 | 内容 |
|:-----|:-------|:-----|
| 2026-07-06 | L1 (Opus 4.7) | 初版起票 (W-R1 S2 T1 / 骨組作成 / issue 未起票) |

---

## 6. 参照

- [requirements.md](../specs/large-scale-review/requirements.md) FR-1 / FR-2 / FR-5 / NFR-1 (R-G6/G7/G8) / NFR-3
- [design.md](../specs/large-scale-review/design.md) §3.1 (tracker) / §3.0 (data flow) / §14 (権限等級)
- [tasks.md](../specs/large-scale-review/tasks.md) W-R1 全 Stage
- [green-state-baseline.md](./r-1-green-state-baseline-2026-07-06.md) (G1-G5 + R-G6/G7/G8 baseline)
- [code-quality-guideline.md](../../.claude/rules/code-quality-guideline.md) (Critical/Warning/Info 判断基準)
