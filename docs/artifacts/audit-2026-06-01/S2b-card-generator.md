# 監査レポート S2b: card_generator.py

対象: `.claude/hooks/analyzers/card_generator.py` (1,305 LOC) / 日付: 2026-06-01 / Pass 1

## サマリー

Critical: 1 / Warning: 7 / Info: 4 / 評価: **Yellow**

---

## Critical

### [Critical] card_generator.py:887-894, 1010-1017, 1204-1211 — RecursionError 握り潰し後の callers 不通知

`detect_circular_dependencies`, `build_topo_order`, `analyze_impact` の3箇所で
`RecursionError` を `logger.warning()` のみで補足し、
それぞれ空リスト返却・`sccs=[]` セット・`sccs=[]` セットに落とす。

```
L887-894  detect_circular_dependencies: except RecursionError → return []
L1010-1017 build_topo_order: except RecursionError → sccs = []
L1204-1211 analyze_impact: except RecursionError → sccs = []
```

根拠: `code-quality-guideline.md` "Silent Failure" — エラーを log して処理続行し、
失敗を呼び出し側が検知不能な状態。`RecursionError` は意味のある障害（グラフが大きすぎて
SCC 検出不能）であり、呼び出し元が「循環依存検出がスキップされた」ことを知る手段がない。
`detect_circular_dependencies` は `[]` を返すため呼び出し側は「循環なし」と誤認する可能性がある。
`build_topo_order` は `sccs=[]` のまま縮約・ソートを続けるため、循環依存グラフで
`CycleError` に到達してさらに `list(condensed.keys())` に落ちる（フォールバックの連鎖）。

修正案: 戻り値の型に「スキップフラグ」を含めるか、カスタム例外を raise するか、
少なくとも `{"in_scope": [], "out_of_scope": [], "scc_detection_skipped": True}` のように
スキップを callers に伝達する。

等級: **SE**

---

## Warning

### [Warning] card_generator.py:230-245, 488-503, 781-796 — load_*card 3関数が構造的コピペ (Rule of Three)

3つのカードロード関数が同一の構造を持つ:

```
load_file_card (L230-245)     : cards_dir / _FILE_CARDS_DIR / _card_filename
load_contract_card (L488-503) : contracts_dir / _contract_card_filename
load_module_card (L781-796)   : cards_dir / _MODULE_CARDS_DIR / _module_card_filename
```

各関数の構造は `path.exists() → json.loads(path.read_text()) → except json.JSONDecodeError → T(**data)` と
完全に一致。同じパターンが4回現れる save_*card、3回現れる `_*_filename` も含め、
永続化 I/O パターンが全体で12個の関数に分散している。

根拠: Rule of Three（Duplication > 3回 = Warning）。バグ修正が3箇所に伝播する。
例えば `json.JSONDecodeError` 以外の例外（`OSError`, `PermissionError` 等）を
ハンドルしたい場合に3箇所を同期的に修正する必要がある。

修正案: ジェネリック関数 `_load_card(state_dir, subdir, filename, cls)` を切り出す。
`save_card` も同様。3つの `_*_filename` 関数も1つに統一できる
（ただし `_card_filename` のドット置換の振る舞いの不整合を先に解消すること）。

等級: **SE**

---

### [Warning] card_generator.py:212-217 vs 453-458, 763-768 — `_card_filename` と他の filename 関数の振る舞い不整合

```
_card_filename (L212-217):          replace("/","-").replace("\\","-").replace(".","-")
_contract_card_filename (L453-458): replace("/","-") のみ（ドット・バックスラッシュ置換なし）
_module_card_filename (L763-768):   replace("/","-") のみ（同上）
```

`_card_filename` だけが `.` を `-` に置換しているため、`"src/foo.py"` は
`"src-foo-py.json"` となり、他2関数と命名規則が異なる。
同一の設計書 Section 4.6 を参照しているが挙動が乖離している。

根拠: 設計書仕様との乖離（どちらが「正しい」か不明のため Critical ではなく Warning）。
`"src.foo"` をモジュール名に使う contract/module の場合ファイル名に `.` が入り
ファイルシステムによっては拡張子として解釈されるリスクがある。

修正案: 設計書 Section 4.6 で想定するパス形式を確認し、3関数の変換ルールを統一する。

等級: **SE**

---

### [Warning] card_generator.py:1264-1305 — `collect_spec_drift_context` の SRP 違反（I/O + 変換 + フォーマット混在）

```python
def collect_spec_drift_context(state_dir, specs_dir) -> str:
    # (1) ファイルシステムから .json を列挙・読み込み
    # (2) JSON → ModuleCard へ変換（エラー時 card=None）
    # (3) ModuleCard.to_markdown() でフォーマット
    # (4) ファイルシステムから .md を列挙・読み込み
    # (5) Markdown 文字列を連結してプロンプト用テキストを生成
```

5つの責務が1関数に混在。テストが困難（I/O をモックしないと単体テスト不能）。

根拠: SRP 違反（複数責務の混在）。42行で nesting depth=4。

修正案:
- `_collect_module_cards_text(state_dir) -> str` — カード収集・整形
- `_collect_specs_text(specs_dir) -> str` — 仕様書収集・整形
- `collect_spec_drift_context` はこれを合成する薄いオーケストレーターに。

等級: **SE**

---

### [Warning] card_generator.py:992-1032 — `build_topo_order` の返り値型が `dict`（型情報なし）

```python
def build_topo_order(import_map: dict[str, list[str]]) -> dict:
```

`dict` と書かれているが実際は `{"topo_order": list[str], "sccs": list[list[str]], "node_to_file": dict[str, str]}`
という固定構造を持つ。呼び出し側はキー名を文字列でアクセスするしかなく、
typo や欠落キーが静的解析で検出できない。

根拠: 不明瞭な命名/型（「意図が読み取れない」に相当）。設計書 Section 5.3 の
明示的な返り値定義と乖離している。

修正案: `TypedDict` または `dataclass`（`TopoResult` 等）に置き換える。

等級: **SE**

---

### [Warning] card_generator.py:831-876 — `_find_sccs` 内クロージャ `strongconnect` のネスト深度と再帰実装リスク

再帰実装の `RecursionError` リスクは docstring に記載されているが、
クロージャ `strongconnect`（L847）が親スコープの6つの変数（`index_counter`, `stack`,
`on_stack`, `indices`, `lowlinks`, `sccs`）を変異させており、
テスト・デバッグ困難な暗黙的ステート共有が発生している。

根拠: Deep Nesting ＋ 暗黙ステート共有 ＋ 既知の RecursionError リスク（docstring に明記）。
CC=11（閾値15未満だが）。

修正案: `strongconnect` を単独の `_tarjan_strongconnect(v, state: TarjanState)` として
明示的なステートオブジェクトを引数渡しにするか、反復実装（スタックベース）に置き換える。

等級: **SE**

---

### [Warning] card_generator.py:1133-1155 — `_bfs_upstream` で `list.pop(0)` を使用（O(n) 操作）

```python
queue = list(start_nodes)
while queue:
    current = queue.pop(0)   # O(n) per iteration
```

BFS キューに `list.pop(0)` を使用しており、ノード数 N に対してループ全体が O(N²)。
`collections.deque` の `popleft()` を使えば O(N) になる。

根拠: パフォーマンスに関わる実装選択ミス。大規模プロジェクト（数百ファイル）での
影響範囲分析（FR-7d）で顕在化する。

修正案:
```python
from collections import deque
queue = deque(start_nodes)
while queue:
    current = queue.popleft()
```

等級: **PG**（自明な修正、振る舞い変化なし）

---

### [Warning] card_generator.py:951-952 — `_condense_sccs` 内の O(N²) スーパーノードメンバー逆引き

```python
for super_name in super_nodes:
    members = [m for m, s in scc_map.items() if s == super_name]  # O(|scc_map|) per super_node
```

`scc_map` 全体を `super_nodes` の数だけ走査する。SCC 数が多い場合に O(N²)。
`_condense_sccs` は `build_topo_order` と `analyze_impact` の両方から呼ばれる。

根拠: 計算量の無駄（`scc_map` 構築時に逆引き辞書も同時に作れる）。

修正案: `scc_map` 構築ループで `super_to_members: dict[str, list[str]]` を同時に構築し、
L951 の内包表現を辞書参照に置き換える。

等級: **PG**

---

## Info

### [Info] card_generator.py:406-433 — `merge_contracts` の public_api 重複除去が O(N²) リスト探索

```python
public_api: list[str] = []
for fp in module_files:
    for name in card.public_api:
        if name not in public_api:      # O(|public_api|) per name
            public_api.append(name)
```

関数は短く（45行）実用上の問題にはなりにくいが、`set` + 順序保持 (`dict.fromkeys`) で
O(N) に改善できる。

等級: **SE**

---

### [Info] card_generator.py:649-694 — `check_unused_reexports` の既知制限がコメントのみで仕様書未記載

docstring の "既知の制限: 深いパスでの import 検出は不完全" は実装上の既知バグだが、
対応する仕様書（FR-4）に Phase 3 移行の明示記述がない（コード内コメントのみ）。

等級: **SE**（仕様書への記録を推奨）

---

### [Info] card_generator.py:841 — Tarjan アルゴリズムの `index_counter = [0]` イディオム

```python
index_counter = [0]   # Python 2 時代の closure 変数変異回避イディオム
```

Python 3.10+ では `nonlocal index_counter` + `int` で素直に書ける。
動作上の問題はない。

等級: **PG**

---

### [Info] card_generator.py:1302 — `specs_dir.glob("*.md")` を2回呼び出し

```python
if not specs_dir.exists() or not list(specs_dir.glob("*.md")):   # L1302 - 2回目のglob
```

L1296 で既に `spec_files = sorted(specs_dir.glob("*.md"))` を取得しているにも関わらず、
L1302 で再度 glob を呼び出している。`if not spec_files:` で代替できる。

等級: **PG**

---

## 横断観察（分割方針の所見）

1,305 行のファイルは現在 **7つの責務ブロック**が混在している。
各ブロックは独立したモジュールの候補である:

| ブロック | 現在の行範囲 | 責務 | 候補モジュール名 |
|----------|------------|------|----------------|
| データモデル | L34-121 | FileCard / ModuleCard / ContractCard dataclass 定義 + `to_markdown` | `cards/models.py` |
| ファイルカード生成 | L122-246 | generate / save / load / parse_responsibility / merge_responsibilities | `cards/file_card.py` |
| 契約カード | L284-503 | parse_contract / merge_contracts / save / load / format_for_prompt | `cards/contract_card.py` |
| Blame Hint | L337-387 | parse_blame_hint | `cards/blame.py` |
| モジュールカード + 境界チェック | L507-796 | detect_module_boundaries / check_* / generate / save / load | `cards/module_card.py` |
| グラフ解析（SCC/Topo/循環検出） | L799-1090 | _build_import_graph / _find_sccs / detect_circular / build_topo | `graph/scc.py` |
| 影響範囲分析 + 仕様ドリフト | L1093-1305 | analyze_impact / classify_impact_for_cards / collect_spec_drift | `analysis/impact.py` |

**最優先の分割候補**: グラフ解析ブロック（L799-1090）と影響範囲分析ブロック（L1093-1305）は
カード生成と依存関係がなく、現在のファイルから独立して切り出せる。
永続化 I/O（save_*/load_*）の共通化と合わせて行うと効果が高い。

大規模リファクタリングは PM級承認が必要。
