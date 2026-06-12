---
name: project-gd-state-w2t2
description: B-3 W2-T2 gd_state.py 実装パターン — spawn-time enforcement・スキーマ・AC-8/AC-9
metadata:
  type: project
---

W2-T2: `.claude/scripts/gd_state.py`（新規）+ `.claude/hooks/tests/test_gd_state.py`（新規）を実装。

**Why:** goal-driven スキルの第一防衛線（spawn-time enforcement）。  
各 Agent 呼び出し後の tokens_used 累積、次 spawn 前の残予算チェック、エスカレーション経路、並列起動チェック、distill hook 点を含む。

**How to apply:**
- `gd_state.py` は `.claude/scripts/` 以下（アンダースコア命名。ハイフン入りは import 不可）
- テストは `test_gd_guard.py` と同じパターン: `_SCRIPTS_DIR` を `sys.path` に追加して `import gd_state`
- `project_root` 引数を `None` にすると `LAM_PROJECT_ROOT` 経由で解決（P-3 対応）
- `check_spawn_budget()` は OR セマンティクス（トークン OR 時間。境界値も "escalate"）
- `check_loop_bound()` は `loop_count >= max_loop_count` で "escalate"
- `check_parallel_spawn_budget()` は `sum(sub_budgets) > remaining` で "sequential"
- `distill_hook_point()` は W4-T1 向け骨格（pass のみ。蒸留本体は対象外）
- `fallback` フィールド（初期値 `None`）は PM 承認済み追加スキーマ
- `status` の取りうる値: `"running"` / `"escalated"` / `"completed"` の 3 値
- `cost_log` は層別内訳のみ（`total_tokens` 重複禁止・design §14 MUST NOT）
- CLI は `_build_arg_parser()` + `_dispatch_command()` に分割して 50 行以内を維持

**スキーマ完全版（config.md §5 + PM 承認済み追加）:**
```json
{
  "task_id": "gd-YYYYMMDD-NNN",
  "task_slug": "...",
  "route": "small|medium|large",
  "nest_depth_limit": 5,
  "global_token_bound": 150000,
  "global_time_bound": 3600,
  "total_tokens": 0,
  "loop_count": 0,
  "max_loop_count": 3,
  "start_time": 1718064000.0,
  "status": "running",
  "fallback": null
}
```

**ルート別 global_token_bound:** small=50000 / medium=150000 / large=400000  
**テスト件数:** 37 件（新規）。既存 218 + 新規 37 = 255 件すべてパス。
