## Stage 1: 静的分析 + 依存グラフ構築

**実行条件**: Stage 0 の Scale Detection で Plan A 以上が有効と判定された場合のみ実行。`scale-detection.json` の `active_plans` に `"A"` が含まれない場合は本 Stage をスキップし Stage 2 に直行する。
**入力**: 対象パス, `review-config.json`（任意）, `scale-detection.json`
**出力（現状）**: `static-issues.json`, `summary.md`

> **実装状況 NOTE（W2-P2 / 旧 W-6）**: `run_phase0()` が現状永続化するのは `static-issues.json` と
> `summary.md` の **2 ファイルのみ**。`ast-map.json` / `import-map.json` / `dependency-graph.json` は
> **未生成**（AST/import 抽出は `parse_ast` の Phase 1 簡易実装どまりで `save_import_map` 等の書き手が不在）。
> このため後続 Step 3（依存グラフ構築）および Stage 3 Layer 3（循環依存検出）はいずれも
> `.exists()` ガードで入力が `{}` に縮退し、**実質 no-op**（Plan D は無効・Plan A のみで動作）。
> 下記コードブロックは将来 AST/import-map 生成を実装した際にそのまま機能する前方互換の足場として残置する。

### Step 1: 静的解析実行

```bash
# 静的解析パイプラインを実行
bash .claude/scripts/py_invoke.sh -c "
import sys, json; sys.path.insert(0, '.claude/hooks')
from analyzers.run_pipeline import run_phase0
from _hook_utils import get_project_root

result = run_phase0(get_project_root())
print(f'Languages: {result.languages}')
print(f'Issues: {len(result.issues)}')
print(f'Lines: {result.line_count}')
print(f'Summary: {result.summary_path}')
"
```

> **NOTE**: `run_phase0` には監査対象パスではなく**常にプロジェクトルート**を渡すこと。
> `get_project_root()` は `LAM_PROJECT_ROOT` 環境変数（設定済みの場合）または
> `_hook_utils.py` の位置（`.claude/hooks/`）から 2 階層上を返すため、
> サブエージェント実行時の cwd 変動に影響されない。
> `Path('.').resolve()` は cwd 依存のため使用禁止（R-3 防止）。
> サブパスを渡すと `<サブパス>/.claude/review-state/` という誤った場所に永続化される。

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

> **⚠️ 現状 no-op（ast-map.json / import-map.json 未生成のため）— 2026-06-19 監査確認**: `run_phase0()` が `import-map.json` を生成しないため、本 Step の `import_map` は常に `{}` に縮退しスキップされる。`ast-map.json` / `import-map.json` 生成が実装された時点で有効化される。（B-4 §3 方針 X 採用）

`import-map.json` の import 情報から依存グラフを構築し、永続化する。
**現状は `import-map.json` が未生成のため import_map は `{}` に縮退し、本 Step はスキップされる**
（上記「実装状況 NOTE」参照）。AST/import-map 生成を実装した時点で有効化される。

```bash
bash .claude/scripts/py_invoke.sh -c "
import sys, json; sys.path.insert(0, '.claude/hooks')
from analyzers.card_generator import build_topo_order
from analyzers.state_manager import save_dependency_graph
from pathlib import Path

state_dir = Path('.claude/review-state')

# import-map.json は現状 run_phase0() が生成しないため、通常 import_map は {} に縮退する（W2-P2）
import_map_path = state_dir / 'import-map.json'
import_map = json.loads(import_map_path.read_text()) if import_map_path.exists() else {}

if import_map:
    result = build_topo_order(import_map)
    graph_data = {
        'topo_order': result.topo_order,
        'sccs': result.sccs,
        'node_to_file': result.node_to_file,
    }
    save_dependency_graph(state_dir, graph_data)
    print(f'Dependency graph: {len(result.topo_order)} nodes, {len(result.sccs)} SCCs')
else:
    print('No import map available; skipping dependency graph construction')
"
```

生成された `dependency-graph.json` は Stage 2（トポロジカル順レビュー）および Stage 4（トポロジカル順修正）で使用される。

Stage 1 完了後、Stage 2 に進む。

---

