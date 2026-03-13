# UI仕様書: LAM 概念説明スライド

## メタ情報
| 項目 | 内容 |
|------|------|
| ステータス | Approved |
| 作成日 | 2026-02-15 |
| 更新日 | 2026-03-13 |
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
- 免疫システム（hooks）とアーキテクチャの詳解
- ユースケースシナリオ（日常開発、進化の物語、新規プロジェクト）
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
  - [x] `file://` プロトコルでスライドが表示される
  - [x] CDN からの外部リソース読み込みのみ（ローカル依存なし）

### FR-002: スライドコンテンツ（6スライドデッキ構成）
- **説明**: LAM の概念を複数のテーマ別スライドデッキで伝える
- **優先度**: Must
- **受け入れ条件**:
  - [x] 以下のスライドデッキ構成を含む:

| デッキ | ファイル | 枚数 | 内容 |
|--------|---------|------|------|
| 目次ハブ | `index.html` | 1ページ | 全デッキへのナビゲーション |
| イントロダクション | `intro.html` | 8 | LAM の概要、Before/After、3フェーズ、始め方 |
| 新規プロジェクト | `story-newproject.html` | 20 | PLANNING→BUILDING→AUDITING の実践シナリオ |
| 日常開発 | `story-daily.html` | 16 | セッション復帰〜リリースの1日フロー |
| 進化の物語 | `story-evolution.html` | 12 | v1→v4 の進化、免疫システム、TDD内省 |
| アーキテクチャ | `architecture.html` | 15 | hooks、権限等級、Green State、lam-orchestrate |

### FR-003: Mermaid 図表示
- **説明**: フェーズフローや構造図を Mermaid で表示
- **優先度**: Must
- **受け入れ条件**:
  - [x] Mermaid CDN を使用してフロー図が描画される
  - [x] ダークテーマに合わせた配色
  - [x] reveal.js `slidechanged` イベントによる遅延レンダリング

### FR-004: ナビゲーション
- **説明**: ユーザーが自分のペースで閲覧できるナビゲーション
- **優先度**: Must
- **受け入れ条件**:
  - [x] 目次ハブ（index.html）から各デッキへジャンプ可能
  - [x] 各デッキから目次への戻りリンク
  - [x] プログレスバー表示（スライド番号 c/t）
  - [x] キーボード操作（矢印キー）

### FR-005: PDF エクスポート
- **説明**: 印刷・PDF 保存が可能
- **優先度**: Won't（`file://` プロトコルでは `?print-pdf` が安定動作しないため見送り）

### FR-006: 日本語・英語対応
- **説明**: 全スライドデッキに日英両バージョンを提供
- **優先度**: Must
- **受け入れ条件**:
  - [x] 各デッキにハイフン区切りの英語版を提供（例: `intro-en.html`）
  - [x] 日英切替リンクを各デッキに配置
  - [x] 目次ハブ（`index.html` / `index-en.html`）も日英対応

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
- HTML ファイル内に直接記述（reveal.js の `data-markdown` は `file://` で動作しないため）
- 変更頻度の目安: LAM のコア概念が変わったときのみ

## 4. 技術仕様

### 4.1 使用ライブラリ
| ライブラリ | バージョン | CDN URL | 用途 |
|-----------|----------|---------|------|
| reveal.js | 5.2.1 | `cdn.jsdelivr.net/npm/reveal.js@5.2.1` | スライドエンジン |
| reveal.js Highlight Plugin | 同梱 | 同上 `/plugin/highlight/highlight.js` | コードハイライト |
| Mermaid | 10.x | `cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs` | 図表描画 |
| Google Fonts | - | `fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;700&display=swap` | Web フォント |

### 4.2 ファイル構成
```
docs/slides/
├── index.html              # 目次ハブページ（日本語）
├── index-en.html           # 目次ハブページ（英語）
├── intro.html              # イントロダクション（日本語）
├── intro-en.html           # イントロダクション（英語）
├── story-newproject.html   # 新規プロジェクト（日本語）
├── story-newproject-en.html # 新規プロジェクト（英語）
├── story-daily.html        # 日常開発（日本語）
├── story-daily-en.html     # 日常開発（英語）
├── story-evolution.html    # 進化の物語（日本語）
├── story-evolution-en.html # 進化の物語（英語）
├── architecture.html       # アーキテクチャ（日本語）
└── architecture-en.html    # アーキテクチャ（英語）
```

**命名規則**: 英語版はハイフン区切り `-en` サフィックス（例: `intro-en.html`）

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
  plugins: [RevealHighlight]
});
```

### 4.4 Mermaid 統合
```javascript
// 遅延レンダリング: slidechanged イベントで現在スライドの Mermaid を描画
Reveal.on('slidechanged', event => {
  const mermaidElements = event.currentSlide.querySelectorAll('.mermaid:not([data-processed])');
  // ... レンダリング処理
});
```

## 5. UI デザイン仕様

### 5.1 テーマ・配色
- **ベーステーマ**: カスタムダークテーマ（reveal.js `black` ベース）
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
- **シナリオカード**: 権限等級別にカラーコード化

### 5.4 アニメーション
- `fragment` による段階表示（控えめに使用）
- 過度なアニメーションは禁止（認知負荷増大のため）

## 6. リンク戦略

### 6.1 スライドからのリンク先
- `CHEATSHEET.md`: コマンド詳細（GitHub URL）
- `README.md`: プロジェクト全体像（GitHub URL）
- `docs/internal/`: SSOT ドキュメント（GitHub URL）

### 6.2 スライドへのリンク元
| ファイル | 追加場所 | 内容 |
|---------|---------|------|
| `README.md` | 「使い方」セクションの前 | 「概念を理解するにはスライドを参照」 |
| `README_en.md` | 同上（英語） | 同上 |
| `CLAUDE.md` | References セクション | AI が初回ユーザーに案内できるように |

### 6.3 スライド間のナビゲーション
- 各デッキから `index.html`（または `index-en.html`）への戻りリンク
- 日英版間の言語切替リンク

## 7. 制約事項
- npm / Node.js への依存禁止
- HTML ファイルは1ファイルで完結（外部 .md ファイルの分離は CDN モードでは `file://` で動かないため）
- スライド内のテキストは概念レベルに限定（具体コマンド名は CHEATSHEET にリンク）

## 8. テスト観点
- ローカル `file://` でスライドが正常表示される
- CDN リソースが読み込める（オンライン時）
- 矢印キーでスライドが遷移する
- Mermaid 図が正常描画される
- 各デッキ間のリンクが正しく遷移する
- 日英切替リンクが正しく機能する
- スマートフォン表示で最低限閲覧可能

## 9. 決定済み事項
- [x] 英語版の提供タイミング → **日本語版と同時提供**（別ファイル `*-en.html`）
- [x] TOC-Progress プラグインの採否 → **不採用**（GPL-3.0 ライセンス汚染リスク、CDN 提供なし）
- [x] Google Fonts → **採用（CDN）**。Inter + JetBrains Mono を Google Fonts CDN で読み込む
- [x] ファイル命名規則 → **ハイフン区切り**（`intro-en.html`）
- [x] PDF エクスポート → **見送り**（`file://` プロトコルでの `?print-pdf` 非安定）
- [x] Markdown プラグイン → **不使用**（`file://` プロトコルで動作しないため HTML 直接記述）
- [x] スライドデッキ構成 → **テーマ別分割**（6デッキ: 目次 + intro + 3ストーリー + architecture）

## 10. 変更履歴
| 日付 | 変更者 | 内容 |
|------|--------|------|
| 2026-02-15 | LAM Coordinator | 初版作成（Draft） |
| 2026-03-13 | full-review | 現行実装に合わせて全面改訂（Approved） |
