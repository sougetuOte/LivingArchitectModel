---
name: spec-template
description: |
  仕様書作成を支援するテンプレートスキル。
  docs/specs/ への仕様書作成時に自動適用され、
  01_REQUIREMENT_MANAGEMENT.md に準拠した構造を提案する。
  要件定義、機能仕様、API仕様の作成時に活用される。
version: 1.0.0
paths:
  - "docs/specs/*.md"
when_to_use: "仕様書・要件定義・機能仕様・API 仕様を作成するとき。docs/specs/ にファイルを作成する場面で活用する。"
allowed-tools: Read, Write, Edit
---

# 仕様書テンプレートスキル

## 目的

このスキルは、仕様書作成時に一貫した構造と品質を確保するためのテンプレートを提供する。

## 適用条件

以下のいずれかに該当する場合、このスキルを適用する:

- `docs/specs/` への新規ファイル作成
- 仕様書、要件定義、機能仕様の作成を求められた
- API仕様、データモデル定義の作成を求められた

## テンプレート選択ガイド

| 目的 | テンプレート | ファイル名規則 |
|------|-------------|---------------|
| 機能要件 | 機能仕様書 | `feat-[機能名].md` |
| API定義 | API仕様書 | `api-[エンドポイント名].md` |
| データ | データモデル仕様 | `data-[エンティティ名].md` |
| UI/UX | UI仕様書 | `ui-[画面名].md` |


## テンプレート本体（必要なものだけ読む）

上の選択ガイドで決めた 1 種類だけを読むこと。3 つとも読む必要はない。

| テンプレート | 参照先 |
|:--|:--|
| 機能仕様書 | [references/template-feature-spec.md](references/template-feature-spec.md) |
| API 仕様書 | [references/template-api-spec.md](references/template-api-spec.md) |
| データモデル仕様 | [references/template-data-model.md](references/template-data-model.md) |
## Definition of Ready チェック

仕様書が完成したら、以下を確認する:

```markdown
## Definition of Ready チェックリスト

- [ ] **Doc Exists**: docs/specs/ に仕様書が存在する
- [ ] **Unambiguous**: A〜Dの要素が明記され、解釈の揺れがない
  - [ ] Core Value (Why & Who)
  - [ ] Data Model (What)
  - [ ] Interface (How)
  - [ ] Constraints (Limits)
- [ ] **Atomic**: タスクが1 PR単位に分割されている
- [ ] **Testable**: 受け入れ条件がテストコードで表現可能
- [ ] **Reviewed**: 3 Agents Model でレビュー済み
```

## 参照ドキュメント

- `docs/internal/01_REQUIREMENT_MANAGEMENT.md`
