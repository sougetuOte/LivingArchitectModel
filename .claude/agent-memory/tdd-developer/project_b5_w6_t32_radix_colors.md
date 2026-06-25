---
name: project_b5_w6_t32_radix_colors
description: B-5 Wave 6 T32 — _radix_colors.py 実装（Radix Colors 96 値定数モジュール）
metadata:
  type: project
---

## 実装内容

- 新規作成: `.claude/scripts/dashboard/_radix_colors.py`（RADIX_LIGHT / RADIX_DARK 定数 + import 時構造検証アサート）
- 新規作成: `.claude/tests/dashboard/test_radix_colors.py`（5 件 / smoke test）
- 新規作成: `docs/artifacts/dashboard/radix-color-sources.md`（出典記録 + 手動スクショ手順）

## データソース

L1 が `C:\Users\metral\radix-values.json` に保存済みの 96 hex 値を使用。
取得元: `radix-ui/colors` GitHub リポジトリ `src/light.ts` / `src/dark.ts`

**Why:** VP-2 方針（AI 転記 + 人間スクショ照合）で R-1 リスク（96 値誤転記）に対応。

**How to apply:** T33 で `_render_style()` 実装時は `from dashboard._radix_colors import RADIX_LIGHT, RADIX_DARK` でインポートする。

## 既知の注意点

- git stash 後の復帰で builder.py に L2-B の未コミット変更が混入していた（L2-B の並列作業）
- `test_parser_errors_view.py` の 2 件 FAIL は T32 作業前から存在する（builder.py の L2-B 変更起因）
  T32 新規ファイルはリグレッションを引き起こしていない
- キー形式: 外側 = str 色名（"gray" 等）、内側 = int step（1〜12）、値 = "#xxxxxx" 小文字 hex
