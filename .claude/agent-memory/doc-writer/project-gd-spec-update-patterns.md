---
name: project-gd-spec-update-patterns
description: goal-driven-orchestration 仕様文書を更新する際の同期パターンと注意点
metadata:
  type: project
---

design.md / config.md / tasks.md の3文書は同期更新が必要。

**スキーマ変更時の必須追従箇所**:
- design.md §10 のスキーマを変更 → config.md §5 の完全スキーマ・フィールド定義表も同一内容に更新
- config.md のフッター行（末尾の `*config.md ここまで。バージョン...` 行）も更新すること
- `.claude/states/goal-driven-orchestration.json` の `planning` セクションに各文書バージョンを記録
- states ファイルの `task_notes` にも関連タスクの状態変化を記録

**バージョン表記の場所**（各ファイル）:
- design.md: ヘッダ行（`- バージョン:`）+ 改訂履歴行（`- 改訂履歴:`）の2箇所
- config.md: ヘッダ行 + 参照設計行 + フッター行の3箇所
- tasks.md: ヘッダ行 + 改訂履歴行 + 参照設計行の3箇所

**Why:** design §10 と config §5 はともに gd-session-state.json の完全スキーマを掲載しており、SSOT は design 側。W1-T2 で config を新規作成した際に fallback フィールドが設計書側にあったにもかかわらず config に転記漏れが発生（2026-06-13 PM 承認ゲートで検出）。

**How to apply:** design §10 のスキーマを変更・追加する場合は必ず config §5 を開いて同一フィールドを追加する。フィールド定義表の記述は design 側は「フィールド補足」表、config 側は「フィールド定義」表と名称が異なるが内容は一致させること。
