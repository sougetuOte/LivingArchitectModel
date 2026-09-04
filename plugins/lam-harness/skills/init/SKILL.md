---
name: init
description: |
  LAM ハーネスの規範層をプロジェクトへ敷く初期化スキル。
  plugin コンポーネントとして配れない層（.claude/rules/ と docs/internal/ = managed、
  および CLAUDE.md 等の starter）をファイルとして配置し、.claude/harness.json に記録する。
  ランタイム（Python）が無い環境では完了を拒む。
  Layer 1（.claude/settings.json の permissions）は敷かず、手作業の手順として提示する。
  Use when the user installs lam-harness into a project, or runs /lam-harness:init.
---

# /lam-harness:init — 規範層の初期化

## このスキルが存在する理由

Claude Code の plugin が配れるコンポーネントは **skills / agents / hooks / MCP / LSP の 5 種**である。
**`.claude/rules/` と `docs/internal/` はその在庫に無い。** しかし LAM のガードのうち
Layer 0（規範）はまさにその 2 つに書かれている。

したがって規範層は「plugin が持ち、init がプロジェクトへ敷く」形にするしかない。
本スキルはその配置係である。

## 射程 —— 何を敷き、何を敷かないか

| 層 | 中身 | 本スキル | 更新 |
|:--|:--|:--|:--|
| **Layer 0 / managed** | `.claude/rules/` 14 件 ＋ `docs/internal/` 10 件 | **敷く** | `/plugin update` で**届く** |
| **Layer 0 / starter** | `CLAUDE.md` / `CHEATSHEET.md` / `CHANGELOG.md` / `SESSION_STATE.md` / `.claude/current-phase.md` / `.claude/harness.json` / `.claude/rules/model-roster.md` / `.claude/rules/terminology.md` | **敷く（初回のみ）** | 届かない（利用者の資産） |
| **Layer 2 / 機構** | `.claude/hooks/` ・ `.claude/agents/` ・ skills | **敷かない** | plugin が直接供給する |
| **Layer 1 / 決定的な禁止** | `.claude/settings.json` の `permissions` | **敷かない** | **利用者の手作業**（下記 Step 6） |

### managed と starter を取り違えないこと（不可逆）

**managed → starter の降格は無害**（更新が止まるだけ）。
**starter → managed の昇格は利用者の編集を破壊する。**
したがって分類は init の設計時点で決まっており、本スキルは分類を変更しない。

---

## 引数

```
/lam-harness:init            # 通常実行
/lam-harness:init --dry-run  # 副作用なしの事前確認
```

## 横断制約

- 書き込みは全てユーザー承認後（dry-run 除く）
- **既存ファイルを承認なしに上書きしない**
- Windows / Unix のパス区切り・改行コードに配慮する
- 自身の SKILL.md に書き込まない（ハーネス自己破壊防止）
- `~` 配下のユーザー設定（user scope の `settings.json`）を書き換えない

---

## Step 0: ランタイム検査（**失敗したら完了を拒む**）

最初に実行する。

```bash
: "${CLAUDE_PLUGIN_ROOT:?plugin root が未解決です。本スキルは plugin 経由でのみ動作します}"
bash "${CLAUDE_PLUGIN_ROOT}/scripts/check-runtime.sh"
```

> **1 行目のガードが要る理由**: bash は未設定の変数を**空文字に展開する**ため、
> ガードが無いと `bash "/scripts/check-runtime.sh"` = **exit 127** になる。
> 中止する結果は同じだが、下の分岐がそれを「ランタイム検査の失敗」と読み、
> 利用者に「**Python を用意して再実行してください**」と案内してしまう
> —— 真因は plugin root の未解決であり、その案内に従っても直らない。
> LAM は同型を一度踏んでいる（`CLAUDE.md` §Python Invocation Convention の
> 段2 fixup 教訓 = skill 内で `$CLAUDE_PROJECT_DIR` が unset だった件）。
> `:?` は unset/空のときにメッセージを出して非零終了する bash の書式である。

- **exit 0**: Step 1 へ進む
- **非零**: **init を中止する。** stderr の内容をそのまま利用者に見せ、
  Python を用意してから再実行するよう案内する。**部分的に敷いて終わらない**
  （中途半端な規範層は「入っているのに効かない」状態を作る）

> **なぜここで止めるのか**: LAM のガードの実体は `.claude/hooks/` の Python である。
> hook の `exit 2` 以外の非零終了は**非ブロッキング**であり、インタプリタ不在の 127 も
> 同じ扱いになる。つまり Python が無い環境では、操作は素通りしたうえで
> 毎回 `hook error` のノイズだけが出る。**fail-open とノイズが同時に起きる。**
> init は「一度きり・利用者起動・対話的」を満たす唯一の地点であり、ここで止めるのが最も安い。

---

## Step 1: 状態判定

| 状態 | 条件 | 挙動 |
|:--|:--|:--|
| ① 適用済 | `.claude/harness.json` が存在 | 既存 `harness_version` を表示して Step 2 へ |
| ② 既存プロジェクト | `.claude/` か `docs/` かソースファイルが存在 | 構造を提示し、続行確認を取ってから Step 2 へ |
| ③ 完全新規 | 上記いずれでもない | Step 3 へ |

ソースファイルの判定に使う拡張子:
`.js .ts .py .go .rs .java .rb .php .cs .cpp .c .h`

### 状態②で必ず伝えること

初期フェーズは `PLANNING` である。PLANNING では**設定ファイルの変更が deny される**ため、
進行中の作業がある場合はそこで止まる可能性がある。続行前にこれを提示し、
必要なら初期フェーズを `BUILDING` にする選択肢を出す。

---

## Step 2: 上書き方針（状態①② のみ）

```
既存ファイルが検出されました:
  - CLAUDE.md
  - CHEATSHEET.md

上書き方針を選択してください:
  1) skip          — 既存ファイルは触らない
  2) overwrite     — 全て上書き（注意）
  3) ask-per-file  — ファイルごとに確認（推奨）
```

**managed 層は既定で overwrite** である（plugin が所有し更新し続けるため）。
ただし利用者が managed を手で編集していた場合は失われるので、**差分がある managed ファイルは
必ず個別に提示**してから上書きする。

---

## Step 3: 生成プラン提示（`--dry-run` はここまで）

実際に配置するファイルは **plugin 側のテンプレートディレクトリから導出する**
（維持リストを持たない）。

```bash
ls "${CLAUDE_PLUGIN_ROOT}/templates/managed/rules"
ls "${CLAUDE_PLUGIN_ROOT}/templates/managed/docs-internal"
ls "${CLAUDE_PLUGIN_ROOT}/templates/starter"
```

配置先の対応:

| テンプレート | 配置先 |
|:--|:--|
| `templates/managed/rules/**` | `.claude/rules/**` |
| `templates/managed/docs-internal/**` | `docs/internal/**` |
| `templates/starter/dot-claude/**` | `.claude/**`（`dot-claude` を `.claude` に読み替える） |
| `templates/starter/<その他>` | プロジェクトルート直下 |

併せて作成するディレクトリ:
`.claude/states/` / `docs/specs/` / `docs/adr/` / `docs/tasks/` / `docs/artifacts/`
（空になるものには `.gitkeep` を置く）

`--dry-run` の場合はここで終了し、`dry-run 完了 — 変更なし` を表示する。

---

## Step 4: 配置

承認後、Step 3 のプランどおりに配置する。

- starter の `<project-name>` / `<branch>` / `<YYYY-MM-DD>` / `<ISO 8601 現在時刻>` は
  実値に置換する。`CLAUDE.md` の**プロジェクト概要欄は置換しない**（利用者が手で書く欄）
- `.claude/harness.json` は既存があれば**他キーを破壊せず**マージする
- `SESSION_STATE.md` は `.gitignore` への追加を**推奨**として提示する（強制はしない）

---

## Step 5: 検証

配置後、次を確認して結果を表示する。

- `.claude/current-phase.md` が行頭 `**PLANNING**`（大文字のみ）を含むこと
  —— ここが崩れるとフェーズ依存のガードが**黙って**効かなくなる
- `.claude/rules/` と `docs/internal/` のファイル数が、テンプレート側の件数と一致すること
- `.claude/harness.json` が読める JSON であること

---

## Step 6: Layer 1 は届かない —— 手作業の手順を提示する（**MUST**）

**本スキルは `.claude/settings.json` の `permissions` を書かない。** 理由は 2 つある。

1. `permissions` への書き込みは安全クラシファイアが**ハードブロック**する
   （ユーザーが承認しても解除されない）
2. 仮に書けたとしても、決定的な禁止を利用者の同意なしに入れるのは越権である

したがって init の完了メッセージで、**Layer 1 が未適用であることを明示**し、
利用者自身が入れるための手順を提示する。

```
このハーネスの射程は Layer 0（規範）と Layer 2（hook）までです。
Layer 1（決定的な禁止 = settings.json の permissions）は入っていません。

有効にするには .claude/settings.json の permissions を自分で編集してください。
何を deny / ask にするかは .claude/rules/security-commands.md
§コマンド許可マトリクス が対応表を持っています。
```

**「入れた瞬間に全部効く」と言わないこと。** 言えば、それは配布物が実体より強い主張をする欠陥である。

---

## Step 7: 次アクション

```
ハーネス初期化完了（harness_version: <version>）

  managed: .claude/rules/ <N> 件 / docs/internal/ <M> 件（/plugin update で更新が届く）
  starter: <K> 件（以後はあなたの資産）
  Layer 1: 未適用（Step 6 の手順を参照）

次のステップ:
  1. CLAUDE.md のプロジェクト概要欄を記入する
  2. .claude/rules/model-roster.md に層 → モデルの割当を書く
  3. PLANNING フェーズを開始する
```

---

## 禁止事項

- ユーザー承認なしの上書き
- `CLAUDE.md` プロジェクト概要欄への自動記入
- `.claude/settings.json` の `permissions` への書き込み
- user scope の設定（`~` 配下）への書き込み
- ランタイム検査に失敗した状態での完了報告

## 関連

- 3 層の分類（managed / starter / 私物）と、分類が不可逆である理由
- `.claude/rules/permission-levels.md` — 権限等級と PM 級パスの正本
- `.claude/rules/security-commands.md` — Layer 1 に入れる deny / ask の対応表
