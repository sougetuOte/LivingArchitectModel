---
description: "BUILDINGフェーズを開始 - TDD実装サイクル"
---

# BUILDINGフェーズ開始

あなたは今から **[BUILDING]** モードに入ります。

## 実行ステップ

1. **フェーズ状態を更新**
   - `.claude/current-phase.md` を `BUILDING` に更新する

2. **必須ドキュメントを読み込む**
   - `docs/internal/02_DEVELOPMENT_FLOW.md` の Phase 2 を精読
   - `docs/internal/03_QUALITY_STANDARDS.md` を確認
   - 関連する `docs/specs/` の仕様書を読み込む

3. **BUILDINGルールを適用**
   - **TDDサイクル厳守**: Red → Green → Refactor
   - 仕様書とコードの同期は絶対
   - 1サイクル完了ごとにユーザーに報告

4. **作業の進め方**
   - TDD実装には `tdd-developer` サブエージェントを推奨
   - 実装前に必ず `docs/specs/` の対応仕様を確認
   - コード変更時は対応ドキュメントも同時更新（Atomic Commit）

## TDDサイクル（t-wada style）

### Step 1: Spec & Task Update
- コードを書く前に `docs/specs/` の更新案を提示

### Step 2: Red (Test First)
- 失敗するテストを先に書く
- テストは「実行可能な仕様書」

### Step 3: Green (Minimal Implementation)
- テストを通す最小限のコードを実装
- 美しさより速さを優先

### Step 4: Refactor
- Green になってから設計を改善
- 重複排除、可読性向上

### Step 5: Commit & Review
- ユーザーに報告
- `walkthrough.md` に検証結果をまとめる

## 禁止事項

- 仕様書なしでの実装開始
- テストなしでの本実装
- ドキュメント更新なしのコード変更

## フェーズ終了条件

以下を満たしたら `/auditing` でAUDITINGフェーズに移行:

- [ ] 全テストがパス
- [ ] 仕様書とコードが同期している
- [ ] `walkthrough.md` で検証完了

## 確認メッセージ

以下を表示してユーザーに確認:

```
[BUILDING] フェーズを開始しました。

適用ルール:
- TDDサイクル: Red → Green → Refactor
- ドキュメント同期: 必須
- 報告: 1サイクルごと

読み込み済み:
- 02_DEVELOPMENT_FLOW.md (Phase 2)
- 03_QUALITY_STANDARDS.md

どのタスクから実装しますか？
（対応する仕様書のパスを教えてください）
```
