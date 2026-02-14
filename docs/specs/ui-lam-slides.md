# UI仕様書: LAM 概念説明スライド

## メタ情報
| 項目 | 内容 |
|------|------|
| ステータス | Draft |
| 作成日 | 2026-02-15 |
| 更新日 | 2026-02-15 |
| 関連ADR | なし |

## 1. 概要

### 1.1 目的
Living Architect Model（LAM）の概念・哲学・ワークフローを初見ユーザーに視覚的に伝えるためのHTMLスライドを作成する。現状、CLAUDE.md や docs/internal/ を直接読む必要があり、初回参加者のオンボーディングハードルが高い。

### 1.2 ユーザーストーリー
```
As a 初めてLAMプロジェクトに参加する開発者,
I want LAMの全体像を視覚的に短時間で把握したい,
So that docs/internal/ を全部読まなくても基本的な使い方がわかる.
```

### 1.3 スコープ
**含む:**
- LAM の哲学・コアコンセプト
- 3フェーズフローと承認ゲートの可視化
- 3 Agents Model の概念説明
- クイックスタート手順（骨格のみ）
- CHEATSHEET / README へのリンク誘導

**含まない:**
- コマンド名やエージェント名の詳細リスト（CHEATSHEET にリンク）
- 実装コードの解説
- API 仕様

## 2. 機能要求

### FR-001: HTML単体で動作
- **説明**: npm install やビルドステップなしで、ブラウザでローカルファイルとして開ける
- **優先度**: Must
- **受け入れ条件**:
  - [ ] `file://` プロトコルでスライドが表示される
  - [ ] CDN からの外部リソース読み込みのみ（ローカル依存なし）

### FR-002: スライドコンテンツ（概念レイヤー）
- **説明**: LAM の概念を15-25枚のスライドで伝える
- **優先度**: Must
- **受け入れ条件**:
  - [ ] 以下のセクション構成を含む:

| セクション | 枚数目安 | 内容 |
|-----------|---------|------|
| タイトル | 1 | プロジェクト名、キャッチフレーズ |
| 課題提起 | 2-3 | AI開発の現状課題（なぜLAMが必要か） |
| コアコンセプト | 3-4 | Active Retrieval, Gatekeeper, Zero-Regression, Living Documentation |
| フェーズ制御 | 3-4 | PLANNING → BUILDING → AUDITING + 承認ゲート |
| 3 Agents Model | 2-3 | Affirmative / Critical / Mediator + AoT |
| クイックスタート | 2-3 | 最初にやること3ステップ + CHEATSHEET へのリンク |
| まとめ | 1 | 次のアクション |

### FR-003: Mermaid 図表示
- **説明**: フェーズフローや構造図を Mermaid で表示
- **優先度**: Should
- **受け入れ条件**:
  - [ ] Mermaid CDN を使用してフロー図が描画される
  - [ ] ダークテーマに合わせた配色

### FR-004: ナビゲーション
- **説明**: ユーザーが自分のペースで閲覧できるナビゲーション
- **優先度**: Should
- **受け入れ条件**:
  - [ ] 目次スライドからセクションジャンプ可能
  - [ ] プログレスバー表示（スライド番号 c/t）
  - [ ] キーボード操作（矢印キー）

### FR-005: PDF エクスポート
- **説明**: 印刷・PDF 保存が可能
- **優先度**: Could
- **受け入れ条件**:
  - [ ] `?print-pdf` パラメータで印刷用レイアウト切替

### FR-006: 日本語・英語対応
- **説明**: 日英両方のスライドを提供（将来対応可）
- **優先度**: Could
- **受け入れ条件**:
  - [ ] 初版は日本語のみ
  - [ ] 英語版追加時の構成が明確（別ファイル or 切替機能）

## 3. 非機能要求

### NFR-001: パフォーマンス
- CDN 読み込み含めて初期表示3秒以内（通常回線）

### NFR-002: 環境要件
- モダンブラウザ（Chrome, Firefox, Safari, Edge の最新2バージョン）
- JavaScript 有効
- インターネット接続（CDN 用）
- Node.js / npm は **不要**

### NFR-003: メンテナンス性
- スライド内容は概念レベルに限定（具体的なコマンド名は CHEATSHEET にリンク）
- HTML ファイル内に Markdown で記述（reveal.js Markdown プラグイン）
- 変更頻度の目安: LAM のコア概念が変わったときのみ

## 4. 技術仕様

### 4.1 使用ライブラリ
| ライブラリ | バージョン | CDN URL | 用途 |
|-----------|----------|---------|------|
| reveal.js | 5.2.1 | `cdn.jsdelivr.net/npm/reveal.js@5.2.1` | スライドエンジン |
| reveal.js Markdown Plugin | 同梱 | 同上 `/plugin/markdown/markdown.js` | Markdown 記述 |
| reveal.js Highlight Plugin | 同梱 | 同上 `/plugin/highlight/highlight.js` | コードハイライト |
| Mermaid | 10.x | `cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs` | 図表描画 |
| Google Fonts | - | `fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;700&display=swap` | Web フォント |

### 4.2 ファイル構成
```
docs/slides/
├── index.html          # 目次ハブページ
├── concept.html        # コンセプト説明スライド（21枚）
├── usecase.html        # ユースケースシナリオスライド（18枚）
├── (concept_en.html)   # 英語版コンセプト（将来）
└── (usecase_en.html)   # 英語版ユースケース（将来）
```

### 4.3 reveal.js 設定
```javascript
Reveal.initialize({
  hash: true,
  progress: true,
  slideNumber: 'c/t',
  transition: 'fade',
  keyboard: true,
  overview: true,
  help: true,
  pdfSeparateFragments: false,
  plugins: [RevealMarkdown, RevealHighlight]
});
```

## 5. UI デザイン仕様

### 5.1 テーマ・配色
- **ベーステーマ**: reveal.js `black`（ダークテーマ）
- **カスタム CSS 変数**:

```css
:root {
  --accent-primary: #4ec9b0;     /* ティール: 強調、見出し */
  --accent-secondary: #569cd6;   /* ブルー: リンク、補助 */
  --accent-warning: #ce9178;     /* オレンジ: 警告、注意 */
  --code-background: #2d2d2d;    /* コードブロック背景 */
}
```

- **フェーズ別カラー**: 各フェーズを色で識別
  - PLANNING: `#569cd6`（ブルー）
  - BUILDING: `#4ec9b0`（ティール）
  - AUDITING: `#ce9178`（オレンジ）

### 5.2 タイポグラフィ
| 要素 | サイズ | フォント |
|------|--------|---------|
| h1 | 2.5em | Inter, sans-serif |
| h2 | 1.6em | Inter, sans-serif |
| 本文 | 1em（24px基準） | Inter, sans-serif |
| コード | 0.8em | JetBrains Mono, monospace |

### 5.3 レイアウトパターン
- **1スライド1コンセプト**: 20-30語以内
- **3 Agents**: Bento Grid（3カラム カード）
- **フロー図**: Mermaid LR/TD + fragment アニメーション
- **階層構造**: ツリー表記

### 5.4 アニメーション
- `fragment` による段階表示（控えめに使用）
- `data-auto-animate` によるフェードトランジション
- 過度なアニメーションは禁止（認知負荷増大のため）

## 6. リンク戦略

### 6.1 スライドからのリンク先
- `CHEATSHEET.md`: コマンド詳細（GitHub URL）
- `README.md`: プロジェクト全体像（GitHub URL）
- `docs/internal/`: SSOT ドキュメント（GitHub URL）

### 6.2 スライドへのリンク元（コミット時に更新）
| ファイル | 追加場所 | 内容 |
|---------|---------|------|
| `README.md` | 「使い方」セクションの前 | 「概念を理解するにはスライドを参照」 |
| `README_en.md` | 同上（英語） | 同上 |
| `CHEATSHEET.md` | 「はじめに」セクション冒頭 | 「まずスライドで概要を掴む」 |
| `CLAUDE.md` | References セクション | AI が初回ユーザーに案内できるように |

## 7. 制約事項
- npm / Node.js への依存禁止
- HTML ファイルは1ファイルで完結（外部 .md ファイルの分離は CDN モードでは `file://` で動かないため）
- スライド内のテキストは概念レベルに限定（具体コマンド名は CHEATSHEET にリンク）

## 8. テスト観点
- ローカル `file://` でスライドが正常表示される
- CDN リソースが読み込める（オンライン時）
- 矢印キーでスライドが遷移する
- Mermaid 図が正常描画される
- `?print-pdf` で印刷レイアウトが適用される
- 各セクションリンクが正しく遷移する
- スマートフォン表示で最低限閲覧可能

## 9. 決定済み事項（旧・未決定事項）
- [x] 英語版の提供タイミング → **日本語版完成後すぐに着手**（別ファイル `index_en.html`）
- [x] TOC-Progress プラグインの採否 → **不採用**（GPL-3.0 ライセンス汚染リスク、CDN 提供なし。reveal.js 標準の `progress` + `slideNumber` + 目次スライドで代替）
- [x] Google Fonts → **採用（CDN）**。Inter + JetBrains Mono を Google Fonts CDN で読み込む

## 10. 変更履歴
| 日付 | 変更者 | 内容 |
|------|--------|------|
| 2026-02-15 | LAM Coordinator | 初版作成 |
