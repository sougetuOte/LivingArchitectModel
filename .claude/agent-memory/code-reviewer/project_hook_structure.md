---
name: hook_structure_quality_issues
description: .claude/hooks/ の実装構造と既知の品質課題（2026-03-12 イテレーション2更新）
type: project
---

hooks/ 構成: _hook_utils.py（共通Utils）/ pre-tool-use.py / post-tool-use.py / pre-compact.py / lam-stop-hook.py

**Why:** イテレーション2監査（2026-03-12）で発見した再発防止のため記録。

**How to apply:** 次回レビュー時に同一 Issue の再発確認に使う。

## 残存課題（包括フルスキャン更新）

- [W-3/SE] lam-stop-hook.py の main() が約 173 行（50行制限超過、前サイクルから未解消）
- [W-5/SE] `_write_state()` がテストファイル2箇所に重複定義（conftest.py への移動が必要）
- [W-6/SE] `test_lam_stop_hook.py` の `spec.loader.exec_module` に None チェックがない
- [I-3/SE] `atomic_write_json` のネストディレクトリ自動作成テストが欠落
- [C-4/PM] `_SECRET_PATTERN` が .md ファイルで偽陽性（対象拡張子の見直し必要）
- [C-5/SE] `conftest.py hook_runner` が os.environ を全コピー（最小限に制限すべき）
- [C-6/SE] ESLint flat config (eslint.config.*) 未検出
- [C-7/SE] `pre-compact.py` 専用テストが存在しない
- [C-8/SE] `go test` カウント正規表現が脆弱（`\nok ` → `^ok\t` 推奨）
- [C-10/PM] `_validate_check_dir` が PROJECT_ROOT 外の実在パスを許可

## 解消された課題（参照用）

- パストラバーサル防止: `_validate_check_dir()` の追加により対応済み（イテレーション2）
- `run_command` の shell=False 固定は継続して維持されている
- [W-1] `_now_utc()` 冗長ラッパー → `now_utc_iso8601()` に集約済み（v4.3.0）
- [W-2] `now_iso8601()` 冗長ラッパー → 同上
- [W-4旧] tool_events 上限 → `_MAX_TOOL_EVENTS = 500` 追加済み（v4.3.0）
- [I-1旧] `_SCAN_EXCLUDE_DIRS` → モジュールレベル frozenset に移動済み（v4.3.0）
