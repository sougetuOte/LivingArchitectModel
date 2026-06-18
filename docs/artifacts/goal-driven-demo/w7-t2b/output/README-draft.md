# lam-demo-app

> **ステータス**: experimental / alpha
> **ライセンス**: MIT
> **バージョン**: 0.1.0

## Overview

LAM 大タスク経路検証用デモ

本プロジェクトは Living Architect Model（LAM）の goal-driven オーケストレーション機構における
大タスク経路（L1-orchestrator → l2-foreman → l3-executor の三層構成）を実証するデモアプリケーションです。
タスク `gd-20260618-001`（w7-t2b-large-route-demo）の工程 2 として、
`metadata.json` の情報を基に本 README ドラフトを自動生成しました。

- **リポジトリ**: https://github.com/example/lam-demo-app.git
- **ホームページ**: https://github.com/example/lam-demo-app
- **バグ報告**: https://github.com/example/lam-demo-app/issues
- **メンテナー**: LAM Project Team &lt;team@example.com&gt;

## Features

- goal-driven オーケストレーション（大タスク三層ルート）の動作実証
- L1-orchestrator / l2-foreman / l3-executor の役割分担デモ
- 並列度 2 での工程実行（工程 2 と工程 3 が並列処理対象）
- rubric 駆動の受入条件チェック（AC-1〜AC-7）
- UTF-8 / 50 行以上の成果物生成制約への準拠確認

## Requirements

| ランタイム | バージョン |
|-----------|-----------|
| Node.js   | >= 18.0.0 |
| Python    | >= 3.10   |

## Setup

### 1. リポジトリのクローン

```bash
git clone https://github.com/example/lam-demo-app.git
cd lam-demo-app
```

### 2. Python 依存パッケージのインストール

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Node.js 依存パッケージのインストール（必要な場合）

```bash
npm install
```

### 4. 環境変数の設定

```bash
cp .env.example .env
# .env を編集して必要な値を設定する
```

### 5. 動作確認

```bash
python -m pytest          # テスト実行
ruff check .              # lint
ruff format .             # フォーマット
```

## Usage

### goal-driven デモの実行

```bash
# L1-orchestrator を起動してデモタスクを投入する
python -m lam_demo.main --task-id gd-20260618-001 --route large

# 生成成果物の確認
ls docs/artifacts/goal-driven-demo/w7-t2b/output/
```

### 個別工程の実行

```bash
# 工程 1: metadata.json 生成
python -m lam_demo.phases.phase1

# 工程 2: README-draft.md 生成
python -m lam_demo.phases.phase2

# 工程 3: CHANGELOG-draft.md 生成
python -m lam_demo.phases.phase3
```

## Architecture

本デモは goal-driven オーケストレーション三層構成を採用しています。

```
L1-orchestrator
  └─ l2-foreman
       ├─ l3-executor (工程 1: metadata 生成)
       ├─ l3-executor (工程 2: README 生成)   ← 本ファイル生成元
       └─ l3-executor (工程 3: CHANGELOG 生成)
```

各 l3-executor は独立して動作し、rubric.md に定義された受入条件を満たすまで
差し戻しループ（最大 2 回）を実行します。

## Contributing

1. このリポジトリを Fork する
2. フィーチャーブランチを作成する（`git checkout -b feature/your-feature`）
3. 変更をコミットする（`git commit -m "feat: your feature description"`）
4. ブランチを Push する（`git push origin feature/your-feature`）
5. Pull Request を作成する

コントリビューション前に `docs/internal/` 配下の設計ドキュメントを参照してください。

## License

MIT License

Copyright (c) 2026 LAM Project Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

*本ファイルは goal-driven オーケストレーション工程 2（readme-draft-generation）により自動生成されました。*
*生成日: 2026-06-18 / task_id: gd-20260618-001*
