---
description: セッション状態のセーブ（SESSION_STATE.md + ループログ + Daily記録）
---

# クイックセーブ

プロジェクトルートの `SESSION_STATE.md` への記録 + ループログ保存 + Daily 記録。
git commit は行わない（コミットは `/ship` を使用）。
コンテキスト消費を抑えるため、簡潔に実行すること。

## 1. プロジェクトルートの SESSION_STATE.md を書き出す

以下の内容を **簡潔に** 記録（各項目は箇条書き数行で十分）:

### 完了タスク
- 今回のセッションで完了した作業を箇条書き

### 進行中タスク
- 作業途中のものとその現在の状態
- 次に何をすべきか

### 次のステップ
- 次セッションで最初にやるべきこと（優先順位付き）

### 変更ファイル一覧
- 今回変更したファイルのパス一覧

### 未解決の問題
- 残っている課題、確認事項（なければ「なし」）

### コンテキスト情報
- 現在のフェーズ (PLANNING / BUILDING / AUDITING)
- 現在のgitブランチ
- 関連するSPEC/ADR/設計書ファイル名

## 2. ループログ保存

`.claude/logs/loop.log` が存在する場合、未コミットのループログを記録に含める。
詳細: `docs/specs/loop-log-schema.md`

## 3. Daily 記録

`docs/daily/YYYY-MM-DD.md` に以下を記録:

### 本日完了
- 完了したタスク（1〜3項目）

### 明日の最優先
- 次にやるべきこと（1項目）

### 課題・気づき
- あれば最大1つ

### KPI 集計

ベースライン確立後（Wave 2 完了後）、KPI を集計・表示する。
詳細定義: `docs/specs/evaluation-kpi.md`

集計手順:
1. `.claude/logs/loop.log` を走査し、K1〜K5 を計算
2. `.claude/logs/permission.log` を走査し、等級分布（PG/SE/PM）を集計
3. テンプレートは `docs/specs/evaluation-kpi.md` Section 6 を参照

## 4. 完了報告

以下を表示:

```
--- quick-save 完了 ---
SESSION_STATE.md: 更新済み
Daily: docs/daily/YYYY-MM-DD.md

再開方法:
  claude -c  （直前セッション続行）
  claude     （新規セッション）

再開後: /quick-load
git commit が必要なら: /ship
---
```
