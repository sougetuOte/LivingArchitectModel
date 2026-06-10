# card_generator.py 分割（⑤）への繰越 Issue

**起票日**: 2026-06-02
**起票元**: full-review iter1（`docs/artifacts/audit-reports/2026-06-02-iter1.md`）
**権限等級**: PM（C-1 戻り値契約）/ SE（C-2/W-4 内部実装）
**ステータス**: **CLOSED**（2026-06-06 BUILDING フェーズで全件決着）
**完了日**: 2026-06-06
**根拠**: SESSION_STATE 調整2（card_generator 構造系は⑤送り）/ 設計 `docs/artifacts/audit-2026-06-01/S2b-card-generator.md`

## 繰越 Issue 一覧

| # | 重要度 | 等級 | 箇所 | 内容 |
|---|--------|------|------|------|
| C-1 | Critical | PM | `card_generator.py:886-912, 1010-1032` | `detect_circular_dependencies()` / `build_topo_order()` の戻り値が「循環なし」と「RecursionError 検出失敗」を区別不能（サイレント見逃し）。戻り値契約を `Optional`/例外/明示フラグへ。**仕様明確化が先決**。 |
| C-2 | Critical | SE | `card_generator.py:831-876` | `_find_sccs()` 再帰 Tarjan で1000ノード超 RecursionError。反復実装へ置換。※実 import グラフは数十ノードで**実発火しない潜在バグ**。 |
| W-4 | Warning | SE | `card_generator.py:840` | `index_counter = [0]` closure workaround → `nonlocal`。 |
| I-2 | Info | SE | `card_generator.py:1297,1302` | `specs_dir.glob("*.md")` 非再帰（サブディレクトリ仕様書を拾わない）。 |

## 免除理由（A-2 準拠）

- **技術的妥当性**: C-1 は戻り値型の仕様変更（PM級）を伴い、AUDITING モードでの即時修正より⑤の TDD（Red→Green）で契約を先にテスト化する方が安全。C-2 は実スケールで未発火の潜在バグであり、分割と同時に反復実装へ置換するのが効率的。
- **対象フェーズ**: ⑤（BUILDING・`/building` 切替で TDD 強制）。
- **追跡**: 本ファイル + `S2b-card-generator.md`（7ブロック分割候補・最優先2ブロック=グラフ解析 L799-1090・影響範囲分析 L1093-1305）。

## 完了条件

- card_generator が2モジュールに分割され、C-1 の戻り値契約が仕様化・テスト化される。
- C-2 が反復実装に置換され、大規模グラフ（>1000ノード）のテストが緑。
- W-4/I-2 が分割の過程で解消。

## iter2 追加分（分割時に一括解消）

full-review iter2（`docs/artifacts/audit-reports/2026-06-02-iter2.md`）で検出。card_generator 内の性能系のため⑤分割と同時に解消するのが効率的。

| # | 重要度 | 箇所 | 内容 |
|---|--------|------|------|
| W2-4 | Warning(SE) | `card_generator.py:1143-1154` | `_bfs_upstream()` が `queue.pop(0)` で O(N) 削除 → `collections.deque` + `popleft()` |
| iter2-Info | Info(SE) | `card_generator.py:952` | `_condense_sccs()` が SCC メンバー探索で `scc_map` 全体を毎回走査（O(N^2)）→ 逆引き辞書で O(N) |

---

## CLOSE 記録（2026-06-06 BUILDING フェーズ）

### 全 Issue 決着状況

| # | 等級 | 決着内容 | SSOT |
|---|------|---------|------|
| C-1 | PM | 仕様化（FR-7a-bis）+ `SccDetectionSkippedError` 例外 + `TopoOrderResult` frozen dataclass。3公開関数の `try/except RecursionError` を全削除し fail-fast に。MAGI 等価議論なしで「選択肢1（exception 伝播）」を採用（選択肢2/3 の検討経緯はセッション履歴に保持）。 | `docs/specs/scalable-code-review-spec.md` FR-7a-bis / FR-7d 補足 |
| C-2 | SE | `_find_sccs` を再帰 Tarjan から反復スタックベース実装に置換。`sys.setrecursionlimit(250)` 下で 600 ノードの線形チェーンおよび 400 ノードの単一サイクルが正常完了することをテストで保証。 | `analyzers/graph/scc.py` `_find_sccs` |
| W-4 | PG | C-2 反復化で `index_counter = [0]` クロージャ workaround が消滅。反復実装では普通の `int` 変数で書ける。 | 同上 |
| W2-4 | PG | `_bfs_upstream` の `queue.pop(0)` を `collections.deque + popleft()` に置換。 | `analyzers/analysis/impact.py` |
| iter2-Info | PG | `_condense_sccs` で `scc_map` と `super_to_members` 逆引き辞書を同一ループで構築（O(N^2) → O(N)）。 | `analyzers/graph/scc.py` `_condense_sccs` |
| I-2 | SE | `collect_spec_drift_context` の `specs_dir.glob("*.md")` を `rglob("*.md")` に変更。サブディレクトリ階層（`docs/specs/<feature>/`）の仕様書も収集対象になる。 | `analyzers/card_generator.py` `collect_spec_drift_context` |

### モジュール切り出し

設計書 S2b 横断観察の「最優先の分割候補」に従い、以下2モジュールを切り出し:

- `analyzers/graph/scc.py`: SCC 検出 / トポロジカルソート / 循環依存検出（旧 L799-1090）
- `analyzers/analysis/impact.py`: 影響範囲分析（旧 L1093-1262）
- `collect_spec_drift_context` は `ModuleCard` 依存のため `card_generator.py` に残置

`card_generator.py` は `as` 形式 explicit re-export で後方互換を維持。既存テストの `from analyzers.card_generator import ...` は無変更で動く。

### 検証

- **テスト**: 680 passed（既存 670 + 新規10件）。`pytest -o addopts="" .claude/hooks/` 全件 Green。
- **ruff**: ⑤ 関連の F401 ゼロ。残 1 件は e2e フィクスチャの既存意図的残置（対象外）。
- **gitleaks**: no leaks。

### 残課題

- ~~`_file_path_to_module_name` が `card_generator.py` と `analyzers/graph/scc.py` に重複定義（scc.py に TODO コメント）。共通 utility モジュールへの統合は PM 級判断で別途。~~ → **A-3 で解決（2026-06-09）**: PM 承認のうえ `analyzers/base.py` に公開関数 `file_path_to_module_name` として集約。card_generator / graph.scc の局所定義と TODO を削除し、analysis.impact の import 元も scc→base に変更。700 passed / ruff clean。
- `analyzers.graph.scc._find_sccs` を monkeypatch する際は、scc / impact / card_generator の3モジュール全てに setattr が必要（`from foo import bar` で取り込まれた参照はモジュール毎に独立）。テスト `_patch_find_sccs_to_raise` ヘルパーで集約済み。
- **`_` プレフィックス内部関数の後方互換 re-export 解消（2026-06-10 B-2 監査 PM-2 委譲）**:
  `card_generator.py:25-44` の re-export（⑤切り出し時の互換措置）のうち、`_` 付き内部関数
  （`_bfs_upstream` / `_build_reverse_graph` / `_expand_scc_members` / `_partition_files_by_scope` /
  `_build_import_graph` / `_collect_supernode_edges` / `_condense_sccs` / `_find_sccs` / `_resolve_node_edges`）
  は API 境界を曖昧化するため、呼出元（主にテスト）を `analyzers.graph.scc` / `analyzers.analysis.impact`
  からの直接 import に移行したうえで re-export を削除する。公開シンボル
  （`analyze_impact` / `classify_impact_for_cards` / `SccDetectionSkippedError` / `TopoOrderResult` /
  `build_topo_order` / `detect_circular_dependencies`）の re-export 維持可否はその際に判断。
  ユーザー判断（PM-2: 選択肢A）により即時修正せず本ファイルへ委譲記録。card_generator に次に構造変更を
  加えるタイミングで一括実施する。
