# Living Architect Model チートシート

## はじめに（初めて使う方へ）

> まず [概念説明スライド](docs/slides/index.html) で LAM の全体像を掴み、[クイックスタートガイド](QUICKSTART.md) で環境構築を行うことをお勧めします。

1. Claude Code CLI を起動する（LAM の設定は自動で読み込まれる）
2. PLANNING フェーズ（手動切替）で設計を開始し、要件を定義する
3. 要件確定後、LAM をプロジェクトに適応させる（AI に依頼するだけ）

```
典型的な流れ:
  PLANNING → 要件定義 → [承認] → 設計 → [承認] → タスク分解 → [承認]
  /building → TDD実装（Red → Green → Refactor）→ [承認]
  AUDITING → 品質監査 → [承認] → 完了
```

## ディレクトリ構造

```
.claude/
├── rules/                 # ガードレール・行動規範（自動ロード）
├── agents/                # サブエージェント
├── skills/                # オーケストレーション・テンプレート出力
├── states/                # 機能ごとの進捗状態
├── hooks/                 # PreToolUse / PostToolUse / Stop / PreCompact
├── logs/                  # permission.log, loop-*.txt（実行時生成）
└── current-phase.md       # 現在のフェーズ

CLAUDE.md                  # 憲法（コア原則のみ）
CHEATSHEET.md              # このファイル（クイックリファレンス）
docs/internal/             # プロセス SSOT
docs/specs/                # 仕様書
docs/adr/                  # アーキテクチャ決定記録
```

## Rules ファイル一覧

**ロード区分**: **R1** = 無条件ロード（毎セッション必ず読まれる / 常駐面の予算対象）/ **R2** = 条件ロード（frontmatter の `paths:` に一致したときのみ）。

| ファイル | 区分 | 内容 |
|---------|:----:|------|
| `core-identity.md` | R1 | Living Architect 行動規範（原理: Active Retrieval / 第 0 原則） |
| `phase-rules.md` | R1 | フェーズ別ガードレール（PLANNING/BUILDING/AUDITING） |
| `security-commands.md` | R1 | コマンド安全基準（許可マトリクス / 反面教師制約 D1・D4） |
| `decision-making.md` | R1 | 意思決定プロトコル（MAGI System + gabriel probe） |
| `permission-levels.md` | R1 | 権限等級分類基準（PG/SE/PM）＋ PM 級パス列挙の**正本** |
| `upstream-first.md` | R1 | 上流仕様優先原則（実在性 → 適合性の二段構え） |
| `terminology.md` | R1 | 用語ガイドライン（Project / Milestone / Step / Wave / Task） |
| `code-quality-guideline.md` | R1 | 重要度分類（Critical / Warning / Info）と Green State 条件 |
| `hga-summoning.md` | R1 | HGA 型 Fable 召喚規律（召喚ゲート / 下調べパイプライン） |
| `model-roster.md` | R1 | 層 → モデルの束縛（**モデル名を書いてよい唯一の場所**）/ 単価・envelope |
| `artifact-length-calibration.md` | R2 | 成果物の長さキャリブレーション |
| `model-delegation-prompting.md` | R2 | 委譲プロンプトの書き方（`paths: .claude/agents/*.md`） |
| `planning-quality-guideline.md` | R2 | 仕様書・設計書・タスクの品質基準 |
| `subprocess-encoding-convention.md` | R2 | サブプロセスの文字コード規約 |
| `test-result-output.md` | R2 | テスト結果ファイル出力ルール（JUnit XML） |
| `auto-generated/` | R1 / R2 | TDD 内省パイプラインの自動生成ルール（`trust-model.md` / `rule-001` = R1 / `rule-002` = R2） |

> **本表は網羅である**（2026-08-26 実測 = トップレベル 15 件 + `auto-generated/`）。**部分列挙にしないこと** —— 以前は 7 件のみを載せており、追加されたルールが約 4 か月にわたり一覧から漏れていた（列挙ドリフト / `docs/artifacts/2026-08-22-enumeration-drift-sweep.md`）。

## 権限等級（PG/SE/PM）

変更のリスクレベルに応じた三段階分類:

| 等級 | 動作 | 例 |
|------|------|-----|
| **PG** | 自動修正・報告不要 | フォーマット、typo、lint 修正 |
| **SE** | 修正後に報告 | テスト追加、内部リファクタリング |
| **PM** | 判断を仰ぐ（承認必須） | 仕様変更、ルール変更 |

迷った場合はまず**第 0 原則の 3 変数**（可逆性 / 復旧コスト / 確認のコスト）で判定し、**決まらない場合のみ** SE 級に丸める（安全側に倒す）。
正本: `.claude/rules/permission-levels.md` §迷った場合

### PreToolUse hook

ファイルパスベースで PG/SE/PM を自動判定:
- `docs/specs/`, `docs/adr/`, `docs/internal/`, `.claude/rules/`, `.claude/settings*.json`, ルート `CLAUDE.md` → **PM級**（block）
  （**正本は `permission-levels.md` §ファイルパスベースの分類** / 本行は写しであり、増減時は正本を先に直す）
- `docs/` 配下（上記以外） → **SE級**（allow + ログ）
- `Read/Glob/Grep` → 常に許可

全判定結果は `.claude/logs/permission.log` に記録。

### フック分類の誤判定率計測（NFR-14a）

NFR-14a の計測スクリプトは v5 Phase 1 で実装予定。Wave 1 段階では未実施。

計測実施時は `.claude/logs/permission.log` を分析し、誤判定のベースラインを確立する:
1. `permission.log` からランダムに N 件サンプリング
2. 各判定の正否を人間がレビュー
3. 誤判定率 = 誤判定数 / サンプル数

## フェーズコマンド

| コマンド | 用途 | 禁止事項 |
|---------|------|---------|
| `/building` | TDD実装 | 仕様なし実装禁止 |

## 承認ゲート

```
requirements → [承認] → design → [承認] → tasks → [承認] → BUILDING → [承認] → AUDITING
```

- 各サブフェーズ完了時に「承認」が必要
- 未承認のまま次に進むことは禁止

## セッション管理コマンド

| コマンド | 用途 | コンテキスト消費 |
|---------|------|----------------|
| `/quick-save` | セーブ（SESSION_STATE.md + ループログ + Daily） | 3-5% |
| `/quick-load` | ロード（SESSION_STATE.md + 関連ドキュメント特定） | 1-2% |

### セーブ/ロードの使い分け
- **セーブ**: `/quick-save`（SESSION_STATE.md + Daily。git操作なし）
- **ロード**: `/quick-load`（SESSION_STATE.md + 関連ドキュメント特定）
- **コミット**: `/ship`（git commit が必要なとき）

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
| `requirement-analyst` | 「要件を整理して」 | PLANNING | - |
| `design-architect` | 「APIを設計して」 | PLANNING | - |
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
| `magi` | 構造化意思決定（AoT + MAGI System + gabriel adversarial probe） | `/magi <議題>` |
| `lam-orchestrate` | タスク分解・並列実行 + `/magi` 統合 | 「lam-orchestrateで実行して」 |
| `adr-template` | ADR作成テンプレート | ADR 作成時に自動適用 |
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
| `/release <version>` | リリース（CHANGELOG -> commit -> tag -> push） |
| `/retro [wave\|phase]` | 構造化振り返り（KPT + 定量分析 + アクション抽出） |

## 参照ドキュメント (SSOT)

| ファイル | 内容 |
|---------|------|
| `docs/internal/00_PROJECT_STRUCTURE.md` | ディレクトリ構成・命名規則・状態管理 |
| `docs/internal/01_REQUIREMENT_MANAGEMENT.md` | 要件定義プロセス |
| `docs/internal/02_DEVELOPMENT_FLOW.md` | 開発フロー・TDD |
| `docs/internal/03_QUALITY_STANDARDS.md` | 品質基準 |
| `docs/internal/04_RELEASE_OPS.md` | リリース・デプロイ・緊急対応 |
| `docs/internal/05_MCP_INTEGRATION.md` | MCP 連携・MEMORY.md 運用ポリシー |
| `docs/internal/06_DECISION_MAKING.md` | 意思決定（MAGI System + AoT + gabriel adversarial probe） |
| `docs/internal/07_SECURITY_AND_AUTOMATION.md` | コマンド安全基準（Allow/Deny List） |
| `docs/internal/08_EXECUTION_DISCIPLINE.md` | 実行規律（帳簿単一・自己監査 14 項目・体験シミュ・F0-F4） |
| `docs/internal/99_reference_generic.md` | 汎用リファレンステンプレート |

## /magi（構造化意思決定）クイックガイド

**いつ使う？**（いずれかに該当）
- 判断ポイントが **2つ以上**
- 影響レイヤー/モジュールが **3つ以上**
- 有効な選択肢が **3つ以上**

**MAGI System**（エヴァンゲリオン由来）
```
MELCHIOR（科学者/推進者）— Value, Speed, Innovation
BALTHASAR（母/批判者）  — Risk, Security, Debt
CASPAR（女/調停者）     — Synthesis, Balance, Decision
```

**ワークフロー**
```
0. Decomposition: 議題を Atom に分解
1-3. MAGI Debate: 各 Atom で MELCHIOR/BALTHASAR/CASPAR 合議
4. gabriel adversarial probe: 独立 subagent が 6-fields JSON schema で adversarial verification（AoT 適用時のみ / ADR-0007 Accepted 2026-07-02 で旧 Reflection から置換）
5. Synthesis: 統合結論 → Action Items
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

**コンテキストが少なくなったら？**
→ `/quick-save` でセーブして `exit`

**次のセッションを始めるときは？**
→ `/quick-load` で前回の続きから（日常）
→ `/quick-load` でセッション復帰

**仕様書はどこ？**
→ `docs/specs/`

**ADRはどこ？**
→ `docs/adr/`

**Rulesはどこ？**
→ `.claude/rules/`
