# doc-writer 実装仕様

**バージョン**: 1.0
**作成日**: 2026-03-08
**対応タスク**: T3-3 (Wave 3: ドキュメント自動追従)
**対応設計書**: docs/design/v4.0.0-immune-system-design.md Section 7

---

## 1. 概要

doc-writer エージェントは、ソースコードの変更に追従してドキュメントの更新案を自動生成する。MVP では `/ship` コマンドの Phase 2 から呼び出される。

## 2. 動作モード

| モード | トリガー | 説明 |
|--------|---------|------|
| **Doc Sync モード** | `/ship` Phase 2 | src/ 変更時にドキュメント更新案を生成 |
| **仕様策定モード** | lam-orchestrate 経由 | 方針から詳細仕様を策定 |
| **通常モード** | 直接呼び出し | ドキュメントの清書・更新 |

## 3. Doc Sync モード詳細

### 3.1 入力仕様

| 入力 | 形式 | 取得元 |
|------|------|--------|
| 変更ファイルパス | 1行1パス（PROJECT_ROOT からの相対パス） | `.claude/doc-sync-flag` |
| 変更差分 | unified diff | `git diff` |

### 3.2 対応 spec ファイルの特定

以下の優先順で対応する仕様書を特定する:

1. **ファイル名パターン**: `src/auth/` → `docs/specs/auth-*.md`
2. **ディレクトリ名**: `src/models/` → `docs/specs/*-model*.md`
3. **import 解析**: 変更ファイルが依存するモジュールの仕様書
4. **フォールバック**: 該当なしの場合、「対応する仕様書なし」と報告

### 3.3 変更分類

| 変更種別 | 仕様書更新 | 理由 |
|---------|-----------|------|
| 公開 API 変更 | 必須 | インターフェース契約の変更 |
| 新機能追加 | 必須 | 仕様書に項目追加が必要 |
| 内部リファクタリング | 任意 | 公開 API 不変なら仕様に影響なし |
| バグ修正 | 場合による | 仕様の誤りが原因なら仕様も修正 |

### 3.4 出力仕様

差分形式で更新案を生成し、ユーザーに提示する。

### 3.5 ADR 起票連携

PM級の設計判断を検出した場合:

1. 変更内容が「アーキテクチャ変更」「技術選定」に該当するか判定
2. 該当する場合、「ADR を起票しますか？」とユーザーに提案
3. 承認時は `adr-template` スキルを適用し、変更内容をコンテキストとして渡す

## 4. `/ship` との連携フロー

```
/ship Phase 1 (棚卸し)
  ↓
/ship Phase 2 (Doc Sync チェック)
  → .claude/doc-sync-flag を参照
  → 変更ファイルを PG/SE/PM に分類
  → SE/PM級あり → doc-writer を Doc Sync モードで呼び出し
  → 更新案をユーザーに提示
  → 承認/スキップ後、doc-sync-flag を削除
  ↓
/ship Phase 3 (グループ分け)
```

## 5. PostToolUse hook との連携

PostToolUse hook が `src/` 配下の Edit/Write を検出し、`.claude/doc-sync-flag` にパスを記録する。

- 重複防止: `grep -qFx` で既存パスをチェック（T3-1 で実装済み）
- フラグクリア: `/ship` Phase 2 完了時に削除

## 6. 権限等級

| 操作 | 等級 |
|------|------|
| 更新案の生成 | SE級 |
| ドキュメント更新適用（docs/ 配下、specs/adr 以外） | SE級 |
| 仕様書更新適用（docs/specs/ 配下） | PM級 |
| ADR 更新適用（docs/adr/ 配下） | PM級 |
| ADR 起票 | PM級 |

## 7. 完全実装（将来）

MVP での `/ship` 時トリガーに加え、PostToolUse hook から即時起動するモードを追加予定:

- PostToolUse hook が変更検出 → doc-writer を非同期で呼び出し
- バッファリング: 短時間の連続変更をまとめて処理
- ユーザーへの通知: 更新案が準備できたことを通知

## 参照

- 設計書: Section 7 (Wave 3: ドキュメント自動追従)
- エージェント定義: `.claude/agents/doc-writer.md`
- フラグファイル: `.claude/doc-sync-flag`
- `/ship` コマンド: `.claude/commands/ship.md`
