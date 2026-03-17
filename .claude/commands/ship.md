---
description: "論理グループ分けコミット - 変更を棚卸し・分類・コミット"
---

# /ship - 論理グループ分けコミット

引数: `dry-run`（任意） — Phase 4 まで実行して終了

## Phase 1: 棚卸し

1. `git status` + `git diff --stat` で変更ファイルを一覧化
2. **gitleaks シークレットスキャン**（staged changes）:
   ```bash
   # Python スクリプトで実行
   python3 -c "
   import sys; sys.path.insert(0, '.claude/hooks')
   from analyzers.gitleaks_scanner import run_protect_staged, is_available, get_install_guide
   if not is_available():
       print('⚠️ gitleaks 未インストール: シークレットスキャンをスキップします')
       print(get_install_guide())
   else:
       issues = run_protect_staged()
       if issues:
           for i in issues:
               print(f'  🔴 {i.file}:{i.line} — {i.message} ({i.rule_id})')
       else:
           print('✅ シークレット検出なし')
   "
   ```
   - **検出なし**: Step 3 へ
   - **検出あり**: 検出内容を表示し、ユーザーに判断を求める
     - 「承知の上で続行」→ Step 3 へ
     - それ以外 → コミット中止
   - **gitleaks 未インストール**: WARNING + インストールガイドを表示し、コミットは許可する
3. 秘密情報パターンを検出した場合は警告して除外:
   - `.env`, `credentials`, `secret`, `token`, `password`, `settings.local.json`
4. 変更ファイル一覧をユーザーに表示

## Phase 2: Doc Sync チェック（v4.0.0 強化）

### 2-1. doc-sync-flag 参照

PostToolUse hook が自動生成する `.claude/doc-sync-flag` を参照する。
このファイルには src/ 配下の変更ファイルパスが1行1パスで記録されている。

- ファイルが存在しない or 空 → Doc Sync スキップ（PG級変更のみと判断）
- ファイルが存在 → 2-2 へ進む（パスは PROJECT_ROOT からの相対パス形式で記録されている）

### 2-2. 変更の PG/SE/PM 分類

変更ファイルを権限等級（`.claude/rules/permission-levels.md`）で分類する:

- **PG級のみ** → Doc Sync スキップ
- **SE/PM級の変更あり** → 2-3 へ進む

### 2-3. ドキュメント更新案の生成

SE/PM級の変更がある場合:

1. 対応する `docs/specs/` ファイルを特定（ファイル名パターンマッチ）
2. `doc-writer` エージェントで更新案を生成（差分形式）
3. 更新案をユーザーに提示:
   - CHANGELOG.md への追記が必要か確認
   - README.md / CHEATSHEET.md への反映が必要か確認
4. PM級の設計判断を検出 → ADR 起票を提案
5. ユーザーが「今は不要」と判断した場合はスキップ可

### 2-4. フラグクリア

Doc Sync チェック完了後（承認・スキップに関わらず）、`.claude/doc-sync-flag` を削除する:

```bash
rm -f .claude/doc-sync-flag
```

これにより次セッションではフラグがリセットされる。削除に失敗した場合はその旨を報告し、手動削除を案内する。

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

コミット完了後、以下を確認して通知する。

### 手動削除候補

プロジェクトに不要と判断されるファイルを列挙:
- テンプレート由来で現プロジェクトに無関係なファイル
- 一時ファイル、デバッグ用の残骸
- `.gitignore` に追加すべきパターン

```
--- 手動削除候補 ---
- [ファイルパス]: [理由]

削除はユーザー自身で行ってください。AI は削除を実行しません。
```

該当なしの場合はこのセクションをスキップする。

### ユーザー作業

- push が必要な場合は `git push origin <branch>` を案内
- リリースが必要な場合は `/release` を案内
- ブランチ作成・マージが必要な場合は手順を案内
- 外部サービスへの通知が必要な場合は列挙
