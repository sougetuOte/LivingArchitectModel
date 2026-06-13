---
name: goal-driven
description: "ゴール駆動オーケストレーション - rubric ファーストの自己修正 BUILDING ループ"
version: 0.1.0
disable-model-invocation: true
---

# goal-driven スキル（B-3 W1-T1 骨格）

## 注意事項（Dynamic Workflows 禁止宣言）

本スキルは Dynamic Workflows を使用しない。
effort 設定は明示的に `low` または `default` とすること。
`"ultracode"`、`"use a workflow"` 等のキーワードを使用してはならない（MUST NOT）。
`disableWorkflows: true`（または `CLAUDE_CODE_DISABLE_WORKFLOWS=1`）を推奨設定として適用すること。

> **重要**: 本スキルは `/goal` コマンドをサブエージェント内で使用しない（Plan B 確定済み）。
> `/goal` は 2026-06-12 の実測検証によりサブエージェント内でスラッシュコマンドとして
> 展開されないことが確認された（`research/oq1-goal-subagent-test.md` 参照）。
> 打ち切り制御は `max_loop_count`（`gd-session-state.json` フィールド・初期値 3）と
> `max_turns`（エージェントフロントマター）の組み合わせで担保する（AC-7 Plan B 対応）。

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
python .claude/scripts/gd_guard.py --check-exclusion
```

`autonomous-state.json` または `lam-loop-state.json` が存在する場合は**起動を拒否**する。
goal-driven スキルは autonomous / lam-orchestrate セッションと同時実行できない。

### ステップ 0b: 残留リカバリ（design §10 フェイルセーフ）

```bash
python .claude/scripts/gd_guard.py --check-residual
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
| L3 max_turns | 10 | 20 | 15（工程ごと） |

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
- 代替の打ち切り制御: `max_loop_count`（差し戻し回数上限）+ エージェントの `max_turns` で担保
- これは Plan B 確定によるやむを得ない仕様変更である（design v0.3.1 §8 に記録済み）

```
自前制御ループ骨格（W3-T2 実装済み・.claude/scripts/gd_loop.py）:

while loop_count < max_loop_count AND total_tokens < global_token_bound:

  [1] bound 残量チェック（spawn-time enforcement）
      → 残量不足ならエスカレーション

  [2] Agent(goal-driven-l3-executor) 起動
      prompt: タスク内容 + rubric.md パス + 前回の差し戻し情報
      → 構造化報告 JSON を受け取る（design §7 スキーマ）

  [3] tokens_used を gd-session-state.json に累積
      total_tokens += report.tokens_used

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
    run_grader_with_retry,    # grader エラー時 1 回再試行
    is_nest_failure,          # §11b ネスト失敗検知
    activate_two_layer_fallback,  # §11b 三層→二層退避
    save_grader_log,          # NFR-3: grader ログ保存
    build_l3_executor_prompt, # l3-executor プロンプト生成
    build_grader_prompt,      # grader プロンプト生成
)
```

`run_plan_b_loop()` の `invoke_executor_fn` / `invoke_grader_fn` には
それぞれ Agent(goal-driven-l3-executor) / Agent(goal-driven-grader) の
呼び出しを渡すこと（AC-5: 独立した Agent 呼び出し・FR-2: 別コンテキスト）。

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
python .claude/scripts/distill-lessons.py \
  --task-id <task_id> \
  --grader-log .claude/logs/gd/<task_id>-loop*-grader.json
```

小タスクルート（grader ログのみ・design §9.1）:
```bash
python .claude/scripts/distill-lessons.py \
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
    is_small_task=False,   # 小タスクルート時は True
)
```

### [9] 後処理・完了報告

1. **rubric-tmp.md の削除**（小タスクルートのみ・design §6 MUST）:
   ```bash
   python .claude/scripts/gd_guard.py --cleanup-rubric-tmp
   ```
   合格・エスカレーションを問わず実行する。

2. `gd-session-state.json` の `status` を更新:
   - 合格完了: `"completed"`
   - エスカレーション: `"escalated"`（手順 [6] で実施済み）

3. コストサマリを出力する（AC-11 / W4-T2 の範囲）。

4. PM に完了または要対応の状況を報告する。

---

## 三段階ルート詳細（FR-6 / design §9）

```
L1 指揮者: タスク分析（LLM 呼び出し）
  ↓
以下をすべて満たすか？
  条件 A: rubric 項目数 ≤ 3
  条件 B: 未解決質問 = 0
  条件 C: 工程数 ≤ 2
  ↓
  YES → [小タスクルート]
          スキルスクリプトが l3-executor を直接起動
          L1 はこの後関与しない（MUST NOT）
          grader 起動主体 = スキルスクリプト（design §9.1）
  ↓
  NO → 工程数 ≥ 3 OR 並列分解が必要か？
        YES → [大タスクルート] L1 → l2-foreman → l3-executor（三層）
        NO  → [中タスクルート] L1 → l3-executor（二層）
```

---

## bound 機構（FR-4 / design §10）

### 二段防衛線

| 防衛線 | 主体 | 方式 |
|--------|------|------|
| **第一（主）** | スキルスクリプト（L1 コンテキスト） | spawn 前に残予算チェック（spawn-time enforcement） |
| **第二（バックストップ）** | Stop hook B-3 節 | セッション状態ファイルを読み、bound 超過なら exit 0 + additionalContext |

### 打ち切り制御（Plan B / AC-7 読み替え）

Plan B（自前ループ）では `/goal` を使用しないため、`or stop after N turns` は不使用。
代替として:
- `max_loop_count`（差し戻し回数上限・外部化設定・FR-4 MUST）でループ打ち切り
- エージェントフロントマターの `max_turns`（小:10 / 中:20 / 大:15）でターン打ち切り
- グローバル bound（tokens + time）でセッション全体を打ち切り

---

## LAM フェーズ整合（NFR-4）

本スキルは BUILDING フェーズで使用する。

```
lam-orchestrate（PLANNING 並列実行）
     ↓ 成果物受け渡し（docs/tasks/<slug>/）
goal-driven スキル（BUILDING 自己修正ループ）  ← 本スキル
     ↓ 最終成果物
full-review（納品前検収）
```

---

## 禁止事項

- Dynamic Workflows の使用（FR-8 / AC-10）
- `"ultracode"` / `"use a workflow"` キーワードの使用
- L3 / grader による自律 spawn（FR-7）
- grader 失敗を合格として扱うこと（FR-2 MUST NOT）
- L1 が実装・テスト・ログ読取を直接行うこと（役割分離）
- 小タスクでの L1 最終検収（design §9.1 MUST NOT）
- rubric-tmp.md の手動削除（スクリプトが担当）

---

## 実装ステータス（W1-T1）

| 機能 | 状態 | 対応タスク |
|------|------|----------|
| SKILL.md 骨格（フロー[1]〜[9] 記述） | **完了** | W1-T1 |
| 排他ガード（gd_guard.py） | **完了** | W1-T1 |
| rubric-tmp.md 削除（gd_guard.py） | **完了** | W1-T1 |
| 残留リカバリ検知（gd_guard.py） | **完了** | W1-T1 |
| エージェント定義 3 件 | 未実装 | W2-T1 |
| bound スクリプト（gd-state.py） | 未実装 | W2-T2 |
| Stop hook B-3 節 | 未実装（PM-G1 必要） | W2-T3 |
| 実行ループ本体（Plan B） | **完了** | W3-T2 |
| distill-lessons.py | **完了** | W4-T1 |

---

## 参照

- 仕様: `docs/specs/goal-driven-orchestration/requirements.md` v1.2.0
- 設計: `docs/specs/goal-driven-orchestration/design.md` v0.3.1
- タスク: `docs/specs/goal-driven-orchestration/tasks.md` v1.2.0
- Plan B 確定根拠: `docs/specs/goal-driven-orchestration/research/oq1-goal-subagent-test.md`
- 設定: `docs/specs/goal-driven-orchestration/config.md`（W1-T2 で作成）
- ガードスクリプト: `.claude/scripts/gd_guard.py`

## 権限等級

- 本スキルの変更: **SE 級**（`.claude/skills/` への変更）
- ガードスクリプト変更: **SE 級**
