# LAM クイックスタートガイド

> LAM の概念をまだ知らない方は、先に [概念説明スライド](docs/slides/index.html) をご覧ください。

## 前提条件

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) がインストール済み
- Git がインストール済み
- GitHub アカウント

## Step 1: テンプレートからリポジトリを作成

GitHub で「Use this template」ボタンをクリックし、新しいリポジトリを作成。

[Create from template](https://github.com/sougetuOte/LivingArchitectModel/generate)

または手動でクローン:

```bash
git clone https://github.com/sougetuOte/LivingArchitectModel.git my-project
cd my-project
rm -rf .git && git init
```

## Step 2: Claude Code を起動して `/planning` で要件定義

```bash
claude
```

Claude Code を起動すると、LAM の設定（`.claude/`、`CLAUDE.md` 等）が自動的に読み込まれる。
`claude init` は不要 — テンプレートに必要なファイルはすべて含まれている。

起動したら `/planning` と入力して PLANNING フェーズを開始し、アイデアを伝える:

```
/planning

「〇〇を管理する Web アプリを作りたい」
```

AI が壁打ち相手になりながら、承認ゲートを一つずつ通過していく:

```
1. アイデアを自然言語で伝える
2. AI と壁打ちしながら要件を具体化
3. 要求仕様書（docs/specs/）が出力される → 「承認」
4. ADR（技術選定の記録）と設計書が出力される → 「承認」
5. タスク分解（docs/tasks/）が出力される → 「承認」
```

全ての承認ゲートを通過して初めて BUILDING に進める。
この丁寧なプロセスが LAM の品質を支えている。

## Step 3: プロジェクトに合わせて LAM を適応

要件が固まったら、LAM をプロジェクトに合わせて適応させる。AI に一言伝えるだけでよい:

```
要件定義が完了したので、LAM の全ファイルを確認して必要な部分をこのプロジェクトに適応させてください。
```

### 適応すべきファイル（プロジェクト固有の内容に書き換え）

| ファイル | 適応内容 |
|---------|---------|
| `CLAUDE.md` | Identity セクションをプロジェクト名・説明に変更 |
| `README.md` / `README_en.md` | プロジェクトの説明に書き換え |
| `CHANGELOG.md` | 白紙から開始 |
| `docs/specs/` | LAM 自体の仕様書を削除 |
| `docs/adr/` | LAM 固有の ADR を削除 |
| `QUICKSTART.md` 等 | LAM 導入ガイドなので削除可 |

### そのままでよいファイル（汎用基盤）

| ディレクトリ | 理由 |
|-------------|------|
| `.claude/rules/` | 汎用ルール（どのプロジェクトでも有効） |
| `.claude/hooks/` | 免疫システム |
| `.claude/commands/` | フェーズ制御・ワークフロー |
| `.claude/agents/`, `skills/` | 専門サブエージェント・スキル |
| `.claude/agent-memory/` | Subagent のセッション跨ぎ学習記録 |
| `docs/internal/` | 開発プロセスの SSOT |
| `docs/artifacts/knowledge/` | プロジェクト知見の蓄積（`/retro` 経由） |
| `CHEATSHEET.md` | コマンドリファレンス（汎用） |

> 迷ったら [スライド](docs/slides/index.html) を見てプロジェクト構成の全体像を確認しよう。

## Step 4: 最初の BUILDING セッション

`/building` と入力して TDD 実装開始。

AI が自律的に Red-Green-Refactor サイクルを回す。
完了したら `/full-review` で自動監査 → Green State を目指す。

## よくある質問

### Q: CLAUDE.md は自分で編集すべき？

A: Step 3 で AI に適応を任せるのが最も簡単。手動で変えるなら Identity セクションのプロジェクト説明。

### Q: docs/internal/ は変更すべき？

A: 最初はそのまま使うことを推奨。プロジェクト固有の方法論が確立してきたら、徐々にカスタマイズ。

### Q: Python は必須？

A: **必須です。** フックスクリプトと StatusLine が Python 3.8+ を使用します。

#### セットアップ（まだ Python がない場合）

**推奨: uv（最速・モダン）**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # Linux/macOS
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

uv venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

uv pip install -r requirements-dev.txt  # テストを実行する場合のみ
```

**フォールバック: venv（追加インストール不要）**

```bash
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

pip install -r requirements-dev.txt     # テストを実行する場合のみ
```

> pyenv, conda 等を既に使っている場合はそちらでも OK です。
> Python 3.8 以上であれば動作します。
> Windows で `python3` コマンドが存在しない場合は `py` または `python` を使用してください。

### Q: セッションが切れたら？

A: `/quick-load` で即座に復帰。

### Q: 仕様書のフォーマットは決まっている？

A: テンプレートスキル (spec-template) が自動適用される。自由記述でも OK。

## 次のステップ

1. [新規プロジェクトスライド](docs/slides/story-newproject.html) でフロー全体を追体験（10分）
2. 実際に `/planning` を始める
3. [CHEATSHEET.md](CHEATSHEET.md) を手元に置いて日常運用
4. 慣れてきたら [docs/internal/](docs/internal/) でプロセス SSOT を深掘り
