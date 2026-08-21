# _SECRET_PATTERN キーワード拡充

**起票日**: 2026-03-14
**起票元**: full-review iter2 セキュリティ監査
**権限等級**: PM
**ステータス**: **CLOSED（対象消滅 / 2026-08-21）**
**クローズ理由**: 拡充対象の `_SECRET_PATTERN` 自体が、**起票の翌日に削除されていた**

## クローズ記録（2026-08-21）

本タスクは `lam-stop-hook.py` の `_SECRET_PATTERN` にキーワードを足すことを求めていたが、
**その `_SECRET_PATTERN` は 2026-03-15 のコミット `cefaf45` で削除されている**
（`_SAFE_PATTERN` とともに）。同コミットのメッセージ:

> lam-stop-hook.py から `_SECRET_PATTERN`/`_SAFE_PATTERN` を削除し、
> シークレット検出を Phase 0 静的解析（bandit B105/B106）に一元化

実測（2026-08-21）: `.claude/hooks/lam-stop-hook.py` に `_SECRET_PATTERN` / `_SAFE_PATTERN` は
**0 件**。シークレット検出は `.claude/hooks/analyzers/gitleaks_scanner.py` と bandit 系アナライザが担う。

つまり本タスクは **起票の翌日から約 5 か月間、存在しないものの拡充を待っていた**。
削除方針は `docs/specs/gitleaks-integration-spec.md:120` および
`docs/specs/scalable-code-review-spec.md:272` が「維持」と明記しており、復活の予定はない。

要求そのもの（キーワード網羅）が今も有効かは、**gitleaks / bandit のルールセットに対して**
問い直すべき別件である。本タスクの宛先は失われている。

## 概要（原文 / 2026-03-14）

`lam-stop-hook.py` の `_SECRET_PATTERN` に以下のキーワードが未網羅:
- `access_key`, `auth_token`, `bearer`, `client_secret`
- `database_url`, `db_password`

## 方針（原文 / 2026-03-14）

現時点ではルールを厳しくしない。実害（実際のシークレット漏洩インシデント）が
確認された場合にキーワードを拡充する。誤検知増加とのトレードオフを考慮。

## 参照

- 監査レポート: `docs/artifacts/audit-reports/2026-03-14-iter2.md`
- 対象ファイル: `.claude/hooks/lam-stop-hook.py:59`
