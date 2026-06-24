# ダッシュボード Chrome 120+ 互換確認（NFR-3 / Chrome 側）

- 検証日時: 2026-06-24
- Task: W5-B5-T26
- 対応 NFR: NFR-3（Chrome/Edge 120+ 対応）
- 検証範囲: **Chrome のみ**（Edge はユーザー実機で別途確認）
- 対象 HTML: `docs/artifacts/dashboard/dashboard.html`
- 検証手段: chrome-devtools-mcp（DevTools 経由 evaluate_script / take_screenshot）

---

## 1. Chrome バージョン

| 項目 | 値 |
|------|-----|
| userAgent | `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36` |
| Chrome バージョン | **149** |
| vendor | Google Inc. |
| NFR-3 基準（120+） | **YES（149 ≧ 120）** |

---

## 2. テーブル配置確認

`document.querySelectorAll('table')` の全件に対して、所属 section / 行数 / 列数 / `display` / 可視性を確認。

| index | sectionId | rows | columns | displayStyle | isVisible |
|:----:|-----------|:----:|:-------:|:------------:|:---------:|
| 0 | `v2-milestones` | 2 | 3 | table | YES |
| 1 | `v3-waves-B-5` | 2 | 3 | table | YES |
| 2 | `v4-tasks` | 379 | 3 | table | YES |

- 全 3 テーブルが `display: table` で可視（`getBoundingClientRect().height > 0`）。
- rows / columns は 1 以上で正しい構造。
- 判定: **PASS**

---

## 3. ステータスバッジ（色付きラベル）確認

`document.querySelectorAll('[class*="status"], [class*="badge"]')` で抽出。

| 項目 | 値 |
|------|-----|
| 検出総数 | **380** 件 |
| サンプル先頭 10 件の `backgroundColor` | 全件 `rgb(...)`（透明 `rgba(0,0,0,0)` ではない） |

サンプル抜粋（先頭 10 件）:

| tag | class | text | backgroundColor | color |
|-----|-------|------|-----------------|-------|
| SPAN | badge | 進行中 | rgb(0, 123, 255) | rgb(255, 255, 255) |
| SPAN | badge | 進行中 | rgb(0, 123, 255) | rgb(255, 255, 255) |
| SPAN | badge | 完了 | rgb(40, 167, 69) | rgb(255, 255, 255) |
| SPAN | badge | 完了 | rgb(40, 167, 69) | rgb(255, 255, 255) |
| SPAN | badge | 完了 | rgb(40, 167, 69) | rgb(255, 255, 255) |
| SPAN | badge | 完了 | rgb(40, 167, 69) | rgb(255, 255, 255) |
| SPAN | badge | 未着手 | rgb(108, 117, 125) | rgb(255, 255, 255) |
| SPAN | badge | 未着手 | rgb(108, 117, 125) | rgb(255, 255, 255) |
| SPAN | badge | 未着手 | rgb(108, 117, 125) | rgb(255, 255, 255) |
| SPAN | badge | 未着手 | rgb(108, 117, 125) | rgb(255, 255, 255) |

- 「進行中（青）/ 完了（緑）/ 未着手（灰）」の 3 種類が色分け表示されることを確認。
- 文字色（白）と背景色のコントラストが取れている。
- 判定: **PASS**

---

## 4. アンカーリンク動作確認

### 4.1 検出件数とリンク内容

`document.querySelectorAll('a[href^="#"]')` で抽出。

| 項目 | 値 |
|------|-----|
| 検出総数 | **2** 件 |

| href | text |
|------|------|
| `#v3-waves-B-5` | B-5 |
| `#v4-tasks` | Task 一覧を見る |

### 4.2 V-1〜V-4 セクション存在確認

仕様（V-1/V-2/V-3/V-4 関連）の対応セクション ID は HTML 上に全件存在することを確認:

| section ID | heading |
|------------|---------|
| `v1-project-summary` | LAM Dashboard |
| `v2-milestones` | Milestone 一覧 |
| `v3-waves-B-5` | Wave 一覧（B-5） |
| `v4-tasks` | Task 一覧 |

→ V-1〜V-4 のセクション ID は HTML 内に存在するが、アンカーリンク（`<a href="#…">`）として張られているのは V-3 / V-4 への遷移のみ。V-1（自身がトップ）・V-2（Milestone 一覧）への明示的なリンクは設けられていない設計。

### 4.3 クリック動作シミュレート

| アンカー | クリック前 scrollY | クリック後 scrollY | 対象 offsetTop | 動作 |
|----------|:------------------:|:-------------------:|:--------------:|------|
| `#v4-tasks` | 0 | 501.6 | 502 | OK（offsetTop と一致） |
| `#v3-waves-B-5` | 0 | 332.0 | 332 | OK（offsetTop と一致） |

- 両アンカーともクリックで scrollY が 0 以上に変化し、目的セクションの `offsetTop` と一致。
- AC「アンカーリンクがクリック可能」は **PASS**（張られている 2 リンクは正常動作）。

### 4.4 仕様差分メモ（Info）

- AC 文言「V-1 → V-2 → V-3 → V-4 アンカーリンク」の解釈について、現実装は **V-3 / V-4 への 2 リンクのみ** で 4 リンクは張られていない。
- HTML 上の構造（4 セクションすべてに ID 付与）と V-3 / V-4 への遷移リンクで「V-1〜V-4 の階層遷移」は実現できているが、文言と実装の数の差異は記録として残す。
- 重要度: **Info**（動作上の問題はない／必要であれば Audit Wave で確認）。

---

## 5. PASS / FAIL 判定（Chrome 側）

| 検証項目 | 判定 |
|----------|:----:|
| Chrome バージョン 120+ | PASS |
| テーブル配置（display=table、可視） | PASS |
| ステータスバッジ（色付きラベル） | PASS |
| アンカーリンク クリック可能 | PASS（張られている 2 リンクは正常動作） |
| **総合判定（Chrome 側）** | **PASS** |

---

## 6. 結論

- Chrome 149.0.0.0（120+ 要件を満たす）でダッシュボードを表示し、テーブル・ステータスバッジ・アンカーリンクのすべてが正常に動作することを確認した。
- NFR-3 の Chrome 側要件は **PASS**。
- AC 文言と実装のアンカーリンク数差異は Info として記録。実装側に「設計」または「文言」のいずれを正とするかの判断は本タスク射程外（PM 級）。

---

## 7. Edge 確認結果（ユーザー実機 / 2026-06-24 追記）

ユーザー実機による Edge 互換確認: **OK（4 項目すべて確認済）**

| # | 確認項目 | 結果 |
|---|----------|:----:|
| 1 | Edge バージョン 120+ | OK |
| 2 | V-2/V-3/V-4 テーブル表示崩れなし | OK |
| 3 | ステータスバッジ 3 色（青/緑/灰）視認 | OK |
| 4 | `#v3-waves-B-5` / `#v4-tasks` アンカー動作 | OK |

→ **NFR-3 完全 PASS（Chrome 149 + Edge 120+）**

---

## 8. 生成ファイル

| ファイル | サイズ |
|----------|--------|
| `docs/artifacts/dashboard-nfr3-chrome-2026-06-24.md` | 本ファイル |
| `docs/artifacts/dashboard-chrome-2026-06-24.webp` | フルページスクリーンショット（50% リサイズ + WebP q90 / 元 PNG ローカル保持） |
