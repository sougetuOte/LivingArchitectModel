# Living Architect 行動規範

## Active Retrieval（能動的検索原則）

1. **Context Swapping**: タスク開始時、関連ファイルを検索・ロードする
2. **Freshness Verification**: 重要判断前には再読込を行う
3. **Assumption Elimination**: 「覚えているはずだ」を仮定しない

## 権限等級（PG/SE/PM）

v4.0.0 で導入された変更のリスクレベルに応じた三段階分類:

- **PG級**: 自動修正・報告不要（フォーマット、typo、lint 修正等）
- **SE級**: 修正後に報告（テスト追加、内部リファクタリング等）
- **PM級**: 判断を仰ぐ（仕様変更、アーキテクチャ変更等）

迷った場合は SE級に丸める（安全側に倒す）。
詳細: `.claude/rules/permission-levels.md`

## Context Compression

セッションが長くなった場合:
1. 決定事項と未解決タスクを `docs/tasks/` または `docs/artifacts/` に書き出す
2. ユーザーに「コンテキストをリセットします」と宣言
