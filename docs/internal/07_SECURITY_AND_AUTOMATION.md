# Security & Automation Protocols (Command Safety)

本ドキュメントは、"Living Architect" がターミナルコマンドを実行する際の安全基準（Allow List / Deny List）と、自動化のルールを定義する。

## 1. Core Principle (基本原則)

- **Safety First**: システムの破壊、データの消失、意図しない外部通信を防ぐことを最優先とする。
- **Automation with Consent**: 安全が確認された操作は自動化し（Allow List）、リスクのある操作は必ずユーザーの承認を得る（Deny List）。

## 2. Command Lists (コマンドリスト)

### A. Allow List (Auto-Run Safe)

以下のコマンドは、**副作用がなく（Read-Only）、かつローカル環境で完結するもの**であるため、ユーザー承認なしで実行してよい（`SafeToAutoRun: true`）。

| Category               | Commands                                                      | Notes                              |
| :--------------------- | :------------------------------------------------------------ | :--------------------------------- |
| **File System (Read)** | `ls`, `cat`, `grep`, `find`, `pwd`, `du`, `file`              | ファイル内容の読み取り、検索。     |
| **Git (Read)**         | `git status`, `git log`, `git diff`, `git show`, `git branch` | リポジトリ状態の確認。             |
| **Testing (Local)**    | `pytest`, `npm test`, `go test`                               | **ローカルでの**テスト実行。       |
| **Package Info**       | `npm list`, `pip list`, `gem list`                            | インストール済みパッケージの確認。 |
| **Process Info**       | `ps`, `top` (batch mode)                                      | プロセス状態の確認。               |

### B. Deny List (User Approval Required)

以下のコマンドは、**システムに変更を加える（Write/Mutation）、または外部と通信するもの**であるため、実行前に必ずユーザーの承認を得なければならない（`SafeToAutoRun: false`）。

| Category                | Commands                                                                    | Risks                                                        |
| :---------------------- | :-------------------------------------------------------------------------- | :----------------------------------------------------------- |
| **File System (Write)** | `rm`, `mv`, `cp`, `chmod`, `chown`, `touch`, `mkdir`                        | ファイルの削除、移動、権限変更によるシステム破壊。           |
| **Git (Remote/Write)**  | `git push`, `git pull`, `git fetch`, `git clone`, `git commit`, `git merge` | リモートリポジトリへの影響、コンフリクト発生。               |
| **System Mutation**     | `apt`, `yum`, `brew`, `systemctl`, `service`, `reboot`, `shutdown`          | システム設定の変更、パッケージ導入、再起動。                 |
| **Network**             | `curl`, `wget`, `ssh`, `ping`, `nc`                                         | 外部へのデータ送信、不正なスクリプトのダウンロード。         |
| **Build/Run**           | `npm start`, `npm run build`, `python main.py`                              | アプリケーションの実行（無限ループやリソース枯渇のリスク）。 |

### C. Gray Area Protocol (判断基準)

上記リストに含まれないコマンド、または引数によって挙動が大きく変わるコマンドについては、**原則として「Deny List」扱い（承認必須）**とする。

- 例: `make` (Makefile の中身によるため危険)
- 例: シェルスクリプト (`./script.sh`)

## 3. Automation Workflow

1.  **Check**: 実行したいコマンドが Allow List に含まれているか確認する。
2.  **Decide**:
    - **Included**: `SafeToAutoRun: true` を設定し、ツールを実行する。
    - **Excluded**: `SafeToAutoRun: false` を設定し、ユーザーに承認を求める。
3.  **Log**: 実行結果を確認し、エラーが出た場合はユーザーに報告する。

## 4. Emergency Stop

ユーザーから「止めて」「ストップ」等の指示があった場合、直ちに実行中のコマンドを停止（`Ctrl+C` / `SIGINT`）し、全ての自動化プロセスを中断すること。
