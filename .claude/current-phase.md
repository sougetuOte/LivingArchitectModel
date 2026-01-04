# Current Phase

**PLANNING**

_要件定義・設計・タスク分解フェーズ_

---

## 状態管理について

このファイルは現在のフェーズを記録するための状態ファイルです。

### フェーズ値
- `PLANNING` - 要件定義・設計・タスク分解フェーズ
- `BUILDING` - TDD実装フェーズ
- `AUDITING` - レビュー・監査・リファクタリングフェーズ

### 更新タイミング
- `/planning` コマンド実行時 → `PLANNING`
- `/building` コマンド実行時 → `BUILDING`
- `/auditing` コマンド実行時 → `AUDITING`

### 参照するルール
- `rules/phase-planning.md` - PLANNINGフェーズのガードレール
- `rules/phase-building.md` - BUILDINGフェーズのガードレール
- `rules/phase-auditing.md` - AUDITINGフェーズのガードレール
