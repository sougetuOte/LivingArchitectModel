**Version**: 1.0.0
**Created**: 2026-06-17
**Status**: confirmed
**Confirmed-by**: L1 (Opus 4.8) at goal-driven rehearsal (W4-T3)
**Source**: docs/tasks/docs-stub-sync/rubric-draft.md v0.1.0

---

# rubric: docs-stub-sync

## 検証項目（grader が判定）

| # | チェック項目 | 検証方法 | 合格条件 |
|---|-------------|---------|---------|
| 1 | README.md のファイル一覧が実ディレクトリと完全一致する | `ls -1 docs/artifacts/goal-driven-demo/` の出力と README.md のファイル一覧テーブルに含まれるファイル名集合を比較 | 過不足 0（READMEテーブルにあるが実在しない or 実在するが README に無い ファイルが存在しないこと） |
| 2 | 既存エントリの説明文が削除・変更されていない | 変更前 README（git show HEAD:docs/artifacts/goal-driven-demo/README.md）と現在の README の差分を取得し、既存エントリ行に diff があるか確認 | 既存エントリ行に変更/削除がないこと（追記行のみ） |
| 3 | 追記形式が既存テーブルの書式と一致する | 新規追加された行が既存テーブルと同じ列構成（`\| filename \| description \|`）であり、ヘッダ・区切り行直下のテーブル本体に含まれていること | 全新規行が既存書式に準拠 |
| 4 | 不足エントリが追加されている（W4-T3-rehearsal-package.md / W6-T2-dw-exclusion-report.md 等） | T1 走査結果で「README にない実在ファイル」として特定された全エントリが、T2 完了後の README に新規行として存在すること | 走査結果との差分 0 |

## 補足

- ファイル一覧の対象は `docs/artifacts/goal-driven-demo/` 直下のファイル（サブディレクトリ含まず）
- README.md 自身もテーブルに含まれていることを許容（自己言及エントリ）
- 拡張子のないファイル（実行ログ等）も対象
- gitignore されたファイルは対象外
