# b4-dashboard Wave 8 — design.md

- バージョン: 0.2.3
- 作成日: 2026-06-28
- ステータス: Draft（PM 承認待ち）
- 根拠文書: `docs/specs/b4-dashboard/wave8/requirements.md` v0.2.0
- 参照文書:
  - `docs/specs/b4-dashboard/design.md` v0.2.0（元設計書 / パーサ独立性原則 §3 / Merger 仕様 §5）
  - `docs/specs/b4-dashboard/wave7/design.md` v0.2.4（直近 Wave / §8 Milestone 識別の実装ベース定義）
  - `docs/artifacts/retro-W7-B5-2026-06-28.md`（Wave 7 retro / chip task_68008f88 引き継ぎ）
- 設計方針: MAGI 合議（2026-06-28 / 案 5 採用）に基づく。元 design.md §5 を SSOT とし、本書は Wave 8 追加事項のみを記述する

---

## §1 Problem Statement

### chip task_68008f88 の核心

Wave 6 retro（2026-06-27）で起票された chip `task_68008f88` は
「`MilestoneInfo.name` vs `TaskInfo.milestone` 体系不整合」であり、
その根本原因は **V-2 Milestone 一覧と V-4 フィルタ選択肢がそれぞれ独立したデータソースを参照していること** にある。

現状の問題:

| ビュー | 参照元 | 乖離リスク |
|:------|:-------|:---------|
| V-2 Milestone 一覧 | `SessionStateParser` 逆引き（SESSION_STATE.md の Task ID から `B{n}` を抽出） | tasks.md にしか存在しない Milestone が V-2 に現れない |
| V-4 フィルタ選択肢 | `DashboardData.milestones`（= V-2 と同じ SessionState 逆引き） | V-2 と同一のデータを参照しているが、SSOT が「SessionState 逆引き」に固定されており tasks.md 由来の Milestone が欠落する |

Wave 7 では wave7/design.md §8「Milestone 識別の実装ベース定義」として SessionStateParser 逆引きを
暫定 SSOT としたが、これは「値の表現は揃っているがデータソース紐付きが弱い」状態であり、
正規化された集約レイヤが必要だった。

### Wave 6 retro 起票文（引用）

「Milestone フィルタ仕様乖離: `MilestoneInfo.name` vs `TaskInfo.milestone` 体系不整合（chip task_68008f88）」

Wave 6 PoC レビュー時に判明したこの問題は、tasks.md の `TaskInfo.milestone` と
SESSION_STATE.md から逆引きした `MilestoneInfo.name` が同一の Milestone を指しているにもかかわらず、
生成元が異なるためフィルタ機能の整合性が保証できないという問題だった。

---

## §2 Goals / Non-Goals

### Goals

- chip `task_68008f88` を `MilestoneSourceMerger` の導入で正式解決する
- V-2 と V-4 フィルタが常に同一 SSOT を参照する設計を確立する
- 将来の `MilestoneRegistry` 昇格に備えた `MilestoneProvider` Protocol 契約を切る
- 既存 4 パーサを無改変で維持し、Wave 7 終端の 398 テストを守る

### Non-Goals（設計スコープ外）

- 元 design.md §5 の再記述・移転（SSOT を一本化 / 本書では追加事項のみ記述）
- 既存 4 パーサ内部の改修（FR-W8-4 MUST NOT 準拠）
- FC-7 Step 別管理の実装
- MilestoneRegistry の本格実装
- CSS・UI 意匠面の変更

---

## §3 アーキテクチャ（集約レイヤ追加）

### 既存 4 パーサとの関係

```
[データソース層]         [パーサ層（無改変）]          [集約レイヤ（Wave 8 新設）]
SESSION_STATE.md  ──→  SessionStateParser  ──┐
                                             ├─→  MilestoneSourceMerger
tasks.md（全 Milestone 再帰走査）──→  TasksParser  ──┘
                                             ↓
                                    DashboardData.milestones（SSOT 確定）
                                             ↓
                                    DashboardBuilder（V-2 / V-4 フィルタ描画）

current-phase.md  ──→  CurrentPhaseParser  ──→  DashboardData.current_phase
git log           ──→  GitHistoryParser    ──→  DashboardData.completed_waves / タスク補完
```

**Merger の配置位置**: `build_dashboard.py`（オーケストレータ）が各パーサ結果を取得した後に
Merger を呼び出し、`DashboardData.milestones` を上書き確定する。
パーサ層と Merger は一方向依存（パーサ → Merger）であり、循環依存を持たない。

### Builder への注入差替方針（概念フロー）

> **I-C-1 反映（v0.2.1）**: §3 の DI スケッチは「概念図」として降格。
> 実装コードの正規版は §5 に記述する。ここではデータフローの意図のみを示す。

```
[パーサループ完了後]
  ↓
data.milestones ← SessionStateParser 逆引き結果（_merge_into() で設定済み）
data.tasks      ← TasksParser 結果（_merge_into() で設定済み）
  ↓
[Wave 8 追加 — Merger による SSOT 確定]
task_ms_names ← data.tasks の milestone 集合（set comprehension）
Merger(session_milestones=data.milestones, task_milestone_names=task_ms_names).get_milestones()
  ↓
data.milestones ← 統合済みリスト（上書き）
  ↓
[既存 Builder 呼び出し — 変更なし]
DashboardBuilder(data).render()
```

この設計により `DashboardBuilder` は `data.milestones` が Merger 由来か否かを知る必要がなく、
既存コード（`_render_v2_milestones()` / `_render_filter_controls()`）の変更が最小で済む。

---

## §4 MilestoneSourceMerger 詳細設計

### クラス図（I-C-3 反映 / v0.2.1）

> **I-C-3 変更**: `MilestoneProvider.get_milestones()` は無引数シグネチャ。
> `MilestoneSourceMerger` は constructor で 2 入力を受け取り、`get_milestones()` で Protocol を実装する。
> 旧 `merge()` は `_merge()` に private 化する。

```
merger.py
  ├─ MilestoneProvider（Protocol）
  │    └─ get_milestones() -> list[MilestoneInfo]    ← Protocol 実装 / 将来 Registry 差し替え契約
  └─ MilestoneSourceMerger（MilestoneProvider を実装 / MUST）
       ├─ __init__(session_milestones, task_milestone_names)  ← 2 入力を constructor で受け取る
       ├─ get_milestones() -> list[MilestoneInfo]   ← Protocol 実装 / _merge() を呼ぶ
       ├─ _merge() -> list[MilestoneInfo]           ← 内部統合ロジック（旧 merge()）
       └─ _make_milestone_from_name(name) -> MilestoneInfo  ← tasks 由来補完用
```

### 入力契約

| 引数 | 型 | 出所 | 失敗時 |
|:-----|:---|:-----|:-------|
| `session_milestones` | `list[MilestoneInfo]` | `SessionStateParser.parse()["data"]["milestones"]` | `ok=False` 時は空リスト `[]` を渡す |
| `task_milestone_names` | `list[str]` | `TasksParser.parse()["data"]["tasks"]` の `milestone` フィールドを `set` で集合化 | `ok=False` 時は空リスト `[]` を渡す |

> **I-C-2 反映（v0.2.1）**: `session_milestones` の `name` 重複なしは SessionStateParser 側で保証済み
> （`session_state.py` L195-209 の `seen_milestones` 機構による）。
> Merger は防衛として dict 変換で後勝ち集約するが、parser 側での重複発生は設計上想定しない。

> **I-W-6 反映（v0.2.1）**: Merger は `None` を受け取らない。
> `build_dashboard.py` が `ok=False` 時に `[]`（空リスト）に正規化する責務を持つ。
> Merger の constructor は `list` 型のみを受け入れる（型ヒントで明示）。

> **I-W-1 反映（v0.2.1）**: 本設計は現行 `.claude/scripts/dashboard/models.py` の
> `TaskInfo.status: str` を前提とする。wave7/design.md §7 の `TaskStatus` 型記述は別件であり、
> 本 Wave 8 では `TaskStatus` 型化は扱わない（I-W-1 / §11 DQ-4 追加）。

### 出力契約

| 戻り値 | 型 | 説明 |
|:-------|:---|:----|
| 統合 Milestone リスト | `list[MilestoneInfo]` | 重複排除・name 昇順（文字列辞書順）ソート済み。`DashboardData.milestones` に直接代入される |

**ソート保証**: name の文字列辞書順（Python デフォルトの `str` 比較）。Wave 7 A3-4 踏襲。
将来 `B-10` 以降で辞書順と数値順が乖離した場合は Wave 8+ で自然順ソートに変更可能（互換破壊なし）。

### merge ロジック（集合演算 / I-C-3 constructor 注入版 / v0.2.1）

> **I-C-3 変更**: constructor 注入後は `get_milestones()` が公開 API。
> `_merge()` が内部ロジックを担う。

```python
class MilestoneSourceMerger:
    def __init__(
        self,
        session_milestones: list[MilestoneInfo],
        task_milestone_names: list[str],
    ) -> None:
        self._session_milestones = session_milestones
        self._task_milestone_names = task_milestone_names

    def get_milestones(self) -> list[MilestoneInfo]:
        """Protocol MilestoneProvider 実装。統合後 Milestone リストを返す（MUST）。"""
        return self._merge()

    def _merge(self) -> list[MilestoneInfo]:
        """内部統合ロジック。

        アルゴリズム:
        1. session_milestones を dict[name → MilestoneInfo] に変換（重複排除・後勝ち）
        2. task_milestone_names を走査し、session dict に存在しない name を補完追加
        3. 全エントリを name 昇順ソートして返す

        エラー耐障害性:
        - 片方が空リストでも継続（MUST）
        - 両方が空なら空リストを返す（MUST）
        """
        # Step 1: session 由来を name → MilestoneInfo の dict にする
        session_dict: dict[str, MilestoneInfo] = {
            ms.name: ms for ms in self._session_milestones
        }

        # Step 2: tasks 由来のうち session にない name を補完追加
        for name in self._task_milestone_names:
            if name not in session_dict:
                session_dict[name] = self._make_milestone_from_name(name)

        # Step 3: 名前昇順ソート
        return sorted(session_dict.values(), key=lambda ms: ms.name)

    def _make_milestone_from_name(self, name: str) -> MilestoneInfo:
        """tasks.md 由来のみのエントリを補完生成する。

        status: "unknown"（SESSION_STATE.md は揮発的 (gitignore/セッション切替で変動) のため
                「SESSION_STATE にない = 未着手」とは限らない。完了済み Milestone の誤情報リスクを
                回避するため、補完は中立な "unknown" とする）
        current_step: "UNKNOWN"（CurrentPhaseParser は別途 DashboardData.current_phase に反映）

        Note (I-I-2): 下記 from インポートは循環インポート回避用（BUILDING で確定）。
        """
        from dashboard.models import MilestoneInfo  # 循環インポート回避用（I-I-2）
        # ※ I-I-N4: merger.py が dashboard/ 直下配置の場合、`from .models import MilestoneInfo` の
        #   モジュールレベルインポートが可能な可能性あり。循環インポートの実発生有無を BUILDING 段階で
        #   確認し、不要なら遅延インポートをモジュールレベルに昇格する（DQ-N1 として §11 に追記済）。
        return MilestoneInfo(name=name, current_step="UNKNOWN", status="unknown")
```

### 重複排除ルール

同一 `name` が session と tasks の両方に存在する場合:
- `session_dict[name]` が優先（step 1 で session の MilestoneInfo を保持）
- tasks 由来エントリは無視（status や current_step の上書きなし）

**設計根拠（I-W-2 反映 / v0.2.1）**: SESSION_STATE.md は gitignore 対象かつセッション切替で変動する揮発的ファイルである。
tasks.md 由来のみの Milestone は `status="unknown"` で補完する（`"not-started"` ではない）。
「SESSION_STATE.md に記録がない = 未着手」とは限らず、完了済み Milestone が誤って `"not-started"` 表示されるリスクを回避するため、
補完値は中立な `"unknown"` とする。
session 由来エントリは `status` 属性（`in-progress` 等）の信頼性が高いため優先する。

### 出典タグ（将来拡張向け）

現実装では出典タグ（`sources: list[str]`）は実装しない（Wave 8 のシンプル化のため）。
将来 Registry 昇格時に `MergedMilestone` 型として拡張可能な設計にしておく（element design.md §5 参照）。

### エラー耐障害性

| ケース | 挙動 |
|:------|:----|
| `session_milestones` が `[]` | tasks のみで構築して返す（MUST） |
| `task_milestone_names` が `[]` | session のみを返す（MUST） |
| 両方が `[]` | 空リストを返す（MUST）。V-2 は「Milestone 情報なし」empty state を表示 |
| session 内重複（例: session に B-5 が 2 件）| dict 変換で後勝ちで 1 件に集約（防衛的実装）。parser 側 `seen_milestones` 機構が一次保証（I-C-2） |
| `None` が渡された場合 | 想定外（build_dashboard.py 側で `ok=False` 時に `[]` に正規化する責務）。Merger の constructor は `list` 型のみ受け入れ（I-W-6） |

---

## §5 Builder への注入差替方針

### 既存 Builder コードへの影響（最小化）

`DashboardBuilder._render_v2_milestones()` および `_render_filter_controls()` は
`self.data.milestones` を参照している。Wave 8 では `DashboardData.milestones` が
Merger 確定済みリストを保持した状態で Builder が呼ばれるため、
**Builder の内部コードは変更不要**である。

変更対象は `build_dashboard.py` の `_merge_into()` 関数付近のオーケストレータロジックのみ。

### `build_dashboard.py` の変更点（正規スケッチ / I-C-1 反映 / v0.2.1）

> **I-C-1 反映**: §3 の DI スケッチは概念図に降格済み。本節（§5）が実装の正規版スケッチ。
> 現行 `_run_parsers()` / `_merge_into()` 構造を前提とし、以下のフローで確定する。

```python
from dashboard.merger import MilestoneSourceMerger

def build(project_root: Path, output_path: Path) -> int:
    data = DashboardData(generated_at=datetime.now().isoformat())

    parsers = [
        ("SessionState",  SessionStateParser(project_root)),
        ("CurrentPhase",  CurrentPhaseParser(project_root)),
        ("Tasks",         TasksParser(project_root)),
        ("GitHistory",    GitHistoryParser(project_root)),
    ]

    # 既存ループ（変更なし） — _merge_into() で data に各パーサ結果をマージ
    for name, parser in parsers:
        try:
            result = parser.parse()
            if result["ok"]:
                _merge_into(data, name, result["data"])
            else:
                data.parser_errors.append(f"{name}: {result['error']}")
        except Exception as e:
            data.parser_errors.append(f"{name}: unexpected error: {e}")

    # ↓ Wave 8 追加: パーサループ完了後（data.tasks 確定後）に Merger を実行
    # task_ms_names は data.tasks（TasksParser 結果）から milestone 集合を取得
    task_ms_names = list({t.milestone for t in data.tasks})
    # constructor 注入版（I-C-3）: session_milestones と task_ms_names を __init__ で受け取る
    data.milestones = MilestoneSourceMerger(
        session_milestones=data.milestones,
        task_milestone_names=task_ms_names,
    ).get_milestones()

    # 既存 Builder 呼び出し（変更なし）
    output_path.parent.mkdir(parents=True, exist_ok=True)
    html_content = DashboardBuilder(data).render()
    output_path.write_text(html_content, encoding="utf-8")
    return 1 if data.parser_errors else 0
```

**注意**: 上記は現行構造を前提とした正規スケッチ。実際の `_merge_into()` 実装は
既存コードに合わせて BUILDING フェーズで調整する。
`data.tasks` が確定した後（パーサループ完了後）に Merger を呼び出すことが必須。

---

## §6 V-2 / V-4 描画ロジック整合化

### V-2 _render_v2_milestones() の整合

Wave 8 実装後:
- `self.data.milestones` は Merger 確定済みリスト（SessionState ∪ tasks.md 由来）
- `_render_v2_milestones()` 内のコードは **変更不要**
  （Wave 7 で実装した `sorted(self.data.milestones, key=lambda m: m.name)` の昇順ソートが継続）
- Merger が昇順ソート済みリストを返すため、Builder 側の再ソートはあっても無害

### V-4 _render_filter_controls() の整合

Wave 8 実装後:
- `self.data.milestones` は Merger 確定済みリスト
- `_render_filter_controls()` 内の `for ms in self.data.milestones:` が Merger 結果を参照するため **変更不要**
- V-4 フィルタ選択肢 ∩ V-2 カード = `data.milestones` で完全一致が保証される

### "unknown" バッジ実装範囲（I-W-N2 / v0.2.2 追加）

Wave 8 で `MilestoneSourceMerger` が補完する `status="unknown"` Milestone に対して、
`DashboardBuilder` が正しいバッジを描画するために以下を追加実装する（FR-W8-N2 MUST）。

**改修対象**:
- `builder.py` の `_STATUS_LABELS` 辞書: `"unknown": "不明"` を追加
- `builder.py` の inline CSS 生成箇所: `.badge[data-status="unknown"] { background: <gray-9相当>; color: #fff; }` を追加

**改修範囲外**:
- 既存 4 値（`completed` / `in-progress` / `blocked` / `not-started`）の挙動・配色は無改変（MUST）
- CSS の意匠面変更（配色テーマ変更・レイアウト変更）は対象外

**配色**: Radix Colors gray-9 相当（`#9ca3af` 等）。BUILDING で実測後に確定する。

### 改修対象メソッド一覧（v0.2.2 更新）

| ファイル | メソッド | 改修内容 | 改修必要性 |
|:--------|:--------|:--------|:---------|
| `build_dashboard.py` | `build()` | Merger 呼び出し追加（パーサループ後） | **必須** |
| `builder.py` | `_STATUS_LABELS` | `"unknown": "不明"` エントリ追加（FR-W8-N2） | **必須** |
| `builder.py` | `_render_style()` 等 | `.badge[data-status="unknown"]` CSS ルール追加（FR-W8-N2） | **必須** |
| `builder.py` | `_render_v2_milestones()` | 変更なし | 不要 |
| `builder.py` | `_render_filter_controls()` | 変更なし | 不要 |
| `merger.py` | 新規ファイル | `MilestoneSourceMerger` / `MilestoneProvider` 実装 | **新規作成** |

---

## §7 既存テスト影響事前分析（ガードレール #4）

### parsers/ 配下: 改変なしを保証

| テストファイル | 想定影響 | 対応 |
|:-------------|:--------|:----|
| `test_session_state_parser.py` | なし | 改変なし確認 |
| `test_current_phase_parser.py` | なし | 改変なし確認 |
| `test_tasks_parser.py` | なし（Wave 7 T56 分含む） | 改変なし確認 |
| `test_git_history_parser.py` | なし | 改変なし確認 |

### builder.py: 最小限の変更

| テストファイル | 想定影響 | 対応 |
|:-------------|:--------|:----|
| `test_v2_view.py` | `data.milestones` が Merger 由来に変わるが、テスト側フィクスチャを Merger 経由に設定すれば影響なし | フィクスチャ確認のみ（改変なし or 最小） |
| `test_v4_view.py` | フィルタ選択肢のテストが `data.milestones` を参照 → 同上 | フィクスチャ確認のみ |
| `test_wave6_stage3_filter.py` | フィルタ UI テスト → `data.milestones` フィクスチャを Merger 対応に調整 | 最小調整（L1 事前承認） |
| `test_wave7_stage3_milestones.py` | V-2 複数 Milestone テスト → Merger 経由で同等結果が得られるか確認 | 確認のみ（改変なし見込み） |

### tests/dashboard/: 影響受けるテストファイル列挙

| テストファイル | 分類 | 対応 |
|:-------------|:----|:----|
| `test_base_parser.py` | 改変なし | パーサ独立性テスト / Merger 無関係 |
| `test_build_dashboard.py` | 最小調整 | `build()` 関数のオーケストレータ変更に伴い、統合テストのフィクスチャまたは mock が必要になる可能性 |
| `test_session_state_parser.py` | 改変なし | — |
| `test_tasks_parser.py` | 改変なし | — |
| `test_v2_view.py` | 改変なし（見込み） | `data.milestones` を直接設定するテストは Merger 経由を前提にしなくてよい（Builder は data を受け取るだけ） |
| `test_v4_view.py` | 改変なし（見込み） | 同上 |
| `test_wave6_stage3_filter.py` | 最小調整（L1 事前承認） | フィルタ選択肢テストが data.milestones を参照 |
| `test_wave7_stage3_milestones.py` | 確認のみ | V-2 複数 Milestone テストが Merger 経由でも同等結果か確認 |
| `test_wave7_stage4_integration.py` | 確認のみ | 統合テスト全体が Merger 追加後も PASS か確認 |
| `test_v2_view.py` / `test_v4_view.py`（"unknown" バッジ） | 追加可能性（I-W-N2） | `_STATUS_LABELS["unknown"]` 追加により `_render_status_badge()` 経由で V-2/V-3/V-4 全ビューへ波及。"unknown" status の Milestone フィクスチャを含むテストで期待値追加が必要になる可能性 |

**総予測**:
- 新規テスト: `test_wave8_merger.py`（Merger 単体 / 6〜10 件想定）+ `test_wave8_integration.py`（統合 / 6〜9 件想定）
- 期待値更新: **1〜5 件（I-W-3 反映）**。BUILDING 着手前に L1 が `test_build_dashboard.py` を Grep して
  `data.milestones` 内容・順序を assert しているテストを特定し、確定後に再見積もりする
- 改変なし: 既存 398 件のうち大多数

### BUILDING 着手前 L1 検証チェックリスト（I-W-3 追加）

BUILDING 着手前に L1 が以下を確認し、期待値更新件数を確定してから実装を開始すること:

- [ ] `test_build_dashboard.py` で `data.milestones` の内容を assert しているテスト件数を Grep
- [ ] `data.milestones` の順序（例: B-4 → B-5）を検証しているテスト件数を Grep
- [ ] Merger 統合により期待値が変わるテストを列挙
- [ ] 期待値更新件数を確定し L1 承認を得てから BUILDING 着手
- [ ] AC-W8-3 フィクスチャパスを確定し AC-W8-3 を更新する（例: `tests/dashboard/fixtures/wave8/session_minimal.txt` の正式名確定 / I-I-N3）
- [ ] `_STATUS_LABELS` に `"unknown"` 追加後、`data-status="unknown"` を assert する既存テストを Grep して影響件数を確認（I-W-N2）

---

## §8 Alternatives Considered

### 案 1（却下）: 軽量パッチ — TasksParser に直接 Milestone 集合を SessionStateParser に渡す

**内容**: SessionStateParser が TasksParser の結果を参照して自分の milestones を補完する。

**Pros**: 変更最小 / 既存テスト影響なし
**Cons**: パーサ独立性原則（design.md §3）の直接違反 / パーサ間の依存が生まれる / テスト困難

**却下理由**: design.md §3「各パーサは他のパーサの結果に依存してはならない（MUST NOT）」に反する。

### 案 2（当初案 / 却下）: TasksParser 内部で Milestone を SessionState 逆引きと統合する

**内容**: TasksParser が `_merge_milestone_with_session_state()` を持ち、自前で統合する。

**Pros**: Merger 不要 / ファイル追加なし
**Cons**: TasksParser が SESSION_STATE.md 依存を持ち、SRP 違反 / テスト複雑化

**却下理由**: 案 1 と同様の原則違反。

### 案 3（却下）: 即時 MilestoneRegistry 本格化

**内容**: 最初から `MilestoneRegistry` として実装し、データソース管理を統合的に行う。

**Pros**: 将来の拡張に強い
**Cons**: 骨子 ⑥ の設計が未確定 / 過剰実装（YAGNI） / Wave 8 スコープが大幅拡大

**却下理由**: 骨子 ⑥ の設計なしに Registry の要件が定まらない。案 5 で踏み石を設けておけば将来に対応可能。

### 案 4（参考）: build_dashboard.py でのアドホック統合

**内容**: `build_dashboard.py` 内で直接集合演算を行い、`data.milestones` を上書きする（クラスを設けない）。

**Pros**: ファイル追加なし / 即実装可能
**Cons**: ロジックがオーケストレータに埋没 / テスト困難 / Registry 昇格時の差し替えが困難

**却下理由**: 将来の Protocol 差し替えが困難。テスト容易性の観点から `merger.py` としてクラス化する方が優る。

### 案 5（採用）: MilestoneSourceMerger を案 3 Registry への踏み石化

**内容**: `MilestoneSourceMerger` を新設（上位集約レイヤ）。`MilestoneProvider` Protocol を定義し、
将来の Registry 差し替えに備える。パーサは無改変。

**Pros**:
- パーサ独立性原則を維持
- 案 3（Registry）への昇格パスを保持
- テスト容易（Merger 単体 / 統合の両方でテスト可能）
- `build_dashboard.py` の変更が局所的
- 既存 Builder コードは変更不要

**Cons**:
- ファイル追加（`merger.py`）
- オーケストレータに Merger 呼び出しを追加する必要がある

**採用理由**:
- MAGI 合議（2026-06-28）で BALTHASAR の「パーサ独立性原則への懸念」と MELCHIOR の「Registry 即時化の推進」を CASPAR が「踏み石化」で統合
- Wave 8 の実装コストを最小化しつつ、将来 Registry への昇格パスを保全する

---

## §9 Success Criteria

`wave8/requirements.md` §5 の AC-W8-1〜7 および AC-W8-N1 を満たすことで設計の成功とみなす。

追加の設計成功条件:

| 条件 | 確認方法 |
|:-----|:--------|
| 既存テスト退行ゼロ | Wave 8 実装後の pytest 全件 PASS |
| V-2 と V-4 フィルタの Milestone SSOT 一致 | 統合テストで `data.milestones` が両箇所で同一参照 |
| パーサ無改変確認 | 4 パーサの git diff が空（ファイル変更なし） |
| Merger 単体テスト | `test_wave8_merger.py` 全件 PASS |

---

## §10 Registry 昇格契約（将来 ⑥ A 設計時の継承点）

### Protocol スケッチ

```python
# merger.py に定義する
from typing import Protocol, runtime_checkable
from dashboard.models import MilestoneInfo


@runtime_checkable
class MilestoneProvider(Protocol):
    """Milestone 一覧を提供するコンポーネントの契約（将来 Registry 差し替え用）。

    MilestoneSourceMerger（Wave 8）も MilestoneRegistry（将来 ⑥ A）も
    このプロトコルを実装することで、build_dashboard.py の変更なしに差し替え可能にする。

    メソッド名は仮称。将来 Registry 設計時に確定する。
    """

    def get_milestones(self) -> list[MilestoneInfo]:
        """統合済みの Milestone リストを返す。"""
        ...
```

### 将来の MilestoneRegistry との継承点（I-C-3 / I-W-5 反映 / v0.2.1）

**MUST**: `MilestoneSourceMerger` は `MilestoneProvider` Protocol を実装しなければならない。
constructor 引数で session/tasks を受け取り、`get_milestones()` で Protocol 契約を直接実装する。

| 継承点 | Wave 8 設計での対応 |
|:------|:-----------------|
| `MilestoneProvider` Protocol を実装する | **MUST**: `MilestoneSourceMerger` が `get_milestones()` を実装（型ヒントで明示）|
| constructor で session/tasks を受け取る | `__init__(session_milestones, task_milestone_names)` で DI（I-C-3）|
| `build_dashboard.py` は型を `MilestoneProvider` として受け取る | Wave 8 実装で `MilestoneProvider` 型の変数として Merger を保持する設計（MUST / G4 達成条件 3 と整合 / I-W-N1 反映 v0.2.2）|
| FC-7 Step 別管理 | Registry 昇格時に `get_milestones_by_step()` 等の追加メソッドで対応可能 |

---

## §11 未解決事項 / 設計判断ログ

| ID | 事項 | 判断方針 |
|:---|:----|:--------|
| DQ-1 | `merger.py` の配置を `parsers/` 配下にするか `dashboard/` 直下にするか | `dashboard/` 直下を採用（パーサ層とは別の集約レイヤであることを明示 / design.md §6 スクリプト配置で確定済み） |
| DQ-2 | `MilestoneProvider.get_milestones()` のシグネチャ最終決定 | I-C-3 反映（v0.2.1）で確定: `get_milestones()` を Protocol の直接実装とし、constructor 注入で session/tasks を受け取る。`_merge()` が内部ロジックを担う |
| DQ-3 | `test_wave8_merger.py` と `test_wave8_integration.py` の境界定義 | 単体: Merger のみをテスト（パーサは mock）/ 統合: `build_dashboard.py` の `build()` をテスト（実ファイル使用） |
| DQ-4 | `TaskStatus` 型化（wave7/design.md §7 記述）との整合 | 本 Wave 8 では扱わない（I-W-1）。現行 `TaskInfo.status: str` を前提とする。`TaskStatus` 型化は別 chip 起票候補として Wave 8+ で検討 |
| DQ-N1 | `_make_milestone_from_name` の遅延インポート要否 | BUILDING 段階で循環インポートの実発生有無を確認する。`merger.py` が `dashboard/` 直下配置のため `from .models import MilestoneInfo` のモジュールレベルインポートが可能な可能性あり。循環なければモジュールレベルに昇格する（I-I-N4）|

---

## §12 改訂履歴

| バージョン | 日付 | 変更内容 |
|:----------|:-----|:--------|
| 0.2.0 | 2026-06-28 | 初版起稿 — MAGI 合議（2026-06-28 / 案 5 採用）に基づく Wave 8 詳細設計。§1〜§12 全セクション起草。chip task_68008f88 対応設計。MilestoneSourceMerger クラス設計・merge ロジック・Registry 昇格契約 |
| 0.2.1 | 2026-06-28 | spec-critic レビュー反映（Critical 3 / Warning 6 / Info 4 / L1 追加 1）— §3 DI スケッチを概念図に降格（I-C-1）/ §4 クラス図を constructor 注入版に変更（I-C-3）/ §4 入力契約に重複なし保証・None 非受領・TaskStatus 型ドリフト前提を追記（I-C-2 / I-W-1 / I-W-6）/ §4 merge ロジックを constructor 注入版に更新（I-C-1 / I-C-3）/ §4 補完 status "not-started" → "unknown"（I-W-2）/ §4 エラー耐障害性に session 内重複・None ケース追加（I-C-2 / I-W-6）/ §5 build_dashboard.py スケッチを正規版に確定（I-C-1 / I-C-3）/ §7 期待値更新を 1〜5 件に範囲化・L1 検証チェックリスト追加（I-W-3）/ §10 Registry 昇格契約を MUST 昇格（I-W-5）/ §11 DQ-4（TaskStatus 型化別件）追加（I-W-1）|
| 0.2.2 | 2026-06-28 | spec-critic ラウンド 2 反映（Warning 2 / Info 4 / "unknown" バッジ Wave 8 スコープ化）— §3 typo「波状」→「completed_waves」修正（I-I-N1）/ §3 概念フロー引数記法統一（I-I-N2）/ §4 遅延インポート Note 追加・DQ-N1 追加（I-I-N4）/ §6 "unknown" バッジ実装範囲節追加・改修対象メソッド一覧更新（I-W-N2）/ §7 `_STATUS_LABELS` 波及テスト行追加・L1 検証チェックリストに fixture パス確定・バッジ確認項目追加（I-I-N3 / I-W-N2）/ §10 継承点テーブル SHOULD → MUST（I-W-N1）/ §11 DQ-N1 追加（I-I-N4）|
| 0.2.3 | 2026-06-28 | spec-critic ラウンド 3 反映 / 最終クリーニング（Warning 2 + Info 3）— §9 Success Criteria を「AC-W8-1〜7 および AC-W8-N1」に更新（I-W-N3）|

---

## §13 参照

- [wave8/requirements.md](./requirements.md)
- [元 design.md v0.2.0](../design.md)（§3 アーキ図 / §5 Merger 仕様 / §6 スクリプト配置）
- [wave7/design.md §8](../wave7/design.md)（Milestone 識別の実装ベース定義 / 暫定 SSOT）
- [future-candidates.md FC-7 / FC-10](../future-candidates.md)
- [retro Wave 7](../../../artifacts/retro-W7-B5-2026-06-28.md)
- [retro Wave 6](../../../artifacts/retro-W6-B5-2026-06-27.md)（chip task_68008f88 起票文）
- [L2 委譲ガードレール](../../../artifacts/knowledge/l2-delegation-guardrails.md)
- [planning-quality-guideline](../../../../.claude/rules/planning-quality-guideline.md)
- [terminology](../../../../.claude/rules/terminology.md)
