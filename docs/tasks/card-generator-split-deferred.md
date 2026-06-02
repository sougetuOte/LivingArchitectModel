# card_generator.py 分割（⑤）への繰越 Issue

**起票日**: 2026-06-02
**起票元**: full-review iter1（`docs/artifacts/audit-reports/2026-06-02-iter1.md`）
**権限等級**: PM（C-1 戻り値契約）/ SE（C-2/W-4 内部実装）
**ステータス**: 繰越（⑤ card_generator 2モジュール分割・`/building` 切替で TDD 強制下にて対応）
**根拠**: SESSION_STATE 調整2（card_generator 構造系は⑤送り）/ 設計 `docs/artifacts/audit-2026-06-01/S2b-card-generator.md`

## 繰越 Issue 一覧

| # | 重要度 | 等級 | 箇所 | 内容 |
|---|--------|------|------|------|
| C-1 | Critical | PM | `card_generator.py:886-912, 1010-1032` | `detect_circular_dependencies()` / `build_topo_order()` の戻り値が「循環なし」と「RecursionError 検出失敗」を区別不能（サイレント見逃し）。戻り値契約を `Optional`/例外/明示フラグへ。**仕様明確化が先決**。 |
| C-2 | Critical | SE | `card_generator.py:831-876` | `_find_sccs()` 再帰 Tarjan で1000ノード超 RecursionError。反復実装へ置換。※実 import グラフは数十ノードで**実発火しない潜在バグ**。 |
| W-4 | Warning | SE | `card_generator.py:840` | `index_counter = [0]` closure workaround → `nonlocal`。 |
| I-2 | Info | SE | `card_generator.py:1297,1302` | `specs_dir.glob("*.md")` 非再帰（サブディレクトリ仕様書を拾わない）。 |

## 免除理由（A-2 準拠）

- **技術的妥当性**: C-1 は戻り値型の仕様変更（PM級）を伴い、AUDITING モードでの即時修正より⑤の TDD（Red→Green）で契約を先にテスト化する方が安全。C-2 は実スケールで未発火の潜在バグであり、分割と同時に反復実装へ置換するのが効率的。
- **対象フェーズ**: ⑤（BUILDING・`/building` 切替で TDD 強制）。
- **追跡**: 本ファイル + `S2b-card-generator.md`（7ブロック分割候補・最優先2ブロック=グラフ解析 L799-1090・影響範囲分析 L1093-1305）。

## 完了条件

- card_generator が2モジュールに分割され、C-1 の戻り値契約が仕様化・テスト化される。
- C-2 が反復実装に置換され、大規模グラフ（>1000ノード）のテストが緑。
- W-4/I-2 が分割の過程で解消。
