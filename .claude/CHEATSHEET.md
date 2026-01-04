# Living Architect Model チートシート

## ディレクトリ構造

```
.claude/
├── rules/                 # ガードレール・行動規範
├── commands/              # スラッシュコマンド
├── agents/                # サブエージェント
├── skills/                # テンプレート出力
├── states/                # 機能ごとの進捗状態
├── current-phase.md       # 現在のフェーズ
└── CHEATSHEET.md          # このファイル

CLAUDE.md                  # 憲法（コア原則のみ）
docs/internal/             # プロセス SSOT
docs/specs/                # 仕様書
docs/adr/                  # アーキテクチャ決定記録
```

## Rules ファイル一覧

| ファイル | 内容 |
|---------|------|
| `core-identity.md` | Living Architect 行動規範 |
| `phase-planning.md` | PLANNING ガードレール |
| `phase-building.md` | BUILDING ガードレール |
| `phase-auditing.md` | AUDITING ガードレール |
| `security-commands.md` | コマンド安全基準（Allow/Deny List） |
| `model-selection.md` | モデル選定ガイド |
| `decision-making.md` | 意思決定プロトコル |

## フェーズコマンド

| コマンド | 用途 | 禁止事項 |
|---------|------|---------|
| `/planning` | 要件定義・設計・タスク分解 | コード生成禁止 |
| `/building` | TDD実装 | 仕様なし実装禁止 |
| `/auditing` | レビュー・監査・リファクタ | 修正の直接実施禁止 |
| `/status` | 進捗状況の表示 | - |

## 承認ゲート

```
requirements → [承認] → design → [承認] → tasks → [承認] → BUILDING → [承認] → AUDITING
```

- 各サブフェーズ完了時に「承認」が必要
- 未承認のまま次に進むことは禁止

## サブエージェント

| エージェント | 呼び出し例 | フェーズ |
|-------------|-----------|---------|
| `requirement-analyst` | 「要件を整理して」 | PLANNING |
| `design-architect` | 「APIを設計して」 | PLANNING |
| `task-decomposer` | 「タスクを分割して」 | PLANNING |
| `tdd-developer` | 「TASK-001を実装して」 | BUILDING |
| `quality-auditor` | 「src/を監査して」 | AUDITING |

## 典型的なプロジェクトの進め方

```
1. /planning
   ├── 要件整理 (requirement-analyst)
   │   └── → 「承認」
   ├── 設計 (design-architect)
   │   └── → 「承認」
   └── タスク分割 (task-decomposer)
       └── → 「承認」

2. /building
   └── タスクごとに TDD サイクル (tdd-developer)
       Red → Green → Refactor → 次のタスク
       └── → 「承認」

3. /auditing
   └── 品質監査 (quality-auditor)
       └── → 「承認」→ 完了
```

## 状態管理

| ファイル | 用途 |
|---------|------|
| `.claude/current-phase.md` | 現在のフェーズ |
| `.claude/states/<feature>.json` | 機能ごとの進捗・承認状態 |

## 補助コマンド

| コマンド | 用途 |
|---------|------|
| `/focus` | 現在のタスクに集中 |
| `/daily` | 日次振り返り |
| `/adr-create` | ADR作成支援 |
| `/security-review` | セキュリティレビュー |
| `/impact-analysis` | 変更の影響分析 |

## 参照ドキュメント (SSOT)

| ファイル | 内容 |
|---------|------|
| `docs/internal/01_REQUIREMENT_MANAGEMENT.md` | 要件定義プロセス |
| `docs/internal/02_DEVELOPMENT_FLOW.md` | 開発フロー・TDD |
| `docs/internal/03_QUALITY_STANDARDS.md` | 品質基準 |
| `docs/internal/06_DECISION_MAKING.md` | 意思決定（3 Agents + AoT） |

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
→ `/status` を実行

**仕様書はどこ？**
→ `docs/specs/`

**ADRはどこ？**
→ `docs/adr/`

**Rulesはどこ？**
→ `.claude/rules/`
