# Wave 8 Stage 1 — 既存テスト影響分析（T100）

- 作成日: 2026-07-04
- 対象: `test_build_dashboard.py`（Merger 追加によるオーケストレータ変更 `build_dashboard.py`）
- 関連: `docs/specs/b4-dashboard/wave8/design.md` §7 / tasks.md T100

## 1. `data.milestones` を直接検証している箇所

`test_build_dashboard.py` を全文 Grep した結果、`data.milestones` またはそれに類する
アサーションは **0 件**。同ファイルのテストは以下 2 系統のみで構成される。

1. `DashboardBuilder` の import / `render()` の型・非空・DOCTYPE・V-1 placeholder 確認（`DashboardData()` を milestones なしで直接構築）
2. `build_dashboard.py` を subprocess 実行し、終了コード（0/1）・HTML ファイル生成・stdout メッセージ・出力ディレクトリ作成を確認（`data.milestones` の中身には一切踏み込まない）

→ **T102（build_dashboard.py へのMerger呼び出し追加）は `test_build_dashboard.py` の既存アサーションに抵触しない**（期待値更新不要）。

## 2. Merger 追加により期待値更新が必要になる可能性がある箇所（暫定リスト）

| ファイル | 該非 | 理由 |
|:--------|:----|:-----|
| `test_build_dashboard.py` | **なし** | §1 の通り `data.milestones` 非検証 |
| `test_v2_view.py` | 要確認（低リスク） | `DashboardData(milestones=[...])` を直接構築してテストしているため、Merger 経由を前提にしない（Builder は `data` を受け取るだけ） |
| `test_v4_view.py` | 要確認（低リスク） | 同上（フィルタ選択肢は `data.milestones` を直接参照） |
| `test_wave6_stage3_filter.py` | 要確認（低リスク） | フィルタ UI テストが `data.milestones` フィクスチャを使用 |
| `test_wave7_stage3_milestones.py` | 要確認（低リスク） | `multi_milestone_data` 等のフィクスチャが `DashboardData(milestones=[...])` を直接構築 |

上記いずれも **`DashboardData` を直接構築するユニットテスト**であり、`build_dashboard.py` の
`build()` 関数（Merger 呼び出し箇所）を経由しない。そのため Merger 導入後もこれらのテストは
無改変で PASS する見込み（Builder 側コードは変更しないため）。

## 3. 破損予測サマリ

- **破損リスク: 極めて低い**。既存 398 テストのうち `build()` を subprocess 実行するテスト
  （`test_build_dashboard_exits_with_0_or_1` 等 5 件）は終了コードと HTML 生成有無のみを見ており、
  `data.milestones` の内容・順序を検証しないため Merger 追加の影響を受けない。
- **新規追加が必要な検証**: V-2 と V-4 の Milestone 集合一致確認は Stage 2 (T105/T106) の新規テストで担う。
- design.md §7 で見積もられた「期待値更新 1〜5 件」は、本分析の結果 **0 件（Stage 1 時点）** に
  下方修正できる。ただし Stage 2/3 で `_STATUS_LABELS["unknown"]` 追加後、`_render_status_badge()`
  経由で V-2/V-3/V-4 の既存 fixture が `status="unknown"` を含む場合の期待値追加要否は Stage 2 で再確認する。
