# Living Architect Model チートシート

## フェーズコマンド

| コマンド | 用途 | 禁止事項 |
|---------|------|---------|
| `/planning` | 要件定義・設計・タスク分解 | コード生成禁止 |
| `/building` | TDD実装 | 仕様なし実装禁止 |
| `/auditing` | レビュー・監査・リファクタ | 修正の直接実施禁止 |

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
   ├── 設計 (design-architect)
   ├── 仕様書作成 → docs/specs/
   ├── ADR作成 → docs/adr/
   └── タスク分割 (task-decomposer)

2. /building
   └── タスクごとに TDD サイクル (tdd-developer)
       Red → Green → Refactor → 次のタスク

3. /auditing
   └── 品質監査 (quality-auditor)
       ├── コード品質
       ├── ドキュメント整合性
       └── セキュリティ
```

## 既存コマンド（補助）

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

**仕様書はどこ？**
→ `docs/specs/`

**ADRはどこ？**
→ `docs/adr/`

**現在のフェーズは？**
→ `.claude/current-phase.md`
