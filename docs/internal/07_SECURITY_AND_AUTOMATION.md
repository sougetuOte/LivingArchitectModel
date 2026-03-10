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

> **Note**: ファイルリネームが必要な場合、`mv` は Deny List に含まれるため以下の代替手段を用いる:
> - `Read` → `Write`（新名称で作成）→ `Write`（旧ファイルを空にするか削除依頼）
> - `git mv`（Git 追跡下のファイルの場合。ユーザー承認は必要）

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

## 5. Hooks-Based Permission System (v4.0.0)

v4.0.0 以降、コマンド安全基準は以下の多層モデルで運用される:

| Layer | 名称 | 実装 | 粒度 |
|:---:|:---|:---|:---|
| 0 | 憲法的プロンプティング | 本ドキュメント Section 2 | コマンドカテゴリ |
| 1 | ネイティブ権限 | `.claude/settings.json` の `permissions` | ツール×パターン |
| 2 | 動的 hook 判定 | `.claude/hooks/pre-tool-use.py` | ファイルパス×権限等級 |

### 権限等級 (PG/SE/PM)

Layer 2 の PreToolUse hook はファイルパスに基づき 3 段階の権限等級を判定する:

- **PG級**: 自動許可（読取専用ツール、lint 修正等）
- **SE級**: 許可 + ログ記録（src/ 配下の変更、ドキュメント更新等）
- **PM級**: ask 応答で承認ダイアログを表示（仕様書、ADR、ルールファイル、設定ファイルの変更）

詳細は `.claude/rules/permission-levels.md` を参照。

### PostToolUse による自動記録

PostToolUse hook はツール実行後に以下を自動処理する:
- テスト結果の記録（TDD パターン検出）
- ドキュメント同期フラグの設定（src/ 配下の変更検知）
- ループ状態ファイルへのイベント記録（自動ループ中）

### Stop hook による自律ループ制御

Stop hook は Claude の応答完了時に発火し、自律ループの収束を判定する:
- Green State（テスト全パス + lint エラーゼロ + セキュリティチェック通過）達成で停止
- 反復上限到達で強制停止
- コンテキスト圧迫検出（PreCompact 連動）で安全停止

## 6. Recommended Security Tools (推奨セキュリティツール)

### Anthropic 公式

| ツール | 用途 | 導入方法 |
|:---|:---|:---|
| [security-guidance plugin](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/security-guidance) | コード編集時のリアルタイムセキュリティ警告 | `/plugin install security-guidance@claude-plugin-directory` |
| [claude-code-security-review](https://github.com/anthropics/claude-code-security-review) | PR 単位の AI セキュリティレビュー（GitHub Action） | `.github/workflows/` に追加 |
| [Claude Code Security](https://www.anthropic.com/news/claude-code-security) | コードベース全体の脆弱性スキャン | Enterprise/Team プラン |

### 依存脆弱性スキャン（プロジェクトに応じて選択）

| 言語 | ツール | コマンド |
|:---|:---|:---|
| JavaScript/Node.js | npm audit | `npm audit --audit-level=critical` |
| Python | pip-audit | `pip-audit --desc` |
| Python | safety | `safety check` |
| Go | govulncheck | `govulncheck ./...` |

### CI/CD 統合

GitHub Actions で `claude-code-security-review` を使用する場合の設定例:

```yaml
- uses: anthropics/claude-code-security-review@main
  with:
    comment-pr: true
    claude-api-key: ${{ secrets.CLAUDE_API_KEY }}
```
