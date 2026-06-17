**Version**: 0.1.0
**Created**: 2026-06-17
**Status**: draft

---

# task-list: docs-stub-sync

| # | タスク説明 | 依存 | 権限等級 | 備考 |
|---|-----------|------|---------|------|
| T1 | `docs/artifacts/goal-driven-demo/` を走査し、実在ファイル一覧を取得する。README.md の既存テーブルと照合して不足エントリを特定する | なし | SE | 読取専用操作。ディレクトリ走査 + テーブル差分抽出 |
| T2 | 特定した不足エントリを `docs/artifacts/goal-driven-demo/README.md` のファイル一覧テーブルに追記する（既存エントリは変更しない） | T1 | SE | 追記のみ。書式は既存テーブル（`\| file \| description \|`）に準拠 |
