# Living Architect Model Cheatsheet

## Getting Started

> We recommend starting with the [concept overview slides](docs/slides/index-en.html) to grasp the big picture of LAM, then following the [quickstart guide](QUICKSTART_en.md) to set up your environment.

1. Launch the Claude Code CLI (LAM settings are loaded automatically)
2. Start the design phase with `/planning` and define requirements
3. After requirements are set, adapt LAM to your project (just ask the AI)

```
Typical flow:
  /planning -> Requirements -> [Approval] -> Design -> [Approval] -> Task breakdown -> [Approval]
  /building -> TDD implementation (Red -> Green -> Refactor) -> [Approval]
  /auditing -> Quality audit -> [Approval] -> Done
```

## Directory Structure

```
.claude/
├── rules/                 # Guardrails and behavioral guidelines (auto-loaded)
├── commands/              # Slash commands
├── agents/                # Subagents
├── skills/                # Orchestration and template output
├── states/                # Per-feature progress state
├── hooks/                 # PreToolUse / PostToolUse / Stop / PreCompact
├── logs/                  # permission.log, loop-*.json (generated at runtime)
└── current-phase.md       # Current phase

CLAUDE.md                  # Constitution (core principles only)
CHEATSHEET.md              # This file (quick reference)
docs/internal/             # Process SSOT
docs/specs/                # Specifications
docs/adr/                  # Architecture Decision Records
```

## Rules Files

| File | Description |
|------|-------------|
| `core-identity.md` | Living Architect behavioral guidelines |
| `phase-rules.md` | Phase-specific guardrails (PLANNING/BUILDING/AUDITING) |
| `security-commands.md` | Command safety standards (Allow/Deny List) |
| `decision-making.md` | Decision-making protocol |
| `permission-levels.md` | Permission level classification (PG/SE/PM) **New in v4.0.0** |

## Permission Levels (PG/SE/PM) **New in v4.0.0**

Three-tier classification based on change risk level:

| Level | Behavior | Examples |
|-------|----------|----------|
| **PG** | Auto-fix, no report needed | Formatting, typos, lint fixes |
| **SE** | Report after fix | Adding tests, internal refactoring |
| **PM** | Requires approval | Spec changes, rule changes |

**When in doubt, default to SE** (err on the safe side). Details: `.claude/rules/permission-levels.md`

### PreToolUse hook

Automatic PG/SE/PM classification based on file paths:
- `docs/specs/`, `docs/adr/`, `.claude/rules/`, `.claude/settings*.json` -> **PM** (block)
- `docs/` (other than above) -> **SE** (allow + log)
- `Read/Glob/Grep` -> Always allowed

All classification results are recorded in `.claude/logs/permission.log`.

### Hook classification false-positive measurement

After Wave 1 completion, analyze `.claude/logs/permission.log` to establish a baseline for misclassifications:
1. Randomly sample N entries from `permission.log`
2. Human review of each classification's correctness
3. Misclassification rate = misclassifications / sample size

## Phase Commands

| Command | Purpose | Restrictions |
|---------|---------|-------------|
| `/planning` | Requirements, design, task breakdown | No code generation |
| `/building` | TDD implementation | No implementation without specs |
| `/auditing` | Review, audit, refactoring | No PM-level fixes (PG/SE allowed) |
| `/project-status` | Display progress status | - |

## Approval Gates

```
requirements -> [Approval] -> design -> [Approval] -> tasks -> [Approval] -> BUILDING -> [Approval] -> AUDITING
```

- "Approval" is required at the completion of each sub-phase
- Proceeding without approval is prohibited

## Session Management Commands

| Command | Purpose | Context consumption |
|---------|---------|---------------------|
| `/quick-save` | Lightweight save (SESSION_STATE.md only) | 3-4% |
| `/quick-load` | Lightweight load (SESSION_STATE.md only) | ~1% |
| `/full-save` | Full save (commit + push + daily) | ~10% |
| `/full-load` | Full load (state check + detailed report) | 2-3% |

### When to use save/load

- **Regular save**: `/quick-save` (safe even below 25% remaining)
- **End of day**: `/full-save` (when context budget allows)
- **Resuming work**: `/quick-load` (daily continuation)
- **Returning after days away**: `/full-load` (detailed state review)

### StatusLine
Displays remaining context at the bottom of the screen (requires Python 3.x):
```
[Opus 4.6] ▓▓▓░░░░░░░ 70% $1.23
```
- Green (>30%): Safe
- Yellow (15-30%): Caution
- Red (<=15%): `/quick-save` recommended

## Subagents

| Agent | Usage example | Phase |
|-------|---------------|-------|
| `requirement-analyst` | "Organize the requirements" | PLANNING |
| `design-architect` | "Design the API" | PLANNING |
| `task-decomposer` | "Break down the tasks" | PLANNING |
| `tdd-developer` | "Implement TASK-001" | BUILDING |
| `quality-auditor` | "Audit src/" | AUDITING |
| `doc-writer` | "Update the docs" / "Draft the spec" | ALL |
| `test-runner` | "Run the tests" | BUILDING |
| `code-reviewer` | "Review the code" | AUDITING |

## Skills

| Skill | Purpose | Usage example |
|-------|---------|---------------|
| `lam-orchestrate` | Auto-coordinate task breakdown and parallel execution | "Run with lam-orchestrate" |
| `ultimate-think` | Integrated thinking: AoT + Three Agents + Reflection | `/ultimate-think <topic>` |
| `skill-creator` | Skill creation guide | "I want to create a new skill" |
| `adr-template` | ADR creation template | Auto-applied when running `/adr-create` |
| `spec-template` | Spec creation template | Auto-applied during spec creation |

## State Management

| File | Purpose |
|------|---------|
| `.claude/current-phase.md` | Current phase |
| `.claude/states/<feature>.json` | Per-feature progress and approval state |
| `SESSION_STATE.md` | Cross-session handoff (auto-generated) |

## Workflow Commands

| Command | Purpose |
|---------|---------|
| `/ship` | Logical group commits (inventory -> classify -> commit) |
| `/full-review <target>` | Parallel audit + full fixes + verification (end-to-end) |
| `/release <version>` | Release (CHANGELOG -> commit -> push -> tag) |
| `/wave-plan [N]` | Wave planning (task selection, dependencies, risk assessment) |
| `/retro [wave\|phase]` | Structured retrospective (KPT + quantitative analysis + actions) |

## Utility Commands

| Command | Purpose |
|---------|---------|
| `/focus` | Focus on the current task |
| `/daily` | Daily retrospective (includes KPI aggregation) |
| `/adr-create` | ADR creation assistant |
| `/security-review` | Security review |
| `/impact-analysis` | Change impact analysis (includes PG/SE/PM classification) |

## Reference Documents (SSOT)

| File | Description |
|------|-------------|
| `docs/internal/00_PROJECT_STRUCTURE.md` | Directory layout, naming conventions, state management |
| `docs/internal/01_REQUIREMENT_MANAGEMENT.md` | Requirements management process |
| `docs/internal/02_DEVELOPMENT_FLOW.md` | Development flow and TDD |
| `docs/internal/03_QUALITY_STANDARDS.md` | Quality standards |
| `docs/internal/04_RELEASE_OPS.md` | Release, deployment, and incident response |
| `docs/internal/05_MCP_INTEGRATION.md` | MCP integration and MEMORY.md usage policy |
| `docs/internal/06_DECISION_MAKING.md` | Decision-making (3 Agents + AoT) |
| `docs/internal/07_SECURITY_AND_AUTOMATION.md` | Command safety standards (Allow/Deny List) |

## AoT (Atom of Thought) Quick Guide

**When to use?** (any of the following apply)
- **2 or more** decision points
- **3 or more** affected layers/modules
- **3 or more** viable options

**Workflow**
```
1. Decomposition: Break the topic into Atoms
2. Debate: 3 Agents discuss each Atom
3. Synthesis: Integrated conclusion -> Implementation
```

**Atom table format**
```
| Atom | Description | Dependencies | Parallelizable (optional) |
```

## Quick Reference

**Asked to implement during PLANNING?**
-> Display a warning and present 3 options

**Deliverable complete?**
-> Display a message requesting approval

**Want to check progress?**
-> Run `/project-status`

**Running low on context?**
-> Save with `/quick-save` and `exit`

**Starting the next session?**
-> `/quick-load` to resume from last session (daily use)
-> `/full-load` for detailed state review (returning after days away)

**Where are the specs?**
-> `docs/specs/`

**Where are the ADRs?**
-> `docs/adr/`

**Where are the Rules?**
-> `.claude/rules/`
