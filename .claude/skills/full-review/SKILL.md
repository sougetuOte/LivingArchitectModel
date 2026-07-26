---
name: full-review
description: "並列監査 + 全修正 + 検証の一気通貫レビュー。--rubric-path=<rubric.md> でゴール条件を注入可能。--auto-approve でサブエージェント向け対話スキップ + 構造化 JSON 出力モード"
version: 1.2.0
disable-model-invocation: true
argument-hint: "<対象ファイル or ディレクトリ> [--rubric-path=<rubric.md>] [--auto-approve]"
---

# /full-review - 並列監査 + 全修正 + 自動ループ

引数: 対象ファイルまたはディレクトリ（必須）

> **⚠️ 警告（直列のみ運用）**: フェーズ 2 では複数 `/full-review` の同時実行を禁止する。
> 状態ファイル（`lam-loop-state.json` 等）は固定名のためレース条件が発生する（R-1/R-2 リスク）。
> 並列対応（invocation_id による状態ファイル分離）はフェーズ 3 で実装予定。

## AUDITING フェーズとの使い分け

- AUDITING フェーズ: 手動でフェーズ切替し段階的に監査（skill 廃止済 / `.claude/current-phase.md` を手動更新）
- `/full-review`: ワンショット実行。並列監査 -> 修正 -> 検証を自動ループで完了

---

## Stage 0: 初期化

**実行条件**: 常に実行
**入力**: 対象パス（引数）
**出力**: `lam-loop-state.json`, `scale-detection.json`

### Step 1: ループ状態ファイル生成

`.claude/lam-loop-state.json` を生成し、自動ループを開始する。

```bash
# 引数から --rubric-path=<value> を抽出（省略時は空文字）
# 例: /full-review src/ --rubric-path=rubric.md → RUBRIC_PATH=rubric.md
RUBRIC_PATH=""
AUTO_APPROVE=false
for arg in $ARGUMENTS; do
  case "$arg" in
    --rubric-path=*) RUBRIC_PATH="${arg#--rubric-path=}" ;;
    --auto-approve) AUTO_APPROVE=true ;;
  esac
done

# TARGET は ARGUMENTS の最初の非オプション引数
TARGET=""
for arg in $ARGUMENTS; do
  case "$arg" in
    --*) ;;
    *) if [ -z "$TARGET" ]; then TARGET="$arg"; fi ;;
  esac
done

# 状態ファイルを生成（Bash で実行）
# 注: $TARGET / $TIMESTAMP / $RUBRIC_PATH / $AUTO_APPROVE はシェル変数。heredoc 内で展開される
# rubric_path は省略時に空文字で格納（後方互換: フィールド追加のみ・既存フィールド変更なし）
# auto_approve は省略時 false（後方互換）
cat > .claude/lam-loop-state.json << EOF
{
  "active": true,
  "command": "full-review",
  "target": "$TARGET",
  "iteration": 0,
  "max_iterations": 5,
  "started_at": "$TIMESTAMP",
  "rubric_path": "$RUBRIC_PATH",
  "auto_approve": $AUTO_APPROVE,
  "log": []
}
EOF
```

**状態ファイルスキーマ** (`.claude/lam-loop-state.json`):

| フィールド | 型 | 説明 | 管理者 |
|-----------|---|------|--------|
| `active` | boolean | ループ有効フラグ | `/full-review` |
| `command` | string | 起動コマンド（常に `"full-review"`） | `/full-review` |
| `target` | string | 監査対象パス（引数から取得） | `/full-review` |
| `iteration` | number | 現在のイテレーション番号（0始まり） | `/full-review` |
| `max_iterations` | number | 最大イテレーション数（デフォルト: **5**） | `/full-review` |
| `started_at` | string | ループ開始時刻（ISO 8601） | `/full-review` |
| `log` | array | 各イテレーションの記録（下記参照） | `/full-review` |
| `fullscan_pending` | boolean | フルスキャン待ちフラグ（Stage 5 でセット、Claude が参照） | `/full-review` |
| `pm_pending` | boolean | PM級承認待ちフラグ（Stage 4 でセット、Claude/Stop hook が参照） | `/full-review` |
| `tool_events` | array | ツール実行イベントの記録（PostToolUse hook が追記） | PostToolUse hook |
| `rubric_path` | string | ゴール条件 rubric ファイルのパス（省略時は空文字 `""`） | `/full-review` |
| `auto_approve` | boolean | 対話スキップ + 構造化 JSON 出力モード（デフォルト: `false`） | `/full-review` |

**log エントリ**:

| フィールド | 型 | 説明 |
|-----------|---|------|
| `iteration` | number | イテレーション番号 |
| `issues_found` | number | 発見した問題数 |
| `issues_fixed` | number | 修正した問題数 |
| `pg` | number | PG級の問題数 |
| `se` | number | SE級の問題数 |
| `pm` | number | PM級の問題数 |
| `test_count` | number | テスト数（Stop hook がエスカレーション判定に使用） |

**ループ制御の仕組み**: ループは Claude（本スキル）が Stage 5 完了後に自分で Stage 2 に戻ることで実現する。
Stop hook はアクティブなループが存在する限り block するが、あくまで安全ネットであり、ループの主制御には使わない。
`stop_hook_active=true` の再帰防止により Stop hook 自身が再帰的に呼ばれることはない。
Green State 判定、イテレーション管理、状態ファイル削除は全て Claude 側の責務。

### Step 2: context7 MCP 検出

full-review 開始時に context7 MCP の利用可否を確認する。

- **利用可能**: 仕様確認（G4/G5）で context7 を使用
- **利用不可**: 以下の警告を表示し、仕様確認をスキップして処理を続行

```
⚠️ context7 MCP が未設定のため、仕様確認（G5）をスキップしました。
  最新仕様との整合性確認が必要な場合は、対話モードで
  PLANNING フェーズまたは upstream-first ルールを利用してください。
  （full-review 内での WebFetch は無応答リスクがあるため使用しません）
```

> WebFetch は対話モード（PLANNING フェーズ, upstream-first）でのみフォールバックとして使用する。
> 自動フロー内での WebFetch は無応答・無限待機のリスクがあるため使用しない。

### Step 3: Scale Detection 判定（Plan E: FR-E2）

プロジェクト規模に応じて有効化する Plan セットを自動判定する。

```bash
bash .claude/scripts/py_invoke.sh .claude/hooks/analyzers/scale_detector.py "$TARGET"
```

判定結果は `.claude/review-state/scale-detection.json` に永続化される。

**後続 Stage の制御**:

| Active Plans | Stage 1 | Stage 2 | Stage 3 | Stage 4 |
|:-------------|:--------|:--------|:--------|:--------|
| なし（~10K） | スキップ | 従来モード | レポート統合のみ | 重要度順修正 |
| Plan A | 実行 | 従来モード | レポート統合のみ | 重要度順修正 |
| Plan A + B | 実行 | チャンクモード | Layer 2/3 実行 | 重要度順修正 |
| Plan A + B + C | 実行 | チャンクモード | 全 Layer 実行 | 重要度順修正 |
| Plan A + B + C + D | 実行 | チャンクモード + トポロジカル順 | 全 Layer 実行 | トポロジカル順修正 |

### Step 4: untracked ファイルの事前確認

`git status --porcelain` で untracked ファイルの有無を確認する。

```
if [ "$AUTO_APPROVE" = "false" ]; then
  # 通常モード: untracked が存在する場合、警告してユーザーに削除/除外の確認を求める
  # （B-2 iter4 で残置一時ファイルが偽陽性 10 件を発生させた教訓。B-2 retro 反映）
  git status --porcelain | grep '^??' && echo "⚠️ untracked ファイルが存在します。静的解析ノイズ源となる可能性があります。削除/除外しますか？"
else
  # auto_approve モード: 警告のみ表示し、対話なしで続行
  git status --porcelain | grep '^??' && echo "⚠️ [auto_approve] untracked ファイルが存在します（静的解析ノイズ源の可能性）。対話スキップのため続行します。"
fi
```

Stage 0 完了後、Stage 1 に進む（Plan A 以上の場合）。Plan セットが「なし」の場合は Stage 1 をスキップし Stage 2 に直行する。

---


## Stage map（以降の手順は必要になった時点で読む）

Stage 0 完了後、**現在の Stage のファイルだけを読んで実行する**。先読みしないこと。

| Stage | 内容 | 参照先 |
|:--|:--|:--|
| Stage 1 | 静的分析 + 依存グラフ構築 | [references/stage-1.md](references/stage-1.md) |
| Stage 2 | チャンク分割 + トポロジカル順レビュー | [references/stage-2.md](references/stage-2.md) |
| Stage 3 | 階層的統合 + レポート生成 | [references/stage-3.md](references/stage-3.md) |
| Stage 4 | トポロジカル順修正 | [references/stage-4.md](references/stage-4.md) |
| Stage 5 | 検証 + Green State 判定 + 完了 | [references/stage-5.md](references/stage-5.md) |

背景資料: [references/scalable-code-review.md](references/scalable-code-review.md)（実行手順ではない）
