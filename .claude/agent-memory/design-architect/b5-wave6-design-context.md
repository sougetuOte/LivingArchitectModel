---
name: b5-wave6-design-context
description: B-5 b4-dashboard Wave 6 design.md v0.1.0 起草の文脈と設計決定の要点
metadata:
  type: project
---

Wave 6 design.md v0.1.0 を 2026-06-24 に起草した。

**Why:** PoC（Wave 1〜5）で HTML/CSS が最小限にとどまり、Lighthouse Accessibility 89（`color-contrast` / `landmark-one-main` 警告）、ソート/フィルタなし、という実用化ギャップがあった。

**How to apply:** 次回 Wave 6 設計を参照・更新する際はこの記録で背景を確認すること。

## 主要な設計決定

1. **Radix Colors CSS 変数名書式（裏取り済）**
   - 正式書式: `--{colorname}-{step}`（例: `--gray-1`〜`--gray-12`）
   - `--gray-app` 等の意味ベース別名は Radix Themes 上位レイヤーであり Radix Colors スタンドアロンには存在しない

2. **ライト/ダーク切替構造（裏取り済）**
   - Radix 公式は `.dark` クラスベース切替を推奨するが、LAM は JS 不要・NFR-5/FR-5 のため採用しない
   - 採用: `@media (prefers-color-scheme: dark) :root { ... }` で Radix スケール変数をダーク値に上書き
   - 2層構造: Layer 1（Radix スケール変数転記）+ Layer 2（意味ベースエイリアス変数）

3. **CSS/JS 管理場所**
   - builder.py 内の `_render_style()` / `_render_script()` メソッドで管理
   - 外部ファイル分離不可（FR-7 単一 HTML 出力・NFR-5 準拠）

4. **新設メソッド**
   - `_render_style()`, `_render_script()`, `_render_nav()`, `_render_filter_controls()`

5. **JS 行数目標**: 100〜150 行（SHOULD）。150 超過時はスコープ縮小 → PM 級判断の順で対処。

6. **テスト戦略**: jsdom 不使用。regex/文字列検索でJS 関数名の存在確認。Stage 4 は chrome-devtools-mcp で Lighthouse 計測。
