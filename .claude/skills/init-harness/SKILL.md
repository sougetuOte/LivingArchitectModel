---
name: init-harness
description: |
  憲法型ハーネスフレームワーク (design-mode / build-mode / audit-mode 三フェーズ規律 +
  Three Agents Model + セッション継続性) を新規 or 既存プロジェクトに opt-in で適用する
  初期化スキル。規約ディレクトリとテンプレートファイルを生成し、
  .claude/harness.json でハーネスバージョンを管理する。
  3状態判定 (ハーネス適用済 / 既存非ハーネス / 完全新規) で適切な挙動に分岐する。
  Use when the user asks to initialize harness, scaffold project structure, or runs `/init-harness`.
---

# /init-harness — ハーネス初期化スキル (LAM プロジェクトローカル)

## 目的

憲法型ハーネスを単一コマンドでプロジェクトに適用する。
全ハーネススキル (design-mode, build-mode, audit-mode, ship, retro 等) の前提条件を保証する。

**特殊性**: 本スキルは **CLAUDE.md を生成する側**。他スキルと異なり、対象プロジェクトに
CLAUDE.md が存在しない状態でも動作する (ブートストラップ責務)。

**LAM オーバーライド**: 本プロジェクト版は user-global skill に対し LAM 固有の禁止事項
(`~/.claude/settings.json` への書き換え禁止 / ADR-0008 LAM 側書き換えゼロ原則) を明示している。
user-global 版を継承する関係ではなく、本ファイル単体で完結する。

> **注記 (ADR-0008 v0.3 / 2026-06-30)**: 旧 Step 0「AutoMode advisory 初回比較表自動表示」は
> 承認 prompt ノイズ過大により撤回。AutoMode 認知は `CLAUDE.md` 冒頭
> `## Execution Permission Modes (Advisory)` および `docs/internal/07_SECURITY_AND_AUTOMATION.md`
> § AutoMode Advisory 等の文書で代替する。本 skill は AutoMode advisory を含まない。

## 引数

```
/init-harness            # 通常実行
/init-harness --dry-run  # 副作用なしの事前確認
```

## 横断制約 (全 Step 共通)

- **NFR-01**: 書き込み操作は全てユーザー承認後 (dry-run 除く)
- **NFR-02**: クロスプラットフォーム動作 (Windows / Unix のパス区切り・改行コードに配慮)
- **NFR-03**: 既存ファイルは承認なしに上書きしない
- **NFR-04**: 対話除く実行時間は 10 秒以内

---

## Step 1: 状態判定 + 分岐 (FR-02 + FR-07)

### 判定ロジック (疑似コード)

```sh
if [ -f ".claude/harness.json" ]; then
    state="①ハーネス適用済"
    echo "既存ハーネス検出: harness_version=$(jq -r .harness_version .claude/harness.json)"
    goto Step2
elif [ -d ".claude" ] || has_source_files || [ -d "docs" ]; then
    state="②既存非ハーネス"
    scan_existing_structure
    echo "⚠ 既存プロジェクトを検出 (ハーネス未適用)"
    read -p "ハーネスを適用しますか? (y/N): " confirm
    [ "$confirm" = "y" ] || abort
    goto Step2
else
    state="③完全新規"
    goto Step3
fi
```

### `has_source_files` の判定

以下の拡張子いずれかが存在: `.js .ts .py .go .rs .java .rb .php .cs .cpp .c .h`

### 確認プロンプト文言 (状態②)

```
⚠ 既存プロジェクトを検出しました (ハーネス未適用)

検出された構造:
  - docs/        (XX ファイル)
  - src/         (YY ファイル)
  - package.json

このプロジェクトにハーネスを適用すると、新規ディレクトリ・ファイルが追加されます。
既存ファイルは破壊しません (上書き時は個別承認)。

続行しますか? (y/N):
```

---

## Step 2: 上書き方針確認 (状態①② のみ、FR-05)

既存テンプレートファイルがある場合のみ実施。

```
既存ファイルが検出されました:
  - CLAUDE.md
  - CHEATSHEET.md

上書き方針を選択してください:
  1) skip          — 既存ファイルは触らない
  2) overwrite     — 全て上書き (注意)
  3) ask-per-file  — ファイルごとに確認 (推奨)

選択 (1-3):
```

---

## Step 3: 生成プラン提示 (FR-09 dry-run はここまで)

```
=== 生成プラン ===

ディレクトリ (mkdir -p):
  ✚ .claude/
  ✚ .claude/states/
  ✚ docs/specs/
  ✚ docs/adr/
  ✚ docs/tasks/      (空 → .gitkeep 配置)
  ✚ docs/artifacts/  (空 → .gitkeep 配置)

ファイル (新規 or 上書き):
  ✚ CLAUDE.md                       [新規]
  ✚ CHEATSHEET.md                   [新規]
  ✚ CHANGELOG.md                    [新規]
  ✚ SESSION_STATE.md                [新規]
  ✚ .claude/current-phase.json      [新規]
  ✚ .claude/harness.json            [新規]

実行しますか? (y/N):
```

`--dry-run` の場合: ここで終了。`✓ dry-run 完了 — 変更なし` を表示。

---

## Step 4: 実行 (FR-03, FR-04, FR-06, FR-10)

承認後、以下を順次実行:

### 4.1 ディレクトリ作成 (FR-03)

```sh
for d in $DIRECTORIES; do
    mkdir -p "$d"
    case "$d" in
        docs/tasks|docs/adr|docs/artifacts|.claude/states)
            touch "$d/.gitkeep"
            ;;
    esac
done
```

### 4.2 テンプレート配置 (FR-04, FR-06, FR-10)

各テンプレートは下記「テンプレート定義」セクションのインライン文字列を使用。
`CLAUDE.md` のプロジェクト概要欄は `<!-- /design-mode で記入 -->` プレースホルダー (FR-06)。

### 4.3 `.claude/harness.json` 記録

新規作成時:

```json
{
  "harness_version": "1.0.0",
  "applied_at": "<ISO 8601 現在時刻>",
  "enabled_skills": [
    "init-harness", "design-mode", "build-mode", "audit-mode",
    "clarify", "magi", "ship", "retro",
    "session-save", "session-load", "project-status",
    "spec-template", "adr-template", "ui-design-guide"
  ],
  "notes": ""
}
```

既存 harness.json がある場合は **既存内容を保持** する (他キーを破壊しない)。

---

## Step 5: 次アクション推奨 (FR-08)

```
✓ ハーネス初期化完了 (harness_version: 1.0.0)

作成されたファイル: 6 件
作成されたディレクトリ: 6 件

次のステップ:
  /design-mode    — 設計フェーズに入る (推奨)
  /project-status — 現状確認

参考:
  CHEATSHEET.md — スキルコマンド一覧。不明時はここを確認
  CLAUDE.md     — プロジェクト概要欄は空。/design-mode 内で記入される
```

---

## テンプレート定義 (インライン文字列)

> **注**: 以下は LLM が SKILL 実行時に書き出すべき内容のリファレンス。
> 各ファイルの完全版は本プロジェクト直下の初期化済みファイルを参照。

### `CLAUDE.md` (FR-06 プレースホルダー)

```markdown
# CLAUDE.md — <project-name>

LLM (Claude Code) 向けプロジェクト規約。**不変に近いルール**のみを記載する。

## プロジェクト概要

<!-- /design-mode で記入 -->

## ハーネス規律

(フェーズ遷移、ディレクトリ規約 — 標準テンプレを展開)

## 禁止事項

- `.claude/` 配下の不用意な書き換え
- `--no-verify` の使用 (明示指示時を除く)
```

### `CHEATSHEET.md` (FR-10 — クイックコマンド表入り、固有セクション空)

```markdown
# CHEATSHEET.md — <project-name>

## クイックコマンド

| やりたいこと | コマンド |
|:-----------|:--------|
| 仕様書を書き始める | `/design-mode` → `spec-template` |
| 実装フェーズに入る | `/build-mode` |
| 監査する | `/audit-mode` |
| 文書精緻化 | `/clarify <path>` |
| 重要判断 | `/magi` (LLM提案時) |
| コミット | `/ship` |
| 振り返り | `/retro` |
| 状況保存/復帰 | `/session-save` / `/session-load` |
| 状態確認 | `/project-status` |

## このプロジェクトのクセ

(未記入)

## ハマりどころ

(未記入)

## Try

(未記入)
```

### `CHANGELOG.md`

Keep a Changelog 1.1.0 雛形 + `[Unreleased]` セクション。

### `SESSION_STATE.md`

完了タスク / 進行中 / 次のステップ / 変更ファイル / 未解決問題 / 削除禁止メモ の見出しのみ。

### `.claude/current-phase.json`

```json
{
  "phase": "none",
  "phase_approved": false,
  "next_recommended": "design",
  "updated_at": "<ISO 8601>",
  "notes": "Harness initialized. Start with /design-mode."
}
```

---

## 禁止事項

- ユーザー承認なしの上書き (NFR-01, NFR-03)
- `CLAUDE.md` への内容収集 (design-mode の責務)
- `tasks/` 省略オプションの提示 (常に作成)
- 自身の SKILL.md への書き込み (ハーネス自己破壊防止)
- `~/.claude/settings.json` への書き換え (ADR-0008 LAM 側書き換えゼロ原則 / PM 級ファイル + 書き資格なし)

## 関連

- 受け入れ仕様 (プロジェクト側): `docs/specs/init-harness/spec.md`
- AutoMode 関連 (Advisory のみ / 本 skill は advisory step を含まない): `docs/adr/0008-approval-gate-redesign.md` v0.3
- 後続スキル: `design-mode`
- マルチセッション環境考慮 (ユーザーメモリ領域 `~/.claude/projects/<key>/memory/reference_claude_code_desktop.md` 参照): 並行 init は最後勝ち、ロック機構なし (Open issue)
