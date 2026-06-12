---
name: project_gd_smoke_w1t3
description: B-3 W1-T3 スモークテスト準備フェーズの実装知見（スタブ定義 + 静的 pytest）
metadata:
  type: project
---

W1-T3 スモークテスト準備（2026-06-13）の実装パターン。

**Why:** エージェントレジストリは「セッション開始時スナップショット」のため、スタブ定義の作成と実機実行は別セッションに分離しなければならない。本セッションは「準備物の作成」に専念し、実機実行は次セッション（PM が /goal-driven を打つ）で行う。

**How to apply:** 同様のスタブ分離パターンを使う場合、以下の 4 成果物を作成する:
1. `.claude/agents/gd-smoke-l3-stub.md` — tools: Bash, Read / model: haiku / 固定成功 JSON（design §7）
2. `.claude/agents/gd-smoke-grader-stub.md` — tools: Read のみ / model: haiku / 固定合格 JSON（design §11）
3. `.claude/hooks/tests/test_gd_smoke_stubs.py` — ファイル存在 / tools に Agent なし / model: haiku / name == ファイル名 / 固定 JSON が json.loads 可能かつ必須フィールド充足
4. `docs/artifacts/goal-driven-demo/smoke-test-runbook.md` — 次セッション実行手順書

**固定 JSON 抽出ロジック:** ```json ... ``` ブロックを regex で抽出し json.loads で検証。先頭の有効な JSON を使う方式。既存の _parse_frontmatter/_tools_contains_agent パターンを再利用（[[project_gd_agent_w2t1]] 参照）。

**テストが Bash なしで完結:** 静的 pytest（ファイル読み取りのみ）のため Bash ツール権限なしに全テストが書けた。

**gd_state.py の l1_tokens に関する重要事実**: gd_state.py（W2-T2 実装済み）が管理するのは `total_tokens`（全エージェント累積）であり、`l1_tokens`（L1 指揮者単体）は管理対象外フィールド。W1-T3 完了条件の「l1_tokens 記録」は Claude Code 使用量表示からの手動追記が必要（gd_state.py では代替できない）。

**runbook 作成時の落とし穴（2026-06-13 修正済み）**: W2-T2/W2-T3 の実装状況を実際に git log で確認せずに「未実装」と書いてしまった。スクリプトの存在・CLI 仕様は必ず Read ツールで確認してから runbook に記載すること。

**W1-T3 完了条件の区分:**
- 本セッション充足: スタブ 2 定義作成 / 静的テスト作成 / runbook 作成
- 次セッション持ち越し: 実機実行 / ログ保存 / l1_tokens 記録 / README 記載
