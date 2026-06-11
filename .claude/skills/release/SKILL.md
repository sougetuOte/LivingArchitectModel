---
name: release
description: "リリース - CHANGELOG 版起こし → commit → tag → push"
version: 1.0.0
disable-model-invocation: true
argument-hint: "<version> (例: v4.8.0)"
---

# /release - リリース

引数: `<version>` — リリースするバージョン（例: `v4.8.0`）。`v` 接頭辞付き semver。
引数がない場合は CHANGELOG の `[Unreleased]` 内容から semver 昇格案（major/minor/patch）を提示し、ユーザーに確定を求める。

## 前提条件チェック

1. リリース対象以外の未コミット変更がないこと（あれば `/ship` を先に案内）
2. `git tag` に同名タグが存在しないこと（存在したら中止）
3. テストが Green であること（例: `.venv/Scripts/python.exe -m pytest .claude tests`）
   - 失敗時は警告し、ユーザーの「承知の上で続行」を得るまで進まない

## Phase 1: CHANGELOG 版起こし

1. `## [Unreleased]` セクションを `## [<version>] - YYYY-MM-DD`（本日）に変換
2. 新しい空の `## [Unreleased]` を `# Changelog` ヘッダ直後に追加
3. 比較リンク等を使用している場合は更新（本プロジェクトは未使用）

## Phase 2: バージョン表記の同期

1. `docs/slides/index.html` / `index-en.html`、`intro.html` / `intro-en.html` の
   タイトルバッジを `<version>` に更新する
   - `story-evolution*.html` の `v4.0.0` は「v3.x→v4.0.0」の歴史比較表のため**据え置き**
2. その他バージョンバッジがないか grep で確認し、現在地表記のみ更新する
   （歴史記述・過去の変更記録・ADR は据え置く）

## Phase 3: commit

1. `git status` + `git diff --stat` で変更を確認
2. gitleaks シークレットスキャン（`/ship` Phase 1 に準ずる。未インストール時は WARNING で続行）
3. `chore(release): <version> — <概要>` でコミット（CHANGELOG + slides 等のリリース成果物）
   - 別機能の未コミット変更がある場合は `/ship` を先に促し、リリースコミットを単独に保つ

## Phase 4: tag

1. `git tag -a <version> -m "<version>"` で注釈付きタグを作成する
   - タグメッセージに CHANGELOG の該当節の概要を含めてもよい
2. `git show <version>` でタグが正しいコミットを指すことを確認

## Phase 5: push

1. ユーザーに最終確認を求める（push は不可逆・共有状態への影響）
2. 承認後、`git push origin <branch>` と `git push origin <version>` を実行
   （または `git push --follow-tags`）
3. `git log --oneline -3` と `git tag --sort=-creatordate | head -3` で結果を表示

## 安全設計

- push は明示承認後にのみ実行する（共有状態への不可逆操作）
- 同名タグが既に存在する場合は中止する
- テスト未通過時は承認を求める
- リリースコミットは単独に保つ（別機能の変更は `/release` 前に `/ship` で確定）

## 権限等級

- CHANGELOG 版起こし・slides バージョン同期: **SE級**（ドキュメント更新）
- tag 作成・push: **PM級**（共有状態への影響。ユーザー承認必須）
