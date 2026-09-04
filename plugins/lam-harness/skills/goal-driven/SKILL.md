---
name: goal-driven
description: "ゴール駆動オーケストレーション - rubric ファーストの自己修正 BUILDING ループ"
version: 0.1.0
disable-model-invocation: true
---

# goal-driven スキル（B-3 W1-T1 骨格）

## 注意事項（Dynamic Workflows 禁止宣言）

本スキルは Dynamic Workflows を使用しない。
effort を `xhigh` へ昇格させる指定をしてはならない（MUST NOT。旧「`low` または `default` 明示」は
2026-07-14 R1-036 で撤回 — `default` は Claude Code EffortLevel の有効値ではない / design §12 参照）。
`"ultracode"`、`"use a workflow"` 等のキーワードを使用してはならない（MUST NOT）。
`disableWorkflows: true`（または `CLAUDE_CODE_DISABLE_WORKFLOWS=1`）を推奨設定として適用すること。

> **重要**: 本スキルは `/goal` コマンドをサブエージェント内で使用しない（Plan B 確定済み）。
> `/goal` は 2026-06-12 の実測検証によりサブエージェント内でスラッシュコマンドとして
> 展開されないことが確認された（`research/oq1-goal-subagent-test.md` 参照）。
> 打ち切り制御は `max_loop_count`（`gd-session-state.json` フィールド・初期値 3）と、L3 の
> **`maxTurns: 20`**（`goal-driven-l3-executor.md` フロントマター）の 2 本で担保する（AC-7 Plan B 対応）。
>
> **キー名の訂正（2026-08-21）**: 旧記述にあった `max_turns`（snake_case）は subagent frontmatter の
> 有効キーではなく、**bound は一度も機能していなかった**（2026-08-20 発覚）。正しいキーは
> **`maxTurns`（camelCase）**であり、plugin agent 専用ではなく `.claude/agents/*.md` でも有効である
> ことを対照実験で確認した（`maxTurns: 2` の agent は 2 ターンで打ち切られ、無指定の対照は 10 ターン
> 完走 / 記録: `docs/artifacts/maxturns-probe-2026-08-21.md`）。

---

## 起動引数

```
/goal-driven <task-description-or-slug>
```

- `<task-description-or-slug>`: 実行するタスクの説明またはスラッグ。
  `docs/tasks/<slug>/` が存在する場合は design.md / rubric-draft.md を参照する。

---

## 前提条件確認（起動前チェック）

### ステップ 0: ハードキャップ確認（NFR-0）

本スキルを使用する前に、**Settings > Usage でハードキャップが設定されていること**を
人間（PM）が確認していなければならない（MUST）。
スキルはこの確認を代替できない。

### ステップ 0a: 排他ガード（design §10 MUST）

```bash
bash .claude/scripts/py_invoke.sh .claude/scripts/gd_guard.py --check-exclusion
```

`autonomous-state.json` または `lam-loop-state.json` が存在する場合は**起動を拒否**する。
goal-driven スキルは autonomous / lam-orchestrate セッションと同時実行できない。

### ステップ 0b: 残留リカバリ（design §10 フェイルセーフ）

```bash
bash .claude/scripts/py_invoke.sh .claude/scripts/gd_guard.py --check-residual
```

`gd-session-state.json` が `status: "running"` のまま存在する場合（前回セッションの
異常終了による残留）、**自動削除はせず PM に提示して明示承認後に削除して新規開始する**。

---

## フロー [1]〜[9]: 実行手順

### [1] 難易度判定（LLM 呼び出し）

L1 指揮者がタスクを分析し、三段階ルートを決定する。

**判定条件（FR-6 / design §9）**:

| ルート | 条件（すべて満たす場合） |
|--------|----------------------|
| **小タスク** | rubric 項目数 ≤ 3 AND 未解決質問 = 0 AND 工程数 ≤ 2 |
| **中タスク** | 小タスク条件を満たさない AND 工程数 < 3 かつ並列分解不要 |
| **大タスク** | 工程数 ≥ 3 OR 並列分解が必要 |

判定後、ルートと理由を出力する。

### [2] rubric 生成（LLM 呼び出し）

**入力処理**:
1. `docs/tasks/<slug>/rubric-draft.md` が存在する場合: 内容を確認・確定し `rubric.md` を生成
2. `rubric-draft.md` がない場合: L1 がゼロから生成
3. `design.md` は L1 の rubric 生成の参照資料として使用

**配置先**:
- 中タスク・大タスク: `docs/tasks/<slug>/rubric.md`（MUST）
- 小タスク: `.claude/rubric-tmp.md`（タスク終了時にスクリプトが削除・design §6 MUST）

**P-4 対応（auto-compact 後の rubric 再読み込み）**:
各エージェントは起動時に rubric.md を Read ツールで再読み込みすること。
コンテキスト圧縮後もファイルシステム経由で参照可能な状態を維持する（MUST）。

### [3] bound 設定（design §9.2 / §10）

`gd-session-state.json` を初期化する（W2-T2 の範囲）。

初期値（`docs/specs/goal-driven-orchestration/config.md` で外部化可能）:

| パラメータ | 小タスク | 中タスク | 大タスク |
|-----------|--------|--------|--------|
| global_token_bound | 50,000 | 150,000 | 400,000 |
| global_time_bound | 3,600s | 3,600s | 7,200s |
| max_loop_count | 3 | 3 | 3 |
| L3 `maxTurns`（frontmatter / **全ルート 20 固定**）| 20 | 20 | 20 |

> **注（2026-08-21 / 前注 2026-08-20 を差し替え）**: `maxTurns` は `goal-driven-l3-executor.md` に
> **20 固定**で設定した。frontmatter は静的であり L3 定義は 1 ファイルしかないため、**ルート別の値
> （設計値 小:10 / 中:20 / 大:15）は表現できない**。設計値の最大値をバックストップとして採っている。
>
> したがって小タスクでも 20 ターンまで走る（設計意図より緩い）。ただし改訂前は
> `max_turns`（snake_case）が無効キーでターン打ち切りが**一切効いていなかった**ため、後退ではない。
> ルート別の粒度を取り戻すには L3 agent 定義のファイル分割が要る（2026-08-21 に見送りを決定）。
> 打ち切りは本項と `max_loop_count`・グローバル bound（token / time）が分担する。

**`gd-session-state.json` スキーマ（design §10）**:
```json
{
  "task_id": "gd-YYYYMMDD-NNN",
  "task_slug": "<slug>",
  "route": "small | medium | large",
  "nest_depth_limit": 5,
  "global_token_bound": 150000,
  "global_time_bound": 3600,
  "total_tokens": 0,
  "loop_count": 0,
  "max_loop_count": 3,
  "start_time": 1718064000.0,
  "status": "running"
}
```

パスは `get_project_root()` で解決した絶対パスを使用する（P-3 対応・cwd 変動リスク回避）。

### [4] 実行ループ（Plan B: 自前制御ループ・design §8）

> **Plan B 確定（2026-06-12 実測）**: `/goal` はサブエージェント内で機能しない。
> SKILL.md スクリプト（L1 コンテキスト）が制御ループを担う。

**打ち切り制御（AC-7 Plan B 対応）**:
- `/goal` を使用しないため `or stop after N turns` は使用しない
- 代替の打ち切り制御: `max_loop_count`（差し戻し回数上限）。当初はエージェントの `max_turns` との
  併用も想定していたが、`max_turns` は subagent frontmatter の有効キーではなく**未実装**（詳細は
  上記「起動引数」直後の注記を参照）
- これは Plan B 確定によるやむを得ない仕様変更である（design v0.3.1 §8 に記録済み）

```
自前制御ループ骨格（W3-T2 実装済み・.claude/scripts/gd_loop.py）:

while loop_count < max_loop_count AND total_tokens < global_token_bound:

  [1] bound 残量チェック（spawn-time enforcement）
      → 残量不足ならエスカレーション

  [2] Agent(goal-driven-l3-executor) 起動
      prompt: タスク内容 + rubric.md パス + 前回の差し戻し情報
      → 構造化報告 JSON を受け取る（design §7 スキーマ）

  [3] Agent ツール結果の実測 subagent_tokens を gd-session-state.json に累積
      （cost_log の l1/l2/l3/grader 層別 + total_tokens 連動加算）
      実測取得失敗時のみ報告 JSON の tokens_used（自己申告）を P-2 フォールバックとして採用
      （WARN ログ出力・乖離率 >0.20 の場合は cost_log._divergences に記録）

  [4] Agent(goal-driven-grader) 起動（別コンテキスト・FR-2）
      prompt: 構造化報告 JSON + rubric.md
      → grader 判定 JSON を受け取る

  [5] grader 判定処理
      - 合格 (overall: "pass") → ループ終了 → [7] へ
      - エスカレーション (escalate: true) → エスカレーション処理 → [9] へ
      - grader エラー / 不正 JSON → 1 回のみ再試行
        再試行も失敗 → エスカレーション（grader 失敗を合格として扱わない MUST NOT）
      - 不合格 (overall: "fail") → loop_count++ → 差し戻し情報を生成 → ループ継続

loop_count >= max_loop_count → エスカレーション（bound 超過）
```

**小タスクルートでは**:
- L1 指揮者はループ後に関与しない（MUST NOT）
- grader 合格をもって完了とする（L1 最終検収スキップ・design §9.1 MUST）

**大タスクルートでは**:
- Agent(goal-driven-l2-foreman) を介して l3-executor を分配する
- ネスト失敗時は `gd-session-state.json` に `fallback: "two_layer"` をセットし
  L1 が l3-executor を直接制御する（三層→二層退避・design §11b）

**W3-T2 実装（`.claude/scripts/gd_loop.py`）の主要 API**:
```python
from gd_loop import (
    run_plan_b_loop,          # Plan B 制御ループ本体
    parse_grader_output,      # grader 判定 JSON パース
    run_grader_with_retry,    # grader エラー時 1 回再試行（戻り型: tuple[dict, Optional[int]]）
    is_nest_failure,          # §11b ネスト失敗検知
    activate_two_layer_fallback,  # §11b 三層→二層退避
    save_grader_log,          # NFR-3: grader ログ保存
    build_l3_executor_prompt, # l3-executor プロンプト生成
    build_grader_prompt,      # grader プロンプト生成
)
```

`run_plan_b_loop()` の `invoke_executor_fn` / `invoke_grader_fn` の型:
```python
Callable[[str], tuple[str, Optional[int]]]
# 引数: prompt: str
# 戻り値: (raw_output: str, subagent_tokens: Optional[int])
#   subagent_tokens は Agent ツール結果から取得した実測値。取得不可時は None。
```

それぞれ Agent(goal-driven-l3-executor) / Agent(goal-driven-grader) の
呼び出しを渡すこと（AC-5: 独立した Agent 呼び出し・FR-2: 別コンテキスト）。

**W4-T2 実装（`.claude/scripts/gd_state.py`）の追加 API（コスト集計）**:
```python
from gd_state import (
    accumulate_subagent_tokens,  # 層別 subagent_tokens を cost_log に累積 + total_tokens 連動加算
    compute_l1_ratio,            # l1_tokens / total_tokens を計算（total=0 時は 0.0）
    build_cost_summary,          # design §14 形式のコスト集計文字列を生成
    record_token_divergence,     # 自己申告 vs 実測の乖離を記録（±20% 超で WARN ログ出力）
)
```

`accumulate_subagent_tokens(layer, tokens, project_root)` の `layer` 引数有効値:
`"l1"` / `"l2"` / `"l3"` / `"grader"`

### [5] grader 呼び出し（FR-2）

grader は毎回独立した Agent 呼び出しで起動する（作業者と別コンテキスト・MUST）。

```
Agent(
  agent="goal-driven-grader",
  prompt="rubric_path=<project_root>/docs/tasks/<slug>/rubric.md\n" +
         "report=<構造化報告 JSON>"
)
```

小タスクでは `rubric_path` に `.claude/rubric-tmp.md` を渡す。

grader の出力スキーマ（design §11）:
```json
{
  "rubric_version": "YYYY-MM-DD",
  "overall": "pass | fail",
  "items": [{"id": 1, "result": "pass", "reason": "..."}],
  "escalate": false,
  "escalate_reason": ""
}
```

grader ログは `.claude/logs/gd/<task_id>-loop<N>-grader.json` に保存する（NFR-3）。

### [6] エスカレーション処理

bound 超過・grader 繰り返し不合格・grader エラー等でエスカレーションする場合:

1. `gd-session-state.json` の `status` を `"escalated"` に更新
2. エスカレーション理由を含む構造化報告を L1 が PM に提示して終了
3. Stop hook B-3 節（第二防衛線）は自動的にバックストップとして機能する（design §10）

### [7] L1 最終検収（中タスク・大タスクのみ）

中タスク・大タスクでは grader 合格後に L1 最終検収（LLM 呼び出し）を実施する。
小タスクルートではこのステップをスキップする（design §9.1 MUST）。

### [8] メモリ蒸留（W4-T1 実装済み）

```bash
bash .claude/scripts/py_invoke.sh .claude/scripts/distill-lessons.py \
  --task-id <task_id> \
  --grader-log .claude/logs/gd/<task_id>-loop*-grader.json
```

小タスクルート（grader ログのみ・design §9.1）:
```bash
bash .claude/scripts/py_invoke.sh .claude/scripts/distill-lessons.py \
  --task-id <task_id> \
  --grader-log .claude/logs/gd/<task_id>-loop01-grader.json \
  --small-task
```

- 小タスクルートでは grader 判定 JSON のみを入力とする（design §9.1）
- 検証済み教訓は `.claude/agent-memory/goal-driven-l3-executor/lessons.md` に書き込む
- `docs/artifacts/knowledge/` への自動書き込みは禁止（W-5 制約・design §13）

**W4-T1 実装（`.claude/scripts/distill_lessons.py`）の主要 API**:
```python
from distill_lessons import (
    distill,               # grader ログ分析・lessons.md 追記（重複スキップ）
    build_lesson_entry,    # grader ログから lessons.md エントリを構築
    get_project_root,      # プロジェクトルート解決（P-3 対応）
    build_arg_parser,      # CLI argparse パーサ（--task-id / --grader-log / --small-task）
)
```

`distill()` の呼び出しパターン:
```python
distill(
    task_id="gd-20260613-001",
    grader_log_paths=["path/to/loop01-grader.json", "path/to/loop02-grader.json"],
    lessons_path=None,     # None でデフォルトパス（.claude/agent-memory/.../lessons.md）を使用
    verified=None,         # None で fail→pass 遷移から自動判定
)
# 小タスクルートは grader_log_paths を 1 件のみ渡す呼び出し方の違いであり、
# distill() のロジックは全ルート共通 (R1-007 / design §9.1)
```

### [9] 後処理・完了報告

1. **rubric-tmp.md の削除**（小タスクルートのみ・design §6 MUST）:
   ```bash
   bash .claude/scripts/py_invoke.sh .claude/scripts/gd_guard.py --cleanup-rubric-tmp
   ```
   合格・エスカレーションを問わず実行する。

2. `gd-session-state.json` の `status` を更新:
   - 合格完了: `"completed"`
   - エスカレーション: `"escalated"`（手順 [6] で実施済み）

3. コストサマリを出力する（AC-11 / W4-T2 の範囲）。

4. PM に完了または要対応の状況を報告する。

---


## 詳細仕様（必要になった時点で読む）

- 三段階ルートの詳細 / bound 機構: [references/route-and-bound.md](references/route-and-bound.md)（フロー [3] と [6] で参照）
- 実装ステータス / Loop Engineering 観点 / 参照文献: [references/background.md](references/background.md)（実行手順ではない）
## 禁止事項

- Dynamic Workflows の使用（FR-8 / AC-10）
- `"ultracode"` / `"use a workflow"` キーワードの使用
- L3 / grader による自律 spawn（FR-7）
- grader 失敗を合格として扱うこと（FR-2 MUST NOT）
- L1 が実装・テスト・ログ読取を直接行うこと（役割分離）
- 小タスクでの L1 最終検収（design §9.1 MUST NOT）
- rubric-tmp.md の手動削除（スクリプトが担当）

---

## 権限等級

- 本スキルの変更: **SE 級**（`.claude/skills/` への変更）
- ガードスクリプト変更: **SE 級**
