---
name: project-b5-wc-stage2-gabriel
description: B-5 Wave C Stage 2 (WC-B5-T3/T4) gabriel.md subagent + 出力契約テスト実装の要点
metadata:
  type: project
---

B-5 Wave C Stage 2 (2026-07-04) で `.claude/agents/gabriel.md`（MAGI adversarial verifier）と
`.claude/tests/wave_c/test_wave_c_gabriel_output.py`（出力契約テスト 16 件 PASS）を実装した。

**Why**: MAGI Reflection（Step 4）の変更率 0% 実機計測（B-4 監査）を受け、独立 subagent gabriel に
よる adversarial probe へ置き換える設計（ADR-0007）。Stage 2 は gabriel.md 本体 + 出力契約の
mock/fixture ベーステストのみで、MAGI フロー統合（Stage 3 = PM 級 T5/T6）は対象外。

**How to apply**:
- `.claude/tests/wave_c/` 配下は既存 `.claude/tests/dashboard/` と同様 `__init__.py` なしで
  pytest 収集可能（pyproject.toml の pytest 設定確認済 / rootdir 明示なしで動く）
- jsonschema ライブラリは既にインストール済み（4.25.1）。pyproject.toml への追加不要だった
  （pyproject.toml に `[project]` セクション自体が存在せず、テスト専用設定のみ）
- クロスフィールド制約（design.md §3 のテーブル）は JSON schema (draft-07) だけでは
  表現できないため、専用バリデータ関数 `_validate_cross_field_constraints` を用意して
  例外 (CrossFieldConstraintError) を送出する方式にした。Silent Failure 回避のため
  「拒否時は None を返す」ではなく必ず例外を投げる設計
- gabriel.md の system prompt には Spike T2（`.claude/.session-spike-w-c-1.md`）の含意
  「結論でなく前提・根拠を独立再検証せよ」を専用セクションとして明示的に埋め込んだ
  （bias 防御。委譲プロンプト経由でのバイアス漏れ対策）
- gabriel.md フロントマターの YAML パース妥当性は pyyaml で静的検証済み
  （`tools: Read, Glob, Grep` / `model: sonnet` / `memory: project`）

参照: [[project_gd_agent_w2t1]]（frontmatter パーサ静的検証パターンの類似実装）
