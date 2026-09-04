## 参照: Scalable Code Review

- Stage 1（静的解析パイプライン）: Scalable Code Review Stage 1 として実装済み（Plan A）
- Stage 2 Step 1-2（AST チャンキング）: Scalable Code Review Stage 2 Step 1-2 として実装済み（Plan B）
- Stage 2 Step 3（チャンクモード並列監査）: Scalable Code Review Stage 2 Step 3 として実装済み（Plan B）
- Stage 3（階層的レビュー）: Scalable Code Review Stage 3 として実装済み（Plan C: C-2b/C-3a/C-3b）
- Stage 2 トポロジカル順レビュー + 契約カード注入: Scalable Code Review Stage 2 として実装済み（Plan D: D-2/D-3）
- Stage 4 トポロジカル順修正: Scalable Code Review Stage 4 として実装済み（Plan D: D-3）
- Stage 0 Scale Detection: Scalable Code Review Stage 0 として実装済み（Plan E: E-1b）
- Stage 5 影響範囲分析（ハイブリッド統合）は Plan E で実装予定

- 要件仕様: `docs/specs/scalable-code-review-spec.md`
- 設計書: `docs/design/scalable-code-review-design.md`
- タスク: `docs/tasks/scalable-code-review-tasks.md`
- 構想メモ: ~~`docs/memos/2026-03-10-scalable-review-and-eval-ideas.md`~~ — **参照先不在**
  （`docs/memos/` ディレクトリ自体は実在するが当該ファイルは存在しない / 2026-08-20 実測。
  代替となる既存メモも確認できず）
