# Release Notes Staging

リリース時に CHANGELOG / README / docs/slides に反映すべき事項を蓄積する。
`/release` 実行時に本ファイルを参照し、反映後に該当項目を削除する。

---

## 未反映の変更

### Code Quality Guideline（`.claude/rules/code-quality-guideline.md`）

BUILDING・AUDITING 両フェーズで適用する言語非依存の品質判断基準を新設。

- **三層モデル**: ツール領域 / 構造領域 / 設計領域の分離
- **重要度分類**: Critical（必須修正）/ Warning（修正推奨）/ Info（参考、修正不要）
- **Green State 再定義**: `Critical=0 AND Warning=0` で監査通過。Info は阻害しない
- **判断フローチャート**: バグになるか→保守困難か→それ以外は Info
- **アンチパターン明示**: Bikeshedding / Style Policing を名指しで禁止

根拠: Google Engineering Practices, Conventional Comments, Martin Fowler Code Smells, SonarSource Cognitive Complexity, Microsoft Research, SOLID 原則

### Planning Quality Guideline（`.claude/rules/planning-quality-guideline.md`）

PLANNING フェーズの成果物（specs, design, tasks）に適用する品質基準を新設。

- **Requirements Smells**: 仕様書の曖昧な単語を自動検出（危険な単語リスト）
- **RFC 2119 キーワード**: MUST / SHOULD / MAY で義務レベルを統一
- **Design Doc チェックリスト**: 非スコープ・代替案・成功基準の必須化
- **SPIDR タスク分割**: 5軸（Spike/Paths/Interfaces/Data/Rules）での分割パターン
- **WBS 100% Rule**: 仕様⇔タスクのトレーサビリティ検証
- **Example Mapping**: ルール→具体例→未解決質問の構造化（`/clarify` 併用）

根拠: IEEE 830, RFC 2119, Google/Stripe Design Docs, SPIDR, PMI WBS, Cucumber Example Mapping

### 関連ファイル更新

Green State 定義の統一（Info 非阻害）を以下に反映:
- `docs/specs/green-state-definition.md`
- `docs/specs/v4.0.0-immune-system-requirements.md`
- `docs/specs/scalable-code-review-spec.md`
- `.claude/commands/full-review.md`
- `.claude/rules/phase-rules.md`（PLANNING 品質基準参照 + AUDITING Green State 条件）
