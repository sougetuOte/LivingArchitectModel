# b4-dashboard Wave 9 — requirements.md

- バージョン: 0.2.3
- 作成日: 2026-06-28
- ステータス: Draft（PM 承認待ち）
- マイルストーン: B-5（Wave 9 / V-4 description 列追加）
- 関連:
  - `docs/specs/b4-dashboard/requirements.md` v0.2.0（PoC 仕様 / 継承元）
  - `docs/specs/b4-dashboard/design.md` v0.2.3（元設計書 / Wave 9 §Non-Goals・§4・§5・§8・§13 更新済み）
  - `docs/specs/b4-dashboard/wave8/requirements.md` v0.2.3（直近 Wave / FR-W8-1〜N2 継承元）
  - `docs/artifacts/retro-W7-B5-2026-06-28.md`（Wave 7 retro / Problem #10 + A10 高優先）
  - 起源 chip: `task_5de9563e`（V-4 description 列なし / Wave 7 PoC レビュー指摘）

---

## §1 概要 / Problem Statement

### 起源

chip `task_5de9563e` は Wave 7 PoC レビュー（2026-06-28）で起票された。
Wave 7 retro Problem #10「PoC レビュー前段階チェックリスト未整備」に関連し、
V-4 Task 一覧ビューで各 Task の description（説明文）が表示されないため
「何のタスクか Task ID だけでは判断できない」という一覧性の問題が根本原因である。

Wave 7 retro Action A10（高優先）にて「V-4 description 列 chip (task_5de9563e) を
Wave 8 PLANNING に取込」と記録されたが、Wave 8 は chip task_68008f88（Milestone フィルタ）
の解決に専念したため Wave 9 として対応する（2026-06-28 L1 MAGI 合議確定）。

### 問題の核心

| 問題 | 現状 | 影響 |
|:-----|:-----|:----|
| **V-4 description 列の欠如** | V-4 は Task ID / 担当 / 状態の 3 列のみ。description が表示されない | Task ID（例: W7-B5-T44）だけでは内容が不明。一覧で「何のタスクか」が判断できない |
| **TaskInfo.description フィールド未定義** | `models.py` の `TaskInfo` に description フィールドが存在しない | parser 側で既に `raw_description` を取得しているが `TaskInfo` に渡していない |
| **TasksParser で description_clean が捨てられている** | `_extract_assignee(raw_description)` の第 1 戻り値（description_clean）が使用されず破棄されている | parser ロジックを追加せずに 1 行変更で解決可能 |

### 設計観点の追加問題

| 問題 | 設計上の影響 |
|------|------------|
| 長い description がレイアウトを崩す可能性 | `max-width` + `text-overflow: ellipsis` による省略表示 CSS が必要 |
| description のソート追加によるアクセシビリティ負担増 | description ソートは意味が薄くソートボタン数増加が a11y 負担になる → ソート不可設計 |

---

## §2 Goals / Non-Goals

### Goals

| Goal | 指標 | 達成判定 |
|:-----|:-----|:--------|
| G1: V-4 description 列の追加 | V-4 の 2 列目（Task ID 右隣）に description 列が表示される | dashboard.html の V-4 テーブルに description 列が確認できる（AC-W9-1）|
| G2: TaskInfo.description フィールド追加 | `models.py` に `description: str = ""` が追加される | フィールドが存在し、assignee 除去後の本文値を保持する（AC-W9-2）|
| G3: TasksParser から description を TaskInfo に渡す | `parsers/tasks.py` で description_clean を TaskInfo に渡す 1 行追加 | parser ロジック追加ゼロで実現（AC-W9-2 / wave9/design.md §5）|
| G4: Wave 8 達成値の退行防止 | pytest 全件 PASS / Lighthouse Accessibility ≥ 95 / CSS ≤ 16,384 bytes | Stage 末の全件確認で達成（AC-W9-6 / AC-W9-7）|

### Non-Goals（明示的に Wave 9 で対応しないこと）

- **description キーワードフィルタ**: V-4 の既存テキスト検索（filter-text）を description まで拡張する機能は Wave 9 のスコープ外。将来候補として記録。
- **詳細表示モーダル**: description を全文表示するポップアップ・モーダルは Wave 9 のスコープ外。`title` 属性 tooltip のみで代替。
- **description の多行折り返し**: 省略表示（ellipsis）のみとし、多行折り返しモードは実装しない。
- **description ソート機能**: description 列にソートボタンは設けない（MAGI 合議 2026-06-28 B2 確定）。
- **V-4 CSS 意匠変更**: `.description-cell` 追加以外の CSS 意匠変更（配色テーマ・レイアウト）は Wave 9 スコープ外。
- **既存 4 パーサ内部ロジックの改修**: Wave 9 の TasksParser 変更は「1 行追加（description フィールドへの渡し）」のみ。parser ロジック（抽出・分岐・regex）の追加はゼロ。
- **他 Wave のテスト・仕様変更**: Wave 9 に関係しない既存テストの修正は行わない。

---

## §3 機能要件（FR）

### FR-W9-1: V-4 の 2 列目に description 列を表示（MUST）

V-4 Task 一覧ビューの **2 列目**（Task ID の右隣）に description 列を表示しなければならない（MUST）。

**MUST 項目**:
- `<thead>` の 2 列目に `<th id="th-description">description</th>` を配置する（MUST）
- `<tbody>` の各行の 2 列目に `<td class="description-cell" title="{full_description}">{display_description}</td>` を配置する（MUST）
- `{full_description}` および `{display_description}` は `html.escape()` で XSS 対策を施した値を使用する（MUST）
- description が空文字列の場合は `<td class="description-cell" title=""></td>`（空セル）を描画し HTML が崩れないこと（MUST / AC-W9-3）

**根拠**: chip `task_5de9563e` — Task ID だけでは内容不明。一覧性最大化のため Task ID の右隣に配置。

### FR-W9-2: `TaskInfo` に description フィールドを追加（MUST）

`models.py` の `TaskInfo` データクラスに `description: str = ""` フィールドを追加しなければならない（MUST）。

**MUST 項目**:
- `description: str = ""` を `TaskInfo` のフィールドとして追加する（MUST）
- 既定値は `""` とし、assignee フィールドの既定値 `"-"` と同じパターンで後方互換を確保する（MUST）
- 既存フィールド（`id` / `milestone` / `status` / `assignee`）の定義・順序は変更しない（MUST NOT modify）

### FR-W9-3: TasksParser が description を TaskInfo に渡す（MUST）

`parsers/tasks.py` の `_extract_tasks()` 内で、`_extract_assignee(raw_description)` の
戻り値第 1 要素（`description_clean`）を `TaskInfo.description` に渡さなければならない（MUST）。

**MUST 項目**:
- `_, assignee = _extract_assignee(raw_description)` を `description_clean, assignee = _extract_assignee(raw_description)` に変更する（MUST）
- `TaskInfo(...)` 生成時に `description=description_clean` を追加する（MUST）
- それ以外の parser ロジック（抽出・分岐・regex・ファイル走査）は変更しない（MUST NOT modify）
- parser ロジック追加ゼロで実現する（既存 `raw_description` の活用）

**根拠**: `_extract_assignee()` は既に `(clean_description, assignee)` のタプルを返しており、
第 1 要素が捨てられていた。1 行変更で description が利用可能になる。

### FR-W9-4: description 列はソート不可（MUST NOT）

description 列のヘッダ（`<th id="th-description">`）にソートボタン（`sort-btn`）を設けてはならない（MUST NOT）。

**MUST NOT 項目**:
- `<th id="th-description">` 内に `<button class="sort-btn">` を含めてはならない（MUST NOT）
- `<th id="th-description">` に `aria-sort` 属性を付与してはならない（MUST NOT）

**根拠**: アルファベット順の description ソートは意味が薄い。ソートボタン数の増加は
a11y 負担になる（MAGI 合議 2026-06-28 B2 確定）。

### FR-W9-5: description 列は省略表示と tooltip を提供（SHOULD）

description 列のセルは以下の表示仕様に従うことが望ましい（SHOULD）:

- CSS `max-width` + `text-overflow: ellipsis` + `white-space: nowrap` で長い description を省略表示する（SHOULD）
- `title` 属性に full description を設定し、ホバー時に tooltip で全文を確認できるようにする（SHOULD）
- `max-width` の値は BUILDING フェーズで実測後に確定する（MAY / 暫定 300px）

---

## §4 非機能要件（NFR）

### NFR-W9-1: パフォーマンス — 元 NFR-4 30 秒以内維持（MUST）

元要件 NFR-4（ダッシュボード生成 30 秒以内）を維持しなければならない（MUST）。
Wave 9 の description 追加は Python 文字列操作のみであり、NFR-4 への実質的影響はゼロとみなす。

### NFR-W9-2: 後方互換 — 既存テスト影響最小化（MUST）

Wave 8 終端時点の pytest（398 + Wave 8 追加分）を維持し、Wave 9 追加分も含めて全件 PASS を維持しなければならない（MUST）。

**MUST 項目**:
- 既存テストの退行ゼロ（MUST）
- `TaskInfo` の `description` フィールド追加による既存テストへの影響は、既定値 `""` により最小化する（MUST）
- 既存テストの緩和は L1 事前承認必須

### NFR-W9-3: CSS 予算（SHOULD）

Wave 9 実装による CSS 増分は 300 bytes 以内とすることが望ましい（SHOULD）。

**根拠**:
- Wave 7 終端 CSS: 10,400 bytes / NFR-W7-1 v0.2.4 上限: 16,384 bytes / 残: 5,984 bytes
- `.description-cell` の最小 CSS（約 3-4 プロパティ）は 100-200 bytes 程度と見積もる
- Wave 9 追加後の推定: 10,500〜10,600 bytes（残 5,784〜5,884 bytes / 緑帯 < 70% 維持見込み）

### NFR-W9-4: Lighthouse Accessibility 維持（MUST）

Wave 8 達成値（Accessibility ≥ 95）を Wave 9 終端でも維持しなければならない（MUST）。

**根拠**: `<th id="th-description">` ヘッダに `aria-sort` がなく `sort-btn` もないことで
Lighthouse が Accessibility を正しく計測できるか BUILDING で確認する（UQ-13 参照）。

---

## §5 受け入れ条件（AC）

### AC-W9-1: V-4 HTML 出力の description 列位置確認（FR-W9-1 対応 / MUST）

生成された dashboard.html の V-4 テーブルで description 列が Task ID の右隣（2 列目）に配置されている。

**検証方法**:
- `<thead>` の 2 番目の `<th>` が `<th id="th-description">` であること
- `<tbody>` の各行の 2 番目の `<td>` が `class="description-cell"` を持つこと

### AC-W9-2: TaskInfo.description が正しい値を保持（FR-W9-2 / FR-W9-3 対応 / MUST）

TasksParser が tasks.md を解析した結果の `TaskInfo.description` が、
Task ID および assignee タグを除去した本文値を保持する。

**検証シナリオ**:

| tasks.md 行 | 期待される `TaskInfo.description` |
|:-----------|:-------------------------------|
| `- [x] W1-B5-T1: BaseParser 実装完了` | `"BaseParser 実装完了"` |
| `- [ ] W7-B5-T50: 担当列実装 @Sonnet` | `"担当列実装"` |
| `- [x] W7-B5-T51: 採点 @Haiku` | `"採点"` |
| `- [ ] W9-B5-T60: description 列追加` | `"description 列追加"` |
| `- [ ] T99: 単発タスク` | `"単発タスク"` |

### AC-W9-3: 空の description でも HTML が崩れない（FR-W9-1 対応 / MUST）

`TaskInfo.description` が空文字列 `""` の場合、V-4 の対応行に空の `<td class="description-cell" title=""></td>` が描画され、テーブルレイアウトが崩れない。

### AC-W9-4: description 列ヘッダに sort-btn が存在しない（FR-W9-4 対応 / MUST）

生成された dashboard.html の `<th id="th-description">` 内に `<button class="sort-btn">` が存在しないこと、および `aria-sort` 属性が付与されていないこと。

**検証方法**:
- grep: `th-description` を含む `<th>` タグ内に `sort-btn` が存在しないこと
- grep: `th-description` を含む `<th>` タグに `aria-sort` 属性がないこと
- 既存ソート JS の動作確認: description 列の存在が JS エラーを引き起こさないこと（UQ-13）

### AC-W9-5: description の省略表示と tooltip（FR-W9-5 対応 / SHOULD）

長い description を持つ Task の description セルで省略表示（`...`）が行われ、
ホバー時に `title` 属性 tooltip で全文が確認できる（CSS による / BUILDING で実測確認）。

### AC-W9-6: pytest 全件 PASS（NFR-W9-2 対応 / MUST）

Wave 9 終端で pytest 全件 PASS（既存 + Wave 8 追加 + Wave 9 追加分）。

### AC-W9-7: Lighthouse Accessibility ≥ 95（NFR-W9-4 対応 / MUST）

Wave 9 終端で Lighthouse 計測し、Accessibility スコアが 95 以上である。

---

## §6 Non-Goals 詳細

### description キーワードフィルタとの関係

Wave 9 は display のみ。filter-text（既存）の検索対象は Task ID・担当のまま変更しない。
description をフィルタ対象に追加する場合は別 Wave（PM 判断）で実施。

### ソート設計との関係

description ソートは「アルファベット順で意味のある順序が得られない」ことと
「ソートボタン数増加が a11y 負担」の 2 理由から除外（MAGI 合議 2026-06-28 B2）。
将来、description フォーマットが機械的にソートできる形式に整理された時点で再検討候補。

### Wave 8 FR-W8-4 との関係

Wave 8 FR-W8-4「既存 4 パーサの無改変 MUST NOT」は Wave 8 スコープ内での宣言である。
Wave 9 は別仕様書の別 FR を持ち、TasksParser の改修（1 行追加）は Wave 9 スコープで
明示的に許可される（FR-W9-3 MUST）。ただし改修は「description を TaskInfo に渡す 1 行追加のみ」
であり、parser ロジックの追加はゼロとする。

---

## §7 解決済み質問（MAGI 合議 2026-06-28）

| # | 質問（B番号） | 回答 |
|:--|:------------|:----|
| B1 | description 列の位置 | V-4 の 2 列目（Task ID 右隣）。タスク内容を Task ID の隣に配置 → 一覧性最大化 / PoC「何のタスクか分からない」根本対応 |
| B2 | description 列のソート可否 | ソート不可（MUST NOT）。アルファベット順 description は意味薄い + ソート UI 数増加で a11y 負担 |
| B3 | TaskInfo / TasksParser 改修方針 | `models.py` に `description: str = ""` フィールド追加 / TasksParser L138-163 で既に `raw_description` を取得済み → `TaskInfo(...)` 生成時に `description=description_clean` を渡す 1 行追加のみ。parser ロジック追加ゼロ（既存処理活用） |

---

## §8 将来候補

以下は本スコープから除外し、将来の Wave で検討する事項:

| 内容 | 採用トリガ |
|:----|:---------|
| description キーワードフィルタ（filter-text の対象拡張） | ユーザーから検索用途の需要が出た時点 |
| 詳細表示モーダル（description 全文表示） | 長大な description を持つ Task が増加し tooltip では不十分になった時点 |
| description の多行折り返しモード | 省略表示のみでは情報損失が大きいと判断された時点 |
| description ソート機能 | description が機械的にソート可能な形式に整理された時点 |

---

## §9 Example Mapping（主要 FR に対する具体例）

### FR-W9-2 / FR-W9-3: description の抽出と格納

**ルール**: `_extract_assignee(raw_description)` の第 1 要素を `TaskInfo.description` に格納する。

| 具体例 | tasks.md 行 | `raw_description` | `description_clean` | `assignee` |
|:------|:-----------|:-----------------|:-------------------|:-----------|
| assignee あり | `- [ ] W7-B5-T50: 担当列実装 @Sonnet` | `"担当列実装 @Sonnet"` | `"担当列実装"` | `"Sonnet"` |
| assignee なし | `- [x] W1-B5-T1: BaseParser 実装完了` | `"BaseParser 実装完了"` | `"BaseParser 実装完了"` | `"-"` |
| description が実質空 | `- [ ] T99: @Haiku` | `"@Haiku"` | `""` | `"Haiku"` |

**未解決質問（Red）**: なし（MAGI 合議 B1/B2/B3 ですべて確定済み）

### FR-W9-1: V-4 HTML 構造

**ルール**: description 列は 2 列目 / ソートボタンなし / description_clean を表示 / full text を title 属性で提供。

| 具体例 | 入力 `TaskInfo` | 期待される `<td>` |
|:------|:--------------|:----------------|
| 通常 description | `description="BaseParser 実装完了"` | `<td class="description-cell" title="BaseParser 実装完了">BaseParser 実装完了</td>` |
| 空 description | `description=""` | `<td class="description-cell" title=""></td>` |
| XSS 対策 | `description="<script>alert(1)</script>"` | `<td class="description-cell" title="&lt;script&gt;alert(1)&lt;/script&gt;">&lt;script&gt;alert(1)&lt;/script&gt;</td>` |

---

## §10 改訂履歴

| バージョン | 日付 | 変更内容 |
|:----------|:-----|:--------|
| 0.2.3 | 2026-06-28 | 初版起稿 — MAGI 合議（2026-06-28）B1/B2/B3 に基づく FR/NFR/AC 定義。chip task_5de9563e 対応。FR-W9-1〜5 / NFR-W9-1〜4 / AC-W9-1〜7 / Example Mapping §9 |

---

## §11 権限等級

- 本要件書の変更: **PM 級**（仕様変更）
- AC 追加・修正: **PM 級**
- 表記の微調整・typo 修正: **PG 級**

---

## §12 upstream-first 裏取りステータス

| 対象 | 実在性確認 | LAM 適合性 | 備考 |
|:-----|:----------|:----------|:----|
| Python `str.strip()` / `str.__getitem__` | ✅（Python 標準） | ✅ | 既存実装で同種操作を使用中 |
| `@dataclass` `field` デフォルト値 | ✅（Python 標準） | ✅ | 既存 models.py で `assignee: str = "-"` パターン使用済み |
| CSS `text-overflow: ellipsis` / `white-space: nowrap` | ✅（CSS3 標準 / 全モダンブラウザ対応） | ✅ | NFR-3（Chrome 120+ / Edge 120+）範囲内 |
| HTML `title` 属性（tooltip） | ✅（HTML 標準）| ✅ | 既存 HTML で使用済みパターン |
| 新規プラットフォーム機能 | N/A | N/A | 本 Wave は Python 標準ライブラリ + 既存 CSS/HTML パターンのみ / upstream-first 該当箇所なし |

---

## §13 参照

- [元 requirements.md v0.2.0](../requirements.md)
- [元 design.md v0.2.3](../design.md)
- [wave8/requirements.md v0.2.3](../wave8/requirements.md)（直近 Wave / FR-W8-4 無改変原則）
- [wave9/design.md](./design.md)
- [retro Wave 7](../../../artifacts/retro-W7-B5-2026-06-28.md)（Problem #10 / A10）
- [planning-quality-guideline](../../../../.claude/rules/planning-quality-guideline.md)
- [terminology](../../../../.claude/rules/terminology.md)
- [L2 委譲ガードレール](../../../artifacts/knowledge/l2-delegation-guardrails.md)
