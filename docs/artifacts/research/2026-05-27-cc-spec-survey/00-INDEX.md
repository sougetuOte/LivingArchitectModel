# Claude Code 仕様・機能 すり合わせ調査（2026-05-27）

## 目的

最終コミット 2026-03-31 〜 現在（約2ヶ月分）の Claude Code プラットフォーム仕様・機能の変化を
収集し、現行 LAM 実装との差分マッピング・更新計画策定の基礎資料とする。

- 根拠ルール: `.claude/rules/upstream-first.md`（Upstream First 原則）
- SSOT 対象: `docs/internal/07_SECURITY_AND_AUTOMATION.md`

## ジャンル別調査文書

| # | ジャンル | 調査手法 | 文書 |
|---|---------|---------|------|
| 10 | LAM 現行依存インベントリ | ローカルファイル精査 | [10-lam-current-dependencies.md](10-lam-current-dependencies.md) |
| 20 | Anthropic 公式仕様 | context7 MCP + 公式docs | [20-anthropic-official-spec.md](20-anthropic-official-spec.md) |
| 30 | コミュニティ評判 | WebSearch（ブログ/Reddit/HN） | [30-community-reputation.md](30-community-reputation.md) |
| 40 | GitHub リリース/Issues | gh CLI / WebFetch | [40-github-releases-issues.md](40-github-releases-issues.md) |
| 50 | 高リスク依存の公式裏取り | context7 + 公式docs 逐語引用 | [50-verification.md](50-verification.md) |

## ステータス

- [x] 10 LAM 現行依存
- [x] 20 公式仕様
- [x] 30 コミュニティ
- [x] 40 GitHub（2026-05-27 全ジャンル収集完了）

## 主要発見の要約（差分マッピングの入口）

- **Hooks の大幅拡張**: イベントが大幅増（PreCompact 正式化、`type: mcp_tool`/`agent`/`prompt` ハンドラ、`effort.level` 入力、exec 形式 `args`、Stop への `background_tasks`/`session_crons` 等）。LAM の 5 hook は新フィールド未活用。
- **要確認の高リスク依存**（文書10より）: PreCompact イベント書式 / Stop の `decision:"block"` / PreToolUse `hookSpecificOutput.permissionDecision:"ask"` / `stop_hook_active` / `$CLAUDE_PROJECT_DIR`。
- **Task→Agent リネーム**（旧名互換あり）、Skills へ `.claude/commands/` 統合、Sub-agents の `memory`/`isolation:worktree`/`background`、MCP の SSE 非推奨・Tool Search デフォルト化。
- **破壊的変更**: MCP サーバー名 `workspace` 予約 / `worktree.baseRef` デフォルト変更。
- **コミュニティ**: Auto mode・PowerShell ネイティブ対応・Plan-first 定着、CVE 2件（リポジトリ経由 RCE/APIキー窃取）。

> 注意: 30/40 の Web 由来のバージョン番号・日付は「収集値」であり、差分マッピング着手時に
> 公式 CHANGELOG で裏取りすること（調査担当の訓練データ範囲外を含むため）。

## 次工程（本調査完了後）

1. 差分マッピング（A×B：現行依存 vs 最新仕様）
2. 更新計画の策定（PLANNING フェーズへ移行）
