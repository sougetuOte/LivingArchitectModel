# Current Phase

**BUILDING**

_B-3: ゴール駆動オーケストレーション・スキルの TDD 実装。仕様: `docs/specs/goal-driven-orchestration/{requirements(v1.2.0),design(v0.3.0),tasks(v1.1.0)}.md`（2026-06-12 ユーザー承認済）。W0-T1（Spike: OQ-1 /goal サブエージェント内動作の実測）から着手。クリティカルパス W0-T1 → W1-T1 → W1-T3 を 6/22 までに完走（無償期間内 L1 実機テスト必須）。体制: Fable=判断・査定のみ / Sonnet=実行 / Haiku=事実突合。_

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
