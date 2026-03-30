# モジュール間帰責判断 タスク定義

**バージョン**: 0.2
**対応仕様**: `docs/specs/cross-module-blame-spec.md`
**対応設計**: `docs/design/cross-module-blame-design.md`

---

## Wave 1（全タスク）

依存関係:

```
T1（独立、並列可能）
T2 → T3 → T4 → T5 → T6
```

T1 は PM 級承認ゲートだが、T2〜T6 とは機能的依存がないため並列実行可能。

### T1: 帰責判断フローチャート追加（FR-1）

- **対象**: `.claude/rules/code-quality-guideline.md`
- **内容**: 「判断に迷った場合」セクションの後に「モジュール間帰責判断」セクションを追加
  - フローチャート（仕様 → 契約 → 組み合わせの 3 段階判断）
  - 帰責分類テーブル（upstream / downstream / spec_ambiguity / unknown）
- **権限等級**: PM（承認ゲート）
- **完了条件**: AC-1
- **依存**: なし

### T2: `parse_blame_hint()` 実装 + テスト（FR-2c）

- **対象**: `.claude/hooks/analyzers/card_generator.py`
- **内容**:
  - マーカー定数 `_BLAME_START`, `_BLAME_END`, `_BLAME_FIELDS` 追加
  - `BlameHint` 型エイリアス定義
  - `parse_blame_hint()` 関数追加（設計書 Section 2.4 準拠）
- **テスト**: `.claude/hooks/analyzers/tests/test_card_generator.py` に 7 ケース追加
  - 正常: 単一マーカー（→ AC-3） / 複数マーカー（→ AC-3）
  - 正常（縮退動作）: 部分フィールドのみ（`issue` と `reason` だけ等。抽出されたフィールドのみで有効な `BlameHint` を返す）
  - フォールバック: マーカーなし（→ AC-4） / 閉じマーカーなし（→ AC-5） / 空コンテンツ（→ AC-5）
  - 共存: CONTRACT-CARD + BLAME-HINT が同一 Agent 出力内に存在する場合、`parse_contract()` と `parse_blame_hint()` が互いに干渉せず独立に動作すること
- **権限等級**: SE
- **完了条件**: AC-3, AC-4, AC-5, AC-12
- **依存**: なし

### T3: プロンプト拡張（FR-2a）

- **対象**: `.claude/hooks/analyzers/orchestrator.py`
- **内容**: `build_review_prompt_with_contracts()` の header に帰責判断ガイド + BLAME-HINT マーカー指示を追加（設計書 Section 2.2 準拠）
- **テスト**: `.claude/hooks/analyzers/tests/test_orchestrator.py` に 3 ケース追加
  - 契約カードあり → 帰責ガイドが含まれる（→ AC-2）
  - 契約カードなし → 帰責指示なし、従来通り（→ AC-10）
  - トークン数上限チェック: 追加テキストの文字数/4 が 200 以下（→ AC-9）
- **権限等級**: SE
- **完了条件**: AC-2, AC-9, AC-10
- **依存**: T2（マーカー定数 `_BLAME_START` 等を `card_generator.py` から参照するため）

### T4: Agent 定義更新（FR-2b）

- **対象**: `.claude/agents/quality-auditor.md`, `.claude/agents/code-reviewer.md`
- **内容**: レビュー観点セクションに「モジュール間帰責」項目を 1 つ追加（設計書 Section 2.3 準拠）
- **権限等級**: SE
- **完了条件**: AC-10（帰責マーカーなし出力でのフォールバック動作が T3 のテストで検証済みであること。T4 は Agent 定義の記載確認）
- **依存**: T3（プロンプト側の指示と整合させるため）

### T5: `/full-review` レポート形式拡張（FR-3, FR-4）

- **対象**: `.claude/commands/full-review.md`
- **内容**:
  - Stage 2 Step 3: `parse_blame_hint()` 呼び出し手順を追加 + **帰責ヒントと Issue ID の紐付けロジック**を記載
  - Stage 3 Step 5: Issue 表示に `** 帰責判断求む **` マーカー形式を追加（FR-3a）
  - Stage 3 Step 5: レポート末尾に帰責サマリーテーブル形式を追加（FR-3b、帰責 Issue 1 件以上の場合のみ）
  - Stage 4: `spec_ambiguity` の自動修正スキップガード + `upstream`/`downstream` の修正確認プロンプト（PG 級除く）を追加（FR-4）
- **権限等級**: SE
- **完了条件**: AC-6, AC-7, AC-8, AC-11
- **依存**: T2, T3, T4

### T6: 回帰テスト + 仕様同期確認

- **内容**:
  - 既存テスト全パス確認（435 件、特に `parse_contract()` の既存テストが回帰していないこと）
  - 仕様書・設計書の未実装項目がないことを確認
  - `docs/design/scalable-code-review-design.md` にクロスリファレンスを追加（本機能の存在を記載。新規仕様追加ではなくドキュメント保守として SE 級）
- **権限等級**: SE
- **完了条件**: 全テストパス、仕様⇔実装の差分ゼロ
- **依存**: T5

---

## トレーサビリティマトリクス

| 仕様 | タスク | AC |
|------|--------|-----|
| FR-1 | T1 | AC-1 |
| FR-2a | T3 | AC-2, AC-9 |
| FR-2b | T4 | AC-10 |
| FR-2b-ii（フォールバック） | T3, T4 | AC-10 |
| FR-2c | T2 | AC-3, AC-4, AC-5, AC-12 |
| FR-3a | T5 | AC-6 |
| FR-3b | T5 | AC-7 |
| FR-4 | T5 | AC-8, AC-11 |
| NFR-1 | T6 | 全テストパス（parse_contract 回帰含む） |
| NFR-2 | T3 | AC-9 |
| NFR-3 | T2 | AC-4, AC-5 |

全 FR/NFR にタスクが対応。孤児タスクなし。
