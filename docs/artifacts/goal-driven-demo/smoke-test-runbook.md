# W1-T3 スモークテスト実行手順書（PM 向け）

- 作成日: 2026-06-13
- 対応タスク: `docs/specs/goal-driven-orchestration/tasks.md` W1-T3
- 期限: **2026-06-22 必須**（無償期間終了前）

---

## 概要

本手順書は、L1=最上位モデルでフロー [1]→[2]→[4]→[5] の最小一周を実機実行し、
L1 の消費トークンを記録するためのものである。

スタブ定義を使用するため、L3 実行・grader 評価は固定応答を返す（実際の実装は行わない）。
目的は「L1 がフロー全体を通して動作すること」と「l1_tokens の記録が機能すること」の確認である。

---

## 前提確認（実行前チェック）

### 1. ハードキャップ設定の確認（NFR-0 MUST）

Settings > Usage でハードキャップが設定されていることを確認すること。
スキルはこの確認を代替できない。

### 2. 本セッションでスタブ定義が作成済みであること

以下の 2 ファイルが `.claude/agents/` に存在すること（本セッションで作成済み）:

- `.claude/agents/gd-smoke-l3-stub.md`
- `.claude/agents/gd-smoke-grader-stub.md`

**重要**: エージェントレジストリはセッション開始時のスナップショットである。
上記ファイルを作成したセッションとは**別の新しいセッション**でのみ、
これらのスタブ定義が解決・使用可能になる。

### 3. 排他ガードの確認

`autonomous-state.json` または `lam-loop-state.json` が存在しないことを確認すること。
存在する場合は goal-driven スキルは起動を拒否する（SKILL.md §0a）。

### 4. 既存テストのパス確認（任意）

```
python -m pytest .claude/hooks/tests/test_gd_smoke_stubs.py -v
```

---

## スモークタスクの選択

小タスクルート判定条件（以下をすべて満たすこと）:

| 条件 | 定義 |
|------|------|
| 条件 A | rubric 項目数 ≤ 3 |
| 条件 B | 未解決質問 = 0 |
| 条件 C | 工程数 ≤ 2 |

**推奨スモークタスク**:

```
docs/artifacts/goal-driven-demo/smoke-hello.txt に固定文字列 "smoke-test-ok" を書く
```

このタスクは:
- rubric 項目数 = 1（「ファイルに文字列が書かれていること」）
- 未解決質問 = 0（明確な完了条件）
- 工程数 = 1（ファイル書き込みのみ）

→ 小タスクルートに判定される（条件 A/B/C をすべて満たす）。

---

## 実行手順

### ステップ 1: 新しいセッションを開く

前述の通り、スタブ定義は新セッションでのみレジストリ解決される。
**本手順書で記載の準備が完了したセッションとは別の新しいセッション**で実行すること。

### ステップ 2: L3/grader をスタブに差し替える指示

`/goal-driven` を起動する前に、L1 に以下の指示を伝えること:

```
W1-T3 スモークテストを実施する。
L3 エージェントとして gd-smoke-l3-stub を使用し、
grader エージェントとして gd-smoke-grader-stub を使用すること。
実際の goal-driven-l3-executor と goal-driven-grader は使用しない。
```

### ステップ 3: スキルを起動する

```
/goal-driven docs/artifacts/goal-driven-demo/smoke-hello.txt に固定文字列 "smoke-test-ok" を書く
```

### ステップ 4: フロー確認ポイント

L1 が以下のフローを実行することを確認する:

| ステップ | 内容 | 確認事項 |
|---------|------|---------|
| [1] 難易度判定 | L1 がタスクを分析し「小タスク」と判定する | "小タスク" または "small" の出力 |
| [2] rubric 生成 | `.claude/rubric-tmp.md` に rubric が生成される | ファイルの存在確認 |
| [4] L3 スタブ実行 | `gd-smoke-l3-stub` が起動し固定 JSON を返す | 構造化報告 JSON の受け取り確認 |
| [5] grader スタブ実行 | `gd-smoke-grader-stub` が起動し `overall: "pass"` を返す | 合格判定の確認 |

**注記**: 小タスクルートでは [3] bound 設定を `gd_state.py --init` で初期化する。
W2-T2（`gd_state.py`）は実装済みのため、下記 ステップ 6 の手順で状態管理が可能。

### ステップ 5: ログ保存

実行ログを保存する:

```
docs/artifacts/goal-driven-demo/smoke-test-YYYYMMDD.log
```

例: `docs/artifacts/goal-driven-demo/smoke-test-20260613.log`

ログには以下を含めること:
- 実行開始・終了日時
- フロー [1]→[2]→[4]→[5] の各ステップの出力
- gd-smoke-l3-stub が返した構造化報告 JSON
- gd-smoke-grader-stub が返した grader 判定 JSON
- L1 の消費トークン数（l1_tokens の値）

### ステップ 6: gd-session-state.json への l1_tokens 記録

W2-T2（`gd_state.py`）は実装済みである。スキルが `--init` で状態ファイルを初期化し、
`--accumulate` でトークン累積を行う。スキルが自動呼び出しする想定だが、手動実行も可能:

```bash
# state 初期化（スキルが自動実行する場合はスキップ可）
python .claude/scripts/gd_state.py --init --task-id gd-smoke-YYYYMMDD-001 \
    --task-slug smoke-hello --route small

# L3 スタブ実行後のトークン累積（構造化報告 JSON の tokens_used 値を渡す）
python .claude/scripts/gd_state.py --accumulate <tokens_used の値>

# 完了ステータス更新
python .claude/scripts/gd_state.py --set-status completed
```

**`l1_tokens` フィールドについて**: `gd_state.py` が管理するのは `total_tokens`（全エージェント累積）であり、
`l1_tokens`（L1 指揮者単体の消費）は gd_state.py の管理対象外のフィールドである。
W1-T3 完了条件（AC-11）の「l1_tokens 記録」は、スキル実行後に Claude Code の使用量表示から
L1 分のトークン数を読み取り、`gd-session-state.json` に手動で追記する:

```json
{
  "task_id": "gd-smoke-YYYYMMDD-001",
  "task_slug": "smoke-hello",
  "route": "small",
  "l1_tokens": <Claude Code 使用量表示から読み取ったトークン数>,
  "status": "completed"
}
```

### ステップ 7: README への記録

`docs/artifacts/goal-driven-demo/README.md` に以下を記載する（6/22 期限確認用）:

```markdown
## W1-T3 スモークテスト結果

| 項目 | 値 |
|------|-----|
| 実施日時 | YYYY-MM-DD HH:MM |
| l1_tokens | <値> |
| フロー完走 | [1]→[2]→[4]→[5] |
| 結果 | 合格 |
```

---

## 後片付け（テスト完了後）

### スタブ定義の削除（PM の手で実施）

`rm` コマンドは禁止されているため、PM が手動でファイルエクスプローラーまたは
他の手段でスタブファイルを削除すること:

- `.claude/agents/gd-smoke-l3-stub.md`
- `.claude/agents/gd-smoke-grader-stub.md`

### rubric-tmp.md の削除

小タスクルートの後処理スクリプトが自動削除するはず（SKILL.md [9]）。
残留している場合はスクリプトで削除:

```bash
python .claude/scripts/gd_guard.py --cleanup-rubric-tmp
```

### gd-session-state.json の確認

`status` が `"completed"` になっていることを確認する。
残留している場合は W1-T3 完了後に PM が削除を判断すること。

---

## 消費トークン記録ログ（実施後に記入）

```
実施日時: ____________
l1_tokens: ____________
フロー完走: [1]→[2]→[4]→[5]  合格 / 不合格
備考: ____________
```

---

## トラブルシューティング

### スタブ定義が解決されない場合

原因: 同一セッション内でのエージェントレジストリは起動時スナップショットのため、
本セッションで作成したスタブ定義は反映されない。

対処: 新しいセッションを開いて再度実行すること。

### 排他ガードでブロックされる場合

`autonomous-state.json` または `lam-loop-state.json` が残留している。
PM が確認・削除を判断すること（自動削除禁止）。

### gd_state.py でエラーが発生する場合

W2-T2（`gd_state.py`）と W2-T3（Stop hook B-3 節）はいずれも実装済みである。
`gd-session-state.json` が存在しない状態で `--accumulate` や `--check-spawn-budget` を呼ぶと
`FileNotFoundError` が発生する。その場合はまず `--init` で初期化してから再実行すること:

```bash
python .claude/scripts/gd_state.py --init --task-id gd-smoke-YYYYMMDD-001 \
    --task-slug smoke-hello --route small
```

---

## 参照

- タスク定義: `docs/specs/goal-driven-orchestration/tasks.md` W1-T3
- 設計書: `docs/specs/goal-driven-orchestration/design.md` §7（構造化報告スキーマ）/ §11（grader 出力スキーマ）
- スキル定義: `.claude/skills/goal-driven/SKILL.md`（フロー [1]→[9]）
- スタブ定義: `.claude/agents/gd-smoke-l3-stub.md` / `.claude/agents/gd-smoke-grader-stub.md`
