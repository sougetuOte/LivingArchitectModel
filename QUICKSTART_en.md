# LAM Quick Start Guide

> New to LAM? Start with the [concept slides](docs/slides/index-en.html) for a visual overview.

## Prerequisites

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed
- Git installed
- A GitHub account

## Step 1: Create a Repository from the Template

Click "Use this template" on GitHub to create a new repository.

[Create from template](https://github.com/sougetuOte/LivingArchitectModel/generate)

Or clone manually:

```bash
git clone https://github.com/sougetuOte/LivingArchitectModel.git my-project
cd my-project
rm -rf .git && git init
```

## Step 2: Launch Claude Code and Adapt to Your Project

```bash
claude
```

Once launched, instruct the AI:

```
Read CLAUDE.md and initialize yourself as a Living Architect.
Adapt CLAUDE.md, .claude/, and docs/internal/ to fit this project.
Clean up the LAM-specific specs in docs/specs/ that aren't relevant here.
```

The AI will analyze your project and adapt LAM's configuration accordingly.
Feel free to discuss and iterate on the adjustments at this stage.

### What you can leave as-is (for now)

These are generic components that work out of the box:

- `.claude/rules/` --- Generic guardrails
- `.claude/hooks/` --- Immune system
- `.claude/commands/` --- Phase controls

## Step 3: Your First PLANNING Session

Type `/planning` to enter the PLANNING phase. Walk through each approval gate:

```
1. Describe your idea in natural language
2. Brainstorm with the AI to refine requirements
3. Requirements spec (docs/specs/) is generated → say "approved"
4. ADR (technology decisions) and design docs are generated → say "approved"
5. Task breakdown (docs/tasks/) is generated → say "approved"
```

Only after all approval gates are passed can you proceed to BUILDING.
This deliberate process is what ensures LAM's quality.

## Step 4: Your First BUILDING Session

Type `/building` to start TDD implementation.

The AI autonomously runs Red-Green-Refactor cycles.
When finished, run `/full-review` for an automated audit to reach Green State.

## FAQ

### Q: Do I need to manually edit CLAUDE.md?

A: The easiest approach is to let the AI adapt it in Step 2. If editing manually, focus on the project description in the Identity section.

### Q: Should I modify docs/internal/?

A: Start with the defaults. Customize gradually as your project develops its own methodology.

### Q: Is Python required?

A: Only if you use StatusLine (context remaining display). It is not required.

### Q: What if my session disconnects?

A: Use `/quick-load` for instant recovery. After a multi-day break, use `/full-load`.

### Q: Is there a fixed format for specs?

A: The template skill (spec-template) is applied automatically. Free-form writing also works.

## Next Steps

1. [New project slides](docs/slides/story-newproject-en.html) to walk through the full flow (10 min)
2. Start your first `/planning` session
3. Keep [CHEATSHEET_en.md](CHEATSHEET_en.md) handy for daily reference
4. Once comfortable, explore [docs/internal/](docs/internal/) for the process SSOT deep dive
