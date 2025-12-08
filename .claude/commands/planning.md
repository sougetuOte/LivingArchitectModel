---
description: "PLANNINGフェーズを開始 - 要件定義・設計・タスク分解"
---

# PLANNINGフェーズ開始

あなたは今から **[PLANNING]** モードに入ります。

## 実行ステップ

1. **フェーズ状態を更新**
   - `.claude/current-phase.md` を `PLANNING` に更新する

2. **必須ドキュメントを読み込む**
   - `docs/internal/01_REQUIREMENT_MANAGEMENT.md` を精読
   - `docs/internal/02_DEVELOPMENT_FLOW.md` の Phase 1 を精読
   - `docs/internal/06_DECISION_MAKING.md`（3 Agents Model）を確認

3. **PLANNINGルールを適用**
   - **コード生成は禁止**（実装コード、テストコード共に）
   - 成果物は `.md` 形式のみ
   - 出力先: `docs/specs/`, `docs/adr/`, `docs/tasks/`

4. **作業の進め方**
   - 要件が曖昧な場合は `requirement-analyst` サブエージェントを推奨
   - 設計検討には `design-architect` サブエージェントを推奨
   - 重要な決定には 3 Agents Model（Affirmative/Critical/Mediator）を適用

## 禁止事項

- `src/` ディレクトリへのファイル作成・編集
- `.ts`, `.js`, `.py`, `.go` 等の実装コード生成
- テストコードの実装（テスト観点の列挙は可）

## フェーズ終了条件

以下を満たしたら `/building` でBUILDINGフェーズに移行:

- [ ] `docs/specs/` に仕様書が存在する
- [ ] Definition of Ready（01_REQUIREMENT_MANAGEMENT.md）を満たしている
- [ ] タスクが1 PR単位に分割されている

## 確認メッセージ

以下を表示してユーザーに確認:

```
[PLANNING] フェーズを開始しました。

適用ルール:
- コード生成: 禁止
- 成果物形式: .md のみ
- 出力先: docs/specs/, docs/adr/, docs/tasks/

読み込み済み:
- 01_REQUIREMENT_MANAGEMENT.md
- 02_DEVELOPMENT_FLOW.md (Phase 1)
- 06_DECISION_MAKING.md

何を検討しますか？
```
