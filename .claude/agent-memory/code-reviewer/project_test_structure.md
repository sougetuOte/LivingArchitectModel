---
name: test_structure_duplication
description: テストスイート構成と重複問題（2026-03-12 初回監査 → 2026-06-02 一元化）
type: project
---

テストスイートは 2 か所: `.claude/hooks/tests/`（hook 本体・subprocess/in-process 混在）と
`.claude/hooks/analyzers/tests/`（analyzer 群）。同時実行で **663 passed**（2026-06-02 時点）。

**Why:** 初回監査（2026-03-12）では root `tests/`（importlib ベース）が併存し、重複カバレッジと
conftest 衝突（`from conftest import write_state` が root 起動時に root conftest へ解決され ImportError）が
あった。2026-06-02 の監査 CP-C ② で root `tests/` を hooks/tests/ へ一元化し削除（コミット 21afc79 / 44f0dbc）。

**How to apply:** テスト追加時は既存ヘルパーの重複がないか確認する。state 書込は
`conftest.py::write_state` fixture（`.claude/hooks/tests/conftest.py:110`）を使う（自前実装を増やさない）。
hook 起動は同 conftest の `hook_runner` fixture（subprocess・クリーン環境・timeout=30）を使う。

主要な課題（2026-06-02 Stage2-iter1 監査で確認）:
- ✅ 解消: `_write_state()` の 3 ファイル重複 → `conftest.py::write_state` fixture に一元化
- ✅ 解消: root `tests/test_lam_stop_hook.py` の独自 `_run_hook()`（二重メンテナンス）→ root 削除で消滅
- ✅ 解消: `test_loop_integration.py` の `import datetime` ローカルスコープ重複 → モジュールトップに集約
- ⚠️ 残存: `DEFAULT_STATE` が `test_stop_hook.py:17` と `test_loop_integration.py:21` の 2 ファイルに重複（command フィールド値が微差）
- ⚠️ 残存: `_detect_analyzers()` / `_persist_results()` に直接ユニットテストがない（`_run_security` 系は各言語 Analyzer のテストでカバー済み）
- ℹ️ 未使用 import F401: combined_issues.py:10 / test_e2e_review.py:12,23 / test_gitleaks_scanner.py:22（ruff 対象、既報）
