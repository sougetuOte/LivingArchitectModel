# 自動生成ルール

このディレクトリには、TDD 内省パイプライン v2 によって自動生成されたルールが配置される。

## ライフサイクル

```
1. PostToolUse hook がテスト結果（JUnit XML）を読み取り、
   FAIL→PASS 遷移を .claude/tdd-patterns.log に記録
   （FAIL→PASS 遷移時に systemMessage で /retro を推奨）

2. /retro 実行時（人間が判断）に tdd-patterns.log を分析
   → 同一パターンが閾値（初期値: 2回）以上出現する場合
   → draft-NNN.md としてルール候補を提案

3. PM級として人間に承認要求
   → 承認: このディレクトリに配置
   → 却下: draft を削除

4. ルール寿命管理
   → 90日以上未使用のルールを /quick-save (Daily記録) で棚卸し通知
   → 削除は PM級（人間承認必須）
```

## ファイル命名規則

- `draft-NNN.md`: 承認待ちルール候補
- `rule-NNN.md`: 承認済みルール
- `trust-model.md`: 信頼度モデルの定義

## 権限等級

- このディレクトリ配下のファイル追加・変更: **PM級**（人間承認必須）
- パターン記録（`.claude/tdd-patterns.log`）: **PG級**（自動記録）

## 参照

- 仕様書: `docs/specs/tdd-introspection-v2.md`
- 信頼度モデル: `trust-model.md`（本ディレクトリ内）
- テスト結果ルール: `.claude/rules/test-result-output.md`
- パターン詳細記録先: `docs/artifacts/tdd-patterns/`
- パターンログ: `.claude/tdd-patterns.log`
- ルール候補: `.claude/rules/auto-generated/draft-*.md`
