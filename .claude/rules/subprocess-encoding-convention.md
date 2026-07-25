# subprocess Encoding 規約

LAM リポジトリ内の Python が `subprocess.run(...)` でテキスト出力を読み取る際の
`encoding` 指定を統一する規約（W1-R2-T5 / FR-7）。

## 背景（grounding — 実測済みの実害）

Windows（cp932 ロケール）環境で `subprocess.run(..., text=True)` を `encoding=`
**未指定**で呼ぶと、`text=True` はロケール既定エンコーディング（Windows では
概ね cp932）でデコードを行う。git の commit message や外部ツールの JSON 出力は
UTF-8 で書かれていることが多く、両者が食い違うと `UnicodeDecodeError` /
`UnicodeEncodeError` で失敗する。

本 Task の BUILDING セッション中に、**この失敗を実機で 3 パターン自然再現**した
（monkeypatch を用いた仮想再現ではなく、実際の失敗）:

1. **`UnicodeDecodeError`（親プロセス側のデコード失敗）**: `/quick-save` の
   dashboard 生成時、`.claude/scripts/dashboard/parsers/git_history.py`
   （修正前）が `subprocess.run(["git", "log", ...], text=True)` で
   日本語コミットメッセージ（例: `983110b docs(M-1): ADR-0011 ...`）を読み取り、
   `UnicodeDecodeError: 'cp932' codec can't decode byte 0x9c in position 53`
   で失敗した。
2. **同型の `PytestUnhandledThreadExceptionWarning`**: フルスイート pytest 実行時に
   `test_git_history_parser.py::test_parse_with_real_git_log` と
   `test_wave2_integration.py` で、`subprocess.py` の `_readerthread` 内で同様の
   `UnicodeDecodeError`（`'cp932' codec can't decode byte 0x8f ...`）が
   バックグラウンドスレッド例外として発生していた。
3. **`UnicodeEncodeError`（子プロセス側のエンコード失敗）**: `.claude/hooks/analyzers/scale_detector.py`
   の `format_scale_detection()` はチェックマーク系記号（✓/✗ に相当する
   U+2713 / U+2717）を出力するが、これは cp932 の文字集合に含まれない。
   `.claude/hooks/analyzers/tests/test_e2e_review.py::TestCLIEntryPoint` が
   この CLI を `env=build_allowlisted_env(...)`（`PYTHONIOENCODING` 未設定）で
   起動していたため、**子プロセス自身の `print()` が cp932 で
   `UnicodeEncodeError` を送出し**、`test_cli_outputs_scale_detection_json` /
   `test_cli_stdout_contains_scale_detection_header` の 2 テストが実際に FAIL
   していた（本 Task で修正済み。詳細は下記「誤例」参照）。

## 適用範囲

LAM リポジトリ内の Python 全域: `.claude/scripts/`, `.claude/hooks/`,
`.claude/tests/`。

## 規約本文

### 既定形

```python
result = subprocess.run(
    [...],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
)
```

- `encoding="utf-8"`: git・大半の CLI ツールの既定出力エンコーディングに合わせる
  （Windows のロケール既定 cp932 に依存させない）。
- `errors="replace"`: 万一エンコーディングが一致しなくても例外で落とさず、
  置換文字で処理を継続する安全網。**クラッシュ防止であり正しいデコードの
  保証ではない**ため、既知の非 UTF-8 出力（例: Windows コマンドのローカライズ
  メッセージ）を扱う場合は個別に検討すること。

### カスタム `env=` を渡す場合: `_utf8_env()` パターン

子プロセスが **Python 自身**であり、かつカスタム `env=`（例:
`build_allowlisted_env()`）を渡す場合は、`PYTHONIOENCODING=utf-8` を注入して
子プロセス自身の標準出力エンコーディングも UTF-8 に固定する。既存実装:

```python
# .claude/tests/rules/test_reference_resolution.py:138-144
def _utf8_env():
    """Windows cp932 の em dash / 全角文字 UnicodeEncodeError 回避。"""
    import os

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return env
```

`build_allowlisted_env()`（`.claude/hooks/_hook_utils.py`）ベースの環境を使う
場合も同様に `PYTHONIOENCODING` を追加する:

```python
env = build_allowlisted_env({"PYTHONPATH": str(hooks_dir), "PYTHONIOENCODING": "utf-8"})
result = subprocess.run(
    [sys.executable, str(script_path), ...],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
    env=env,
)
```

**適用が必須になる条件**: 子プロセスが Python であり、かつその出力が
cp932 に含まれない Unicode 文字（記号・絵文字等）を含みうる場合。子プロセスが
非 Python（Node.js / Rust バイナリ等）の場合、`PYTHONIOENCODING` は子プロセスの
挙動に影響しないため、既定形（デコード側の `encoding="utf-8", errors="replace"`）
のみで十分である。

### 例外規定（対象外）

以下は本規約の対象外とし、`encoding=` の追加を要求しない:

- **ASCII 固定出力しか返さない呼び出し**（例: `["claude", "--version"]`,
  `[sys.executable, "-m", "pytest", "--version"]`）。バージョン文字列は
  ASCII で構成されるため、文字化け・デコード失敗のリスクが実質的にない。
- **`text=True` を指定せず、stdout をテキストとして消費しない呼び出し**
  （例: `capture_output=True` のみでバイト列を得て、JSON レポートは別途
  `Path.read_text(encoding="utf-8")` 等で明示エンコーディング指定して読む場合）。
  この場合デコードは別の箇所で行われるため、当該 `subprocess.run(...)` 自体は
  対象外。
- **コメント内の記述**（実行されないコード片）。

## 正例

`.claude/scripts/r-1-git-log-usage.py:45-52`:

```python
def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd="D:/work7/LivingArchitectModel",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
```

## 誤例（修正前の実装 / 本 Task で修正済み）

- `.claude/scripts/r1_inventory.py:59-62`（修正前）:
  ```python
  result = subprocess.run(
      ["git", "ls-files"],
      capture_output=True, text=True, check=True,
  )
  ```
- `.claude/scripts/dashboard/parsers/git_history.py:63-68`（修正前）:
  ```python
  result = subprocess.run(
      ["git", "log", "--oneline", "-100"],
      cwd=str(self._project_root),
      capture_output=True,
      text=True,
  )
  ```
- `.claude/hooks/analyzers/tests/test_e2e_review.py`（修正前・実害あり）:
  `env=build_allowlisted_env({"PYTHONPATH": str(hooks_dir)})`（`PYTHONIOENCODING`
  未設定）で `scale_detector.py` を起動しており、子プロセス自身の
  `UnicodeEncodeError` によって CLI が非ゼロ終了し、2 テストが実際に FAIL
  していた（上記「背景」#3 参照）。

いずれも `.claude/tests/rules/test_subprocess_encoding_convention.py` で
回帰テスト化済み。

## grep baseline

### 本 Task が対象とした baseline（着手時に指示された測定式）

```bash
grep -rn "subprocess.run(" .claude/scripts .claude/hooks | grep -v "encoding="
```

- **着手時**: 20 件
- **完了後**: 20 件（変化なし — 下記「baseline の既知の限界」参照）

### baseline の既知の限界（重要）

上記コマンドは **行単位** で `encoding=` の有無を判定するため、
`subprocess.run(` と `encoding=` が別の行にある複数行呼び出し（本規約が
推奨するスタイルそのもの）を **false positive として誤検出し続ける**。
実際、本 Task で 14 件を修正した後も生の行数は 20 件のまま変化しなかった
（修正後の呼び出しも `encoding="utf-8"` を次行以降に書いているため）。

20 件の内訳（本 Task の実測・個別判定）:

| 区分 | 件数 | 内容 |
|---|---:|---|
| 修正対象（今回 `encoding="utf-8", errors="replace"` を追加） | 14 | 下記「修正対象ファイル」参照 |
| 対象外（例外規定に該当） | 4 | `detect-permission-mode.py:84`（`--version`）/ `check_g1_test.py:109`（`--version`）/ `gd_state.py:598`（コメント行）/ `gitleaks_scanner.py:203`（stdout をテキスト消費しない） |
| false positive（複数行呼び出しで既に `encoding=` 済み） | 2 | `r-1-git-log-usage.py:45` / `verify_import_availability.py:123` |

**修正対象ファイル（14 件・9 ファイル）**:
`.claude/scripts/dashboard/parsers/git_history.py`,
`.claude/scripts/r1_inventory.py`,
`.claude/hooks/analyzers/javascript_analyzer.py`（2 箇所: eslint / npm audit）,
`.claude/hooks/analyzers/python_analyzer.py`（2 箇所: ruff / bandit）,
`.claude/hooks/analyzers/rust_analyzer.py`（2 箇所: clippy / cargo audit）,
`.claude/hooks/analyzers/tests/test_e2e_review.py`（3 箇所）,
`.claude/hooks/checkers/check_g1_test.py`（1 箇所 / `run_check()` 本体呼び出し。
`--version` 探索呼び出しは対象外のまま）,
`.claude/hooks/lam-stop-hook.py`,
`.claude/hooks/tests/conftest.py`。

### 参考: design.md §4.4 が指定するより広い baseline

design.md / tasks.md の grep 式は `.claude/tests` も含む
（`grep -rn "subprocess.run(" .claude/scripts .claude/hooks .claude/tests | grep -v encoding=`）。
本 Task 実測ではこの式で **28 件**（本 Task の 20 件 baseline + `.claude/tests`
配下 8 件）がヒットする。うち 2 件（`test_reference_resolution.py:149,161`）は
`_utf8_env()` パターンを既に用いた false positive、残り 6 件
（`test_build_dashboard.py` 4 箇所 / `test_wave2_integration.py` 1 箇所 /
`test_r1_inventory.py` 1 箇所）は本 Task の判定対象（F4 の 20 件）に
含まれておらず、**本 Task のスコープ外として未着手のまま残っている**。
これは今後の rule 化 Task（またはフォローアップ）で回収すべき既知のギャップ
として記録する。

## 検証コマンド

複数行呼び出しに対応した正確な検証は、行単位 grep ではなく
括弧対応抽出を行う以下の pytest で行う（規約の第一の検証手段）:

```bash
bash .claude/scripts/py_invoke.sh -m pytest .claude/tests/rules/test_subprocess_encoding_convention.py -o addopts=""
```

行単位 grep は「修正候補の一次スクリーニング」としてのみ用い、各ヒットは
本規約の「例外規定」「正例」と照合して個別に Read で確認すること
（false positive を機械的に除外できないため）。

## 権限等級

本ルールファイルの変更: **PM級**（`.claude/rules/` 配下）。

## 参照

- `docs/specs/r-2-consolidation/design.md` §4.4（T5: subprocess encoding 規約）
- `docs/specs/r-2-consolidation/tasks.md` W1-R2-T5
- `docs/specs/r-2-consolidation/requirements.md` FR-7（機構を伴う Task の Done 形式）/ NFR-2（Python 3.8 互換性）
- `.claude/tests/rules/test_subprocess_encoding_convention.py`（本規約の回帰テスト・静的検査）
- `.claude/tests/rules/test_reference_resolution.py:138-144`（`_utf8_env()` の既存実装）
- `.claude/hooks/_hook_utils.py`（`build_allowlisted_env()`）
- `.claude/rules/test-result-output.md`（構成の参考元）
