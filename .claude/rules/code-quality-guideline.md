# Code Quality Guideline — 重要度分類と判断基準

BUILDING（予防）と AUDITING（検出）の両フェーズで適用する、言語非依存の品質判断基準。

## 三層モデル

```
Layer 1: ツール領域（formatter/linter が担当 → LAM 監査対象外）
Layer 2: 構造領域（Code Smells / Complexity → LAM 監査の主戦場）
Layer 3: 設計領域（アーキテクチャ整合 / 仕様乖離 → LAM 固有の価値）
```

## 重要度分類

### Critical（必須修正 — blocking）

修正しなければマージ不可。バグ・セキュリティ・データ損失リスク。

- **Error Swallowing / Silent Failure**: エラーの握りつぶし・黙殺。空の catch、`except: pass`、エラーを log して処理続行、失敗を `None`/`null` で返し呼び出し側が検知不能、等
- セキュリティ脆弱性（注入、認証バイパス、秘密情報の露出）
- データ損失・破損の可能性
- 仕様との明確な不一致（ロジックバグ）
- 競合状態・並行性バグ

### Warning（修正推奨 — non-blocking）

改善すべきだが、修正しなくても動作に問題はない。

- **Cognitive Complexity > 15**（関数単位）
- **SRP 違反**: 1つのクラス/関数に複数の責務
- **Code Smells**: Feature Envy, Shotgun Surgery, God Class/Method
- **Deep Nesting > 3階層**
- **Long Function > 50行**（03_QUALITY_STANDARDS.md「30-50行を目安」の上限を採用）
- **Parameter Explosion > 4引数**
- **Duplication > 3回**（Rule of Three）
- **Dead Code / Unreachable Branch**: 使われていない関数・変数、到達不能な分岐（上流で既にバリデーション済みの再チェック等）。lint が拾う未使用 import とは別に、ロジック上到達しない経路が対象
- **テストが存在しない新規ロジック**: BUILDING フェーズの TDD ルール違反でもあるが、保守困難性の観点で Warning
- 不明瞭な命名（意図が読み取れないもの）
- 不足しているエッジケースのテスト

### Info（参考情報 — non-blocking, 修正不要で Green State）

改善の余地はあるが、現時点で対応不要。修正しなくても監査は通過する。

- 命名の微改善（動くし読めるが、より良い名前がある）
- コメントの追加提案
- 「自分ならこう書く」レベルの代替案
- 将来的なリファクタリング候補
- テストのアサーション追加提案（主要パスはカバー済み）

## Green State の Issue 条件

```
Critical = 0 かつ Warning = 0 → Issue 観点で Green State（監査通過）
```

Info は件数にかかわらず Green State を阻害しない。

> 本ガイドラインは Green State 5条件のうち **G3（Issue 解決）** の判定基準を定める。
> G1（テスト）、G2（lint）、G4（仕様差分）、G5（セキュリティ）は
> `docs/specs/green-state-definition.md`（SSOT）を参照。

## 判断に迷った場合

### フローチャート

```
この指摘がないとバグになるか？ → Yes → Critical
                                → No ↓
この指摘がないと保守が困難になるか？ → Yes → Warning
                                      → No ↓
Info（または指摘しない）
```

### アンチパターン（指摘してはならない）

- **Bikeshedding**: formatter/linter で解決すべきスタイル議論
- **Style Policing**: 動くし読めるコードへの好み押し付け
- **過剰な抽象化要求**: 1箇所でしか使わないコードの共通化提案
- **読みやすさを犠牲にした行数削減**（03_QUALITY_STANDARDS.md 禁止事項）

### モジュール間帰責判断

複数モジュールにまたがる Issue で、修正責任が曖昧な場合の判断基準。
`/full-review` の Stage 3 レポートおよび Stage 4 修正時に適用する。

#### フローチャート

```
モジュール間境界に Issue を発見
  │
  ├─ 仕様書（docs/specs/）に該当 API/インターフェースの定義がある？
  │    ├─ Yes → 仕様と乖離している側が修正対象（仕様ドリフト帰責）
  │    └─ No  → 仕様の欠落が根本原因 → PM級（仕様明確化が先決）
  │
  ├─ 上流モジュールの契約カードと下流の呼び出しに矛盾がある？
  │    ├─ 下流が契約違反 → 下流モジュールを修正
  │    └─ 上流の契約自体が不十分/不正確 → 上流の契約（≒仕様）を更新 → PM級
  │
  └─ 単体では問題なく、組み合わせで初めて顕在化する？
       → 上流の Green State は「単体での Green State」であり、結合時の再審査で
         Issue が出ることは正常動作
       → 修正は「変更コストが小さい側」に寄せる（Postel's Law 的判断）
       → 判断が困難な場合は PM級にエスカレーション
```

#### 帰責の分類

| 分類 | 意味 | 対応 |
|------|------|------|
| upstream | 上流モジュールの契約/実装に問題 | 上流を修正 |
| downstream | 下流モジュールが契約に違反 | 下流を修正 |
| spec_ambiguity | 仕様の欠落/曖昧さが根本原因 | PM級（仕様明確化が先決） |
| unknown | 判断不能 | PM級にエスカレーション |

## BUILDING フェーズでの適用

実装時は Critical/Warning に該当するコードを **書かない** ことを目指す。
TDD サイクルの Refactor ステップで以下を確認:

1. Cognitive Complexity が 15 を超えていないか
2. 関数が 50 行を超えていないか
3. ネストが 3 階層を超えていないか

## AUDITING フェーズでの適用

監査レポートの各指摘に重要度ラベルを必ず付与する:

```
[Critical] 未処理の例外: func_x() の catch ブロックが空
[Warning]  Cognitive Complexity 22: process_data() の分割を推奨
[Info]     命名改善案: data → parsed_records
```

## 根拠

- Google Engineering Practices: 重要度ラベル体系（Required/Nit/Optional/FYI）
- Conventional Comments: 構造化レビューコメント
- Martin Fowler: Code Smells（24の匂い）
- SonarSource: Cognitive Complexity（計測可能メトリクス）
- Microsoft Research: 「コードレビューの主な価値は設計改善」
- SOLID 原則（特に SRP）

## 権限等級

本ルールファイルの変更: **PM級**
