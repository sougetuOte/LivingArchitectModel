---
name: project-gd-distill-w4t1
description: B-3 W4-T1 distill-lessons.py 実装（メモリ蒸留 FR-5）完了。スクリプト分割・argparse・design §13 スキーマ準拠テスト 21 件
metadata:
  type: project
---

## B-3 W4-T1: distill-lessons.py 実装（メモリ蒸留 FR-5）

**完了日**: 2026-06-13

### 実装ファイル

- `.claude/scripts/distill_lessons.py` — 実装本体（Python モジュール）
- `.claude/scripts/distill-lessons.py` — SKILL.md フロー[8] 呼び出し用エントリポイント（ハイフン形式）
- `.claude/hooks/tests/test_distill_lessons.py` — TDD テスト 21 件
- `.claude/agent-memory/goal-driven-l3-executor/` — 作成（lessons.md 書き込み先ディレクトリ）

### 主要設計判断

- `distill-lessons.py`（ハイフン）と `distill_lessons.py`（アンダースコア）の 2 ファイル構成
  - SKILL.md フロー[8] の呼び出し形式（ハイフン）に合わせ、ラッパーを作成
  - モジュール本体はアンダースコア（Python 命名規約）

- `verified=None` の自動判定ロジック: fail→pass 遷移の有無で検証済み/未検証を自動判定
  - pass のみ → 未検証（一般則が確立できない）
  - fail→pass あり → 検証済み

- 重複スキップ: 同一 task_id のエントリは追記しない（idempotency）

### W-5 制約の実装

`docs/artifacts/knowledge/` への書き込みコードが存在しない。
実行時テスト（`test_distill_does_not_write_to_knowledge_dir`）でも確認済み。

### テスト構成（21 件）

- `TestLessonsEntryFormat` (4件) — design §13 スキーマ準拠
- `TestDistillVerified` (3件) — 書き込み先・フォーマット
- `TestDistillUnverified` (3件) — 未検証タグ・自動判定
- `TestSmallTaskRoute` (2件) — design §9.1 小タスクルート
- `TestNoKnowledgeDirWrite` (2件) — W-5 制約
- `TestArgparseInterface` (4件) — SKILL.md フロー[8] インターフェース
- `TestMultipleGraderLogs` (2件) — 複数ループ
- `TestIdempotency` (1件) — 重複スキップ

### SKILL.md 更新

- 実装ステータス表の W4-T1 行を「**完了**」に更新
- フロー[8] に API 参照（`distill()` / `build_lesson_entry()` / `build_arg_parser()`）を追記

**Why:** W4-T1 は FR-5 メモリ蒸留の具現化。教訓の書き込みを自動化しつつ、
精査は人間（/retro Step 4）に委ねる設計が CLAUDE.md Memory Policy と整合する。

**How to apply:** 次セッションで W4-T2（コスト集計）を実装する際は、
gd_loop.py の `tokens_used` 累積と `distill()` の呼び出しが連携することを確認する。
