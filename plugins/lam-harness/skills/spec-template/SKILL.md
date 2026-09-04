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
  - "docs/specs/*/*.md"
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

## Step 1: 配置を決める

配置は「Milestone に属する仕様一式か、単独の仕様書か」で決まる。

| ケース | 配置 | 例 |
|:--|:--|:--|
| **Milestone の仕様一式**（既定） | `docs/specs/<milestone-slug>/` に `requirements.md` / `design.md` / `tasks.md` | `docs/specs/m-1-opus5-migration/requirements.md` |
| **単独の仕様書**（Milestone に属さない機能・機構） | `docs/specs/<topic>.md`（主題を表す slug / prefix 規約なし） | `docs/specs/tdd-introspection-v2.md` |

`<milestone-slug>` の規約は `.claude/rules/terminology.md` §4「命名規則」が SSOT。
判断に迷う場合は Milestone ディレクトリ形式に倒す（LAM の現行運用の主形）。

## Step 2: テンプレートを選ぶ

`requirements.md` / 単独仕様書 / その他の仕様文書は、**内容の種類**でテンプレートを選ぶ。

| 書く内容 | テンプレート | 参照先 |
|:--|:--|:--|
| 機能要件（FR / NFR / スコープ / 受け入れ条件） | 機能仕様書 | [references/template-feature-spec.md](references/template-feature-spec.md) |
| API エンドポイント定義（リクエスト / レスポンス / エラー） | API 仕様書 | [references/template-api-spec.md](references/template-api-spec.md) |
| データ構造・エンティティ定義 | データモデル仕様 | [references/template-data-model.md](references/template-data-model.md) |

**選んだ 1 種類だけを読むこと。3 つとも読む必要はない。**

### このスキルが担当しない文書

| 文書 | 担当 |
|:--|:--|
| `design.md`（設計・アーキテクチャ） | `design-architect` サブエージェント |
| `tasks.md`（タスク分解） | `task-decomposer` サブエージェント |
| ADR | `adr-template` スキル |

### UI 仕様を書く場合

**専用テンプレートは持たない。** 機能仕様書テンプレートの
「## 5. インターフェース > ### UI（該当する場合）」節に書く。
画面単位で独立した仕様書にする場合も、同テンプレートを土台にする
（実例: `docs/specs/ui-lam-slides.md`）。

## Step 3: Definition of Ready チェック

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
