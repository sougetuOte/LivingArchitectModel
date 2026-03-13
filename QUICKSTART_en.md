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

## Step 2: Launch Claude Code and Define Requirements with `/planning`

```bash
claude
```

When Claude Code starts, LAM's configuration (`.claude/`, `CLAUDE.md`, etc.) is loaded automatically.
No need for `claude init` — the template includes everything.

Once launched, type `/planning` to enter the PLANNING phase and describe your idea:

```
/planning

"I want to build a web app that manages ..."
```

The AI will brainstorm with you, walking through each approval gate:

```
1. Describe your idea in natural language
2. Brainstorm with the AI to refine requirements
3. Requirements spec (docs/specs/) is generated → say "approved"
4. ADR (technology decisions) and design docs are generated → say "approved"
5. Task breakdown (docs/tasks/) is generated → say "approved"
```

Only after all approval gates are passed can you proceed to BUILDING.
This deliberate process is what ensures LAM's quality.

## Step 3: Adapt LAM to Your Project

Once requirements are defined, adapt LAM to fit your project. Just tell the AI:

```
Requirements are complete. Please review all LAM files and adapt the necessary parts to this project.
```

### Files to adapt (replace with project-specific content)

| File | What to change |
|------|---------------|
| `CLAUDE.md` | Update Identity section with your project name and description |
| `README.md` / `README_en.md` | Rewrite with your project's description |
| `CHANGELOG.md` | Start fresh |
| `docs/specs/` | Remove LAM-specific specs |
| `docs/adr/` | Remove LAM-specific ADRs |
| `QUICKSTART.md` etc. | LAM onboarding guides — can be deleted |

### Files to keep as-is (generic infrastructure)

| Directory | Why |
|-----------|-----|
| `.claude/rules/` | Generic guardrails (effective for any project) |
| `.claude/hooks/` | Immune system |
| `.claude/commands/` | Phase controls and workflows |
| `.claude/agents/`, `skills/` | Specialized subagents and skills |
| `.claude/agent-memory/` | Subagent cross-session learning records |
| `docs/internal/` | Development process SSOT |
| `docs/artifacts/knowledge/` | Project knowledge accumulation (via `/retro`) |
| `CHEATSHEET.md` | Command reference (generic) |

> When in doubt, check the [slides](docs/slides/index-en.html) for an overview of the project structure.

## Step 4: Your First BUILDING Session

Type `/building` to start TDD implementation.

The AI autonomously runs Red-Green-Refactor cycles.
When finished, run `/full-review` for an automated audit to reach Green State.

## FAQ

### Q: Do I need to manually edit CLAUDE.md?

A: Let the AI adapt it in Step 3 after requirements are defined. If editing manually, focus on the project description in the Identity section.

### Q: Should I modify docs/internal/?

A: Start with the defaults. Customize gradually as your project develops its own methodology.

### Q: Is Python required?

A: **Yes, it is required.** Hook scripts and StatusLine use Python 3.8+.

#### Setup (if you don't have Python yet)

**Recommended: uv (fastest, modern)**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # Linux/macOS
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

uv venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

uv pip install -r requirements-dev.txt  # Only if running tests
```

**Fallback: venv (no additional install needed)**

```bash
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

pip install -r requirements-dev.txt     # Only if running tests
```

> If you already use pyenv, conda, etc., those work too.
> Any Python 3.8+ will work.
> On Windows, if `python3` is not available, use `py` or `python` instead.

### Q: What if my session disconnects?

A: Use `/quick-load` for instant recovery.

### Q: Is there a fixed format for specs?

A: The template skill (spec-template) is applied automatically. Free-form writing also works.

## Next Steps

1. [New project slides](docs/slides/story-newproject-en.html) to walk through the full flow (10 min)
2. Start your first `/planning` session
3. Keep [CHEATSHEET_en.md](CHEATSHEET_en.md) handy for daily reference
4. Once comfortable, explore [docs/internal/](docs/internal/) for the process SSOT deep dive
