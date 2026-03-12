---
name: hook_structure_quality_issues
description: .claude/hooks/ の実装構造と既知の品質課題（2026-03-12 イテレーション2更新）
type: project
---

hooks/ 構成: _hook_utils.py（共通Utils）/ pre-tool-use.py / post-tool-use.py / pre-compact.py / lam-stop-hook.py

**Why:** イテレーション2監査（2026-03-12）で発見した再発防止のため記録。

**How to apply:** 次回レビュー時に同一 Issue の再発確認に使う。

## 残存課題（イテレーション2時点）

- [W-3/SE] lam-stop-hook.py の main() が約 173 行（50行制限超過、前サイクルから未解消）
- [W-1/SE] post-tool-use.py の `_now_utc()` が `now_utc_iso8601()` の単純ラッパーで冗長
- [W-2/SE] pre-compact.py の `now_iso8601()` も同様の冗長ラッパー
- [W-4/SE] `_handle_loop_log()` の tool_events に上限がなく長期運用で JSON が肥大化
- [W-5/SE] `_write_state()` がテストファイル2箇所に重複定義（conftest.py への移動が必要）
- [W-6/SE] `test_lam_stop_hook.py` の `spec.loader.exec_module` に None チェックがない
- [I-1/PG] `_SCAN_EXCLUDE_DIRS` が関数内定義（毎回 frozenset を生成）
- [I-3/SE] `atomic_write_json` のネストディレクトリ自動作成テストが欠落

## 解消された課題（参照用）

- パストラバーサル防止: `_validate_check_dir()` の追加により対応済み（イテレーション2）
- `run_command` の shell=False 固定は継続して維持されている
