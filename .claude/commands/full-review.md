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
# 注: $TARGET と $TIMESTAMP はシェル変数。heredoc 内で展開される
cat > .claude/lam-loop-state.json << EOF
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
| `pm_pending` | boolean | PM級承認待ちフラグ（Phase 3 でセット、Stop hook で参照） | `/full-review` Phase 3 |
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

**自動ループの仕組み**: Phase 4 の検証で Green State 未達の場合、Claude の応答が終了すると Stop hook (`lam-stop-hook.py`) が発火し、状態ファイルを確認して自動的に Phase 1 に戻る。ユーザーの操作は不要。

## Phase 0.5: context7 MCP 検出

full-review 開始時に context7 MCP の利用可否を確認する。

- **利用可能**: 仕様確認（G4/G5）で context7 を使用
- **利用不可**: 以下の警告を表示し、仕様確認をスキップして処理を続行

```
⚠️ context7 MCP が未設定のため、仕様確認（G5）をスキップしました。
  最新仕様との整合性確認が必要な場合は、対話モードで
  /planning または upstream-first ルールを利用してください。
  （full-review 内での WebFetch は無応答リスクがあるため使用しません）
```

> WebFetch は対話モード（`/planning`, upstream-first）でのみフォールバックとして使用する。
> 自動フロー内での WebFetch は無応答・無限待機のリスクがあるため使用しない。

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
5. **統合レポートを `docs/artifacts/audit-reports/` に永続化**（ファイル名: `YYYY-MM-DD-iterN.md`）
6. 統合レポートをユーザーに提示し、修正方針の承認を得る

**レポート永続化**: 監査レポートはコンテキスト内だけでなく、必ずファイルに書き出す。セッション断絶時にも Issue が追跡可能であること。

```
=== 監査統合レポート（イテレーション N） ===
保存先: docs/artifacts/audit-reports/YYYY-MM-DD-iterN.md
Critical: X件 / Warning: X件 / Info: X件
PG: X件（自動修正可） / SE: X件（修正後報告） / PM: X件（承認必要）

[C-1] Critical [SE]: <内容> (file:line)
[W-1] Warning [PG]: <内容> (file:line)
...

修正に進みますか？（承認 / 一部除外 / 中止）
PM級の問題がある場合、PG/SE級を先に修正した後、PM級の修正案を提示してループを一時停止します。
```

## Phase 3: 全修正（audit-fix-policy）

承認後、権限等級に応じて修正:

- **PG級**: 自動修正（承認不要）— フォーマット、typo、lint 修正等
- **SE級**: 修正 + ログ記録 — テスト追加、内部リファクタリング等
- **PM級**: **ループ一時停止 + ユーザー判断待ち** — 仕様変更、アーキテクチャ変更等

### PM級の処理フロー

PM級の Issue が存在する場合、PG/SE級を先に修正した後、以下の手順でユーザーの判断を仰ぐ:

1. PG/SE級を通常通り修正
2. PM級の Issue 一覧と修正案をユーザーに提示
3. `pm_pending: true` を状態ファイルにセット
4. 応答を終了（Stop hook は `pm_pending=true` を検出し、block せずに停止を許可）
5. ユーザーが条件付き承認・修正指示・却下などを返答
6. 指示に従い PM級を修正
7. `pm_pending: false` を状態ファイルにセット + 応答終了
8. Stop hook が通常通り block → 次のサイクル（差分監査）へ

```bash
# PM級 Issue 発見時に実行
TMP_FILE=$(mktemp) && jq '.pm_pending = true' .claude/lam-loop-state.json > "${TMP_FILE}" && mv "${TMP_FILE}" .claude/lam-loop-state.json
```

```bash
# PM級修正完了後に実行
TMP_FILE=$(mktemp) && jq '.pm_pending = false' .claude/lam-loop-state.json > "${TMP_FILE}" && mv "${TMP_FILE}" .claude/lam-loop-state.json
```

共通ポリシー:
- **A-1**: 全重篤度（Critical / Warning / Info）に対応する。検出した Issue の defer（先送り）は禁止
- **A-2**: **スコープ外 Issue の扱い** — 以下の条件を**すべて**満たす場合のみ、当該イテレーションでの修正を免除できる:
  1. 依存先が未実装（別 Phase/Wave のスコープ）等、**技術的に着手不可能**であること
  2. 「コンテキスト不足」「工数が多い」「面倒」は理由にならない。コンテキスト逼迫時は `/quick-save` でセッション分割せよ
  3. スタブや暫定対策で塞げる場合はその場で実施すること
  4. 免除する場合は **理由 + 対象 Wave/Phase + 追跡 Issue（`docs/tasks/` に起票）** を明記
  5. 免除 Issue は完了報告に件数・一覧を含めること（黙って消えることを許さない）
- **A-3**: 仕様ズレが発見された場合は `docs/specs/` も同時修正
- **A-4**: 修正は1件ずつ、テストが壊れないことを確認しながら進める

## Phase 4: 検証（Green State 判定）

全修正完了後、Green State 5条件を検証:

1. **G1**: テスト全パス（pytest / npm test 等）
2. **G2**: lint エラーゼロ（設定がある場合）
3. **G3**: 対応可能 Issue ゼロ（PG/SE級は修正済み、PM級は理由付き保留済み）※完全実装
4. **G4**: 仕様差分ゼロ（docs/specs/ と実装の整合性確認）※完全実装
5. **G5**: セキュリティチェック通過（依存脆弱性 + シークレットスキャン）

### 真の Green State の定義

**Green State とは「スキャンして Issue がゼロ」の状態である。「修正後にゼロ」ではない。**

つまり、あるイテレーションで Issue を全件修正しても、それは Green State ではない。
次のイテレーションで再スキャンし、**Phase 1 の監査で新規 Issue が 0件** であって初めて Green State となる。

```
iter 1: 発見 37件 → 修正 37件 → ❌ まだ Green State ではない
iter 2: 発見 19件 → 修正 19件 → ❌ まだ Green State ではない
iter 3: 発見  0件 →             → ✅ Green State 達成
```

この原則により、修正の副作用で生まれた新たな問題が見逃されることを防ぐ。

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
TMP_FILE=$(mktemp) && jq '.fullscan_pending = true' .claude/lam-loop-state.json > "${TMP_FILE}" && mv "${TMP_FILE}" .claude/lam-loop-state.json
```

Stop hook がこのフラグを検出すると、もう1サイクル（フルスキャン）を実行する。フルスキャンでも Green State なら本当の停止となる。

フルスキャンの結果、新たな問題が発見された場合は Green State 未達とし、ループを継続する。

### 状態ファイル更新

Phase 4 完了時に `.claude/lam-loop-state.json` を更新する:
- `iteration` をインクリメント
- `log[]` に当該イテレーションの結果（issues_found, issues_fixed, pg/se/pm 件数）を追記

### ループ継続/停止の判定

**Phase 1 で Issue 0件（Before=0）** → Green State 達成 → Phase 5 へ
**Phase 1 で Issue 1件以上** → Phase 2〜4 を実行 → 「修正完了。再スキャンへ」と応答 → Stop hook が自動的に Phase 1 に戻す

## Phase 5: 完了報告 + ループログ出力

```
=== Full Review 完了 ===

イテレーション数: N（最終イテレーションの Before=0 で Green State 確定）
最終イテレーション: Before 0件（スキャンで Issue ゼロ = 真の Green State）
累計修正: Critical X / Warning X / Info X

修正ファイル: X件
テスト: PASSED (X tests)
lint: PASSED
Green State: 達成（Before=0 確認済み）

対応不可 Issue:
- [I-3] <理由> → 追跡先: docs/tasks/xxx.md
```

Phase 5 完了時:
1. `.claude/lam-loop-state.json` を削除（ループ終了）
2. ループログを `.claude/logs/` に保存

---

## 将来拡張: Scalable Review（モジュール分割レビュー）

大規模プロジェクト（数万行超）では、コンテキストウィンドウの制約により品質が低下する可能性がある。
その場合、以下のアプローチでモジュール単位の分割レビューを検討する。

```
/planning でレビュー計画書を作成
├── グループA: src/auth/       （認証モジュール）
├── グループB: src/api/        （APIエンドポイント）
├── グループC: src/models/     （データモデル）
└── グループD: src/utils/      （ユーティリティ）

→ 各グループを /full-review → 進捗記録 → 次のグループへ
→ 全グループ完了後に横断的な統合レビュー
```

### 検討事項

- **のりしろ**: モジュール間にまたがる問題は最終統合レビューで横断チェック
- **`/batch` スキル**: Claude Code ビルトインの `/batch` がworktree分離並列実行をサポートしており、参考になる
- **lam-orchestrate 連携**: lam-orchestrate の Wave 分割で小規模な分割レビューは現時点でも可能

### 参照

- 構想メモ: `docs/memos/2026-03-10-scalable-review-and-eval-ideas.md`
- 計画メモ: `docs/memos/2026-03-12-knowledge-layer-and-platform-alignment.md`
