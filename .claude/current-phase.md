# Current Phase

**BUILDING**

_B-4 Wave 1: v5 fat 削減リファクタ実装フェーズ。PLANNING spec（`docs/specs/v5-fat-reduction/`）承認済み・WBS 100% / Green State 確認済み（2026-06-20）。Wave 1 スコープ: §1 NFR cleanup（`v4.0.0-immune-system-requirements.md` の NFR-6/7/8/17 削除 + NFR-14a 再起票）、§2 distill-lessons（lessons-learned 抽出・docs 整理）、§4 MAGI 警告ラベル温存（Reflection セクションへの no-op マーカー追記確認）。**スコープ境界**: gabriel 設計・ADR 新設・magi スキル全面改訂は v5 ② 別マイルストーン（future-candidates.md で引き継ぎ）。体制: Opus=判断・PM 整理 / Sonnet=実装・編集 / Haiku=突合。_

---

## 状態管理について

このファイルは現在のフェーズを記録するための状態ファイルです。

### フェーズ値
- `PLANNING` - 要件定義・設計・タスク分解フェーズ
- `BUILDING` - TDD実装フェーズ
- `AUDITING` - レビュー・監査・リファクタリングフェーズ
- `AUTONOMOUS` - 自律統治モード（対象 spec を Green State まで自律実装。FR-9 統治ファイル deny が有効化）

### 更新タイミング
- `/planning` コマンド実行時 → `PLANNING`
- `/building` コマンド実行時 → `BUILDING`
- `/auditing` コマンド実行時 → `AUDITING`
- `/autonomous <spec_target>` 実行・承認時 → `AUTONOMOUS`

### 参照するルール
- `.claude/rules/phase-rules.md` - フェーズ別ガードレール（PLANNING/BUILDING/AUDITING）
- `AUTONOMOUS` の駆動・制約: `.claude/skills/autonomous/SKILL.md`（phase-rules への `## AUTONOMOUS` 節追加は T5-2 / Wave 5 予定）
