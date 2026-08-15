---
name: quick-save
description: "セッション状態のセーブ（SESSION_STATE.md + ループログ + Daily記録）"
version: 1.1.0
disable-model-invocation: true
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

### 決定と棄却案
- **決定**: 本セッションで下した判断のうち、ADR / retro に書かない粒度のものを 1 行ずつ
- **採らなかった案**: 棄却した選択肢とその理由（1 行 / なければ「なし」）
- **未検証の仮説**: 保留中の疑問・確かめていない前提（1 行 / なければ「なし」）

> 行動ログだけを残すと、次セッションは「何をしたか」は分かるが「なぜそう決めたか」を再導出できない。
> ADR 化に至らない粒度の判断はここでしか残らない。

### コンテキスト情報
- 現在のフェーズ (PLANNING / BUILDING / AUDITING)
- 現在のgitブランチ
- 関連するSPEC/ADR/設計書ファイル名

### 書き出し後の retention 確認（MUST）

`SESSION_STATE.md` を書き換えたら、Milestone / Wave 表記の retention を確認する（`.claude/rules/auto-generated/rule-001.md` / 観測 5 回）:

```
bash .claude/scripts/py_invoke.sh -m pytest .claude/tests/dashboard/test_session_state_parser.py::test_parse_real_session_state_contains_milestone .claude/tests/dashboard/test_session_state_parser.py::test_parse_real_session_state_contains_wave -q
```

FAIL した場合、`SESSION_STATE.md` に Milestone 表記（`[A-Z]-\d+`）と Wave 表記（`Wave N` または `W-XN`）が最低 1 箇所ずつ残っているかを確認する。

> **注意（形骸化させないために）**: `rule-001` は「Milestone / Wave **不在期**には、この検査が**痕跡テキストの保持を強制する**」という未解決の構造的論点を自ら記録している（同ファイル §構造的論点 / 観測 #5）。**FAIL したときに機械的な文字列追加で緑にするのは誤り。** 現に Milestone が存在しないなら、それは同論点の 2 回目の発火であり、恒久解の検討（選択肢 a/b/c は rule-001 に記載）に進む。

## 2. ループログ保存

`.claude/logs/loop-*.txt` が存在する場合、未コミットのループログを記録に含める。
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
1. `.claude/logs/loop-*.txt` を走査し、K1〜K5 を計算
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

## 5. ダッシュボード更新（SHOULD）

build_dashboard.py を呼び出してダッシュボードを更新する。

実行:

```
bash .claude/scripts/py_invoke.sh .claude/scripts/build_dashboard.py
```

成功時: 完了報告に「Dashboard: docs/artifacts/dashboard/dashboard.html 更新済み」を追記する。

失敗時: 警告を表示し、quick-save 全体の成否には影響させない（エラー終了しない）。
