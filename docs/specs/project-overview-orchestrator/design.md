# 設計書: Project Overview Orchestrator（POO）

- バージョン: 0.3.0
- 作成日: 2026-06-29
- ステータス: Draft（R3 修正済み / PM 承認待ち）
- 根拠文書: `docs/specs/project-overview-orchestrator/requirements.md` v0.5.0
- 参照文書:
  - `docs/specs/project-overview-orchestrator/spike/README.md` v0.4.0（Spike V-1〜3 / Wave 11 引き渡し情報）
  - `docs/adr/0006-loop-engineering-vocabulary-and-lam-alignment.md`（Stage 3 位置付け / Glossary）
  - `docs/specs/b4-dashboard/wave8/design.md` v0.2.3（MilestoneSourceMerger / Protocol 昇格契約 §10）
  - `docs/specs/b4-dashboard/design.md`（パーサ層 / 集約レイヤ全体設計）
  - `docs/specs/autonomous-mode/design.md`（層別エージェント設計の手本）
  - `docs/specs/goal-driven-orchestration/design.md`（rubric ファースト + 独立 grader 設計の手本）
- 起草者: a-design-d1（design-architect）

> 本書は「どう実現するか（How）」を定義する。「何を（What）」は requirements.md v0.5.0、
> 採用決定の根拠は ADR-0006 を参照（重複させない）。

---

## §1 Problem Statement

requirements.md §1 を継承する。ここでは設計が解くべき課題を述べる。

LAM プロジェクトは 4 階層（Milestone / Step / Wave / Task）で作業を管理し、
`/autonomous`・`/goal-driven`・`/lam-orchestrate`・`/full-review` の 4 スキルを保有する。
これらは Wave 単位の実装ループ（Loop Engineering Stage 2 Loop）として機能するが、
**Milestone をまたぐ俯瞰・現在地特定・次着手推奨** を担う coordinator 層が存在しない。

ADR-0006 は ⑥（骨子 プロジェクト俯瞰オーケストレータ）を **Loop Engineering Stage 3 Orchestrated Teams の典型設計**として位置付け、coordinator 層の常駐化を推奨改善方針に挙げた。

### 設計課題

| 課題 | 設計アプローチ |
|:-----|:------------|
| Milestone 現在地が揮発的ファイルに分散している | `MilestoneRegistry` を SSOT として確立し、POO が read-only API で参照する |
| 次着手推奨の判断基準が人間の経験則に依存する | Phase フィルタ表 + Hick's Law 上限 3 件で構造化推奨を生成する |
| 既存スキルへの呼び出し契約が未定義 | FR-W10-3 起動 API 契約を薄い仕様として定義（スキル側の内部不改修）|
| Milestone SSOT が未整備で b4-dashboard と POO が二重管理になるリスクがある | Wave 8 の `MilestoneProvider` Protocol を共通基盤として POO と dashboard が同一 Registry を参照する |

---

## §2 Non-Goals（設計上）

requirements.md §2 に加えて、設計レベルで扱わない領域を明示する。

- **gabriel 統合 / MAGI v2 設計**: v2 以降の別 ADR で扱う。本 design では POO の単独動作のみを設計する
- **MilestoneRegistry 実装詳細（昇格 vs 差し替え）**: OQ-1 に従い Wave 11 design.md で確定する。本書では Protocol 契約のみ確定する
- **SESSION_STATE.md パーサ実装**: フォーマット仕様の実機合わせは Wave 11 BUILDING で行う
- **tasks.md 起票**: Wave 11 PLANNING で起草する（本 Wave のスコープ外）
- **POO 自体の SKILL.md 起草**: Wave 11 PLANNING で確定する
- **DQ-W10-1 以降の設計 OQ の実装確定**: 各 OQ は Wave 11 PLANNING および BUILDING で解消する
- **Git 履歴ベースの状態推定**: Wave 11 BUILDING で MilestoneRegistry が確定するまで、`git log` を介した状態推定は Wave 10 設計のスコープ外とする。POO は SESSION_STATE.md / tasks.md / current-phase.md の 3 ソースのみを参照する（W-3 対応）

---

## §3 アーキテクチャ概観

### 層別構成

```
[ユーザー / L1 統括]
        |
        | /poo 起動（判断補助要求）
        v
[POO Orchestrator]  ────────────────────────────────→  [推奨提示（4 次元 + 注記）]
        |                                               現在地: Milestone=X / Step=X /
        | read-only API のみ                             Wave=X / Task=X
        v                                               [注記] Phase=unknown（条件付き）
[MilestoneRegistry]  ←───── [b4-dashboard も同一 Registry を参照]
        |
        | MilestoneProvider Protocol 経由
        v
[パーサ層（既存 / 無改変）]
  ├── SessionStateParser  → SESSION_STATE.md
  ├── TasksParser         → docs/specs/<milestone>/tasks.md
  └── CurrentPhaseParser  → .claude/current-phase.md
```

### データフロー（POO 実行時）

```
1. POO 起動
2. MilestoneRegistry.get_milestones() → list[MilestoneInfo]
3. SESSION_STATE.md 読み取り → Step / Wave 特定
4. docs/specs/<milestone>/tasks.md 読み取り → 未完了 Task 特定
5. .claude/current-phase.md 読み取り → Phase 特定（内部処理用）
6. 4 次元現在地を組み立てる（欠損次元は unknown）
7. Phase に基づく推奨スキルフィルタリング（FR-W10-5 Phase フィルタ表）
8. priority 順に最大 3 件の推奨候補を生成（FR-W10-2 / NFR-W10-6）
9. 出力:
   - 4 次元現在地（MUST）
   - [注記] Phase=unknown（current-phase.md 不在時 MUST）
   - 推奨候補 最大 3 件 + 各推奨の根拠参照
10. POO 正常終了
```

### アーキテクチャ上の制約（read-only 保証）

POO は全ファイルを読み取り専用で扱う（NFR-W10-5）。
ファイルへの書き込みを実行してはならない（MUST NOT）。
これにより、POO は冪等であり、実行による副作用が発生しない。

---

## §4 設計詳細

### D-1: MilestoneRegistry（read-only API 契約）

#### 目的

Wave 8 で定義した `MilestoneProvider` Protocol を POO と b4-dashboard の共通 SSOT として確立する。
本節では Protocol 契約を確定する。「昇格（extend）」か「差し替え（replace）」かの実装選択は Wave 11 設計書で確定する（OQ-1）。

#### MilestoneProvider Protocol（Wave 8 定義の継承）

Wave 8 design.md §10 で定義された `MilestoneProvider` Protocol をそのまま継承する。
本 design での追加変更はない。

```python
# Wave 8 merger.py 定義（継承・再掲）
from typing import Protocol, runtime_checkable
from dashboard.models import MilestoneInfo

@runtime_checkable
class MilestoneProvider(Protocol):
    """Milestone 一覧を提供するコンポーネントの契約。

    MilestoneSourceMerger（Wave 8）も MilestoneRegistry（POO / Wave 11）も
    このプロトコルを実装することで、参照側の変更なしに差し替え可能にする。
    """

    def get_milestones(self) -> list[MilestoneInfo]:
        """統合済みの Milestone リストを返す。"""
        ...
```

#### MilestoneRegistry の最小 API シグネチャ案（Spike V-1 を確定候補に格上げ）

以下は Wave 11 設計書でレビューを経て確定するシグネチャ案である。
本 Wave 10 では Spike V-1 で MUST 確定済みの `get_milestones()` のみを最小確定 API とする（C-2 対応）。

```python
# registry.py（配置先は Wave 11 設計書で確定 / OQ-1 参照）
class MilestoneRegistry:
    """MilestoneProvider Protocol を実装する共通基盤 SSOT。

    read-only のみ実装する（MUST NOT write）。
    """

    def __init__(self, project_root: Path) -> None:
        """データソースパスを受け取り初期化する。"""
        ...

    def get_milestones(self) -> list[MilestoneInfo]:
        """MilestoneProvider 実装。統合済み Milestone リストを返す（MUST）。"""
        ...
```

> **注記**: `get_milestones()` のみが Wave 10 で確定する最小 API シグネチャである。
> `get_current()` / `list_waves()` 等の追加 API については DQ-W10-4 を参照。

#### エラー耐障害性 API 契約

| ケース | 挙動 |
|:------|:----|
| データソースの一部が欠如している | 取得できた Milestone を返し継続する（MUST）|
| 全データソースが欠如している | 空リスト `[]` を返す（MUST）|
| Registry が利用不可（Wave 11 実装前） | 当該次元を `unknown` として出力継続（NFR-W10-4 / MUST）（詳細は D-6 graceful degradation 仕様を参照）|

#### b4-dashboard との SSOT 共有方針（FR-W10-6）

- `MilestoneRegistry` 導入後、`build_dashboard.py` が `MilestoneSourceMerger` を参照している箇所を `MilestoneProvider` 型変数への差し替えのみで切り替えられる設計を維持する（MUST）
- b4-dashboard の `builder.py` / `build_dashboard.py` 等の **内部ロジック実装**は変更してはならない（MUST NOT）。ただし `MilestoneSourceMerger` から `MilestoneRegistry` への参照経路切替に伴う**型変数の差し替え（例: `MilestoneSourceMerger` から `MilestoneProvider` 型変数への変更）** は許可される（MAY）。requirements.md §5 前提 1 の「差し替えのみで実現」MUST との整合（W-4 対応）
- 本 design では差し替え経路の接続仕様を定義する。変更量の確認は Wave 11 PLANNING で Grep により実測する

---

### D-2: 現在地特定ロジック（FR-W10-1 実装方針）

#### データソース優先順位

| 次元 | プライマリソース | フォールバック | unknown 条件 |
|:-----|:-------------|:-------------|:-----------|
| Milestone | `MilestoneRegistry.get_milestones()` | なし | Registry が空リストを返す |
| Step | `SESSION_STATE.md` の「現在の Step」フィールド | なし | フィールド不在 / パースエラー |
| Wave | `SESSION_STATE.md` の「現在の Wave」フィールド | `tasks.md` の進行中 Wave | 両方不在 |
| Task | `docs/specs/<milestone>/tasks.md` の未完了 Task | なし | ファイル不在 / 未完了 Task なし |

> **注記（前提 3 対応）**: SESSION_STATE.md の具体的なフィールド名・正規表現・パース方法は
> Wave 11 BUILDING で実機合わせして確定する（OQ-4 の実装レベル詳細）。
> 本 design では「SESSION_STATE.md から Step / Wave を読み取る」という方針のみを確定する。

#### 4 次元出力フォーマット（AC-W10-1）

```
現在地: Milestone=<名前> / Step=<PLANNING|BUILDING|AUDITING> / Wave=<番号> / Task=<ID>
```

各次元の具体例:

```
現在地: Milestone=B-5 / Step=BUILDING / Wave=10 / Task=T-W10-1
現在地: Milestone=B-5 / Step=unknown / Wave=unknown / Task=unknown   ← SESSION_STATE.md 不在時
現在地: Milestone=B-5 / Step=BUILDING / Wave=10 / Task=unknown       ← tasks.md 不在時
```

#### Phase=unknown 別行注記（FR-W10-5 (c)）

`current-phase.md` が存在しない場合、4 次元出力の直後に以下の別行注記を出力しなければならない（MUST）:

```
[注記] Phase=unknown (current-phase.md 不在)
```

この注記は 4 次元フォーマットに追加する形式であり、4 次元出力自体は変更しない（MUST）。
Step 次元は SESSION_STATE.md 由来の値を継続使用する。

#### graceful degradation（NFR-W10-4）

各次元が単独で欠損した場合の挙動:

| 欠損ケース | POO の挙動 |
|:---------|:---------|
| Milestone 次元のみ unknown | Step / Wave / Task の表示を継続。Milestone=unknown で出力 |
| Step 次元のみ unknown | Milestone / Wave / Task の表示を継続。Step=unknown で出力 |
| Wave 次元のみ unknown | Milestone / Step / Task の表示を継続。Wave=unknown で出力 |
| Task 次元のみ unknown | Milestone / Step / Wave の表示を継続。Task=unknown で出力 |
| tasks.md が存在しない Milestone | Wave=unknown / Task=unknown で出力継続（AC-W10-2）|
| 全次元 unknown | `現在地: Milestone=unknown / Step=unknown / Wave=unknown / Task=unknown` を出力 |

いずれの欠損ケースでも **POO は正常終了する（MUST）**。

---

### D-3: 推奨ロジック（FR-W10-2 + FR-W10-5）

#### Phase フィルタ表

| 現在の Phase | 推奨対象スキル | 非推奨（SHOULD NOT）|
|:-----------|:------------|:----------------|
| PLANNING | `/lam-orchestrate` | `/autonomous` / `/goal-driven` / `/full-review` |
| BUILDING | `/autonomous` / `/goal-driven` | `/lam-orchestrate` / `/full-review` |
| AUDITING | `/full-review` | `/autonomous` / `/goal-driven` / `/lam-orchestrate` |
| unknown | （全スキルを推奨候補とし、Phase=unknown 注記を付与）| なし |

> **Phase=unknown 時の扱い**: `current-phase.md` が存在しない場合、Phase によるフィルタを適用せず
> 全 4 スキルを推奨候補に含める。出力には D-2 の別行注記（`[注記] Phase=unknown`）を付与する。

#### SHOULD NOT 逸脱判定（FR-W10-5 (a)）

- SHOULD NOT 対象スキルの推奨候補追加は、**ユーザーが明示的に当該スキルを指定した場合のみ** 認める
- POO は当該スキルを推奨に含める際に「Phase 規律外の推奨（ユーザー明示指定による）」を出力に明示する（SE 級相当）
- Phase 規律の上書き判断はユーザーが `.claude/rules/phase-rules.md` に従い別途行う（POO の責務外）

#### 推奨選定の優先順位基準

推奨候補の priority 順（1: 最優先）を決定するロジック:

1. Phase フィルタを通過したスキルを推奨候補とする
2. **現在地の各次元（Step / Wave / Task）が `unknown` ではないスキルを優先する**。次元の値が `unknown` であるほど priority を下げる（例: Step != unknown かつ Wave != unknown は最高 priority / Step != unknown かつ Wave = unknown は中 priority / 全て unknown は最低 priority）。**注記: 本例示は Step / Wave の 2 次元による優先順位を示す。Task 次元はタイブレーク対象として DQ-W10-3 に委ねる（Wave 11 BUILDING TDD Red で確定）**（W-2 対応）
3. 推奨根拠（FR / AC / retro アクション等）が存在するスキルを優先する
4. 推奨件数が Hick's Law 上限（3 件）を超える場合は priority の高い 3 件のみ出力する（NFR-W10-6）

#### 第 5 スキル（既知 4 スキル外）の扱い

既知 4 スキル（`/autonomous` / `/goal-driven` / `/lam-orchestrate` / `/full-review`）以外のスキルが
推奨候補として現れた場合は「未分類」として提示し、推奨対象外とする（MUST）。

#### 推奨 0 件時の出力（FR-W10-2 MUST 5/6）

Phase フィルタ後の推奨候補が 0 件になった場合:

```
推奨なし: 現在の Phase=<Phase> では推奨スキルが存在しません。
状況説明: <欠如している前提条件の説明>
```

MUST 5（全タスク完了等）と MUST 6（Phase フィルタ後 0 件）が同時発生した場合は、
両方の状況説明を統合した単一の「推奨なし」出力を返す（FR-W10-2 末尾規定）。

#### 推奨出力フォーマット例

```
推奨（priority 順）:
1. /autonomous — 対象 spec が確定しており BUILDING Phase にあるため（根拠: FR-W10-3 / AC-W10-3）
2. /goal-driven — rubric.md が存在しており BUILDING Phase にあるため（根拠: FR-W10-3 / AC-W10-3）
```

推奨理由の説明は SHOULD（推奨する）。説明が存在しない場合でも推奨自体は出力できる。

---

### D-4: 起動 API 契約（FR-W10-3）

既存 4 スキルへの呼び出し契約を定義する。既存スキルの内部実装は変更しない（MUST NOT）。

#### 起動 API 契約表

| スキル | 呼び出し前提条件（POO 推奨フィルタとしての論理的条件）| 期待出力 | 失敗判定 |
|:------|:-------------------------------------------|:--------|:--------|
| `/autonomous` | 対象 spec が確定しており BUILDING Phase にある | Green State 達成または PM ハードストップ報告 | Green State 未達かつループ終了 |
| `/goal-driven` | rubric.md が存在しており BUILDING Phase にある | Green State または grader 判定報告（overall: pass/fail）| grader 繰り返し不合格 / bound 超過 |
| `/lam-orchestrate` | PLANNING Step にある（設計・タスク成果物の生成が必要）| design / tasks 成果物の生成 | FATAL エラー / 成果物未生成 |
| `/full-review` | AUDITING Phase にある | 監査レポート（Critical / Warning / Info 件数）| max_iterations 到達かつ Critical 残存 |

> **注記（C-1 対応）**: 本表の「失敗判定」列は **POO の参照情報であり、推奨ロジック（D-3）の入力としては使用しない**。
> 実装者は失敗判定値を D-3 の priority 計算に組み込んではならない（MUST NOT）。
> 失敗判定の活用は Wave 11+ の拡張機能として将来検討する（本 Wave のスコープ外）。

> **注記（FR-W10-3 / OQ-4）**: 本表の「呼び出し前提条件」は POO の推奨フィルタリングとして確認する
> **論理的条件**であり、スキル側の起動ガードではない。スキル側の起動時前提検証は各 SKILL.md の
> 責務として独立する。本表の実装レベルの詳細（Step 判定の参照ファイル経路 / unknown 条件の閾値）は
> Wave 11 PLANNING で確定する（OQ-4）。

#### Cross-spec 整合確認（requirements.md §11 記録を継承）

requirements.md §11 の a-design3 R3 による cross-spec 整合確認（2026-06-29）の結果を継承する:

- `/autonomous`: SKILL.md → 「対象 spec が確定しており BUILDING Phase にある」前提 → `lam-stop-hook.py` の G1 checker exit 0 で Green State 達成 → 整合
- `/goal-driven`: SKILL.md → 「rubric.md が存在しており BUILDING Phase にある」前提 → grader `overall: pass` で Green State → 整合
- `/lam-orchestrate`: SKILL.md → 「PLANNING Step にある」前提 → Phase 1-4 設計成果物生成フロー → 整合
- `/full-review`: SKILL.md → 「AUDITING Phase にある」前提 → 監査レポート Critical / Warning / Info 件数出力 → 整合

> **注記**: 本セクションは整合確認結果の継承宣言であり、整合の詳細根拠は requirements.md §11 トレーサビリティを参照すること。design.md 単独では cross-spec 整合の詳細にアクセスできないため、本 design 読解時は requirements.md §11 を併せて参照する必要がある（§参照節にも記載済）。

---

### D-5: Phase=unknown 別行注記の出力仕様（FR-W10-5 (c) + AC-W10-1）

#### 出力規則（MUST）

- `current-phase.md` が存在しない場合、POO は Phase 次元を `unknown` として扱う
- AC-W10-1 の 4 次元出力フォーマット（Milestone / Step / Wave / Task）は変更しない（MUST）
- 4 次元出力の直後の別行に以下を出力しなければならない（MUST）:

```
[注記] Phase=unknown (current-phase.md 不在)
```

- Step 次元は `current-phase.md` とは独立して SESSION_STATE.md 由来の値を継続使用する

#### 出力位置の具体例

```
現在地: Milestone=B-5 / Step=BUILDING / Wave=10 / Task=T-W10-1
[注記] Phase=unknown (current-phase.md 不在)

推奨（Phase=unknown のため全スキルを候補とします）:
1. /lam-orchestrate — Step=PLANNING のため（根拠: FR-W10-5）
2. /autonomous — ...
3. /goal-driven — ...
```

> **注記（Info-3 対応）**: 上記の例で 3 件のみ示されているのは Hick's Law 上限 3 件（NFR-W10-6）によるカットの結果である。
> `/full-review` は AUDITING Phase 向けスキルであり、本例（Phase=unknown）では priority が 3 位以下に下がりカットされた
> （具体的 priority 決定基準は DQ-W10-3 / Wave 11 BUILDING で確定）。

---

### D-6: graceful degradation の詳細仕様（NFR-W10-4）

#### POO 正常終了の保証

依存資産（`MilestoneRegistry` を含む任意のデータソース）が利用不可の場合でも:

- 当該次元を `unknown` として出力を継続する（MUST）
- AC-W10-1 形式の 4 次元出力を返す（MUST）
- POO 自体は起動完了し、正常終了する（MUST）

#### 依存資産別の degradation 挙動

| 依存資産 | 不可時の挙動 |
|:---------|:---------|
| `MilestoneRegistry`（Wave 11 実装前を含む）| **Milestone=unknown のみ**で出力継続（Wave / Task 次元は SESSION_STATE.md / tasks.md から取得継続）|
| `SESSION_STATE.md` | Step=unknown / Wave=unknown（Session 由来）で出力継続 |
| `tasks.md`（対象 Milestone）| Wave=unknown / Task=unknown で出力継続（AC-W10-2）|
| `.claude/current-phase.md` | Phase=unknown 注記を出力して推奨ロジックは全スキル対象で継続 |

#### read-only 保証（NFR-W10-5）

POO は SESSION_STATE.md / tasks.md / `.claude/current-phase.md` をはじめとする全ファイルを
読み取り専用で扱わなければならない（MUST）。ファイルへの書き込みを実行してはならない（MUST NOT）。

---

## §5 Alternatives Considered

Design Doc チェックリスト準拠（planning-quality-guideline.md §3）として必須セクション。

### 案 α（却下）: b4-dashboard 拡張（UI 上に俯瞰機構を統合）

**概要**: b4-dashboard の HTML / JavaScript / Python に POO 相当の機能を追加する。
Milestone 現在地と推奨を dashboard のビュー V-5 として実装する。

**Pros**:
- 既存 UI との統合により UX が一貫する
- 新規スキルファイルが不要

**Cons**:
- b4-dashboard の責務が「表示」から「推奨エンジン」まで肥大化する（SRP 違反）
- JavaScript / Python の両方に推奨ロジックを実装しなければならず、SSOT が分断される
- b4-dashboard の変更が POO 仕様の変更と連動し、両方の CI 影響範囲が拡大する
- requirements.md Non-Goals「dashboard UI 変更は対象外」に抵触する

**却下理由**: 責務肥大 + SRP 違反 + b4-dashboard Non-Goals 違反。

---

### 案 β（却下）: 独立スキル（MilestoneRegistry 共通基盤なし）

**概要**: POO を完全独立の新スキルとして実装し、SESSION_STATE.md / tasks.md を
POO 独自のパーサで直接読み取る。b4-dashboard との SSOT 共有はしない。

**Pros**:
- b4-dashboard への影響ゼロ
- 実装が最もシンプル（Registry 不要）

**Cons**:
- SESSION_STATE.md / tasks.md から Milestone 情報を取得するパーサが POO と b4-dashboard で二重実装される
- Wave 8 で整備した `MilestoneSourceMerger` の知見が活かされない
- b4-dashboard の表示と POO の推奨が異なる Milestone 情報を参照するリスクがある（SSOT 二重化リスク）

**却下理由**: SSOT 二重化リスク + Wave 8 共通基盤の再利用機会の損失。

---

### 案 γ（採用）: 共通基盤化（MilestoneRegistry SSOT + POO と b4-dashboard が同一 Registry を参照）

**概要**: Wave 8 の `MilestoneSourceMerger` を昇格（extend）または差し替え（replace）して
`MilestoneRegistry` を確立する。POO と b4-dashboard が同一 `MilestoneProvider` Protocol を介して
同一 SSOT を参照する。

**Pros**:
- Milestone SSOT が一元化される（b4-dashboard と POO で乖離が発生しない）
- Wave 8 の `MilestoneProvider` Protocol 設計への投資が活かされる（Spike V-1 検証済み）
- b4-dashboard 側は `MilestoneProvider` 型変数への差し替えのみで対応可能（既存コードへの影響最小）
- パーサ層（SessionStateParser / TasksParser 等）は無改変を維持できる

**Cons**:
- `MilestoneRegistry` の実装（Wave 11 BUILDING）が前提条件になる
- Wave 8 の G4 達成条件 3 が満たされていることへの依存がある（**requirements.md §5 前提 1 参照**）

**採用理由**: SSOT 一元化 + Wave 8 共通基盤の継承 + 最小影響で b4-dashboard との連携が実現できる。
MAGI 合議（requirements.md §9 A3 / Spike V-1 検証）で確定。

---

### その他の却下案

| 案 | 概要 | 却下理由 |
|:---|:-----|:---------|
| gabriel 先行統合（v1 で MAGI 連携） | POO v1 で gabriel（骨子 ②）との統合を実施する | 別 ADR 未策定 / gabriel 設計が未確定 / Wave 10 スコープ超過 |
| 自動起動権限を v1 で付与 | POO が推奨スキルを自動起動する権限を Wave 10 で実装する | 承認ゲート後退・自律化の段階を飛ばすことへのリスク / requirements.md Non-Goals 違反 |
| tasks.md を Wave 10 で起票 | design.md と同一 Wave で tasks.md も起草する | Wave 11 PLANNING で design を踏まえた tasks を起草するのが正規フロー |
| Phase=unknown を 5 次元目として出力 | 4 次元出力に Phase 列を追加する | requirements.md §9 P3・R5-W1 で「4 次元フォーマット固定 / Phase は別行注記」に確定済み |

---

## §6 Success Criteria

requirements.md §7 AC-W10-1〜9 への設計対応マトリクス（WBS 100% Rule）。

| AC | 条件（要約）| 対応する設計節 |
|:---|:----------|:------------|
| AC-W10-1 | 4 次元形式（Milestone/Step/Wave/Task）で現在地が出力される。current-phase.md 不在時は別行注記 | D-2（4 次元出力フォーマット） / D-5（Phase=unknown 別行注記）|
| AC-W10-2 | データソース欠如でも出力継続し、欠如次元を unknown 表示。tasks.md 不在 Milestone は Wave/Task=unknown | D-2（graceful degradation 表） / D-6（degradation 詳細）|
| AC-W10-3 | 推奨が最大 3 件、priority 順で含まれ、各推奨に根拠参照が明示される | D-3（推奨選定の優先順位基準 / 推奨出力フォーマット例）|
| AC-W10-4 | Phase=BUILDING 時に /autonomous または /goal-driven が推奨に含まれ、/lam-orchestrate は含まれない | D-3（Phase フィルタ表）|
| AC-W10-5 | MilestoneRegistry.get_milestones() が MilestoneProvider に従い list[MilestoneInfo] を返す。Wave 10 内では spec 記述が受入条件 | D-1（MilestoneProvider Protocol / API シグネチャ案）|
| AC-W10-6 | MilestoneRegistry にファイル書き込みメソッドが存在しない（read-only 保証）| D-1（API シグネチャ案）/ D-6（read-only 保証）|
| AC-W10-7 | b4-dashboard を MilestoneSourceMerger から MilestoneRegistry に切り替えた場合に既存 pytest が全件 PASS。Wave 10 内では spec 記述が受入条件 | D-1（b4-dashboard との SSOT 共有方針）|
| AC-W10-8 | POO 実行から現在地特定 + 推奨出力完了まで 30 秒以内 | §4 全体（ファイル I/O を逐次 / 外部ネットワーク接続なし設計）/ **§8 実装制約（標準ライブラリ制約 / NFR-W10-3 連携）** / Spike V-3（パフォーマンス想定）|
| AC-W10-9 | FR-W10-3 の 4 スキル起動 API 契約が spec に記述されている | D-4（起動 API 契約表）|

### NFR 対応マトリクス補足（W-1 対応）

| NFR | 条件（要約）| 対応する設計節 |
|:---|:----------|:------------|
| NFR-W10-3 | 標準ライブラリのみで実装すること（追加ライブラリは NFR-W10-1 未達の実測根拠がある場合のみ MAY）| §8 実装制約サブセクション（§8 直前に配置）|

---

## §7 影響を受けるコンポーネント

### 直接影響（Wave 11 BUILDING で実装）

| コンポーネント | 影響内容 | 参照先 |
|:------------|:--------|:------|
| `MilestoneRegistry`（新規 / Wave 11 BUILDING）| D-1 の API シグネチャ案に基づき実装する | D-1 / Spike V-1 |
| `build_dashboard.py`（最小変更）| `MilestoneSourceMerger` 参照箇所を `MilestoneProvider` 型変数に差し替える。変更量は Wave 11 PLANNING で Grep 実測後に確定 | D-1 / Spike V-2 |
| POO スキル本体（新規 / Wave 11 BUILDING）| `MilestoneRegistry` read-only API + D-2〜D-5 のロジックを実装する | D-2〜D-6 全体 |

### 間接影響（起動 API 契約として参照されるが内部不改修）

| コンポーネント | 影響内容 |
|:------------|:--------|
| `/autonomous` SKILL.md | 起動 API 契約の「前提条件・期待出力」として D-4 に参照される。内部実装の変更はない |
| `/goal-driven` SKILL.md | 同上 |
| `/lam-orchestrate` SKILL.md | 同上 |
| `/full-review` SKILL.md | 同上 |

### 影響なし（明示）

- `autonomous-mode/design.md` / `goal-driven-orchestration/design.md` 等の設計書の内部
- `.claude/rules/` 配下の全ファイル
- `docs/adr/` 配下の既存 ADR
- **既存 3 パーサ（SessionStateParser / TasksParser / CurrentPhaseParser）の内部実装**（GitHistoryParser は POO スコープ外 / §2 Non-Goals 参照）
- `merger.py` の `MilestoneSourceMerger` クラスの内部実装（Registry 昇格後も merge ロジックは保持）

---

## §8 権限等級

### 実装制約（NFR-W10-3 対応 / W-1）

POO の Wave 11 BUILDING 実装は Python 3.x 標準ライブラリのみを使用しなければならない（MUST）。
追加ライブラリの採用は NFR-W10-1（30 秒以内）を標準ライブラリで達成できない実測値がある場合に限り
`pyproject.toml` に明示した上で許可される（MAY）。

### 権限等級テーブル

| 操作 | 等級 | 備考 |
|:-----|:-----|:----|
| POO の推奨提示 | SE 級 | 読み取り + 推奨出力のみ。副作用なし / **根拠: requirements.md §5 制約・前提 + FR-W10-5（II-C-N2 案 A 採用結果）**（Info-2 対応）|
| スキル起動判断・承認 | PM 級 | ユーザー（L1 統括）の責務。POO は推奨するだけ |
| Phase 規律上書き判断 | PM 級 | ユーザー責務 / POO の責務外（FR-W10-5 (b)）|
| `MilestoneRegistry` の実装（Wave 11）| SE 級 | 既存 API 不変の新規モジュール追加 |
| `build_dashboard.py` の型変数差し替え（Wave 11）| SE 級 | 既存 API 不変の最小変更 |
| 本 design.md の修正 | PM 級 | `docs/specs/` 配下の仕様変更 |

---

## §9 未解決質問（設計レベル OQ）

requirements.md §10 の OQ-1〜4 との重複を避け、設計レベルで残る論点のみを記録する。

**DQ 間の依存関係（Wave 11 着手時の参考）**:
- DQ-W10-1（Registry 配置モジュール）は OQ-1 解消が前提
- DQ-W10-2（出力フォーマット）は OQ-2 解消が前提
- DQ-W10-3（priority タイブレーク基準）は DQ-W10-2 解消結果に依存する可能性あり（出力フォーマットが priority 表現に影響する場合）
- DQ-W10-4（追加 API シグネチャ）は具体的な使用場面の Wave 11 design 定義が前提

| # | 質問 | 想定回答先 |
|:--|:-----|:---------|
| DQ-W10-1 | `MilestoneRegistry` の配置モジュール: `dashboard/` 直下か上位共通モジュールか。Spike V-1 では `.claude/scripts/dashboard/` または新規モジュールを候補としているが、循環インポートの実発生有無（Spike R1）によって選択が変わる | Wave 11 PLANNING（Spike R1 の評価結果を踏まえて確定）|
| DQ-W10-2 | POO の出力形式（OQ-2 に対応する設計詳細）: Markdown テキストとして推奨を出力する場合の定型フォーマット確定。D-3 の「推奨出力フォーマット例」を正式フォーマットとして採用するか、または JSON 構造化出力と使い分けるか | Wave 11 PLANNING（OQ-2 解消後に確定）|
| DQ-W10-3 | 推奨 priority 決定アルゴリズムの詳細: D-3 で「各次元が `unknown` ではないスキルを優先」と定義したが、タイブレーク（同一 unknown 数のスキル間での優先順位決定基準）を実装レベルで確定する必要がある | Wave 11 BUILDING（TDD Red ステップで仕様として確定）|
| DQ-W10-4 | `get_current()` / `list_waves()` 等の追加 API シグネチャは Wave 11 design.md で具体的な使用場面と共に確定する。本 Wave 10 では `get_milestones()` のみを最小確定 API とする（C-2 対応）| Wave 11 PLANNING（具体的な使用場面を設計書で定義後に確定）|

---

## §10 変更履歴

| バージョン | 日付 | 変更内容 |
|:----------|:-----|:--------|
| 0.3.0 | 2026-06-29 | R3 修正（spec-critic design R2 指摘 7 件対応 / R3 Final Green 狙い）: C-1（§7 影響なし明示から GitHistoryParser 削除・既存 3 パーサに訂正・§2 参照追加）/ W-1（D-3 ステップ 2 括弧内に Task 次元は DQ-W10-3 委任の注記追加）/ W-2（§6 AC-W10-8 対応設計節に §8 実装制約参照追加）/ W-3（D-6 MilestoneRegistry 不可時を Milestone=unknown のみに訂正・Wave/Task 次元継続取得を明示）/ Info-1（D-1 エラー耐障害性表 3 行目に D-6 参照注記追加）/ Info-2（D-4 Cross-spec 整合確認末尾に requirements.md §11 参照宣言注記追加）/ Info-3（§9 冒頭に DQ 間の依存関係注記追加）|
| 0.2.0 | 2026-06-29 | R2 修正（spec-critic design R1 指摘 9 件対応）: C-1（D-4 失敗判定列 orphan 注記追加）/ C-2（D-1 get_current・list_waves 削除・DQ-W10-4 追加）/ W-1（§8 実装制約サブセクション追加・§6 NFR マトリクス追加）/ W-2（D-3 priority 基準を unknown 判定軸に明確化）/ W-3（§3 GitHistoryParser 削除・§2 Non-Goals に Git 履歴推定スコープ外追加）/ W-4（D-1 MUST NOT 文言を内部ロジック限定に明確化）/ Info-1（§5 案 γ 参照先明確化）/ Info-2（§8 SE 級根拠追記）/ Info-3（D-5 出力 3 件のみ理由注記追加）|
| 0.1.0 | 2026-06-29 | 初版起草。requirements.md v0.5.0 + spike/README.md v0.4.0 に基づく §1〜§10 全セクション起草。D-1〜D-6（設計詳細）/ Alternatives §5（4 案）/ AC マトリクス §6（全 9 件）確定 |

---

## 権限等級

本ファイルの変更: **PM 級**（仕様書変更）
表記の微調整・typo 修正: **PG 級**

---

## 参照

- `docs/specs/project-overview-orchestrator/requirements.md` v0.5.0（FR-W10-1〜6 / NFR-W10-1〜6 / AC-W10-1〜9 / OQ-1〜4）
- `docs/specs/project-overview-orchestrator/spike/README.md` v0.4.0（V-1〜3 / Wave 11 引き渡し情報）
- `docs/adr/0006-loop-engineering-vocabulary-and-lam-alignment.md`（Stage 3 位置付け / Glossary / 推奨改善方針）
- `docs/specs/b4-dashboard/wave8/design.md` v0.2.3（MilestoneSourceMerger / §10 Registry 昇格契約）
- `docs/specs/b4-dashboard/design.md`（パーサ層独立性原則 / 集約レイヤ設計）
- `docs/specs/autonomous-mode/design.md`（層別エージェント設計の手本）
- `docs/specs/goal-driven-orchestration/design.md`（rubric ファースト + 独立 grader 設計の手本）
- `.claude/skills/autonomous/SKILL.md`（起動 API 契約参照）
- `.claude/skills/goal-driven/SKILL.md`（起動 API 契約参照）
- `.claude/skills/lam-orchestrate/SKILL.md`（起動 API 契約参照）
- `.claude/skills/full-review/SKILL.md`（起動 API 契約参照）
- `.claude/rules/planning-quality-guideline.md`（Design Doc チェックリスト / RFC 2119 / WBS 100% Rule）
- `.claude/rules/terminology.md`（Milestone / Step / Wave / Task 用語ガイドライン）
- `.claude/rules/permission-levels.md`（PG/SE/PM 等級）
