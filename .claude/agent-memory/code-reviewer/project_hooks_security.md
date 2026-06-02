---
name: hooks security findings
description: .claude/hooks/ セキュリティ監査結果と要注意箇所（2026-06-02 イテレーション3更新）
metadata:
  type: project
---

2026-06-02 イテレーション3監査で更新（full-review Stage 2）。

**Why:** フックスクリプトは Claude Code の権限制御レイヤーであり、迂回・誤動作は直接的なセキュリティリスクになる。

**How to apply:** hooks/ 関連コードをレビューする際は以下の点を優先確認する。

## 要注意箇所（優先度順）

1. [Medium/SE] `lam-stop-hook.py:268` — `_run_g1_checker` が `os.environ` 全コピーでサブプロセス起動。
   `conftest.py` の `_ENV_ALLOWLIST` パターンを本番コードにも適用すべき。
   現時点はローカル実行前提で実害なし。CI 展開時にリスク顕在化。

2. [Medium/SE] `_hook_utils.py:95-116` — `normalize_path` が `p.resolve()` でシンボリックリンクを展開しない。
   パス文字列レベルの比較のためシンボリックリンクバイパスが理論上可能。
   ただし前提条件が多く、ローカル実行環境での実害はほぼなし。

3. [Low/PG] `tests/test_stop_hook_autonomous.py:36` — テストで `os.environ` 全コピー（`_full_env()`）。
   Windows システム変数が必要という理由だが、選択的列挙に変更すべき。

4. [Low/PG] `analyzers/tests/test_e2e_review.py:506,534,552` — E2E テストが ALLOWLIST パターンを使用せず全コピー。

## 旧記録が削除・解消された課題

- `_SECRET_PATTERN` / `_SAFE_PATTERN` / `_run_security()` / `_validate_check_dir()` は
  すべてリファクタリングで削除済み（セキュリティスキャン機能は `gitleaks_scanner.py` に移管）。
- `conftest.py` の `hook_runner` が全コピーだった問題は `_ENV_ALLOWLIST` で解消済み。

## 良好な点（参照用）

- `run_command` は `shell=False` 固定（コマンドインジェクションなし）
- `atomic_write_json` で競合状態を防止
- `shutil.which()` でコマンドパス解決（PATH インジェクション対策）
- `eval`/`exec`/`pickle` の不使用（危険なデシリアライゼーションなし）
- gitleaks の Match/Secret フィールドを Issue に格納しない設計（シークレット値の永続化防止）
- FR-9/FR-3.4 の二重防御（pre-tool-use.py 層2 + settings.autonomous.json 層1）
- `except Exception` の多用はフック障害で Claude をブロックしない設計方針に基づく意図的なもの
