# MAGI: Action 4 —— 「実行参照」の参照モデル設計

**日付**: 2026-09-06（セッション 34）
**モード**: **AoT 適用**（判断ポイント 4 / 影響レイヤー = 正本 skills・agents / 生成器 / 検査 / ADR-0010 / 利用者環境 = 5 / 選択肢 3+）
**議題**: Action 4「正本 97 箇所の namespaced 化」の着手前に、**何を「実行参照」と定義するか**と、**「残っていない」をどう証明するか**を決める。
**ユーザー指示**（2026-09-06）: 「HGA・MAGI の利用を躊躇わない / `/full-review` の利用も考慮 / 自律・並列も考慮 / **課題の抽象度を上げ、類似問題と解決をネットで探す** / **まず適切な抽象度の設計を文書に残し**、それから実行」

---

## Step -1: 実測（分解の前に置く / 本 MAGI で最も重い発見）

`plugins/lam-harness/` 配下の全テキストファイルに対し、コンポーネント名 27 個（agents 12 / skills 15）の
出現を、**領域 × 出現位置**で数えた（スクリプトは scratchpad / 再現可能）。

### 領域別（総ヒット 410）

| 領域 | 位置づけ | ヒット | 実行参照の実数 |
|:--|:--|--:|:--|
| **T3-正本: skills** | Action 4 の対象 | **172** | ごく少数（下表） |
| **T3-正本: agents** | Action 4 の対象 | **62** | ごく少数（うち 12 は自分の `name:` 宣言） |
| T3-正本: hooks | Action 4 の対象 | 25 | **0**（`autonomous-state.json` 等のファイル名との同名衝突） |
| T1-派生: scripts | **正本は `.claude/scripts/`** | 86 | **0**（`magi_dispatch.py` の出力テンプレート文字列と docstring） |
| T1-派生: rules / docs-internal | **正本は `.claude/rules/` `docs/internal/`** | 60 | **0**（散文） |
| 他 | — | 5 | 0 |

**すでに namespaced な形は `skills/init/SKILL.md` の 4 箇所のみ**（`lam-harness:init`）。正本の残りは全て bare。

### 決定的な発見: **マークアップは実行参照と相関しない**

「コードスパン／フェンス内にあるものが実行参照」という素朴な規則は、実測に**反例が大量にある**。

| 実例 | 位置 | 実行参照か |
|:--|:--|:--|
| `agents/gabriel.md:2` `name: gabriel` | frontmatter | **否。宣言である**。ns 化すると `lam-harness:lam-harness:gabriel` になり**壊れる** |
| `skills/magi/SKILL.md:234` `### gabriel probe` | フェンス内 | 否。**出力テンプレートの見出し** |
| `skills/goal-driven/SKILL.md:115` `` `goal-driven-l3-executor.md` `` | コードスパン | 否。**ファイル名の言及** |
| `agents/quality-auditor.md:9`「1 観点）には code-reviewer を使うこと。」 | frontmatter の散文 | **是**。マークが無いのに実行指示 |
| `skills/magi/SKILL.md:120` `subagent_type=gabriel` | コードスパン | **是** |

すなわち **「97 箇所」は変換対象の母数ではない**。母数は 1 桁台であり、
**97 という数は「名前が出現した回数」であって「解決される回数」ではなかった**。

---

## Step -0.5: 外部知見（ネット調査 / 独立 2 subagent 並列）

抽象度を上げると本課題は 2 つの既知問題の合流点にある。両方について prior art を採った。

### (α) 修飾なし識別子 → 名前空間修飾への一括移行

| 事例 | 同型性 |
|:--|:--|
| **PEP 328** 絶対 import 移行 | `from __future__ import absolute_import` による**ファイル単位 opt-in → 警告 → 既定化**の 3 段 |
| **Rust 2018 edition** / `cargo fix --edition` | per-crate オプトイン境界。**直せなかったものは警告として残す**（沈黙 = 完了ではない） |
| **Rails classic → Zeitwerk** | 専用の全数チェックタスク `zeitwerk:check` が規約違反を 1 件ずつ列挙し、成功時に明示的に「全部良し」と言わせる |
| **containers/image の短縮イメージ名** | `short-name-mode` = `disabled / permissive / enforcing` の**厳格度 3 段**。移行期専用の中間値を持つ |
| **Google の Large-Scale Changes (Rosie)** | shard 分割 / 自動生成コミットと手動コミットの分離 / **完了後の再混入防止 gate を必ず一緒に入れる** |
| **Stripe の codemod 実務** | regex で当て、**パーサ・型チェッカを検算器として使う**。「型チェッカに変換対象を全数列挙させる」 |

出典: https://peps.python.org/pep-0328/ ・ https://doc.rust-lang.org/stable/edition-guide/editions/advanced-migrations.html ・
https://edgeguides.rubyonrails.org/classic_to_zeitwerk_howto.html ・ https://github.com/containers/image/blob/main/docs/containers-registries.conf.5.md ・
https://abseil.io/resources/swe-book/html/ch22.html ・ https://blog.jez.io/codemods-tips/

### (β) 散文中の語が「解決される識別子」か「ただの語」かの判別

| 事例 | 方式 | 同型性 |
|:--|:--|:--|
| **Rustdoc intra-doc links (RFC 1946)** | **明示構文** | 散文の `Iterator` はただの語、`[Iterator]` だけが解決対象。**角括弧が唯一の signal** |
| **Sphinx の role + `nitpicky`** | **明示構文** | `:py:func:` で「参照である」だけでなく「どう解決するか」まで宣言。`nitpick_ignore` は**例外を名指しで表に載せる** |
| **Doxygen AUTOLINK** | **推論** | 大文字を含む語＝クラス等の表層ヒューリスティック。**誤爆用の打ち消し記法 `%` が必須の対** |
| **Wiki の CamelCase 自動リンク** | 推論 → **廃止** | 「偶発マッチが多すぎる」「リンク意図のない語が赤リンクで埋まり文章が読めない」→ 明示 `[[ ]]` へ移行 |
| **研究（APIReal / WikiSER）** | 推論（機械学習） | 最良でも **F1 70〜80% 帯**。汎用ツールの再現率は 16〜39% |

出典: https://rust-lang.github.io/rfcs/1946-intra-rustdoc-links.html ・ https://www.sphinx-doc.org/en/master/usage/configuration.html ・
https://www.doxygen.nl/manual/autolink.html ・ https://meatballwiki.org/wiki/CamelCase ・ https://arxiv.org/abs/2308.10564

**外部知見の一致点**: 実運用に耐えたシステムは**例外なく明示構文**を選んでいる。推論型を採った系
（Doxygen / CamelCase wiki）は打ち消し記法を必要とし、あるいは廃止された。
**推論の実測精度 70〜80% を我々の母数に当てれば、20〜30% が誤変換される。**

---

## Step 0: AoT Decomposition

| Atom | 判断内容 | 読む状態 | 書く状態 |
|:--|:--|:--|:--|
| **A1** | **「実行参照」をどう定義するか** | Step -1 の実測 / E2E 実測（bare は解決しない・`test-runner` は組み込みに衝突）/ ADR-0010 I-4 / Step -0.5 (β) | 本アンカーの A1 結論（定義） |
| **A2** | **「bare 実行参照が残っていない」をどう証明するか** | A1 の定義 / 既存検査群（`verify_plugin_containment` / `derive_project_copies`）/ Step -0.5 の verification パターン | 本アンカーの A2 結論（検査の形） |
| **A3** | **移行の順序と段階** | A1・A2 の結論 / 危険度の非対称（`not found` vs 黙って別物）/ Step -0.5 (α) の二相移行 | 本アンカーの A3 結論（着手順） |
| **A4** | **対象外の境界確定** | Step -1 の領域別実測 / T1 と T3 の向き / `name:` の意味 | 本アンカーの A4 結論（射程） |

**A1 → A2 → A3 は逐次**（A2 は A1 の書く状態を、A3 は A1・A2 の書く状態を読む）。
**A4 はどの Atom の書く状態も読まない**ため並列可。書込集合は本アンカーのみで交わらない。

---

## Atom A1: 「実行参照」の定義

**[MELCHIOR]**: 定義は単純だ ——「ハーネスが解決する位置」。それは有限で列挙可能である。
`Agent` ツールの `subagent_type`、agent frontmatter の `tools: Agent(...)`、skill の起動名。
これを列挙して ns 化すれば終わる。97 という数字は幻で、実数は 1 桁だと実測が示した。速やかに片付けるべきだ。

**[BALTHASAR]**: その列挙は**二種類の異質なものを同じ袋に入れている**。分けねば必ず破綻する。

- **(H) 機構がパースする位置** —— agent frontmatter の `tools: Agent(...)`、`hooks.json`、`plugin.json`、
  skill frontmatter の `allowed-tools`。**Claude Code 自身が構文として読む**。有限・完全列挙可能・
  YAML/JSON パーサで機械判定できる。ここに推測は要らない。
- **(M) モデルに読ませる指示** —— 「`subagent_type=gabriel` を起動する」。
  **ハーネスはこの文字列をパースしない**。読むのは LLM であり、LLM がそれを見て tool call を組み立てる。
  つまりこれは**自然言語の指示**であって、構文上の位置ではない。

**97 箇所の呪いの正体は、M を H と同じ道具で扱おうとしたことである。** M は Doxygen AUTOLINK と
同じ土俵にあり、prior art の実測が示すとおり**推論では 20〜30% 誤る**。

さらに **`name:` は参照ですらない。宣言である**。ns 化すれば `lam-harness:lam-harness:gabriel` になる。
「全部 ns 化」案はこの 1 点で即死する —— これは実測で確認済みの**反例**であって、意見ではない。

**[CASPAR]**: 結論 —— **実行参照を 2 クラスに分割して定義する。**

> **定義（本設計の一次定義）**
>
> **クラス H（machine-resolved）**: ハーネスが構文として読む位置に現れる名前。
> 具体的には agent frontmatter の `tools:` 内 `Agent(<name>)`、`hooks.json` / `plugin.json` 内の
> コンポーネント名、skill frontmatter の `allowed-tools` 内 `Agent(<name>)`。
> **完全列挙可能であり、パーサで判定する。推測しない。**
>
> **クラス M（model-directed）**: モデルに「この名前で起動せよ」と読ませる指示文。
> **著者が明示的にマークしたものだけが M である。** マークされていない同じ字面は、
> **定義により散文であり、検査対象ではない**（RFC 1946 の設計を写す）。
>
> **クラス D（declaration / 対象外）**: `name:` frontmatter。**ns 化を禁止する**。

**この定義により「97 箇所」という母数が消える。** 母数は `H ∪ M` であり、H は機械が数え、
M は著者が宣言する。**数えられない集合を数えようとするのをやめる**のが本 Atom の結論である。

**採用しなかった選択肢とその理由**:

- **マークアップ（コードスパン／フェンス）を実行参照の必要条件とする** → Step -1 に反例が大量。
  既存コーパスはその規律で書かれておらず、**遡って構文を意図として読むと誤爆する**
  （Doxygen AUTOLINK / CamelCase wiki と同型の失敗）。
- **全出現を機械的に ns 化** → `name: gabriel` と出力テンプレートで壊れる。実測済みの反例がある。
- **分類器・LLM で推測させる** → prior art の実測 F1 70〜80%。**推測の誤りは緑のまま残る**。
- **97 箇所を「§roster で解決せよ」の間接記述に畳む** → 2026-09-05 の MAGI で棄却済（散文の間接参照を
  解決する機構が無い）。**本 Atom はこれを再論しない**（争点 E 規律）。

---

## Atom A2: 「残っていない」をどう証明するか

**[MELCHIOR]**: A1 の定義があれば検査は素直だ。H はパーサで全数判定、M はマークの有無で判定。
どちらも exit 1 にすれば「残っていない」が証明される。既存の `verify_plugin_containment.py` に
検査を 1 本足すだけで済む。

**[BALTHASAR]**: **マーク方式には致命的な穴がある。「マークし忘れた実行指示」は検査に映らない。**
定義上マークされていないものは散文なのだから、**検査は緑のまま壊れる**。

これは `rule-001` 観測 #6 と**同型**である —— 検査は緑、しかし事実と食い違う。
そして本プロジェクトは **「緑なのに事実と食い違う形を見たら即停止」という異常判定の線を引いている**。
その線に触れる設計を、線を引いた本人が提案してはならない。

補いは 3 つ考えられる。

- **(a) 陰性対照** —— 既知の実行指示を bare に戻すと赤くなること。**必要だが十分ではない**
  （既知のものしか守れない）。
- **(b) 外部の不動点 = plugin 有効サンドボックスでの E2E** —— bare は `not found` になる。
  Stripe の「型チェッカに全数列挙させる」に相当する。**ただし全経路は踏めない**。
- **(c) 危険度の非対称を使う** —— bare の失敗は**質が 2 種類ある**:
  - `not found` で**止まる**（うるさいが安全）
  - **黙って別物が動く** —— 実測で確認された組み込み agent `test-runner` との衝突のみ

**12 名のうち `test-runner` 1 名だけが後者である。** ここは**マークの有無によらず無条件に検査すべき**だ。
沈黙する failure に対してだけは、推論の誤爆コストを払う価値がある。

**[CASPAR]**: 結論 —— **検査を 3 層に分ける。層ごとに重大度を変える**（Docusaurus が
`onBrokenLinks: throw` と `onBrokenAnchors: warn` を分けているのと同じ思想）。

| 層 | 対象 | 判定 | 重大度 |
|:--|:--|:--|:--|
| **L-H** | クラス H（frontmatter / json の構文位置） | **パーサで全数**。ns 無しは違反 | **error** |
| **L-M** | クラス M（明示マーク済み） | マーク内の名前が ns 付きか | **error** |
| **L-X** | **組み込みと衝突する名前**（現時点 `test-runner` 1 名） | マーク無関係に **bare 出現を全数報告** | **warn**（例外は名指し表） |

加えて **陰性対照テストを必須とする**（LAM の誕生ゲート §1.3 / 機構が沈黙したときに気づくため）。

**L-X の衝突名リストは「維持リスト」になる** —— これは LAM の趣味（維持リストを持たない / 機構 #7・#11）に
反する。だが**基質から導出できない**（上流の組み込み agent 一覧を取得する経路が無い）。
よって **表として持ち、各行に出典（E2E 実測ログの参照）を併記する**。
**表が古びることを検知できない点は、本設計の既知の限界として明記する**（将来 E2E で
`Available agents:` 一覧を採取して突合する検査を入れる余地がある / Action 7 の隣）。

**採用しなかった選択肢とその理由**:

- **L-X を error にする** → 現時点で正しい散文の言及まで赤くなり、「常時鳴る計器は殺される」型に直行する
  （`-c` を一律 PM にしなかったのと同じ判断）。
- **L-X を持たず L-H + L-M だけにする** → **黙って別物が動く**唯一の経路を無防備にする。
  重大度が非対称なのだから、検査も非対称にすべきである。
- **E2E を検査の本体にする** → 全経路を踏めず、かつ実行が高価。**補助**として位置づける。

---

## Atom A3: 移行の順序と段階

**[MELCHIOR]**: H は 1 桁台なので即座に全部変換し、検査を error で入れて終わり。
段階を刻むほうがコストが高い。

**[BALTHASAR]**: **危険度が均一でないのに一律に扱うのは、優先順位の放棄である。**
`test-runner` 以外は失敗が可視（`not found`）で、**気づけるものは急がなくてよい**。
一方 `test-runner` は沈黙する。**今すぐ確認すべきはこの 1 名だけ**であり、
残りは gate を置いて漸進すればよい。

そして prior art の一致点は**二相移行**（PEP 328 / containers/image の `short-name-mode` /
Sphinx の `nitpicky` 既定 False）と、**自動生成コミットと手動コミットの分離**（Stripe）である。
**混ぜたコミットは捨てて作り直せない。**

**[CASPAR]**: 結論 —— **3 段。各段は独立にコミットする。**

| 段 | 内容 | 等級 | 検査の厳格度 |
|:-:|:--|:--|:--|
| **段 1** | **クラス H の変換**（機械的・1 桁台）＋ **L-H 検査を error で新設** ＋ 陰性対照 ＋ **`test-runner` の bare 出現を全数目視確認** | SE | L-H = error / L-X = warn |
| **段 2** | **クラス M のマーク付与**（著者判断 / **ファイル単位の opt-in** = PEP 328 型）。マーク済みファイルのみ L-M を error 適用 | SE | L-M = error（マーク済みファイルのみ） |
| **段 3** | 全対象ファイルがマーク済みになった時点で既定を反転。**再混入防止 gate として常設** | SE | 既定 error |

**コミット分離**（Stripe）: 機械変換のコミットと手編集のコミットを混ぜない。
機械変換側はコミットメッセージに生成コマンドを書き、**いつでも捨てて再生成できる**状態にする。

**`.claude/` 派生側は 1 行も手で触らない** —— `derive_project_copies.py --write` が生成する。

---

## Atom A4: 対象外の境界

**[MELCHIOR]**: 対象は `plugins/lam-harness/{skills,agents}` でよい。実測でそう出ている。

**[BALTHASAR]**: **境界は「対象」より「対象外である根拠」を書かねば意味がない。**
とくに `templates/managed/` は**危険な誤解を招く場所**である —— そこには 146 件のヒットがあり、
かつ **T1 の向きは T3 と逆**（正本が `.claude/` 側）である。もし managed 配下に実行参照が
あったなら、**T1 には順変換（bare → ns）が存在しないため、配布物が壊れたまま検査は緑になる**。

したがって「0 件だった」を**測った事実として記録する**必要がある。**測っていないのと 0 だったのは違う。**

**[CASPAR]**: 結論 —— 射程を以下に確定する。

| 領域 | 射程 | 根拠（**実測**） |
|:--|:--|:--|
| `plugins/lam-harness/skills/**` | **対象** | T3 正本 |
| `plugins/lam-harness/agents/**` | **対象** | T3 正本。ただし `name:` はクラス D で ns 化禁止 |
| `plugins/lam-harness/hooks/**` | **対象だが実行参照 0** | 25 ヒットは `autonomous-state.json` 等のファイル名との同名衝突 |
| `plugins/lam-harness/templates/managed/**` | **対象外** | **T1 の派生**（正本は `.claude/rules` `docs/internal` `.claude/scripts`）。かつ**実行参照 0 を実測**（`magi_dispatch.py` の 86 ヒットは出力テンプレート文字列と docstring） |
| `.claude/{skills,agents,hooks}/**` | **対象外（生成物）** | `derive_project_copies.py` が書く。手で触らない |

**T1 に順変換が要る事態は現時点で発生していない。将来 managed 配下に実行参照が入れば
「配布物が壊れたまま検査が緑」になる** —— この経路を既知の限界として記録する。

---

## Step 4: gabriel probe（1 巡目）

| 項目 | 値 |
|:--|:--|
| verdict | **refuted** |
| severity | **critical** |
| affected_atoms | A1 / A2 / A3 |
| recommended_action | re-magi |
| confidence | 0.60 |

**指摘の要旨**:

1. **A2 の L-X 完全性が未検証** —— 「`test-runner` のみが組み込みと衝突する」の一次証拠は
   実測ログの `Available agents: … ` が **elided** されており、**12 名全員分の突合記録が存在しない**。
2. **最重大 —— クラス M の「著者マーク方式」は HGA #33 裁定 2 と正面衝突する**。
   裁定 2 は「書込集合は列挙ではなく**閉包**であり、**閉包は機構の側にしか存在しないので手書きの宣言は
   必ず落とす**」と結論した。**手作業の宣言に頼る設計を、その手作業の宣言が直前に 3 回連続で破綻した
   直後に提案しながら、裁定に一切言及していない。**
3. **A3 の段 2 → 段 3 に強制発火点が無い** —— LAM が自認する「決めたのに実装しない型」と同型。

計器: `.claude/gabriel-metrics.log` に 1 行追記済（`resolved_action: re_magi`）。

**再 MAGI ではなく HGA へ上げた** —— これは**本プロジェクトで 3 回連続の critical** であり、
セッション 32 で引いた異常判定の線「次に gabriel が critical を返したら局所修正で流さず HGA へ」に該当する。
加えてユーザーが「HGA・MAGI の利用を躊躇うな」と明示指示していた。

---

## Step 4.5: HGA #34 の裁定（記録は `hga-summon-log.md#34` / 確信度 0.75）

### 裁定 1 —— gabriel は正しい。かつ理由は裁定 2 違反だけではない

**A1 は読者モデルを誤っていた。** RFC 1946 の角括弧規約が成立するのは、**読者が人間**で、
語と参照を区別するからである。**本件の読者は LLM** であり、無マーク散文
（`agents/quality-auditor.md:9`「1 観点）には code-reviewer を使うこと。」）からも tool call を組み立てる。
**「マーク無し = 定義により散文」は、地図を書き換えただけで領土（モデルの解決挙動）は変わらない。**

**L1 の対案（機械生成ベースライン ratchet）も裁定 2 を満たさない。** ベースラインの中身は
「bare 出現の全数」であって「bare **実行参照**の全数」ではない。人がエントリを減らす操作は、
**裁定 1 が「導出ではない」とした分類そのもの**を 1 件ずつ手でやることになり、残るのは
**符号を反転させた宣言**（＝人が「散文だ」と承認した例外表）である。誤分類は緑のまま残る。
加えて ratchet が正当なのは残余が「残ってよいもの（lint 負債）」の場合であり、
**本件の残余は欠陥そのもの**である。

> **正しい形 = 分類を消す。** 「実行参照か散文か」を判定するのをやめ、
> **kind（agent か skill か）と構文位置だけで決まる規則**にする。

### 裁定 2 —— 不確実性は消せる。ただし固定リストにするな

組み込み一覧の非公式取得経路が 2 本ある（① 清浄サンドボックスで存在しない `subagent_type` を叩き
`Available agents:` **全文**を貼る ② subagent 自身の system prompt に注入されている一覧を写させる）。
ただし一覧は **CC 版と環境に依存**するため **L-X を固定リストにしてはならない**。
**かつ裁定 1 の形を採れば L-X は独立層として不要になる**（穴そのものを塞ぐので補修が要らない）。

**新発見**: 組み込み `init` **skill が実在**し、LAM の `init` と bare 衝突する
（`test-runner` の skill 側対応物 / HGA 自身の system prompt から観測）。
**L1 が本セッションの自コンテキストで独立に確認した** —— 組み込み skills 一覧に
`init: Initialize a new CLAUDE.md file with codebase documentation` が実在する。

### 裁定 3 —— 強制発火点を設計する前に、発火を待つ段階を無くせ

段 2・3 が存在した理由は「M は著者が 1 件ずつマークする」からであり、分類を消せば
**codemod 1 コミット + 往復恒等 + 検査を error で同時投入**で終わる。**来ない段階は作らないのが最良の強制。**

残余を許す設計になった場合の原則: **カウンタは計器であって強制ではない**（LAM で通知は無視される。
実際に効く強制は「やりたい操作が exit 1 で拒否される」のみ）/ 拒否は **`release`** に置け
（害が実体化する瞬間）/ **`/ship`・`/quick-save` に置くな**（毎コミット鳴る計器は殺される）。

### HGA が指摘した「L1 が見落としていた分岐点」5 件

1. **読者モデルが LLM である**前提が MAGI ログのどこにも書かれていない
2. **skills と agents は解決文法が違う** —— skills には slash があり agents には無い。
   同じ規則を当てると、片方で phase 語彙を壊し、片方で散文指示を取り逃す
3. 利用者環境での**見出し不整合**（唯一の実害候補）
4. **dev 側の shadowing 依存** —— LAM 本体は bare `test-runner` で動いており、
   「project が組み込みに勝つ」上流挙動に依存している
5. frontmatter `Agent(lam-harness:x)` をハーネスが受理するかは**ブリーフ外の仮定**

---

## Step 4.6: HGA 裁定を受けた追加実測（L1 / HGA の最大の不確実要因を潰す）

HGA は確信度を下げる最大要因として「**agents の散文 125 件を目視ではなく集計で見たこと**」を挙げた。
そこで**フェンス内の agent 名ヒット 40 件を、フェンスの言語タグとともに全数目視**した。

### 発見 A: **フェンスの言語タグが、すでに分類を与えている**

| 言語タグ | 中身 | 件数 | 実行参照 |
|:--|:--|--:|:--|
| ` ```markdown ` | **出力テンプレート**（生成される文書の見た目）—— `### gabriel probe` / `**監査者**: quality-auditor` / 監査レポートの表 | **32** | **0** |
| ` ```json ` | **スキーマ**（`"description"` 文字列） | 2 | **0** |
| ` ``` `（タグ無し） | **擬似コード・フロー図** —— `Agent(quality-auditor)` / `[2] Agent(goal-driven-l3-executor) 起動` / `agent="goal-driven-grader"` / 「設計が不適切 → design-architect と協議」 | 6 | **5**（1 件はフロー図） |

> **訂正（gabriel 2 巡目の指摘 / 2026-09-06）**: 初稿はこの表を `36 / 2 / 6` と書き、合計 44 が
> 本文の「40 件」と食い違っていた。**再集計した実数は `32 / 2 / 6 = 40`** である。
> gabriel は本文と表の**算術不一致**を指摘し、それによって「例外は 1 件も無かった」という
> 完全性主張の精度が揺らぐと述べた。指摘は正しく、集計は目視ではなく再実行で確定した。

**40 件全数を目視し、例外は 1 件も無かった。** これは L1 が発明したマークではなく、
**コーパスがすでに持っていた構文**である（Sphinx / rustdoc が「既存の構文に意味を載せる」のと同じ）。

### 発見 B: **agents は T1 チェーンと分裂しないが、skills は 55 箇所で分裂する**

| | T3 正本（`plugins/`）| T1 チェーン正本（`.claude/rules` + `docs/internal`）| 分裂するか |
|:--|--:|--:|:--|
| **agent 名の実行参照** | 少数（下記 §規則 R-A 参照） | **0**（実測 / 60 ヒットはすべて散文と出力テンプレート） | **しない** |
| **skill の slash 形** | **85**（`/full-review` 41 / `/ship` 19 / `/retro` 10 …） | **55**（`/retro` 18 / `/quick-save` 11 / `/ship` 6 …） | **する** |

**T1 チェーンの向きは T3 と逆**（正本が `.claude/` 側）であり、**順変換（prefix 付与）が存在しない**。
`.claude/rules/` は **LAM 自身が plugin disabled で読む正本**なので、そこを `/lam-harness:ship` に
書き換えれば **LAM 自身が壊れる**。よって slash 形を T3 側だけ ns 化すると、
**配布物の中で「`/lam-harness:ship` と書いてある文書」と「`/ship` と書いてある文書」が同居する。**

**これは Action 4 の中で解けない。** 別の設計判断（T1 に順変換を入れるか / rules 側の扱い）を要し、
それは残務 §1 の #5「182 箇所の参照是正」と同じ問題領域である。

---

## Step 5: AoT Synthesis（最終）

### 統合結論

**Action 4 の本体は「97 箇所の変換」ではなく「分類をやめること」だった。**
そして実測は、**Action 4 を 2 つに割るべきこと**を示した ——
**agents は本セッションで閉じられ、skills（slash 形）は閉じられない。**

### 規則（**構文だけで決まる / 1 件ずつの判断を含まない**）

#### 規則 R-A —— agents（12 / 固有名詞）: 正本の**全出現を ns 化**する

除外は**構文的に判定できる 3 位置のみ**。

| 除外 | 内容 | 根拠 |
|:--|:--|:--|
| **(D) 宣言** | frontmatter `name:` の値 | ns 化すると `lam-harness:lam-harness:gabriel` になる。**ハーネスが plugin 名を前置して登録する** |
| **(P) パス・ファイル名文脈** | `agents/<n>.md` / `` `<n>.md` `` | 名前ではなくファイルを指している |
| **(T) 出力テンプレート・スキーマ** | 言語タグが `markdown` / `json` のフェンス内 | 発見 A（40 件全数目視）。かつ ns 化すると **T1 チェーンの `.claude/rules/decision-making.md` §Output Format と `.claude/scripts/magi_dispatch.py` の emit 文字列と 3 者不一致**になる（順変換が存在しないため解消不能） |

除外タグ集合は `{markdown, json}` の 2 個。**既定は ns 化**であり、
**新しいタグのフェンスは自動的に ns 化対象になる**（安全側 = 過剰に付く方に倒れ、diff で見える）。

#### 規則 R-S —— skills（15 / 一般語）: **本セッションでは実施しない**

理由は発見 B。実測で `phase="building"` / `"command": "full-review"` / `"mode": "autonomous"` が存在し
**一律 ns 化は壊す**。かつ slash 形だけを T3 側で ns 化すると T1 チェーンと**配布物の中で分裂する**。
**`Action 4b` として分離し、T1 の向きの扱いと同時に設計する**（残務 §1 の #5 と統合する）。

**例外**: `skills/init/SKILL.md` の既存 4 箇所（`lam-harness:init`）は**そのまま維持**する。
組み込み `init` skill が実在するため、この 4 箇所は**すでに正しい**。

#### 規則 D —— `name:` は宣言であり参照ではない（ns 化禁止 / 据え置き）

### 検算器（**主張ではなく証明**）

**往復恒等**: 変換後の正本に既存の `to_project_text` を当てた結果が、**変換前の正本とバイト一致**すること。

これが成り立てば **`.claude/` 派生は 1 バイトも変わらない** —— すなわち
**LAM 自身の実行実体に対する Zero-Regression が証明される**（テストが通ることの主張ではなく、
生成関数の性質としての証明）。`### gabriel probe` を assert する wave_c テスト 2 件も
dev 側で走るため無影響（HGA 実測）。

### 検査（**codemod と同一の関数を使う**）

規則 R-A が ns 化すべき位置に bare が残っていたら **exit 1**。
**検査と codemod は同じ関数を共有する** —— 別実装にすると両者がドリフトする
（`verify_plugin_containment.to_project_text` を検査と生成が共有しているのと同じ思想）。

#### 除外 (T) の代理性を、検査可能な不変条件に変える（**gabriel 2 巡目の処方**）

gabriel は「**(T) 除外はフェンスのタグを、実際の不変量（T1 チェーンとの逐語重複）の代理指標として
使っている。将来 ` ```markdown ` の中に真の実行指示が混入すれば、代理指標だけでは検出できない**」と
指摘した（そのとき severity は critical へ上がるべき、とも）。これは正しい。

**代理を検査可能な不変条件に変える** —— 除外フェンス（`markdown` / `json`）の内側に
**ハーネス呼び出し構文**（`Agent(` / `subagent_type=` / `agent="` / `subagent_type="`）が
現れたら **exit 1** とする。

これで「除外領域には実行指示が入らない」という前提が**主張ではなく検査**になる。
現在この検査は緑である（実測: 除外フェンス 34 件のいずれにも呼び出し構文は無い / 呼び出し構文 5 件は
すべてタグ無しフェンス側）。**混入した瞬間に赤くなる**ので、gabriel の言う「検出できない」経路が閉じる。

**段階を作らない**（HGA 裁定 3）。codemod と検査を**同一コミット**で入れる。
**再混入防止 gate として常設**する（Google LSC）。

### 射程（A4 から更新）

| 領域 | 射程 | 根拠 |
|:--|:--|:--|
| `plugins/lam-harness/{skills,agents}/**/*.md` の **agent 名** | **本セッションで実施** | R-A |
| `plugins/lam-harness/hooks/**` | **対象外** | **モデルが読む文書ではなく実行されるコード**。コメントの読者は開発者であってハーネスでもモデルでもない（HGA 裁定 1 の読者モデル論が及ばない）。実測: agent 名の出現は過去の合議に言及する散文コメント **1 件**、実行参照 **0**（gabriel 2 巡目が独立に再現確認） |
| **skill の slash 形（両チェーン 140 箇所）** | **Action 4b へ分離** | 発見 B |
| `plugins/lam-harness/templates/managed/**` | **対象外** | T1 派生。実行参照 0 を実測 |
| `.claude/**` | **対象外（生成物）** | `derive_project_copies.py --write` が書く |

### 積み残し（**閉じずに記録する**）

1. **組み込み一覧の採取**（HGA 裁定 2 の経路 ①）—— 設計はもう依存しないが、
   **`test-runner` の shadowing 依存**（HGA の見落とし分岐点 4）を測るために要る。**別起票**
2. **`test-runner` の改名** —— PM 級・別件。**本 Action に混ぜない**（HGA）
3. **frontmatter `Agent(lam-harness:x)` の受理性** —— 未検証の仮定。現状は制限自体が無効なので無害
4. **Action 4b**（skill の slash 形 + T1 の向き）—— 残務 §1 の #5 と統合

### 変えないもの（HGA / #33 裁定 2 から継承）

- **裁定 1 の向き**（正本 = `plugins/` / 派生は prefix 除去）。**生成器に順変換を足さない** ——
  付与は一度きりの codemod であって常設の導出ではない
- **ADR-0010 I-4 の改訂を要しない** —— R-A は I-4 をテキストに文字どおり適用したもの
- **「丁寧に宣言せよ」型の常駐条項を足さない** / **L1 の勤勉さの問題として扱わない**
- **gabriel の閾値・再 MAGI 上限** / **「常時鳴る計器は殺される」の線**

---

## Step 4b: gabriel probe（2 巡目 / 改訂後の Synthesis に対して）

| 項目 | 値 |
|:--|:--|
| verdict | **refuted** |
| severity | **warning** |
| affected_atoms | R-A |
| recommended_action | **proceed** |
| confidence | 0.60 |

分岐は **AC-W-C-6（`refuted & warning` → MAGI 結論に gabriel 指摘を併記 + 警告ラベル）**。
計器: `.claude/gabriel-metrics.log` に 1 行追記済（`resolved_action: annotate_warning`）。

### 併記する gabriel 指摘（**警告ラベル付きで結論に残す**）

1. **【是正済】算術不一致** —— Step 4.6 の表が `36 / 2 / 6 = 44` で本文の「40 件」と食い違っていた。
   **再集計で `32 / 2 / 6 = 40` に訂正**。gabriel の言うとおり、この 1 点で完全性主張の精度が揺らいでいた。
2. **【是正済 / 構造的】除外 (T) は代理指標である** —— フェンスのタグは、実際の不変量
   （T1 チェーンとの逐語重複）の代理にすぎない。` ```markdown ` の中に真の実行指示が混入すれば
   代理指標では検出できず、そのとき severity は critical へ上がるべき。
   → **§検査 に「除外フェンス内に呼び出し構文が現れたら exit 1」を追加して不変条件化した。**
3. **【独立に再現確認された】射程境界** —— gabriel は `plugins/lam-harness/hooks` と
   `templates/managed/` 全域を 12 名の厳密一致で grep し、`Agent()` / `subagent_type=` が
   **0 件**であることを**独立に再現**した。A4 の射程は裏取りされた。
4. **【過大主張ではないと確認】往復恒等** —— 「LAM 自身の `.claude/` 側にのみ scope した証明」であり、
   本文がそう明記していることを gabriel が確認した。
5. **矛盾なし** —— ADR-0010 I-4 / 追補 2 / HGA #33・#34 との矛盾は検出されなかった。

### 残る警告（**閉じない / ラベルとして残す**）

**除外 (T) は経験則から不変条件へ格上げしたが、「`{markdown, json}` という 2 要素の集合」自体は
依然として手で置いた値である。** 新しいタグの出現時は既定で ns 化される（安全側）ため沈黙はしないが、
**このタグ集合が正しいかは、本セッションのコーパスに対してしか検証されていない。**

---

# 実施記録（Action 4a / 2026-09-06）

## 変更したもの

| 分類 | 実体 |
|:--|:--|
| 規則の実装（**codemod と検査が共有**） | `.claude/scripts/verify_plugin_containment.py` —— `to_namespaced_agent_text()` / `agent_names()` / `check_source_namespacing()`（**T5**）/ 除外定数 3 種 |
| codemod | `.claude/scripts/namespace_source_refs.py`（新規 / `--check` `--write` / **往復恒等を書き込み前に検証**し、破れたら何も書かずに落ちる） |
| テスト（新規 19 件 / 陰性対照 3 件を含む） | `.claude/tests/scripts/test_source_namespacing.py` |
| 正本の変換 | `plugins/lam-harness/{skills,agents}` の **22 ファイル**（約 90 箇所） |
| 派生 | **0 バイト**（`derive_project_copies.py --check` = 更新 0 件） |

**`.claude/` 側は 1 行も手で触っていない。** git 差分にも現れない —— これが往復恒等の実証である。

## 検証

| 検査 | 結果 |
|:--|:--|
| pytest（`.claude/tests` + `.claude/hooks/tests`） | **1400 passed / 14 skipped**（着手前 1381 から +19） |
| `verify_plugin_containment.py` | OK（T1・T2・T3・T4・**T5**） |
| `derive_project_copies.py --check` | OK（更新 **0 件** = 派生は不変） |
| `verify_distributable_claims.py` / `verify_reference_resolution.py` / `verify_model_reference.py` | OK |

## HGA が指定した diff レビュー（1 回 / **確信度を下げていた最大要因への対処**）

HGA #34 は「agents の散文を目視ではなく集計で見た」ことを最大の不確実要因に挙げ、
`phase="building"` 型の「別名前空間の値」が agent 名側にも潜んでいれば規則に穴が開くと述べた。
**置換 90 箇所を全数レビューし、該当は 1 件も無かった** —— agent 名 12 個はいずれも固有名詞で、
設定値・語彙と衝突する語を含まない（skills 側と対照的である）。

**ただしレビューで 1 件、設計時に見えていなかった危険が見つかった。**

> **`lam-harness:` はコロンを含む。** `description:` は frontmatter の plain scalar であり、
> コロンの解釈次第で**値が文字列でなくなる**（dict 化する）。ハーネスは frontmatter を
> 構文として読むため、ここが壊れると **agent / skill がそもそも登録されない** ——
> 本 codemod で唯一「静かに全部壊れる」経路である。
>
> 実測: **55 件の frontmatter を YAML として再パースし、破損 0**（`lam-harness:code-reviewer` は
> コロンの直後に空白が無いため plain scalar のまま）。**恒久の対照テストとして固定した**
> （`test_frontmatter_still_parses_after_namespacing` / `pytest.importorskip("yaml")`）。

## 積み残し（**閉じずに残す** / 本文 §積み残し を参照）

1. **Action 4b** —— skill の slash 形（T3 側 85 / T1 チェーン 55）。**T1 の向きの扱いと同時に設計する**
2. **組み込み一覧の採取** —— `test-runner` の shadowing 依存（HGA の見落とし分岐点 4）を測るため
3. **`test-runner` の改名** —— PM 級・別件。本 Action に混ぜない
4. **frontmatter `Agent(lam-harness:x)` の受理性** —— 未検証の仮定（現状は制限自体が無効なので無害）

## 残る警告（gabriel 2 巡目 / **ラベルとして残す**）

除外 (T) は「除外フェンス内にハーネス呼び出し構文が現れたら exit 1」で不変条件化したが、
**`{markdown, json}` というタグ集合自体は手で置いた値**であり、本セッションのコーパスに対してしか
検証されていない。新しいタグは既定で ns 化される（安全側）ため沈黙はしない。
