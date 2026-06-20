# Current Phase

**BUILDING**

_B-5: b4-dashboard BUILDING Step Wave 1 完了状態を維持（Wave 2 着手判断待ち）。ADR-0006「Loop Engineering 観点からの LAM 構成再評価と統一語彙」起票完了（commit `5e95a9e`）。BUILDING ガードレール継承: 仕様確認必須 / TDD サイクル厳守（Red→Green→Refactor）/ ドキュメント同期。次の選択肢: Wave 2 着手 / docs 同期（UQ-3 反映）/ AUDITING 切替 / 別 Milestone 起案。体制: Fable=判断 / Sonnet=実装・編集 / Haiku=突合・採点。_

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
