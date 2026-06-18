**Version**: 0.1.0
**Created**: 2026-06-18
**Status**: draft
**Task Slug**: w7-t2b-large-route-demo
**用途**: W7-T2b 実機検証用 大タスク（L1 → l2-foreman → l3-executor 三層）

---

# design: w7-t2b-large-route-demo

## §1 目的 / Problem Statement

大タスク経路（L1 統括 → l2-foreman 班長 → l3-executor 末端の三層）が
実機で正しく動作することを検証するためのデモタスク。

題材は「プロジェクト雛形生成」とし、軽量フィクションとして実プロダクト変更を伴わない。
生成物は `docs/artifacts/goal-driven-demo/w7-t2b/output/` 配下にのみ書き込み、
既存ファイルを上書きしない。

### 大タスクとして選定した根拠

- **工程数: 3**（メタデータ生成 / README 雛形生成 / CHANGELOG 雛形生成）
  → 大タスク判定条件「工程数 ≥ 3」を充足
- **並列分解必要**: 工程 2 と工程 3 が工程 1 の出力に依存するが、工程 2 と 3 は相互独立
  → 大タスク判定条件「並列分解必要」を充足
- rubric 項目数: 7（中タスク条件「≤ 4」を外れる）
- 副作用が `output/` ディレクトリのみに限定され実プロダクトを汚さない

---

## §2 工程グラフ

依存関係を以下に示す（`|` は並列起動可能を表す）:

```
工程1（メタデータ生成・直列） → ┬─ 工程2（README 生成・並列）
                              └─ 工程3（CHANGELOG 生成・並列）
```

| 工程 | 順序 | 依存 | 並列可否 |
|------|------|------|---------|
| 工程 1 | 直列・最初 | なし | - |
| 工程 2 | 直列・後段 | 工程 1 の出力 | 工程 3 と並列起動可 |
| 工程 3 | 直列・後段 | 工程 1 の出力 | 工程 2 と並列起動可 |

合計工程数 = 3 / 最大並列度 = 2

---

## §3 各工程の責務

### 工程 1: メタデータ JSON 生成

- 入力: プロジェクト名 `lam-demo-app` / 説明 `LAM 大タスク経路検証用デモ` / バージョン `0.1.0`
- 出力: `output/metadata.json`
- 必須キー: `name` / `description` / `version`
- 担当: l3-executor（工程 1 専属）

### 工程 2: README 雛形生成

- 入力: 工程 1 の `metadata.json`
- 出力: `output/README-draft.md`
- 必須セクション: `## Overview`（`description` を引用）/ `## Setup`（任意の手順例）
- 50 行以上（rubric AC-7）
- 担当: l3-executor（工程 2 専属、工程 3 と並列）

### 工程 3: CHANGELOG 雛形生成

- 入力: 工程 1 の `metadata.json`
- 出力: `output/CHANGELOG-draft.md`
- 冒頭行: `# Changelog`
- `version` セクション（`## [0.1.0]` 等）を含む
- 50 行以上（rubric AC-7）
- 担当: l3-executor（工程 3 専属、工程 2 と並列）

---

## §4 入出力契約

### 読取対象（入力）

| ファイル | 用途 | 利用工程 |
|---------|------|---------|
| 本 design.md | 工程仕様・契約参照 | 全工程 |
| `rubric-draft.md` | L1 入力用受入条件草案（SKILL.md フロー[2]） | L1 |
| `rubric.md` | L1 が確定生成した受入条件 | 全工程（生成後） |
| `output/metadata.json` | 後段工程の入力 | 工程 2, 3 |

### 書込対象（出力）

| ファイル | 内容 | 権限等級 | 生成工程 |
|---------|------|---------|---------|
| `docs/artifacts/goal-driven-demo/w7-t2b/output/metadata.json` | プロジェクトメタデータ | SE | 工程 1 |
| `docs/artifacts/goal-driven-demo/w7-t2b/output/README-draft.md` | README 雛形 | SE | 工程 2 |
| `docs/artifacts/goal-driven-demo/w7-t2b/output/CHANGELOG-draft.md` | CHANGELOG 雛形 | SE | 工程 3 |

書込先ディレクトリは `output/` 直下のみ。サブディレクトリ作成禁止。

---

## §5 並列分解条件

工程 2 と工程 3 が並列起動可能である根拠:

1. **入力の共有**: 両工程とも `metadata.json` を読み取るのみで、相互に書込を行わない
2. **出力の独立**: `README-draft.md` と `CHANGELOG-draft.md` は別ファイル（書込競合なし）
3. **計算の独立**: 一方の工程の中間状態が他方の入力にならない
4. **失敗の隔離**: 工程 2 の失敗が工程 3 の進行を阻害しない（rubric は両出力を独立判定）

L1 統括は工程 1 完了確認後に l2-foreman を呼び出し、l2-foreman は工程 2 / 3 を
並列で l3-executor に分配する。

---

## §6 完了条件 / Success Criteria

受入条件は `rubric.md` の AC-1〜AC-7 を参照。grader が機械判定する。

| AC | 概要 |
|----|------|
| AC-1〜AC-2 | `metadata.json` の存在と必須キー |
| AC-3〜AC-4 | `README-draft.md` の存在と必須セクション |
| AC-5〜AC-6 | `CHANGELOG-draft.md` の存在と冒頭行 |
| AC-7 | 全ファイルが UTF-8 で 50 行以上 |

Critical = 0 かつ AC 全 7 件 Pass で Green State。

---

## スコープ外（やらないこと）

- `output/` 以外への書込
- 既存ファイル（`README.md` / `CHANGELOG.md` 等）の更新・削除
- パッケージ・依存関係の実インストール
- 雛形に記載するコマンドの実行
- サブディレクトリ作成

---

## 参照

| ドキュメント | 箇所 |
|-------------|------|
| `docs/specs/goal-driven-orchestration/design.md` | §9 三段階ルート / 大タスク判定条件 |
| `docs/specs/goal-driven-orchestration/handoff-format.md` | §3〜§4 受け渡し形式定義 |
| `.claude/agents/goal-driven-l2-foreman.md` | l2-foreman の責務定義 |
| `.claude/agents/goal-driven-l3-executor.md` | l3-executor の責務定義 |
