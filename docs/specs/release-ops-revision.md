# 仕様書: 04_RELEASE_OPS.md 改訂

**ステータス**: approved (2026-03-13)
**対象**: `docs/internal/04_RELEASE_OPS.md`（SSOT）
**分類**: PM級（SSOT 改訂）

## 背景

v4.4.1 監査で発見された3件の Issue に対応する。
現行の `04_RELEASE_OPS.md` は Web サービスを前提とした記述が含まれており、
LAM フレームワークとしての中立性を損なっている。

## 改訂方針

LAM はプロジェクト種別（Web サービス、CLI ツール、ライブラリ、ドキュメント等）に
依存しないフレームワークである。SSOT 文書もこの中立性を維持すべき。

## 改訂項目

### P1: Section 2 (Release Flow) の汎用化

**現状**: Web サービス固有の手順（Staging, DB Backup, Blue/Green, Canary, Smoke Test）

**改訂後**: プロジェクト種別に依存しない汎用リリースフロー

```markdown
## 2. Release Flow (リリースフロー)

1. **Verification**: リリース対象の動作確認。
   - プロジェクトの性質に応じた検証を実施する（例: テストスイート実行、手動確認、ステージング環境検証等）。
2. **Backup**: 必要に応じ、リリース前の状態を保全する（例: git tag、データバックアップ等）。
3. **Release**: リリースの実施。
   - プロジェクトの配布形態に応じた手順に従う（例: パッケージ公開、デプロイ、タグ作成等）。
4. **Post-Release Check**: リリース後の簡易確認。
```

### P2: Section 1 (Deployment Criteria) の Performance Check 見直し

**現状**: `Performance Check: 応答速度やリソース消費が許容範囲内である。`

**改訂後**: Performance Check を汎用的な品質ゲートに置換

```markdown
- [ ] **Quality Gate Passed**: プロジェクトが定めるリリース品質基準を満たしている
  （例: 監査 Green、パフォーマンス基準、セキュリティスキャン等。基準はプロジェクトごとに定義）。
```

### P3: Section 4 (Versioning) の PATCH 定義拡充

**現状**: `PATCH: 後方互換性のあるバグ修正`

**改訂後**:

```markdown
- `PATCH`: 後方互換性のあるバグ修正、ドキュメント修正、内部改善
```

## 変更しない箇所

- Section 3 (Emergency Protocols): 十分に汎用的。変更不要。
- Section 1 の他の項目（All Tests Green, No Critical Bugs, Documentation Updated, Retrospective Done）: 変更不要。

## 影響範囲

- `docs/internal/04_RELEASE_OPS.md` のみ。
- 他の SSOT 文書、実装コード、テストへの影響なし。
- `.claude/commands/release.md` は既に `/retro` 前提チェックを含んでおり、追加変更不要。
