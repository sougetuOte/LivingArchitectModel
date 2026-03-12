---
name: test_structure_duplication
description: テストスイート構成と重複問題（2026-03-12 初回監査）
type: project
---

テストスイートが 2 か所に分散: `.claude/hooks/tests/`（subprocess ベース）と `tests/`（importlib ベース）

**Why:** 初回監査で判明。重複カバレッジと不整合な _write_state / DEFAULT_STATE 定義が 3 ファイルに散在。

**How to apply:** テスト追加時は既存ヘルパーの重複がないか確認する。conftest.py の hook_runner fixture は hooks/tests/ にのみ存在。

主要な既知課題:
- `_write_state()` が test_stop_hook.py / test_loop_integration.py / tests/test_lam_stop_hook.py の 3 ファイルに重複
- `DEFAULT_STATE` が test_stop_hook.py と test_loop_integration.py の 2 ファイルに重複
- tests/test_lam_stop_hook.py が hooks/tests/ の conftest.py fixture を使わず独自 _run_hook() を持つ（二重メンテナンス）
- _run_security() / _detect_*() 系の関数に直接ユニットテストがない
- test_loop_integration.py 内で `import datetime` がテストメソッドのローカルスコープ内に重複 (L199, L223)
