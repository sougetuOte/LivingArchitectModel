---
description: "論理グループ分けコミット - 変更を棚卸し・分類・コミット"
---

# /ship - 論理グループ分けコミット

引数: `dry-run`（任意） — Phase 4 まで実行して終了

## Phase 1: 棚卸し

1. `git status` + `git diff --stat` で変更ファイルを一覧化
2. 秘密情報パターンを検出した場合は警告して除外:
   - `.env`, `credentials`, `secret`, `token`, `password`, `settings.local.json`
3. 変更ファイル一覧をユーザーに表示

## Phase 2: Doc Sync チェック

1. 実装ファイル（src/ 等）に変更がある場合:
   - 対応する `docs/specs/` の更新が必要か確認
   - CHANGELOG.md への追記が必要か確認
   - README.md / CHEATSHEET.md への反映が必要か確認
2. 不足があれば追記対象をリスト化し、ユーザーに提示
   - ユーザーが「今は不要」と判断した場合はスキップ可

## Phase 3: グループ分け + コミット計画

1. 変更を論理グループに分類:
   - `feat`: 新機能
   - `fix`: バグ修正
   - `docs`: ドキュメントのみ
   - `refactor`: リファクタリング
   - `test`: テストのみ
   - `chore`: 設定・ビルド等
2. グループごとにコミットメッセージ案を作成
3. コミット計画をユーザーに提示

## Phase 4: 確認

コミット計画全体を表示:

```
=== コミット計画 ===

[1] feat: <メッセージ>
    - file1.py
    - file2.py

[2] docs: <メッセージ>
    - README.md
    - CHANGELOG.md

合計: X コミット / Y ファイル

実行しますか？（承認 / 修正指示 / 中止）
```

`dry-run` の場合はここで終了。

## Phase 5: 実行

1. 承認後、グループ単位で `git add <files>` + `git commit` を実行
2. 全コミット完了後、`git log --oneline -N` で結果を表示
3. push はしない（push は明示的な別操作として分離）

## 手動作業通知

コミット完了後、以下を確認:
- push が必要な場合は `git push origin <branch>` を案内
- リリースが必要な場合は `/release` を案内
