---
name: project-gd-cost-w4t2
description: W4-T2 コスト集計+実測正規化の実装知見（方針A・invoke_*_fn シグネチャ変更・累積ロジック）
metadata:
  type: project
---

W4-T2「コスト集計 + 実測正規化」Phase 1+2 完了（2026-06-16）。

## 採用方針
方針 A: `invoke_executor_fn` / `invoke_grader_fn` の戻り型を `tuple[str, Optional[int]]` に変更。
第2要素が実測 `subagent_tokens`（None なら P-2 フォールバック）。

## gd_state.py 追加関数
- `accumulate_subagent_tokens(layer, tokens, project_root)` — 層別累積 + total_tokens 連動加算
- `compute_l1_ratio(project_root)` — l1_tokens / total_tokens（zero-div 時 0.0）
- `build_cost_summary(project_root)` — design §14 L767-778 形式文字列
- `record_token_divergence(layer, self_reported, measured, project_root)` — ±20% 超で WARN + _divergences 記録

## gd_loop.py 改修要点
1. `run_grader_with_retry` の戻り型が `tuple[dict, Optional[int]]` に変更（旧: dict のみ）
2. `_accumulate_agent_tokens()` 内部ヘルパーで実測優先・None 時 P-2 フォールバック（WARN 必須）
3. grader は self_reported=0 で呼び出す（grader は tokens_used を自己申告しない設計）

## P-2 フォールバック定義
subagent_tokens=None の場合、自己申告 tokens_used を採用し [gd-warn] ログを出力する。
silent failure 禁止のため WARN なしの握りつぶしは Critical 扱い。

## テスト変更
- 既存テストで invoke_*_fn を返す lambda を `_make_executor_fn()` / `_make_grader_fn()` ヘルパーに統一
- `TestGraderRetryLogic` の mock と assertion を tuple 戻り値に対応（`result, _ = run_grader_with_retry(...)`）
- 新規テスト: TestAccumulateSubagentTokens(7), TestBuildCostSummary(5), TestRecordTokenDivergence(3), TestSubagentTokenAccumulation(3) = 18件追加
- 合計: 78 → 348 passed（全スイート込み）

**Why:** cost_log 層別内訳と total_tokens 二重保持禁止（design §14 MUST NOT）は既存テスト `test_cost_log_not_duplicated_in_total_tokens` で保護済み。
**How to apply:** 次フェーズ（Phase 3 design.md/SKILL.md 更新）では run_grader_with_retry の戻り型変更を文書化する。
