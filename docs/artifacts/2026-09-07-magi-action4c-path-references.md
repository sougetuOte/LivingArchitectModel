# MAGI: Action 4c —— 配布物のパス参照と、配布集合の閉包

**日付**: 2026-09-07（セッション 35）
**モード**: **AoT 適用**（判断ポイント 5 / 影響レイヤー = 計器・T1 生成器・T3 codemod・T2 検査・配布集合・ADR-0010・利用者環境 = 7 / 選択肢 3+）
**議題**: 配布物のパス参照が利用者環境で解決しない問題（**91 参照 / 192 箇所**）の設計。
**先行**: `2026-09-06-magi-action4-reference-model.md`（4a）/ `2026-09-06-magi-action4b-skill-references.md`（4b）/ **HGA #35**（本セッション）

---

## Step -1: 実測

### (1) 192 箇所は 1 つの問題ではない —— 分類名でなく**実在**で割り直した

計測器（`census_dangling.py`）の `NG-*` は**参照先ディレクトリの prefix** による分類である。
これを捨て、「**配布物にその実体があるか**」で割り直した（probe: `exists_dist(P)`）。

| | uniq refs | sites |
|:--|--:|--:|
| **移設もの**（配布物に実体が在るが、利用者環境では別の場所） | 17 | **35** |
| **本当に無いもの**（配布物に実体が無い） | 74 | **157** |

**prefix では判定できない**ことが実測で出た —— `.claude/hooks/analyzers/scale_detector.py` は
prefix が mirror 領域（`.claude/hooks`）だが、plugin の `hooks/` には**無い**（analyzers は
import 閉包外で非配布）。**判定はファイル単位でなければならない。**

### (2) 参照元の層 —— **T1 managed が最大**

| 層 | 移設もの | それ以外 |
|:--|--:|--:|
| **T1 managed**（利用者の `.claude/rules/` `docs/internal/` になる） | **22** | **75** |
| T3 skill | 10 | 65 |
| T3 agent | 2 | 22 |
| hooks 実装 | 1 | 3 |
| starter | 0 | 1 |

### (3) **4b の分離根拠は偽だった**

4b は 4c を分離する理由をこう書いた ——「パスからコンポーネント参照への変換は**情報の欠落を伴う**
（`.claude/skills/magi/SKILL.md:120` のような**行・節の指定が消える**）」。

**実測**: 移設もの 35 箇所のうちアンカーを伴うのは **7 箇所のみ**。
**`:120` 形式の行番号参照は 1 件も存在しない。** 7 件はすべて節見出し（`§Step 4.1` / `Stage 0` / `ステップ5`）。

**4b が挙げた「情報の欠落」は成立していない。**（ただし 4c を独立 Action にする理由は別に在る → Atom C1）

### (4) **計器に偽陽性がある —— ただし半分は計器のバグ**（HGA #35 §0-3 / L1 が実読して確認）

`census_dangling.py:102` の `PATH_RE` は `*` を語構成文字に含まない:

```python
PATH_RE = re.compile(r"(?:\.claude|docs|plugins|src|tests|scripts)(?:/[\w.@+-]+)+")
PLACEHOLDER = re.compile(r"[<>{}*?]|NNN|YYYY|\bN\b")
...
if PLACEHOLDER.search(span[: m.start()] + ref):   # ← 一致部分より「前」＋一致部分しか見ない
```

`` `.claude/agents/*.md` `` は **`.claude/agents` で切り詰められ**、その後の PLACEHOLDER 検査は
**切り詰めた後の文字列に対して**走るため除外に掛からない。**glob は分類問題ではなくトークナイザ問題**であり、
例外表を持たずに消える。

残る偽陽性 3 種の正体（**いずれも例外表を要さない** / 詳細は Atom C0）:

| 種類 | 実例 | なぜ例外表が要らないか |
|:--|:--|:--|
| 意図的な誤記 | `` `.claude/Rules/security-commands.md` ``（PM ゲートの大小文字非区別の**証拠テキスト**） | case-sensitive 比較では `exists_dev` = **False** → 4c の射程（`exists_dev ∧ ¬exists_user`）に**入らない** |
| 分類ラベル | `` | Layer 2 / 機構 | `.claude/hooks/` ・ `.claude/agents/` | **敷かない** | plugin が直接供給 | `` | 規則を当てても文意は真のまま（「plugin の hooks/ は敷かない」） |
| 範囲記法 | `docs/internal/00-08` | `exists_dev` = False → 射程外 |

### (5) **計器が見ていない実害 13 箇所**（HGA #35「見落とし 1」/ L1 が測って確定）

census の走査対象は「コードスパンと Markdown リンク」のみで、**``` フェンス内のコマンドは射程外**。
そこには**読者が実行する**パスがあり、解決しなければ**必ず落ちる**。

厳密判定（`ref in ufiles or ref in udirs` のみを解決とみなす）で **13 箇所**:

| 参照元（配布 skill / 規範） | 呼ぶ実体 | 配布されているか |
|:--|:--|:--|
| **`quick-save/SKILL.md:121`** | `.claude/scripts/build_dashboard.py` | **されていない** |
| **`quick-save/SKILL.md:52`** | `.claude/tests/dashboard/test_session_state_parser.py` | **されていない** |
| **`full-review/SKILL.md:130`** | `.claude/hooks/analyzers/scale_detector.py` | **されていない** |
| **`managed/rules/subprocess-encoding-convention.md:205`** | `.claude/tests/rules/test_subprocess_encoding_convention.py` | **されていない** |
| `release/SKILL.md:61` | `.claude/scripts/verify_plugin_containment.py` | されていないが **`[ -d plugins ] &&` で防御済** |
| `autonomous` / `full-review` / `lam-orchestrate` の 6 箇所 | `.claude/lam-loop-state.json` 等 | **実行時生成物**（偽陽性） |

**`/lam-harness:quick-save` と `/lam-harness:full-review` は、利用者環境で実際に落ちる。**
これは cosmetic ではなく**機能破壊**であり、192 箇所のどれよりも重い。

### (6) containment 欠陥 —— 配布規範が非配布規範を前提にしている

`.claude/rules/` **19 件** vs `templates/managed/rules/` **14 件**。非配布は
`hga-summoning.md` / `auto-generated/rule-001.md` / `auto-generated/rule-002.md`（＋ starter 経由 2 件）。

- `managed/docs-internal/06_DECISION_MAKING.md:256` → `.claude/rules/hga-summoning.md`
- `managed/rules/model-delegation-prompting.md:79` → 同上
- `skills/quick-save/SKILL.md:49` → `.claude/rules/auto-generated/rule-001.md`
- `managed/docs-internal/08_EXECUTION_DISCIPLINE.md:243` → 同上

### (7) upstream 実測（**2026-09-07 / 一次資料を逐語取得**）

`code.claude.com/docs/en/plugins-reference` §Environment variables の表（逐語）:

| Plugin component | Fields where placeholders resolve |
|:--|:--|
| **Skill and agent content** | **Anywhere the placeholder appears** |
| Hook and monitor commands | Anywhere the placeholder appears |
| MCP `stdio` servers | `command`, `args`, `env` |
| MCP `http`/`sse`/`ws` | `url`, `headers`, `headersHelper` |
| LSP servers | `command`, `args`, `env`, `workspaceFolder` |

変数は 3 つ（`${CLAUDE_PLUGIN_ROOT}` / `${CLAUDE_PLUGIN_DATA}` / `${CLAUDE_PROJECT_DIR}`）。
**`${CLAUDE_SKILL_DIR}`** は `docs/en/skills` に別途あり（「allowed-tools と skill prompt body の両方で使う」）が
**plugins-reference には記載が無い**（射程差は**未確認**）。

**決定的な帰結**: `${CLAUDE_PLUGIN_ROOT}` は **skill / agent content では散文中でも展開される**。
しかし **T1 managed の出力は plugin component ではない**（利用者のただの project ファイル）ため、
**そこでは展開されない**。そして T1 が最大の参照元である（上記 (2)）。

### (8) その他の確定事実

- 既存検査 **T2 = `check_reference_closure`** の `_NON_DISTRIBUTED_REFS` は **手書き 1 件**（`docs/private/`）
- `_PLUGIN_ROOT_REF_RE` は **T4 で既に使用中**
- `verify_plugin_containment.py` の呼び出しは **`release/SKILL.md:61` の 1 箇所のみ**（実読確認）
- plugin `version` = **0.1.0**、リポジトリ tag = **v5.1.0**。**対応していない**（URL の pin に効く）
- リポジトリは **public**（`https://github.com/sougetuOte/LivingArchitectModel`）

---

## Step -0.5: 外部知見（独立 2 subagent / 2026-09-07）

### (ε) パッケージ内文書が同パッケージ内ファイルを指す形

**収束**: 全生態系が「**物理パスを捨て、論理アンカー ＋ 実行時解決に置換**」で一致。錨は
importlib=パッケージ名 / Node=パッケージ名 / Antora=resource ID / VS Code=`extensionUri` /
Claude Code=`${CLAUDE_PLUGIN_ROOT}`。**錨は「install 後にランタイムが知っている値」でなければならない。**

**収束**: 参照の**解決**と**許可**は同じ機構の裏表（Node `exports` / VS Code `localResourceRoots`）。

**収束**: **行番号は誰も推奨していない**。Sphinx `:lines:` は「編集すると黙って別の行にずれる」。

**割れ目**: **節/行の精度を保てるのは Antora だけ**。Claude Code の錨は**ファイル止まり**。

**割れ目**: **「同梱するか」で分岐する** —— Sphinx は viewcode（同梱・埋め込み）と
linkcode（**外部 URL を返す**）を**別拡張として分離**した。

**割れ目**: root 相対の環境変数を散文中で展開するか —— Claude Code は**認める**。
VS Code は文字列置換を採らず**型のある変換関数**（`asWebviewUri`）を要求する。

出典: docs.python.org/3/library/importlib.resources.html ・ setuptools.pypa.io/en/latest/userguide/datafiles.html ・
sphinx-doc.org/…/viewcode.html ・ …/linkcode.html ・ …/directives.html ・
docs.antora.org/antora/latest/page/resource-id-coordinates/ ・ code.visualstudio.com/api/extension-guides/webview ・
nodejs.org/api/packages.html ・ pnpm.io/motivation ・ code.claude.com/docs/en/plugins-reference

### (ζ) 配布物中の「開発専用物への参照」

**収束**: 「**同梱物の選定**」と「**参照の健全性**」は**別レイヤー**。npm `files` / Cargo `include` /
MANIFEST.in は*ファイルが出荷されるか*だけを決め、文書内の参照テキストに一切関与しない。

**収束**: どの生態系も「**既知の欠落**」という**第三の状態**を持つ（Sphinx `nitpick_ignore` =
"a way to mark missing references as 'known missing'" / lychee `.lycheeignore` / check-manifest `ignore` /
rustdoc `#[allow]`）。**消すか残すかの二択にしていない。**

**収束（allowlist）**: 出荷物は allowlist が最終権限。npm は「ルート `.npmignore` は `files` を
上書きしない」と明言、Cargo は `include` 指定時に gitignore を適用しない。

**割れ目 1（既定の厳しさ）**: Docusaurus `onBrokenLinks: 'throw'`（既定で落とす）vs
Sphinx `nitpicky: False`（既定で黙る）vs MkDocs / rustdoc = 既定 warn。
**新規コーパス前提か既存コーパス前提かで既定が逆向き。**

**割れ目 3（死んだ参照の是非）**: パッケージング系・リンクチェッカ系は**死リンク＝欠陥**。
**ADR 原典（Nygard）は意図的に残す** —— "we will keep the old one around, but mark it as superseded" /
"It's still relevant to know that it *was* the decision"。根拠は**追跡可能性**で軸が違う。

**割れ目 4（消すか書き換えるか）**: **Kubernetes** は非同梱物への参照を**正典 URL へ書き換える**
（"Wherever possible, Kubernetes docs link to canonical sources instead of hosting dual-sourced content" /
理由は「二重管理は保守コスト倍・陳腐化が速い」）。**Rust** は書き換えず `#[doc(hidden)]` で
**同一ソースを配布形態別に出し分ける gate 方式**。

出典: docs.npmjs.com/cli/v10/configuring-npm/package-json ・ pypi.org/project/check-manifest/ ・
doc.rust-lang.org/cargo/reference/manifest.html ・ doc.rust-lang.org/rustdoc/lints.html ・
docusaurus.io/docs/api/docusaurus-config ・ sphinx-doc.org/en/master/usage/configuration.html ・
github.com/lycheeverse/lychee ・ mkdocs.org/user-guide/configuration/ ・
cognitect.com/blog/2011/11/15/documenting-architecture-decisions ・ kubernetes.io/docs/contribute/style/content-guide/

---

## Step -0.25: HGA #35 の裁定（要点 / 全文は `hga-summon-log.md` §35）

- **crux 1**: 「構文位置だけで決まる」は転用できない。転用できるのは**一段上の原理 =「分類を基質からの導出に置き換える」**。4c の基質は **2 つの環境のファイルシステム**（`exists_dev` / `exists_user`）＋既存の構造定数。**判定はファイル単位**（prefix では壊れる）
- **crux 2**: T1 に「利用者環境で機械的に解決する綴り」は**原理的に無い**。`${CLAUDE_PLUGIN_ROOT}` を
  展開されない場所でも**論理アンカー**として使う案を推奨。**歯止め**: 「生成器の各変換は、既存の構造定数
  または基質からの導出関数のみを入力とし、**新しいリストを持ち込んではならない**」
- **crux 3**: **Kubernetes 型の正典 URL を採用**。分岐の軸は `exists_user(P)`（**用途による分岐は置かない**）
- **crux 4**: **第三の状態は不要**。「R-P は全域規則なので残余はゼロになる」。ゲートは `/release` に据え置き、
  T2 を `exists_user` ベースへ差し替えて exit 1
- **crux 5**: **層で 3 分割**（4c-0 計器 / 4c-1 配布集合 = **PM 級** / 4c-2 参照）。着手順は 0 → 1 → 2
- **見落とし 5**: **名前参照への変換（パス → `lam-harness:magi`）は採るな。** 名前は「起動」の錨、
  パスは「読む」の錨。変換すると「invoke せずに Read する」経路が消える
- **確信度 0.70**。最大の不確実要因は「`${CLAUDE_PLUGIN_ROOT}` を rules で論理アンカーとして使う案の未実測」

---

## Step 0: AoT Decomposition

| Atom | 判断内容 | 読む状態 | 書く状態 |
|:--|:--|:--|:--|
| **C0** | **計器の是正範囲** —— census を gate の文法へ昇格させるとき、何を直すか | Step -1 (1)(4)(5) / `census_dangling.py:102-153` 実読 / HGA #35 crux 1・見落とし 1 | 本アンカー §Atom C0 |
| **C1** | **規則 R-P の定義** —— 何を何へ写すか。とくに T1 で `${CLAUDE_PLUGIN_ROOT}` を使うか | Step -1 (2)(3)(7) / (ε) の錨の条件 / HGA #35 crux 2・見落とし 3・5 / `CLAUDE.md` §Python Invocation Convention 段2 教訓 | 本アンカー §Atom C1 |
| **C2** | **配布集合の閉包** —— 非配布実体を呼ぶ配布 skill（実害 13）と非配布規範への参照をどうするか | Step -1 (5)(6) / (ζ) の allowlist 収束 / HGA #35 crux 5・見落とし 2 | 本アンカー §Atom C2 |
| **C3** | **ゲートの形と置き場所** —— T2 をどう差し替え、第三の状態を持つか | C0・C1・C2 の結論 / Step -1 (8) / (ζ) 割れ目 1 / HGA #35 crux 4 / LAM の「常時鳴る計器は殺される」 | 本アンカー §Atom C3 |
| **C4** | **分割・着手順・条文改訂** | C0〜C3 の結論 / ADR-0010 追補 3 / HGA #35 crux 5 | 本アンカー §Atom C4 |

**書込集合は本アンカーの相異なる節のみで交わらない。**
**C0 と C1 は互いの書く状態を読まない → 並列可。C2 は C1 の結論を読まない**（配布集合の決定は綴りに依らない）
**が、C1 の分岐 2/3 は C2 の結論（`exists_user` の値）を読む** → **C2 → C1 の順**。
**C3 は C0・C1・C2 を読み、C4 は C0〜C3 を読む** → 逐次。

> **前段の訂正**: 初稿では C1 → C2 と置いたが、**配布集合が動けば `exists_user` が変わり
> R-P の出力が反転する**（`hga-summoning.md` への参照が URL ↔ ローカルで入れ替わる）。
> HGA #35 crux 5 の「集合を先に凍結しないと codemod が二度走る」に従い順序を入れ替えた。

---

## Atom C0: 計器の是正範囲

**[MELCHIOR]**: 4 点直せば済む。(a) `PATH_RE` に `*?` を含めるか PLACEHOLDER をスパン全体に当てる
（glob 切り詰め）/ (b) 比較を case-sensitive にする（利用者環境は Linux でありうる）/
(c) `exists_dev × exists_user` の 2 環境行列を出す / (d) フェンス内コマンドを走査する。
どれも小さく、テストで固定できる。

**[BALTHASAR]**: 3 点。

**(i) (d) は「走査対象を広げる」ではなく「別の検査を足す」である。** フェンス内コマンドの
パス引数に対して R-P を当てるのは**無意味かつ有害**である —— コマンド引数が URL に化けたら
コマンドとして壊れる。あれは**参照の問題ではなく配布集合の問題**（C2）であり、
**計器としては別の出力欄に分けねばならない**。混ぜると C2 の判断材料が C1 の変換対象に流れ込む。

**(ii) (b) の case-sensitive 化は、意図的誤記を射程外に落とす仕掛けとして機能するが、
それは副作用であって根拠ではない。** 根拠は「利用者環境が Linux でありうる」であり、
**その根拠で正しいことが、たまたま偽陽性も消す**。**逆順に導出してはならない**
（「偽陽性を消したいから case-sensitive にする」は、目的から手段を逆算した例外表と同型）。

**(iii) 陰性対照が要る。** 私は本セッションで、自分の probe が「ディレクトリ配下を無条件に
解決済み扱いする」バグを持っていたのを**陰性対照で発見した**（50 件すべて緑 → 厳密化して 13 件）。
**計器の是正には、是正が効いていることを示す対照が要る。**

**[CASPAR]**: 結論 —— **4 点すべて直す。ただし (d) は別欄に分ける。**

| # | 是正 | 根拠 | 対照 |
|:-:|:--|:--|:--|
| a | glob 切り詰めの修正 | `PATH_RE` に `*` が無く、PLACEHOLDER が一致部分より後を見ない（実読） | `` `.claude/agents/*.md` `` が除外されること／`.claude/agents/gabriel.md` は除外**されない**こと |
| b | 比較を case-sensitive に | **利用者環境が Linux でありうる**（意図的誤記が射程外に落ちるのは帰結であって根拠ではない） | `.claude/Rules/...` が `exists_dev`=False になること |
| c | `exists_dev × exists_user` の 2 環境行列 | 機構 #10（LAM 内で解決するか）との**役割分担を明示**する。意図的誤記は #10 の領分 | 4 象限すべてに件数が出ること |
| d | **フェンス内コマンドを別欄で走査** | **実害 13 箇所は 192 のどれより重い**（機能破壊） | 実行時生成物（`lam-loop-state.json`）が偽陽性として分離されること |

**(d) を別欄にする理由を明文化する**: **コマンド引数に R-P を当ててはならない。**
URL 化すればコマンドが壊れ、`${CLAUDE_PLUGIN_ROOT}` 化しても*非配布*なら実体が無い。
**これは綴りでは直らない。配るか、手順から外すかの二択である**（→ C2）。

**採用しなかった選択肢とその理由**:

- **census をゲート化してから直す** → 「初日から真っ赤」を自作する。HGA #34 裁定 3 と 4b B4 #3
  （codemod + 生成器 + 検査を同一コミット）に反する
- **偽陽性を除外リストで消す** → 4a・4b が 2 度棄却した「人が 1 件ずつ承認する分類」。
  かつ (a) は**そもそもバグ**であり、除外リストで隠せば原因が残る
- **`NG-*` の分類名を変える** → 記録との突合が切れる（HGA #35「変えてはならないもの」）。**列は足してよい**

---

## Atom C2: 配布集合の閉包（**PM 級を含む**）

> **順序の都合により C1 より先に置く**（Step 0 の訂正を参照）。

**[MELCHIOR]**: 実害 13 箇所は、必要なものを配れば消える。`build_dashboard.py` と
`scale_detector.py` を `templates/managed/scripts/` に足し、テストも配ればよい。
非配布規範（`hga-summoning.md` / `rule-001.md`）も配ってしまえば containment 欠陥も消える。
**allowlist を広げるのが最も単純である。**

**[BALTHASAR]**: **その単純さが罠である。** 4 点。

**(i) 「配れば解決する」は配布集合の意味を壊す。** `hga-summoning.md` は **Fable 5 召喚の LAM 固有規律**で、
envelope・weekly quota・過去の召喚単価まで含む。利用者に配るものではない。
`auto-generated/rule-001.md` は **LAM の SESSION_STATE が 6 回壊れた観測記録**であり、
利用者が持つべきは**生成の仕組み**（`README.md` と `trust-model.md` = 既に配布済）であって
**LAM の観測結果ではない**。**配布集合は「利用に要るか」で決まる**（(ζ) npm / Cargo の収束点）。

**(ii) テストを配るのは別の判断である。** `.claude/tests/` を配れば、利用者は LAM の
回帰テストを丸ごと受け取る。**それは製品ではなく開発資産**である。しかし
`quick-save/SKILL.md:52` は「rule-001 に従って SESSION_STATE を確認せよ」の**検証手段**として
そのテストを名指ししている。**手段を配らずに手順だけ配ったのが誤り**であって、
テストを配るのが正解とは限らない。

**(iii) `subprocess-encoding-convention.md`（最大の参照元 18 箇所）は製品規範か。**
中身は「LAM リポジトリ内の Python 全域で `build_allowlisted_env()` を使え」という**開発規約**で、
誤例・回帰テスト・grep baseline がすべて LAM 内部の事象を指す。**配るべきかを問い直す価値がある**
（HGA #35 見落とし 2: 「配布集合の決定 1 件で 18 箇所が消える」）。**ただしこれは私の読みであり、
ユーザー意思の確認を要する PM 級判断である。**

**(iv) 逆に、`build_dashboard.py` は配るべきかもしれない。** `/lam-harness:quick-save` は
**利用者が日常的に打つ skill** であり、その手順が落ちるのは製品の欠陥である。
**skill が呼ぶ実体は配る**（P2 複製相で `py_invoke.sh` について既に通った判断 ——
`_MANAGED_AREAS` の `scripts` はまさにその事故の後に足された）。

**[CASPAR]**: 結論 —— **配布集合の判断軸は「利用に要るか、開発に要るか」の一本**（(ζ) の収束点）。
**これは参照の分類ではなく、有界な集合（19 − 14 = 5 ＋ 実害 13 の被参照実体）に対するファイル単位の出荷可否**であり、
「分類の復活」とは区別される。**PM 級としてユーザーに諮る。**

L1 の提案（**決定はユーザー**）:

| 対象 | 提案 | 根拠 |
|:--|:--|:--|
| `build_dashboard.py` | **配る**（`templates/managed/scripts/`） | `/lam-harness:quick-save` が呼ぶ。skill が呼ぶ実体は配る（P2 の既決パターン） |
| `scale_detector.py` | **配る** | `/lam-harness:full-review` Stage 1 が呼ぶ。同上。**監査 W-1 とも重なる** |
| `.claude/tests/**` | **配らない** | 開発資産。代わりに**手順側を書き換える**（下記） |
| `hga-summoning.md` | **配らない** | LAM 固有（Fable envelope / 召喚単価）。参照は URL 化（C1） |
| `auto-generated/rule-001.md` / `rule-002.md` | **配らない** | LAM の観測記録。生成の仕組み（`README.md` / `trust-model.md`）は既に配布済 |
| **`subprocess-encoding-convention.md`** | **要ユーザー判断**（L1 の読みは「開発規約であり配布対象外」） | 18 箇所が 1 決定で消える。**ただし配布中の既存規範を引き上げる = 利用者の規範が減る** |

**テストを配らない場合の手順側の書き換え**（`quick-save` / `subprocess-encoding-convention`）:
検証コマンドが**利用者環境に存在しないファイル**を名指ししている箇所は、
**「LAM 開発時のみ」と明示するか、利用者環境で実行可能な検証に置き換える**。
これは C1 の綴り変換では直らない（コマンドは実行される）。

**採用しなかった選択肢とその理由**:

- **すべて配る** → 配布集合が「LAM リポジトリ全体」に膨張し、allowlist の意味が消える。
  (ζ) の「npm はルート `.npmignore` が `files` を上書きしないと明言」= allowlist が最終権限、に反する
- **何も配らず参照だけ直す** → **実害 13 が残る**。`/lam-harness:quick-save` は落ちたままで、
  「綴りは緑だが製品は壊れている」= `rule-001` 観測 #6 型（緑なのに事実と食い違う）
- **skill 側の手順から検証ステップごと削除** → `rule-001` は観測 6 回の恒久解であり、
  検証を落とすと守られなくなる。**手段を配るか、代替手段を与えるかであって、規律を消す話ではない**

---

## Atom C1: 規則 R-P の定義

**[MELCHIOR]**: HGA #35 の 3 分岐をそのまま採る。

```
exists_user(P)                          → そのまま
¬exists_user ∧ 配布物に実体あり          → ${CLAUDE_PLUGIN_ROOT}/<plugin 相対パス>
¬exists_user ∧ 配布物に実体なし          → <base URL>/<P>
```

逆写像は固定文字列の除去で**無損失**。`_PLUGIN_ROOT_REF_RE` は T4 で実在。
T3 は逆方向、T1 は順方向に**同じ prefix 写像**を当てる（規則 1 本・向き 2 つ / HGA 見落とし 3）。
名前参照（`lam-harness:magi`）には**変換しない**（HGA 見落とし 5: 名前は起動の錨、パスは読む錨）。

**[BALTHASAR]**: 分岐 2 に **LAM が既に一度踏んだ穴**がある。

**`CLAUDE.md` §Python Invocation Convention の「段2 fixup 教訓」を読め** ——

> settings.json hook 形式（`bash "$CLAUDE_PROJECT_DIR/..."`）を SKILL.md にコピペしたが、
> Bash tool 実行環境で `$CLAUDE_PROJECT_DIR` が unset のため展開結果が
> **`bash "/.claude/scripts/py_invoke.sh"`（exit 127）**となる問題を push 前に L1 実測で検出

**`${CLAUDE_PLUGIN_ROOT}` が展開されない文脈で、モデルがそれを Bash に渡せば
`/hooks/pre-tool-use.py` という「ファイルシステム root 直下の絶対パス」に潰れる。**
**LAM は全く同じ形で 26 箇所を作り、push 前にかろうじて捕まえた。**

そして **T1 managed の出力はまさに「展開されない文脈」である**（Step -1 (7)）。
**最大の参照元（97 箇所）に、過去に事故った形を意図的に植えることになる。**

**さらに悪いのは非対称性である** —— 展開される T3（skill/agent content）では正しく動き、
展開されない T1 では静かに潰れる。**同じ綴りが場所によって別の意味を持つ**。
Ansible の bare `copy` 事故（「短縮形だと思っていたら別解決だった」）と同型である。

**[MELCHIOR]**: では T1 は URL にすればよい。URL は**構文的にパスではない**ので、
Bash に渡っても `/hooks/...` には潰れない。分岐 2 を T3 に限れば非対称は消える。

**[BALTHASAR]**: それは「用途による分岐」ではないか。HGA は「用途で分けるな」と言った。

**[MELCHIOR]**: 用途ではない。**参照元がどの層か**であり、それは `_MIRROR_AREAS` /
`_MANAGED_AREAS` という**既存の構造定数**で決まる。1 件ずつの判断を含まない。

**[CASPAR]**: 結論 —— **R-P を「参照元の層 × 参照先の実在」の全域規則として定義する。
分岐 2 は T3（プレースホルダが展開される層）に限定する。**

```
R-P(P, src) =
  exists_user(P)                                   → P（そのまま）
  ¬exists_user(P) ∧ src ∈ T3 ∧ exists_dist(P)      → ${CLAUDE_PLUGIN_ROOT}/<plugin 相対>
  otherwise                                        → <base URL>/<P>
```

- **`src ∈ T3`**（= `plugins/<plugin>/{skills,agents}` の Markdown）は **`_MIRROR_AREAS` から導出**する。
  用途の判断ではない
- **`exists_dist(P)` は<ins>ファイル単位</ins>**（prefix ではない）。反例: `.claude/hooks/analyzers/scale_detector.py`
- **T1 managed は常に URL** —— 展開されない場所にプレースホルダを植えない
- **名前参照への変換はしない**。節アンカー（`§Step 4.1`）は**どちらの形でも後置のまま保持される**
- **逆写像**: `${CLAUDE_PLUGIN_ROOT}/<area>/X → .claude/<area>/X`（`_MIRROR_AREAS`）/
  `<base URL>/<P> → P`（base の除去）。**両方とも無損失** → 往復恒等が両方向で成立する

**base URL の ref**: `blob/master/` を採る。理由 —— plugin `version` 0.1.0 と tag v5.1.0 が
**対応していない**（Step -1 (8)）ため version pin の経路が無い。commit SHA を焼くと**生成が非冪等**になり
T1 検査（派生 == 導出）が HEAD 移動のたびに落ちる（**禁止**）。
**release 手順で plugin version と tag を揃える運用ができれば pin へ移れる** → C4 で起票。

**HGA が置いた歯止めを採用する**: **生成器の各変換は、既存の構造定数または基質からの導出関数のみを
入力とし、新しいリテラル集合を持ち込んではならない。** R-A は `component_names()`、R-S は `skill_names()`、
R-P は `_MIRROR_AREAS` ＋ `build_user_env()` ＋ `exists_dist()` を読む。
**新しい `_SOMETHING = (...)` を伴う変換追加は分類の復活であり却下。**

**採用しなかった選択肢とその理由**:

- **T1 でも `${CLAUDE_PLUGIN_ROOT}` を論理アンカーとして使う**（HGA #35 の推奨）→
  **展開されない文脈に植えると `/hooks/...` へ潰れる**。LAM は同型の事故を 2026-07-12 に
  26 箇所作っている（`CLAUDE.md` 段2 教訓）。**HGA 自身が「未実測」を最大の不確実要因に挙げていた箇所であり、
  実測ではなく既存の事故記録で否定できた**
- **すべて URL に統一する**（分岐 2 を廃止）→ T3 では `${CLAUDE_PLUGIN_ROOT}` が**実際に展開される**
  （上流が明記）。**解決する綴りがあるのに解決しない綴りを選ぶ**ことになる。
  かつ「invoke せずに Read する」経路を失う（HGA 見落とし 5）
- **パス → 名前参照（`lam-harness:magi`）** → 起動の錨と読む錨の混同。節アンカーの行き先が消える
- **削除** → 根拠・棄却理由は実質であって filler ではない（`artifact-length-calibration.md`）。
  かつ削除は逆写像を持たず生成器に載らない

---

## Atom C3: ゲートの形と置き場所

**[MELCHIOR]**: T2 の `_NON_DISTRIBUTED_REFS`（手書き 1 件）を `exists_user` ベースへ差し替え、
`/release` で exit 1。第三の状態は要らない —— R-P は全域規則なので残余はゼロになる。

**[BALTHASAR]**: **「残余はゼロになる」は R-P の射程内での話である。** 3 点。

**(i) 実害 13（フェンス内コマンド）は R-P の射程外**であり、C2 の決定で消えるが、
**「配らない」と決めた分は残る**（テストを配らないなら、手順側の書き換えが要る）。
**残余がゼロだという主張は、C2 の決定を待たなければ立たない。**

**(ii) ゲートの射程を宣言せよ。** census の走査は「コードスパンと Markdown リンク」で、
**素の散文のパスは拾わない**（docstring 明記の下界）。**ゲート化したとき、
「緑 = 解決しない参照が無い」ではなく「緑 = 走査した範囲に無い」である。**
これを書かないと `rule-001` 観測 #6 型（緑なのに事実と食い違う）を再生産する。

**(iii) `/release` に置くのは正しいが、`/release` が現に呼んでいるのは
`verify_plugin_containment.py` **1 本のみ**であり、そこに `[ -d plugins ] &&` のガードが付いている。
**利用者環境では `plugins/` が無いのでスキップされる。** これは意図どおり（利用者は配布しない）だが、
**LAM 自身が `/release` を打たない限りゲートは一度も走らない**。発火点の実在を確認せよ。

**[CASPAR]**: 結論 ——

| # | 内容 |
|:-:|:--|
| 1 | **T2 を `exists_user` ベースへ差し替え**、`/release` で **exit 1**。`/ship` `/quick-save` には置かない（「常時鳴る計器は殺される」） |
| 2 | **第三の状態（既知の欠落リスト）は持たない。** ratchet も nitpick_ignore も「人が承認した宣言」であり、HGA #34 裁定 1 が「符号を反転させた宣言」と呼んだ族。**R-P が全域なら残余はゼロ**であり、ゼロでないなら**規則か配布集合が間違っている**（そちらを直す） |
| 3 | **ゲートの射程を docstring と検査メッセージに明記する** —— 「走査対象はコードスパン・Markdown リンク・フェンス内コマンド。**素の散文は射程外（下界）**」 |
| 4 | **同一コミット**で codemod（T3 正本）＋ 生成器 R-P（T1）＋ 検査差し替えを入れる。**段階を作らない**（HGA #34 裁定 3） |
| 5 | **陰性対照を置く** —— 「利用者環境に実在する参照（`.claude/rules/permission-levels.md` 等）が緑のままであること」「実行時生成物が偽陽性にならないこと」 |

**採用しなかった選択肢とその理由**:

- **ベースライン ratchet / `nitpick_ignore` 型の既知欠落リスト** → 4a で棄却済（**再論しない**）。
  外部知見が持つのは「推論型の検査に打ち消し記法が必須の対として付く」ためで、**LAM は推論型を採らない**
- **警告から始めて後で error に上げる** → 「来ない段階は作らないのが最良の強制」（HGA #34 裁定 3）
- **`/ship` にも置く** → 毎コミット鳴る計器は殺される（HGA #34）

---

## Atom C4: 分割・着手順・条文改訂

**[MELCHIOR]**: HGA の 3 分割（4c-0 / 4c-1 / 4c-2）をそのまま採り、0 → 1 → 2 で進む。

**[BALTHASAR]**: 条文が先である。**ADR-0010 追補 3 の不変条件は「bare の<ins>実行参照</ins>」しか
拘束していない**。パス参照が実行参照に当たるかは**解釈**であり、解釈で機構を入れれば
「実装と条文のドリフト」を自分で作る —— **4b が gabriel の指摘 1 で踏み止まった、まさにその形**である。

かつ **K4「配布集合 ⊆ 開発ロード集合」には「規範から規範への参照について閉じている」が無い**。
C2 の決定（何を配り何を配らないか）は、その閉包条項が無ければ**次に必ず破れる**。

**[CASPAR]**: 結論 —— **ADR-0010 追補 4（PM 級）を 4c-2 の前に置く。**

| Action | 層 | 内容 | 等級 |
|:--|:--|:--|:--|
| **4c-0** | 計器 | census の 4 点是正（glob / case / 2 環境行列 / フェンス内コマンドを**別欄**で） | SE |
| **4c-1** | 配布集合 | C2 の表をユーザーに諮り、配布集合を凍結。実害 13 の解消（配る or 手順書き換え） | **PM** |
| **追補 4** | 条文 | 不変条件に**パス参照**を加える ＋ K4 に**規範間参照の閉包**を加える | **PM** |
| **4c-2** | 参照 | R-P を生成器（T1 順 / T3 逆）へ追加、T3 正本 codemod、T2 差し替え、**diff 全数レビュー**、往復恒等の両方向検証 | SE |

**着手順: 4c-0 → 4c-1 →（追補 4）→ 4c-2。**
4c-1 を先に置く理由: **配布集合が動けば `exists_user` が変わり、R-P の出力が反転する**
（`hga-summoning.md` への参照が URL ↔ ローカルで入れ替わる）。集合を凍結しないと codemod が二度走る。

**追補 4 の文言案**（PM 級 / ユーザー承認を要する）:

> **不変条件（追補 3 の拡張）**: 配布される側に残ってよいのは、(a) 利用者環境で解決する参照、
> (b) `${CLAUDE_PLUGIN_ROOT}` を用いた参照（**プレースホルダが展開される層に限る**）、
> (c) 正典 URL のいずれかである。**bare な repo 相対パスは配布される側に残さない。**
>
> **K4 の拡張**: 配布集合は**規範から規範への参照について閉じている** ——
> 配布される規範が名指しする規範・スクリプト・検証手段は、配布されるか、
> **利用者環境で実行可能な代替が示されていなければならない**。

**採用しなかった選択肢とその理由**:

- **4c を 1 つの Action として実施** → 192 箇所は少なくとも 4 種の別問題（Step -1）。
  4a → 4b の分割が正しかったのと同じ理由
- **条文を後追いで直す** → 追補 2 決定 3 自身が「**観測と条文のドリフトは、条文側を直さなければまた失われる**」と述べる
- **症状（移設もの / 開発記録 / 偽陽性 / containment）で分割** → 症状は結論であって層ではない。
  (ζ) の「同梱物の選定と参照の健全性は別レイヤー」に従い**層で切る**

---

## Step 4: gabriel probe（1 巡目）

| 項目 | 値 |
|:--|:--|
| verdict | **refuted** |
| severity | **critical** |
| affected_atoms | C0 / C1 / C2 / C3 / C4 |
| recommended_action | **re-magi** |
| confidence | 0.72 |

分岐は **AC-W-C-5**（`refuted & critical` 初回 → **再 MAGI 1 ラウンド**）。
計器: `.claude/gabriel-metrics.log` に 1 行追記済（`resolved_action: re_magi` / **分岐前に記録**）。

### L1 による独立検証（**gabriel を額面で受け取らない**）

gabriel の実測主張を L1 が独立に確認した。**全件が実在した。**

| gabriel の主張 | L1 の検証 |
|:--|:--|
| `templates/managed/scripts` に `build_dashboard.py` / `scale_detector.py` が無い | **真**（12 ファイルを実見） |
| `scale_detector.py` は `.claude/hooks/analyzers/` にあり `analyzers.config` / `analyzers.run_pipeline` を import | **真**（:16-17 実読） |
| `build_dashboard.py` は `dashboard.{builder,merger,models,parsers.*}` を import | **真**（:131-172 実読 / 6 モジュール） |
| `pre-tool-use.py:645` が非配布の `docs/artifacts/incident-patterns.yaml` を読み **fail-open** | **真**（:645・:681 実読 / `find plugins -name incident-patterns.yaml` = **0 件** / 一方 loader `_incident_patterns.py` は**配布されている**） |
| `verify()` は `test_real_repo_has_no_violations` で**実リポジトリに毎回走る** | **真**（`test_verify_plugin_containment.py:56` 実読） |
| **`py-fixture` 除外の理由が偽** | **真**。9 件の中身を実見したところ、**6 件が配布コードの docstring**（`hooks/pre-compact.py:119,131` / `hooks/pre-tool-use.py:306` / `templates/managed/scripts/verify_distributable_claims.py:15,237` 他）。残る 3 件のみが真の合成例（`.claude/Rules/...` / `docs/../specs` / `.claude/hooks-local`） |
| `PATH_RE` が生成 URL の内部に**再マッチ**する | **真**（実行確認: `…/blob/master/docs/adr/0010-x.md` → `['docs/adr/0010-x.md']`） |
| starter `CHEATSHEET.md:34` が `otherwise` に落ちて URL 化される | **真**（実測 1 箇所） |
| 4a/4b との衝突（`magi/SKILL.md:350`）は**成立しない** | **真**（R-A の除外 (P) が効く。gabriel は自らこの疑いを棄却した） |

**gabriel の指摘は正しい。C3 の「残余はゼロ」は基質と矛盾していた。**

---

# 再 MAGI（2 巡目 / AC-W-C-5 / gabriel.reasoning を Divergence 入力に追加）

## Step 1': Divergence（gabriel が突きつけた 5 争点）

1. **R-P の適用域は `.md` のみか**（→ C3 の「残余ゼロ」が生きるか死ぬか）
2. **C2 の「配る」の単位はファイルかパッケージか**（import 閉包 ＋ `_MANAGED_AREAS` の扱い）
3. **配布コンポーネントの実行時データ依存を閉包に含めるか**（`incident-patterns.yaml`）
4. **starter を R-P の第 3 層として射程外に置くか**
5. **分岐 2 / URL 分岐に到達性検査を付けるか**（ゲートのトートロジー化の回避）

---

## Atom C0'（改訂）: 計器の是正範囲

**[MELCHIOR]**: 4 点に 1 点足せばよい。`py-fixture` 除外を解体する。

**[BALTHASAR]**: **2 点、書き方そのものを直せ。**

**(i) 「比較を case-sensitive にする」は処方として誤りである。** 既存判定は `ref in files`
（Python の集合メンバシップ）で**既に厳密一致**である。case が化けるのは、C0 (c) で新設する
`exists_dev` を **`Path.is_file()` で実装した場合**であり、NTFS では case-insensitive になる。
**これは `permission-levels.md` が 2026-09-05 に踏んだ罠と同型**（`normalize_path` が FS に
問い合わせないため `.claude/Rules/…` が SE 判定になった）。
**正しい処方は「FS 問い合わせを使わず、`rglob` 由来の集合で判定する」**である。

**(ii) `py-fixture` の解体は「除外を消す」ではなく「偽の理由を真の理由に置き換える」である。**
9 件は 2 種に割れる —— **真の合成例 3 件**（意図的に実在しない文字列）と
**配布コードの docstring 6 件**。前者は「合成例」、後者は「**`.py` は R-P の射程外**」であり、
**理由が違えば別の除外である**。1 つの箱に入れていたから理由が偽になった。

**[CASPAR]**: 結論 —— **是正は 5 点。うち 2 点は 1 巡目の記述を訂正する。**

| # | 是正 | 根拠 | 陰性対照 |
|:-:|:--|:--|:--|
| a | glob 切り詰めの修正 | `PATH_RE` に `*` が無く PLACEHOLDER が一致部分より後を見ない | `` `.claude/agents/*.md` `` が除外され、`.claude/agents/gabriel.md` は除外**されない** |
| b | **（訂正）** `exists_dev` / `exists_dist` を **`rglob` 由来の集合**で判定する（`Path.is_file()` を使わない） | NTFS の case-insensitive が判定を化かす。**`permission-levels.md` 2026-09-05 と同型** | `.claude/Rules/...` が `exists_dev`=False になること |
| c | `exists_dev × exists_user` の 2 環境行列 | 機構 #10 との役割分担（意図的誤記は #10 の領分） | 4 象限すべてに件数が出る |
| d | フェンス内コマンドを**別欄**で走査 | **実害 13 箇所は 192 のどれより重い**。**コマンド引数に R-P を当ててはならない** | 実行時生成物が偽陽性として分離される |
| e | **（新規）** `py-fixture` を **2 つの真の理由**へ解体 | 除外理由が**偽**だった（実測 6/9 が配布コードの docstring） | 配布 docstring 6 件が「`.py` 射程外」に、合成例 3 件が「合成例」に落ちる |

---

## Atom C2'（改訂）: 配布集合を**列挙ではなく閉包の導出**にする

**[MELCHIOR]**: 1 巡目の表（配る / 配らない）を直せば済む。`scale_detector.py` は
`plugins/lam-harness/hooks/analyzers/` へ、`build_dashboard.py` は `dashboard/` パッケージごと。

**[BALTHASAR]**: **表を直すのでは同じことがまた起きる。原因は表の中身ではなく、表であることだ。**

`_MIRROR_AREAS` の注記はこう書いている ——

> 開発側の analyzers / checkers / tests は **hook の import 閉包に含まれない（実測）** ため配布せず

**閉包は正しく計算されていた。計算したエントリポイントが hook だけだったのである。**
`/lam-harness:full-review` Stage 1 は `scale_detector.py` を呼ぶ。**skill をエントリポイントに
含めていれば analyzers は閉包内に入っていた。** `incident-patterns.yaml` も同じ ——
**loader（`_incident_patterns.py`）は配布されているのに、それが読むデータが閉包に入っていない。**

**したがって直すべきは「配布集合」ではなく「閉包の定義」である。**

**[CASPAR]**: 結論 —— **配布集合を、エントリポイントからの到達閉包として導出する**（維持リストを持たない / 機構 #7・#11 と同型）。

```
配布集合 = 閉包( エントリポイント )

エントリポイント = 配布 hooks ∪ 配布 skills のフェンス内コマンドが名指しする実体
                 ∪ 配布規範が名指しする検証手段
到達関係       = import 閉包 ∪ 実行時データ依存（コード中のパス構築）
```

**帰結（1 巡目の表を訂正する）**:

| 対象 | 1 巡目 | **2 巡目（訂正）** | 理由 |
|:--|:--|:--|:--|
| `scale_detector.py` | 「配る（`templates/managed/scripts/`）」 | **配る。ただし所在は `plugins/lam-harness/hooks/analyzers/`（T3 mirror）で、`analyzers` パッケージごと** | `_MANAGED_AREAS["scripts"] = .claude/scripts` なので managed へ置くと T1 が赤。かつ単ファイルでは import に失敗する |
| `build_dashboard.py` | 「配る」 | **配る。`dashboard/` パッケージごと**（`templates/managed/scripts/dashboard/`） | 6 モジュールを import する |
| **`incident-patterns.yaml`** | **表に無かった** | **配る**（実行時データ依存 / **security 機構が全利用者環境で沈黙している**） | loader は配布済。データだけ欠けて fail-open |
| `.claude/tests/**` | 配らない | 配らない（不変） | 開発資産。手順側を書き換える |
| `hga-summoning.md` / `rule-001` / `rule-002` | 配らない | 配らない（不変） | LAM 固有。参照は URL 化 |
| `subprocess-encoding-convention.md` | 要ユーザー判断 | **要ユーザー判断**（不変） | 18 箇所が 1 決定で消える |

**配る単位は<ins>ファイルではなくパッケージ</ins>である。**

**採用しなかった選択肢とその理由**:
- **表を直すだけ** → 閉包の定義が hook 限定のまま残り、次のエントリポイント追加で必ず再発する
- **`_MANAGED_AREAS` に行を足して `analyzers` を managed 扱いにする** → HGA #35 の歯止め
  （新しいリテラル集合を持ち込まない）に抵触し、かつ **analyzers は hook の隣に置くのが実体に忠実**
- **fail-open を仕様として文書化して配らない** → **security 機構が黙って無効**なまま。
  `rule-001` 観測 #6 型（緑のまま事実と食い違う）そのもの

---

## Atom C1'（改訂）: R-P の適用域・冪等性・合成順

**[MELCHIOR]**: 適用域は `.md` のみ。4a・4b と揃う。starter は射程外。

**[BALTHASAR]**: **それを認めるなら、C3 の「残余ゼロ」を撤回せねばならない。**
`.py` 内の参照は恒久的に残る。**残るものを「ゼロ」と言えば、それは計器の嘘である。**

かつ 2 点、1 巡目が書いていない要件がある。

**(i) 冪等性**: `PATH_RE` は生成 URL の内部に**再マッチする**（実測確認済）。
`collect()` の URL ガードは `span.startswith("http")` の**スパン単位**なので、
**スパン途中の URL は素通りする**。R-P の再適用が二重ラップになれば往復恒等が壊れる。

**(ii) 合成順**: R-A ∘ R-S ∘ R-P の順序が宣言されていない。
gabriel は危険候補 1 行（`magi/SKILL.md:350`）を実測して順序非依存と確認したが、
**測った 1 行が安全だったことは規則が順序非依存であることの証明ではない**。

**[CASPAR]**: 結論 —— **適用域を明記し、残余ゼロを撤回し、冪等性と合成順を要件に加える。**

| 項目 | 決定 |
|:--|:--|
| **適用域** | **配布物の `.md` のみ**。`.py` / `.sh` / `.json` は射程外（**読者は開発者** / 4a・4b と同じ判断 / 拡張子は構文的で分類を含まない） |
| **層の射程** | **`templates/starter/**` は第 3 層として射程外**。starter は「以後はあなたの資産」= **利用者所有ファイル**であり、配布物衛生の対象ではない。URL 化すれば利用者の CHEATSHEET が他人の repo を指す（**カテゴリ違い**） |
| **冪等性** | R-P は**トークン単位**で `http(s)://` 配下を除外する（スパン単位ガードでは不足 / 実測）。`R-P(R-P(x)) == R-P(x)` をテストで固定する |
| **合成順** | **R-P → R-A → R-S** に固定し、**固定した順序で往復恒等を検証する**。順序非依存は主張しない |
| 規則本体 | 1 巡目の 3 分岐を維持（`exists_user` / `src ∈ T3 ∧ exists_dist` / `otherwise` = URL）。**`exists_dist` はファイル単位** |

**残余についての正しい言明**（C3' で使う）:

> **残余は射程内（配布物の `.md` / starter を除く）でゼロになる。**
> **射程外（`.py` / `.sh` / starter / 素の散文）には残余が在り、それは真の理由で除外される。**

---

## Atom C3'（改訂）: ゲートの形

**[MELCHIOR]**: T2 を `exists_user` ベースへ差し替え、`/release` で exit 1。

**[BALTHASAR]**: **発火点の記述が事実と違う。** `verify()` は
`test_verify_plugin_containment.py::test_real_repo_has_no_violations` から
**実リポジトリに対して毎 pytest 走っている**（実読確認）。
「`/release` だけ」という前提で設計すると、**4c-2 の途中経過で全テストが赤になる**。

かつ **1 巡目のゲートはトートロジーである** —— R-P が全域なら「bare パスが無いこと」は
変換した以上自明に真であり、**検出できるのは新しく書かれた bare パスだけ**。
`${CLAUDE_PLUGIN_ROOT}/X` の X が消えても、URL の先が消えても、誰も気づかない。

**[CASPAR]**: 結論 ——

| # | 内容 |
|:-:|:--|
| 1 | **「残余ゼロ」を撤回**し、**射程を docstring と検査メッセージに明記する**（`.md` のみ / starter 除く / 素の散文は**下界**） |
| 2 | **到達性検査を足す**（**gabriel の指摘 / `exists_dist` は既に計算しているので無料**）—— 分岐 2 の出力は **T4 と同型**に plugin 内の実体を照合、URL 出力は **path 部が `exists_dev`** であることを照合。**これでゲートはトートロジーでなくなり、同時に `master` 固定 URL の腐敗検出も得られる** |
| 3 | **発火点を正しく書く** —— `verify()` は `/release` と**全 pytest 実行の両方**に載っている。同一コミット投入（#4）を守れば commit 時点で緑だが、**設計意図と実装ビークルの食い違いを明示する** |
| 4 | **同一コミット**で codemod ＋ 生成器 ＋ 検査を入れる（段階なし） |
| 5 | **第三の状態は持たない**（不変）。ただし根拠を訂正する —— 「全域だから残余ゼロ」ではなく、
**「射程内の残余はゼロ。射程外は<ins>構文的に</ins>（拡張子・パス prefix）除外され、参照ごとの承認を含まない」** |
| 6 | 陰性対照: 利用者環境に実在する参照が緑のまま / 実行時生成物が偽陽性にならない / **合成例 3 件が「合成例」の理由で除外される** |

---

## Atom C4'（改訂）: 分割・着手順・条文

**[CASPAR]**: 1 巡目の 4 段（4c-0 → 4c-1 → 追補 4 → 4c-2）は**維持する**。内容を 3 点改める。

1. **4c-1 は「表を諮る」ではなく「閉包を導出し、その結果を諮る」**（C2'）。導出器そのものが成果物になる
2. **追補 4 の K4 拡張文に「実行時データ依存」を入れる**（gabriel の指摘 3 / 現行案の
   「規範・スクリプト・検証手段」の 3 語では `incident-patterns.yaml` を捕捉しない）
3. **4c-2 の書込集合を宣言し直す**（1 巡目は 1 つ落としていた）

**4c-2 の書込集合（宣言）**:

| # | 対象 |
|:-:|:--|
| 1 | `plugins/lam-harness/{skills,agents}/**/*.md`（R-P codemod / T3 正本） |
| 2 | `plugins/lam-harness/templates/managed/**`（T1 再生成 = `derive_managed_templates.py --write`） |
| 3 | **`.claude/{skills,agents}/**`（T3 派生の再生成 = `derive_project_copies.py --write`）** ← **1 巡目に無かった。忘れると T3 が赤** |
| 4 | `.claude/scripts/{census_dangling,verify_plugin_containment,derive_managed_templates,derive_project_copies,namespace_source_refs}.py` |
| 5 | `.claude/tests/scripts/**`（新規・改訂） |
| 6 | **hook 副作用**: `.claude/logs/permission.log`（append-only / 他 Atom が読み返さない） |

**追補 4 の文言案（改訂 / PM 級）**:

> **不変条件（追補 3 の拡張）**: 配布される側の **Markdown** に残ってよいパス参照は、
> (a) 利用者環境で解決するもの、(b) `${CLAUDE_PLUGIN_ROOT}` を用いるもの（**プレースホルダが
> 展開される層に限る**）、(c) 正典 URL のいずれかである。**bare な repo 相対パスは残さない。**
> **`.md` 以外と `templates/starter/**` は射程外**（読者が開発者、または利用者所有ファイルであるため）。
>
> **K4 の拡張**: 配布集合は**エントリポイントからの到達閉包**として導出する。到達関係は
> **import 閉包に加えて実行時データ依存を含む**。配布されるコンポーネントが実行時に読むデータ、
> 配布される規範・skill が名指しするスクリプト・検証手段は、配布されるか、
> **利用者環境で実行可能な代替が示されていなければならない。**

---

## Step 4': gabriel probe（2 巡目）

| 項目 | 値 |
|:--|:--|
| verdict | **refuted** |
| severity | **warning** |
| affected_atoms | C0' / C2' / C3' / C4' |
| recommended_action | **proceed** |
| confidence | 0.75 |

分岐は **AC-W-C-6**（`refuted & warning` → **gabriel 指摘を併記 + 警告ラベル / 最終判断はユーザー**）。
計器: `.claude/gabriel-metrics.log` に 1 行追記済（**分岐前に記録**）。

> **[WARNING by gabriel]**: C2' の「閉包の導出へ置き換える」向きは堅い。ただし
> **C3'#5「射程内の残余はゼロ」は 1 巡目とは別の実例でもう一度偽**であり、
> `incident-patterns.yaml`「配る」は**配布経路が存在しない**ため実行不能、
> `analyzers` の plugin hooks 配下への配置は **T3 の再帰比較を起動して 30 件超の違反**を出す。

### L1 による独立検証（**gabriel が「未検証」と明示した中心主張**）

gabriel は 1-b を「分類ロジックの静的追跡による導出であり、実行出力での確認はしていない」と自ら注記した。
**L1 が census の実出力で確認した ——**

```
[NG-other] .claude/Rules/security-commands.md
     plugins/lam-harness/hooks/_hook_utils.py:65 / :67
     plugins/lam-harness/templates/managed/rules/permission-levels.md:87   ← 配布 .md / 射程内
[NG-other] docs/Specs
     plugins/lam-harness/templates/managed/rules/permission-levels.md:87   ← 同上
```

**両件とも「残り（kept）」に実在する。gabriel の 1-b は真である。**

---

## Step 5: AoT Synthesis（**2 巡の合議 + HGA #35 + gabriel 2 回を経た最終結論**）

### 統合結論

**Action 4c の本体は「パス参照の綴りを直すこと」ではなかった。**

実測は 3 段階で前提を覆した ——
**(1)** 4b が分離根拠とした「情報の欠落」は存在しなかった（行番号参照 0 件）。
**(2)** 192 箇所は**少なくとも 4 種の別問題**であり、最大の層（T1 managed）には
**上流の解決機構が原理的に届かない**。
**(3)** そして計器が見ていなかった場所に、**綴りではなく機能が壊れている箇所**があった ——
配布 skill が非配布の実体を呼ぶ **13 箇所**と、配布 hook が非配布データを読んで
**fail-open する security 機構**（ADR-0008 の動的 deny が全利用者環境で沈黙）。

**したがって 4c の中心は配布集合であり、参照の変換はその後に来る。**

そして配布集合の欠陥の**原因は表の中身ではなく、閉包を計算したエントリポイントが hook だけだったこと**である
（`_MIRROR_AREAS` の注記「analyzers は hook の import 閉包に含まれない」は**正しく計算されていた**）。
**直すのは集合ではなく閉包の定義である。**

### 最終決定（gabriel 2 巡目の 8 指摘を反映した確定形）

#### D1. 規則 R-P（**確定**）

```
R-P(P, src) =
  exists_user(P)                                  → P（そのまま）
  ¬exists_user(P) ∧ src ∈ T3 ∧ exists_dist(P)     → ${CLAUDE_PLUGIN_ROOT}/<plugin 相対>
  otherwise                                       → <base URL>/<P>
```

- **適用域は配布物の `.md` のみ**。`.py` / `.sh` / `.json` / `.yaml` は射程外（**読者は開発者** / 拡張子は構文的）
- **`templates/starter/**` は第 3 層として射程外**（利用者所有ファイル）
- `exists_dist` は**ファイル単位**。`exists_dev` / `exists_dist` は **`rglob` 由来の集合**で判定する（`Path.is_file()` を使わない）
- **冪等性**: トークン単位で `http(s)://` 配下を除外（スパン単位ガードでは不足 / 実測）
- **合成順**: 順方向 **R-P → R-A → R-S**（既存 `to_distributed_text` は R-A → R-S で固定済なので R-P を先頭に挿す）。
  **逆写像は R-P⁻¹ を最後に適用する。** 3 者のパターンは互いに素で可換だが、**テストで固定する**
- **名前参照への変換はしない**（名前は起動の錨、パスは読む錨）

#### D2. 射程内の残余の扱い（**gabriel 指摘 1 の解決 / C3'#5 を再訂正**）

**射程内に「意図的に解決しない参照」が実在する** —— `permission-levels.md:87` の
`.claude/Rules/security-commands.md` と `docs/Specs`（PM ゲートの大小文字非区別を説明する**証拠テキスト**）。

**これを閉じる手段は例外表ではなく<ins>本文の修正</ins>である。**

> **規則: 射程内に残余が出たら、規則に例外を足すのではなく本文を直す。**

**4b の先例と同型である** —— codemod の diff レビューでブレース展開のパス列挙が壊れたとき、
例外表に載せず**文章を直した**。HGA #35 も「規則か文章を直す、表に載せない」と述べている。

したがって **C3'#5 の正しい言明は「射程内の残余はゼロに<ins>できる</ins>。手段は本文の修正である」**。
「ゼロである」という無条件の主張は**撤回する**（1 巡目・2 巡目で 2 度偽だった）。

#### D3. 除外理由の単一化（**gabriel 指摘 2**）

`py-fixture` 9 件は**全件が `.py` 内のみ**（L1 実測）。
**「`.py` は R-P の射程外（読者は開発者）」という単一の真の理由で 9 件すべてを覆える。**
1 巡目・2 巡目案の「合成例」という第 2 カテゴリは**降ろす**（census の報告メタデータに留め、ゲート判定の入力にしない）。

> なお 1 巡目の L1 検証表が「合成例 3 件」と書いたのは誤りだった ——
> `.claude/hooks-local` は**実在するディレクトリ**であり、合成例ではない。

#### D4. 配布集合＝閉包の導出（**gabriel 指摘 3 で第 3 項を構文化**）

```
配布集合 = 閉包( エントリポイント )

エントリポイント = 配布 hooks ∪ 配布 .md（skills / agents / managed 規範）の
                 ***フェンス内コマンド***が名指しする実体
到達関係       = import 閉包 ∪ 実行時データ依存
```

**2 巡目案の第 3 項「配布規範が名指しする検証手段」を削除した。** 文意判定を要したためである
（gabriel 2-a）。代わりに**構文で切る** ——

| 形 | 扱い |
|:--|:--|
| **フェンス内コマンド**（読者が**実行する**） | **閉包に入れる**（配るか、手順を書き換える） |
| **コードスパン内の散文参照**（読者が**読む**） | **R-P で処理**（URL 化） |

これで gabriel が挙げた 8 件の散文引用（`phase-rules.md:39` の `test_planning_config_deny.py` 等）は
**閉包ではなく R-P の対象**になり、provenance として URL で保たれる。**エントリポイントに `agents/**` を含める。**

#### D5. 配布集合の具体（**PM 級 / ユーザー判断を要する**）

| 対象 | L1 の提案 | gabriel が暴いた制約 |
|:--|:--|:--|
| `scale_detector.py`（`/lam-harness:full-review` Stage 1） | **手順書き換えを既定**（実体が無ければ scale 検出を skip して継続）。配る場合は 11 モジュールの閉包 | `plugins/…/hooks/analyzers/` へ置くと **T3 の再帰比較が起動し 30 件超が赤**。`templates/managed/scripts/` へ置くと `_MANAGED_AREAS["scripts"]=.claude/scripts` と食い違い **T1 が赤**。**配るには構造の移動が要る** |
| `build_dashboard.py`（`/lam-harness:quick-save`） | **配る**（`dashboard/` 6 モジュールごと） | 同上の T1 制約。`.claude/scripts/dashboard/` は既に `.claude/scripts` 配下なので**整合する** |
| `.claude/tests/**`（rule-001 検証 / 規約検証） | **配らない**。手順側を「LAM 開発時のみ」と明示、または利用者環境で実行可能な検証に置換 | — |
| **`incident-patterns.yaml`** | **配る（security 機構が全利用者環境で沈黙している）**。ただし**経路の新設が要る** | hook は `get_project_root()/docs/artifacts/` を読む＝**利用者のプロジェクト**を指す。`_MANAGED_AREAS` にも starter にも `docs/artifacts` 宛の経路が無い。**hook のパス解決を `${CLAUDE_PLUGIN_ROOT}` 相対へ変える**のが既存構造定数を動かさない。加えて `source_md` が**非配布の LAM retro を指し、マッチ時に利用者へ提示される** |
| `hga-summoning.md` / `rule-001` / `rule-002` | 配らない（LAM 固有）。参照は URL 化 | — |
| **`subprocess-encoding-convention.md`** | **要ユーザー判断**（L1 の読み: 開発規約であり配布対象外 / 配らなければ 18 箇所が消える） | — |

#### D6. ゲート（**確定**）

| # | 内容 |
|:-:|:--|
| 1 | T2 を `exists_user` ベースへ差し替え、**exit 1** |
| 2 | **到達性検査を足す** —— 分岐 2 は T4 同型に plugin 内実体を照合、URL は path 部が `exists_dev`。**ゲートがトートロジーでなくなり、`master` 固定 URL の腐敗検出も同時に得る** |
| 3 | **射程を docstring と検査メッセージに明記**（`.md` のみ / starter 除く / **素の散文は下界**） |
| 4 | **発火点を正しく書く** —— `verify()` は `/release` と**全 pytest 実行の両方**に載る（`test_real_repo_has_no_violations`）。**4c-1 にも同じ危険がある**（配布集合を動かすと T1/T3 が即赤） |
| 5 | **第三の状態は持たない**。根拠は D2（残余は本文修正で閉じる） |
| 6 | 段階を作らない（同一コミット） |

#### D7. 分割・着手順（**確定**）

| Action | 内容 | 等級 |
|:--|:--|:--|
| **4c-0** | census の 5 点是正（glob / rglob 集合判定 / 2 環境行列 / フェンス内コマンド別欄 / `py-fixture` を単一の真の理由へ） | SE |
| **4c-1** | **閉包の導出器**を作り、その実出力をユーザーに諮って配布集合を凍結。実害 13 の解消（配る or 手順書き換え）。`incident-patterns.yaml` の経路と `source_md` の扱い | **PM** |
| **追補 4** | ADR-0010 の不変条件にパス参照を、K4 に**実行時データ依存**を加える | **PM** |
| **4c-2** | R-P を生成器（T1 順 / T3 逆）へ、T3 正本 codemod、T2 差し替え、**diff 全数レビュー**、往復恒等の両方向検証、**D2 の本文修正 2 件** | SE |

**着手順: 4c-0 → 4c-1 →（追補 4）→ 4c-2。**

**書込集合の宣言**:

| Action | 書込集合 |
|:--|:--|
| **4c-0** | `.claude/scripts/census_dangling.py` / `.claude/tests/scripts/test_census_dangling.py` |
| **4c-1** | 配布集合の決定に依存（`plugins/lam-harness/hooks/**` = パス解決改修 / `templates/managed/scripts/**` / 手順書き換え対象の配布 `.md`）＋ 導出器 1 本＋テスト |
| **4c-2** | ① `plugins/lam-harness/{skills,agents}/**/*.md` ② `templates/managed/**`（T1 再生成）③ **`.claude/{skills,agents}/**`（T3 派生の再生成）** ④ `.claude/scripts/{census_dangling,verify_plugin_containment,derive_managed_templates,derive_project_copies,namespace_source_refs}.py` ⑤ `.claude/tests/scripts/**` ⑥ **hook 副作用**: `.claude/logs/permission.log` ＋ **`.claude/test-results.xml` / `.claude/tdd-patterns.log`**（pytest 実行で PostToolUse hook が書く / `security-commands.md` §計器への書き込みを伴う検証 が「復元不能」と記録した対象） |

#### D8. 追補 4 の文言（**PM 級 / 要承認**）

> **不変条件（追補 3 の拡張）**: 配布される側の **Markdown** に残ってよいパス参照は、
> (a) 利用者環境で解決するもの、(b) `${CLAUDE_PLUGIN_ROOT}` を用いるもの（**プレースホルダが
> 展開される層に限る**）、(c) 正典 URL のいずれかである。**bare な repo 相対パスは残さない。**
> **`.md` 以外と `templates/starter/**` は射程外**（読者が開発者、または利用者所有ファイルであるため）。
> **射程内に解決しない参照が現れた場合、規則に例外を足さず本文を直す。**
>
> **K4 の拡張**: 配布集合は**エントリポイントからの到達閉包**として導出する。
> エントリポイントは配布 hooks と、**配布 Markdown のフェンス内コマンドが名指しする実体**である。
> 到達関係は **import 閉包に加えて実行時データ依存を含む**。
> 配布されるコンポーネントが実行時に読むデータは、配布されるか、
> **その不在時の挙動が仕様として明示されていなければならない**（fail-open を黙認しない）。

### gabriel 指摘の反映状況（**AC-W-C-6 に基づく併記**）

| # | gabriel 2 巡目の指摘 | 反映 |
|:-:|:--|:--|
| 1 | C3'#5 が再び偽（`permission-levels.md:87` の 2 件） | **D2 で解決**（本文修正 / 例外表を作らない） |
| 2 | 「合成例」を除外理由から降ろせ | **D3 で採用** |
| 3 | エントリポイントに `agents/**`、第 3 項を構文化 | **D4 で採用**（第 3 項を**削除**し、フェンス内 / コードスパンで構文的に二分） |
| 4 | 閉包の実出力を 4c-1 の入口で測れ | **D7 で採用**（4c-1 の成果物を「導出器 + 実出力」に） |
| 5 | `incident-patterns.yaml` の配布経路が無い | **D5 で採用**（hook のパス解決改修 ＋ `source_md` の扱いを PM 判断へ） |
| 6 | `analyzers` の配置が T3 を壊す | **D5 で採用**（**手順書き換えを既定**へ変更） |
| 7 | 4c-1 の書込集合が未宣言 / 計器 2 本が抜け | **D7 で採用** |
| 8 | 逆写像の適用順を明記 | **D1 で採用** |

### 未解決として残すもの（**信じて進まない**）

- **`${CLAUDE_PLUGIN_ROOT}` が展開されない文脈での挙動は未実測**。D1 は T3（展開される層）に限定したため
  **本設計は影響を受けない**が、上流の展開範囲表が変われば D1 の分岐 2 が動く
- **URL の pin が不可能**（plugin `0.1.0` ≠ tag `v5.1.0`）。`master` を採る。
  腐敗検出は D6 #2 の到達性検査が兼ねる。**release 手順に version と tag の整合を足す**のは別 Action
- **`subprocess-encoding-convention.md` の配布可否**（PM / 18 箇所が 1 決定で消える）
- census の走査は**下界**（素の散文を拾わない）

---

# 決定記録（2026-09-07 / **ユーザー承認**）

L1 の推奨 4 件がすべて承認された。**D5 の「L1 の提案」列は以下で確定する。**

| # | 決定 | 帰結 |
|:-:|:--|:--|
| **A** | **`subprocess-encoding-convention.md` の配布をやめる** | 最大の参照元 **18 箇所が 1 決定で消える**。`templates/managed/rules/` から除去（T1 の派生集合が 14 → 13）。**L1 の読み「これは製品規範ではなく LAM 開発規約」をユーザーが追認した**。`.claude/rules/` の正本は残る（LAM 自身は使い続ける） |
| **B** | ~~**実害 13 は手順書き換えを既定**（`scale_detector.py` / `build_dashboard.py` とも**配らない**）~~ **→ 2026-09-08 に supersede された**（`docs/artifacts/2026-09-08-magi-analyzers-distribution-route.md` §決定記録）。**前提だった「実害 13 箇所」が過小だった** —— 閉包導出器の実測は gap 40 件で、実体は `full-review` Stage 1-3 と `ship` の gitleaks が **analyzers 6 モジュールへの依存 11 箇所**で機能しないことだった。以下は当時の記録として保存する | 配布 skill を「実体が無ければそのステップを skip して継続」へ書き換える。**配布集合を膨らませず、T1／T3 の構造制約にも触れない**（`analyzers` の plugin hooks 配下への配置 = T3 が 30 件超赤 / `templates/managed/scripts/` 配置 = T1 が赤、をどちらも回避）。利用者は scale 検出とダッシュボードを失うが、**skill は落ちなくなる** |
| **C** | **`incident-patterns.yaml` は hook のパス解決を改修して配る** | `pre-tool-use.py` に `${CLAUDE_PLUGIN_ROOT}` 相対のフォールバックを足す（プロジェクト側にあればそちらを優先）。**既存の構造定数を動かさない**（HGA #35 の歯止めに触れない）。併せて `source_md` の非配布 LAM retro 参照（`retro-W6-B5-2026-06-25.md` / `retro-B4-W1-W15-2026-06-20.md`）を URL 化または空にする —— **マッチ時に利用者へ提示される**ため |
| **D** | **ADR-0010 追補 4 を承認** | D8 の文言で条文化する。**4c-2 の前に入れる**（4b が追補 3 で通った道と同じ / 実装と条文のドリフトを自分で作らない） |

## 決定 B の副次的帰結（**記録しておく**）

「配らない」を選んだため、**利用者環境で `/lam-harness:quick-save` の rule-001 検証は実行できない**
（`.claude/tests/dashboard/test_session_state_parser.py` も非配布）。
skill 側は「**LAM 開発時のみ**」と明示するか、利用者環境で実行可能な検証に置き換える。
**規律そのものは消さない**（rule-001 は観測 6 回の恒久解）。

## 決定 A の副次的帰結

`subprocess-encoding-convention.md` を配らないことで、**それが名指ししていた
`.claude/tests/rules/test_subprocess_encoding_convention.py` への参照（フェンス内コマンド 1 件）も
同時に消える** —— 実害 13 のうち 1 件が A の決定で解消する。
残る実害は B で手順書き換え、C で配布により解消される。

## 着手順（確定）

```
4c-0（計器の 5 点是正 / SE）
  → 4c-1（決定 A・B・C の実施 + 閉包導出器 / PM 承認済）
  → ADR-0010 追補 4（条文 / PM 承認済）
  → 4c-2（R-P の実装 + codemod + T2 差し替え / SE）
```

**追補 4 は 4c-1 と独立に先行できる**（条文は配布集合の具体値に依存しない）。
