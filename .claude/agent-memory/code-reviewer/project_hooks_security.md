---
name: hooks security findings
description: .claude/hooks/ セキュリティ監査結果と要注意箇所（2026-03-12 イテレーション2更新）
type: project
---

2026-03-12 イテレーション2監査で更新。

**Why:** フックスクリプトは Claude Code の権限制御レイヤーであり、迂回・誤動作は直接的なセキュリティリスクになる。

**How to apply:** hooks/ 関連コードをレビューする際は以下の点を優先確認する。

## 要注意箇所（優先度順）

1. [Critical/PM] `_SECRET_PATTERN` の偽陽性（`lam-stop-hook.py:379-382`）: `.md`/`.txt` の例示コードにも発火し `sec_fail=True` でループが機能不全になる可能性。コメント行スキップや対象拡張子の見直しは PM 承認が必要。
2. [Critical/SE] `_run_security()` が `check_dir` を再検証せずに再帰スキャン（`lam-stop-hook.py:363`）: `_validate_check_dir()` で project_root 外を許可した場合、任意ディレクトリをスキャンする。スキャン開始前の二重チェックを追加すべき。
3. [旧既知/解消済み] `normalize_path` の out-of-root パスが PM 級として捕捉される設計は `__out_of_root__/` プレフィックスにより機能している（前サイクルの懸念は解消確認）。
4. `_SAFE_PATTERN` の `test` が広すぎる（`lam-stop-hook.py:60`）: 実際の漏洩を誤抑止する可能性（前サイクルから継続）。
5. `conftest.py` の `hook_runner` が `os.environ` を全コピー: CI で機密変数漏洩リスク（前サイクルから継続）。

## 良好な点（参照用）

- `run_command` は `shell=False` 固定（コマンドインジェクションなし）
- `atomic_write_json` で競合状態を防止
- `shutil.which()` でコマンドパス解決（PATH インジェクション対策）
- `_validate_check_dir()` 追加によりパストラバーサル対策が強化された（イテレーション2で追加）
- `except Exception` の多用はフック障害で Claude をブロックしない設計方針に基づく意図的なもの
