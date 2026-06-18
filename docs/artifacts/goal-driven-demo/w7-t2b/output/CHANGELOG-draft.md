# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

- 今後追加予定の機能をここに記載する

### Changed

- 今後変更予定の内容をここに記載する

---

## [0.1.0] - 2026-06-18

### Added

- goal-driven オーケストレーション三層構成（L1-orchestrator / l2-foreman / l3-executor）の初期実装
- large ルート（工程数 3 / 並列度 2）の基本動作デモを追加
- `metadata.json` 生成工程（工程 1）: プロジェクトメタデータの構造化出力
- `README-draft.md` 生成工程（工程 2）: プロジェクト概要ドキュメントの自動生成
- `CHANGELOG-draft.md` 生成工程（工程 3）: 変更履歴ファイルの自動生成
- rubric.md による受入条件定義（AC-1 〜 AC-7 の 7 項目）
- grader サブエージェントによる機械的品質検証の基盤を追加
- Keep a Changelog 形式への準拠を確認するための雛形出力機能
- UTF-8 エンコーディング保証と 50 行以上の出力長チェック
- 出力ディレクトリを `docs/artifacts/goal-driven-demo/w7-t2b/output/` に固定する制約
- サブディレクトリ作成禁止制約の実装
- タスクスラッグ `w7-t2b-large-route-demo` に対応した工程ルーティング

### Changed

- 初回リリースのため変更履歴なし

### Deprecated

- 初回リリースのため廃止予定項目なし

### Removed

- 初回リリースのため削除項目なし

### Fixed

- 初回リリースのため修正項目なし

### Security

- 初回リリースのためセキュリティ修正なし
- 出力先ディレクトリをプロジェクト内の所定パスに限定し、任意パスへの書き込みを禁止
- ファイル生成時の文字コードを UTF-8 に統一し、文字化けリスクを排除

---

## 参考情報

### プロジェクト概要

- **プロジェクト名**: lam-demo-app
- **説明**: LAM 大タスク経路検証用デモ
- **バージョン**: 0.1.0
- **ライセンス**: MIT
- **ステータス**: experimental (alpha)
- **言語**: Japanese (ja)

### タスク情報

- **タスク ID**: gd-20260618-001
- **タスクスラッグ**: w7-t2b-large-route-demo
- **経路種別**: large（L1 → l2-foreman → l3-executor 三層）
- **並列度**: 2
- **工程数**: 3

### リポジトリ

- **URL**: https://github.com/example/lam-demo-app
- **バグ報告**: https://github.com/example/lam-demo-app/issues

### 動作環境

- Node.js: >= 18.0.0
- Python: >= 3.10

---

[Unreleased]: https://github.com/example/lam-demo-app/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/example/lam-demo-app/releases/tag/v0.1.0
