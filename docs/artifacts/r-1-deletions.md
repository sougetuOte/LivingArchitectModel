# R-1 削除履歴

**Milestone**: R-1 (大規模レビュー & リファクタリング)
**単一 SSOT**: 本ファイル (`docs/artifacts/r-1-deletions.md`)
**生成日**: 2026-07-13 (W-R4 S3-T3)
**関連 tracker**: `docs/artifacts/r-1-audit-tracker.md` §0.12

---

## 1. 削除実施履歴 (W-R4 S3 / 2026-07-13)

FR-4 の 3 条件 AND (grep 参照ゼロ / Python import ゼロ / 90 日未使用) を満たした skill 8 件を削除。

| # | 対象 | lines | last_commit | 削除理由 | 根拠 |
|:-:|:---|:-:|:---|:---|:---|
| 1 | `.claude/skills/auditing/SKILL.md` | 143 | 2026-05-29 | 30日窓 hit=0 + last_commit >40d | usage-baseline §5 #1 / tracker §0.10 |
| 2 | `.claude/skills/clarify/SKILL.md` | 178 | 2026-05-28 | 同上 (>40d) | usage-baseline §5 #2 |
| 3 | `.claude/skills/pattern-review/SKILL.md` | 79 | 2026-05-29 | 同上 (>40d) | usage-baseline §5 #4 |
| 4 | `.claude/skills/planning/SKILL.md` | 115 | 2026-05-29 | 同上 (>40d) | usage-baseline §5 #5 |
| 5 | `.claude/skills/project-status/SKILL.md` | 90 | 2026-05-29 | 同上 (>40d) | usage-baseline §5 #6 |
| 6 | `.claude/skills/skill-creator/SKILL.md` | 170 | 2026-05-28 | 同上 (>40d) | usage-baseline §5 #7 |
| 7 | `.claude/skills/ui-design-guide/SKILL.md` | 95 | 2026-05-28 | 同上 (>40d) | usage-baseline §5 #8 |
| 8 | `.claude/skills/wave-plan/SKILL.md` | 112 | 2026-05-29 | 同上 (>40d) | usage-baseline §5 #9 |

**合計**: 8 files / 982 lines

**除外**: `.claude/skills/lam-orchestrate/SKILL.md` (usage-baseline §5 #3 で delete_candidate 判定だが tier=orchestrator 保護で除外 / `docs/specs/large-scale-review/requirements.md` §42 / 中核制御フロー保護)

**削除コマンド** (L1 直 / 束ね実施):
```bash
git rm .claude/skills/auditing/SKILL.md \
       .claude/skills/clarify/SKILL.md \
       .claude/skills/pattern-review/SKILL.md \
       .claude/skills/planning/SKILL.md \
       .claude/skills/project-status/SKILL.md \
       .claude/skills/skill-creator/SKILL.md \
       .claude/skills/ui-design-guide/SKILL.md \
       .claude/skills/wave-plan/SKILL.md
```

**commit**: 本 ship で実施 (git log 参照)

---

## 2. 参照書き換え履歴 (CAT-A 82 hits / 16 files)

上記 8 skill 削除に伴い、repo 全域の grep hit を 5 カテゴリ精査 (L2 Sonnet grep triage) し、**CAT-A (実行指示 82 hits)** を書き換え実施 (L2 Sonnet rewriter / 別委譲)。**CAT-B (歴史記述 153 hits) は保持** (retro / rename migration / spec history / test fixture 等)。

### 精査集計 (L2 Sonnet grep triage / 前段)

| category | hits | 意味 | 処置 |
|:---|-:|:---|:---|
| CAT-A | 82 | 実行指示 (slash command / template array / cross-skill 案内) | 書き換え |
| CAT-B | 153 | 歴史記述 (retro / rename 履歴 / phase 名文脈) | 保持 |
| CAT-C | 19 | SKILL.md 自身の self-reference | 自動消滅 (削除で解決) |
| CAT-D | 0 | settings.json / allowlist | 対象なし |
| CAT-E | 1 | L1 判断要 (`hga-summoning.md:155`) | §3 で処置 |

boundary_deviations: 2 (scratchpad 内 tmp file / repo 影響なし)

### 書き換え対象 16 files (81 hits / 45 unique edits)

`.claude/skills/project-status/SKILL.md` (1 hit) は削除対象なので自動消滅で除外 → 実質 16 files / 81 hits。

| # | file | hits | 主要処置内容 |
|:-:|:---|:-:|:---|
| 1 | `.claude/skills/init-harness/SKILL.md` | 21 | harness.json テンプレ配列から 5 skill 除去 / quick-start / quick-reference 表 4 行削除 / description の phase 名大文字化 / template placeholder 手動記入化 |
| 2 | `CHEATSHEET.md` | 17 | フェーズコマンド表・スキル表・ワークフロー表から該当行削除 / `/clarify` クイックガイド section 全削除 |
| 3 | `README.md` | 8 | フェーズコマンド表・補助コマンド section 削除 / オンボーディング文言を phase 名表記に置換 |
| 4 | `.claude/rules/phase-rules.md` | 5 | Example Mapping 併用先変更 / 審査コマンド行削除 / phase 警告テンプレの skill 名を phase 名で書き直し |
| 5 | `docs/internal/02_DEVELOPMENT_FLOW.md` | 5 | 承認ゲート参照を phase 名表記に置換 / §文書精緻化 (`/clarify`) section 全削除 |
| 6 | `.claude/skills/full-review/SKILL.md` | 4 | `§/auditing との使い分け` を `§AUDITING フェーズとの使い分け` に書き直し / WebFetch fallback 文言を phase 名表記に置換 |
| 7 | `.claude/skills/building/SKILL.md` | 3 | `/planning` `/pattern-review` `/auditing` を phase 名 or 生存 skill (`/retro` Step 2.5) に置換 |
| 8 | `docs/internal/00_PROJECT_STRUCTURE.md` | 3 | commands/ 一覧から `/wave-plan` 除去 / current-phase.md 更新機構を手動更新+`/building` 表記に修正 |
| 9 | `docs/specs/magi-skill-spec.md` | 3 | Problem Statement / FR-M6 / 受け入れ基準表の 3 箇所から `wave-plan` 関連記述除去 |
| 10 | `CLAUDE.md` | 1 (2 hits collapse) | Execution Modes 表から `/planning` `/auditing` 行削除 (**PM 級 / S3-T2c 事前承認済**) |
| 11 | `.claude/current-phase.md` | 2 | 更新タイミング一覧の `/planning` `/auditing` を手動更新表記に置換 |
| 12 | `.claude/rules/planning-quality-guideline.md` | 2 | 併用スキル列挙・Example Mapping 見出しから `/clarify` 除去 |
| 13 | `docs/internal/01_REQUIREMENT_MANAGEMENT.md` | 2 | Clarification 手順・DoR チェックリストの `/clarify` を手動検出手順表記に置換 |
| 14 | `docs/specs/evaluation-kpi.md` | 1 | §7 見出しを「廃止済 skill 向け未実装機能案・保留」注記付きに書き換え (KPI K1-K5 定義本体は仕様知識散逸防止で保持 / pattern-uncertain L1 承認済) |
| 15 | `.claude/agents/tdd-developer.md` | 1 | エスカレーション先を `/planning` から PLANNING フェーズ差し戻し表記に置換 |
| 16 | `docs/specs/cc-spec-alignment/diff-skills-subagents.md` | 1 | 採否意思決定の場を `/planning` から PLANNING フェーズ表記に置換 |

**Sonnet rewriter 実測**: 45 unique edits / boundary_deviations = [] / unverified = [] / pattern-uncertain 2 件 (CHEATSHEET.md L202 phase 名 no-op = 妥当 / evaluation-kpi.md §7 KPI 定義保持 = 妥当 / 両方 L1 承認)

### 書き換え原則 6 パターン

| ID | パターン | 処置 |
|:-:|:---|:---|
| P1 | コマンド表行 (`\| /skill \| ... \|`) | 行削除 |
| P2 | Slash command 呼び出し (`/skill を実行`) | 削除 or Phase 名で置換 |
| P3 | Template array literal / config 内 skill 名 | 配列から skill 名除去 |
| P4 | Skill 併用言及 (`/skill と併用可`) | 削除 or 「(廃止済)」注記 |
| P5 | Cross-skill 案内 (他 SKILL.md 内の `/skill で〜してください`) | Phase 名で書き直し |
| P6 | Section 見出し (`## /skill クイックガイド`) | section 全削除 |

---

## 3. CAT-E 処置 (1 hits / L1 SE 級)

**`.claude/rules/hga-summoning.md:155`** (R1-016 incident 例で `skill-creator/SKILL.md` を実 path 引用):

**処置**: `(R-1 W-R4 S3 で削除済 / docs/artifacts/r-1-deletions.md 参照)` 注記を追記
- **理由**: incident 例としての意味 (subagent がローカル SKILL.md を公式スキーマと誤認する癖の実例) を保持しつつ、削除後 stale prose にならないよう明示化
- **第 0 原則との整合**: 可逆性 = 有 (git revert 可) / 復旧コスト = 低 (1 行差分) / 確認コスト = S3-T2c 一括承認内で吸収済

---

## 4. 権限等級

本ファイル: SE (`docs/artifacts/` 配下 / 非 SSOT)

`.claude/rules/hga-summoning.md` の Edit: PM (S3-T2c 一括宣言で事前承認取得済)

---

## 5. 参照

- `docs/artifacts/r-1-usage-baseline-2026-07-11.md` §5 (delete_candidate 9 件 / lam-orchestrate 除外根拠)
- `docs/artifacts/r-1-audit-tracker.md` §0.10 (defer 判断根拠) / §0.12 (本削除の実施記録)
- `docs/specs/large-scale-review/requirements.md` FR-4 (3 条件 AND 定義) / §42 (orchestrator 保護)
- `docs/specs/large-scale-review/tasks.md` §5 W-R4 S3 (Task 定義)
- `.claude/rules/model-delegation-prompting.md` §2 (Sonnet 委譲品質基準)
- Sonnet grep triage 出力: `~/.claude/projects/<>/tool-results/toolu_01EEasvymhGSZEeiYNG6bVWE.json` (ローカル / gitignore 対象外だが sensitive 情報なし)
- Sonnet rewriter 完了報告: 本セッション conversation transcript
