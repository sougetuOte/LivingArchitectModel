# Architectural Standards & Quality Gates

本ドキュメントは、"Living Architect" がコードを生成・レビューする際の基準値（Quality Gates）である。

## 1. Design Principles (設計原則)

### Single Source of Truth (SSOT)

- 設定値、定数、型定義は一箇所で定義する。重複定義はバグの温床とみなす。
- ドキュメントとコードが乖離した場合、ドキュメントを正とする。

### Cognitive Load Management (認知負荷の管理)

- **Magic Numbers/Strings**: 禁止。定数化すること。
- **Function Length**: 1 関数は 1 画面（約 30-50 行）を目安とする。
- **Naming**: 「何が入っているか」だけでなく「何のためにあるか」がわかる名前をつける。

## 2. Documentation Standards (ドキュメント基準)

### ADR (Architectural Decision Records)

重要な技術的決定（ライブラリ選定、DB 設計、アーキテクチャ変更）を行う際は、必ず ADR を作成すること。

- Status, Context, Decision, Consequences を記述する。

### Docstrings & Comments

- **What**: コードで語る。
- **Why**: コメントで語る。
- **Workaround**: `FIXME` または `HACK` タグと理由を記述する。

## 3. Spec Maturity (仕様の成熟度)

- **Unambiguous**: 自然言語の曖昧さが排除されている。
- **Testable**: テストケースとして記述可能である。
- **Atomic**: 独立して実装・検証可能である。

## 4. Refactoring Triggers (リファクタリングのトリガー)

以下の兆候が見られた場合、機能追加を停止し、リファクタリングを優先する。

- **Deep Nesting**: ネスト > 3 階層
- **Long Function**: 行数 > 50 行
- **Duplication**: 重複 > 3 回 (Rule of Three)
- **Parameter Explosion**: 引数 > 4 個
- **Nested Ternary**: ネストした三項演算子
- **Dense One-liner**: 理解に時間がかかるワンライナー

## 5. Code Clarity Principle（コード明確性原則）

**Clarity over Brevity（明確さ > 簡潔さ）** を原則とする。

### 推奨
- 読みやすさを最優先する
- 明示的なコードを書く（暗黙の挙動に頼らない）
- 適切な抽象化を維持する（1箇所でしか使わなくても意味のある抽象化は残す）
- 条件分岐は switch/if-else で明確に書く

### 禁止
- ネストした三項演算子
- 読みやすさを犠牲にした行数削減
- 複数の関心事を1つの関数に統合
- デバッグ・拡張を困難にする「賢い」コード
- 3行程度の類似コードを無理に共通化

### 判断基準
「このコードを3ヶ月後の自分が読んで、すぐに理解できるか？」

## 6. Technology Trend Awareness (トレンド適応)

- ライブラリの Deprecated 状況を定期的に確認する。
- 長期保守性を最優先し、枯れた技術と最新技術のバランスをとる。
