---
name: b3-goal-driven-design-context
description: B-3 ゴール駆動オーケストレーション設計書の主要決定事項と未確認事項の記録
metadata:
  type: project
---

B-3 goal-driven スキル設計書 v0.2.0 を 2026-06-11 に更新（spec-critic C-1〜C-4/W-1〜W-7/I-1〜I-4/P-1〜P-4 対応）。
出力先: `docs/specs/goal-driven-orchestration/design.md`

**Why:** BUILDING フェーズの自己修正ループ機構の欠如（コスト非効率・自走性欠如）を解消するため。

**How to apply:** 次回セッションで実装タスクに入る際は設計書の §8 検証タスク（OQ-1 の /goal サブエージェント内動作実測）を先に実施すること。

## 主要設計決定

- OQ-2 選定: (c) スキル + 自前スクリプト（保存済みワークフローは mid-run 入力不可・トークン消費大の制約で却下）
- OQ-5 解決: 小タスクの grader 起動主体 = スキルスクリプト（L1 コンテキスト内）。l3-executor からの自律起動は FR-7 で禁止
- 内側ループ Plan A（/goal）/ Plan B（自前ループ）の二案構えで OQ-1 を解決
- Stop hook の bound 超過: exit 0 + additionalContext（block ではない）。第二防衛線位置づけ
- 第一防衛線: スキルスクリプトが spawn 前に残予算チェック（subagent-stop.py 新規フックは不要）
- /goal 条件文: ターン数打ち切りのみ（`or stop after N turns`）。トークン閾値は未確認（要裏取り）
- distill-lessons.py の自動書き込み先は agent-memory のみ。docs/artifacts/knowledge/ への昇格は人間（/retro）のみ

## 未確認事項（実装着手前に実測が必要）

- /goal のサブエージェント内動作（OQ-1）+ トークン条件書式: research/oq1-goal-subagent-test.md に結果を記録してから Plan A/B を確定
- ネストサブエージェントのデフォルト有効性（ファクトシート §2）
- 深さ上限 5 の確定性（外部化で対処済み）
- Agent ツール結果の subagent_tokens 安定性（多層・並列時は未検証）

## PM 承認が必要な作業（PM級）

- lam-stop-hook.py への B-3 節追加（競合排除条件設計を PM に提示してから着手）
- full-review 改造着手（research/full-review-analysis.md 承認後）
