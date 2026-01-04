# モデル選定ガイドライン

## Purpose

フェーズに応じた最適なモデル選定を案内する。

## Recommendations

| フェーズ | 推奨モデル | 理由 |
|---------|-----------|------|
| **PLANNING** | Claude Opus / Sonnet | 複雑な依存関係解決、要件定義、リスク分析に推論能力が必須 |
| **BUILDING** | Claude Sonnet | TDD サイクルの実装品質担保。単純コーディングなら Haiku も可 |
| **AUDITING** | Claude Opus (Long Context) | 大量コードベースの全体整合性チェックに長いコンテキストが必要 |

## Selection Criteria

- **推論の深さが必要** → Opus
- **バランス重視** → Sonnet
- **速度・コスト重視** → Haiku

## Usage

ユーザーがモデル選択について質問した場合、上記表を提示する。
