# full-review iter2 残 Issue（次セッションで対応）

**起票日**: 2026-06-02
**起票元**: full-review iter2（`docs/artifacts/audit-reports/2026-06-02-iter2.md`）
**ステータス**: **全件決着（2026-06-02 追補セッション・CLOSED）**。SE/PG 7件解消 + PM 2件決着（W2-P2 解消 / W2-P1 見送り）。
**前セッション修正済み**: W2-3（握りつぶしログ化）/ W2-5（hookEventName 対称化）/ RET501（冗長 return None 削除）— 663 passed 回帰なし
**追補セッション修正済み（2026-06-02・670 passed 回帰なし）**:
- SE: W2-1（`_apply_g1_result()` 抽出）/ W2-2（`_determine_by_path`/`_determine_by_command` 分離）/ W2-6（`conftest.make_default_state` ファクトリ集約）/ W2-7（isinstance アサート）/ W2-8（3テスト分割）/ Info-a（gitleaks report_path 防御初期化）/ Info-b（_hook_utils stderr ログ）
- PG: SEC-N2（test env allowlist 化）/ SEC-N3（`_sanitize_target` で Cc/Cf 制御文字除去）
- 検証: ruff クリーン（残 F401 1件は e2e フィクスチャの意図的・対象外）/ 全 670 passed（e2e マーカー5件含む）

## 方針

ユーザー判断: 「最終的に Critical/Warning は全部、Info もできる限り、PM も全部。ただしコンテキスト/ツール破損リスクから1セッションで全部はやらない。低リスク SE+PG（推奨計画）を実施したら次セッションで残りを潰す」。
今セッションは本体の低リスク核心（W2-3 ほか）のみ実施。以下が次セッション対象。

## 未対応 Issue 一覧

### SE 級（修正対象）

| # | 箇所 | 内容 | 備考 |
|---|------|------|------|
| W2-1 | `lam-stop-hook.py:282-332` | `_handle_autonomous()` 51行・3責務 → `_apply_g1_result()` 抽出 | 権限/Stop hook 中核・回帰リスク → 668テストで慎重に |
| W2-2 | `pre-tool-use.py:111-170` | `_determine_level_and_reason()` 60行 → パス判定/コマンド判定に分離 | 権限判定中核・回帰リスク |
| W2-6 | `tests/test_stop_hook.py:17` / `test_loop_integration.py:21` | `DEFAULT_STATE` 2ファイル重複 → conftest に集約 | SESSION_STATE 既知 W-7 と同一 |
| W2-7 | `tests/test_autonomous_state.py` | `state_file_path()` の `isinstance(Path)` アサート欠落 | 1行追加 |
| W2-8 | `tests/test_loop_integration.py::test_init_fail_then_converge` | 50行3フェーズ詰込・block 検証重複 → 分割 | |
| Info-a | `gitleaks_scanner.py:176-219` | `report_path` 未定義時 NameError 可能性 → `report_path=None` 初期化 + finally ガード | iter1 I-4 継続 |
| Info-b | `_hook_utils.py:43-44` | `LAM_PROJECT_ROOT` 不正時ログなしフォールバック → stderr ログ | iter1 I-5 継続 |

### PG 級（自動修正可）

| # | 箇所 | 内容 |
|---|------|------|
| SEC-N2 | `analyzers/tests/test_e2e_review.py:504,532,550` | `{**os.environ}` env 全継承 → `_ENV_ALLOWLIST` パターン適用（conftest hook_runner は iter1 修正済み） |
| SEC-N3 | `pre-tool-use.py:221-225` | `target` の Unicode 双方向制御文字（U+202E 等）未エスケープ → Cf カテゴリフィルタ追加 |

### PM 級（承認・決着済み 2026-06-02）

| # | 箇所 | 内容 | 決定 |
|---|------|------|------|
| W2-P1 | `javascript_analyzer.py:53-116` | ESLint flat config（`eslint.config.{js,mjs,cjs}`）未検出。ESLint v9 普及で実害率増。検出ロジック追加は仕様判断 | **見送り（future-candidates 相当）** |
| W2-P2（=W-6） | `SKILL.md` Stage1 Step3 / `run_pipeline.py` | SKILL.md は「import-map.json を `run_phase0()` が永続化」と記すが実装に生成処理なし（`save_import_map` 不在）。Plan D を無効化。現状 Plan A のみで実害なし | **解消（SKILL.md を実態へ修正）** |

#### W2-P2 解消内容（ユーザー承認: SKILL.md 修正方針）

`run_phase0()` の実出力は `static-issues.json` + `summary.md` の 2 ファイルのみ。`ast-map.json` /
`import-map.json` / `dependency-graph.json` は未生成（AST/import 抽出が `parse_ast` Phase 1 簡易実装どまり）。
`.claude/skills/full-review/SKILL.md` の Stage 1（出力行・Step 3）/ Stage 2 入力 / Stage 3 入力・Layer 2 コメントに
**「実装状況 NOTE」** を追加し、虚偽の「永続化済み」記述を「現状未生成・`{}` 縮退・実質 no-op（Plan D 無効）」へ修正。
前方互換の足場コードブロックは残置（将来 AST/import-map 生成実装時にそのまま機能）。Zero-Regression（挙動不変・ドキュメントのみ）。

#### W2-P1 見送り判断（ユーザー承認: 現状維持）

- `javascript_analyzer.run_lint` は `npx eslint --format json` を直実行し、ESLint 自身が flat（v9）/ legacy 両設定を
  ネイティブに解決する。設定不在時も `returncode∉(0,1)` → warning ログ + 空リスト（完全な silent failure ではない）。
- 実害は限定的・追加価値は低・検出仕様変更のリスクに見合わないため**見送り**。
- 将来 JS/TS 案件比率が上がり「設定不在の明示スキップ」が必要になった時点で再評価する（flat + legacy + `package.json` の
  `eslintConfig` 検出 → 不在時は明示スキップ + テスト追加）。本項を future-candidate として記録。

## 棄却（再検出不要）

- pytest マーカー未登録（PM 候補）→ `pyproject.toml` に `e2e_llm`/`e2e_convergence` 登録済み・偽陽性
- SEC-N1（B314 XXE）→ Python 3.8+ デフォルト安全 + 信頼境界内 XML・対処不要

## 既存タスクへ委譲

- W2-4（`card_generator.py:1143` `_bfs_upstream` の `queue.pop(0)`→deque）・`_condense_sccs` O(N^2)（`card_generator.py:952`）→ `card-generator-split-deferred.md`（⑤分割時に一括解消）
- W-9（通知B）→ `tdd-notification-b-deferred.md`
- W-14/W-15（env継承・symlink）→ `hooks-security-hardening-ci.md`
- W-12（state_dir パス不整合・`.claude/hooks/.claude/` junk 再生成）→ 別案件（恒久対策: scale_detector/run_phase0 を project_root 基準に統一 or `.gitignore` に `**/.claude/review-state/`）

## 参照

- 監査レポート: `docs/artifacts/audit-reports/2026-06-02-iter2.md`
- ループログ: `.claude/logs/full-review-iter2-*.json`
