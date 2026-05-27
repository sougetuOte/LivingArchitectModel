# Claude Code 仕様すり合わせ — 差分マッピング統合サマリー

最終更新: 2026-05-27 / フェーズ: PLANNING（差分マッピング = As-Is 分析）

## 目的

最終コミット 2026-03-31 以降の Claude Code プラットフォーム仕様と現行 LAM 実装の差分を、
**現状維持で安全 / 新機能で改善可（列挙のみ）/ 要更新** の3分類で棚卸しする。
本サマリーは後続 requirements（更新計画）の入力。採否判断は requirements で行う。

## 入力資料

- 調査一式: `docs/artifacts/research/2026-05-27-cc-spec-survey/`（10/20/30/40/50）
- 詳細マッピング（本サマリーの根拠）:
  - [diff-hooks.md](diff-hooks.md)（Hooks）
  - [diff-skills-subagents.md](diff-skills-subagents.md)（Skills + Sub-agents）
  - [diff-mcp-settings.md](diff-mcp-settings.md)（MCP + Settings + Permissions）

## 全体集計

| 分類 | Hooks | Skills+Sub | MCP+Settings | 合計 |
|------|------:|-----------:|-------------:|-----:|
| 現状維持で安全 | 10 | 11 | 9 | 30 |
| 新機能で改善可 | 16 | 27 | 21 | 64 |
| 要更新 | 2 | 3 | 2 | 7 |

**結論**: 高リスク依存（hook の権限ガード・自律ループ・パス解決）は全て公式と一致＝**破壊的な乖離はゼロ**。
要更新7件はいずれも影響度 低〜中で、過半が「ドキュメント記述の陳腐化」と「新機能の未活用」。
ユーザー方針（公式と乖離しないこと／低中リスクは着手可）と整合する穏当な状況。

## 要更新7件（更新計画の主対象）

| ID | 領域 | 内容 | 影響度 | 性質 | 推定権限等級 |
|----|------|------|:------:|------|:----:|
| H-02 | Hooks | `pre-compact.py` L8 の「公式未掲載」注記が陳腐化（PreCompact は正式掲載済み） | 低 | コメント修正 | PG |
| H-20 | Hooks | `_hook_utils.get_tool_response` の `tool_response` キーと公式サンプル `tool_result` の不一致疑い（**要逐語確認**） | 中 | 要再調査→修正 | SE |
| C-1 | Skills | `.claude/commands/` 11本がフロントマター非対応で Skills 新機能を活用不可（動作は継続） | 低 | 移行余地 | SE |
| C-2 | Sub-agents | CLAUDE.md の「agent-memory は公式機能でない」記述が陳腐化（公式 `memory:` で同パス対応済み） | 低 | 記述更新＋方針判断 | PM |
| C-3 | Sub-agents | 全8エージェントに `memory: project` 未設定（自前運用宣言と公式機構が未接続） | 中 | 方針判断 | PM |
| S-1 | Settings | Windows managed-settings 旧パス `C:\ProgramData\ClaudeCode\` 非サポート化（LAM settings.json に直接参照なし） | 中 | 環境影響確認 | SE |
| S-3 | Settings | `worktree.baseRef` デフォルトが `head`→`fresh` に変更（worktree 活用時のみ影響） | 低 | 設定要否判断 | SE |

### メインエージェントの統合所見

- **C-2 と C-3 は連動した1つの論点**: 「公式 `memory:` 機構へ寄せるか / 自前 agent-memory 運用を維持するか」という設計判断（PM級）。LAM の Memory Policy（CLAUDE.md）に直結するため、requirements で最初に決すべき核。
- **H-20 は着手前に逐語確認が必須**: `tool_response` vs `tool_result` は裏取り未完（後述）。確定するまで「修正」ではなく「再調査」扱い。
- **残りの H-02 / C-1 / S-1 / S-3 は低リスクの個別対応**: ユーザー方針上、着手可能な範囲。

## 新機能で改善可（64件）— 採否は requirements で議論

代表例（列挙のみ、採用是非は未判断）:
- **Hooks**: 新ハンドラ `type: mcp_tool/agent/prompt`、`effort.level` 入力、`terminalSequence` 通知、Stop の `background_tasks`/`session_crons`、`updatedInput` によるツール入力書換、`CLAUDE_ENV_FILE`
- **Skills**: `paths`（パターン自動起動）、`allowed-tools`、`when_to_use`、`model`、`shell`(PowerShell)、動的コンテキスト `!` ブロック
- **Sub-agents**: `isolation: worktree`、`maxTurns`、`permissionMode`、`disallowedTools`、`skills` プリロード、`color`
- **Permissions/Settings**: `permissionDecision: "defer"`、`skillOverrides`、`permissions.defaultMode`、`additionalDirectories`

## 公式裏取りが未完の項目（requirements 前に解消推奨）

1. H-20: `tool_response` / `tool_result` の正しい PostToolUse 入力キー（逐語確認）
2. PreCompact のブロック出力可否の逐語確認
3. `type: "mcp_tool"` hook の完全スキーマ
4. Windows managed-settings パス廃止の確定バージョン
5. `xhigh` effort の対応モデル一覧 / `policyHelper`・`disableRemoteControl` のバージョン番号

## 次サブフェーズ（requirements）への引き継ぎ

1. 核となる設計判断: **公式 `memory:` 機構への移行可否**（C-2/C-3）→ MAGI 適用候補
2. 低リスク要更新（H-02/C-1/S-1/S-3）の更新範囲確定
3. 採用する新機能の選定（64件から）
4. 未確認5件の追加裏取り
