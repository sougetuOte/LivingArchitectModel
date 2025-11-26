# Changelog

All notable changes to this project will be documented in this file.

## [v2.0.0] - 2025-11-26

### Changed

- **Breaking**: Migrated from Gemini to Claude Code
  - `GEMINI.md` → `CLAUDE.md`
  - Updated all documentation to reference Claude models
  - Model recommendations updated: Claude Opus/Sonnet/Haiku
- **Docs**: Updated `README.md` and `README_ja.md` for Claude Code
- **Docs**: Updated `docs/internal/00_PROJECT_STRUCTURE.md` directory structure
- **Docs**: Updated `docs/internal/99_reference_generic.md` starter kit

### Added

- **Feature**: Added Claude Code slash commands (`.claude/commands/`)
  - `/focus` - 現在のタスクに集中
  - `/daily` - 日次振り返り
  - `/adr-create` - 新しいADRを作成

### Removed

- **Breaking**: Removed `GEMINI.md` (replaced by `CLAUDE.md`)

## [v1.4.0] - 2025-11-24

### Added

- **Protocol**: Integrated Antigravity Artifacts (`implementation_plan.md`, `task.md`, `walkthrough.md`) into `docs/internal/02_DEVELOPMENT_FLOW.md`.
- **Docs**: Added references to new protocols in `README.md` and `README_ja.md`.

### Changed

- **Protocol**: Clarified Mediator's decision-making authority in `docs/internal/06_DECISION_MAKING.md`.

## [v1.3.0] - 2025-11-24

### Added

- **Protocol**: Implemented "Three Agents" Multi-Perspective Decision Making Protocol (`docs/internal/06_DECISION_MAKING.md`).
- **Protocol**: Implemented Command Safety Protocols with Allow/Deny Lists (`docs/internal/07_SECURITY_AND_AUTOMATION.md`).

### Changed

- **Docs**: Updated `CLAUDE.md` to include new protocols in the SSOT list.
- **Docs**: Integrated "Perspective Check" into `01_REQUIREMENT_MANAGEMENT.md`.
- **Docs**: Integrated "Critical Agent" risk assessment into `02_DEVELOPMENT_FLOW.md`.

## [v1.2.2] - 2025-11-24

### Added

- **Docs**: Added `docs/internal/99_reference_generic.md` as a generic reference pack for the Living Architect Model.
- **Docs**: Updated `CLAUDE.md` to include `99_reference_generic.md` in the SSOT priority list.

## [v1.2.1] - 2025-11-22

### Changed

- **Config**: Updated `.gitignore` to include agent and tool directories (`.agent/`, `memos/`, `.serena/`, `data/`).
- **Docs**: Generalized MCP configuration examples in `docs/internal/05_MCP_INTEGRATION.md`.
