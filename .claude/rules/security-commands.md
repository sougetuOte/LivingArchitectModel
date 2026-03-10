# コマンド実行安全基準

## Allow List（自動実行可）

| カテゴリ | コマンド |
|---------|---------|
| ファイル読取 | `ls`, `cat`, `grep`, `find`, `pwd`, `du`, `file` |
| Git 読取 | `git status`, `git log`, `git diff`, `git show`, `git branch` |
| テスト | `pytest`, `npm test`, `go test` |
| パッケージ情報 | `npm list`, `pip list` |
| プロセス情報 | `ps` |

## 高リスクコマンド（Layer 0: 承認必須）

| カテゴリ | コマンド | リスク |
|---------|---------|--------|
| ファイル削除 | `rm`, `rm -rf` | データ消失 |
| 権限変更 | `chmod`, `chown` | セキュリティ |
| システム変更 | `apt`, `brew`, `systemctl`, `reboot` | システム破壊 |
| ファイル操作 | `mv`, `cp`, `mkdir`, `touch` | 意図しない変更 |
| Git 書込 | `git push`, `git commit`, `git merge` | リモート影響 |
| ネットワーク | `curl`, `wget`, `ssh` | 外部通信 |
| 実行 | `npm start`, `python main.py`, `make` | リソース枯渇 |

上記に含まれないコマンドは **高リスク扱い**（承認必須）。

> Layer 1（`settings.json`）では、上記コマンドの多くが `deny` または `ask` に分類されている。
「止めて」「ストップ」等の指示で直ちに停止。

## v4.0.0: ネイティブ権限モデルへの移行

v4.0.0 以降、コマンド安全基準は以下の二層で管理される:

- **Layer 1（ネイティブ権限）**: `.claude/settings.json` の `permissions`（allow/ask/deny）で粗粒度の境界を設定
- **Layer 2（PreToolUse hook）**: `.claude/hooks/pre-tool-use.py` でファイルパスベースの動的判定（PG/SE/PM 分類）

本ファイルの Allow/Deny List は Layer 0（憲法的プロンプティング）として引き続き有効。
Layer 1 の `permissions.allow` に PG級コマンド（`ruff format`, `eslint --fix` 等）が追加されている。

権限等級の詳細: `.claude/rules/permission-levels.md`
