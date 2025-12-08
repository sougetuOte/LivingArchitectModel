---
name: planning-guardrail
description: |
  PLANNINGフェーズでの作業時に自動適用するガードレール。
  要件定義、設計検討、仕様策定、タスク分解のセッションで、
  コード生成を抑制しドキュメント作成に集中させる。
  .claude/current-phase.md が PLANNING の場合、または
  /planning コマンド実行後のセッションで適用される。
allowed-tools: Read, Glob, Grep, Write, Edit, WebSearch, WebFetch, Task
---

# PLANNINGフェーズ ガードレール

## 目的

このスキルは、PLANNINGフェーズにおいて Claude が「つい実装しようとする」傾向を抑制し、ドキュメント作成に集中させるためのガードレールを提供する。

## 適用条件

以下のいずれかに該当する場合、このスキルを適用する:

- `.claude/current-phase.md` の内容が `PLANNING` である
- ユーザーが要件定義、設計、仕様策定について議論している
- `docs/specs/`, `docs/adr/`, `docs/tasks/` への出力を求められている

## 禁止事項（MUST NOT）

1. **実装コードの生成禁止**
   - `.ts`, `.js`, `.py`, `.go`, `.java`, `.rs` 等のソースファイル作成
   - `src/` ディレクトリへのファイル作成・編集

2. **テストコードの実装禁止**
   - `*.test.ts`, `*.spec.js`, `test_*.py` 等のテストファイル作成
   - ただし、テスト観点・テストケースの列挙（.md形式）は許可

3. **設定ファイルの変更禁止**
   - `package.json`, `tsconfig.json`, `pyproject.toml` 等の変更
   - ただし、仕様書内での設定方針の記述は許可

## 許可事項（MAY）

1. **ドキュメント作成**
   - `docs/specs/*.md` への仕様書作成
   - `docs/adr/*.md` へのADR作成
   - `docs/tasks/*.md` へのタスク定義
   - `docs/memos/*.md` への検討メモ

2. **既存コードの読み取り**
   - 仕様策定のための既存実装の確認
   - 影響範囲分析のためのコード検索

3. **図表の作成**
   - Mermaid記法によるER図、シーケンス図、クラス図

## 警告義務

ユーザーから実装コードの生成を求められた場合、以下の警告を必ず表示すること:

```
⚠️ フェーズ警告

現在は PLANNING フェーズです。
実装コードの生成はこのフェーズでは推奨されません。

選択肢:
1. このまま仕様策定を続ける
2. /building コマンドで BUILDING フェーズに移行する
3. 「承知の上で実装」と明示して続行する

どちらを選びますか？
```

## 推奨ワークフロー

1. **要件の明確化**
   - ユーザーストーリーの作成
   - 受け入れ条件の定義
   - 3 Agents Model による検証

2. **設計の検討**
   - データモデルの定義（ER図）
   - インターフェースの定義（API仕様）
   - アーキテクチャの決定（ADR）

3. **タスクの分解**
   - 1 PR 単位への分割
   - 依存関係の明確化
   - Definition of Ready の確認

## 成果物テンプレート

仕様書作成時は以下の構造を提案する:

```markdown
# 機能仕様書: [機能名]

## 1. 概要
### 目的
### ユーザーストーリー

## 2. 機能要求
### FR-001: [要求名]
- 説明:
- 受け入れ条件:
  - [ ]

## 3. 非機能要求
### NFR-001: [要求名]

## 4. データモデル
（Mermaid ER図）

## 5. インターフェース
（API定義 or UI仕様）

## 6. 制約事項

## 7. 未決定事項
```

## 参照ドキュメント

- `docs/internal/01_REQUIREMENT_MANAGEMENT.md`
- `docs/internal/02_DEVELOPMENT_FLOW.md` (Phase 1)
- `docs/internal/06_DECISION_MAKING.md`
