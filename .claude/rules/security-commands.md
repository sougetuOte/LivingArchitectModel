# コマンド実行安全基準

## Purpose

ターミナルコマンド実行時の安全基準を定義する。

## Permission Categories

### Allow List（自動実行可）

副作用がなく、ローカル環境で完結するもの（`SafeToAutoRun: true`）:

| カテゴリ | コマンド |
|---------|---------|
| ファイル読取 | `ls`, `cat`, `grep`, `find`, `pwd`, `du`, `file` |
| Git 読取 | `git status`, `git log`, `git diff`, `git show`, `git branch` |
| テスト | `pytest`, `npm test`, `go test` |
| パッケージ情報 | `npm list`, `pip list` |
| プロセス情報 | `ps` |

### Deny List（承認必須）

システムに変更を加える、または外部通信するもの（`SafeToAutoRun: false`）:

| カテゴリ | コマンド | リスク |
|---------|---------|--------|
| ファイル削除 | `rm`, `rm -rf` | データ消失 |
| 権限変更 | `chmod`, `chown` | セキュリティ |
| システム変更 | `apt`, `brew`, `systemctl`, `reboot` | システム破壊 |
| ファイル操作 | `mv`, `cp`, `mkdir`, `touch` | 意図しない変更 |
| Git 書込 | `git push`, `git commit`, `git merge` | リモート影響 |
| ネットワーク | `curl`, `wget`, `ssh` | 外部通信 |
| 実行 | `npm start`, `python main.py`, `make` | リソース枯渇 |

## Gray Area Protocol

上記に含まれないコマンドは **Deny List 扱い**（承認必須）。

## Emergency Stop

「止めて」「ストップ」等の指示で直ちに停止。

## References

- `docs/internal/07_SECURITY_AND_AUTOMATION.md`
