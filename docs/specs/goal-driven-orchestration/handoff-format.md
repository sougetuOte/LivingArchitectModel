**Version**: 0.1.0
**Status**: draft
**作成日**: 2026-06-17
**対応要件**: AC-15（FR-10: lam-orchestrate 接続）
**参照設計**: `docs/specs/goal-driven-orchestration/design.md` §16（v0.3.3）

---

# lam-orchestrate → goal-driven 受け渡し形式定義

## 1. 概要

### 責務分担

| スキル | フェーズ | 責務 |
|--------|---------|------|
| `lam-orchestrate` | PLANNING | タスクの並列設計・分解・設計文書生成 |
| `goal-driven` | BUILDING | rubric ファーストの自己修正実装ループ |
| `full-review` | AUDITING | 納品前最終検収 |

`lam-orchestrate` は PLANNING フェーズの成果物（設計文書・rubric 素案・タスクリスト）を
`docs/tasks/<task-slug>/` に配置して `goal-driven` スキルに受け渡す。
`goal-driven` はこれらを入力として BUILDING フェーズの自己修正ループを開始する。

### 本書の位置づけ

本書は受け渡しインターフェース（ディレクトリ構造・各ファイルの内容仕様・`goal-driven` 側の処理方法）を定義し、
AC-15「lam-orchestrate → 新スキルへの成果物受け渡し形式が定義されていること」要件を満たす。

### AC-15 との対応

AC-15 は requirements.md §8 に定義された受け入れ条件であり、FR-10（lam-orchestrate 接続）の充足確認基準である。
本書各章の対応は「§7 AC-15 充足の根拠」に示す。

---

## 2. パイプライン位置

> 引用元: design.md §16.1

```
lam-orchestrate（PLANNING 並列実行）
     ↓ 成果物受け渡し
goal-driven スキル（BUILDING 自己修正ループ）
     ↓ 最終成果物
full-review（納品前検収）
```

`lam-orchestrate` の出力（設計文書・rubric 素案）を `goal-driven` スキル フロー[2] の入力として受け取る。
本スキルは `lam-orchestrate`（上流）と `full-review`（下流）の間に位置する直列パイプラインの中間段である。

---

## 3. ディレクトリレイアウト

`lam-orchestrate` が生成する成果物は、以下の標準ディレクトリ構造で配置する。

```
docs/tasks/<task-slug>/
  ├── design.md         # 必須: lam-orchestrate 経由 design-architect が生成
  ├── rubric-draft.md   # 任意: lam-orchestrate 経由 doc-writer が生成した場合のみ存在
  └── task-list.md      # 必須: lam-orchestrate 経由 task-decomposer が生成
```

**`<task-slug>`**: タスクを一意に識別するケバブケースの識別子（例: `auth-refactor`, `w6-t1-handoff-spec`）。
`goal-driven` スキルの起動引数 `/goal-driven <task-slug>` と一致する。

### ファイルの必須 / 任意 分類

| ファイル | 区分 | 不在時の動作 |
|---------|------|-----------|
| `design.md` | **必須** | `goal-driven` は起動を拒否する（MUST NOT start without design.md） |
| `task-list.md` | **必須** | `goal-driven` は起動を拒否する（MUST NOT start without task-list.md） |
| `rubric-draft.md` | **任意** | 不在時は L1 指揮者がゼロから rubric を生成する（§6 参照） |

---

## 4. 各ファイルの内容仕様

### 4.1 design.md

`lam-orchestrate` が `design-architect` サブエージェントを通じて生成する設計文書。

**必須セクション**:

| セクション | 内容 | 必須理由 |
|-----------|------|---------|
| 目的 / Problem Statement | 何を解決するか | L1 の rubric 生成の前提情報 |
| 完了条件 / Success Criteria | 何をもって成功とするか | rubric 項目の源泉となる |
| インターフェース定義 | 公開 API・ファイル形式・フィールド名 | L1 の rubric 生成・grader の照合基準 |

**最低限の項目**:

- 機能要件（FR）または受け入れ条件（AC）の列挙
- 出力ファイル・ディレクトリのパスと形式
- 依存関係・前提条件

**`goal-driven` での使用**:
- フロー[2] で L1 指揮者が `rubric.md` を生成する際の参照資料として使用する（design §16 より）
- `rubric-draft.md` が存在しない場合は `design.md` のみから rubric をゼロ生成する

### 4.2 rubric-draft.md

`lam-orchestrate` が `doc-writer` サブエージェントを通じて生成する rubric 素案。
L1 指揮者が確定・補完するための **素案（draft）** であり、そのまま `rubric.md` として使用してはならない（MUST NOT）。

**スキーマ（design §16.2 準拠）**:

> 引用元: design.md §16.2

```markdown
# rubric-draft: <タスク名>（素案）

## 検証候補項目（L1 指揮者が確定・追記すること）

| # | チェック項目（素案） | 検証方法候補 | 備考 |
|---|-------------------|------------|------|
| 1 | FR-X の仕様フィールド名一致 | grader 判定（候補） | |
| 2 | 全テスト通過 | run: pytest（候補） | |
```

**スキーマ詳細**:

| フィールド | 説明 | 例 |
|-----------|------|-----|
| タイトル行 `# rubric-draft: <タスク名>（素案）` | 素案であることを明示するヘッダ | `# rubric-draft: auth-refactor（素案）` |
| `## 検証候補項目` | 素案項目の表。L1 が確定することを注記として必須付記 | 上記スキーマ参照 |
| `#` | 項目番号（整数） | `1`, `2`, `3` |
| `チェック項目（素案）` | 検証すべき要件・仕様の素案記述 | `FR-1 の仕様フィールド名一致` |
| `検証方法候補` | 検証方法の候補（`run:` / `grader` / `human` のいずれか） | `grader 判定（候補）` |
| `備考` | 不明点・L1 への指示・未確認事項 | `verify_command は L1 が確定すること` |

**`（候補）` 注記の義務**: `rubric-draft.md` の検証方法は `（候補）` サフィックスを付けること（MUST）。
これにより L1 が確定前の素案であることを区別できる。

**lam-orchestrate 側の責務**:
- `design.md` の FR / AC から rubric 項目候補を抽出すること
- 検証方法は `run` / `grader` / `human` のいずれかを候補として記載すること
- 検証コマンドが不明な場合は備考欄に「未確認（要 L1 確定）」と記載すること

### 4.3 task-list.md

`lam-orchestrate` が `task-decomposer` サブエージェントを通じて生成するタスクリスト。

**必須事項**:

| 項目 | 要件 | 理由 |
|------|------|------|
| タスク粒度 | 1 タスクが 1 L3 実行ループで完了できる規模 | goal-driven の大タスク・中タスク工程分解の単位 |
| 依存関係表記 | タスク間の実行順序依存を明示 | L1 / L2 の工程分配に使用 |
| SE/PM 級分類 | 各タスクの権限等級を明示 | PM 級タスクの事前確認ゲートに使用 |

**推奨フォーマット**:

```markdown
# task-list: <タスク名>

| # | タスク説明 | 依存 | 権限等級 | 備考 |
|---|-----------|------|---------|------|
| T1 | [タスク説明] | なし | SE | |
| T2 | [タスク説明] | T1 | SE | |
| T3 | [タスク説明] | T2 | PM | 仕様変更を伴う |
```

---

## 5. rubric-draft.md スキーマ詳細（design §16.2 完全準拠）

> 引用元: design.md §16.2

`rubric-draft.md` のスキーマは design.md §16.2 で定義された形式に完全準拠する。
スキーマの核心は「L1 指揮者が確定・追記することを前提とした素案」である。

### 5.1 ファイル全体構造

```markdown
# rubric-draft: <タスク名>（素案）

## 検証候補項目（L1 指揮者が確定・追記すること）

| # | チェック項目（素案） | 検証方法候補 | 備考 |
|---|-------------------|------------|------|
| 1 | [チェック項目] | [検証方法]（候補） | [備考] |
| 2 | [チェック項目] | [検証方法]（候補） | [備考] |
```

### 5.2 検証方法種別（design §6 の `run` / `grader` / `human` に対応）

| 種別 | rubric-draft での表記 | L1 確定後の rubric.md での表記 |
|------|-----------------------|-------------------------------|
| `run` | `run: <コマンド>（候補）` | `run: pytest --tb=short` |
| `grader` | `grader 判定（候補）` | `grader: rubric 項目 N を読み src/ と照合せよ` |
| `human` | `human 判断（候補）` | `human: PM による目視確認` |

### 5.3 rubric-draft.md と rubric.md の差異

| 項目 | rubric-draft.md | rubric.md（確定版） |
|------|-----------------|---------------------|
| 作成者 | lam-orchestrate 経由 doc-writer | goal-driven L1 指揮者 |
| ヘッダ | `# rubric-draft: <名前>（素案）` | `# rubric: <名前>` |
| セクション | `## 検証候補項目` | `## 検証項目` |
| 検証方法 | `（候補）` サフィックス付き | 確定した命令形 |
| `global_bound` フィールド | 存在しない（L1 が設定） | 存在する（design §6 スキーマ） |
| `## 差し戻しルール` | 存在しない | 存在する（design §6 スキーマ） |
| 配置パス | `docs/tasks/<slug>/rubric-draft.md` | `docs/tasks/<slug>/rubric.md` |

---

## 6. goal-driven フロー[2] での処理

### 6.1 rubric-draft.md の有無分岐

> 引用元: design.md §16.2（フロー[2] 入力処理）

```
goal-driven フロー[2]: rubric 生成（LLM 呼び出し）
  ↓
rubric-draft.md が存在するか？
  ├─ YES: L1 が内容を確認・確定し rubric.md を生成する（§6.2）
  └─ NO : L1 がゼロから生成する（§6.3）

（いずれの場合も）
design.md を参照資料として使用する
```

SKILL.md フロー[2]（`.claude/skills/goal-driven/SKILL.md`）の実装:

```
[2] rubric 生成（LLM 呼び出し）

入力処理:
1. docs/tasks/<slug>/rubric-draft.md が存在する場合: 内容を確認・確定し rubric.md を生成
2. rubric-draft.md がない場合: L1 がゼロから生成
3. design.md は L1 の rubric 生成の参照資料として使用
```

### 6.2 rubric-draft.md が存在する場合の処理手順

L1 指揮者が以下の手順で `rubric.md` を生成する:

1. `rubric-draft.md` を Read ツールで読み込む
2. `design.md` を Read ツールで読み込み、FR / AC 一覧と照合する
3. 素案の検証方法候補（`（候補）` 付き）を確定した命令形に変換する
4. `design.md` の FR / AC のうち素案に欠けている項目を追記する
5. `global_bound` フィールドをルートに応じた値（design §9.2）で設定する
6. `## 差し戻しルール` を `max_loop_count` の初期値（3 回）で設定する
7. `docs/tasks/<slug>/rubric.md` に確定版を書き込む（MUST）

**確定版 `rubric.md` のスキーマ（design §6 準拠）**:

```markdown
# rubric: <タスク名>

- 生成日: YYYY-MM-DD
- タスク種別: 小 / 中 / 大
- global_bound: tokens=150000 OR time=3600s

## 検証項目

| # | チェック項目 | 検証方法 | 検証コマンド / grader 指示 | 合否基準 |
|---|------------|---------|--------------------------|--------|
| 1 | 全テスト通過 | 実行コマンド | `pytest --tb=short` | exit 0 |
| 2 | FR-X 仕様フィールド名一致 | grader 判定 | rubric 項目 2 を読み src/ と照合せよ | 完全一致 |

## 差し戻しルール

- 連続 N 回不合格でエスカレーション（N = max_loop_count、初期値 3）
- 同一項目 2 回連続不合格 → L1 に報告（再 rubric または工程分割を検討）
```

### 6.3 rubric-draft.md が存在しない場合の処理手順

L1 指揮者が以下の手順で `rubric.md` をゼロから生成する:

1. `design.md` を Read ツールで読み込む
2. `task-list.md` を Read ツールで読み込み、実装スコープを確認する
3. `design.md` の FR / AC / 完了条件から rubric 項目を抽出する
4. 各項目の検証方法（`run` / `grader` / `human`）を決定する
5. `global_bound` をルートに応じた値で設定し、`rubric.md` を書き込む（MUST）

### 6.4 処理の擬似コード

```python
# goal-driven フロー[2]: rubric 生成
task_dir = project_root / "docs" / "tasks" / slug

# 1. 入力ファイル読み込み
design_md = read(task_dir / "design.md")          # 必須・不在なら起動拒否
task_list_md = read(task_dir / "task-list.md")    # 必須・不在なら起動拒否
rubric_draft = try_read(task_dir / "rubric-draft.md")  # 任意

# 2. rubric 生成（LLM 呼び出し）
if rubric_draft exists:
    # 素案を確定版に昇格させる（§6.2 の手順）
    rubric_md = L1_confirm_and_complete(rubric_draft, design_md)
else:
    # ゼロから生成する（§6.3 の手順）
    rubric_md = L1_generate_from_scratch(design_md, task_list_md)

# 3. 確定版を配置
if route in ("medium", "large"):
    write(task_dir / "rubric.md", rubric_md)
else:  # small task
    write(project_root / ".claude" / "rubric-tmp.md", rubric_md)
```

---

## 7. AC-15 充足の根拠

AC-15: 「lam-orchestrate → 新スキルへの成果物受け渡し形式が定義されていること（FR-10）」

| AC-15 の充足要素 | 本書の対応箇所 |
|----------------|--------------|
| 受け渡しファイルが定義されている | §3 ディレクトリレイアウト（design.md / rubric-draft.md / task-list.md） |
| 各ファイルの内容仕様が定義されている | §4 各ファイルの内容仕様 |
| rubric-draft.md のスキーマが設計書に準拠している | §5 rubric-draft.md スキーマ詳細（design §16.2 完全準拠） |
| goal-driven スキルの入力処理が定義されている | §6 goal-driven フロー[2] での処理 |
| lam-orchestrate と goal-driven が直列接続として機能する | §2 パイプライン位置（design §16.1 引用） |
| lam-orchestrate の出力が goal-driven の入力に接続する | §3〜§6 の全体（完全定義） |

**FR-10 要件との対応**:

> FR-10: lam-orchestrate の出力（設計文書・rubric 素案）を本スキルのフロー[2] の入力として
> 受け取れる受け渡し形式を定義しなければならない（MUST）

- 「設計文書」→ `design.md`（§4.1）
- 「rubric 素案」→ `rubric-draft.md`（§4.2, §5）
- 「フロー[2] の入力として受け取れる」→ §6 の処理定義（有無分岐・処理手順・擬似コード）

---

## 8. 将来の拡張余地

現在の受け渡し形式は `design.md` / `rubric-draft.md` / `task-list.md` の 3 ファイルで構成されるが、
将来的に以下のファイルが追加候補となり得る。

- **`architecture-diagram.md`**: システム構成図・モジュール依存図。大タスクルートで L2 班長が
  工程分解を行う際の参照資料として有用。`lam-orchestrate` の `design-architect` が生成候補。

- **`risk-analysis.md`**: 実装リスク・依存サービスの可用性・ロールバック計画。`goal-driven` の
  エスカレーション判断（bound 超過前に既知リスクを L1 が認識）に活用できる。

これらは任意ファイルとして追加する設計にすること。`goal-driven` は不在でも動作しなければならない（MUST）。
追加時は本仕様書（§3 ディレクトリレイアウト）を更新し、AC-15 の充足根拠（§7）も更新すること。

---

*仕様書ここまで。Version 0.1.0 / 2026-06-17 / W6-T1 初版（AC-15 / FR-10 対応）*
