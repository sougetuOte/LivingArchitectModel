# コマンド実行安全基準

## Allow List（自動実行可）

| カテゴリ | コマンド |
|---------|---------|
| ファイル読取 | `ls`, `cat`, `grep`, `find`, `pwd`, `du`, `file` |
| Git 読取 | `git status`, `git log`, `git diff`, `git show`, `git branch` |
| テスト | `pytest`, `npm test`, `go test` |
| パッケージ情報 | `npm list`, `pip list` |
| プロセス情報 | `ps` |

## Deny List（承認必須）

| カテゴリ | コマンド | リスク |
|---------|---------|--------|
| ファイル削除 | `rm`, `rm -rf` | データ消失 |
| 権限変更 | `chmod`, `chown` | セキュリティ |
| システム変更 | `apt`, `brew`, `systemctl`, `reboot` | システム破壊 |
| ファイル操作 | `mv`, `cp`, `mkdir`, `touch` | 意図しない変更 |
| Git 書込 | `git push`, `git commit`, `git merge` | リモート影響 |
| ネットワーク | `curl`, `wget`, `ssh` | 外部通信 |
| 実行 | `npm start`, `python main.py`, `make` | リソース枯渇 |

上記に含まれないコマンドは **Deny List 扱い**（承認必須）。
「止めて」「ストップ」等の指示で直ちに停止。
