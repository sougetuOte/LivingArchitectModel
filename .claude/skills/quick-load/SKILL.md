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

## 4. モード認知サマリ表示

`.claude/scripts/detect-permission-mode.py` を Bash で実行し、stdout の JSON を受け取って
復帰サマリーの末尾に 1 行追記する。ADR-0008 軸 2 に基づく自己責任モデルの認知導線。

mode 値別の表示:

- `mode == "auto"`: `Mode: auto (LAM 推奨設定 / Claude 自律性最大)`
- `mode in ["default", "acceptEdits", "plan", "dontAsk"]`: `Mode: <値> (AutoMode 採用を推奨 / 詳細: CLAUDE.md §Permission Modes Advisory)`
- `mode == "bypassPermissions"`: `Mode: bypassPermissions ⚠ AutoMode への切替を強く推奨 (LAM 規律 hook のみ稼働中)`
- 検知不能 (`mode == null`): `Mode: 不明 (~/.claude/settings.json 読み取り失敗 / 詳細: CLAUDE.md §Permission Modes Advisory)`

スクリプト実行自体に失敗した場合も「検知不能」扱いで 1 行追記する。
stderr の warning は復帰サマリには出さず無視する (出力先は stderr のため Bash 結果には混ざらない)。

## 5. ユーザーの指示を待つ

ドキュメントの読み込みは、実際に作業を開始するタイミングで行う。
**先回りして大量のファイルを読み込まないこと。**
