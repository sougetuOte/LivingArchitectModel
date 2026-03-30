# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [v4.6.1] - 2026-03-31

### 概要

モジュール間帰責判断機能の追加。`/full-review` でモジュール境界の Issue を検出した際に、帰責のヒントと判断フローチャートを提供する。

### Added

- **feat**: `parse_blame_hint()` — Agent 出力から BLAME-HINT マーカーを抽出するパーサー
  - 複数ブロック対応、壊れたマーカーの安全なスキップ（NFR-3）
  - `_VALID_RESPONSIBLE` による無効値の `unknown` 正規化
- **feat**: `build_review_prompt_with_contracts()` に帰責判断ガイドを注入
  - 契約カード注入時のみ帰責指示が有効化（単一モジュール時は従来通り）
- **feat**: `code-quality-guideline.md` にモジュール間帰責判断フローチャート追加
  - 仕様ドリフト帰責 → 契約違反帰責 → 組み合わせ顕在化の 3 段階判断
  - 帰責分類: upstream / downstream / spec_ambiguity / unknown
- **feat**: `/full-review` Stage 2/3/4 に帰責関連手順追加
  - `** 帰責判断求む **` マーカーによる視認性確保
  - 帰責サマリーテーブル（帰責 Issue 1 件以上の場合）
  - `spec_ambiguity` の自動修正禁止ガード
- **test**: 帰責パーサー 11 テスト + プロンプト拡張 3 テスト（合計 481 テスト）
- **docs**: 仕様書・設計書・タスク定義 + 移植パッケージ

### Changed

- **docs**: Agent 定義（quality-auditor, code-reviewer）にモジュール間帰責観点を追加
- **docs**: `scalable-code-review-design.md` にクロスリファレンス追加

## [v4.6.0] - 2026-03-17

### 概要

gitleaks 統合によるシークレットスキャン基盤の導入、延期 Issue 全件解消。

### Added

- **feat**: gitleaks 統合 — 言語・ファイル形式を問わない包括的シークレット検出
  - `/full-review` Stage 1 に `gitleaks detect`（全体スキャン）統合
  - `/ship` Phase 1 に `gitleaks protect --staged`（差分スキャン）統合
  - 未インストール時は G5 FAIL + インストールガイド表示
  - 明示的オプトアウト: `review-config.json` の `gitleaks_enabled: false`
  - タイムアウト・実行失敗の検出と区別（scan-timeout / scan-failed）
- **test**: gitleaks テスト 28 件 + 既存テスト拡充 7 件（合計 480 テスト）

### Changed

- **docs**: `hooks-python-migration-design.md` にテスト方式 3（conftest sys.path）追記
- **docs**: `scalable-code-review-spec.md` FR-7e に gitleaks 統合言及
- **docs**: `full-review.md` G5 セキュリティチェックを gitleaks に置換
- **docs**: `ship.md` Phase 1 に gitleaks protect 追加
- **docs**: README（日英）に gitleaks を環境要件として追記

### Fixed

- 延期 Issue 全件解消（A〜G）:
  - A+D: シークレットスキャン範囲拡大（gitleaks 統合で解決）
  - B: PostToolUseFailure ランタイム検証（正常動作確認）
  - C: PG 引数制御（既に実装済みと確認）
  - E: テスト方式記述更新
  - F: pre-compact.py テスト拡充
  - G: セキュリティスキャンテスト（既存 + gitleaks で十分）

## [v4.5.0] - 2026-03-16

### 概要

Scalable Code Review Phase 3〜5（Plan C/D/E）完了、/magi スキル新設、
全文書の MAGI System 命名統一。

### Added

- **feat**: Plan C — 階層的レビュー（Layer 2 モジュール統合 + Layer 3 システムレビュー）
- **feat**: Plan D — 依存グラフ駆動（トポロジカル順レビュー・修正 + 契約カード + 影響範囲分析）
- **feat**: Plan E — Stage 体系再編（11 Phase → 6 Stage）+ 自動スケール判定（scale_detector.py）+ E2E テストフレームワーク
- **feat**: /magi スキル — AoT + MAGI System（MELCHIOR/BALTHASAR/CASPAR）+ Reflection による構造化意思決定
- **feat**: /clarify スキル — 文書精緻化インタビュー（曖昧さ・矛盾・欠落検出）
- **docs**: Code Quality Guideline（三層モデル + 重要度分類 + Green State 再定義）
- **docs**: Planning Quality Guideline（Requirements Smells + RFC 2119 + SPIDR + WBS 100%）
- **docs**: Green State 定義統一（Info 非阻害）
- **test**: 435 テスト（v4.4.1 の 68 から大幅増）

### Changed

- **refactor**: Three Agents Model → MAGI System に改名（旧名は括弧書きで後方互換維持）
- **refactor**: full-review.md を Stage 体系に全面再編（23 箇所の self-reference 更新）
- **refactor**: lam-orchestrate の構造化思考セクションを /magi 参照に置換
- **docs**: 全スライド（日英 8 ファイル）を MAGI System + Stage 体系に更新
- **docs**: README, CHEATSHEET（日英）を MAGI 命名に統一
- **docs**: 01_REQUIREMENT_MANAGEMENT, 02_DEVELOPMENT_FLOW に /magi + /clarify 反映
- **docs**: TDD 品質チェックに R-5（テスト名一致）/ R-6（設計書アサーション）追加

## [v4.4.1] - 2026-03-13

### 概要

hooks 品質改善（full-review 8イテレーション監査）、テスト品質強化、
リリースオペレーション文書の汎用化。

### Changed

- **Refactor**: lam-stop-hook 品質改善
  - シークレットスキャンで file:line を WARN ログに記録
  - 状態ファイル読取エラー時のログ出力追加
  - `now_utc_iso8601()` に統一（インラインの datetime 生成を排除）
  - STEP 番号を 1-7 に統一（モジュール/関数 docstring/main コメント全箇所）
  - Green State G1/G2/G5 スコープを docstring に明記
- **Refactor**: post-tool-use — `_handle_loop_log` JSON パース失敗時の早期 return
  （空 dict で上書きしてループ状態を破壊するバグを修正）
- **Refactor**: _hook_utils — 例外キャッチを `Exception` → 具体的型に限定
- **Docs**: 04_RELEASE_OPS.md 汎用化（P1/P2/P3 優先度体系導入）
- **Docs**: design.md lam-stop-hook 行数実績更新（約670行）
- **Docs**: スライドのバージョン表記を v4.4.1 に更新

### Added

- **Test**: go test 失敗記録テスト追加（`test_go_test_fail_recorded`）
- **Test**: ループ統合テスト改善（stdout 空チェック追加、field count 検証強化）
- **Docs**: retro-v4.4.0.md, retro-v4.4.1.md（振り返り記録）
- **Docs**: 監査レポート v4.4.1 iter1-4

## [v4.4.0] - 2026-03-13

### 概要

TDD 内省パイプライン v2 設計、hooks の堅牢性強化（pip-audit 誤検出修正、symlink 対応、
convergence_reason 導入）、およびプロジェクト全体の包括的整合性監査を実施。

### Added

- **Feature**: TDD 内省パイプライン v2 — JUnit XML ベースのテスト結果追跡
  - PostToolUse hook が `.claude/test-results.xml` を読み取り FAIL→PASS 遷移を記録
  - パターン記録: `.claude/tdd-patterns.log`（自動、PG級）
  - 閾値 2回以上でルール候補を `/retro` 実行時に提案
  - 信頼度モデル: `.claude/rules/auto-generated/trust-model.md`
- **Rule**: `upstream-first.md` — プラットフォーム機能の実装前に公式ドキュメント確認を必須化
- **Rule**: `test-result-output.md` — テスト結果の JUnit XML 出力を必須化
- **Docs**: 監査レポート永続化（`docs/artifacts/audit-reports/`）

### Changed

- **Refactor**: lam-stop-hook 大幅改善
  - `_loop_result_label()` 廃止 → `convergence_reason` を直接渡すチェーンに変更
  - pip-audit 誤検出修正（`[project]` セクションのない pyproject.toml でスキップ）
  - シークレットスキャンで symlink をスキップ（Linux/macOS 対応）
  - セキュリティツール timeout を FAIL 扱いに変更
- **Refactor**: _hook_utils — LAM_PROJECT_ROOT の resolve() + is_dir() 検証追加
- **Refactor**: post-tool-use — log_entry をモジュールレベル import に修正、go test 正規表現修正
- **Security**: `mv` コマンドを承認必須(ask) → 実行禁止(deny) に格上げ
- **Docs**: 仕様書全面整合性更新
  - v4.0.0-immune-system-requirements: 閾値 3回→2回（全箇所）
  - ui-lam-slides: 現行実装に合わせて全面改訂（Draft→Approved）
  - hooks-python-migration-design: Wave 5 完了マーク
  - loop-log-schema: convergence_reason enum 追加
- **Docs**: ルート文書・スライド整合性更新
  - CHEATSHEET(日英): Rules一覧に upstream-first, test-result-output 追加
  - CHEATSHEET(日英): Memory列 project→- に修正（v4.3.0 反映）
  - README(日英): /wave-plan, /retro コマンド追加
  - slides: docs/internal/ ファイル名誤記修正、/full-save→/ship、閾値25%→20%
- **Docs**: full-review コマンドの jq 依存を Python ワンライナーに置換

### Removed

- **Cleanup**: 廃止コマンド・スキル削除（ultimate-think, daily, focus 等）

## [v4.3.1] - 2026-03-12

### 概要

`find` コマンドの deny バイパス脆弱性を修正するセキュリティパッチ。

### Fixed

- **Security**: `Bash(find *)` が allow リストにあり、`find -delete` / `find -exec rm` 等で
  deny ルールをバイパスできる脆弱性を修正
  - allow から `Bash(find *)` を削除
  - deny に `find * -delete *`, `find * -exec rm *`, `find * -exec chmod *`, `find * -exec chown *` を追加
  - ask に `Bash(find *)` を追加（通常の find は確認付きで実行可能）

## [v4.3.0] - 2026-03-12

### 概要

full-review ループの PM 級制御フロー（pm_pending）を導入し、
セキュリティ強化（normalize_path、シークレットスキャン範囲拡大）を実施。
memory: project フロントマターを公式外フィールドとして全エージェントから削除。

### Added

- **Feature**: `pm_pending` フラグによる PM 級ループ制御
  - PM 級 Issue 検出時にループを一時停止し、ユーザーの条件付き承認を待つ
  - Stop hook が `pm_pending=true` を検出すると block せず停止を許可
  - full-review.md / lam-orchestrate SKILL.md にフロー・スキーマを追記
- **Security**: `normalize_path` に `__out_of_root__` ガード追加
  - project_root 外パスを PM 級として捕捉（Write 操作の権限ゲート強化）
- **Security**: シークレットスキャン範囲を `src/` → `check_dir` 全体に拡大
  - 除外ディレクトリ対応（.git, node_modules, __pycache__ 等）
  - `_SAFE_PATTERN` を単語境界 `\b` に変更（偽陽性抑制）
- **Test**: pm_pending / fullscan_pending / out-of-root 等 8テスト追加（計 64 テスト）
- **Docs**: ADR-0004 — Bash(cat/grep *) 無制限許可の意図的設計判断を記録
- **Docs**: full-review 監査レポートの永続化（iter1/iter2）
- **Security**: `07_SECURITY_AND_AUTOMATION.md` Allow List に pip-audit/npm audit/safety check 追加

### Changed

- **Breaking**: 全6エージェントから `memory: project` フロントマターを削除
  - 公式 Claude Code フロントマターではないことを確認
  - CLAUDE.md の記述を「自発的書き込み方式」に修正
  - `.claude/agent-memory/` の仕組み自体は維持（CLAUDE.md 指示で動作）
- **Refactor**: `now_utc_iso8601()` を `_hook_utils.py` に集約、各 hook のラッパー関数を削除
- **Refactor**: ループログ出力を `loop-log-schema.md` MVP フォーマットに準拠
- **Fix**: `tool_events` に 500 件上限追加（状態ファイル肥大化防止）
- **Fix**: `pre-tool-use.py` TSV ログのタブ/改行エスケープ
- **Docs**: `feat-v4.0.0-immune-system.md` — max_iterations 3→5 変更注記、TDD パターン記録先統一
- **Docs**: `docs/design/lam-orchestrate-design.md` — quality-auditor 追加、memory コメント更新

## [v4.2.0] - 2026-03-12

### 概要

LAM の知識管理を3層構造に再編し、コマンド/スキルの出力先を `docs/artifacts/` に分離した。
`docs/memos/` は個人用の gitignore 領域として明確に位置づけ、プロジェクト資産との混在を解消。

### Added

- **Feature**: 3層メモリアーキテクチャの導入
  - **Knowledge Layer** (`docs/artifacts/knowledge/`): `/retro` Step 4 で人間が意図的に整理した知見・教訓を蓄積。patterns.md / pitfalls.md / conventions.md のテンプレートを同梱
  - **Subagent Persistent Memory** (`.claude/agent-memory/`): 6エージェントに `memory: project` を追加。セッションを跨いでプロジェクト固有のパターンや慣例を自動学習する
    - 対象: code-reviewer, tdd-developer, quality-auditor, doc-writer, design-architect, requirement-analyst
    - 除外: test-runner, task-decomposer（単純タスク実行のため学習不要）
  - **Auto Memory** (`MEMORY.md`): 既存の Claude Code auto memory はビルドコマンド・デバッグ知見等の作業効率学習に限定使用と明文化
- **Feature**: `/retro` Step 4 に「エージェント調整」「知見の蓄積」アクションカテゴリを追加
- **Feature**: `docs/artifacts/` ディレクトリ新設 — コマンド/スキルが生成する構造化成果物の保存先
- **Docs**: `/full-review` に Scalable Review（モジュール分割レビュー）の将来拡張セクションを追記

### Changed

- **Breaking**: コマンド/スキル出力先を `docs/memos/` → `docs/artifacts/` に移行
  - 影響範囲: `/full-review`, `/auditing`, `/building`, `/retro`, `/pattern-review`, `/ultimate-think`, trust-model, phase-rules, core-identity 等 18箇所
  - `docs/memos/` は個人メモ・参考資料専用の gitignore 領域として維持
  - 既存の `docs/memos/` 内ファイルの自動移行は行わない（手動で `docs/artifacts/` にコピーが必要）
- **Docs**: CLAUDE.md の MEMORY.md Policy を Memory Policy に改訂（3層メモリアーキテクチャに対応）
- **Docs**: CHEATSHEET — Subagent 表に Memory 列（project/-）追加、状態管理に `docs/artifacts/knowledge/` と `.claude/agent-memory/` を追記
- **Docs**: QUICKSTART 日英 — 「そのままでよいファイル」に `.claude/agent-memory/` と `docs/artifacts/knowledge/` を追加
- **Docs**: スライド — バージョン表記を v4.2.0 に更新（index/intro 日英4ファイル）、architecture 日英のファイル構成マップに `agent-memory/` と `artifacts/knowledge/` を追加

### Migration Guide

v4.1.0 からの移行手順:

1. `docs/memos/` 内のコマンド出力物（audit-reports/, tdd-patterns/, retro-*.md 等）がある場合は `docs/artifacts/` にコピー
2. `docs/memos/knowledge/` が存在する場合は `docs/artifacts/knowledge/` にコピー
3. 個人メモ・参考資料は `docs/memos/` にそのまま残してよい（gitignore 対象）

### 3層メモリアーキテクチャ

| 層 | 保存先 | 蓄積者 | タイミング | 内容 |
|----|--------|--------|-----------|------|
| Knowledge Layer | `docs/artifacts/knowledge/` | 人間（/retro 経由） | Wave/Phase 完了時 | 意図的に整理された知見・教訓 |
| Subagent Memory | `.claude/agent-memory/` | Subagent（自動） | タスク実行中 | 実行中に学んだパターン・慣例 |
| Auto Memory | `MEMORY.md` | Claude 本体（自動） | セッション中 | ビルドコマンド、デバッグ知見等 |

## [v4.1.0] - 2026-03-10

### Added

- **Feature**: hooks Python 移行 — bash 4本を Python に完全置換
  - `pre-tool-use.py` / `post-tool-use.py` / `lam-stop-hook.py` / `pre-compact.py`
  - 共通ユーティリティ `_hook_utils.py`（JSON パース、パス判定、権限等級分類）
  - 統合テスト `test_loop_integration.py`（7件）+ ユニットテスト（49件）
- **Skill**: `/retro`（振り返り）、`/wave-plan`（Wave 計画）新設
- **Enhancement**: `/ship`、`/project-status` 強化

### Changed

- **Enhancement**: hooks 基盤を bash → Python に移行（テスタビリティ・保守性向上）
- **Docs**: QUICKSTART / README に Python 3.8+ 必須を反映
- **Docs**: 仕様書同期（`.sh` → `.py`、`deny` → `ask`、H 番号体系、スキーマ更新）
- **Docs**: CHEATSHEET の Python バージョン表記を 3.x → 3.8+ に統一
- **Docs**: スライド（intro / intro-en）Quick Start に Python 3.8+ 必須を追記
- **Docs**: ADR-0002 ステータスを Accepted に更新、スクリプト参照を `.py` に修正

### Removed

- **Breaking**: 旧 bash hooks 4本（`pre-tool-use.sh` 等）+ bash テスト 5本を削除

## [v4.0.1] - 2026-03-09

### Fixed

- **Docs**: QUICKSTART / README の導入フロー修正 — Step 2 で `/planning`（要件定義）、Step 3 で LAM 適応の順序に変更
- **Docs**: CHEATSHEET の「初期化してください」指示を削除 — 初期化不要のフローに統一
- **Docs**: スライド修正 — intro の Quick Start Step 3 から `.claude/` `docs/internal/` を適応対象外に修正、story-newproject に LAM 適応スライド追加、story-evolution の「生成される」→「含まれている」
- 全修正は日英両方に適用（12ファイル）

## [v4.0.0] - 2026-03-09

### Added

- **Feature**: 免疫システム（Immune System）— 5 Wave 全22タスク完了
  - Wave 0: KPI定義・ループログスキーマ・Green State仕様
  - Wave 1: 権限等級システム（PG/SE/PM）+ PreToolUse/Stop hooks基盤
  - Wave 2: Stop hook本実装 + PostToolUse hook本実装 + full-review統合フロー
  - Wave 3: Doc Sync パイプライン（/ship 連携）+ TDD内省パイプライン
  - Wave 4: TDD内省 — パターン記録・信頼度モデル・ルール候補自動生成
- **Feature**: ループログ生成 + lam-stop-hook 強化
- **Feature**: Green State G5 セキュリティチェック統合
- **Skill**: `ui-design-guide` — UI/UX設計チェックリスト（フレームワーク非依存）
- **Docs**: スライド全面再構築 — ストーリー駆動5本構成（日英10本）
  - intro / story-newproject / story-daily / story-evolution / architecture
- **Docs**: `QUICKSTART.md` / `QUICKSTART_en.md` — 初心者向け5分導入ガイド
- **Docs**: `CLAUDE_en.md` / `CHEATSHEET_en.md` — 全ドキュメント英語版完備
- **Docs**: ADR-0003: context7 vs WebFetch 方針決定

### Changed

- **Security**: pre-tool-use フック強化（CWD検証・sed escape修正）
- **Enhancement**: テスト基盤改善（test-helpers.sh共通化 + set -e耐性）
- **Enhancement**: README.md / README_en.md — 初心者ナビ・Option B/C改善・「コマンド暗記不要」追加
- **Enhancement**: CHEATSHEET.md — QUICKSTART相互リンク追加
- **Docs**: docs/internal 全体ブラッシュアップ（v4.0.0整合 + セキュリティツール参照）

### Removed

- **Docs**: 旧スライド削除（concept / usecase / lifecycle — 日英6本）

### Migration Notes

- 権限等級（PG/SE/PM）が全操作に適用されます
- AUDITING フェーズで PG/SE級の修正が許可に緩和（v3.x は修正禁止）
- hooks が自動でファイル変更を監視し、Doc Sync フラグを生成します
- `/pattern-review` で TDD内省パターンの確認・承認が可能です

## [v3.9.0] - 2026-03-06

### Added

- **Command**: `/ship` — 論理グループ分けコミット（棚卸し -> Doc Sync -> 分類 -> 確認 -> 実行）
  - 秘密情報自動検出・除外、dry-run モード対応
  - push は分離（安全側に倒す設計）
- **Command**: `/full-review` — 並列監査 + 全修正 + 検証の一気通貫レビュー
  - 複数エージェント並列監査 -> レポート統合 -> audit-fix-policy に基づく全修正 -> 検証
  - `/auditing`（フェーズ切替）との使い分けを明確化
- **Rule**: TDD 品質チェック（R-1: 仕様突合、R-4: テスト網羅）を BUILDING ルールに追加
- **Rule**: 仕様同期ルール（S-1, S-3, S-4）を BUILDING ルールに追加
- **Docs**: SSOT 3層アーキテクチャ（docs/internal -> .claude/ -> CHEATSHEET）を明文化
- **Docs**: AUDITING チェックリストに SSOT 整合性チェック 2項目追加

### Changed

- **Spec**: `docs/specs/v3.9.0-improvement-adoption.md` 新規作成（採用判定の仕様書）
- **Docs**: CHEATSHEET / README / README_en にワークフローコマンドセクション追加

## [v3.8.2] - 2026-02-23

### Fixed

- **Fix**: セーブ/ロードコマンドの SESSION_STATE.md パス表記を統一
  - `quick-save.md`, `quick-load.md`, `full-save.md` に「プロジェクトルートの」を明記
  - `full-load.md` は既に明記済み（変更なし）
  - 別プロジェクトへのテンプレート適用時にパスが曖昧になる問題を解消
- **Config**: `.gitignore` に `.claude/commands/release.md` を追加

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
- **Spec**: `docs/design/lam-orchestrate-design.md` v2.0.0 → v3.0.0
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

- **Spec**: `docs/design/lam-orchestrate-design.md` v1.0.0 → v2.0.0
- `.gitignore` に `SESSION_STATE.md` を追加

## [v3.5.0] - 2026-02-15

### Changed

- **Spec**: `docs/design/lam-orchestrate-design.md` v1.0.0 → v2.0.0
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
