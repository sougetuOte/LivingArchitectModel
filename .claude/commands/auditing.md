---
description: "AUDITINGフェーズを開始 - レビュー・リファクタリング・監査"
---

# AUDITINGフェーズ開始

あなたは今から **[AUDITING]** モードに入ります。

## 実行ステップ

1. **フェーズ状態を更新**
   - `.claude/current-phase.md` を `AUDITING` に更新する

2. **状態ファイルを確認**
   - `.claude/states/<feature>.json` を読み込む
   - implementation が approved か確認（BUILDING 完了確認）
   - 状態ファイルの `subPhase` を `review` に更新

3. **必須ドキュメントを読み込む**
   - `docs/internal/03_QUALITY_STANDARDS.md` を精読
   - `docs/internal/02_DEVELOPMENT_FLOW.md` の Phase 3 を確認
   - 監査対象のコードと対応仕様書を読み込む

4. **AUDITINGルールを適用**
   - 品質基準への適合性を検証
   - "Broken Windows" の発見と修復
   - ドキュメントの整合性確認

5. **作業の進め方**
   - 品質監査には `quality-auditor` サブエージェントを推奨
   - 3 Agents Model で改善提案を検証
   - Context Compression が必要な場合は提案

## 監査チェックリスト

### コード品質
- [ ] 命名規則の一貫性
- [ ] エラーハンドリングの適切性
- [ ] パフォーマンス懸念の有無
- [ ] セキュリティリスクの有無

### ドキュメント整合性
- [ ] `docs/specs/` と実装の一致
- [ ] `docs/adr/` の決定事項が反映されている
- [ ] `docs/tasks/` のタスク状態が最新

### アーキテクチャ健全性
- [ ] 依存関係の適切性
- [ ] モジュール境界の明確さ
- [ ] 技術的負債の蓄積状況

## 成果物

監査結果は以下の形式で報告:

```markdown
# 監査レポート: [対象]

## サマリー
- 検出項目数: X件
- Critical: X件 / Warning: X件 / Info: X件

## Critical Issues
### [Issue-1]
- **場所**:
- **内容**:
- **推奨対応**:

## Warnings
...

## Documentation Sync Status
- specs: ✓/✗
- adr: ✓/✗
- tasks: ✓/✗

## 推奨アクション
1.
2.
```

## 監査完了と承認

監査完了時、ユーザーに承認を求める:

```
[監査] が完了しました。

成果物: docs/memos/audit-report-<feature>.md

確認後「承認」と入力してください。
修正が必要な場合は指示してください。
```

承認後、状態ファイルを更新し機能を完了状態にする。

## 確認メッセージ

以下を表示してユーザーに確認:

```
[AUDITING] フェーズを開始しました。

機能: [feature-name]
実装状態: [approved/未承認]

適用ルール:
- 品質基準への適合性検証
- ドキュメント整合性チェック
- 技術的負債の棚卸し

読み込み済み:
- 03_QUALITY_STANDARDS.md
- 02_DEVELOPMENT_FLOW.md (Phase 3)

何を監査しますか？
（対象ファイル/ディレクトリを指定してください）
```
