# 監査レポート S3: autonomous サブシステム

対象: `.claude/hooks/autonomous_state.py` / `.claude/hooks/checkers/check_g1_test.py` / `.claude/hooks/checkers/__init__.py` / `.claude/settings.autonomous.json` / `.claude/hooks/lam-stop-hook.py`（autonomous フロー部）
日付: 2026-06-01 / Pass 1

---

## サマリー

Critical: 2 / Warning: 4 / Info: 3 ／ 評価: **Yellow**

Critical が 2 件あるため Green State ではない。いずれも FR-4.1b（モデルの自己宣言を完了根拠にしない）またはフェイルセーフの方向性に関わる安全重要部の欠陥。

---

## Critical

### [Critical] lam-stop-hook.py:273 — `stop_hook_active` 再帰ガードを autonomous フローで適用しない

**概要**: `_handle_autonomous` は `stop_hook_active = input_data.get("stop_hook_active")` を取得し INFO ログに書き出すだけで、その値によって early exit しない（line 273-274）。`main()` の full-review フロー冒頭（`_check_recursion_and_state`、line 136）では `stop_hook_active=True` で即時停止するが、autonomous フローはその前に `_is_autonomous_active` で分岐し（line 330）、再帰ガードのパスを完全にバイパスする。

**影響**: autonomous フロー中に Claude Code が Stop hook を再帰的に発火させた場合（block の応答に対して再度 stop しようとした場合）、block cap を消費し続け、設計意図（D1「`stop_hook_active=true` を見て早期 exit して停止を許す」）に反する。結果として最大 8 回の連続 block の後にプラットフォームが override してターンを強制終了させる（D1 の block cap=8 制約）。

**根拠**: design D1 §「block cap 制約（T0-1 裏取り）」「`lam-stop-hook` は入力の `stop_hook_active` を見て進捗がなければ早期 exit して停止を許す（無限 block 回避）」。D3 §「`stop_hook_active=true` かつ進捗なしなら早期 exit（block cap=8 回避）」。

**修正案**: `_handle_autonomous` の冒頭（G1 checker 実行の前）で `stop_hook_active=True` かつ前回 iteration と同値なら `_stop()` する（または iteration が進捗しているなら block 継続を許容するロジックへ）。ログ出力で終わっている現状は対策なしと等価。

**等級**: SE（hook の内部ロジック変更、公開 API 変更なし）

---

### [Critical] lam-stop-hook.py:279 — state 読み取り失敗時に `_stop()` でフェイルオープン

**概要**: `_handle_autonomous` の state 読み取り（line 277-279）が例外を送出した場合、`_stop(log_file, "autonomous: state read error → normal stop")` を呼んで Claude の completion を許可している。

```python
try:
    state = json.loads(auto_state_file.read_text(encoding="utf-8"))
except Exception:
    _stop(log_file, "autonomous: state read error → normal stop")
```

**影響**: autonomous-state.json が壊れている・ロックされている・部分的に書き込まれている（クラッシュ後の断片）などの障害時に、G1 checker を一切実行せずに completion を許可する。これは FR-4.1b「モデルの自己宣言を完了の唯一根拠にしない」および D3「障害時に誤って completion させない（fail-safe 方向）」に直接違反する。G1 が実際には赤でも、状態ファイル障害のタイミングで停止が許可されてしまう。

**根拠**: `_run_g1_checker` の docstring（line 237-241）が「障害時は FAIL(2) 扱い。誤って completion させない（決定的 gate を維持）」と定義している。同じ fail-safe 方針が state read 障害時にも適用されるべき。

**修正案**: state 読み取り失敗時は `_stop()` ではなく `_block()` を呼ぶ（または G1 checker を project_root のみで実行してデフォルト FAILとして扱う）。ログに `ERROR` を記録した上で continuation を block し、ユーザーに state ファイルの修復を求める。

**等級**: SE

---

## Warning

### [Warning] lam-stop-hook.py:295-311 — `checker_results` を非アトミックに書き込む

**概要**: G1 checker 結果（line 295-297）と active/phase の更新（line 300-309）を一度の `_write_autonomous_state` で書く設計だが、`_write_autonomous_state`（line 226-233）は `file.write_text()` の単純書き込みで、`_hook_utils.atomic_write_json`（指数バックオフ付き tmpfile→replace）を使っていない。

**影響**: Windows 環境でファイルロック中に PermissionError が発生した場合、状態ファイルが空または中途書きになる。次回起動時に `_handle_autonomous` の state 読み取りが Critical #2 で指摘したエラーパスに流れる可能性がある。`atomic_write_json` がすでに存在するにもかかわらず未使用（コードの再利用機会の喪失）。

**根拠**: code-quality-guideline.md「Dead Code / Unreachable Branch」相当（利用可能な安全ユーティリティを使わない）。Windows では `file.write_text` の上書き中にプロセスが干渉すると破損しやすい。

**修正案**: `_write_autonomous_state` の実装を `_hook_utils.atomic_write_json` に委譲する。`autonomous_state.py` と `lam-stop-hook.py` 両方に影響するが変更は1行。

**等級**: SE

---

### [Warning] check_g1_test.py:109-110 — `FileNotFoundError` を PASS-skip として扱う

**概要**: `run_check` の subprocess 実行で `FileNotFoundError` が発生した場合（テストコマンドが PATH に存在しない）、`exit 0` と `PASS-skip` の detail を返している（line 109-110）。

```python
except FileNotFoundError:
    return 0, f"test command not found: {cmd[0]} (G1 PASS-skip)"
```

**影響**: `detect_test_command` がテストFWを検出した（pytest/npm/go/make のいずれかが設定ファイルから見つかった）にもかかわらず、コマンドが PATH にない場合に PASS として扱う。設定ファイルに pytest の記述があるが CI 環境で pytest がインストールされていない状態が「テスト全通過」と誤判定される。テストFWが検出されない場合のみ PASS-skip とする設計意図（docstring line 10）と、実装（コマンド未発見でも PASS）が矛盾している。

**根拠**: code-quality-guideline.md「仕様との明確な不一致（ロジックバグ）」、design D3「barrier exit 2=FAIL（stderr に赤の詳細）/ exit 0=PASS」。「検出されたがコマンドがない」は「未検出」とは性質が異なる障害。

**修正案**: `FileNotFoundError` は FAIL(2) として扱い、stderr に「test command not found: {cmd}」を出す。テストFW設定があるが実行できない環境での誤 PASS を防ぐ。

**等級**: SE（behavior 変更だが公開 API は変わらない。exit code 仕様の修正）

---

### [Warning] check_g1_test.py:50-51 — `pyproject.toml` の pytest 検出が過剰マッチ

**概要**: pytest の検出条件（line 50-51）が `"pytest" in content` と文字列全体に対する包含判定になっている。

```python
if "[tool.pytest" in content or "pytest" in content:
    return ["pytest"]
```

**影響**: pyproject.toml に `pytest` という文字列が任意の文脈（コメント行、パッケージ説明文 `"A tool inspired by pytest"` 等）で含まれていれば pytest テストが検出されたと誤判定される。pytest に依存しないプロジェクトで G1 checker が誤って pytest を実行し、FileNotFoundError または実際のテスト失敗でブロックする可能性がある。green-state-definition.md §3.1 の「テストFW自動検出」の精度要件に反する。

**根拠**: code-quality-guideline.md「仕様との明確な不一致（ロジックバグ）」。文字列包含の過剰マッチはセクションスコープの検出（`[tool.pytest.ini_options]` / `[tool.pytest]` セクションの有無）に留めるべき。

**修正案**: `"pytest" in content` を `re.search(r'^\[tool\.pytest', content, re.MULTILINE) is not None` または `"[tool.pytest" in content` のみに絞る（後者は既にある条件で十分）。あるいは `dependencies`/`dev-dependencies` の `pytest` 依存検出なら TOML パースで行う。

**等級**: SE

---

### [Warning] settings.autonomous.json:8-17 — `docs/specs/**` が deny パターンから欠落

**概要**: settings.autonomous.json の deny リストには `docs/adr/**` はあるが `docs/specs/**` がない。

現在の deny パターン:
- `.claude/rules/**`
- `docs/adr/**`
- `.claude/settings*.json`
- `.claude/hooks/**`
- `.claude/skills/autonomous/**`

**影響**: FR-9.1 の定義（requirements.md line 75）に「`docs/adr/` / `.claude/rules/` / `.claude/settings*.json` / `.claude/hooks/` / 自律モード自身のスキル・スクリプト定義」とあるが、design D5 FR-9_PATTERNS（line 161-164）には `docs/adr/**` のみで `docs/specs/**` は含まれていない。ただし FR-3.4（line 46）は「spec・ADR・rules 書換」を C層の即時ハードストップ対象と明示しており、仕様上は `docs/specs/**` も deny すべきである。`docs/specs/**` への書込が autonomous セッション中に許可されたままであり、仕様の無断改変が可能。

**根拠**: requirements FR-3.4「spec・ADR・rules 書換はキュー化対象外とし即時ハードストップ」、code-quality-guideline.md「仕様との明確な不一致（ロジックバグ）」。

**修正案**: `settings.autonomous.json` の deny に `"Edit(/docs/specs/**)"` と `"Write(/docs/specs/**)"` を追加。合わせて PreToolUse hook の FR-9 強制パターンにも `docs/specs/**` を追加（二重防御の整合）。

**等級**: PM（settings*.json の変更は PM 級）

---

## Info

### [Info] autonomous_state.py:37 — `DEFAULT_MAGI_LIMIT` と `DEFAULT_FULL_REVIEW_LIMIT` が build_initial_state に未反映

**概要**: `DEFAULT_MAGI_LIMIT = 3`、`DEFAULT_FULL_REVIEW_LIMIT = 1` が定義されているが（line 37-38）、`build_initial_state` 内の `escalation_budget` はハードコードされた数値リテラル（line 83-86）を使っており、定数を参照していない。

```python
"escalation_budget": {
    "magi_count": 0,
    "magi_limit": DEFAULT_MAGI_LIMIT,      # ← 定数を使っている
    "full_review_count": 0,
    "full_review_limit": DEFAULT_FULL_REVIEW_LIMIT,  # ← 定数を使っている
},
```

実際には定数を使っているため問題なし（コードを再確認: line 83-86 は正しく定数参照）。ただし `DEFAULT_PM_QUEUE_LIMIT = 5` は `build_initial_state` で直接 `DEFAULT_PM_QUEUE_LIMIT` として参照されており一貫性がある。全体として定数定義と使用は整合している。

→ 実際には問題なし。取り消し。

---

### [Info] lam-stop-hook.py:226-233 — `_write_autonomous_state` のエラーハンドリングが Silent Failure に近い

**概要**: `_write_autonomous_state` が `except Exception as e: sys.stderr.write(...)` で例外をログだけして続行する（line 232-233）。書き込みが失敗した場合でも呼び出し元は成功と見なし、続く `_stop()` / `_block()` が実行される。

**影響**: 状態の永続化に失敗した後に completion が許可される（または block が送出される）可能性があるが、状態が失われるだけで完全なデータ損失にはならない（次回起動時に state なしとして停止）。Critical 判定には至らないが Silent Failure 傾向がある。

**等級**: SE（修正対応は Warning #1 の atomic_write_json 採用でカバーされる）

---

### [Info] check_g1_test.py:13 — checker パスが Stop hook から呼ばれる際の相対パス前提

**概要**: docstring line 13「`python3 checkers/check_g1_test.py` としてサブプロセス実行する想定」とあるが、`_run_g1_checker`（lam-stop-hook.py line 242）では `_HOOKS_DIR / "checkers" / "check_g1_test.py"` の絶対パスで正しく呼んでいる。docstring が古い表記。コードは正しい。

---

### [Info] lam-stop-hook.py:97-118 — `_save_loop_log` のフィールドが autonomous スキーマと不整合

**概要**: `_save_loop_log` は `state.get("command")` / `state.get("target")` を参照しているが（line 97-99）、autonomous-state.json のスキーマ（D1）にはこれらのフィールドが存在せず（`spec_target` が対応）、`command` は lam-loop-state.json のフィールドである。`_handle_autonomous` の completion パス（line 302-304）では `_save_loop_log` を呼ばないため現状は実害なし。ただし将来 autonomous フローに completion ログを追加する場合、`spec_target` → `command`/`target` のマッピングが必要になる。

---

## 仕様乖離（design D1/D3/D7 ↔ 実装）

### D1 — block cap 対策の実装欠落（Critical #1 と連動）

**仕様**: design D1「`lam-stop-hook` は入力の `stop_hook_active` を見て進捗がなければ早期 exit して停止を許す（無限 block 回避）」

**実装**: `_handle_autonomous` は `stop_hook_active` を読み出し（line 273）、INFO ログ（line 274）を書くだけで early exit 条件を持たない。full-review フローの `_check_recursion_and_state`（line 136）にある `stop_hook_active=True → _stop()` が autonomous フローでは適用されない。

**影響度**: High（8 回 block でプラットフォームが強制終了 → max_iterations=20 の意図が活かせない）

---

### D3 — `checking → auditing` / `checking → done` フェーズ遷移の未実装

**仕様**: design D3 フロー step 4「全 exit 0 → `phase` を次へ進め、Green State の非決定的観点（G3/G4）評価へ。最終的に completion 許可（`active=false`）」。状態機械（line 87-88）「`checking → auditing`: G1/G2/G5 全 PASS → `Checking → Done`: Green State 達成」

**実装**: `_handle_autonomous` は G1 exit 0 で即座に `phase = "done"` / `active=false` として completion を許可（line 300-304）。`checking → auditing` のフェーズは存在せず、G2（lint）/ G5（security）も実行されていない（`checker_results` の `g2_exit`・`g5_exit` は常に `None` のまま）。

**影響度**: Medium（Wave 1 MVP のスコープ内と思われるが、D3 の設計と乖離が明示されていない。G1 のみで completion が許可される動作が意図的 MVP 省略か実装漏れか不明瞭）

**補足**: タスク定義（T1-2〜T1-4）が Wave 1 スコープを示しているが、設計書には「G1 のみでの一時 PASS」が明記されていない。コメントやスキーマの `g2_exit`/`g5_exit` は将来対応前提だが、現実装での「G1 PASS = completion」という短絡は非明示的省略である。仕様書に Wave 1 の explicit な limitation として記述することを推奨。

---

### D7 — `disableBypassPermissionsMode` の設定値が仕様と一致しない

**仕様**: design D7「`disableBypassPermissionsMode:"disable"` で `--dangerously-skip-permissions` 経由の deny 回避を封鎖」（仕様 line 190）。ここで値は `"disable"` と記述されている。

**実装**: `settings.autonomous.json` line 5 に `"disableBypassPermissionsMode": "disable"` がある。値が `"disable"` に一致している。

**実際には乖離なし**。ただし公式の取りうる値が `"disable"` か `true` か `false` かは裏取りが必要（T1-4 findings を確認すべき点）。仕様書と実装は整合。

---

### D1 — `phase` フィールドの状態遷移が部分的にしか実装されていない

**仕様**: D1「`phase`: `building | checking | auditing | blocked | done`」（line 80）

**実装**: `_handle_autonomous` は `"building"` と `"done"` のみ使用（line 308, 302）。`"checking"` フェーズへの遷移（= Stop hook 発火 = checker 実行中）が実装されていない。checker を実行する前後で `phase = "checking"` を書いて状態を記録すれば、クラッシュ時に「checker 実行中に落ちた」と診断できる。現状は G1 checker 実行中も `phase = "building"` のまま。

**影響度**: Low（診断可能性の低下のみ。動作には影響なし）

---

## 横断観察

1. **フェイルセーフの方向性が混在している**: `_run_g1_checker` は一貫して障害 → FAIL(2)（フェイルセーフ・fail-closed）の方針だが、`_handle_autonomous` の state 読み取り障害は → PASS（fail-open）と逆方向になっている（Critical #2）。autonomous サブシステム全体でフェイルセーフ方針を統一すべき。

2. **`atomic_write_json` の未活用**: `_hook_utils.py` には Windows PermissionError 対策のアトミック書き込みユーティリティが実装済みだが、`_write_autonomous_state` はこれを使わずに直接 `write_text` を呼んでいる。プロジェクトの Windows 環境（CLAUDE.md 記載）を考慮すると、状態ファイルの書き込み安定性に影響する可能性がある。

3. **Wave 1 MVP 省略の透明性**: G2/G5 checker 未実装は意図的省略と思われるが、コード・仕様書いずれにも「Wave 1 では G1 のみ」と明記されていない。`checker_results` に `g2_exit: null` が残る動作が意図的かどうかが監査者・将来の実装者に不明瞭。仕様書の D3 に「MVP(Wave 1): G1 のみ実装。G2/G5 は後続 Wave で追加」と一行追記することで乖離を解消できる。

4. **FR-9 deny パターンの `docs/specs/**` 欠落**（Warning #4）は、FR-3.4「spec 書換は即時ハードストップ」という要件の実装的強制点が抜けている最大のギャップ。`docs/adr/**` は保護されているが `docs/specs/**` は未保護という非対称性は、仕様の意図から見て不自然であり PM 級での対応が必要。
