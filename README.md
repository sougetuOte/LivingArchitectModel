# The Living Architect Model (LAM)

**governance 型 AI エージェント・ハーネス。**
AI エージェントに「何を独断でやってよいか / 何に人間の承認が要るか / **ルール自体をどう増減させるか**」を与える**統治層**です。

> **境界**: 実行基盤（runtime substrate）は Claude Code 本体が担います。LAM が提供するのはその上に載る統治層であり、**単体では動きません**。

**現在の版**: **v5.1.0**（2026-08-26 / [CHANGELOG.md](CHANGELOG.md)）

> **"AI は単なるツールではない。パートナーだ。"**

標準的なコーディングアシスタントは、指示されればたいてい何でもやります。LAM を配置すると、同じアシスタントがフェーズ規律・権限等級・承認ゲートの下で動き、**仕様なしの実装・独断の仕様変更・不可逆操作の素通し**を自ら止めるようになります。

## 初めての方へ

| ステップ | リソース | 所要時間 |
|---------|---------|---------|
| 1. 概念を理解する | [スライド](docs/slides/index.html) | 5分 |
| 2. 環境を構築する | [クイックスタート](QUICKSTART.md) | 10分 |
| 3. 日常の使い方を知る | [チートシート](CHEATSHEET.md) | 参照用 |

## コアコンセプト

### 統治（LAM 固有）

- **権限等級 (PG / SE / PM)**: すべての変更を「自動修正してよい (PG)」「やってから報告 (SE)」「**人間の判断を仰ぐ (PM)**」に三分割する。PM 級のファイルパスは事前に列挙され、hook が実行時に判定する。
- **第 0 原則**: 進むか確認するかを、AI の自信ではなく **可逆性 / 復旧コスト / 確認のコスト** の 3 変数で決める。「安全のための質問」も無料ではない（ユーザーの集中を 1 回中断する）と明示的に扱う。
- **Approval Gates (承認ゲート)**: requirements → design → tasks の各段でユーザー承認を必須にし、未承認のまま次へ進むことを禁じる。
- **誕生ゲート — ルールに天井と通貨を持たせる**: 常駐ルールに **上限 80 指令**を設け、**新しい条項を 1 つ入れるには既存の条項を 1 つ退出させる**（交換レート 1 対 1）。ルールが際限なく増えて誰も読まなくなる事態を、努力目標ではなく**会計**で防ぐ。台帳は `docs/artifacts/clause-gate-ledger.md`。
- **3.5 層委譲**: 統括 (L1) / 司令塔 (L1.5) / 実行 (L2) / 採点 (L3) に役割を分ける。モデル名の束縛は**ロスター 1 枚**に集約し、世代交代でそこだけを直せば済むようにする。

### 品質

- **Gatekeeper Role (門番の役割)**: 低品質なコードや曖昧な仕様がコードベースに混入するのを阻止する。
- **Zero-Regression (退行ゼロ)**: 厳格な影響分析と TDD サイクルにより、リグレッション（先祖返り）を防ぐ。
- **Multi-Perspective Decisions (多角的意思決定)**: MAGI System（MELCHIOR・BALTHASAR・CASPAR）＋ **gabriel probe** —— 合議の結論を、**独立したコンテキストの検証者が敵対的に再検証**する。
- **Phase Control (フェーズ制御)**: PLANNING / BUILDING / AUDITING の明示的な切り替えにより、「つい実装してしまう」問題を防止。
- **Command Safety (コマンド安全基準)**: Allow / Ask / Deny の**明示列挙**（ワイルドカード非依存）による、偶発的な事故の防止。
- **Active Retrieval (能動的検索)**: 受動的な記憶に頼らず、能動的にコンテキストを検索・ロードする。
- **Living Documentation (生きたドキュメント)**: ドキュメントをコードと同様に扱い、**同一の不可分な単位**として更新する。

## 収録内容

### 憲法・チートシート

| ファイル | 説明 |
|---------|------|
| `CLAUDE.md` | 憲法。AI のアイデンティティ、基本原則、権限を定義 |
| `CHEATSHEET.md` | クイックリファレンス。コマンド・エージェント一覧 |

### 運用プロトコル (`docs/internal/`)

| ファイル | 説明 |
|---------|------|
| `00_PROJECT_STRUCTURE.md` | 物理構成と命名規則 |
| `01_REQUIREMENT_MANAGEMENT.md` | アイデアから仕様へ (Definition of Ready) |
| `02_DEVELOPMENT_FLOW.md` | 影響分析、TDD、レビューサイクル |
| `03_QUALITY_STANDARDS.md` | コーディング規約と品質ゲート |
| `04_RELEASE_OPS.md` | デプロイと緊急対応プロトコル |
| `05_MCP_INTEGRATION.md` | MCP サーバー連携・MEMORY.md 運用ポリシー（オプション） |
| `06_DECISION_MAKING.md` | 意思決定プロトコル (MAGI System + AoT + gabriel probe) |
| `07_SECURITY_AND_AUTOMATION.md` | コマンド実行の安全基準 (Allow/Deny List) |
| `99_reference_generic.md` | 一般的な助言とベストプラクティス (Non-SSOT) |

### Claude Code 拡張 (`.claude/`)

| ディレクトリ | 説明 |
|-------------|------|
| `rules/` | 行動規範・ガードレール（自動ロード） |
| `agents/` | 専門サブエージェント（要件分析、設計、TDD等） |
| `skills/` | スキル（タスクオーケストレーション、テンプレート出力） |

## 使い方

> **`docs/private/` について**: このディレクトリは LAM 開発者個人の統治記録です。テンプレート・clone・ZIP のいずれの経路で入手した場合も、どこからもロードされないため**そのまま削除して構いません**。

### Option A: テンプレートとして使用 (推奨)

GitHub 上でリポジトリページ上部の **"Use this template"** ボタンをクリックし、この構成済み構造で新しいリポジトリを作成してください。

**参考ドキュメント:**
- [テンプレートからリポジトリを作成する - GitHub Docs (日本語)](https://docs.github.com/ja/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template)
- [Creating a repository from a template - GitHub Docs (English)](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template)

### Option B: git clone

```bash
git clone https://github.com/sougetuOte/LivingArchitectModel.git my-project
cd my-project
rm -rf .git && git init
```

LAM は `.claude/`、`docs/internal/`、`CLAUDE.md` が連携して動作するため、一式をそのまま使うことを推奨します。

### Option C: 既存プロジェクトへの導入

既に開発が進んでいるプロジェクトに LAM を導入する場合:

1. プロジェクト内に作業用ディレクトリを作り、LAM リポジトリの ZIP をそこに展開する

```bash
mkdir _lam_source
cd _lam_source
# ZIP をダウンロードして展開
```

2. Claude Code を起動し、以下のように指示する:

```
_lam_source/ にある Living Architect Model をこのプロジェクトに配置してください。
```

3. 既存の要件定義や仕様書がある場合は、それを参照させて適応を指示する:

```
<要件定義ファイル> を参照して、LAM の全ファイルを確認し必要な部分を適応させてください。
```

既存の要件がない場合は、適応せずそのまま使い始めてよい。PLANNING フェーズで要件定義を行った後に適応すればよい。

## フェーズコマンド

| コマンド | 用途 | 禁止事項 |
|---------|------|---------|
| `/building` | TDD実装 | 仕様なし実装禁止 |

### 承認ゲート

```
requirements → [承認] → design → [承認] → tasks → [承認] → BUILDING → [承認] → AUDITING
```

各サブフェーズ完了時にユーザー承認が必要。未承認のまま次に進むことは禁止。

## コマンドを覚える必要はありません

以下にコマンドやエージェントの一覧が続きますが、暗記する必要はありません。AI に「今の状況で使えるコマンドは？」と聞けば、適切なものを提案してくれます。まずは PLANNING フェーズから始めてみてください。

## サブエージェント

| エージェント | 用途 | 推奨フェーズ |
|-------------|------|-------------|
| `requirement-analyst` | 要件分析・ユーザーストーリー | PLANNING |
| `design-architect` | API設計・アーキテクチャ | PLANNING |
| `task-decomposer` | タスク分割・依存関係整理 | PLANNING |
| `tdd-developer` | Red-Green-Refactor 実装 | BUILDING |
| `quality-auditor` | 品質監査・セキュリティ | AUDITING |
| `doc-writer` | ドキュメント作成・仕様策定・更新 | ALL |
| `test-runner` | テスト実行・分析 | BUILDING |
| `code-reviewer` | コードレビュー（LAM品質基準） | AUDITING |
| `gabriel` | MAGI 合議の結論を**独立コンテキストで敵対的に検証**（読み取り専用） | ALL |
| `goal-driven-l2-foreman` | 大タスクの工程分解・L3 への分配（班長） | ALL |
| `goal-driven-l3-executor` | 実装・テスト実行の末端（自律 spawn 禁止） | BUILDING |
| `goal-driven-grader` | rubric との突合・合否判定（作業者と別コンテキスト） | ALL |

## セッション管理コマンド

| コマンド | 用途 |
|---------|------|
| `/quick-save` | セーブ（SESSION_STATE.md + ループログ + Daily） |
| `/quick-load` | ロード（SESSION_STATE.md + 関連ドキュメント特定） |

## ワークフローコマンド

| コマンド | 用途 |
|---------|------|
| `/ship` | 論理グループ分けコミット（棚卸し -> 分類 -> コミット） |
| `/full-review <対象>` | 並列監査 + 全修正 + 検証（一気通貫） |
| `/release <version>` | リリース（CHANGELOG -> commit -> tag -> push） |
| `/retro [wave\|phase]` | 振り返り（Wave/Phase 完了時の学習サイクル） |

## 推奨モデル

| フェーズ | 推奨モデル |
|---------|----------|
| **PLANNING** | Claude Opus / Sonnet |
| **BUILDING** | Claude Sonnet (単純作業なら Haiku) |
| **AUDITING** | Claude Opus (Long Context) |

## 環境要件

| 要件 | 用途 | 必須/任意 |
|------|------|----------|
| [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) | AI アシスタント実行環境 | 必須 |
| Python 3.8+ | フック・StatusLine に必要 | 必須 |
| Git | バージョン管理 | 必須 |
| [gitleaks](https://github.com/gitleaks/gitleaks) | シークレットスキャン（`/full-review` の G5 チェック） | 推奨 |

gitleaks が未インストールの場合、`/full-review` で Green State G5 が FAIL になります。不要な場合は **`.claude/review-config.json`**（任意ファイル / 無ければ新規作成）に `"gitleaks_enabled": false` を設定してください。

## ライセンス

MIT License
