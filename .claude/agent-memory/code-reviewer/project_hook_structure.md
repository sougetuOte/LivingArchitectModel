---
name: hook_structure_quality_issues
description: .claude/hooks/ の実装構造と既知の品質課題（2026-06-02 イテレーション4更新）
type: project
---

hooks/ 構成: _hook_utils.py（共通Utils）/ pre-tool-use.py / post-tool-use.py / pre-compact.py / lam-stop-hook.py
analyzers/: base.py / config.py / orchestrator.py / chunker.py / reducer.py / run_pipeline.py / scale_detector.py / state_manager.py / gitleaks_scanner.py / python_analyzer.py / javascript_analyzer.py / rust_analyzer.py / card_generator.py（1,305行・⑤送り分割計画済み）

**Why:** イテレーション4監査（2026-06-02 iter2）で更新。

**How to apply:** 次回レビュー時に同一 Issue の再発確認に使う。

## 残存課題（イテレーション4更新 = iter2 後の状態）

### Critical（要対応）
- [C-1/PM] `detect_circular_dependencies()` / `build_topo_order()` の戻り値が「循環なし」と「解析失敗（RecursionError）」を区別不能。card_generator.py:886-912, 1010-1032（⑤送り）
- [C-2/SE] `_find_sccs()` が再帰 Tarjan 実装のため、ノード数1000以上で RecursionError（反復実装への置き換えが必要）。card_generator.py:831-876（⑤送り）

### Warning（要対応）
- [W-1/SE] `lam-stop-hook.py:main()` が51行（50行制限超過）（未解消）
- [W-iter2-1/SE] `lam-stop-hook.py:_handle_autonomous()` が51行（新規 iter2）
- [W-iter2-2/SE] `pre-tool-use.py:_determine_level_and_reason()` が60行（新規 iter2 — 権限判定中核関数）
- [W-iter2-3/SE] `pre-tool-use.py:_read_current_phase()` の `except Exception: pass` がエラー黙殺（新規 iter2）
- [W-iter2-4/SE] `card_generator.py:_bfs_upstream()` が `queue.pop(0)` で O(N) 削除（新規 iter2）
- [W-iter2-5/PM] ESLint flat config (eslint.config.*) 未検出（javascript_analyzer.py:53-116）（継続）
- [W-3/SE] `pre-compact.py:update_session_state()` で OSError を捕捉していない（未解消）
- [W-4/SE] `card_generator.py:_find_sccs()` の `index_counter = [0]` が Python 3 では nonlocal で書ける（⑤送り）
- [W-5/PM] `lam-stop-hook.py` の `_SECRET_PATTERN` が .md/.txt で偽陽性（未解消）
- [W-6/PM] `pre-tool-use.py:_FR9_PATTERNS` が `.claude/hooks/` 配下テストも DENY する（未解消）

### Info（参考）
- [I-1/PG] `post-tool-use.py:140` `return None` 冗長（継続）
- [I-2/SE] `card_generator.py:collect_spec_drift_context()` の specs_dir.glob が非再帰（⑤送り）
- [I-3/SE] `scale_detector.py:_check_plan_a()` の reason 文字列がハードコード（継続）
- [I-4/SE] `gitleaks_scanner.py:_run_gitleaks()` の report_path 未定義時 NameError 経路（継続）
- [I-5/SE] `_hook_utils.py:get_project_root()` のフォールバック時に警告なし（継続）
- [I-iter2-2/SE] `card_generator.py:952` `_condense_sccs()` が SCC メンバー探索を全走査 O(N^2)（⑤送り）

## 解消された課題（参照用）

- パストラバーサル防止: `_validate_check_dir()` の追加により対応済み（イテレーション2）
- `run_command` の shell=False 固定は継続して維持されている
- [W-2旧/SE] `lam-stop-hook.py:_save_loop_log()` の `except Exception: pass` → WARNING ログ化済み（iter1 修正）
- import 統一（W-11）: iter1 で修正済み
- [W-1旧] `_now_utc()` 冗長ラッパー → `now_utc_iso8601()` に集約済み（v4.3.0）
- [W-4旧] tool_events 上限 → `_MAX_TOOL_EVENTS = 500` 追加済み（v4.3.0）
- run_pipeline.py の `line_count` が analyzers 未検出時も常時カウントされるよう修正済み（監査 S2a）
