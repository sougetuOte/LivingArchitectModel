# 包括フルスキャン監査レポート

**対象**: プロジェクト全域（.claude/, docs/internal/, docs/specs/, docs/artifacts/, ルート .md）
**実施日**: 2026-03-12
**エージェント数**: 6（並列）
**重複排除後の統合結果**

---

## サマリー

| カテゴリ | Critical | Warning | Info | 計 |
|---------|:--------:|:-------:|:----:|:--:|
| A. 今回修正対象（統合作業の残り） | 2 | 8 | 3 | 13 |
| B. 仕様書の歴史的参照（v4.0.0 設計書） | 4 | 3 | 2 | 9 |
| C. hooks リファクタリング（既知継続） | 2 | 5 | 3 | 10 |
| D. settings.local セキュリティ強化 | 2 | 3 | 1 | 6 |
| E. アーキテクチャ課題（ADR 検討） | 0 | 3 | 2 | 5 |
| **合計** | **10** | **22** | **11** | **43** |

---

## A. 今回修正対象（統合作業スコープ）

### Critical

| ID | 等級 | ファイル | 内容 |
|----|------|---------|------|
| A-C1 | PM | `docs/internal/07_SECURITY_AND_AUTOMATION.md:18` | Allow List に `find` が残存。v4.3.1 で ask に移動済みだが 07 未反映 |
| A-C2 | PM | `docs/internal/07_SECURITY_AND_AUTOMATION.md:22-23` | Allow List に `gem list`, `top`, Security Audit ツールがあるが settings.json に未定義 |

### Warning

| ID | 等級 | ファイル | 内容 |
|----|------|---------|------|
| A-W1 | SE | `CLAUDE_en.md:61-64` | Memory Policy が旧仕様のまま。Subagent Persistent Memory, Knowledge Layer 欠落 |
| A-W2 | PM | `CLAUDE_en.md:63-64` | Memory Policy の記述が CLAUDE.md と矛盾（subagent role know-how に限定する誤記） |
| A-W3 | SE | `README.md:112` / `README_en.md:112` | `/auditing` 制約が v3.x（修正禁止）のまま。v4.0.0 の PG/SE 許可が未反映 |
| A-W4 | SE | `CHEATSHEET_en.md:137-143` | State Management に knowledge/ と agent-memory/ が欠落 |
| A-W5 | SE | `lam-orchestrate SKILL.md:149-155` | Subagent 選択テーブルに task-decomposer, design-architect, requirement-analyst 未掲載 |
| A-W6 | SE | `02_DEVELOPMENT_FLOW.md:3` | 冒頭スコープに Phase 3 未記載 |
| A-W7 | PG | `agent-memory/.../project_hook_structure.md:16-19` | W-4(tool_events上限) と I-1(frozenset) が残存課題に残っているが解消済み |
| A-W8 | SE | CHEATSHEET.md / README.md 全般 | `ui-design-guide` スキルがどの一覧表にも未掲載 |

### Info

| ID | 等級 | ファイル | 内容 |
|----|------|---------|------|
| A-I1 | PM | `CLAUDE.md:73` | `/quick-save` を「SESSION_STATE.md のみ」と記述。実際は Daily 記録も含む |
| A-I2 | SE | `CHEATSHEET_en.md` | Subagent 表に Memory 列がない（JP 版にはある） |
| A-I3 | SE | `README.md`/`README_en.md` | `/project-status` がフェーズ表と補助表の両方に重複掲載 |

---

## B. 仕様書の歴史的参照（v4.0.0 設計書）

v4.0.0 設計書は「設計時の記録」であり、実装と乖離するのは自然。
ただし、仕様書としての信頼性を維持するため最低限の注記を推奨。

### Critical

| ID | 等級 | ファイル | 内容 |
|----|------|---------|------|
| B-C1 | PM | `docs/design/v4.0.0-immune-system-design.md:627-630` | 削除済みコマンド（daily, full-save, impact-analysis, security-review）への変更指示が残存 |
| B-C2 | PM | `v4.0.0-*-design/requirements.md` | `ultimate-think` スキルが「稼働中」「変更不要」と記述 |
| B-C3 | PM | `v4.0.0-*-design/requirements/feat` 3ファイル | TDD パターン記録先が `docs/memos/` vs `docs/artifacts/` で不一致 |
| B-C4 | PM | `evaluation-kpi.md` / `quick-save.md` / `loop-log-schema.md` | ループログ参照形式が `.json` / `.log` / `.txt` の3パターン混在 |

### Warning

| ID | 等級 | ファイル | 内容 |
|----|------|---------|------|
| B-W1 | PM | `docs/design/v4.0.0-immune-system-design.md:657` | 「変更不要」リストに削除済みコマンド（focus, full-load, adr-create） |
| B-W2 | PM | `feat-v4.0.0-immune-system.md` | 中間成果物が `docs/specs/` に残置。`docs/artifacts/` に移動推奨 |
| B-W3 | SE | `docs/design/lam-orchestrate-design.md` | 参照 Claude Code バージョンが古い + ui-design-guide 未記載 |

### Info

| ID | 等級 | 内容 |
|----|------|------|
| B-I1 | PG | `docs/design/v4.0.0-immune-system-design.md` 未解決事項の番号欠番 |
| B-I2 | SE | `hooks-python-migration/tasks.md` W5-T2 のチェック未完了 |

---

## C. hooks リファクタリング（既知継続、agent-memory 記録済み）

次回 hooks リファクタリング Wave のスコープ。今回は修正しない。

| ID | 等級 | 内容 |
|----|------|------|
| C-1 | SE | `lam-stop-hook.py main()` 173行（50行制限超過） |
| C-2 | SE | `_write_state()` テスト3ファイルに重複定義 |
| C-3 | SE | `spec.loader.exec_module` None チェック欠落 |
| C-4 | PM | `_SECRET_PATTERN` が .md ファイルで偽陽性 |
| C-5 | SE | `conftest.py hook_runner` が os.environ を全コピー |
| C-6 | SE | ESLint flat config (eslint.config.*) 未検出 |
| C-7 | SE | `pre-compact.py` 専用テストが存在しない |
| C-8 | SE | `go test` カウント正規表現が脆弱 |
| C-9 | SE | エラーログに絶対パスが含まれる |
| C-10 | PM | `_validate_check_dir` PROJECT_ROOT 外パス許可 |

---

## D. settings.local セキュリティ強化

settings.local.json は個人設定だが、リポジトリに含まれるためレビュー対象。

| ID | 等級 | 内容 |
|----|------|------|
| D-1 | PM | `Bash(claude *)` 包括 allow（個別指定で代替可） |
| D-2 | PM | `Bash(sqlite3 *)` 無制限 allow |
| D-3 | PM | `Bash(git checkout *)` allow（作業ディレクトリ上書きリスク） |
| D-4 | PM | `Bash(git rm *)` allow（一括削除リスク） |
| D-5 | PM | `git reset/stash/clean` が deny/ask どちらにもない |
| D-6 | PM | WebFetch ドメイン 20+ がアドホックに蓄積 |

---

## E. アーキテクチャ課題（ADR 検討レベル）

| ID | 等級 | 内容 |
|----|------|------|
| E-1 | PM | 00 の「SSOT 3層」Layer と 07 の「Permission Layer」で番号体系衝突 |
| E-2 | PM | `permission-levels.md` の参照セクションが孤立（「要件定義書 Section 5.1」が不在） |
| E-3 | PM | `07` Deny List の記述が settings.json の ask と意味が異なる（deny≠ask） |
| E-4 | SE | `02` の `implementation_plan.md` 保存先が未定義 |
| E-5 | SE | `lam-loop-state.json` スキーマが3ファイルに分散 |
