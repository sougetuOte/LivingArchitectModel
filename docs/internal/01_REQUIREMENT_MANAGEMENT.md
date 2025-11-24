# Requirement Management & Definition of Ready

本ドキュメントは、**Phase 0 (要件定義フェーズ)** におけるプロトコルを定義する。
ユーザーの「アイデア」を「実装可能な仕様」に変換するプロセスである。

## 1. From Memo to Spec (要件定義プロセス)

ユーザーの曖昧なメモや初期要望 (`docs/memos/`) を仕様書 (`docs/specs/`) に昇華させるため、以下の 4 要素を確定させること。

### A. Core Value (Why & Who)

- **User Story**: 「誰が」「何をしたいか」「なぜなら...」
- **Problem Statement**: 現状の課題と、解決後の理想状態。

### B. Data Model (What)

- **Entities**: 扱うデータの実体（名詞）。
- **Relationships**: エンティティ間の関係性（1 対多、多対多）。
- **Diagrams**: Mermaid 記法を用いた ER 図 または クラス図。

### C. Interface (How)

- **API Definition**: エンドポイント、リクエスト/レスポンス形式（JSON Schema）。
- **UI Mock**: 画面構成要素、遷移フロー、状態変化。

### D. Constraints (Limits)

- **Non-Functional Requirements**: パフォーマンス、セキュリティ、対応ブラウザ。
- **Tech Stack**: 使用するライブラリ、フレームワークのバージョン制約。

### E. Perspective Check (3 Agents)

- `docs/internal/06_DECISION_MAKING.md` に基づき、Affirmative / Critical / Mediator の視点で仕様をレビュー済みか確認する。
- 特に「Critical Agent」によるリスク指摘が解決されているかを確認すること。

## 2. Definition of Ready (着手判定基準)

実装タスク（Phase 1）へ移行する前に、以下のチェックリストを全て満たさなければならない。

- [ ] **Doc Exists**: `docs/specs/` に仕様書が存在する。
- [ ] **Unambiguous**: 上記 A〜D の要素が明記され、解釈の揺れがない。
- [ ] **Atomic**: タスクが 1 Pull Request で完結するサイズに分割されている。
- [ ] **Testable**: Acceptance Criteria（完了条件）がテストコードで表現可能である。
