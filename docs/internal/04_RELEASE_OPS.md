# Release Operations & Emergency Protocols

本ドキュメントは、**Phase 4 (デプロイ・運用)** におけるプロトコルを定義する。
開発された機能が安全にユーザーの手元に届き、安定稼働するためのルールである。

## 1. Deployment Criteria (デプロイ基準)

本番環境へのデプロイは、以下の条件を全て満たした場合のみ許可される。

- [ ] **All Tests Green**: 全ての自動テストが通過している。
- [ ] **No Critical Bugs**: 優先度 High 以上の既知のバグが存在しない。
- [ ] **Quality Gate Passed**: プロジェクトが定めるリリース品質基準を満たしている（例: 監査 Green、パフォーマンス基準、セキュリティスキャン等。基準はプロジェクトごとに定義）。
- [ ] **Documentation Updated**: 変更内容が `CHANGELOG.md` およびユーザーマニュアルに反映されている。
- [ ] **Retrospective Done**: `/retro` による振り返りが実施済みである。

## 2. Release Flow (リリースフロー)

1.  **Verification**: リリース対象の動作確認。プロジェクトの性質に応じた検証を実施する（例: テストスイート実行、手動確認、ステージング環境検証等）。
2.  **Backup**: 必要に応じ、リリース前の状態を保全する（例: git tag、データバックアップ等）。
3.  **Release**: リリースの実施。プロジェクトの配布形態に応じた手順に従う（例: パッケージ公開、デプロイ、タグ作成等）。
4.  **Post-Release Check**: リリース後の簡易確認。

## 3. Emergency Protocols (緊急対応プロトコル)

障害発生時は、以下の手順で対応する。**「止血」を最優先**とする。

### Level 1: Minor Issue (軽微なバグ)

- 次回リリースでの修正を目指す。
- 必要に応じて Hotfix を作成し、レビューを経て適用する。

### Level 2: Critical Incident (サービス停止・データ破損)

1.  **Rollback**: 直ちに直前の安定バージョンへ切り戻す。原因究明はその後に行う。
2.  **Announcement**: ユーザーへ障害発生と状況を通知する。
3.  **Post-Mortem**: 事後分析を行い、`docs/artifacts/` に記録する。アーキテクチャ判断が伴う場合は `docs/adr/` にも ADR を起票する。

## 4. Versioning Strategy (バージョニング)

- **Semantic Versioning (SemVer)** に従う。
  - `MAJOR`: 破壊的変更
  - `MINOR`: 後方互換性のある機能追加
  - `PATCH`: 後方互換性のあるバグ修正、ドキュメント修正、内部改善
