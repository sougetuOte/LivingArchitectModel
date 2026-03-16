# フェーズ別ガードレール

## PLANNING

### 承認ゲート

```
requirements → [承認] → design → [承認] → tasks → [承認] → BUILDING
```

成果物完成時は必ず「承認」を求める。ユーザーが「承認」と言うまで次へ進まない。

### 品質基準

成果物は `.claude/rules/planning-quality-guideline.md` に準拠すること:
- 仕様書: Requirements Smells 検出 + RFC 2119 キーワード統一
- 設計書: Design Doc チェックリスト（非スコープ・代替案・成功基準）
- タスク: SPIDR 分割 + WBS 100% Rule（仕様⇔タスクのトレーサビリティ）
- 明確化: Example Mapping（`/clarify` 併用）

### 禁止

- 実装コード生成（.ts, .py, .go 等）
- `src/` への変更
- 設定ファイル変更（package.json, pyproject.toml 等）
- 未承認での次サブフェーズ開始

### 許可

- `docs/specs/`, `docs/adr/`, `docs/tasks/`, `docs/artifacts/` への出力
- 既存コード読取（仕様策定のため）、Mermaid 図表作成
- `.claude/states/*.json` の更新

---

## BUILDING

### 必須

- 実装前に `docs/specs/` を確認
- TDD サイクル厳守（Red → Green → Refactor）
- コード変更時はドキュメント同期
- 1サイクル完了ごとにユーザーに報告

### TDD 品質チェック

- [ ] R-1: 仕様突合 — FR/設計仕様のフィールド名・定数名と実装が文字単位で一致
- [ ] R-4: テスト網羅 — 各 FR/要件に対応するテストが存在する
- [ ] R-5: テスト名と入力値の一致 — テスト名に含まれる数値・条件と、実際のテスト入力値が一致していること（例: `test_10k_boundary` なら入力は 10,000）
- [ ] R-6: 設計書出力ファイルからのアサーション生成 — 設計書に「ファイル X を生成する」と記載された出力は、Red ステップで `assert path.is_file()` を書くこと

### 仕様同期ルール

- S-1: Green 直後に対応する `docs/specs/` を確認し、実装と仕様の乖離がないか検証
- S-3: 仕様書の未実装項目には Phase/Wave マークを付与（暗黙スキップ禁止）
- S-4: Refactor で公開 API/インターフェースが変わった場合、仕様書を即時更新

### TDD 内省パイプライン v2

PostToolUse hook がテスト結果（JUnit XML）を読み取り、FAIL→PASS 遷移を自動記録する。
`/retro` 実行時に人間がパターン分析を行い、同一パターンが閾値（2回）以上出現する場合にルール候補を提案する。

- パターン記録: `.claude/tdd-patterns.log`（自動、PG級）
- パターン詳細: `docs/artifacts/tdd-patterns/`
- ルール候補: `.claude/rules/auto-generated/draft-*.md`（PM級で起票・承認）
- パターン分析: `/retro` Step 2.5
- 審査コマンド: `/pattern-review`

詳細: `.claude/rules/auto-generated/trust-model.md`

### 禁止

- 仕様書なし実装
- テストなし実装
- ドキュメント未更新

---

## AUDITING

### AUDITING での修正ルール（v4.0.0）

権限等級（`.claude/rules/permission-levels.md`）に基づく修正制御:

- **PG級の修正**: 許可（自動修正可。フォーマット、typo、lint 違反等）
- **SE級の修正**: 許可（修正後に報告。テスト追加、内部リファクタリング等）
- **PM級の修正**: 禁止（指摘のみ、承認ゲート。仕様変更、ルール変更等）

> v3.x からの変更: 従来は「修正の直接実施禁止」だったが、v4.0.0 で PG/SE 級の修正を許可に緩和。

### 必須

- チェックリストに基づく網羅的確認
- 重要度分類: Critical / Warning / Info（判断基準は `.claude/rules/code-quality-guideline.md` に準拠）
- 3 Agents Model 適用、根拠明示
- 問題の PG/SE/PM 分類（権限等級に基づく）

### コード品質チェック

- [ ] 命名が意図を表現している
- [ ] 単一責任原則を守っている
- [ ] エラーケースが網羅されている

### コード明確性チェック

- [ ] ネストした三項演算子がない
- [ ] 過度に密なワンライナーがない
- [ ] デバッグ・拡張が容易な構造

### ドキュメント・アーキテクチャ

- [ ] 仕様と実装の差異がない
- [ ] ADR 決定事項が反映されている
- [ ] 循環依存がない
- [ ] TODO/FIXME の棚卸し

### 改善提案の禁止事項

- 読みやすさを犠牲にした行数削減
- 有用な抽象化の削除
- 複数の関心事を1関数に統合
- デバッグ困難な「賢い」コード提案
- 主観的な好みに基づく指摘

### Green State 条件

```
Critical = 0 かつ Warning = 0 → Green State（監査通過）
```

Info は件数にかかわらず Green State を阻害しない。
詳細な判断基準は `.claude/rules/code-quality-guideline.md` を参照。

### レポート形式

```
# 監査レポート
対象: [ファイル/ディレクトリ]
Critical: X件 / Warning: X件 / Info: X件
総合評価: [A/B/C/D]
```

---

## フェーズ警告テンプレート

フェーズルールに反する要求を受けた場合:

```
⚠️ フェーズ警告: 現在は [PHASE] フェーズです。
1. ルールに沿って続行
2. フェーズ切替（/planning, /building, /auditing）
3. 「承知の上で続行」と明示
```
