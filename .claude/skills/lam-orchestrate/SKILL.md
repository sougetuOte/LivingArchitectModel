---
name: lam-orchestrate
description: >
  LAM Coordinator - タスクを分解し、適切な Subagent で並列実行する。
  複数ファイル/モジュールにまたがる作業の自動分解・並列実行に使用。
  Use proactively when the user requests multi-file or multi-module operations.
version: 1.0.0
---

# LAM Orchestrate Coordinator

あなたは LAM プロジェクトの **Coordinator**（調整者）です。
ユーザーから与えられたタスクを分析し、最適な実行計画を立案・実行します。

## 実行フロー

### Phase 1: 分析

1. タスクの全体像を把握する
2. 対象ファイル/ディレクトリを `Glob` と `Grep` で調査する
3. **Git 状態の確認**:
   - `git status` でワーキングツリーの状態を把握
   - 対象ファイルに未コミット変更がある場合、`git diff` で差分を確認
   - `.claude/current-phase.md` を読み取り、現在のフェーズを把握
4. 独立して実行可能な単位に分解する
5. 各単位に最適な Subagent を割り当てる

### Phase 2: 実行計画の提示

分解結果を以下の形式で表示し、ユーザーの承認を得る:

```
## 実行計画

| # | タスク | Subagent | Wave |
|---|--------|----------|:----:|
| 1 | [タスク説明] | [subagent-name] | 1 |
| 2 | [タスク説明] | [subagent-name] | 1 |
| 3 | [タスク説明] | [subagent-name] | 2 |

**並列数**: N（Wave 内で並列実行）
**推定 Subagent 数**: M

続行しますか？ [Y/n]
```

**承認の範囲**:
- ユーザーが計画を承認した場合、全 Wave の実行が許可されたものとする
- Wave 完了ごとの再承認は不要（ただし FATAL エラー発生時は停止し報告）
- 途中で計画変更が必要になった場合は「Phase 5: 計画変更プロトコル」に従う

`--dry-run` が指定された場合、計画表示のみで実行しない。

### Phase 3: 実行

1. 並列実行可能なタスクを **1メッセージで複数の Task を呼び出す**
2. 依存関係があるタスクは Wave を分けて逐次実行する
3. 各 Wave の完了を待ってから次の Wave を開始する

### Phase 4: 統合

1. 各 Subagent の結果を収集する
2. 変更ファイル一覧を統合する
3. 整合性チェック（インポートの競合等）を行う
4. 統合レポートを作成する

### Phase 5: 計画変更プロトコル（Phase 3 実行中に発動）

Phase 3（実行）の途中でユーザーから追加要望が発生した場合、以下の手順で対応する:

1. **差分計画の作成**: 既存計画との差分を明示した「変更計画」を作成する
2. **影響範囲の分析**: 既に完了した Wave への影響（ファイル再編集の要否等）を分析する
3. **変更計画の提示**: 以下の形式で提示し、承認を得る

````
## 計画変更提案

**追加要件**: [ユーザーの追加要望]

**影響**:
- Wave X（完了済み）: 再実行不要 / ファイル Z の再編集が必要

**追加タスク**:
| # | タスク | Subagent | Wave |
|---|--------|----------|:----:|
| N | [新規タスク] | [agent] | M |

続行しますか？ [Y/n]
````

4. **承認後実行**: 承認されれば Phase 3 の実行ルールに従って追加タスクを実行する

## 並列実行ルール

```
最大並列数: 5（デフォルト）
引数 --parallel=N で上書き可能

並列化の条件:
  ✓ 異なるファイル/ディレクトリを対象としている
  ✓ 相互に依存しないタスク
  ✗ 同一ファイルへの書き込み → 直列化
  ✗ 出力が次の入力になる → Wave 分離
```

## 構造化思考（MAGI System）

複雑な判断が必要な場面で `/magi` スキルの思考フレームワークを発動する。
SSOT は `docs/internal/06_DECISION_MAKING.md`。

### 発動条件（いずれか）

- 判断ポイントが 2 つ以上
- 影響レイヤー/モジュールが 3 つ以上
- 有効な選択肢が 3 つ以上
- 不可逆な決定を含む

判断ポイントが 2 つ未満の場合は発動しない（従来手法で処理）。

### 実行フロー

`/magi` スキルの Step 0〜5 に従う。詳細は `.claude/skills/magi/SKILL.md` を参照。

```
Step 0: AoT Decomposition → Step 1-3: MAGI Debate → Step 4: Reflection → Step 5: AoT Synthesis
```

| レベル | 条件 | モデル |
|:---|:---|:---|
| Level 1 | 判断ポイント 2+、単一ドメイン | Sonnet |
| Level 2 | 影響レイヤー 3+ or 選択肢 3+ | Sonnet |
| Level 3 | 不可逆 or 複数ドメイン高リスク | Opus |

### アンカーファイル

思考過程を `docs/artifacts/YYYY-MM-DD-magi-{用途}.md` に書き出す（可視化・追跡可能）。
- 書き込み権限: CASPAR のみ（Single-Writer）
- 読み取り権限: 全 Agent（Multi-Reader）
- 削除: ユーザーのみ可能
- フォーマット: `.claude/skills/magi/references/anchor-format.md` を参照

### 参照

- `/magi` スキル: `.claude/skills/magi/SKILL.md`
- SSOT: `docs/internal/06_DECISION_MAKING.md`

## Subagent 選択ルール

`.claude/agents/` に定義されたカスタム Subagent を優先し、
未定義のパターンにはビルトイン Subagent を使用する。

| ファイルパターン | 推奨 Subagent | 備考 |
|------------------|---------------|------|
| `*test*`, `*spec*` | test-runner | カスタム定義 |
| `*.md`, `docs/` | doc-writer | カスタム定義。仕様策定（思考）と清書（整形）の両方を担当。方針と調査結果を渡し、詳細策定を委ねる |
| コードレビュー系 | code-reviewer | カスタム定義（LAM品質基準適用） |
| 品質監査・整合性 | quality-auditor | カスタム定義（アーキテクチャ・仕様ドリフト検証） |
| 要件分析系 | requirement-analyst | カスタム定義（3 Agents Model 内蔵） |
| 設計・アーキテクチャ系 | design-architect | カスタム定義（データモデル・API設計） |
| タスク分解系 | task-decomposer | カスタム定義（1PR単位分割） |
| 調査・探索系 | Explore | ビルトイン |
| その他 | general-purpose | ビルトイン |

> プロジェクト固有の Subagent（例: `rust-specialist`, `frontend-dev`）は
> `.claude/agents/` に追加すれば自動的に選択候補に含まれる。

## ループ統合（v4.0.0）

lam-orchestrate は `/full-review` コマンドと連携し、自動ループの状態管理を担う。

### 状態ファイル: `.claude/lam-loop-state.json`

lam-orchestrate または `/full-review` Phase 1 が生成し、ループのライフサイクル全体を通じて管理する中核ファイル。
`/full-review` が単独実行された場合は `/full-review` 自身が生成する。lam-orchestrate 経由の場合は lam-orchestrate が生成する。

**スキーマ定義（SSOT）**: `/full-review` コマンド（`.claude/commands/full-review.md` Phase 1）を参照。

### ループライフサイクル

```
1. 初期化（/full-review Phase 1）
   `/full-review` または lam-orchestrate が状態ファイルを生成
   → active: true, iteration: 0

2. 状態更新（各イテレーション完了時）
   Phase 4 検証後に iteration をインクリメント
   log[] に当該イテレーションの結果を追記
   → issues_found, issues_fixed, pg/se/pm 件数, test_count

3. 終了処理（Green State 達成 or 上限到達）
   Phase 5 で状態ファイルを削除
   ループログを .claude/logs/ に保存
```

### hooks との連携

lam-orchestrate が生成・更新する状態ファイルを、各 hook が参照して動作する:

| hook | 参照タイミング | 動作 |
|------|-------------|------|
| **Stop hook** (`lam-stop-hook.py`) | Claude 応答完了時 | `active: true` なら Green State 判定。未達なら `block` で継続 |
| **PostToolUse hook** (`post-tool-use.py`) | ツール実行後 | `active: true` ならツール実行結果を `tool_events[]` に追記 |
| **PreToolUse hook** (`pre-tool-use.py`) | ツール実行前 | ループ中も PG/SE/PM 権限判定は通常通り適用 |

**データフロー**:
```
lam-orchestrate (状態ファイル生成)
    ↓
/full-review Phase 1-4 (Claude が監査・修正を実行)
    ↓
PostToolUse hook (ツール結果を状態ファイルに記録)
    ↓
Claude 応答完了
    ↓
Stop hook (状態ファイルを読み、継続/停止を判定)
    ↓ block（継続）
Phase 1 に戻る（自動ループ）
```

### `/full-review` コマンドとの統合

lam-orchestrate と `/full-review` の状態ファイル生成責任:

- **単独実行**: `/full-review` 自身が Phase 1 で状態ファイルを生成する
- **lam-orchestrate 経由**: lam-orchestrate が状態ファイルを生成し、`/full-review` は生成をスキップする（既存ファイルを検出した場合）

lam-orchestrate は、より複雑なマルチタスク実行時に `/full-review` を内包する形で使用される。

### fullscan_pending フラグ管理

Phase 4 の差分チェックで Green State を達成した場合、フルスキャンを発動するためにフラグをセットする:

```bash
# Phase 4 で差分チェック Green State 達成時に実行
python3 -c "import json,pathlib;p=pathlib.Path('.claude/lam-loop-state.json');d=json.loads(p.read_text());d['fullscan_pending']=True;p.write_text(json.dumps(d,indent=2,ensure_ascii=False))"
```

フルスキャン発動は Claude の自律制御による（`/full-review` Phase 5 参照）。Stop hook は `fullscan_pending` フラグを直接検出しない。

### エスカレーション条件

ループ中に以下の条件を検出した場合、自動ループを停止しユーザーにエスカレーションする:

| 条件 | 検出者 | 対応 | 実装状況 |
|------|--------|------|---------|
| `stop_hook_active=true`（再帰防止） | Stop hook STEP 0 | 無条件 exit 0 | 実装済み |
| PM級の問題を検出 | `/full-review` Phase 2 | ループ停止、承認待ち | 実装済み |
| max_iterations 到達 | Stop hook | ループ強制停止 | 実装済み |
| コンテキスト枯渇（PreCompact 発火） | Stop hook | ループ停止、`/quick-save` 推奨 | 実装済み |
| 前サイクルの Issue 再発 | Claude 自律制御 | ループ停止、手動介入推奨 | Claude 判断で実施 |
| テスト数減少 | Claude 自律制御 | ループ停止、PM級エスカレーション | Claude 判断で実施 |

## 禁止事項

- Subagent からの Subagent 起動（Claude Code の技術的制約）
- 未分析でのタスク実行
- ユーザー承認なしでの実行開始（`--no-confirm` 指定時を除く）

## エラー処理

| エラー種別 | 対応 |
|-----------|------|
| RECOVERABLE（タイムアウト等） | 最大3回リトライ |
| PARTIAL_FAILURE（一部失敗） | 成功結果を保持し、失敗タスクを報告 |
| FATAL（前提条件エラー） | 全体停止、エラーレポート出力 |

## 実行結果フォーマット

```
## 実行結果

| タスク | 状態 | 変更 | 詳細 |
|--------|:----:|------|------|
| [タスク1] | ✅ | N files | [概要] |
| [タスク2] | ✅ | N files | [概要] |
| [タスク3] | ❌ | - | [エラー内容] |

**合計**: X ファイル変更、Y エラー
```
