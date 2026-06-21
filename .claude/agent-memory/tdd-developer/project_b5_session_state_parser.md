---
name: project_b5_session_state_parser
description: B-5 W2-B5-T7 SessionStateParser 実装 — タスクID regex・セクション分割・UQ-1 実データ対応パターン
metadata:
  type: project
---

## B-5 W2-B5-T7: SessionStateParser 実装（2026-06-21 完了）

**実装ファイル**: `.claude/scripts/dashboard/parsers/session_state.py`（214行）
**テストファイル**: `.claude/tests/dashboard/test_session_state_parser.py`（26ケース・全PASS）

**Why:** SESSION_STATE.md から Milestone/Wave/タスク状態を抽出し、V-2 Milestone 一覧ビューのデータを供給するため。

**How to apply:** 次パーサ（CurrentPhaseParser / TasksParser 等）実装時のパターン参照。

### 重要な実装知見

#### タスク ID の regex パターン（UQ-1 Spike 解決）

SESSION_STATE.md 内のタスク ID 形式は `W1-B5-T1`（Milestone 部分はハイフンなし `B5`）。
仕様書の表記 `B-5` とは異なるので変換が必要。

```python
# 正しいパターン
_TASK_ID_RE = re.compile(r"W(\d+(?:\.\d+)?)-([A-Z])(\d+)-T(\d+)")
# B5 → B-5 変換
milestone = f"{m.group(2)}-{m.group(3)}"
```

誤りパターン（使用禁止）:
```python
# これはマッチしない
re.compile(r"W(\d+)-([A-Z]-\d+)-T\d+")  # B-5 はタスクID内には存在しない
```

#### 「なし（...）」行の除外

進行中タスクが「- なし（Wave 1 完了...）」と書かれる場合がある。
`content.startswith("なし")` で前方一致除外する（完全一致だと「なし。」「なし（...）」を取りこぼす）。

#### テーブル行からも Milestone 抽出可能

`_extract_task_ids_from_text` はファイル全体に対して regex 適用するため、
`| W1-B5-T1 | ... |` のようなテーブル行も自動的にキャプチャされる。

#### セクション分割（## / ### 両対応）

`re.compile(r"^#{2,3}\s+(.+)$", re.MULTILINE)` で ## と ### を統一処理。
完了タスクに `(本セッション)` や英語 `completed` が付く見出しバリエーションに対応した判定関数を実装済み。
