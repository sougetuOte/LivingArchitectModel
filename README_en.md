# The Living Architect Model

**"AI as a Partner, Not Just a Tool."**

This repository defines the **"Living Architect Model"**, a protocol set designed to enable Large Language Models (specifically Claude) to act as an autonomous "Architect" and "Gatekeeper" for medium-to-large scale software development projects.

By placing these definition files in your project root, you transform a standard coding assistant into a proactive guardian of project consistency and health.

## Core Concepts

- **Active Retrieval**: The AI must actively search and load context, rather than relying on passive memory.
- **Gatekeeper Role**: The AI blocks low-quality code and ambiguous specs before they enter the codebase.
- **Zero-Regression**: Strict impact analysis and TDD cycles to prevent regressions.
- **Multi-Perspective Decisions**: Use the "Three Agents" model (Affirmative, Critical, Mediator) for robust decision-making.
- **Command Safety**: Strict Allow/Deny lists for terminal commands to prevent accidental damage.
- **Living Documentation**: Documentation is treated as code, updated dynamically in every cycle.
- **Phase Control**: Explicit switching between PLANNING/BUILDING/AUDITING phases to prevent "accidental implementation".
- **Approval Gates**: Explicit approvals between sub-phases prevent rushing ahead with incomplete deliverables.

## Contents

### Constitution & Quick Reference

| File | Description |
|------|-------------|
| `CLAUDE.md` | The Constitution. Defines the AI's identity, core principles, and authority |
| `.claude/CHEATSHEET.md` | Quick reference. Commands and agents list |

### Operational Protocols (`docs/internal/`)

| File | Description |
|------|-------------|
| `00_PROJECT_STRUCTURE.md` | Physical layout and naming conventions |
| `01_REQUIREMENT_MANAGEMENT.md` | From idea to spec (Definition of Ready) |
| `02_DEVELOPMENT_FLOW.md` | Impact analysis, TDD, and review cycles |
| `03_QUALITY_STANDARDS.md` | Coding standards and quality gates |
| `04_RELEASE_OPS.md` | Deployment and emergency protocols |
| `05_MCP_INTEGRATION.md` | Guide for integrating MCP servers (Serena, Heimdall) |
| `06_DECISION_MAKING.md` | Multi-Perspective Decision Making Protocol (3 Agents + AoT) |
| `07_SECURITY_AND_AUTOMATION.md` | Command Safety Protocols (Allow/Deny Lists) |
| `99_reference_generic.md` | General advice and best practices (Non-SSOT) |

### Claude Code Extensions (`.claude/`)

| Directory | Description |
|-----------|-------------|
| `commands/` | Slash commands (phase control + utilities) |
| `agents/` | Specialized subagents (requirements, design, TDD, etc.) |
| `skills/` | Auto-applied skills (guardrails, templates) |

## How to Use

### Option A: Use as a Template (Recommended)

On GitHub, click the **"Use this template"** button at the top of this repository page to create a new repository with this structure pre-configured.

**Reference Documentation:**
- [Creating a repository from a template - GitHub Docs (English)](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template)
- [テンプレートからリポジトリを作成する - GitHub Docs (日本語)](https://docs.github.com/ja/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template)

### Option B: Manual Installation

1. Copy `CLAUDE.md` to your project root.
2. Copy the `docs/internal/` directory to your project's `docs/` folder.
3. Copy the `.claude/` directory to your project root.
4. Instruct your AI assistant: _"Read CLAUDE.md and initialize yourself as the Living Architect."_

## Phase Commands

| Command | Purpose | Prohibited |
|---------|---------|------------|
| `/planning` | Requirements, design, task decomposition | Code generation |
| `/building` | TDD implementation | Implementation without specs |
| `/auditing` | Review, audit, refactoring | Direct fixes |
| `/status` | Display progress status | - |

### Approval Gates

```
requirements → [approval] → design → [approval] → tasks → [approval] → BUILDING → [approval] → AUDITING
```

User approval is required at the completion of each sub-phase. Proceeding without approval is prohibited.

## Subagents

| Agent | Purpose | Recommended Phase |
|-------|---------|-------------------|
| `requirement-analyst` | Requirements analysis, user stories | PLANNING |
| `design-architect` | API design, architecture | PLANNING |
| `task-decomposer` | Task breakdown, dependencies | PLANNING |
| `tdd-developer` | Red-Green-Refactor implementation | BUILDING |
| `quality-auditor` | Quality audit, security | AUDITING |

## Utility Commands

| Command | Purpose |
|---------|---------|
| `/focus` | Focus on current task |
| `/daily` | Daily retrospective |
| `/adr-create` | Create Architecture Decision Record |
| `/security-review` | Security review |
| `/impact-analysis` | Impact analysis |

## Recommended Models

| Phase | Recommended Model |
|-------|-------------------|
| **PLANNING** | Claude Opus / Sonnet |
| **BUILDING** | Claude Sonnet (or Haiku for simple tasks) |
| **AUDITING** | Claude Opus (Long Context) |

## License

MIT License
