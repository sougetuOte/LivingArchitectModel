# Current Phase

**AUDITING**

_B-1: 本セッション変更分（A-1 env allowlist DRY / A-2 通知B W-9 / A-3 `file_path_to_module_name` の base 集約）＋ card_generator 分割モジュール（graph.scc / analysis.impact）の Green State 確定再確認。B-2（LAM 全体 full-review）とは切り分け、対象を限定。モデル: Opus 4.8 (1M context)._

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
