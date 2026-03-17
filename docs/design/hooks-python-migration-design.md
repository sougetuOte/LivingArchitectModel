# フックスクリプト Python 一本化 — 設計書

## 1. ファイル構成

```
.claude/hooks/
├── pre-tool-use.py          # H1: 権限等級判定
├── post-tool-use.py         # H2: TDD パターン検出 + doc-sync-flag + ループログ
├── lam-stop-hook.py         # H3: 自律ループ収束判定
├── pre-compact.py           # H4: コンテキスト圧縮前保存
├── _hook_utils.py           # 共通ユーティリティ
├── tests/
│   ├── conftest.py          # pytest fixtures（旧 test-helpers.sh）
│   ├── test_hook_utils.py   # _hook_utils.py ユニットテスト
│   ├── test_pre_tool_use.py
│   ├── test_post_tool_use.py
│   ├── test_stop_hook.py
│   └── test_loop_integration.py
# bash 版 (.sh) は Wave 5 で全削除済み
```

## 2. 共通ユーティリティ (`_hook_utils.py`)

bash 版で各フックに重複していた処理を集約する。

```
_hook_utils.py
├── get_project_root() -> Path
│     # __file__ から ../../ を辿って PROJECT_ROOT を取得
│     # テスト用: 環境変数 LAM_PROJECT_ROOT が設定されていればそちらを優先
├── read_stdin_json() -> dict
│     # stdin から JSON を読み取り。失敗時は空 dict を返す
├── get_tool_name(data: dict) -> str
├── get_tool_input(data: dict, key: str) -> str
├── get_tool_response(data: dict, key: str, default)
├── normalize_path(file_path: str, project_root: Path) -> str
│     # 絶対パスを相対パスに正規化
├── log_entry(log_file: Path, level: str, source: str, message: str)
│     # TSV 形式のログ追記
├── now_utc_iso8601() -> str
│     # 現在時刻を UTC ISO 8601 形式（%Y-%m-%dT%H:%M:%SZ）で返す
├── atomic_write_json(path: Path, data: dict)
│     # tempfile + os.replace によるアトミック書き込み
│     # tempfile の dir= に対象ファイルと同ディレクトリを指定（クロスデバイス回避）
│     # Windows での PermissionError は exponential backoff で retry (3回, 100ms/200ms/400ms)
├── run_command(args: list[str], cwd: str, timeout: int) -> tuple[int, str, str]
│     # 型ヒント: Python 3.10+ 組み込み型。from __future__ import annotations で 3.8 互換
│     # subprocess.run ラッパー。shutil.which() でコマンド解決
│     # shell=False 固定。timeout は subprocess パラメータで制御（OS の timeout コマンド非依存）
└── safe_exit(code: int = 0)
      # sys.exit ラッパー
```

### 設計判断

- `_` プレフィックスで「内部モジュール」を明示（公開 API ではない）
- 標準ライブラリのみ: `json`, `sys`, `os`, `pathlib`, `tempfile`, `datetime`, `shutil`, `subprocess`
- 各フックは `#!/usr/bin/env python3` + `from _hook_utils import ...`

### クロスプラットフォーム注意事項

- **コマンド解決**: `shutil.which()` で実行パスを解決（Windows の `.cmd` 拡張子問題を吸収）
- **タイムアウト**: `subprocess.run(timeout=N)` を使用（OS の `timeout` コマンドは使わない）
- **アトミック書き込み**: `os.replace()` は Windows でファイルロック競合時に `PermissionError` を起こすため、retry ロジックを組み込む
- **パス区切り**: `pathlib.Path` を一貫使用。文字列パスとの比較時は `PurePosixPath` に正規化
- **改行コード**: ファイル書き込みは `open(..., newline='\n')` で `\n` 統一
- **タイムスタンプ**: `datetime.timezone.utc` で ISO 8601 形式に統一

## 3. 各フックの設計概要

### H1: pre-tool-use.py（権限等級判定）

```
入力: stdin JSON { tool_name, tool_input }
出力: exit 0（PG/SE 許可）or stdout JSON + exit 0（PM ask — 承認ダイアログ表示）

フロー:
1. read_stdin_json()
2. tool_name が Read/Glob/Grep/WebSearch/WebFetch → PG, exit 0
3. file_path / command を取得
4. normalize_path() でパス正規化
5. パスパターンマッチ → PG/SE/PM 判定
6. AUDITING フェーズの PG 級コマンド特別処理
7. ログ記録（トランケート 100 文字）
8. PM → ask JSON 出力（承認ダイアログ）、それ以外 → exit 0
```

bash 版との差分: jq/grep+sed フォールバック分岐が不要。`re` モジュールでパターンマッチ。

### H2: post-tool-use.py（TDD パターン検出 + doc-sync + ループログ）

```
入力: stdin JSON { tool_name, tool_input, tool_response }
出力: FAIL→PASS 遷移時は systemMessage を stdout に出力（tdd-introspection-v2.md §4.2 参照）。それ以外は exit 0 のみ。副作用としてファイル書き込み

フロー:
1. read_stdin_json()
2. テストコマンド判定（pytest/npm test/go test）
   → 失敗: tdd-patterns.log に FAIL 記録
   → 成功（前回失敗）: PASS 記録
3. Edit/Write + src/ 配下 → doc-sync-flag に追記（重複防止）
4. lam-loop-state.json 存在時 → tool_events に追記（atomic_write_json）
```

### H3: lam-stop-hook.py（自律ループ収束判定）

```
入力: stdin JSON { stop_hook_active, cwd, ... }
出力: exit 0（停止許可、出力なし）or stdout JSON {"decision":"block","reason":"..."} + exit 0（継続指示）
      # 注: "block" は唯一の有効な decision 値。停止許可時は JSON を出力しない（公式仕様準拠）

フロー:
1. 再帰防止チェック（stop_hook_active）
2. 状態ファイル確認（lam-loop-state.json）
3. 反復上限チェック
4. PreCompact 発火フラグによるコンテキスト残量チェック
5. Green State 判定（テスト自動検出 + lint 自動検出 + セキュリティチェック）
6. エスカレーション条件チェック（テスト数減少、Issue 再発）
7. 継続 or 停止

テスト/lint 実行: subprocess.run() でホワイトリスト方式
タイムアウト: subprocess の timeout パラメータ
```

最大のフック。bash 版 690 行 → Python 実装 約670 行（Green State 判定・セキュリティスキャン等の機能追加により当初見込みより増加）。

### H4: pre-compact.py（コンテキスト圧縮前保存）

```
入力: stdin JSON（使用しない）
出力: なし（exit 0）

フロー:
1. pre-compact-fired フラグにタイムスタンプ書き込み
2. SESSION_STATE.md に PreCompact 発火記録
3. lam-loop-state.json のバックアップ
```

最小のフック。bash 版 42 行 → Python で 30-40 行。

## 4. テスト設計

### conftest.py（共通 fixtures）

```python
@pytest.fixture
def project_root(tmp_path):
    """テスト用の仮プロジェクトルートを作成"""

@pytest.fixture
def hook_runner(project_root):
    """フックを subprocess で実行するヘルパー"""

# cleanup_files は不要: tmp_path ベースの project_root により自動クリーンアップされる
```

### テスト実行方式

3つの方式を併用する。テスト対象の性質に応じて使い分ける。

#### 1. subprocess 方式（ブラックボックステスト）

フックのエントリポイント（`main()`）を **subprocess として実行** してテストする。
理由: 実際の Claude Code 環境と同じ実行パスを通るため、パリティ検証として最も信頼性が高い。

```python
# conftest.py の hook_runner fixture が提供
def run_hook(hook_path, input_json, env=None):
    result = subprocess.run(
        [sys.executable, str(hook_path)],  # python3 ハードコード回避
        input=json.dumps(input_json),
        capture_output=True, text=True,
        env=env, timeout=30
    )
    return result
```

用途: フック全体の統合テスト、stdin/stdout/exit code の検証。

#### 2. importlib 方式（ホワイトボックステスト）

内部モジュール（`_hook_utils` 等）を **直接 import** してテストする。

```python
# conftest.py の hooks_on_syspath / hook_utils fixture が提供
@pytest.fixture()
def hook_utils(hooks_on_syspath):
    import _hook_utils
    return _hook_utils
```

用途: ユーティリティ関数の単体テスト、エッジケースの網羅的検証。
subprocess のオーバーヘッドなく高速に実行できる。

#### 3. conftest sys.path 方式（analyzers テスト）

`.claude/hooks/analyzers/tests/` 配下のテストで使用する。
`conftest.py` で `.claude/hooks` を `sys.path` に追加し、
`from analyzers.xxx import ...` の形式で直接 import する。

```python
# .claude/hooks/analyzers/tests/conftest.py
_HOOKS_DIR = Path(__file__).resolve().parent.parent.parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))
```

用途: analyzers パッケージの全テスト。subprocess オーバーヘッドなく、
かつ analyzers の内部構造（`base.Issue`, `config.ReviewConfig` 等）に
直接アクセスできる。外部ツール（ruff, bandit, gitleaks 等）の呼び出しは
`unittest.mock.patch` でモックする。

**注意**: この方式は analyzers がパッケージ構造（`__init__.py` なし、
`conftest.py` による sys.path 設定に依存）であることに起因する。
新規テストを追加する際は、必ず `.claude/hooks/analyzers/tests/` 配下に
配置すること。`tests/` 直下に配置すると import 解決に失敗する。

#### 使い分け基準

| 方式 | テスト配置先 | 対象 | 例 |
|------|------------|------|-----|
| subprocess | `.claude/hooks/tests/` | フック全体の振る舞い | stdin→stdout 変換、exit code |
| importlib | `.claude/hooks/tests/` | 内部関数の単体テスト | パス正規化、JSON パース、ログ出力 |
| conftest sys.path | `.claude/hooks/analyzers/tests/` | analyzers パッケージ | Issue 変換、パイプライン実行、gitleaks |

### テストケース対応表

| bash テスト | pytest テスト | 内容 |
|------------|--------------|------|
| test-pre-tool-use.sh TC-1 | - | shellcheck（Python 不要、削除） |
| TC-2 | test_read_tool_pg_allow | Read → PG 許可 |
| TC-3 | test_edit_specs_pm_ask | Edit docs/specs/ → PM ask |
| TC-4 | test_edit_rules_auto_generated_pm_ask | Edit rules/auto-generated/ → PM ask |
| TC-5 | test_absolute_path_normalization | 絶対パス正規化 |
| TC-6 | test_edit_src_se_allow | Edit src/ → SE 許可 |
| TC-7 | test_log_truncation | ログトランケート |
| - | test_glob_tool_pg_allow | Glob → PG 許可（追加） |
| - | test_grep_tool_pg_allow | Grep → PG 許可（追加） |
| test-post-tool-use.sh T1 | test_pytest_fail_recorded | pytest 失敗 → FAIL 記録 |
| T2 | test_pytest_pass_after_fail | 失敗→成功パターン |
| T3 | test_edit_src_doc_sync_flag | Edit src/ → doc-sync-flag |
| T4 | test_write_src_doc_sync_flag | Write src/ → doc-sync-flag |
| T5 | test_edit_docs_no_sync_flag | Edit docs/ → flag なし |
| T6 | test_loop_state_tool_events | ループログ追記 |
| T7 | - | jq なしフォールバック（Python 不要、削除） |
| T8 | test_npm_test_fail_recorded | npm test 失敗記録 |
| T9 | test_go_test_fail_recorded | go test 失敗記録 |
| T10 | test_non_test_command_no_record | 非テストコマンド → 記録なし |
| - | test_atomic_write_safety | アトミック書き込み安全性（追加） |
| test-stop-hook.sh TC-1 | - | shellcheck（削除） |
| TC-2 | test_no_state_file_stops | 状態ファイルなし → 停止 |
| TC-3 | test_max_iterations_stops | 上限到達 → 停止 |
| TC-4 | test_recursion_guard | 再帰防止 |
| TC-5 | test_makefile_test_fail_blocks | テスト失敗 → block |
| TC-6 | test_precompact_stops | PreCompact → 停止 |
| TC-7 | test_state_schema_valid | スキーマ正当性 |
| test-loop-integration.sh S-1 | test_green_state_stops_loop | 正常収束（Green State → 停止） |
| S-2 | test_test_failure_blocks, test_active_false_stops | PM 級エスカレーション |
| S-3 | test_below_max_continues, test_at_max_stops | 上限到達ライフサイクル |
| S-4 | test_precompact_recent_stops | コンテキスト枯渇（PreCompact） |
| S-5 | test_init_fail_then_converge | ライフサイクル全体 |

削除対象: shellcheck テスト（TC-1）、jq フォールバックテスト（T7）。これらは bash 固有のため。

注: H4（pre-compact）は既存 bash 版にもテストスイートが存在しないため、対応表に記載なし。手動パリティ確認 + Wave 1 での test_hook_utils.py で基盤を検証する。

### PostToolUseFailure イベントへの対応

公式仕様では `PostToolUse`（成功後）と `PostToolUseFailure`（失敗後）が別イベント。

**実機検証結果（2026-03-14）:**

- Bash ツールで exit code 0 の場合: `PostToolUse` が発火する
- Bash ツールで exit code != 0 の場合: `PostToolUseFailure` が発火する（`PostToolUse` は発火しない）

検証方法: 意図的に失敗するテストを実行し、`last-test-result` ファイルの更新有無で発火を判定。
成功テストでは更新されたが、失敗テストでは更新されなかったことから上記の結論を得た。

**対応:** `settings.json` に `PostToolUseFailure` イベントを追加し、`Bash` ツールに対して
`post-tool-use.py` を登録した。これにより、テスト失敗時も TDD パターン記録（FAIL 記録）が動作する。

## 5. 移行順序

小さいものから順に、1フック + 対応テストをセットで移行する。

| Wave | 対象 | 理由 |
|------|------|------|
| **Wave 1** | H4 (pre-compact) + _hook_utils.py + settings.json 切替(H4のみ) | 最小（42行）。共通ユーティリティの土台を作る。即座に実動作確認 |
| **Wave 2** | H1 (pre-tool-use) + T1 テスト + settings.json 切替(H1) + **起動時間計測** | 中規模（163行）。最頻フック。切替後に実動作確認。NFR-1 実測 |
| **Wave 3** | H2 (post-tool-use) + T2 テスト + settings.json 切替(H2) | 中規模（161行）。切替後に実動作確認 |
| **Wave 4** | H3 (lam-stop-hook) + T3,T5 テスト + settings.json 切替(H3) | 最大（690行）。切替後に実動作確認 |
| **Wave 5** ✅ | .sh 全削除 + requirements-dev.txt + README/QUICKSTART 更新 + 全フック統合テスト | クリーンアップ + ドキュメント整備（完了済み） |

### Wave ごとの完了条件

- Python 版フックが対応テストに全 PASS
- bash 版と意味的に同等の出力（パリティ確認。下記定義参照）
- **settings.json を当該フックのみ切替え、Claude Code 上で実動作確認**（Wave 1-4 各回）
- **Wave 2 追加条件**: PreToolUse の起動時間を計測（`time python3 pre-tool-use.py < test.json`）。500ms 以内であること（NFR-1）
- 各 .py ファイルに実行権限を付与（`chmod +x`）
- Wave 5 で全 .sh 削除後、全フック統合テスト PASS

### パリティ検証の定義

「同一出力」とは **意味的同等** を指す:
- **exit code**: 完全一致
- **stdout JSON**: キーと値が一致（キー順序は問わない）
- **タイムスタンプ**: ISO 8601 形式（`YYYY-MM-DDTHH:MM:SSZ`）で統一。秒単位の差異は許容
- **ログファイル**: 改行は `\n` 統一。フィールド区切り・フォーマットは同一
- **トランケート**: 文字数基準（バイト数ではない）で 100 文字

## 6. Python 環境セットアップ

### 6.1 新規ファイル

```
requirements-dev.txt   # 開発用依存（pytest のみ）
```

内容:
```
# LAM hook 開発・テスト用
pytest>=7.0
```

ランタイム用 `requirements.txt` は作成しない（フックは標準ライブラリのみで動作）。

### 6.2 QUICKSTART.md / QUICKSTART_en.md 更新

既存の「Q: Python は必要？」セクションを以下に差し替え:

```markdown
### Q: Python は必要？

A: **必須です。** フックスクリプトと StatusLine が Python 3.8+ を使用します。

#### セットアップ（まだ Python がない場合）

**推奨: uv（最速・モダン）**

curl -LsSf https://astral.sh/uv/install.sh | sh   # Linux/macOS
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

uv venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

uv pip install -r requirements-dev.txt  # テストを実行する場合のみ

**フォールバック: venv（追加インストール不要）**

python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

pip install -r requirements-dev.txt     # テストを実行する場合のみ

> pyenv, conda 等を既に使っている場合はそちらでも OK です。
> Python 3.8 以上であれば動作します。
```

### 6.3 README.md / README_en.md 更新

前提条件セクションに以下を追加:

```
- Python 3.8+（フック・StatusLine に必要）
```

### 6.4 対象外

- `pyproject.toml` は作成しない（LAM はテンプレートであり Python パッケージではない）
- `.venv/` は `.gitignore` に追加する（未登録の場合）
- `__pycache__/`, `*.pyc` も `.gitignore` に追加する（未登録の場合）

## 7. settings.json 変更計画

各 Wave で 1 フックずつ切り替える:

```
Wave 1: PreCompact のみ .py に切替
Wave 2: + PreToolUse を .py に切替
Wave 3: + PostToolUse を .py に切替
Wave 4: + Stop を .py に切替（全フック .py 完了）
Wave 5: .sh 削除のみ
```

最終形（方式 A: python3 明示呼び出し）:

```json
"PreToolUse": [{ "hooks": [{ "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/pre-tool-use.py" }] }],
"PostToolUse": [{ "matcher": "Edit|Write|Bash", "hooks": [{ "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/post-tool-use.py" }] }],
"PostToolUseFailure": [{ "matcher": "Bash", "hooks": [{ "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/post-tool-use.py" }] }],
"Stop": [{ "hooks": [{ "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/lam-stop-hook.py" }] }],
"PreCompact": [{ "hooks": [{ "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/pre-compact.py" }] }]
```

最終形（方式 B: shebang + 直接実行 — Windows で python3 が存在しない環境向け）:

```json
"PreToolUse": [{ "hooks": [{ "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/pre-tool-use.py" }] }],
"PostToolUse": [{ "matcher": "Edit|Write|Bash", "hooks": [{ "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/post-tool-use.py" }] }],
"PostToolUseFailure": [{ "matcher": "Bash", "hooks": [{ "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/post-tool-use.py" }] }],
"Stop": [{ "hooks": [{ "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/lam-stop-hook.py" }] }],
"PreCompact": [{ "hooks": [{ "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/pre-compact.py" }] }]
```

方式選定: Wave 1 で方式 A を試行し、動作確認後に方式 B も検証。
Linux/macOS では両方式とも動作する（shebang + chmod +x）。
Windows で `python3` コマンドが存在しない場合は方式 B + Python Launcher (`py.exe`) にフォールバック。
QUICKSTART に両方式の注記を記載する。
