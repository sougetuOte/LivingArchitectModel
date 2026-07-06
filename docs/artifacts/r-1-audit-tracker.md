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

**W-R1 S4-T4 完成 (2026-07-06)**: 11 モジュール監査完了 → 33 セル実測値埋め済

| モジュール | Critical | Warning | Info |
|:----------|:--------:|:-------:|:----:|
| 1. `.claude/scripts/dashboard/` | **1** | **2** | **5** |
| 2. `.claude/scripts/` (外) | **0** | **3** | **5** |
| 3. `.claude/skills/` (23 SKILL.md) | **0** | **3** | **2** |
| 4. `.claude/tests/` | **0** | **2** | **3** |
| 5. `.claude/hooks/` + `settings*.json` | **0** | **3** | **4** |
| 6. `.claude/agents/` (12 件) | **0** | **3** | **2** |
| 7. `.claude/rules/` (11 files + auto-generated/) | **0** | **2** | **3** |
| 8. `docs/internal/` (00-07) | **0** | **4** | **5** |
| 9. `docs/specs/` (74 files / depth 制御) | **0** | **1** | **4** |
| 10. `docs/adr/` (10 files) | **0** | **3** | **7** |
| 11. `CLAUDE.md` + `CHEATSHEET.md` | **0** | **2** | **3** |
| **合計 (全 11 module)** | **1** | **28** | **43** |
| **open** (前倒し 2 件 closed 除外) | **1** | **26** | **43** |

**NFR-3 閾値超過確定 (最終)** (spec-critic W5 対応):
- 累計 Critical + Warning = **29 件** (open = 27 件)
- 暫定閾値 10 の **2.9 倍超過** / 予測 (S3 線形外挿 31-32) に整合
- **S5-T4 で条件分岐 sub-task 起票必須** (「閾値超過時 = 優先順位付け sub-task 起票」)
- 実測ベース閾値提案: Critical 単独 3 件 or Critical + Warning 30 件 前後 (S5-T4 で MAGI 判断)

**進捗履歴** (参考): W-R1 S2 module 1-4 (2026-07-06 前半) / S3 module 5-8 (2026-07-06 中盤) / S4 module 9-11 + ヒートマップ完成 (2026-07-06 後半) → 11 モジュール監査完了

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

**監査完了**: 2026-07-06 (W-R1 S3 T1 / code-reviewer subagent + L1 監督)
**集計**: Critical 0 / Warning 3 / Info 4
**特記**: F-2 (python3 hardcode) は subagent 判定 Warning 維持 (単一ユーザー環境でも将来リスク / attribution: `self` + spec_ambiguity 併記)。F-5 の duplication は post-tool-use.py L55 コメントで「同等」と自認済 → maintenance risk として Warning 確定。subagent 生指摘 3 W + 4 I はすべて実在確認済 / 降格・棄却なし。

#### R1-032: `_determine_by_command` の PG コマンド判定が shell メタ文字 (`;` `&&` `` ` `` `$()`) を素通し
- **severity**: **Warning**
- **responsibility_tag**: `permission-check`
- **attribution**: `self`
- **status**: **`closed`** (前倒し消化 / W-R1 期に優先度高判断)
- **opened_at**: 2026-07-06
- **closed_at**: 2026-07-06
- **closed_by_commit**: `8c00786` (TDD Red-Green 完了 / 10 テスト新規 PASS)
- **evidence_file**: `.claude/hooks/pre-tool-use.py`
- **evidence_line**: 163-181 (特に 170-179)
- **evidence_summary**: `command == pg_prefix or command.startswith(pg_prefix + " ")` prefix マッチ後、`_PG_BLACKLISTED_ARGS` (フラグ名のみ) を走査するのみで `;` / `&&` / `||` / `|` / `` ` `` / `$(` の shell 連結・置換演算子を検査しない。例: `ruff format x.py; rm -rf /tmp` は settings.json L4-32 allow (`Bash(ruff format *)`) にも合致し、hook も PG (auto-allow) を返すため両層で通過。コード自身が pre-tool-use.py L65-70 で「settings.json の粗いワイルドカードを hook 側で精密フィルタする二重防御」と明記しており設計意図と実装が乖離。
- **推奨修正方針**: Red で合成 command (`'ruff format x.py; rm -rf /tmp'`) を `_determine_by_command` に渡し AUDITING フェーズで `level != "PG"` を assert。Green で `args_part` に対し `;` / `&&` / `||` / `|` / `` ` `` / `$(` のいずれかを含む場合は無条件で `("PM", "PG command contains shell metacharacter")` を返す分岐を `_PG_BLACKLISTED_ARGS` チェック前段に追加。**W-R4 S3-T4 (hooks 統合)** で消化推奨。

#### R1-033: settings.json 全 5 hook 起動コマンドが `python3` ハードコード (Windows portability リスク)
- **severity**: Warning
- **responsibility_tag**: `settings`
- **attribution**: `self` (併記: `spec_ambiguity` — hook 起動コマンドのポータビリティ要件が仕様未定義)
- **status**: `open`
- **opened_at**: 2026-07-06
- **evidence_file**: `.claude/settings.json`
- **evidence_line**: 74, 80, 86, 91, 96
- **evidence_summary**: 全 hook 起動コマンドが `python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/*.py` 固定。CLAUDE.md は「Windows 11 Pro + Git Bash」明記だが素の Windows Python installer は `python3` エイリアスを提供しない (現環境は pyenv-win 経由で解決)。将来環境変更や新規 contributor 環境で hook が silent failure する構造リスク (hook 起動失敗 = permission システム全崩壊)。
- **推奨修正方針**: (a) `python "$CLAUDE_PROJECT_DIR"/...` に統一 or (b) `command -v python3 >/dev/null && python3 ... || python ...` fallback シェルに変更 or (c) `docs/internal/07_SECURITY_AND_AUTOMATION.md` にポータビリティ要件明文化 (spec_ambiguity 解消のみ)。**W-R4 S3-T4 (hooks 統合)** で消化推奨。

#### R1-034: `_PM_PATH_PATTERNS_FOR_CACHE` (post-tool-use.py) と `_PM_PATTERNS` (pre-tool-use.py) が別々定義で重複保守
- **severity**: Warning
- **responsibility_tag**: `permission-check`
- **attribution**: `self`
- **status**: `open`
- **opened_at**: 2026-07-06
- **evidence_file**: `.claude/hooks/post-tool-use.py`, `.claude/hooks/pre-tool-use.py`
- **evidence_line**: post-tool-use.py L55-61 / pre-tool-use.py L92-99
- **evidence_summary**: post-tool-use.py L55 コメントで「pre-tool-use.py の `_PM_PATTERNS` と同等 / キャッシュ対象判定用」と自認しつつ、正規表現リストが手書き複製 (4 patterns)。**out-of-root パターン (pre 側 L94) はキャッシュ側に存在せず**、out-of-root 経由の PM 判定はセッションスコープ降格キャッシュ対象外という非対称挙動 (意図的か未検証か design.md 上でも確認できず)。将来どちらか一方のみ更新すると PM 級キャッシュ判定と実際の PM 級判定が drift する保守リスク。
- **推奨修正方針**: Red で「両リストのパス系パターン (out-of-root を除く) が完全一致」を assert するテスト追加。Green で `_hook_utils.py` に一本化し双方 import に切替。out-of-root asymmetry は「安全側維持 or キャッシュ対象化」を design 側で決定してからコメントで意図明示。**W-R4 S3-T4 (hooks 統合)** で消化推奨。

#### R1-I16: subagent 起動 (Task/Agent) の非 AUTONOMOUS フェーズ二重ログ記録
- **severity**: Info
- **evidence_file**: `.claude/hooks/pre-tool-use.py`
- **evidence_summary**: `_handle_subagent_boundary` が非 AUTONOMOUS で `("LOG", ...)` を返し `main()` が 1 行書き込むが、`sys.exit()` せず後続 `_determine_level_and_reason` に継続 → Task/Agent は file_path/command 未保持のため `("SE", "no-path (default SE)")` として 2 行目書き込み。1 回の subagent 起動につき permission.log に 2 行 (LOG + SE) が記録され解析時に紛らわしい。次回 hooks リファクタで統一候補。

#### R1-I17: `docs/artifacts/incident-patterns.yaml` の毎回ファイル I/O ロード
- **severity**: Info
- **evidence_file**: `.claude/hooks/_incident_patterns.py`
- **evidence_line**: 8-9, 51-97
- **evidence_summary**: モジュール docstring が「副作用なし・毎回ファイル読込」を意図的設計と明記 (即時反映・テスト容易性のトレードオフ)。現状ファイルサイズ (6.2KB) では実害軽微だが、パターン数増大時のレイテンシ影響懸念。設計意図明示済のため Info 起票のみ。

#### R1-I18: out-of-root マーカーが PM 級キャッシュ機構でスキップされる非対称設計
- **severity**: Info
- **evidence_file**: `.claude/hooks/pre-tool-use.py`, `.claude/hooks/post-tool-use.py`
- **evidence_summary**: pre-tool-use.py L94 `_PM_PATTERNS` には `^__out_of_root__/` が PM 理由として含まれるが、post-tool-use.py L56-61 `_PM_PATH_PATTERNS_FOR_CACHE` には未含有。root 外パス書込が PM 級判定された場合、承認後もセッションスコープ降格キャッシュに登録されず、同一セッション内で毎回 PM ダイアログ再表示 (安全側挙動 / 実害なし)。**R1-034 と一体で消化**。

#### R1-I19: `settings.local.json` の `Read` allow が個人環境パスを含む (ローカル限定・共有非対象)
- **severity**: Info
- **evidence_file**: `.claude/settings.local.json`
- **evidence_line**: 1-9
- **evidence_summary**: `Read(//c/Users/metral/**)` / `Read(//c/work5/Kage-Shiki/**)` は個人環境固有パス。ファイル名 `.local.json` からチーム共有非対象 (LAM 監査対象外 / Green State 判定に影響なし)。指摘のみ記録。

### module 6: `.claude/agents/`

**監査完了**: 2026-07-06 (W-R1 S3 T2 / L1 直監査 + context7 upstream 裏取り)
**集計**: Critical 0 / Warning 3 / Info 2
**特記**: context7 (`/websites/code_claude` sub-agents / AgentDefinition Python dataclass) で公式 frontmatter フィールド確定 → `# permission-level:` は非公式 (dead comment cluster) / `effort:` は公式だが `default` は EffortLevel 列挙値外 / `tools: Agent(name)` parametrized は `settings.json permissions.deny` 側は公式サポート済だが subagent frontmatter `tools:` allowlist 側は未確定 (要実測)。

#### R1-035: `# permission-level: XX` コメントアウトが 8 agents に散在 (dead comment cluster)
- **severity**: Warning
- **responsibility_tag**: `frontmatter`
- **attribution**: `self`
- **status**: `open`
- **opened_at**: 2026-07-06
- **evidence_file**: `.claude/agents/code-reviewer.md`, `design-architect.md`, `doc-writer.md`, `quality-auditor.md`, `requirement-analyst.md`, `task-decomposer.md`, `tdd-developer.md`, `test-runner.md`
- **evidence_line**: 各 L7-L8
- **evidence_summary**: `# permission-level: SE/PG/PM` コメントアウトが 8 files で散在 (grep 実測)。context7 (`/websites/code_claude` sub-agents / `AgentDefinition` dataclass) 検証結果、`permission-level:` は公式 sub-agents frontmatter に**存在しない** (公式フィールド = name/description/tools/model/memory/skills/effort/permissionMode/mcpServers/initialPrompt/maxTurns/background/disallowedTools/hooks)。LAM の permission-level 判定は `pre-tool-use.py` のパスベース判定 (`permission-levels.md`) で実装済のため、frontmatter 側経路は完全に dead。gabriel / goal-driven-* 4 agents は既に持たない (統一済状態が正)。
- **推奨修正方針**: 8 files から `# permission-level:` 行を削除。**W-R4 S2-T4 (agents 改名) or W-R3 S3 (rules 相互矛盾解消)** で消化。

#### R1-036: `goal-driven-l3-executor.md` の `effort: default` は EffortLevel 列挙値外 (dead config 疑い)
- **severity**: Warning
- **responsibility_tag**: `frontmatter`
- **attribution**: `self` (併記: `spec_ambiguity`)
- **status**: `open`
- **opened_at**: 2026-07-06
- **evidence_file**: `.claude/agents/goal-driven-l3-executor.md`
- **evidence_line**: 9, 28, 120
- **evidence_summary**: `effort:` フィールドは公式 (`AgentDefinition.effort: EffortLevel | int | None` / context7 検証済) だが EffortLevel 列挙値は `low/medium/high/xhigh/max` 相当。**`default` は列挙外**。design §12 FR-8「ultracode (xhigh) 昇格禁止」の意図実現手段として使用されているが Claude Code が受け付ける値ではなく effectively ignored (R1-016 と同型 dead config)。docs/specs/goal-driven-orchestration/design.md §12 側も同時更新必要 (spec drift 兆候)。**Fable→Opus gap**: 仕様側の暗黙値決定が upstream 仕様確認前になされた可能性 (retro §Problem P1 事例 #2/#3 の変種)。
- **推奨修正方針**: (a) `effort: low` に置換 + design §12 更新 or (b) フィールド削除 + 別手段で xhigh 封じ。**W-R3 S3 (rules 相互矛盾解消) or W-R4 S3 (skills 削除 + hooks 統合)** で追加調査後に消化。

#### R1-037: `goal-driven-l2-foreman.md` の `tools: Agent(goal-driven-l3-executor)` parametrized 記法が subagent frontmatter で未文書化
- **severity**: Warning
- **responsibility_tag**: `frontmatter`
- **attribution**: `self` (併記: `spec_ambiguity`)
- **status**: `open`
- **opened_at**: 2026-07-06
- **evidence_file**: `.claude/agents/goal-driven-l2-foreman.md`
- **evidence_line**: 7
- **evidence_summary**: `tools: Read, Glob, Grep, Agent(goal-driven-l3-executor)` の parametrized 記法。context7 検証で 2026-w25 `settings.json permissions.deny` 側の `Agent(model:opus)` 記法は公式サポート確認済だが、subagent frontmatter `tools:` allowlist 側でこの記法が正当かは**明記なし**。可能性: (a) 公式サポート未文書化 / (b) plain `Agent` として parse され parametrized 部分無視 (実質全 Agent 起動許可 = overpermission) / (c) parse error で `Agent` tool 無効化。実測必要。
- **推奨修正方針**: (1) 実測 (`.claude/agents/goal-driven-l2-foreman` を Task ツールで起動 → 別 agent の spawn を試みる → 挙動観察)。(2) 結果に応じて `disallowedTools` で明示他 agent 封じ or `tools: Agent` (plain) 化 + 実装側自制。**W-R4 S3-T4 (hooks 統合)** で追加調査後に消化。

#### R1-I20: agent description YAML block style 不統一 (`>` folded vs `|` literal)
- **severity**: Info
- **evidence_summary**: 12 agents 中 `code-reviewer` / `doc-writer` / `test-runner` が `>` (folded)、他 9 が `|` (literal) (grep 実測)。両方 YAML 正当だが inconsistent。description は plain text として consume されるため実害なし。次回 hygiene で統一候補。

#### R1-I21: gabriel.md のみ完全 JSON schema 定義、他 11 agents は Markdown 例示のみ
- **severity**: Info
- **evidence_file**: `.claude/agents/gabriel.md`
- **evidence_line**: 79-121, 134-147
- **evidence_summary**: gabriel.md は JSON schema draft-07 完全定義 + クロスフィールド制約 (FR-W-C-6) 明記。他 agents (goal-driven-grader / l2-foreman / l3-executor 含む) は Markdown 出力例のみ。gabriel は high-stakes verifier のため厳密性重視の意図あり (正当な差別化 / 変更不要)。統一提案は Info 級。

### module 7: `.claude/rules/` + `auto-generated/`

**監査完了**: 2026-07-06 (W-R1 S3 T3 / code-reviewer subagent + L1 監督)
**集計**: Critical 0 / Warning 2 / Info 3
**特記**: subagent が全 14 files で参照する実装・仕様・ADR・internal SSOT を Grep/Bash で実在確認済 (unverified なし)。両 Warning は「同一トピックの重要度/枠組み定義の rules 間 drift」で construct-level (実運用破綻は未確認 / W-R3 で消化)。

#### R1-038: `code-quality-guideline.md` と `phase-rules.md` の「テストなし実装」重要度判定 drift
- **severity**: Warning
- **responsibility_tag**: `rules-consistency`
- **attribution**: `self` (併記: `spec_ambiguity` — 両者の優先順位が rules 上で明記されていない)
- **status**: `open`
- **opened_at**: 2026-07-06
- **evidence_file**: `.claude/rules/code-quality-guideline.md`, `.claude/rules/phase-rules.md`
- **evidence_line**: code-quality-guideline.md L37 / phase-rules.md L87
- **evidence_summary**: `code-quality-guideline.md` L37 は「テストが存在しない新規ロジック」を明示的に **Warning (non-blocking)** に分類し「BUILDING の TDD ルール違反でもあるが、保守困難性の観点で Warning」と注記。一方 `phase-rules.md` L87 は BUILDING 「禁止」リストに「テストなし実装」を無条件掲載し Critical 相当の絶対規律として読める。同一トピックで AUDITING 時の重要度 (Warning) と BUILDING 時の規律 (絶対禁止) が別重みづけを持ち、優先順位が rules 上未明記。監査担当が Critical/Warning に倒すべきか判断がぶれるリスク。
- **推奨修正方針**: code-quality-guideline.md L37 に「ただし BUILDING フェーズ中の禁止事項 (`phase-rules.md`) としては別途扱う。AUDITING 時点での重要度判定は本項の Warning を用いる」等、両者関係性を明示する 1 文追加。**W-R3 S3 (rules 相互矛盾解消)** で消化。

#### R1-039: `hga-summoning.md` の envelope 記述に新旧併存の矛盾 (月 $40-80 単一枠 vs 二軸化後の実 $/quota 分離)
- **severity**: Warning
- **responsibility_tag**: `rules-consistency`
- **attribution**: `self`
- **status**: `open`
- **opened_at**: 2026-07-06
- **evidence_file**: `.claude/rules/hga-summoning.md`
- **evidence_line**: 94-110
- **evidence_summary**: L96「以下は月 $40-80 の envelope の**外**とする」が、直後 L103-110「envelope 定義 (2026-07-04 二軸化)」節で導入された「実 $ envelope (月 $10-40)」+「Opus quota envelope (weekly cap 20%)」の二軸とどう対応するか不明瞭。二軸化後は「月 $40-80 envelope」概念が実質置換されているが L96 旧記述残存 → 「対話モード召喚」「branch モード」がどちらの軸の外かユーザーが判断不能。
- **推奨修正方針**: L96 を「以下は実 $ envelope (月 $10-40) および Opus quota envelope (weekly cap 20%) の両方の**外**とする」等、二軸化後の用語に統一。**PM 級ファイルのため W-R3 S3 で人間承認取得の上修正**。

#### R1-I22: `hga-summoning.md` L200/L245 の「Wave C」表記が terminology.md アルファベット付番禁止に近接
- **severity**: Info
- **evidence_file**: `.claude/rules/hga-summoning.md`, `.claude/rules/terminology.md`
- **evidence_line**: hga-summoning.md L200, 245 / terminology.md §2 Wave 節 (L64-68 相当)
- **evidence_summary**: hga-summoning.md に「Wave C Spike」表記が 2 箇所 (2026-07-04 追加 = terminology.md 適用開始日 2026-06-20 以降の新規記述)。terminology.md §2「Wave は正整数または『整数.5』形式で付番 (Wave 1a 等のアルファベット混在は使わない)」に近接違反。ただし terminology.md §5 経過措置により Info 起票許容 (旧 B-4 Milestone 期の Wave A/B/C/D 命名の legacy 引き継ぎと推定)。
- **推奨修正方針**: 次回 hga-summoning.md 編集時に「B-5 Wave 2 Spike」等の正式 Wave 番号 or 単なる「Spike セッション」等の作業名に置換。優先度低。

#### R1-I23: `hga-summoning.md` 移行期注記 (L314-318) が監査時点で翌日 (2026-07-07) 期限
- **severity**: Info
- **evidence_file**: `.claude/rules/hga-summoning.md`
- **evidence_line**: 314-318
- **evidence_summary**: 「移行期注記」節が「2026-07-07 までは... 直セッション運用も許容」「2026-07-07 以降のクレジット従量移行後は本規律を既定」と記述。監査実施日 (currentDate 2026-07-06) から翌日で条件分岐切替。R-1 Milestone 進行中に運用条件変化 → W-R2/W-R3 タイミングで「2026-07-07 経過後の要否確認」の棚卸し対象。
- **推奨修正方針**: 修正不要 (現時点で矛盾ではない)。次回 hga-summoning.md 編集時に本節要否・内容更新を検討。

#### R1-I24: `test-result-output.md` の「テストFW設定追加 = PG級」が permission-levels.md PG 級定義と緊張関係
- **severity**: Info
- **evidence_file**: `.claude/rules/test-result-output.md`, `.claude/rules/permission-levels.md`
- **evidence_line**: test-result-output.md L100-103 / permission-levels.md L6-15 (PG 級列挙)
- **evidence_summary**: test-result-output.md L103 が「テストFW設定追加」を PG 級と定めるが、permission-levels.md PG 級列挙は「既存振る舞いを変えない機械的修正」限定 (フォーマット / typo / lint 自動修正等)。`pyproject.toml` へのテストレポーター設定追加 (新規パス導入 = 振る舞い変更) は厳密には非該当で、むしろ SE 級「テスト追加・修正」に近い。実害小 (両ルールとも「軽い関与で良い」結論は近い) だが等級定義に微妙な不整合。
- **推奨修正方針**: test-result-output.md L103 を SE 級修正 or permission-levels.md PG 級列挙に「本ルールに従ったテストFW設定追加」明示追加。**W-R3 S3 (rules 相互矛盾解消)** で消化候補。優先度低。

### module 8: `docs/internal/` (00-07)

**監査完了**: 2026-07-06 (W-R1 S3 T4 / code-reviewer subagent + L1 監督)
**集計**: Critical 0 / Warning 4 / Info 5 (subagent 生指摘 W 5 → F-5 (phase-rules 2 軸表 absence) を Info 降格 / subagent 自身が「Info 昇格でも可・境界事例」明記)
**特記**: docs/internal SSOT 親と子 rules / 実装 / spec の drift が主軸。W-R3 S2 (docs/internal SSOT drift 解消 / 一括承認 Stage) の直接材料。特に **R1-042 (gabriel 出力契約 6 vs 4 field drift)** は分岐制御 field 欠落で優先度高。

#### R1-040: `docs/design/` ディレクトリが 00_PROJECT_STRUCTURE.md 構成表に存在しない (実体は 02 が参照 + 6 files 実在)
- **severity**: Warning
- **responsibility_tag**: `ssot-parent-child-consistency`
- **attribution**: `self`
- **status**: `open`
- **opened_at**: 2026-07-06
- **evidence_file**: `docs/internal/00_PROJECT_STRUCTURE.md`
- **evidence_line**: 9-37 (Directory Structure ツリー)
- **evidence_summary**: `00_PROJECT_STRUCTURE.md` §1 ディレクトリ構成ツリーには `docs/specs/` `docs/adr/` `docs/tasks/` `docs/internal/` `docs/artifacts/` `docs/slides/` `docs/daily/` `docs/memos/` のみ列挙、`docs/design/` **欠落**。一方 `docs/internal/02_DEVELOPMENT_FLOW.md` L47 は `/clarify docs/design/<feature>-design.md` を明示参照し、実ディレクトリ `docs/design/` には `cross-module-blame-design.md` 等 **6 files 実在** (subagent Bash `ls docs/design` で確認済)。「ドキュメント資産の地図」としての 00 が実運用と乖離。
- **推奨修正方針**: 00_PROJECT_STRUCTURE.md §1 ツリーに `docs/design/` (設計書 / Phase 1 成果物) 追加 + §2-B (Specifications) 類似の配置ルール節新設。**W-R3 S2 (docs/internal SSOT drift 解消)** で消化。

#### R1-041: 07_SECURITY_AND_AUTOMATION.md の Green State 記述が MVP/完全実装の段階区分欠落 (G3/G4 常時必須のように読める)
- **severity**: Warning
- **responsibility_tag**: `spec-drift`
- **attribution**: `downstream` (07 が SSOT 親 `green-state-definition.md` §2.1-2.2 の段階導入情報を反映していない)
- **status**: `open`
- **opened_at**: 2026-07-06
- **evidence_file**: `docs/internal/07_SECURITY_AND_AUTOMATION.md`
- **evidence_line**: 111-115 (Stop hook 自律ループ制御節)
- **evidence_summary**: 07 は「Green State (G1: テスト全パス + G2: lint 0 + G3: Issue 解決 + G4: 仕様差分 0 + G5: セキュリティ) 達成で停止」と記載のみで、`docs/specs/green-state-definition.md` §2.1「MVP では G1+G2+G5 の 3 条件を自動判定 / G3, G4 は完全実装で段階的追加」の段階導入に触れず。同仕様 §2.2 「AUTONOMOUS モードは Wave 2 まで G1 のみ」も未反映。07 通り読むと現行 AUTONOMOUS 実装 (G1 のみ) が「未達成状態」と誤読されうる。
- **推奨修正方針**: 07 §5「Stop hook による自律ループ制御」に「MVP は G1+G2+G5 / G3/G4 は完全実装で段階導入 (詳細: `green-state-definition.md` §2.1-2.2)」を 1 文追記。**W-R3 S2** で消化。

#### R1-042: 06_DECISION_MAKING.md §6.5 の gabriel 出力契約 6 fields が `.claude/rules/decision-making.md` 要約版で 4 fields に縮退 (`affected_atoms` + `recommended_action` 欠落)
- **severity**: **Warning** (優先度高 / 分岐制御 field 欠落)
- **responsibility_tag**: `ssot-parent-child-consistency`
- **attribution**: `downstream` (子 rules が親 SSOT の必須 field を反映していない)
- **status**: **`closed`** (前倒し消化 / W-R1 期に優先度高判断 = 実運用で gabriel abort 判定損失リスク解消)
- **opened_at**: 2026-07-06
- **closed_at**: 2026-07-06
- **closed_by_commit**: `8c00786` (6 fields + 分岐優先順位追記)
- **evidence_file**: `docs/internal/06_DECISION_MAKING.md`, `.claude/rules/decision-making.md`
- **evidence_line**: 06 L242-251 (§6.5 gabriel 出力契約 6 fields) / decision-making.md L59-64 (gabriel probe 出力フォーマット 4 items)
- **evidence_summary**: 親 SSOT 06 は gabriel 出力契約を **6 fields** と明記: `verdict/severity/affected_atoms/reasoning/recommended_action/confidence`。`affected_atoms` (verdict=refuted 時非空必須) と `recommended_action` (proceed/re-magi/abort 分岐制御必須 / §6.6 失敗時挙動が abort/critical/warning/info 分岐に依存) を含む。しかし実行時ロードされる要約版 `.claude/rules/decision-making.md` の Output Format には **4 items のみ** (verdict/severity/confidence/reasoning) 記載で、**分岐制御に必須の 2 fields が欠落**。要約版のみ参照する実行時に abort 判定が抜け落ちるリスク。
- **推奨修正方針**: `.claude/rules/decision-making.md` の gabriel probe セクションに `affected_atoms` と `recommended_action` 追加 + 06 §6.6 の分岐優先順位 (abort > critical > warning > info > confirmed > inconclusive) への言及も 1 文追加。**PM 級ファイルのため W-R3 S2 一括承認想定**。

#### R1-043: 00_PROJECT_STRUCTURE.md の `.claude/states/*.json` 説明 (「フェーズごとの承認ゲート管理」) が実態 (機能/Milestone 単位) と乖離
- **severity**: Warning
- **responsibility_tag**: `spec-drift`
- **attribution**: `self`
- **status**: `open`
- **opened_at**: 2026-07-06
- **evidence_file**: `docs/internal/00_PROJECT_STRUCTURE.md`
- **evidence_line**: 68
- **evidence_summary**: 00 §2-E は「`.claude/states/*.json`: フェーズごとの承認ゲート管理、タスク進捗の永続的状態記録」と記述。しかし実ファイルは `cc-spec-alignment.json` / `cross-module-blame.json` / `gitleaks-integration.json` / `goal-driven-orchestration.json` / `hooks-python-migration.json` / `large-scale-review.json` / `magi-skill.json` / `scalable-code-review.json` / `v4.0.0-immune-system.json` の **9 files** (subagent Bash `ls` 実測)、**いずれも Milestone/機能単位命名**で「フェーズ (PLANNING/BUILDING/AUDITING) ごと」の粒度ではない。フェーズ現在値管理は `.claude/current-phase.md` (00 §2-E 直後で正確に説明) が担い、states/*.json は別責務 (機能別承認ゲート・進捗)。
- **推奨修正方針**: 00 §2-E 該当行を「機能/Milestone 単位の承認ゲート状態・進捗記録 (例: `<milestone-slug>.json`)」に修正 + 「フェーズごとの」誤解表現除去。**W-R3 S2** で消化。

#### R1-I25: 02_DEVELOPMENT_FLOW.md が phase-rules.md の「フェーズ × 権限等級」二軸表 (3x3) 全体像要約を欠く
- **severity**: Info (境界事例 / subagent 生 Warning → L1 監督で Info 降格 / subagent 自身「Info 昇格でも可」明記)
- **evidence_file**: `docs/internal/02_DEVELOPMENT_FLOW.md`, `.claude/rules/phase-rules.md`
- **evidence_line**: 02 L100-107 (権限等級に基づく修正制御節 / AUDITING のみ抜粋) / phase-rules.md 冒頭「フェーズとの二軸設計」表
- **evidence_summary**: 02 Phase 3 節は AUDITING の PG/SE/PM 制御のみ抜粋、子 rules phase-rules.md 冒頭の「PLANNING/BUILDING/AUDITING × PG/SE/PM」3x3 マトリクス (PLANNING 全列 `-` = 承認ゲートのみ) の全体像を欠く。02 Phase 1 (PLANNING) 節も権限等級言及なし → 読者は「PLANNING では PG/SE/PM 適用なし」を 02 単独では読み取れず (phase-rules.md separate 読了必要)。矛盾ではないが親 SSOT が子の全体設計要約を欠く。
- **推奨修正方針**: 02 Phase 1 冒頭 or Phase 3 冒頭に「フェーズ × 権限等級全体設計は `.claude/rules/phase-rules.md` 冒頭二軸表参照 (PLANNING は承認ゲートのみで PG/SE 概念適用なし)」の 1 文追加。**W-R3 S2** で消化候補。

#### R1-I26: 05_MCP_INTEGRATION.md §5 の `.mcp.json` 設定例がプレースホルダーのみで実プロジェクト未存在
- **severity**: Info
- **evidence_file**: `docs/internal/05_MCP_INTEGRATION.md`
- **evidence_line**: 84-118
- **evidence_summary**: `.mcp.json` は Glob 実測で本プロジェクトに未存在。05 冒頭で「MCP サーバーはすべてオプション」明記のため矛盾ではないが、LAM 自身が serena/heimdall 等未採用の旨明記なし。
- **推奨修正方針**: 冒頭 Note に「本 LAM プロジェクトでは現時点で MCP サーバー未導入」1 文追記 (任意)。

#### R1-I27: 02_DEVELOPMENT_FLOW.md「MAGI System との連携」節が AoT 適用要否判断基準 (06 §5.3) 参照を欠く
- **severity**: Info
- **evidence_file**: `docs/internal/06_DECISION_MAKING.md`, `docs/internal/02_DEVELOPMENT_FLOW.md`
- **evidence_line**: 06 L68-77 (AoT SSOT 宣言) / 02 L27-40 (MAGI System 連携表)
- **evidence_summary**: 02「タスク分割 | タスクの Atom 化 + Wave 構成判断」記述が 06 の AoT 適用条件 (判断ポイント 2+ / レイヤー 3+ / 選択肢 3+) と併記されず、02 単独読了で AoT 適用要否判断基準が見えない。06 参照リンクで充足しているとも判断可能な境界事例。
- **推奨修正方針**: 対応不要 (現状 06 参照で充足)。将来的に 02 表に「適用要否は 06 §5.3 参照」1 行追加すると親切。

#### R1-I28: 04_RELEASE_OPS.md がプロジェクト非依存の一般テンプレートで LAM リリース実態 (Milestone/Wave 開発 / 配布物なし) との接続が薄い
- **severity**: Info
- **evidence_file**: `docs/internal/04_RELEASE_OPS.md`
- **evidence_line**: 1-43 (全文)
- **evidence_summary**: 04 は「本番環境デプロイ」「パッケージ公開」等 SaaS/アプリ開発前提の汎用内容で、LAM (Claude Code 設定・rule・skill 群) の実際の運用 (CHANGELOG.md 実在確認済 / SemVer 運用実例 / git tag 運用実態) との接続が示されず。05 MCP と同様の汎用テンプレート性で致命的ではない。
- **推奨修正方針**: 対応不要、または「本プロジェクトでは配布物を持たないため §1-2 は将来のプロダクト化時に適用」の Note 追記。

#### R1-I29: `.claude/rules/decision-making.md` の AoT フロー表記が 06 §5.2/5.4 mermaid と異なる (テキスト矢印 vs mermaid)
- **severity**: Info
- **evidence_file**: `docs/internal/06_DECISION_MAKING.md`, `.claude/rules/decision-making.md`
- **evidence_line**: 06 L98-109 (mermaid flowchart) / decision-making.md L37-43 (テキスト矢印)
- **evidence_summary**: 内容自体は矛盾していないが、06 が mermaid で厳密フローチャート (分岐含む) を持つのに対し、要約版はシンプルな一直線矢印表現のみで「複数条件のいずれか該当」の OR 分岐ニュアンスが失われる (実害は R1-042 の方が大 / 表現形式の違いのみ)。
- **推奨修正方針**: 対応不要 (要約版としての簡略化は許容範囲)。

### module 7: `.claude/rules/` + `auto-generated/`

_W-R1 S3 T3 (module 7 監査 / 11 files + auto-generated) で起票予定_

### module 8: `docs/internal/` (00-07)

_W-R1 S3 T4 (module 8 監査) で起票予定_

### module 9: `docs/specs/` (74 files / depth 制御)

**監査完了**: 2026-07-06 (W-R1 S4 T1 / code-reviewer subagent + L1 監督 / **depth 3-tier 制御**)
**集計**: Critical 0 / Warning 1 / Info 4 (subagent 集計 header 誤り W=4/I=3 → L1 実測 W=1/I=4 に訂正)
**depth 分類**: Tier A 精読 15 files / Tier B 骨子スキャン 20 files / Tier C 存在確認 39 files
**特記**: 74 files (15,396 行) の巨大モジュールを depth 制御で監査 → 主要 SSOT の drift 検出に集中し context 節約。**F-1 は 3 Milestone 横断の系統的 drift** (Rule of Three 該当 / 個別 spec 誤記ではなく Milestone クローズ運用の欠落) で W-R3 S4 一括修正候補。F-3 (v5-fat-reduction 反証記録) は W-R3 一括修正時の誤爆防止情報として起票価値高。

#### R1-046: 実装完了済み spec の親メタ「ステータス」が Draft のまま (3 Milestone 系統的 drift / Rule of Three)
- **severity**: Warning
- **responsibility_tag**: `spec-drift`
- **attribution**: `self` (systematic / Milestone クローズ運用の欠落)
- **status**: `open`
- **opened_at**: 2026-07-06
- **evidence_file**: `docs/specs/b4-dashboard/{design,requirements}.md`, `docs/specs/goal-driven-orchestration/{requirements,design,tasks,config}.md`, `docs/specs/magi-v2-gabriel/{requirements,design}.md`
- **evidence_line**: 各ファイル冒頭 5-7 行目付近「ステータス」フィールド
- **evidence_summary**: 3 独立 Milestone で「実装完了済み (tasks.md 本文 or 実コード確認済)」だが親仕様メタ status が未更新:
  1. **b4-dashboard**: `design.md` = "Draft (Wave 9 設計反映 / PM 承認待ち)" だが `wave9/design.md` は "Approved (2026-07-02 Phase 6 PM 一括承認)" で Wave 1-9 全 Approved 済 (B-5 Milestone 完了確認済)。
  2. **goal-driven-orchestration**: 4 files 全て "Draft (PM 承認待ち)" だが `tasks.md` L4-9 で「B-3 完了 / PM-G3 承認 2026-06-18」明記。実装 (`.claude/agents/goal-driven-*.md` 3 件 / `.claude/scripts/gd_*.py`) は module 2/6 で稼働確認済。
  3. **magi-v2-gabriel**: `requirements.md` / `design.md` (v0.4.0) 全て "Draft" だが `tasks.md` は "Approved (2026-07-02 Phase 6 PM 一括承認)"。`.claude/agents/gabriel.md` は module 6 R1-036/R1-037 で稼働確認済 (`model: sonnet`)。

  Rule of Three 該当 = 個別誤記でなく「Milestone クローズ時のメタ status 同期プロセス欠落」の運用 gap。
- **推奨修正方針**: **W-R3 S4 (`docs/specs/` 一貫性修正)** で一括対応。各ファイル冒頭ステータス行を実態 (Approved + 承認日) に更新。**重要**: v5-fat-reduction も同じ Draft 表記だが実は未着手正常状態 (R1-I34 反証記録参照 / 誤爆防止)。**恒久対策**: `/ship` or Milestone クローズ時チェックリストに「関連 `docs/specs/*/requirements.md` + `design.md` のステータス行同期」追加 (rule 化候補 / W-R5 retro で判断)。

#### R1-I33: `handoff-format.md` も同系統で "draft" のまま
- **severity**: Info
- **evidence_file**: `docs/specs/goal-driven-orchestration/handoff-format.md`
- **evidence_line**: 2
- **evidence_summary**: `**Status**: draft`。対応要件 AC-15 (FR-10) 実装済 (`lam-orchestrate` 接続稼働確認済 / `tasks.md` W6-T2 完了記録)。R1-046 と同根 → 一括対応で解消。

#### R1-I34: v5-fat-reduction の "Draft" は正しい状態 (反証記録 / R1-046 の誤爆防止)
- **severity**: Info
- **responsibility_tag**: `false-positive-check`
- **evidence_file**: `docs/specs/v5-fat-reduction/{requirements,design,tasks}.md`, `docs/artifacts/retro-B4-W1-W15-2026-06-20.md`
- **evidence_line**: retro L83
- **evidence_summary**: F-1 (R1-046) と同じ "Draft (PM 承認待ち)" 表記だが、実際は BUILDING 未実施 (tasks.md チェックボックス 57 中 3 のみ `[x]` / retro に「Wave 1 で完結 / Wave 2 存在せず」明記)。**W-R3 S4 での R1-046 対応時に誤って v5-fat-reduction を "Approved" 化しないよう注意** (逆 drift 発生防止)。

#### R1-I35: `magi-skill-spec.md` (Tier C flat spec) の "draft" 表記が長期未更新
- **severity**: Info
- **evidence_file**: `docs/specs/magi-skill-spec.md`
- **evidence_line**: 5
- **evidence_summary**: `**ステータス**: draft` (作成日 2026-03-16)。`.claude/skills/magi/SKILL.md` は module 3 監査で orchestrator tier 稼働確認済。長期未更新 Tier C ファイルのため深追いせず Info 止。将来の docs/specs 棚卸し候補。

#### R1-I36: `tdd-introspection-v2.md` の前提文書参照は実在確認済 (drift なし / positive observation)
- **severity**: Info
- **responsibility_tag**: `reference-integrity`
- **evidence_file**: `docs/specs/tdd-introspection-v2.md`, `docs/design/v4.0.0-immune-system-design.md`
- **evidence_line**: tdd-introspection-v2.md L6
- **evidence_summary**: 「前提: v4.0.0 免疫系アーキテクチャ (`docs/design/v4.0.0-immune-system-design.md`)」参照は実ファイル存在確認済 (`ls` 実測)。R1-040 (module 8 で `docs/design/` が 00_PROJECT_STRUCTURE.md 未掲載を指摘) と根は同じだが本ファイル記述に誤りなし。**R1-040 対応で自動解消**。

### module 10: `docs/adr/` (10 files / 1,580 行)

**監査完了**: 2026-07-06 (W-R1 S4 T2 / code-reviewer subagent + L1 監督)
**集計**: Critical 0 / Warning 3 / Info 7 (subagent 生 W=4/I=6 → L1 監督で F-4 「Wave C 表記」を Warning → Info 降格 / R1-I22 module 7 で同型を既に Info 起票済との一貫性)
**特記**: ADR 特有の「決定の記録」性質上、Accepted 済決定への異議は原則起票禁止。W 3 件はいずれも「ADR 間相互参照 supersede 明記欠落」or「実装パス stale」の追跡性 (traceability) 問題。**F-1 が唯一「決定と実装の乖離」で優先度最高** (ADR-0001 Proposed 放置 + 決定内容の第2層が未実装)。

#### R1-047: ADR-0001 が Proposed のまま約 4 ヶ月放置 + 決定内容の第2層 (prompt/haiku ハンドラ) が未実装
- **severity**: **Warning** (優先度高 / 「決定と実装の乖離」)
- **responsibility_tag**: `adr-status`
- **attribution**: `self`
- **status**: `open`
- **opened_at**: 2026-07-06
- **evidence_file**: `docs/adr/0001-model-routing-strategy.md`
- **evidence_line**: 4, 38-44
- **evidence_summary**: status = `Proposed` (2026-03-08 のまま)。決定内容 = 3 層ルーティング「第1層 パスベース (command型) / 第2層 内容ベース (prompt型 / haiku) / 第3層 深い検証 (agent型 / sonnet)」。実測: `.claude/settings.json` hooks 全 5 件 = `type: command` のみ、`.claude/hooks/pre-tool-use.py` 等は純粋 Python で LLM 呼び出しなし、grep で「第2層 prompt handler」の実装は一切見つからず未実装。実際のモデル出し分けは hooks 内 3 層カスケードではなく、`.claude/agents/*.md` frontmatter の `model:` 個別指定 (12 agents 実測済 / module 6 参照) という別アーキテクチャで実現。決定と実装が乖離しつつ ADR は Proposed → Accepted 審議も Superseded 記録もなし。
- **推奨修正方針**: (a) ADR-0001 を Superseded とし、新規 ADR or 既存 ADR-0007/0009 に実装済モデル出し分け方針明記 or (b) ADR-0001 を Accepted へ正式遷移 + 「第2層は不採用 (subagent 個別指定で代替)」を改訂履歴に追記。**W-R3 S4 (docs/adr 整合修正)** で消化。

#### R1-048: ADR-0008 が ADR-0004 (security-commands.md 決定元) を全面書き換えしつつ Supersede 明記なし (traceability gap)
- **severity**: Warning
- **responsibility_tag**: `superseded-not-noted`
- **attribution**: `self`
- **status**: `open`
- **opened_at**: 2026-07-06
- **evidence_file**: `docs/adr/0008-approval-gate-redesign.md`, `docs/adr/0004-bash-read-commands-allow-list.md`
- **evidence_line**: 0008 L10 (関連 ADR: 0005/0006/0007 のみ), L185 (Phase A-6 `security-commands.md` 書き換え記述) / 0004 全文 (34 行 / 0008 前方参照なし)
- **evidence_summary**: ADR-0004 (2026-03-12 Accepted) = `security-commands.md` の Read-Only コマンド無制限 allow 決定。ADR-0008 (2026-06-30 Accepted) Phase A-6 = 同一ファイル `security-commands.md` を反面教師制約 D1/D4 に基づき書き換え。しかし ADR-0008「関連 ADR」欄には 0005/0006/0007 のみで 0004 なし。実ファイル (`security-commands.md` L34) 確認で ADR-0004 決定内容 (`cat`/`grep` 等の無制限 allow) は結果的に維持されているため実害なしだが、後続読者が「ADR-0004 は ADR-0008 でどう扱われたか」を辿る手段が ADR 間参照になく追跡性欠落。
- **推奨修正方針**: ADR-0008「関連 ADR」欄に ADR-0004 追加 + 軸5節に「Phase A-6 は ADR-0004 決定内容を継承しつつ反面教師制約で再文書化」等の 1 文追記。**W-R3 S4** で消化。

#### R1-049: ADR-0003「結果」節の実装パス `.claude/commands/full-review.md` が現行 `.claude/skills/full-review/SKILL.md` と drift
- **severity**: Warning
- **responsibility_tag**: `spec-drift`
- **attribution**: `self`
- **status**: `open`
- **opened_at**: 2026-07-06
- **evidence_file**: `docs/adr/0003-context7-vs-webfetch.md`
- **evidence_line**: 56
- **evidence_summary**: 「`.claude/commands/full-review.md` — Phase 0.5 として context7 検出 + 警告ロジック追加済」記述だが、実測 (`ls .claude/commands/`) で当該ディレクトリ自体不在。実体は `.claude/skills/full-review/SKILL.md` に「Step 2: context7 MCP 検出」として存在 (内容自体はロジック的に整合 / grep 確認済)。commands→skills 全プロジェクト移行に ADR-0003 参照パスが追随せず。決定内容 (B 案: context7 優先 + WebFetch フォールバック) は正しく維持されているため実装破綻なし → Warning (Critical でない)。
- **推奨修正方針**: ADR-0003 L56 参照パスを `.claude/skills/full-review/SKILL.md` (Step 2) に更新。**W-R3 S4** で他 ADR の同種 stale path と一括棚卸し。

#### R1-I37: ADR-0006 / ADR-0007 に「Wave C」表記が terminology.md 適用後に残存 (R1-I22 と同型 legacy 引き継ぎ)
- **severity**: Info (subagent 生 Warning → L1 監督で降格 / R1-I22 module 7 で同型を既に Info 起票済 = 一貫性)
- **evidence_file**: `docs/adr/0006-loop-engineering-vocabulary-and-lam-alignment.md`, `docs/adr/0007-magi-v2-gabriel-integration.md`
- **evidence_line**: 0006 L81, L92-94 / 0007 L244, L249
- **evidence_summary**: terminology.md §2 (2026-06-20 適用開始) は「Wave 1a 等のアルファベット混在禁止」。0006 L81「Wave C / 2026-07-05」、0007 L244「Wave C / 骨子②PLANNING」等が適用開始後の新規記述だが magi-v2-gabriel の Wave C 命名 (spec 側 legacy) を引き継いだ形。R1-I22 (`hga-summoning.md`) と同一パターン。terminology.md §5 経過措置により Info 起票許容範囲。
- **推奨修正方針**: 次回該当 ADR 編集時に「Wave C」→ 正式 Milestone/Wave 番号 or 作業名に置換。**W-R3 で R1-I22 と一括対応** 推奨。

#### R1-I38: ADR-0005 の FR-9.1 → FR-4.1a 自己訂正注記 = drift 解消好例 (positive observation)
- **severity**: Info
- **evidence_file**: `docs/adr/0005-thin-harness-autonomous-governance.md`
- **evidence_line**: 238-243
- **evidence_summary**: L238-243「注記: Accepted 後の整合修正 (2026-05-30)」で FR 番号更新を自己完結的に実施済。ADR-0007 L231 が ADR-0005 引用時は「Reflection 追補」内容のみ参照し FR 番号自体には触れず → 二次的 drift リスクなし。drift 解消好例の記録。

#### R1-I39: ADR-0009 コスト実測 vs `hga-summoning.md` day-1 実測記述の整合 (positive observation)
- **severity**: Info
- **evidence_summary**: ADR-0009 day-1 実測 ($1.84〜$12.66) + ADR-0010 (2026-07-04) の HGA #4 実施記録が時系列上 ADR-0009 推奨枠内に収まり、`hga-summoning.md` day-1 実測チェックリスト (#1-#5) とも整合 (module 7 で drift 未検出)。

#### R1-I40: ADR-0010 I-6 gabriel 配布経路と ADR-0007 実装スコープの整合 (positive observation)
- **severity**: Info
- **evidence_summary**: ADR-0010 I-6「gabriel 配布時に agents/ 追加 + version bump」は ADR-0007 (gabriel 2026-07-02 Accepted / プロジェクトローカル実装) と時系列整合。「本筋プロジェクトローカル実装先行 → 整備済 channel で一度だけ配布」の 2026-07-03 PM 決定とも矛盾なし。ADR-0010 最終行 TODO 「gabriel 配布時: lam-harness agents/ 追加」未完了は ADR 明示 TODO で drift ではない。

#### R1-I41: ADR-0002 Stop hook 実装ファイル名の完全一致 (positive observation)
- **severity**: Info
- **evidence_file**: `docs/adr/0002-stop-hook-implementation.md`
- **evidence_line**: 39-40
- **evidence_summary**: L39「スクリプト: `.claude/hooks/lam-stop-hook.py`」「状態ファイル: `.claude/lam-loop-state.json`」記述と実ファイル (`ls .claude/hooks/` で `lam-stop-hook.py` 実在) が完全一致。ADR ステータス整合の良好事例 (R1-047 との対比材料)。

#### R1-I42: ADR-0001〜0004 の簡易ヘッダ形式 vs ADR-0005 以降のメタ情報表形式で不統一 (テンプレート進化過程)
- **severity**: Info
- **evidence_file**: `docs/adr/0004-bash-read-commands-allow-list.md`
- **evidence_summary**: 他 9 件は「メタ情報」表 (ステータス/日付/意思決定者/関連 ADR/関連仕様) 保持だが、ADR-0001〜0004 (初期 4 件) は簡易ヘッダのみ。ADR テンプレート自体の進化過程と推測、内容の正誤には影響せず。過去記録のフォーマット差は許容 (adr-template skill 現行版が新規 ADR 適用されていれば十分)。

### module 11: `CLAUDE.md` + `CHEATSHEET.md`

**監査完了**: 2026-07-06 (W-R1 S4 T3 / L1 直監査)
**集計**: Critical 0 / Warning 2 / Info 3
**特記**: CLAUDE.md 単体は憲法として整合。CHEATSHEET.md 側で複数の spec drift 発見 (Reflection→gabriel 未反映複数箇所 + Rules 表 4/11 files 欠落)。

#### R1-050: CHEATSHEET.md の「Reflection」記述複数箇所が ADR-0007 gabriel 置換 (2026-07-02 Accepted) を反映せず
- **severity**: Warning
- **responsibility_tag**: `spec-drift`
- **attribution**: `self`
- **status**: `open`
- **opened_at**: 2026-07-06
- **evidence_file**: `CHEATSHEET.md`
- **evidence_line**: 138 (skill 表 "MAGI System + Reflection"), 183 (SSOT 表 06_DECISION_MAKING 説明 "AoT + Reflection"), 205-206 (magi クイックガイド Step 4 "Reflection: 結論の致命的見落としを検証（1回限り）")
- **evidence_summary**: ADR-0007 (Accepted 2026-07-02) で Reflection → gabriel 独立 subagent に構造的置換済。`.claude/rules/decision-making.md` L19 も注記済 (旧 Reflection は Wave C で gabriel に置換済)。しかし CHEATSHEET.md 3 箇所で旧 Reflection 記述残存 = ユーザー参照ドキュメントとしての最重要 UI 面で spec drift。
- **推奨修正方針**: 3 箇所全て「gabriel adversarial probe」に置換 + Step 4 の説明を「gabriel 独立 subagent が 6-fields JSON schema で adversarial verification」に更新。**W-R3 S4 (ルート統治文書一貫性修正)** で消化 (PM 級)。

#### R1-051: CHEATSHEET.md Rules ファイル一覧が 4/11 files 欠落 (36% 未列挙) + auto-generated 3 files 全欠落
- **severity**: Warning
- **responsibility_tag**: `reference-integrity`
- **attribution**: `self`
- **status**: `open`
- **opened_at**: 2026-07-06
- **evidence_file**: `CHEATSHEET.md`
- **evidence_line**: 38-49
- **evidence_summary**: 現在 7 files 列挙 (core-identity / phase-rules / security-commands / decision-making / permission-levels / upstream-first / test-result-output)。**欠落 4 files**: `code-quality-guideline.md` (2026-06-08 追加) / `planning-quality-guideline.md` (2026-06-19) / `terminology.md` (2026-06-20) / `hga-summoning.md` (2026-07-02)。**auto-generated 3 files 全欠落**: README.md / rule-001.md / trust-model.md。実測 (`ls .claude/rules/` で 11 files + auto-generated/ 3 files)。
- **推奨修正方針**: 表を全 11 rules + 3 auto-generated に更新 (or 「代表的な rules ファイル (抜粋)」と明記して抜粋であることを示す)。**W-R3 S4** で消化 (PM 級)。

#### R1-I43: CHEATSHEET.md の `**v4.0.0 新規**` タグが stale (現行 v4.6+)
- **severity**: Info
- **evidence_file**: `CHEATSHEET.md`
- **evidence_line**: 46, 50, 57
- **evidence_summary**: `permission-levels.md **v4.0.0 新規**` タグは追加時のバージョン記録として有価値だが、現行 v4.6+ で「新規」ではない。次回 hygiene で削除 or 「v4.0.0 で導入」表現に変更検討。実害なし。

#### R1-I44: CHEATSHEET.md スキル表 (L134-145) が 7 skill のみ列挙 (実 23 skill / 補助テーブル分割意図あり)
- **severity**: Info
- **evidence_file**: `CHEATSHEET.md`
- **evidence_line**: 134-145
- **evidence_summary**: スキル表に列挙されるのは 7 skill (magi / clarify / lam-orchestrate / skill-creator / adr-template / spec-template / ui-design-guide)。実際は 23 skill 存在 (module 3 監査済)。ただし他 skill (auditing / build-dashboard / building / full-review / goal-driven / init-harness 等) は「ワークフローコマンド」表 (L156-171) と「補助コマンド」表 (L166-171) に分散配置されている意図あり。網羅性完全化は Bikeshedding リスクあり Info 止め。

#### R1-I45: CLAUDE.md L88 の 委譲閾値ルール表 と user feedback memory (「並列実行ガンガン」) の緊張関係 (memory 側補足済 / 実害なし)
- **severity**: Info
- **evidence_file**: `CLAUDE.md`
- **evidence_line**: 88-100 (委譲の閾値ルール表)
- **evidence_summary**: 表に「並列子 (2 名超) を分配する必要」→ L1.5 司令塔経路、「並列子 2 名以下」→ L1 直経路の記述あり。user feedback memory (2026-06-27 「並列実行ガンガン」明示指示) と一見緊張関係だが、memory 側で「委譲先選定基準であり L1 直作業を逐次化する根拠ではない / L1 直独立タスクは 3-4 並列まで遠慮なく」と補足済で解消可能。実害なし / 記録のみ。

---

## 5. 変更履歴

| 日付 | 変更者 | 内容 |
|:-----|:-------|:-----|
| 2026-07-06 | L1 (Opus 4.7) | 初版起票 (W-R1 S2 T1 / 骨組作成 / issue 未起票) |
| 2026-07-06 | L1 (Opus 4.7) | W-R1 S2 module 1-4 監査完了 (issue R1-001..R1-031 / R1-I01..R1-I15 起票) |
| 2026-07-06 | L1 (Opus 4.7) | W-R1 S3 module 5-8 監査完了 (issue R1-032..R1-043 + R1-I16..R1-I29 起票 / 累計 C=1 W=22 I=29 / NFR-3 閾値超過確定 → S5-T4 条件分岐 sub-task 起票必須) |
| 2026-07-06 | L1 (Opus 4.7) | **前倒し消化 2 件** (Wave 分離規律の例外 / ユーザー判断 = 実運用リスク優先): R1-042 (gabriel 6 fields drift / decision-making.md 更新 / PM 級) / R1-032 (pre-tool-use.py shell metachar / TDD Red-Green / 10 テスト新規 PASS / 534+14 SKIP 維持) → status open→closed |
| 2026-07-06 | L1 (Opus 4.7) | W-R1 S4 module 9-11 監査完了 + ヒートマップ 33 セル完成 (issue R1-046..R1-051 + R1-I33..R1-I45 起票 / 全 11 module 累計 C=1 W=28 I=43 / open C=1 W=26 / NFR-3 閾値 2.9 倍超過確定) |

---

## 6. 参照

- [requirements.md](../specs/large-scale-review/requirements.md) FR-1 / FR-2 / FR-5 / NFR-1 (R-G6/G7/G8) / NFR-3
- [design.md](../specs/large-scale-review/design.md) §3.1 (tracker) / §3.0 (data flow) / §14 (権限等級)
- [tasks.md](../specs/large-scale-review/tasks.md) W-R1 全 Stage
- [green-state-baseline.md](./r-1-green-state-baseline-2026-07-06.md) (G1-G5 + R-G6/G7/G8 baseline)
- [code-quality-guideline.md](../../.claude/rules/code-quality-guideline.md) (Critical/Warning/Info 判断基準)
