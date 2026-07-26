## テンプレート定義 (インライン文字列)

> **注**: 以下は LLM が SKILL 実行時に書き出すべき内容のリファレンス。
> 各ファイルの完全版は本プロジェクト直下の初期化済みファイルを参照。

### `CLAUDE.md` (FR-06 プレースホルダー)

```markdown
# CLAUDE.md — <project-name>

LLM (Claude Code) 向けプロジェクト規約。**不変に近いルール**のみを記載する。

## プロジェクト概要

<!-- ユーザーが手動記入 -->

## ハーネス規律

(フェーズ遷移、ディレクトリ規約 — 標準テンプレを展開)

## 禁止事項

- `.claude/` 配下の不用意な書き換え
- `--no-verify` の使用 (明示指示時を除く)
```

### `CHEATSHEET.md` (FR-10 — クイックコマンド表入り、固有セクション空)

```markdown
# CHEATSHEET.md — <project-name>

## クイックコマンド

| やりたいこと | コマンド |
|:-----------|:--------|
| 実装フェーズに入る | `/building` |
| 重要判断 | `/magi` (LLM提案時) |
| コミット | `/ship` |
| 振り返り | `/retro` |
| 状況保存/復帰 | `/quick-save` / `/quick-load` |

## このプロジェクトのクセ

(未記入)

## ハマりどころ

(未記入)

## Try

(未記入)
```

### `CHANGELOG.md`

Keep a Changelog 1.1.0 雛形 + `[Unreleased]` セクション。

### `SESSION_STATE.md`

完了タスク / 進行中 / 次のステップ / 変更ファイル / 未解決問題 / 削除禁止メモ の見出しのみ。

### `.claude/current-phase.json`

```json
{
  "phase": "none",
  "phase_approved": false,
  "next_recommended": "design",
  "updated_at": "<ISO 8601>",
  "notes": "Harness initialized."
}
```

