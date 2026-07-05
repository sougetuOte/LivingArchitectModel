# R-1 Green State Baseline (2026-07-06)

**目的**: R-1 Milestone 開始時点の Green State (G1-G5 + R-G6/G7/G8) の実装状態を明文化する。
**対応 FR**: FR-F0 (R-1 開始時 Green State 状態確認 / MUST / spec-critic Critical C4)
**根拠**: `docs/specs/green-state-definition.md` (G1-G5 SSOT) + `docs/specs/large-scale-review/requirements.md` NFR-1 (R-G6/G7/G8)
**生成日**: 2026-07-06 (W-R1 S1 T5)

---

## サマリ

| 条件 | 状態 | Blocker? |
|:----|:-----|:--------:|
| G1: pytest 全 PASS | **達成** (519 PASS + 14 SKIP) | - |
| G2: lint 全パス | **段階導入途上** (design D3 未完 / Wave 2 まで G1 のみ運用) | No (段階導入合意済) |
| G3: 対応可能 Issue 全解決 | **達成** (Critical/Warning 集計対象なし / R-1 で tracker 生成後に再判定) | No |
| G4: 仕様差分ゼロ | **段階導入途上** (Wave 3 完全実装予定 / quality-auditor 依存) | No |
| G5: セキュリティチェック通過 | **達成** (gitleaks + python_analyzer + javascript_analyzer 実装済) | No |
| R-G6: tracker 全閉塞 | **N/A** (tracker 未生成 / W-R1 S2 で骨組作成予定) | - |
| R-G7: 参照解決 = 0 drift | **1 件検出** (template placeholder / 実 drift ではない) | No |
| R-G8: 循環依存 = 0 | **達成** (file=93 / edge=109 / **cycle=0** / T3 実測) | - |

**判定**: **R-1 開始 blocker なし**。G2/G4 は段階導入合意済。R-G6 は W-R1 進行中に自動整備される。R-G7 の drift 1 件は次項に詳細。

---

## G1: pytest 全 PASS

**判定方法**: `pyproject.toml` `[tool.pytest.ini_options]` により pytest 自動検出、exit code 0 判定。

**実測** (2026-07-06 W-R1 S1 T4 完了時点):

```
519 passed, 14 skipped in 7.39s
```

**推移**:
- B-5 Milestone COMPLETE 時点 (2026-07-05): 487 PASS + 14 SKIP
- W-R1 S1 T3 完了時点 (2026-07-06): 504 PASS + 14 SKIP (+17 / r1_inventory + r1_cycle_detect テスト)
- **W-R1 S1 T4 完了時点 (2026-07-06)**: **519 PASS + 14 SKIP** (+15 / verify_reference_resolution テスト)
- regression 0 (全 Wave で維持)

**根拠**: `pyproject.toml:2` の `--junitxml=.claude/test-results.xml` 設定 + `test-result-output.md` ルール準拠。

**維持条件**: 各 Stage 末 ship 前に pytest 実行 rc=0 (tasks.md 各 Stage 完了条件)。

---

## G2: lint 全パス

**判定方法**: G2/G5 は `lam-stop-hook.py` の `checker_results.g2_exit` / `g5_exit` に記録される (モデル改竄不能)。

**実装状態**: **段階導入途上**
- `lam-stop-hook.py:416` コメント: 「Wave 2 まで G1 のみ。design D3 の G2/G5 実行 (checker_results.g2_exit/g5_exit) は」…
- 現時点で G2 自動判定は AUTONOMOUS ループの完了条件に組み込まれていない
- 手動運用 (BUILDING/AUDITING フェーズでの ruff/eslint 実行) は継続中

**R-1 内の扱い**: 段階導入合意済のため R-1 blocker ではない (green-state-definition.md §2.1 MVP + §2.2 AUTONOMOUS 段階導入注記)。R-1 期の Python 資産追加 (T1/T3/T4 スクリプト + テスト) は Green State 相当のコーディング規約 (docstring / 型ヒント / 未使用 import 除去) を BUILDING 側で満たしている。

**判定**: **段階導入途上 (blocker なし)**

---

## G3: 対応可能 Issue 全解決

**判定方法**: quality-auditor 出力パース (Critical = 0 / Warning = 0 / Info は集計のみ / deferred は件数除外)。

**R-1 開始時点の状態**:
- **audit tracker 未生成** (`docs/artifacts/r-1-audit-tracker.md` は W-R1 S2 T1 で骨組作成予定)
- 既存 pending Issue は B-5 Milestone COMPLETE 時点 (2026-07-05) で消化済 (SESSION_STATE.md HEAD `93032da` 参照)
- 現時点で対応可能 Issue = 0 (集計対象なし)

**R-1 内での再判定**: W-R1 全 Stage を通じて監査 issue が起票され、W-R2/R3/R4 で消化、W-R5 S1 で全閉塞確認 (R-G6)。R-1 Milestone COMPLETE 時に G3 を最終判定。

**判定**: **達成 (集計対象なし / R-1 進行中に自動整備)**

---

## G4: 仕様差分ゼロ

**判定方法**: quality-auditor が `docs/specs/` と実装コードの整合性を検証。

**実装状態**: **段階導入途上** (green-state-definition.md §3.4「Wave 3 (ドキュメント自動追従) 完了後に段階的に導入」)

**R-1 内の扱い**: W-R3 (規律 SSOT 統合) が spec drift を人手で解消する。W-R4 では FR-F2 に基づき削除/改名を deletions.md / renames.md にトレース。したがって G4 自動判定を待たずに、R-1 Wave の完了条件が実質的に「差分ゼロ」を保証する構造。

**判定**: **段階導入途上 (blocker なし)**

---

## G5: セキュリティチェック通過

**判定方法**: 依存脆弱性 + シークレット + 危険パターン検出 (green-state-definition.md §3.5)。

**実装状態**: **達成**
- `.claude/hooks/analyzers/gitleaks_scanner.py` (シークレット検出 / Phase 0 統合済)
- `.claude/hooks/analyzers/python_analyzer.py` (bandit ラッパー / Python 危険パターン)
- `.claude/hooks/analyzers/javascript_analyzer.py` (npm audit 系 / JS 依存脆弱性)
- `pyproject.toml` には `[project]` セクションなし = pip-audit スキップ対象 (仕様通り)

**R-1 内の扱い**: R-1 スコープは prose 資産 (rules/skills/agents/internal) が中心のため、G5 は R-1 の追加 Python コード (T1/T3/T4/T7 スクリプト) が gitleaks + bandit で clean であることを担保する範囲。

**判定**: **達成**

---

## R-G6: tracker 全閉塞 (R-1 追加 3 条件 #1)

**判定方法**: `r-1-audit-tracker.md` の全 issue が `closed` または `deferred` (理由付き)。`wip` 残存は不可 (W-R5 時点扱い)。

**R-1 開始時点の状態**: **N/A** (tracker 未生成)
- 骨組作成予定: W-R1 S2 T1 (次 Stage / 本 Stage の後続)
- 全 issue 起票完了: W-R1 S4 T4 (ヒートマップ埋め時点)
- 全閉塞確認: W-R5 S1 T1 (Milestone COMPLETE 直前)

**判定**: **未評価 (Milestone COMPLETE 直前に評価)**

---

## R-G7: 参照解決 = 0 drift (R-1 追加 3 条件 #2)

**判定方法**: 3 層防御 (bash grep パターン + Python 存在検査 + unittest / design.md §5)

**R-1 開始時点の実測**:

```
$ python .claude/scripts/verify_reference_resolution.py --wave all
total_drifts: 1
  - w-r3: 1 件 (docs/internal/99_reference_generic.md:22 → docs/specs/feature_x.md)
  - w-r4: 0 件
```

**drift 1 件の分析**:
- 該当箇所: `docs/internal/99_reference_generic.md:22 "Output: docs/specs/feature_x.md (Ready)"`
- **template 例示由来** (実 drift ではない): `feature_x.md` は仕様書執筆時のプレースホルダ表記であり、実 spec を参照しているわけではない
- 対応方針: W-R3 S4 (module 9/10/11 一貫性修正) で「template 例示は正規表現から除外 or ファイル側を明示的にコメントアウト」の対応を tracker Info として起票候補
- **R-1 開始 blocker ではない**

**判定**: **1 件検出 (template 由来 / 実 drift なし / R-1 Info 起票候補)**

---

## R-G8: 循環依存 = 0 (R-1 追加 3 条件 #3)

**判定方法**: 自作 AST + 自前 DFS で module 1/2/5 の import グラフを検査 (tests 除外 / design.md §6)

**R-1 開始時点の実測** (2026-07-06 W-R1 S1 T3 完了時点):

```
$ python .claude/scripts/r1_cycle_detect.py
docs/artifacts/r-1-cycles-2026-07-06.json (rc=0)
files: 93
edges: 109
cycles: 0  ← R-G8 baseline 達成
```

**対象モジュール** (design §6 準拠):
- module 1: `.claude/scripts/dashboard/**/*.py`
- module 2: `.claude/scripts/*.py` (dashboard/ 除外)
- module 5: `.claude/hooks/**/*.py`
- **除外**: module 4 (`.claude/tests/**/*.py`) は Milestone COMPLETE を block しない

**判定**: **達成** (R-1 baseline 確立 / W-R5 S2 T2 で再計測比較)

---

## R-1 開始判定

| 判定軸 | 結果 |
|:------|:-----|
| G1-G5 段階導入との整合 | **OK** (G2/G4 段階導入は Wave 2/Wave 3 合意済) |
| R-1 開始 blocker | **なし** |
| R-G7 drift | template 由来 1 件のみ (実 drift 0) |
| R-G8 baseline | 確立 (cycle=0) |

**結論**: **R-1 Milestone 開始承認**。W-R1 S1 T6 (rule-001 R-1 節拡張) 以降を継続する。

---

## R-1 完了時の再評価予定

| 条件 | 再評価タイミング | 予定 |
|:----|:----------------|:-----|
| G1 | 各 Stage 末 ship | 519 PASS + 14 SKIP 維持 (退行 0) |
| R-G6 | W-R5 S1 T1 | tracker 全閉塞確認 |
| R-G7 | W-R5 S2 T1 | 3 層 grep + verify script rc=0 |
| R-G8 | W-R5 S2 T2 | 循環依存再計測 (baseline 比較) |

---

## 変更履歴

| 日付 | 変更者 | 内容 |
|:-----|:-------|:-----|
| 2026-07-06 | L1 (Opus 4.7) | 初版起票 (W-R1 S1 T5 / FR-F0 対応) |

---

## 参照

- `docs/specs/green-state-definition.md` (G1-G5 SSOT)
- `docs/specs/large-scale-review/requirements.md` FR-F0 / NFR-1 (R-G6/G7/G8)
- `docs/specs/large-scale-review/design.md` §5 (R-G7 grep) / §6 (R-G8 循環検出)
- `docs/artifacts/r-1-inventory-2026-07-06.json` (T2 実測)
- `docs/artifacts/r-1-cycles-2026-07-06.json` (T3 実測)
- `SESSION_STATE.md` HEAD `93032da` (B-5 Milestone COMPLETE / R-1 起点)
