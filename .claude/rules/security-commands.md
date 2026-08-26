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
| ファイル移動 | — | — | `mv` (不可逆な上書きを含むため / **2026-08-26 に Ask から移動 = 実装は当初から deny**) |
| ファイル操作 (作成系) | — | `cp`, `mkdir`, `touch` | — |
| ファイル検索 | — | `find` (v4.3.1 で ask に移動) | `find -delete`, `find -exec rm`, `find -exec chmod`, `find -exec chown` (破壊的パターン) |
| 権限変更 | — | — | `chmod`, `chown` (セキュリティ境界の破壊) |
| Git 読取 | `git status`, `git log`, `git diff`, `git show`, `git branch` | — | — |
| Git 書込 | — | `git commit`, `git merge` | `git push --force` / `-f` (4 形), `git reset --hard` (AutoMode soft_deny と二重 / **2026-08-22 に実装済**) |
| Git リモート | — | `git push`, `git pull`, `git fetch`, `git clone` | — |
| テスト | `pytest`, `python -m pytest`, `python3 -m pytest`, `npm test`, `go test` | — | — |
| 静的解析・整形 (PG 級 auto allow) | `ruff check`, `ruff check --fix`, `ruff format`, `python -m ruff check`, `npx prettier`, `npx eslint --fix` | — | — |
| シークレット走査 | `gitleaks detect`, `gitleaks protect`, `gitleaks version` | — | — |
| LAM スクリプト実行 | `bash .claude/scripts/py_invoke.sh` (Python 呼び出しの単一 entry point / D4 の allowlist prefix 1 本) | — | — |
| パッケージ情報 | `npm list`, `pip list` | — | — |
| プロセス情報 | `ps` | — | — |
| ネットワーク | — | `curl <既知 URL>`, `wget`, `ssh` | `curl \| bash`, `curl \| sh`, `wget \| bash` (外部通信 + 実行の複合) |
| 実行 | — | `python` (全般), `npm start`, `npm run`, `make` | — |
| システム変更 | — | — | `apt`, `yum`, `brew`, `systemctl`, `service`, `reboot`, `shutdown` (システム設定の変更) |

> **本表は `.claude/settings.json` の実測（allow 29 / ask 17 / deny 24）と一致する**（2026-08-26 突合 / `docs/artifacts/2026-08-22-enumeration-drift-sweep.md` §2）。片方だけを更新しないこと —— **表と実装のどちらが正しいかは、表からは判定できない**（同掃き §6 共通の教訓）。

上記に含まれないコマンドは **高リスク扱い**（ask / ユーザー判断必須）。

> Layer 1（`settings.json`）で deny / ask の実際の制御粒度を設定する。
「止めて」「ストップ」等の指示で直ちに停止。

## 計器への書き込みを伴う検証

**計器に書き込みうる検証を実行する前に、隔離が効いていることを先に確認する（MUST）。**

計器とは、LAM が自分の状態を観測するために書き出すファイルを指す
（`.claude/tdd-patterns.log` / `.claude/test-results.xml` / `.claude/.pre-compact-fired` 等）。

**根拠**: 2026-08-17、1 セッションで計器に 3 回触れて 2 回壊した
（`docs/artifacts/retro-2026-08-17.md` P1）。環境変数名の取り違えによる偽値の上書きは復元できたが、
`tdd-patterns.log` のデータ欠損は**復元不能**だった。

**機構との二重化**（誕生ゲート設計 §1.3）: `.claude/tests/hooks/test_instrument_isolation.py`
（R3 機構 #8）が **pytest セッション内**での汚染を検出する。**ただしその射程は手動実行を含まない**
—— 2026-08-17 の実際の事故は手動の hook スモーク実行であり、機構はそれを捕捉しない。
**本条項が守るのはその外側**であり、同時に機構が沈黙したときにそれを知るための規範でもある。

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
