---
description: "PLANNINGフェーズを開始 - 要件定義・設計・タスク分解"
---

# PLANNINGフェーズ開始

あなたは今から **[PLANNING]** モードに入ります。

## 実行ステップ

1. **フェーズ状態を更新**
   - `.claude/current-phase.md` を `PLANNING` に更新する

2. **状態ファイルを確認**
   - `.claude/states/` 内に対象機能の状態ファイルがあるか確認
   - なければ初期化を提案:「機能名を教えてください（例: auth-system）」
   - あれば読み込み、現在のサブフェーズを確認

3. **必須ドキュメントを読み込む**
   - `docs/internal/01_REQUIREMENT_MANAGEMENT.md` を精読
   - `docs/internal/02_DEVELOPMENT_FLOW.md` の Phase 1 を精読
   - `docs/internal/06_DECISION_MAKING.md`（3 Agents Model）を確認

4. **PLANNINGルールを適用**
   - **コード生成は禁止**（実装コード、テストコード共に）
   - 成果物は `.md` 形式のみ
   - 出力先: `docs/specs/`, `docs/adr/`, `docs/tasks/`

5. **作業の進め方**
   - 要件が曖昧な場合は `requirement-analyst` サブエージェントを推奨
   - 設計検討には `design-architect` サブエージェントを推奨
   - 重要な決定には 3 Agents Model（Affirmative/Critical/Mediator）を適用

## サブフェーズと承認ゲート

```
requirements → [承認] → design → [承認] → tasks → [承認] → BUILDING へ
```

**承認ルール**:
- 各サブフェーズの成果物完成時、ユーザーに承認を求める
- ユーザーが「承認」と言うまで次のサブフェーズに進まない
- 承認されたら状態ファイルを更新する

**承認要求メッセージ例**:
```
[要件定義] が完了しました。

成果物: docs/specs/<feature>/requirements.md

確認後「承認」と入力してください。
修正が必要な場合は指示してください。
```

**承認時の状態更新**:
```json
{
  "status": { "requirements": "approved" },
  "approvals": { "requirements": "2025-12-09T10:00:00Z" }
}
```

## 禁止事項

- `src/` ディレクトリへのファイル作成・編集
- `.ts`, `.js`, `.py`, `.go` 等の実装コード生成
- テストコードの実装（テスト観点の列挙は可）
- **前サブフェーズが未承認のまま次に進むこと**

## フェーズ終了条件

以下を満たしたら `/building` でBUILDINGフェーズに移行:

- [ ] requirements が approved
- [ ] design が approved
- [ ] tasks が approved
- [ ] `docs/specs/` に仕様書が存在する

## 確認メッセージ

以下を表示してユーザーに確認:

```
[PLANNING] フェーズを開始しました。

適用ルール:
- コード生成: 禁止
- 成果物形式: .md のみ
- 出力先: docs/specs/, docs/adr/, docs/tasks/
- 承認ゲート: 各サブフェーズ完了時に承認が必要

現在の状態:
- 機能: [機能名 or 未設定]
- サブフェーズ: [requirements/design/tasks]

何を検討しますか？
```
