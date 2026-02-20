# Changelog

All notable changes to this project will be documented in this file.

## [v3.8.1] - 2026-02-20

### Added

- **Feature**: `ultimate-think` スキル（AoT + Three Agents + Reflection 統合思考）
  - Phase 0: Web サーチによる事実接地 + 複雑度自動判定
  - Level 1-3 の適応的深度制御
  - アンカーファイルによる思考の永続化と漂流防止
  - 仕様書: `docs/specs/ultimate-think.md`
- **Feature**: `skill-creator` スキル（スキル作成ガイド）
  - Progressive Disclosure 設計パターン
  - ワークフロー・出力パターンのリファレンス付き

### Fixed

- **Security**: `.gitignore` に `.claude/settings.local.json` を追加
  - ローカル許可設定（パス・ドメイン・MCP 名）の誤 push を防止

## [v3.8.0] - 2026-02-17

### Changed

- **Refactor**: コンテキスト注入量を 34% 削減（406行 → 266行）
  - `rules/phase-planning.md` + `phase-building.md` + `phase-auditing.md` → `phase-rules.md` に統合
  - `rules/model-selection.md` → `CLAUDE.md` の Execution Modes 表に統合して削除
  - 全 rules ファイルから定型セクション（Purpose/Activation/References）を除去
  - `rules/core-identity.md` と `CLAUDE.md` の重複内容を排除
  - `rules/security-commands.md` を簡素化
- **Enhancement**: `/quick-load` コマンド新規追加（日常の軽量セッション再開）
- **Enhancement**: `/full-load` を最適化（dead code 削除 + テンプレート簡素化）
- **Enhancement**: `/quick-save` にフェーズ情報を追加
- **Docs**: CLAUDE.md セーブ/ロード説明を4コマンド体系に更新
- **Docs**: CHEATSHEET.md Rules ファイル一覧・セーブ/ロード説明を更新
- **Docs**: README.md / README_en.md セッション管理コマンド一覧を更新
- **Docs**: スライド（usecase.html / usecase-en.html）に `/quick-load` 追加
- **Docs**: `.claude/current-phase.md` の参照ルールを `phase-rules.md` に更新

## [v3.7.0] - 2026-02-15

### Changed

- **Enhancement**: lam-orchestrate 設計書フィードバック反映
  - `SKILL.md` Phase 1: Git 状態確認・フェーズ状態確認ステップ追加
  - `SKILL.md` Phase 2: 承認範囲の明確化（計画承認 = 全Wave承認）
  - `SKILL.md` Phase 5: 計画変更プロトコル新設（実行中の要件追加対応）
  - `SKILL.md` Subagent 選択ルール: doc-writer 役割定義を拡充（仕様策定+清書）
- **Enhancement**: `docs/internal/02_DEVELOPMENT_FLOW.md`
  - Phase 1 に Git State Verification / Phase State Verification 追加
- **Enhancement**: `docs/internal/00_PROJECT_STRUCTURE.md`
  - Section 2.A: 中間成果物（Intermediate Reports）の用途追加
  - Section 2.D: State Management セクション新設（SESSION_STATE / states/ / current-phase の棲み分け）
- **Enhancement**: `docs/internal/05_MCP_INTEGRATION.md`
  - Section 6: MEMORY.md Policy（auto memory 運用ポリシー）新設
- **Enhancement**: `docs/internal/07_SECURITY_AND_AUTOMATION.md`
  - ファイルリネーム代替手段の Note 追加
- **Enhancement**: `.claude/agents/doc-writer.md`
  - 仕様策定モード（lam-orchestrate 経由）の担当範囲追加
- **Docs**: CLAUDE.md に MEMORY.md Policy 追記（詳細は 05_MCP へ委譲）
- **Docs**: README.md / README_en.md / CHEATSHEET.md 整合性更新
  - doc-writer フェーズを ALL に変更
  - 05_MCP 説明に MEMORY.md Policy 追加
  - CHEATSHEET 参照ドキュメントに 00/04/07 追加
- **Spec**: `lam-orchestrate-design.md` v2.0.0 → v3.0.0
  - 運用フィードバック反映: Phase 構成を 5 段階に拡張
  - 承認フロー・計画変更プロトコル追加
  - Agent 一覧を実装（8 agent）に合わせて更新
  - 状態遷移図に PlanApproved / PlanChange 追加
  - 実装チェックリスト全項目完了
- `.gitignore` に `docs/daily/` を追加

## [v3.6.0] - 2026-02-15

### Added

- **Feature**: LAM スライドサイト (`docs/slides/`)
  - `index.html`: 目次ハブページ（カード型リンク集）
  - `concept.html`: コンセプト説明スライド（全25枚、"Living" 解説含む）
  - `usecase.html`: ユースケースシナリオスライド（全18枚、会話形式）
  - `lifecycle.html`: ライフサイクルスライド（全16枚、複数サイクルの進化を体験）
  - reveal.js 5.2.1 (CDN)、Mermaid フロー図、Google Fonts 対応
  - npm / Node.js 不要、HTML ファイル単体で動作
  - Mermaid lazy rendering（reveal.js 非表示スライドとの互換性対応）
- **Feature**: lam-orchestrate スキル + カスタムサブエージェント
  - `.claude/skills/lam-orchestrate/SKILL.md` - タスクオーケストレーション
  - `.claude/agents/doc-writer.md` - ドキュメント作成
  - `.claude/agents/test-runner.md` - テスト実行
  - `.claude/agents/code-reviewer.md` - コードレビュー
- **Docs**: スライドへのリンクを README, README_en, CHEATSHEET, CLAUDE.md に追加
- **Docs**: スキル・エージェント情報を CHEATSHEET, README, README_en に追加
- **Spec**: `ui-lam-slides.md` - スライド UI 仕様書

### Changed

- **Spec**: `lam-orchestrate-design.md` v1.0.0 → v2.0.0
- `.gitignore` に `SESSION_STATE.md` を追加

## [v3.5.0] - 2026-02-15

### Changed

- **Spec**: `lam-orchestrate-design.md` v1.0.0 → v2.0.0
  - ステータス: On Hold → Active (Public API Aligned)
  - Skill 定義を公式 SKILL.md 形式に移行（ディレクトリ構造、kebab-case frontmatter）
  - Subagent 定義を公式 `.claude/agents/` 仕様に準拠（`memory`, `hooks`, `skills` 等の新フィールド対応）
  - Section 7: 「Swarm 機能待ち」→「Agent Teams（Experimental → Stable 後に移行検討）」
  - 実装チェックリスト更新（ビルトイン Subagent との重複確認追加）
  - 参照 Claude Code バージョン: 2.1.42

## [v3.4.0] - 2026-02-15

### Added

- **Feature**: Session management commands
  - `/quick-save` - 軽量セーブ（SESSION_STATE.md のみ、3-4% コンテキスト消費）
  - `/full-save` - フルセーブ（commit + push + daily）
  - `/full-load` - セッション復元
- **Feature**: StatusLine script (`statusline.py`)
  - コンテキスト残量をバー表示（緑/黄/赤）
  - クロスプラットフォーム対応（Windows/macOS/Linux）
- **Docs**: Context Management section in `CLAUDE.md`
- **Docs**: Session management section in `CHEATSHEET.md`
- **Docs**: Getting started guide in `CHEATSHEET.md`
- **Docs**: Environment requirements section in `README.md` / `README_en.md`

### Changed

- **Enhancement**: Renamed `/status` to `/project-status` (reflected in all docs)
- **Enhancement**: Updated `docs/internal/05_MCP_INTEGRATION.md`
  - All MCP servers marked as optional
  - Updated terminology from "Antigravity" to "Claude Code"
- **Enhancement**: Updated `CHEATSHEET.md` for first-time users
- **Docs**: Updated `README.md` / `README_en.md` with new commands and requirements

### Removed

- **Config**: Removed Serena MCP from active configuration
  - コンテキストコスト（5-10K トークン + セーブ時 3-5%）の削減
  - 個人開発規模では grep/find で十分と判断

## [v3.3.0] - 2026-01-05

### Added

- **Feature**: Claude Code Rules integration (`.claude/rules/`)
  - `core-identity.md` - Living Architect 行動規範
  - `phase-planning.md` - PLANNING フェーズガードレール
  - `phase-building.md` - BUILDING フェーズガードレール
  - `phase-auditing.md` - AUDITING フェーズガードレール
  - `security-commands.md` - コマンド安全基準（Allow/Deny List）
  - `model-selection.md` - モデル選定ガイドライン
  - `decision-making.md` - 意思決定プロトコル（3 Agents + AoT）

### Changed

- **Enhancement**: Simplified `CLAUDE.md` (205 → 53 lines, 74% reduction)
  - コア原則のみを保持し、詳細は Rules へ移行
  - 参照構造を明確化
- **Enhancement**: Updated `CHEATSHEET.md` with Rules file listing
- **Docs**: Terminology alignment in security-commands.md
  - SSOT（07_SECURITY_AND_AUTOMATION.md）と用語統一

### Removed

- **Breaking**: Removed guardrail Skills (migrated to Rules)
  - `.claude/skills/planning-guardrail/`
  - `.claude/skills/building-guardrail/`
  - `.claude/skills/auditing-guardrail/`

### Migration Notes

- Skills ガードレールは Rules に統合されました
- 既存のコマンド（`/planning`, `/building`, `/auditing`）は引き続き動作します
- Rules は自動的にロードされるため、追加設定は不要です

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
- **Docs**: AoT quick guide in `CHEATSHEET.md`

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
- **Docs**: Updated `CHEATSHEET.md` with approval flow and state management

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
- **Docs**: Added `CHEATSHEET.md` quick reference
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
