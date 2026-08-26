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
3. テストが Green であること（例: `bash .claude/scripts/py_invoke.sh -m pytest .claude/tests`）
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

## Phase 6: GitHub Release の作成（**省略不可**）

> **タグと Release は別のオブジェクトである。** `git push --follow-tags` が作るのは**タグだけ**で、
> GitHub の Releases ページには**何も現れない**。Phase 5 で止めると、リリースページは前版のまま
> Latest 表示が更新されない（2026-08-26 に v5.1.0 で実際に発生し、ユーザーの指摘で発覚）。

1. **タグがリモートに到達しているか確認**する:
   ```bash
   git ls-remote --tags origin | grep <version>
   ```
2. **リリースノート本文を作成**する。CHANGELOG の該当節をそのまま貼らず、**受け取る側に効くものを選んで要約**する
   （25 節をそのまま貼ると読まれない）。書式は直近リリースに合わせる:
   ```bash
   gh release view <前版> --json body -q .body   # 既存の書式を確認してから書く
   ```
   構成の既定形（v5.0.1 / v5.1.0 で使用）:
   - `## 主題` — このリリースが何の世代か（1-2 段落）
   - `## 修正（受け取る側に効くもの）` — 配布先で実際に直る不具合を優先
   - `## 追加` / `## 整理`
   - `## 既知の未解決` — **未解決は隠さず明示する**（解決したふりより配布物として健全）
   - 末尾に `**検証**: pytest N passed / 詳細は [CHANGELOG.md](<リポジトリ URL>/blob/master/CHANGELOG.md)`
3. 本文はスクラッチパッドに `.md` として書き出し、`--notes-file` で渡す
   （**インラインの `--notes` は使わない** —— 日本語 + 改行 + バッククォートがシェルで壊れる）
4. **Release を作成**する:
   ```bash
   gh release create <version> --title "<version> — <概要>" --notes-file <本文.md> --latest
   ```
   - タイトルは `<version> — <概要>` 形式（過去 32 件と統一）
   - `--latest` を明示する（Latest バッジの付け替え）
   - draft にしない / prerelease にしない（本プロジェクトは未使用）
5. **結果を確認**する:
   ```bash
   gh release list --limit 3
   ```
   最上段が新版で `Latest` が付いていること。付いていなければ `gh release edit <version> --latest`。

> **前提**: `gh auth status` が認証済であること。未認証ならユーザーに `gh auth login` を案内し、
> **Phase 6 を飛ばしたまま完了と報告しない**（タグだけ残ってリリースページが古いまま放置される）。

## 安全設計

- push は明示承認後にのみ実行する（共有状態への不可逆操作）
- **Release 作成も公開操作である**。Phase 6 も明示承認後にのみ実行する
- 同名タグが既に存在する場合は中止する
- テスト未通過時は承認を求める
- リリースコミットは単独に保つ（別機能の変更は `/release` 前に `/ship` で確定）
- **Phase 5 で終わらせない** —— タグのみの状態は「リリースしたつもり」を生む最も蓋然性の高い失敗形である

## 完了条件（チェックリスト）

- [ ] CHANGELOG に `## [<version>] - YYYY-MM-DD` があり、空の `## [Unreleased]` が復活している
- [ ] `docs/slides/` の 4 ファイル（`index` / `index-en` / `intro` / `intro-en`）のバージョンバッジが新版
- [ ] `chore(release): <version> — <概要>` コミットが単独で存在する
- [ ] `git ls-remote --tags origin` に新タグが見える
- [ ] **`gh release list` の最上段が新版 + `Latest`**

## 権限等級

- CHANGELOG 版起こし・slides バージョン同期: **SE級**（ドキュメント更新）
- tag 作成・push: **PM級**（共有状態への影響。ユーザー承認必須）
- **GitHub Release の作成: PM級**（公開操作。ユーザー承認必須）
