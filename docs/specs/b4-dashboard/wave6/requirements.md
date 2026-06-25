# b4-dashboard Wave 6 — requirements.md

- バージョン: 0.2.0
- 作成日: 2026-06-24
- 更新日: 2026-06-25（design.md v0.2.0 spec-critic レビューに基づく整合修正）
- ステータス: **Approved**（v0.1.0 承認 2026-06-24 / v0.2.0 ユーザー事後承認 2026-06-25）
- マイルストーン: B-5（Wave 6+ UI 改善反復フェーズ）
- 関連:
  - `docs/specs/b4-dashboard/requirements.md` v0.2.0（PoC 仕様 / 継承元）
  - `docs/specs/b4-dashboard/wave6/clarify-2026-06-24.md`（PLANNING インタビュー / 最優先）
  - `docs/artifacts/b4-dashboard-poc-review.md`（Wave 5 PoC レビュー / 要望起点）

---

## §1 Problem Statement

B-5 b4-dashboard は Wave 1〜5 の BUILDING を経て PoC 完了（AC-1〜AC-8 全 GREEN）したが、
ユーザー実機レビュー（2026-06-24）にて「素の HTML 感」に起因する実用化阻害が確認された。
具体的には CSS スタイリングが最小限に留まり視認性が低く、テーブルソートおよびフィルタリング機能が
存在しないため、ユーザーが所望の情報を素早く特定できない。

Wave 6 はこの実用化ギャップを解消することを目的とする。CSS スタイリング・テーブルソート・
フィルタリングの三軸を一括対応し、Lighthouse Accessibility スコア 95+ を客観指標として
実用ダッシュボードへの格上げを目指す。

---

## §2 Goals

Wave 6 で達成する成果を SMART で定義する。

1. **ユーザビリティ**: ユーザーが「ダッシュボードが使いやすい」と主観評価で OK を出すこと
2. **アクセシビリティ**: Lighthouse Accessibility スコアが 95 以上に達すること（現状: 89）
3. **スタイリング**: Radix Colors パレットを CSS カスタムプロパティで適用し、ライト/ダーク両テーマで一貫した配色を実現すること
4. **ソート**: テーブル列ヘッダクリックで昇順・降順ソートが動作すること
5. **フィルタ**: 状態値・Milestone・テキスト検索でテーブル行を絞り込めること
6. **既存 NFR 維持**: NFR-1（500 KB 未満）/ NFR-4（30 秒以内生成）/ NFR-5（外部依存なし）/ FR-5（オフライン動作）を全て維持すること

---

## §3 Non-Goals（明示的に Wave 6 で対応しないこと）

以下は Wave 6 のスコープ外とする。着手した場合は scope creep として差し戻す。

- **完全レスポンシブ対応**: PC ブラウザ専用とする（横スクロールは許容。Wave 7+ 候補）
- **CSS フレームワーク採用**: Tailwind / Bootstrap / Pico CSS 等は採用しない。pure CSS フルスクラッチのみ
- **独自ブランドカラー設計**: Radix Colors 標準パレット（gray / blue / green / amber）を使用する。独自パレット策定は行わない
- **JS ライブラリ採用**: Vanilla JS inline のみ。Alpine.js / jQuery 等は使用しない
- **Task ↔ Wave / Milestone 階層化**: 情報構造の再設計は Wave 7+ 候補（clarify Q1 選択肢 D 不採用）
- **複数 Milestone Step 独立管理（FC-7 完全対応）**: Wave 6 では現行の単一フェーズ表示を維持する。FC-7 の着手トリガーは未達成のため Wave 7+ 候補
- **グラフ・チャートによる統計可視化**: FC-8 として将来候補
- **npm パッケージの追加**: NFR-5 堅持・package.json 変更（PM 級）は本 Wave で行わない
- **`.claude/settings.json` の変更**: 追加フックの設定変更は本 Wave で行わない（PM 級変更のため）

---

## §4 機能要件（FR）

> **継承宣言**: 既存 FR-1〜FR-11（PoC 仕様 v0.2.0）は Wave 6 でも全て維持する（§7 参照）。
> 本節は Wave 6 で**新規追加**する機能要件のみを定義する。

### FR-W6-1: CSS 基盤（MUST）

ダッシュボード HTML は以下の CSS 仕様を満たさなければならない:

- CSS カスタムプロパティ（`--` プレフィックス変数）で全配色を定義しなければならない（MUST）
- ライトモードとダークモードの 2 セットのカスタムプロパティを定義しなければならない（MUST）
- `@media (prefers-color-scheme: dark)` によりユーザーの OS 設定に自動追従しなければならない（MUST）
- 追加 CSS のサイズは 10 KB 以下でなければならない（MUST）（Radix Colors 手動転記分を含む）
- 外部 CSS ファイルへの参照を持ってはならない（MUST NOT）。全 CSS は単一 HTML 内に `<style>` タグとして埋め込むこと
- CSS Grid または flexbox を使用してレイアウト構造を定義してよい（MAY）

### FR-W6-2: Radix Colors パレット適用（MUST）

ダッシュボードは以下のカラーパレット仕様を満たさなければならない:

- 使用するカラースケール: gray / blue / green / amber の 4 系統（各 12-step scale）× ライト / ダーク 2 セット（MUST）
- 各カラーの CSS 変数値は https://www.radix-ui.com/colors の公式値を手動転記して `<style>` 内に定義しなければならない（MUST）
- 外部 CDN または npm パッケージへの参照を持ってはならない（MUST NOT）（FR-5 / NFR-5 と整合）
- 本文テキストには step 11 または step 12 の値を使用しなければならない（MUST）（コントラスト比 4.5:1 以上を確保するため）
- 背景色には step 1 または step 2 の値を使用しなければならない（MUST）

> **upstream-first ステータス**: Radix Colors の CSS 変数名書式（例: `--gray-1`、`--gray-app` 等）は
> 公式ページ（https://www.radix-ui.com/colors）での確認を推奨する。
> 本 requirements.md の段階では変数名の正確な書式を規定せず、design.md で裏取り済みの書式を定義すること。
> 変数名書式が未確認の場合は design.md 起草時に「未確認（要裏取り）」と明示する。

### FR-W6-3: アクセシビリティ基盤（MUST）

ダッシュボードは以下のアクセシビリティ要件を満たさなければならない:

- **フォント**: システムフォントスタック `system-ui, -apple-system, "Segoe UI", "Hiragino Sans", "Noto Sans JP", sans-serif` を使用しなければならない（MUST）
- **等幅フォント**: コードまたは数値表示には `ui-monospace, "SF Mono", Consolas, monospace` を使用しなければならない（MUST）
- **コントラスト（通常テキスト）**: WCAG 2.1 AA 準拠として、テキストと背景のコントラスト比が 4.5:1 以上でなければならない（MUST）
- **コントラスト（大型テキスト、18pt 以上または 14pt 以上の太字）**: コントラスト比が 3:1 以上でなければならない（MUST）
- **フォーカス可視化**: フォーカス可能な要素はすべて `:focus-visible` 疑似クラスで outline 2px 以上かつコントラスト比 3:1 以上の outline を表示しなければならない（MUST）
- **セマンティック HTML**: `<main>` / `<nav>` / `<section>` / `<article>` タグを適切な箇所で使用しなければならない（MUST）。Wave 5 で指摘された `landmark-one-main` Lighthouse 警告を解消しなければならない（MUST）
- **ARIA**: ソートボタンには `aria-label` を付与しなければならない（MUST）。ソート状態の列ヘッダには `aria-sort` 属性を付与しなければならない（MUST）。フィルタ適用後の結果件数表示には `aria-live` 属性を付与しなければならない（MUST）
- **キーボード操作**: テーブルソートボタンはキーボードの Tab キーで移動でき、Enter または Space キーで動作しなければならない（MUST）

> **upstream-first ステータス（`aria-sort`）**: `aria-sort` の有効な属性値（ascending / descending / none / other）は
> WAI-ARIA 仕様（https://www.w3.org/TR/wai-aria/#aria-sort）で定義されており、
> 一般に確立した API であるため裏取り済みとみなす。
> ただし具体的な実装パターンは design.md で明確化すること。

> **upstream-first ステータス（`:focus-visible`）**: CSS `:focus-visible` 疑似クラスは
> Chrome 86+ / Edge 86+ 以降でサポート（NFR-3 Chrome 120+ / Edge 120+ 要件と整合）。
> 書式は MDN（https://developer.mozilla.org/ja/docs/Web/CSS/:focus-visible）で確認済みとみなす。

### FR-W6-4: テーブルソート（MUST）

V-4 Task 一覧テーブルは以下のソート要件を満たさなければならない:

- 列ヘッダをクリックすることで当該列の昇順ソートを実行しなければならない（MUST）
- 同一列ヘッダを再クリックすることで降順ソートに切り替えなければならない（MUST）
- ソート実装は Vanilla JS で inline 記述し、`Array.from(tbody.rows).sort()` を用いた DOM 再挿入方式を採用しなければならない（MUST）（FR-5・NFR-5 と整合）
- ソート対象列は Task ID / 担当（AI 種別）/ 状態 の 3 列とする（MUST）

> **v0.2.0 修正履歴（C-NEW-1 対応 / 2026-06-25）**: v0.1.0 では「Task ID / 担当 / 状態 / 完了判定」の 4 列としていたが、既存 `_render_v4_tasks()` 実装（`builder.py:273-318`）が「Task ID / 担当 / 状態」の 3 列構成であり、「完了判定」は独立列ではなく状態列バッジ内の `data-status` 属性として埋め込まれていることが design.md v0.2.0 §9 起草時に判明した。design.md v0.2.0 §9 で 3 列構成を維持する方針が確定し、本要件もこれに整合させた。状態列ソートは `STATUS_ORDER = {not-started:0, in-progress:1, blocked:2, completed:3}` の固定順序で代替し、業務的進捗順序を維持する（完了判定の独立列を追加するスコープは Wave 7+ 候補）。
- ソート用 JS のサイズは全機能合計（ソート + フィルタ）で 100 行以上 150 行以下でなければならない（SHOULD）

> **upstream-first ステータス（HTMLTableElement.rows）**: `HTMLTableElement.rows` プロパティは
> MDN（https://developer.mozilla.org/ja/docs/Web/API/HTMLTableElement/rows）に記載された
> 確立した Web API であるため裏取り済みとみなす。

### FR-W6-5: テーブルフィルタ（MUST）

V-4 Task 一覧テーブルは以下のフィルタ要件を満たさなければならない:

- **状態値フィルタ**: FR-2 で定義する 4 状態値（not-started / in-progress / blocked / completed）でテーブル行を絞り込めなければならない（MUST）
- **Milestone フィルタ**: 表示中の Milestone 名でテーブル行を絞り込めなければならない（MUST）
- **テキスト検索フィルタ**: テキスト入力による部分一致検索で Task ID または担当列の行を絞り込めなければならない（MUST）
- フィルタの適用は `row.style.display` の切替で実現しなければならない（MUST）（Vanilla JS inline、外部ライブラリ禁止）
- フィルタ適用後、一致した行数を `aria-live` 属性付きの要素に表示しなければならない（MUST）（FR-W6-3 と連動）
- フィルタをリセットする手段を提供しなければならない（MUST）（全行を再表示する「クリア」操作）
- 複数フィルタの AND 条件結合をサポートしなければならない（MUST）

---

## §5 非機能要件（NFR）

> **継承宣言**: 既存 NFR-1〜NFR-6（PoC 仕様 v0.2.0）は Wave 6 でも全て維持する（§7 参照）。
> 本節は Wave 6 で**新規追加・変更**する NFR のみを定義する。

### NFR-W6-1: Lighthouse Accessibility スコア（MUST）

Wave 6 完了後の dashboard.html を Chrome で測定した Lighthouse Accessibility スコアは 95 以上でなければならない（MUST）。

> 現状: 89（Wave 5 PoC 完了時点）。Wave 5 で発覚した `color-contrast` および `landmark-one-main` 警告の解消が前提条件。

### NFR-W6-2: ダークモード切替の視覚的完全性（MUST）

OS のカラーテーマ設定をライトとダークで切り替えた場合、ダッシュボード全体（V-1〜V-4 のすべてのテキスト・背景・ボーダー・状態バッジ）が対応する CSS カスタムプロパティに従って切替わらなければならない（MUST）。一部の要素が切替わらない状態があってはならない（MUST NOT）。

### NFR-W6-3: 追加 CSS サイズ上限（MUST）

Wave 6 で追加する CSS（Radix Colors カスタムプロパティ転記分 + レイアウト / タイポグラフィ / ソート / フィルタ UI スタイル）の合計サイズは 10 KB 以下でなければならない（MUST）。既存 NFR-1（HTML 全体 500 KB 未満）の制約下においてこれを達成すること。

> 参考: Wave 5 完了時点の HTML サイズは 130 KB。追加 CSS 10 KB でも 140 KB 以下に収まり NFR-1 の余裕は十分。

---

## §6 アクセプタンス条件（AC）

> **継承宣言**: 既存 AC-1〜AC-8（PoC 仕様 v0.2.0）は Wave 6 でも全て維持する（§7 参照）。
> 本節は Wave 6 で**新規追加**する AC のみを定義する。

| ID | 条件 | 対応 FR/NFR |
|----|------|-------------|
| AC-W6-1 | ライトモードとダークモードで全テキストのコントラスト比が 4.5:1 以上（大型テキストは 3:1 以上）であること（手動または自動ツールで確認） | FR-W6-3 / NFR-W6-1 |
| AC-W6-2 | Chrome で Lighthouse Accessibility を実行し、スコアが 95 以上であること | NFR-W6-1 |
| AC-W6-3 | `@media (prefers-color-scheme: dark)` を DevTools でエミュレートし、全 V-1〜V-4 の配色が切替わること | FR-W6-1 / NFR-W6-2 |
| AC-W6-4 | V-4 テーブルのいずれかの列ヘッダをクリックした後、当該列で昇順・再クリックで降順に並び替えられること | FR-W6-4 |
| AC-W6-5 | V-4 テーブルで状態値・Milestone・テキスト検索の各フィルタを適用した後、条件に一致しない行が非表示になること | FR-W6-5 |
| AC-W6-6 | V-4 テーブルで複数フィルタを同時に適用した場合に AND 条件で絞り込まれること | FR-W6-5 |
| AC-W6-7 | フィルタ適用後に一致件数が画面上に表示され、スクリーンリーダーで読み上げ可能な `aria-live` 領域として実装されていること | FR-W6-5 / FR-W6-3 |
| AC-W6-8 | Wave 6 完了後の HTML サイズが 500 KB 未満（NFR-1 維持）かつ追加 CSS が 10 KB 以下（NFR-W6-3）であること | NFR-1 / NFR-W6-3 |
| AC-W6-9 | ソートおよびフィルタ操作がネットワーク接続なしのオフライン環境（ブラウザのオフラインモード）で動作すること | FR-5 |
| AC-W6-10 | Wave 6 で追加した JS（ソート + フィルタ）のコード行数が 100〜150 行（コメント・空行除く）であること（SHOULD 検証） | FR-W6-4 / FR-W6-5 |
| AC-W6-11 | ユーザー主観評価「ダッシュボードが使いやすい」を Wave 6 完了 PoC レビューで OK が出ること | §2 Goals ①  |

---

## §7 既存仕様からの継承・差分

### 継承（変更なし）

以下は PoC 仕様（requirements.md v0.2.0）から全て継承し、Wave 6 で変更・上書きしない。

| 区分 | 対象 | 継承内容の要約 |
|------|------|--------------|
| FR（継承） | FR-1 | V-1〜V-4 ビュー構成・表示必須情報（構造は維持し、Wave 6 でスタイルを追加する） |
| FR（継承） | FR-2 | 状態値 4 値（not-started / in-progress / blocked / completed）の定義 |
| FR（継承） | FR-3 | V-1→V-4 のナビゲーション・ドリルダウン（SHOULD） |
| FR（継承） | FR-4 | データソース（SESSION_STATE.md / current-phase.md / tasks.md / git log）の固定 |
| FR（継承） | FR-5 | オフライン動作・外部 CDN 禁止（MUST NOT）— Wave 6 の Radix Colors 手動転記もこれに準拠 |
| FR（継承） | FR-6 | ファイル読み込みエラー時の部分表示継続 |
| FR（継承） | FR-7 | 単一 HTML ファイル出力 |
| FR（継承） | FR-8 | 出力先 `docs/artifacts/dashboard/` |
| FR（継承） | FR-9a/b | ビルドコマンド（SHOULD）・実行環境（Windows 11 / Git Bash / Python 3.x） |
| FR（継承） | FR-10 | `/build-dashboard` スキル（SHOULD） |
| FR（継承） | FR-11 | `/quick-save` 連動（SHOULD） |
| NFR（継承） | NFR-1 | HTML ファイル 500 KB 未満 |
| NFR（継承） | NFR-2 | ブラウザ表示完了 3 秒以内 |
| NFR（継承） | NFR-3 | Chrome 120+ / Edge 120+ 対応 |
| NFR（継承） | NFR-4 | スクリプト実行から HTML 生成完了まで 30 秒以内 |
| NFR（継承） | NFR-5 | 生成スクリプトは Python 3.x 標準ライブラリのみ（または pyproject.toml 管理） |
| NFR（継承） | NFR-6 | 全データソース欠如でもエラー終了しない |
| AC（継承） | AC-1〜AC-8 | Wave 5 PoC 受け入れ条件（全 PASS 維持） |

### 差分（Wave 6 追加）

| 区分 | ID | 内容の概要 |
|------|----|-----------|
| FR（追加） | FR-W6-1 | CSS 基盤・カスタムプロパティ・ライト/ダーク 2 セット |
| FR（追加） | FR-W6-2 | Radix Colors パレット手動転記適用 |
| FR（追加） | FR-W6-3 | アクセシビリティ基盤（フォント / コントラスト / フォーカス / セマンティック / ARIA） |
| FR（追加） | FR-W6-4 | テーブルソート（Vanilla JS inline） |
| FR（追加） | FR-W6-5 | テーブルフィルタ（状態値・Milestone・テキスト検索 / AND 結合） |
| NFR（追加） | NFR-W6-1 | Lighthouse Accessibility ≥ 95 |
| NFR（追加） | NFR-W6-2 | ダークモード切替の視覚的完全性 |
| NFR（追加） | NFR-W6-3 | 追加 CSS サイズ ≤ 10 KB |
| AC（追加） | AC-W6-1〜AC-W6-11 | Wave 6 固有の受け入れ条件 |

### 上書き（変更あり）

なし。既存 FR / NFR / AC の削除・変更は行わない。Wave 6 は追加のみである。

---

## §8 Wave 6 内部 Stage 分割（情報）

Wave 6 は以下の 4 Stage に内部分割して進める（clarify-2026-06-24.md §7 確定）。
各 Stage 末に軽量レビュー（内部ゲート）を実施し、Stage 4 末に本格 PoC レビューを行う。

| Stage | 内容 | 推定工数 | 主要 FR/NFR 対応 |
|-------|------|:--------:|-----------------|
| Stage 1 | CSS 基盤 + Radix Colors 適用 + カスタムプロパティ + ライト/ダーク対応 | 1〜2 セッション | FR-W6-1 / FR-W6-2 / FR-W6-3 / NFR-W6-2 / NFR-W6-3 |
| Stage 2 | テーブルソート（Vanilla JS inline） | 1 セッション | FR-W6-4 / AC-W6-4 / AC-W6-10 |
| Stage 3 | フィルタリング（状態値・Milestone・テキスト検索 / AND 結合） | 1 セッション | FR-W6-5 / AC-W6-5〜AC-W6-7 |
| Stage 4 | Lighthouse 95+ 達成検証 + 統合テスト + PoC レビュー | 1 セッション | NFR-W6-1 / AC-W6-1〜AC-W6-3 / AC-W6-8〜AC-W6-11 |

総推定: 3〜5 セッション。

### Stage ゲート条件（各 Stage 末の確認事項）

- **Stage 1 ゲート**: ライト/ダーク切替が DevTools でエミュレート確認できること / 追加 CSS ≤ 10 KB（NFR-W6-3 中間確認）
- **Stage 2 ゲート**: V-4 テーブルの全ソート対象列で昇順・降順動作確認（AC-W6-4）
- **Stage 3 ゲート**: 全フィルタ種別（状態値・Milestone・テキスト）と AND 結合の動作確認（AC-W6-5〜AC-W6-7）
- **Stage 4 ゲート**: Lighthouse Accessibility ≥ 95（AC-W6-2）/ HTML ≤ 500 KB / ユーザー PoC レビュー OK（AC-W6-11）

---

## §9 将来候補（Wave 7+ への送り）

以下は Wave 6 で対応しない項目として、`docs/specs/b4-dashboard/future-candidates.md` に継続記録する。

| FC ID | 内容 | 理由 |
|-------|------|------|
| FC-5（完了） | 配色・UI スタイリングの確定 | Wave 6 で対応完了予定 |
| FC-7 | 複数 Milestone 同時進行時の Step 表示方針（Milestone 別 Phase 管理） | 採用トリガー未達成（2 Milestone 並列が常態化していない）。Wave 7+ で再評価 |
| ※新候補 | 完全レスポンシブ対応（スマホ表示最適化） | Wave 6 では PC 専用を維持。実需確認後に Wave 7+ で検討 |
| ※新候補 | Task のジャンル分け・グルーピング表示 | 情報構造の再設計が必要。clarify Q1 で Wave 6 スコープ外と確定 |
| ※新候補 | Wave / Milestone 一覧の充実（複数 Milestone 横断表示） | FC-7 と連動するため FC-7 着手後に再評価 |

---

## §10 PM 確定回答記録

### 2026-06-24: requirements.md v0.1.0 承認

- **承認者**: ユーザー（PM 級）
- **承認日時**: 2026-06-24
- **承認文言**: 「おおよそ読んだ。今のところAでいいと思う。なんかあったらまた話し合おう。」
- **承認時のステータス**: Draft → **Approved**
- **L1 観察事項**（design.md で対応予定 / PM 級ではない）:
  1. AC-W6-10「JS 行数 100〜150 行（SHOULD）」: 150 行超過時の扱いを design.md で明文化
  2. §11 upstream-first 未確認の 2 項目（Radix Colors CSS 変数名書式・ライト/ダーク命名規則）: design.md 起草前に WebSearch / context7 で裏取り必須
  3. §9 「FC-5（完了）」表記: Wave 6 完了時に future-candidates.md 更新で確定扱いとする（現時点は「Wave 6 で対応中」と読む）

### 2026-06-25: requirements.md v0.2.0 整合修正（C-NEW-1）

- **修正者**: L1（ユーザー指示「抽出されたもの、全件対象」による自動進行）
- **修正日時**: 2026-06-25
- **修正種別**: PM 級（仕様変更）/ ユーザー承認は事後に求める
- **修正内容**: FR-W6-4 のソート対象列を「Task ID / 担当 / 状態 / 完了判定」（4 列）→「Task ID / 担当 / 状態」（3 列）に縮小
- **修正根拠**: 既存実装（`builder.py:273-318`）は 3 列構成。「完了判定」は独立列ではなく状態列バッジの `data-status` 属性。design.md v0.2.0 §9 で 3 列方針が一次情報に基づいて確定済み。v0.1.0 FR-W6-4 の 4 列前提は実装根拠を欠いた誤前提であった
- **代替手段**: 状態列ソートに `STATUS_ORDER` 固定順序を導入し業務的進捗順序を維持
- **影響範囲**: FR-W6-4 / AC-W6-4 は文言調整のみ（受入条件は実質維持）/ NFR / 他 AC への波及なし
- **再承認**: 次の design.md v0.3.0 承認時にユーザーが本修正を併せて承認する想定

### 2026-06-25: requirements.md v0.2.0 + design.md v0.3.0 同時承認

- **承認者**: ユーザー（PM 級）
- **承認日時**: 2026-06-25
- **承認文言**: 「Aでお願いします」（spec-critic 第 2 回レビュー結果を全件反映した v0.3.0 / requirements.md v0.2.0 を承認）
- **承認対象**: requirements.md v0.2.0 整合修正 + design.md v0.3.0 全 15 件修正
- **次フェーズ**: Wave 6 PLANNING Stage 3 = tasks.md v0.1.0 起草（task-decomposer 委譲予定）

---

## §11 upstream-first 裏取りステータス

本要件定義書内で使用する Web API・CSS プロパティ・ARIA 属性の裏取りステータス。

| 項目 | ステータス | 備考 |
|------|-----------|------|
| `@media (prefers-color-scheme: dark)` | 裏取り済 | MDN 掲載・Chrome 76+ / Edge 79+ サポート（NFR-3 と整合） |
| `:focus-visible` | 裏取り済 | MDN 掲載・Chrome 86+ / Edge 86+ サポート（NFR-3 と整合） |
| `aria-sort` 属性値（ascending / descending / none / other） | 裏取り済 | WAI-ARIA 1.1 仕様に記載 |
| `aria-live` 属性 | 裏取り済 | WAI-ARIA 仕様に記載・スクリーンリーダー対応標準 |
| `aria-label` 属性 | 裏取り済 | WAI-ARIA 仕様に記載 |
| `HTMLTableElement.rows` | 裏取り済 | MDN 掲載（clarify §4 Q6 でも参照） |
| Radix Colors CSS 変数名の正確な書式（`--gray-1` 等） | **未確認（要裏取り）** | design.md 起草時に公式サイト（https://www.radix-ui.com/colors）で確認すること |
| Radix Colors のライト/ダーク変数名の命名規則 | **未確認（要裏取り）** | 同上。step 番号の付番形式・ダーク用接尾辞の有無等を確認すること |

---

## §12 Definition of Ready チェックリスト

- [x] Problem Statement が明確（§1）
- [x] Goals / Non-Goals が明記されている（§2 / §3）
- [x] 全機能要件に RFC 2119 キーワードが付与されている（§4）
- [x] Requirements Smells（曖昧形容詞・計測不能用語）が排除されている
- [x] Wave 6 固有の FR / NFR / AC が FR-W6-X / NFR-W6-X / AC-W6-X 形式で採番されている
- [x] 既存 v0.2.0 仕様からの継承・差分・上書きが明示されている（§7）
- [x] 数値基準が明示されている（Lighthouse 95+ / コントラスト 4.5:1 / CSS ≤ 10 KB 等）
- [x] upstream-first 裏取りステータスが明示されている（§11）
- [x] Wave 6 内部 Stage 分割が情報として記載されている（§8）
- [x] 将来候補が明示されている（§9）
- [ ] タスク分解（1 PR / Task 単位への分割）→ tasks.md フェーズで対応

---

## §13 権限等級

本ファイルの変更: **PM 級**（仕様書変更 / `docs/specs/` 配下）

---

## §14 参照

- `docs/specs/b4-dashboard/requirements.md` v0.2.0（PoC 仕様・継承元 SSOT）
- `docs/specs/b4-dashboard/wave6/clarify-2026-06-24.md`（PLANNING インタビュー記録・最優先）
- `docs/artifacts/b4-dashboard-poc-review.md`（Wave 5 PoC レビュー・要望起点）
- `docs/specs/b4-dashboard/design.md` v0.1.0（PoC 設計書・参照）
- `docs/specs/b4-dashboard/future-candidates.md`（FC-5 / FC-7 継続記録）
- `.claude/rules/planning-quality-guideline.md`（Requirements Smells / RFC 2119 / SPIDR / WBS 100% Rule）
- `.claude/rules/terminology.md`（Wave / Stage / Task 用語階層）
- https://www.radix-ui.com/colors（Radix Colors 公式 / CSS 変数名裏取り先）
- https://www.w3.org/TR/wai-aria/#aria-sort（WAI-ARIA aria-sort 仕様）
- https://developer.mozilla.org/ja/docs/Web/CSS/@media/prefers-color-scheme（MDN prefers-color-scheme）

---

## §15 改訂履歴

| バージョン | 日付 | 変更概要 |
|-----------|------|---------|
| 0.1.0 | 2026-06-24 | 初版 Draft（clarify-2026-06-24.md の PLANNING インタビュー結果を全反映） |
| 0.2.0 | 2026-06-25 | C-NEW-1 対応: FR-W6-4 のソート対象列を 4 列 → 3 列に縮小（既存 V-4 実装との整合 / 「完了判定」は状態列 `data-status` で代替）。詳細は §10 「2026-06-25: v0.2.0 整合修正」を参照 |
