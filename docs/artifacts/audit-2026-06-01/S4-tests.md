# 監査レポート S4: テスト

対象: `.claude/hooks/tests/` (10 ファイル) + `tests/` (root: 3 ファイル) / 日付: 2026-06-01 / Pass 1

---

## サマリー

Critical: 0 / Warning: 7 / Info: 3 ／ 評価: Yellow

Green State 条件（Critical=0 かつ Warning=0）を満たしていない。
Warning 7 件はいずれもカバレッジ穴またはテスト品質の問題であり、
いくつかはバグが潜在してもテストで検出できない状態を意味する。

---

## カバレッジ穴（実装→テスト欠落の対応表）

| 実装 file:func | テスト有無 | リスク |
|---|---|---|
| `post-tool-use.py:_handle_test_result` (is_failure_event=True 分岐) | **なし** | PostToolUseFailure イベント時に XML を読まず直接 FAIL 記録する分岐が未テスト。誤動作しても検出できない |
| `post-tool-use.py:_handle_loop_log` (tool_events > 500 上限切り捨て) | **なし** | 500 件超のトリミングが正しく動作するかの保証がない |
| `post-tool-use.py:_handle_doc_sync_flag` (重複パス記録スキップ) | **なし** | 同一パスの二重追記防止ロジックのテストがない |
| `lam-stop-hook.py:_save_loop_log` | **なし** | ループ終了ログ保存関数が直接テストされていない |
| `lam-stop-hook.py:_run_g1_checker` (checker 未存在 / timeout / 例外 各 3 分岐) | **なし** | 障害時 FAIL(2) フォールバックが実運用で確認されていない |
| `lam-stop-hook.py:_handle_autonomous` (state_file 読み込みエラー分岐) | **なし** | autonomous フローでの state.json 壊れ時の graceful stop が未テスト |
| `pre-tool-use.py:_determine_level_and_reason` (コマンドなし・パスなし分岐) | **なし** | `no-path (default SE)` ケースの回帰テストがない |
| `lam-stop-hook.py:_check_recursion_and_state` (state_file parse エラー分岐) | **なし** | JSON 壊れ状態ファイル時の graceful stop が未検証 |
| `_hook_utils.py:run_command` (全体) | **なし** | `shutil.which` 失敗、timeout、例外の各 path が未テスト |
| `_hook_utils.py:atomic_write_json` (PermissionError retry / all-retry-exhausted) | **なし** | Windows PermissionError の exponential backoff + 全失敗時 RuntimeError が未テスト |
| `autonomous_state.py:state_file_path` (単純だが) | 間接テストのみ | 独立テストなし（D1 分離の検証は test_autonomous_state.py に存在） |
| `analyzers/scale_detector.py` (全体) | **なし** | `detect_scale`, `format_scale_detection`, `_persist_result` などが全未テスト |
| `analyzers/run_pipeline.py:run_phase0`, `count_lines`, `should_enable_static_analysis` | **なし** | Phase 0 パイプライン全体が `.claude/hooks/tests/` に存在しない（analyzers/tests/ は別途存在） |

---

## Warning

### [Warning] W-1: post-tool-use.py — PostToolUseFailure 分岐のカバレッジ穴

`.claude/hooks/post-tool-use.py:186-194`

`_handle_test_result()` の `is_failure_event=True` 分岐（PostToolUseFailure イベント時に
JUnit XML をスキップして直接 FAIL 記録する処理）に対応するテストが存在しない。
この分岐は「古い XML による誤判定を防ぐ」というセキュリティ的意図があり、
バグが混入しても `test_post_tool_use.py` には検出できない。

根拠: `Grep(PostToolUseFailure, .claude/hooks/tests/)` → 0件。
`hook_event_name` フィールドも test_post_tool_use.py のどの入力 JSON にも含まれていない。

修正案: `hook_event_name: "PostToolUseFailure"` を持つ入力で hook_runner を呼び出すテストを追加。
期待値: tdd-patterns.log に `"PostToolUseFailure event"` 文字列が記録される。
等級: SE

---

### [Warning] W-2: post-tool-use.py — tool_events 500 件上限のカバレッジ穴

`.claude/hooks/post-tool-use.py:281-283`

`_handle_loop_log()` で `_MAX_TOOL_EVENTS = 500` を超えた際に古いイベントを切り捨てる分岐が未テスト。
`test_post_tool_use.py:TestAtomicWriteSafety.test_atomic_write_safety` は 3 件しか積んでおらず、
上限切り捨て路を通らない。上限超過時の動作は保証されていない。

修正案: 501 件のイベントを積んで hook_runner を呼び出し、
最終的に `tool_events` が 500 件に収まり最古イベントが消えていることをアサートするテストを追加。
等級: SE

---

### [Warning] W-3: post-tool-use.py — doc-sync-flag 重複スキップの未テスト

`.claude/hooks/post-tool-use.py:234-247`

`_handle_doc_sync_flag()` には「既に記録済みのパスはスキップ」するロジックがあるが、
`TestDocSyncFlag` には同一ファイルを 2 回 Edit した場合のテストがない。
重複記録防止が壊れてもテストでは検出されない。

修正案: 同一 `src/main.py` に対して 2 回 Edit イベントを発行し、
`doc-sync-flag` に 1 行しか追記されないことをアサートするテストを追加。
等級: SE

---

### [Warning] W-4: lam-stop-hook.py — state.json パースエラー時の graceful stop が未テスト

`.claude/hooks/lam-stop-hook.py:143-147`

`_check_recursion_and_state()` では state_file が壊れた JSON の場合に
`_stop()` を呼ぶフォールバックが実装されているが、
`tests/test_lam_stop_hook.py` にも `.claude/hooks/tests/test_stop_hook.py` にも
「壊れた JSON の state_file を渡した際に exit 0 で停止する」テストが存在しない。

類似して `_handle_autonomous()` の state 読み込みエラー分岐
（`lam-stop-hook.py:278-279`）も未テスト。

根拠: Grep で "corrupt", "broken json", "parse error", "invalid state" を
`.claude/hooks/tests/` 内で検索しても 0 件。

修正案:
- `_write_state(project_root, "invalid json{{{")` 相当で壊れたファイルを書き込み、
  hook_runner の出力が exit 0 かつ stdout 空（停止許可）であることをアサート。
- autonomous フローでも `p.write_text("broken", ...)` で同様のテストを追加。
等級: SE

---

### [Warning] W-5: lam-stop-hook.py — _run_g1_checker の各障害 path が未テスト

`.claude/hooks/lam-stop-hook.py:236-263`

`_run_g1_checker()` では以下の 3 つの障害分岐が FAIL(2) として扱われる:
1. checker_path が存在しない（行244）
2. subprocess.TimeoutExpired（行255-257）
3. その他の例外（行258-260）

`test_stop_hook_autonomous.py` の `TestAutonomousStopHook` は G1 PASS/FAIL の
ハッピーパスしかカバーしていない。checker 自体が起動できない場合の動作が未テスト。

仕様上 "障害は FAIL(2) 扱い" であり（設計 D3 の「誤って completion させない」）、
この保証がテストで裏付けられていないことは保守上のリスク。

修正案:
- `_run_g1_checker` に monkeypatch で `subprocess.run` が `TimeoutExpired` を送出するケースを追加。
- checker_path を存在しない場所に向けた状態で hook_runner を呼び出し、`decision: "block"` になることを確認。
等級: SE

---

### [Warning] W-6: _hook_utils.py — run_command が全未テスト

`.claude/hooks/_hook_utils.py:172-203`

`run_command()` 関数（subprocess ラッパー）は test_hook_utils.py に一切テストがない。
- `shutil.which` 失敗時（コマンド未存在）の `(1, "", "command not found: ...")` 返却
- `subprocess.TimeoutExpired` 時の `(1, "", "command timed out...")` 返却
- その他例外時の `(1, "", str(e))` 返却

`run_command` が hook から呼ばれていることは確認できないが、
`_hook_utils.py` はユーティリティモジュールであり、
`safe_exit`, `log_entry`, `atomic_write_json` などは全てテストされているのに
`run_command` だけが完全に除外されている。Dead code の可能性がある一方、
将来使用時に障害パスが検証されていないリスクがある。

修正案: 少なくとも `command_not_found`, `timeout` の 2 パスをユニットテストで追加。
等級: SE

---

### [Warning] W-7: analyzers/scale_detector.py — 全関数が hooks/tests/ にテストなし

`.claude/hooks/analyzers/scale_detector.py:50-272`

`detect_scale()`, `format_scale_detection()`, `_persist_result()`,
各 `_check_plan_*()` など 14 関数が `.claude/hooks/tests/` 側に一切テストがない。

`analyzers/tests/` に独立テストスイートが存在するかを確認したところ、
`ls .claude/hooks/analyzers/tests/` に `test_run_pipeline.py` 等はあるが
`test_scale_detector.py` は**存在しない**。

`scale_detector.py` は `run_pipeline.py` から呼ばれる実質的な「Phase 0 の前段」であり、
`detect_scale()` のバグは Plan 選択ロジック全体を誤動作させる。

修正案: `analyzers/tests/test_scale_detector.py` を新規作成し、
`_determine_recommended_plans()` の境界値、`detect_scale()` の Plan 判定、
`format_scale_detection()` の出力形式を最低限テストする。
等級: SE

---

## Info

### [Info] I-1: root tests/ と .claude/hooks/tests/ の責任境界が不明確

`tests/test_lam_stop_hook.py` と `.claude/hooks/tests/test_stop_hook.py` は
同一の `lam-stop-hook.py` を対象とする重複スイートである。
両者の設計意図（root が旧世代 or 補完 or 回帰）がドキュメント化されていない。

重複テストケースの例:
- `test_no_state_file_stops` / `test_no_state_file_allows_stop` — 同一テスト
- `test_max_iterations_stops` — 両方に存在
- `test_recursion_guard` — 両方に存在

また root `tests/conftest.py` は `.claude/hooks/tests/conftest.py` の
`hooks_on_syspath`, `hook_runner`, `write_state` fixture をコピーせず簡略化している。
`tests/test_lam_stop_hook.py` は `_run_hook()` を独自実装しており、
hook の動作変更時に片方のスイートだけ更新され diverge するリスクがある。

修正案(Info): 役割分担を README または conftest の docstring に記述する（SE 相当）。
削除する場合は PM 級承認が必要（テストの削除）。
等級: SE（ドキュメント追加）または PM（重複テスト削除）

---

### [Info] I-2: test_settings_autonomous.py — 実ファイル依存テストのテスト分類

`test_settings_autonomous.py` は `.claude/settings.autonomous.json` の
実際のファイル内容を読み込むテストであり、scope="module" fixture を使用している。
このテストは「実ファイルが正しいか検証する」という意味で統合テストに近いが、
`.claude/hooks/tests/` 側に配置されている。

正しく機能しており現時点で問題はないが、
ファイルが一時的に削除された際の assert が分かりにくいエラーを出す
（`_SETTINGS_FILE.is_file()` が False の assert は `FileNotFoundError` でなく `AssertionError`）。

等級: Info（動作に問題なし）

---

### [Info] I-3: test_check_g1_test.py — pytest exit code 5（no tests collected）の暗黙的使用

`tests/test_lam_stop_hook.py:TestPmPending.test_pm_pending_false_continues_loop`（行 119-136）では
`pyproject.toml` だけを置いてテストなしの状態にすることで pytest exit 5 を期待し、
その結果として G1 FAIL → block を確認している。

pytest exit 5（"no tests collected"）が G1 FAIL 扱いになることは `check_g1_test.py` の設計上
正しいが、テスト名 `test_pm_pending_false_continues_loop` から「pytest exit 5」の意図が
読み取れない。読者が誤解する可能性がある。

等級: Info（テスト名の説明追加候補）

---

## 2スイートの整合所見

### 構造

| スイート | 場所 | テスト数 | 主な対象 |
|---|---|---|---|
| 主スイート | `.claude/hooks/tests/*.py` | 10 ファイル / 約 1,650 LOC | hooks + checkers + analyzers/tests間接 |
| サブスイート | `tests/*.py` | 3 ファイル / 約 400 LOC | lam-stop-hook, pre-compact の重複テスト |

### 重複と diverge リスク

root `tests/` は主スイートと比べて:
- **重複**: `test_lam_stop_hook.py` と `test_stop_hook.py` が同一 hook をテスト。
  テストケースの約 60% が同じシナリオをカバーしており、保守コストが倍増している。
- **後れを取っている**: root `tests/test_lam_stop_hook.py` は autonomous フローに関する
  テストを一切持たない。autonomous フロー追加（T1-3）後も root スイートは更新されておらず、
  古い設計仮定（stop hook が Green State 判定を行う）に部分的に依存したコードが残っている
  （`test_pm_pending_false_continues_loop` の G1 checker 間接実行）。
- **conftest の差異**: root `conftest.py` は `hooks_on_syspath`, `hook_utils` fixture を持たず、
  最小限の構成。hook_runner と write_state は root テスト内に独自実装されている。

### 推奨（Info）

root `tests/` を廃止して `.claude/hooks/tests/` に一元化するか、
root は smoke test として残し重複ケースを削除するかを明確化すること。
削除する場合は PM 級承認が必要。
