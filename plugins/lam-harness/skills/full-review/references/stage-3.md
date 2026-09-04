## Stage 3: 階層的統合 + レポート生成

**実行条件**: 常に実行（Layer 2/3 は Plan C 以上の場合のみ。レポート統合は常に実行）
**Layer 2/3 実行条件**: `scale-detection.json` の `active_plans` に `"C"` が含まれる場合のみ Layer 2（モジュール統合）と Layer 3（システムレビュー）を実行。含まれない場合は Step 5（レポート統合）に直行する。
**入力**: `file-cards/`, `contracts/`（任意）, `ast-map.json` / `import-map.json`（**現状未生成・`{}` 縮退**。Stage 1 NOTE 参照 → Layer 3 の循環依存検出は実質 no-op）
**出力**: 統合レポート（`audit-reports/YYYY-MM-DD-iterN.md`）, `module-cards/`, `layer3-issues.json`

Stage 2 の並列監査完了後、Layer 2 → Layer 3 の順で逐次実行する。

### Step 1: Layer 2 — モジュール統合

> **⚠️ 現状 no-op（ast-map.json / import-map.json 未生成のため）— 2026-06-19 監査確認**: `ast-map.json` が未生成のため `ast_map` は常に `{}` に縮退し、`detect_module_boundaries([])` が空リストを処理して実質何もしない。Plan C（100K 行超）が有効化され、かつ `ast-map.json` 生成が実装された時点で機能する。（B-4 §3 方針 X 採用）

Stage 2 の概要カード生成（C-1a/C-1b）完了後、モジュール境界を検出し要約カードを生成する。

```bash
bash .claude/scripts/py_invoke.sh -c "
import sys, json; sys.path.insert(0, '.claude/hooks')
from analyzers.card_generator import (
    detect_module_boundaries, generate_module_cards, save_module_card
)
from analyzers.state_manager import load_chunks_index
from pathlib import Path

state_dir = Path('.claude/review-state')
# ast_map / import_map は現状未生成のため通常 {} に縮退する（W2-P2・Stage 1 NOTE 参照）
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
bash .claude/scripts/py_invoke.sh -c "
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

> **⚠️ 現状 no-op（ast-map.json / import-map.json 未生成のため）— 2026-06-19 監査確認**: `import-map.json` が未生成のため `import_map` は常に `{}` に縮退し、`detect_circular_dependencies({})` は常に空リストを返す。循環依存検出・命名違反検出ともに実質 0 件固定。Plan C（100K 行超）および `import-map.json` 生成実装後に機能する。（B-4 §3 方針 X 採用）

```bash
bash .claude/scripts/py_invoke.sh -c "
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
bash .claude/scripts/py_invoke.sh -c "
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
6. 修正方針の承認（`auto_approve` 状態により分岐）

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
```

**承認分岐（auto_approve）**:

- `auto_approve=false`（通常モード）: 上記レポートをユーザーに提示し、「修正に進みますか？（承認 / 一部除外 / 中止）」の確認を求める。PM級の問題がある場合、PG/SE級を先に修正した後、PM級の修正案を提示してループを一時停止する。
- `auto_approve=true`（サブエージェントモード）: 対話なしで Stage 4 の修正に直行する（PG/SE級のみ）。PM級 Issue がある場合は Step 5 とは別に Stage 4 Step 2 の `auto_approve` 分岐で処理する（後述）。

**帰責ヒントの表示ルール（FR-3a/FR-3b）**:
- `parse_blame_hint()` で抽出された帰責ヒントが存在する Issue には `** 帰責判断求む **` マーカーを付与する
- `→` 以降に `suspected_responsible` と `reason` を表示する
- 帰責ヒントがない Issue にはマーカーを付与しない
- 帰責ヒント付き Issue が 1 件以上ある場合のみ、レポート末尾に帰責サマリーテーブルを出力する

---

