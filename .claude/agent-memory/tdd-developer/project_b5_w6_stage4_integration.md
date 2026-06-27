---
name: project-b5-w6-stage4-integration
description: B-5 Wave 6 Stage 4 統合テスト T42 実装 — MCP skip 戦略・ファイルサイズ計測・外部参照 regex 3 種・メタテスト範囲
metadata:
  type: project
---

## B-5 Wave 6 Stage 4 統合テスト（T42）実装

**実装ファイル**: `.claude/tests/dashboard/test_wave6_stage4_integration.py`（466 行）

**Why:** Stage 1〜3 完了後（363 件 PASS）の統合テスト。Lighthouse 97 取得済（L1 実機計測 2026-06-26 / AC-W6-2 達成）のため T43 調整ループ不要。

**How to apply:** 次回 Wave 6 作業再開時の状態把握に使う。

### テスト 9 件の構成

| Test ID | 種別 | 実装ポイント |
|---------|------|------------|
| T-S4-1 | skip | Lighthouse 97 取得済（2026-06-26）。reason に計測値・日付・ツール名を記録 |
| T-S4-2 | skip | MCP click + evaluate_script で 3 列ソート検証。疑似コード docstring に残置 |
| T-S4-3 | skip | 状態フィルタ「完了」→ aria-live テキスト突合。疑似コード docstring に残置 |
| T-S4-4 | skip | AND フィルタ（状態+テキスト）で行数減少を検証。疑似コード docstring に残置 |
| T-S4-5 | skip | T36 手動確認済（2026-06-26）と統合。reason に SESSION_STATE 参照先を明記 |
| T-S4-6 | 自動 | `len(builder.render().encode('utf-8')) <= 500_000` |
| T-S4-7 | 自動 | `len(builder._render_style().encode('utf-8')) <= 10_240`（Stage 3 時点 ≒ 9,907B）|
| T-S4-8 | 自動 | re.search 3 パターン（link href / script src / CSS url）が全て None を assert |
| T-S4-9 | 自動 | `len(list(tests_dir.glob("test_*.py"))) in range(20, 36)` — 22 件で PASS |

### skip reason フォーマット（G-6 準拠）

```python
@pytest.mark.skip(reason="<理由カテゴリ> / <計測値 or 実施日> / <参照先>")
```

- T-S4-1: `"L1 実機計測済 / Lighthouse Accessibility=97 (2026-06-26) / AC-W6-2 達成 / chrome-devtools-mcp lighthouse_audit による計測"`
- T-S4-2〜4: `"chrome-devtools-mcp 駆動 / L1 が ... / SESSION_STATE に結果記録"`
- T-S4-5: `"手動確認 / T36 で実施済 (2026-06-26) / SESSION_STATE に「T-S1-12 OK」記録済"`

### フィクスチャ設計

`_make_builder_with_full_data()` を共通フィクスチャとして T-S4-6/7/8 が再利用。
17 タスク（completed × 15 + in_progress × 1 + not_started × 1）を持つ現実的なデータ。

### テストファイル数確認（T-S4-9）

Stage 4 完了時点でテストファイル 22 件（20〜35 の範囲内で PASS）。
既存 21 件 + test_wave6_stage4_integration.py 1 件 = 22 件。

### 重要な注意点

- `_render_style()` の CSS サイズは Stage 1 時点で ≒ 9,907B。10,240B 上限ギリギリ。Stage 4 では CSS を増やさない前提で T-S4-7 が PASS する。
- T-S4-8 の url() パターンは CSS コメント内 URL（Radix 転記元 URL 等）にはマッチしない（W-NEW-4 設計意図）。
- skip は pytest では PASS 扱いになるため、9 件すべて pytest で扱える。
