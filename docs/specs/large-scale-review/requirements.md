# R-1 Milestone Requirements: 大規模レビュー & リファクタリング

## メタ情報

| 項目 | 内容 |
|:-----|:-----|
| Milestone | R-1 (Refactoring シリーズ 初回) |
| ステータス | **Approved** (2026-07-05 / MAGI 4 Atom + gabriel 2 round + HGA #5 + spec-critic 統合) |
| 作成日 | 2026-07-05 |
| 更新日 | 2026-07-05 |
| 起源 | B-5 Milestone COMPLETE 直後の独立レビュー要請 (ユーザー指示 2026-07-05) |
| SSOT | 本ファイル |
| 意思決定記録 | `docs/artifacts/2026-07-05-magi-r1-planning.md` (MAGI 4 Atom + gabriel 2 round + HGA #5) |
| 計画書 | `docs/artifacts/future-large-scale-review-plan-2026-07-05.md` |
| 関連 ADR | [ADR-0005](../../adr/0005-thin-harness-autonomous-governance.md) / [ADR-0007](../../adr/0007-magi-v2-gabriel-integration.md) / [ADR-0009](../../adr/0009-hga-fable-summoning.md) |

---

## 1. 概要

### 1.1 目的

B-5 Milestone を通じて積み上げた資産 (dashboard / MAGI v2 / HGA / TDD 内省 v2 / 3.5 層委譲 / AutoMode 等) が相互干渉なく機能し、**恒久資産としての品質基準** を満たすことを、独立レビュー + リファクタリングによって検証する。

### 1.2 ユーザーストーリー

```
As a LAM プロジェクト運用者 (L1 統括 = Living Architect),
I want B-5 期累積資産の凝集度 / 結合度 / 仕様ドリフト / 規律相互矛盾 を検出し、
   moderate 破壊的変更で再構造化する Milestone,
So that R-2 以降の新規機能開発を健全な基盤の上で始められる.
```

### 1.3 スコープ

**含む (11 モジュール分類 / MAGI + gabriel + HGA #5 統合)**:

| # | モジュール | 監査対象 | 備考 |
|:-:|:----------|:---------|:-----|
| 1 | `.claude/scripts/dashboard/` | Wave 2-8 累積 (builder.py, parsers/, merger.py 等) | 424 テスト保護下 |
| 2 | `.claude/scripts/` (dashboard 外) | gd_guard/gd_state/gd_loop/magi_dispatch/hga_usage/scan_nfr_refs/distill-lessons | テスト保護薄 |
| 3 | `.claude/skills/` | **23 SKILL.md** (実測) | `tier=orchestrator / utility` タグ付与必須 (orchestrator 5 件 = magi/full-review/lam-orchestrate/autonomous/goal-driven は R-G7 強度) |
| 4 | `.claude/tests/` | dashboard/ + wave_c/ + hooks/ 等 | 487 PASS + 14 SKIP 維持 |
| 5 | `.claude/hooks/` + `.claude/settings*.json` | hooks + settings 配線 (併合改称) | pre-tool-use / post-tool-use / セッション PM edit cache 等 |
| 6 | `.claude/agents/` | **12 件** (実測 / repo 内 / plugin 由来は out of scope) | gabriel / goal-driven-* / tdd-developer / doc-writer 等 |
| 7 | `.claude/rules/` | 11 files + `auto-generated/` (rule-001.md 承認済) | 相互矛盾検出主戦場 |
| 8 | `docs/internal/` | 00-07 憲法 SSOT | 規範文の重複ペア検査対象 |
| 9 | `docs/specs/` | b4-dashboard/, magi-v2-gabriel/, v5-fat-reduction/, cc-spec-alignment/, tdd-introspection-v2/ 等 | 仕様ドリフト検出 |
| 10 | `docs/adr/` | 0005-0009 の 5 件 | 決定記録の一貫性 |
| 11 | **`CLAUDE.md` + `CHEATSHEET.md`** | **ルート統治文書** (NEW / HGA #5 Fable 追加) | blast radius 最大 / 全モジュール参照ハブ |

**含まない (Non-Goals / HGA #5 Fable 明記)**:

- `SESSION_STATE.md` (gitignore 済揮発資産 / セッション断絶時に再構築される)
- `docs/artifacts/` 配下 (歴史記録 / retro / MAGI 合議記録 / 実測メモ 等の**不変監査対象**)
- 新機能開発 (R-1 は refactor 専用 / 機能追加は B-6 以降)
- 破壊的変更のうち後方互換破壊 (`.claude/agents/gabriel.md` の 6 フィールド JSON 契約等の I/O 契約変更は禁止)
- plugin 由来リソース (repo 外の agent / skill / MCP 由来) の削除・改名

**モジュール分類の相互排他性** (spec-critic 見えない前提): 11 モジュールは **ファイルは 1 モジュールにのみ属する** ことを前提とする。境界曖昧ケース (例: `.claude/settings*.json` が rules を参照する記述) は `code-quality-guideline.md` §モジュール間帰責判断 のフローチャートに従い upstream/downstream を判定する (issue の帰責先タグで区別)。

**skills 削除の位置付け** (spec-critic 見えない前提): `.claude/skills/` の `tier=utility` (非オーケストレータ) 側で未使用 SKILL.md が判明した場合、FR-4 の 3 条件 AND (grep 0 + import 0 + 90 日未使用) を満たせば削除対象とする。`tier=orchestrator` (magi / full-review / lam-orchestrate / autonomous / goal-driven) 側の SKILL.md は削除対象外 (中核制御フローのため / R-1 では改善のみ)。

---

## 2. 機能要求 (FR)

FR は MAGI 4 Atom 結論 (A1-A4) + gabriel 2 round refinement + HGA #5 Fable 追加 5 項目 (F1-F5) から導出する。RFC 2119 準拠。

### FR-1: 監査スコープ形式 = hybrid (MUST)

**説明**: W-R1 で widescan 監査 (全 11 モジュール一括問題リスト作成)、W-R2〜W-R4 で layered 実装、W-R5 で最終監査。

**W-R1 は read-only 前提** (spec-critic 見えない前提): W-R1 は問題リスト作成のみを目的とし、実装変更は行わない。W-R1 中に誤って実装変更が混入した場合は revert (git reset) 対象。実装は W-R2 以降の layered Wave で行う。

**受け入れ条件**:
- [ ] W-R1 監査アウトプットが 11 モジュール全てをカバーしている
- [ ] 各 issue に **重要度 (Critical / Warning / Info)** が付与されている (`code-quality-guideline.md` §重要度分類 準拠)
- [ ] 各 issue に **帰責先 (upstream / downstream / spec_ambiguity / unknown)** が付与されている (`code-quality-guideline.md` §モジュール間帰責判断 準拠)
- [ ] W-R1 期の全 commit が read-only (監査アウトプット追記 + tracker 起票のみ / 実装変更ゼロ)

**優先度**: MUST

### FR-2: 監査アウトプット = tracker (MUST)

**説明**: 監査結果は `docs/artifacts/r-1-audit-tracker.md` (Markdown table) として単一 SSOT に集約する。

**受け入れ条件**:
- [ ] tracker が Markdown table 形式で存在する
- [ ] 各 issue に `id / module / summary / severity / responsibility / status / opened_at / closed_at / closed_by_commit` の列が定義される
- [ ] `status` 列は `open / wip / closed / deferred` の 4 値
- [ ] `deferred` は理由付き必須 (`green-state-definition.md` §4 準拠)
- [ ] **`wip` は Stage 内一時状態** (spec-critic Warning W3): 特定 Stage 内で作業中の issue に付与。**W-R5 (最終監査) 時点で `wip` 残存は Green State 不成立** (R-G6 tracker 全閉塞違反 / `wip` を放置したまま Milestone COMPLETE にはできない)

**tracker 破損時の復旧手順 (spec-critic Warning W5)**:

tracker ファイル (`docs/artifacts/r-1-audit-tracker.md`) が誤削除・破損した場合:
1. まず `git log --all --oneline -- docs/artifacts/r-1-audit-tracker.md` で最新の生存 commit を特定
2. `git show <commit>:docs/artifacts/r-1-audit-tracker.md > docs/artifacts/r-1-audit-tracker.md` で復元
3. 復元後、最新 ship 以降に closed / deferred / opened された issue を該当 commit の commit message (`closed issue IDs` 列挙 / FR-1 準拠) から手動再構築
4. 復旧完了を SESSION_STATE.md に記録

**優先度**: MUST

### FR-3: 実施形態 = in-place (MUST)

**説明**: master 直改修。R-1 期を通じて `master` に in-place で ship + push を継続。branch/worktree は使用しない。

**受け入れ条件**:
- [ ] R-1 期の全 commit が `master` 直コミット
- [ ] 各 Stage 末で ship (commit + push) + Green State 判定 が完了している
- [ ] Stage 冒頭で `python -m pytest .claude/tests/dashboard/test_session_state_parser.py::test_parse_real_session_state_contains_b5_milestone .claude/tests/dashboard/test_session_state_parser.py::test_parse_real_session_state_contains_wave` の smoke test が PASS する (rule-001.md 発動)

**優先度**: MUST

### FR-4: 破壊的変更許容範囲 = moderate (MUST)

**説明**: 未使用検知済み agent/rule/hook は直接削除許容。ただし削除前に **PM 級承認** + **削除履歴 artifact** への記録 + **3 条件 AND** の充足を必須とする。

**受け入れ条件**:
- [ ] 削除実施前に PM 級承認取得済
- [ ] 削除履歴が `docs/artifacts/r-1-deletions.md` に記録されている
- [ ] 削除対象は以下 3 条件を **全て** 満たしている (AND):
  - `grep` で参照ゼロ
  - Python `import` 参照ゼロ
  - 判定データソース (FR-F4) 上で 90 日以上未使用
- [ ] 削除実施と同時に tracker の該当 issue が `closed` に更新されている

**FR-F4 データソース確定失敗時の fallback (spec-critic Critical C1)**:

FR-F4 で判定データソースが W-R4 着手までに確定しなかった場合:
1. W-R4 の **削除タスク全体を `deferred` に降格** (tracker 該当 issue に `deferred_reason='FR-F4 data source undetermined'` 付与)
2. W-R4 は削除以外の整理タスク (`.claude/agent-memory/` 更新パス / hook 重複統合 / 責務タグ整理 等) のみで完了
3. deferred 分は R-2 以降で判定データソース確定後に再着手
4. **3 条件 AND の 2 条件 OR への縮退は禁止** (`grep` + `import` のみでの削除は不可)

**優先度**: MUST

### FR-5: 監査粒度 = モジュール単位 + 責務タグ (MUST)

**説明**: W-R1 監査アウトプットはモジュール単位でグルーピングし、各 issue に責務タグを付与する。

**受け入れ条件**:
- [ ] tracker は 11 モジュールごとにセクション化 (§5.1 〜 §5.11)
- [ ] 各 issue に責務タグが付与されている (SRP / DRY / 凝集度 / 認知複雑度 / 仕様ドリフト / セキュリティ / drift / dead_code / duplication のいずれか)
- [ ] tracker 冒頭に **モジュール別問題数ヒートマップ** (Markdown table / モジュール × 重要度) が存在する

**優先度**: MUST

### FR-6: HGA スケジュール = 3 回構成 (SHOULD)

**説明**: R-1 期の HGA 型 Fable 召喚は以下 3 回に固定する。カレンダー駆動ではなくゲート駆動。

**受け入れ条件** (spec-critic Critical 1 対応: HGA #6 design review 追加によるリナンバー同期):
- [ ] HGA #5 は 2026-07-05 に消化済 (本 requirements 起稿の crux 分岐)
- [ ] **HGA #6 は 2026-07-05 に消化済** (design.md adversarial review / 追加召喚 / SHOULD 逸脱 = retro 集計対象)
- [ ] **HGA #7 (旧 #6)** は 2026-07-07 以前に必須消化 (第一候補: W-R1 監査結果妥当性検証 / スライド時: 監査 rubric 事前検証)
- [ ] **HGA #8 (旧 #7)** は W-R3 (規律 SSOT 統合設計時) に発火 (7/8 以降クレジット従量 / #4 型パターン準拠で $2-3 圏想定)
- [ ] W-R5 は HGA 召喚しない (検証は gabriel の実質貢献領域 / gabriel 実運用初日 refute 2/2 で実証済)
- [ ] 全召喚を `docs/artifacts/hga-summon-log.md` に追記する

**HGA #7 (旧 #6) 期限内消化失敗時の 3 段 fallback (spec-critic Critical C5 + Critical 1 リナンバー)**:

1. **Level 1**: 7/7 中に W-R1 完成済分の **部分検証召喚に切替** (対象スライド / 完成済モジュールの範囲で監査結果検証 / 6 モジュール以上完了下限)
2. **Level 2**: Level 1 不可なら W-R3 直前 (7/8 以降 / 従量) に **#8 (旧 #7) と統合召喚** (対象: SSOT 統合 + W-R1 監査事後検証の合わせ技 / 想定 $4-6)
3. **Level 3**: Level 2 も不可なら **A2/HGA スケジュール自体を再 MAGI 合議** (retry_count=0 リセット可能 / R-1 継続可否判断)

**優先度**: SHOULD

### FR-7: MAGI + gabriel の積極活用 (SHOULD)

**説明**: R-1 期の重要判断 (Wave 分割 / 削除判定 / SSOT 統合等) は MAGI + gabriel で構造化する。

**受け入れ条件**:
- [ ] 判断ポイント 2+ / 影響レイヤー 3+ / 選択肢 3+ のいずれかに該当する判断で MAGI を発火
- [ ] AoT 適用時は gabriel probe を必ず発火 (opt-out は L1 明示宣言時のみ / 理由 1 文以上記録必須)
- [ ] gabriel 発火は `.claude/gabriel-metrics.log` に JSONL 記録する
- [ ] opt-out 記録先は `gabriel-metrics.log` の `opt_out` フィールド (既定スキーマ) + MAGI anchor `docs/artifacts/YYYY-MM-DD-magi-*.md` の両方 (W-R5 監査で機械的検証可能に / spec-critic Warning W1)
- [ ] **同一議題で gabriel が 3 回連続 refute した場合は自動人間エスカレーション** (retry_count=1 上限を超える連続 refute は運用継続可否をユーザーが判断 / spec-critic Warning W6)

**優先度**: SHOULD

### FR-F0: R-1 開始時 Green State 状態確認 (MUST / spec-critic Critical C4 追加)

**説明**: R-1 開始時点で `green-state-definition.md` の G1-G5 が完全実装済であることを確認する。未完全実装ならば R-1 は開始 blocker とする。

**受け入れ条件**:
- [ ] W-R1 冒頭で `green-state-definition.md` の G1-G5 各条件の実装完了度を確認するタスクを実施
- [ ] G1 (pytest 全 PASS 維持) は本日 2026-07-05 時点で 487 PASS + 14 SKIP により確認済 (SESSION_STATE.md HEAD `93032da`)
- [ ] G2/G3/G4/G5 の実装完全性を W-R1 開始時に文書化 (`docs/artifacts/r-1-green-state-baseline-YYYY-MM-DD.md`)
- [ ] G3/G4 が段階導入途上と判明した場合、R-1 スコープ内で完全実装するか R-1 blocker として PM 級エスカレーションするかを判断

**優先度**: MUST (R-1 開始条件)

### FR-F1: W-R1 冒頭 インベントリ再生成 (MUST / HGA #5 Fable 追加)

**説明**: 記憶・ブリーフ由来の件数を信用せず、ファイルシステムから 11 モジュール全件を再生成する。

**受け入れ条件**:
- [ ] W-R1 の最初のタスクとして inventory 再生成が定義されている
- [ ] 各モジュールの実在ファイル数が確定している (例: SKILL.md 実測 23 件 / agents 実測 12 件 の drift 検出済)
- [ ] plugin 由来リソース (repo 外) は `out_of_scope` タグ付きで inventory から除外される

**優先度**: MUST

### FR-F2: agent-memory の扱い + 改名操作 (MUST / HGA #5 Fable 追加 / spec-critic Warning W4 対応 α)

**説明**: `.claude/agent-memory/` は現 11 モジュール分類に含まれないが、agent 削除・改名時に古い memory が改名後 agent を誤誘導するリスクを持つ。W-R4 に無効化・更新パス タスクを設ける。

**改名操作の位置付け (spec-critic Warning W4 対応)**: agent/rule/hook の **改名も削除同等の破壊的変更カテゴリ** として扱う。改名は「旧名の削除 + 新名の追加」と等価であるため、A3 の 3 条件 AND (FR-4) を **改名にも適用する** (grep 参照ゼロ + import 参照ゼロ + 90 日以上未使用の後に改名実施可)。

**受け入れ条件**:
- [ ] W-R4 の tasks.md に「agent-memory 無効化・更新」タスクが存在する
- [ ] agent 削除 (FR-4) 時に対応する agent-memory エントリーが同時に無効化 or 削除される
- [ ] agent 改名時に agent-memory の参照パスが更新される
- [ ] 改名実施は FR-4 と同じ 3 条件 AND を満たすこと (改名前の旧名について grep 0 + import 0 + 90 日未使用)
- [ ] 改名実施は PM 級承認要 (FR-4 準拠)
- [ ] 改名履歴は `docs/artifacts/r-1-renames.md` (削除履歴と別ファイル) に記録

**優先度**: MUST

### FR-F3: prose 資産の smoke test (R-G7 連動 / MUST / HGA #5 Fable 追加)

**説明**: W-R3 (規律 SSOT 統合) / W-R4 (hooks/agents 整理) の対象は prose 資産 (rules/skills/agents/internal/adr) であり、pytest 保護下にない。R-G7 (参照解決 = 0 drift) を Stage 末 smoke test に組み込むことで、A2 (in-place) 前提の破綻を防ぐ。

**受け入れ条件**:
- [ ] W-R3 の各 Stage 末で「SKILL.md / rules 参照解決 = 0 drift」チェック (grep ベース) が自動実行される
- [ ] W-R4 の各 Stage 末で同上のチェックが実行される
- [ ] チェック失敗時は Stage 完了とみなさない (Green State 不成立)

**grep パターン設計 (spec-critic Warning W8 / §11 で具体化)**:

- **W-R3 用パターン** (rules 側監査): rules 内の相互参照 (例: ``.claude/rules/*.md`` 内の ``` `X.md` ``` / ``` ${X-rule-name} ``` / ``` See: X ```) が実在ファイルに解決するかを検査
- **W-R4 用パターン** (agents/hooks 側監査): SKILL.md / agents/*.md の frontmatter tools/subagent_type 参照 + rules 側からの agent 呼び出し記述が実在エージェント名に解決するかを検査
- **共通**: verdict フィールド名 (`verdict / severity / affected_atoms / reasoning / recommended_action / confidence`) が gabriel 契約と一致するかを検査
- 具体的 grep コマンドは design.md §5 (§11 未決定事項) で確定

**優先度**: MUST

### FR-F4: A3 削除判定データソース確定 (MUST / HGA #5 Fable 追加 / HGA #6 Fable 再定義 2026-07-05)

**説明**: FR-4 の削除判定に用いるデータソースを明文化する。**HGA #6 Fable 実測に基づき「90 日窓」から「実運用保持窓 + リソース種別別検出パターン」に再定義**。

**保持窓の再定義 (HGA #6 Crux 1-b)**:
- **git log** 側: 最終 touch commit の日付 (filter なし / 過去全期間対象)
- **session log** 側: **直近 30 日窓** (Claude Code CLI の `cleanupPeriodDays` 既定値 30 日 / 実測: 最古 jsonl `2026-06-06` = 本日 2026-07-05 から 30 日前)
- 上記の非対称 (git = 全期間 / session = 30 日) は保持窓の実態に沿った不可避の縮退 (2 条件 OR 縮退禁止の趣旨は逸脱していない)

**リソース種別別検出パターン (HGA #6 Crux 5-1)**:

| リソース種別 | 使用検出パターン | 根拠 |
|:-----------|:---------------|:-----|
| **agents (`.claude/agents/*.md`)** | session log (jsonl) 内で `subagent_type=<agent_name>` を grep | Task/Agent tool 経由起動時のフィールド |
| **skills (`.claude/skills/**/SKILL.md`)** | session log (jsonl) 内で Skill 起動記録 (フィールド名は W-R4 S1 で実 jsonl 1 本開いて確定 / **要検証の仮定**) | Skill tool 経由起動 / subagent_type ではない |
| **hooks (`.claude/hooks/*.py`)** | `.claude/settings*.json` の hook 配線に該当 hook が登録されているか + 直近 30 日の実行痕跡 (PostToolUse log 等) | hooks は subagent ではない |

**受け入れ条件**:
- [ ] W-R4 S1 で判定データソース (git log + session log + リソース種別別パターン) が確定している
- [ ] 確定したデータソースが `docs/specs/large-scale-review/design.md` に明記されている
- [ ] データソース確定なしに FR-4 削除実施は行わない
- [ ] skills 側の Skill 起動記録フィールド名を W-R4 S1 で実 jsonl 開示し確定 (要検証の仮定の解消)
- [ ] 3 条件 AND の第 3 条件は「git log 全期間 filter なし + session log 30 日窓 + リソース種別別パターン」で構成 (**旧 90 日窓は放棄**)

**優先度**: MUST

### FR-F5: rule-001 を tracker 認識に拡張 (SHOULD / HGA #5 Fable 追加)

**説明**: `rule-001.md` (SESSION_STATE.md fallback 保守) は tracker 存在を知らない。R-1 期のセッション断絶時の復旧手順に tracker 状態確認を追加する。

**受け入れ条件**:
- [ ] `rule-001.md` を編集し、SESSION_STATE.md 復旧チェックリストに `docs/artifacts/r-1-audit-tracker.md` 状態確認の 1 行を追加
- [ ] または `rule-002.md` として tracker 復旧手順を独立ルール化 (PM 級承認要)

**優先度**: SHOULD

### FR-8: Wave 数固定 (MUST)

**説明**: R-1 は **5 Wave (W-R1 〜 W-R5) 固定**。Wave 追加は Milestone 再計画 = PM 級承認要 (`terminology.md` ペア 5 準拠 / クローズ済 Milestone の再開禁止と同思想)。

**受け入れ条件**:
- [ ] R-1 期を通じて Wave 数 5 が維持される
- [ ] Wave 途中で湧いた項目は無条件で tracker に `deferred` として記録される
- [ ] `deferred` から Wave 内 `open` への昇格は「in-scope モジュールの Green State 条件 (Critical / Warning) を block する場合」のみ (二値・機械判定 / MAGI 呼ぶ余地なし)

**優先度**: MUST

---

## 3. 非機能要求 (NFR)

### NFR-1: R-1 Green State 追加 3 二値条件 (MUST / HGA #5 Fable 追加 / spec-critic Critical C2/C3 補強)

**説明**: `green-state-definition.md` の G1-G5 に加え、R-1 完了条件として以下 3 条件を追加する。連続量指標 (認知複雑度平均 / 結合度低下率) は Green State ゲートには入れず、W-R1 で観測値として記録するのみとする (R-2 以降の比較材料)。

**受け入れ条件**:
- [ ] **R-G6: tracker 全閉塞** — `r-1-audit-tracker.md` の全 issue が `closed` または `deferred` (理由付き)。`wip` 残存は不可 (FR-2 W-R5 時点扱い準拠)
- [ ] **R-G7: SKILL.md / rules 参照解決 = 0 drift** (spec-critic Critical C2 補強): 以下 3 層防御で判定
  - **層 1 (静的 grep)**: 23 SKILL.md + rules が参照するパス・rule 名・verdict フィールド名が grep で明白参照として実在解決する
  - **層 2 (手動監査 / W-R3)**: 変数展開・間接参照 (例: `f".claude/rules/{rule_name}.md"` / `${VAR}` 展開) は手動で監査
  - **層 3 (パターン列挙 unittest)**: 層 1/2 でカバー困難な参照は unittest 相当の逐条列挙 (`.claude/tests/rules/test_reference_resolution.py` 相当) で検査
  - **false negative の扱い**: 層 1-3 のいずれかで false negative が判明した場合、tracker に「open drift」として新規起票 (Milestone COMPLETE 前に closed 化必須)
- [ ] **R-G8: Python モジュール循環依存 = 0** (spec-critic Critical C3 補強): dashboard / scripts の import グラフで循環ゼロ
  - **W-R1 冒頭で現状値を計測** (FR-F1 連動 / `.claude/scripts/` + `.claude/hooks/` + `.claude/tests/` の import グラフを `pydeps` または相当ツールで生成)
  - **既存循環依存があった場合**: R-1 スコープ内解消対象 (Critical issue として tracker 起票)
  - **解消不可判明時の緩和**: R-1 Wave 内で解消不可能と確定した場合 (例: API 契約由来 / 破壊的変更なしに解消不可)、R-G8 は「= 0 for R-1 scope in-scope module」に緩和。既存分は R-2 以降に deferred (deferred_reason 必須 / green-state-definition.md §4 準拠)

**優先度**: MUST (R-1 Milestone COMPLETE の必要条件)

### NFR-2: pytest 全 PASS 維持 (MUST / G1 準拠)

**説明**: R-1 期を通じて 487 PASS + 14 SKIP の状態を退行なく維持する。

**受け入れ条件**:
- [ ] 各 Stage 末で `pytest .claude/tests/` が 487 PASS + 14 SKIP 相当を維持
- [ ] テスト追加は許容 (487 → N with N >= 487)
- [ ] テスト削除は Wave 内で PM 級承認要

**優先度**: MUST

### NFR-3: 監査アウトプットの認知負荷管理 (SHOULD / spec-critic Warning W2)

**説明**: W-R1 監査 issue 数が過多になった場合の認知負荷を管理する。**issue 数の見積は本 requirements 段階では未確定** (W-R1 冒頭 inventory 再生成 + 監査完了時に実測)。

**受け入れ条件**:
- [ ] tracker 冒頭にモジュール別問題数ヒートマップ (11 モジュール × 3 重要度 = 33 セル) を配置
- [ ] W-R1 監査完了時点で **Critical 件数閾値を実測に基づき確定** (初期閾値 = 10 件は暫定 / W-R1 実測後に閾値見直しを含む)
- [ ] Critical 件数が確定閾値を超える場合、W-R1 で優先順位付けタスクを追加
- [ ] Info 件数は集計のみ (Green State には影響しない)

**優先度**: SHOULD

### NFR-4: gabriel メトリクス月次集計 (SHOULD)

**説明**: R-1 期の全 gabriel 発火を `.claude/gabriel-metrics.log` に記録し、月次 retro で集計する。

**受け入れ条件**:
- [ ] 全 MAGI 合議で gabriel 発火が JSONL 追記される (`gabriel-metrics-environment-2026-07-05.md` §2 スキーマ準拠)
- [ ] R-1 完了時に retro で gabriel 起動回数 / refute 率 / inconclusive 率 / 平均経過時間 / re-magi 発動数 を集計
- [ ] refute 率 20% 超なら gabriel rubric 見直し議題化 / 5% 未満なら AoT トリガー閾値見直し議題化

**優先度**: SHOULD

### NFR-5: HGA envelope 監視 (SHOULD)

**説明**: R-1 期の HGA 召喚を envelope 内に収める。

**受け入れ条件**:
- [ ] 実 $ envelope: 月 $10-40 圏内 (`hga-summoning.md` §envelope 定義準拠)
- [ ] Opus quota envelope: weekly cap 20% 以内
- [ ] 7/8 以降 (クレジット従量移行後) は `hga-summon-log.md` § day-1 実測メモの API 実メータリング基準で監視

**優先度**: SHOULD

### NFR-6: 権限等級遵守 (MUST)

**説明**: R-1 期の全変更は `permission-levels.md` § PG/SE/PM 分類に従う。

**受け入れ条件**:
- [ ] PM 級ファイル (`docs/specs/large-scale-review/` / `.claude/rules/` / `.claude/settings*.json` / 削除実施) は事前宣言 + ユーザー承認
- [ ] SE 級ファイル (`docs/artifacts/` / `docs/tasks/` / 実装コード) は修正後報告
- [ ] PG 級 (フォーマット / lint) は自動修正

**優先度**: MUST

---

## 4. データモデル

### 4.1 tracker エントリー

```
r-1-audit-tracker.md の各 issue エントリー:

| id       | module | summary        | severity | responsibility  | responsibility_tag | status | opened_at  | closed_at  | closed_by_commit |
|:---------|:-------|:---------------|:---------|:----------------|:-------------------|:-------|:-----------|:-----------|:-----------------|
| R1-001   | 3      | SKILL.md drift | Warning  | upstream        | drift              | closed | 2026-07-06 | 2026-07-08 | abc1234          |
| R1-002   | 5      | hook 重複      | Info     | downstream      | dead_code          | open   | 2026-07-06 | -          | -                |
```

- `id`: `R1-` prefix + 3 桁連番 (R1-001, R1-002, ...)
- `module`: 1-11 (§1.3 スコープ表の #)
- `severity`: Critical / Warning / Info (`code-quality-guideline.md` 準拠)
- `responsibility`: upstream / downstream / spec_ambiguity / unknown
- `responsibility_tag`: SRP / DRY / cohesion / cognitive_complexity / drift / security / dead_code / duplication のいずれか
- `status`: open / wip / closed / deferred (`deferred` 時は `deferred_reason` 列必須)
- `closed_by_commit`: closed 時の master コミット SHA (7 桁短縮)

### 4.2 削除履歴エントリー

```
docs/artifacts/r-1-deletions.md の各エントリー:

| id       | deleted_path                | 3 条件 verification            | approver | date       | commit  | tracker_issue_id |
|:---------|:----------------------------|:-------------------------------|:---------|:-----------|:--------|:-----------------|
| D-001    | .claude/agents/xxx.md       | grep 0 / import 0 / 91 days    | user     | 2026-07-10 | def5678 | R1-042           |
```

---

## 5. 成功基準 (Definition of Done)

R-1 Milestone COMPLETE の判定条件:

**MUST (必要条件)**:
- [ ] G1-G5 (既存 Green State) を全 Wave で退行なく維持
- [ ] **R-G6 (tracker 全閉塞)** 達成
- [ ] **R-G7 (参照解決 = 0 drift)** 達成
- [ ] **R-G8 (循環依存 = 0)** 達成
- [ ] 全 5 Wave (W-R1 〜 W-R5) が Green State + ship + push で完了
- [ ] R-1 Milestone retro が実施済 (`docs/artifacts/retro-R1-*-2026-*.md`)

**観測 (SHOULD の遵守状況を集計)** (spec-critic Warning W7 対応 β / RFC 2119 一貫性のため MUST 判定条件から降格):
- Fable HGA 召喚 3 回 (#5 済 / #6 7/7 前必須 / #7 W-R3) の完遂状況を **retro で集計** (FR-6 SHOULD 準拠 / MUST ではない)
- R-1 期の全 gabriel 発火が `.claude/gabriel-metrics.log` に記録されている状況を **月次集計** (FR-7 SHOULD + NFR-4 SHOULD 準拠)
- HGA/gabriel 実施率が retro 議題化 (SHOULD 逸脱の合理性判定 / 逸脱 = Milestone COMPLETE 阻害要因ではない)

### gabriel 併記警告 (Synthesis 由来)

以下は Milestone クローズ判定を **block しない** が retro で議題化必須:

- **A1 消化率追跡**: tracker 手動運用の rule 化予防機構 (rule-002 起票候補) が rule に昇格していない場合、次 Milestone で議題化
- **A2 7/7 前 HGA 集中消化**: 実現可能性は本 requirements 起稿時点で B-5 前提残務完了確認により障害なしと判定 (SESSION_STATE.md HEAD `93032da`)
- **A3 × A1 連動**: FR-4 受け入れ条件で明記済 (削除実施と同時に tracker 該当 issue を closed に更新)
- **SKILL.md 22 vs 23 件差**: Fable 実測で 23 件に修正済 (§1.3 スコープ表)

---

## 6. Definition of Ready チェックリスト

- [x] **Doc Exists**: `docs/specs/large-scale-review/requirements.md` (本ファイル)
- [x] **Unambiguous**:
  - [x] Core Value (Why): §1.1 目的 (B-5 期累積資産の恒久資産化)
  - [x] Data Model: §4 tracker / 削除履歴エントリー
  - [x] Interface: §3 NFR (Green State 追加 3 条件)
  - [x] Constraints: §1.3 Non-Goals / FR-8 Wave 数固定
- [x] **Atomic**: 5 Wave 分割済 (design.md で SPIDR 垂直分割詳細化予定)
- [x] **Testable**: 受け入れ条件は grep / import / tracker status 等の機械判定可能
- [x] **Reviewed**: MAGI 4 Atom (2 round) + gabriel 2 round + HGA #5 Fable = 3 Agents Model 拡張 (MELCHIOR/BALTHASAR/CASPAR + gabriel + Fable HGA) 適用済

---

## 7. 権限等級 (v4.0.0)

| 変更対象 | 権限等級 | 理由 |
|:--------|:--------|:-----|
| 本 requirements.md 修正 | **PM 級** | `docs/specs/` 配下 (`permission-levels.md`) |
| `r-1-audit-tracker.md` 起票 (W-R1) | SE 級 | `docs/artifacts/` 配下 |
| `r-1-audit-tracker.md` の status 列更新 | PG 級 | 実測値の反映 |
| `r-1-deletions.md` 起票 (W-R4) | SE 級 | `docs/artifacts/` 配下 |
| FR-4 削除実施 (agent/rule/hook) | **PM 級** | 削除は不可逆 |
| `.claude/rules/` 変更 (W-R3) | **PM 級** | `permission-levels.md` |
| `docs/internal/` 変更 (W-R3) | SE 級 (**注記**) | `permission-levels.md` 準拠 (docs/ 配下 rules/specs/adr 以外は SE 級) — ただし `docs/internal/` は Hierarchy of Truth では Architecture & Protocols 層に属し `.claude/rules/` と同格 SSOT。この非対称は `permission-levels.md` の **drift** であり、W-R3 (規律 SSOT 統合) の議題として PM 級整合を検討 (spec-critic Warning W9) |
| `CLAUDE.md` / `CHEATSHEET.md` 変更 (W-R3 検討時) | **PM 級** | ルート統治文書 / blast radius 最大 |
| `.claude/scripts/` / `.claude/skills/` 実装変更 | SE 級 | src 相当 |

---

## 8. 制約事項

- **技術制約**: Windows + Git Bash 環境 (`CLAUDE.md` §Execution Environment) / worktree 実運用実績少のため使用禁止 (A2 in-place 採用の根拠)
- **時間制約**: Fable HGA 週枠期限 2026-07-07 (以降クレジット従量移行)
- **予算制約**: HGA envelope 実 $10-40/月 + Opus quota weekly cap 20% 以内
- **コンテキスト制約**: 使用量 180K で `/quick-save` 提案 (`CLAUDE.md` §Context Management) / 200K 超で新セッション推奨
- **後方互換制約**: `.claude/agents/gabriel.md` の 6 フィールド JSON I/O 契約変更禁止 (Wave C 実装済 / R-2 以降で議題化)

---

## 9. 依存関係

- **完了済**: B-5 Milestone (Wave 8 + gabriel Wave C) / rule-001.md 承認 / HGA #5 発火
- **並行**: HGA #6 (7/7 前必須 / W-R1 監査結果 or rubric 事前検証)
- **後続**: R-2 or B-6 (R-1 完了後)

---

## 10. テスト観点

### W-R1 (監査)
- 11 モジュール全件が inventory 再生成で捕捉されているか
- issue に責務タグ + 重要度 + 帰責先が全て付与されているか
- tracker のヒートマップが 11 モジュール × 3 重要度で完備されているか

### W-R2 (dashboard refactor)
- 424 テストが退行なく維持されているか
- SESSION_STATE.md fallback 保守 (rule-001.md) が発動しているか

### W-R3 (規律 SSOT 統合)
- R-G7 (参照解決 = 0 drift) が Stage 末 smoke test で通過するか
- 規範文の重複ペア (decision-making.md 型) が全て検査済か

### W-R4 (hooks/agents 整理)
- 削除 3 条件 AND (grep / import / 90 日) が全削除で検証されているか
- 削除時に agent-memory の対応エントリーが同時無効化されているか
- 削除時に tracker の該当 issue が closed になっているか

### W-R5 (最終監査)
- G1-G5 + R-G6/G7/G8 が全て達成されているか
- gabriel 実運用メトリクスが集計されているか

---

## 11. 未決定事項 (design.md で確定)

- [ ] Wave 内 Stage 分割の粒度 (Stage 数 / 各 Stage の入出力契約)
- [ ] W-R1 の inventory 再生成手順 (スクリプト or 手動 / Glob パターン)
- [ ] 規範文の重複ペア検査手法 (grep 差分 / 手動 diff / spec-critic 委譲)
- [ ] FR-F4 のデータソース具体案 (git log --diff-filter / セッション履歴 grep / 他) — **確定失敗時は削除タスク全体を deferred (FR-4 fallback 準拠)**
- [ ] FR-F5 の rule-001 拡張 vs rule-002 新設の選択
- [ ] NFR-1 R-G7 grep パターンの具体設計 (FR-F3 準拠 / W-R3 用 rules 相互参照 + W-R4 用 SKILL/agents frontmatter / spec-critic Warning W8)
- [ ] NFR-3 Critical 件数閾値の確定 (W-R1 監査完了時 / 初期値 10 は暫定)
- [ ] R-G8 pydeps 相当ツール選定 (循環依存グラフ生成手段)

---

## 12. 変更履歴

| 日付 | 変更者 | 内容 |
|:-----|:-------|:-----|
| 2026-07-05 | L1 (Opus 4.7) | 初版起草 (MAGI 4 Atom + gabriel 2 round + HGA #5 Fable 統合) |
| 2026-07-05 | L1 (Opus 4.7) | spec-critic 独立レビュー Critical 5 + Warning 6 (mechanical) 反映 (FR-F0 新設 / FR-4 fallback / FR-6 fallback / FR-2 wip 扱い / FR-7 opt-out 記録 + 連続 refute / FR-F3 grep パターン / NFR-1 R-G7 3 層防御 + R-G8 現状値計測 / NFR-3 閾値見直し / tracker 破損復旧手順) |
| 2026-07-05 | L1 (Opus 4.7) | spec-critic 独立レビュー Warning W4/W7/W9 反映 (Q1 α: FR-F2 改名を 3 条件 AND 対象化 / Q2 β: §5 HGA 完遂を観測降格 / Q3 β: docs/internal/ SE 級維持 + drift 議題化) + 見えない前提 3 件 (W-R1 read-only 明記 / モジュール分類相互排他性 / skills 削除対象性) 補完 |
| 2026-07-05 | L1 (Opus 4.7) | HGA #6 Fable adversarial review (design.md 対象) の Requirements 側反映: FR-F4 を「90 日窓」から「git log 全期間 + session log 30 日窓 + リソース種別別検出パターン (agents=subagent_type / skills=Skill 起動記録 / hooks=settings 配線 + 実行痕跡)」に再定義。skills 検出の subagent_type 誤用による体系的偽陽性削除リスク (Crux 5-1 Critical) を解消。 |
| 2026-07-05 | L1 (Opus 4.7) | spec-critic on tasks.md Critical 1 対応: FR-6 の HGA 番号を新採番に同期 (#5 済 / #6 済 design review / #7 = W-R1 検証 / #8 = W-R3 SSOT) + fallback level 内も #7/#8 表記に更新 |

---

## 13. 参照

- MAGI 合議記録: `docs/artifacts/2026-07-05-magi-r1-planning.md`
- gabriel 1st probe JSON: `docs/artifacts/2026-07-05-gabriel-probe-r1-planning.json`
- gabriel 2nd probe JSON: `docs/artifacts/2026-07-05-gabriel-probe-r1-planning-2nd.json`
- HGA 召喚ログ: `docs/artifacts/hga-summon-log.md` (#5 追記済)
- 計画書 (原案): `docs/artifacts/future-large-scale-review-plan-2026-07-05.md`
- Green State 定義: `docs/specs/green-state-definition.md`
- コード品質基準: `.claude/rules/code-quality-guideline.md`
- 権限等級: `.claude/rules/permission-levels.md`
- HGA 規律: `.claude/rules/hga-summoning.md`
- MAGI 規律: `.claude/rules/decision-making.md`
- 用語ガイドライン: `.claude/rules/terminology.md`
- ADR-0007: `docs/adr/0007-magi-v2-gabriel-integration.md` (gabriel 統合根拠)
- ADR-0009: `docs/adr/0009-hga-fable-summoning.md` (HGA 型導入根拠)
- rule-001: `.claude/rules/auto-generated/rule-001.md` (SESSION_STATE.md fallback 保守)
- gabriel メトリクス環境: `docs/artifacts/gabriel-metrics-environment-2026-07-05.md`
