# b4-dashboard Wave 9 — design.md

- バージョン: 0.2.3
- 作成日: 2026-06-28
- ステータス: Draft（PM 承認待ち）
- 根拠文書: `docs/specs/b4-dashboard/wave9/requirements.md` v0.2.3
- 参照文書:
  - `docs/specs/b4-dashboard/design.md` v0.2.3（元設計書 / §4 V-4 DOM 構成案・§5 TaskInfo/TasksParser・§8 CSS 更新済み）
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
3. **`builder.py`**: `_render_v4_tasks()` の `<thead>` に `<th id="th-description">` 追加 / `<tbody>` の各行に `<td class="description-cell">` 追加 / CSS に `.description-cell` ルール追加（HTML テンプレート追加）

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

**変更後（4 列）**:
```html
<tr>
  <th id="th-task-id" aria-sort="none">
    <button class="sort-btn" data-col="0" aria-label="Task IDで昇順にソート">Task ID</button>
  </th>
  <th id="th-description">description</th><!-- ソートボタンなし / aria-sort 属性なし（FR-W9-4 MUST NOT）-->
  <th id="th-assignee" aria-sort="none">
    <button class="sort-btn" data-col="1" aria-label="担当で昇順にソート">担当</button>
  </th>
  <th id="th-status" aria-sort="none">
    <button class="sort-btn" data-col="2" aria-label="状態で昇順にソート">状態</button>
  </th>
</tr>
```

> **data-col 再採番**: description 列が 2 列目に挿入されるため、
> 担当（旧 data-col=1 → 新 data-col=1 / 列位置は 3 列目へ変化）、
> 状態（旧 data-col=2 → 新 data-col=2 / 列位置は 4 列目へ変化）の
> data-col 数値は変わらない。ただし表示上の列位置（DOM の何番目 `<td>`）は 1 シフトする。
> 既存 JS の `applySort(col)` は `data-col` 値で列を特定するため、
> thead 側の data-col と tbody 側 `<td>` の物理位置が対応していれば動作する。
> **BUILDING で実動作確認が必須**（UQ-13 / AC-W9-4）。

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

| ファイル | メソッド | 改修内容 | 改修必要性 |
|:--------|:--------|:--------|:---------|
| `models.py` | `TaskInfo` | `description: str = ""` フィールド追加（FR-W9-2） | **必須** |
| `parsers/tasks.py` | `_extract_tasks()` | `description_clean, assignee = _extract_assignee(...)` に変更 + `TaskInfo` に `description=` 追加（FR-W9-3） | **必須** |
| `builder.py` | `_render_v4_tasks()` | `<thead>` に description 列追加 / `<tbody>` 各行に `<td class="description-cell">` 追加 | **必須** |
| `builder.py` | `_render_style()` 等 | `.description-cell` CSS ルール追加（FR-W9-5 SHOULD） | **推奨** |
| `parsers/session_state.py` | — | 変更なし（Wave 9 スコープ外） | 不要 |
| `parsers/current_phase.py` | — | 変更なし | 不要 |
| `parsers/git_history.py` | — | 変更なし | 不要 |
| `merger.py` | — | 変更なし（Wave 8 で新設済み） | 不要 |
| `build_dashboard.py` | — | 変更なし | 不要 |

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
| 改変なし | 既存の大多数（parsers テスト全件 / V-2/V-3 テスト全件 / Merger テスト全件） |

### BUILDING 着手前 L1 検証チェックリスト

BUILDING 着手前に L1 が以下を確認し、期待値更新件数を確定してから実装を開始すること:

- [ ] `test_v4_view.py` で V-4 の `<thead>` 列数を assert しているテスト件数を Grep
- [ ] `test_v4_view.py` で `<td>` 列数（1 行あたり 3 セル固定）を assert しているテスト件数を Grep
- [ ] `test_wave7_stage4_integration.py` で V-4 の HTML を assert している箇所を Grep
- [ ] `test_wave6_stage3_filter.py` でテーブル列数を assert している箇所を Grep
- [ ] `TaskInfo(id=..., milestone=..., status=..., assignee=...)` とキーワード引数省略で生成している既存テストを Grep（`description` 追加で引数不足エラーが出ないか確認）
- [ ] 期待値更新件数を確定し L1 承認を得てから BUILDING 着手

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
| DQ-W9-2 | 既存 applySort() JS と description 列の干渉 | `applySort()` が `data-col` 値（整数）でソート対象列を特定するため、`<th id="th-description">` に `data-col` がなければ干渉しない見込み。BUILDING で動作確認（AC-W9-4 / UQ-13） |
| DQ-W9-3 | test_v4_view.py の期待値更新件数 | BUILDING 着手前に L1 が Grep で確定する（§8 チェックリスト参照）。2〜6 件を想定 |
| DQ-W9-4 | description が `None` になるケース | `_extract_assignee()` は `str` を受け取り `str` を返す実装であり `None` は返さない。`raw_description` は `description[len(id_prefix):].strip()` で得られる `str` 型であるため `None` が渡ることはない。ただし BUILDING で型確認を実施する |

---

## §12 改訂履歴

| バージョン | 日付 | 変更内容 |
|:----------|:-----|:--------|
| 0.2.3 | 2026-06-28 | 初版起稿 — MAGI 合議（2026-06-28 B1/B2/B3）に基づく Wave 9 詳細設計。chip task_5de9563e 対応。§1〜§12 全セクション起草。TaskInfo フィールド追加・TasksParser 改修詳細・builder.py V-4 改修・CSS 設計・既存テスト影響事前分析 |

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
