---
description: "並列監査 + 全修正 + 検証の一気通貫レビュー"
---

# /full-review - 並列監査 + 全修正 + 自動ループ

引数: 対象ファイルまたはディレクトリ（必須）

## /auditing との使い分け

- `/auditing`: フェーズ切替。AUDITING モードに入り、手動で段階的に監査
- `/full-review`: ワンショット実行。並列監査 -> 修正 -> 検証を自動ループで完了

---

## Stage 0: 初期化

**実行条件**: 常に実行
**入力**: 対象パス（引数）
**出力**: `lam-loop-state.json`, `scale-detection.json`

### Step 1: ループ状態ファイル生成

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
| `fullscan_pending` | boolean | フルスキャン待ちフラグ（Stage 5 でセット、Claude が参照） | `/full-review` |
| `pm_pending` | boolean | PM級承認待ちフラグ（Stage 4 でセット、Claude/Stop hook が参照） | `/full-review` |
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
  /planning または upstream-first ルールを利用してください。
  （full-review 内での WebFetch は無応答リスクがあるため使用しません）
```

> WebFetch は対話モード（`/planning`, upstream-first）でのみフォールバックとして使用する。
> 自動フロー内での WebFetch は無応答・無限待機のリスクがあるため使用しない。

### Step 3: Scale Detection 判定（Plan E: FR-E2）

プロジェクト規模に応じて有効化する Plan セットを自動判定する。

```bash
python3 .claude/hooks/analyzers/scale_detector.py "$TARGET"
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

Stage 0 完了後、Stage 1 に進む（Plan A 以上の場合）。Plan セットが「なし」の場合は Stage 1 をスキップし Stage 2 に直行する。

---

## Stage 1: 静的分析 + 依存グラフ構築

**実行条件**: Stage 0 の Scale Detection で Plan A 以上が有効と判定された場合のみ実行。`scale-detection.json` の `active_plans` に `"A"` が含まれない場合は本 Stage をスキップし Stage 2 に直行する。
**入力**: 対象パス, `review-config.json`（任意）, `scale-detection.json`
**出力**: `static-issues.json`, `ast-map.json`, `import-map.json`, `dependency-graph.json`, `summary.md`

### Step 1: 静的解析実行

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

**注**: Stage 1 の実行可否は Stage 0 の Scale Detection（`scale-detection.json` の `active_plans`）で決定済み。本 Step に到達した時点で Plan A が有効であることが保証されている。

**NOTE: gitleaks シークレットスキャン** — `run_phase0()` 内で gitleaks によるシークレットスキャンが自動実行される（言語 Analyzer の後に実行）。

- gitleaks インストール済み: `gitleaks detect` でリポジトリ全体をスキャン。検出結果は Critical Issue として `static-issues.json` に含まれる
- gitleaks 未インストール: `rule_id="gitleaks:not-installed"` の Critical Issue が生成される。この Issue が存在する限り **G5 FAIL**（Green State 未達）となり、インストールガイドが表示される
- gitleaks 実行失敗: `rule_id="gitleaks:scan-failed"` の Critical Issue が生成される（G5 FAIL）
- 明示的無効化（`review-config.json` で `gitleaks_enabled: false`）: スキップ + INFO ログ（G5 PASS）

### Step 2: 静的解析結果の Stage 2 への接続

静的解析で Issue が検出された場合、Stage 2（並列監査）のエージェントに以下の追加コンテキストを提供する:
- `.claude/review-state/summary.md` の内容を各監査エージェントのプロンプトに含める
- 静的解析で既に検出済みの Issue は LLM が重複検出する必要がないことを伝える
- セキュリティ Issue は `code-reviewer`（セキュリティ）エージェントに優先的に渡す

### ツール未インストール時

静的解析ツール（ruff, bandit 等）が未インストールの場合は `ToolNotFoundError` が発生する。
エラーメッセージにインストール手順が表示されるため、ユーザーに案内して Stage 1 を中止する。
Stage 2 以降は静的解析なしで続行可能。

gitleaks が未インストールの場合は Stage 1 を中止せず、not-installed Issue を記録して続行する。
G5 チェック（Stage 5）でこの Issue が FAIL を引き起こす。

### Step 3: 依存グラフ構築（FR-7a）

Step 1 で生成された `ast-map.json` の import 情報から依存グラフを構築し、永続化する。

```bash
python3 -c "
import sys, json; sys.path.insert(0, '.claude/hooks')
from analyzers.card_generator import build_topo_order
from analyzers.state_manager import save_dependency_graph
from pathlib import Path

state_dir = Path('.claude/review-state')

# import-map.json は Stage 1 の run_phase0() が永続化済み
import_map_path = state_dir / 'import-map.json'
import_map = json.loads(import_map_path.read_text()) if import_map_path.exists() else {}

if import_map:
    result = build_topo_order(import_map)
    graph_data = {
        'topo_order': result['topo_order'],
        'sccs': result['sccs'],
        'node_to_file': result['node_to_file'],
    }
    save_dependency_graph(state_dir, graph_data)
    print(f'Dependency graph: {len(result[\"topo_order\"])} nodes, {len(result[\"sccs\"])} SCCs')
else:
    print('No import map available; skipping dependency graph construction')
"
```

生成された `dependency-graph.json` は Stage 2（トポロジカル順レビュー）および Stage 4（トポロジカル順修正）で使用される。

Stage 1 完了後、Stage 2 に進む。

---

## Stage 2: チャンク分割 + トポロジカル順レビュー

**実行条件**: 常に実行（チャンクモード/従来モードは Plan B の有無で分岐）
**チャンクモード判定**: `scale-detection.json` の `active_plans` に `"B"` が含まれ、かつ tree-sitter が利用可能な場合はチャンクモード。それ以外は従来のファイル全体レビュー。
**入力**: `ast-map.json`, `import-map.json`, `dependency-graph.json`（任意）, `static-issues.json`（任意）
**出力**: `file-cards/`, `contracts/`, `chunk-results/`（チャンクモード時）

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
- **利用不可** → 以下の Warning を表示し、Stage 2 では従来のファイル全体レビューにフォールバック

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

### Step 3: 並列監査

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

#### 概要カード責務フィールド + 契約カード（Stage 2 Agent 追加出力）

Stage 2 の各 Agent プロンプトに以下の指示を追加し、レビュー対象ファイルの責務と契約フィールドを出力させる:

```
レビュー結果の末尾に、以下のマーカーで囲んだ責務フィールドを出力してください。
対象ファイルが「何を担当するモジュールか」を1行で記述してください。

---FILE-CARD-RESPONSIBILITY---
[責務の1行サマリー]
---END-FILE-CARD-RESPONSIBILITY---

また、以下のマーカーで囲んだ契約フィールドも出力してください。
モジュールの前提条件・保証・副作用・不変条件を記述してください。

---CONTRACT-CARD---
preconditions: [前提条件1, 前提条件2]
postconditions: [保証1, 保証2]
side_effects: [副作用1]
invariants: [不変条件1]
---END-CONTRACT-CARD---
```

Agent 出力から:
- `parse_responsibility()` で責務フィールドを抽出し、`merge_responsibilities()` で概要カードにマージ
- `parse_contract()` で契約フィールドを抽出し、`merge_contracts()` でモジュール単位に集約
- `parse_blame_hint()` で帰責ヒントを抽出し、Issue ID と紐付けてレポート統合（Stage 3）に渡す
- マーカーがない場合は空文字/空辞書/空リストにフォールバック（Agent が出力し忘れた場合のロバスト性確保）

### Step 4: 概要カード + 契約カード生成

Stage 2 の全 Agent 完了後、以下のフローでカード群を生成する:

1. `generate_file_cards(ast_map, import_map, issues, chunk_issues)` で機械的フィールドのカードを生成
2. 各 Agent 出力から `parse_responsibility()` で責務を抽出し、ファイルパスをキーとする dict に集約
3. `merge_responsibilities(cards, responsibilities)` で責務をマージ
4. `save_file_card(state_dir, card)` で各カードを永続化
5. 各 Agent 出力から `parse_contract()` で契約フィールドを抽出
6. `merge_contracts(file_cards, contract_fields, ast_map, module_to_files)` でモジュール単位に契約カードを生成
7. `save_contract_card(state_dir, card)` で `review-state/contracts/` に永続化

### チャンクモード（Step 2 でチャンクが生成された場合）

Step 2 でチャンクが生成されている場合（`.claude/review-state/chunks.json` が存在）、
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
2. **依存グラフが存在する場合（Stage 4: Plan D）**: `order_chunks_by_topo(chunks, topo_order, node_to_file, sccs)` でチャンクをトポロジカル順にグループ化。グループ内は `batch_chunks()` で並列分割
3. **依存グラフがない場合**: 従来通り `batch_chunks(chunks, batch_size=max_parallel_agents)` でバッチ分割
4. グループ/バッチごとに:
   a. `build_review_prompt_with_contracts(chunk, upstream_contracts)` でレビュープロンプトを生成（上流の契約カードをコンテキストに注入）
   b. Agent ツールで `run_in_background=true` で並列起動
   c. 全 Agent 完了待ち
   d. 結果を `ReviewResult` に変換し `save_chunk_result()` で永続化
   e. Agent 出力から `parse_contract()` で契約フィールドを抽出し、下流グループのコンテキストに蓄積
5. エラー時: 最大 `agent_retry_count` 回リトライ。リトライ後も失敗は Warning 続行
6. 全バッチ完了後、`collect_results()` で統合
7. `deduplicate_issues()` で重複排除
8. `check_naming_consistency()` で命名規則チェック

**トポロジカル順レビューの流れ（FR-7b）**:

```
dependency-graph.json を読み込み
  ↓
topo_order: [A, B, scc_0, C]
  ↓
Step 1: A のチャンクをレビュー → 契約カード(A) を parse_contract() で抽出
Step 2: B のチャンクをレビュー（契約カード(A) を上流コンテキストに注入）→ 契約カード(B) 抽出
Step 3: scc_0 のチャンクをバッチレビュー（契約カード(A,B) を注入）→ 契約カード(scc_0) 抽出
Step 4: C のチャンクをレビュー（契約カード(A,B,scc_0) を注入）→ 契約カード(C) 抽出
  ↓
merge_contracts() でモジュール単位に集約 → save_contract_card() で永続化
```

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

---

## Stage 3: 階層的統合 + レポート生成

**実行条件**: 常に実行（Layer 2/3 は Plan C 以上の場合のみ。レポート統合は常に実行）
**Layer 2/3 実行条件**: `scale-detection.json` の `active_plans` に `"C"` が含まれる場合のみ Layer 2（モジュール統合）と Layer 3（システムレビュー）を実行。含まれない場合は Step 5（レポート統合）に直行する。
**入力**: `file-cards/`, `contracts/`（任意）, `ast-map.json`, `import-map.json`
**出力**: 統合レポート（`audit-reports/YYYY-MM-DD-iterN.md`）, `module-cards/`, `layer3-issues.json`

Stage 2 の並列監査完了後、Layer 2 → Layer 3 の順で逐次実行する。

### Step 1: Layer 2 — モジュール統合

Stage 2 の概要カード生成（C-1a/C-1b）完了後、モジュール境界を検出し要約カードを生成する。

```bash
python3 -c "
import sys, json; sys.path.insert(0, '.claude/hooks')
from analyzers.card_generator import (
    detect_module_boundaries, generate_module_cards, save_module_card
)
from analyzers.state_manager import load_chunks_index
from pathlib import Path

state_dir = Path('.claude/review-state')
# ast_map と import_map は Stage 1/2 で永続化済み
ast_map = json.loads((state_dir / 'ast-map.json').read_text()) if (state_dir / 'ast-map.json').exists() else {}
import_map = json.loads((state_dir / 'import-map.json').read_text()) if (state_dir / 'import-map.json').exists() else {}

root = Path('\$TARGET').resolve()
boundaries = detect_module_boundaries(list(ast_map.keys()))
# file_cards は Stage 2 で生成済み（cards/file-cards/ に永続化）
# generate_module_cards と save_module_card で要約カードを生成・保存
print(f'Modules: {len(boundaries)}')
"
```

### Step 2: 契約カード永続化（FR-7c）

Stage 2 のトポロジカル順レビュー中に `parse_contract()` でリアルタイム抽出された契約フィールドを、
モジュール単位に集約して永続化する。
（契約フィールドの抽出・注入自体は Stage 2 のチャンクモード内で実行済み。ここでは永続化のみ。）

```bash
python3 -c "
import sys, json; sys.path.insert(0, '.claude/hooks')
from analyzers.card_generator import (
    merge_contracts, save_contract_card, detect_module_boundaries,
    load_file_card
)
from analyzers.state_manager import load_ast_map
from pathlib import Path

state_dir = Path('.claude/review-state')
ast_map_data = load_ast_map(state_dir)

# file_cards を cards/file-cards/ から読み込み
# contract_fields は Stage 2 の Agent 出力から parse_contract() で抽出済み
# module_to_files は detect_module_boundaries() で取得

file_paths = list(ast_map_data.keys()) if ast_map_data else []
module_to_files = detect_module_boundaries(file_paths)

# contract_fields: {file_path: {preconditions: [...], ...}}
# → merge_contracts() でモジュール単位に集約
# → save_contract_card() で review-state/contracts/ に永続化
print(f'Modules for contracts: {len(module_to_files)}')
"
```

契約カードは `review-state/contracts/{module-name}.json` に永続化される。
次回再レビュー時のコンテキストとして利用可能。

### Step 3: Layer 3 — システムレビュー（機械的チェック）

```bash
python3 -c "
import sys, json; sys.path.insert(0, '.claude/hooks')
from analyzers.card_generator import (
    detect_circular_dependencies, detect_module_naming_violations
)
from pathlib import Path

state_dir = Path('.claude/review-state')
import_map = json.loads((state_dir / 'import-map.json').read_text()) if (state_dir / 'import-map.json').exists() else {}
ast_map = json.loads((state_dir / 'ast-map.json').read_text()) if (state_dir / 'ast-map.json').exists() else {}

circ_issues = detect_circular_dependencies(import_map)
naming_issues = detect_module_naming_violations(ast_map)
print(f'Circular dependencies: {len(circ_issues)}')
print(f'Naming violations: {len(naming_issues)}')

# Issue を review-state に永続化
all_issues = [{'file': i.file, 'line': i.line, 'severity': i.severity, 'category': i.category, 'tool': i.tool, 'message': i.message, 'rule_id': i.rule_id, 'suggestion': i.suggestion} for i in circ_issues + naming_issues]
(state_dir / 'layer3-issues.json').write_text(json.dumps(all_issues, indent=2, ensure_ascii=False))
"
```

### Step 4: Layer 3 — LLM 仕様ドリフト検出

```bash
python3 -c "
import sys; sys.path.insert(0, '.claude/hooks')
from analyzers.card_generator import collect_spec_drift_context
from pathlib import Path

context = collect_spec_drift_context(
    Path('.claude/review-state'),
    Path('docs/specs')
)
Path('.claude/review-state/spec-drift-context.md').write_text(context)
print(f'Context size: {len(context)} chars')
"
```

上記でコンテキストを永続化した後、Agent を起動して仕様ドリフトを検出する:

```
Agent(quality-auditor): 仕様ドリフト検出
  入力: .claude/review-state/spec-drift-context.md の内容
  指示: 「モジュール実装サマリー」と「仕様書」を比較し、
        仕様に記述されているが実装されていない機能、
        実装されているが仕様に記述されていない機能を
        Issue として報告してください。
  出力: Critical/Warning/Info ラベル付き Issue リスト
```

### Stage 3 の Issue 統合

Layer 2 の境界チェック Issue + Layer 3 の機械的チェック Issue + LLM 仕様ドリフト Issue を
Stage 5（レポート統合）に合流させる。

### Step 5: レポート統合 + PG/SE/PM 分類

1. 各エージェントの結果 + **Stage 3 の Issue** を統合
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
[W-3] Warning [SE]: <内容> (file:line)
      ** 帰責判断求む ** → downstream(Module Z): A の precondition に型チェック要求あり
...

=== 帰責判断が必要な Issue ===
（帰責ヒント付き Issue が 1 件以上の場合のみ出力）
| # | Issue | 帰責候補 | モジュール | 理由 |
|---|-------|---------|-----------|------|
| 1 | [W-3] | downstream | Module Z | A の precondition に型チェック要求あり |

上記 Issue は自動修正の対象外です。帰責判断後に修正方針を指示してください。
PM級の仕様明確化が必要な Issue: X件

修正に進みますか？（承認 / 一部除外 / 中止）
PM級の問題がある場合、PG/SE級を先に修正した後、PM級の修正案を提示してループを一時停止します。
```

**帰責ヒントの表示ルール（FR-3a/FR-3b）**:
- `parse_blame_hint()` で抽出された帰責ヒントが存在する Issue には `** 帰責判断求む **` マーカーを付与する
- `→` 以降に `suspected_responsible` と `reason` を表示する
- 帰責ヒントがない Issue にはマーカーを付与しない
- 帰責ヒント付き Issue が 1 件以上ある場合のみ、レポート末尾に帰責サマリーテーブルを出力する

---

## Stage 4: トポロジカル順修正

**実行条件**: 常に実行
**トポロジカル順修正**: `scale-detection.json` の `active_plans` に `"D"` が含まれ、かつ `dependency-graph.json` が存在する場合はトポロジカル順で修正。それ以外は重要度順で修正。
**入力**: 統合レポート, `dependency-graph.json`（任意）
**出力**: 修正済みコード

承認後、権限等級に応じて修正:

- **PG級**: 自動修正（承認不要）— フォーマット、typo、lint 修正等
- **SE級**: 修正 + ログ記録 — テスト追加、内部リファクタリング等
- **PM級**: **ループ一時停止 + ユーザー判断待ち** — 仕様変更、アーキテクチャ変更等

### Step 0: 帰責ヒント付き Issue のガード（FR-4）

修正開始前に、帰責ヒント付き Issue を以下のルールで振り分ける:

- `suspected_responsible` が `spec_ambiguity` → **自動修正しない**。PM級としてユーザーに提示
- `suspected_responsible` が `upstream` または `downstream` → 帰責ヒントを添えてユーザーに修正方針の確認を求める。ただし `.claude/rules/permission-levels.md` の PG 級に該当する修正（フォーマット、typo、lint 違反等）は帰責ヒントに関わらず自動修正可
- `suspected_responsible` が `unknown` または帰責ヒントなし → 従来通りの重要度ベース修正

帰責判断の詳細フローチャートは `.claude/rules/code-quality-guideline.md` の「モジュール間帰責判断」セクションを参照。

### Step 1: PG/SE 級修正（トポロジカル順）

依存グラフが存在する場合（`dependency-graph.json`）、修正順序をトポロジカル順にする:
- `order_files_by_topo(file_paths, topo_order, node_to_file)` で修正対象ファイルをソート
- 上流モジュールから修正し、下流への波及を最小化する
- 依存グラフがない場合は従来通り Issue 重要度順で修正

### Step 2: PM 級処理フロー

PM級の Issue が存在する場合、PG/SE級を先に修正した後、以下の手順でユーザーの判断を仰ぐ:

1. PG/SE級を通常通り修正
2. PM級の Issue 一覧と修正案をユーザーに提示
3. `pm_pending: true` を状態ファイルにセット
4. 応答を終了（Stop hook は `pm_pending=true` を検出し、block せずに停止を許可）
5. ユーザーが条件付き承認・修正指示・却下などを返答
6. 指示に従い PM級を修正
7. `pm_pending: false` を状態ファイルにセット + 応答終了
8. Claude が応答を再開し、Stage 2 に戻って再監査

```bash
# PM級 Issue 発見時に実行
python3 -c "import json,pathlib;p=pathlib.Path('.claude/lam-loop-state.json');d=json.loads(p.read_text());d['pm_pending']=True;p.write_text(json.dumps(d,indent=2,ensure_ascii=False))"
```

```bash
# PM級修正完了後に実行
python3 -c "import json,pathlib;p=pathlib.Path('.claude/lam-loop-state.json');d=json.loads(p.read_text());d['pm_pending']=False;p.write_text(json.dumps(d,indent=2,ensure_ascii=False))"
```

共通ポリシー:
- **A-1**: Critical / Warning に対応する。Info は参考情報であり修正不要（`code-quality-guideline.md` 準拠）。Critical/Warning の defer（先送り）は原則禁止（PM級 Warning のみ理由付き deferred を許可）
- **A-2**: **スコープ外 Issue の扱い** — 以下の条件を**すべて**満たす場合のみ、当該イテレーションでの修正を免除できる:
  1. 依存先が未実装（別 Phase/Wave のスコープ）等、**技術的に着手不可能**であること
  2. 「コンテキスト不足」「工数が多い」「面倒」は理由にならない。コンテキスト逼迫時は `/quick-save` でセッション分割せよ
  3. スタブや暫定対策で塞げる場合はその場で実施すること
  4. 免除する場合は **理由 + 対象 Wave/Phase + 追跡 Issue（`docs/tasks/` に起票）** を明記
  5. 免除 Issue は完了報告に件数・一覧を含めること（黙って消えることを許さない）
- **A-3**: 仕様ズレが発見された場合は `docs/specs/` も同時修正
- **A-4**: 修正は1件ずつ、テストが壊れないことを確認しながら進める

---

## Stage 5: 検証 + Green State 判定 + 完了

**実行条件**: 常に実行
**入力**: テスト結果, lint 結果, `lam-loop-state.json`
**出力**: Green State 判定, ループログ（`logs/`）

### Step 1: G1〜G5 チェック

全修正完了後、Green State 5条件を検証:

1. **G1**: テスト全パス（pytest / npm test 等）
2. **G2**: lint エラーゼロ（設定がある場合）
3. **G3**: 対応可能 Issue ゼロ（PG/SE級は修正済み、PM級は理由付き保留済み）※完全実装
4. **G4**: 仕様差分ゼロ（docs/specs/ と実装の整合性確認）※完全実装
5. **G5**: セキュリティチェック通過（依存脆弱性 + シークレットスキャン）

#### 真の Green State の定義

**Green State とは「スキャンして Issue がゼロ」の状態である。「修正後にゼロ」ではない。**

つまり、あるイテレーションで Issue を全件修正しても、それは Green State ではない。
次のイテレーションで再スキャンし、**Stage 2 の監査で新規 Issue が 0件** であって初めて Green State となる。

```
iter 1: 発見 37件 → 修正 37件 → ❌ まだ Green State ではない
iter 2: 発見 19件 → 修正 19件 → ❌ まだ Green State ではない
iter 3: 発見  0件 →             → ✅ Green State 達成
```

この原則により、修正の副作用で生まれた新たな問題が見逃されることを防ぐ。

#### G5 セキュリティチェックの詳細

| チェック項目 | ツール | 判定基準 |
|:---|:---|:---|
| 依存脆弱性 | `npm audit` / `pip audit` / `safety check` | Critical/High 脆弱性ゼロ |
| シークレット漏洩 | **gitleaks**（Stage 1 Step 1.5 で実行済み） | gitleaks Issue ゼロ（`gitleaks:not-installed` 含む） |
| 危険パターン | OWASP Top 10 チェック | eval/exec、SQL文字列結合、pickle.load 等なし |

**gitleaks 未インストール時の G5 判定**: `gitleaks:not-installed` Issue は Critical として扱われるため、**G5 は FAIL** となる。gitleaks をインストールして再実行すれば解消される。インストールガイドは Stage 1 Step 1.5 のログに表示される。

依存脆弱性・危険パターンのツールが未インストールの場合は PASS（スキップ）扱いとし、ログに記録する。
プロジェクトに Anthropic 公式 `security-guidance` plugin がインストールされている場合は、そちらの検出結果も考慮する。

### Step 2: 影響範囲分析（FR-7d）

再レビュー時に `analyze_impact()` で影響範囲を計算し、`classify_impact_for_cards()` で概要カードの再利用判定を行う。
影響範囲外のファイルの概要カード機械的フィールドはハッシュ未変更なら再利用可能。

#### 再レビューループでの Stage 3 再実行（C-3b）

修正後の再スキャン時、Stage 3 も含めて全 Layer をゼロベースで再実行する:

- **概要カード・要約カードも再生成する**（キャッシュしない）
- Layer 2 の境界チェック、Layer 3 の循環依存・命名・仕様ドリフトも毎回再実行
- 静的解析（Stage 1）は変更ファイルのみ再実行（キャッシュ利用）

```
再スキャンフロー:
Stage 1（静的解析: 変更ファイルのみ）
  → Stage 2（チャンク分割: 再実行）
  → Stage 2（並列監査: ゼロベース全体）
  → Stage 3（階層的レビュー: Layer 2→3 全再実行）
  → Stage 4〜5（統合・修正・検証）
```

#### 監査範囲と検証範囲

| ステージ | 範囲 | 目的 |
|---------|------|------|
| Stage 2（監査） | **毎回、対象全体をゼロベース** | 修正の副作用、他エラーに隠れていた問題を発見 |
| Stage 3（階層的レビュー） | **毎回、全 Layer をゼロベース** | カード再生成、構造問題の再検出 |
| Stage 5（テスト・lint） | 変更ファイル中心（最終サイクルで全体） | テスト実行コストの最適化 |

### Step 3: ループ継続/停止判定

**フルスキャンの発動手順**: 差分チェックで Green State を達成したら、Claude が状態ファイルに `fullscan_pending: true` をセットし、自分で Stage 2 に戻る:

```bash
# 差分チェック Green State 達成時に実行
python3 -c "import json,pathlib;p=pathlib.Path('.claude/lam-loop-state.json');d=json.loads(p.read_text());d['fullscan_pending']=True;p.write_text(json.dumps(d,indent=2,ensure_ascii=False))"
```

Claude が `fullscan_pending=true` を確認し、もう1サイクル（フルスキャン）を Stage 2 から実行する。フルスキャンでも Green State なら Step 4（完了報告）に進む。

#### 状態ファイル更新

Stage 4 完了時に `.claude/lam-loop-state.json` を更新する:
- `iteration` をインクリメント
- `log[]` に当該イテレーションの結果（issues_found, issues_fixed, pg/se/pm 件数）を追記

#### ループ継続/停止の判定（Claude 側で制御）

**重要**: ループは Claude が自分で制御する。応答を終了せずに Stage 2 に戻ること。

**絶対ルール: Before=0 を確認するまで終了してはならない。**
修正後に Issue 0件になっても、それは Green State ではない。
次のイテレーションで再スキャン（Stage 2）し、**スキャン結果が 0件** であって初めて Green State となる。

```
Stage 2 + 3（再スキャン: 全 Layer）
  ├── Issue 0件（Before=0、全 Layer 含む）→ ✅ Green State 達成 → Stage 5（完了報告）へ
  └── Issue 1件以上 → Stage 4〜5（修正）→ Stage 2 に戻る（応答を継続）

例外（応答を終了してよいケース）:
  ├── max_iterations 到達 → Stage 5（完了報告）へ
  └── PM級 Issue あり → PG/SE 修正後、PM級を提示して応答を終了（ユーザー判断待ち）
```

**禁止**: 修正完了をもって Green State と見なすこと。必ず再スキャンで Before=0 を確認すること。

### Step 4: 完了報告 + ループログ出力

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

- Stage 1（静的解析パイプライン）: Scalable Code Review Stage 1 として実装済み（Plan A）
- Stage 2 Step 1-2（AST チャンキング）: Scalable Code Review Stage 2 Step 1-2 として実装済み（Plan B）
- Stage 2 Step 3（チャンクモード並列監査）: Scalable Code Review Stage 2 Step 3 として実装済み（Plan B）
- Stage 3（階層的レビュー）: Scalable Code Review Stage 3 として実装済み（Plan C: C-2b/C-3a/C-3b）
- Stage 2 トポロジカル順レビュー + 契約カード注入: Scalable Code Review Stage 2 として実装済み（Plan D: D-2/D-3）
- Stage 4 トポロジカル順修正: Scalable Code Review Stage 4 として実装済み（Plan D: D-3）
- Stage 0 Scale Detection: Scalable Code Review Stage 0 として実装済み（Plan E: E-1b）
- Stage 5 影響範囲分析（ハイブリッド統合）は Plan E で実装予定

- 要件仕様: `docs/specs/scalable-code-review-spec.md`
- 設計書: `docs/design/scalable-code-review-design.md`
- タスク: `docs/tasks/scalable-code-review-tasks.md`
- 構想メモ: `docs/memos/2026-03-10-scalable-review-and-eval-ideas.md`
