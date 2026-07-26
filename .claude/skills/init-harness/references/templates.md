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

### `CHANGELOG.md` (Keep a Changelog 1.1.0 雛形 + `[Unreleased]`)

```markdown
# Changelog

このプロジェクトの主要な変更はこのファイルに記録する。

書式は [Keep a Changelog 1.1.0](https://keepachangelog.com/ja/1.1.0/) に準拠し、
バージョニングは [Semantic Versioning 2.0.0](https://semver.org/lang/ja/) に従う。

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security
```

> 空の見出しは初期化時点では削除しない（次の変更をどのカテゴリに書くかの手掛かりになるため）。
> 初回リリース時に該当なしの見出しを落とす。

### `SESSION_STATE.md` (見出しのみ / 中身は `/quick-save` が書く)

```markdown
# SESSION_STATE

**最終更新**: <YYYY-MM-DD>
**ブランチ**: <branch>
**現在の Milestone**: (未設定)

> **削除禁止**: 本ファイルは `/quick-save` が上書き更新し、`/quick-load` が読み込む
> セッション継続の受け渡し口である。見出し構成を変えると復帰時に情報が落ちる。

---

## 完了タスク

(未記入)

## 進行中タスク

(未記入)

## 次のステップ

(未記入)

## 変更ファイル一覧

(未記入)

## 未解決の問題

なし

## コンテキスト情報

- **フェーズ**: (PLANNING / BUILDING / AUDITING のいずれか)
- **ブランチ**: <branch>
- **関連文書**: (SPEC / ADR / 設計書のパス)
```

> 見出し 6 種は `/quick-save` が書き込む記録項目（`.claude/skills/quick-save/SKILL.md` §1）と
> 対応している。項目を増減する場合は quick-save 側と同時に変更する。
>
> `SESSION_STATE.md` はローカル限定の作業状態ファイルであり、**`.gitignore` への追加を推奨**する
> （LAM 本体でも gitignore 済）。追加するかはプロジェクト側の判断に委ねる。

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

