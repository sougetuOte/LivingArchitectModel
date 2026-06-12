---
name: project-gd-loop-w3t2
description: B-3 W3-T2 gd_loop.py 実装パターン — Plan B 制御ループ・grader retry・§11b fallback
metadata:
  type: project
---

W3-T2: `.claude/scripts/gd_loop.py`（新規）+ `.claude/hooks/tests/test_gd_loop.py`（新規）を実装。

**Why:** goal-driven スキルの Plan B 制御ループ本体（SKILL.md フロー[4][5]）。  
l3-executor と grader を独立した Agent 呼び出しで起動し、grader の判定に従って合格/差し戻し/エスカレーションに分岐する。

**How to apply:**
- `gd_loop.py` のパブリック API:
  - `run_plan_b_loop()`: ループ本体（invoke_executor_fn・invoke_grader_fn を DI で受け取る）
  - `parse_grader_output()`: grader 判定 JSON → verdict 分類（pass/fail/escalate/error）
  - `run_grader_with_retry()`: grader エラー時 1 回のみ再試行・再失敗でエスカレーション（MUST NOT 合格扱い）
  - `is_nest_failure()`: Agent ツール結果の error フィールドからネスト失敗を検知（§11b）
  - `activate_two_layer_fallback()`: `fallback: "two_layer"` セット（§11b）
  - `save_grader_log()`: `.claude/logs/gd/<task_id>-loop<N 2桁>-grader.json`（NFR-3）
  - `build_l3_executor_prompt()` / `build_grader_prompt()`: プロンプト生成

- ログファイル命名は `f"{task_id}-loop{loop_num:02d}-grader.json"`（`gd-` プレフィックスを重複させない）。`task_id` 自体が `gd-YYYYMMDD-NNN` 形式であるため。

- `run_plan_b_loop()` はループ本体を `_check_bounds()` / `_parse_executor_report()` / `_build_fail_feedback()` に分割してリファクタリング済み（50行以内維持）。

- テストは DI パターン（`invoke_executor_fn` / `invoke_grader_fn` にラムダを渡す）でモック grader を実現。実ランタイムファイル不使用・tmp_path で完結。

- `is_nest_failure()` は `error` フィールドのテキストに "sub-agent" / "nesting" / "not supported" を含む場合に True。大文字小文字は `.lower()` で正規化。

**テスト件数:** 41 件（新規）。既存 293 + 新規 41 = 334 件すべてパス。

**AC-5 対応:** `invoke_executor_fn` と `invoke_grader_fn` を分離することで、実際の呼び出し元が Agent(l3-executor) と Agent(grader) をそれぞれ独立した呼び出しで起動することを設計として強制する。
