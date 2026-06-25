---
name: project_b5_w6_t34_semantic_html
description: B-5 W6-T34 セマンティック HTML + <main>/<nav> ランドマーク追加の実装知見・T31 分析漏れパターン
metadata:
  type: project
---

## 実装内容（W6-B5-T34）

`builder.py` に `_render_nav()` 新設 + `render()` 改修で `<main id="main-content">` / `<nav id="nav-landmarks">` を追加。

**Why:** Wave 5 Lighthouse 警告 `landmark-one-main` の解消（AC-W6-1 / requirements.md FR-W6-3）。

**How to apply:** T35 以降の CSS テスト実装時も `render()` 出力は `<nav>` + `<main>` 構造前提で書く。

## T31 分析漏れパターン（要注意）

T31 の事前影響分析が見落とした「HTML 全体絶対数カウント系チェック」が 2 件 FAIL した:

| ファイル | 行 | パターン | 影響 |
|---------|-----|---------|------|
| `test_parser_errors_view.py` | 296 | `html.count("<li>")` | `<nav>` の `<li>` 3 件が混入 |
| `test_parser_errors_view.py` | 311 | `html.count("<li>")` | 同上 |

**緩和方針（案 A 改良版）**: セクション限定スライス + count に変更。
```python
start = html.find('<section id="parser-errors">')
end = html.find("</section>", start) + len("</section>")
errors_section = html[start:end]
li_count = errors_section.count("<li>")
```

**教訓**: 今後 `<nav>` / `<main>` / `<ul>` 等のラッパー要素を追加する際は、`html.count("<tag>")` 系の全体カウントテストが潜んでいないか事前 grep を必ず実施すること。

```bash
grep -rn 'html\.count\|len(re\.findall' .claude/tests/dashboard/
grep -rnE 'count\("(<li>|<ul>|<a |<button|<section|<nav|<main)' .claude/tests/dashboard/
```

## 最終結果

- 既存 324 件: 全 PASS（緩和 2 件 + リグレッション 0）
- 構造確認: `<nav id="nav-landmarks">` / `<main id="main-content">` / `class="skip-link"` すべて出力
- V-3 動的生成: milestones=[] のとき 0 件 / [B-4, B-5] のとき nav 内 2 件
- parser-errors は `</main>` の外側に配置（既存位置維持）

## 注意点

- `html.count('href="#v3-waves-')` は `<nav>` の V-3 リンクと V-2 ビューの anchor リンクが両方ヒットする（2 Milestone ならば 4 件）。nav スコープで限定してカウントすること
- `_radix_colors.py` は L2-A 並列担当。`test_radix_colors.py` は `--ignore` で除外して実行
