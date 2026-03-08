# 自動生成ルール

このディレクトリには、TDD 内省パイプライン（Wave 4）によって自動生成されたルールが配置される。

## ライフサイクル

```
1. PostToolUse hook がテスト失敗→成功パターンを検出
   → .claude/tdd-patterns.log に記録

2. パターンが閾値（初期値: 3回）に到達
   → draft-NNN.md としてルール候補を生成

3. PM級として人間に承認要求
   → 承認: このディレクトリに配置
   → 却下: draft を削除

4. ルール寿命管理（完全実装）
   → 90日以上未使用のルールを /daily で棚卸し通知
   → 削除は PM級（人間承認必須）
```

## ファイル命名規則

- `draft-NNN.md`: 承認待ちルール候補
- `rule-NNN.md`: 承認済みルール
- `trust-model.md`: 信頼度モデルの定義（T4-2 で作成）

## 権限等級

- このディレクトリ配下のファイル追加・変更: **PM級**（人間承認必須）
- パターン記録（`.claude/tdd-patterns.log`）: **PG級**（自動記録）

## 参照

- 設計書: Section 8 (Wave 4: TDD 内省)
- パターン記録先: `docs/memos/tdd-patterns/`
- パターンログ: `.claude/tdd-patterns.log`
