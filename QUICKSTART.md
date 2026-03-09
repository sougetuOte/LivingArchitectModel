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

## Step 2: Claude Code を起動してプロジェクトに適応

```bash
claude
```

起動したら、AI に指示する:

```
CLAUDE.md を読み込んで、Living Architect として初期化してください。
このプロジェクトに合わせて CLAUDE.md、.claude/、docs/internal/ を適応させてください。
docs/specs/ にある LAM 自体の仕様書は不要なので整理してください。
```

AI がプロジェクトの内容を分析し、LAM の設定を適応させてくれる。
この段階で AI と相談しながら、プロジェクトに合った調整を行うとよい。

### AI に任せなくていいこと（最初は）

以下はそのまま使える汎用的な部品なので、特に触らなくてよい:

- `.claude/rules/` --- 汎用ルール
- `.claude/hooks/` --- 免疫システム
- `.claude/commands/` --- フェーズ制御

## Step 3: 最初の PLANNING セッション

`/planning` と入力して PLANNING フェーズを開始。承認ゲートを一つずつ通過していく:

```
1. アイデアを自然言語で伝える
2. AI と壁打ちしながら要件を具体化
3. 要求仕様書（docs/specs/）が出力される → 「承認」
4. ADR（技術選定の記録）と設計書が出力される → 「承認」
5. タスク分解（docs/tasks/）が出力される → 「承認」
```

全ての承認ゲートを通過して初めて BUILDING に進める。
この丁寧なプロセスが LAM の品質を支えている。

## Step 4: 最初の BUILDING セッション

`/building` と入力して TDD 実装開始。

AI が自律的に Red-Green-Refactor サイクルを回す。
完了したら `/full-review` で自動監査 → Green State を目指す。

## よくある質問

### Q: CLAUDE.md は自分で編集すべき？

A: Step 2 で AI に適応を任せるのが最も簡単。手動で変えるなら Identity セクションのプロジェクト説明。

### Q: docs/internal/ は変更すべき？

A: 最初はそのまま使うことを推奨。プロジェクト固有の方法論が確立してきたら、徐々にカスタマイズ。

### Q: Python は必要？

A: StatusLine（コンテキスト残量表示）を使う場合のみ。必須ではない。

### Q: セッションが切れたら？

A: `/quick-load` で即座に復帰。数日ぶりなら `/full-load`。

### Q: 仕様書のフォーマットは決まっている？

A: テンプレートスキル (spec-template) が自動適用される。自由記述でも OK。

## 次のステップ

1. [新規プロジェクトスライド](docs/slides/story-newproject.html) でフロー全体を追体験（10分）
2. 実際に `/planning` を始める
3. [CHEATSHEET.md](CHEATSHEET.md) を手元に置いて日常運用
4. 慣れてきたら [docs/internal/](docs/internal/) でプロセス SSOT を深掘り
