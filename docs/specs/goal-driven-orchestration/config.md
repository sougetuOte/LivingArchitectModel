# 設定リファレンス: ゴール駆動オーケストレーション・スキル

- バージョン: 1.0.0
- 作成日: 2026-06-12
- ステータス: Draft（tasks.md v1.2.0 の PM 承認に包含）
- 参照設計: `design.md` v0.3.1
- 参照要件: `requirements.md` v1.2.0
- 対応タスク: W1-T2

---

## 目次

1. [運用前提: ハードキャップの設定（必須）](#1-運用前提ハードキャップの設定必須)
2. [bound 初期値表](#2-bound-初期値表)
3. [Dynamic Workflows 排除設定](#3-dynamic-workflows-排除設定)
4. [nest_depth_limit の外部化](#4-nest_depth_limit-の外部化)
5. [gd-session-state.json スキーマ](#5-gd-session-statejson-スキーマ)
6. [get_project_root() によるパス解決](#6-get_project_root-によるパス解決)

---

## 1. 運用前提: ハードキャップの設定（必須）

> **要件出典**: requirements.md §0 / design.md §12

本スキルを起動する前に、**Settings > Usage でハードキャップを確認・設定しなければならない（MUST）**。

### なぜ必要か

本スキルが設定する bound（FR-4）はモデルへの指示レベルで機能するが、プラットフォームの課金動作は
LAM の bound では制御できない外部要因である。サブスクプランの使用量超過時、使用クレジットへ自動的に
課金が溢れる設定がデフォルトになっている場合があり、スキル起動前に bound を設定しても
API 課金は発生し得る。

### 手順

1. Claude Code > Settings > Usage にアクセスする
2. ハードキャップ（Hard Limit）の値を確認する
3. スキル実行前にハードキャップが適切に設定されていることを人間（PM）が確認する

**ハードキャップの設定はスキル実装では代替できない。設定は PM の責任である。**

---

## 2. bound 初期値表

> **出典**: design.md §9.2（各ルートの設定値表）/ design.md §10（bound 機構・層別 bound 表）

### グローバル bound 初期値（ルート別）

| ルート | global_token_bound（初期値） | global_time_bound（初期値） |
|--------|-----------------------------|-----------------------------|
| 小タスク | 50,000 トークン | 3,600 秒（1 時間） |
| 中タスク | 150,000 トークン | 3,600 秒（1 時間） |
| 大タスク | 400,000 トークン | 7,200 秒（2 時間） |

**注記**:
- `global_bound` は OR セマンティクスを採用する。いずれか早く到達した方で打ち切る（design §6 I-4 対応）
- 数値はすべて初期値であり、`rubric.md` の `global_bound` フィールドで上書き可能（NFR-5）
- `gd-session-state.json` の `global_token_bound` / `global_time_bound` フィールドに書き込まれ、スキルスクリプトおよび Stop hook B-3 節がこれを参照する

### L3 max_turns 初期値（ルート別）

| ルート | L3 max_turns（初期値） |
|--------|----------------------|
| 小タスク | 10 ターン |
| 中タスク | 20 ターン |
| 大タスク | 15 ターン（工程ごと） |

> **出典**: design.md §9.2

### グローバル bound フォールバック値（Stop hook B-3 節）

Stop hook の B-3 節では `gd-session-state.json` から `global_token_bound` が読み取れない場合に
フォールバック値として **200,000 トークン** を使用する。

この値はルート別初期値より緩い。バックストップ（第二防衛線）は第一防衛線（スキルスクリプト）の
失敗時のみ作動する設計であるため、この差異は許容設計上のトレードオフである。

> **出典**: design.md §10（フォールバック値 200,000 の意図）

---

## 3. Dynamic Workflows 排除設定

> **出典**: design.md §12（Dynamic Workflows 排除・FR-8）/ requirements.md FR-8 / AC-10

### 推奨設定: settings.json

以下の設定を `.claude/settings.json` に追加することを推奨する:

```json
{
  "disableWorkflows": true
}
```

### 代替手段: 環境変数

```bash
CLAUDE_CODE_DISABLE_WORKFLOWS=1
```

### 3 段構えの排除保証

design §12 が定める 3 段構えはすべて維持しなければならない（MUST）:

| 段 | 対応箇所 | 内容 |
|----|---------|------|
| 1 | SKILL.md 冒頭の注意事項 | Dynamic Workflows 使用禁止の明示宣言 |
| 2 | 本ファイル §3（本節） | `disableWorkflows: true` 推奨設定の文書化 |
| 3 | l3-executor フロントマター | `effort: default` の明記（`ultracode` による自動起動防止） |

### 将来の「特大」タスクルートにおける DW 使用

将来 Dynamic Workflows を使用する場合も、起動には人間（PM）の明示承認ゲートを設けなければならない（MUST）。自動起動・暗黙起動は禁止（MUST NOT）（requirements.md FR-8 / OQ-4）。

---

## 4. nest_depth_limit の外部化

> **出典**: design.md §10（gd-session-state.json スキーマ）/ design.md §11 / requirements.md NFR-5

### 外部化の方針

サブエージェントのネスト深さ上限および grader 差し戻し回数上限は `gd-session-state.json` に
外部化する（MUST NOT ハードコード）。

| フィールド名 | 型 | 初期値 | 説明 |
|-------------|-----|--------|------|
| `nest_depth_limit` | integer | 5 | ネスト深さ上限（暫定値・確定次第更新） |
| `max_loop_count` | integer | 3 | grader 差し戻し回数上限（NFR-5 外部化対象） |

**`max_loop_count` の外部化要件** (requirements.md NFR-5 / design §10):
- 差し戻し回数上限はハードコードしてはならない（MUST NOT）
- 変更時にコード修正を不要とするため `gd-session-state.json` の `max_loop_count` フィールドから取得する（MUST）
- `rubric.md` の差し戻しルール記述においても `max_loop_count` フィールドを参照すること（design §6 参照）

### 現時点のネスト深さ計算

| パス | ネスト深さ |
|------|-----------|
| SKILL（L1） | 1 |
| SKILL → l2-foreman | 2 |
| SKILL → l2-foreman → l3-executor | 3 |
| full-review（L1 直下・ループ外） | 2 |
| full-review → 内部サブエージェント（想定） | 3 |

最大ネスト深さは **3**。`nest_depth_limit = 5` に対して余裕があるが、上限 5 の確定性は
未確認（design §18 D3）のため外部化設定で対応する。

> **出典**: design.md §11（ネスト深さ最大値の計算）

---

## 5. gd-session-state.json スキーマ

> **出典**: design.md §10（セッション状態ファイル定義・フォールバック値・フェイルセーフ）

### 配置パス

```
<project_root>/.claude/gd-session-state.json
```

パスは `cwd` 依存ではなく `get_project_root()` で解決したプロジェクトルート絶対パスを使用する（§6 参照）。

### 完全スキーマ

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

### フィールド定義

| フィールド | 型 | 初期値 | 説明 |
|-----------|-----|--------|------|
| `task_id` | string | — | タスク識別子（例: `gd-YYYYMMDD-NNN`） |
| `task_slug` | string | — | タスクのスラッグ（`docs/tasks/` のディレクトリ名に対応） |
| `route` | string | — | ルート種別: `"small"` / `"medium"` / `"large"` |
| `nest_depth_limit` | integer | 5 | ネスト深さ上限（NFR-5 外部化。§4 参照） |
| `global_token_bound` | integer | ルート別初期値 | グローバルトークン bound（§2 参照） |
| `global_time_bound` | integer | ルート別初期値 | グローバル時間 bound（秒単位。§2 参照） |
| `total_tokens` | integer | 0 | **グローバル bound 判定の正規フィールド**。各 Agent 呼び出し後に累積更新する（MUST） |
| `loop_count` | integer | 0 | grader 差し戻し回数の現在値 |
| `max_loop_count` | integer | 3 | grader 差し戻し回数上限（NFR-5 外部化対象。§4 参照） |
| `start_time` | float | — | スキル起動時の UNIX タイムスタンプ（秒） |
| `status` | string | `"running"` | セッション状態: `"running"` / `"escalated"` / `"completed"` |

### total_tokens と cost_log の関係

グローバル bound 判定の正規フィールドは **トップレベルの `total_tokens`** である。

```json
{
  "total_tokens": 70000,
  "cost_log": {
    "l1_tokens": 12000,
    "l2_tokens": 5000,
    "l3_tokens": 45000,
    "grader_tokens": 8000,
    "l1_ratio": 0.17
  }
}
```

- `total_tokens`: グローバル bound 判定・Stop hook B-3 節の参照先。各 Agent 呼び出し後に更新（MUST）
- `cost_log`: 層別内訳のみを保持する。合計値を重複保持してはならない（design §14 MUST NOT）
- `l1_ratio`: `l1_tokens / total_tokens` で算出。分母はトップレベルの `total_tokens`（design §14）

> **出典**: design.md §14（正規フィールドの定義・`cost_log` は層別内訳のみ保持・重複保持禁止）

### status フィールドの遷移

```
"running"  →（bound 超過・差し戻し上限）→  "escalated"
"running"  →（grader 合格・完了）         →  "completed"
```

### 残留時のフェイルセーフ

スキル起動時に `gd-session-state.json` が `status: "running"` のまま存在する場合
（前回セッションの異常終了による残留）、**自動削除はせず PM に提示し、明示承認後に削除して
新規開始する**（design §10 フェイルセーフ）。

---

## 6. get_project_root() によるパス解決

> **出典**: design.md §10（P-3 対応）/ requirements.md §19 P-3

### P-3 問題

サブエージェント内では `cwd`（カレントワーキングディレクトリ）が変動する既知リスクがある。
`gd-session-state.json` のパスを `cwd` に依存させると、サブエージェントが異なるディレクトリで
実行された場合にファイルが見つからず、bound チェックが機能しなくなる。

### 指針

`gd-session-state.json` および関連ファイル（`rubric.md` を除く）のパス解決には、
`get_project_root()` 関数（`_hook_utils` モジュール）でプロジェクトルート絶対パスを取得し、
それを基底パスとして使用しなければならない（MUST）。

```python
# 実装例（design §10 B-3 節コードより）
gd_state_path = get_project_root() / ".claude" / "gd-session-state.json"
```

### 適用対象ファイル

| ファイル | パス解決方式 |
|---------|------------|
| `gd-session-state.json` | `get_project_root()` 絶対パス（MUST） |
| `.claude/logs/gd/` ログ | `get_project_root()` 絶対パス |
| `rubric.md` | `docs/tasks/<task-slug>/` 絶対パスで参照（auto-compact 後も安定。design §6 P-4） |
| `.claude/rubric-tmp.md` | `get_project_root()` 絶対パス（小タスク暫定 rubric） |

---

*config.md ここまで。バージョン 1.0.0 / 2026-06-12 / doc-writer サブエージェント（W1-T2）*
