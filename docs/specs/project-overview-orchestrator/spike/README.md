# Spike: MilestoneRegistry read-only API — 実在可能性検証

- バージョン: 0.4.0
- 作成日: 2026-06-29
- 更新日: 2026-06-29（R4 修正）
- ステータス: Draft
- 関連要件: `docs/specs/project-overview-orchestrator/requirements.md` FR-W10-4（MilestoneRegistry read-only API）
- 起草者: a-design1（design-architect）

> **Spike の性質**: 本文書は仕様検証の記録である。実装ファイル（`src/` 配下等）への commit はスコープ外。
> API シグネチャ案・擬似コード断片は含むが、動作コードの作成はしない。

---

## §1 Spike の目的

Wave 10 内で、`MilestoneRegistry` read-only API の **実在可能性（feasibility）** を検証する。
具体的には以下の問いに答えることが目的である。

1. Wave 8 の `MilestoneSourceMerger`（`MilestoneProvider` Protocol 実装済み）を **read-only API でラップする最小設計** は実現可能か
2. `MilestoneRegistry` が `MilestoneProvider` Protocol を実装することで、b4-dashboard と POO が **同一 SSOT を参照できるか**
3. `MilestoneRegistry` の導入が b4-dashboard の既存実装（`build_dashboard.py` / `builder.py` 等）に **最小限の変更で収まるか**

Spike の成果物は「設計書への入力（Wave 11 design.md 起草の前提）」として扱われる。
実装の完了・テストの通過は Spike の成果物として求めない。

> **ADR-0006 §却下案 B との境界**: ADR-0006 は「先行実装の罠」として ⑥ の先行実装を却下した。
> 本 Spike は「仕様の確定手段」であり「実装の先行」ではない。シグネチャ案・接続経路の検証のみを行い、
> `src/` への commit を行わないことで、この境界を維持する。

---

## §2 Spike の範囲

### 対象

| 対象 | 内容 |
|:-----|:-----|
| `MilestoneProvider` Protocol（Wave 8 実装済み）| `get_milestones() -> list[MilestoneInfo]` の実装済み契約を確認し、`MilestoneRegistry` への昇格パスを評価する |
| `MilestoneRegistry` API シグネチャ案 | `MilestoneProvider` を実装した `MilestoneRegistry` クラスの最小インターフェース候補を定義する |
| b4-dashboard 参照経路の確認 | `build_dashboard.py` が `MilestoneSourceMerger` から `MilestoneRegistry` へ切り替えるために必要な変更量を特定する |
| パフォーマンス想定 | `MilestoneRegistry.get_milestones()` の処理時間の概算（既存 Merger の計測値 NFR-W8-1: 1 秒以内 を基準に評価）|

### 非対象（§4 Non-Spike に明記）

`src/` への実装ファイルのコミット、テストコードの作成、dashboard UI の変更は対象外。

---

## §3 検証項目

### V-1: `MilestoneRegistry` API シグネチャ案

**目的**: `MilestoneProvider` Protocol を満たす `MilestoneRegistry` の最小クラス設計を確定する。

**検証方法**: 既存 `MilestoneSourceMerger`（`docs/specs/b4-dashboard/wave8/design.md` §4）を参照し、
以下のシグネチャ案が Protocol 契約を満たすかを文書上で確認する。

**シグネチャ案（擬似コード）**:

```python
# registry.py（将来の配置候補: .claude/scripts/dashboard/ または新規モジュール）
from typing import Protocol, runtime_checkable
from dashboard.models import MilestoneInfo

class MilestoneRegistry:
    """MilestoneProvider Protocol を実装する共通基盤 SSOT。
    
    Wave 8 の MilestoneSourceMerger が担っていた「SessionState + tasks.md の Milestone 集約」を
    プロジェクト共通の読み取り口として提供する。

    read-only のみ実装する（MUST NOT write）。
    """

    def __init__(self, project_root: Path) -> None:
        """データソースパスを受け取り、初期化する（遅延ロード / Merger を内包）。"""
        ...

    def get_milestones(self) -> list[MilestoneInfo]:
        """MilestoneProvider 実装。統合済み Milestone リストを返す。"""
        ...
```

**確認ポイント**:
- `get_milestones()` が Protocol の無引数シグネチャに合致するか（Yes: 合致）
- `MilestoneSourceMerger` を内包する設計（昇格）と、完全置換の設計のどちらが b4-dashboard への影響が小さいか

**事前評価（Wave 8 design.md §10 参照）**:
`MilestoneProvider` Protocol は `get_milestones() -> list[MilestoneInfo]` として Wave 8 で定義済み。
`MilestoneRegistry` がこの Protocol を実装することで、`build_dashboard.py` 内の `MilestoneSourceMerger`
参照箇所を型 `MilestoneProvider` に変更するだけで差し替えが可能な設計になっている（G4 達成条件 3 の既存根拠）。

---

### V-2: b4-dashboard 参照経路の影響評価

**目的**: `MilestoneSourceMerger` から `MilestoneRegistry` への切り替えが b4-dashboard に与える変更量を事前評価する。

**対象ファイル（確認対象 / 変更は非スコープ）**:

| ファイル | 確認内容 | 想定変更量 |
|:--------|:--------|:---------|
| `build_dashboard.py` | `MilestoneSourceMerger` のインポート箇所・呼び出し箇所数 | `import` 文 1 行 + 呼び出し 1 箇所（constructor 注入）の変更想定 |
| `merger.py` | `MilestoneSourceMerger` の内部を `MilestoneRegistry` がラップするか、引き継ぐかの経路 | 「ラップ」採用の場合は merger.py は無変更のまま Registry が上位に立つ |
| 既存テスト群（test_build_dashboard.py 等）| Registry 切替後に期待値が変わるテスト数 | `data.milestones` の取得経路が変わるが結果は同等になるため変更最小の見込み |

**Spike 時の確認手順**:
1. `build_dashboard.py` 内の `MilestoneSourceMerger` 参照箇所を Grep で特定し行数を記録する
2. 「`MilestoneProvider` 型変数への差し替え」で何行の変更が発生するかを評価する
3. `tests/dashboard/` 内の `data.milestones` を assert するテストを Grep で特定し件数を記録する

> 上記確認は Spike 実施者が Read / Grep ツールで行い、その結果を本文書の §5「想定リスク」または §6「後続 Wave への引き渡し」に反映する。

---

### V-3: パフォーマンス想定

**目的**: NFR-W10-1（30 秒以内）が `MilestoneRegistry` 導入後も充足されるかを事前評価する。

**評価根拠**:

| 指標 | 値 | 根拠 |
|:-----|:--|:-----|
| `MilestoneSourceMerger.get_milestones()` 上限 | 1 秒以内（NFR-W8-1 / 最大 30 件想定）| b4-dashboard wave8/requirements.md §4 |
| POO の現在地特定処理（FR-W10-1）| SESSION_STATE.md 読み取り + パース：概算 1〜2 秒 | **概算 1〜2 秒の根拠**: Wave 7 以前の実測値の参照先は未確定（本 Spike では推定値として扱う / Wave 11 BUILDING 開始時に実測で検証する）|
| POO の推奨生成処理（FR-W10-2）| tasks.md 読み取り + フィルタリング：概算 1〜3 秒 | ファイル数・サイズに依存 |

**事前評価**: Registry の処理時間（≤ 1 秒）+ POO 固有処理（≤ 5 秒）= 合計 6 秒以内の見込み。
NFR-W10-1（30 秒）に対して余裕があり、パフォーマンスは問題なしと評価する。

**要実測**: Wave 11 BUILDING 時に実際のプロジェクトデータで計測し、本見積もりを更新する。

---

## §4 Non-Spike（実装に踏み込まない範囲）

以下は本 Spike では実施しない。Wave 11 以降の設計・実装フェーズで扱う。

| 項目 | 理由 |
|:-----|:-----|
| `src/` / `.claude/scripts/` への実装ファイルコミット | Spike = 仕様検証。実装着手は Wave 11 BUILDING |
| テストコードの作成・実行 | Wave 11 tasks.md 確定後に TDD サイクルで実施 |
| b4-dashboard の `build_dashboard.py` 変更 | registry.py が確定してから Wave 11 で実施 |
| dashboard UI の変更（HTML / CSS / JS）| b4-dashboard は変更対象外（requirements.md §2 Non-Goals 参照）|
| SESSION_STATE.md への書き戻し設計 | Wave 11+ の別 Wave で扱う |
| gabriel（骨子 ②）との統合 | 別 ADR / POO v2 |

> **ADR-0006 §却下案 B との境界（再確認）**: 「先行実装の罠」を回避するため、
> 本 Spike は「設計の入力情報の収集」に徹する。
> API シグネチャ「案」は Wave 11 設計書でレビューを経て「確定」に昇格する。
> Spike 段階の「案」を実装に使用してはならない。

---

## §5 想定リスク

| # | リスク | 影響度 | 対策 |
|:--|:------|:------|:-----|
| R1 | `MilestoneRegistry` の配置モジュールが b4-dashboard 内（`.claude/scripts/dashboard/`）と POO モジュール間で循環インポートを引き起こす | 中 | registry.py を両モジュール共通の上位モジュールに配置する案を Wave 11 設計書で検討する |
| R2 | b4-dashboard の既存テストが `MilestoneSourceMerger` の constructor に直接依存しており、Registry 切替で期待値変更が多発する | 中 | V-2 の Grep 調査で事前に件数を確定する。10 件超の場合は Wave 11 でフィクスチャ分離を先行する |
| R3 | Wave 8 の `MilestoneProvider` Protocol が `runtime_checkable` でない場合、`isinstance` チェックに依存するコードが動作しない | 低 | `wave8/design.md` §10 に `@runtime_checkable` が明示されているため影響なし（確認済み）|
| R4 | `tasks.md` の形式が Milestone ごとに異なり、全 Milestone の tasks.md を走査する処理時間が NFR-W10-1 の閾値を超える | 低 | V-3 の事前評価では 6 秒以内の見込み。Wave 11 BUILDING 開始時に実測する |
| R5 | Wave 11 に引き渡す前提条件が Wave 10 内で確定されず、Wave 11 tasks.md 起票時に再度 Spike が必要になる | 低 | §6 の引き渡し方法に OQ-1〜3 の回答状況を明記することで再 Spike リスクを可視化する |

---

## §6 後続 Wave への引き渡し方法

Wave 11 tasks.md 起票時（Wave 11 PLANNING 着手時）に前提条件として提示する情報を記録する。

### Wave 11 設計書（design.md）の前提条件

| 前提条件 | 本 Spike での確定状況 | 確定方法 |
|:---------|:--------------------|:--------|
| `MilestoneRegistry` の配置モジュール | 未確定（OQ-1 に連動）| Spike 実施後に §5 R1 の評価結果で更新する |
| b4-dashboard 側の変更量（行数）| 事前評価のみ（V-2 で Grep 後に確定）| Spike 実施者が行数を §5 または本節に追記する |
| `MilestoneRegistry` のシグネチャ（確定版）| V-1 の案を Wave 11 design で確定 | Wave 11 設計書レビュー（spec-critic）で確定 |
| パフォーマンス実測値 | 想定値のみ（V-3 参照）| Wave 11 BUILDING 開始時に実測 |
| OQ-1〜4 の解消状況確認（OQ-4 は FR-W10-3 表の実装レベル詳細 / Wave 11 PLANNING で確定）| OQ-1〜3 は未回答（Wave 10 Open Questions）/ OQ-4 は論理的条件確定済み・実装詳細は Wave 11 PLANNING | Spike 実施 + Wave 11 設計書レビューで解消 |

### Wave 11 tasks.md の起票トリガー

以下が揃った状態を Wave 11 tasks.md 起票の前提条件とする。

Wave 11 PLANNING の進め方: PLANNING 開始 → **Wave 11 design.md 起草 → PM 承認 → tasks.md 起票 → BUILDING 着手** の順序で進める。

- [ ] Wave 10 の `requirements.md` が PM 承認済み
- [ ] **Wave 11 PLANNING で起草する `design.md` が PM 承認済み**（本 Spike は design.md の Input となる）
- [ ] Spike 実施者が §6 の空欄（変更量・確定事項）を埋めた状態で本文書を更新済み
- [ ] OQ-1〜4 の解消状況が確認されている（OQ-1〜3 は未回答の場合は Wave 11 design.md で解消する計画を明記 / OQ-4 は論理的条件確定済み・実装レベル詳細は Wave 11 PLANNING で確定）

---

## 変更履歴

| バージョン | 日付 | 変更内容 |
|:----------|:-----|:--------|
| 0.1.0 | 2026-06-29 | 初版起稿 |
| 0.2.0 | 2026-06-29 | R2 修正（W5 対応）。§6 の Wave 11 前提条件「Wave 10 の `design.md` が PM 承認済み」を「Wave 11 PLANNING で起草する `design.md` が PM 承認済み」に訂正。Wave 11 の構造（PLANNING → design.md 起草 → PM 承認 → tasks.md 起票 → BUILDING 着手）の順序を §6 に明記 |
| 0.3.0 | 2026-06-29 | R3 修正（II-I-N2 対応）。§3 V-3 の POO 現在地特定処理の概算根拠に「参照先未確定 / 推定値 / Wave 11 実測検証方針」を追記 |
| 0.4.0 | 2026-06-29 | R4 修正（I-R4-3）。§6 OQ 参照リストに OQ-4 を追加（「OQ-4 は FR-W10-3 表の実装レベル詳細 / Wave 11 PLANNING で確定」を明記）。Wave 11 tasks.md 起票トリガーの OQ 参照も OQ-1〜4 に更新 |

---

## 権限等級

本ファイルの変更: **PM 級**（仕様書変更）
Spike 結果の追記（§5・§6 の空欄埋め）: **SE 級**（調査結果の記録）

---

## 参照

- `docs/specs/project-overview-orchestrator/requirements.md`（FR-W10-4 / Wave 10 スコープ）
- `docs/specs/b4-dashboard/wave8/design.md`（§4 MilestoneSourceMerger 詳細設計 / §10 Registry 昇格契約）
- `docs/specs/b4-dashboard/wave8/requirements.md`（NFR-W8-1 パフォーマンス上限 / MilestoneProvider Protocol）
- `docs/adr/0006-loop-engineering-vocabulary-and-lam-alignment.md`（§却下案 B — 先行実装の罠）
- `.claude/rules/planning-quality-guideline.md`（Design Doc チェックリスト / Non-Goals 定義）
