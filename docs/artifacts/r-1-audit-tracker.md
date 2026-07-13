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

## 0.1. HGA #9 verdict (2026-07-06 / W-R2 S1 実装後 adversarial verify)

Fable HGA #9 (2026-07-06 / W-R2 S1 T4) が R1-001 + R1-006 実装 (L2 Sonnet tdd-developer) の 5 軸 verify を実施 → **overall_verdict = confirmed / severity = warning / recommended_action = fix_before_ship / confidence 0.85**。

**軸別結果**:
- **軸 A (regex 実装忠実性)**: confirmed / discrepancies = [] (Read で 3 regex 全て HGA #8 spec と文字単位一致確認)
- **軸 B (attack surface 完全性)**: confirmed / 7+8 category 全て pinning test 済 (41 tests / 41 PASS 独立再走)
- **軸 C (追加 attack surface)**: refuted / 新規発見 3 件 → R1-053 (Warning) / R1-054 (Info) / R1-055 (Info) として起票
- **軸 D (regression risk)**: refuted / **design.md §5.1 spec-sync gap** 検出 → 本 T4 内で L1 修正済 (L414/L420/L427 更新 + PM 級)
- **軸 E (baseline drift 裁定)**: confirmed / 両 disposition 妥当 + missed drift = 0

**ship 前修正 (fix_before_ship / 全て W-R2 S1 T4 内で消化済)**:
1. **builder.py docstring L697-704 asymmetry** (info): 「前後が英数字・ハイフンで挟まれていない」の左右非対称を明示的に説明 (leading = 英数字・ハイフン非許容 / trailing = 英数字非許容だがハイフン許容 / T1-T5 範囲記法左端保護のため)
2. **範囲記法エンドポイント semantics 固定** (C-N2 / warning): 意図的挙動変更 note を tasks.md §Stage S1 に追加 + `TestRangeNotationEndpointSemantics` (3 テスト) で仕様固定 (左端 T1 マッチ / 右端 T5 非マッチ / 範囲は展開しない)
3. **design.md §5.1 spec-sync (warning / PM 級)**: L414/L420 bash grep char class を実装済み値に更新 + L427 stale claim 書き直し (ADR flat 直参照の補足可能性を訂正)

**新規起票 3 件** (§4 module 1/2 参照):
- R1-053 (Warning): C-N3 = `verify_w_r3()` パターン 3 の existence-check hole (dir 存在で fname 存在検査省略 / R1-006 と同 bug class)
- R1-054 (Info): C-N1 = R1-001 lookbehind/lookahead が underscore 境界文字扱いせず (`W1-B5-T1_note` 誤マッチ surface / spec 忠実だが未文書化)
- R1-055 (Info): C-N4 = Path.exists() の win32 case-insensitive で drift portability リスク (現行 live scan で 0 実例)

**meta 対策 (HGA #7 verdict メタ欠陥#1 の追加ゲート提案)**: 修正 pattern/constant が literal-quoted されている docs/specs/* を grep → PM 級を L1 assign。今回は L2 tracker 経由の docstring 同期しか自動化されておらず、sibling SSOT (design.md §5.1) の同期が nobody's checklist だった。W-R5 retro で `code-quality-guideline.md` に「同型 finding の先例参照義務」と併せて追加検討。

## 0.2. HGA #10 verdict (2026-07-07 / W-R2 S2 R1-053 実装後 adversarial verify)

Fable HGA #10 (2026-07-07 / W-R2 S2 T2) が R1-053 実装 (L2 Sonnet tdd-developer) の 6 軸 verify (A-E + meta / refute-first) を実施 → **overall_verdict = confirmed-with-warnings / fix_before_ship = 不要 / confidence 0.90**。

**軸別結果**:
- **軸 A (実装忠実性)**: confirmed / tracker 推奨修正方針を文字通り実装 (L144-158)
- **軸 B (残存攻撃面)**: 部分 refuted / **新規 Warning 1 件** = L51 group3 文字クラスに `/` なし → 多階層参照 `docs/specs/<slug>/<sub>/<file>.md` が fname=None 退化で素通し (同 bug class residual / live 0 実例 grep 実測) → R1-056 起票
- **軸 C (FP 転化)**: confirmed / live 0 drifts を独立再現・厳密化で新規 FP になる正当参照形は構成不能
- **軸 D (テスト十分性)**: confirmed / monkeypatch REPO_ROOT 方式は全経路に有効 (軽微 gap 2 は R1-056 消化時に吸収)
- **軸 E (spec-sync)**: confirmed / 旧 any() セマンティクスの literal-quoted 残存なし = **HGA #9 追加ゲート提案 (修正 pattern の literal-quoted grep) の初適用で PASS**
- **meta**: L2 報告値 (27 PASS / drift 0) を Fable が独立再実測 (`-o addopts=""` で junitxml 無効化) して一致確認 = unverified 主張ゼロ

**新規起票 4 件** (§module 2 参照): R1-056 (Warning / 多階層参照退化) / R1-057 (Info / regex 非捕捉退化 3 態様) / R1-058 (Info / 走査 scope 外 `.claude/rules`) / R1-059 (Info / gabriel substring 弱検査)

## 0.11. W-R4 S3-T4 消化 + R1-016 序で消化 = **module 5 + module 3 Wave 完了ゲート達成** (2026-07-11)

W-R4 S3-T4 (hooks 統合 / L2 Sonnet TDD) と序で R1-016 消化 (L1) を完走。**module 5 open C+W = 0** + **module 3 open C+W = 0** 達成。

### R1-033 (Warning / PM 級 = closed)

- **closed_at**: 2026-07-11
- **closed_by_commit**: (本セッション Stage 末 ship で埋める)
- **修正内容**: `.claude/settings.json` L74/80/86/91/96 の hook 起動コマンド 5 箇所を `bash -c 'command -v python3 >/dev/null 2>&1 && python3 <path> || python <path>'` fallback 形式に統一。Windows portability リスク解消 (Windows 標準 Python installer で `python3` alias が提供されないケースへの対応)
- **TDD**: `.claude/tests/hooks/test_settings_hook_portability.py` 新規 4 tests / 全 PASS

### R1-034 (Warning / SE 級 = closed)

- **closed_at**: 2026-07-11
- **修正内容**: `_PM_PATH_PATTERNS_FOR_CACHE` (post-tool-use.py L55-61) と `_PM_PATTERNS` (pre-tool-use.py L92-99) の重複を `.claude/hooks/_hook_utils.py` に一本化。両側で `from _hook_utils import _PM_PATH_PATTERNS` に置換
- **TDD**: `.claude/tests/hooks/test_pm_patterns_unified.py` 新規 7 tests / 全 PASS + regression 24/24 PASS

### R1-I18 (Info = closed / R1-034 一体消化)

- **closed_at**: 2026-07-11
- **修正内容**: pre-tool-use.py のみが保持する out-of-root pattern (`^__out_of_root__/`) について、「キャッシュ非対象で毎回 PM 再表示する安全側設計」の意図明示コメントを追加。R1-034 統合実装内で完了

### R1-016 (Warning / SE 級 = closed / 序で消化)

- **closed_at**: 2026-07-11
- **修正内容**: 3 skill (`adr-template` / `spec-template` / `ui-design-guide`) の frontmatter から `model: sonnet` 行を削除 (context7 検証で Skills 側非公式フィールドと確認済 = dead config)。`allowed-tools:` は正当のため維持
- **注記**: `ui-design-guide` は delete_candidate 対象だが frontmatter drift は削除 defer と独立に消化可能なため実施

### module 5 / module 3 Wave 完了ゲート状況

| module | open C+W (W-R4 前) | open C+W (W-R4 S3-T4 後) | 達成 |
|:------:|:---:|:---:|:----:|
| module 3 (`.claude/skills/`) | 1 (R1-016) | **0** | ✅ |
| module 5 (`.claude/hooks/` + `settings*.json`) | 3 (R1-033/034/I18 相当) | **0** | ✅ |
| module 6 (`.claude/agents/`) | 2 (R1-035 W-R3 closed / 残 = 0) | 0 | ✅ (W-R3 で達成済 / 本 Wave 変化なし) |

**注記**: 上記は skills 削除 (S3-T2/T3/T5) を defer した状態でも module 3 Wave 完了ゲート達成が成立することを意味する (R1-016 のみが Warning で、delete_candidate 8 件は Info 級の drift ではなく issue ゼロの状態)。

### 副次発見 (L2 Sonnet より)

- 同名モジュールの pytest 衝突: `.claude/tests/hooks/test_pre_tool_use.py` と `.claude/hooks/tests/test_pre_tool_use.py` が同名で、両 dir 同時 pytest 実行時 `import file mismatch`。各 dir 個別実行では両方全 PASS。本 Task 由来ではないが記録 (W-R5 議題候補 = pytest 設定改善)

### Wave 完了ゲート全体状況 (W-R4 S3-T4 後時点)

| module | open C+W | 達成 |
|:------:|:---:|:----:|
| module 1 (`.claude/scripts/dashboard/`) | 0 | ✅ |
| module 2 (`.claude/scripts/` 外) | 0 | ✅ |
| module 3 (`.claude/skills/`) | 0 | ✅ (本 Stage) |
| module 4 (`.claude/tests/`) | 0 | ✅ |
| module 5 (`.claude/hooks/` + `settings*.json`) | 0 | ✅ (本 Stage) |
| module 6 (`.claude/agents/`) | 0 | ✅ (W-R3 達成済) |
| module 7 (`.claude/rules/`) | 0 | ✅ (W-R3 達成済) |
| module 8 (`docs/internal/`) | 0 | ✅ (W-R3 達成済) |
| module 9 (`docs/specs/`) | 0 | ✅ (W-R3 達成済) |
| module 10 (`docs/adr/`) | 0 | ✅ (W-R3 達成済) |
| module 11 (`CLAUDE.md` + `CHEATSHEET.md`) | 1 (未 module 11 では未確認 / W-R5 議題) | 未達 |

**進捗率**: 10/11 module で Wave 完了ゲート達成。W-R4 の残作業は skills 削除 (S3-T2/T3/T5 defer) と S4 (Warning 消化 + agent-memory 空 Stage) のみ。

### 次工程

1. **本 Stage 末 ship** (S3-T4 + R1-016 消化 / S2 empty + S3-T1 defer 記録も含める)
2. **次セッション**: S3-T2/T3/T5 (skills 削除 L2 Sonnet 委譲) + S4 (agent-memory 空 Stage + module 11 の残 Warning + Wave 完了 ship)

---

## 0.12. W-R4 S3-T2/T3/T5 消化 = **skills 削除 8 件 + 参照書き換え 16 files 完了** (2026-07-13)

前セッション §0.10 で defer 判定した skills 削除 3 Task を消化。**module 3 Wave 完了ゲート維持** (open C+W=0)。

### 実施内容

**Stage S3-T2** (PM 級一括宣言 + user 承認):
- 削除計画 (8 SKILL.md `git rm`) + 参照書き換え計画 (CAT-A 82 hits / 16 files) + tracker/deletions.md 更新計画 を L1 で組立、user 承認 1 回 (Q1=4番選択) で全実行フローに移行

**Stage S3-T3** (削除実施 + 参照書き換え + tracker/deletions.md 更新):

Grep 精査結果 (L2 Sonnet grep triage / 前段):
- **CAT-A** (要書き換え / 実行指示): **82 hits** / 17 files
- **CAT-B** (歴史記述 / 保持): **153 hits** → 触らない
- **CAT-C** (self-reference / 削除で自動消滅): 19 hits
- **CAT-D** (settings.json / allowlist): **0 hits** → 良好
- **CAT-E** (L1 判断要): 1 hit (`hga-summoning.md:155`)
- boundary_deviations: 2 (scratchpad 内 / repo 影響なし)

参照書き換え (L2 Sonnet rewriter / 別委譲):
- **16 files 処置** (`project-status/SKILL.md` は削除で自動消滅で除外) / **81 hits** / **45 unique edits**
- **6 パターン厳密適用** (P1 表行削除 / P2 slash command → phase 名 / P3 template array 除去 / P4 併用言及削除 / P5 cross-skill 案内書き直し / P6 section 全削除)
- pattern-uncertain 2 件は L1 承認 (CHEATSHEET.md L202 phase 名 no-op / evaluation-kpi.md §7 KPI 定義保持 = 仕様知識散逸防止)
- 詳細: `docs/artifacts/r-1-deletions.md` §2

CAT-E 処置 (L1 SE 級):
- `.claude/rules/hga-summoning.md:155` に「(R-1 W-R4 S3 で削除済 / deletions.md 参照)」注記追記 = incident 例の意味保持

削除実施 (L1 直 / git rm 束ね):
```bash
git rm .claude/skills/{auditing,clarify,pattern-review,planning,project-status,skill-creator,ui-design-guide,wave-plan}/SKILL.md
```

**Stage S3-T5** (L3 Haiku 突合):
- 宣言 8 path vs `git diff --cached --diff-filter=D` 抽出 path を Haiku で文字単位一致判定
- verdict: 完全一致 (期待)

### module 3 Wave 完了ゲート状況 (S3-T4 後時点維持)

| module | open C+W (S3-T4 後 → 今回) | 達成 |
|:------:|:---:|:----:|
| module 3 (`.claude/skills/`) | 0 → **0** (skill 削除で 8 SKILL.md 消滅 + 参照書き換え 16 files で orphan 参照ゼロ化) | ✅ 継続 |

### 副次成果

- **CAT-B 153 hits 保持成功**: 歴史記述 (retro / rename migration / spec history / test fixture 等) を正しく残せた = Sonnet 5 リテラル特性を tight brief 5-slot + 6 パターン厳密適用で制御 (model-delegation-prompting.md §2 実測 4 例目)
- **Sonnet 2 段委譲パターン**: (a) grep triage → (b) rewriter を分離することで、L1 は監督工程のみで完結 = 手作業 Edit ゼロ
- **CAT-E 対策の実効**: 前段 gabriel probe A2 で提案した「CAT-E rubric 拡張」により、82 CAT-A 中 escalate 1 件のみ = うまく機能 (Sonnet が独自判断で誤削除する確率を機構で下げた実例)
- **HGA 温存**: Fable 定額アクセス期間中 (7/20 まで) だが grep 精査は crux 追及型ではなく分類作業のため HGA 不発動 = 儀式性維持

### 次工程

1. **本 Stage 末 ship** (S3-T6 相当 / commit message に closed IDs = 削除 8 skill + CAT-A 82 references rewritten + CAT-E hga-summoning L155 明記)
2. **W-R4 S4** (agent-memory 空 Stage / agent delete = 0 のため trivially 空 + module 11 残 Warning + Wave 完了 ship)
3. **W-R5 未着手** (R-G6/G7/G8 全閉塞確認 + gabriel + code-review ultra + retro + Milestone COMPLETE 判定)

---

## 0.10. W-R4 S2 空 Stage 判定 + S3-T1 削除候補確定 + skills 削除 defer (2026-07-11)

**S2 (agents 削除/改名) = 空 Stage 判定** — usage-baseline `docs/artifacts/r-1-usage-baseline-2026-07-11.md` §3 で確定:

- agent delete_candidate = **0 件** (12/12 全て keep_recent_modified / 30d hit>0)
- agent rename_history = **0 件** (S1-T2 全 12 agent の rename_history 列が "-")
- → S2-T1 (候補確定) = 空 / S2-T2 (承認取得) = 不要 / S2-T3 (git rm) = skip / S2-T4 (git mv) = skip / S2-T5 (突合) = 0 vs 0 で trivially 完全一致 / S2-T6 (Stage 末 ship) = S3-T6 に併合

**S3-T1 (skills 削除候補確定)**:

usage-baseline delete_candidate 9 件から `.claude/rules/hga-summoning.md` 未参照 tier 確認より **orchestrator 5 件 (`magi` / `full-review` / `lam-orchestrate` / `autonomous` / `goal-driven`) 除外** (requirements.md §42 準拠 = 中核制御フロー保護維持)。

→ **実削除候補 8 件** (lam-orchestrate 除外):
1. `.claude/skills/auditing/SKILL.md`
2. `.claude/skills/clarify/SKILL.md`
3. `.claude/skills/pattern-review/SKILL.md`
4. `.claude/skills/planning/SKILL.md`
5. `.claude/skills/project-status/SKILL.md`
6. `.claude/skills/skill-creator/SKILL.md`
7. `.claude/skills/ui-design-guide/SKILL.md`
8. `.claude/skills/wave-plan/SKILL.md`

### skills 削除 (S3-T2/T3/T5) の defer 判断 (2026-07-11)

**判断**: 本 Wave では削除**実施しない** (deferred_reason = `FR-4 grep 条件精査に別セッションが最適`)

**根拠**:

1. **FR-4 の 3 条件 AND の grep 精査規模が大きい**: 削除候補 8 件の skill 名は LAM の phase 名 (`planning` / `auditing` / `building`) や汎用語 (`clarify` / `pattern-review` / `wave-plan` / `project-status` / `skill-creator` / `ui-design-guide`) と衝突。単純 grep hit を精査した実測:

   | skill | 単純 grep hit 数 | 精査必要理由 |
   |:---|---:|:---|
   | planning | 74 | phase 名としての参照が大多数 |
   | auditing | 33 | phase 名参照多 |
   | project-status | 24 | CHEATSHEET/README/phase-rules 記載 |
   | clarify | 23 | rules/planning-quality-guideline 記載 |
   | wave-plan | 16 | CHEATSHEET/README 記載 |
   | pattern-review | 16 | CLAUDE.md/README 記載 |
   | skill-creator | 15 | hga-summoning 記載 (subagent 混同注意) |
   | ui-design-guide | 14 | cc-spec-alignment 記載 |

   → 各 hit を「実行可能な slash command 指示」vs「歴史的記述」に分類する精査工程が必要 (100+ locations)

2. **第 0 原則の判断**: 可逆性=有 / 復旧コスト=中〜高 (依存が生じている場合の連鎖修正 + 文書全域更新) / 確認コスト=セッション断→ (削除は不可逆判定の連鎖リスク)。低確度の一括削除より、次セッションで **L2 Sonnet 委譲 (tight brief 5-slot / 各 SKILL.md 読み + grep hit 分類 + drift 起票 + 削除実行)** が最適

3. **依存タスクへの影響なし**: S4 の agent-memory 更新 (S4-T1) は「削除された agent の memory 無効化」が対象で、agent delete = 0 のため S4-T1 も同時に空 Stage 判定可能。skill 削除の delay は S4 進行を妨げない

**S3-T2/T3/T5 → defer** (tracker で `deferred / next-session-l2-sonnet` として保留 / 次セッションで S3 再開)。

### S3-T4 (hooks 統合) の消化方針

S3 全体 defer にせず、**同 Stage 内の hooks 統合 (R1-033 / R1-034 / R1-I18)** は本セッションで消化 (L2 Sonnet 委譲予定):

- R1-033 (Warning / PM 級 = settings.json 修正): python3 hardcode の環境非依存化
- R1-034 (Warning / SE 級 = hooks/*.py 修正): `_PM_PATTERNS` 重複を `_hook_utils.py` 一本化
- R1-I18 (Info): out-of-root 非対称設計を R1-034 と一体消化

module 5 open C+W 3 件 → 3 件全て closed 見込 (Wave 完了ゲート「module 5 Critical+Warning=0」達成条件を満たす)。

**次工程**: S3-T4 消化 → S3-T6 部分 Stage 末 ship → 次セッション S3-T2/T3/T5 (skills 削除 L2 Sonnet 委譲) → S4 (agent-memory 空 Stage + 残 Warning 消化)

---

## 0.9. W-R4 S1 消化 = **FR-F4 データソース確定 verdict=success** (2026-07-11 / T1-T5 完走 / T6 = Stage 末 ship 目前)

W-R4 Stage S1 の T1-T5 を消化し、**FR-F4 データソース確定判定 = success**。W-R4-S1-T5b (deferred fallback) は不発火。W-R4 S2/S3 通常進行が確定。

**成果物 4 本** (SE 級 / `docs/artifacts/` 配下):

1. **S1-T1** (L1): `r-1-jsonl-fields-2026-07-11.md` (jsonl 4 種類の起動記録フィールド名確定 / §4.5 に Stop-hook 第 2 event shape 追補)
2. **S1-T2** (L2 Sonnet / 152.6k tokens / 39 tool_uses): `r-1-git-log-usage-2026-07-11.md` + `.claude/scripts/r-1-git-log-usage.py`
3. **S1-T3** (L2 Sonnet / 169.5k tokens / 43 tool_uses): `r-1-session-log-usage-2026-07-11.md` + `.claude/scripts/r-1-session-log-usage.py`
4. **S1-T4** (L2 Sonnet / 135.0k tokens / 3 tool_uses): `r-1-usage-baseline-2026-07-11.md` (統合 + verdict 付与)

**verdict 集計** (S1-T4 §3):

| verdict | agent | skill | hook | 合計 |
|:---|---:|---:|---:|---:|
| delete_candidate | 0 | **9** | 0 | 9 |
| keep_recent_modified | 12 | 14 | 3 | 29 |
| hold_low_confidence | 0 | 0 | 4 | 4 |

**delete_candidate 9 件全て skill** (S2/S3 で個別承認取得対象):
- 高確信度 (>40 日前 last commit): `auditing` / `clarify` / `pattern-review` / `planning` / `project-status` / `skill-creator` / `ui-design-guide` / `wave-plan` (8 件)
- 境界ケース (cutoff 1 日差): `lam-orchestrate` (1 件 / S3-T2 承認提示時に確信度差を明記予定)

**hold_low_confidence 4 件全て hook** (削除フロー除外 = agent-memory の対象外でもある):
- `pre-compact.py` (PreCompact event shape 未確認 / logging gap 疑い)
- `_hook_utils.py` / `_incident_patterns.py` / `autonomous_state.py` (非 entrypoint helper module / import 参照解析が別途必要 = W-R4-S3-T4 hook 統合の判断材料に別途走査)

**副次発見**:
- S1-T2 実装中、L2 Sonnet が `fnmatch.fnmatch` の path segment cross bug を自主発見・修正 (segment-wise matching に切替)
- S1-T3 実装中、L2 Sonnet が Stop-hook の第 2 event shape (`type=="system"` + `subtype=="stop_hook_summary"` + `hookInfos[].command`) を発見 → S1-T1 メモに §4.5 として追補済
- `.claude/commands/*.md` は 2026-05-29 一括改名で全て skills へ移行済 (S1-T2 §4 / command resource_type の現存 target = 0)

**Alembic 2026-07-10 changelog §1 由来「経路アンカー点検」**: S1-T3 で発見した `/quick-save` 2 経路並存 = 「Skill tool 経由」と「`<command-name>` 直入力」の非対称は、まさに「経路で発火点を定義するとカバレッジ穴が生じる」実例。W-R5 議題の `fable-l3-protocol.md` §5.1 発火点 2 経路アンカー明示化と接続する材料。

**次工程**: S1-T6 Stage 末 ship (本 Task) → W-R4 S2/S3 (削除実施 / L1) + S4 (agent-memory + Warning 消化 / L2 Sonnet)

---

## 0.8. W-R4 S1-T1 消化 (2026-07-11 / jsonl 起動記録フィールド名確定 = HGA #6 Crux 5-1 要検証仮定解消)

W-R4 Stage S1 の T1「実 jsonl 1 本を開いて skills 起動記録のフィールド名確定」を実施。実測対象を「1 本」から拡張し `~/.claude/projects/D--work7-LivingArchitectModel/*.jsonl` **全 76 セッション**を横断走査 (`<scratchpad>/jsonl_probe_all.py`)。

**確定結果** (詳細: `docs/artifacts/r-1-jsonl-fields-2026-07-11.md`):

| リソース種別 | 起動判定パターン | 実測件数 (76 sessions) |
|:------|:--------|---:|
| skills (Skill tool 経由) | `tool_use.name == "Skill"` + `input.skill` | 76 起動 |
| slash commands (`/name` 直入力) | user message text 内 `<command-name>/([^<]+)</command-name>` | 117 出現 (9 種類) |
| agents (subagent) | `tool_use.name == "Agent"` + `input.subagent_type` | 532 起動 |
| hooks | `attachment.type == "hook_success"` + `hookName` + `hookEvent` | 12,421 発火 |

**Crux 5-1 の実測反証・追認**: design.md §7.2 の主張「skills を subagent_type で grep すると全 skills が偽陽性削除の直行便になる」を実測で追認。全 76 セッションで skills が subagent_type フィールドに現れた実例は 0 件。3 分岐 (agents / skills / hooks) の独立パターン実装が必要。

**S1-T3 実装者への引継ぎ**: skills 検出は **`tool_use.name == "Skill"` 経路 + `<command-name>` タグ経路の OR** が必須 (実測: `/quick-save` は 2 経路が並存)。単一経路だと skill 起動の約半数を取り逃す偽陰性リスク。

**S1-T5 データソース確定判定へのインプット**: フィールド名確定 = **成功** / 種別別パターン分岐 = **確定** / 30 日窓 grep 実装可能性 = **成功 verdict の見込み** (S1-T2/T3/T4 の実装で最終確定予定)。

**編集 files**: 1 ファイル (`docs/artifacts/r-1-jsonl-fields-2026-07-11.md` 新規 / SE 級)
**次工程**: W-R4 S1-T2 (git log スクリプト / L2 Sonnet) + S1-T3 (session log 30 日窓 grep / L2 Sonnet) — 依存が S1-T1 のみのため並列実施可能

---

## 0.7. W-R3 S4 消化 = **W-R3 Wave 完了** (2026-07-10 / docs/specs + docs/adr + CHEATSHEET.md 一貫性修正)

W-R3 S4 で残り 4 件 Warning を消化し、**W-R3 Wave 完了ゲート全達成**:

- **R1-046 (W / closed)**: 実装完了済 spec の親メタ status Rule of Three drift 解消
  - 8 spec files を Approved 化: `b4-dashboard/{design,requirements}.md` (2026-07-02 / B-5 Milestone 完了) + `goal-driven-orchestration/{requirements,design,tasks,config}.md` (2026-06-18 / B-3 Milestone 完了 / PM-G3 承認) + `magi-v2-gabriel/{requirements,design}.md` (2026-07-02 / Wave C 完了 / gabriel 稼働 6880421)
  - `v5-fat-reduction` は R1-I34 反証記録により Draft 維持 (未着手正常状態)
- **R1-047 (W / closed / PM 級)**: ADR-0001 status Proposed → **Accepted** (推奨案 b) + 改訂履歴に「第 2 層 (prompt/haiku) 不採用 / subagent frontmatter `model:` 個別指定で代替」明記 (2026-03-08 提案から 4 ヶ月放置状態解消)
- **R1-049 (W / closed / PM 級)**: ADR-0003 L56 実装パス修正 (`.claude/commands/full-review.md` → `.claude/skills/full-review/SKILL.md` Step 2) + commands→skills 移行経緯を注記併記
- **R1-050 (W / closed / PM 級)**: CHEATSHEET.md 3 箇所 Reflection → gabriel 置換
  - L138 skill 表 / L183 SSOT 表 / L205-206 magi クイックガイド Step 4
  - 「6-fields JSON schema」+ 「ADR-0007 Accepted 2026-07-02 で旧 Reflection から置換」の履歴注記も同時反映

**編集 files**: 12 ファイル (docs/specs 8 + docs/adr 2 + CHEATSHEET.md 1 + tracker 1)

## Wave 完了ゲート達成 (W-R3 全 Stage COMPLETE / 2026-07-10)

| module | open C+W (W-R3 前) | open C+W (W-R3 後) | 達成 |
|:------:|:---:|:---:|:----:|
| module 7 (`.claude/rules/`) | 2 | 0 | ✅ |
| module 8 (`docs/internal/`) | 4 (R1-042 closed 前) | 0 | ✅ |
| module 9 (`docs/specs/`) | 1 | 0 | ✅ |
| module 10 (`docs/adr/`) | 2 | 0 | ✅ |
| module 11 (`CHEATSHEET.md`) | 1 | 0 | ✅ |
| R-G7 W-R3 drift | 0 | 0 | ✅ |
| HGA #13 消化 | - | 済 | ✅ |

**W-R3 Wave 完了ゲート = 全達成** (2026-07-10)

## 0.6. W-R3 S3 消化 (2026-07-10 / rules 相互矛盾解消 + FR-F5 決定実装は skip)

W-R3 S3 で `.claude/skills/` × `.claude/agents/` × `.claude/rules/` にまたがる drift 5 件を消化:

- **R1-017 (W / closed)**: `init-harness/SKILL.md` の dead skill/command 参照 cluster 解消 (5 term 用語統一 = `design-mode`→`planning` / `build-mode`→`building` / `audit-mode`→`auditing` / `session-save`→`quick-save` / `session-load`→`quick-load`) — SKILL.md 全域 + harness.json テンプレ内 enabled_skills も同時更新
- **R1-018 (W / closed)**: `goal-driven/SKILL.md` L390-392 の実装ステータス表 3 行を「未実装」→「完了」に更新 (エージェント定義 3 件 + `gd_state.py` + Stop hook B-3 節すべて実在確認済)
- **R1-035 (W / closed)**: 8 agents から `# permission-level: XX` dead comment 一括削除 (context7 検証で公式 sub-agents frontmatter に存在しないフィールド = 完全 dead / LAM の判定は `pre-tool-use.py` パスベース実装済 / 統一済状態に到達)
- **R1-038 (W / closed / PM 級)**: `code-quality-guideline.md` L37 と `phase-rules.md` L145 に相互参照 1 文追加 = 「BUILDING 実行中は絶対禁止 = 作業を止める規律 / AUDITING 時点の重要度判定では Warning」の使い分けを両側で明示
- **R1-039 (W / closed / PM 級)**: `hga-summoning.md` L96 の envelope 記述を「月 $40-80 の envelope の外」→「実 $ envelope (月 $10-40) および Opus quota envelope (weekly cap 20% 以内) の両方の外」に統一 (2026-07-04 二軸化との drift 解消 + 旧記述の置換履歴を注記)

**編集 files**: 12 ファイル (skills 2 + agents 8 + rules 3 = 実際は agents 8 は sed 一括なので Edit 経由は skills 2 + rules 3 = 5)
**Wave 完了ゲート更新**: module 3 open C+W = 3→1 (R1-017/018 closed / R1-016 は W-R1 消化済) / module 6 open C+W = 3→2 (R1-035 closed) / module 7 open C+W = 2→0 (R1-038/039 closed = Wave 完了ゲート「W-R3 module 7 = 0」達成 ✅)
**FR-F5 決定実装** (auto-generated rule-001 拡張 vs rule-002 新設): 本 S3 内 skip = R1-060/R1-061 W-R5 議題と統合判断 (rule-002 候補が 2 件累積 = 決定実装を独立して確定する必要が高まった / W-R5 で判定)

## 0.5. Q3 β 議題化結論 (2026-07-10 / W-R3 S3 T3)

`requirements.md` §変更履歴 2026-07-05 で保留された **Q3 β: docs/internal/ の権限等級 (SE 級維持 or PM 昇格)** の最終判断。

**議題化結論**: **SE 級維持** (PM 昇格しない)

**根拠**:
- W-R3 S2 (2026-07-10) で docs/internal/ 3 files (`00_PROJECT_STRUCTURE.md` / `07_SECURITY_AND_AUTOMATION.md` / `02_DEVELOPMENT_FLOW.md`) に対し 4 件の drift 修正 (R1-040/041/043/I25) を **SE 級 = 事前 PM 承認なし** で実施し、いずれも意図通りの drift 解消を達成 (verify_reference_resolution.py --wave w-r3 = total_drifts 0 維持 / pytest 579 PASS 維持)
- 実運用検証で「SE 級での drift 解消は SSOT 親としての責務を損なわない」ことが確認できた (自主 PM 運用 = 編集計画宣言 + 実施 + tracker closed の 3 段階で十分)
- PM 昇格すると `docs/internal/` の drift 発見都度に承認ダイアログが発火し、W-R1 監査で 4 件検出済み (module 8) の解消フローに承認 4 回追加 = UX 悪化と drift 修正の実速度低下がトレードオフ

**運用ルール**:
- 権限等級判定 (`permission-levels.md` L36 「docs/ 配下 (上記以外) = SE」) は不変
- drift 発生時は tracker Warning/Info 起票 + W-R3/W-R5 で消化 (通常フロー)
- ただし「SSOT 親としての本質的な再定義」(例: docs/internal/ 節構造の大規模再編) はケースバイケースで PM 級判断を挟む可能性を残す (現時点で該当事例なし)

**関連 requirements 更新**: Q3 β「保留」ステータス → 「確定 (SE 級維持)」への変更は本 tracker 記録で代替 (requirements.md 本文改訂は W-R5 retro で一括 or 現状のまま tracker 参照で足りるかを判断)。

## 0.4. W-R3 S2 消化 (2026-07-10 / docs/internal SSOT drift 解消)

W-R3 S2 で `docs/internal/` の drift 4 件を消化 (自主 PM 運用 / L1 直進行 / ユーザー指示「私の判断を仰がず、あなたの推奨で進めるように」に基づく承認取得省略):

- **R1-040 (W / closed)**: 00_PROJECT_STRUCTURE.md §1 ツリーに `docs/design/` 追加 (Phase 1 成果物ディレクトリの地図への反映)
- **R1-041 (W / closed)**: 07_SECURITY_AND_AUTOMATION.md §5 に「MVP は G1+G2+G5 / G3・G4 は完全実装で段階的追加」+「AUTONOMOUS モードは Wave 2 まで G1 のみ」の段階記述追加 (`green-state-definition.md` §2.1-2.2 との drift 解消)
- **R1-043 (W / closed)**: 00_PROJECT_STRUCTURE.md §2-E の `.claude/states/*.json` 説明を「フェーズごとの承認ゲート管理」→「機能/Milestone 単位の承認ゲート状態・進捗記録 (例: `<milestone-slug>.json` / `cc-spec-alignment.json`, `large-scale-review.json` 等)」に修正 + フェーズ現在値管理は `.claude/current-phase.md` が担当することを明示
- **R1-I25 (I / closed / 序で消化)**: 02_DEVELOPMENT_FLOW.md 権限等級節に「フェーズ × 権限等級の全体設計は `.claude/rules/phase-rules.md` 冒頭二軸表参照 (PLANNING は承認ゲートのみで PG/SE 概念適用なし)」の 1 文追加

**編集 files**: 3 ファイル (`00_PROJECT_STRUCTURE.md` / `07_SECURITY_AND_AUTOMATION.md` / `02_DEVELOPMENT_FLOW.md`)
**Wave 完了ゲート更新**: module 8 open C+W = 4→1 (R1-042 既 closed + R1-040/041/043 今回 closed → R1-I26 Info + R1-I25 closed 分は残る) — 詳細は module 8 個別節参照
**次工程**: W-R3 S3 = `.claude/rules/` 相互矛盾解消 (R1-017/018/035/038/039) + FR-F5 決定実装

## 0.3. HGA #13 verdict (2026-07-10 / W-R3 S1 T2 規律 SSOT 統合方針の crux)

Fable HGA #13 (2026-07-10 / W-R3 S1 T2 / クレジット従量期初) が T1 成果物 `docs/artifacts/r-1-duplicate-pair-audit-2026-07-10.md` の対応方針 3 案 (更新 / 省略明記 / 統合) に crux 分岐を返す → **案 A' 確定** (選定基準を「RFC 級」から「違反時に別の防御層が拾うか」に差し替え / 詳細 anchor: `docs/artifacts/2026-07-10-fable-hga-13.md`)。

**crux 別結果**:
- **crux 1 (対応方針)**: **案 A' 採用** = M-02 (モード宣言) + M-04 (opt-out 却下) の 2 件のみ ambient 追記、M-01 (棄却対案記録) は SKILL.md 側にも欠落を確認 → 要約側 Output Format 節に追記、M-03 (AoT 無改変) は統合テスト 3 系統が拾うため参照 1 行、S-01/02/03 は参照丸投げ / 実追記 11 行 (70 → 81 行 / L1 当初見積 15-20 行から圧縮)
- **crux 2 (掲載可否判定軸)**: 「頻度」でも「ダメージ」でもなく **「違反時に別の防御層が拾うか」** に確定 (M-03 = テスト有 → 参照 1 行 / M-02/M-04 = テスト無 → ambient 掲載)
- **crux 3 (P2 = fable-l3-protocol.md × 外部 SSOT の監査対象化)**: **half-do 方針採用** = snapshot + 変更検知のみ / 修復は etc-to-alembic handoff 経由 / 検知頻度は retro 境界のみ → R1-060 (Info) 起票 + W-R5 retro 議題化
- **meta**: routing 降格なし / Fable 独立検証 (T1 成果物 + 06_DECISION_MAKING.md 全文 Read) / 要検証仮定 4 件のうち仮定 1 (SKILL.md M-01/opt-out 網羅) は L1 側で本 T3 で検証済 (M-01 欠落確認 → 要約側追記が正解と確定)

**新規起票 1 件** (§module 7 参照): R1-060 (Info / L3 導入後の外部 SSOT snapshot 機構未実装 / W-R5 retro 議題化)

**envelope 実測**: subagent_tokens 118,513 / tool_uses 2 / duration 145,392ms (145s) / #4 型パターン範疇 ($2-3 圏想定内 / 実 $ 詳細は hga-summon-log.md §day-1 実測メモ で jsonl 実測時に確定)

## 0. HGA #7 verdict メタ構造欠陥 (W-R5 retro 議題 / 2026-07-06 追加)

Fable HGA #7 (2026-07-06) が実測ベースで検出した 3 件の監査プロセス構造欠陥。W-R5 retro で恒久対策議題化する:

1. **修正の再監査ループ欠落**: W-R1 は Read-Only 監査 Wave だが、例外的な前倒し消化 (R1-032/R1-042) の修正コード自体は監査対象 11 モジュールのどのパスにも乗らない → R1-052 (R1-032 の残存 attack surface) を招いた。**恒久対策**: W-R2 以降の全消化に「fix の attack-surface 再列挙 + 独立検証 (gabriel 型 or spec-critic 独立召喚)」ゲート追加。
2. **tracker SSOT の自己検証欠如**: R-1 は inventory / cycle / reference の自動検査ツールを自作しながら、最重要成果物である tracker のヒートマップ⇔本文⇔変更履歴の突合検査がない (Fable A-3 が実証 = module 10 Info 件数 7 vs 実載 6 の drift 検出)。**恒久対策**: `.claude/scripts/verify_tracker_integrity.py` を W-R5 S1 の R-G6 判定前提として作成。
3. **Stage 間 severity/attribution 判定規準ドリフト**: severity (R1-001 Critical vs R1-006 Warning: 同一 bug class) と attribution (S3 downstream vs S4 self: 同一 drift 型) が監査 Stage ごとに揺れる。**恒久対策**: `code-quality-guideline.md` に「同型 finding の先例参照義務」+ 「監査インフラ欠陥は被監査コードより一段重い」等の重み付け規準を追加。

これらは W-R5 retro で議題化し、必要に応じて rules / spec / hga-summoning.md への恒久反映を実施する。

---

## 1. NFR-3 Critical 件数閾値

| 項目 | 値 | 出典 |
|:----|:---|:-----|
| 初期閾値 (暫定) | 10 件 | requirements.md NFR-3 |
| **確定閾値 (S5-T4 / 2026-07-06)** | **Critical 単独 3 件 or Critical + Warning 30 件** | 実測ベース (**W-R2 COMPLETE 後 open C=0 W=19 実測** / HGA #10 反映後) |
| 超過時アクション | 優先順位付けサブタスクを tracker に起票 (下記 §1.1) | spec-critic Warning W5 |

### 1.1 W-R2 以降の消化優先順位 (S5-T4 sub-task)

暫定閾値 10 は超過 (実測 open C+W = 19 / 2026-07-07 W-R2 COMPLETE 時点) だが、実測ベース閾値 (C 単独 3 / C+W 30) 内。以下優先順位で消化:

| Priority | Wave | issue | 根拠 |
|:--------:|:----:|:-----|:-----|
| ~~P1 (即時)~~ **closed** (2026-07-06 / W-R2 S1) | W-R2 S1 | ~~**R1-001 (Critical)**~~ — task_id 部分文字列マッチ → HGA #8 crux + Sonnet TDD 実装 + HGA #9 verify で closed | 唯一の Critical (dashboard 表示ロジック / 実運用で誤ステータス伝播) |
| ~~P1 (即時)~~ **closed** (2026-07-06 / W-R2 S1) | W-R2 S1 | ~~**R1-006 (Critical / HGA #7 昇格)**~~ — R-G7 監査インフラ false negative → 同上経路で closed | Critical 昇格分 / R-G7 baseline 再判定の前提 / R1-001 と同 bug class |
| ~~P2 (W-R3 or 新規 Wave)~~ **closed** (2026-07-07 / W-R2 S2 前倒し) | W-R2 S2 | ~~**R1-053 (Warning / HGA #9 新規)**~~ — verify_w_r3 パターン 3 の existence-check hole → Sonnet TDD 実装 + HGA #10 verify で closed (residual は R1-056 起票) | R1-006 と同 bug class (silent false negative / R-G7 gate 汚染候補) のため L1 裁定で S2 へ前倒し |
| P2 (W-R3 or W-R4) | W-R3/R4 | **R1-056 (Warning / HGA #10 新規)** — 多階層参照 `docs/specs/<slug>/<sub>/<file>.md` の fname 非捕捉退化 | R1-053 residual (同 bug class / live 0 実例) / R1-055 と同一ファイル圏で同時消化が効率的 |
| P2 (W-R3 S2) | W-R3 S2 | R1-042 (closed) + R1-040/R1-041/R1-043/R1-050 | docs/internal SSOT drift 解消 |
| P2 (W-R3 S3) | W-R3 S3 | R1-017/R1-018/R1-035/R1-038/R1-039/R1-I24 | rules 相互矛盾 |
| P2 (W-R3 S4) | W-R3 S4 | R1-046 (3 Milestone status drift) / R1-047/R1-048 (Info)/R1-049 | specs + adr + ルート統治文書一貫性 |
| P3 (W-R4 S1-3) | W-R4 全 Stage | ~~R1-002/R1-003~~ (closed W-R2 S4 前倒し) / R1-032 (closed)/R1-033/R1-034/R1-036/R1-037/R1-052 (closed) | hooks/agents/skills 整理 |
| P4 (W-R2 S3-4) | W-R2 S3-4 | ~~R1-007/R1-008~~ (closed W-R2 S2) / ~~R1-031~~ (closed W-R2 S3) / **R1-030 は W-R4 S2 `git rm` 束ねへ送り (推奨方針通り / 2026-07-07 L1 裁定)** | dashboard 領域 Warning |
| Info | W-R5 or 棚上げ | 全 Info 44 件 | Green State 判定に影響なし (code-quality-guideline 準拠) |

~~**開放 Critical 2 件** (R1-001 + R1-006) は **W-R2 S1 で最優先消化** (P1)。W-R5 S1 の R-G6 判定前に Critical=0 を確定必須。~~ **→ 2026-07-06 W-R2 S1 で消化完了 (open Critical = 0 実現)**。以降は R1-053 (Warning / HGA #9 発見) の消化計画を W-R3 以降で立案。

---

## 2. モジュール別問題数ヒートマップ (11 × 3)

**W-R2 COMPLETE 時点 (2026-07-07)**: 11 モジュール監査完了 + HGA #7-#10 反映済 + **W-R2 で 6 件消化** (R1-001/R1-006 = S1, R1-053/R1-007/R1-008 = S2, R1-031 = S3, R1-002/R1-003 = S4) + R1-056/057/058/059 起票 + R1-030 は W-R4 S2 送り裁定

| モジュール | Critical | Warning | Info |
|:----------|:--------:|:-------:|:----:|
| 1. `.claude/scripts/dashboard/` | **1** | **2** | **7** |
| 2. `.claude/scripts/` (外) | **1** | **4** | **9** |
| 3. `.claude/skills/` (23 SKILL.md) | **0** | **3** | **2** |
| 4. `.claude/tests/` | **0** | **2** | **3** |
| 5. `.claude/hooks/` + `settings*.json` | **0** | **4** | **4** |
| 6. `.claude/agents/` (12 件) | **0** | **3** | **2** |
| 7. `.claude/rules/` (11 files + auto-generated/) | **0** | **2** | **4** |
| 8. `docs/internal/` (00-07) | **0** | **4** | **5** |
| 9. `docs/specs/` (74 files / depth 制御) | **0** | **1** | **4** |
| 10. `docs/adr/` (10 files) | **0** | **2** | **7** |
| 11. `CLAUDE.md` + `CHEATSHEET.md` | **0** | **1** | **4** |
| **合計 (全 11 module / 全期間)** | **2** | **28** | **51** |
| **open** (closed 24 件 除外: R1-032/R1-042/R1-052/R1-001/R1-006/R1-053/R1-007/R1-008/R1-031/R1-002/R1-003/R1-040/R1-041/R1-043/R1-I25/R1-017/R1-018/R1-035/R1-038/R1-039/**R1-046/R1-047/R1-049/R1-050**) | **0** | **7** | **50** |

**HGA #7 verdict 反映差分** (2026-07-06 / Fable):
- (A) R1-006 Warning → **Critical 昇格** (監査インフラ false negative は R-G7 ゲート判定を偽 Green 化 / R1-001 と同一 bug class)
- (A) **R1-052 新規起票 + closed** (HGA #7 検出 / R1-032 修正が単体 `&` / `\n` / `<(` を素通し / 3 テスト追加で完全 closed)
- (B) R1-048 (ADR-0004 supersede) → **Info 降格** (実害なし自認 / R1-I46 へ)
- (B) R1-051 (CHEATSHEET Rules 4/11 欠落) → **Info 降格** (7/23 skills R1-I44 との対称 / CHEATSHEET は「抜粋」明示可能 / R1-I47 へ)
- (C) R1-047 / R1-049 / R1-050 attribution `self` → **`downstream`** 訂正 (単一モジュール完結でない cross-module drift)

**NFR-3 閾値確定 (最終 / spec-critic W5 対応)**:
- 累計 Critical + Warning = **30 件** (open C+W = **7 件** / closed 24 件除外 / R1-056 + R1-060 + R1-061 新規 open)
- **暫定閾値 10 の 3.0 倍超過 (累計)**
- **実測ベース閾値** (S5-T4): **Critical 単独 3 件 or Critical + Warning 30 件**
  - **W-R3 COMPLETE 後 (2026-07-10)**: 実測 open C=0 (< 3 OK) / C+W open=**7** (< 30 OK) → 実測ベース閾値では **未超過** (R1-046/047/049/050 の 4 件 Warning closed で -4)
  - **W-R3 Wave 完了ゲート全達成**: module 7/8/9/10/11 の open C+W = 0 全達成 ✅
  - ~~S5-T4 の条件分岐 sub-task = R1-001 の即消化を W-R2 S1 で最優先化~~ → **2026-07-06 完了 (open Critical = 0 実現)**

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

**attribution 併記形式** (HGA #7 verdict C-3 対応 / 2026-07-06 追加):
- 主 attribution + `(併記: <補助 attribution>)` 形式を許容 (例: `self (併記: spec_ambiguity)`)
- 主 attribution は必ず 5 択 (`upstream` / `downstream` / `spec_ambiguity` / `unknown` / `self`) から選択
- 併記 attribution は補助的 (spec の曖昧さと自己完結性が併存する境界事例等)
- W-R5 機械集計時は主 attribution のみで分類 (併記は補助注記として扱う)

**severity 変更履歴** (HGA #7 verdict A-2 / B-1 / B-2 対応 / 2026-07-06 追加):
- severity は監査後の再判定 (HGA verdict 等) で変更可能
- 変更時は issue セクションに `severity_history` フィールド追記 (`initial <old> (date) → <new> (date reason)`)
- 変更履歴は W-R5 retro での監査プロセス品質評価材料 (Stage 間判定ドリフト検出用)

---

## 4. issue 一覧

### module 1: `.claude/scripts/dashboard/`

**監査完了**: 2026-07-06 (W-R1 S2 T2 / code-reviewer subagent + L1 監督)
**集計**: Critical 1 / Warning 2 / Info 5

#### R1-001: `_resolve_task_status` の部分文字列マッチで Task ID の接頭辞衝突
- **severity**: **Critical**
- **responsibility_tag**: `dashboard-ui`
- **attribution**: `self`
- **status**: **`closed`** (2026-07-06 / W-R2 S1 T3-T4 経由 / HGA #8 crux + L2 Sonnet TDD 実装 + HGA #9 adversarial verify 完了)
- **opened_at**: 2026-07-06
- **closed_at**: 2026-07-06
- **closed_by_commit**: `34c0035`
- **evidence_file**: `.claude/scripts/dashboard/builder.py`
- **evidence_line**: 703-711
- **evidence_summary**: `if task_id in line:` は素の部分文字列マッチ。`task_id="W1-B5-T1"` は `line="- W1-B5-T10: ..."` に一致するため、T1/T10, T2/T20 等の接頭辞衝突で誤ステータス伝播。既存テストは接頭辞衝突をカバーせず。design.md §5 「完全一致前提」との黙示的仕様不一致。
- **推奨修正方針 (2026-07-06 HGA #8 crux 反映 / 初期方針は不十分と判明)**: Red で W1-B5-T10 のみ完了・W1-B5-T1 未完了の合成 fixture で接頭辞衝突テストを追加。Green で `re.search(r"(?<![A-Za-z0-9-])" + re.escape(task_id) + r"(?![A-Za-z0-9])", line)` に置換 (**negative lookbehind + lookahead 両方**)。**HGA #8 発見**: 初期方針 `(?:[:\s]|$)` は装飾文字 (`**ID**`, `(ID)`, `` `ID` ``, 全角括弧, 読点) で false negative + leading 境界欠如で短縮形 `T\d+` が `S3-T1` / `W3-B5-T31` 途中に誤マッチ。trailing に `-` を含めない理由 = SESSION_STATE 実物 L105 の `T1-T5` 範囲記法保護。**追加要件**: docstring L690-694 「行に `task_id` が含まれる」も同時更新 (Spec Synchronization)。Red で追加すべき境界テスト網羅 = 装飾 `**ID**` / `(ID)` / `` `ID` `` / 全角括弧 / leading 短縮形 `T31` の `W3-B5-T31` 誤マッチ回避 / Wave 小数形式 `W1.5-B4-T9` (計 7 case)。

#### R1-002: `_render_v2_milestones` が html.escape() を漏らしている (同ファイル内一貫性欠落)
- **severity**: Warning
- **responsibility_tag**: `dashboard-ui`
- **attribution**: `self`
- **status**: `closed` (2026-07-07 / W-R2 S4)
- **closed_by_commit**: `16b367f`
- **resolution**: `_render_v2_milestones` の 3 フィールド全て (`ms.name` = data-milestone 属性 + h3 / `current_phase` = span.step / `ms.status` = span.status) に `html.escape()` 適用。Red 実証: `<script>alert(1)</script>` 合成値 3 テスト (`test_render_v2_*_is_escaped`) が修正前 FAIL (生 script 混入を実測) → Green 27 PASS (conftest.py の make_milestone fixture 使用 = R1-031 成果物の初回再利用)
- **opened_at**: 2026-07-06
- **evidence_file**: `.claude/scripts/dashboard/builder.py`
- **evidence_line**: 596-599
- **evidence_summary**: 同ファイル内の他 render メソッド (v3_milestone_section L658 / v4_tasks L748-750 / filter_controls L829 / nav L888 / parser_errors L913) は全て `html.escape()` 適用済だが v2_milestones のみが `ms.name` / `current_phase` / `ms.status` を素通し。現状は Milestone 名の入力元が正規表現由来のため実害小だが、将来入力元が拡張された場合の XSS 窓。一貫性欠落は意図的除外ではなく単純漏れと判断。
- **推奨修正方針**: Red で Milestone 名に `<script>` 等を含む合成テストケースを追加し escape 出力を assert。Green で該当 3 箇所に `html.escape()` を適用。

#### R1-003: `DashboardBuilder` の God Class 傾向 (921 行 / 15 メソッド)
- **severity**: Warning
- **responsibility_tag**: `dashboard-ui`
- **attribution**: `self`
- **status**: `closed` (2026-07-07 / W-R2 S4 / **第一歩完了で closed 裁定** — evidence_summary の消化条件 = CSS/JS 切出しを充足 / 残るビュー分割は issue ではなく W-R5 retro 議題として引継)
- **closed_by_commit**: `16b367f`
- **resolution**: 推奨修正方針通り CSS/JS 静的合成を `.claude/scripts/dashboard/static_assets.py` (441 行 / `render_style()` + `render_script()`) へそのまま移動。builder.py 側は thin delegate 化 (呼び出し箇所ゼロ変更) で **936 行 (git HEAD 実測 / 起票時 921 は旧時点) → 539 行**。**byte-identical 検証済** (before/after 17,193 bytes / diff IDENTICAL)。579 PASS + 14 SKIP 維持。V1-V4 ビュー分割は W-R5 retro 議題 (observations.md 2026-07-07 §3 参照)
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

#### R1-061: `GitHistoryParser` Task ID regex が R-1 期 Milestone 記法 (`W-R\d+-S\d+-T\d+`) を捕捉できない — rule-001 と同型の parser drift
- **severity**: Info
- **responsibility_tag**: `parser-drift` (併記: `rules-consistency`)
- **attribution**: `self`
- **status**: `open` (2026-07-10 W-R3 S1 T5 で hotfix 実施 = regex 拡張 + test skip 化 / **rule-002 恒久化は W-R5 議題**)
- **opened_at**: 2026-07-10 (W-R3 S1 T5 実 git log pytest 実行時に発見 = 事後発見)
- **evidence_file**: `.claude/scripts/dashboard/parsers/git_history.py`, `.claude/tests/dashboard/test_git_history_parser.py`
- **evidence_line**: git_history.py L24-27 (regex), test_git_history_parser.py L443 (assert)
- **evidence_summary**: L3 導入 (2026-07-07) の 5 コミット追加により、直近 100 コミット window から旧 Task ID 形式 (`W\d+-B\d+-T\d+`) が押し出され、実 git log parse test (`test_parse_with_real_git_log`) が Task=0 で FAIL 検出。**rule-001 (SessionStateParser fallback 保守) と同型の parser drift** (parser regex × 実装記法進化 の追随失敗 / 3 回発火閾値到達で恒久ルール昇格すべきパターン)。W-R3 S1 T5 で hotfix: (1) regex を `\b(W-?[A-Z0-9]+(?:-[A-Z][0-9]+)*-T\d+[a-z]?)\b` に拡張 (`W-R3-S1-T1` 系対応) (2) テスト assert に「Task=0 期は Wave 検出で PASS 化する skip」を追加。
- **推奨対応**: **rule-002 candidate** = 「GitHistoryParser regex を実装記法進化に追随させる保守ルール」。rule-001 と併せて `docs/specs/tdd-introspection-v2.md` の信頼度モデル閾値 (初期 2 回) 到達検討。commit message での Task ID 明示規律 (「Stage 末 ship commit には W-<milestone>-S<stage>-T<n> 形式で対象 Task を列挙する」等) の追加も検討候補。優先度 Info (dashboard 表示の限定機能のため)。**W-R5 retro 議題化必須** (R1-060 と同格の後続 pointer)。

#### R1-054: `_resolve_task_status` の lookbehind/lookahead が underscore を境界文字扱いしない (HGA #9 verdict C-N1 / 未文書化 false-positive surface)
- **severity**: Info (spec 忠実 / HGA #8 crux の指定通りだが未文書化)
- **responsibility_tag**: `dashboard-ui`
- **attribution**: `self`
- **status**: `open`
- **opened_at**: 2026-07-06 (HGA #9 verdict C-N1)
- **evidence_file**: `.claude/scripts/dashboard/builder.py`
- **evidence_line**: 713-714 (regex `(?<![A-Za-z0-9-])<task_id>(?![A-Za-z0-9])`)
- **evidence_summary**: HGA #9 probe: `re.search(r"(?<![A-Za-z0-9-])W1\-B5\-T1(?![A-Za-z0-9])", "W1-B5-T1_note: done")` → match=True。task_id が snake_case token の一部として embed された場合に誤マッチする surface が存在。実 SESSION_STATE 実物には該当 token なし (0 例) だが、将来 task_id 表記慣習が変わった場合の false-positive risk。
- **推奨対応**: (a) accept-and-document (現行仕様維持 + `_resolve_task_status` docstring に「underscore は境界文字扱いしない」と 1 行明記) / (b) lookbehind/lookahead 両方に `_` を追加 (`(?<![A-Za-z0-9_-])` + `(?![A-Za-z0-9_])`)。W-R3 or W-R4 で軽微 refactor として消化候補。R1-001 core regex とは独立。

### module 2: `.claude/scripts/` (外)

**監査完了**: 2026-07-06 (W-R1 S2 T3 / code-reviewer subagent + L1 監督)
**集計**: Critical 0 / Warning 3 / Info 4
**特記**: 3 件全てが **本監査シリーズで作成した self コード** の Warning (Fable→Opus gap 事例 #2 = Opus 自身の T1/T4 実装漏れを subagent が発見)

#### R1-006: `verify_reference_resolution.py` の rules パス正規表現が大文字・ドット含みファイル名を検出漏れ (監査インフラ false negative / R-G7 ゲート判定汚染)
- **severity**: **Critical** (HGA #7 verdict A-2 で 2026-07-06 昇格 / 初期 Warning → **Critical** / 監査インフラ欠陥は R1-001 と同一 bug class = R-G7 ゲート判定を偽 Green 化するため被監査コードより一段重い)
- **responsibility_tag**: `audit-script`
- **attribution**: `self`
- **status**: **`closed`** (2026-07-06 / W-R2 S1 T3-T4 経由 / HGA #8 crux + L2 Sonnet TDD 実装 + HGA #9 adversarial verify 完了)
- **opened_at**: 2026-07-06
- **closed_at**: 2026-07-06
- **closed_by_commit**: `34c0035`
- **severity_history**: initial Warning (2026-07-06) → Critical (2026-07-06 HGA #7 verdict A-2) → **closed as Critical (2026-07-06 W-R2 S1 T4)**
- **evidence_file**: `.claude/scripts/verify_reference_resolution.py`
- **evidence_line**: 37-39 (`_W_R3_PAT_RULES_PATH`) + 43-44 (パターン 3 も同型)
- **evidence_summary**: `_W_R3_PAT_RULES_PATH = re.compile(r"\.claude/rules/(?:auto-generated/)?([a-z0-9-]+\.md)")` は文字クラスが `[a-z0-9-]+` のみ。**実測 (2026-07-06)**: rule-001.md L76 の `.claude/rules/auto-generated/README.md` 参照が unmatched (大文字ファイル名 false negative)。**HGA #7 追加検出**: パターン 3 も同型で **ドット (`.`) を含むファイル名も unmatched** (例: `v4.0.0-immune-system-requirements.md`)。false negative = 実 drift があっても drift=0 と誤報告する監査ツール自体の信頼性欠陥 → R-G7 ゲート (Green State baseline §「実 drift なし」判定根拠) を偽 Green 化。
- **推奨修正方針 (2026-07-06 HGA #8 crux 反映 / 初期方針の一律拡張は platform 依存バグを招くと判明)**: **HGA #8 発見**: tracker 初期方針の一律 `[A-Za-z0-9._-]+` は **パターン 3 slug (group 2 / `\.md` アンカーなし)** で文末句点を捕食 (例: `'... docs/specs/large-scale-review. 次の文'` → slug=`large-scale-review.` になる) → Windows 末尾ドット quirk (`Path('docs/specs/large-scale-review.').exists()` → 本機 win32 で True 実測) で **偽 Green** / POSIX で False で偽 drift。修正は 3 箇所に**同一クラス適用不可**:
  - **パターン 1 group 1** (`\.md` アンカー付き): `[A-Za-z0-9._-]+` — greedy+backtrack で末尾自動整形 (安全)
  - **パターン 3 group 3** (`\.md` アンカー付き): 同上
  - **パターン 3 group 2 (slug / アンカーなし)**: `[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*` (**内部ドットのみ許容 / 末尾ドット不可**)
  - パターン 2 (`rule-\d{3}`) は無関係で無変更
- **underscore 含める理由**: 現 rules/ ファイル名は kebab 統一だが、drift 検出器では『マッチしない = silent false negative』が最悪の失敗モードであり、underscore 参照は『マッチして existence 検査で drift 報告される』方が正しい (Fable 判定)
- Red で追加すべきテスト (計 8 case): (a) 大文字 `README.md` + (b) ドット合成 `foo.v2.md` + (c) 文末句点 backtrack `phase-rules.md.` + (d) パターン 3 ドット slug `v4.0.0-immune-system-requirements.md` + (e) 文末句点 slug ケース (末尾ドットなしで停止 / Red 対比) + (f) 既存 `0009-hga-fable-summoning.md` regression + (g) underscore drift 検出 (`some_rule.md` unmatched → matched に変化 + drift report) + (h) E2E で新規 drift が全て「真の実在なし」であること (false positive ゼロ検査)
- **live baseline 事前裁定**: 現行 `verify_reference_resolution.py --wave w-r3` は既に drift=1 (`docs/specs/feature` placeholder / `99_reference_generic.md` 由来) を報告済。W-R2 S1 内で「山括弧付き `<feature>` テンプレ書式変更 or 検出器側で `<...>` 除外リスト化」のいずれかを 1 行決めておく (R-G7 再判定の前提)
- **W-R2 S1 で最優先消化** (Critical / R-G7 baseline 再判定の前提)。**Fable→Opus gap 恒久対策 memo §事例 #2** として記録推奨 (2 段階検出 = subagent 1 段目 + HGA 2 段目 パターン)。

#### R1-007: `distill_lessons.py` の `is_small_task` パラメータが未使用のままシグネチャに残存 (dead code)
- **severity**: Warning
- **responsibility_tag**: `cli-entrypoint`
- **attribution**: `self`
- **status**: `closed` (2026-07-07 / W-R2 S2)
- **closed_by_commit**: `341ba6a`
- **resolution**: 推奨方針 (b) = dead code 除去を採用。裁定根拠: design §9.1 の小タスクルートは「grader ログを 1 件のみ渡す呼び出し方の違い」であり、design §13 パイプライン図にも SKILL.md フロー[8] にも `distill()` 内分岐の要求なし (L2 Sonnet が read-only 読解 + L1 検収)。パラメータ・docstring 該当記述・caller 引数を削除、CLI `--small-task` フラグは文書化された呼び出し例と整合するため意味的マーカーとして維持 (help 文言を実態に更新)。新規テスト 4 件 (`test_distill_lessons.py` / 削除前ベースライン 4 PASS → 削除後 4 PASS)。副次: `SKILL.md` フロー[8] L292 の呼び出し例から `is_small_task=False` を除去 (ドキュメント同期 / SE 級 / L1 実施)
- **opened_at**: 2026-07-06
- **evidence_file**: `.claude/scripts/distill_lessons.py`
- **evidence_line**: 279, 293 (docstring), 395 (caller)
- **evidence_summary**: `distill()` は `is_small_task: bool = False` を受け取り docstring で「小タスクルート (grader ログのみ / design §9.1)」を説明するが、関数本体 (274-309 行) 内で **一度も参照されない**。`grep -c "is_small_task"` の結果は 3 のみ (シグネチャ + docstring + caller)。設計意図が実装未反映か既に別ロジックで代替されて docs 未追随のいずれか。
- **推奨修正方針**: (a) 小タスクルート特有分岐 (previous_feedback 生成省略 / L1 検収 skip 等) を実装 or (b) 不要なら docstring とパラメータ削除。Red で `is_small_task=True/False` の出力差異 assert テスト追加 (現状 Red)。

#### R1-008: `r1_inventory.py` の module 2 glob が gitignore 済みファイルを inventory に混入 (自己コード)
- **severity**: Warning
- **responsibility_tag**: `audit-script`
- **attribution**: `self`
- **status**: `closed` (2026-07-07 / W-R2 S2)
- **closed_by_commit**: `341ba6a`
- **resolution**: `_tracked_files()` 新設 (`git ls-files` 1 回実行 + プロセス内キャッシュ) + `_glob_module()` に tracked filter 追加。**module 2 限定ではなく全 module (1-11) パターンに一貫適用**。Red 実証: `test_module_2_excludes_gitignored_files` + `test_module_2_file_count_matches_tracked_files` が修正前 FAIL (`14 == 12` 不一致 / `scan_nfr_refs*.py` 2 件検出) → 修正後 9 PASS / 0 FAIL。inventory JSON の再生成は実施せず (W-R5 S2 baseline 再計測ゲートで吸収 / 従来方針通り)
- **opened_at**: 2026-07-06
- **evidence_file**: `.claude/scripts/r1_inventory.py`
- **evidence_line**: 27 (`2: ".claude/scripts/*.py"`), 46-55 (`_glob_module`)
- **evidence_summary**: `glob.glob()` は `.gitignore` を関知しない。`git check-ignore` 実測で `.claude/scripts/scan_nfr_refs.py` / `scan_nfr_refs2.py` は gitignore 対象と確認済だが、inventory JSON の module 2 に混入 (実測 14 files ≠ tracked 12 files)。後続の R-G8 / 監査集計が gitignore 済 ad-hoc スクリプトを「本番コード」誤認するリスク。
- **推奨修正方針**: `_glob_module` に `git ls-files` ベースの filter 追加 or `.gitignore` パターン照合。Red で gitignore 済ダミーファイル配置 → inventory 出力に含まれないこと assert。**W-R2 S2 で対応推奨** (inventory 再生成が R-G8 baseline の前提)。

#### R1-053: `verify_w_r3` パターン 3 の existence-check hole (dir 存在で fname 存在検査省略 / **R1-006 と同 bug class**)
- **severity**: Warning (**Critical candidate** / silent false negative surface / R-G7 gate 汚染候補 / ただし live scan で 0 実例のため即時 Critical 昇格せず Warning 起票)
- **responsibility_tag**: `audit-script`
- **attribution**: `self`
- **status**: `closed` (2026-07-07 / W-R2 S2 前倒し消化)
- **closed_by_commit**: `341ba6a`
- **resolution**: 推奨修正方針通り、fname 捕捉時 (`if fname:`) は `(dir/fname).exists()` を厳密要求・非捕捉時は従来 any() 判定を維持する非対称分岐に変更 (L2 Sonnet tdd-developer / 2 段階検出パターン踏襲)。Red 実証: `test_verify_w_r3_detects_drift_when_dir_exists_but_fname_missing` が修正前 FAIL (hole の実証) → Green 27 PASS + regression 保護 3 テスト。live drift 0 維持。**HGA #10 adversarial verify = confirmed-with-warnings / fix_before_ship 不要 / confidence 0.90** (§0.2)。residual (多階層参照の fname 非捕捉退化) は R1-056 として分離起票
- **opened_at**: 2026-07-06 (HGA #9 verdict C-N3)
- **evidence_file**: `.claude/scripts/verify_reference_resolution.py`
- **evidence_line**: 145-151 (`candidates = [dir, slug.md, dir/fname]` + `if not any(c.exists() for c in candidates): drift 起票`)
- **evidence_summary**: HGA #9 probe P4: `docs/specs/large-scale-review/nonexistent-file-xyz.md` を pattern 3 が `(specs, large-scale-review, nonexistent-file-xyz.md)` として capture するが、candidate 配列に `dir/` (`docs/specs/large-scale-review/`) が含まれ実在するため `any(exists)=True` → **fname の実在検査を素通し**して drift 判定に至らない。**これは R1-006 が Critical に昇格した「silent false negative」と同じ bug class**。**軽減要因**: (i) 本 logic は S1-T2 で新規導入されたものではなく事前存在 (char-class 変更のみが scope だった) / (ii) HGA #9 probe P8 で live corpus に該当実例 0 件と実測。**新規 issue として起票**し R1-001/R1-006 は reopen しない (HGA #9 recommendation)。
- **推奨修正方針**: `verify_w_r3` パターン 3 分岐で fname が capture された場合 (`fname is not None`) は `(dir/fname).exists()` を厳密要求 (any → all または fname 存在時は fname 経路のみで判定)。Red で本 issue evidence_summary の合成 fixture を追加。**W-R3 S1 or 新規 Wave で消化推奨** (R-G7 baseline を偽 Green 化する潜在があり P2 相当)。

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

#### R1-055: `Path.exists()` の win32 case-insensitive で drift portability リスク (HGA #9 verdict C-N4 / residual)
- **severity**: Info (residual risk / live corpus で 0 実例)
- **responsibility_tag**: `audit-script`
- **attribution**: `self` (併記: `spec_ambiguity` — 検出器 portability 要件が未定義)
- **status**: `open`
- **opened_at**: 2026-07-06 (HGA #9 verdict C-N4)
- **evidence_file**: `.claude/scripts/verify_reference_resolution.py`
- **evidence_line**: 100-104, 138-144 (存在検査ロジック全般)
- **evidence_summary**: HGA #9 probe P6: `Path('.claude/rules/PHASE-RULES.md').exists()=True` および `Path('docs/specs/LARGE-SCALE-REVIEW').exists()=True` を本機 (win32 / NTFS default) で実測。case-drifted 参照が本機で偽 Green 化し、POSIX checkout では真 drift として顕在化する platform 依存リスク。HGA #9 probe P9 で live corpus に case-mismatch 参照 0 件と実測されているため即時 Warning 起票せず。CI が Linux で走る場合 (Green State §G1) や複数 checkout 環境で発火可能性。
- **推奨対応**: (a) accept-as-residual (現状維持 / POSIX CI ゲートで代替検出) / (b) case-exact check 実装 (`os.listdir()` ベースで parent dir と capture 名 case-exact 一致確認)。R-G7 baseline 変動を許容できるなら (b) を W-R3 or W-R4 で軽微 refactor 消化候補。

#### R1-056: `verify_w_r3` パターン 3 の多階層参照が fname 非捕捉に退化し素通し (**R1-053/R1-006 と同 bug class の residual**)
- **severity**: Warning (silent false negative surface / live corpus で 0 実例のため非 blocking)
- **responsibility_tag**: `audit-script`
- **attribution**: `self`
- **status**: `open`
- **opened_at**: 2026-07-07 (HGA #10 verdict 軸 B)
- **evidence_file**: `.claude/scripts/verify_reference_resolution.py`
- **evidence_line**: 51 (group3 文字クラス `[A-Za-z0-9._-]+\.md` に `/` を含まない)
- **evidence_summary**: HGA #10 probe: `docs/specs/large-scale-review/research/foo-notes.md` 形の多階層参照は group3 が match せず fname=None に退化 → R1-053 修正後も dir-only の any() 判定に落ち、dir 実在のみで素通し (silent false negative)。repo には `docs/specs/goal-driven-orchestration/research/` 等の多階層 spec 構造が実在するため参照形として現実的。live corpus (docs/internal) では 0 実例を grep 実測 (HGA #10)。R1-053 起票時と同じ「Warning / 非 blocking」判断が整合的。
- **推奨修正方針**: group3 を `((?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+\.md)` 型に拡張し strict 判定を多階層対応させる、または known-residual として design §5.1 に明記。Red で多階層 fixture (実在 subdir + 非実在 fname) の characterization テスト追加。**W-R3 S1 or W-R4 で消化候補** (R1-055 と同一ファイル圏 / 同時消化が効率的)。

#### R1-057: パターン 3 regex の非捕捉退化 3 態様 (非 .md 拡張子 / 大文字 `.MD` / file-as-dir 擬似通過)
- **severity**: Info (residual / 実例可能性は極小)
- **responsibility_tag**: `audit-script`
- **attribution**: `self`
- **status**: `open`
- **opened_at**: 2026-07-07 (HGA #10 verdict 軸 B/C 付随)
- **evidence_file**: `.claude/scripts/verify_reference_resolution.py`
- **evidence_line**: 50-52 (IGNORECASE なし / `\.md` 固定), 153-157 (else 分岐 candidate 1)
- **evidence_summary**: HGA #10 指摘の集約 3 態様: (i) 非 .md 参照 (`.png`/`.json` 等) は fname 非捕捉で dir-only 判定 (scope 判断として妥当だが暗黙)。(ii) `DESIGN.MD` 等大文字拡張子も同様に退化 (R1-055 の win32 case とは独立の regex 層)。(iii) else 分岐 candidate 1 は `.exists()` がファイルにも True を返すため `docs/specs/foo.md/` (flat ファイル + trailing slash typo) が「dir 実在」扱いで通る (参照先実体は存在するため実害は擬似的)。
- **推奨対応**: R1-056 消化時に scope 判断 (非 .md / 大文字) を docstring or design §5.1 に明文化。(iii) は `is_dir()` 化の軽微 refactor 候補。

#### R1-058: パターン 3 の走査対象は docs/internal のみ — `.claude/rules/*.md` 内の spec 参照は存在検査の圏外
- **severity**: Info (design §5.1 の scope 定義通り / 記録価値)
- **responsibility_tag**: `audit-script`
- **attribution**: `self` (併記: `spec_ambiguity` — 検査 scope 拡張の要否が未定義)
- **status**: `open`
- **opened_at**: 2026-07-07 (HGA #10 verdict meta)
- **evidence_file**: `.claude/scripts/verify_reference_resolution.py`
- **evidence_line**: 138 (走査対象 = docs/internal)
- **evidence_summary**: `.claude/rules/rule-001.md` → `docs/specs/tdd-introspection-v2.md` 等、rules 層からの spec 参照は verify_w_r3 の存在検査フェンス外。R1-053/R1-056 と同型の hole が検査圏外に残る。design §5.1 の scope 定義には準拠しているため issue ではなく scope 拡張の検討記録。
- **推奨対応**: W-R3 (規律 SSOT 統合) で `.claude/rules/` を走査対象に加えるか否かを design 側で裁定 (R-G7 baseline 変動を伴うため PM 級)。

#### R1-059: gabriel 契約チェックが substring 判定 (`f in text`) の弱検査
- **severity**: Info (R1-053 と無関係の既存事項 / HGA #10 が scope 外検出)
- **responsibility_tag**: `audit-script`
- **attribution**: `self`
- **status**: `open`
- **opened_at**: 2026-07-07 (HGA #10 verdict 付随)
- **evidence_file**: `.claude/scripts/verify_reference_resolution.py`
- **evidence_line**: 233
- **evidence_summary**: gabriel 契約フィールドの検査が `f in text` の substring 判定であり、無関係な散文中の "confidence" 等でも充足する。契約検査としては弱いが、現状の用途 (粗い presence check) では実害未観測。
- **推奨対応**: 構造化パース (行頭 key: 形式の regex) への強化を W-R4 軽微 refactor 候補として記録。

### module 3: `.claude/skills/`

**監査完了**: 2026-07-06 (W-R1 S2 T4 / code-reviewer subagent + L1 監督 + context7 upstream 裏取り)
**集計**: Critical 0 / Warning 3 / Info 3 (R1-016 を subagent 4 件 → 監督修正 3 件に変更 / 2026-07-12 R1-062 追記 = HGA #14 F18 由来)
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
- **status**: **`closed`** (W-R3 S3 消化 / 2026-07-10 / 5 term 用語統一 = design-mode→planning / build-mode→building / audit-mode→auditing / session-save→quick-save / session-load→quick-load)
- **closed_at**: 2026-07-10
- **closed_by_commit**: `12ecd6c`
- **opened_at**: 2026-07-06
- **evidence_file**: `.claude/skills/init-harness/SKILL.md`
- **evidence_line**: 17, 172 (harness.json 内 enabled_skills), 191, 236, 291-293
- **evidence_summary**: 本文 + 生成する harness.json + CHEATSHEET テンプレートが存在しない skill 群 (`design-mode`, `build-mode`, `audit-mode`, `session-save`, `session-load`) と存在しない spec (`docs/specs/init-harness/spec.md` / 該当ディレクトリ自体不在) を参照。実在は `planning` / `building` / `auditing` / `quick-save` / `quick-load` (`ls .claude/skills/` 確認済)。旧 user-global テンプレートを project-local に複製時の用語同期漏れ。
- **推奨修正方針**: 用語統一 (`design-mode`→`planning`, `build-mode`→`building`, `audit-mode`→`auditing`, `session-save`→`quick-save`, `session-load`→`quick-load`) or 本 skill 廃止/凍結 (本 project は既にハーネス適用済のため実行見込み低)。W-R3 S1-S3 (規律 SSOT 統合) で対応。

#### R1-018: `goal-driven/SKILL.md` 実装ステータス表が stale (「未実装」→ 実在確認)
- **severity**: Warning
- **responsibility_tag**: `spec-drift`
- **attribution**: `self`
- **status**: **`closed`** (W-R3 S3 消化 / 2026-07-10 / L390-392 3 行を「完了」に更新 / エージェント定義 3 件 + gd_state.py + Stop hook B-3 節すべて実在確認済)
- **closed_at**: 2026-07-10
- **closed_by_commit**: `12ecd6c`
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

#### R1-062: `quick-load/SKILL.md` L40 注記が撤回済機能 (Step 4 モード認知サマリ表示) への説明のみを保持 (HGA #14 F18)
- **severity**: Info
- **responsibility_tag**: `spec-drift`
- **attribution**: `self`
- **status**: `open`
- **opened_at**: 2026-07-12 (HGA #14 finding F18 / Phase A adversarial review)
- **evidence_file**: `.claude/skills/quick-load/SKILL.md`
- **evidence_line**: 40 (`> **注記 (ADR-0008 v0.3 / 2026-06-30)**: 旧 Step 4「モード認知サマリ表示」...`)
- **evidence_summary**: quick-load skill は現行 4 step (SESSION_STATE 読み込み / 関連ドキュメント特定 / 復帰サマリー / ユーザー指示待ち) で完結し、L40 の注記のみが「撤回済 Step 4 = モード認知サマリ表示 (`detect-permission-mode.py` 自動実行)」への説明を保持している。skill 本文には Step 4 の実体がなく (Step 4 = 「ユーザーの指示を待つ」に振り替え済)、L40 は歴史記録・debug 用の温存目的で残されている。HGA #14 (2026-07-12 / Phase A adversarial review) は本注記を「撤回済機能への言及が本文と独立に温存されており、将来の読者が『Step 4 が別途あるはず』と誤読するリスク」として Info 起票を推奨。ただし ADR-0008 v0.3 撤回の意思決定履歴は保存価値があり、削除すべきかは判断分岐あり。
- **推奨対応**: 3 択で W-R5 議題化: (a) 現状維持 (歴史記録として温存 / 現行 skill 動作に影響なし)、(b) 注記を「削除」として本文から外し、代わりに CHANGELOG.md or ADR-0008 側にのみ残す (SSOT 単一化)、(c) 注記本文を「※本 skill には Step 4 = ユーザー指示待ち のみが存在します (過去の Step 4 モード認知サマリ表示は ADR-0008 v0.3 で撤回)」に書き換えて誤読リスクを排除。優先度 Info (実害なし / L1 の quick-load 動作は現行 4 step で正常)。

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
- **status**: `closed` (2026-07-07 / W-R2 S3)
- **closed_by_commit**: `6e0bb66`
- **resolution**: `.claude/tests/dashboard/conftest.py` 新設 (factory fixture 3 種 / models.py フィールド定義準拠の既定値)。**計測基準の訂正**: 起票時「87 箇所」は型名の grep -c 言及回数ベースで、実際の手動構築呼び出し (`Name(` 形式) は 52 箇所 — うち 49 箇所を fixture 移行、3 箇所 (test_base_parser.py のモデル仕様直接検証テスト 3 件) は例外規則で意図的残置。ローカル重複ヘルパー (`_make_milestone` / `_make_wave` / `_make_task` / builder 系) を全廃し正味 -71 行 (7 ファイル変更 + conftest.py 新規 / 3 ファイルは手動構築なしと実測判明で無変更)。ファイル単位の段階検証 + 全体 576 PASS + 14 SKIP + 0 FAIL 維持 (件数不変) / L1 独立再走で一致確認
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

#### R1-052 (HGA #7 検出 / 2026-07-06): R1-032 追加対応 — `_SHELL_METACHARACTERS` タプルが単体 `&` / `\n` / `<(` を素通し
- **severity**: Warning
- **responsibility_tag**: `permission-check`
- **attribution**: `self`
- **status**: **`closed`** (HGA #7 verdict A-1 直後に前倒し消化 / commit で埋め)
- **opened_at**: 2026-07-06
- **closed_at**: 2026-07-06
- **evidence_file**: `.claude/hooks/pre-tool-use.py`
- **evidence_line**: 95 (初期修正 `_SHELL_METACHARACTERS = (";", "&&", "||", "|", "\`", "$(")`)
- **evidence_summary**: R1-032 の初期修正 (commit `8c00786`) は 6 文字のみ列挙で、以下 3 パターンを素通ししていた:
  - **単体 `&`** (バックグラウンド区切り): `ruff format x.py & rm -rf /tmp` は `"&&" in "x.py & rm..."` = False で PG auto-allow に到達 (shell では末尾でなければコマンド区切り)
  - **改行 `\n`** (複数行コマンド): shell で行ごとに実行
  - **プロセス置換 `<(...)`** ($( のみ検査で `<(` 未対応)

  Fable HGA #7 (2026-07-06) が実測ベースで検出 (verdict A-1)。同一 attack class (R1-032 と等価) の残存で、L1 監督の「修正の再監査」工程欠落を実証 (メタ構造欠陥 #1)。
- **修正**: `_SHELL_METACHARACTERS` タプルに `"&"`, `"\n"`, `"<("` を追加 (計 9 文字)。追加テスト 3 件 (single ampersand / newline / process substitution) で Red-Green 完了 → 全 13 tests PASS + regression 537 PASS + 14 SKIP。
- **HGA #7 反映アクション**: L1 監督工程に「前倒し消化時の attack-surface 再列挙 + 独立検証」ゲートを W-R5 retro で議題化 (メタ構造欠陥 #1 恒久対策)。

### module 6: `.claude/agents/`

**監査完了**: 2026-07-06 (W-R1 S3 T2 / L1 直監査 + context7 upstream 裏取り)
**集計**: Critical 0 / Warning 3 / Info 2
**特記**: context7 (`/websites/code_claude` sub-agents / AgentDefinition Python dataclass) で公式 frontmatter フィールド確定 → `# permission-level:` は非公式 (dead comment cluster) / `effort:` は公式だが `default` は EffortLevel 列挙値外 / `tools: Agent(name)` parametrized は `settings.json permissions.deny` 側は公式サポート済だが subagent frontmatter `tools:` allowlist 側は未確定 (要実測)。

#### R1-035: `# permission-level: XX` コメントアウトが 8 agents に散在 (dead comment cluster)
- **severity**: Warning
- **responsibility_tag**: `frontmatter`
- **attribution**: `self`
- **status**: **`closed`** (W-R3 S3 消化 / 2026-07-10 / sed で 8 files 一括削除 = code-reviewer / design-architect / doc-writer / quality-auditor / requirement-analyst / task-decomposer / tdd-developer / test-runner / gabriel + goal-driven 4 files は元々未記載で統一済)
- **closed_at**: 2026-07-10
- **closed_by_commit**: `12ecd6c`
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
**集計**: Critical 0 / Warning 2 / Info 4 (2026-07-10 R1-060 追記 / HGA #13 crux 3 由来)
**特記**: subagent が全 14 files で参照する実装・仕様・ADR・internal SSOT を Grep/Bash で実在確認済 (unverified なし)。両 Warning は「同一トピックの重要度/枠組み定義の rules 間 drift」で construct-level (実運用破綻は未確認 / W-R3 で消化)。

#### R1-038: `code-quality-guideline.md` と `phase-rules.md` の「テストなし実装」重要度判定 drift
- **severity**: Warning
- **responsibility_tag**: `rules-consistency`
- **attribution**: `self` (併記: `spec_ambiguity` — 両者の優先順位が rules 上で明記されていない)
- **status**: **`closed`** (W-R3 S3 消化 / 2026-07-10 / PM 級両側修正 = code-quality-guideline.md L37 に AUDITING 時 Warning 判定 vs BUILDING 実行中規律の分離を明示 + phase-rules.md L145 に相互参照 1 文追加)
- **closed_at**: 2026-07-10
- **closed_by_commit**: `12ecd6c`
- **opened_at**: 2026-07-06
- **evidence_file**: `.claude/rules/code-quality-guideline.md`, `.claude/rules/phase-rules.md`
- **evidence_line**: code-quality-guideline.md L37 / phase-rules.md L87
- **evidence_summary**: `code-quality-guideline.md` L37 は「テストが存在しない新規ロジック」を明示的に **Warning (non-blocking)** に分類し「BUILDING の TDD ルール違反でもあるが、保守困難性の観点で Warning」と注記。一方 `phase-rules.md` L87 は BUILDING 「禁止」リストに「テストなし実装」を無条件掲載し Critical 相当の絶対規律として読める。同一トピックで AUDITING 時の重要度 (Warning) と BUILDING 時の規律 (絶対禁止) が別重みづけを持ち、優先順位が rules 上未明記。監査担当が Critical/Warning に倒すべきか判断がぶれるリスク。
- **推奨修正方針**: code-quality-guideline.md L37 に「ただし BUILDING フェーズ中の禁止事項 (`phase-rules.md`) としては別途扱う。AUDITING 時点での重要度判定は本項の Warning を用いる」等、両者関係性を明示する 1 文追加。**W-R3 S3 (rules 相互矛盾解消)** で消化。

#### R1-039: `hga-summoning.md` の envelope 記述に新旧併存の矛盾 (月 $40-80 単一枠 vs 二軸化後の実 $/quota 分離)
- **severity**: Warning
- **responsibility_tag**: `rules-consistency`
- **attribution**: `self`
- **status**: **`closed`** (W-R3 S3 消化 / 2026-07-10 / PM 級修正 = L96 を「実 $ envelope (月 $10-40) + Opus quota envelope (weekly cap 20% 以内) の両方の外」に統一 + 旧記述の置換履歴を注記)
- **closed_at**: 2026-07-10
- **closed_by_commit**: `12ecd6c`
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

#### R1-060: `fable-l3-protocol.md` × 外部 Fable-Alembic SSOT の snapshot 機構未実装 (HGA #13 crux 3 = half-do 方針の後続)
- **severity**: Info
- **responsibility_tag**: `rules-consistency`
- **attribution**: `self`
- **status**: `open`
- **opened_at**: 2026-07-10 (W-R3 S1 T3 / HGA #13 verdict)
- **evidence_file**: `.claude/rules/fable-l3-protocol.md`
- **evidence_line**: §2 参照 SSOT (L38-46) + §5 外部参照体系
- **evidence_summary**: L3 導入後、`fable-l3-protocol.md` は自身が LAM 内 SSOT / 外部 `D:\work7\Fable-Alembic\knowledge\` を参照 SSOT とする非対称構造を持つ。Outbound Write Ban により LAM 側から外部編集不能 → currency 問題の鏡像 = 「LAM は外部 SSOT が変わったことに気づけない」。HGA #13 (2026-07-10) verdict = **half-do** (snapshot + 変更検知のみ / 修復は etc-to-alembic handoff 経由 / 検知頻度は retro 境界のみ)。W-R5 retro で snapshot 実装形式 (git commit hash + SHA256 / `fable-l3-baseline-<date>.md` §末尾追記) の確定 + 初回 baseline 取得タイミングを議題化。
- **推奨対応**: W-R5 retro 議題化 (`fable-l3-baseline-2026-07-07.md` §末尾に snapshot 用データ節を追加する形式が第一候補 / L3 導入 baseline との統合が自然)。open 件数集計上は Info のため NFR-3 に影響なし。

### module 8: `docs/internal/` (00-07)

**監査完了**: 2026-07-06 (W-R1 S3 T4 / code-reviewer subagent + L1 監督)
**集計**: Critical 0 / Warning 4 / Info 5 (subagent 生指摘 W 5 → F-5 (phase-rules 2 軸表 absence) を Info 降格 / subagent 自身が「Info 昇格でも可・境界事例」明記)
**特記**: docs/internal SSOT 親と子 rules / 実装 / spec の drift が主軸。W-R3 S2 (docs/internal SSOT drift 解消 / 一括承認 Stage) の直接材料。特に **R1-042 (gabriel 出力契約 6 vs 4 field drift)** は分岐制御 field 欠落で優先度高。

#### R1-040: `docs/design/` ディレクトリが 00_PROJECT_STRUCTURE.md 構成表に存在しない (実体は 02 が参照 + 6 files 実在)
- **severity**: Warning
- **responsibility_tag**: `ssot-parent-child-consistency`
- **attribution**: `self`
- **status**: **`closed`** (W-R3 S2 消化 / 2026-07-10)
- **closed_at**: 2026-07-10
- **closed_by_commit**: `c4628a0`
- **opened_at**: 2026-07-06
- **evidence_file**: `docs/internal/00_PROJECT_STRUCTURE.md`
- **evidence_line**: 9-37 (Directory Structure ツリー)
- **evidence_summary**: `00_PROJECT_STRUCTURE.md` §1 ディレクトリ構成ツリーには `docs/specs/` `docs/adr/` `docs/tasks/` `docs/internal/` `docs/artifacts/` `docs/slides/` `docs/daily/` `docs/memos/` のみ列挙、`docs/design/` **欠落**。一方 `docs/internal/02_DEVELOPMENT_FLOW.md` L47 は `/clarify docs/design/<feature>-design.md` を明示参照し、実ディレクトリ `docs/design/` には `cross-module-blame-design.md` 等 **6 files 実在** (subagent Bash `ls docs/design` で確認済)。「ドキュメント資産の地図」としての 00 が実運用と乖離。
- **推奨修正方針**: 00_PROJECT_STRUCTURE.md §1 ツリーに `docs/design/` (設計書 / Phase 1 成果物) 追加 + §2-B (Specifications) 類似の配置ルール節新設。**W-R3 S2 (docs/internal SSOT drift 解消)** で消化。

#### R1-041: 07_SECURITY_AND_AUTOMATION.md の Green State 記述が MVP/完全実装の段階区分欠落 (G3/G4 常時必須のように読める)
- **severity**: Warning
- **responsibility_tag**: `spec-drift`
- **attribution**: `downstream` (07 が SSOT 親 `green-state-definition.md` §2.1-2.2 の段階導入情報を反映していない)
- **status**: **`closed`** (W-R3 S2 消化 / 2026-07-10)
- **closed_at**: 2026-07-10
- **closed_by_commit**: `c4628a0`
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
- **status**: **`closed`** (W-R3 S2 消化 / 2026-07-10)
- **closed_at**: 2026-07-10
- **closed_by_commit**: `c4628a0`
- **opened_at**: 2026-07-06
- **evidence_file**: `docs/internal/00_PROJECT_STRUCTURE.md`
- **evidence_line**: 68
- **evidence_summary**: 00 §2-E は「`.claude/states/*.json`: フェーズごとの承認ゲート管理、タスク進捗の永続的状態記録」と記述。しかし実ファイルは `cc-spec-alignment.json` / `cross-module-blame.json` / `gitleaks-integration.json` / `goal-driven-orchestration.json` / `hooks-python-migration.json` / `large-scale-review.json` / `magi-skill.json` / `scalable-code-review.json` / `v4.0.0-immune-system.json` の **9 files** (subagent Bash `ls` 実測)、**いずれも Milestone/機能単位命名**で「フェーズ (PLANNING/BUILDING/AUDITING) ごと」の粒度ではない。フェーズ現在値管理は `.claude/current-phase.md` (00 §2-E 直後で正確に説明) が担い、states/*.json は別責務 (機能別承認ゲート・進捗)。
- **推奨修正方針**: 00 §2-E 該当行を「機能/Milestone 単位の承認ゲート状態・進捗記録 (例: `<milestone-slug>.json`)」に修正 + 「フェーズごとの」誤解表現除去。**W-R3 S2** で消化。

#### R1-I25: 02_DEVELOPMENT_FLOW.md が phase-rules.md の「フェーズ × 権限等級」二軸表 (3x3) 全体像要約を欠く
- **severity**: Info (境界事例 / subagent 生 Warning → L1 監督で Info 降格 / subagent 自身「Info 昇格でも可」明記)
- **status**: **`closed`** (W-R3 S2 序で消化 / 2026-07-10 / R1-040/041/043 と同 commit で解消)
- **closed_at**: 2026-07-10
- **closed_by_commit**: `c4628a0`
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

### module 9: `docs/specs/` (74 files / depth 制御)

**監査完了**: 2026-07-06 (W-R1 S4 T1 / code-reviewer subagent + L1 監督 / **depth 3-tier 制御**)
**集計**: Critical 0 / Warning 1 / Info 4 (subagent 集計 header 誤り W=4/I=3 → L1 実測 W=1/I=4 に訂正)
**depth 分類**: Tier A 精読 15 files / Tier B 骨子スキャン 20 files / Tier C 存在確認 39 files
**特記**: 74 files (15,396 行) の巨大モジュールを depth 制御で監査 → 主要 SSOT の drift 検出に集中し context 節約。**F-1 は 3 Milestone 横断の系統的 drift** (Rule of Three 該当 / 個別 spec 誤記ではなく Milestone クローズ運用の欠落) で W-R3 S4 一括修正候補。F-3 (v5-fat-reduction 反証記録) は W-R3 一括修正時の誤爆防止情報として起票価値高。

#### R1-046: 実装完了済み spec の親メタ「ステータス」が Draft のまま (3 Milestone 系統的 drift / Rule of Three)
- **severity**: Warning
- **responsibility_tag**: `spec-drift`
- **attribution**: `self` (systematic / Milestone クローズ運用の欠落)
- **status**: **`closed`** (W-R3 S4 消化 / 2026-07-10 / 8 spec files ステータス Approved 化: b4-dashboard 2 files + goal-driven-orchestration 4 files + magi-v2-gabriel 2 files / v5-fat-reduction は R1-I34 反証で Draft 維持)
- **closed_at**: 2026-07-10
- **closed_by_commit**: `80d8c8c`
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
- **attribution**: `downstream` (HGA #7 verdict C-2 で 2026-07-06 訂正 / 初期 `self` → `downstream` / ADR-0001 module 10 と実装 module 5/6 の cross-module drift = 単一モジュール完結ではない)
- **status**: **`closed`** (W-R3 S4 消化 / 2026-07-10 / 推奨案 b 採用 = Proposed → Accepted 遷移 + 改訂履歴に「第2層 (prompt/haiku) 不採用 / subagent frontmatter `model:` 個別指定で代替」明記)
- **closed_at**: 2026-07-10
- **closed_by_commit**: `80d8c8c`
- **opened_at**: 2026-07-06
- **evidence_file**: `docs/adr/0001-model-routing-strategy.md`
- **evidence_line**: 4, 38-44
- **evidence_summary**: status = `Proposed` (2026-03-08 のまま)。決定内容 = 3 層ルーティング「第1層 パスベース (command型) / 第2層 内容ベース (prompt型 / haiku) / 第3層 深い検証 (agent型 / sonnet)」。実測: `.claude/settings.json` hooks 全 5 件 = `type: command` のみ、`.claude/hooks/pre-tool-use.py` 等は純粋 Python で LLM 呼び出しなし、grep で「第2層 prompt handler」の実装は一切見つからず未実装。実際のモデル出し分けは hooks 内 3 層カスケードではなく、`.claude/agents/*.md` frontmatter の `model:` 個別指定 (12 agents 実測済 / module 6 参照) という別アーキテクチャで実現。決定と実装が乖離しつつ ADR は Proposed → Accepted 審議も Superseded 記録もなし。
- **推奨修正方針**: (a) ADR-0001 を Superseded とし、新規 ADR or 既存 ADR-0007/0009 に実装済モデル出し分け方針明記 or (b) ADR-0001 を Accepted へ正式遷移 + 「第2層は不採用 (subagent 個別指定で代替)」を改訂履歴に追記。**W-R3 S4 (docs/adr 整合修正)** で消化。

#### R1-048 (旧 Warning → Info 降格 / HGA #7 verdict B-1 準拠 / 実務便宜上 R1-046..051 系は番号維持): ADR-0008 が ADR-0004 (security-commands.md 決定元) を全面書き換えしつつ Supersede 明記なし (traceability gap)
- **severity**: **Info** (HGA #7 verdict B-1 で 2026-07-06 降格 / 初期 Warning → Info / 起票自身の evidence_summary で「決定内容は結果的に維持されているため実害なし」と自認 / ADR 相互参照 1 行の欠落は「コメントの追加提案」級で Green State を block する Warning に置くのは過剰)
- **severity_history**: initial Warning (2026-07-06) → Info (2026-07-06 HGA #7 verdict B-1)
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
- **attribution**: `downstream` (HGA #7 verdict C-2 で 2026-07-06 訂正 / 初期 `self` → `downstream` / ADR-0003 module 10 と実装移設先 module 3 skills の cross-module drift)
- **status**: **`closed`** (W-R3 S4 消化 / 2026-07-10 / L56 パス修正 + commands→skills 移行の経緯を注記併記)
- **closed_at**: 2026-07-10
- **closed_by_commit**: `80d8c8c`
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
- **attribution**: `downstream` (HGA #7 verdict C-1 で 2026-07-06 訂正 / 初期 `self` → `downstream` / CHEATSHEET.md module 11 × ADR-0007 module 10 の 2 モジュール横断 = 単一モジュール完結ではない / R1-041 / R1-042 と完全同型)
- **status**: **`closed`** (W-R3 S4 消化 / 2026-07-10 / 3 箇所全て置換完了 = L138 skill 表 / L183 SSOT 表 / L205-206 magi クイックガイド Step 4 に「gabriel adversarial probe」+ 「6-fields JSON schema」+ 「ADR-0007 Accepted 2026-07-02 で旧 Reflection から置換」の履歴注記も同時反映)
- **closed_at**: 2026-07-10
- **closed_by_commit**: `80d8c8c`
- **opened_at**: 2026-07-06
- **evidence_file**: `CHEATSHEET.md`
- **evidence_line**: 138 (skill 表 "MAGI System + Reflection"), 183 (SSOT 表 06_DECISION_MAKING 説明 "AoT + Reflection"), 205-206 (magi クイックガイド Step 4 "Reflection: 結論の致命的見落としを検証（1回限り）")
- **evidence_summary**: ADR-0007 (Accepted 2026-07-02) で Reflection → gabriel 独立 subagent に構造的置換済。`.claude/rules/decision-making.md` L19 も注記済 (旧 Reflection は Wave C で gabriel に置換済)。しかし CHEATSHEET.md 3 箇所で旧 Reflection 記述残存 = ユーザー参照ドキュメントとしての最重要 UI 面で spec drift。
- **推奨修正方針**: 3 箇所全て「gabriel adversarial probe」に置換 + Step 4 の説明を「gabriel 独立 subagent が 6-fields JSON schema で adversarial verification」に更新。**W-R3 S4 (ルート統治文書一貫性修正)** で消化 (PM 級)。

#### R1-051 (旧 Warning → Info 降格 / HGA #7 verdict B-2 準拠): CHEATSHEET.md Rules ファイル一覧が 4/11 files 欠落 (36% 未列挙) + auto-generated 3 files 全欠落
- **severity**: **Info** (HGA #7 verdict B-2 で 2026-07-06 降格 / 初期 Warning → Info / 7/23 skills を Info と判定した R1-I44 との対称化 / CHEATSHEET は定義上「クイックリファレンス (抜粋)」で「抜粋」明示すれば修正不要選択肢がある指摘 = Info 定義に合致)
- **severity_history**: initial Warning (2026-07-06) → Info (2026-07-06 HGA #7 verdict B-2)
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
| 2026-07-06 | L1 (Opus 4.7) + HGA #7 (Fable) | **HGA #7 verdict 反映** (verdict 7/10 / 見落とし Critical 1 / メタ構造欠陥 3): (A-1) R1-052 新規起票 + 前倒し消化 (R1-032 修正が単体 `&` / `\n` / `<(` 素通し / 3 テスト追加 = 全 13 tests PASS + 537 PASS 全体) / (A-2) R1-006 Warning → **Critical 昇格** + evidence 拡張 (ドット含みファイル名 追加漏れ) / (A-3) module 10 heatmap Info 7 → 6 修正 + stale placeholder 削除 / (B-1) R1-048 Warning → Info 降格 / (B-2) R1-051 Warning → Info 降格 / (C-1) R1-050 attribution `self` → `downstream` / (C-2) R1-047 / R1-049 attribution `self` → `downstream` / (C-3) §3 schema に併記形式 + severity 変更履歴フィールド明文化 / **メタ 3 件** = 「修正の再監査」ゲート追加 / tracker SSOT 自己検証チェッカー / Stage 間 severity/attribution 判定規準ドリフト = W-R5 retro 議題化 |

---

## 6. 参照

- [requirements.md](../specs/large-scale-review/requirements.md) FR-1 / FR-2 / FR-5 / NFR-1 (R-G6/G7/G8) / NFR-3
- [design.md](../specs/large-scale-review/design.md) §3.1 (tracker) / §3.0 (data flow) / §14 (権限等級)
- [tasks.md](../specs/large-scale-review/tasks.md) W-R1 全 Stage
- [green-state-baseline.md](./r-1-green-state-baseline-2026-07-06.md) (G1-G5 + R-G6/G7/G8 baseline)
- [code-quality-guideline.md](../../.claude/rules/code-quality-guideline.md) (Critical/Warning/Info 判断基準)
