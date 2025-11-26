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

## Contents

- **`CLAUDE.md`**: The Constitution. Defines the AI's identity, core principles, and authority.
- **`docs/internal/`**: Operational Protocols.
  - `00_PROJECT_STRUCTURE.md`: Physical layout and naming conventions.
  - `01_REQUIREMENT_MANAGEMENT.md`: From idea to spec (Definition of Ready).
  - `02_DEVELOPMENT_FLOW.md`: Impact analysis, TDD, and review cycles.
  - `03_QUALITY_STANDARDS.md`: Coding standards and quality gates.
  - `04_RELEASE_OPS.md`: Deployment and emergency protocols.
  - `05_MCP_INTEGRATION.md`: Guide for integrating MCP servers (Serena, Heimdall).
  - `06_DECISION_MAKING.md`: Multi-Perspective Decision Making Protocol (Three Agents Model).
  - `07_SECURITY_AND_AUTOMATION.md`: Command Safety Protocols (Allow/Deny Lists).
  - `99_reference_generic.md`: General advice and best practices (Non-SSOT).

## How to Use

### Option A: Use as a Template (Recommended)

Click the **"Use this template"** button at the top of this repository to create a new repository with this structure pre-configured.

### Option B: Manual Installation

1. Copy `CLAUDE.md` to your project root.
2. Copy the `docs/internal/` directory to your project's `docs/` folder.
3. Instruct your AI assistant: _"Read CLAUDE.md and initialize yourself as the Living Architect."_

## Recommended Models

| Role                              | Model                                                     |
| :-------------------------------- | :-------------------------------------------------------- |
| **Architect (Planning/Auditing)** | **Claude Opus / Sonnet**                                  |
| **Builder (Coding)**              | **Claude Sonnet** (or Claude Haiku for simple tasks)      |

## Slash Commands (Optional)

This project includes optional slash commands for Claude Code:

| Command | Purpose |
|:--------|:--------|
| `/focus` | Focus on current task - narrow down to essential information |
| `/daily` | Daily retrospective - 3-minute status update |
| `/adr:create` | Create a new Architecture Decision Record |

See `.claude/commands/` for details.

## License

MIT License
