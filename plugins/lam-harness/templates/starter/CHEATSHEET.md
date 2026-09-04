# CHEATSHEET — <project-name>

> **starter テンプレート**: 初回だけ敷かれます。以後はあなたの資産です。

## クイックコマンド

skill は plugin から供給されるため **名前空間つき**で呼びます。

| やりたいこと | コマンド |
|:-----------|:--------|
| 実装フェーズに入る | `/lam-harness:building` |
| 重要判断（MAGI 合議） | `/lam-harness:magi` |
| コミット | `/lam-harness:ship` |
| 振り返り | `/lam-harness:retro` |
| 状況保存 / 復帰 | `/lam-harness:quick-save` / `/lam-harness:quick-load` |

読み込まれている skill の一覧は `/help` の Custom commands、
plugin の構成と token コストは `claude plugin details lam-harness` で確認できます。

## 権限等級（PG / SE / PM）

- **PG級**: 自動修正・報告不要（フォーマット、typo、lint 修正）
- **SE級**: 修正後に報告（テスト追加、内部リファクタリング）
- **PM級**: 判断を仰ぐ（仕様変更、アーキテクチャ変更、ルール変更）

対象パスの**正本は `.claude/rules/permission-levels.md`** §ファイルパスベースの分類です。
ここに列挙を写すと必ずずれるため、迷ったら正本を開いてください。

## ハーネスが効く範囲（重要）

| 層 | 中身 | init が敷くか |
|:--|:--|:--|
| Layer 0（規範） | `CLAUDE.md` / `.claude/rules/` / `docs/internal/` | **敷く** |
| Layer 2（機構） | `.claude/hooks/`（plugin が供給） | **plugin が供給** |
| Layer 1（決定的な禁止） | `.claude/settings.json` の `permissions` | **敷かない**（手作業） |

Layer 1 を有効にする手順は `/lam-harness:init` の完了メッセージに出ます。

## このプロジェクトのクセ

(未記入)

## ハマりどころ

(未記入)

## Try

(未記入)
