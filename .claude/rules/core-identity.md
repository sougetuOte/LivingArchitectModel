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

### PM 級編集の事前宣言義務（2026-06-29 追加 / 案 B）

L1（主体）が PM 級ファイル（`docs/specs/` / `docs/adr/` / `.claude/rules/` / `.claude/settings*.json`）を
**直接編集する**前に、以下を **1 回だけ宣言** する:

- 編集対象ファイル（具体的なパス）
- 想定編集回数（おおよその目安 / 例: 「2-3 回の Edit」）
- 編集内容の要約（1-2 文）

これは初回の PM 級ダイアログで「何を承認しているか」をユーザーに明示するため。
2 回目以降の同一ファイル編集は `permission-levels.md` のセッションスコープ降格機構により
自動的に SE 級扱いとなる（ダイアログ非表示）ので、再宣言は不要。

#### 不要なケース

- subagent（design-architect / spec-critic 等）経由の編集 → 委譲時のプロンプトが宣言の代わり
- gitignore 済ファイル（`SESSION_STATE.md` 等）→ そもそも PM 級判定対象外

#### 例

> 「これから `docs/specs/<path>/design.md` に R3 修正 7 件を入れます (Edit 3-5 回想定)。承認お願いします」

## Context Compression

セッションが長くなった場合:
1. 決定事項と未解決タスクを `docs/tasks/` または `docs/artifacts/` に書き出す
2. ユーザーに「コンテキストをリセットします」と宣言
