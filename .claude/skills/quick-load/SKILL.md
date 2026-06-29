---
name: quick-load
description: "セッション状態のロード（SESSION_STATE.md + 関連ドキュメント特定）"
version: 1.0.0
disable-model-invocation: true
---

# クイックロード

プロジェクトルートの `SESSION_STATE.md` を読み込み、セッション状態を復帰する。

## 1. SESSION_STATE.md を読み込む

プロジェクトルートの `SESSION_STATE.md` を読む。
存在しない場合は「SESSION_STATE.md が見つかりません。新規セッションとして開始します。」と報告して終了。

## 2. 関連ドキュメントの特定

SESSION_STATE.md の「コンテキスト情報」セクションに記載されたドキュメントのうち、
「次のステップ」の実行に必要なものを特定する。**読み込みはまだ行わない**（コンテキスト節約）。

## 3. 復帰サマリーを報告

```
--- quick-load 完了 ---
前回: YYYY-MM-DD | Phase: [Phase]

完了: [要約]
未完了: [あれば/なし]
次: 1. ... 2. ...
参照予定: [ファイルパス]
---
```

## 4. ユーザーの指示を待つ

ドキュメントの読み込みは、実際に作業を開始するタイミングで行う。
**先回りして大量のファイルを読み込まないこと。**

> **注記 (ADR-0008 v0.3 / 2026-06-30)**: 旧 Step 4「モード認知サマリ表示」(`detect-permission-mode.py` 自動実行) は承認 prompt ノイズ過大により撤回。AutoMode 認知は `CLAUDE.md` 冒頭 `## Execution Permission Modes (Advisory)` 等の文書で代替する。ユーザーが手動確認したい場合は `python .claude/scripts/detect-permission-mode.py` を直接実行できる (スクリプト本体は debug 用に温存)。
