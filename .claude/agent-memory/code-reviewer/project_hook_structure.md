---
name: hook_structure_quality_issues
description: .claude/hooks/ の実装構造と既知の品質課題（2026-06-02 イテレーション3更新）
type: project
---

hooks/ 構成: _hook_utils.py（共通Utils）/ pre-tool-use.py / post-tool-use.py / pre-compact.py / lam-stop-hook.py
analyzers/: base.py / config.py / orchestrator.py / chunker.py / reducer.py / run_pipeline.py / scale_detector.py / state_manager.py / gitleaks_scanner.py / python_analyzer.py / javascript_analyzer.py / rust_analyzer.py / card_generator.py（1,305行・⑤送り分割計画済み）

**Why:** イテレーション3監査（2026-06-02）で発見した再発防止のため記録。

**How to apply:** 次回レビュー時に同一 Issue の再発確認に使う。

## 残存課題（イテレーション3更新）

### Critical（要対応）
- [C-1/PM] `detect_circular_dependencies()` / `build_topo_order()` の戻り値が「循環なし」と「解析失敗（RecursionError）」を区別不能。card_generator.py:886-912, 1010-1032
- [C-2/SE] `_find_sccs()` が再帰 Tarjan 実装のため、ノード数1000以上で RecursionError（反復実装への置き換えが必要）。card_generator.py:831-876

### Warning（要対応）
- [W-1/SE] `lam-stop-hook.py:main()` が50行制限超過（前サイクル [W-3/SE] と同一、未解消）
- [W-2/SE] `lam-stop-hook.py:_save_loop_log()` の `except Exception: pass` がエラー黙殺（L117）
- [W-3/SE] `pre-compact.py:update_session_state()` で OSError を捕捉していない
- [W-4/SE] `card_generator.py:_find_sccs()` の `index_counter = [0]` が Python 3 では nonlocal で書ける（可読性）
- [W-5/PM] `lam-stop-hook.py` の `_SECRET_PATTERN` が .md/.txt で偽陽性（前サイクル [C-4/PM] と同一、未解消）
- [W-6/PM] `pre-tool-use.py:_FR9_PATTERNS` が `.claude/hooks/` 配下テストも DENY する（FR-9 の対象範囲が仕様と齟齬の可能性）
- [C-6/SE] ESLint flat config (eslint.config.*) 未検出（前サイクルから継続）
- [C-8/SE] `go test` カウント正規表現が脆弱（前サイクルから継続）

### Info（参考）
- [I-1/PG] `post-tool-use.py:140` `return None` 冗長
- [I-2/SE] `card_generator.py:collect_spec_drift_context()` の specs_dir.glob が非再帰
- [I-3/SE] `scale_detector.py:_check_plan_a()` の reason 文字列がハードコード
- [I-4/SE] `gitleaks_scanner.py:_run_gitleaks()` の report_path 未定義時 NameError 経路
- [I-5/SE] `_hook_utils.py:get_project_root()` のフォールバック時に警告なし

## 解消された課題（参照用）

- パストラバーサル防止: `_validate_check_dir()` の追加により対応済み（イテレーション2）
- `run_command` の shell=False 固定は継続して維持されている
- [W-1旧] `_now_utc()` 冗長ラッパー → `now_utc_iso8601()` に集約済み（v4.3.0）
- [W-2旧] `now_iso8601()` 冗長ラッパー → 同上
- [W-4旧] tool_events 上限 → `_MAX_TOOL_EVENTS = 500` 追加済み（v4.3.0）
- [I-1旧] `_SCAN_EXCLUDE_DIRS` → モジュールレベル frozenset に移動済み（v4.3.0）
- run_pipeline.py の `line_count` が analyzers 未検出時も常時カウントされるよう修正済み（監査 S2a）
