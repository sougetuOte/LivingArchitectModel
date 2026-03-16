# Development Flow & TDD Cycle

本ドキュメントは、**Phase 1 (設計)**、**Phase 2 (実装)**、および **Phase 3 (定期監査)** におけるプロトコルを定義する。
"Definition of Ready" を通過したタスクのみが、このフローに乗ることができる。

## Phase 1: The "Pre-Flight" Impact Analysis (着手前影響分析)

**[PLANNING]** モードにて、以下の分析を行う。

1.  **Dependency Traversal (依存関係の巡回)**:
    - `Grep` / `Glob` 等を用いて、変更対象モジュールの依存元・依存先を物理的に特定する。
2.  **Static & Mental Simulation**:
    - コードを実行せず、静的解析と論理的思考実験により、DB スキーマや API への波及効果を予測する。
3.  **Git State Verification (Git 状態の検証)**:
    - `git status` および `git diff` を用いて、変更対象ファイルの現在の状態を確認する。
    - 未コミット変更がある場合、その差分を分析に含める。
4.  **Phase State Verification (フェーズ状態の検証)**:
    - `.claude/current-phase.md` を確認し、現在の開発フェーズ（PLANNING/BUILDING/AUDITING）を把握する。
    - フェーズとタスク内容が一致しない場合（例: BUILDING 中に仕様策定を要求された）、ユーザーに確認する。
5.  **Risk Assessment (Critical Agent)**:
    - `docs/internal/06_DECISION_MAKING.md` の **Critical Agent** として振る舞い、「手戻りリスク」と「破壊的変更の有無」を徹底的に洗い出す。
    - 楽観的な予測は排除し、最悪のケースを想定してユーザーに報告する。
6.  **Implementation Plan**:
    - 変更内容と検証計画をユーザーに提示し、承認を得ることを必須とする（`/planning` の承認ゲートフロー）。
    - 実装計画書は `docs/tasks/{feature_name}-tasks.md` に保存する。

### MAGI System（構造化意思決定）との連携

Phase 1 の各ステップにおいて、`/magi` スキル（AoT + MAGI Debate + Reflection）を活用できる:

| ステップ | 適用 | 参照 |
|----------|------|------|
| 要件定義 | 要件の Atom 分解 + MAGI 合議 | `/magi`, `.claude/agents/requirement-analyst.md` |
| 設計 | 設計の Atom 分解 + トレードオフ分析 | `/magi`, `.claude/agents/design-architect.md` |
| タスク分割 | タスクの Atom 化 + Wave 構成判断 | `/magi`, `.claude/agents/task-decomposer.md` |

詳細は `docs/internal/06_DECISION_MAKING.md` を参照。

> **Note**: `/magi` は主に Phase 1 で使用するが、Phase 2 での実装中に新たな設計判断が発生した場合や、
> Phase 3 でのリファクタリング方針決定時にも適用可能である。

### 文書精緻化（/clarify）

Phase 1 で作成した仕様書・設計書は `/clarify` スキルで曖昧さ・矛盾・欠落を検出し精緻化する:

- 仕様書ドラフト完成後に `/clarify docs/specs/<feature>-spec.md` を実行
- 設計書完成後に `/clarify docs/design/<feature>-design.md` を実行
- 文書間の横断チェック（spec ↔ design ↔ tasks）にも対応

## Phase 2: The TDD & Implementation Cycle (実装サイクル)

**[BUILDING]** モードにて、以下の厳格なサイクル（t-wada style）を回す。

### Step 1: Spec & Task Update (Dynamic Documentation)

- コードを書く前に、必ず `./docs/specs/` および `./docs/adr/` の更新案を提示する。
- ドキュメントとコードの同期は絶対である。
- 進捗管理には `docs/tasks/{feature_name}-tasks.md` を使用し、タスクの細分化と完了状況を可視化することを推奨する。

### Step 2: Red (Test First)

- 「仕様をコードで表現する」段階。
- 実装対象の機能要件を満たし、かつ**現在は失敗する**テストコードを作成する。
- テスト環境がない場合は、テストコード自体を「実行可能な仕様書」として提示する。

### Step 3: Green (Minimal Implementation)

- テストを通過させるための**最小限のコード**を実装する。
- 最速で Green にすることを優先し、設計の美しさは二の次とする。

### Step 4: Refactor (Clean Up)

- **Green になった後、初めて設計を改善する。**
- 重複排除、可読性向上、複雑度低減を行う。

### Step 5: Commit & Review

- 一つのサイクル（Red-Green-Refactor）が完了したら、直ちにユーザーに報告する。
- 検証結果は `docs/artifacts/walkthrough-<feature>.md` にまとめ、スクリーンショットやログと共に報告することを推奨する。

### Automated TDD Introspection v2

PostToolUse hook がテスト実行結果を自動監視し、以下を記録する:
- JUnit XML（`.claude/test-results.xml`）を読み取り、テスト成否を `.claude/tdd-patterns.log` に蓄積
- FAIL→PASS 遷移検出時に `/retro` 実行を推奨（通知のみ、自動実行なし）
- 同一パターン 2回以上出現で `/retro` 内でルール候補を提案（PM級承認）
- `src/` 配下のファイル変更を検知し、ドキュメント同期フラグを設定（詳細は `/ship` コマンド参照）

詳細は `.claude/rules/auto-generated/trust-model.md` を参照。

## Phase 3: Periodic Auditing (定期監査)

**[AUDITING]** モードにて、以下の活動を行う。

1.  **Full Codebase Review**: "Broken Windows" の修復。
2.  **Massive Refactoring**: アーキテクチャレベルの改善。
3.  **Documentation Gardening**: ドキュメントの動的保守と整合性確認。
4.  **Context Compression**: セッションが長期化した際、決定事項をドキュメントに書き出し、コンテキストリセットを提案する。

### 権限等級に基づく修正制御 (v4.0.0)

AUDITING フェーズでの修正は権限等級に基づく:
- **PG級**: 自動修正可（フォーマット、typo、lint 等）
- **SE級**: 修正後に報告（テスト追加、内部リファクタリング等）
- **PM級**: 指摘のみ、承認ゲート（仕様変更、アーキテクチャ変更等）

詳細は `.claude/rules/permission-levels.md` を参照。
