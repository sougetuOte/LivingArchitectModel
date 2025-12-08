---
name: adr-template
description: |
  ADR（Architecture Decision Record）作成を支援するテンプレートスキル。
  docs/adr/ へのADR作成時に自動適用され、
  06_DECISION_MAKING.md の3 Agents Modelに準拠した構造を提案する。
  アーキテクチャ決定、技術選定、設計方針の記録時に活用される。
---

# ADRテンプレートスキル

## 目的

このスキルは、ADR（Architecture Decision Record）作成時に一貫した構造と3 Agents Modelによる多角的検証を確保するためのテンプレートを提供する。

## 適用条件

以下のいずれかに該当する場合、このスキルを適用する:

- `docs/adr/` への新規ファイル作成
- アーキテクチャ決定、技術選定の記録を求められた
- `/adr-create` コマンドの実行時

## ファイル命名規則

```
docs/adr/
├── 0001-initial-architecture.md
├── 0002-database-selection.md
├── 0003-api-design-pattern.md
└── ...
```

形式: `NNNN-kebab-case-title.md`
- NNNN: 4桁の連番（0001から）
- タイトル: ケバブケースで簡潔に

## ADRテンプレート

```markdown
# ADR-NNNN: [決定タイトル]

## メタ情報
| 項目 | 内容 |
|------|------|
| ステータス | Proposed / Accepted / Deprecated / Superseded |
| 日付 | YYYY-MM-DD |
| 意思決定者 | [名前/ロール] |
| 関連ADR | [ADR-XXXX](./XXXX-*.md) |

## コンテキスト

### 背景
[この決定が必要になった背景、課題]

### 制約条件
- [技術的制約]
- [ビジネス制約]
- [リソース制約]

### 要求事項
- [満たすべき要件1]
- [満たすべき要件2]

## 検討した選択肢

### Option A: [選択肢名]
**概要**: [簡潔な説明]

**メリット**:
- [利点1]
- [利点2]

**デメリット**:
- [欠点1]
- [欠点2]

### Option B: [選択肢名]
**概要**: [簡潔な説明]

**メリット**:
- [利点1]

**デメリット**:
- [欠点1]

### Option C: [選択肢名]
...

## 3 Agents Analysis

### [Affirmative] 推進者の視点
> 最高の結果はどうなるか？どうすれば実現できるか？

- [採用時のメリット、可能性]
- [開発効率への貢献]
- [ユーザー価値への貢献]

### [Critical] 批判者の視点
> 最悪の場合どうなるか？何が壊れるか？

- [リスク、懸念点]
- [エッジケース、失敗シナリオ]
- [技術的負債の可能性]
- [セキュリティ懸念]

### [Mediator] 調停者の視点
> 今、我々が取るべき最善のバランスは何か？

- [両視点の統合]
- [リスク緩和策]
- [段階的導入の提案]

## 決定

**採用**: Option [X]

### 決定理由
[なぜこの選択肢を採用したか]

### 却下理由
- **Option [Y]**: [却下した理由]
- **Option [Z]**: [却下した理由]

## 影響

### ポジティブな影響
- [良い影響1]
- [良い影響2]

### ネガティブな影響
- [悪い影響1]（緩和策: [対策]）

### 影響を受けるコンポーネント
- `src/[path]`: [影響内容]
- `docs/specs/[file]`: [更新必要]

## 実装計画

### フェーズ1: [フェーズ名]
- [ ] [タスク1]
- [ ] [タスク2]

### フェーズ2: [フェーズ名]
- [ ] [タスク3]

## 検証方法
- [この決定が正しかったかを検証する方法]
- [見直しのトリガー条件]

## 参考資料
- [参考リンク1]
- [参考リンク2]
```

## ADRステータスの遷移

```
Proposed → Accepted → [Deprecated | Superseded]
    ↓
  Rejected
```

| ステータス | 説明 |
|-----------|------|
| Proposed | 提案中、レビュー待ち |
| Accepted | 承認済み、実装可能 |
| Deprecated | 非推奨、新規採用不可 |
| Superseded | 新しいADRに置き換え |
| Rejected | 却下 |

## ADR作成ワークフロー

1. **起案**
   - コンテキストと選択肢を整理
   - ステータス: `Proposed`

2. **3 Agents 分析**
   - Affirmative: メリットを最大化
   - Critical: リスクを洗い出し
   - Mediator: バランスを取る

3. **レビュー**
   - ステークホルダーからのフィードバック
   - 選択肢の追加・修正

4. **決定**
   - 最終決定を記録
   - ステータス: `Accepted`

5. **実装追跡**
   - 影響を受けるコンポーネントの更新
   - 検証結果の記録

## 既存ADRの更新

### Supersede（置き換え）の場合

旧ADR:
```markdown
## メタ情報
| ステータス | Superseded by [ADR-XXXX](./XXXX-*.md) |
```

新ADR:
```markdown
## メタ情報
| 関連ADR | Supersedes [ADR-YYYY](./YYYY-*.md) |
```

## 参照ドキュメント

- `docs/internal/06_DECISION_MAKING.md`
- `/adr-create` コマンド
