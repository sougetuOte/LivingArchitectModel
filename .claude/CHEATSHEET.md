# Living Architect Model チートシート

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
| `docs/internal/06_DECISION_MAKING.md` | 意思決定（3 Agents） |

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
