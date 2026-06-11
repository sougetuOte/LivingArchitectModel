---
name: hook_structure_quality_issues
description: .claude/hooks/ の実装構造と既知の品質課題（2026-06-10 イテレーション5更新）
type: project
---

hooks/ 構成: _hook_utils.py（共通Utils）/ pre-tool-use.py / post-tool-use.py / pre-compact.py / lam-stop-hook.py / autonomous_state.py（新規）
checkers/: __init__.py / check_g1_test.py（G1 決定的ゲート）
analyzers/: base.py / config.py / orchestrator.py / chunker.py / reducer.py / run_pipeline.py / scale_detector.py / state_manager.py / gitleaks_scanner.py / python_analyzer.py / javascript_analyzer.py / rust_analyzer.py / card_generator.py（1,305行・⑤送り分割計画済み）

**Why:** イテレーション5監査（2026-06-10 full-review Stage 2）で更新。

**How to apply:** 次回レビュー時に同一 Issue の再発確認に使う。

## 残存課題（イテレーション3 SRC-A ゼロベース監査 2026-06-10 更新）

### Critical（要対応）

なし（B-2 full-review iter7 で Green State 確定・2026-06-11）。

- ~~[C-iter3-1/SE] `lam-stop-hook.py:285-292` `_write_autonomous_state` が非アトミック書き込み。~~ → ✅ 解消（B-2 iter1 C-1: `atomic_write_json` に置換済み）
- ~~[C-iter6-1/SE] `gitleaks_scanner.py:246` `_parse_gitleaks_json` で `data` が list でない場合（None/dict）に TypeError/AttributeError が未捕捉。~~ → ✅ 解消（B-2 iter2 W2-1: `isinstance(data, list)` ガード + 警告ログ + TDD テスト追加済み）

### Warning（要対応）

オープン残: ⑤送り/継続の 2 件のみ（B-2 iter7 Green State 確定時点・2026-06-11）。

- [W-iter2-4/SE] `card_generator.py:_bfs_upstream()` が `queue.pop(0)` で O(N) 削除（⑤送り）
- [W-iter2-5/PM] ESLint flat config (eslint.config.*) 未検出（javascript_analyzer.py:53-116）（継続）

#### B-2 で解消/降格済み（2026-06-11 整理）

- ~~[W-SrcA-1/SE] `check_g1_test.py` `_parse_junit_xml` ValueError 未捕捉~~ → ✅ 解消（`except ValueError: return None` 実装済み・iter3 実行検証済み。帰属訂正: 該当は post-tool-use 側 = B-2 iter2 W2-2）
- ~~[W-SrcA-2/SE] `_hook_utils.py` `get_tool_response` Dead Code~~ → ✅ 解消（B-2 iter2 W2-3: 関数 + テスト7件削除済み）
- ~~[W-iter3-NEW-1/SE] `pre-tool-use.py:main()` 69行 Long Function~~ → ✅ 解消（B-2 iter3 W3-1: `_build_deny_reason`/`_emit_permission_response` 抽出済み）
- ~~[W-iter3-NEW-2/SE] `normalize_path()` 54行~~ → Info 降格（B-2 iter3: docstring/セキュリティ根拠コメントが大半・実質 ~25行）
- ~~[W-iter3-NEW-3/4/5] `_handle_test_result`/`_record_fail`/`_record_pass` の Long Function/Parameter Explosion~~ → Info 降格（B-2 iter3: 単一呼出経路の private helper 連鎖・dataclass 化は過剰抽象化。将来責務追加時に再検討）
- ~~[W-iter3-2/SE] `_read_current_phase` 二重読取リスク~~ → Info 降格（B-2 iter1 SRC-A-3 で記録のみ査定・iter3 再出は棄却）
- ~~[W-iter3-3/SE] `detect_test_command` の pyproject/Makefile 読取 OSError 未捕捉~~ → ✅ 解消（B-2 iter1 W-3）
- ~~[W-6/PM] `_FR9_PATTERNS` が hooks/ 配下テストも DENY~~ → ✅ PM 決着（B-2 iter1 PM-1: 現状維持 + `autonomous-mode/requirements.md` FR-9.1 に意図明示。ask 緩和案は future-candidates に記録）
- ~~[W-iter6-1/SE] `_find_sccs` 69行~~ → Info 降格（B-2 iter2: 反復 Tarjan の凝集性が高く分割は可読性低下リスク・将来リファクタ候補）
- ~~[W-iter6-2/SE] `chunk_file` 60行~~ → Info 降格（B-2 iter2: docstring 除く実質 ~40行で閾値内）
- ~~[W-iter6-3/SE] `_run_gitleaks` 57行~~ → ✅ 解消（B-2 iter2 W2-4: `_make_scan_error_issue()` 抽出で ~45行に削減）
- ~~[W-iter6-4/SE] `check_unused_reexports` 54行~~ → Info 降格（B-2 iter2: 実質41行で閾値内）

### Info（参考）
- [I-SrcA-1/SE] `lam-stop-hook.py:373-374` `_handle_autonomous`: `stop_hook_active` 変数がロギングのみ使用、再帰防止に未使用（設計非対称性・実害なし）。
- [I-SrcA-2/PG] `_hook_utils.py:292-294` `safe_exit`: `sys.exit` の薄いラッパーで附加価値なし（モックテスト用・意図的）。
- [I-1/PG] `post-tool-use.py:160` `return None` 冗長（継続）
- [I-iter3-4/SE] `lam-stop-hook.py:198-203` `_cleanup_state_file` が削除失敗を stderr 出力のみ（`_save_loop_log` の WARNING ログパターンと非一貫）
- [I-iter3-5/SE] `check_g1_test.py:107-129` `subprocess.run` に `shell=False` 未明示（_hook_utils.run_command との一貫性）
- ~~[I-iter3-NEW-1/Info] `lam-stop-hook.py:288-289` `_check_context_pressure` 最終フォールバックが `except Exception: pass`~~ → ✅ 解消（B-2 iter4 W4-1: `_log(WARN)` 追加済み）
- [I-2/SE] `card_generator.py:collect_spec_drift_context()` の specs_dir.glob が非再帰（⑤送り）
- [I-3/SE] `scale_detector.py:_check_plan_a()` の reason 文字列がハードコード（継続）
- [I-4/SE] `gitleaks_scanner.py:_run_gitleaks()` の report_path 未定義時 NameError 経路（継続）
- [I-iter2-2/SE] `card_generator.py:952` `_condense_sccs()` が SCC メンバー探索を全走査 O(N^2)（⑤送り）

## 解消された課題（参照用）

- パストラバーサル防止: `_validate_check_dir()` の追加により対応済み（イテレーション2）
- `run_command` の shell=False 固定は継続して維持されている
- [W-2旧/SE] `lam-stop-hook.py:_save_loop_log()` の `except Exception: pass` → WARNING ログ化済み（iter1 修正）
- import 統一（W-11）: iter1 で修正済み
- [W-1旧] `_now_utc()` 冗長ラッパー → `now_utc_iso8601()` に集約済み（v4.3.0）
- [W-4旧] tool_events 上限 → `_MAX_TOOL_EVENTS = 500` 追加済み（v4.3.0）
- run_pipeline.py の `line_count` が analyzers 未検出時も常時カウントされるよう修正済み（監査 S2a）
- [W-iter2-1/SE] `lam-stop-hook.py:_handle_autonomous()` 51行 → 32行に削減済み（iter3 実計測確認）
- [W-iter2-2/SE] `pre-tool-use.py:_determine_level_and_reason()` 60行 → 24行に削減済み（iter3 実計測確認）
- [W-iter2-3/SE] `pre-tool-use.py:_read_current_phase()` の `except Exception: pass` → stderr 記録済み（iter3 確認）
- [W-5/PM] `lam-stop-hook.py` の `_SECRET_PATTERN` → AUTONOMOUS モード関連リファクタで削除済み（iter3 確認）
- [I-5/SE] `_hook_utils.py:get_project_root()` のフォールバック時に警告なし → WARNING 追加済み（iter3 確認）
- [W-1/SE] `lam-stop-hook.py:main()` 51行 → 37行に削減済み（iter3 実計測確認）
- [W-3/SE] `pre-compact.py:update_session_state()` の OSError 未捕捉 → 全分岐で try/except OSError 実装済み（iter3 実計測確認）
- [W-SrcA-1] `check_g1_test.py:_parse_junit_xml` の ValueError 未捕捉 → `except ValueError: return None` 実装済み（iter3 実行検証済み）
