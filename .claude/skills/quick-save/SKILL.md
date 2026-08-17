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

### 書き出し後の宣言欄確認（MUST / **2026-08-17 改訂**）

`SESSION_STATE.md` を書き換えたら、**Milestone 宣言欄が存在し解釈可能であること**を確認する（`.claude/rules/auto-generated/rule-001.md` / 観測 6 回 / 2026-08-17 恒久解 (c)）:

```
bash .claude/scripts/py_invoke.sh -m pytest .claude/tests/dashboard/test_session_state_parser.py::test_parse_real_session_state_contains_milestone .claude/tests/dashboard/test_session_state_parser.py::test_parse_real_session_state_contains_wave -q
```

ヘッダに次のいずれかの形で宣言があること。**「なし」は正当な値であり、欠落ではない。**

```markdown
**現在の Milestone**: **なし**（注釈は任意）
**現在の Milestone**: **B-5**（注釈は任意）
```

FAIL した場合の原因は 2 つに限られる: (1) **宣言欄が無い** → 上記の書式で追加する / (2) **値が「なし」とも Milestone 名とも読めない**（典型: 誤字） → 値を直す。

> **本文中の Milestone / Wave 表記に retention 義務はない**（2026-08-17 撤廃）。過去の実績記録は自由に整理してよい。
>
> **旧仕様（2026-07-06〜2026-08-17）との違い**: 旧版は「本文にパターンを最低 1 箇所ずつ残す」ことを要求し、Milestone 不在期に (i) 痕跡テキストの保持を強制する（観測 #5 = **赤くなる**）か (ii) 過去への言及から誤った現在状態を導出して**緑のまま嘘をつく**（観測 #6 = クローズ済 Milestone を進行中と表示）かのいずれかになっていた。恒久解 (c) で**パーサが宣言欄を正本として読む**ようにしたため、この構造的論点は解決済み。**機械的な文字列追加で緑にする誘惑自体が消えた。**

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
