# Changelog

All notable changes to this project will be documented in this file.

## [v3.2.0] - 2025-12-17

### Added

- **Feature**: Atom of Thought (AoT) framework integration
  - 複雑な議題を構造化するためのフレームワーク
  - 判断ポイント2つ以上、影響レイヤー3つ以上、選択肢3つ以上の場合に適用
  - Three Agents との組み合わせワークフロー
- **Docs**: AoT SSOT section in `docs/internal/06_DECISION_MAKING.md`
  - 適用基準の定量化（閾値明示）
  - Decomposition → Debate → Synthesis ワークフロー
  - Atom テーブル形式の標準化
- **Docs**: AoT quick guide in `.claude/CHEATSHEET.md`

### Changed

- **Enhancement**: Updated `docs/internal/02_DEVELOPMENT_FLOW.md` with AoT integration
  - Phase 1 の各ステップでの AoT 活用ガイド
- **Enhancement**: Updated subagent definitions with AoT sections
  - `requirement-analyst.md`: Step 1.5 AoT による要件分解
  - `design-architect.md`: Step 1.5 AoT による設計分解
  - `task-decomposer.md`: Step 3.5 AoT によるタスク分解
- **Docs**: Standardized Atom table format with optional 並列可否 column

## [v3.1.0] - 2025-12-09

### Added

- **Feature**: Approval gate system for sub-phase transitions
  - 要件定義 → [承認] → 設計 → [承認] → タスク分解 → [承認] → 実装
  - 各サブフェーズ完了時にユーザー承認が必須
  - 未承認での次フェーズ進行をブロック
- **Feature**: State management system (`.claude/states/`)
  - 機能ごとの進捗状態を JSON で管理
  - ステータス値: `pending` / `in_progress` / `approved`
  - 承認日時の記録
- **Feature**: `/status` command for progress visualization
  - 機能ごとの進捗状況を表形式で表示
  - 次のアクション提案

### Changed

- **Enhancement**: Updated `/planning` command with approval gate logic
- **Enhancement**: Updated `/building` command with prerequisite checks
- **Enhancement**: Updated `/auditing` command with state management
- **Enhancement**: Updated `planning-guardrail` skill with approval enforcement
- **Docs**: Updated `.claude/CHEATSHEET.md` with approval flow and state management

## [v3.0.0] - 2025-12-08

### Added

- **Feature**: Phase control system for explicit PLANNING/BUILDING/AUDITING mode switching
  - `/planning` - 要件定義・設計フェーズ（コード生成禁止）
  - `/building` - TDD実装フェーズ（仕様確認必須）
  - `/auditing` - 監査・レビューフェーズ（修正禁止）
- **Feature**: Specialized subagents (`.claude/agents/`)
  - `requirement-analyst` - 要件分析専門
  - `design-architect` - 設計・アーキテクチャ専門
  - `task-decomposer` - タスク分解専門
  - `tdd-developer` - TDD実装専門
  - `quality-auditor` - 品質監査専門
- **Feature**: Auto-applied skills (`.claude/skills/`)
  - `planning-guardrail` - PLANNINGフェーズのガードレール
  - `building-guardrail` - BUILDINGフェーズのガードレール
  - `auditing-guardrail` - AUDITINGフェーズのガードレール
  - `spec-template` - 仕様書テンプレート
  - `adr-template` - ADRテンプレート
- **Docs**: Added `.claude/CHEATSHEET.md` quick reference
- **Docs**: Added `.claude/current-phase.md` phase state file
- **Docs**: Added implementation records in `docs/memos/`
  - `03-living-architect-adaptation-plan.md`
  - `04-phase-support-mechanisms-analysis.md`
  - `05-phase-control-implementation-record.md`

### Changed

- **Breaking**: Restructured `.claude/` directory
  - Added `agents/` directory for subagents
  - Added `skills/` directory for auto-applied skills
- **Docs**: Updated `CLAUDE.md` with phase control section (Section 4)
- **Docs**: Reorganized README files
  - `README_ja.md` → `README.md` (Japanese as primary)
  - `README.md` → `README_en.md` (English as secondary)
- **Docs**: Updated both READMEs with phase commands, subagents, and new structure

## [v2.1.0] - 2025-11-26

### Added

- **Feature**: Added Claude Code integration section to `CLAUDE.md`
  - ディレクトリ構成の定義
  - Slash Commands 命名規則
  - Permission Model（権限モデル）
  - MCP サーバー連携ルール
- **Feature**: Added new slash commands
  - `/security-review` - セキュリティレビュー
  - `/impact-analysis` - 影響分析
- **Config**: Added `.claude/settings.json` with allow/deny/ask permission lists
  - `docs/internal/07_SECURITY_AND_AUTOMATION.md` と整合

### Changed

- **Docs**: Updated `README.md` and `README_ja.md` with new commands

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
