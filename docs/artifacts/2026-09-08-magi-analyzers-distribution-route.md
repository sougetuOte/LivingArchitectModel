# MAGI: analyzers 18 件の配布経路 —— `_hook_utils` 依存と無主のスロット

**日付**: 2026-09-08 / **モード**: **AoT 適用**（判断ポイント 5 / 影響レイヤー 6 / 選択肢 4）
**議題**: Action 4c-1。閉包導出器の実出力に基づきユーザーが「analyzers は managed に 1 行足して配る」を
決定したが、**その案を推した L1 自身が実装前検証で欠陥を見つけた**。置き場所を決め直す。
**前提となる決定**: 決定 A（`subprocess-encoding-convention.md` を配らない）/ 決定 C
（`incident-patterns.yaml` を配る）/ 小物 3 件は手順書き換え —— **いずれも本 MAGI の対象外**。

---

## Step -1: 実測（2026-09-08 / すべて本セッションで実行して確認）

### (1) 閉包導出の実出力

閉包 65 件 / 未配布 40 件。エントリポイント別: `full-review` **18** / `ship` **3**（18 の部分集合）/
`quick-save` **13** / `subprocess-encoding-convention.md` **10**（決定 A で消滅）/ `hooks.json` 1 /
`release` 1 / `update-model` 1。

### (2) **L1 が推した managed 案は `_hook_utils` 依存で破れる**

`analyzers` の **4 モジュール**（`gitleaks_scanner` / `javascript_analyzer` / `python_analyzer` /
`rust_analyzer`）が `from _hook_utils import build_allowlisted_env` している。
`_hook_utils.py` は **Layer 2 = plugin が直接供給**であり、利用者の `.claude/hooks/` には**敷かれない**。
よって `templates/managed/analyzers/` → `.claude/hooks/analyzers/` と敷いても、
`sys.path.insert(0, '.claude/hooks')` 経由の import は **ImportError で落ちる**。

**これは「配ったのに動かない」形**であり、4c-1 が解こうとしている問題そのものである。

### (3) T3 の片側無視は**トップレベル名の積集合**である（実読）

```python
plugin_names = {p.name: p for p in plugin_area_root.iterdir()}
dev_names    = {p.name: p for p in dev_area_root.iterdir()}
for name in sorted(set(plugin_names) & set(dev_names)):   # ← 積集合のみ再帰比較
```

`.claude/hooks/analyzers` は dev 片側なので現在は無視される。`plugins/lam-harness/hooks/analyzers/`
を作れば積集合に入り、**40 対 18 の再帰比較**が起動する（dev 側 `analyzers/tests` **22 件**が片側）。
gabriel の 2026-09-07 実測「30 件超が赤」を裏づける。

### (4) `plugins/lam-harness/scripts/` は**無主のスロット**である

中身は `check-runtime.sh` **1 件のみ**。`_MIRROR_AREAS` にも `_MANAGED_AREAS` にも属さない。
そして `init/SKILL.md:63` が既に `bash "${CLAUDE_PLUGIN_ROOT}/scripts/check-runtime.sh"` を
**フェンス内で実行しており、skill 内での `${CLAUDE_PLUGIN_ROOT}` 展開は repo 内に先例がある**
（設計 §Step -1 (7) の上流実測「Skill and agent content で展開される」と一致）。

### (5) `init/SKILL.md` の層分類表と衝突する

> `| **Layer 2 / 機構** | `.claude/hooks/` ・ `.claude/agents/` ・ skills | **敷かない** | plugin が直接供給する |`

managed 案は `.claude/hooks/` の一部を敷く。**表の言明が偽になる。**
同ファイルは「**managed と starter を取り違えないこと（不可逆）**」という節を持ち、
分類の変更を設計時点の決定として凍結している。

### (6) `build_allowlisted_env` は 10 行 + 定数 1 個

`CHECKER_ENV_ALLOWLIST` のキーだけを `os.environ` から抜き出すセキュリティヘルパー
（W-14 対応 / サブプロセスへの機密環境変数の継承を止める）。
利用者は analyzers 4 件 ＋ `lam-stop-hook.py` ＋ `checkers/check_g1_test.py` ＋ テスト群。

### (7) `derive_managed_templates.py` は**新規テンプレートを作らない**

```python
for template in _iter_text_files(area_root):   # 既存テンプレートのみ走査
    ...
    if not source.is_file():
        continue                                # 生成器は新規作成しない
```

配布集合への**追加は人の決定**、追加後の同期は生成器 —— 境界が実装されている。

### (8) analyzers の外部依存は tree-sitter のみで、不在時の挙動は仕様化済

`chunker.py` が `except ImportError` → `TreeSitterNotAvailable` を送出。
追補 4 の「不在時の挙動が仕様として明示されていなければならない」を満たす。

---

## Step 0: AoT Decomposition

| Atom | 判断内容 | 読む状態 | 書く状態 |
|:--|:--|:--|:--|
| **A1** | `_hook_utils` 依存をどう解くか | `analyzers/{gitleaks_scanner,javascript_analyzer,python_analyzer,rust_analyzer}.py` の import 行 / `_hook_utils.build_allowlisted_env`（10 行）/ その他の利用者 7 ファイル | 依存の向き（どのモジュールがどれを import するか）/ `_hook_utils.py` と analyzers のソース |
| **A2** | analyzers の配布経路（置き場所） | A1 の結論 / `_MANAGED_AREAS` / `_MIRROR_AREAS` のトップレベル積集合ロジック / `plugins/lam-harness/scripts/` の無主性 / `${CLAUDE_PLUGIN_ROOT}` の展開層 | `verify_plugin_containment.py` の構造定数 / plugin 内の配置先 / 配布 skill 11 箇所のフェンス内コマンド |
| **A3** | dev 正本と配布実体の同期機構 | A2 の結論 / `derive_managed_templates.py`（新規作成しない）/ `derive_project_copies.py` | 生成器の有無と向き / `.claude/scripts/*.py` |
| **A4** | `init/SKILL.md` 層分類表との整合 | A2 の結論 / Layer 表 / Step 3 の `ls` 列挙 / 「取り違えないこと（不可逆）」節 | `init/SKILL.md` の本文 |
| **A5** | dashboard 11 件は別経路でよいか | `_MANAGED_AREAS["scripts"] = .claude/scripts` / `.claude/scripts/dashboard/**` の import 閉包 / `build_dashboard.py` | `templates/managed/scripts/**` に増えるファイル |

> 依存は導出される —— A2 は A1 の書く状態を読み、A3・A4 は A2 を読む。
> A5 の書込集合（`templates/managed/scripts/**`）は A1・A2 の書込集合と交わらないため、**A5 は並列可**。
> 逆に **A2 の書込集合は配布 skill 11 箇所を含む**ので、A2 が決まるまで skill 本文を触ってはならない。

---

## Atom A1: `_hook_utils` 依存をどう解くか

**[MELCHIOR]**: 3 案ある。

- **(1) `_hook_utils.py` も配布先に敷く** —— 最小の変更。ただし plugin が `hooks/_hook_utils.py` を
  持っているのに、利用者の `.claude/hooks/_hook_utils.py` にも同じものが置かれる = **複製相の新設**
- **(2) sys.path に plugin の hooks/ を足す** —— 配布 skill のフェンスを
  `sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/hooks')` に書き換える。実体は plugin 内に必ずある
- **(3) `build_allowlisted_env` を analyzers 側へ移す** —— 10 行なので移動は容易。
  analyzers が自己完結する

**[BALTHASAR]**: (1) と (3) を潰す。

**(1) は LAM が 3 回解体してきた形そのものである。** HGA #33 が T3 の複製相を生成へ解体し、
4b が T1 に生成器を入れた。ここで新しい複製相を**手で**建てるのは退行である。
しかも `_hook_utils.py` は **PM 級の判定ロジック（`_PM_PATH_PATTERNS`）を持つ**。
2 箇所に置けば、片方だけ古い版が残ったとき**権限判定が環境によって変わる**。

**(3) は依存の向きを壊す。** `build_allowlisted_env` は `CHECKER_ENV_ALLOWLIST` を伴い、
`lam-stop-hook.py` と `checkers/check_g1_test.py` も使う。analyzers へ移せば
**hook が analyzers を import する**ことになり、analyzers が hook の import 閉包に入る。
すると「analyzers は hook の import 閉包に含まれない」という `_MIRROR_AREAS` の注記が偽になり、
**hooks 配下に置かねばならなくなって A2 の選択肢が (3) の副作用で潰れる**。
—— これは A1 が A2 の書く状態を侵している。**Atom のエラー隔離が破れる案は採らない。**

**[CASPAR]**: 結論 —— **(2) を採る。** sys.path に `${CLAUDE_PLUGIN_ROOT}/hooks` を足す。

根拠は 3 点。**第 1 に、実体が必ずある**（`hooks/_hook_utils.py` は hooks.json が名指しする
配布物であり、plugin が無ければ skill 自体が存在しない）。**第 2 に、複製を増やさない**
（A1 の書込集合が空になる = ソースを一切変更しない）。**第 3 に、先例がある**
（`init/SKILL.md:63` が同じ形で `${CLAUDE_PLUGIN_ROOT}/scripts/` を実行している）。

**採用しなかった選択肢とその理由**:

- **(1) `_hook_utils.py` を二重に配る** → 複製相の新設。かつ PM 級判定ロジックが 2 箇所に散り、
  版ずれが**権限判定の環境差**になる。LAM が 3 回解体してきた形の再生産
- **(3) ヘルパーを analyzers へ移す** → 依存の向きが逆転し hook が analyzers を import する。
  A2 の選択肢を副作用で潰す（エラー隔離違反）

---

## Atom A2: analyzers の配布経路（置き場所）

**[MELCHIOR]**: A1 (2) を前提にすると、置き場所は `${CLAUDE_PLUGIN_ROOT}` 配下ならどこでもよい。
**`plugins/lam-harness/scripts/analyzers/`** が最短である —— `_MIRROR_AREAS` にも
`_MANAGED_AREAS` にも属さないので **T1 も T3 も起動しない**。init は何も敷かない。
分類表とも衝突しない（Layer 2「plugin が直接供給する」の文字どおり）。

**[BALTHASAR]**: 3 点。

**(i) 「検査が起動しない」は利点ではなく赤旗である。** `plugins/lam-harness/scripts/` が
無主なのは `check-runtime.sh` 1 件（plugin 専有・dev 側に正本を持たない）しか無かったからで、
そこに **dev 側に正本がある 18 ファイル**を置けば、**無検査の複製相**が生まれる。
これは (1) を潰した理由と同じ形であり、置き場所を変えただけで問題は移動していない。
**→ A3（同期機構）を必ず伴わせること。**

**(ii) `${CLAUDE_PLUGIN_ROOT}` の展開層を跨がせてはならない。** 書き換え対象 11 箇所のうち、
`skills/*/SKILL.md` と `skills/full-review/references/*.md` は T3（展開される層）だが、
**`templates/managed/rules/subprocess-encoding-convention.md:177` は T1 である**。
T1 の出力は利用者の `.claude/rules/` になり plugin component ではないので、
**そこに `${CLAUDE_PLUGIN_ROOT}` を植えると `/hooks/...` に潰れる** ——
LAM は同型の事故を 2026-07-12 に 26 箇所作っている。
**ただし決定 A でこのファイルは配らないので、対象から落ちる**（要確認）。

**(iii) `references/*.md` が展開層かは未実測である。** 上流の表は
"Skill and agent content" と書いており、skill ディレクトリ内の参照ファイルが
含まれるかは逐語では確定しない。**`SKILL.md` 本体と同じ扱いだという仮定に依存している。**

**[CASPAR]**: 結論 —— **`plugins/lam-harness/scripts/analyzers/` を採る。ただし 2 つの条件を付す。**

**条件 1**: **A3 の同期機構を同一コミットで入れる**（無検査の複製相を作らない）。
**条件 2**: **書き換え対象 11 箇所の層を先に確定する**。決定 A で落ちるものを除いた残りが
すべて T3 であることを実測し、**T1 に 1 箇所でも残るなら、その箇所は書き換えず
「LAM 開発時のみ」と明示する**（BALTHASAR (ii)）。

**(iii) の未実測は残す** —— `references/*.md` の展開可否は**本決定の可逆性を損なわない**
（外れていれば `references` の 8 箇所を `SKILL.md` へ畳むか、相対パスに戻せばよい）。
ただし **4c-1 の受け入れ条件に「利用者環境相当での実行 1 回」を入れる**こと。

**採用しなかった選択肢とその理由**:

- **`templates/managed/analyzers/` → `.claude/hooks/analyzers/`（ユーザー承認済の案）**
  → A1 の実測により `_hook_utils` で破れる。救うには `_hook_utils.py` の二重配布（A1 (1)）が要り、
  そこで潰れる。**加えて init の層分類表を偽にする（A4）**
- **`plugins/lam-harness/hooks/analyzers/`** → T3 のトップレベル積集合に入り、
  dev 側 `analyzers/tests` 22 件が片側となって 30 件超が赤（gabriel 2026-09-07 実測 / 本セッションで
  ロジックを実読して裏づけた）
- **dev 正本を `.claude/scripts/analyzers/` へ移す** → `_MANAGED_AREAS["scripts"]` に自動で載るが、
  **`_hook_utils` 問題は解けない**うえ、`.claude/hooks/analyzers/tests` 22 件と
  11 箇所の `sys.path` と 565 件のテスト参照が動く。**利得ゼロで移動量最大**
- **配らない（決定 B のまま）** → ユーザーが棄却済

---

## Atom A3: dev 正本と配布実体の同期機構

**[MELCHIOR]**: `_MIRROR_AREAS` に `"analyzers": .claude/hooks/analyzers` を足せばよい ——
ただし現在の `_MIRROR_AREAS` は `plugin_dir / area` を見るので、`plugins/lam-harness/analyzers/`
を期待してしまう。`scripts/analyzers` に置くならキーの解決を変える必要がある。

**[BALTHASAR]**: **構造定数の意味を変えるな。** `_MIRROR_AREAS` は「plugin 直下の名前 ↔ dev 側ディレクトリ」
という単純な対応で、その単純さが T3 の理解可能性を支えている。ここに「plugin 側だけ 2 階層」の
例外を入れると、**次に読む人が積集合ロジックを誤読する**。

**[CASPAR]**: 結論 —— **`plugins/lam-harness/analyzers/` に置き、`_MIRROR_AREAS` に 1 行足す。**

A2 の「`scripts/` の下」を **plugin 直下 `analyzers/` に修正する**。理由は BALTHASAR の
構造定数の単純さの保存であり、A2 が `scripts/` を選んだ根拠（無主・無検査）は
**A3 の条件 1 で否定されている**ので、`scripts/` に置く積極的理由はもう無い。

- T3 の積集合は `plugins/lam-harness/analyzers/` ↔ `.claude/hooks/analyzers/` で成立する
- dev 側の `tests/`（22 件）は**トップレベル片側**として無視される —— これは
  `hooks` エリアで既に効いている仕組みと**同じ粒度**であり、新しい例外ではない
- skill 側は `sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}')` として `analyzers.X` を import し、
  併せて `${CLAUDE_PLUGIN_ROOT}/hooks` も挿す（A1 (2)）

**採用しなかった選択肢とその理由**:

- **`scripts/analyzers/` + キー解決の拡張** → 構造定数の意味を複雑にする。読み手が積集合を誤読する
- **生成器を新設せず手コピー** → SESSION_STATE ⚠️(5) 違反。4b が解体した形の再生産

---

## Atom A4: `init/SKILL.md` 層分類表との整合

**[MELCHIOR]**: A3 の結論なら init は何も敷かない。表は無傷である。

**[BALTHASAR]**: 無傷ではない。**表の「Layer 2 / 機構」行は列挙**であり、
`.claude/hooks/` ・ `.claude/agents/` ・ skills しか書いていない。**analyzers を足さねば
「plugin が直接供給するもの」の一覧が実際より小さくなる**。
—— これは 4c-0 で直した「除外理由が偽」と同じ型（列挙が実体より小さい）である。
また Step 3 の `ls` は **managed の 3 エリアを列挙している**ので、
managed が増えないことの確認にはなるが、analyzers の存在は読者に見えない。

**[CASPAR]**: 結論 —— **Layer 2 行に analyzers を明記する。** 1 行の追記であり、
表の意味は変わらない（敷かない / plugin が直接供給する）。**分類の変更ではないので
「取り違えないこと（不可逆）」節には抵触しない。**

---

## Atom A5: dashboard 11 件は別経路でよいか

**[MELCHIOR]**: `.claude/scripts/` 配下なので `_MANAGED_AREAS["scripts"]` にそのまま載る。
`templates/managed/scripts/` に 11 ファイル（`build_dashboard.py` ＋ `dashboard/**` 10）を
足せば終わり。構造定数を触らない。

**[BALTHASAR]**: 2 点。**(i)** 生成器は新規作成しないので、**テンプレートを人が置く**必要がある。
置いた瞬間の内容は `derive_managed_text` の出力と一致していなければ T1 が赤になる ——
**空ファイルを置いて生成器を回す**手順を明示せよ。
**(ii)** 閉包が拾った `docs/artifacts/dashboard/dashboard.html` は**出力先**であって依存ではない。
計器は read/write を判別できない。**配布集合に入れてはならない。**

**[CASPAR]**: 結論 —— **managed scripts に 11 件を足す。`dashboard.html` は入れない**
（出力先 / `write-dest` と同類）。`.claude/tests/dashboard/test_session_state_parser.py` も
入れない（小物 3 件の決定＝手順書き換えに従い、quick-save 側で「LAM 開発時のみ」と明示）。
テンプレートの追加手順は **空ファイル設置 → 生成器実行 → T1 緑**を明示する。

---

## Step 5 に進む前の暫定統合

**A2 は A3 によって修正された。** 最終形は以下。

| # | 決定 |
|:-:|:--|
| 1 | `_hook_utils` は**移さず二重配布もしない**。skill 側で `${CLAUDE_PLUGIN_ROOT}/hooks` を sys.path に足す |
| 2 | analyzers 18 件は **`plugins/lam-harness/analyzers/`**（plugin 直下）へ置く |
| 3 | **`_MIRROR_AREAS` に `"analyzers": .claude/hooks/analyzers` を 1 行足す**（T3 が同期を強制する / dev 側 `tests/` はトップレベル片側として無視される） |
| 4 | 配布 skill の 11 箇所を `${CLAUDE_PLUGIN_ROOT}` 経由に書き換える。**ただし T1 層に残る箇所があれば書き換えず「LAM 開発時のみ」と明示** |
| 5 | `init/SKILL.md` の Layer 2 行に analyzers を明記（分類変更ではない） |
| 6 | dashboard 11 件は `templates/managed/scripts/` へ（空ファイル → 生成器 → T1 緑）。`dashboard.html` と test は入れない |

**未検証として残すもの（信じて進まない）**:

- `skills/*/references/*.md` で `${CLAUDE_PLUGIN_ROOT}` が展開されるか（8 箇所が該当）
- `_MIRROR_AREAS` に `analyzers` を足したとき T3 が実際に何件を比較し、
  `derive_project_copies.py`（T3 の生成器）が analyzers を扱えるか
- 書き換え対象 11 箇所の層の内訳（決定 A で何件落ちるか）

---

## Step 4: gabriel probe（1 巡目）

- verdict: **refuted** / severity: **critical** / confidence: 0.60
- affected_atoms: A1, A2, A3, A4, A5
- recommended_action: **re-magi**
- reasoning（要約）: **「analyzers を配る」という決定が repo のどこにも記録されていない。**
  記録されている決定 B（2026-09-07 アンカー §決定記録 / ユーザー承認済）は
  「`scale_detector.py` / `build_dashboard.py` とも**配らない**・手順書き換えに倒す」であり、
  本アンカー冒頭の前提と正面から矛盾する。ADR-0010 にこれを覆す追補 5 も存在しない。
  加えて **T3 方向の `to_project_text` には `.md` 限定ガードが無い**（T1 の
  `derive_managed_text` は持つ）ため、`.py` を `_MIRROR_AREAS` に入れる A3 の前提が危うい。
- 処理: **再 MAGI 1 ラウンド**（AC-W-C-5 / 初回 critical）
- メトリクス: `.claude/gabriel-metrics.log` **11 行目**に追記済

### L1 による独立検証（gabriel を額面で受け取らない）

| gabriel の主張 | L1 の実測 | 判定 |
|:--|:--|:--|
| 決定 B は「配らない」であり本アンカーと矛盾 | 2026-09-07 アンカー §決定記録 決定 B を実読。**そのとおり** | **正しい** |
| ADR-0010 に追補 5 は無い | 実読。**無い** | **正しい** |
| `to_project_text` に `.md` ガードが無い | `verify_plugin_containment.py:248-263` を実読。**無い**。さらに `invert_managed_text` の docstring が「**`.md` 以外に `to_project_text` を当ててはならない**」と明記している | **正しい** |
| `_compare_mirror_entry` は `.py` にも当てる | `:611` を実読。**suffix ガード無し**。既に `hooks` エリアの `.py` に当たっている = **既存の潜在欠陥**であり analyzers が作るものではない | **正しい / ただし新規リスクではない** |
| T3 のトップレベル積集合と `tests/` 片側無視は成立 | `_iter_mirror_matches` を実読。**成立** | **A3 を補強** |

**gabriel が見ていないもの**: 本セッションで**ユーザーが AskUserQuestion に回答し**、
「analyzers = managed に 1 行足して配る」「dashboard = 配る」「小物 3 件 = 手順書き換え」を
**決定している**。gabriel はファイルしか読めないため、この会話を見ていない。
gabriel 自身も「可動部: 本セッション内の会話でユーザーが実際に決定 B を覆す発言をしていれば、
この指摘は解消する」と書いている。

**したがって指摘の実体は「決定が覆ったのに、記録が repo に無い」という<ins>記録の欠落</ins>である。**
これは実在の欠陥である —— このまま実装すれば、次のセッションは決定 B を読んで矛盾する。
**露出の実測**: 配布 `.py` と analyzers `.py` に `lam-harness:` prefix は **0 件**（現状は無害な潜在）。

---

# 再 MAGI（2 巡目 / AC-W-C-5 / gabriel.reasoning を Divergence 入力に追加）

## Atom A6（新規）: 覆った決定をどこに、どの格で記録するか

**[MELCHIOR]**: SESSION_STATE と CHANGELOG に書けば足りる。実装を止める理由にはならない。

**[BALTHASAR]**: 足りない。**決定 B は「ユーザー承認済の決定記録」という格を持つ**。
同じ格の記録で上書きしなければ、次の読者は 2 つの承認済決定を見て**どちらが新しいかを
日付で推測する**ことになる。LAM はこの型の事故を既に持っている ——
`hga-summoning.md` の移行期規定が失効後 4 週間残り、新旧どちらのゲートが有効か曖昧になった。

一方、**ADR-0010 の追補 5 は不要**である。追補 4 が条文にしたのは「配布集合は閉包として
導出する」という**方法**であり、閉包の中身がどれだけになるかは条文事項ではない。
中身を条文に書けば、実測が動くたびに ADR を改訂することになる（**維持リストの再発明**）。

**[CASPAR]**: 結論 —— **本アンカーに「決定記録（2026-09-08 / ユーザー承認）」節を設け、
決定 B を supersede すると明記する。併せて 2026-09-07 アンカーの決定 B 行に前方参照を 1 行入れる。**
ADR 追補は作らない（方法は追補 4 で足りている）。**記録は実装より先**
—— 追補 4 が 4c-2 の前に入ったのと同じ順序である。

**採用しなかった選択肢とその理由**:

- **SESSION_STATE / CHANGELOG だけに書く** → 格が違う。承認済決定は承認済決定で上書きする
- **ADR-0010 追補 5 を起こす** → 配布集合の中身を条文に持つと、実測のたびに ADR 改訂になる。
  追補 4 が「方法」を条文にしたのは、まさに中身を条文から追い出すためだった
- **2026-09-07 アンカーの決定 B を書き換える** → **過去の記録を改竄しない**。
  supersede は前方参照で示す

## Atom A3'（改訂）: `.py` を複製相に入れる前に、導出の非対称を閉じる

**[MELCHIOR]**: 現状 `lam-harness:` prefix の検出は 0 件なので、放置しても今日は壊れない。

**[BALTHASAR]**: **「今日は壊れない」で入れるのが潜在欠陥の作り方である。**
しかも `invert_managed_text` の docstring は**この誤りを既に言語化している** ——
「`.md` 以外に `to_project_text` を当ててはならない。導出が恒等写像である領域に prefix 除去を
当てると、もともと名前空間つきで書かれていた記述まで剥がしてしまう」。
**片方向にだけ書かれた規則は、もう片方向で必ず破られる。** analyzers 18 件の `.py` を
複製相に入れるなら、露出は 8 ファイル（hooks）から 26 ファイルへ 3 倍になる。

**[CASPAR]**: 結論 —— **T3 の導出にも `.md` ガードを入れ、T1 と対称にする。**
現状の検出が 0 件であることは**利点**である —— **挙動不変のまま入れられ、
陰性対照（`.py` の docstring に `lam-harness:ship` を書いても剥がれないこと）を
テストで固定できる**。**analyzers を `_MIRROR_AREAS` に足すのと同一コミット**に含める。

**採用しなかった選択肢とその理由**:

- **ガードを入れずに analyzers を足す** → 露出 3 倍の潜在欠陥。既存 docstring が禁止と書いている当の操作
- **analyzers だけ特例で除外する** → 例外表。4a・4b が 2 度棄却した形

## Atom A1' / A2' / A4' / A5'（再確認 / 変更なし）

gabriel は A1（sys.path 解法）と A3 の積集合ロジックを**実読で裏づけた**。
A2 の棄却理由（managed 案の `_hook_utils` 破れ / `hooks/analyzers` の T3 赤）も追認された。
**A6 と A3' 以外に変更はない。**

## Step 5: AoT Synthesis（2 巡目後の確定形）

| # | 決定 | 順序 |
|:-:|:--|:--|
| **0** | **決定 B を supersede する記録**を本アンカーに置き、2026-09-07 アンカーへ前方参照を 1 行入れる | **最初** |
| 1 | T3 の導出に **`.md` ガード**を入れ T1 と対称にする（挙動不変 + 陰性対照 / **理由は §Atom A3'** —— `invert_managed_text` の docstring が既にこの誤りを禁止と書いていた） | 2 と同一コミット |
| 2 | analyzers 18 件を **`plugins/lam-harness/analyzers/`**（plugin 直下）へ置き、`_MIRROR_AREAS` に 1 行足す。dev 側 `tests/` 22 件はトップレベル片側として無視される | — |
| 3 | 配布 skill の 11 箇所を `sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}')` ＋ `'${CLAUDE_PLUGIN_ROOT}/hooks'` へ書き換え。**T1 層に残る箇所は書き換えず「LAM 開発時のみ」と明示** | 2 と同一コミット |
| 4 | `init/SKILL.md` の Layer 2 行に analyzers を明記（分類変更ではない） | 同上 |
| 5 | dashboard 11 件を `templates/managed/scripts/` へ（空ファイル → 生成器 → T1 緑）。`dashboard.html` と test は入れない | **並列可**（書込集合が交わらない） |

**未検証として残すもの（信じて進まない）**: `skills/*/references/*.md` での
`${CLAUDE_PLUGIN_ROOT}` 展開可否（8 箇所）/ `derive_project_copies.py` が analyzers を
扱えるか / 書き換え 11 箇所の層の内訳（決定 A で何件落ちるか）。
**いずれも 4c-1 の実装入口で実測する**（`.md` ガードと同様、実測前に本文を書き換えない）。

---

## Step 4': gabriel probe（2 巡目）

- verdict: **refuted** / severity: **warning** / confidence: 0.65
- affected_atoms: A2, A6
- recommended_action: **proceed**
- 処理: **AC-W-C-6 = 指摘を併記して進む**（人間エスカレーションではない）
- メトリクス: `.claude/gabriel-metrics.log` **12 行目**に追記済（`verify_reference_resolution` 緑）

**gabriel が実読で裏づけた**（結論を補強した側）: `_hook_utils` bare import は 4 件で一致 /
`.md` ガード追加は `lam-harness:` 出現 0 件のため**挙動不変** / `_iter_mirror_matches` は
area 直下の `iterdir()` 積集合なので **`tests/` 22 件の片側無視は成立** /
**A6 の「追補 5 不要」論は ADR-0010 追補 4 決定 2 の実文（方法のみを条文化し中身を持たない）と整合**。

### 併記する警告 2 件と、その処理

**[WARNING 1 by gabriel]**: `plugins/lam-harness/analyzers/` という新規トップレベルディレクトリの
plugin ローダ安全性が、**upstream 一次資料で直接確認されていない**（1 巡目でも依頼したが未回答だった）。

→ **本セッションで確認した（context7 `/websites/code_claude` / `plugins-reference`）。**
機能ディレクトリは**列挙されている** —— `skills/` `commands/` `agents/` `workflows/`
`output-styles/` `themes/` `monitors/` `hooks/` `bin/` `scripts/` ＋ `settings.json` `.mcp.json`
`.lsp.json`。**`analyzers` は予約名ではなく、未知のトップレベルは走査対象でもない。**
**ただし `bin/` は中身が PATH に載る特殊枠**なので、この名前だけは使わない。
—— **警告 1 は解消。**

**[WARNING 2 by gabriel]**: **書込集合の宣言漏れ。** `_MIRROR_AREAS` に analyzers を足した後の
pytest 実行が生む hook 副作用が、A1〜A6 のどの「書く状態」にも無い
（2026-09-07 アンカー Atom C4' は明示していた）。

→ **正当。以下を書込集合に加える（宣言漏れは Action 7 の起票理由でもある）。**

| 追加する書込先 | 由来 |
|:--|:--|
| `.claude/test-results.xml` / `.claude/tdd-patterns.log` | pytest 実行で PostToolUse hook が書く。**`security-commands.md` §計器への書き込みを伴う検証 が「復元不能」と記録した対象** |
| `.claude/logs/permission.log` | PreToolUse hook が全判定を書く |
| `.claude/gabriel-metrics.log` | 本 MAGI の probe 2 回（**追記済**） |
| `plugins/lam-harness/analyzers/**`（新規 18 件） | 決定 2 |
| `.claude/hooks/analyzers/**` | T3 生成器 `derive_project_copies.py --write` が**開発側を書き換える**（向きが逆 / 正本は plugin 側） |
| `.claude/tests/scripts/**` ＋ `.claude/tests/plugin/**` | `.md` ガードの陰性対照 / `_MIRROR_AREAS` の集合アサーション（`test_verify_plugin_containment.py:320` が現行 3 エリアを固定している） |

**A6 の記録が未実装である**という指摘も正当 —— 決定 0 は「最初にやること」であって、
**この時点ではまだ書かれていない**。次節がそれである。

---

## 決定記録（2026-09-08 / **ユーザー承認**）

> **本節は 2026-09-07 アンカー §決定記録 の決定 B を supersede する。**
> 同アンカーの決定 B 行に前方参照を入れた（過去の記録は消さず、取り消し線と参照で示す）。
> 経路は MAGI の確定形（plugin 直下 `analyzers/`）で承認された ——
> **L1 が推し、ユーザーが一度承認した managed 案は、実装前検証で `_hook_utils` 依存により破れた**。

**決定 B が過小な実測に基づいていた経緯**: 決定 B は「実害 13 箇所」を前提に
「`scale_detector.py` / `build_dashboard.py` とも配らない・手順書き換え」と定めた。
本セッションの閉包導出で **gap 40 件・入口別内訳**が出て、実体は
`/lam-harness:full-review` Stage 1-3 と `/lam-harness:ship` の gitleaks 走査が
**利用者環境で機能しない**ことだと判明した（analyzers 6 モジュールへの依存 11 箇所）。
ユーザーはこれを受けて「配る」と判断した（本セッションの AskUserQuestion）。

**確定形は §Step 5 の表**（決定 0〜5）。要点のみ再掲する ——
analyzers は **`plugins/lam-harness/analyzers/`**（`_MIRROR_AREAS` に 1 行 / T3 が同期を強制）、
`_hook_utils` は**移さず二重配布もせず** skill 側で `${CLAUDE_PLUGIN_ROOT}/hooks` を sys.path に足す、
dashboard は **managed scripts**、`.md` ガードは analyzers 追加と**同一コミット**。
