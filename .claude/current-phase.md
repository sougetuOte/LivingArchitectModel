# Current Phase

**BUILDING**

_hooks 残課題の TDD 消化。A-1: テスト env allowlist の重複（conftest / test_e2e_review の `_ENV_ALLOWLIST`）を正本 `_hook_utils.CHECKER_ENV_ALLOWLIST` へ DRY 統合。A-2: Stop hook 通知B（W-9・未分析 TDD パターンの /retro 推奨）を `_save_loop_log` funnel に実装。700 passed / ruff clean。モデル: Opus 4.8 (1M context)._

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
