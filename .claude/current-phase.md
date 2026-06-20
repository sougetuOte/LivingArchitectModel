# Current Phase

**PLANNING**

_B-5: b4-dashboard BUILDING Step Wave 1 完了（commit `daa50e1`）直後の一時 PLANNING 切替。目的: ADR-XXXX「Loop Engineering 観点からの LAM 構成再評価」起票。切替元の BUILDING Wave 1 成果（commit `daa50e1`）は確定済み。起票完了後、BUILDING Step（Wave 2 以降）へ復帰予定。PLANNING ガードレール継承: コード生成禁止 / `src/` 変更禁止 / 設定ファイル変更禁止。承認ゲート: ADR 起票完了 → [承認] → BUILDING 復帰。体制: Fable=判断 / Sonnet=起票・編集 / Haiku=（本タスクでは不使用）。_

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
