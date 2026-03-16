# Scalable Code Review Phase 5 要件仕様書（Plan E: ハイブリッド統合）

**バージョン**: 1.0
**作成日**: 2026-03-16
**ステータス**: draft
**前提**: Plan A〜D 実装完了（396テスト PASSED、Green State 達成）
**親仕様**: `docs/specs/scalable-code-review-spec.md` FR-8
**設計ノート**: `docs/tasks/scalable-code-review-tasks.md` Plan E 設計ノート

---

## 1. 目的

Plan A〜D で段階的に追加された Scalable Code Review の各コンポーネントを
統一的な Stage 体系に再編し、プロジェクト規模に応じた自動スケール判定と
エンドツーエンド品質検証を実現する。

### Problem Statement

現行の `/full-review` は Plan A〜D の追加により Phase 番号が 11 段階
（0, 0.3, 1, 1.5, 1.7, 2, 2.5, 3, 4, 5, 6）に肥大化している。
歴史的経緯で追加された中間 Phase が多く、以下の問題がある:

- **認知負荷**: フロー全体を把握しづらい（AI にとっても人間にとっても）
- **スケール判定の分散**: Plan ごとの有効化判定がバラバラに実装されている
- **E2E 検証の欠如**: データフローの自動テストはあるが、LLM 出力を含む全体品質の検証手段がない

### 解決後の理想状態

- full-review.md が 5+1 段階の Stage 体系で構造化されている
- プロジェクト規模に応じて Plan の有効化が自動判定される
- E2E テストで Issue 検出精度を定量的に検証できる

---

## 2. 機能要件

### FR-E1: Stage 体系への再編

full-review.md の Phase 構造を以下の Stage 体系に再編する。

| Stage | 内容 | 統合元 Phase | Python コード変更 |
|:------|:-----|:-------------|:-----------------|
| Stage 0 | 初期化（ループ状態、context7 検出） | Phase 1, 1.5 | なし |
| Stage 1 | 静的分析 + 依存グラフ構築 | Phase 0, 0.3 | なし |
| Stage 2 | チャンク分割 + トポロジカル順レビュー | Phase 1.7, 2 | なし |
| Stage 3 | 階層的統合 + レポート生成 | Phase 2.5, 3 | なし |
| Stage 4 | トポロジカル順修正 | Phase 4 | なし |
| Stage 5 | 検証 + Green State 判定 + 完了 | Phase 5, 6 | なし |

#### FR-E1a: Stage 体系の制約

- **Python コード変更禁止**: Plan A〜D で構築した Python 関数群は変更しない。再編は full-review.md のドキュメント再構成のみ
- **Stage 番号の安定性**: Stage 0〜5 の番号体系は Plan E 以降で変更しない（MUST）
- **後方互換**: 小規模プロジェクト（~10K行）では Stage 1〜3 がスキップされ、現行動作と同一になること（NFR-2 維持）

#### FR-E1b: Stage 間のデータフロー明示

各 Stage の入力・出力を明確に定義し、full-review.md に記述する。

| Stage | 入力 | 出力 |
|:------|:-----|:-----|
| Stage 0 | 対象パス | `lam-loop-state.json` |
| Stage 1 | 対象パス、`review-config.json` | `static-issues.json`, `ast-map.json`, `dependency-graph.json`, `summary.md` |
| Stage 2 | `chunks.json`, `dependency-graph.json`, 上流契約カード | `chunk-results/`, 契約フィールド、責務フィールド |
| Stage 3 | `file-cards/`, `module-cards/`, `contracts/`, `layer3-issues.json` | 統合レポート（`audit-reports/`） |
| Stage 4 | 統合レポート、`dependency-graph.json` | 修正済みコード |
| Stage 5 | テスト結果、lint 結果 | Green State 判定、ループログ |

### FR-E2: 自動スケール判定

プロジェクト規模と環境条件に基づき、有効化する Plan を自動判定する。

#### FR-E2a: 行数ベース閾値テーブル

| 行数 | 推奨 Plan セット | Stage 動作 |
|:-----|:----------------|:-----------|
| ~10K | なし（現行 full-review） | Stage 0 → Stage 2（従来モード） → Stage 3〜5 |
| 10K-30K | Plan A（提案） | Stage 0 → Stage 1（提案） → Stage 2 → Stage 3〜5 |
| 30K-100K | Plan A + B | Stage 0 → Stage 1（自動） → Stage 2（チャンクモード） → Stage 3〜5 |
| 100K-300K | Plan A + B + C | 全 Stage 自動 |
| 300K+ | Plan A + B + C + D | 全 Stage 自動（トポロジカル順） |

#### FR-E2b: Plan 固有の前提条件チェック

行数テーブルで有効化が判定された後、各 Plan の前提条件を個別にチェックする。

| Plan | 前提条件 | 未充足時の動作 |
|:-----|:---------|:-------------|
| Plan A | ruff, bandit がインストール済み | Warning 表示 + Plan A スキップ |
| Plan B | tree-sitter がインストール済み | Warning 表示 + 従来のファイル全体レビューにフォールバック |
| Plan C | Stage 2 の概要カードが生成済み | （Plan B が有効なら自動的に満たされる） |
| Plan D | `import-map.json` が生成済み | Warning 表示 + トポロジカル順をスキップし従来のバッチ順 |

#### FR-E2c: 判定結果の出力

Stage 0 の初期化時に、以下の形式で判定結果を表示する（MUST）:

```
=== Scale Detection ===
Lines: 45,230
Recommended: Plan A + B + C
Active Plans:
  Plan A: ✓ (ruff: installed, bandit: installed)
  Plan B: ✓ (tree-sitter: installed)
  Plan C: ✓ (auto)
  Plan D: ✗ (import-map.json not found — skipping topological ordering)
```

#### FR-E2d: 判定ロジックの実装場所

`scale_detector.py`（新規）に判定ロジックを集約する（MUST）。
full-review.md からは Stage 0 で `scale_detector.py` を呼び出し、
その結果に基づいて後続 Stage の動作を制御する。

### FR-E3: エンドツーエンドテスト

Plan A〜D パイプライン全体の品質を検証するテストフレームワーク。

#### FR-E3a: テスト責務の棲み分け

| レイヤー | 担当 | 検証内容 | 決定性 |
|:---------|:-----|:---------|:-------|
| データフロー | D-5 `test_integration_pipeline.py`（既存） | 関数チェーンの入出力整合 | 決定的（pytest） |
| 品質・精度 | E-3 `test_e2e_review.py`（新規） | Issue 検出精度、Green State 到達 | 非決定的（LLM 依存） |

#### FR-E3b: テストシナリオ

1. **検出率テスト**: 既知の Issue を仕込んだテストコードに対して `/full-review` を実行し、検出率を測定
   - テストフィクスチャ: `.claude/hooks/analyzers/tests/fixtures/e2e/` に配置
   - 仕込む Issue 種別: Critical（Silent Failure）、Warning（Long Function）、Security（ハードコードパスワード）
   - 検出率の目標値: Critical 100%、Warning 80%以上（非決定的テストのため MUST 基準ではなく改善トリガーとして扱う）
2. **収束テスト**: LAM 自体に対して `/full-review` を実行し、max_iterations 以内に Green State に到達することを確認
3. **スケール判定テスト**: 異なる行数のプロジェクトで `scale_detector.py` が正しい Plan セットを返すことを検証（決定的、pytest）

#### FR-E3c: 非決定的テストの扱い

LLM 出力に依存するテスト（FR-E3b の 1, 2）は以下のルールで管理する:
- CI/CD には組み込まない（実行コストと非決定性のため）
- `/retro` またはリリース前の手動実行として位置づける
- 結果は `docs/artifacts/e2e-results/` に記録する
- 検出率が SHOULD 基準を下回った場合、プロンプト改善の Issue を起票する

---

## 3. 非機能要件

### NFR-E1: Python コード変更の最小化

Plan E の主要成果物は full-review.md の再構成である。
新規 Python ファイルは `scale_detector.py` と `test_e2e_review.py` に限定する（MUST）。
Plan A〜D の既存関数群は修正してはならない（MUST NOT）。

### NFR-E2: 段階的検証

Stage 体系の再編後、以下の順序で検証する:
1. 既存テスト（396件）が全 PASSED であること
2. `scale_detector.py` の単体テストが PASSED であること
3. LAM 自体に対する `/full-review` が Green State に到達すること（手動）

### NFR-E3: ドキュメント整合性

full-review.md の再編に合わせて以下のドキュメントも更新する:
- `docs/design/scalable-code-review-design.md` Section 6（Plan E）
- `docs/tasks/scalable-code-review-tasks.md` Phase 5 セクション
- `docs/specs/scalable-code-review-spec.md` FR-8 / Section 5

---

## 4. スコープ外（Non-Goals）

- `/auditing` や CI/CD パイプラインへの統合（Plan F 以降）
- プロンプトテンプレートの変更（Stage 再編に伴うセクション見出しの統合・改番のみを許容し、指示文・プロンプト内容の変更は禁止）
- Plan A〜D の Python コードの変更・リファクタリング
- `_find_sccs` の反復実装化（既知制限、別途対応）
- `import_map` 生成ロジックの新規実装（Phase A のアーキテクチャ判断として据え置き）

---

## 5. 成功基準

| 基準 | 計測方法 |
|:-----|:--------|
| full-review.md が Stage 体系で構成されている | Stage 0〜5 のセクションが存在し、中間 Phase 番号がないこと |
| 自動スケール判定が動作する | `scale_detector.py` の単体テストで ~10K / 30K / 100K / 300K の各閾値が正しく判定されること |
| 前提条件チェックが動作する | `scale_detector.py` のテストで ruff/bandit/tree-sitter 未インストール時に Warning が表示され、対応 Plan がスキップされること |
| E2E テストフレームワークが存在する | `test_e2e_review.py` が実行可能で、テストフィクスチャ（Critical/Warning/Security の3種）が `.claude/hooks/analyzers/tests/fixtures/e2e/` に配置されていること |
| 既存テストが全 PASSED | 396+ テスト全 PASSED |
| NFR-2 後方互換 | ~10K 行のプロジェクトで `scale_detector.py` が Plan セット「なし」を返し、Stage 1〜3 をスキップするログが出力されること |

---

## 6. 参照

- 親仕様: `docs/specs/scalable-code-review-spec.md`
- 設計書: `docs/design/scalable-code-review-design.md`
- Plan E 設計ノート: `docs/tasks/scalable-code-review-tasks.md` Phase 5 セクション
- D-5 統合チェーンテスト: `.claude/hooks/analyzers/tests/test_integration_pipeline.py`
- 現行 full-review: `.claude/commands/full-review.md`
