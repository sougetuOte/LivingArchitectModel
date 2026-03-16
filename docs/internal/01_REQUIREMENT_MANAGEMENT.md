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

### E. Perspective Check (MAGI System)

- `docs/internal/06_DECISION_MAKING.md` に基づき、MELCHIOR / BALTHASAR / CASPAR の視点で仕様をレビュー済みか確認する。
- 特に BALTHASAR（批判者）によるリスク指摘が解決されているかを確認すること。
- 複雑な判断（判断ポイント 2+、影響レイヤー 3+、選択肢 3+）には `/magi` スキルの活用を推奨する。

### F. Clarification（曖昧さの解消）

- 仕様書ドラフト完成後、`/clarify` スキルで曖昧さ・矛盾・欠落を検出する。
- 「適切に」「必要に応じて」等の曖昧な修飾語を数値・条件に置換する。
- 詳細は `.claude/rules/planning-quality-guideline.md`（Requirements Smells）を参照。

## 2. Definition of Ready (着手判定基準)

実装タスク（Phase 1）へ移行する前に、以下のチェックリストを全て満たさなければならない。

- [ ] **Doc Exists**: `docs/specs/` に仕様書が存在する。
- [ ] **Unambiguous**: 上記 A〜D の要素が明記され、解釈の揺れがない。`/clarify` で精緻化済みであること。
- [ ] **Atomic**: タスクが 1 Pull Request で完結するサイズに分割されている。
- [ ] **Testable**: Acceptance Criteria（完了条件）がテストコードで表現可能である。
