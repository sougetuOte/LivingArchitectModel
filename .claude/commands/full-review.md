---
description: "並列監査 + 全修正 + 検証の一気通貫レビュー"
---

# /full-review - 並列監査 + 全修正 + 自動ループ

引数: 対象ファイルまたはディレクトリ（必須）

## /auditing との使い分け

- `/auditing`: フェーズ切替。AUDITING モードに入り、手動で段階的に監査
- `/full-review`: ワンショット実行。並列監査 -> 修正 -> 検証を自動ループで完了

## Phase 0: ループ初期化（v4.0.0）

`.claude/lam-loop-state.json` を生成し、自動ループを開始する。

```bash
# 状態ファイルを生成（Bash で実行）
cat > .claude/lam-loop-state.json << 'EOF'
{
  "active": true,
  "command": "full-review",
  "target": "$TARGET",
  "iteration": 0,
  "max_iterations": 5,
  "started_at": "$TIMESTAMP",
  "log": []
}
EOF
```

**状態ファイルスキーマ** (`.claude/lam-loop-state.json`):

| フィールド | 型 | 説明 |
|-----------|---|------|
| `active` | boolean | ループ有効フラグ |
| `command` | string | 起動コマンド（常に `"full-review"`） |
| `target` | string | 監査対象パス（引数から取得） |
| `iteration` | number | 現在のイテレーション番号（0始まり） |
| `max_iterations` | number | 最大イテレーション数（デフォルト: **5**） |
| `started_at` | string | ループ開始時刻（ISO 8601） |
| `log` | array | 各イテレーションの記録（下記参照） |

**追加フィールド**（hook が管理）:

| フィールド | 型 | 説明 | 管理者 |
|-----------|---|------|--------|
| `fullscan_pending` | boolean | フルスキャン待ちフラグ（Phase 4 でセット、Stop hook で参照） | `/full-review` Phase 4 |
| `tool_events` | array | ツール実行イベントの記録（PostToolUse hook が追記） | PostToolUse hook |

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

Phase 0 完了後、Phase 1 に進む。

**自動ループの仕組み**: Phase 4 の検証で Green State 未達の場合、Claude の応答が終了すると Stop hook (`lam-stop-hook.sh`) が発火し、状態ファイルを確認して自動的に Phase 1 に戻る。ユーザーの操作は不要。

## Phase 1: 並列監査

対象に対して以下のサブエージェントを並列起動:

| エージェント | 観点 | 出力要件 |
|-------------|------|---------|
| `code-reviewer` (1) | ソースコード品質（命名、構造、エラー処理） | 各 Issue に PG/SE/PM 分類を付与 |
| `code-reviewer` (2) | テストコード品質（網羅性、可読性、テストパターン） | 各 Issue に PG/SE/PM 分類を付与 |
| `quality-auditor` | アーキテクチャ・仕様整合性（依存関係、**仕様ドリフト**、**構造整合性**） | 仕様ドリフト + 構造整合性結果を含む |
| `code-reviewer` (3) | セキュリティ（OWASP Top 10、シークレット漏洩、依存脆弱性、インジェクション） | 各 Issue にリスクレベル (Critical/High/Medium/Low) + PG/SE/PM 分類を付与 |

プロジェクト規模に応じてエージェント構成を調整可能。
小規模の場合は `code-reviewer` x1 + `quality-auditor` x1 でもよい（ただしセキュリティ観点は省略しないこと）。

各エージェントは独立した監査レポートを生成する。

**イテレーション2回目以降の差分チェック**: 2回目以降のサイクルでは、前サイクルで修正されたファイルのみを対象にする（差分チェック）。これにより不要な再監査を避け、収束を早める。

**仕様ドリフトチェック（quality-auditor）**: quality-auditor は `docs/specs/` と対象コードの整合性を検証する。仕様に記述されているが実装されていない機能、または実装されているが仕様に記述されていない機能を「仕様ドリフト」として報告する。

**セキュリティチェック（code-reviewer セキュリティ）**: OWASP Top 10 に基づくコードレベルの脆弱性検出を行う。具体的には:
- **インジェクション**: SQL/NoSQL/コマンドインジェクション、eval 使用
- **認証・認可**: ハードコードされた認証情報、不適切なアクセス制御
- **シークレット漏洩**: API キー、パスワード、トークンのコード内露出
- **依存脆弱性**: 既知の脆弱性を持つライブラリの使用
- **データ露出**: ログへの機密情報出力、エラーメッセージでの内部情報漏洩
- **安全でないデシリアライゼーション**: pickle、yaml.load 等の危険なパターン

公式参考: [Anthropic security-guidance plugin](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/security-guidance)

**構造整合性チェック（quality-auditor）**: コンポーネント間の「接続」が正しいかを検証する。Wave やタスクを跨いで構築されたコンポーネント（hooks, commands, skills, agents）間で、以下の整合性を確認する:

- **スキーマ整合性**: 状態ファイル（`lam-loop-state.json` 等）の書き手と読み手でフィールド名・型が一致しているか
- **参照整合性**: コマンドやスキルが参照するファイル・エージェントが実在するか、パスが正しいか
- **データフロー整合性**: hook 間の入出力チェーン（PreToolUse → ツール実行 → PostToolUse → Stop）でデータの受け渡しに断絶がないか
- **設定整合性**: `settings.json` の hooks 定義と実際のスクリプトパス・イベント名が一致しているか
- **ドキュメント間整合性**: 同一概念（スキーマ、フロー、等級定義等）が複数ファイルに記述されている場合、記述が一致しているか

## Phase 2: レポート統合 + PG/SE/PM 分類（v4.0.0）

1. 各エージェントの結果を統合
2. 重複 Issue を排除
3. 重要度分類: Critical / Warning / Info
4. **各 Issue を PG/SE/PM に分類**（権限等級に基づく）
5. 統合レポートをユーザーに提示し、修正方針の承認を得る

```
=== 監査統合レポート（イテレーション N） ===
Critical: X件 / Warning: X件 / Info: X件
PG: X件（自動修正可） / SE: X件（修正後報告） / PM: X件（承認必要）

[C-1] Critical [SE]: <内容> (file:line)
[W-1] Warning [PG]: <内容> (file:line)
...

修正に進みますか？（承認 / 一部除外 / 中止）
PM級の問題がある場合、ループを停止しユーザーに判断を委ねます。
```

## Phase 3: 全修正（audit-fix-policy）

承認後、権限等級に応じて修正:

- **PG級**: 自動修正（承認不要）— フォーマット、typo、lint 修正等
- **SE級**: 修正 + ログ記録 — テスト追加、内部リファクタリング等
- **PM級**: **ループ停止 + エスカレーション** — 仕様変更、アーキテクチャ変更等

共通ポリシー:
- **A-1**: 全重篤度（Critical / Warning / Info）に対応する
- **A-2**: 対応不可の Issue は理由 + 追跡先 + 暫定対策を明記
- **A-3**: 仕様ズレが発見された場合は `docs/specs/` も同時修正
- **A-4**: 修正は1件ずつ、テストが壊れないことを確認しながら進める

## Phase 4: 検証（Green State 判定）

全修正完了後、Green State 5条件を検証:

1. **G1**: テスト全パス（pytest / npm test 等）
2. **G2**: lint エラーゼロ（設定がある場合）
3. **G3**: Critical Issue ゼロ
4. **G4**: 修正した箇所の仕様書との整合性を再確認
5. **G5**: セキュリティチェック通過（依存脆弱性 + シークレットスキャン）

### G5 セキュリティチェックの詳細

| チェック項目 | ツール例 | 判定基準 |
|:---|:---|:---|
| 依存脆弱性 | `npm audit` / `pip audit` / `safety check` | Critical/High 脆弱性ゼロ |
| シークレット漏洩 | `grep` パターンマッチ | API キー・パスワード等のハードコードなし |
| 危険パターン | OWASP Top 10 チェック | eval/exec、SQL文字列結合、pickle.load 等なし |

ツールが未インストールの場合は PASS（スキップ）扱いとし、ログに記録する。
プロジェクトに Anthropic 公式 `security-guidance` plugin がインストールされている場合は、そちらの検出結果も考慮する。

### 差分チェックとフルスキャン

| サイクル | チェック範囲 | 目的 |
|---------|------------|------|
| 毎サイクル | **変更ファイルのみ**（Phase 3 で修正したファイル） | 修正による新規問題の検出、収束の加速 |
| 最終サイクル（Green State 達成後） | **対象全体のフルスキャン** | 修正の副作用が他のファイルに波及していないことを最終確認 |

**フルスキャンの発動手順**: 差分チェックで Green State を達成したら、`/full-review`（または lam-orchestrate）が状態ファイルに `fullscan_pending: true` をセットする:

```bash
# Phase 4 で差分チェック Green State 達成時に実行
# jq で fullscan_pending フラグをセット
jq '.fullscan_pending = true' .claude/lam-loop-state.json > /tmp/lam-tmp.json && mv /tmp/lam-tmp.json .claude/lam-loop-state.json
```

Stop hook がこのフラグを検出すると、もう1サイクル（フルスキャン）を実行する。フルスキャンでも Green State なら本当の停止となる。

フルスキャンの結果、新たな問題が発見された場合は Green State 未達とし、ループを継続する。

### 状態ファイル更新

Phase 4 完了時に `.claude/lam-loop-state.json` を更新する:
- `iteration` をインクリメント
- `log[]` に当該イテレーションの結果（issues_found, issues_fixed, pg/se/pm 件数）を追記

### ループ継続/停止の判定

**Green State 達成** → Phase 5 へ
**Green State 未達** → 「Green State 未達。残 Issue: X件」と応答して終了 → Stop hook が自動的に Phase 1 に戻す

## Phase 5: 完了報告 + ループログ出力

```
=== Full Review 完了 ===

イテレーション数: N
Before: Critical X / Warning X / Info X
After:  Critical 0 / Warning 0 / Info X（対応不可: X件）

修正ファイル: X件
テスト: PASSED (X tests)
lint: PASSED
Green State: 達成

対応不可 Issue:
- [I-3] <理由> → 追跡先: docs/tasks/xxx.md
```

Phase 5 完了時:
1. `.claude/lam-loop-state.json` を削除（ループ終了）
2. ループログを `.claude/logs/` に保存
