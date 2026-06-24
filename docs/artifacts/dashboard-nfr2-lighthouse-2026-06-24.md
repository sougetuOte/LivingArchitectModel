# ダッシュボード ブラウザ表示完了時間 計測記録（NFR-2 / AC-6）

- 計測日時: 2026-06-24
- Task: W5-B5-T23
- 対応 NFR: NFR-2（ブラウザ表示完了時間 3 秒以内）
- 対応 AC: AC-6（Chrome DevTools Lighthouse 等で 3 秒以内表示を確認）

---

## 環境情報

| 項目 | 値 |
|------|-----|
| OS | Windows 11 Pro 10.0.26200 |
| ブラウザ | Chrome 149.0.0.0（Lighthouse hostUserAgent 由来） |
| User Agent | `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36` |
| Lighthouse | 13.3.0 |
| 計測経路 | chrome-devtools-mcp（Performance Trace + Lighthouse Audit） |
| 対象 URL | `file:///D:/work7/LivingArchitectModel/docs/artifacts/dashboard/dashboard.html` |
| 対象 HTML サイズ | 132 KB |
| CPU throttling | 1x（スロットリングなし） |
| Network throttling | none |

---

## 計測結果（Performance Trace / Core Web Vitals）

chrome-devtools-mcp `performance_start_trace`（reload=true, autoStop=true）で 1 回計測。

| メトリクス | 計測値 | 備考 |
|------------|--------|------|
| **LCP（Largest Contentful Paint）** | **62 ms** | LCP 要素は `<td>` テキスト（nodeId 89）。ネットワーク取得なし |
| TTFB（Time to First Byte） | 0.5 ms | LCP の 0.8% |
| Element Render Delay | 61 ms | LCP の 99.2% |
| **CLS（Cumulative Layout Shift）** | **0.00** | レイアウトシフトなし |
| FCP | 計測ツール側で個別値の明示なし（LCP=62ms と同等以下と推定） | LCP より早く発火する性質上、LCP の上限値が FCP の上限値となる |

> 補足: `performance_analyze_insight(LCPBreakdown)` は "Estimated savings: none" を返した（追加の最適化余地なし）。

---

## 計測結果（Lighthouse Audit）

chrome-devtools-mcp `lighthouse_audit`（device=desktop, mode=snapshot）で実行。

> Lighthouse の `navigation` モードは `file://` URL を受け付けず `INVALID_URL` エラーとなるため、`snapshot` モードを採用。Performance カテゴリは Lighthouse の仕様上含まれない（公式説明: "This excludes performance. For performance audits, run performance_start_trace"）ため、Performance は上記 Performance Trace を主指標とする。

| カテゴリ | スコア |
|---------|-------|
| Accessibility | 89 |
| Best Practices | 100 |
| SEO | 60 |
| Agentic Browsing | 50 |

監査結果サマリ: Passed 20 / Failed 5 / Total Timing 2052.88ms

### Failed audits 内訳

| Audit ID | カテゴリ | 内容 |
|----------|----------|------|
| `color-contrast` | Accessibility | 背景色と前景色のコントラスト比不足 |
| `landmark-one-main` | Accessibility | `<main>` ランドマークが存在しない |
| `meta-description` | SEO | meta description が存在しない |
| `robots-txt` | SEO | robots.txt が無効（ローカル file:// 由来） |
| `llms-txt` | Agentic Browsing | llms.txt がレコメンデーションに従っていない |

---

## NFR-2 / AC-6 基準との比較

| 基準 | 基準値 | 実測値 | 達成 |
|------|--------|--------|------|
| NFR-2（ブラウザ表示完了時間） | 3,000 ms 以内 | **LCP = 62 ms** | **PASS** |
| AC-6（Lighthouse 等で 3 秒以内表示を確認） | Lighthouse 計測実施・3 秒以内 | LCP 計測実施・62 ms（基準の約 1/48） | **PASS** |

LCP 62 ms は NFR-2 基準（3,000 ms）の約 **2.1%** であり、極めて大きなマージンで基準を達成している。CLS=0.00 によりレイアウトシフトもない。

---

## 生成ファイル一覧

| ファイル | サイズ | 用途 |
|---------|--------|------|
| `docs/artifacts/dashboard-nfr2-lighthouse-2026-06-24.md` | 本ファイル | NFR-2 計測記録（本ドキュメント） |
| `docs/artifacts/lighthouse-2026-06-24/report.html` | 404 KB | Lighthouse 監査レポート HTML |
| `docs/artifacts/lighthouse-2026-06-24/report.json` | 320 KB | Lighthouse 監査レポート JSON（原データ） |

---

## 観察事項

### Performance 観点

- LCP 62 ms / CLS 0.00 で NFR-2 を大きく下回り達成。`docs/artifacts/dashboard/dashboard.html` は単一 HTML（132 KB）に CSS/JS をインライン化した自己完結ファイルであり、外部依存・ネットワーク fetch が無いため理論上の最速ケースに近い
- LCP の 99.2% が Render Delay（61 ms）であり、TTFB は 0.5 ms。最適化の追加余地は Lighthouse 側も "Estimated savings: none" と評価

### Lighthouse 観点

- **Best Practices 100** は維持
- **Accessibility 89** — 主な指摘は (1) コントラスト不足 (2) `<main>` ランドマーク欠如。AC-9（WCAG 2.1 AA）との突合は別タスク（T28 想定）で再評価対象
- **SEO 60 / Agentic Browsing 50** — `meta description` 欠如、`robots.txt` 不在、`llms.txt` 不在による減点。本ダッシュボードはローカル file:// で配布する内部生成物のため SEO/Agentic 系減点は **要件外**（NFR/AC 対象外）と判断
- `navigation` モードを使えなかった点は file:// プロトコルの Lighthouse 制約由来。HTTP サーバ経由で再計測すれば Performance カテゴリも取得可能だが、本タスク要件は LCP ≤ 3 秒の確認であり Performance Trace で達成済み

### 環境制約

- 計測は 1 回（要件: 「3 秒以内を確認」の単発検証）。揺れマージン考慮しても LCP 62 ms は基準の 1/48 であり、回帰が起きても余裕は十分
- file:// URL では Lighthouse `navigation` モードが INVALID_URL を返す。これは Lighthouse 13 系の既知挙動

---

## 指示射程超過の発生有無

**なし**（指示書の範囲内で完結）。

- 書き出しは `docs/artifacts/dashboard-nfr2-lighthouse-2026-06-24.md` の 1 ファイル + Lighthouse レポート 2 ファイル（指示通り `docs/artifacts/lighthouse-2026-06-24/` 配下）
- `emulate` 系設定は触っていない（T25 用に Chrome 状態保持）
- gitignore 判定は実施せず（観察結果のみを下記に記録）

### gitignore 観察メモ（L1 判断委ね）

- `docs/artifacts/lighthouse-2026-06-24/` 配下に合計 約 724 KB（report.html 404 KB + report.json 320 KB）が生成された
- 日付付きディレクトリ命名であり、計測のたびに新規ディレクトリが増える設計。中長期で `docs/artifacts/lighthouse-*/` を gitignore 対象にするか、定期棚卸し対象にするかは PM 級判断対象

---

## 次タスク T25 への影響メモ

| 項目 | 現状 |
|------|------|
| Chrome | 起動中・page 1 が selected |
| 現在の URL | `file:///D:/work7/LivingArchitectModel/docs/artifacts/dashboard/dashboard.html` |
| Viewport / emulate | 未改変（デフォルト・desktop） |
| Network throttling | none（未改変） |
| CPU throttling | 1x（未改変） |
| キャッシュ状態 | Performance Trace で 1 回 reload 済み（次タスクで再 reload しても問題なし） |

T25（オフライン検証）は同じ Chrome を流用可能。`emulate(networkConditions=...)` で offline 化する想定であれば、本ページのまま reload/navigate して動作確認できる。

---

## 結論

NFR-2（ブラウザ表示完了時間 3 秒以内）および AC-6（Lighthouse 等で 3 秒以内表示を確認）は **PASS**。LCP 62 ms / CLS 0.00 / Lighthouse Best Practices 100 / Accessibility 89。Performance 観点での追加最適化余地は計測ツール側も "none" と評価。
