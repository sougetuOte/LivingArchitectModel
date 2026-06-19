# Current Phase

**PLANNING**

_B-4: v5 fat 削減 spec 起草。MAGI 合議（2026-06-20）で確定したスコープに基づき `docs/specs/v5-fat-reduction/` を単一群として起草する（requirements.md / design.md / tasks.md / future-candidates.md）。連動して `v4.0.0-immune-system-requirements.md` を直接編集し NFR-6/7/8/17 削除 + NFR-14a 再起票（削除箇所 HTML コメント残し）。**スコープ境界**: gabriel 設計・ADR 新設・magi スキル全面改訂は v5 ② 別マイルストーン送り（future-candidates.md で引き継ぎ）。B-4 内では Reflection 警告ラベル温存のみ。承認後 BUILDING へ。体制: Opus=判断・PM 整理 / Sonnet=起草・編集 / Haiku=合否判定・突合。_

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
