# Green State 定義書

**バージョン**: 1.1
**作成日**: 2026-03-08
**フェーズ**: BUILDING / Wave 0
**対応仕様**:
- 要件定義書: Section 5.0, P5-FR-1
- 設計書: Section 4.1 (Green State 定義)
- KPI定義書: `docs/specs/evaluation-kpi.md`
- ループログスキーマ: `docs/specs/loop-log-schema.md`

---

## 1. 概要

Green State とは、自動ループが「品質基準を満たした」と判定し、正常収束するための条件セットである。Stop hook がこの条件を評価し、全条件を満たした場合にループを停止させる。

**核心原則: Green State は「スキャンして Issue がゼロ」の状態である。「修正後にゼロ」ではない。**

あるイテレーションで Issue を全件修正しても、それは Green State ではない。次のイテレーションで再スキャン（Phase 1）を実行し、**新規 Issue が 0件** であって初めて Green State が確定する。この原則により、修正の副作用で生まれた問題が見逃されることを防ぐ。

---

## 2. Green State 5条件

| # | 条件 | MVP | 完全実装 | 判定方法 |
|---|------|-----|---------|---------|
| G1 | テスト全パス | ○ | ○ | テストフレームワークの exit code == 0 |
| G2 | lint 全パス | ○ | ○ | lint ツールの exit code == 0（設定がある場合） |
| G3 | 対応可能Issue全解決 | - | ○ | quality-auditor の出力パース + deferred ルール |
| G4 | 仕様差分ゼロ | - | ○ | 仕様ドリフト検知（quality-auditor による docs/specs/ と実装の照合） |
| G5 | セキュリティチェック通過 | ○ | ○ | 依存脆弱性 + シークレットスキャン + 危険パターン検出 |

### 2.1 MVP での Green State

MVP では G1 + G2 + G5 の3条件を自動判定する。G3, G4 は完全実装で段階的に追加する。

---

## 3. 各条件の判定方法

### 3.1 G1: テスト全パス

**判定方法**: テストフレームワークを実行し、exit code が 0 であること。

**テストフレームワークの自動検出**（未解決事項 #1 対応）:

| 検出順序 | 検出条件 | 実行コマンド |
|---------|---------|-------------|
| 1 | `pyproject.toml` に `[tool.pytest]` または `pytest` 依存 | `pytest` |
| 2 | `package.json` に `"test"` スクリプト | `npm test` |
| 3 | `go.mod` が存在 | `go test ./...` |
| 4 | `Makefile` に `test` ターゲット | `make test` |
| 5 | 上記いずれもなし | G1 を PASS 扱い（テスト基盤なし、警告ログを出力） |

**timeout**: 各テストコマンドに個別の timeout を設定する（デフォルト: 120秒）。hooks 全体の 600s timeout 内に収まるようにする。

**テスト数減少の定義**: 前サイクルのテスト実行結果と比較し、テスト数（test count）が減少した場合をエスカレーション条件とする。

- テスト数の取得方法: テストフレームワークの出力をパースする
  - pytest: `X passed` の X を抽出
  - npm test (jest): `Tests: X passed` の X を抽出
  - go test: `ok` 行の数をカウント
- **エスカレーション**: テスト数減少を検出した場合、「テスト統合の可能性」を併記して人間に判断を委ねる

### 3.2 G2: lint 全パス

**判定方法**: lint ツールを実行し、exit code が 0 であること。

**lint ツールの自動検出**（未解決事項 #2 対応）:

| 検出順序 | 検出条件 | 実行コマンド |
|---------|---------|-------------|
| 1 | `pyproject.toml` に `[tool.ruff]` または `ruff` 依存 | `ruff check .` |
| 2 | `package.json` に `"lint"` スクリプト | `npm run lint` |
| 3 | `.eslintrc*` が存在 | `npx eslint .` |
| 4 | `Makefile` に `lint` ターゲット | `make lint` |
| 5 | 上記いずれもなし | G2 を PASS 扱い（lint 基盤なし、警告ログを出力） |

**timeout**: デフォルト 60秒。

### 3.3 G3: 対応可能Issue全解決（完全実装）

**G3 の定義（v1.2 更新: 再定義済み）**:

旧定義「Critical Issue 0件」を拡張し、「当該フェーズで対応可能な Issue が全て解決済み」とする。

| 重要度 | Green State 条件 |
|--------|-----------------|
| Critical | 0件（必須） |
| Warning | 0件（必須）。PG/SE級は修正済み。PM級は「理由付き保留（deferred）」としてログ記録（deferred は件数に含めない） |
| Info | **Green State を阻害しない**。件数にかかわらず監査通過。対応は任意 |

**核心ルール**: Critical と Warning の「放置」は禁止。Warning の残存 Issue は全て修正済みまたは `deferred` + 理由が記録されている状態を Green State とする。Info は対応不要（`code-quality-guideline.md` 参照）。

**PG/SE/PM 等級定義との整合**: 権限等級の判定は `permission-levels.md`（TASK 1-1）に準拠する。G3 は権限等級システムに依存するため、完全実装は Wave 1 完了後に着手する。

### 3.4 G4: 仕様差分ゼロ（完全実装）

**判定方法**: quality-auditor が `docs/specs/` と実装コードの整合性を検証し、差分がないことを確認する。

**完全実装時期**: Wave 3（ドキュメント自動追従）完了後に段階的に導入。

### 3.5 G5: セキュリティチェック通過

**判定方法**: 依存脆弱性チェック + シークレットスキャン + 危険パターン検出を実行し、Critical/High の問題がないこと。

**チェック項目**:

| チェック | ツール例 | 判定基準 |
|:---|:---|:---|
| 依存脆弱性 | `npm audit` / `pip audit` / `safety check` | Critical/High 脆弱性ゼロ |
| シークレット漏洩 | `grep` パターンマッチ | API キー・パスワード等のハードコードなし |
| 危険パターン | OWASP Top 10 チェック | eval/exec、SQL文字列結合、pickle.load 等なし |

**ツール未インストール時**: PASS（スキップ）扱いとし、ログに記録する。

**timeout**: デフォルト 60秒。

---

## 4. 理由付き保留（deferred）フォーマット

### 4.1 フォーマット定義

ループログの `deferred_items` 配列に以下の形式で記録する:

```json
{
  "issue": "Warning: 関数 foo() の cyclomatic complexity が閾値超過",
  "reason": "PM級のリファクタリングが必要。Wave 3 スコープで対応予定",
  "level": "warning"
}
```

### 4.2 テキスト形式（MVP）

```
deferred: [issue内容] — 理由: [保留理由]
```

### 4.3 典型的な保留理由

| パターン | 例 |
|---------|-----|
| 権限等級による保留 | `deferred: PM級のため承認待ち` |
| スコープ外 | `deferred: Wave 3 スコープ` |
| 設計判断が必要 | `deferred: アーキテクチャ決定が必要（ADR 起票推奨）` |
| 外部依存 | `deferred: 外部ライブラリのアップデート待ち` |

### 4.4 禁止パターン

以下は deferred として認められない:

- 理由なしの保留（`deferred:` のみ、理由が空）
- 「後で対応」のような曖昧な理由
- PG級の Issue に対する保留（PG級は自動修正すべき）

---

## 5. Green State 判定フロー

```
Stop hook 発火
  │
  ├─ G1: テスト実行
  │   ├─ FAIL → 継続（block）
  │   └─ PASS ─┐
  │             │
  ├─ G2: lint 実行
  │   ├─ FAIL → 継続（block）
  │   └─ PASS ─┐
  │             │
  ├─ [完全実装] G3: Issue 解決チェック
  │   ├─ 未解決 Issue あり（deferred 以外） → 継続（block）
  │   └─ 全解決 or deferred 済み ─┐
  │                               │
  ├─ [完全実装] G4: 仕様差分チェック
  │   ├─ 差分あり → 継続（block）
  │   └─ 差分なし ─┐
  │                │
  ├─ G5: セキュリティチェック
  │   ├─ Critical/High 脆弱性あり → 継続（block）
  │   └─ PASS ─┐
  │             │
  └─ Green State 達成 → フルスキャン実行
      ├─ 新規 Issue あり → 追加サイクル（block）
      └─ 新規 Issue なし → 完了（exit 0）
```

---

## 6. 完全実装スケジュール

| 条件 | 実装時期 | 前提条件 |
|------|---------|---------|
| G1 (テスト) | Wave 2 (TASK 2-2) | テストFW自動検出ロジック |
| G2 (lint) | Wave 2 (TASK 2-2) | lint ツール自動検出ロジック |
| G3 (Issue解決) | Wave 2 完了後 | 権限等級システム (Wave 1), quality-auditor の PG/SE/PM 分類出力 |
| G4 (仕様差分) | Wave 3 完了後 | ドキュメント自動追従, 仕様ドリフト検知 |
| G5 (セキュリティ) | Wave 2 (TASK 2-2) | 依存脆弱性チェック, シークレットスキャン |

---

*本文書は BUILDING フェーズ Wave 0 にて作成されました。*
*更新日: 2026-03-15（v1.1: G3 条件更新 — Info 非阻害、`code-quality-guideline.md` 準拠）*
