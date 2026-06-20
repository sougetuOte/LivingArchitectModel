# Current Phase

**PLANNING**

_B-5: b4-dashboard（可視化レイヤー）の要件定義準備フェーズ。前マイルストーン B-4 Wave 1+1.5 完了（2026-06-20）を受けて、次マイルストーン骨子の着手順序が MAGI 合議で確定（⑤[今回]→⑥→①→②→③）。サブフェーズ: requirements 起草準備（着手日 2026-06-20）。Wave 1 では PLANNING 標準ガードレール（コード生成禁止 / `src/` 変更禁止 / 設定ファイル変更禁止 / 未承認での次サブフェーズ開始禁止）を継承し、`docs/specs/` `docs/adr/` `docs/tasks/` `docs/artifacts/` への出力と既存コード読取のみ許可する。承認ゲート: requirements → [承認] → design → [承認] → tasks → [承認] → BUILDING。体制: Opus=判断・PM 整理 / Sonnet=起草・編集 / Haiku=突合。_

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
