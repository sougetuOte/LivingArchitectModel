# ADR-0004: settings.json の Bash(cat/grep *) 無制限許可を現行維持

**日付**: 2026-03-12
**ステータス**: Accepted
**関連**: `.claude/settings.json`, `.claude/rules/security-commands.md`

---

## コンテキスト

`settings.json` の `permissions.allow` に `Bash(cat *)`, `Bash(grep *)` が設定されており、
プロジェクト外ファイルの読み取りも自動承認される状態にある。

## 判断対象

プロジェクト外ファイルへの Read-Only アクセスを制限すべきか。

## 選択肢

### A: パスをプロジェクト配下に限定

- 安全性は向上するが、システムファイル参照（`/etc/`, ログ等）が毎回承認ダイアログになり作業効率が低下

### B: 現行仕様を維持（採用）

- `cat`, `grep` は Read-Only 操作であり、データ破壊リスクなし
- PreToolUse hook の `__out_of_root__` ガードは Write 操作（Edit/Write）に対して PM 級として機能
- Read-Only 操作に対する過度な制限はコスト対効果が見合わない

## 決定

**案 B を採用**。Read-Only コマンド（`cat`, `grep`）の無制限許可は意図的な設計判断として維持する。

Write 操作に対するセキュリティは PreToolUse hook の `__out_of_root__` パターン（PM 級）で担保されている。
