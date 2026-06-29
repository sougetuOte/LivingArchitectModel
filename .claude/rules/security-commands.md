# コマンド実行安全基準

## 反面教師制約 (ADR-0008 § 軸 5 / Accepted 2026-06-30)

### D1: deny ↔ allow 二重化必須

deny list 各項目は、対応する allow list (PG 級 auto allow 条件) と併記する。
deny 単独で守らない。

**根拠**: Cursor の denylist 単独廃止 (1.3 で廃止予定 / Base64 obfuscation で bypass) を反面教師として、
allowlist (明示的に許可するもの) と deny list (明示的に禁止するもの) を対で運用する。
allow に含まれず deny にも含まれない操作は **ask** (ユーザー判断) に倒す。

### D4: allowlist はワイルドカード非依存 / 明示コマンド列挙ベース

`.claude/settings.json` の `permissions.allow` 設計は、ワイルドカード (`Bash(*)`, `Edit(*)`, `mcp__*` 等) に依存せず、
**明示的なコマンド列挙** を基本とする。

**根拠**: Claude Code 側のワイルドカード未尊重バグ (GH #27139 / #9924 Critical / #13077) が 2026 半ば時点で
未解決のため。AutoMode 進入時に広汎 allow が drop される挙動 (上流発見 4) も併発する。
将来バグ修正後に再評価するが、当面は明示列挙で運用する。

## コマンド許可マトリクス (D1 二重化準拠)

### 設計原則 (D4 / ワイルドカード非依存)

本ルールの allow / ask / deny 列挙は、ワイルドカード (`*`, `?`) に依存しない明示列挙ベースで設計する。
`.claude/settings.json` の `permissions.allow` 等の実装も同原則に従う。
理由: Claude Code 側のワイルドカード未尊重バグ (GH #27139 / #9924 / #13077) 未解決のため (2026-06 時点)。
将来バグ修正後に再評価するが、当面は明示列挙で運用する。

| カテゴリ | Allow (auto / PG 級) | Ask (ユーザー判断) | Deny (実行禁止) |
|---|---|---|---|
| ファイル読取 | `ls`, `cat`, `grep`, `pwd`, `du`, `file` | — | — |
| ファイル削除 | — | — | `rm`, `rm -rf` (不可逆なデータ消失) |
| ファイル移動 | — | `mv <src> <dst>` (引数明示) | — |
| ファイル操作 (作成系) | — | `cp`, `mkdir`, `touch` | — |
| ファイル検索 | — | `find` (v4.3.1 で ask に移動) | `find -delete`, `find -exec rm` (破壊的パターン) |
| 権限変更 | — | — | `chmod`, `chown` (セキュリティ境界の破壊) |
| Git 読取 | `git status`, `git log`, `git diff`, `git show`, `git branch` | — | — |
| Git 書込 | — | `git commit`, `git merge` | `git push --force`, `git reset --hard` (AutoMode soft_deny と二重) |
| Git リモート | — | `git push` | — |
| テスト | `pytest` (引数明示 or 既知パス), `npm test`, `go test` | — | — |
| パッケージ情報 | `npm list`, `pip list` | — | — |
| プロセス情報 | `ps` | — | — |
| ネットワーク | — | `curl <既知 URL>`, `wget`, `ssh` | `curl | bash`, `wget <不明ホスト>` (外部通信 + 実行の複合) |
| 実行 | — | `npm start`, `python main.py`, `make` | — |
| システム変更 | — | — | `apt`, `brew`, `systemctl`, `reboot` (システム設定の変更) |

上記に含まれないコマンドは **高リスク扱い**（ask / ユーザー判断必須）。

> Layer 1（`settings.json`）で deny / ask の実際の制御粒度を設定する。
「止めて」「ストップ」等の指示で直ちに停止。

## v4.0.0: ネイティブ権限モデルへの移行

v4.0.0 以降、コマンド安全基準は以下の二層で管理される:

- **Layer 1（ネイティブ権限）**: `.claude/settings.json` の `permissions`（allow/ask/deny）で粗粒度の境界を設定
- **Layer 2（PreToolUse hook）**: `.claude/hooks/pre-tool-use.py` でファイルパスベースの動的判定（PG/SE/PM 分類）

本ファイルの Allow/Deny/Ask マトリクスは Layer 0（憲法的プロンプティング）として引き続き有効。
Layer 1 の `permissions.allow` に PG 級コマンド（`ruff format`, `eslint --fix` 等）が追加されている。

権限等級の詳細: `.claude/rules/permission-levels.md`

## 参照

- `.claude/rules/permission-levels.md`（PG/SE/PM 権限等級分類基準）
- `docs/specs/v4.0.0-immune-system-requirements.md` Section 5.1（権限等級の原定義）
- `docs/internal/07_SECURITY_AND_AUTOMATION.md` Section 5（Hooks-Based Permission System）
- `docs/internal/02_DEVELOPMENT_FLOW.md`（フェーズ別の権限適用）
- ADR-0008 `docs/adr/0008-approval-gate-redesign.md`（本ファイル書き換えの根拠 / 自己責任モデル + 反面教師制約 D1/D4）
