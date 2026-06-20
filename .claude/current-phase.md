# Current Phase

**BUILDING**

_B-5: b4-dashboard（可視化レイヤー）BUILDING Step Wave 1。前 PLANNING Step 完了（commit `e39afd2`、PLANNING 4 本セット: requirements / design / tasks / adr）を受けて、Wave 1 実装（W1-T1〜T5: ビルド骨格 + 最小 HTML + V-1 スケルトン）に着手する。基準文書: `docs/specs/b4-dashboard/` 配下 5 ファイル（不可変）。BUILDING 標準ガードレール継承: 仕様確認必須 / TDD サイクル厳守（Red → Green → Refactor）/ コード変更時ドキュメント同期 / テスト追加必須。承認ゲート: Wave 1 完了 → [承認] → Wave 2。体制: Fable=判断・PM 整理 / Sonnet=実装・編集 / Haiku=突合・採点。_

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
