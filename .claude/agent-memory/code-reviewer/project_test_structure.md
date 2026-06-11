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

主要な課題（2026-06-10 iter2 ゼロベース監査で更新）:
- ✅ 解消: `_write_state()` の 3 ファイル重複 → `conftest.py::write_state` fixture に一元化
- ✅ 解消: root `tests/test_lam_stop_hook.py` の独自 `_run_hook()`（二重メンテナンス）→ root 削除で消滅
- ✅ 解消: `test_loop_integration.py` の `import datetime` ローカルスコープ重複 → モジュールトップに集約
- ✅ 解消: `test_e2e_review.py` / `test_gitleaks_scanner.py` の F401 除去済み（iter1修正）
- ~~⚠️ 残存 Warning: `DEFAULT_STATE` が 2 ファイルに重複~~ → Info 降格（B-2 iter2 TEST-A-4: 重複2回で Rule of Three 未達・記録のみ）
- ~~⚠️ 残存 Warning: `pytest.mark.e2e_llm` / `e2e_convergence` がマーカー未登録~~ → ✅ 棄却（B-2 iter1 TEST-B-7: 登録済みを確認・再検出だった）
- ~~⚠️ **NEW iter2 Warning [TEST-A-2]**: `test_stop_hook_autonomous.py:13-16` の `sys.path.insert` 直接操作~~ → ✅ 棄却（B-2 iter2: W-15 で意図的に導入された修正。モジュールレベル import に必須・`not in sys.path` ガード付き）
- ~~⚠️ **NEW iter2 Warning [TEST-A-1]**: `test_no_analyzed_marker_counts_all_entries` テスト名が仕様を反映せず~~ → ✅ 解消（B-2 iter2 docstring 補強 + iter3 W3-5 で `test_no_analyzed_marker_with_transition_counts_all_entries` にリネーム済み）
- ~~ℹ️ 残存 Info: `test_hook_utils.py:188` テスト名と実動作のズレ（`test_atomic_write_json_creates_parent`）~~ → ✅ 解消（B-2 iter1 W-10: 親なしパスでの検証に修正済み）
- ℹ️ 残存 Info: `combined_issues.py` の F401 は意図的（Issue 検出サンプル）— 修正しないこと
- ℹ️ **NEW iter2 Info [TEST-A-3]**: `test_post_tool_use.py` の `TestPostToolUseFailure._failure_input` が `self` を使わないインスタンスメソッド（staticmethod 化が望ましい）
- ℹ️ **NEW iter2 Info [TEST-A-5]**: `stop_hook` fixture が `test_lam_stop_hook_env_allowlist.py` と `test_tdd_notification_b.py` に重複（conftest.py 共通化の余地あり）
