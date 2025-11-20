# Development Flow & TDD Cycle

本ドキュメントは、**Phase 1 (設計)** および **Phase 2 (実装)** におけるプロトコルを定義する。
"Definition of Ready" を通過したタスクのみが、このフローに乗ることができる。

## Phase 1: The "Pre-Flight" Impact Analysis (着手前影響分析)

**[PLANNING]** モードにて、以下の分析を行う。

1.  **Dependency Traversal (依存関係の巡回)**:
    - `grep_search` 等を用いて、変更対象モジュールの依存元・依存先を物理的に特定する。
2.  **Static & Mental Simulation**:
    - コードを実行せず、静的解析と論理的思考実験により、DB スキーマや API への波及効果を予測する。
3.  **Risk Assessment**:
    - 「手戻りリスク」と「破壊的変更の有無」をユーザーに報告する。

## Phase 2: The TDD & Implementation Cycle (実装サイクル)

**[BUILDING]** モードにて、以下の厳格なサイクル（t-wada style）を回す。

### Step 1: Spec & Task Update (Dynamic Documentation)

- コードを書く前に、必ず `./docs/specs/` および `./docs/adr/` の更新案を提示する。
- ドキュメントとコードの同期は絶対である。

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

## Phase 3: Periodic Auditing (定期監査)

**[AUDITING]** モードにて、以下の活動を行う。

1.  **Full Codebase Review**: "Broken Windows" の修復。
2.  **Massive Refactoring**: アーキテクチャレベルの改善。
3.  **Documentation Gardening**: ドキュメントの動的保守と整合性確認。
