# フックスクリプト Python 一本化 — 要件定義書

## 1. Core Value (Why & Who)

### User Story

Windows ユーザーとして、LAM をクローンしたらフックが動く状態にしたい。
なぜなら、現在 `.sh` スクリプトは bash 環境がないと動作せず、Windows では別途 Git Bash や WSL が必要になるから。

### Problem Statement

- **現状**: 全フック（4本）と全テスト（5本）が bash スクリプト。Windows ネイティブ環境では動作しない
- **理想**: `python3` さえあれば全 OS で動作する。LAM は既に StatusLine で Python 3 を前提としており、新たな依存は増えない
- **副次効果**: bash の `jq` フォールバック（grep + sed による簡易 JSON パース）が不要になり、コードが大幅に簡潔化する

## 2. 移行対象ファイル

### 本体フック（4本）

| # | 現行ファイル | 行数 | Python 版 | 責務 |
|---|-------------|------|-----------|------|
| H1 | `pre-tool-use.sh` | 163 | `pre-tool-use.py` | 権限等級判定（PG/SE/PM） |
| H2 | `post-tool-use.sh` | 161 | `post-tool-use.py` | TDD パターン検出、doc-sync-flag、ループログ |
| H3 | `lam-stop-hook.sh` | 690 | `lam-stop-hook.py` | 自律ループ収束判定 |
| H4 | `pre-compact.sh` | 42 | `pre-compact.py` | コンテキスト圧縮前の状態保存 |

### テスト（5本）

| # | 現行ファイル | Python 版 |
|---|-------------|-----------|
| T1 | `tests/test-pre-tool-use.sh` | `tests/test_pre_tool_use.py` |
| T2 | `tests/test-post-tool-use.sh` | `tests/test_post_tool_use.py` |
| T3 | `tests/test-stop-hook.sh` | `tests/test_stop_hook.py` |
| T4 | `tests/test-helpers.sh` | `tests/conftest.py`（pytest fixtures） |
| T5 | `tests/test-loop-integration.sh` | `tests/test_loop_integration.py` |

### 設定ファイル（1本）

| # | ファイル | 変更内容 |
|---|---------|---------|
| S1 | `.claude/settings.json` | 全 hook command を `.py` に切替 |

## 3. 機能要件（FR）

### FR-1: 完全なパリティ

Python 版は bash 版と **同一の入出力** を保証する。

- 同一の stdin JSON → 同一の stdout JSON / exit code
- 同一のファイル副作用（ログファイル、フラグファイル、状態ファイル）

### FR-2: jq 依存の除去

- `json` 標準ライブラリのみ使用（外部パッケージ不要）
- bash 版にあった jq/grep+sed フォールバック分岐が不要になる

### FR-3: クロスプラットフォーム対応

- Linux / macOS / Windows (Python 3.8+) で動作すること
- パス区切り: `os.path` または `pathlib` を使用（`/` ハードコード禁止）
- 日時: `datetime` 標準ライブラリを使用（`date` コマンド非依存）
- ファイルロック: 必要な場合は `fcntl`（Unix）/ `msvcrt`（Windows）のフォールバック、またはアトミック書き込み（`tempfile` + `os.replace`）

### FR-4: エラー耐性

- フック障害時は常に exit 0（Claude をブロックしない）
- `try/except` で全体をラップし、例外時は exit 0 + 可能ならログ記録

### FR-5: settings.json の更新

```json
"command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/<name>.py"
```

Windows では `python3` が `python` の場合がある。この点については以下の方針:
- settings.json では `python3` を使用（Claude Code が動作する環境では python3 が標準）
- README/QUICKSTART に「Windows で `python3` が見つからない場合は `python` に読み替え」の注記を追加

### FR-6: テストフレームワーク

- pytest を使用（本プロジェクトは既に pytest を前提）
- 既存テストの全テストケースを移植（TC/T 番号の対応表を維持）
- テスト実行: `pytest .claude/hooks/tests/`

## 4. 非機能要件（NFR）

### NFR-1: パフォーマンス

- Python の起動オーバーヘッドが許容範囲内であること
- 目安: 1フック実行あたり 500ms 以内（bash 版は 50-200ms 程度）
- Stop hook のテスト/lint 実行は外部プロセス呼び出しのため、起動オーバーヘッドは支配的でない

### NFR-2: 保守性

- 各フックは単一 `.py` ファイルで完結（import は標準ライブラリのみ）
- 共通ユーティリティがある場合は `_hook_utils.py` に切り出し可
- テストは pytest 標準パターン（conftest.py + fixtures）

### NFR-3: 後方互換性

- 移行完了後、`.sh` ファイルは削除する（併記しない）
- `.sh` テストファイルも削除する

## 5. Constraints

### 技術スタック

- Python 3.8+（型ヒントは Optional 等の旧書式でも可。3.10+ 記法 `X | Y` は使わない）
- 外部パッケージ依存なし（標準ライブラリのみ）
- テスト: pytest

### 対象外

- フックのロジック変更・機能追加（純粋な言語移行のみ）
- StatusLine の変更
- `docs/internal/` の設計書更新（完了後にドキュメント同期として実施）

## 6. Perspective Check (3 Agents)

### [Affirmative]

- jq フォールバックの完全除去により、コードが 40-60% 短縮される見込み
- Windows ユーザーの参入障壁が大幅に下がる
- `json` + `pathlib` + `datetime` で bash の苦しい文字列処理から解放される
- テストも pytest 化することで、プロジェクト全体のテスト体験が統一される

### [Critical]

- Python 起動オーバーヘッド（コールドスタート 100-200ms）がフック実行ごとに発生
  - **緩和策**: PreToolUse/PostToolUse は毎回呼ばれるが、処理自体は軽量。Stop hook は元々テスト実行を含むため支配的でない
- `subprocess.run` で外部コマンド（pytest, ruff 等）を呼ぶ際、Windows のパス解決が異なる可能性
  - **緩和策**: `shutil.which()` でコマンドの存在確認、`shell=False` で直接実行
- `settings.json` の `python3` が Windows で見つからないケース
  - **緩和策**: ドキュメントに注記。Claude Code 自体が Python 環境を前提としているため、実質的な問題は小さい

### [Mediator]

- **結論**: 移行は実施する。リスクは全て緩和策があり、得られるメリット（クロスプラットフォーム対応 + コード簡潔化）が大きい
- NFR-1（パフォーマンス）は移行後に実測で確認し、問題があれば対処する
- 移行は段階的に実施（H4 → H1 → H2 → H3 の順。小さいものから）

## 7. Acceptance Criteria

- [ ] AC-1: 全 Python 版フックが bash 版と同一の入出力を返す（テストで検証）
- [ ] AC-2: 全既存テストケースが pytest で PASS する
- [ ] AC-3: `settings.json` が `.py` を参照し、Claude Code でフックが正常動作する
- [ ] AC-4: `.sh` ファイルが全て削除されている
- [ ] AC-5: Linux 環境で全テスト PASS（Windows テストは任意。構造的にクロスプラットフォーム対応であること）
- [ ] AC-6: 外部パッケージへの依存がない（標準ライブラリのみ）
