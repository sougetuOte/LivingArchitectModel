**Version**: 0.1.0
**Created**: 2026-06-17
**Status**: draft
**Task Slug**: docs-stub-sync
**用途**: W4-T3 実機リハーサル用 中タスク

---

# design: docs-stub-sync

## 目的 / Problem Statement

`docs/artifacts/goal-driven-demo/README.md` のファイル一覧テーブルを実ディレクトリと照合し、
不足エントリを追記する。

本タスクは W4-T3 実機リハーサルにおける **中タスク経路（L1 → l3-executor 二層）** の
検証用実タスクとして機能する。作業内容自体も実際の docs 整備として意義があり、
リハーサル完了後もプロジェクトの成果物管理に継続的に貢献する。

### 中タスクとして選定した根拠

- rubric 項目数: 4（小タスク条件「≤ 3」を外れる）
- 工程数: 2（ディレクトリ走査 → README 更新）。並列分解不要
- 変更範囲が 1 ファイル（README.md）のみで副作用が限定的
- 実行ログ保存先（`docs/artifacts/goal-driven-demo/`）が完了条件と一致し整合が取れる

---

## 完了条件 / Success Criteria

1. `docs/artifacts/goal-driven-demo/README.md` のファイル一覧テーブルが
   実ディレクトリの全ファイルと完全一致していること
2. 既存エントリの説明文が削除・変更されていないこと（追記のみ）
3. 追記形式が既存テーブルの書式（`| file | description |`）と一致していること
4. 不足エントリ（`W4-T3-rehearsal-package.md` 等）が追加されていること
5. 実行ログが `docs/artifacts/goal-driven-demo/` に保存されていること

---

## インターフェース定義

### 読取対象ファイル

| ファイル / ディレクトリ | 用途 |
|----------------------|------|
| `docs/artifacts/goal-driven-demo/README.md` | 更新対象のファイル一覧テーブルを含む |
| `docs/artifacts/goal-driven-demo/`（ディレクトリ走査） | 実ディレクトリの存在ファイル一覧を取得 |

### 出力ファイル

| ファイル | 内容 | 権限等級 |
|---------|------|---------|
| `docs/artifacts/goal-driven-demo/README.md` | 不足エントリ追記後の更新版 | SE |

### テーブル書式

既存テーブルの書式に準拠すること:

```markdown
| ファイル名 | 説明 |
|-----------|------|
| example.md | 例の説明 |
```

---

## スコープ外（やらないこと）

- `docs/artifacts/goal-driven-demo/` 以外のディレクトリの README 更新
- 既存エントリの説明文の変更・改善（追記のみが許可される）
- テーブル以外のセクションの変更
- 新規ファイルの作成（README.md の更新のみ）
- `docs/artifacts/goal-driven-demo/` 配下のファイル内容の変更

---

## 依存関係・前提条件

- `docs/artifacts/goal-driven-demo/README.md` が存在すること
- `docs/artifacts/goal-driven-demo/` ディレクトリが読取可能であること
- goal-driven スキル（`docs/tasks/docs-stub-sync/rubric-draft.md`）が配置済みであること

---

## 参照

| ドキュメント | 箇所 |
|-------------|------|
| `docs/artifacts/goal-driven-demo/W4-T3-rehearsal-package.md` | §2 候補 A 詳細 |
| `docs/specs/goal-driven-orchestration/handoff-format.md` | §3〜§4 受け渡し形式定義 |
| `docs/specs/goal-driven-orchestration/design.md` | §9（ルート判定）/ §16（rubric-draft スキーマ） |
