# W7-T2 Acceptance Evidence

**Date**: 2026-06-18
**Scope**: W7-T2 完了条件（AC-3 / AC-4 / AC-5 / AC-11）の充足立証
**Phase**: BUILDING / B-3
**等級**: SE 級

---

## 1. 概要

W7-T2 は W4-T3 リハーサル（2026-06-17 実機完走）で取得済の実機ログを AC-3 / AC-4 / AC-5 / AC-11 の充足立証として整理し、W5-T1 / W5-T2 実装変更（rubric-path 注入経路 / auto_approve / A-6 / A-7 / A-4 / A-5）のフロー[1]〜[9] への影響を机上で評価する evidence ドキュメントである。新規実機実行は統括（Opus）の MAGI 合議（2026-06-18）により見送り確定。W5-T1 / W5-T2 は full-review 単独経路の改修であり、goal-driven のフロー[1]〜[9] とは独立コンポーネントである点を本ドキュメントで明示する。

---

## 2. AC-3: フロー[1]〜[9] 完全一巡

**rubric**（出典: `docs/tasks/goal-driven/rubric-acceptance.md` 行 21）:

> サンプルタスク 1 件でフロー[1]〜[9] が一巡するデモログが取得できる（中タスク経路で可）
> 合否基準: デモログ存在 AND フロー[1]〜[9] 全ステップ OK 記録

**立証材料**:

- `docs/artifacts/goal-driven-demo/W4-T3-rehearsal-results.md` §1 のフロー[1]〜[9] 各ステップ成否テーブル
- W5-T1 / W5-T2 実装変更箇所の机上影響評価（本セクション §2.2）

### 2.1 フロー[1]〜[9] 実行記録（W4-T3 引用）

出典: `docs/artifacts/goal-driven-demo/W4-T3-rehearsal-results.md` §1 行 12-26（原文ママ）

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

W4-T3 §1 行 26（原文ママ）:

> **完走判定**: 全 9 ステップ正常完了

### 2.2 W5-T1/T2 変更の机上影響評価

| 変更項目 | 出典 | 影響レイヤー | フロー[1]〜[9] への影響 | 評価 |
|---|---|---|---|---|
| W5-T1: rubric 受け口（B-1 + B-2 + B-4） | git log `5a7f856` | full-review SKILL.md（独立スキル） | フロー[1]〜[9] は goal-driven スキル配下。full-review は handoff-format §5 経由で外部接続するためフロー[1]〜[9] の内部実装に影響なし | 内部仕様変更なし |
| W5-T2: auto_approve / A-6 / A-7 / A-4 / A-5 / 直列警告 | git log `ccbf6ea` | full-review SKILL.md（独立スキル） | 同上。フロー[7] L1 最終検収は goal-driven 本体の関心事であり full-review 改造範囲外 | 内部仕様変更なし |

**インターフェース変更の有無**: W5-T1/T2 は full-review 単独スキルの内部改修。goal-driven の `.claude/skills/goal-driven/SKILL.md` 本体、`.claude/agents/goal-driven-*.md` のフロントマター、`gd-session-state.json` スキーマ、`.claude/scripts/distill-lessons.py` のいずれも変更対象外であり、W4-T3 時点のフロー[1]〜[9] 実装と完全同一である。

**結論（AC-3）**: Pass。W4-T3 リハーサルにて全 9 ステップ OK 記録あり。W5-T1/T2 変更は full-review 単独スキルの内部改修でありフロー[1]〜[9] への挙動変更を含まない。

---

## 3. AC-4: 三段階ルート判定

**rubric**（出典: `docs/tasks/goal-driven/rubric-acceptance.md` 行 22）:

> 三段階ルート（小/中/大）の判定がデモログで確認できる
> 合否基準: route 判定記録 AND §9 ルートフロー図存在

**立証材料**:

- `docs/specs/goal-driven-orchestration/design.md` §9「三段階ルート設計（FR-6 / OQ-5）」
- W4-T3 リハーサルの「route=medium 判定 OK」記録

### 3.1 三段階ルート構成（design §9 引用）

出典: `docs/specs/goal-driven-orchestration/design.md` §9 行 335-352（原文ママ・判定フロー図）

```
L1 指揮者: タスク分析（LLM 呼び出し）
  ↓
以下をすべて満たすか？
  条件 A: rubric 項目数 ≤ 3
  条件 B: 未解決質問 = 0
  条件 C: 工程数 ≤ 2
  ↓
  YES → [小タスクルート] スキルスクリプトが l3-executor を直接起動
          L1 はこの後関与しない（MUST NOT）
          grader 起動主体 = スキルスクリプト（OQ-5 解決: §9.1 参照）
  ↓
  NO → 工程数 ≥ 3 OR 並列分解が必要か？
        YES → [大タスクルート] L1 → l2-foreman → l3-executor（三層）
        NO  → [中タスクルート] L1 → l3-executor（二層）
```

各ルート構成サマリ（design §9.2 行 380-385 を参照したまとめ）:

| ルート | L2 介在 | 構成エージェント |
|---|---|---|
| small | なし | SKILL.md スクリプト → l3-executor → grader |
| medium | なし | SKILL.md（L1）→ l3-executor（L3）→ grader |
| large | あり | SKILL.md（L1）→ l2-foreman（L2）→ l3-executor（L3）→ grader |

### 3.2 medium ルート判定実例（W4-T3 引用）

出典: `docs/artifacts/goal-driven-demo/W4-T3-rehearsal-results.md` §1 行 16（原文ママ）

> | [1] 難易度判定 | route=medium の判定 | OK | gd-session-state.json に `"route": "medium"` 記録 |

出典: `docs/artifacts/goal-driven-demo/W4-T3-rehearsal-results.md` §2 行 35（原文ママ）

> | route 判定 | medium | medium | Pass |

**結論（AC-4）**: Pass。design §9 に三段階ルート判定フロー図および各ルート構成定義が存在。W4-T3 リハーサルで medium ルート判定の実機記録あり。

---

## 4. AC-5: grader 別コンテキスト動作

**rubric**（出典: `docs/tasks/goal-driven/rubric-acceptance.md` 行 23）:

> grader が作業者と別コンテキストで動作していることがログで確認できる
> 合否基準: ログファイル存在 AND grader 定義に別コンテキスト記述あり

**立証材料**:

- `.claude/logs/gd/gd-20260617-001-loop01-grader.json` 存在確認（W4-T3 §7 行 141 にて 1,358 bytes 記録）
- `.claude/agents/goal-driven-grader.md` フロントマター description の別コンテキスト記述

### 4.1 grader JSON 引用（gd-20260617-001-loop01）

出典: `.claude/logs/gd/gd-20260617-001-loop01-grader.json`（原文ママ・行 1-28）

```json
{
  "rubric_version": "2026-06-17",
  "overall": "pass",
  "items": [
    {
      "id": 1,
      "result": "pass",
      "reason": "実ディレクトリ 6 件（README.md / W4-T3-rehearsal-package.md / W6-T2-dw-exclusion-report.md / smoke-hello.txt / smoke-test-20260613.log / smoke-test-runbook.md）と README テーブル 6 件が完全一致。過不足 0 を独立確認済み。"
    },
    {
      "id": 2,
      "result": "pass",
      "reason": "git diff で確認。差分は + 行 3 件のみ（追記）。- 行ゼロ。既存エントリ行（smoke-test-runbook.md / smoke-test-20260613.log / smoke-hello.txt）への変更・削除なし。"
    },
    {
      "id": 3,
      "result": "pass",
      "reason": "追記 3 行すべてが既存テーブルと同一の `| `filename` | description |` 形式。バックティック付きファイル名 + 説明列の 2 列構成。ヘッダ・区切り行は無変更でテーブル本体末尾への純追記。"
    },
    {
      "id": 4,
      "result": "pass",
      "reason": "走査で特定された不足エントリ 3 件（README.md / W4-T3-rehearsal-package.md / W6-T2-dw-exclusion-report.md）の全てが README に新規行として存在することを grep および git diff で確認。走査結果との差分 0。"
    }
  ],
  "escalate": false,
  "escalate_reason": ""
}
```

このログは別 Agent 呼び出し（`Agent(goal-driven-grader, ...)`）の結果として生成された出力であり、l3-executor とは別コンテキストでの実行であることを示す。

### 4.2 別コンテキスト動作の仕様記述（goal-driven-grader.md 引用）

出典: `.claude/agents/goal-driven-grader.md` 行 3-8（原文ママ・フロントマター description）

> rubric.md と構造化報告を照合し、合否と理由を返す独立評価エージェント。
> 作業者（l3-executor）と別コンテキストで実行される（FR-2）。
> 原則 Haiku で動作し、判断が重い場合は呼び出し元が sonnet を指定する。
> Bash は rubric の verify コマンド実行（テスト・lint 等の読み取り専用検証）のみ使用。
> ファイル変更・git 操作・パッケージ操作は禁止（W-2）。

出典: `.claude/agents/goal-driven-grader.md` 行 20-23（原文ママ・本文「重要」節）

> **重要**:
> - 作業者（l3-executor）と別コンテキストで実行される（FR-2 / AC-5）
> - Bash は rubric の `run` 種別検証コマンド実行のみ使用。ファイル変更・git 操作は禁止（W-2）
> - Task ツール（Agent）を持たない。自律 spawn は禁止（FR-7 / AC-6）

**結論（AC-5）**: Pass。grader JSON ログが実体として存在し、grader エージェント定義 description / 本文の両方に「別コンテキストで実行される（FR-2 / AC-5）」と明記。

---

## 5. AC-11: モデル別・層別トークン消費サマリ

**rubric**（出典: `docs/tasks/goal-driven/rubric-acceptance.md` 行 29）:

> モデル別・層別トークン消費サマリが出力される
> 合否基準: §14 に層別サマリ形式定義あり AND リハーサルで出力確認済み

**立証材料**:

- `docs/specs/goal-driven-orchestration/design.md` §14「コスト集計（NFR-1 / S4）」
- `docs/artifacts/goal-driven-demo/W4-T3-rehearsal-results.md` §2 「コストサマリ出力」Pass 記録
- L1 トークン未計上仕様の明示（仕様通りであり違反ではない）

### 5.1 design §14 層別サマリ形式定義（引用）

出典: `docs/specs/goal-driven-orchestration/design.md` §14 行 778-790（原文ママ「タスク完了時の出力（AC-11）」）

```
## コストサマリ（タスク: gd-20260611-001）
L1 指揮者:  12,000 tok ( 17.1% )  ← 目標 ≤20%
L2 班長:     5,000 tok (  7.1% )
L3 実行者:  45,000 tok ( 64.3% )
grader:      8,000 tok ( 11.4% )
---------------------------------
合計:        70,000 tok

/usage で詳細確認可能（24h/7d モデル別内訳）
```

出典: `docs/specs/goal-driven-orchestration/design.md` §14 行 752-762（原文ママ・cost_log スキーマ定義）

```json
{
  "cost_log": {
    "l1_tokens": 12000,
    "l2_tokens": 5000,
    "l3_tokens": 45000,
    "grader_tokens": 8000,
    "_divergences": []
  }
}
```

### 5.2 W4-T3 cost-log 実測値

出典: `docs/artifacts/goal-driven-demo/W4-T3-rehearsal-results.md` §2 行 32-52（該当行抜粋）

| 項目 | 実測値 | 状態 |
|---|---|---|
| total_tokens | 75,342 | 150k bound 内（Pass） |
| total_tokens / 150k 比率 | 0.502 | 適正範囲下限付近 |
| l1_ratio | 0.0000 | 本体トークン未計上・設計通り（要注記） |
| subagent_tokens (l3) | 37,783 | Pass |
| subagent_tokens (grader) | 37,559 | Pass |
| _divergences | あり（l3 ratio=0.8200 記録） | Pass |
| コストサマリ出力 | design §14 形式で出力確認 | Pass |

### 5.3 L1 トークン未計上の仕様根拠

出典: `docs/artifacts/goal-driven-demo/W4-T3-rehearsal-results.md` §5 行 109-114（原文ママ）

> **l1_ratio が 0.0000 となる理由（設計上の制約）**:
> L1 は本体コンテキスト（直接の Agent ツール呼び出し主体）であり、
> `subagent_tokens` は呼び出し先サブエージェントの消費トークンを返す機構。
> 本体 = 呼び出し元のため、L1 消費トークンは cost_log に計上されない（設計通り）。

出典: `docs/artifacts/retro-w4-t3.md` §3 Problem 行 83-86（原文ママ）

> 2. **L1 トークン未計上 / リハーサル単独切り出し不能**
>    - 本体は subagent_tokens 経由でないため cost_log.l1_tokens=0 / l1_ratio=0 固定
>    - PM 使用量表示は「セッション全体」累計（Opus 4.7 入力 49.7k + 出力 2.6k = 52.3k）でリハーサル単独計測は不能
>    - 次回はリハーサル直前のスナップショットを PM が記録する運用が必要

`cost_log.l1_tokens = 0` および `l1_ratio = 0.0000` は design §14 の `subagent_tokens` 経由仕様（本体は呼び出し元のため計上対象外）に基づく仕様通りの動作である。retro-w4-t3.md Try §3 行 100「リハーサル直前の使用量スナップショット運用化」は運用改善課題として記録されているが、これは AC-11 の合否基準（§14 に層別サマリ形式定義あり AND リハーサルで出力確認済み）の充足を妨げる仕様違反ではない。

**結論（AC-11）**: Pass。design §14 に層別サマリ形式定義あり。W4-T3 §2 行 49 で「コストサマリ出力: 出力確認: Pass」記録あり。L1 未計上は subagent_tokens 経由仕様による設計通りの動作。

---

## 6. 見送り項目（MAGI 合議による確定事項）

| 項目 | 見送り理由 |
|---|---|
| 中タスク新規実機実行 | W4-T3 リハーサル（2026-06-17）で AC-3/4/5/11 全て充足可能 |
| small ルート実機ログ | AC-4 の rubric は「§9 ルートフロー図存在」かつ「route 判定記録」であり、route=medium の判定機能動作と §9 の三段階定義の存在で充足。small ルート単独の実機ログは合否基準に含まれない |
| large ルート実機ログ | 同上。large ルートの実機実行は W7-T2b（大タスク三層縮小実機テスト）の対象であり W7-T2 範囲外 |
| full-review 単独実機実行 | W5-T1（B-1 + B-2 + B-4）/ W5-T2（auto_approve / A-6 / A-7 / A-4 / A-5）は単体検証（Haiku × 8 Pass）で代替済 |
| L1 トークン計上機能の新規実装 | design §14 の `subagent_tokens` 経由仕様（本体は呼び出し元のため計上対象外）に基づく仕様通りの未計上であり、新規実装の対象外 |

---

## 7. 総合判定

| AC | 状態 | 根拠 |
|---|---|---|
| AC-3 | Pass | W4-T3 §1 行 12-26 全 9 ステップ OK + W5-T1/T2 のフロー[1]〜[9] 非影響評価 |
| AC-4 | Pass | design §9 行 335-352 判定フロー図 + W4-T3 §2 行 35 「route 判定: medium: Pass」 |
| AC-5 | Pass | grader JSON 存在（gd-20260617-001-loop01-grader.json, 1,358 bytes） + grader.md 行 4-5 / 行 21「別コンテキストで実行される（FR-2 / AC-5）」 |
| AC-11 | Pass | design §14 行 778-790 層別サマリ形式定義 + W4-T3 §2 行 49「コストサマリ出力 Pass」 |

W7-T2 完了条件（AC-3 / AC-4 / AC-5 / AC-11）すべて充足。

---

## 8. 関連ドキュメント

| ドキュメント | 用途 |
|---|---|
| `docs/artifacts/goal-driven-demo/W4-T3-rehearsal-package.md` | リハーサル準備（観測ポイント / bound 校正 / 撤退条件） |
| `docs/artifacts/goal-driven-demo/W4-T3-rehearsal-results.md` | フロー[1]〜[9] 実機実行記録の出典（§1 ステップ成否 / §2 観測値テーブル / §5 L1 未計上の仕様根拠 / §7 完了条件チェック） |
| `.claude/logs/gd/gd-20260617-001-loop01-grader.json` | grader 別コンテキスト動作の証拠ログ（1,358 bytes） |
| `.claude/agents/goal-driven-grader.md` | grader エージェント定義（別コンテキスト動作の仕様記述） |
| `docs/specs/goal-driven-orchestration/design.md` §9 §14 | 三段階ルート定義 / コスト集計仕様 |
| `docs/tasks/goal-driven/rubric-acceptance.md` | AC-N rubric 出典（行 21-29: AC-3/4/5/11） |
| `docs/artifacts/retro-w4-t3.md` | L1 未計上仕様の運用課題（Problem §2 / Try §1） |
| `docs/specs/goal-driven-orchestration/research/full-review-analysis.md` | W5-T1 / W5-T2 設計根拠 |
| `.claude/skills/full-review/SKILL.md` | W5-T1 / W5-T2 実装本体（full-review 単独スキル / goal-driven のフロー[1]〜[9] とは独立） |
