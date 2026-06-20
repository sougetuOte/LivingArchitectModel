# v5 fat 削減 — 将来候補リスト

作成日: 2026-06-20
根拠: `docs/specs/v5-fat-reduction/requirements.md` §7 / PM 決定 2026-06-19

本ファイルは `requirements.md` の Non-Goals として除外された候補を記録する。
各候補には除外理由と再評価条件を明記する。

---

## FC-1: MAGI v2（gabriel 統合）

- **内容**: gabriel エージェント（出題・決断者）を導入し、現行 Reflection（Step 4）を
  gabriel adversarial probe として機能強化する
- **設計根拠**: ADR-0005 Reflection 追補（2026-05-29）が示した
  「別セッション・独立文脈での検証が 3 catch を発見」パターン。
  Reflection の入力同一問題（Step 3 直後の同一文脈再処理）を構造的に解消する
- **統合方針**:
  - gabriel が Convergence 後に独立文脈で adversarial probe を実行
  - MELCHIOR / BALTHASAR / CASPAR は純調停化
  - AoT 分解は温存（独立機構・実績あり）
- **実施条件**: v5 ② gabriel エージェント設計・ADR 新設・MAGI SKILL.md 全面改訂との同時実施
- **権限等級（将来）**: PM 級（アーキテクチャ変更・ADR 新設）
- **マイルストーン**: v5 ②

---

## FC-2: distill-lessons セマンティック重複チェック

- **内容**: 既存エントリとのテキスト類似度（Jaccard 係数等）を計算し、
  類似度が閾値以上のエントリをスキップする
- **除外理由**: 現状 2 エントリでは過剰投資。実装コストが高く、効果を計測できる段階にない
- **再評価条件**: `lessons.md` エントリが 30 件を超えた時点
- **権限等級（将来）**: SE 級（内部ロジック変更）

---

## FC-3: /full-review Stage 1/3 物理撤去

- **内容**: no-op 確定の 4 Step（Stage 1 Step 3 / Stage 2 Step 1-2 / Stage 3 Step 1/3）を
  SKILL.md から物理削除する
- **除外理由**: Plan B（tree-sitter チャンク分割）/ Plan C（Layer 2/3 階層統合）/
  Plan D（トポロジカル順修正）の復活余地を残すため。現状マーカー追記（commit c674ec8）で認知的負荷は解消済み
- **再評価条件**: Plan B/C/D のいずれかを v5 以降で実装すると決定した時点
- **権限等級（将来）**: PM 級（SKILL.md 仕様変更）

---

## FC-4: /retro Step 4 への lessons.md 確認手順追加

- **内容**: `/retro` Step 4 のチェックリストに
  「lessons.md の未検証エントリを確認し、精査不要なものを削除する」手順を追加する
- **除外理由**: v5 PLANNING フェーズで他の /retro 更新と統合して検討するため後送り（PM 決定）
- **再評価条件**: v5 PLANNING フェーズ開始時
- **権限等級（将来）**: SE 級（SKILL.md 更新）

---

## FC-5: NFR-14a 計測スクリプト実装

- **内容**: フック分類の誤判定率を計測する Python スクリプトを実装し、
  `permission.log` から自動集計してベースラインを確立する
- **除外理由**: 本要件定義（§1 FR-1.5）では NFR-14a の Phase 対象更新のみを行う。
  スクリプト実装は v5 Phase 1 のタスクとして別途起票する
- **実施条件**: v5 Phase 1 BUILDING フェーズ
- **権限等級（将来）**: SE 級（新規スクリプト追加）
