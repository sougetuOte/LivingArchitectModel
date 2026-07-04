# magi-v2-gabriel Future Candidates

Wave C（gabriel 統合）のスコープ外だが、将来 Wave / 別 Milestone で対応を検討する候補を記録する。

## FC-1: `.claude/agents/spec-critic.md` (project-local) 化

**発見**: 2026-07-04 Wave C Spike 実施中、tasks.md WC-B5-T3 が「spec-critic.md を参考形式として採用」と記述していたが、`.claude/agents/spec-critic.md` は本プロジェクトに存在しないと判明（project-local には `code-reviewer.md`, `design-architect.md`, `doc-writer.md`, `goal-driven-grader.md`, `goal-driven-l2-foreman.md`, `goal-driven-l3-executor.md`, `quality-auditor.md`, `requirement-analyst.md`, `task-decomposer.md`, `tdd-developer.md`, `test-runner.md` の 11 agent のみ）。

`spec-critic` 自体は Claude Code の global/plugin agent として利用可能（"Adversarial review of specifications, ADRs, and design docs. Plays the 'Critical' role in the Three Agents Model"）だが、project-local .md ファイルとしては未実装。

**課題**:
- LAM の Three Agents Model（`decision-making.md`）は Critical / Affirmative / Mediator ロールを規定するが、**Critical 専用の project-local subagent 定義は不在**
- 現状は global spec-critic に依存 → project 内で custom 化する経路がない
- gabriel は adversarial verifier だが「MAGI 結論の後追い検証」用途で、spec/ADR/design doc 単独の critical review は担当外
- Milestone をまたぐ spec/ADR 起票時に project 固有の critical lens（LAM 憲法・Zero-Regression Policy 等の観点）を適用したい

**候補内容**:
- `.claude/agents/spec-critic.md` を project-local に作成
- system prompt に LAM 憲法（`docs/internal/00-07`）と `.claude/rules/` を参照する critical lens を組み込む
- 対象: `docs/specs/`, `docs/adr/`, `docs/tasks/` の起票時 adversarial review
- global spec-critic との差分: project 固有の rules・permission levels・phase 規律を審査基準に組み込む点

**Milestone 候補**: gabriel Wave C 完了後の別 Milestone（例: B-6 統治強化 / spec-critic 導入）。gabriel と混同しないよう独立 Milestone を推奨。

**優先度**: 低（gabriel が Critical 相当の verify を担うため急務ではない / spec/ADR 起票頻度に依存）。gabriel BUILDING 完了後 retro での再評価対象とする。

**関連参照**:
- `.claude/rules/decision-making.md` §Three Agents Model
- `docs/internal/06_DECISION_MAKING.md`
- `docs/specs/magi-v2-gabriel/tasks.md` WC-B5-T3（本 FC の起源）
- global spec-critic agent（Claude Code plugin 提供）
