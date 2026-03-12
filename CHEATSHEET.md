# Living Architect Model チートシート

## はじめに（初めて使う方へ）

> まず [概念説明スライド](docs/slides/index.html) で LAM の全体像を掴み、[クイックスタートガイド](QUICKSTART.md) で環境構築を行うことをお勧めします。

1. Claude Code CLI を起動する（LAM の設定は自動で読み込まれる）
2. `/planning` で設計フェーズを開始し、要件を定義する
3. 要件確定後、LAM をプロジェクトに適応させる（AI に依頼するだけ）

```
典型的な流れ:
  /planning → 要件定義 → [承認] → 設計 → [承認] → タスク分解 → [承認]
  /building → TDD実装（Red → Green → Refactor）→ [承認]
  /auditing → 品質監査 → [承認] → 完了
```

## ディレクトリ構造

```
.claude/
├── rules/                 # ガードレール・行動規範（自動ロード）
├── commands/              # スラッシュコマンド
├── agents/                # サブエージェント
├── skills/                # オーケストレーション・テンプレート出力
├── states/                # 機能ごとの進捗状態
├── hooks/                 # PreToolUse / PostToolUse / Stop / PreCompact
├── logs/                  # permission.log, loop-*.json（実行時生成）
└── current-phase.md       # 現在のフェーズ

CLAUDE.md                  # 憲法（コア原則のみ）
CHEATSHEET.md              # このファイル（クイックリファレンス）
docs/internal/             # プロセス SSOT
docs/specs/                # 仕様書
docs/adr/                  # アーキテクチャ決定記録
```

## Rules ファイル一覧

| ファイル | 内容 |
|---------|------|
| `core-identity.md` | Living Architect 行動規範 |
| `phase-rules.md` | フェーズ別ガードレール（PLANNING/BUILDING/AUDITING） |
| `security-commands.md` | コマンド安全基準（Allow/Deny List） |
| `decision-making.md` | 意思決定プロトコル |
| `permission-levels.md` | 権限等級分類基準（PG/SE/PM）**v4.0.0 新規** |

## 権限等級（PG/SE/PM）**v4.0.0 新規**

変更のリスクレベルに応じた三段階分類:

| 等級 | 動作 | 例 |
|------|------|-----|
| **PG** | 自動修正・報告不要 | フォーマット、typo、lint 修正 |
| **SE** | 修正後に報告 | テスト追加、内部リファクタリング |
| **PM** | 判断を仰ぐ（承認必須） | 仕様変更、ルール変更 |

**迷ったら SE級**（安全側に倒す）。詳細: `.claude/rules/permission-levels.md`

### PreToolUse hook

ファイルパスベースで PG/SE/PM を自動判定:
- `docs/specs/`, `docs/adr/`, `.claude/rules/`, `.claude/settings*.json` → **PM級**（block）
- `docs/` 配下（上記以外） → **SE級**（allow + ログ）
- `Read/Glob/Grep` → 常に許可

全判定結果は `.claude/logs/permission.log` に記録。

### フック分類の誤判定率計測

Wave 1 完了後に `.claude/logs/permission.log` を分析し、誤判定のベースラインを確立する:
1. `permission.log` からランダムに N 件サンプリング
2. 各判定の正否を人間がレビュー
3. 誤判定率 = 誤判定数 / サンプル数

## フェーズコマンド

| コマンド | 用途 | 禁止事項 |
|---------|------|---------|
| `/planning` | 要件定義・設計・タスク分解 | コード生成禁止 |
| `/building` | TDD実装 | 仕様なし実装禁止 |
| `/auditing` | レビュー・監査・リファクタ | PM級の修正禁止（PG/SE級は許可） |
| `/project-status` | 進捗状況の表示 | - |

## 承認ゲート

```
requirements → [承認] → design → [承認] → tasks → [承認] → BUILDING → [承認] → AUDITING
```

- 各サブフェーズ完了時に「承認」が必要
- 未承認のまま次に進むことは禁止

## セッション管理コマンド

| コマンド | 用途 | コンテキスト消費 |
|---------|------|----------------|
| `/quick-save` | 軽量セーブ（SESSION_STATE.md のみ） | 3-4% |
| `/quick-load` | 軽量ロード（SESSION_STATE.md のみ） | ~1% |
| `/full-save` | フルセーブ（commit + push + daily） | 約10% |
| `/full-load` | フルロード（状態確認 + 詳細報告） | 2-3% |

### セーブ/ロードの使い分け
- **普段のセーブ**: `/quick-save`（残量 25% 以下でも安全）
- **一日の終わり**: `/full-save`（残量に余裕があるとき）
- **前回の続き**: `/quick-load`（日常の再開）
- **数日ぶりの復帰**: `/full-load`（詳細な状態確認）

### StatusLine
画面下部にコンテキスト残量を常時表示（要 Python 3.8+）:
```
[Opus 4.6] ▓▓▓░░░░░░░ 70% $1.23
```
- 緑 (>30%): 安全
- 黄 (15-30%): 注意
- 赤 (<=15%): `/quick-save` 推奨

## サブエージェント

| エージェント | 呼び出し例 | フェーズ | Memory |
|-------------|-----------|---------|:------:|
| `requirement-analyst` | 「要件を整理して」 | PLANNING | project |
| `design-architect` | 「APIを設計して」 | PLANNING | project |
| `task-decomposer` | 「タスクを分割して」 | PLANNING | - |
| `tdd-developer` | 「TASK-001を実装して」 | BUILDING | - |
| `quality-auditor` | 「src/を監査して」 | AUDITING | - |
| `doc-writer` | 「ドキュメントを更新して」「仕様を策定して」 | ALL | - |
| `test-runner` | 「テストを実行して」 | BUILDING | - |
| `code-reviewer` | 「コードレビューして」 | AUDITING | auto |

Memory 列: `auto` = `.claude/agent-memory/<name>/` に知見を自発的に蓄積（CLAUDE.md 指示による）。

## スキル

| スキル | 用途 | 呼び出し例 |
|--------|------|-----------|
| `lam-orchestrate` | タスク分解・並列実行の自動調整 | 「lam-orchestrateで実行して」 |
| `ultimate-think` | AoT + Three Agents + Reflection 統合思考 | `/ultimate-think 議題` |
| `skill-creator` | スキル作成ガイド | 「新しいスキルを作りたい」 |
| `adr-template` | ADR作成テンプレート | `/adr-create` 実行時に自動適用 |
| `spec-template` | 仕様書作成テンプレート | 仕様書作成時に自動適用 |

## 状態管理

| ファイル | 用途 |
|---------|------|
| `.claude/current-phase.md` | 現在のフェーズ |
| `.claude/states/<feature>.json` | 機能ごとの進捗・承認状態 |
| `SESSION_STATE.md` | セッション間の引き継ぎ（自動生成） |
| `docs/artifacts/knowledge/` | プロジェクト知見の構造化蓄積（/retro 経由） |
| `.claude/agent-memory/` | Subagent の自動学習記録 |

## ワークフローコマンド

| コマンド | 用途 |
|---------|------|
| `/ship` | 論理グループ分けコミット（棚卸し -> 分類 -> コミット） |
| `/full-review <対象>` | 並列監査 + 全修正 + 検証（一気通貫） |
| `/release <version>` | リリース（CHANGELOG -> commit -> push -> tag） |
| `/wave-plan [N]` | Wave 計画策定（タスク選定・依存関係・リスク評価） |
| `/retro [wave\|phase]` | 構造化振り返り（KPT + 定量分析 + アクション抽出） |

## 補助コマンド

| コマンド | 用途 |
|---------|------|
| `/focus` | 現在のタスクに集中 |
| `/daily` | 日次振り返り（KPI 集計含む） |
| `/adr-create` | ADR作成支援 |
| `/security-review` | セキュリティレビュー |
| `/impact-analysis` | 変更の影響分析（PG/SE/PM 分類含む） |

## 参照ドキュメント (SSOT)

| ファイル | 内容 |
|---------|------|
| `docs/internal/00_PROJECT_STRUCTURE.md` | ディレクトリ構成・命名規則・状態管理 |
| `docs/internal/01_REQUIREMENT_MANAGEMENT.md` | 要件定義プロセス |
| `docs/internal/02_DEVELOPMENT_FLOW.md` | 開発フロー・TDD |
| `docs/internal/03_QUALITY_STANDARDS.md` | 品質基準 |
| `docs/internal/04_RELEASE_OPS.md` | リリース・デプロイ・緊急対応 |
| `docs/internal/05_MCP_INTEGRATION.md` | MCP 連携・MEMORY.md 運用ポリシー |
| `docs/internal/06_DECISION_MAKING.md` | 意思決定（3 Agents + AoT） |
| `docs/internal/07_SECURITY_AND_AUTOMATION.md` | コマンド安全基準（Allow/Deny List） |

## AoT（Atom of Thought）クイックガイド

**いつ使う？**（いずれかに該当）
- 判断ポイントが **2つ以上**
- 影響レイヤー/モジュールが **3つ以上**
- 有効な選択肢が **3つ以上**

**ワークフロー**
```
1. Decomposition: 議題を Atom に分解
2. Debate: 各 Atom で 3 Agents 議論
3. Synthesis: 統合結論 → 実装
```

**Atom テーブル形式**
```
| Atom | 内容 | 依存 | 並列可否(任意) |
```

## クイックリファレンス

**PLANNINGで実装を頼まれたら？**
→ 警告を表示し、3つの選択肢を提示

**成果物が完成したら？**
→ 承認を求めるメッセージを表示

**進捗を確認したい？**
→ `/project-status` を実行

**コンテキストが少なくなったら？**
→ `/quick-save` でセーブして `exit`

**次のセッションを始めるときは？**
→ `/quick-load` で前回の続きから（日常）
→ `/full-load` で詳細な状態確認（数日ぶり）

**仕様書はどこ？**
→ `docs/specs/`

**ADRはどこ？**
→ `docs/adr/`

**Rulesはどこ？**
→ `.claude/rules/`
