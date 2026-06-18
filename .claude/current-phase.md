# Current Phase

**AUDITING**

_B-4: v5 統一階層フレームワーク構想の入り口として、骨子 ④「fat 化監査 + 削減リファクタ」の監査フェーズに着手。MAGI 合議結論（2026-06-19）に基づき以下の順序・形式で監査する: ④KPI ログ項目仕分け → ②distill-lessons skip 機構 → ③/full-review Phase 数削減 → ①MAGI Reflection 廃止 or 統合。各候補は Standard 深度（分類 + 数値根拠 + 削減プラン）で監査し、`docs/artifacts/v5-fat-audit-2026-06-19.md` に集約。削減基準マトリクスは「使用頻度 × 失敗時影響」（v5 構想 ④）。AUDITING は監査・PG/SE 修正のみで PM 級は指摘止め。承認後に PLANNING へ切替えて削減 spec を起草する。体制: Fable=判断・査定・PM 整理のみ / Sonnet=実機監査・grep / Haiku=事実突合・集計。_

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
