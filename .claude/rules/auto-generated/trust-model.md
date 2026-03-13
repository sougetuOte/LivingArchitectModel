# 信頼度モデル

TDD 内省パイプライン v2 において、テスト失敗パターンからルール候補を生成するための信頼度モデル。

## データソース

PostToolUse hook が `.claude/test-results.xml`（JUnit XML）を読み取り、
テスト成否を `.claude/tdd-patterns.log` に記録する。

v1 では `tool_response.exitCode` を使用していたが、Claude Code の PostToolUse 入力に
exitCode が存在しないため動作していなかった（2026-03-13 判明）。

## 観測と分析のフロー

```
テスト実行 → JUnit XML 出力
    ↓
PostToolUse hook → tdd-patterns.log に FAIL/PASS 記録
    ↓
FAIL→PASS 遷移時 → systemMessage で /retro 推奨（通知A）
    ↓
/retro 実行（人間が判断）→ Step 2.5 でパターン分析
    ↓
頻出パターン（2回以上）→ ルール候補を draft-NNN.md として提案
    ↓
人間が承認/却下（PM級）
```

## 閾値

| 条件 | アクション |
|------|-----------|
| FAIL→PASS 遷移 | `tdd-patterns.log` に自動記録（PG級） |
| 同一パターン 2回以上 | `/retro` でルール候補を提案（PM級） |

**初期閾値: 2回**。v1 の3回から引き下げ。`/retro` が人間実行であり誤爆リスクが低いため。

## パターン照合ロジック

`/retro` の Step 2.5 で実施:

1. `tdd-patterns.log` から最終 `ANALYZED` マーカー以降のエントリを抽出
2. FAIL→PASS ペアを構成（同一テストフレームワーク、時系列順）
3. 失敗テスト名の一致で同一パターンを特定
4. 2回以上出現するパターンをルール候補として提案

## ルール候補のフォーマット

```markdown
# Draft Rule: [ルール名]

**生成日**: YYYY-MM-DD
**観測回数**: N
**ステータス**: draft | approved | rejected

## 根拠パターン

| # | 日付 | テスト名 | 失敗内容 |
|---|------|---------|---------|
| 1 | YYYY-MM-DD | test_xxx | [要約] |
| 2 | YYYY-MM-DD | test_xxx | [要約] |

## 推奨ルール

[ルール文: 「XXX のような変更を行う際は YYY に注意すること」]

## 適用範囲

- 対象ファイルパターン: `src/**/*.py`
- 対象操作: [Edit/Write]
```

## ルール寿命管理

- 各承認済みルールに `last_matched` 日付をメタデータとして記録（ISO 8601形式）
- `/quick-save` の Daily 記録時に 90 日以上未使用のルールを棚卸し対象として通知
- ルール削除は **PM級**（人間承認必須）

## 権限等級

- 信頼度モデル自体の変更: **PM級**
- パターン記録の追加: **PG級**（PostToolUse hook が自動記録）
- ルール候補の生成・承認・却下: **PM級**（`/retro` 内で人間が判断）

## 参照

- 仕様書: `docs/specs/tdd-introspection-v2.md`
- テスト結果ルール: `.claude/rules/test-result-output.md`
- パターンログ: `.claude/tdd-patterns.log`
- ルール候補: `.claude/rules/auto-generated/draft-*.md`
