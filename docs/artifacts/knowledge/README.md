# Knowledge Layer

プロジェクト固有のコンテキスト知識を蓄積するディレクトリ。
`/retro` の Step 4「知見の蓄積」から記録される。

## ファイル構成

| ファイル | 内容 |
|---------|------|
| `patterns.md` | うまくいったコーディング・設計パターン |
| `pitfalls.md` | 踏んだ地雷と回避策 |
| `conventions.md` | プロジェクト固有の慣例・ルール候補 |

## 管理ルール

- カテゴリファイル上限: 5ファイル
- 各ファイル行数上限: 200行
- 90日未参照の知見は `/quick-save` の Daily 記録時に棚卸し通知（trust-model と同じ寿命管理）
- 繰り返し参照される知見は `.claude/rules/` への昇格を検討（PM級）

## 権限等級

| 操作 | 等級 |
|------|------|
| knowledge/ への記録 | SE級 |
| knowledge/ から rules/ への昇格 | PM級 |
| knowledge/ の棚卸し・削除 | PM級 |

## Subagent Memory との棲み分け

| 仕組み | 蓄積者 | タイミング | 内容 |
|--------|--------|-----------|------|
| `docs/artifacts/knowledge/` | 人間（/retro 経由） | Wave/Phase 完了時 | 意図的に整理された知見・教訓 |
| `.claude/agent-memory/` | Subagent（自動） | 実行中に自発的に | 実行中に学んだパターン・慣例 |
| Auto Memory (`MEMORY.md`) | Claude 本体（自動） | セッション中 | ビルドコマンド、デバッグ知見等 |

## 参照

- 提案メモ: `docs/memos/2026-03-12-knowledge-layer-and-platform-alignment.md`
- trust-model: `.claude/rules/auto-generated/trust-model.md`
