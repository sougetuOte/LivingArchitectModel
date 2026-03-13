# 権限等級分類基準

v4.0.0 で導入された変更のリスクレベルに応じた三段階分類。
全てのツール操作・ファイル変更はこの等級に基づいて処理される。

## PG級（自動修正・報告不要）

自明な修正。プロジェクトの振る舞いを変えない変更。

- フォーマット修正（prettier, ruff format 等）
- typo 修正
- lint 違反の自動修正（eslint --fix, ruff check --fix 等）
- import 整理
- テスト失敗の自明な修正（型ミスマッチ等）
- 不要な空白・末尾改行の除去

## SE級（修正後に報告）

技術的な判断を含むが、公開 API や仕様に影響しない変更。

- テストの追加・修正
- 内部リファクタリング（公開 API 不変）
- ドキュメントの細部更新（`docs/` 配下、ただし `docs/specs/` と `docs/adr/` を除く）
- 依存パッケージの minor/patch update
- 内部関数の名前変更（外部インターフェース不変）
- ログ出力の追加・修正
- コメントの追加・修正

## PM級（判断を仰ぐ）

プロジェクトの方向性・仕様・アーキテクチャに影響する変更。人間の承認が必須。

- 仕様変更（`docs/specs/` の変更）
- アーキテクチャ変更（`docs/adr/` の変更）
- `.claude/rules/` の追加・変更
- `.claude/settings*.json` の変更
- 公開 API の変更
- 依存パッケージの major update
- フェーズの巻き戻し
- テストの削除
- 機能の削除

## フェーズとの二軸設計

| | PLANNING | BUILDING | AUDITING |
|--|----------|----------|----------|
| PG | - | 自動修正可 | 自動修正可 |
| SE | - | 修正後報告 | 修正後報告 |
| PM | 承認ゲート | 承認ゲート | 承認ゲート |

## ファイルパスベースの分類（PreToolUse hook 用）

| パスパターン | 等級 | 理由 |
|-------------|------|------|
| `docs/specs/*.md` | PM | 仕様変更 |
| `docs/adr/*.md` | PM | アーキテクチャ変更 |
| `.claude/rules/*.md`, `.claude/rules/*/*.md` | PM | ルール変更（サブディレクトリ含む） |
| `.claude/settings*.json` | PM | 設定変更 |
| `docs/` 配下（上記以外） | SE | ドキュメント更新 |
| `src/` 配下 | SE | ソースコード変更（デフォルト） |
| その他 | SE | 安全側に倒す |

## 迷った場合

**SE級に丸める**（安全側に倒す）。

判断に迷う典型例:
- 「テストの大幅な書き換え」→ SE級（公開 API は変わらない）
- 「README の構成変更」→ SE級（仕様書ではない）
- 「.claude/commands/ の変更」→ SE級（ルールではなくコマンド）
- 「package.json の scripts 変更」→ SE級（ビルド設定）
- 「.gitignore の変更」→ SE級

## 参照

- `docs/specs/v4.0.0-immune-system-requirements.md` Section 5.1 (権限等級の原定義)
- `docs/internal/07_SECURITY_AND_AUTOMATION.md` Section 5 (Hooks-Based Permission System)
- `docs/internal/02_DEVELOPMENT_FLOW.md` (フェーズ別の権限適用)
