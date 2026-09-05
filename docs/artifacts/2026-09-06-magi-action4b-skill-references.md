# MAGI: Action 4b —— skill 参照と、T1 に残された複製相

**日付**: 2026-09-06（セッション 34）
**モード**: **AoT 適用**（判断ポイント 4 / 影響レイヤー = T1 複製相・T3 正本・生成器・検査・ADR-0010・利用者環境 = 6 / 選択肢 3+）
**議題**: Action 4a が分離した **skill の slash 形**をどう扱うか。実測はそれが単独では解けず、
**T1 に残っている「手で 2 部維持する複製相」**が本体であることを示した。
**先行**: `2026-09-06-magi-action4-reference-model.md`（Action 4a / MAGI 2 巡 + HGA #34）

---

## Step -1: 実測

### (1) 変換対象の規模

| チェーン | 正本 | R-S（slash 形）で変わる行 | R-A（agent 名）で変わる行 |
|:--|:--|--:|--:|
| **T3** | `plugins/lam-harness/{skills,agents}` | **67**（skills 61 / agents 6） | 0（**4a で完了**） |
| **T1** | `.claude/rules/` ＋ `docs/internal/` | **51** | **36** |

T1 正本に**既存の名前空間つき表記は 0 件**（往復恒等の前提が成立する）。

### (2) **T1 には生成器が無い —— 検査だけがある**

`verify_plugin_containment.check_managed_identity` は `templates/managed/` と `.claude/` の
**バイト恒等**を要求するが、**書く側の機構が存在しない**。つまり T1 は今も
「**同じ内容を 2 人が書き、検査で一致を強制する**」形 —— HGA #33 が T3 について
「解体せよ」と裁定した、まさにその形のまま残っている。

**T1 の向きは T3 と逆**（正本が `.claude/` 側）であり、必要な変換は **prefix の付与**である。

### (3) 配布物の中で、**規約と実体が矛盾している**

| 層 | 表記 | 状態 |
|:--|:--|:--|
| `templates/starter/CLAUDE.md` | 「本ハーネスの skill は plugin から供給されるため、**常に `/lam-harness:` を前置**する」 | **規約を明文化済** |
| `templates/starter/CHEATSHEET.md` | `/lam-harness:ship` / `/lam-harness:magi` … | **規約に準拠** |
| `plugins/**/skills/*.md`（配布 skill 本体） | `/ship` `/full-review` … **67 行** | **規約に違反** |
| `templates/managed/{rules,docs-internal}`（配布規範） | `/retro` `/quick-save` … **51 行** | **規約に違反** |

**同じ配布物の中で、規約を書いた層だけが規約を守っている。**

### (4) `.claude/rules/` ⊋ managed —— 非配布が **5 件**ある

`.claude/rules/` **19 件**（再帰） vs `templates/managed/rules/` **14 件**。差の 5 件は
`hga-summoning.md` / `model-roster.md` / `terminology.md` /
**`auto-generated/rule-001.md`** / **`auto-generated/rule-002.md`**
（`model-roster` と `terminology` は **starter** として別途 1 回だけ敷かれる）。
`docs/internal/` は 10 件で**全件配布**。**向きの反転案に効く事実である**（→ Atom B1）。

> **訂正（gabriel の指摘 3 / 2026-09-06）**: 初稿は「非配布 3 件」と書いた。
> `comm` でディレクトリエントリ `auto-generated` と basename を突き合わせた誤りで、
> **`auto-generated/` 配下の 2 件を数え落としていた**。再帰で数え直して 5 件に訂正した。
> なお Atom B1 本文の「5 件が `.claude/` 正本」は結果的に正しかった（14 + 5 = 19）。

### (5) 対象外の候補（**測った上で外す**）

- `templates/managed/scripts/` の `.py` / `.sh` に slash 形 **7 箇所**（docstring・コメント）
- `templates/starter/**` は T1 検査の対象ですらなく、かつ既に正しい

---

## Step -0.5: 外部知見（独立 2 subagent 並列 / 4a とは別の問い）

### (γ) 一つの原本を、規約の違う 2 つの読者へ配る

| 事例 | 要点 |
|:--|:--|
| **Sphinx / Antora の参照解決** | 著者は**完全修飾を 1 回書き**、短縮形・表示形はツールが文脈から導出する。**「2 つの綴り」を著者が持たない** |
| **cargo-rdme** | 正本 1 つ・派生は生成。`--check` が exit **0=最新 / 3=古い / 4=警告**を返す |
| **Jupytext** | 双方向変換を許すが**優先側を規約で固定**し、非優先側が外部で変更されていたら**黙って上書きせずエラー** |
| **gettext** | 原文が変われば `fuzzy` が自動で付き、**`msgfmt` は fuzzy を出力に載せない**（古い派生物は既定で無効） |
| **Sphinx `only::` の失敗**（#1420） | 有効化されていない分岐は**そもそもビルドされないので検査されない**。`wontfix` |

**最重要の指摘**: Sphinx / Antora / DITA / Doxygen に双方向の問題が無いのは、
**出力が 2 つでも入力が 1 つ**だからである。**両方が正本という解を採っている例は 1 件も無かった。**

正本の選び方として観測できた基準は 2 つ ——
**(a) 情報量が少なく規則的な側**（Rust の doc comment）/ **(b) 人間が日常的に編集する側**（Jupytext）。

出典: https://www.sphinx-doc.org/en/master/usage/domains/python.html ・ https://docs.antora.org/antora/latest/page/xref/ ・
https://lib.rs/crates/cargo-rdme ・ https://jupytext.readthedocs.io/en/latest/paired-notebooks.html ・
https://www.gnu.org/software/gettext/manual/html_node/Fuzzy-Entries.html ・ https://github.com/sphinx-doc/sphinx/issues/1420

### (δ) plugin エコシステムの「短名 → 完全修飾名」移行

| 事例 | 要点 |
|:--|:--|
| **Ansible FQCN 移行** | bare を残し推奨に留め、強制を **ansible-lint** に外出し。`fqcn` は 5 サブルール・**autofix つき** |
| **Ansible の最大の事故** | **「bare は修飾形の単なる短縮」という前提が偽だった** —— bare `copy` は `ansible.legacy.copy` で**ローカル override を拾う**。`ansible.builtin.copy` は拾わない。**autofix が挙動を静かに変えた** |
| **`collections:` キーワード** | 「この文脈では bare でよい」の宣言機構。**role に継承されず**静かに誤解決した。lint は**この機構の使用自体**を叩く（`fqcn[keyword]`） |
| **ansible-lint の立場** | `collections:` を解決に**一切考慮しない**。**文脈依存の bare 許可を認めなかったから機械化できた** |
| **Terraform 0.13** | 移行コマンドを本体に同梱し、`init` の失敗メッセージから案内。**未解決の旧名は特別な名前空間 `registry.terraform.io/-/` に押し込んで可視化**（「まだ移行していない」を型として持つ） |
| **Homebrew** | core と同名の tap formula は**併存できない**。公式指導は「修飾で呼び分けろ」ではなく **「別名を付けろ」** ——**名前空間を足しても、インストール先が 1 つなら曖昧性は解けない** |
| **Ansible のドキュメント** | 自分の文書を**一括で FQCN へ書き換えた**。URL 構造自体を FQCN 化し、「**ドキュメントの可搬性**」を FQCN 採用の公式理由として明記 |
| **運用** | Terraform も ansible-lint も **「VCS で差分を確認してからコミットせよ」**と明示。書き換えコミットを内容変更と混ぜない |

出典: https://docs.ansible.com/projects/ansible/latest/porting_guides/porting_guide_2.10.html ・
https://github.com/ansible/ansible-lint/blob/main/src/ansiblelint/rules/fqcn.md ・
https://docs.ansible.com/ansible/latest/collections_guide/collections_using_playbooks.html ・
https://developer.hashicorp.com/terraform/language/v1.1.x/upgrade-guides/0-13 ・
https://docs.brew.sh/How-to-Create-and-Maintain-a-Tap ・ https://docs.brew.sh/Tap-Trust

---

## Step 0: AoT Decomposition

| Atom | 判断内容 | 読む状態 | 書く状態 |
|:--|:--|:--|:--|
| **B1** | **T1 複製相の形**（生成器を入れるか / 向きを反転するか / 現状維持か） | Step -1 (2)(4) / HGA #33 裁定 1・#34「順変換を足すな」/ Step -0.5 (γ) の正本選択基準 | 本アンカーの B1 結論 |
| **B2** | **規則 R-S の定義**（何を skill の実行参照とみなすか） | Step -1 (3) / `starter/CLAUDE.md` の規約 / Step -0.5 (δ) の Ansible 事故 / 4a の R-A | 本アンカーの B2 結論 |
| **B3** | **射程**（`.md` のみか / scripts / starter / 182 箇所の 37） | B1・B2 の結論 / Step -1 (5) / `2026-09-05-distribution-scope-review.md` §2 | 本アンカーの B3 結論 |
| **B4** | **検査と移行の形** | B1〜B3 の結論 / T3 が 2026-09-05 に通った改訂 / Step -0.5 の検証パターン | 本アンカーの B4 結論 |

**B1 と B2 は独立**（B1 は機構、B2 は規則。互いの書く状態を読まない）→ **並列可**。
**B3 は B1・B2 を読み、B4 は B1〜B3 を読む** → 逐次。書込集合は本アンカーのみで交わらない。

---

## Atom B1: T1 複製相の形

**[MELCHIOR]**: T1 に生成器を入れればよい。HGA #33 が T3 に下した裁定をそのまま T1 へ適用するだけだ。
`.claude/` を正本、`templates/managed/` を派生とし、前向き変換（prefix 付与）を置く。
外部知見の一致点も明快で、**入力 1・出力 2** にすれば双方向の問題は消える。

**[BALTHASAR]**: 3 点ある。

**(i) HGA #34 は「生成器に順変換を足すな」と明言した。** それを翌日に破るなら理由が要る。

**(ii) 向きの選択基準が 2 つあって食い違う。** Rust の「情報量が少なく規則的な側を正本」に従えば
**修飾形の側**（除去は無損失、付与は規則を要する）。Jupytext の「人間が日常的に編集する側」に従えば
`.claude/rules/`。外部知見はここで割れている。

**(iii) だが反転案には致命傷がある。** `.claude/rules/` **19 件のうち 5 件は配布されない**
（`hga-summoning.md` / `model-roster.md` / `terminology.md` / `auto-generated/rule-001.md` /
`auto-generated/rule-002.md`）。反転すれば 14 件が plugins 正本・
5 件が `.claude/` 正本という **正本の分裂**が起きる。加えて **PM 級ゲートは `.claude/rules/` を指している**
（`permission-levels.md` §ファイルパスベースの分類）ため、全ゲートの付替が要る。
**正本が 2 箇所に散れば検査が成立しない** —— LAM が繰り返し潰してきた型そのものである。

**[CASPAR]**: 結論 —— **T1 に生成器を入れ、正本は `.claude/` 側に据え置く。**

**HGA #34 の「順変換を足すな」は射程外になった。** あの裁定の根拠は
「**付与は『実行指示か概念の言及か』の分類を要し、分類は導出ではない**」であった。
**R-A の成立によりその根拠は消えている** —— R-A は除外 3 位置を持つ**全域規則**であり、
1 件ずつの判断を含まない。**裁定を覆すのではなく、裁定が前提していた条件が変わった。**

向きは **正本の分裂を作らない側**を採る。外部の 2 基準は食い違うが、
**分裂の回避はどちらにも優先する**。そして `.claude/` を正本に据えれば
**入力 1・出力 2** が達成される —— 著者は `.claude/rules/` を 1 つ書き、
LAM 自身はそれを読み、利用者は導出物を読む。

**採用しなかった選択肢とその理由**:

- **(b) 向きを反転**（正本 = `templates/managed/`）→ 非配布 5 件で**正本が分裂**。PM 級ゲートの全付替。
  ADR-0010 追補 2「rules は `.claude/rules/` が正本」の改訂（PM 級）も要る。
- **(c) 現状維持**（手で 2 部 + バイト恒等）→ 配布物の中で**規約（starter）と実体（managed / skills）が
  矛盾したまま**残る。かつ HGA #33 が T3 について解体した形を T1 に温存する。
- **(d) managed から参照を消す（間接記述に畳む）** → 2026-09-05 の MAGI で棄却済
  （散文の間接参照を解決する機構が無い）。**再論しない**（争点 E 規律）。

---

## Atom B2: 規則 R-S の定義

**[MELCHIOR]**: slash 形 `/<skill>` を `/<ns>:<skill>` にする。構文的で曖昧さは無い。
実測で `phase="building"` / `"command": "full-review"` / `"mode": "autonomous"` という
別名前空間の値があることは分かっているが、**それらに slash は付いていない**。

**[BALTHASAR]**: **Ansible の最大の事故を踏むかどうかが、この Atom の全てである。**

あちらは「bare は修飾形の単なる短縮」という前提で autofix を作り、**それが偽だった** ——
bare `copy` は `ansible.legacy.copy` であり**ローカル override を拾う**。
`ansible.builtin.copy` は拾わない。**機械置換が挙動を静かに変えた。**

**我々も同じ構造を持っているか。持っている。** そして **LAM 自身が既に答えを書いている** ——
`templates/starter/CLAUDE.md`:

> 名前空間を省くと、**同名の personal / project skill があった場合にそちらが起動する**。

つまり **bare ≠ 短縮形**である。bare は「**利用者の override を拾う解決**」であり、
`ansible.legacy` と同型である。

**ただしこれは変換をやめる理由ではない。変換が正しいことの根拠である** ——
配布物が指しているのは**我々の skill** であって利用者の override ではない。Ansible が
「FQCN を使え」と推奨した理由（衝突回避・**ドキュメントの可搬性**）がそのまま当てはまる。

帰結が 2 つ: **(i) 意味が変わる変換なので diff レビューは必須**（Ansible の autofix 事故と同型）。
**(ii) 利用者向けの表（`starter/CHEATSHEET.md`）は既に修飾形なので触らない。**

**[CASPAR]**: 結論 —— **R-S: ハーネスの起動構文のみ ns 化する。**

| ns 化する | ns 化しない |
|:--|:--|
| slash 形 `/<name>` / `Skill(skill="<name>")` | slash の無い bare（概念の言及 / 4a の判断を継承） |
| | 除外 (T) = 言語タグ `markdown` / `json` のフェンス内（R-A と共通） |

**slash は著者が発明したマークではなく、ハーネス自身の起動文法である。**
RFC 1946 が要求した「唯一の signal」の条件（読者がそれで解決する）を満たす。

**加えて「bare は短縮形ではなく、利用者 override を拾う別解決である」ことを設計に明記する。**
Ansible はこれを事故の後に明文化した。**我々は先に書ける。**

**採用しなかった選択肢とその理由**:

- **skill 名の全出現を ns 化**（R-A と同型にする）→ 実測で `phase="building"` 等の
  **別名前空間の値**と衝突し**壊す**。skill 名は一般語であり固有名詞ではない。
- **`collections:` 相当の「この文脈では bare でよい」宣言を導入** → Ansible で
  **role に継承されず静かに誤解決**し、lint が機構の使用自体を叩く対象になった。
  文脈依存の許可は境界で破れる。
- **bare を残して推奨に留める**（Ansible の実際の選択）→ あちらは既存資産が膨大で
  ハードカットが不可能だった。**我々の対象は 118 行であり、その制約が無い。**
  かつ bare を残すと**規約（starter）と実体の矛盾が残り続ける**。

---

## Atom B3: 射程

**[MELCHIOR]**: `.md` のみ。4a と揃える。

**[BALTHASAR]**: 3 つ確認が要る。

**(i) `templates/managed/scripts/` の `.py` / `.sh` に slash 形が 7 箇所ある**（docstring・コメント）。
読者は開発者なので 4a の hooks 除外と同じ理由で対象外だが、**測った上で外すこと**。
測っていないのと 0 だったのは違う（4a の A4 で確認した規律）。

**(ii) starter は対象外**。既に規約に準拠しており、T1 検査の対象ですらない。

**(iii) 182 箇所のうち 37 箇所（`.claude/skills/...` パス自己参照）は別問題である。**
あれは「名前の修飾」ではなく「**パス参照が plugin 配布下で原理的に壊れる**」形であり、
変換規則が違う —— パスからコンポーネント参照への変換は**情報の欠落を伴う**
（`.claude/skills/magi/SKILL.md:120` のような行・節の指定が消える）。**混ぜてはならない。**

**[CASPAR]**: 結論 —— 射程は **`.md` のみ**。

| 領域 | 射程 | 根拠 |
|:--|:--|:--|
| `plugins/lam-harness/{skills,agents}/**/*.md` | **対象**（R-S / 67 行） | T3 正本 |
| `.claude/rules/*.md` ＋ `docs/internal/*.md` | **対象**（R-S 51 行 ＋ R-A 36 行 / **生成器が派生側に書く。正本は 1 バイトも変えない**） | T1 正本 |
| `templates/managed/scripts/**` | **対象外** | 読者は開発者（実測 7 箇所 / 4a の hooks 除外と同じ理由） |
| `templates/starter/**` | **対象外** | 既に規約準拠。T1 検査の対象でもない |
| **182 箇所のうち 37（パス自己参照）** | **Action 4c へ分離** | 変換規則が違い、**情報の欠落を伴う** |

---

## Atom B4: 検査と移行の形

**[MELCHIOR]**: 4a と同じでよい。codemod と検査を同一コミットで入れる。

**[BALTHASAR]**: T1 は事情が違う。**T1 の検査は今「バイト恒等」であり、それを「== 導出」に変える** ——
2026-09-05 に T3 で通ったのと同じ改訂だが、**T1 は 36 ファイルあり、生成器が初めて書く**。

3 点を要求する。

**(i) 往復恒等を両方向で証明せよ。** T1 は `to_project_text(forward(x)) == x`（正本に戻る）、
T3 は既存の `to_project_text(正本) == 開発側`。**前者が破れれば `templates/managed/` が
`.claude/` から乖離し、T1 が守ってきた不変条件そのものが壊れる。**

**(ii) 例外表を作るな。** ansible-lint が機械化できたのは
**「文脈依存の bare 許可」を解決に一切考慮しないと決めたから**である。

**(iii) codemod は「差分を確認してからコミットせよ」と言え。** Terraform も ansible-lint も
そうした。**bare は意味が違うので、この変換は挙動を変える。**

**[CASPAR]**: 結論 ——

| # | 内容 |
|:-:|:--|
| 1 | **T1 生成器を新設**し、T1 検査を「バイト恒等」→「**managed == 導出(`.claude` 正本)**」へ改める（T3 が通った道と同型） |
| 2 | **往復恒等を両方向で検証**。T1 は `to_project_text(forward(x)) == x`、T3 は既存 |
| 3 | **段階を作らない**（HGA #34 裁定 3 の継承）。codemod + 生成器 + 検査を同一コミット |
| 4 | **例外表を作らない**（ansible-lint の立場） |
| 5 | **diff レビューを必須の工程として書く**（Ansible の autofix 事故 / bare は意味が違う） |
| 6 | **T5 検査を R-S へ拡張**し、`.claude/` 正本にも「slash 形が bare で残っていないこと」ではなく **「生成器の出力と一致すること」**を課す（正本は bare のままが正しいため、正本側に R-S 検査を当ててはならない） |

**採用しなかった選択肢とその理由**:

- **段階移行（warn → error）** → HGA #34 裁定 3「来ない段階は作らないのが最良の強制」。
  対象は 118 行であり、一括で終わる。
- **ベースライン ratchet** → 4a で棄却済（**符号を反転させた宣言**にすぎない）。**再論しない**。
- **T1 検査を残したまま managed を手で直す** → 手で 2 部維持を温存する。B1 の結論に反する。

---

## Step 4: gabriel probe

| 項目 | 値 |
|:--|:--|
| verdict | **refuted** |
| severity | **warning** |
| affected_atoms | B1 / B4 |
| recommended_action | **proceed** |
| confidence | 0.60 |

分岐は **AC-W-C-6**（`refuted & warning` → gabriel 指摘を併記 + 警告ラベル）。
計器: `.claude/gabriel-metrics.log` に 1 行追記済（`resolved_action: annotate_warning`）。

### 指摘 1【最重大 / **未解決・PM 級**】ADR-0010 追補 2 決定 2 との衝突

決定 2 の条文はこうである。

> 派生物はテキスト上 bare 名を含む。**I-4 は「著者が書く正本」を拘束し、機械的に導出された派生物は
> 対象外**とする。検査は「派生 == 導出(正本)」と「**正本側に bare の実行参照が残っていないこと**」の
> 2 本で閉じる（前者だけでは、正本に bare が残ったまま両側 bare で一致し、**緑のまま配布物が壊れる**）。

**文字どおり適用すると、B1 が「bare のままが正しい」とする `.claude/rules/` 自身が ns 化対象になる。**
gabriel はこの衝突を指摘し、**B1・B4 が決定 2 に一言も触れていない**ことを問題とした。指摘は正しい。

**衝突の正体は、決定 2 が「正本 = 配布される側」を暗黙に前提していることである。**
条文自身が目的を書いている ——「緑のまま**配布物**が壊れる」。守ろうとしているのは**配布物**であって
「正本」ではない。2026-09-05 時点では T3 しか存在せず、そこでは 正本（`plugins/`）= 配布側だったため、
両者が一致していた。**T1 は正本（`.claude/`）が配布されない側であり、この前提が成り立たない。**

> **したがって正しい一般形は「配布される側に bare の実行参照が残っていないこと」である。**
> T3 ではそれが 正本 に、T1 では 派生 に落ちる。決定 2 はその特殊形である。

**これは条文の改訂を要する（ADR-0010 追補 3 / PM 級）。** 決定 3 自身が
「**観測と条文のドリフトは、条文側を直さなければまた失われる**」と述べており、
「domain-scoped に読めばよい」で済ませることは、その決定 3 に反する。

**本設計は、この追補が承認されるまで実装に進まない。**

### 指摘 2【是正済 / 実測で解消】R-S の構文的純度が未実測だった

gabriel は「B1 の『HGA #34 の順変換禁止は射程外』は、R-A（固有名詞 12・除外 3 位置・**全数 diff レビュー済**）
の成立を R-S（一般語 15・フェンス除外のみ）へ**無検証で外挿する類推**である」と指摘した。正しい。

→ **R-S の置換候補 125 箇所を全数レビューした**（T3 skills / T3 agents / T1 rules / T1 docs-internal）。
**誤爆はゼロ** —— 125 件すべてがハーネスのコマンド呼び出しへの参照であり、
`phase="building"` / `"command": "full-review"` / `"mode": "autonomous"` のような
**別名前空間の値は 1 件も混入していない**（それらに slash が付かないため、構文で分離できている）。

R-A のときと同じ形の検証（**集計ではなく全数目視**）を通した。**外挿ではなく実測になった。**

### 指摘 3【是正済】非配布件数の内部不整合

Step -1 (4) の「3 件」が誤りで、正しくは **5 件**。→ 同節に訂正を記載した。

### 指摘 4【確認された】B3 の分離は数値が正確

gabriel は 4c として分離する 37 箇所が `2026-09-05-distribution-scope-review.md` と一致することを確認した。

### 追加で確認した点（gabriel の疑問 3 への回答）

「**正本側に R-S 検査を当ててはならない**という非対称は構文だけで判定できるか。
同じファイルが両方の性質を持つ経路はないか」——

**判定できる。** どちらのチェーンかは `_MANAGED_AREAS`（`.claude/rules` / `docs/internal` / `.claude/scripts`）と
`_MIRROR_AREAS`（`.claude/skills` / `.claude/agents` / `.claude/hooks`）という**構造定数**で決まり、
1 件ずつの判断を含まない。**両集合のディレクトリは互いに素**であり、同一ファイルが
両方の性質を持つ経路は存在しない。

---

## Step 5: AoT Synthesis（**2026-09-06 承認・実施済**）

### 統合結論

**Action 4b の本体は skill の slash 形ではなく、T1 に残された「手で 2 部維持する複製相」だった。**
HGA #33 が T3 について解体した形が、**向きが逆であるという理由だけで T1 に温存されていた**。

そして gabriel の指摘 1 が、その温存が生んだ第二の帰結を暴いた ——
**条文（ADR-0010 追補 2 決定 2）もまた「正本 = 配布される側」という T3 だけの前提で書かれていた。**

### 前提とした条文改訂（**承認済 / 実施済**）

**ADR-0010 追補 3 を先に入れた。** 条文と設計が食い違ったまま実装すれば、
「実装と条文のドリフト」を自分で作ることになる —— 本プロジェクトが繰り返し潰してきた型である。

### 承認を得た内容（1 点のみ / ユーザー承認 2026-09-06）

> **ADR-0010 に追補 3 を追加し、決定 2 の不変条件を
> 「正本側に bare の実行参照が残っていないこと」から
> 「**配布される側に bare の実行参照が残っていないこと**」へ一般化する。**
>
> - T3（正本 = `plugins/` = 配布側）では**現行と同じ判定**になる。4a の実装（T5）は無変更。
> - T1（正本 = `.claude/` / 派生 = `templates/managed/` = 配布側）で初めて意味を持つ。
> - 決定 2 の目的節（「緑のまま**配布物**が壊れる」）と整合する。**目的は変えず、射程を正す。**

承認後の実施内容は Atom B1〜B4 の結論のとおり（T1 生成器の新設 / R-S の適用 / 検査の改訂 /
往復恒等の両方向検証 / 段階なし / 例外表なし / diff レビュー必須）。

---

# 実施記録（Action 4b / 2026-09-06 / ユーザー承認後）

## 変更したもの

| 分類 | 実体 |
|:--|:--|
| **条文（PM 級 / 承認済）** | `docs/adr/0010-...md` **追補 3** —— 不変条件を「配布される側に bare の実行参照が残っていないこと」へ一般化 |
| 規則の実装 | `verify_plugin_containment.py` —— `skill_names()` / `to_namespaced_skill_text()`（**R-S**）/ `to_distributed_text()`（R-A ∘ R-S）/ `derive_managed_text()` / `invert_managed_text()` / `_enclosing_token()` |
| **T1 生成器（新設）** | `.claude/scripts/derive_managed_templates.py` —— **T1 が初めて生成器を持った** |
| 検査の改訂 | **T1**: バイト恒等 → **「派生 == 導出(正本)」** / **T5**: R-A に加えて **R-S** も検査 |
| codemod | `namespace_source_refs.py` を R-A ∘ R-S へ拡張 |
| テスト（新規 12 / 追加 12 / 改訂 1） | `test_managed_derivation.py`（新規）/ `test_source_namespacing.py`（R-S・(P) 拡張）/ `test_verify_plugin_containment.py`（T1 の判定変更に追随） |
| 変換 | T3 正本 **16 ファイル** / T1 派生 **18 ファイル** |

**`.claude/skills` `.claude/agents` `.claude/rules` `docs/internal` の差分は 0 件。**
LAM 自身が読む正本は 1 バイトも変わっていない。

## 検証

| 検査 | 結果 |
|:--|:--|
| pytest | **1400 → 1423 passed / 14 skipped** |
| `verify_plugin_containment.py` | OK（T1〜T5 / **T1 は導出一致・T5 は R-A + R-S**） |
| `derive_project_copies.py --check`（T3） | OK（更新 0 件） |
| `derive_managed_templates.py --check`（T1） | OK（更新 0 件） |
| `verify_distributable_claims` / `verify_reference_resolution` / `verify_model_reference` | OK |

## diff レビューが実際に捕まえたもの（**必須工程にした根拠**）

Ansible の autofix 事故（「bare は短縮形」という偽の前提で機械置換し、挙動を静かに変えた）を
踏まえて diff レビューを必須工程に置いた。**そして実際に 1 件、意味の壊れた置換が見つかった。**

> `docs/internal/08_EXECUTION_DISCIPLINE.md` の
> `` `.claude/agents/{doc-writer,requirement-analyst,design-architect,task-decomposer,quality-auditor}.md` ``
> —— **ブレース展開によるファイル列挙**。2 件目以降は直前が `,` であるため、
> `/` の lookbehind だけでは (P) 除外に掛からず、**5 件すべてが名前空間化されて
> パスが壊れた**（`.claude/agents/lam-harness:doc-writer,...`）。

**規則の穴であり、1 件だけの例外ではない。** よって (P) の定義を直した ——
「**その語を含むトークンが `/` を含むか**」で判定する（区切りは空白とバッククォートのみ。
カンマを区切りにするとブレースの内側が分断され、同じ穴が再発する）。

**この 1 件は集計では出てこない。** 全数目視でしか見つからず、
HGA #34 が「確信度を下げる最大要因」として名指ししたのもこの類だった。

## テストが捕まえたもの（**陰性対照の実績**）

往復恒等の検証を素朴に `to_project_text` 一本で書いたところ、
`.claude/scripts/verify_distributable_claims.py` のコメントが **意図的に `/lam-harness:init` を
持っている**ため偽陽性で落ちた（`.py` は導出が恒等写像なのに、逆写像だけが prefix を剥がした）。

→ 逆写像を `invert_managed_text()` として正しく定義した（**`.md` にのみ prefix 除去を当てる**）。
**導出と逆写像は定義域が一致していなければならない**という、書く前には見えていなかった要件である。

## 積み残し

1. **Action 4c** —— 182 箇所のうち 37（`.claude/skills/...` のパス自己参照）。
   変換が**情報の欠落を伴う**ため別設計
2. 組み込み一覧の採取 / `test-runner` の改名（PM 級・別件）/ frontmatter `Agent(ns:x)` の受理性
   —— いずれも 4a から継続

## 残る警告（gabriel / **ラベルとして残す**）

- 除外 (T) のタグ集合 `{markdown, json}` は依然として**手で置いた値**である（4a から継続）
- 除外 (P) の「トークンに `/` を含むか」は、**本セッションのコーパスで全数レビューして
  誤爆 0 を確認した**が、判定そのものは経験則である。`/` を含む語の中で agent 名を
  参照する記法が現れれば取り逃す（既定が「変換しない」側なので**壊れる方向ではない**）
