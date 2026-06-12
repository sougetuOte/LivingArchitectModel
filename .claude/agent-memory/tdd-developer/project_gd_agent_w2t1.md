---
name: project-gd-agent-w2t1
description: B-3 W2-T1 エージェント定義 3 件の実装パターンと完了状況
metadata:
  type: project
---

B-3 W2-T1（goal-driven エージェント定義 3 件）を TDD で完了（2026-06-12）。

**Why:** design §11 の仕様に基づき、フロントマター書式と本文内容の両方を静的 pytest で検証するアプローチを採用。

**How to apply:**
- エージェント定義の静的検証は `_parse_frontmatter()` + `_get_body()` ヘルパーで frontmatter / 本文を分離
- `_tools_contains_agent()` は正規表現で境界チェック（単純な `"Agent" in tools_value` は誤判定の恐れあり）
- test ファイルは `.claude/hooks/tests/test_gd_agent_definitions.py`
- 作成した 3 エージェント: `goal-driven-l2-foreman.md`, `goal-driven-l3-executor.md`, `goal-driven-grader.md`

Links: [[oserror-test-windows]]
