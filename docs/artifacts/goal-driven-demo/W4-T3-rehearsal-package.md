# W4-T3 中タスク実機リハーサル 準備パッケージ

- 作成日: 2026-06-17
- 対象タスク: W4-T3（tasks.md v1.4.2 §W4-T3）
- ステータス: PM 承認待ち（実機起動は承認ゲート通過後）
- 参照: `docs/specs/goal-driven-orchestration/tasks.md` §W4-T3 / `design.md` v0.3.3 / `SKILL.md` v0.1.0

---

## 1. リハーサル概要

### 目的

中タスク経路（L1 → l3-executor 二層）でフロー [1]〜[9] を実機 1 周し、以下の 4 点を検証する:

1. **実機完走**: W5 full-review 連携を除く実装済み範囲（[1]〜[9]）がエラーなく完走すること
2. **乖離計測**: W4-T2 実測正規化（`subagent_tokens` 実測 vs `tokens_used` 自己申告）の実機検証
3. **bound 妥当性評価**: 中タスク初期値（150k tokens / 3600s / max_loop=3）が実タスクに対して適切か評価し `config.md` 再校正の要否を判断する
4. **OQ-3 判断材料収集**: L1 モデル選定に向けた `l1_ratio` 実測データ取得

### 完了条件（tasks.md W4-T3 の 7 項目）

- [ ] 中タスク経路（L1 → l3-executor 二層）でフロー [1]〜[9] が実機完走する（W5 連携を除く実装済み範囲）
- [ ] 報告 JSON の `tokens_used`（自己申告）と Agent 結果の `subagent_tokens`（実測）の乖離が計測・記録されている
- [ ] bound 初期値（中: 150k/3600s）の妥当性が実測データで評価され、`config.md` 再校正の要否が判断されている（要校正の場合は PM へ改訂提案を提示）
- [ ] コストサマリ・`l1_ratio` が実機出力されている（W4-T2 実装の実機検証）
- [ ] 実行ログが `docs/artifacts/goal-driven-demo/` に保存されている
- [ ] `l1_tokens` が記録されている（W1-T3 と同一の運用: PM が使用量表示から読み取り）
- [ ] 発見された問題が記録され、W7-T1 検収前に解消方針が確定している

---

## 2. 対象タスク選定案

中タスク判定条件: 「小タスク条件（rubric 項目数 ≤ 3 AND 未解決質問 = 0 AND 工程数 ≤ 2）を満たさない AND 工程数 < 3 かつ並列分解不要」（SKILL.md フロー [1] / design §9）。

### 候補 A: `docs-stub-sync`（推奨）

**内容**: `docs/artifacts/goal-driven-demo/README.md` のファイル一覧テーブルを実ディレクトリと照合し、不足エントリを追記する。

**スラッグ**: `docs-stub-sync`

**rubric-draft.md 最小版**（design §16 形式）:

```markdown
# rubric-draft: docs-stub-sync（素案）

## 検証候補項目（L1 指揮者が確定・追記すること）

| # | チェック項目（素案） | 検証方法候補 | 備考 |
|---|-------------------|------------|------|
| 1 | README.md のファイル一覧が実ディレクトリと完全一致する | grader 判定（ls 出力と照合） | |
| 2 | 既存エントリの説明文が削除・変更されていない | grader 判定（diff 確認） | |
| 3 | 追記形式が既存テーブルの書式（`| file | description |`）と一致する | grader 判定（目視照合） | |
| 4 | 不足エントリが追加されている（W4-T3-rehearsal-package.md 等） | grader 判定 | |
```

**期待実行時間**: 5〜10 分  
**概算トークン**: l3 executor: 3,000〜8,000 tok / grader: 2,000〜5,000 tok / 合計: 10,000〜20,000 tok（中タスク bound 150k の 10〜13%）

**中タスクとして妥当な根拠**:
- 工程数: 2（ディレクトリ走査 → README 更新）。工程 < 3 で並列分解不要 → 中タスク条件を満たす
- rubric 項目数: 4 → 小タスク条件（≤ 3）を外れる
- 実装量が軽量で bound 消費が 10〜15% 程度と見込まれ、bound 超過リスクが低い
- `docs/artifacts/goal-driven-demo/` への保存が完了条件にあるため成果物パスが明確
- ファイル変更範囲が 1 ファイル（README.md）のみで副作用が限定的

---

### 候補 B: `tdd-patterns-index`

**内容**: `.claude/tdd-patterns.log` の最新エントリを読み取り、`docs/artifacts/tdd-patterns/` に日付別インデックスファイルを作成する。既存インデックスがある場合は最新エントリを追記する。

**スラッグ**: `tdd-patterns-index`

**rubric-draft.md 最小版**:

```markdown
# rubric-draft: tdd-patterns-index（素案）

## 検証候補項目（L1 指揮者が確定・追記すること）

| # | チェック項目（素案） | 検証方法候補 | 備考 |
|---|-------------------|------------|------|
| 1 | `docs/artifacts/tdd-patterns/` にインデックスファイルが存在する | grader 判定（ls 確認） | |
| 2 | インデックス内のエントリが `.claude/tdd-patterns.log` の内容と整合する | grader 判定（ファイル比較） | |
| 3 | 既存インデックスが上書き破壊されていない（追記のみ） | grader 判定（git diff 確認） | |
| 4 | ファイル命名規則が `YYYY-MM-DD-index.md` 形式 | grader 判定（ファイル名確認） | |
| 5 | エントリ形式が Markdown テーブル（`| date | test | result |`） | grader 判定（目視照合） | |
```

**期待実行時間**: 5〜15 分  
**概算トークン**: 15,000〜30,000 tok（中タスク bound の 10〜20%）

**中タスクとして妥当な根拠**:
- 工程数: 2〜3（ログ読み取り → 解析 → 出力ファイル作成）。並列分解不要
- rubric 項目数: 5 → 小タスク条件（≤ 3）を外れる
- `docs/` 配下への書き込みのみで副作用が限定的
- tdd-patterns.log は既存ファイルであり読み取り対象が明確

---

### 候補 C: `skill-md-status-update`

**内容**: `SKILL.md` の「実装ステータス」テーブル（末尾セクション）を現在の実装状態に照合し、未完了だった W2-T1/W2-T2/W3-T2/W4-T1/W4-T2 の状態を「完了」に更新する。

**スラッグ**: `skill-md-status-update`

**rubric-draft.md 最小版**:

```markdown
# rubric-draft: skill-md-status-update（素案）

## 検証候補項目（L1 指揮者が確定・追記すること）

| # | チェック項目（素案） | 検証方法候補 | 備考 |
|---|-------------------|------------|------|
| 1 | 実装ステータステーブルの全エントリが現在の実装状態と一致する | grader 判定（src との照合） | |
| 2 | 「未実装」だった機能のうち完了済みのものが「完了」に更新されている | grader 判定 | W2-T1/T2 / W3-T2 / W4-T1/T2 対象 |
| 3 | 「完了」と記録された機能のスクリプトファイルが実在する | grader 判定（Glob 確認） | |
| 4 | 対応タスク列の記載が変更されていない（既存情報の保全） | grader 判定（diff 確認） | |
```

**期待実行時間**: 3〜8 分  
**概算トークン**: 8,000〜15,000 tok（中タスク bound の 5〜10%）

**中タスクとして妥当な根拠**:
- rubric 項目数: 4 → 小タスク条件（≤ 3）を外れる
- 変更対象ファイルが 1 つ（SKILL.md）で副作用が非常に限定的
- 工程数: 2（現状照合 → テーブル更新）。並列分解不要
- ただし SKILL.md は SE 級（`.claude/skills/` 配下）なので、変更後の報告が必要

> **推奨**: 候補 A（`docs-stub-sync`）を第一候補とする。理由は (1) 完了条件「実行ログが `docs/artifacts/goal-driven-demo/` に保存」との親和性が高く、リハーサル成果物の保存先と一致するため整合が取れる。(2) 変更範囲が最も限定的でリバートが容易。(3) 中タスクとしての適切な規模（rubric 4 項目・工程 2 段階）を満たしている。

---

## 3. 実機起動コマンド一覧

**注意**: 以下のコマンドは PM 承認ゲート通過後にコピペで実行すること。実機起動前に §4 の事前確認チェックリストをすべて完了させること。

### 事前確認コマンド

```bash
# 1. gd-session-state.json の残留確認（残留があれば PM に提示・自動削除禁止）
python .claude/scripts/gd_guard.py --check-residual

# 2. 排他ガード確認（autonomous-state.json / lam-loop-state.json の不在確認）
python .claude/scripts/gd_guard.py --check-exclusion

# 3. .claude/logs/gd/ の状態確認（前回ログが残っていないか確認）
ls .claude/logs/gd/ 2>/dev/null && echo "既存ログあり → PM へ確認" || echo "ログなし（正常）"

# 4. 対象タスクディレクトリの存在確認（候補 A の場合）
ls docs/tasks/docs-stub-sync/ 2>/dev/null || echo "未作成（rubric-draft.md を手動配置する必要あり）"

# 5. Settings > Usage でハードキャップが設定されていることを PM が目視確認（NFR-0 MUST）
# → この確認はスクリプトで代替不可
```

### スキル起動コマンド

```bash
# 候補 A を使用する場合
/goal-driven docs-stub-sync

# 候補 B を使用する場合
/goal-driven tdd-patterns-index

# 候補 C を使用する場合
/goal-driven skill-md-status-update
```

### 起動前の rubric-draft.md 配置（候補 A の場合の手動作業）

```bash
mkdir -p docs/tasks/docs-stub-sync
# その後、§2 候補 A の rubric-draft.md 内容を手動で配置する
# （BUILDING フェーズのためファイル作成はスキル起動前に PM が実施）
```

### 並走モニタリング

```bash
# grader ログのリアルタイム確認（別ターミナル）
# Windows Git Bash では tail -f が使用可能
tail -f .claude/logs/gd/*.json 2>/dev/null || echo "ログファイル未作成"

# セッション状態の確認（loop 中に別ターミナルで随時）
python -c "import json; s=json.load(open('.claude/gd-session-state.json')); print(json.dumps(s, indent=2, ensure_ascii=False))"

# 経過トークン確認
python -c "
import json
s = json.load(open('.claude/gd-session-state.json'))
print(f'total_tokens: {s[\"total_tokens\"]:,} / {s[\"global_token_bound\"]:,}')
print(f'loop_count: {s[\"loop_count\"]} / {s[\"max_loop_count\"]}')
print(f'status: {s[\"status\"]}')
"
```

### 中断時のリカバリ手順

```
1. セッションを強制終了した場合:
   → gd-session-state.json が status: "running" のまま残留する可能性がある
   → 次回起動前に `gd_guard.py --check-residual` を実行し PM へ提示
   → PM の明示承認後に手動削除（自動削除禁止）: ファイルを削除 → 新規起動

2. grader parse error が発生した場合:
   → .claude/logs/gd/ の最新 grader ログを確認
   → 1 回のみ自動再試行（gd_loop.py の run_grader_with_retry）。それでも失敗 → エスカレーション

3. bound 超過でエスカレーションした場合:
   → gd-session-state.json の status を確認（"escalated" になっているはず）
   → L1 が PM に提示したエスカレーション報告を確認
   → §5 の bound 校正判断基準に従い config.md 更新の要否を PM が判断

4. 停止 hook が発火してセッションが終了した場合:
   → Stop hook B-3 節が additionalContext にエスカレーション理由を注入済み
   → Claude のメッセージを確認し gd-session-state.json の内容を PM へ報告
```

---

## 4. 観測ポイント・チェックリスト

フロー [1]〜[9] の各ステップで以下の値を観測・記録すること。

### [1] 難易度判定

- [ ] L1 出力に `route=medium` が含まれること（中タスク判定が正しく機能している）
- [ ] 判定理由（rubric 項目数 ≥ 4、工程数 < 3、並列分解不要）が説明されていること
- [ ] `gd-session-state.json` が `route: "medium"` で初期化されていること

### [2] rubric 生成

- [ ] `docs/tasks/<slug>/rubric.md` が生成されること（中タスク: MUST。`rubric-tmp.md` は不使用）
- [ ] rubric.md の `global_bound` フィールドに `tokens: 150000, time: 3600` が記載されていること（または省略で config 参照）
- [ ] rubric バージョン（生成日 YYYY-MM-DD）が設定されていること

### [3] bound 設定

- [ ] `gd-session-state.json` に以下の値が記録されていること:
  ```json
  {
    "route": "medium",
    "global_token_bound": 150000,
    "global_time_bound": 3600,
    "max_loop_count": 3,
    "loop_count": 0,
    "status": "running"
  }
  ```
- [ ] `task_id` が `gd-YYYYMMDD-NNN` 形式であること
- [ ] `start_time` が Unix タイムスタンプ（float）で記録されていること

### [4] l3-executor 実行後のトークン累積

- [ ] Agent ツール結果から `subagent_tokens` が取得できているか確認（None の場合: P-2 WARN ログが `.claude/logs/gd/` または stdout に出力されているか確認）
- [ ] `gd-session-state.json` の `total_tokens` が executor 実行後に更新されていること
- [ ] `cost_log.l3_tokens` に executor の実測トークンが累積されていること
- [ ] `tokens_used`（自己申告）と `subagent_tokens`（実測）の乖離率を記録すること
  - 乖離率 > 0.20 の場合: `[gd-warn] token divergence` ログが出力されているか確認
  - `cost_log._divergences` に乖離情報が記録されているか確認

### [5] grader 実行後のトークン累積

- [ ] `cost_log.grader_tokens` に grader の実測トークンが累積されていること
- [ ] grader の `subagent_tokens` 取得成否を記録すること
- [ ] grader ログが `.claude/logs/gd/<task_id>-loop1-grader.json` に保存されていること
- [ ] grader 出力 JSON が design §11 のスキーマを満たしていること:
  ```json
  {
    "rubric_version": "YYYY-MM-DD",
    "overall": "pass | fail",
    "items": [...],
    "escalate": false,
    "escalate_reason": ""
  }
  ```

### [6] 乖離検知（≥ 0.20 の場合のみ）

- [ ] stdout に `[gd-warn] token divergence: layer=l3, self_reported=X, measured=Y, ratio=Z` 形式のログが出力されていること
- [ ] `cost_log._divergences` 配列に以下の形式で記録されていること:
  ```json
  {"layer": "l3", "self_reported": X, "measured": Y, "ratio": Z}
  ```
- [ ] W1-T3 で観測された大幅乖離（自己申告 100 tok vs 実測 26,305 tok）と比較した際の傾向を記録すること

### [7] L1 最終検収

- [ ] grader 合格後に L1 最終検収（LLM 呼び出し）が実施されること（中タスクルートでは MUST・小タスクと異なる）
- [ ] L1 最終検収で消費されたトークンが `cost_log.l1_tokens` に加算されていること
- [ ] 最終検収後に `gd-session-state.json` の `status` が `"completed"` に更新されること

### [8] メモリ蒸留

- [ ] `python .claude/scripts/distill-lessons.py --task-id <task_id> --grader-log .claude/logs/gd/<task_id>-loop*-grader.json` が正常終了すること
- [ ] `.claude/agent-memory/goal-driven-l3-executor/lessons.md` にエントリが追記されていること

### [9] 後処理・コストサマリ出力

- [ ] `build_cost_summary()` の出力が以下の design §14 形式と整合していること:
  ```
  ## コストサマリ（タスク: <task_id>）
  L1 指揮者:  X,XXX tok ( XX.X% )  ← 目標 ≤20%
  L2 班長:        0 tok (  0.0% )
  L3 実行者:  X,XXX tok ( XX.X% )
  grader:     X,XXX tok ( XX.X% )
  ---------------------------------
  合計:       X,XXX tok
  ```
- [ ] `gd-session-state.json` の `status` が `"completed"` であること
- [ ] 実行ログが `docs/artifacts/goal-driven-demo/<slug>/` に保存されていること

### 期待ログパス一覧

| ログ種別 | パス |
|---------|------|
| grader ログ（ループ 1 回目） | `.claude/logs/gd/<task_id>-loop1-grader.json` |
| grader ログ（ループ N 回目） | `.claude/logs/gd/<task_id>-loopN-grader.json` |
| セッション状態 | `.claude/gd-session-state.json` |
| 実行成果物 | `docs/artifacts/goal-driven-demo/<slug>/` |
| l3-executor lessons | `.claude/agent-memory/goal-driven-l3-executor/lessons.md` |

---

## 5. bound 校正の判断基準

リハーサル結果から以下のルールに従い bound 再校正の要否を判断する。

| 実測 `total_tokens` / `global_token_bound`（150k）の比率 | 判断 | アクション |
|----------------------------------------------------------|------|----------|
| **0.5 未満**（75k tok 以下で完了） | 下方再校正候補 | 中タスク bound を 50k〜100k に引き下げる提案を PM に提示。config.md §2 の `medium.global_token_bound` を更新 |
| **0.5〜0.9**（75k〜135k） | 適正範囲 | 再校正不要。現行値維持 |
| **0.9 超**（135k〜150k） | 上方再校正必要 | 中タスク bound を 200k〜250k に引き上げる提案を PM に提示。超過リスクが高い |
| **bound 到達でエスカレーション** | bound 別問題 | 比率ではなく要因分析が必要（rubric が困難すぎる / タスク選定が不適切 / 実装エラーの繰り返し等）。PM へエスカレーション報告を提示 |

### max_loop_count に関する判断基準

- ループ 1 回で合格: 理想的。タスク選定とrubric品質が良好
- ループ 2 回で合格: 許容範囲。差し戻し内容を記録
- ループ 3 回（max_loop=3）で合格: 上限到達だが完走。rubric の複雑さを再評価
- ループ 3 回到達 + escalate: **bound 別問題**。上表の「bound 到達でエスカレーション」に分類。タスク選定または rubric の見直しが必要

### 経過時間に関する判断基準

- 実測 elapsed / 3600s（1h bound）の比率:
  - 0.5 未満: 適正
  - 0.5〜0.9: 余裕あり
  - 0.9 超: 長時間タスクには 7200s への引き上げを検討
  - time_bound 到達: エスカレーション（第一防衛線 or Stop hook B-3 節が発動）

---

## 6. OQ-3 判断材料の収集項目

OQ-3（L1 モデル選定・6/23 以降に PM が判断）のために以下のメトリクスを記録する。

### 必須記録項目

| 項目 | 記録方法 | 記録先 |
|------|---------|--------|
| `l1_ratio` 実測値 | `compute_l1_ratio()` の戻り値 | §7 報告書テンプレートの観測値表 |
| L1 消費トークン内訳（フロー[1] 難易度判定） | PM が使用量表示から読み取り | §7 報告書テンプレート |
| L1 消費トークン内訳（フロー[7] 最終検収） | PM が使用量表示から読み取り | §7 報告書テンプレート |
| L3 実測トークン（executor） | `cost_log.l3_tokens` | gd-session-state.json |
| grader 実測トークン | `cost_log.grader_tokens` | gd-session-state.json |
| ループ回数 | `loop_count` | gd-session-state.json |

### l1_ratio の期待値と評価基準

- **期待範囲（中タスク）**: 5〜15%（design §14「L1 指揮者: 目標 ≤20%」）
- 実測 l1_ratio ≤ 20%: 現行 Sonnet 継続で問題なし
- 実測 l1_ratio > 20%: rubric 生成の委任（L2 に移管）を検討（design §14 OQ-3 連携）
- 5 タスク以上のデータが揃った時点で PM が最終判断（本タスクはデータポイント 1 として位置づけ）

### 判断品質に問題があった場合の記録

- 差し戻し理由（grader の fail 判定内容）を `docs/artifacts/goal-driven-demo/<slug>/` に保存
- 差し戻しパターン（同一 rubric 項目への繰り返し不合格）がある場合は rubric 文言の改善候補として記録

---

## 7. リハーサル後の成果物：PM 報告書テンプレート

**保存先**: `docs/artifacts/goal-driven-demo/<slug>/W4-T3-report.md`（実機実行後に作成）

```markdown
# W4-T3 中タスク実機リハーサル 実行報告

- 実施日時: YYYY-MM-DD HH:MM
- task_id: gd-YYYYMMDD-NNN
- task_slug: <slug>
- 実施者: PM（手動起動） + L1/L3/grader（エージェント）

## 1. 実機完走

- 完走: Yes / No
- 理由（No の場合）: <記載>

## 2. 観測値 vs 期待値

| 観測項目 | 期待値 | 実測値 | 判定 |
|---------|--------|--------|------|
| route | medium | <実測> | Pass / Fail |
| global_token_bound（初期値） | 150,000 | <実測> | Pass / Fail |
| global_time_bound（初期値） | 3,600 | <実測> | Pass / Fail |
| max_loop_count | 3 | <実測> | Pass / Fail |
| 実際のループ回数 | 1〜3 | <実測> | 記録のみ |
| 実測 total_tokens | — | <実測> | 記録のみ |
| total_tokens / 150k 比率 | 0.5〜0.9 | <実測> | 適正 / 要校正 |
| l1_ratio | 5〜15% | <実測> | 適正 / 要確認 |
| subagent_tokens 取得 | 成功（None でない） | <成功/失敗> | Pass / Fail |
| grader ログ保存 | .claude/logs/gd/*.json | <実測> | Pass / Fail |
| コストサマリ出力 | design §14 形式 | <出力確認> | Pass / Fail |

## 3. 乖離検知の発生有無

| 層 | 自己申告 tokens_used | 実測 subagent_tokens | 乖離率 | WARN 発生 |
|----|---------------------|---------------------|--------|----------|
| l3-executor | <値> | <値> | <値> | Yes / No |
| grader | <値> | <値> | <値> | Yes / No |

## 4. bound 校正提案

- 再校正の要否: 不要 / 必要
- 提案内容（必要な場合）: <記載>
  - `config.md` §2 `medium.global_token_bound`: 150,000 → <提案値>

## 5. OQ-3 データ

| 項目 | 値 |
|------|-----|
| l1_tokens（フロー[1] 難易度判定） | PM 読み取り値: |
| l1_tokens（フロー[7] 最終検収） | PM 読み取り値: |
| total_tokens（gd-session-state.json） | |
| l1_ratio（compute_l1_ratio() 出力） | |
| ループ回数 | |

## 6. 発見問題リスト

| # | 問題 | 重要度 | 対応方針 | W7-T1 前解消 |
|---|------|--------|---------|-------------|
| 1 | <問題> | Critical / Warning / Info | <方針> | Yes / No |

## 7. W4-T3 完了条件チェック

- [ ] 中タスク経路でフロー [1]〜[9] が実機完走した
- [ ] tokens_used vs subagent_tokens の乖離が計測・記録された
- [ ] bound 初期値の妥当性が評価された
- [ ] コストサマリ・l1_ratio が実機出力された
- [ ] 実行ログが docs/artifacts/goal-driven-demo/ に保存された
- [ ] l1_tokens が記録された
- [ ] 発見された問題の解消方針が確定した
```

---

## 8. リスクと撤退条件

### 即時中断すべき条件

| 条件 | 対応 |
|------|------|
| bound 超過でエスカレーション（escalated）が起きたとき | セッションを終了し、gd-session-state.json の内容を確認。§5 の要因分析を実施後 PM に報告 |
| grader が parse error を連発し再試行も失敗したとき（`run_grader_with_retry` が escalate を返したとき） | grader ログを確認し rubric の記述問題または grader の応答フォーマット問題を特定。PM に報告 |
| 想定外のスタックトレース（Python 例外）が発生したとき | エラーメッセージとスタックトレース全文を `docs/artifacts/goal-driven-demo/<slug>/error-<timestamp>.txt` に保存。PM に報告 |
| `gd-session-state.json` に `fallback: "two_layer"` が設定されたとき | 三層→二層退避（design §11b）が発動。中タスクでは通常起きない異常事態のため PM に報告 |
| ネスト深さ上限（`nest_depth_limit: 5`）超過エラーが発生したとき | プラットフォーム制約。中タスクは二層（深さ 2）のため通常起きない。発生した場合は PM に報告 |

### 撤退後の状態管理

```
撤退後必須作業:
1. gd-session-state.json の status 確認（"escalated" になっているか）
2. なっていない場合は PM が手動で "escalated" に更新（自動削除禁止）
3. .claude/logs/gd/ の最新 grader ログを保存
4. §7 報告書テンプレートの問題リストに記載
5. 次の起動前に gd_guard.py --check-residual を必ず実行
```

### 中断しない許容範囲

- ループ 1〜2 回の差し戻し（max_loop=3 内の正常動作）
- grader が 1 回エラーを返した後に自動再試行で成功した場合（`run_grader_with_retry` の正常動作）
- `subagent_tokens` が None になり P-2 フォールバック（自己申告 `tokens_used` を採用）が発動した場合（WARN ログを確認して記録するが続行可）

---

## 参照

| ドキュメント | 箇所 |
|-------------|------|
| `docs/specs/goal-driven-orchestration/tasks.md` | §W4-T3 完了条件・依存関係 |
| `docs/specs/goal-driven-orchestration/design.md` | §9.2（ルート設定値）/ §10（bound 機構）/ §14（コスト集計）/ §16（rubric-draft スキーマ） |
| `.claude/skills/goal-driven/SKILL.md` | フロー [1]〜[9] 詳細・禁止事項 |
| `.claude/scripts/gd_loop.py` | `run_plan_b_loop` / `run_grader_with_retry` / `save_grader_log` |
| `.claude/scripts/gd_state.py` | `accumulate_subagent_tokens` / `compute_l1_ratio` / `build_cost_summary` / `record_token_divergence` |
| `docs/artifacts/goal-driven-demo/smoke-test-runbook.md` | W1-T3 スモーク手順書（参考） |
| `docs/specs/goal-driven-orchestration/config.md` | bound 外部化設定 |
