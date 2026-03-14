# _SECRET_PATTERN キーワード拡充

**起票日**: 2026-03-14
**起票元**: full-review iter2 セキュリティ監査
**権限等級**: PM
**ステータス**: 延期

## 概要

`lam-stop-hook.py` の `_SECRET_PATTERN` に以下のキーワードが未網羅:
- `access_key`, `auth_token`, `bearer`, `client_secret`
- `database_url`, `db_password`

## 方針

現時点ではルールを厳しくしない。実害（実際のシークレット漏洩インシデント）が
確認された場合にキーワードを拡充する。誤検知増加とのトレードオフを考慮。

## 参照

- 監査レポート: `docs/artifacts/audit-reports/2026-03-14-iter2.md`
- 対象ファイル: `.claude/hooks/lam-stop-hook.py:59`
