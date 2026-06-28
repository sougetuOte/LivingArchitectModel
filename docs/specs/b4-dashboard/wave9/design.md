# b4-dashboard Wave 9 — design.md

- バージョン: 0.2.7
- 作成日: 2026-06-28
- 更新日: 2026-06-28（v0.2.7 = 最終クリーニング / Green State 完全達成）
- ステータス: Draft（PM 承認待ち）
- 根拠文書: `docs/specs/b4-dashboard/wave9/requirements.md` v0.2.7
- 参照文書:
  - `docs/specs/b4-dashboard/design.md` v0.2.7（元設計書 / §4 V-4 DOM 構成案・§5 TaskInfo/TasksParser・§8 CSS 更新済み / §13 UQ-13 Critical 解決済）
  - `docs/specs/b4-dashboard/wave7/design.md` v0.2.3（Assignee 列実装パターン参照元 / §6 Stage 2）
  - `docs/artifacts/retro-W7-B5-2026-06-28.md`（Wave 7 retro / chip task_5de9563e 引き継ぎ）
- 設計方針: MAGI 合議（2026-06-28 B1/B2/B3）に基づく。元 design.md §5 を SSOT とし、本書は Wave 9 追加事項のみを記述する。

---

## §1 Problem Statement

### chip task_5de9563e の核心

Wave 7 PoC レビュー（2026-06-28）で起票された chip `task_5de9563e` は
「V-4 Task 一覧で description が表示されない」という問題であり、
その根本原因は **TasksParser が `raw_description` から `assignee` のみを取得し
`description_clean` を破棄している** ことにある。

現状:

| 観点 | 現状 | 問題 |
|:-----|:-----|:----|
| `_extract_assignee()` の戻り値 | `(description_clean, assignee)` のタプルを返す | 第 1 要素（`description_clean`）が呼び出し側で破棄されている（`_, assignee = ...`）|
| `TaskInfo` モデル | `id / milestone / status / assignee` の 4 フィールドのみ | `description` フィールドが存在しない |
| V-4 テーブル | Task ID / 担当 / 状態 の 3 列 | description 列がない → Task ID だけでは内容不明 |

Wave 7 の `_extract_assignee()` 実装（`parsers/tasks.py` L54-69）は既に
`clean_description`（= assignee タグ除去後の本文）を計算しているが、
それを返してはいるものの呼び出し元（L154）で捨てていた。

### 修正の最小性

本設計の変更は以下の 3 箇所に限定される:

1. **`models.py`**: `TaskInfo` に `description: str = ""` を追加（1 フィールド追加）
2. **`parsers/tasks.py`**: L154 の `_, assignee = _extract_assignee(...)` を `description_clean, assignee = _extract_assignee(...)` に変更し、L155-162 の `TaskInfo(...)` に `description=description_clean` を追加（2 行変更）
3. **`builder.py`**: `_render_v4_tasks()` の `<thead>` に `<th id="th-description">` 追加 / `<tbody>` の各行に `<td class="description-cell">` 追加 / CSS に `.description-cell` ルール追加（HTML テンプレート追加）/ thead テンプレートの data-col 属性値更新（担当 1→2 / 状態 2→3）/ `sortTable()` の `ths.forEach` 内 aria-sort 更新ロジック修正（`idx === columnIndex` → `thCol === columnIndex` / thCol は `th.querySelector('.sort-btn')?.dataset.col` を parseInt）

---

## §2 Goals / Non-Goals

### Goals

- chip `task_5de9563e` を description 列追加で正式解決する
- `TaskInfo.description` フィールドを models.py に追加し、TasksParser から description を受け取る
- V-4 の 2 列目（Task ID 右隣）に description を表示し、「何のタスクか」を一覧で把握可能にする
- 既存テストへの影響を既定値 `""` で最小化する

### Non-Goals（設計スコープ外）

- 元 design.md §5 の再記述・移転（SSOT を一本化 / 本書では追加事項のみ記述）
- TasksParser の parser ロジック（抽出・分岐・regex）の追加（1 行変更のみで完結）
- CSS 意匠面の変更（`.description-cell` 追加以外）
- description ソート / キーワードフィルタ / モーダル
- Wave 8 FR-W8-4 が宣言した「既存 4 パーサ無改変」の継続義務（Wave 9 は別仕様書で明示的に改修を許可）

---

## §3 アーキテクチャ（description フロー追加）

### 既存フローとの差分（Wave 9 変更箇所）

```
[データソース層]       [パーサ層（Wave 9: tasks.py のみ 2 行変更）]    [モデル層]         [出力層]
tasks.md      ──→  TasksParser._extract_tasks()                ──→  TaskInfo        ──→  DashboardBuilder
                     L154: description_clean, assignee = _extract_assignee(raw_description)
                     L162: TaskInfo(id=..., milestone=..., status=..., assignee=assignee,
                                    description=description_clean)  ← Wave 9 追加
                                                                         ↓
                                                                TaskInfo.description ──→ _render_v4_tasks()
                                                                                              ↓
                                                                                       <td class="description-cell"
                                                                                            title="{full}">
                                                                                         {escaped}
                                                                                       </td>
```

### パーサ独立性原則との整合

Wave 9 の TasksParser 変更は parser 内部の `TaskInfo` 生成時の 1 行追加であり、
他のパーサ（SessionState / CurrentPhase / GitHistory）への依存を生じさせない。
パーサ独立性原則（元 design.md §3）に違反しない。

---

## §4 TaskInfo フィールド追加詳細

### models.py 現状

```python
@dataclass
class TaskInfo:
    id: str
    milestone: str
    status: str
    assignee: str = "-"
```

### Wave 9 変更後

```python
@dataclass
class TaskInfo:
    id: str
    milestone: str
    status: str
    assignee: str = "-"
    description: str = ""  # Wave 9 追加（FR-W9-2）: Task ID・assignee タグ除去後の本文。既定値 "" で後方互換維持
```

**設計判断**:
- `description` を末尾に追加することで、既存の位置引数コード（`TaskInfo(id, milestone, status, assignee)` 等）との後方互換を維持する
- 既定値 `""` は `assignee: str = "-"` と同じパターンを踏襲する
- `MilestoneInfo.status` のコメント更新（UQ-11 / Wave 8 残）は本 Wave 9 でも対象外（既存優先）

---

## §5 TasksParser 改修詳細

### 現行コード（parsers/tasks.py L138-163）

```python
def _extract_tasks(self, content: str, fallback_milestone: str) -> list[TaskInfo]:
    tasks: list[TaskInfo] = []
    for line in content.splitlines():
        match = _CHECKBOX_RE.match(line)
        if match is None:
            continue
        checkbox_value = match.group(1)
        description = match.group(2).strip()
        status = _STATUS_MAP[checkbox_value]
        task_id = self._extract_task_id(description)
        if task_id is None:
            continue
        milestone = self._resolve_milestone(task_id, fallback_milestone)
        id_prefix = task_id + ":"
        raw_description = description[len(id_prefix):].strip()
        _, assignee = _extract_assignee(raw_description)      # ← 第1要素を破棄（旧）
        tasks.append(
            TaskInfo(
                id=task_id,
                milestone=milestone,
                assignee=assignee,
                status=status,
            )
        )
    return tasks
```

### Wave 9 変更後（変更箇所のみ抜粋）

```python
        raw_description = description[len(id_prefix):].strip()
        description_clean, assignee = _extract_assignee(raw_description)  # ← Wave 9: 第1要素を使用（FR-W9-3）
        tasks.append(
            TaskInfo(
                id=task_id,
                milestone=milestone,
                assignee=assignee,
                status=status,
                description=description_clean,                              # ← Wave 9: description 追加
            )
        )
```

**変更内容**:
- 旧: `_, assignee = _extract_assignee(raw_description)`（第 1 要素を `_` で捨てる）
- 新: `description_clean, assignee = _extract_assignee(raw_description)`（第 1 要素を `description_clean` に束縛）
- `TaskInfo(...)` に `description=description_clean` を追加

**parser ロジック追加ゼロの保証**:
`_extract_assignee()` は Wave 7 で既に `(clean_description, assignee)` を返す実装であり、
新たな抽出・分岐・regex の追加は一切不要である。

---

## §6 builder.py V-4 改修詳細

### JS 定数値 + data-col 属性値 + sortTable 修正（Critical 解決 / 案 A + 選択肢 A + (c) aria-sort 修正）

description 列が 2 列目（物理インデックス 1）に挿入されることで、
JS の `cells[N]` アクセスと物理列位置がずれる。
**`builder.py` の JS 定数定義および thead テンプレートの data-col 属性値を以下のように更新しなければならない（MUST）**。

**data-col 属性値も更新必須（担当: 1→2 / 状態: 2→3）**。これにより `sortTable()` の `cells[columnIndex]` が物理列と整合する。`applyFilters()` の `cells[COL_STATUS]` / `cells[COL_ASSIGNEE]` は定数経由で同様に整合する。

更新内容:
- **(a) JS 定数値**（`applyFilters()` の `cells` アクセス整合）:
  - `COL_DESCRIPTION = 1` を新規追加
  - `COL_ASSIGNEE = 2`（旧 1）
  - `COL_STATUS = 3`（旧 2）
- **(b) thead テンプレートの data-col 属性値**（`sortTable()` の `cells[columnIndex]` 整合）:
  - 担当 th: `data-col="1"` → `data-col="2"` に更新
  - 状態 th: `data-col="2"` → `data-col="3"` に更新
  - Task ID th: `data-col="0"`（変更なし）
  - description th: data-col 属性なし（ソート不可 / FR-W9-4 MUST NOT）

(a)(b) の両方が更新されることで、`sortTable()` の `cells[columnIndex]` アクセスと
`applyFilters()` の `cells[COL_STATUS]`/`cells[COL_ASSIGNEE]` アクセスの両方が
Wave 9 後の物理列位置と整合する状態になる（FR-W9-N1 (a)(b) 参照）。

**改修対象**: `.claude/scripts/dashboard/builder.py`

| 箇所 | 行番号（目安） | 変更内容 |
|:-----|:------------|:--------|
| JS 定数定義 | L352-354 | `COL_DESCRIPTION = 1` を新規追加 / `COL_ASSIGNEE = 2`（旧 1）/ `COL_STATUS = 3`（旧 2）|
| `sortTable()` | L373-375 | `cells[COL_STATUS]` 参照は変数名不変 / 定数値変更のみで正しく動作 |
| `applyFilters()` | L430-434 | `cells[COL_STATUS]` / `cells[COL_ASSIGNEE]` 参照は変数名不変 / 定数値変更のみで正しく動作 |

**変更前の JS 定数**:
```javascript
const COL_TASK_ID  = 0;
const COL_ASSIGNEE = 1;
const COL_STATUS   = 2;
```

**変更後（Wave 9）の JS 定数**:
```javascript
const COL_TASK_ID      = 0;
const COL_DESCRIPTION  = 1;  // Wave 9 新規追加（description 列 = 2 列目）
const COL_ASSIGNEE     = 2;  // 旧 1 → 新 2（description 列挿入で 1 シフト）
const COL_STATUS       = 3;  // 旧 2 → 新 3（description 列挿入で 1 シフト）
```

> **`cells[COL_ASSIGNEE]` / `cells[COL_STATUS]` の参照コード変更は不要**。
> 定数値が更新されることで `cells[2]` / `cells[3]` に自動的に対応する。
> ただし BUILDING で `sortTable()` / `applyFilters()` の実動作確認が必須（AC-W9-4）。

> **DQ-W9-2 解決済み**（案 A 採用 / 2026-06-28 ユーザー承認）:
> 旧 DQ-W9-2「既存 applySort() JS と description 列の干渉」は、
> JS 定数値を更新することで `cells[COL_STATUS] = cells[3]` / `cells[COL_ASSIGNEE] = cells[2]`
> となり整合性が確保される。BUILDING での確認が残るが設計上の未解決事項は解消。

### _render_v4_tasks() の thead 変更

**変更前（3 列）**:
```html
<tr>
  <th id="th-task-id" aria-sort="none">
    <button class="sort-btn" data-col="0" aria-label="Task IDで昇順にソート">Task ID</button>
  </th>
  <th id="th-assignee" aria-sort="none">
    <button class="sort-btn" data-col="1" aria-label="担当で昇順にソート">担当</button>
  </th>
  <th id="th-status" aria-sort="none">
    <button class="sort-btn" data-col="2" aria-label="状態で昇順にソート">状態</button>
  </th>
</tr>
```

**変更後（4 列 / Wave 9 実装完了後の最終形）**:
```html
<tr>
  <th id="th-task-id" aria-sort="none">
    <button class="sort-btn" data-col="0" aria-label="Task IDで昇順にソート">Task ID</button>
  </th>
  <th id="th-description">description</th><!-- ソートボタンなし / aria-sort 属性なし（FR-W9-4 MUST NOT）-->
  <th id="th-assignee" aria-sort="none">
    <button class="sort-btn" data-col="2" aria-label="担当で昇順にソート">担当</button>
  </th>
  <th id="th-status" aria-sort="none">
    <button class="sort-btn" data-col="3" aria-label="状態で昇順にソート">状態</button>
  </th>
</tr>
```

**注記**: 本テンプレートは Wave 9 BUILDING 完了後の最終形を示す。担当 th の
data-col="2"、状態 th の data-col="3" は FR-W9-N1 (b) の更新後の値である。
Wave 9 着手前（現状）は担当=1 / 状態=2 であり、選択肢 A 採用によりこれらを
同時更新する。

> **data-col 属性値も更新必須（担当 1→2 / 状態 2→3）**。これにより `sortTable()` の `cells[columnIndex]` が物理列と整合する。`applyFilters()` の `cells[COL_STATUS]` / `cells[COL_ASSIGNEE]` は定数経由で同様に整合する。`data-col` 属性値（HTML）と JS 定数値（JS）の両方が整合していることで `applySort()` / `applyFilters()` が正しく動作する（FR-W9-N1 (a)(b) 参照）。

### _render_v4_tasks() の tbody 行変更

**変更前（3 セル）**:
```python
rows.append(
    f'      <tr data-task-id="{escaped_id}" data-milestone="{escaped_milestone}">\n'
    f"        <td>{escaped_id}</td>\n"
    f"        <td>{escaped_assignee}</td>\n"
    f"        <td>{badge_html}</td>\n"
    "      </tr>"
)
```

**変更後（4 セル）**:
```python
escaped_description = html.escape(task.description)
rows.append(
    f'      <tr data-task-id="{escaped_id}" data-milestone="{escaped_milestone}">\n'
    f"        <td>{escaped_id}</td>\n"
    f'        <td class="description-cell" title="{escaped_description}">{escaped_description}</td>\n'
    f"        <td>{escaped_assignee}</td>\n"
    f"        <td>{badge_html}</td>\n"
    "      </tr>"
)
```

**設計判断**:
- `title` 属性には full description を設定し tooltip を提供する（FR-W9-5 SHOULD）
- `class="description-cell"` を付与し CSS `.description-cell` スタイルを適用する（FR-W9-5 SHOULD）
- `html.escape()` による XSS 対策は必須（既存パターン踏襲）

### 改修対象メソッド一覧

| ファイル | メソッド / 箇所 | 改修内容 | 改修必要性 |
|:--------|:--------------|:--------|:---------|
| `models.py` | `TaskInfo` | `description: str = ""` フィールド追加（FR-W9-2） | **必須** |
| `parsers/tasks.py` | `_extract_tasks()` | `description_clean, assignee = _extract_assignee(...)` に変更 + `TaskInfo` に `description=` 追加（FR-W9-3） | **必須** |
| `parsers/tasks.py` | `_extract_tasks()` docstring | 関数説明中「3 列」→「4 列」等の列数記述を更新（SE 級 / I-W-5） | **推奨** |
| `builder.py` | JS 定数定義（L352-354） | `COL_DESCRIPTION = 1` 追加 / `COL_ASSIGNEE = 2` / `COL_STATUS = 3` に更新（Critical 解決 / 案 A） | **必須** |
| `builder.py` | `sortTable()`（L373-375） | JS 定数値変更のみで `cells[COL_STATUS]` 参照が自動的に正しい列を指す（コード変更不要） | 定数更新に伴う確認 |
| `builder.py` | `sortTable()` aria-sort 更新ロジック（L391-408） | `ths.forEach` 内の `idx === columnIndex` 判定を `thCol === columnIndex`（thCol は `th.querySelector('.sort-btn')?.dataset.col` を parseInt）に変更（FR-W9-N1 (c) / NFR-W9-4） | **必須** |
| `builder.py` | `applyFilters()`（L430-434） | JS 定数値変更のみで `cells[COL_STATUS]` / `cells[COL_ASSIGNEE]` が正しい列を指す（コード変更不要） | 定数更新に伴う確認 |
| `builder.py` | `_render_v4_tasks()` 内 thead テンプレート | `<thead>` に description 列追加 / 担当 th data-col 1→2 / 状態 th data-col 2→3 に更新（選択肢 A 補完 / FR-W9-N1 (b) / builder.py L700 周辺） | **必須** |
| `builder.py` | `_render_v4_tasks()` tbody 行 | `<tbody>` 各行に `<td class="description-cell">` 追加 | **必須** |
| `builder.py` | `_render_style()` 等 | `.description-cell` CSS ルール追加（FR-W9-5 SHOULD） | **推奨** |
| `parsers/session_state.py` | — | 変更なし（Wave 9 スコープ外） | 不要 |
| `parsers/current_phase.py` | — | 変更なし | 不要 |
| `parsers/git_history.py` | — | 変更なし | 不要 |
| `merger.py` | — | 変更なし（Wave 8 で新設済み） | 不要 |
| `build_dashboard.py` | — | 変更なし | 不要 |

### colNames 配列について（Wave 9 後も 3 要素のままで正しい理由）

`sortTable()` 内の `colNames` 配列は `th[aria-sort]` を持つ `<th>` に対応しており、
Wave 9 後の 4 列構成においても **3 要素のままで正しく動作する**。

```javascript
const colNames = ['Task ID', '担当', '状態'];  // Wave 9 後も変更なし
```

理由:

- `th[aria-sort]` の querySelectorAll が対象とする列は Task ID / 担当 / 状態 の 3 列のみ
- description 列（`<th id="th-description">`）は `aria-sort` 属性を持たないため NodeList から自動除外される
- 結果として Wave 9 後も NodeList の idx は 0=Task ID / 1=担当 / 2=状態 の 3 要素連続で維持される

**aria-label 更新の整合**: aria-label 更新（`colNames[idx]`）は idx（NodeList の連続 0-2）を使い続ける。
NodeList 内では Wave 9 前後で idx=0→Task ID / idx=1→担当 / idx=2→状態 の対応関係が変化しないため
（description 列は aria-sort を持たず NodeList から除外される）、aria-label は正しく動作する。
**aria-sort の th 特定のみ** data-col 値ベースに変更する必要がある（FR-W9-N1 (c)）。

`sortTable()` 内の `idx === columnIndex` 判定について — **Wave 9 後は修正が必要**:

- `idx` は `th[aria-sort]` NodeList の位置（0-2 連続）
- `columnIndex` は `btn.dataset.col` の値（data-col 属性値: Wave 9 後は 0/2/3 と**非連続**）
- **Wave 9 後の問題**: NodeList idx（0/1/2 連続）と columnIndex（0/2/3 非連続）が
  担当列・状態列で**常に不一致**（担当: `1 === 2` が false / 状態: `2 === 3` が false）
- → ソート機能自体は `cells[columnIndex]` で正しく動作するが、**aria-sort 属性が更新されない**
- → スクリーンリーダーの「現在のソート方向」伝達が破壊される（NFR-W9-4 違反リスク）

この問題を解決するために FR-W9-N1 (c) の sortTable() aria-sort 更新ロジック修正が必要となる（次節参照）。

### (c) sortTable() aria-sort 更新ロジック修正（FR-W9-N1 (c) / NFR-W9-4 整合）

**改修対象**: `.claude/scripts/dashboard/builder.py` L391-408（sortTable 内 ths.forEach ブロック）

**問題の核心**:
- Wave 9 後、`sortTable()` の `ths.forEach((th, idx) => { ... })` 内で
  `idx === columnIndex` による th 特定が担当列（`1 === 2`）・状態列（`2 === 3`）で常に false になる
- aria-sort 属性が当該 th に設定されないためスクリーンリーダーがソート方向を認識できない

**変更前（現行 / Wave 9 後に破壊される）**:

```javascript
ths.forEach((th, idx) => {
  if (idx === columnIndex) {
    th.setAttribute('aria-sort', currentSort.dir === 'asc' ? 'ascending' : 'descending');
    th.setAttribute('aria-label', colNames[idx] + (currentSort.dir === 'asc' ? 'で昇順にソート中' : 'で降順にソート中'));
  } else {
    th.setAttribute('aria-sort', 'none');
    th.setAttribute('aria-label', colNames[idx] + 'で昇順にソート');
  }
});
```

**変更後（選択肢 A / data-col 値で比較）**:

```javascript
ths.forEach((th, idx) => {
  const thCol = parseInt(th.querySelector('.sort-btn')?.dataset.col ?? '-1', 10);
  if (thCol === columnIndex) {
    th.setAttribute('aria-sort', currentSort.dir === 'asc' ? 'ascending' : 'descending');
    th.setAttribute('aria-label', colNames[idx] + (currentSort.dir === 'asc' ? 'で昇順にソート中' : 'で降順にソート中'));
  } else {
    th.setAttribute('aria-sort', 'none');
    th.setAttribute('aria-label', colNames[idx] + 'で昇順にソート');
  }
});
```

**設計判断**:
- `thCol` は `th.querySelector('.sort-btn')?.dataset.col` を `parseInt(..., 10)` したもの
  （sort-btn が存在しない th（description 列）は `?.` でオプショナルチェーン → `'-1'` fallback → `-1`）
- `-1 === columnIndex` は常に false → description 列の aria-sort は `'none'` に設定される
  （FR-W9-4 MUST NOT: description th に aria-sort がない設計を侵食しない）
- aria-label 更新の `colNames[idx]` は idx（NodeList 0-2 連続）を使い続ける
  （idx=0→Task ID / idx=1→担当 / idx=2→状態 の対応は Wave 9 後も変化しない）

**fallback `-1` の動作補足**: description 列の th は aria-sort 属性を持たないため、
`th[aria-sort]` NodeList に含まれず `ths.forEach` ループに登場しない。したがって
fallback `-1` は安全網として残すが、現行設計では実際には発動しない（description 列が
NodeList に現れないため）。将来的に description 列に aria-sort 属性が追加される場合、
fallback `-1` が機能して description 列の aria-sort が `'none'` のままに維持される。

この設計により、colNames 配列の要素数を変えることなく description 列の追加が完結する。

---

## §7 CSS / レイアウト設計

### 新規 .description-cell CSS

```css
/* Wave 9 追加: V-4 description 列省略表示（FR-W9-5 SHOULD）*/
.description-cell {
  max-width: 300px;          /* 仮値 / BUILDING で実測後に確定 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
```

**設計判断**:
- `max-width: 300px` は仮値。実際の dashboard.html をブラウザで確認後に調整する（MAY）
- `title` 属性の tooltip は HTML ネイティブ機能であり CSS・JS 追加不要
- `white-space: nowrap` は ellipsis の前提条件として必須

### CSS 増分予測

| 項目 | 推定バイト数 |
|:----|:----------|
| `.description-cell` CSS ルール（4 プロパティ） | 約 100-150 bytes |
| thead/tbody の HTML 変更（Python 文字列） | CSS カウント対象外 |
| **Wave 9 CSS 増分合計** | **100-150 bytes** |

**予算確認**:
- Wave 7 終端: 10,400 bytes
- Wave 9 増分上限（NFR-W9-3 SHOULD）: 300 bytes
- Wave 9 後推定: 10,500〜10,550 bytes
- NFR-W7-1 v0.2.4 上限 16,384 bytes に対し残: 5,834〜5,884 bytes（**緑帯 < 70% 維持**）

---

## §8 既存テスト影響事前分析（ガードレール #4 / 必須）

### parsers/ 配下: 影響テスト

| テストファイル | 想定影響 | 対応 |
|:-------------|:--------|:----|
| `test_tasks_parser.py` | `TaskInfo` の `description` フィールドが追加されるため、`TaskInfo(...)` を直接生成している assert が影響を受ける可能性がある。ただし既定値 `""` により、キーワード引数を使わない既存テストは影響ゼロの見込み | フィクスチャ確認 + description フィールドの期待値追加（新規テスト内） |
| `test_session_state_parser.py` | 影響なし（TaskInfo を使わない） | 確認のみ |
| `test_current_phase_parser.py` | 影響なし | 確認のみ |
| `test_git_history_parser.py` | 影響なし | 確認のみ |

### builder.py 関連テスト

| テストファイル | 想定影響 | 対応 |
|:-------------|:--------|:----|
| `test_v4_view.py` | V-4 の HTML 期待値が 3 列 → 4 列に変わるため、**期待値更新が必要**。description 列の `<th>` / `<td>` が期待値に含まれるようになる | 期待値更新（L1 事前承認） |
| `test_wave7_stage4_integration.py` | 統合テストが V-4 の HTML 構造を assert している場合は 4 列対応が必要 | 確認 + 必要に応じて期待値更新（L1 事前承認） |
| `test_wave6_stage3_filter.py` | フィルタ UI テスト（V-4 テーブル構造を確認）は description 列追加で列数が変わるため確認が必要 | 確認 + 必要に応じて最小調整（L1 事前承認） |
| `test_v2_view.py` / `test_v3_view.py` | 影響なし（V-4 スコープ外） | 確認のみ |
| `test_wave8_merger.py` / `test_wave8_integration.py` | 影響なし（Merger スコープ外） | 確認のみ |

### 既存テスト件数影響

| カテゴリ | 予測 |
|:--------|:----|
| 新規テスト（Wave 9） | `test_wave9_description.py` 新設（tasks.py + builder.py + integration / 10〜15 件想定） |
| 期待値更新 | `test_v4_view.py` が主体 / `test_wave7_stage4_integration.py` が副次的（2〜6 件想定 / L1 事前承認） |
| ソート/フィルタ統合テスト（新規） | `test_wave9_sort_filter_integration.py` または `test_wave9_description.py` 内に追加: ① `cells[COL_STATUS] = cells[3]` がバッジを持つセルにアクセスすること / ② `cells[COL_ASSIGNEE] = cells[2]` が担当値を持つセルにアクセスすること / ③ JS 定数値（COL_DESCRIPTION=1 / COL_ASSIGNEE=2 / COL_STATUS=3）が HTML ソース内で確認できること（AC-W9-N1 対応） |
| ソート機能テスト（data-col=3 経由） | 選択肢 A 補完として: 状態列ソート時に `btn.dataset.col="3"` → `columnIndex=3` → `cells[3]` が `.badge` を含むセルにアクセスすることを確認する（AC-W9-N1 検証手段 3 対応） |
| aria-sort 属性更新テスト（新規 / NFR-W9-4 アクセシビリティ回帰防止） | 担当列クリック後に担当 th の aria-sort が `ascending` にセット / 状態列クリック後に状態 th の aria-sort が `ascending` にセット / Task ID 列クリック後も同様 / description 列は aria-sort を持たない（AC-W9-N1 検証手段 6 対応） |
| 改変なし | 既存の大多数（parsers テスト全件 / V-2/V-3 テスト全件 / Merger テスト全件） |

### BUILDING 着手前 L1 検証チェックリスト

BUILDING 着手前に L1 が以下を確認し、期待値更新件数を確定してから実装を開始すること:

- [ ] `test_v4_view.py` で V-4 の `<thead>` 列数を assert しているテスト件数を Grep
- [ ] `test_v4_view.py` で `<td>` 列数（1 行あたり 3 セル固定）を assert しているテスト件数を Grep
- [ ] `test_wave7_stage4_integration.py` で V-4 の HTML を assert している箇所を Grep
- [ ] `test_wave6_stage3_filter.py` でテーブル列数を assert している箇所を Grep
- [ ] `TaskInfo(id=..., milestone=..., status=..., assignee=...)` とキーワード引数省略で生成している既存テストを Grep（`description` 追加で引数不足エラーが出ないか確認）
- [ ] 期待値更新件数を確定し L1 承認を得てから BUILDING 着手

**注**: 以下 3 項目は BUILDING 着手前に設計書 §6 の変更後コード例・thead テンプレートを
読んで実装計画を把握する事前確認である（実装後の検証は AC-W9-N1 検証手段 1-6 で実施）。

- [ ] FR-W9-N1 (a): builder.py JS 定数値が `COL_DESCRIPTION=1` / `COL_ASSIGNEE=2` / `COL_STATUS=3` に更新されていること（設計書 §6 (a) を確認）
- [ ] FR-W9-N1 (b): thead テンプレートで担当 th が `data-col="2"` / 状態 th が `data-col="3"` に更新されていること（設計書 §6 (b) を確認）
- [ ] FR-W9-N1 (c): `sortTable()` の aria-sort 更新ロジックが `thCol === columnIndex` ベース（data-col 値比較）に修正されていること（設計書 §6 (c) を確認）

---

## §9 Alternatives Considered

### 案 1（採用）: description を V-4 2 列目に表示 + ソート不可 + ellipsis

**内容**: `TaskInfo.description` フィールド追加 / TasksParser で 1 行追加 / builder.py で 2 列目に `<td class="description-cell" title="...">` を挿入 / ソートなし / CSS ellipsis

**Pros**:
- 実装最小（2 ファイル変更 + 1 フィールド追加）
- PoC 指摘「何のタスクか分からない」を根本解決
- 既存 parser ロジック追加ゼロ（`_extract_assignee()` の戻り値を活用）
- a11y 負担ゼロ（ソートボタン追加なし）

**Cons**:
- `test_v4_view.py` 等の HTML 期待値を更新する必要がある

**採用理由**: 最小変更で最大効果。MAGI 合議（B1/B2/B3）の全結論と整合する。

### 案 2（却下）: description を末尾列（4 列目）に表示

**内容**: Task ID / 担当 / 状態 の既存 3 列を維持し、description を末尾 4 列目に追加する。

**Pros**: 既存列の変更最小
**Cons**: Task ID の右隣でない → 「タスク内容を Task ID の隣で確認」という一覧性が低下。PoC 指摘の根本対応として不十分。

**却下理由**: 一覧性最大化のため Task ID の右隣（2 列目）が最適（MAGI 合議 B1 確定）。

### 案 3（却下）: description ソート可能

**内容**: `<th id="th-description">` に `sort-btn` を追加しソート機能を持たせる。

**Pros**: 一貫性（全列ソート可能）
**Cons**: アルファベット順 description は意味薄い / ソートボタン数増加で a11y 負担増

**却下理由**: MAGI 合議 B2 確定（ソート不可）。

### 案 4（却下）: description フィールドを追加せず builder で都度抽出

**内容**: `TaskInfo.description` を追加せず、`builder.py` が `task.id` + 別途 parser を呼んで description を再取得する。

**Pros**: `TaskInfo` モデルの変更なし
**Cons**: SRP 違反（builder がパーサ責務を担う） / 二重パース / テスト困難 / 設計の凝集性が低下

**却下理由**: `_extract_assignee()` の第 1 戻り値を活用する案 1 が圧倒的に優れる。

---

## §10 Success Criteria

`wave9/requirements.md` §5 の AC-W9-1〜7 を満たすことで設計の成功とみなす。

追加の設計成功条件:

| 条件 | 確認方法 |
|:-----|:--------|
| 既存テスト退行ゼロ | Wave 9 実装後の pytest 全件 PASS（既存 + Wave 8 追加 + Wave 9 追加） |
| parser ロジック追加ゼロ | `parsers/tasks.py` の diff が 2 行変更のみ（`_, assignee` → `description_clean, assignee` + `description=description_clean` 追加）|
| `TaskInfo.description` の後方互換 | 既定値 `""` により既存テストがキーワード引数省略でも PASS |
| V-4 列構造の正確性 | `<thead>` が 4 `<th>` / `<tbody>` 各行が 4 `<td>` |

---

## §11 未解決事項 / 設計判断ログ

| ID | 事項 | 判断方針 |
|:---|:----|:--------|
| DQ-W9-1 | description の max-width 実測値 | BUILDING でブラウザ上の実表示を確認し、300px から調整する（MAY）。300px を仮値として実装を開始する |
| DQ-W9-2 | ~~既存 applySort() JS と description 列の干渉~~ | **解決済み（案 A + 選択肢 A 補完 + sortTable() 修正 / 2026-06-28 ユーザー承認）**: JS 定数値（COL_DESCRIPTION=1 / COL_ASSIGNEE=2 / COL_STATUS=3）更新・thead data-col 属性値（担当 1→2 / 状態 2→3）更新・`sortTable()` の `ths.forEach` 内 aria-sort 判定を `idx === columnIndex` → `thCol === columnIndex`（thCol: data-col 値 parseInt）に変更 — の 3 点（FR-W9-N1 (a)(b)(c)）を同期実施することで、cells アクセスと aria-sort 属性更新の両方が Wave 9 後の物理列と整合する。BUILDING での AC-W9-N1 動作確認（検証手段 1-6）は引き続き必須（§6「JS 定数値 + data-col 属性値 + sortTable 修正」節参照）|
| DQ-W9-3 | test_v4_view.py の期待値更新件数 | BUILDING 着手前に L1 が Grep で確定する（§8 チェックリスト参照）。2〜6 件を想定 |
| DQ-W9-4 | description が `None` になるケース | `_extract_assignee()` は `str` を受け取り `str` を返す実装であり `None` は返さない。`raw_description` は `description[len(id_prefix):].strip()` で得られる `str` 型であるため `None` が渡ることはない。ただし BUILDING で型確認を実施する |

> **将来候補 Note（FC-N1 / I-I-4）**: SessionStateParser / GitHistoryParser が将来 TaskInfo を
> 直接生成するように拡張される場合、`description` フィールドの初期値・取得元・空文字列の扱いを
> 別途設計する必要がある（FC-N1 候補）。Wave 9 時点では TasksParser のみが `TaskInfo.description`
> を設定し、他パーサは `description` を生成しない（既定値 `""` で安全に動作）。

---

## §12 改訂履歴

| バージョン | 日付 | 変更内容 |
|:----------|:-----|:--------|
| 0.2.3 | 2026-06-28 | 初版起稿 — MAGI 合議（2026-06-28 B1/B2/B3）に基づく Wave 9 詳細設計。chip task_5de9563e 対応。§1〜§12 全セクション起草。TaskInfo フィールド追加・TasksParser 改修詳細・builder.py V-4 改修・CSS 設計・既存テスト影響事前分析 |
| 0.2.4 | 2026-06-28 | spec-critic ラウンド 1 反映（Critical 2 / Warning 6 / Info 4 / 案 A 採用）— §6 JS 定数値更新節追加（COL_DESCRIPTION=1 / COL_ASSIGNEE=2 / COL_STATUS=3 / Critical I-C-1・I-C-2 解決）/ §6 data-col Note 訂正（I-W-1）/ §6 改修対象メソッド一覧拡張（JS 定数・sortTable・applyFilters・docstring 追加 / I-W-5）/ §8 ソート/フィルタ統合テスト（新規）追加（AC-W9-N1 対応）/ §11 DQ-W9-2 解決済化 / §11 FC-N1 将来候補 Note 追加（I-I-4） |
| 0.2.5 | 2026-06-28 | spec-critic ラウンド 2 反映（Critical 1 / Warning 2 / Info 3 / 選択肢 A 補完 / 2026-06-28 ユーザー承認）— §6 thead テンプレート data-col 更新（担当 1→2 / 状態 2→3 / I-C-N1 / FR-W9-N1 (b)）/ §6 節名を「JS 定数値 + data-col 属性値更新」に改訂・説明を (a)(b) 構造で拡張 / §6 改修対象メソッド一覧に thead テンプレート data-col 更新行追加（選択肢 A 補完 / builder.py L700 周辺）/ §6 thead テンプレート直後に「Wave 9 最終形」注記追加（I-I-N1）/ §6 colNames 配列サブセクション追加（Wave 9 後も 3 要素で正しい理由 / I-W-N1）/ §8 ソート機能テスト（data-col=3 経由）行追加（選択肢 A 補完 / AC-W9-N1 検証手段 3）/ §11 DQ-W9-2 を「選択肢 A 補完」で再訂正 |
| 0.2.6 | 2026-06-28 | spec-critic ラウンド 3 反映（Critical 1 / Warning 1 / Info 2 / 選択肢 A + sortTable aria-sort 修正 / 2026-06-28 ユーザー承認）— §1 修正最小性リストに「data-col 属性値更新 + sortTable() aria-sort ロジック修正」追記（I-I-R2）/ §6 節名を「JS 定数値 + data-col 属性値 + sortTable 修正」に改訂 / §6 colNames サブセクションに「Wave 9 後の問題」記述を追加し `idx === columnIndex` が担当/状態列で常に false になる理由を明示（I-C-R1）/ §6 aria-label 更新の正当性を colNames サブセクションに追記（I-I-R1）/ §6「(c) sortTable() aria-sort 更新ロジック修正」節を新設（変更前/変更後コード + 設計判断 / FR-W9-N1 (c) / NFR-W9-4）/ §6 改修対象メソッド一覧に「sortTable() aria-sort 更新ロジック（L391-408）」行追加（必須 / I-C-R1）/ §8 BUILDING 着手前チェックリストに FR-W9-N1 (a)(b)(c) 確認 3 項目追加（I-W-R1）/ §8 aria-sort 属性更新テスト行追加（NFR-W9-4 アクセシビリティ回帰防止 / AC-W9-N1 検証手段 6 対応）/ §11 DQ-W9-2 を最終訂正（案 A + 選択肢 A 補完 + sortTable() 修正の 3 点で解決済み / 検証手段 1-6 言及） |
| 0.2.7 | 2026-06-28 | 最終クリーニング / Green State 完全達成（Critical = 0 / Warning = 0 / Info = 0）— §6 (c) fallback `-1` 動作補足追記（description 列は NodeList 不参加のため現行設計では実際に発動しない / 将来的な aria-sort 追加時の安全網として維持 / I-I-RR1）/ §8 着手前確認 3 項目（FR-W9-N1 (a)(b)(c)）の冒頭に共通注記追加（事前確認 vs AC-W9-N1 実装後検証の区別を明示 / I-W-RR1）/ ヘッダ版数 v0.2.7 化 / 根拠文書・参照文書を v0.2.7 に統一 |

---

## §13 参照

- [wave9/requirements.md](./requirements.md)
- [元 design.md v0.2.3](../design.md)（§4 V-4 DOM 構成案・§5 TaskInfo/TasksParser・§8 CSS 更新済み）
- [wave7/design.md §6 Stage 2](../wave7/design.md)（Assignee 列実装パターン参照元）
- [wave8/design.md](../wave8/design.md)（波及参照：直近 Wave）
- [retro Wave 7](../../../artifacts/retro-W7-B5-2026-06-28.md)（Problem #10 / A10）
- [planning-quality-guideline](../../../../.claude/rules/planning-quality-guideline.md)
- [terminology](../../../../.claude/rules/terminology.md)
- [L2 委譲ガードレール](../../../artifacts/knowledge/l2-delegation-guardrails.md)
