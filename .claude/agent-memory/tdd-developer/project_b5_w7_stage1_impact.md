---
name: b5-w7-stage1-impact
description: B-5 Wave 7 Stage 1 影響分析（T44）— TasksParser regex 厳格化の破損予測
metadata:
  type: project
---

Wave 7 Stage 1 T44 Spike 完了。TasksParser regex 厳格化の影響分析結果。

**Why:** T45（regex 厳格化実装）・T46（既存テスト更新）の前に影響範囲を確定するため。

**How to apply:** T45/T46 着手時に `docs/artifacts/wave7-stage1-impact-analysis.md` を参照。

## 現行実装確認済み事実

- `_TASK_ID_PREFIX_RE = re.compile(r"^(W\d+(?:\.\d+)?-[A-Za-z0-9]+-T\d+)")` (tasks.py L28)
- マッチしない場合は description 全体を id として返す（フォールバック）
- 実データ: 全 6 Milestone の tasks.md 内 378 件チェックボックス行のうち Task ID 形式 0 件

## 新 regex 仕様（design.md §6）

```
r"^- \[([ x])\] (W\d+(?:\.\d+)?-[A-Z]\d+-T\d+|T\d+):"
```

- Milestone 名を `[A-Z]\d+`（大文字+数字のみ）に厳格化
- コロン直後が必須
- Wave 1.5 形式（`W\d+(?:\.\d+)?`）は維持

## 破損予測（確実）

`test_tasks_parser.py` の以下テストが fixture の `W1-A1-T1:` 形式使用のため破損リスクあり:
- L306: `test_parse_scans_multiple_milestones` — `len(tasks) == 3` が変化
- L340: `test_parse_tasks_from_both_milestones_have_correct_milestone_field`
- L387: `test_parse_mixed_milestones_includes_only_existing_tasks_md`

`[A-Z]\d+` は `A1` にマッチするため通過する可能性もある → T45 着手時に実測確認必須。

## 影響なし（確認済み）

- `test_v4_view.py`: TaskInfo を直接構築するため Parser 変更に依存しない（全テスト影響なし）
- `test_wave6_stage4_integration.py`: 同上

## L1 承認待ち緩和案

- fixture の Task ID を `W1-B5-T1:` 等の実プロジェクト形式に統一する（T46 で適用）
- integration テスト群の TasksParser 実呼び出し有無を L1 リレー pytest で確認後 T45 着手
