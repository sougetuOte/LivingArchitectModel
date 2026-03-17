# The Living Architect Model

**"AI as a Partner, Not Just a Tool."**

This repository defines the **"Living Architect Model"**, a protocol set designed to enable Large Language Models (specifically Claude) to act as an autonomous "Architect" and "Gatekeeper" for medium-to-large scale software development projects.

By placing these definition files in your project root, you transform a standard coding assistant into a proactive guardian of project consistency and health.

## Getting Started

| Step | Resource | Time |
|------|----------|------|
| 1. Understand concepts | [Slides](docs/slides/index-en.html) | 5 min |
| 2. Set up your project | [Quick Start](QUICKSTART_en.md) | 10 min |
| 3. Daily reference | [Cheatsheet](CHEATSHEET_en.md) | Reference |

## Core Concepts

- **Active Retrieval**: The AI must actively search and load context, rather than relying on passive memory.
- **Gatekeeper Role**: The AI blocks low-quality code and ambiguous specs before they enter the codebase.
- **Zero-Regression**: Strict impact analysis and TDD cycles to prevent regressions.
- **Multi-Perspective Decisions**: Use the MAGI System (MELCHIOR, BALTHASAR, CASPAR) + Reflection for robust structured decision-making.
- **Command Safety**: Strict Allow/Deny lists for terminal commands to prevent accidental damage.
- **Living Documentation**: Documentation is treated as code, updated dynamically in every cycle.
- **Phase Control**: Explicit switching between PLANNING/BUILDING/AUDITING phases to prevent "accidental implementation".
- **Approval Gates**: Explicit approvals between sub-phases prevent rushing ahead with incomplete deliverables.

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
| `06_DECISION_MAKING.md` | Multi-Perspective Decision Making Protocol (MAGI System + AoT + Reflection) |
| `07_SECURITY_AND_AUTOMATION.md` | Command Safety Protocols (Allow/Deny Lists) |
| `99_reference_generic.md` | General advice and best practices (Non-SSOT) |

### Claude Code Extensions (`.claude/`)

| Directory | Description |
|-----------|-------------|
| `rules/` | Behavioral guidelines and guardrails (auto-loaded) |
| `commands/` | Slash commands (phase control + utilities) |
| `agents/` | Specialized subagents (requirements, design, TDD, etc.) |
| `skills/` | Skills (task orchestration, template outputs) |

## How to Use

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

If no existing requirements exist, just start using LAM as-is. You can adapt after defining requirements with `/planning`.

## Phase Commands

| Command | Purpose | Prohibited |
|---------|---------|------------|
| `/planning` | Requirements, design, task decomposition | Code generation |
| `/building` | TDD implementation | Implementation without specs |
| `/auditing` | Review, audit, refactoring | PM-level fixes prohibited (PG/SE allowed) |
| `/project-status` | Display progress status | - |

### Approval Gates

```
requirements → [approval] → design → [approval] → tasks → [approval] → BUILDING → [approval] → AUDITING
```

User approval is required at the completion of each sub-phase. Proceeding without approval is prohibited.

## You Don't Need to Memorize Commands

The tables below list all available commands and agents, but you don't need to memorize them. Just ask the AI: "What commands should I use here?" and it will suggest the right ones. Start with `/planning` and go from there.

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
| `/release <version>` | Release (CHANGELOG -> commit -> push -> tag) |
| `/wave-plan [N]` | Wave planning (select tasks and execution order for next Wave) |
| `/retro [wave\|phase]` | Retrospective (learning cycle at Wave/Phase completion) |

## Utility Commands

| Command | Purpose |
|---------|---------|
| `/pattern-review` | TDD pattern review |
| `/project-status` | Project status display |

## Recommended Models

| Phase | Recommended Model |
|-------|-------------------|
| **PLANNING** | Claude Opus / Sonnet |
| **BUILDING** | Claude Sonnet (or Haiku for simple tasks) |
| **AUDITING** | Claude Opus (Long Context) |

## Requirements

| Requirement | Purpose | Required |
|-------------|---------|----------|
| [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) | AI assistant runtime | Required |
| Python 3.8+ | Required for hooks and StatusLine | Required |
| Git | Version control | Required |
| [gitleaks](https://github.com/gitleaks/gitleaks) | Secret scanning (`/full-review` G5 check) | Recommended |

If gitleaks is not installed, `/full-review` will fail at Green State G5. Set `"gitleaks_enabled": false` in `review-config.json` to disable if not needed.

## License

MIT License
