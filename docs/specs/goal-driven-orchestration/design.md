# 設計書: ゴール駆動オーケストレーション・スキル

- バージョン: 0.3.1
- 作成日: 2026-06-11
- 改訂日: 2026-06-12（W0-T1 実測結果の反映: §8 Plan B 確定・§18 D1 解決。設計判断の変更なし。PM 承認済み）
- 改訂履歴: 2026-06-12 v0.3.0（2巡目レビュー R2-C-1〜4 / R2-W-1〜5 / R2-I-1〜2 ほか対応・リファクタリング）/ 2026-06-11 v0.2.0（spec-critic レビュー C-1〜C-4 / W-1〜W-7 / I-1〜I-4 / P-1〜P-4 対応）
- ステータス: Draft（PM 承認待ち）
- 参照要件: `docs/specs/goal-driven-orchestration/requirements.md` v1.2.0
- 参照ファクト: `docs/specs/goal-driven-orchestration/research/platform-facts-2026-06-11.md`

---

## 目次

1. [Problem Statement](#1-problem-statement)
2. [Non-Goals](#2-non-goals)
3. [Alternatives Considered（OQ-2: 決定的骨格の実装方式選定）](#3-alternatives-considered)
4. [Success Criteria](#4-success-criteria)
5. [システム構成概要](#5-システム構成概要)
6. [rubric ファイル形式（FR-1）](#6-rubric-ファイル形式)
7. [構造化報告スキーマ（FR-3）](#7-構造化報告スキーマ)
8. [内側ループ: 二案構え（OQ-1 / FR-3 / AC-12）](#8-内側ループ二案構え)
9. [三段階ルート設計（FR-6 / OQ-5）](#9-三段階ルート設計)
10. [bound 機構（FR-4）](#10-bound-機構)
11. [エージェント定義群（FR-7 / R7）](#11-エージェント定義群)
    - [11b. NFR-6: ネスト失敗フォールバック（W-7）](#11b-nfr-6-ネスト失敗フォールバック)
12. [Dynamic Workflows 排除（FR-8）](#12-dynamic-workflows-排除)
13. [メモリ蒸留（FR-5）](#13-メモリ蒸留)
14. [コスト集計（NFR-1）](#14-コスト集計)
15. [full-review 連携（FR-9）](#15-full-review-連携)
16. [lam-orchestrate 受け渡し形式（FR-10）](#16-lam-orchestrate-受け渡し形式)
17. [FR / NFR トレーサビリティ表](#17-fr--nfr-トレーサビリティ表)
18. [Open Questions と検証タスク](#18-open-questions-と検証タスク)
19. [前提と既知の不確実性](#19-前提と既知の不確実性)
20. [NFR-8: 本スキル成果物の検収設計](#20-nfr-8-本スキル成果物の検収設計)

---

## レビュー ID 凡例

本文中の `C-n` / `W-n` / `I-n` / `P-n` は 1巡目 spec-critic レビュー（2026-06-11）の指摘 ID であり、`R2-` プレフィックスは 2巡目レビュー（2026-06-12）の指摘 ID である。これらは設計判断を特定の結論に確定させた根拠として本文に残置する。

---

## 1. Problem Statement

要件書 §1 を継承する。設計上の補足として以下を記す。

現行 `lam-orchestrate` は PLANNING 成果物の並列処理（Wave 方式）に最適化されており、
BUILDING フェーズでの「実行→評価→修正」の自己修正ループを持たない。
また `/full-review` は完成後の品質監査ツールとして機能するが、実装ループ内でのインライン評価
には重すぎる（コスト・時間の両面で）。

本スキルはこのギャップを埋めるもので、`lam-orchestrate`（PLANNING 出力）→ 本スキル（BUILDING
自己修正ループ）→ `full-review`（最終検収）という直列パイプラインに位置する。

---

## 2. Non-Goals

要件書 §3 を継承する。設計上の追加非スコープ:

- SKILL.md 以外の既存スキル（`/full-review`, `lam-orchestrate`, `/magi`）の内部書き換え
- Python / Node.js 等の外部ランタイムへの依存（スクリプトは bash + python3 stdlib のみ）
- L1 モデルの固定化（設定値で差し替え可能に保つ）

---

## 3. Alternatives Considered

### OQ-2: 決定的骨格の実装方式選定（AC-13）

決定的処理（フロー遷移・三段階ルート分岐・エスカレーション）の実装方式を以下の 3 案で比較する。

| 評価軸 | (a) 保存済みワークフロー | (b) hooks | (c) スキル + 自前スクリプト |
|--------|----------------------|-----------|--------------------------|
| mid-run 入力可否 | **不可**（確認済み制約） | 一部可（Stop hook で block） | **可** |
| トークン消費 | **大**（"meaningfully more" 公式注記） | 少（hook は非モデル実行） | 最小（LLM 呼び出しは判断箇所のみ） |
| LLM 非呼び出し部の実装 | 不可（全処理がモデル実行） | **可**（スクリプトで決定的に） | **可** |
| プラットフォーム依存度 | 高（workflow 書式に依存） | 中（hook イベントに依存） | **低**（スキル内スクリプトが主体） |
| rubric 照合・grader 起動 | 不可（スクリプト FS 直接アクセス禁止） | 可（PostToolUse/Stop） | **可** |
| bound 超過エスカレーション | 不可（mid-run 入力不可） | 可（Stop hook block → 人間介入） | **可** |
| 設計原則§3b 適合 | **不適合**（全処理がモデル実行） | 部分適合 | **適合** |

**選定: (c) スキル + 自前スクリプト**

理由:
1. 保存済みワークフローは mid-run 入力不可・トークン消費大・スクリプト FS アクセス禁止の三重制約があり、
   本スキルの bound エスカレーション・grader 起動・rubric 照合の要件を満たせない（FR-4, FR-2, FR-1）
2. hooks 単体は決定的フロー制御に使えるが、三段階ルート分岐・rubric 生成・モデル選択など
   LLM 判断が必要な箇所との統合には SKILL.md 内スクリプトとの組み合わせが必要
3. スキル + スクリプト方式は LLM 呼び出しを判断箇所（難易度判定・rubric 生成・最終検収）のみに
   限定でき、設計原則 §3b に最も適合する
4. hooks は補完的に使用する（SubagentStop, TaskCompleted でトークン集計・エスカレーション判定）

**hooks の補完的役割（本設計での使用箇所）**:
- Stop hook: グローバル bound のバックストップ（第二防衛線）。bound 超過時は **exit 0（通常停止）+
  `hookSpecificOutput.additionalContext` でエスカレーション理由を注入**する（`block` ではない）
- （subagent-stop.py 新規フックは不要: §10 C-2 参照）

---

## 4. Success Criteria

要件書 AC-1〜AC-15 を満たすことを成功基準とする。ここでは設計が保証する対応を記す。

| AC | 設計での対応 |
|----|------------|
| AC-1 | `.claude/skills/goal-driven/SKILL.md` として配置。呼び出しは `/goal-driven <task>` |
| AC-2 | FR-1〜FR-10 は §5〜§16 の各設計セクションで具現化 |
| AC-3 | デモログ取得手順を SKILL.md に記載（中タスク経路） |
| AC-4 | §9 三段階ルートのフロー図で確認可能 |
| AC-5 | grader は独立エージェント（別コンテキスト）として起動（§8, §11） |
| AC-6 | L3 / grader フロントマターに `Agent` を含めない（§11） |
| AC-7 | /goal 使用箇所の条件文テンプレートに打ち切り句を必須化（§8） |
| AC-8 | グローバル bound テスト（I-1）: `gd-session-state.json` の `total_tokens` を閾値超の値に設定した状態でスキルスクリプトの spawn-time チェック関数を単体テスト（pytest）。期待値: エスカレーション経路に到達しスポーン中断 |
| AC-9 | エスカレーション E2E テスト（I-1）: 「常に fail を返す grader スタブ」 + `loop_count=max_loop_count` の状態ファイルを用意し、スキルスクリプトがエスカレーション報告を出力することを確認。grader スタブは `goal-driven-grader` フロントマターと同一インターフェースのテスト用 fixture |
| AC-10 | §12 の設定文書化と `disableWorkflows: true` 推奨 |
| AC-11 | §14 コスト集計スキーマで出力 |
| AC-12 | §8 で Plan A / Plan B と検証手順を記載 |
| AC-13 | §3 比較表と選定理由を記載 |
| AC-14 | FR-9: research/full-review-analysis.md（Draft 完成・PM 承認待ち）で対応。本設計書は §15 で参照のみ |
| AC-15 | §16 で lam-orchestrate 受け渡し形式を定義 |

---

## 5. システム構成概要

### コンポーネント一覧

| コンポーネント | 種別 | 配置パス | 役割 |
|--------------|------|---------|------|
| goal-driven スキル | スキル | `.claude/skills/goal-driven/SKILL.md` | エントリポイント・ルート分岐・rubric 生成指示・トークン集計（第一防衛線） |
| l2-foreman | エージェント | `.claude/agents/goal-driven-l2-foreman.md` | 大タスクの工程分解・L3 分配 |
| l3-executor | エージェント | `.claude/agents/goal-driven-l3-executor.md` | 実装・テスト実行（Task ツールなし） |
| grader | エージェント | `.claude/agents/goal-driven-grader.md` | rubric 照合・合否判定 |
| bound-monitor | Stop hook 拡張（PM級） | `.claude/hooks/lam-stop-hook.py` 内の B-3 節 | グローバル bound バックストップ（第二防衛線） |
| lessons-writer | スクリプト（SE級） | `.claude/scripts/distill-lessons.py`（新規） | メモリ蒸留（FR-5） |
| config.md | 設定ガイド（PM級） | `docs/specs/goal-driven-orchestration/config.md`（新規） | DW 無効化・effort 設定等の運用ガイド（I-2） |

### フロー図（全体）

```
人間: /goal-driven <task>
  ↓
[SKILL.md] L1 指揮者コンテキスト起動
  ↓ LLM 呼び出し: 難易度判定
  ├─ 小 → [スクリプト] L3 直行パス（§9）
  ├─ 中 → [スクリプト] L1→L3 二層パス
  └─ 大 → [スクリプト] L1→L2→L3 三層パス
            ↓ Agent ツールで l2-foreman 起動
            ↓ l2-foreman が l3-executor を分配
  ↓
[L3 実行ループ] Plan A or Plan B（§8）
  ↓ 構造化報告（§7）
  ↓
[grader エージェント] rubric.md 照合
  ├─ 不合格 → L3 差し戻し（bound チェック後）
  └─ 合格 ↓
  ↓
[L1 最終検収] LLM 呼び出し（小タスクルートではスキップ: §9.1）
  ↓
[distill-lessons.py] メモリ蒸留（§13）
  ↓
[full-review] 納品前検証（§15）
  ↓
人間: 受領
```

### プラットフォーム依存の分離層

```
[LAM 固有層]  rubric 生成 / メモリ蒸留 / コスト集計 / full-review 連携
              ↑ 疎結合インターフェース（rubric.md, cost-log.json）
[プラットフォーム層] /goal コマンド / Agent ツール / hooks / エージェント定義
```

§3b 設計原則に従い、LAM 固有層はプラットフォーム層に直接依存しない。
プラットフォーム側の仕様変更時は疎結合インターフェースの橋渡し部分のみ修正する。

---

## 6. rubric ファイル形式（FR-1）

### 配置パス

```
docs/tasks/<task-slug>/rubric.md   # 中タスク・大タスク（MUST）
.claude/rubric-tmp.md              # 小タスク暫定（実行後に削除）
```

小タスクの `.claude/rubric-tmp.md` は L1（rubric 生成の LLM 呼び出し）が生成し、タスク終了時（合格・エスカレーションを問わず）にスキルスクリプトが削除する。

### スキーマ

```markdown
# rubric: <タスク名>

- 生成日: YYYY-MM-DD
- タスク種別: 小 / 中 / 大
- global_bound: tokens=200000 OR time=3600s
  # OR セマンティクス: いずれか早く到達した方で打ち切り（I-4）

## 検証項目

| # | チェック項目 | 検証方法 | 検証コマンド / grader 指示 | 合否基準 |
|---|------------|---------|--------------------------|--------|
| 1 | 全テスト通過 | 実行コマンド | `pytest --tb=short` | exit 0 |
| 2 | FR-1 仕様フィールド名一致 | grader 判定 | rubric 項目 2 を読み `src/` と照合せよ | 完全一致 |
| 3 | ドキュメント更新済み | grader 判定 | docs/specs/ の更新日が実装日以降であること | 日付確認 |

## 差し戻しルール

- 連続 N 回不合格でエスカレーション（N = `max_loop_count`、`gd-session-state.json` のフィールド・初期値 3・NFR-5 で外部化可能）
- 同一項目 2 回連続不合格 → L1 に報告（再 rubric または工程分割を検討）
```

### 検証方法の種別

| 種別 | 内容 | grader への指示 |
|------|------|---------------|
| `run` | コマンド実行・exit code で判定 | grader は Bash 実行結果を確認 |
| `grader` | LLM が rubric 項目と成果物を照合 | grader エージェントがファイルを読んで判定 |
| `human` | 人間判断が必要（エスカレーション） | 自動ループを停止し PM に提示 |

**P-4: auto-compact 後の rubric 参照可能性（要件書 §0 の前提保証）**:
rubric.md は `docs/tasks/<task-slug>/rubric.md` に共有ファイルとして配置されるため、
auto-compact によるコンテキスト圧縮後も全層からファイルシステム経由で参照可能である。
コンテキスト内の rubric 内容が圧縮された場合、各エージェントは起動時に rubric.md を Read ツールで
再読み込みするよう SKILL.md のプロンプトに明記する。

---

## 7. 構造化報告スキーマ（FR-3）

L3 → L2/L1 への報告は以下の JSON スキーマに従う。自由文の直接転送は禁止（MUST NOT）。

```json
{
  "$schema": "goal-driven-report/v1",
  "task_id": "string（例: gd-20260611-001）",
  "rubric_version": "string（rubric.md の生成日 YYYY-MM-DD）",
  "changes": [
    {"file": "src/foo.py", "summary": "add validate() function"}
  ],
  "test_results": {
    "command": "pytest --tb=short",
    "passed": 12,
    "failed": 0,
    "skipped": 1,
    "exit_code": 0
  },
  "unresolved": [
    "NFR-5 の設定外部化: config.yaml のキー名が未定"
  ],
  "next_suggestion": "string（次ターンで試みる改善案。空文字列可）",
  "tokens_used": 8500
}
```

**フィールド定義**:
- `changes`: 変更ファイルの要約のみ。diff 全文を渡してはならない（MUST NOT）
- `unresolved`: rubric の未達項目または技術的懸念のみ列挙
- `next_suggestion`: bound 到達時は `"ESCALATE"` を設定し、ループを終了する
- `tokens_used`: L3 実行ループ内の消費トークン（Agent ツール結果から取得）

---

## 8. 内側ループ二案構え（OQ-1 / FR-3 / AC-12）

### 背景

`/goal` のサブエージェント内動作は未確認（ファクトシート §1）。
v2.1.154 の changelog 記述（evaluator がサブエージェント実行中に誤 firing）は
メインセッション専用設計の可能性を示唆する。

### Plan A: /goal が L3 内で使える場合

```
l3-executor 起動
  └─ /goal <rubric の run 項目を条件文に変換> or stop after <N> turns
       └─ Haiku evaluator が各ターン後に条件評価（/goal ネイティブ機能）
  ↓ 条件達成 or N ターン超過
  └─ 構造化報告（§7）を出力して終了
```

条件文テンプレート（FR-4 打ち切り句必須 / C-4 対応: ターン数打ち切りのみ）:
```
/goal all rubric items pass (see docs/tasks/<slug>/rubric.md)
      or stop after <N> turns
```

`<N>` には §9.2 の L3 max_turns（小:10 / 中:20 / 大:15）をルートに応じて代入する。

**C-4 注記**: トークン閾値条件（`or stop if total_tokens > N`）は確認済みの `/goal` 書式になく、テンプレートから削除済み。詳細は §10 の C-4 対応を参照。検証は §18 D1 に帰属。

### Plan B: /goal が使えない場合（フォールバック）

```
SKILL.md スクリプト（L1 コンテキスト内）が制御ループを担う:

while bound.remaining > 0:
  1. Agent ツール → l3-executor 起動（1回分の実装）
  2. Agent ツール → grader 起動（rubric.md を渡す）
  3. grader 結果を JSON で受け取る
  4. 合格 → ループ終了
  5. 不合格 → l3-executor に差し戻し報告を注入して 1 へ
  6. bound 超過 → エスカレーション
```

この方式でも R2（独立 grader・別コンテキスト）・R4（bound）は満たされる。
grader は毎回独立した Agent 呼び出しで起動するため、L3 コンテキストと分離される。

**grader 呼び出し失敗時の扱い**: grader がエラーまたは不正 JSON を返した場合、1 回のみ再試行してよい（MAY）。再試行も失敗した場合はエスカレーションする（MUST）。grader 失敗を合格として扱ってはならない（MUST NOT）。

### 検証タスク（実装着手前に実施）

```
手順:
1. L3 相当の minimalist エージェント定義を作成（tools: Bash, Read のみ）
2. そのエージェント内から /goal コマンドを発行
3. Haiku evaluator が発火するかログで確認
4. 結果を research/oq1-goal-subagent-test.md に記録
5. 結果に応じて Plan A / Plan B を確定し、本設計書の §8 を更新する（`docs/specs/` 配下のため **PM級**・PM 承認ゲートを経ること）
```

**NFR-2 対応**: Plan B（自前 grader ループ）を最終採用した場合、その理由（/goal を使用しない根拠＝検証結果）を本設計書 §8 と `research/oq1-goal-subagent-test.md` に記録する（MUST）。

**確定: Plan B**（2026-06-12 実測。/goal はサブエージェント内でスラッシュコマンドとして展開されず、evaluator も発火しない。検証手順と根拠は `research/oq1-goal-subagent-test.md` を参照）。NFR-2 例外条件（プラットフォームネイティブ機能が利用不能）に該当するため Plan B を採用する。W3 は W3-T2（Plan B）のみ実施する。

---

## 9. 三段階ルート設計（FR-6 / OQ-5）

### 判定フロー図

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

### 9.1 OQ-5 解決: 小タスクルートの grader 起動主体

FR-7 は末端エージェントの自律 spawn を禁止する。小タスクルートでは
l3-executor が grader を自律起動することは禁止（MUST NOT）。

**設計回答**: スキル本体（L1 コンテキストのスクリプト部）が grader を起動する。
小タスクルートでも L1 コンテキストは生きており、l3-executor の終了後に
スクリプトが grader を別 Agent 呼び出しとして起動する。L1 の LLM は
最終検収に関与しないが、スクリプト実行コンテキストとして機能する。

```
[小タスク: スクリプト制御]
SKILL.md スクリプト
  → Agent(l3-executor, prompt=task+rubric)
  ← 構造化報告 JSON
  → Agent(goal-driven-grader, prompt=report+rubric)
  ← grader 判定 JSON
  合格 → 終了
  不合格 + bound 残り → l3-executor に差し戻し
  不合格 + bound 切れ → エスカレーション
```

**小タスクルートの完了処理**: 小タスクルートでは L1 最終検収（LLM 呼び出し）をスキップし、grader 合格をもって完了とする（MUST）。`distill-lessons.py` は全ルート共通でスクリプトとして実行するが、小タスクでは L1 検収時の抽出に代えて grader 判定 JSON のみを入力とする。

### 9.2 各ルートの設定値

| パラメータ | 小タスク | 中タスク | 大タスク |
|-----------|--------|--------|--------|
| L3 max_turns | 10 | 20 | 15（工程ごと） |
| grader モデル | Haiku | Haiku | Haiku（判断重い場合 Sonnet） |
| global bound | tokens=50k | tokens=150k | tokens=400k |
| L2 介在 | なし | なし | あり |

**注記**: 数値はすべて初期値。`rubric.md` の `global_bound` フィールドで上書き可能（NFR-5）。

---

## 10. bound 機構（FR-4）

### 二段防衛線の設計（C-1/C-2 対応）

bound 超過を二段で検知する。第一防衛線がメインであり、Stop hook はバックストップ。

| 防衛線 | 主体 | 方式 |
|--------|------|------|
| **第一（主）** | スキルスクリプト（L1 コンテキスト） | 各 Agent 呼び出し後に usage を加算し、**次の spawn 前に残予算チェック**（spawn-time enforcement） |
| **第二（バックストップ）** | Stop hook B-3 節 | セッション状態ファイルを読み、bound 超過なら exit 0 + additionalContext 注入 |

この設計により subagent-stop.py 新規フック（cost-logger）は**不要**。
コンポーネント表（§5）から `cost-logger` を削除済み。

### 層別 bound（`global_bound` フィールドは OR 条件: いずれか早く到達した方で打ち切り）

| 層 | bound 種別 | 設定値（初期値・外部化可） | 超過時の動作 |
|----|-----------|------------------------|------------|
| L3 実行ループ | max_turns（フロントマター） | 小:10 / 中:20 / 大:15 | 構造化報告に `next_suggestion: "ESCALATE"` を設定 |
| /goal 条件文 | 打ち切り句（C-4 対応: ターン数のみ） | `or stop after N turns`（N は上表） | evaluator が打ち切り |
| グローバル | 総トークン OR 経過時間 | 小:50k/3600s, 中:150k/3600s, 大:400k/7200s | スクリプト（第一）or Stop hook（第二）でエスカレーション |

**C-4 対応**: `/goal` 条件文のトークン閾値（`stop if total_tokens > N`）は確認済み書式なし。
条件文テンプレートからトークン条件を削除し、**ターン数打ち切りのみ**に限定する。
トークンベース打ち切りの `/goal` 組み込みサポートは未確認（要裏取り）として §18 D1 検証タスクに追加。

### L3 サブ予算の割り当て（C-3 対応）

**課題**: Plan A（/goal 使用）ではグローバル bound が L3 コンテキスト内に直接届かない。

**設計回答**:
1. L3 spawn 時に**サブ予算を割り当て**: `maxTurns` フロントマター + 条件文の打ち切り句で L3 の実行量を有界化
2. L3 帰還時に `tokens_used`（構造化報告 §7）をグローバルから減算し、残予算を更新
3. 次の spawn 前に残予算チェック（第一防衛線）

**並列起動時の扱い**: L2 が複数の l3-executor を並列起動する場合、並列グループの各サブ予算の合計が残予算以下であることを spawn 前に確認する（MUST）。確認できない場合は順次起動に退避する。

**残余リスク（明示的文書化）**: L3 の 1 回分の実行がサブ予算を超過した場合、
その超過分はグローバル bound 超過として L3 帰還後に初めて検知される（最大 1 スパン遅れ）。
これは許容リスクとする。Stop hook（第二防衛線）が補完的に機能するが、
サブエージェント実行中の hook 発火は L3 帰還後になるため同様の遅延がある。

### セッション状態ファイル: `<project_root>/.claude/gd-session-state.json`

**P-3 対応**: パスは `cwd` 依存ではなく `get_project_root()` で解決したプロジェクトルート絶対パスを使用する（サブエージェント内 cwd 変動の既知リスク対応）。

```json
{
  "task_id": "gd-20260611-001",
  "task_slug": "example-task",
  "route": "medium",
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

### Stop hook B-3 節の設計（C-1 修正・PM級）

既存 `lam-stop-hook.py` の `main()` に、AUTONOMOUS / lam-loop の評価順序の後に B-3 節を追加する。
**競合排除**: gd-session-state.json は `autonomous-state.json` および `lam-loop-state.json` と**同時実行禁止**。
スキル起動時に他 state ファイルの存在を確認し、存在すれば起動を拒否する。
hook 側では他 2 つが不在（`auto_state is None` かつ `lam-loop-state.json` 未存在）の場合のみ B-3 節を評価する。

**残留時のリカバリ**: スキル起動時に `gd-session-state.json` が `status: "running"` のまま存在する場合（前回セッションの異常終了による残留）、自動削除はせず PM に提示し、明示承認後に削除して新規開始する（フェイルセーフ）。

```python
# B-3: goal-driven グローバル bound バックストップ（第二防衛線）
# 第一防衛線（スキルスクリプト）が失敗した場合のみここが発動する
gd_state_path = get_project_root() / ".claude" / "gd-session-state.json"
if gd_state_path.exists():
    try:
        gd_state = json.loads(gd_state_path.read_text(encoding="utf-8"))
        if gd_state.get("status") == "running":
            total_tokens = gd_state.get("total_tokens", 0)
            global_token_bound = gd_state.get("global_token_bound", 200000)
            elapsed_s = time.time() - gd_state.get("start_time", time.time())
            global_time_bound = gd_state.get("global_time_bound", 3600)
            if total_tokens >= global_token_bound or elapsed_s >= global_time_bound:
                # C-1修正: bound 超過 = 停止（exit 0）+ エスカレーション通知
                # block（継続強制）ではない
                reason = (
                    f"[goal-driven] global bound exceeded: "
                    f"tokens={total_tokens}/{global_token_bound}, "
                    f"time={elapsed_s:.0f}s/{global_time_bound}s. "
                    "Escalating to PM. Please check gd-session-state.json."
                )
                print(json.dumps({
                    "hookSpecificOutput": {"additionalContext": reason}
                }), flush=True)
                sys.exit(0)  # 通常停止（セッション終了を許可しエスカレーション）
    except Exception as e:
        _log(log_file, "WARN", f"gd bound check error: {e}")
        # バックストップ障害時はフェイルセーフで通過（Claude を止めない）
```

**フォールバック値 200,000 の意図**: `global_token_bound` 欠落は異常系（状態ファイルの手動編集・破損）であり、200,000 はその場合の最終上限である。ルート別初期値（§9.2: 小50k/中150k/大400k）より緩い値だが、バックストップは第一防衛線の失敗時のみ作動する設計のため許容する。

### エスカレーション経路

```
第一防衛線（スキルスクリプト）: spawn 前チェックで bound 超過検出
  ↓
gd-session-state.json: status = "escalated"
  ↓
L1 コンテキストが構造化報告の unresolved リストを PM に提示して終了

（第一防衛線が機能しなかった場合）
第二防衛線（Stop hook B-3 節）: exit 0 + additionalContext でエスカレーション理由注入
  ↓
Claude がメッセージを受け取り PM に報告
```

---

## 11. エージェント定義群（FR-7 / R7）

確認済みのフロントマター書式（ファクトシート §3）を使用する。

### goal-driven-l2-foreman.md

```yaml
---
name: goal-driven-l2-foreman
description: |
  大タスクの工程分解・L3 分配を担う班長エージェント。
  L1 からの rubric と工程リストを受け取り、l3-executor を分配する。
  goal-driven スキルの大タスクルートで使用。
tools: Read, Glob, Grep, Agent(goal-driven-l3-executor)
model: sonnet
memory: project
---
```

### goal-driven-l3-executor.md

```yaml
---
name: goal-driven-l3-executor
description: |
  実装・テスト実行を担う末端エージェント。
  rubric.md を参照し、構造化報告 JSON を返す。
  Task ツール（Agent）を持たず、自律 spawn 禁止。
tools: Read, Glob, Grep, Write, Edit, Bash
model: sonnet
effort: default
memory: project
---
```

**重要**: `tools` に `Agent` を含まない（FR-7 MUST）。`effort: default` は §12（FR-8: Dynamic Workflows 排除）対応。

### goal-driven-grader.md

```yaml
---
name: goal-driven-grader
description: |
  rubric.md と構造化報告を照合し、合否と理由を返す独立評価エージェント。
  作業者（l3-executor）と別コンテキストで実行される（FR-2）。
  原則 Haiku で動作し、判断が重い場合は呼び出し元が sonnet を指定する。
  Bash は rubric の verify コマンド実行（テスト・lint 等の読み取り専用検証）のみ使用。
  ファイル変更・git 操作・パッケージ操作は禁止（W-2）。
tools: Read, Glob, Grep, Bash
model: haiku
memory: project
---
```

grader の出力スキーマ:
```json
{
  "rubric_version": "YYYY-MM-DD",
  "overall": "pass | fail",
  "items": [
    {"id": 1, "result": "pass", "reason": "pytest exit 0 confirmed"},
    {"id": 2, "result": "fail", "reason": "field name mismatch: expected 'user_id', got 'userId'"}
  ],
  "escalate": false,
  "escalate_reason": ""
}
```

**判定不能時の扱い**: rubric の記述が不十分で合否を判定できない場合は、`overall: "fail"` とせず `escalate: true` を設定し、`escalate_reason` に rubric の不明確箇所を記載する。

**モデル選定根拠**:
- l2-foreman / l3-executor: Sonnet 4.6（既存 LAM 実行体制と統一）
- grader: Haiku 4.5（rubric 照合は判断負荷が低い。要件書 §4 参照）
- l2-foreman の Opus 昇格: 差し戻し頻発時に `model: opus` で再起動（実行時オプション）

**ネストサブエージェントの有効性（部分確認）**:
v2.1.172 で解禁（ファクトシート §2）。深さ上限は現時点 5 だが確定値か未確認。
深さ上限は `gd-session-state.json` の `nest_depth_limit` フィールドで外部化（NFR-5）。

**ネスト深さ最大値の計算（W-6 対応）**:

| パス | ネスト深さ |
|------|-----------|
| SKILL（L1） | 1 |
| SKILL → l2-foreman | 2 |
| SKILL → l2-foreman → l3-executor | 3 |
| フロー[8] full-review（L1 直下・ループ外） | 2（L1 → full-review） |
| full-review → Stage 2 内部サブエージェント（想定） | 3（L1 → full-review → 審査エージェント） |

最大ネスト深さ: **3**（上限 5 に対して余裕あり）。
full-review はループ内ではなく L1 直下で実行するため、三層ルートとの同時起動はない。
**上限 5 未確定リスク**: ファクトシート §2 の未確認事項。外部化設定で対応済み（NFR-5）。

**NFR-3: grader ログ永続化（W-4 対応）**:

grader の判定結果（合否理由）を `.claude/logs/gd/` に保存する。

```
.claude/logs/gd/
  gd-20260611-001-loop01-grader.json   # タスクID-ループ番号-grader
  gd-20260611-001-loop02-grader.json
  ...
```

rubric 改善への活用: `/retro` 実行時に `.claude/logs/gd/` を参照し、
同一 rubric 項目への繰り返し不合格パターンを集計して rubric 文言改善を提案する。

---

## 11b. NFR-6: ネスト失敗フォールバック（W-7 対応）

### 検知方法

L2 からの Agent(l3-executor) 呼び出しがエラーを返した場合にネスト失敗とみなす。
エラーの判別基準:
- Agent ツール結果の `error` フィールドが非空
- エラーメッセージに "sub-agent" / "nesting" / "not supported" 等が含まれる

### 発火条件

```
l2-foreman から l3-executor の spawn を試みる
  ↓ Agent ツールがエラー返却
  ↓ スクリプトがエラーパターンを検出
  → フォールバック発火
```

### フォールバック後フロー（三層→二層退避）

```
[フォールバック発火]
  ↓
gd-session-state.json: "fallback": "two_layer" を設定
  ↓
l2-foreman を廃し、SKILL.md スクリプト（L1 コンテキスト）が
l3-executor を直接制御（大タスクルートが中タスクルートと同等に）
  ↓
工程リストはスクリプトが逐次管理し、l3-executor を 1 工程ずつ起動
  ↓
グローバル bound・grader・構造化報告はそのまま維持（R2・R4 充足を保つ）
```

**制約**: 二層退避後は並列分解（工程の並列起動）が不可になる。
これは許容トレードオフとして明示的に記録する。

**NFR-6 MUST**: フォールバック有無・方式の記録 → 本節が設計書上の記録として機能する。

---

## 12. Dynamic Workflows 排除（FR-8）

### デフォルト経路からの排除担保

以下の 3 段構えで Dynamic Workflows がデフォルト経路に入らないことを保証する:

1. **SKILL.md 冒頭の明示禁止**: スキル定義内に以下を記載する
   ```
   ## 注意事項
   本スキルは Dynamic Workflows を使用しない。
   effort 設定は明示的に low または default とすること。
   "ultracode"、"use a workflow" 等のキーワードを使用してはならない（MUST NOT）。
   ```

2. **設定値の文書化**: `docs/specs/goal-driven-orchestration/config.md` に
   以下の推奨設定を記載する:
   ```json
   // .claude/settings.json（推奨）
   {
     "disableWorkflows": true
   }
   ```
   または環境変数: `CLAUDE_CODE_DISABLE_WORKFLOWS=1`

   config.md には requirements §0 の運用前提（Settings > Usage でのハードキャップ確認 MUST）も記載する。

3. **effort 設定の明示化**: l3-executor フロントマターに `effort: default` を明記し、
   `ultracode`（xhigh）になることを防ぐ。

### 将来の「特大」タスクルートへの対応（OQ-4）

FR-8 の要件通り、Dynamic Workflows を使う場合は PM の明示承認ゲートを設ける。
設計は現時点では不要（Non-Goals §2 参照）。

---

## 13. メモリ蒸留（FR-5）

### 蒸留パイプライン

```
タスク終了（合格 or エスカレーション）
  ↓
[L1 最終検収時（LLM 呼び出し）] fail→pass の修正ポイントを抽出
  ↓
[distill-lessons.py] 以下のルールで分類・追記（W-5 対応）:
  - 検証済みの一般則 → .claude/agent-memory/<agent-name>/lessons.md のみ
  - 未検証の推測 → 同ファイルに「未検証」タグ付きで追記（MUST）

※ docs/artifacts/knowledge/ への書き込みは distill-lessons.py の自動処理対象外。
  /retro Step 4 で人間が lessons.md を読み、精査した知見のみ手動で昇格させる。
  （CLAUDE.md Memory Policy §Knowledge Layer と整合）
```

### lessons.md エントリ形式

```markdown
## [YYYY-MM-DD] <タスク ID>: <教訓タイトル>

**状態**: 検証済み / 未検証
**ループ回数**: N
**fail 原因**: [要約]
**修正内容**: [要約]
**一般則**: [再発防止のためのルール文]
**適用範囲**: [対象ファイルパターン / 操作]
```

### 既存機構との接続

| 記録先 | 内容 | 機構 | 書き込み主体 |
|--------|------|------|------------|
| `.claude/agent-memory/goal-driven-l3-executor/lessons.md` | L3 実行パターンの教訓 | Subagent persistent memory（CLAUDE.md §Memory Policy） | distill-lessons.py（自動） |
| `docs/artifacts/knowledge/` | 人間が精査した知見 | Knowledge Layer | **/retro Step 4 の人間のみ**（自動書き込み禁止・W-5） |
| `.claude/tdd-patterns.log` | TDD fail→pass 遷移 | 既存 TDD 内省パイプライン v2 | PostToolUse hook（既存） |

---

## 14. コスト集計（NFR-1 / S4）

### 実装方式

Agent ツールの結果には `subagent_tokens`（確認済み・ファクトシート §5）が含まれる。
スキルスクリプトがこれを読み取り、モデル別・層別に `gd-session-state.json` に累積する。

```json
{
  "cost_log": {
    "l1_tokens": 12000,
    "l2_tokens": 5000,
    "l3_tokens": 45000,
    "grader_tokens": 8000,
    "l1_ratio": 0.17
  }
}
```

**正規フィールドの定義**: グローバル bound 判定の正規フィールドは `gd-session-state.json` **トップレベルの `total_tokens`**（§10）であり、Stop hook B-3 節もこれを参照する。`cost_log` は層別内訳のみを保持し、合計値を重複保持しない（二重更新による bound 不全を防ぐ）。`l1_ratio` の分母はトップレベル `total_tokens`。

### タスク完了時の出力（AC-11）

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

### L1 消費比率の計測方法（OQ-3 連携）

- `l1_ratio = l1_tokens / total_tokens` を毎タスク記録
- 5 タスク以上のデータが揃った時点で PM が L1 モデル継続可否を判断（OQ-3）
- 比率が 20% を超えた場合は rubric 生成の委任（L2 に移管）を検討

**未確認（要裏取り）**: OTEL によるエージェント別トークン計測（ファクトシート §5）。
`subagent_tokens` での代替計測で十分と判断するが、要確認。

---

## 15. full-review 連携（FR-9）

**本セクションはインターフェース定義のみ。**
現仕様分析・改造範囲・工数見積もりは `research/full-review-analysis.md`（Draft 完成・PM 承認待ち）に委ねる。

### 呼び出し形態（暫定案 / W-1 対応）

> **注意**: 以下のインターフェースは暫定案である。`research/full-review-analysis.md` の
> PM 承認後に確定形 API を定義する。承認前に full-review 側の実装を進めてはならない（FR-9 MUST NOT）。

フロー [8] 納品前検証として、スキルスクリプトが `/full-review` をサブエージェントとして呼び出す（I-3 参照）:

```
# 暫定案（確定形は full-review-analysis.md の承認後）
Agent(
  agent="full-review",
  prompt="rubric_path=<project_root>/docs/tasks/<slug>/rubric.md mode=subagent"
)
```

**W-6/ネスト深さ**: フロー [8] の full-review はループ内ではなく**メインセッション直下（L1）で実行**する。
full-review 内部は Stage 2 で最大 4 並列のサブエージェントを持つ可能性があるため、
ネスト深さ計算は §11 の表を参照すること。

### rubric 入力インターフェース（暫定）

`full-review` が rubric ファイルを受け取れるよう以下のインターフェースを暫定定義する:

| パラメータ | 型 | 説明 |
|-----------|----|------|
| `rubric_path` | string | rubric.md のプロジェクトルート絶対パス |
| `mode` | `standalone` \| `subagent` | subagent 時は報告のみ（直接修正なし） |

### 既存用途の温存（FR-9 MUST）

`/full-review` をトップレベルコマンドとして単体で使う既存ユーザーへの影響:
- `rubric_path` は省略可能（省略時は従来動作）
- `mode` のデフォルトは `standalone`

**改造の承認ゲート**: `research/full-review-analysis.md` が PM に提出・承認されるまで
full-review への改造には着手しない（FR-9 MUST NOT）。

### I-3: full-review-analysis との対応

`research/full-review-analysis.md` では full-review 改造を 3 フェーズで分析することが想定される:
- フェーズ 1（現状分析）: full-review の現在の呼び出し形態・パラメータ受け渡し方式を確認
- フェーズ 2（互換性評価）: `rubric_path`/`mode` 追加が既存 Stage 0〜5 に与える影響
- **フェーズ 3（実装承認）**: PM 承認後に本スキルの subagent 呼び出しが成立

本スキルのフロー [8] が実際に機能するのはフェーズ 3 承認後であり、
それ以前はフロー [8] を「スキップ（人間が手動で full-review を実行）」にフォールバックする。

---

## 16. lam-orchestrate 受け渡し形式（FR-10）

### パイプライン位置

```
lam-orchestrate（PLANNING 並列実行）
     ↓ 成果物受け渡し
goal-driven スキル（BUILDING 自己修正ループ）
     ↓ 最終成果物
full-review（納品前検収）
```

### lam-orchestrate 出力 → goal-driven 入力 の形式

lam-orchestrate の出力（設計文書・rubric 素案）を本スキル フロー[2] の入力として受け取る。

**受け渡しファイル**（`docs/tasks/<task-slug>/` に配置）:

| ファイル | 作成者 | 内容 |
|---------|--------|------|
| `design.md` | lam-orchestrate 経由 design-architect | 設計文書（実装の根拠） |
| `rubric-draft.md` | lam-orchestrate 経由 doc-writer | rubric 素案（L1 が完成させる） |
| `task-list.md` | lam-orchestrate 経由 task-decomposer | WBS タスクリスト |

**rubric-draft.md のスキーマ**（lam-orchestrate が準拠すべき形式）:

```markdown
# rubric-draft: <タスク名>（素案）

## 検証候補項目（L1 指揮者が確定・追記すること）

| # | チェック項目（素案） | 検証方法候補 | 備考 |
|---|-------------------|------------|------|
| 1 | FR-X の仕様フィールド名一致 | grader 判定（候補） | |
| 2 | 全テスト通過 | run: pytest（候補） | |
```

**goal-driven スキルのフロー[2] 入力処理**:
1. `rubric-draft.md` が存在する場合: L1 が内容を確認・確定し `rubric.md` を生成
2. `rubric-draft.md` がない場合: L1 がゼロから生成
3. `design.md` は L1 の rubric 生成の参照資料として使用

---

## 17. FR / NFR トレーサビリティ表

WBS 100% Rule の準備として、要件と設計セクションの対応を記す。

| 要件 ID | 内容（要約） | 設計セクション |
|--------|------------|--------------|
| FR-1 | rubric ファースト | §6 |
| FR-2 | 独立 grader | §8, §11 |
| FR-3 | 構造化報告 | §7 |
| FR-4 | bound（多層対応） | §10 |
| FR-5 | メモリ蒸留 | §13 |
| FR-6 | 三段階ルート | §9 |
| FR-7 | 最小権限（Task ツール除外） | §11 |
| FR-8 | Dynamic Workflows 除外 | §12 |
| FR-9 | full-review 連携 | §15 |
| FR-10 | lam-orchestrate 接続 | §16 |
| NFR-1 | コスト可観測性 | §14 |
| NFR-2 | /goal 優先 | §8（Plan A 優先） |
| NFR-3 | grader ログ保持 | §11（NFR-3: grader ログ永続化節） |
| NFR-4 | LAM フェーズ整合 | §1, §5, §16（パイプライン位置）, §15 |
| NFR-5 | ネスト深さ外部化 | §10（gd-session-state.json）, §11 |
| NFR-6 | フォールバック | §11b（NFR-6 フォールバック節） |
| NFR-7 | 既存 LAM との競合時先行提示 | §18（権限等級表・PM 確認事項） |
| NFR-8 | 成果物自体の独立 grader 検収 | §20 |
| OQ-1 | /goal サブエージェント内動作 | §8（検証タスク） |
| OQ-2 | 決定的骨格実装方式 | §3（比較表・選定） |
| OQ-3 | L1 モデル選定（6/23 以降） | §14（比率計測→PM 判断） |
| OQ-4 | 特大タスクルート | §12（将来対応、承認ゲート言及） |
| OQ-5 | 小タスク grader 起動主体 | §9.1（スクリプトが起動） |

---

## 18. Open Questions と検証タスク

### 設計フェーズ残課題

| # | 内容 | 根拠 | 対応方針 |
|---|------|------|---------|
| D1 | /goal サブエージェント内動作の実測 + トークン条件の書式確認（C-4 追加） | OQ-1 / AC-12 | **解決済み（2026-06-12）**: Plan B 確定。トークン条件書式の検証は Plan B 確定により不要化。`research/oq1-goal-subagent-test.md` 参照 |
| D2 | ネストサブエージェントのデフォルト有効性 | ファクトシート §2 | v2.1.172 環境で実測 |
| D3 | 深さ上限 5 の確定性 | ファクトシート §2 | 暫定として外部化（NFR-5）。確定次第更新 |
| D4 | Stop hook への B-3 節追加の既存への影響 | lam-stop-hook.py 改修 | NFR-7: 着手前に既存 Stop hook ロジックを PM へ提示 |
| D5 | full-review-analysis.md の PM 承認 | FR-9 / AC-14 | Draft 完成済み・PM 承認待ち。本設計書は参照のみ |

### 権限等級表（W-3 対応）

| 作業 | 等級 | 理由 |
|------|------|------|
| `lam-stop-hook.py` への B-3 節追加 | **PM級** | 既存 Stop hook（`.claude/rules/` 隣接の hooks 設定に相当）の改修 |
| `subagent-stop.py` 新規フック追加 | **PM級**（不要化のため実施なし） | settings.json 変更を伴うため |
| `.claude/scripts/distill-lessons.py` 新規 | SE級 | 既存 API 不変の新規スクリプト |
| `.claude/agents/goal-driven-*.md` 新規 | SE級（本設計の PM 承認に含まれる） | エージェント定義追加 |
| `docs/specs/goal-driven-orchestration/config.md` 新規 | **PM級**（本設計・tasks.md の PM 承認に包含） | `docs/specs/` 配下のドキュメント追加 |
| `docs/specs/goal-driven-orchestration/design.md` 更新 | **PM級** | `docs/specs/` 配下の仕様変更 |

### PM 確認事項（NFR-7 対応）

以下は実装着手前に PM の確認・承認が必要な事項である:

1. **D4（PM級）**: lam-stop-hook.py への B-3 節追加。競合排除条件（§10）の設計を PM に提示し承認を得ること
2. **D5（PM級）**: full-review 改造の着手承認（`research/full-review-analysis.md` 提出後）
3. **grader エージェントの配置（SE級・報告必須）**: `.claude/agents/` 配下への新規ファイル追加
4. **NFR-8 準拠**: 本スキルの SKILL.md 完成後、独立 grader（または PM）による検収を経ること（§20 参照）

---

## 19. 前提と既知の不確実性

本節は「見えない前提」を明文化し、後続フェーズの実装担当が暗黙の前提に依存しないようにする。

| ID | 前提 / 不確実性 | 現状 | 保証または対応 |
|----|----------------|------|--------------|
| P-1 | /goal の evaluator が独立コンテキストの Haiku である | ファクトシート §1 で「確認済み」（session-scoped Stop hook ラッパー・Haiku 使用）。ただし provider 依存性（Anthropic 専用か）は未確認 | 実装時に evaluator の実際のモデルをログで確認。プロバイダ非依存の Plan B 設計で代替可 |
| P-2 | Agent ツール結果に subagent_tokens が安定して返る | N=1 実測（ファクトシート §5 確認済み）。多層・並列時は未検証 | 実装時の検証項目に追加。取得失敗時は消費トークン 0 扱いではなく推定値（spawn 数×平均値）でフォールバック。`subagent_tokens` の取得単位（累計か単一スパン分か）も実装時検証項目に含める |
| P-3 | gd-session-state.json のパス解決 | cwd 依存は危険（サブエージェント内で cwd が変動する既知リスク） | パスは `get_project_root()` 関数（_hook_utils）でプロジェクトルート絶対パスを使用（§10 セッション状態ファイル） |
| P-4 | auto-compact 後も rubric.md が全層参照可能 | rubric.md は共有ファイルとしてファイルシステムに配置されるため成立（コンテキスト圧縮に依存しない） | §6 で保証内容を明記済み。SKILL.md プロンプトで起動時の rubric 再読み込みを指示 |

---

## 20. NFR-8: 本スキル成果物の検収設計

NFR-8 の要件: 本スキル実装成果物（SKILL.md 等）は実装担当者の自己申告完了を合格条件としない。

### 検収対象

| 成果物 | 検収基準 |
|--------|---------|
| `SKILL.md` | requirements.md AC-1〜AC-15 を rubric として照合 |
| エージェント定義 3 件 | FR-7 の tools 制約確認（Agent 除外）|
| `distill-lessons.py` | FR-5 蒸留フローの動作確認 |
| `lam-stop-hook.py` B-3 節 | C-1 修正後のセマンティクス確認（exit 0 + additionalContext）|

### 検収手順

```
[実装担当（tdd-developer 等）] SKILL.md 等の実装完了を宣言
  ↓
[検収エージェント（goal-driven-grader または quality-auditor）]
  - 別コンテキストで起動
  - rubric: requirements.md AC-1〜AC-15 + 本設計書の各 FR セクション
  - 合否と理由を JSON で出力
  ↓
[PM] 検収結果を確認し、合格判定を行う
```

### rubric（検収用）

```markdown
# rubric: goal-driven スキル検収

## 検証項目

| # | チェック項目 | 検証方法 | 合否基準 |
|---|------------|---------|--------|
| 1 | AC-1: SKILL.md が .claude/skills/goal-driven/ に存在する | run: ls | ファイル存在 |
| 2 | AC-6: L3/grader フロントマターに Agent が含まれない | grader: tools フィールド確認 | Agent 不在 |
| 3 | AC-7: /goal 条件文に打ち切り句が含まれる | grader: SKILL.md 読み取り | `or stop after N turns` 存在 |
| 4 | C-1: Stop hook B-3 節が exit 0 + additionalContext 方式 | grader: B-3 節読み取り | block 不在・exit 0 確認 |
| 5 | W-5: distill-lessons.py が docs/artifacts/knowledge/ に書かない | grader: スクリプト読み取り | 書き込み先が agent-memory のみ |
```

---

*設計書ここまで。バージョン 0.3.0 / 2026-06-12 / 2巡目レビュー（3層体制: spec-critic + トレーサビリティ + 機械突合）対応*
