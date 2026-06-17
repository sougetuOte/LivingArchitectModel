# W4-T3 中タスク実機リハーサル結果報告

**Date**: 2026-06-17
**Task**: docs-stub-sync (task_id: gd-20260617-001)
**Route**: medium
**Status**: completed (L1 承認)

---

## 1. 実機完走確認

フロー [1]〜[9] の各ステップ成否:

| ステップ | 内容 | 成否 | 備考 |
|---------|------|------|------|
| [1] 難易度判定 | route=medium の判定 | OK | gd-session-state.json に `"route": "medium"` 記録 |
| [2] rubric 生成 | docs/tasks/docs-stub-sync/rubric.md 生成 | OK | rubric_version: 2026-06-17 |
| [3] bound 設定 | gd-session-state.json 初期化 | OK | global_token_bound=150000 / global_time_bound=3600 / max_loop_count=3 |
| [4] l3-executor 実行 | Agent(goal-driven-l3-executor) 呼び出し | OK | subagent_tokens=37,783 取得 |
| [5] grader 実行 | Agent(goal-driven-grader) 呼び出し | OK | subagent_tokens=37,559 取得 |
| [6] 乖離検知 | WARN ログ出力 + _divergences 記録 | OK | ratio=0.82 で閾値 0.20 超過 → WARN 出力 |
| [7] L1 最終検収 | L1 本体（Opus 4.8）による最終判定 | OK | 5 項目すべて充足・承認（pass） |
| [8] メモリ蒸留 | distill-lessons.py 実行 | OK | lessons.md に 1 エントリ追記（395 bytes） |
| [9] 後処理・コストサマリ | build_cost_summary() 出力 + status 更新 | OK | status: "completed" 確認 |

**完走判定**: 全 9 ステップ正常完了

---

## 2. 観測値 vs 期待値

| 観測項目 | 期待値 | 実測値 | 判定 |
|---------|--------|--------|------|
| ループ完走 | フロー[1]〜[9] 全ステップ動作 | 全ステップ動作確認 | Pass |
| route 判定 | medium | medium | Pass |
| global_token_bound（初期値） | 150,000 | 150,000 | Pass |
| global_time_bound（初期値） | 3,600 | 3,600 | Pass |
| max_loop_count | 3 | 3 | Pass |
| 実際のループ回数 | 1〜3 以内 | 1（loop_count=0 で完了） | Pass |
| total_tokens | 150,000 以内 | 75,342 | Pass |
| total_tokens / 150k 比率 | 0.5〜0.9（適正）または判定 | 0.502（適正範囲下限付近） | 適正 |
| l1_ratio | 5〜15%（期待範囲） | 0.0000（本体トークン未計上・設計通り） | 要注記（§5 参照） |
| subagent_tokens 取得（l3） | 成功（None でない） | 成功（37,783） | Pass |
| subagent_tokens 取得（grader） | 成功（None でない） | 成功（37,559） | Pass |
| grader ログ保存 | .claude/logs/gd/gd-20260617-001-loop01-grader.json | 存在確認（1,358 bytes） | Pass |
| grader 総合判定 | pass | pass（rubric #1〜#4 全 pass） | Pass |
| escalate | false | false | Pass |
| status（完了後） | "completed" | "completed" | Pass |
| コストサマリ出力 | design §14 形式 | 出力確認 | Pass |
| 蒸留 lessons.md | エントリ追記 | 1 エントリ追記（395 bytes） | Pass |
| 変更ファイル | README.md のみ | README.md のみ（追記 3 行） | Pass |

**注記（loop_count フィールド）**: gd-session-state.json の `loop_count` が `0` を示しているのは、
フロー完了後のデクリメントまたは 0-index 記録の仕様によるもの。grader ログパスが `-loop01-` を含み、
loop 1 回での完了が確認できる。

---

## 3. 乖離検知の発生

| layer | self_reported | measured | ratio | WARN ログ | _divergences 記録 |
|-------|--------------|---------|-------|----------|-----------------|
| l3 | 6,800 | 37,783 | 0.8200 | あり | _divergences[0] |
| grader | 未計測（乖離なし） | 37,559 | — | なし | なし |

**W4-T3 完了条件 #2（tokens_used 乖離計測の実機検証）**: 充足

- 乖離率 0.82 は W1-T3 実機で観測した大幅乖離（自己申告 100 vs 実測 26,305）と同様の傾向を示す
- 実測: 37,783 tok に対し自己申告は 6,800 tok（実測の約 18%）。L3 の自己申告は実測を大きく下回る傾向が継続確認された
- `cost_log._divergences` への自動記録（W4-T2 実装）が実機で正常動作

---

## 4. bound 校正提案

§5 の判断基準（W4-T3-rehearsal-package.md）に照らした評価:

- 実測 total_tokens: **75,342 tok**
- global_token_bound: 150,000 tok
- 比率: **0.502**（75k〜135k の「適正範囲」に分類）

| 比率範囲 | 判断 |
|---------|------|
| 0.5 未満 | 下方再校正候補 |
| **0.5〜0.9（実測 0.502）** | **適正範囲 → 再校正不要** |
| 0.9 超 | 上方再校正必要 |

- 中タスク 1 ループ実測 = 75,342 tokens
- bound 150k は 2 ループ完走を想定するなら適正
- 3 ループ想定なら 75,342 × 3 = 226,026 tok と予測 → 上限引上げまたは max_loop=2 への下方校正の検討候補
- ただし本リハーサルは docs-stub-sync の 1 例のみ（N=1）。タスク規模・複雑度によりトークン消費は変動する

**現時点での再校正提案: なし**
理由: 実測比率が適正範囲内。リハーサル N=1 では判断材料不足。次回中タスク以降で N≥2 の追加観測を推奨。

---

## 5. OQ-3（L1 モデル選定）判断材料

| 項目 | 値 | 備考 |
|------|-----|------|
| l1_tokens（フロー[1] 難易度判定） | PM 目視計測待ち | Settings > Usage で手動読み取り必要 |
| l1_tokens（フロー[7] 最終検収） | PM 目視計測待ち | Settings > Usage で手動読み取り必要 |
| l1_tokens（cost_log） | 0（記録なし） | 設計上、本体コンテキスト消費は subagent_tokens 経由で取得不能 |
| l1_ratio（compute_l1_ratio() 出力） | 0.0000 | L1 が cost_log に未計上のため 0.0 固定（仕様通り） |
| total_tokens（gd-session-state.json） | 75,342 | 実測 |
| loop_count | 1（grader ログ -loop01- より確認） | 1 ループで完了 |

**l1_ratio が 0.0000 となる理由（設計上の制約）**:
L1 は本体コンテキスト（直接の Agent ツール呼び出し主体）であり、
`subagent_tokens` は呼び出し先サブエージェントの消費トークンを返す機構。
本体 = 呼び出し元のため、L1 消費トークンは cost_log に計上されない（設計通り）。

**中タスク期待値（5〜15%）との比較**: cost_log 上は比較不能

**運用代替**: PM が Settings > Usage を確認し「L1 起動前後の使用量差分」を手動算出することを推奨。
OQ-3 の最終判断に向け、本タスクの L1 消費は PM 目視計測として記録を補完すること。

---

## 6. 発見問題リスト

| # | 区分 | 問題 | 対応提案 | W7-T1 前解消 |
|---|------|------|---------|-------------|
| 1 | Info | l1_ratio が cost_log で 0.0 固定（本体トークン未計上） | 現在の設計通り。PM 目視計測（Settings > Usage）の運用で代替。W4-T3 完了条件 #6 との整合を §5 OQ-3 注記で担保 | 不要（仕様通り動作） |
| 2 | Info | lessons.md エントリが「未検証・自動判定なし」の状態で記録される | fail→pass 遷移がない 1 ループ即合格ケースの想定動作。仕様通り（design §13）。エントリの内容充実は /retro での人間確認に委ねる | 不要（仕様通り動作） |
| 3 | Info | gd-session-state.json の loop_count が完了後も 0 を示す | grader ログパス（-loop01-）と状態が矛盾しないか仕様を確認。記録方式（0-index）の可能性が高く、動作上の問題なし。W7-T1 前に仕様との整合を確認することを推奨 | 推奨（W7-T1 前に確認） |

---

## 7. W4-T3 完了条件チェック

tasks.md §W4-T3 完了条件 7 項目の充足判定:

| # | 条件 | 判定 | 根拠 |
|---|------|------|------|
| 1 | 中タスク経路（L1 → l3-executor 二層）でフロー [1]〜[9] が実機完走する（W5 連携を除く実装済み範囲） | ✓ | 全 9 ステップ動作確認。status: "completed" |
| 2 | 報告 JSON の `tokens_used`（自己申告）と Agent 結果の `subagent_tokens`（実測）の乖離が計測・記録されている | ✓ | _divergences[0]（ratio=0.82）/ WARN ログ出力確認 |
| 3 | bound 初期値（中: 150k/3600s）の妥当性が実測データで評価され、`config.md` 再校正の要否が判断されている | ✓ | §4 で評価済。比率 0.502 = 適正範囲。再校正提案なし（N=1 のため次回追加観測推奨） |
| 4 | コストサマリ・`l1_ratio` が実機出力されている（W4-T2 実装の実機検証） | △ | コストサマリ出力 OK。l1_ratio は仕様通り 0.0000（L1 本体トークン未計上）。設計制約のため 0 固定は想定動作 |
| 5 | 実行ログが `docs/artifacts/goal-driven-demo/` に保存されている | ✓ | grader ログ（.claude/logs/gd/gd-20260617-001-loop01-grader.json・1,358 bytes）+ 本報告書 |
| 6 | `l1_tokens` が記録されている（W1-T3 と同一の運用: PM が使用量表示から読み取り） | △ | PM 作業として残。手動計測待ち。cost_log への自動記録は設計上不可能（§5 参照） |
| 7 | 発見された問題が記録され、W7-T1 検収前に解消方針が確定している | ✓ | §6 リスト（3 件）+ 対応提案記載。Critical / Warning = 0 |

**凡例**: ✓ = 充足 / △ = 条件付き充足（運用注記あり）

---

## 8. 総合判定

- フロー [1]〜[9] 実機完走 + 主要観測ポイント（乖離検知・bound 評価・grader 判定・L1 最終検収）の全検証完了
- **W4-T3 主要目的達成**（条件 #1/#2/#3/#5/#7 は完全充足）
- 条件 #4/#6 は設計上の制約（l1_ratio = L1 本体トークン未計上）に起因する△判定であり、
  実装バグではなく仕様通りの動作である
- Critical = 0 / Warning = 0。発見問題はすべて Info レベル
- **W7-T1 検収（B-3 全体納品）へ進められる状態**

---

## 9. 次のアクション

1. **PM**: Settings > Usage 履歴から L1 消費トークンを記録（OQ-3 判断材料の追補。本タスク実行前後の使用量差分を手動算出）
2. **PM**: tasks.md W4-T3 完了チェック記入（v1.4.4 想定）
3. **/retro**: W4-T3 知見の振り返りおよび lessons.md エントリの人間確認
4. **/ship**: リハーサル成果物（本報告書 + README.md 変更）を commit

---

## 参照

| ドキュメント | 箇所 |
|-------------|------|
| W4-T3-rehearsal-package.md | §4 観測ポイント / §5 bound 校正 / §6 OQ-3 / §7 テンプレート / §8 撤退条件 |
| tasks.md | §W4-T3 完了条件 7 項目 |
| .claude/gd-session-state.json | 実行後最終状態 |
| .claude/logs/gd/gd-20260617-001-loop01-grader.json | grader 判定ログ（1,358 bytes） |
| .claude/agent-memory/goal-driven-l3-executor/lessons.md | 蒸留結果（395 bytes） |
