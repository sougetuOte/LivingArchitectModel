# R-1 Milestone Tasks: 大規模レビュー & リファクタリング

## メタ情報

| 項目 | 内容 |
|:-----|:-----|
| Milestone | R-1 |
| ステータス | **Approved** (2026-07-05 / spec-critic Critical 3 + Warning 7 反映済 / R-1 PLANNING クローズ) |
| 作成日 | 2026-07-05 |
| requirements | [requirements.md](./requirements.md) (Approved) |
| design | [design.md](./design.md) (Approved) |
| SPIDR 分割 | 垂直分割 (Wave 内 Stage を全層貫通) |
| WBS 100% Rule | 全 FR/NFR がタスクに対応 (§7 トレーサビリティ表) |

---

## 1. Wave / Stage / Task 対応表

命名規約: `W-R<n>-S<m>-T<k>` (Wave n / Stage m / Task k)
`n` ∈ {1..5} / `m` ∈ {1..5} / `k` ∈ {1..9}

各 Task には以下 5 フィールド:
- **F**: 対応 FR/NFR (requirements.md)
- **D**: 依存する先行 Task (blocks 関係)
- **担当層**: L1 / L2 (Sonnet) / L3 (Haiku) / HGA (Fable)
- **完了条件**: 二値・機械判定可能
- **commit**: 中間 (WIP prefix) / Stage 末 ship

---

## 2. W-R1: 監査 (Read-Only)

### Stage S1: Green State 確認 + inventory + rule-001 前倒し

| Task | 内容 | F | D | 担当層 | 完了条件 | commit |
|:-----|:-----|:--|:--|:------:|:---------|:------:|
| **W-R1-S1-T1** | `.claude/scripts/r1_inventory.py` 作成 (Python + AST + Glob / 11 モジュール MODULES dict / import グラフ生成) | FR-F1 / R-G8 | - | L1 | スクリプト作成 + `python r1_inventory.py --dry-run` 成功 | WIP |
| **W-R1-S1-T2** | inventory 実行 → `docs/artifacts/r-1-inventory-*.json` 生成 | FR-F1 | T1 | L1 | inventory.json 生成 + 11 モジュール count 実測記載 | WIP |
| **W-R1-S1-T3** | 自作 AST + 自前 DFS で循環依存グラフ生成 (module 1/2/5 対象 / tests 除外) | R-G8 | T2 | L1 | 循環リスト作成 (JSON) / 循環 0 なら baseline に記録 / 存在なら tracker 起票用リスト作成 | WIP |
| **W-R1-S1-T4** | `.claude/scripts/verify_reference_resolution.py` + `.claude/tests/rules/test_reference_resolution.py` 作成 (層 3 unittest 用) | FR-F3 / R-G7 層 3 | T2 | L1 | 両ファイル作成 + テスト空実行成功 | WIP |
| **W-R1-S1-T5** | G1-G5 実装確認 + `docs/artifacts/r-1-green-state-baseline-2026-07-*.md` 起票 | FR-F0 | - | L1 | baseline.md 生成 (G1-G5 各条件の状態明文化) | WIP |
| **W-R1-S1-T6** | rule-001 R-1 節拡張 (design §8.2 差分適用 / HGA #6 Crux 4-c 前倒し) | FR-F5 | - | L1 | rule-001.md 差分 commit + PM 級承認取得 | WIP |
| **W-R1-S1-T7** | Stage 末 ship (T1-T6 統合 commit / closed issue IDs 列挙は空 / W-R1 期は監査対象 issue が未確定) | - | T1-T6 | L1 | commit + push 成功 + 424+63=487 PASS + 14 SKIP 維持 | **Stage 末 ship** |

**Stage 完了ゲート**: inventory.json 存在 + baseline.md 存在 + verify script 存在 + rule-001 拡張済 + 循環依存判定完了 + G1-G5 明文化完了

### Stage S2: widescan 監査 module 1-4 (dashboard 系 + tests)

| Task | 内容 | F | D | 担当層 | 完了条件 | commit |
|:-----|:-----|:--|:--|:------:|:---------|:------:|
| **W-R1-S2-T1** | tracker.md 骨組み作成 (Markdown table + ヒートマップ 11×3 プレースホルダ) | FR-2 | S1-T2 | L1 | tracker.md 存在 + ヒートマップ骨組完備 | WIP |
| **W-R1-S2-T2** | module 1 (`.claude/scripts/dashboard/`) 監査 → issue 起票 (責務タグ + 重要度 + 帰責先 + evidence_file/line/summary) | FR-1 / FR-5 / R-G7 | S2-T1 | L1 | module 1 セクション完備 + 全 issue に 6 属性付与 | WIP |
| **W-R1-S2-T3** | module 2 (`.claude/scripts/` 外) 監査 → issue 起票 | FR-1 / FR-5 | S2-T1 | L1 | module 2 セクション完備 | WIP |
| **W-R1-S2-T4** | module 3 (`.claude/skills/`) 監査 → issue 起票 + **tier=orchestrator/utility タグ付与** (magi/full-review/lam-orchestrate/autonomous/goal-driven = orchestrator 5 件) | FR-1 / FR-5 / スコープ表 | S2-T1 | L1 | module 3 セクション完備 + tier タグ全 SKILL.md 付与 | WIP |
| **W-R1-S2-T5** | module 4 (`.claude/tests/`) 監査 → issue 起票 | FR-1 / FR-5 | S2-T1 | L1 | module 4 セクション完備 | WIP |
| **W-R1-S2-T6** | S2 Stage 末 ship (module 1-4 統合) | - | S2-T2..T5 | L1 | ship + push / smoke test (rule-001) PASS | **Stage 末 ship** |

**Stage 完了ゲート**: module 1-4 の 4 セクション完備 + 各 issue に 6 属性完備

### Stage S3: widescan 監査 module 5-8

| Task | 内容 | F | D | 担当層 | 完了条件 | commit |
|:-----|:-----|:--|:--|:------:|:---------|:------:|
| **W-R1-S3-T1** | module 5 (`.claude/hooks/` + `settings*.json`) 監査 | FR-1 / FR-5 | S2 完了 | L1 | module 5 セクション完備 | WIP |
| **W-R1-S3-T2** | module 6 (`.claude/agents/`) 監査 (12 件実測 / plugin 由来除外) | FR-1 / FR-5 / スコープ表 | S2 完了 | L1 | module 6 セクション完備 | WIP |
| **W-R1-S3-T3** | module 7 (`.claude/rules/` 11 files + auto-generated/) 監査 | FR-1 / FR-5 | S2 完了 | L1 | module 7 セクション完備 | WIP |
| **W-R1-S3-T4** | module 8 (`docs/internal/` 00-07) 監査 | FR-1 / FR-5 | S2 完了 | L1 | module 8 セクション完備 | WIP |
| **W-R1-S3-T5** | S3 Stage 末 ship | - | S3-T1..T4 | L1 | ship + push | **Stage 末 ship** |

### Stage S4: widescan 監査 module 9-11 + ヒートマップ

| Task | 内容 | F | D | 担当層 | 完了条件 | commit |
|:-----|:-----|:--|:--|:------:|:---------|:------:|
| **W-R1-S4-T1** | module 9 (`docs/specs/`) 監査 | FR-1 / FR-5 | S3 完了 | L1 | module 9 セクション完備 | WIP |
| **W-R1-S4-T2** | module 10 (`docs/adr/`) 監査 | FR-1 / FR-5 | S3 完了 | L1 | module 10 セクション完備 | WIP |
| **W-R1-S4-T3** | module 11 (`CLAUDE.md` + `CHEATSHEET.md`) 監査 | FR-1 / FR-5 / スコープ表 | S3 完了 | L1 | module 11 セクション完備 | WIP |
| **W-R1-S4-T4** | ヒートマップ実測値埋め (11 モジュール × 3 重要度 = 33 セル) | FR-5 / NFR-3 | S4-T1..T3 | L1 | ヒートマップ 33 セル完備 | WIP |
| **W-R1-S4-T5** | S4 Stage 末 ship | - | S4-T1..T4 | L1 | ship + push | **Stage 末 ship** |

**Stage 完了ゲート**: 11 モジュール全カバー + ヒートマップ 33 セル完備

### Stage S5: HGA #7 消化 + 閾値確定

| Task | 内容 | F | D | 担当層 | 完了条件 | commit |
|:-----|:-----|:--|:--|:------:|:---------|:------:|
| **W-R1-S5-T1** | HGA #7 (旧計画 #6) 発火判定 (第一候補 = 監査結果検証 / スライド候補 = rubric 事前検証) | FR-6 | S4 完了 | L1 | 判定完了 + 対象確定 | - |
| **W-R1-S5-T2** | HGA #7 Fable 召喚実行 (design §10.1 手順準拠) | FR-6 | S5-T1 | L1 + HGA (Fable) | Fable 応答受領 + `docs/artifacts/2026-07-*-fable-hga-7.md` 起票 | WIP |
| **W-R1-S5-T3** | Fable 応答を tracker に反映 (1 件以上の tracker 差分 commit / Warning W3 機械判定) | FR-6 | S5-T2 | L1 | tracker 差分 1 件以上 commit | WIP |
| **W-R1-S5-T4** | NFR-3 Critical 件数閾値確定 (実測に基づく / 初期 10 は暫定) + **閾値超過時のみ**: 優先順位付けサブタスクを tracker に起票 (spec-critic Warning W5 対応 / 条件分岐 Task 化) | NFR-3 | S5-T3 | L1 | tracker 冒頭に閾値注記追加 + 超過時は優先順位付け sub-task 起票済 (超過しない場合は sub-task 起票なし) | WIP |
| **W-R1-S5-T5** | hga-summon-log.md に #7 追記 | FR-6 | S5-T2 | L1 | log 追記 | WIP |
| **W-R1-S5-T6** | W-R1 Wave 完了 ship (全 issue 起票 + tracker 完成 + HGA #7 反映) | - | S5-T1..T5 | L1 | ship + push + `[R-1 W-R1 COMPLETE]` タグ commit message | **Wave 末 ship** |

**Wave 完了ゲート**: G1-G5 維持 + 11 モジュール全カバー + evidence pointer 完備 + ヒートマップ完備 + HGA #7 消化済 (fallback level 記録)

---

## 3. W-R2: dashboard 領域 refactor

### Stage S1-S4 共通方針

- **担当層**: L2 Sonnet (tdd-developer subagent / `disallowedTools: [Agent]` + Executor boilerplate 適用)
- **TDD サイクル**: 各 Stage 内で 1 Critical issue = 1 Red-Green-Refactor
- **Stage 末 ship** に commit message に **closed issue IDs 列挙** (FR-1 準拠 / git log 経由の消化率追跡)
- **L2 Sonnet ブリーフ (tight brief 4-slot / spec-critic Warning W6 対応)**: Stage 内で「N 件の Critical issue」を一括委譲する場合、`hga-summoning.md` §tight brief 4-slot に従い objective (issue X の refactor) / output format / tool guidance / task boundaries を Task 単位で明記。1 Task = N 件の Critical を「issue ごとに順次サイクル実行」と読める粒度に精緻化
- **Stage 末 ship 前の L3 Haiku 突合** (spec-critic Warning W8 対応 / §9 リスク緩和策との整合): Stage 末 ship の直前に L3 Haiku で「tracker で closed 化された issue ID vs commit message 内の closed IDs 列挙」の突合を実施 (W-R2/W-R3/W-R4 の全 Stage 末 ship Task に共通適用)

### Stage S1: module 1/2 Critical 消化 (R1-001 + R1-006 / **Fable HGA #8 crux 反映 / 2026-07-06**)

**変更履歴**: 2026-07-06 に HGA #7 で R1-006 が Warning → Critical 昇格したため、S1 スコープを module 1 単独から **module 1/2 両 Critical 併合** に拡張 (元 S2 の R1-006 を S1 に吸収)。S2 は module 2 残 Warning 消化に scope 変更。

**Fable HGA #8 crux (2026-07-06)** — tracker 推奨の regex は両方とも不十分と判明:

- **R1-001**: tracker 推奨 `(?:[:\s]|$)` は装飾文字 (`**ID**`, `(ID)`, `` `ID` ``, 全角括弧, 読点) で false negative + leading 境界欠如で短縮形 `T\d+` が `S3-T1` / `W3-B5-T31` 途中に誤マッチ。**Fable 推奨**: `re.search(r"(?<![A-Za-z0-9-])" + re.escape(task_id) + r"(?![A-Za-z0-9])", line)` (negative lookbehind + lookahead 両方 / trailing に `-` を含めない理由 = `T1-T5` 範囲記法保護)
- **R1-006**: tracker 推奨の一律 `[A-Za-z0-9._-]+` は slug (パターン3 group2) がドット捕食 → Windows 末尾ドット quirk (`Path('docs/specs/xxx.').exists()` → True) で偽 Green。**Fable 推奨**: アンカー付き 2 箇所 (パターン1 group1 + パターン3 group3) は `[A-Za-z0-9._-]+`、slug (パターン3 group2 / アンカーなし) は構造化形 `[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*` (**内部ドットのみ許容 / 末尾ドット不可**)

**副産物** (Fable crux 由来 / 実装時忘れ防止):
- **docstring 同時更新必須**: `builder.py` L690-694 の「行に `task_id` が含まれる」→「行に `task_id` が (英数字と接する形なく) 現れる」相当に改訂 (Spec Synchronization)
- **live baseline drift=1 の裁定**: 現行 `verify_reference_resolution.py --wave w-r3` は既に drift=1 (`docs/specs/feature` placeholder / `99_reference_generic.md` 由来) を報告している。W-R2 S1 内で「テンプレ placeholder として山括弧付きの `<feature>` に書式変更 (現状既に山括弧 / crux 内 unverified 側)、もしくは検出器側で `<...>` を含む参照を除外リスト化」のいずれかを 1 行決めておく (R-G7 再判定の前提)
- **R1-001 の意図的挙動変更 (2 件 / HGA #9 verdict C-N2 で 2 件目追加)**:
  1. 短縮形 `task.id='T31'` (非 W 形式) が完全形 'W3-B5-T31' 行にリンクしなくなる (現行 substring で偽リンクしていた) — この cross-form リンク前提の運用があるかを T3 で確認
  2. **範囲記法エンドポイント semantics** (HGA #9 C-N2 追加): SESSION_STATE.md の "T1-T5" のような範囲記法に対し、**範囲は展開しない** (左端 T1 のみマッチ / 右端 T5 は非マッチ)。旧 substring 実装は両端マッチしていたが、旧実装は接頭辞衝突 (R1-001) を含む欠陥のため旧挙動は仕様ではない (未文書化の副産物であった)。呼び出し側で範囲を扱う必要があれば個別 ID (T1, T2, T3, T4, T5) を completed リストに列挙する運用とする。この仕様は `test_r1_001_task_status_token_boundary.py::TestRangeNotationEndpointSemantics` (Case 8 / 3 テスト) で固定。

| Task | 内容 | F | D | 担当層 | 完了条件 | commit |
|:-----|:-----|:--|:--|:------:|:---------|:------:|
| **W-R2-S1-T1** | ✅ 完了 (本セッション内 / HGA #8 crux-scoping で吸収) — R1-001 + R1-006 の Critical リスト抽出 + Fable crux 分析 | FR-1 | W-R1 完了 | L1 | Critical リスト + Fable crux 応答 | - |
| **W-R2-S1-T2** | Red-Green-Refactor 実行: (a) R1-001 = `builder.py` `_resolve_task_status` + docstring 修正 + Fable 提示 test cases 7 件追加 / (b) R1-006 = `verify_reference_resolution.py` パターン 1/3 修正 + Fable 提示 test cases 7 件追加 | FR-3 / R-G6 | S1-T1 | L2 Sonnet (tdd-developer) | 両 Critical = 0 / 537 PASS + 14 SKIP + 追加 tests 全 PASS / regression 0 | WIP |
| **W-R2-S1-T3** | **Fable HGA #9 adversarial verify** (修正コード + 追加テストを独立検証 / HGA #7 メタ欠陥#1 対策) — attack surface 抜け / edge case 漏れ / regression risk を独立検出 | FR-3 補足 | S1-T2 | Fable | verdict = confirmed (or refuted → S1-T2 に戻る) | - |
| **W-R2-S1-T4** | tracker で R1-001 / R1-006 を wip → closed 更新 + `severity_history` (R1-006 のみ) + `closed_by_commit` 記録 + baseline drift 裁定を反映 | FR-2 | S1-T3 | L1 | tracker status = closed | WIP |
| **W-R2-S1-T5** | S1 Stage 末 ship (closed issue IDs = R1-001, R1-006 列挙) + HGA #8/#9 を `hga-summon-log.md` に追記 | - | S1-T4 | L1 | ship + push + smoke test PASS | **Stage 末 ship** |

**Fable HGA #8 呼応** (2026-07-06): crux-scoping brief (small brief 2-3k / 2 段召喚) で R1-001+R1-006 の crux 特定。tool_uses 16 / duration 27min / probe スクリプト実測含む。応答は本 tasks.md および tracker 更新に反映済。

### Stage S2: module 2 (scripts/ 外) Warning 消化 (旧 Critical 消化 → S1 に吸収)

| Task | 内容 | F | D | 担当層 | 完了条件 | commit |
|:-----|:-----|:--|:--|:------:|:---------|:------:|
| **W-R2-S2-T1** | module 2 残 issue リスト抽出 → **R1-053 (W / HGA #9 起票 / 前倒し) + R1-007 + R1-008** (2026-07-07 L1 裁定: R1-053 は tracker P2 = W-R3 相当だが R1-006 と同 bug class + R-G7 gate 汚染候補のため S2 へ前倒し消化) | FR-1 | S1 完了 | L1 | リスト作成 | - |
| **W-R2-S2-T2** | 各 issue に Red-Green-Refactor 実行 (既存テスト十分な場合は Red スキップ可 / tracker コメント欄に明記) / R1-053 は実装後 HGA verify (2 段階検出パターン踏襲 / crux-scoping 不要 = bug 局所化明確) | FR-3 / R-G6 | S2-T1 | L2 Sonnet | R1-053/R1-007/R1-008 修正完了 / smoke test PASS | WIP × N |
| **W-R2-S2-T3** | tracker 更新 | FR-2 | S2-T2 | L1 | status closed | WIP |
| **W-R2-S2-T4** | S2 Stage 末 ship | - | S2-T2/T3 | L1 | ship + push | **Stage 末 ship** |

### Stage S3: module 4 (tests/) Warning 消化 (テスト分割 / fixture 重複除去)

| Task | 内容 | F | D | 担当層 | 完了条件 | commit |
|:-----|:-----|:--|:--|:------:|:---------|:------:|
| **W-R2-S3-T1** | module 4 Warning 抽出 → **R1-031 (fixture 共通化) を本 Stage 消化 / R1-030 (debug スクリプト 5 件削除) は tracker 推奨方針通り W-R4 S2 `git rm` 束ねへ送り** (2026-07-07 L1 裁定) | FR-1 | S2 完了 | L1 | リスト作成 | - |
| **W-R2-S3-T2** | Warning 消化 (fixture 共通化 / テスト分割) | FR-3 | S3-T1 | L2 Sonnet | **576 PASS + 14 SKIP 維持** (S2 完了時点実測 / 旧 487 は W-R1 計画時 baseline) | WIP × N |
| **W-R2-S3-T3** | tracker 更新 | FR-2 | S3-T2 | L1 | status closed | WIP |
| **W-R2-S3-T4** | S3 Stage 末 ship | - | S3-T2/T3 | L1 | ship + push | **Stage 末 ship** |

### Stage S4: module 1/2/4 Warning 消化 + 観測値記録

| Task | 内容 | F | D | 担当層 | 完了条件 | commit |
|:-----|:-----|:--|:--|:------:|:---------|:------:|
| **W-R2-S4-T1** | 残 Warning 抽出 (module 1/2/4 の Warning 全件) | FR-1 | S3 完了 | L1 | リスト作成 | - |
| **W-R2-S4-T2** | Warning 消化 | FR-3 | S4-T1 | L2 Sonnet | module 1/2/4 Warning = 0 | WIP × N |
| **W-R2-S4-T3** | 認知複雑度・重複コード観測値記録 (`docs/artifacts/r-1-observations-2026-07-*.md`) | NFR-1 補足 | S4-T2 | L1 | observations.md 起票 | WIP |
| **W-R2-S4-T4** | tracker 更新 + Wave 完了 ship | - | S4-T2/T3 | L1 | `[R-1 W-R2 COMPLETE]` + 579 PASS + 14 SKIP (実測 / 旧 487 は W-R1 計画時 baseline) + G1-G5 維持 | **Wave 末 ship** |

**Wave 完了ゲート**: module 1/2/4 の Critical = 0 + Warning = 0 (**W-R3/R4 送り裁定分 = R1-030・R1-056 を除く** / 2026-07-07 更新) / 576 PASS + 14 SKIP 以上維持 (旧 487 は W-R1 計画時 baseline) / observations.md 完備

---

## 4. W-R3: 規律 SSOT 統合 (逐次 / W-R2 完了後)

### Stage S1: HGA #8 + 重複ペア検査

| Task | 内容 | F | D | 担当層 | 完了条件 | commit |
|:-----|:-----|:--|:--|:------:|:---------|:------:|
| **W-R3-S1-T1** | 規範文の重複ペア検査 (design §9 準拠 / 「SSOT 親宣言」grep → diff → 差分要約) | FR-F3 補足 | W-R2 完了 | L1 | `docs/artifacts/r-1-duplicate-pair-audit-2026-07-*.md` 起票 | WIP |
| **W-R3-S1-T2** | HGA #8 (旧 #7) Fable 召喚 (design §10.2 手順 / 重複ペア検査結果 + 対応方針 3 案) | FR-6 | S1-T1 | L1 + HGA (Fable) | Fable 応答受領 + anchor 起票 | WIP |
| **W-R3-S1-T3** | Fable 応答を design/tracker に反映 (1 件以上の差分 commit) | FR-6 | S1-T2 | L1 | 差分 1 件以上 commit | WIP |
| **W-R3-S1-T4** | hga-summon-log.md に #8 追記 | FR-6 | S1-T2 | L1 | log 追記 | WIP |
| **W-R3-S1-T5** | S1 Stage 末 ship | - | S1-T1..T4 | L1 | ship + push + verify_reference_resolution.py --wave w-r3 PASS | **Stage 末 ship** |

### Stage S2: docs/internal/ SSOT drift 解消 (自主 PM 運用)

| Task | 内容 | F | D | 担当層 | 完了条件 | commit |
|:-----|:-----|:--|:--|:------:|:---------|:------:|
| **W-R3-S2-T1** | **Stage 冒頭に 8 ファイル編集計画を宣言 + 一括承認取得** (HGA #6 Crux 4-b 自主 PM 運用) | Q3 β / HGA #6 | S1 完了 | L1 | ユーザー一括承認取得 | - |
| **W-R3-S2-T2** | module 8 (`docs/internal/`) の重複ペア差分反映 + drift 解消 | FR-1 | S2-T1 | L1 | internal 修正差分 | WIP × N |
| **W-R3-S2-T3** | tracker 更新 | FR-2 | S2-T2 | L1 | status closed | WIP |
| **W-R3-S2-T4** | S2 Stage 末 ship (R-G7 W-R3 grep PASS 確認) | R-G7 | S2-T2/T3 | L1 | ship + push + `verify_reference_resolution.py --wave w-r3` PASS | **Stage 末 ship** |

### Stage S3: .claude/rules/ 相互矛盾解消 + FR-F5 決定実装

| Task | 内容 | F | D | 担当層 | 完了条件 | commit |
|:-----|:-----|:--|:--|:------:|:---------|:------:|
| **W-R3-S3-T1** | Stage 冒頭に rules 編集計画宣言 + PM 級承認取得 | permission-levels | S2 完了 | L1 | 承認取得 | - |
| **W-R3-S3-T2** | rules 相互矛盾解消 (11 files 対象) | FR-1 | S3-T1 | L1 | rules 修正差分 | WIP × N |
| **W-R3-S3-T3** | permission-levels.md 側の docs/internal/ 権限等級 drift 議題化 (SE 級維持 or PM 昇格 の最終判断 / requirements Q3 β) | Q3 β | S3-T2 | L1 | 議題結論を rules 差分に反映 | WIP |
| **W-R3-S3-T4** | tracker 更新 + S3 ship | - | S3-T2/T3 | L1 | ship + push + R-G7 W-R3 PASS | **Stage 末 ship** |

### Stage S4: docs/specs/ + docs/adr/ + ルート統治文書 一貫性修正

| Task | 内容 | F | D | 担当層 | 完了条件 | commit |
|:-----|:-----|:--|:--|:------:|:---------|:------:|
| **W-R3-S4-T1** | Stage 冒頭に specs/adr/ルート統治文書 編集計画宣言 + PM 級承認取得 | permission-levels | S3 完了 | L1 | 承認取得 | - |
| **W-R3-S4-T2** | module 9/10/11 の一貫性修正 (specs/adr/CLAUDE.md/CHEATSHEET.md) | FR-1 | S4-T1 | L1 | 修正差分 | WIP × N |
| **W-R3-S4-T3** | tracker 更新 + Wave 完了 ship | - | S4-T2 | L1 | `[R-1 W-R3 COMPLETE]` + R-G7 全 PASS | **Wave 末 ship** |

**Wave 完了ゲート**: module 7/8/9/10/11 の Critical + Warning = 0 / R-G7 W-R3 用 grep = 0 drift / HGA #8 消化済

---

## 5. W-R4: hooks / agents 整理 (逐次 / W-R3 完了後)

### Stage S1: FR-F4 データソース確定 + usage-baseline 生成

| Task | 内容 | F | D | 担当層 | 完了条件 | commit |
|:-----|:-----|:--|:--|:------:|:---------|:------:|
| **W-R4-S1-T1** | 実 jsonl 1 本を開いて skills 起動記録のフィールド名確定 (HGA #6 Crux 5-1 の要検証仮定解消) | FR-F4 | W-R3 完了 | L1 | フィールド名確定 (例: `command_name` / `skill_name` 等) | - |
| **W-R4-S1-T2** | git log スクリプト作成 (filter なし / 各リソース種別対象) | FR-F4 | S1-T1 | L2 Sonnet | スクリプト作成 + 全 target_path 走査完了 | WIP |
| **W-R4-S1-T3** | session log 30 日窓 grep スクリプト作成 (agents/skills/hooks 3 分岐) | FR-F4 | S1-T1 | L2 Sonnet | スクリプト作成 + 3 分岐実装 + 全 target_path 走査完了 | WIP |
| **W-R4-S1-T4** | usage-baseline.md 生成 (§3.4 スキーマ / verdict = delete_candidate / keep_recent_modified / hold_low_confidence 分岐) | FR-F4 | S1-T2/T3 | L2 Sonnet | usage-baseline.md 生成 + verdict 全付与 | WIP |
| **W-R4-S1-T5** | **データソース確定判定** (成功 = W-R4 継続 / 失敗 = 次 Task で deferred 降格実施 / requirements FR-4 fallback) | FR-F4 | S1-T4 | L1 | 判定結果を tracker と SESSION_STATE.md に記録 | - |
| **W-R4-S1-T5b** | **判定失敗時のみ実行** (spec-critic Critical 2 対応): W-R4-S2/S3 の全削除 Task を tracker で deferred 化 (deferred_reason = 'FR-F4 data source undetermined' 付与) + W-R4-S2-T1〜T5 と W-R4-S3-T1〜T3 の実行を skip | FR-4 fallback | S1-T5 (failure verdict の場合) | L1 | 対象 Task 全件 deferred 化完了 / SESSION_STATE.md に降格記録 (成功時は本 Task 自体を skip) | WIP |
| **W-R4-S1-T6** | S1 Stage 末 ship | - | S1-T2..T5b | L1 | ship + push | **Stage 末 ship** |

**判定分岐**:
- **成功** → S2/S3/S4 通常進行
- **失敗** → S2/S3 削除タスク全 deferred (tracker に deferred_reason='FR-F4 data source undetermined') / S3 の agent-memory 更新 + S4 の Warning 消化のみ進行

### Stage S2: agents 削除 / 改名 実施

| Task | 内容 | F | D | 担当層 | 完了条件 | commit |
|:-----|:-----|:--|:--|:------:|:---------|:------:|
| **W-R4-S2-T1** | agents 削除候補確定 (usage-baseline verdict=delete_candidate + tracker Critical/Warning issue 連動) | FR-4 | S1 完了 (成功) | L1 | 候補リスト作成 | - |
| **W-R4-S2-T2** | **Stage 冒頭に削除リスト一括宣言 + 一括承認取得** (HGA #6 Crux 4-a) | permission-levels | S2-T1 | L1 | 一括承認取得 | - |
| **W-R4-S2-T3** | 削除実施 (束ね `git rm <path1> <path2> ...` / Bash ask 1 回) + agent-memory 対応エントリー無効化 + tracker closed 化 + deletions.md 追記 | FR-4 / FR-F2 (memory 連動) | S2-T2 | L1 | git rm 成功 + deletions.md 追記完了 + tracker closed | WIP |
| **W-R4-S2-T4** | 改名候補確定 (存在すれば) → PM 級承認 → `git mv` 束ね実施 + renames.md 追記 + tracker closed | FR-F2 | S2-T3 | L1 | 完了 (改名候補ゼロなら本 Task skip) | WIP |
| **W-R4-S2-T5** | L3 Haiku で「宣言リスト vs 実行リスト」の文字単位一致突合 (HGA #6 Crux 4-a) | permission-levels | S2-T3/T4 | L3 Haiku | 突合結果 = 完全一致 | - |
| **W-R4-S2-T6** | S2 Stage 末 ship | - | S2-T3..T5 | L1 | ship + push + verify_reference_resolution.py --wave w-r4 PASS | **Stage 末 ship** |

### Stage S3: skills (utility) 削除 + hooks 統合

| Task | 内容 | F | D | 担当層 | 完了条件 | commit |
|:-----|:-----|:--|:--|:------:|:---------|:------:|
| **W-R4-S3-T1** | skills 削除候補確定 (**tier=utility 限定** / orchestrator 5 件は保護維持) | FR-4 / スコープ表 | S1 完了 (spec-critic Warning W9 対応: S2 待ちは並列化余地を潰す / S1 の usage-baseline のみに依存) | L1 | 候補リスト (tier フィルタ済) | - |
| **W-R4-S3-T2** | Stage 冒頭一括宣言 + 承認取得 | permission-levels | S3-T1 | L1 | 承認取得 | - |
| **W-R4-S3-T3** | skills 削除実施 + tracker closed + deletions.md 追記 | FR-4 | S3-T2 | L1 | 完了 | WIP |
| **W-R4-S3-T4** | hooks 重複統合 (module 5 の Warning 消化) | FR-1 | S3 - | L2 Sonnet | hooks 統合完了 + 既存 hook テスト維持 | WIP |
| **W-R4-S3-T5** | L3 Haiku 突合 | permission-levels | S3-T3 | L3 Haiku | 完全一致 | - |
| **W-R4-S3-T6** | S3 Stage 末 ship | - | S3-T3..T5 | L1 | ship + push + R-G7 W-R4 PASS | **Stage 末 ship** |

### Stage S4: agent-memory 更新 + Warning 消化

| Task | 内容 | F | D | 担当層 | 完了条件 | commit |
|:-----|:-----|:--|:--|:------:|:---------|:------:|
| **W-R4-S4-T1** | agent-memory 更新パス作成 (削除された agent の memory エントリー無効化スクリプト) | FR-F2 | S3 完了 | L2 Sonnet | スクリプト作成 + テスト PASS (TDD Red-Green-Refactor) | WIP |
| **W-R4-S4-T2** | module 3/5/6 の残 Warning 消化 | FR-1 | S4-T1 | L2 Sonnet + L1 | Warning = 0 | WIP × N |
| **W-R4-S4-T3** | Wave 完了 ship (R-G7 W-R4 全 PASS + tracker 更新) | R-G7 | S4-T2 | L1 | `[R-1 W-R4 COMPLETE]` + R-G7 = 0 drift | **Wave 末 ship** |

**Wave 完了ゲート**: module 3/5/6 の Critical + Warning = 0 / R-G7 W-R4 grep = 0 drift / 削除+改名履歴完備 / agent-memory 整合 / FR-F4 データソース確定 (成功時) or 削除全 deferred (失敗時)

---

## 6. W-R5: 最終監査 (逐次)

### Stage S1: tracker 全閉塞確認 (R-G6)

| Task | 内容 | F | D | 担当層 | 完了条件 | commit |
|:-----|:-----|:--|:--|:------:|:---------|:------:|
| **W-R5-S1-T1** | tracker 全 issue 状態確認 (open/wip 残存 = 0 / closed/deferred のみ) | R-G6 | W-R4 完了 | L3 Haiku | 検証レポート `docs/artifacts/r-1-tracker-closure-report-*.md` | WIP |
| **W-R5-S1-T2** | S1 ship | - | S1-T1 | L1 | ship + push | **Stage 末 ship** |

### Stage S2: R-G7/G8 検証

| Task | 内容 | F | D | 担当層 | 完了条件 | commit |
|:-----|:-----|:--|:--|:------:|:---------|:------:|
| **W-R5-S2-T1** | R-G7 全 grep 通し (W-R3 用 + W-R4 用 + 層 3 unittest / verify_reference_resolution.py + test_reference_resolution.py) | R-G7 | S1 完了 | L3 Haiku | 全 PASS + false negative リスト作成 | WIP |
| **W-R5-S2-T2** | R-G8 循環依存再計測 (自作 AST + DFS 再実行 / W-R1 baseline との比較) | R-G8 | S1 完了 | L3 Haiku | 循環 = 0 (or R-1 scope 限定 = 0 + 既存分 deferred 記録) | WIP |
| **W-R5-S2-T3** | 検証レポート統合 | - | S2-T1/T2 | L1 | `docs/artifacts/r-1-final-audit-report-2026-07-*.md` | WIP |
| **W-R5-S2-T4** | S2 ship | - | S2-T3 | L1 | ship + push | **Stage 末 ship** |

### Stage S3: gabriel + code-review ultra

| Task | 内容 | F | D | 担当層 | 完了条件 | commit |
|:-----|:-----|:--|:--|:------:|:---------|:------:|
| **W-R5-S3-T1** | gabriel adversarial verify 発火 (R-1 全体結論 = final-audit-report + tracker + baseline) | FR-7 | S2 完了 | L1 + gabriel | 6 フィールド JSON 応答受領 + gabriel-metrics.log 追記 | - |
| **W-R5-S3-T2** | **gabriel verdict 分岐処理** (HGA #6 Crux 2-c α): refuted+critical → tracker 新規起票 → R-G6 で block / refuted+warning → 併記 / confirmed → 進む | FR-7 | S3-T1 | L1 | 分岐処理完了 | WIP |
| **W-R5-S3-T3** | `/code-review ultra` 別セッション実行案内 (L1 温存 / ユーザーがクラウドセッション起動 / spec-critic Warning W10: ユーザーは 3.5 層委譲モデル外の担当 = 明示委譲) | - | S3-T2 | ユーザー (委譲外) | code-review 結果受領 | - |
| **W-R5-S3-T4** | code-review 指摘反映 (Critical のみ即時 / Warning は Info と共に retro 議題化) | - | S3-T3 | L1 or L2 Sonnet | Critical = 0 | WIP × N |
| **W-R5-S3-T5** | S3 ship | - | S3-T4 | L1 | ship + push | **Stage 末 ship** |

### Stage S4: retro + Milestone COMPLETE 判定 + rule-001 R-1 節削除

| Task | 内容 | F | D | 担当層 | 完了条件 | commit |
|:-----|:-----|:--|:--|:------:|:---------|:------:|
| **W-R5-S4-T1** | R-1 Milestone retro 起草 (`docs/artifacts/retro-R1-2026-07-*.md`) | - | S3 完了 | L1 | retro 完成 (KPT + アクション + Green State + HGA/gabriel メトリクス集計) | WIP |
| **W-R5-S4-T2** | Milestone COMPLETE 判定 (§5 全 MUST 条件 checkbox 確認 + gabriel 併記警告確認 + **FR-8 Wave 数 5 維持の最終確認** / spec-critic Warning W7) | Definition of Done + FR-8 | S4-T1 | L1 + ユーザー | COMPLETE 判定承認取得 + Wave 数 5 維持確認済 | - |
| **W-R5-S4-T3** | **rule-001 R-1 節削除** (最終操作 / HGA #6 Crux 4-c 順序固定 / 判定が覆った場合の保険を最後まで残す) | FR-F5 | S4-T2 | L1 | rule-001.md 差分 commit + PM 級承認 | WIP |
| **W-R5-S4-T4** | SESSION_STATE.md 更新 + Wave 完了 + Milestone COMPLETE ship | - | S4-T3 | L1 | `[R-1 W-R5 COMPLETE + Milestone COMPLETE]` タグ commit + push | **Milestone COMPLETE ship** |

**Milestone 完了ゲート**: G1-G5 全 Wave 維持 + R-G6/G7/G8 全達成 + 全 5 Wave 完了 + retro 実施済 + gabriel + code-review ultra 発火完了

---

## 7. トレーサビリティ (WBS 100% Rule 検証)

requirements.md の全 FR/NFR がタスクに対応することを確認:

| requirements 項目 | 対応 Task |
|:------------------|:---------|
| FR-1 (hybrid スコープ) | W-R1 S2-S4 全 T + W-R2/R3/R4 実装 Stage 全体 |
| FR-2 (tracker) | W-R1 S2-T1 (骨組) + W-R2/R3/R4 の status 更新 + W-R5 S1-T1 (閉塞確認) |
| FR-3 (in-place) | W-R2/R3/R4 全体 (master 直改修) |
| FR-4 (moderate 削除) | W-R4 S2/S3 削除実施 全 T |
| FR-5 (モジュール単位) | W-R1 S2-S4 全 T (11 モジュール + 責務タグ) |
| FR-6 (HGA 3 → 4 回 SHOULD 逸脱) | W-R1 S5-T1..T5 (HGA #7) + W-R3 S1-T2..T4 (HGA #8) + 既発火 #5/#6 |
| FR-7 (MAGI + gabriel 積極活用) | W-R1 S5-T4 (閾値確定 MAGI) + W-R5 S3-T1/T2 (gabriel + verdict 分岐) + 他 Wave 内判断で発火 |
| FR-8 (Wave 数固定) | 全 Wave = 5 固定 + tracker deferred 昇格基準 (二値判定) |
| FR-F0 (R-1 開始時 G1-G5 確認) | W-R1 S1-T5 |
| FR-F1 (inventory 再生成) | W-R1 S1-T1/T2 |
| FR-F2 (agent-memory + 改名) | W-R4 S2-T3 (memory 無効化) + S2-T4 (改名) + S4-T1 (更新パス) |
| FR-F3 (prose smoke test = R-G7) | W-R1 S1-T4 (verify script 作成) + W-R3/R4 Stage 末 verify 実行 + W-R5 S2-T1 |
| FR-F4 (削除判定データソース) | W-R4 S1 全 T (確定 + baseline 生成 + 判定分岐) |
| FR-F5 (rule-001 拡張) | W-R1 S1-T6 (前倒し) + W-R5 S4-T3 (R-1 節削除) |
| NFR-1 (R-G6/G7/G8) | R-G6: W-R5 S1 / R-G7: W-R5 S2-T1 / R-G8: W-R5 S2-T2 |
| NFR-2 (pytest 全 PASS 維持) | 各 Stage 末 ship の smoke test 条件 |
| NFR-3 (認知負荷管理) | W-R1 S4-T4 (ヒートマップ) + S5-T4 (閾値確定) |
| NFR-4 (gabriel メトリクス月次集計) | W-R5 S4-T1 (retro での集計) |
| NFR-5 (HGA envelope 監視) | 各 HGA 発火直後 (design §10.4 準拠) |
| NFR-6 (権限等級遵守) | 全 Stage 冒頭の事前宣言 (design §14 Stage 単位表準拠) |

**孤児 (Orphan) 検出**: なし。全タスクが FR/NFR にトレース可。

---

## 8. 権限等級 (Stage 単位 / design §14 準拠)

design.md §14 の Stage 単位表を参照。本 tasks.md は design §14 と整合。

---

## 9. リスクと緩和策 (tasks 固有 / design §13 補完)

| リスク | 影響 | 緩和策 |
|:------|:-----|:-------|
| L2 Sonnet 委譲時の meta-response 早期終了 | Stage 完了失敗 | `disallowedTools: [Agent]` + Executor boilerplate 適用 (`hga-summoning.md` §Sonnet L2 委譲時の追加防御) |
| W-R2 Critical 消化中の 424 テスト退行 | Wave blocker | 各 Task の Green ステップで pytest 実行 / Red スキップ判断は tracker コメントに明記 |
| W-R4 S1-T5 データソース確定失敗 | W-R4 大半 deferred | S2/S3 の削除 Task を deferred_reason 付きで tracker 記録 / S4 (agent-memory 更新 + Warning 消化) のみ進行 |
| Stage 末 ship の commit message closed IDs 列挙漏れ | git log 消化率追跡不能 | L3 Haiku で ship 直前に「tracker で closed 化された ID vs commit message の ID」の突合 |
| HGA #7 が 7/7 期限内消化不能 | HGA schedule 破綻 | design §10.3 3 段 fallback (Level 1 部分検証 6 モジュール下限 → Level 2 #8 統合 → Level 3 再 MAGI) |
| gabriel W-R5 S3 で refuted+critical | Milestone COMPLETE block | HGA #6 Crux 2-c α で tracker 新規起票 → R-G6 経由 block (既存機構) |

---

## 10. 変更履歴

| 日付 | 変更者 | 内容 |
|:-----|:-------|:-----|
| 2026-07-05 | L1 (Opus 4.7) | 初版起草 (5 Wave × 各 4-5 Stage × 全 Task 展開 / WBS 100% Rule トレーサビリティ完備 / requirements.md + design.md 全反映) |
| 2026-07-05 | L1 (Opus 4.7) | spec-critic 独立レビュー Critical 3 + Warning 7 反映: HGA リナンバー同期 (requirements FR-6 の #6/#7 → #7/#8 更新 / Critical 1) / W-R4-S1-T5b deferred 降格実施 Task 追加 (Critical 2) / design §14 W-R4 S4 の rule-001 削除 + W-R1 S1 T6 に PM 級注記追加 (Critical 3 + Warning W4) / W-R2 S1-S4 共通方針に tight brief 4-slot 精緻化 (W6) + L3 Haiku Stage 末 ship 突合 (W8) / W-R1 S5-T4 に閾値超過時条件分岐 (W5) / W-R4 S3-T1 依存を S1 に修正 (W9 並列化) / W-R5 S3-T3 の「ユーザー (委譲外)」担当層明記 (W10) / W-R5 S4-T2 に FR-8 Wave 数維持確認追加 (W7) |

---

## 11. 参照

- [requirements.md](./requirements.md) (Approved)
- [design.md](./design.md) (Approved)
- MAGI 記録: `docs/artifacts/2026-07-05-magi-r1-planning.md`
- HGA 記録: `docs/artifacts/hga-summon-log.md` (#5-#6)
- gabriel メトリクス: `.claude/gabriel-metrics.log`
- 3.5 層委譲: `CLAUDE.md` §作業体制
- Sonnet L2 委譲時追加防御: `.claude/rules/hga-summoning.md`
- rule-001: `.claude/rules/auto-generated/rule-001.md`
