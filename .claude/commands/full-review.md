---
description: "並列監査 + 全修正 + 検証の一気通貫レビュー"
---

# /full-review - 並列監査 + 全修正 + 自動ループ

引数: 対象ファイルまたはディレクトリ（必須）

## /auditing との使い分け

- `/auditing`: フェーズ切替。AUDITING モードに入り、手動で段階的に監査
- `/full-review`: ワンショット実行。並列監査 -> 修正 -> 検証を自動ループで完了

## Phase 0: 静的解析パイプライン（Scalable Code Review）

プロジェクトの行数に基づき、静的解析パイプラインの実行を判定する。

### Step 1: 行数カウントと有効化判定

```bash
# 行数カウントと有効化判定を実行
python3 -c "
import sys; sys.path.insert(0, '.claude/hooks')
from analyzers.run_pipeline import count_lines, should_enable_static_analysis
from analyzers.config import ReviewConfig
from pathlib import Path

root = Path('$TARGET').resolve()
config = ReviewConfig.load(root)
lines = count_lines(root, config.exclude_dirs)
level = should_enable_static_analysis(lines, config.auto_enable_threshold)
print(f'Lines: {lines}')
print(f'Level: {level}')
"
```

| 行数 | 判定 | 動作 |
|------|------|------|
| ~10K | `skip` | Phase 0 をスキップし Phase 1 に直行（現行動作と同一、NFR-2） |
| 10K-30K | `suggest` | ユーザーに静的解析の実行を提案。承認されれば Step 2 へ |
| 30K~ | `auto` | 自動的に Step 2 を実行 |

### Step 2: 静的解析実行

```bash
# 静的解析パイプラインを実行
python3 -c "
import sys, json; sys.path.insert(0, '.claude/hooks')
from analyzers.run_pipeline import run_phase0
from pathlib import Path

result = run_phase0(Path('$TARGET').resolve())
print(f'Languages: {result.languages}')
print(f'Issues: {len(result.issues)}')
print(f'Lines: {result.line_count}')
print(f'Summary: {result.summary_path}')
"
```

実行結果:
- `.claude/review-state/static-issues.json` に Issue リストを永続化
- `.claude/review-state/summary.md` に LLM 向けサマリーを生成
- サマリーは NFR-4（Lost in the Middle 対策）に従い Critical を先頭、カウントを末尾に配置

### Step 3: 静的解析結果の Phase 2 への接続

静的解析で Issue が検出された場合、Phase 2（並列監査）のエージェントに以下の追加コンテキストを提供する:
- `.claude/review-state/summary.md` の内容を各監査エージェントのプロンプトに含める
- 静的解析で既に検出済みの Issue は LLM が重複検出する必要がないことを伝える
- セキュリティ Issue は `code-reviewer`（セキュリティ）エージェントに優先的に渡す

### ツール未インストール時

静的解析ツール（ruff, bandit 等）が未インストールの場合は `ToolNotFoundError` が発生する。
エラーメッセージにインストール手順が表示されるため、ユーザーに案内して Phase 0 を中止する。
Phase 1 以降は静的解析なしで続行可能。

Phase 0 完了後、Phase 1 に進む。

---

## Phase 1: ループ初期化（v4.0.0）

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

**追加フィールド**:

| フィールド | 型 | 説明 | 管理者 |
|-----------|---|------|--------|
| `fullscan_pending` | boolean | フルスキャン待ちフラグ（Phase 5 でセット、Claude が参照） | `/full-review` |
| `pm_pending` | boolean | PM級承認待ちフラグ（Phase 4 でセット、Claude/Stop hook が参照） | `/full-review` |
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

Phase 1 完了後、Phase 1.5 に進む。

**ループ制御の仕組み**: ループは Claude（本スキル）が Phase 5 完了後に自分で Phase 2 に戻ることで実現する。
Stop hook はアクティブなループが存在する限り block するが、あくまで安全ネットであり、ループの主制御には使わない。
`stop_hook_active=true` の再帰防止により Stop hook 自身が再帰的に呼ばれることはない。
Green State 判定、イテレーション管理、状態ファイル削除は全て Claude 側の責務。

## Phase 1.5: context7 MCP 検出

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

## Phase 1.7: AST チャンキング（Scalable Code Review Phase 2）

tree-sitter を用いて対象ファイルを構文的に妥当なチャンクに分割する。
30K 行以上のプロジェクトで自動有効化される（Phase 0 で行数カウント済み）。

### Step 1: tree-sitter 利用可否チェック

```bash
python3 -c "
import sys; sys.path.insert(0, '.claude/hooks')
from analyzers.chunker import chunk_file, TreeSitterNotAvailable
try:
    chunk_file('x = 1', 'test.py')
    print('tree-sitter: available')
except TreeSitterNotAvailable:
    print('tree-sitter: not available')
"
```

- **利用可能** → Step 2 へ
- **利用不可** → 以下の Warning を表示し、Phase 2 は従来のファイル全体レビューにフォールバック

```
⚠️ tree-sitter が未インストールのため、AST チャンキングをスキップします。
  大規模プロジェクトではチャンク分割によるレビュー精度向上が期待できます。
  インストール: pip install tree-sitter tree-sitter-python
```

### Step 2: 全対象ファイルをチャンク分割

```bash
python3 -c "
import sys, json; sys.path.insert(0, '.claude/hooks')
from analyzers.chunker import chunk_file
from analyzers.state_manager import save_chunks_index
from analyzers.config import ReviewConfig
from pathlib import Path

root = Path('$TARGET').resolve()
config = ReviewConfig.load(root)
chunks = []
for py_file in root.rglob('*.py'):
    rel = str(py_file.relative_to(root))
    if any(d in rel.split('/') for d in config.exclude_dirs):
        continue
    source = py_file.read_text(encoding='utf-8', errors='ignore')
    chunks.extend(chunk_file(source, rel, config.chunk_size_tokens, config.overlap_ratio))

save_chunks_index(Path('.claude/review-state'), chunks)
print(f'Chunks: {len(chunks)}')
for c in chunks[:5]:
    print(f'  {c.file_path}:{c.start_line}-{c.end_line} ({c.level}) {c.node_name} [{c.token_count} tokens]')
if len(chunks) > 5:
    print(f'  ... and {len(chunks) - 5} more')
"
```

チャンク一覧は `.claude/review-state/chunks.json` に永続化される。

### Step 3: Phase 2 への接続

チャンクが存在する場合、Phase 2 ではチャンク単位で Agent を起動する（後述）。
チャンクが 0 件の場合は従来のファイル全体レビューにフォールバックする。

Phase 1.7 完了後、Phase 2 に進む。

---

## Phase 2: 並列監査

対象に対して以下のサブエージェントを並列起動:

| エージェント | 観点 | 出力要件 |
|-------------|------|---------|
| `code-reviewer` (1) | ソースコード品質（命名、構造、エラー処理） | 各 Issue に PG/SE/PM 分類を付与 |
| `code-reviewer` (2) | テストコード品質（網羅性、可読性、テストパターン） | 各 Issue に PG/SE/PM 分類を付与 |
| `quality-auditor` | アーキテクチャ・仕様整合性（依存関係、**仕様ドリフト**、**構造整合性**） | 仕様ドリフト + 構造整合性結果を含む |
| `code-reviewer` (3) | セキュリティ（OWASP Top 10、シークレット漏洩、依存脆弱性、インジェクション） | 各 Issue にリスクレベル (Critical/High/Medium/Low) + PG/SE/PM 分類を付与 |

**セキュリティチェックリスト（統合済み）**:
- [ ] 入力値検証（Input Validation）
- [ ] 認証・認可（Authentication/Authorization）
- [ ] SQL/NoSQL/コマンドインジェクション対策
- [ ] XSS/CSRF 対策
- [ ] シークレット管理（ハードコードされていないか）
- [ ] ログ出力（機密情報が含まれていないか）
- [ ] エラーハンドリング（情報漏洩リスク）

セキュリティリスクと権限等級の対応:

| リスクレベル | 権限等級 | 対応 |
|-------------|---------|------|
| Critical/High | PM | 即時報告、承認ゲート |
| Medium | SE | 修正後報告 |
| Low | PG | 自動修正可 |

プロジェクト規模に応じてエージェント構成を調整可能。
小規模の場合は `code-reviewer` x1 + `quality-auditor` x1 でもよい（ただしセキュリティ観点は省略しないこと）。

各エージェントは独立した監査レポートを生成する。

### チャンクモード（Phase 1.7 でチャンクが生成された場合）

Phase 1.7 でチャンクが生成されている場合（`.claude/review-state/chunks.json` が存在）、
従来のファイル全体レビューに代えて、チャンク単位で Agent を起動する。

```bash
# チャンク一覧を読み込み
python3 -c "
import sys, json; sys.path.insert(0, '.claude/hooks')
from analyzers.state_manager import load_chunks_index
from analyzers.orchestrator import batch_chunks
from analyzers.chunker import Chunk
from pathlib import Path

index = load_chunks_index(Path('.claude/review-state'))
print(f'Total chunks: {len(index)}')
# バッチ分割（デフォルト 4 並列）
# batch_chunks は Chunk オブジェクトを受け取るが、ここでは件数確認のみ
print(f'Batches: {(len(index) + 3) // 4}')
"
```

**バッチ並列実行手順**:

1. `.claude/review-state/chunks.json` からチャンク一覧を読み込む
2. `batch_chunks(chunks, batch_size=max_parallel_agents)` でバッチ分割
3. バッチごとに:
   a. `build_review_prompt(chunk)` で各チャンクのレビュープロンプトを生成
   b. Agent ツールで `run_in_background=true` で並列起動
   c. 全 Agent 完了待ち
   d. 結果を `ReviewResult` に変換し `save_chunk_result()` で永続化
4. エラー時: 最大 `agent_retry_count` 回リトライ。リトライ後も失敗は Warning 続行
5. 全バッチ完了後、`collect_results()` で統合
6. `deduplicate_issues()` で重複排除
7. `check_naming_consistency()` で命名規則チェック

チャンクモードでも、セキュリティ・仕様ドリフト・構造整合性チェックは通常通り実施する。
チャンクなし（従来モード）の場合は上記をスキップし、従来通りファイル全体で Agent を起動する。

**イテレーション2回目以降もゼロベース全ファイル監査**: 2回目以降のサイクルでも、対象の全ファイルをゼロベースで監査する。前回の指摘事項の修正確認に偏ってはならない。理由: (1) 修正の副作用で新たな不整合が生じうる、(2) 他のエラーが消えたことで初めて浮かび上がるエラーがある、(3) 前回と同じ検証ポイントだけを見ると視野が狭まる。監査エージェントには「前回の指摘を確認せよ」ではなく「全ファイルを読み、全観点で監査せよ」と指示すること。

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

## Phase 3: レポート統合 + PG/SE/PM 分類（v4.0.0）

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

## Phase 4: 全修正（audit-fix-policy）

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
8. Claude が応答を再開し、Phase 2 に戻って再監査

```bash
# PM級 Issue 発見時に実行
python3 -c "import json,pathlib;p=pathlib.Path('.claude/lam-loop-state.json');d=json.loads(p.read_text());d['pm_pending']=True;p.write_text(json.dumps(d,indent=2,ensure_ascii=False))"
```

```bash
# PM級修正完了後に実行
python3 -c "import json,pathlib;p=pathlib.Path('.claude/lam-loop-state.json');d=json.loads(p.read_text());d['pm_pending']=False;p.write_text(json.dumps(d,indent=2,ensure_ascii=False))"
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

## Phase 5: 検証（Green State 判定）

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

### 監査範囲と検証範囲

| フェーズ | 範囲 | 目的 |
|---------|------|------|
| Phase 2（監査） | **毎回、対象全体をゼロベース** | 修正の副作用、他エラーに隠れていた問題を発見 |
| Phase 5（テスト・lint） | 変更ファイル中心（最終サイクルで全体） | テスト実行コストの最適化 |

**フルスキャンの発動手順**: 差分チェックで Green State を達成したら、Claude が状態ファイルに `fullscan_pending: true` をセットし、自分で Phase 2 に戻る:

```bash
# 差分チェック Green State 達成時に実行
python3 -c "import json,pathlib;p=pathlib.Path('.claude/lam-loop-state.json');d=json.loads(p.read_text());d['fullscan_pending']=True;p.write_text(json.dumps(d,indent=2,ensure_ascii=False))"
```

Claude が `fullscan_pending=true` を確認し、もう1サイクル（フルスキャン）を Phase 2 から実行する。フルスキャンでも Green State なら Phase 6 に進む。

### 状態ファイル更新

Phase 4 完了時に `.claude/lam-loop-state.json` を更新する:
- `iteration` をインクリメント
- `log[]` に当該イテレーションの結果（issues_found, issues_fixed, pg/se/pm 件数）を追記

### ループ継続/停止の判定（Claude 側で制御）

**重要**: ループは Claude が自分で制御する。応答を終了せずに Phase 2 に戻ること。

**絶対ルール: Before=0 を確認するまで終了してはならない。**
修正後に Issue 0件になっても、それは Green State ではない。
次のイテレーションで再スキャン（Phase 2）し、**スキャン結果が 0件** であって初めて Green State となる。

```
Phase 2（再スキャン）
  ├── Issue 0件（Before=0）→ ✅ Green State 達成 → Phase 6 へ
  └── Issue 1件以上 → Phase 3〜5（修正）→ Phase 2 に戻る（応答を継続）

例外（応答を終了してよいケース）:
  ├── max_iterations 到達 → Phase 6 へ（未達で終了）
  └── PM級 Issue あり → PG/SE 修正後、PM級を提示して応答を終了（ユーザー判断待ち）
```

**禁止**: 修正完了をもって Green State と見なすこと。必ず再スキャンで Before=0 を確認すること。

## Phase 6: 完了報告 + ループログ出力

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

Green State 確定後（Claude が実行）:
1. `.claude/lam-loop-state.json` を削除（ループ終了）
2. ループログを `.claude/logs/` に保存

---

## 参照: Scalable Code Review

- Phase 0（静的解析パイプライン）: Scalable Code Review Phase 1 として実装済み
- Phase 1.7（AST チャンキング）: Scalable Code Review Phase 2 として実装済み
- Phase 2（チャンクモード並列監査）: Scalable Code Review Phase 2 として実装済み
- Phase 3 以降（階層的レビュー、依存グラフ駆動）は将来の Phase で実装予定

- 要件仕様: `docs/specs/scalable-code-review-spec.md`
- 設計書: `docs/design/scalable-code-review-design.md`
- タスク: `docs/tasks/scalable-code-review-tasks.md`
- 構想メモ: `docs/memos/2026-03-10-scalable-review-and-eval-ideas.md`
