---
name: test_structure_duplication
description: テストスイート構成と重複問題（2026-03-12 初回監査 → 2026-06-02 一元化）
type: project
---

テストスイートは 2 か所: `.claude/hooks/tests/`（hook 本体・subprocess/in-process 混在）と
`.claude/hooks/analyzers/tests/`（analyzer 群）。同時実行で **668 passed**（2026-06-02 iter2 時点）。

**Why:** 初回監査（2026-03-12）では root `tests/`（importlib ベース）が併存し、重複カバレッジと
conftest 衝突（`from conftest import write_state` が root 起動時に root conftest へ解決され ImportError）が
あった。2026-06-02 の監査 CP-C ② で root `tests/` を hooks/tests/ へ一元化し削除（コミット 21afc79 / 44f0dbc）。

**How to apply:** テスト追加時は既存ヘルパーの重複がないか確認する。state 書込は
`conftest.py::write_state` fixture（`.claude/hooks/tests/conftest.py:110`）を使う（自前実装を増やさない）。
hook 起動は同 conftest の `hook_runner` fixture（subprocess・クリーン環境・timeout=30）を使う。

主要な課題（2026-06-02 Stage2-iter2 監査で確認）:
- ✅ 解消: `_write_state()` の 3 ファイル重複 → `conftest.py::write_state` fixture に一元化
- ✅ 解消: root `tests/test_lam_stop_hook.py` の独自 `_run_hook()`（二重メンテナンス）→ root 削除で消滅
- ✅ 解消: `test_loop_integration.py` の `import datetime` ローカルスコープ重複 → モジュールトップに集約
- ✅ 解消: `test_e2e_review.py` / `test_gitleaks_scanner.py` の F401 除去済み（iter1修正）
- ⚠️ 残存 Warning: `DEFAULT_STATE` が `test_stop_hook.py:17` と `test_loop_integration.py:21` の 2 ファイルに重複（command フィールド値が微差: "test_command" vs "full-review"）
- ⚠️ 残存 Warning: `test_e2e_review.py` の `pytest.mark.e2e_llm` / `e2e_convergence` がマーカー未登録（PM確認推奨）
- ℹ️ 残存 Info: `test_hook_utils.py:188` テスト名と実動作のズレ（`test_atomic_write_json_creates_parent`）
- ℹ️ 残存 Info: `combined_issues.py` の F401 は意図的（Issue 検出サンプル）— 修正しないこと
