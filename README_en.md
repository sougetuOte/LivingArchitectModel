# The Living Architect Model (LAM)

**A governance-type AI agent harness.**
LAM gives an AI agent an explicit answer to three questions: what it may do on its own, what requires human approval, and **how the rules themselves are allowed to grow or shrink**.

> **Scope**: The runtime substrate is provided by Claude Code itself. What LAM supplies is the **governance layer** that sits on top of it — **LAM does not run on its own**.

**Current version**: **v5.1.0** (2026-08-26 / [CHANGELOG.md](CHANGELOG.md))

> **"AI as a Partner, Not Just a Tool."**

A standard coding assistant will do more or less whatever it is told. With LAM in place, the same assistant operates under phase discipline, permission grades, and approval gates — and stops itself from **implementing without a spec, changing the spec unilaterally, or waving through irreversible operations**.

## Getting Started

| Step | Resource | Time |
|------|----------|------|
| 1. Understand concepts | [Slides](docs/slides/index-en.html) | 5 min |
| 2. Set up your project | [Quick Start](QUICKSTART_en.md) | 10 min |
| 3. Daily reference | [Cheatsheet](CHEATSHEET_en.md) | Reference |

## Core Concepts

### Governance (specific to LAM)

- **Permission Grades (PG / SE / PM)**: Every change is sorted into "fix it silently (PG)", "fix it and report (SE)", or "**ask the human (PM)**". PM-grade file paths are enumerated in advance, and a hook decides at execution time.
- **Principle Zero**: Whether to proceed or to ask is decided not by the AI's confidence but by three variables — **reversibility / recovery cost / cost of asking**. A "just to be safe" question is explicitly treated as *not free*: it interrupts the user's focus once.
- **Approval Gates**: User approval is mandatory at each of requirements → design → tasks. Proceeding without it is prohibited.
- **The Birth Gate — a ceiling and a currency for rules**: Resident rules are capped at **80 directives**, and **admitting one new clause requires retiring an existing one** (1-for-1 exchange). Rule sprawl — the state where nobody reads the rules any more — is prevented by *accounting* rather than by good intentions. The ledger lives at `docs/artifacts/clause-gate-ledger.md`.
- **3.5-Tier Delegation**: Work is split across supervision (L1), dispatch (L1.5), execution (L2), and grading (L3). Model-name bindings are consolidated into **a single roster file**, so a model generation change touches exactly one document.

### Quality

- **Gatekeeper Role**: The AI blocks low-quality code and ambiguous specs before they enter the codebase.
- **Zero-Regression**: Strict impact analysis and TDD cycles to prevent regressions.
- **Multi-Perspective Decisions**: The MAGI System (MELCHIOR, BALTHASAR, CASPAR) plus a **gabriel probe** — the conclusion of the deliberation is **adversarially re-examined by a verifier running in an independent context**.
- **Phase Control**: Explicit switching between PLANNING / BUILDING / AUDITING prevents "accidental implementation".
- **Command Safety**: Allow / Ask / Deny lists written as **explicit enumerations** (no wildcard dependency) to prevent accidental damage.
- **Active Retrieval**: The AI actively searches and loads context instead of relying on passive memory.
- **Living Documentation**: Documentation is treated as code and updated as **one inseparable unit** with it.

## Contents

### Constitution & Quick Reference

| File | Description |
|------|-------------|
| `CLAUDE.md` / `CLAUDE_en.md` | The Constitution. Defines the AI's identity, core principles, and authority |
| `CHEATSHEET.md` / `CHEATSHEET_en.md` | Quick reference. Commands and agents list |

### Operational Protocols (`docs/internal/`)

| File | Description |
|------|-------------|
| `00_PROJECT_STRUCTURE.md` | Physical layout and naming conventions |
| `01_REQUIREMENT_MANAGEMENT.md` | From idea to spec (Definition of Ready) |
| `02_DEVELOPMENT_FLOW.md` | Impact analysis, TDD, and review cycles |
| `03_QUALITY_STANDARDS.md` | Coding standards and quality gates |
| `04_RELEASE_OPS.md` | Deployment and emergency protocols |
| `05_MCP_INTEGRATION.md` | MCP server integration & MEMORY.md policy (optional) |
| `06_DECISION_MAKING.md` | Multi-Perspective Decision Making Protocol (MAGI System + AoT + gabriel probe) |
| `07_SECURITY_AND_AUTOMATION.md` | Command Safety Protocols (Allow/Deny Lists) |
| `08_EXECUTION_DISCIPLINE.md` | Execution Discipline (single ledger, 14-point self-audit, experience simulation, F0-F4) |
| `99_reference_generic.md` | General advice and best practices (Non-SSOT) |

### Claude Code Extensions (`.claude/`)

| Directory | Description |
|-----------|-------------|
| `rules/` | Behavioral guidelines and guardrails (auto-loaded) |
| `agents/` | Specialized subagents (requirements, design, TDD, etc.) |
| `skills/` | Skills (task orchestration, template outputs) |

## How to Use

> **About `docs/private/`**: This directory holds the LAM author's personal governance records. However you obtained LAM — template, clone, or ZIP — nothing loads from it, so **you may simply delete it**.

### Option A: Use as a Template (Recommended)

On GitHub, click the **"Use this template"** button at the top of this repository page to create a new repository with this structure pre-configured.

**Reference Documentation:**
- [Creating a repository from a template - GitHub Docs (English)](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template)
- [テンプレートからリポジトリを作成する - GitHub Docs (日本語)](https://docs.github.com/ja/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template)

### Option B: git clone

```bash
git clone https://github.com/sougetuOte/LivingArchitectModel.git my-project
cd my-project
rm -rf .git && git init
```

LAM components (`.claude/`, `docs/internal/`, `CLAUDE.md`) work together as a system. We recommend using the full set rather than copying individual files.

### Option C: Adopt into an Existing Project

To introduce LAM into a project already in development:

1. Create a working directory inside your project and extract the LAM ZIP there

```bash
mkdir _lam_source
cd _lam_source
# Download and extract the ZIP here
```

2. Launch Claude Code and instruct it:

```
Place the Living Architect Model from _lam_source/ into this project.
```

3. If you have existing requirements or specs, have the AI reference them for adaptation:

```
Reference <your-requirements-file> and review all LAM files to adapt the necessary parts.
```

If you have no existing requirements, just start using LAM as-is. You can adapt it later, after defining requirements in the PLANNING phase.

## Phase Commands

| Command | Purpose | Prohibited |
|---------|---------|------------|
| `/building` | TDD implementation | Implementation without specs |

To enter PLANNING, tell the AI "Start the PLANNING phase". **The source of truth for the current phase is `.claude/current-phase.md`** — the AI updates that file, and the hook guards read its value. You can verify the switch yourself with `cat .claude/current-phase.md`; **if it was not updated, no phase guard is active**.

### Approval Gates

```
requirements → [approval] → design → [approval] → tasks → [approval] → BUILDING → [approval] → AUDITING
```

User approval is required at the completion of each sub-phase. Proceeding without approval is prohibited.

## You Don't Need to Memorize Commands

The tables below list the available commands and agents, but you don't need to memorize them. Just ask the AI: "What commands should I use here?" and it will suggest the right ones. Start with the PLANNING phase and go from there.

## Subagents

| Agent | Purpose | Recommended Phase |
|-------|---------|-------------------|
| `requirement-analyst` | Requirements analysis, user stories | PLANNING |
| `design-architect` | API design, architecture | PLANNING |
| `task-decomposer` | Task breakdown, dependencies | PLANNING |
| `tdd-developer` | Red-Green-Refactor implementation | BUILDING |
| `quality-auditor` | Quality audit, security | AUDITING |
| `doc-writer` | Documentation creation, spec drafting, and updates | ALL |
| `test-runner` | Test execution and analysis | BUILDING |
| `code-reviewer` | Code review (LAM quality standards) | AUDITING |
| `gabriel` | **Adversarial re-examination of MAGI conclusions in an independent context** (read-only) | ALL |
| `goal-driven-l2-foreman` | Breaks large tasks into steps and dispatches them to L3 | ALL |
| `goal-driven-l3-executor` | Leaf executor for implementation and tests (no autonomous spawning) | BUILDING |
| `goal-driven-grader` | Grades results against the rubric in a context separate from the worker | ALL |

## Session Management Commands

| Command | Purpose |
|---------|---------|
| `/quick-save` | Save (SESSION_STATE.md + loop log + Daily) |
| `/quick-load` | Load (SESSION_STATE.md + related doc identification) |

## Workflow Commands

| Command | Purpose |
|---------|---------|
| `/ship` | Logical grouping commits (inventory -> classify -> commit) |
| `/full-review <target>` | Parallel audit + fix all + verify (end-to-end) |
| `/release <version>` | Release (CHANGELOG -> commit -> tag -> push) |
| `/retro [wave\|phase]` | Retrospective (learning cycle at Wave/Phase completion) |

## Recommended Models

| Phase | Recommended Model |
|-------|-------------------|
| **PLANNING** | Claude Opus / Sonnet |
| **BUILDING** | Claude Sonnet (or Haiku for simple tasks) |
| **AUDITING** | Claude Opus (Long Context) |

## Requirements

| Requirement | Purpose | Required/Optional |
|-------------|---------|-------------------|
| [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) | AI assistant runtime | Required |
| Python 3.8+ | Needed by hooks and the StatusLine | Required |
| Git | Version control | Required |
| [gitleaks](https://github.com/gitleaks/gitleaks) | Secret scanning (`/full-review` G5 check) | Recommended |

If gitleaks is not installed, Green State G5 will FAIL during `/full-review`. If you do not need it, set `"gitleaks_enabled": false` in **`.claude/review-config.json`** (an optional file — create it if it does not exist).

## License

MIT License
