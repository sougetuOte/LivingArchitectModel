# Current Phase

**BUILDING**

_⑤ card_generator 2モジュール分割（scalable-code-review）。Critical 解消（C-1: SccDetectionSkippedError 契約 / C-2: 反復 Tarjan）＋ Warning 解消（W2-4 deque / W-4 nonlocal / iter2-Info 逆引き辞書 / I-2 specs_dir.glob 再帰化）＋ グラフ解析（L799-1090）/ 影響範囲分析（L1093-1305）モジュール切り出し。モデル: Opus 4.7 (1M context)._

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
