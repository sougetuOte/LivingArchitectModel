# b4-dashboard Wave 8 — requirements.md

- バージョン: 0.2.3
- 作成日: 2026-06-28
- ステータス: Draft（PM 承認待ち）
- マイルストーン: B-5（Wave 8 / Milestone フィルタ仕様乖離解決）
- 関連:
  - `docs/specs/b4-dashboard/requirements.md` v0.2.0（PoC 仕様 / 継承元）
  - `docs/specs/b4-dashboard/design.md` v0.2.0（元設計書 / Wave 8 §Non-Goals・§3・§4・§5 更新済み）
  - `docs/specs/b4-dashboard/wave7/requirements.md` v0.2.4（直近 Wave / FR-W7-1〜4 継承元）
  - `docs/specs/b4-dashboard/future-candidates.md` FC-7 / FC-10
  - `docs/artifacts/retro-W7-B5-2026-06-28.md`（Wave 7 retro / 引き継ぎ事項）
  - 起源 chip: `task_68008f88`（Milestone フィルタ仕様乖離）

---

## §1 概要 / Problem Statement

### 起源

chip `task_68008f88` は Wave 6 retro（2026-06-27）で起票された。Wave 6 PoC レビュー時に判明した
「`MilestoneInfo.name` と `TaskInfo.milestone` 体系不整合」に起因する Milestone フィルタ仕様乖離が
根本問題である。

### 問題の核心

| 問題 | 現状 | 影響 |
|:-----|:-----|:----|
| **データソース乖離** | V-2 Milestone 一覧と V-4 フィルタ選択肢のデータソースが実質的に分離している（SessionStateParser の逆引き ≠ TasksParser の tasks.milestone 集合） | 同一 Milestone が V-2 と V-4 フィルタで不一致になるリスクがある |
| **tasks.md 由来の Milestone が欠落** | V-2 は SESSION_STATE.md の Task ID 逆引きのみ。tasks.md にしか存在しない Milestone は V-2 に現れない | フィルタ選択肢と実際の Task 分類が乖離する |
| **元 design.md §5 の Milestone 検出記述が実装と乖離** | 元 design.md §5 は「`docs/specs/` 直下の glob 走査」と記述していたが、実装は Task ID からの逆引き（SessionStateParser）と再帰走査（TasksParser T56） | 仕様と実装の間の ドリフト |

Wave 7 では「実装ベース SSOT」として SessionStateParser 逆引きを暫定維持したが（wave7/design.md §8）、
Wave 8 では `MilestoneSourceMerger` を新設してこの乖離を正式解決する。

### 設計観点の追加問題

| 問題 | 設計上の影響 |
|------|------------|
| SessionState と tasks.md の双方から Milestone を取得する統合レイヤが存在しない | V-2 と V-4 フィルタが常に一致する保証ができない |
| パーサの独立性原則（design.md §3）を崩さずに集約する方法が未設計 | 単純に TasksParser 結果を SessionStateParser 内で参照すると原則違反 |

---

## §2 Goals / Non-Goals

### Goals

| Goal | 指標 | 達成判定 |
|:-----|:-----|:--------|
| G1: Milestone フィルタ仕様乖離の解消 | V-2 Milestone 一覧と V-4 フィルタ選択肢が常に同一 SSOT（MilestoneSourceMerger）を参照する | dashboard.html 上で V-2 表示と V-4 フィルタ選択肢の Milestone 集合が一致する |
| G2: tasks.md 由来の Milestone 反映 | tasks.md の Task ID から逆引きした Milestone が V-2 と V-4 フィルタに反映される | tasks.md にしか存在しない Milestone が dashboard に表示される（統合テストで確認） |
| G3: パーサ独立性原則の維持 | 既存 4 パーサ（SessionState / CurrentPhase / Tasks / GitHistory）は無改変 | 既存 398 テストが改変なし or 最小で維持される |
| G4: Registry 昇格契約の確立（MUST / I-W-5 反映） | `MilestoneProvider` Protocol を定義し、MilestoneSourceMerger が Protocol を実装し、build_dashboard.py が MilestoneProvider 型で Merger を参照する | 達成条件: (1) `MilestoneProvider` Protocol が wave8/design.md §10 に定義されている (2) `MilestoneSourceMerger` が `MilestoneProvider` を実装している（型ヒントで明示） (3) `build_dashboard.py` の Merger 利用箇所が `MilestoneProvider` 型として参照されている |
| G5: Wave 7 達成値の退行防止 | pytest 全件 PASS / Lighthouse Accessibility ≥ 95 / CSS ≤ 16,384 bytes | Stage 末の全件確認で達成 |

### Non-Goals（明示的に Wave 8 で対応しないこと）

- **MilestoneRegistry 本格化（案 3）**: `MilestoneSourceMerger` を将来の Registry 昇格への踏み石と位置付けるが、Registry 自体の実装は本 Wave のスコープ外。骨子 ⑥（プロジェクト俯瞰オーケストレータ）の設計確定後に実施する（FC-10）
- **FC-7 Step 別管理**: Milestone 別の Step（PLANNING/BUILDING/AUDITING）管理は引き続き将来候補。Merger はデータソース統合（集合演算）のみを担い、Step 情報は扱わない
- **双方向同期**: Merger は read-only 集約レイヤであり、SessionState や tasks.md への書き戻し（双方向同期）は行わない（MUST NOT）
- **V-4 description 列追加**: chip `task_5de9563e`（Wave 7 PoC 指摘）の対応は Wave 8 PLANNING で別途取込判断を行う（Wave 7 retro A10 参照）
- **既存 4 パーサの改修**: SessionState / CurrentPhase / Tasks / GitHistory の各パーサ内部は変更しない（MUST NOT modify）
- **CSS の意匠面変更**: Wave 8 は Merger 追加に伴う最小限の改修にとどめ、CSS の意匠変更は行わない
  ※ 例外: `"unknown"` バッジ 1 エントリの追加（機能的正確性・表示崩れ防止）は許可する。
    意匠変更ではなく機能要件（FR-W8-N2）として Wave 8 スコープ内とする（I-W-N2 / v0.2.2）。

---

## §3 機能要件（FR）

> ※ FR-W8-N* / AC-W8-N* の "N" は "New" の意。v0.2.2 で新規追加された要件であることを示す
> マーカーとして使用する（既存連番 FR-W8-1〜6 / AC-W8-1〜7 との衝突回避 + 追加経緯の可視化）。（I-I-N5 v0.2.3）

### FR-W8-1: MilestoneSourceMerger の統合提供（MUST）

`MilestoneSourceMerger` は SessionStateParser が返す Milestone 集合（`list[MilestoneInfo]`）と
TasksParser が返す tasks から抽出した Milestone 名集合（`list[str]`）を集合演算（和集合）で統合し、
単一の SSOT として `DashboardData.milestones` に反映しなければならない（MUST）。

**MUST 項目**:
- SessionState 由来と tasks.md 由来の両 Milestone 集合の和集合を取る（MUST）
- 重複を排除し、name 昇順（文字列辞書順）でソートして返す（MUST）
- SessionState 由来エントリは status 属性（`in-progress` 等）を保持する（MUST）
- tasks.md 由来のみのエントリは `status="unknown"` で補完する（MUST）
  （SESSION_STATE.md は揮発的なため「記録なし = 未着手」とは限らない。完了済み Milestone の誤表示リスク回避のため "unknown" を使用。詳細: wave8/design.md §4 重複排除ルール）
- `build_dashboard.py` オーケストレータが各パーサ結果を取得後に Merger に渡す設計とする（MUST）
  （パーサが Merger を直接参照してはならない / パーサ独立性原則 MUST NOT 違反防止）

**根拠**: chip `task_68008f88` — V-2 と V-4 フィルタの Milestone SSOT が乖離しており、
同一 Milestone が 2 つの場所で不一致になるリスクがある。

### FR-W8-2: V-2 ビューの Milestone SSOT を Merger に変更（MUST）

V-2 Milestone 一覧ビューが表示する Milestone リストは、`MilestoneSourceMerger` の統合結果を
SSOT としなければならない（MUST）。

**MUST 項目**:
- `DashboardBuilder._render_v2_milestones()` は `self.data.milestones`（Merger 確定済みリスト）をそのまま使用する（MUST）
- 表示順は name 昇順を継続する（MUST / Wave 7 A3-4 踏襲）
- Wave 7 で実装した `<article class="milestone-card">` 構造を維持する（MUST / 後方互換）

### FR-W8-3: V-4 フィルタ選択肢の Milestone SSOT を Merger に変更（MUST）

V-4 Task 一覧ビューの「Milestone フィルタ」選択肢は、`MilestoneSourceMerger` の統合結果を
SSOT としなければならない（MUST）。

**MUST 項目**:
- `DashboardBuilder._render_filter_controls()` の `self.data.milestones`（Merger 確定済みリスト）から選択肢を生成する（MUST）
- Wave 6 で実装した `<select id="filter-milestone">` 構造を維持する（MUST / 後方互換）

### FR-W8-4: 既存 4 パーサの無改変（MUST NOT modify）

以下の既存パーサはコードを改変してはならない（MUST NOT）:

- `SessionStateParser`（`parsers/session_state.py`）
- `CurrentPhaseParser`（`parsers/current_phase.py`）
- `TasksParser`（`parsers/tasks.py`）
- `GitHistoryParser`（`parsers/git_history.py`）

**根拠**: パーサ独立性原則（design.md §3）を維持する。既存 398 テストへの影響を最小化する。

### FR-W8-5: MilestoneProvider Protocol の定義（MUST / I-W-5 反映 v0.2.1）

`MilestoneSourceMerger` が実装する `MilestoneProvider` Protocol を定義しなければならない（MUST）。

**MUST 項目**:
- `merger.py` に `MilestoneProvider` Protocol を定義する（MUST）
- `MilestoneSourceMerger` が `MilestoneProvider` を実装する（型ヒントで明示 / MUST）
- `build_dashboard.py` のオーケストレータは `MilestoneProvider` 型として Merger を参照する（MUST）
- 将来 `MilestoneRegistry` が同 Protocol を実装することで差し替え可能にする（継承点 / wave8/design.md §10）

### FR-W8-6: エラー耐障害性（MUST）

`MilestoneSourceMerger` は以下のエラーケースで動作を継続しなければならない（MUST）:

- `session_milestones` が空リストの場合: `task_milestone_names` のみで構築して継続する（MUST）
- `task_milestone_names` が空リストの場合: `session_milestones` のみを返す（MUST）
- 両方が空の場合: 空リストを返す。ダッシュボードは「Milestone 情報なし」を表示する（MUST）
- 片方のパーサが `ok=False` を返した場合: もう片方の結果のみで Merger を実行する（MUST）

### FR-W8-N2: "unknown" status バッジ表示（MUST / v0.2.2 新規追加 / I-W-N2）

Wave 8 で `MilestoneSourceMerger` が補完する `status="unknown"` の Milestone に対し、
`DashboardBuilder` は `data-status="unknown"` 属性を持つバッジを描画しなければならない（MUST）。

**MUST 項目**:
- `builder.py` の `_STATUS_LABELS` 辞書に `"unknown"` キーを追加する（MUST）。ラベル: **`"不明"`（spec 段階で確定）**
- `builder.py` の inline CSS（`_render_style()` 等）に `.badge[data-status="unknown"]` CSS ルールを追加する（MUST）
- 配色: 灰色系（Radix Colors gray-9 相当 / **`#9ca3af`**。Bootstrap secondary 系 `#6c757d` ではなく Radix Colors gray-9 相当の `#9ca3af` を採用する / BUILDING で実測後に最終確定）
- 既存 4 値（`completed` / `in-progress` / `blocked` / `not-started`）の挙動・配色は無改変（MUST）
- Lighthouse Accessibility ≥ 95 を維持する（NFR-W8-5 / 退行ゼロ）

**根拠**: `status="unknown"` バッジが CSS 未定義のままだと、V-2 Milestone カードのバッジが無スタイルで表示され
表示崩れが発生する。機能的正確性のための最小限の追加であり、意匠変更には該当しない。

---

## §4 非機能要件（NFR）

### NFR-W8-1: パフォーマンス — Merger 追加による追加コスト上限（MUST）

NFR-4（元要件 / ダッシュボード生成 30 秒以内）を維持しなければならない（MUST）。

**MUST 項目**:
- `MilestoneSourceMerger.get_milestones()` の処理時間は **1 秒以内** とする（現実的な Milestone 数: 最大 **30 件**を想定 / I-I-1 反映 v0.2.1）
- 集合演算（Python `set` / `dict`）を使用し、O(n) の実装とする（MUST）
- NFR-4（30 秒以内）に上乗せされる Merger 追加分は 1 秒以内であるため、NFR-4 への実質的影響はゼロとみなす

> **I-I-1 変更理由（v0.2.1）**: 旧「最大 100 件」は過剰余裕かつ現実に即しない計測困難な値だった。
> LAM プロジェクトの実績 Milestone 数（B-4 / B-5 等）から 30 件を現実的な上限とした。

### NFR-W8-2: 後方互換 — 既存テスト 398 件（MUST）

Wave 7 終端時点の pytest 398 PASS / 10 SKIP を、Wave 8 追加分も含めて維持しなければならない（MUST）。

**MUST 項目**:
- 既存 398 テスト（PASS）を退行させない（MUST）
- 既存 10 テスト（SKIP）の skip 理由を変更しない（MUST）
- 既存テストの緩和は L1 事前承認必須

### NFR-W8-3: Registry 昇格契約の保持（MUST / I-W-5 反映 v0.2.1）

`MilestoneProvider` Protocol を実装しなければならない（MUST）。FR-W8-5 MUST 昇格に連動。
将来の `MilestoneRegistry` 差し替えが `build_dashboard.py` 変更なしに可能であること。

### NFR-W8-4: CSS 予算維持（SHOULD）

Wave 8 実装による CSS 追加は最小限とし、16,384 bytes（NFR-W7-1 v0.2.4 改定値）以内を維持することが望ましい（SHOULD）。
Wave 7 終端実測: 10,400 bytes（残 5,984 bytes / 緑帯 < 70%）。Merger 追加は CSS に影響しないため、現状緑帯を維持できる見込み。

### NFR-W8-5: Lighthouse Accessibility 維持（MUST）

Wave 7 達成値（Accessibility 97）を Wave 8 終端で 95 以上に維持しなければならない（MUST）。

---

## §5 受け入れ条件（AC）

### AC-W8-1: MilestoneSourceMerger の統合動作（FR-W8-1 対応 / MUST）

`MilestoneSourceMerger(session_milestones=..., task_milestone_names=...).get_milestones()` のテストにおいて、
SessionState 由来の Milestone 集合と tasks.md 由来の Milestone 集合の和集合が name 昇順で返される。

**検証シナリオ**:
- Session: `["B-4", "B-5"]` / tasks: `["B-5", "B-6"]` → 結果: `["B-4", "B-5", "B-6"]`
- Session: `["B-5"]` / tasks: `[]` → 結果: `["B-5"]`（Session のみ）
- Session: `[]` / tasks: `["B-5"]` → 結果: `["B-5"]`（tasks のみ）
- Session: `[]` / tasks: `[]` → 結果: `[]`（空）

### AC-W8-2: V-2 と V-4 フィルタの Milestone 一致（FR-W8-2 / FR-W8-3 対応 / MUST）

dashboard.html を生成し、V-2 ビューに表示される Milestone 名と
V-4 フィルタ選択肢（`<select id="filter-milestone">`）の Milestone 名が完全に一致する。

**検証方法**: 統合テストで `data.milestones` が V-2 と V-4 フィルタの両方に反映されていることを確認。

### AC-W8-3: tasks.md 由来 Milestone の反映（FR-W8-1 対応 / MUST）

SESSION_STATE.md に Task ID が存在しない Milestone が tasks.md に存在する場合、
その Milestone が V-2 および V-4 フィルタ選択肢に表示される。

**検証手段（2 段階 / I-W-4 反映 v0.2.1）**:

1. **単体テスト（Merger）**:
   - フィクスチャ: `tests/dashboard/fixtures/wave8/session_minimal.txt`（B-5 のみ Task ID）
     および `tests/dashboard/fixtures/wave8/tasks_with_extra.txt`（B-5 + B-4 Task ID）
   - 期待: `MilestoneSourceMerger(...).get_milestones()` の戻り値に B-4 が含まれ、
     その `status` は `"unknown"`

2. **統合テスト（dashboard.html）**:
   - 期待: 生成 HTML 内に `<article class="milestone-card" data-milestone="B-4">` が含まれる
     かつ V-4 フィルタ `<select>` に `<option value="B-4">` が含まれる
   - grep パターン: `r'data-milestone="B-4"'` および `r'<option[^>]*value="B-4"'`
   - 追加期待（I-W-N2 / v0.2.2）: B-4 の Milestone カードに `data-status="unknown"` バッジが描画されている
     （grep: `r'data-status="unknown"'`）
   - CSS 適用確認: 生成 HTML 内の `<style>` ブロックに `.badge[data-status="unknown"]` の CSS ルールが存在する

### AC-W8-N1: "unknown" バッジ CSS と _STATUS_LABELS の追加（FR-W8-N2 対応 / MUST / v0.2.2 新規追加）

**検証手段**:

1. `builder.py` の `_STATUS_LABELS` 辞書に `"unknown"` キーが追加されている（例: `"unknown": "不明"`）
2. `builder.py` の inline CSS 生成メソッド（`_render_style()` 等）に `.badge[data-status="unknown"]` の CSS ルールが追加されている
3. 配色: 灰色系（Radix Colors gray-9 / `#9ca3af` 等。BUILDING で確定）
4. Lighthouse Accessibility: AC-W8-6 を参照（重複検証回避）

### AC-W8-4: 既存 4 パーサの無改変確認（FR-W8-4 対応 / MUST）

Wave 8 実装後に既存パーサの各テストファイルが全件 PASS を維持する。

**検証方法**:
- `test_session_state_parser.py` 全件 PASS
- `test_current_phase_parser.py` 全件 PASS
- `test_tasks_parser.py` 全件 PASS（Wave 7 追加分含む）
- `test_git_history_parser.py` 全件 PASS

### AC-W8-5: pytest 全件 PASS（NFR-W8-2 対応 / MUST）

Wave 8 終端で pytest 全件 PASS（既存 398 件 + Wave 8 追加分）。

### AC-W8-6: Lighthouse Accessibility ≥ 95（NFR-W8-5 対応 / MUST）

Stage 末で Lighthouse 計測し、Accessibility スコアが 95 以上である。

### AC-W8-7: エラー耐障害性 — 片方パーサ欠如時（FR-W8-6 対応 / MUST）

SessionStateParser または TasksParser のどちらかが `ok=False` を返した場合でも、
ダッシュボード生成が正常完了し（returncode 0 or 1）、残方のデータで V-2 が表示される。

**I-W-6 明確化（v0.2.1）**: `ok=False` 時は `build_dashboard.py` が `session_milestones=[]`（空リスト）を
Merger に渡す責務を持つ。Merger は `None` を受け取らない。
空リスト渡しにより Merger は tasks.md 由来のみで Milestone リストを構築して継続する。

---

## §6 Non-Goals 詳細（Wave 8 スコープ外の明示）

### FC-7: Step 別管理との関係

FC-7（複数 Milestone 同時進行時の Step 別管理）は引き続き将来候補。
Wave 8 の Merger は Milestone 名の集合演算のみを担い、`MilestoneInfo.current_step` は
従来通り `CurrentPhaseParser` の単一値（全 Milestone 共通）を使用する。
FC-7 と Registry 昇格（UQ-9）を合わせて将来実施可能性を検討する。

### MilestoneRegistry 本格化との関係

`MilestoneSourceMerger`（Wave 8）は将来の `MilestoneRegistry` への踏み石だが、
Registry 自体は Wave 8 のスコープ外。波及: `MilestoneProvider` Protocol を定義することで、
`build_dashboard.py` の変更なしに将来 Registry への差し替えを可能にする（FR-W8-5 MUST / I-W-N1 反映 v0.2.2）。

### Merger と Tasks/SessionState の双方向同期

Merger は read-only 集約専用（MUST NOT 双方向同期）。設計上の根拠: 単方向のデータフロー
（ファイル → パーサ → Merger → Builder）を維持することで、予期しない副作用（ファイル書き換え等）を防ぐ。

### 全 tasks.md の新規格統一

Wave 7 でパイロット運用を開始した tasks.md の新規格 Task ID 形式（`W{n}-B{n}-T{n}`）への
全ファイル統一は Wave 8 のスコープ外。Wave 7 retro の継続未消化事項として引き続き Wave 8+ で検討。

---

## §7 解決済み質問（MAGI 合議 / 2026-06-28）

以下は Wave 8 PLANNING 時の MAGI 合議（2026-06-28）で確定した 7 項目。

> **I-I-4 注（v0.2.1）**: 下表の「D = Wave 8」は本 Wave 8 設計書全体のスコープ識別子として使用している。
> 「D」は chip `task_68008f88` 対応の Wave 番号（Wave 8）を指す。

| # | 質問 | 回答 |
|:--|:----|:----|
| 1 | Merger の実体は何か | b4-dashboard 内に `MilestoneSourceMerger` を新設する（SessionState + tasks.md の Milestone 集合を merge して SSOT を提供） |
| 2 | Registry 化するか | Wave 8 段階ではしない。ただし将来 ⑥ A 設計で `MilestoneRegistry` に昇格できる Protocol 契約を切る |
| 3 | 元 design.md を改修するか | はい。§3 アーキ図・§5 Merger 仕様・§4 V-2/V-4 データソース記述を整合化済み |
| 4 | Wave 番号 | D = Wave 8（確定）※ D は chip task_68008f88 対応 Wave 8 のスコープ識別子 |
| 5 | 既存パーサを改修するか | しない（4 パーサ無改変 / FR-W8-4） |
| 6 | テスト方針 | 新規（merger 単体 + integration）。既存 398 テストは改変なし or 最小 |
| 7 | パーサ独立性原則との整合 | Merger は「上位集約レイヤ」として位置付け、原則違反しない（build_dashboard.py がパーサ結果を Merger に渡す設計） |

---

## §8 将来候補（FC 番号は future-candidates.md に揃える）

本スコープから除外し、将来の Wave で検討する事項:

| FC | 内容 | 採用トリガ |
|:---|:----|:---------|
| FC-7 | 複数 Milestone 同時進行時の Step 別管理 | 2 Milestone 以上が異なる Step で並列進行が常態化した時点 |
| FC-10 | /project-vision スキル連携（⑥ A MilestoneRegistry） | 骨子 ⑥ 設計確定後 |
| — | 全 tasks.md の新規格 Task ID 統一 | Wave 8+ で Milestone 重要度評価後 |
| — | Merger から MilestoneRegistry への昇格 | FC-10 採用時（UQ-9 解決時）|

---

## §9 Example Mapping（主要 FR に対する具体例）

### FR-W8-1: MilestoneSourceMerger の統合

**ルール**: SessionState と tasks.md の和集合を取り、重複排除・昇順ソートする。

| 具体例 | 入力（session / tasks） | 期待出力 |
|:------|:--------------------|:--------|
| 両方にエントリあり、重複あり | session=`[B-4, B-5]`, tasks=`[B-5, B-6]` | `[B-4, B-5, B-6]` |
| session のみ | session=`[B-5]`, tasks=`[]` | `[B-5]` |
| tasks のみ | session=`[]`, tasks=`[B-5]` | `[MilestoneInfo(name="B-5", status="unknown")]` |
| 両方空 | session=`[]`, tasks=`[]` | `[]` |
| session 取得失敗 | `session_milestones=[]`（build_dashboard.py が ok=False 時に空リストに正規化）, tasks=`[B-5]` | `[B-5]`（tasks のみで継続）|

**ルール**: session 由来エントリの status を保持する。

| 具体例 | SessionState のエントリ | 期待出力 |
|:------|:--------------------|:--------|
| session に status あり | `MilestoneInfo(name="B-5", status="in-progress")` が session に存在 | 出力も `status="in-progress"` を保持 |
| tasks 由来のみ | tasks に `"B-6"` のみ存在 | `MilestoneInfo(name="B-6", status="unknown")` で補完（SESSION_STATE.md 揮発性のため中立値 / I-W-2）|

### FR-W8-2: V-2 ビューの SSOT 整合

**ルール**: `DashboardData.milestones` が Merger 結果なら、V-2 は必ず Merger 結果を表示する。

| 具体例 | `data.milestones` | V-2 表示 |
|:------|:-----------------|:--------|
| Merger が B-4/B-5/B-6 を返す | `[B-4, B-5, B-6]` | 3 枚のカードが昇順で表示 |
| Merger が空リストを返す | `[]` | 「Milestone 情報なし」empty state |

### FR-W8-3: V-4 フィルタ選択肢の SSOT 整合

**ルール**: V-4 の `<select id="filter-milestone">` 選択肢が `data.milestones` と一致する。

| 具体例 | `data.milestones` | フィルタ選択肢 |
|:------|:-----------------|:------------|
| `[B-4, B-5]` | — | `すべて / B-4 / B-5` |
| `[]` | — | `すべて`（のみ） |

**未解決質問（Red）**: なし（MAGI 合議 7 項目ですべて確定済み）

---

## §10 改訂履歴

| バージョン | 日付 | 変更内容 |
|:----------|:-----|:--------|
| 0.2.0 | 2026-06-28 | 初版起稿 — MAGI 合議（2026-06-28 / 案 5 採用）に基づく FR/NFR/AC 定義。chip task_68008f88 対応。FR-W8-1〜6 / NFR-W8-1〜5 / AC-W8-1〜7 / Example Mapping §9 |
| 0.2.1 | 2026-06-28 | spec-critic レビュー反映（Critical 3 / Warning 6 / Info 4 / L1 追加 1）— FR-W8-1 補完 status "not-started" → "unknown"（I-W-2）/ FR-W8-5 SHOULD → MUST 昇格（I-W-5）/ NFR-W8-1 最大 100 件 → 30 件（I-I-1）/ NFR-W8-3 SHOULD → MUST（I-W-5 連動）/ AC-W8-1 API 名を constructor 注入版に更新（I-C-3）/ AC-W8-3 検証手段を 2 段階（単体 + 統合）に具体化（I-W-4）/ AC-W8-7 ok=False 時の空リスト正規化を明示（I-W-6）/ §2 G4 達成条件を 3 点で明示（I-W-5）/ §7 「D」脚注追加（I-I-4）/ §9 Example Mapping の session=None 表記を session_milestones=[] に統一・tasks 由来 status "not-started" → "unknown"（I-W-2 / I-W-6）|
| 0.2.2 | 2026-06-28 | spec-critic ラウンド 2 反映（Warning 2 / Info 4 / "unknown" バッジ Wave 8 スコープ化）— §2 Non-Goals に "unknown" バッジ例外条項追加（I-W-N2）/ §3 FR-W8-N2 新規追加（"unknown" バッジ MUST / I-W-N2）/ §5 AC-W8-3 統合テストに "unknown" バッジ確認追加（I-W-N2）/ §5 AC-W8-N1 新規追加（FR-W8-N2 受入条件 / I-W-N2）/ §6 L258 FR-W8-5 SHOULD → MUST に修正（I-W-N1）|
| 0.2.3 | 2026-06-28 | spec-critic ラウンド 3 反映 / 最終クリーニング（Warning 2 + Info 3）— §3 冒頭に FR-W8-N*/AC-W8-N* 命名根拠注記追加（I-I-N5）/ §3 FR-W8-N2 ラベル "不明" を spec 確定値に変更・配色を `#9ca3af` に統一（I-I-N7 / I-W-N4）/ §5 AC-W8-N1 検証手段 4 を AC-W8-6 参照に置換（I-I-N6）|

---

## §11 権限等級

- 本要件書の変更: **PM 級**（仕様変更）
- AC 追加・修正: **PM 級**
- 表記の微調整・typo 修正: **PG 級**

---

## §12 upstream-first 裏取りステータス

| 対象 | 実在性確認 | LAM 適合性 | 備考 |
|:-----|:----------|:----------|:----|
| Python `set` 集合演算（和集合）| ✅（Python 標準）| ✅ | 既存実装で同種演算を使用中 |
| `typing.Protocol`（Python 3.8+）| ✅（Python 標準）| ✅ | 標準ライブラリ / 外部依存なし |
| `@dataclass`（Python 3.7+）| ✅（Python 標準）| ✅ | 既存 models.py で使用中 |
| 新規 API キー名・プラットフォーム機能 | N/A | N/A | 本 Wave は Python 標準ライブラリのみ / upstream-first 該当箇所なし |

---

## §13 参照

- [元 requirements.md v0.2.0](../requirements.md)
- [元 design.md v0.2.0](../design.md)
- [wave8/design.md](./design.md)
- [future-candidates.md FC-7 / FC-10](../future-candidates.md)
- [retro Wave 7](../../../artifacts/retro-W7-B5-2026-06-28.md)
- [retro Wave 6](../../../artifacts/retro-W6-B5-2026-06-27.md)
- [planning-quality-guideline](../../../../.claude/rules/planning-quality-guideline.md)
- [terminology](../../../../.claude/rules/terminology.md)
- [L2 委譲ガードレール](../../../artifacts/knowledge/l2-delegation-guardrails.md)
