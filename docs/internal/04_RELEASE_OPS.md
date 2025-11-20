# Release Operations & Emergency Protocols

本ドキュメントは、**Phase 4 (デプロイ・運用)** におけるプロトコルを定義する。
開発された機能が安全にユーザーの手元に届き、安定稼働するためのルールである。

## 1. Deployment Criteria (デプロイ基準)

本番環境へのデプロイは、以下の条件を全て満たした場合のみ許可される。

- [ ] **All Tests Green**: 全ての自動テストが通過している。
- [ ] **No Critical Bugs**: 優先度 High 以上の既知のバグが存在しない。
- [ ] **Performance Check**: 応答速度やリソース消費が許容範囲内である。
- [ ] **Documentation Updated**: 変更内容が `CHANGELOG.md` およびユーザーマニュアルに反映されている。

## 2. Release Flow (リリースフロー)

1.  **Staging Verification**: ステージング環境での動作確認。
2.  **Backup**: DB および重要データのバックアップ取得。
3.  **Deploy**: 本番環境への適用（Blue/Green または Canary 推奨）。
4.  **Smoke Test**: 主要機能が動作することの簡易確認。

## 3. Emergency Protocols (緊急対応プロトコル)

障害発生時は、以下の手順で対応する。**「止血」を最優先**とする。

### Level 1: Minor Issue (軽微なバグ)

- 次回リリースでの修正を目指す。
- 必要に応じて Hotfix を作成し、レビューを経て適用する。

### Level 2: Critical Incident (サービス停止・データ破損)

1.  **Rollback**: 直ちに直前の安定バージョンへ切り戻す。原因究明はその後に行う。
2.  **Announcement**: ユーザーへ障害発生と状況を通知する。
3.  **Post-Mortem**: 事後分析を行い、再発防止策を `docs/adr/` に記録する。

## 4. Versioning Strategy (バージョニング)

- **Semantic Versioning (SemVer)** に従う。
  - `MAJOR`: 破壊的変更
  - `MINOR`: 後方互換性のある機能追加
  - `PATCH`: 後方互換性のあるバグ修正
