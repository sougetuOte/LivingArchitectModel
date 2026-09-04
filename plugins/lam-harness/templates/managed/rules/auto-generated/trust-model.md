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

## カウント単位

信頼度モデルにおける「同一パターンの発火回数」は **検出イベント単位**で数える。

**検出イベント単位の定義**: 1 つの検証イベント (1 セッション内の /retro 実行 / 1 回の HGA 召喚 / 1 回の監査 Stage / 1 回の gabriel probe 等) 内で検出された複数 issue は、件数によらず **1 カウント**とする。

**データソース** (design §4.2 W-c 反映): 検出イベントは `tdd-patterns.log` の FAIL→PASS 遷移に限らず、以下も含む:

- HGA 召喚 (`docs/artifacts/hga-summon-log.md` 記載の各 #N)
- 監査 Stage (`docs/artifacts/*-audit-*.md` 記載の Stage 単位)
- gabriel probe (`gabriel-metrics.log` 記載の各 probe 実行)

**遡及一貫性**: rule-001 の実績カウント (4 検出イベント: 2026-06-27 / 2026-07-05 / 2026-07-06 / 2026-07-07) は本定義と遡及一貫する (異日付・異セッションが各 1 検出イベント)。

**変更は PM 級**: 検出イベント単位の定義変更は trust-model.md 改訂 = PM 級承認が必要。

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

## N 回目発火時の恒久解検討

同一パターンが **N 回目** (初期値: **N = 3**) の検出イベントで発火した場合、fallback regex の場当たり的拡張ではなく、**構造的な恒久解**の検討を必須化する。

**恒久解の例**: regex 汎化 (特定 prefix → 抽象 pattern 化) / データ構造の変更 / upstream の設計見直し 等。

**具体事例**: `rule-001.md` 「### 拡張の根拠 (2026-07-06 / R-1 W-R1 S1 T6)」節を参照。B-N 専用 regex が Milestone 命名体系変更 (R-1 / S-1 / T-1 …) で 3 回目発火した際、`\b(B-\d+)\b` → `\b([A-Z]-\d+)\b` の regex 汎化を恒久解として実施した実例。

**N の変更は PM 級**: N の値変更は trust-model.md 改訂 = PM 級承認が必要。初期値 3 は rule-001 の実績 (3 回目発火で恒久解実施) と整合する。

## 権限等級

- 信頼度モデル自体の変更: **PM級**
- パターン記録の追加: **PG級**（PostToolUse hook が自動記録）
- ルール候補の生成・承認・却下: **PM級**（`/retro` 内で人間が判断）

## 参照

- 仕様書: `docs/specs/tdd-introspection-v2.md`
- テスト結果ルール: `.claude/rules/test-result-output.md`
- パターンログ: `.claude/tdd-patterns.log`
- ルール候補: `.claude/rules/auto-generated/draft-*.md`
