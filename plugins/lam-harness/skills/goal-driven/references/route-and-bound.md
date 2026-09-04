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
- `maxTurns: 20`（`goal-driven-l3-executor.md` フロントマター）で L3 のターン打ち切り
  → **2026-08-21 に実装**。旧記述の `max_turns`（snake_case）は subagent frontmatter の有効キーではなく
  **一度も効いていなかった**（2026-08-20 発覚）。正しいキーは **`maxTurns`（camelCase）**であり、
  `.claude/agents/*.md` で有効であることを対照実験で確認済み
  （`maxTurns: 2` の agent は 2 ターンで打ち切られ、無指定の対照は 10 ターン完走
  / 記録: `docs/artifacts/maxturns-probe-2026-08-21.md`）。
  **値は 20 固定でルート別ではない**。frontmatter は静的であり L3 定義は 1 ファイルのため、
  設計値（小:10 / 中:20 / 大:15）の最大値をバックストップとして採った
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

