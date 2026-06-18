**Version**: 0.1.0
**Created**: 2026-06-18
**Status**: draft（L1 確定待ち）
**Source**: design.md v0.1.0 §6 完了条件
**Task Slug**: w7-t2b-large-route-demo

---

# rubric-draft: w7-t2b-large-route-demo

> **注記**: 本ファイルは SKILL.md フロー[2] における `rubric-draft.md`（L1 入力用草案）。
> L1 が本ドラフトを Read し内容を確認・確定した上で同ディレクトリに `rubric.md` を生成する。

- 生成日: 2026-06-18
- タスク種別: 大（工程数 3 / 並列度 2 / AC 7 項目）
- global_bound: tokens=400000 OR time=7200s（大タスク初期値 / design §9.2 準拠）
- 対応設計: design.md §3 各工程の責務 / §4 入出力契約 / §6 完了条件

## 検証項目

| # | 工程 | チェック項目 | 検証方法 | 検証コマンド / grader 指示 | 合否基準 |
|---|------|------------|---------|--------------------------|--------|
| AC-1 | 工程1 | `metadata.json` が所定ディレクトリに存在する | run | `ls docs/artifacts/goal-driven-demo/w7-t2b/output/metadata.json` | exit 0（ファイル存在） |
| AC-2 | 工程1 | `metadata.json` に必須キー `name` / `description` / `version` が含まれる | grader | `docs/artifacts/goal-driven-demo/w7-t2b/output/metadata.json` を Read し、JSON パース後に 3 キーすべてが top-level に存在することを確認 | 3 キーすべて存在 AND 値が空文字でない |
| AC-3 | 工程2 | `README-draft.md` が所定ディレクトリに存在する | run | `ls docs/artifacts/goal-driven-demo/w7-t2b/output/README-draft.md` | exit 0（ファイル存在） |
| AC-4 | 工程2 | `README-draft.md` に必須セクション `## Overview` / `## Setup` が含まれる | grader | `docs/artifacts/goal-driven-demo/w7-t2b/output/README-draft.md` を Read し、行頭一致で `## Overview` と `## Setup` が各 1 回以上出現することを確認 | 2 セクションすべて存在 |
| AC-5 | 工程3 | `CHANGELOG-draft.md` が所定ディレクトリに存在する | run | `ls docs/artifacts/goal-driven-demo/w7-t2b/output/CHANGELOG-draft.md` | exit 0（ファイル存在） |
| AC-6 | 工程3 | `CHANGELOG-draft.md` の冒頭が `# Changelog` で始まる | grader | `docs/artifacts/goal-driven-demo/w7-t2b/output/CHANGELOG-draft.md` を Read し、1 行目が `# Changelog`（前後空白を除く完全一致）であることを確認 | 1 行目 == `# Changelog` |
| AC-7 | 全工程 | 全生成ファイルが UTF-8 で 50 行以上である | grader | 3 ファイル（`metadata.json` / `README-draft.md` / `CHANGELOG-draft.md`）を Read し、各ファイルの行数（改行コード LF/CRLF 問わず）が 50 以上であることを確認。UTF-8 デコードが例外なく完了することを併せて確認 | 3 ファイルすべて 50 行以上 AND UTF-8 デコード成功 |

## 差し戻しルール

- max_loop_count: 2（grader 不合格時の差し戻し回数上限）
- 同一項目 2 回連続 Fail → PM エスカレーション
- 上限到達時または escalate=true 時は人間（PM）にエスカレーション

## grader への引き継ぎ事項

- 本 rubric は AC-1〜AC-7 の 7 項目を個別行として列挙
- 検証方法種別:
  - `run`（コマンド実行・exit code 判定）: AC-1, AC-3, AC-5 の 3 件
  - `grader`（ファイル読み取り・内容判定）: AC-2, AC-4, AC-6, AC-7 の 4 件
- grader 出力 JSON は `.claude/logs/gd/W7-T2b-grader.json` に保存（goal-driven-grader 標準スキーマ準拠）
- 全 AC 機械判定可能。human 判定項目なし

## 補足

- 対象ディレクトリは `docs/artifacts/goal-driven-demo/w7-t2b/output/` 直下のみ
- サブディレクトリは検査対象外（design §4 によりサブディレクトリ作成は禁止）
- 行数カウントは末尾改行の有無に関わらず内容行数で判定
- AC-7 の 50 行基準は雛形として最低限の構造を持たせるための下限値
