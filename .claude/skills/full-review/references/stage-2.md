## Stage 2: チャンク分割 + トポロジカル順レビュー

**実行条件**: 常に実行（チャンクモード/従来モードは Plan B の有無で分岐）
**チャンクモード判定**: `scale-detection.json` の `active_plans` に `"B"` が含まれ、かつ tree-sitter が利用可能な場合はチャンクモード。それ以外は従来のファイル全体レビュー。
**入力**: `static-issues.json`（任意）, `ast-map.json` / `import-map.json` / `dependency-graph.json`（**いずれも現状未生成・`{}` 縮退**。Stage 1 NOTE 参照）
**出力**: `file-cards/`, `contracts/`, `chunk-results/`（チャンクモード時）

### Step 1: tree-sitter 利用可否チェック

> **⚠️ 現状 no-op（ast-map.json / import-map.json 未生成のため）— 2026-06-19 監査確認**: 現環境では tree-sitter が未インストールのため、本 Step は常に「利用不可」判定となり、Step 2（チャンク分割）とともに従来モードにフォールバックする。実質 19 Run 中 0 回のチャンクモード機能。tree-sitter インストール後、かつ Plan B（30K 行超）が有効化された時点で機能する。（B-4 §3 方針 X 採用）

```bash
bash .claude/scripts/py_invoke.sh -c "
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
bash .claude/scripts/py_invoke.sh -c "
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
再監査ループで Critical・契約違反・セキュリティ系 Issue が 2 巡連続ゼロの場合は、縮小構成（SRC+SEC 統合 / TEST 統合 / QA の 3 体）への移行を推奨する。Warning 判定は「新系統 Critical 級・契約違反・具体的攻撃シナリオ・guideline 閾値の明確な超過」に限定する。（B-2 retro 反映）

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

#### rubric 要約注入（B-4）

`lam-loop-state.json` の `rubric_path` が空でない場合、Agent プロンプト構築前に以下の手順で rubric 内容を読み込み、各 Agent プロンプトの末尾に注入する。`rubric_path` が空文字または未設定の場合はこの手順をスキップし、Agent プロンプトは従来通り（後方互換）。

```bash
# rubric_path を lam-loop-state.json から取得（1行 py_invoke.sh -c を使用）
RUBRIC_PATH=$(bash .claude/scripts/py_invoke.sh -c "import json,sys; d=json.load(open('.claude/lam-loop-state.json')); print(d.get('rubric_path',''))")
```

`RUBRIC_PATH` が非空の場合、rubric ファイルの先頭 200 行を読み込んで `RUBRIC_CONTENT` に格納し、各 Agent プロンプトの末尾に以下のセクションを追記する（既存プロンプト本文は破壊しない・追記のみ）:

```
---RUBRIC-CONTEXT---
以下はゴール条件 rubric です。レビュー時にこれらの条件を観点に加えてください。
rubric への合否判定（G6）は別の grader が担当するため、本 Agent は rubric 観点でのコメントを
Issue リストに含めれば十分です（rubric 不適合は Warning 相当として扱う）。

[RUBRIC_CONTENT の内容をここに挿入]
---END-RUBRIC-CONTEXT---
```

### Step 4: 概要カード + 契約カード生成

Stage 2 の全 Agent 完了後、以下のフローでカード群を生成する:

1. `generate_file_cards(ast_map, import_map, issues, chunk_issues)` で機械的フィールドのカードを生成
2. 各 Agent 出力から `parse_responsibility()` で責務を抽出し、ファイルパスをキーとする dict に集約
3. `merge_responsibilities(cards, responsibilities)` で責務をマージ
4. `save_file_card(state_dir, card)` で各カードを永続化
5. 各 Agent 出力から `parse_contract()` で契約フィールドを抽出
6. `merge_contracts(file_cards, contract_fields, module_to_files, ast_map)` でモジュール単位に契約カードを生成
7. `save_contract_card(state_dir, card)` で `review-state/contracts/` に永続化

### チャンクモード（Step 2 でチャンクが生成された場合）

Step 2 でチャンクが生成されている場合（`.claude/review-state/chunks.json` が存在）、
従来のファイル全体レビューに代えて、チャンク単位で Agent を起動する。

```bash
# チャンク一覧を読み込み
bash .claude/scripts/py_invoke.sh -c "
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

**前巡査定記録の注入**: 2回目以降の監査プロンプトには、前巡までの Info 降格・棄却記録（監査レポートの査定メモ）を「再指摘不要リスト」として注入し、同一ボーダーライン指摘の再出を抑制する。（B-2 retro 反映）

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

