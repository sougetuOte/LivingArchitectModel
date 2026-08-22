# `core-identity.md` 廃止案（案 2）の経緯と影響範囲の実測

**起草日**: 2026-08-22
**位置づけ**: `SESSION_STATE.md` 次のステップ #1「案 2 の判断」の前提として、2026-08-21 MAGI が「**影響範囲の全数調査を経てから改めて問う**」と条件づけた調査の結果。**実施・不実施のいずれを選ぶ場合でも、本文書が影響範囲の正本**である。
**先行文書**: `docs/artifacts/2026-08-21-magi-core-identity-merge.md`（案 1/2/3 の MAGI アンカー / gabriel probe / HGA #26・#27）

> **本文書は判断を確定させない。** 案 2' の選択と §7 の未決 4 点は MAGI（AoT + gabriel）へ送る。

---

## 1. 経緯と推移

| 段階 | 日付 | 出来事 |
|:---|:---|:---|
| ① 発案 | 2026-08-21 | 在庫 #4（計器隔離の規範）を R1 に入場させる**交換相手を探す**過程で、`core-identity.md` と `permission-levels.md` の重複 3 組 6 項（赤 = 権限等級の要約 / 黄 = 第 0 原則 3 変数の逐語再掲 / 青 = 接続 3 項）を発見。整理案として **案 1（権限等級の一本化）/ 案 2（`core-identity.md` の廃止・分配）/ 案 3（青の A 1 行のみ削除）** が並ぶ |
| ② MAGI | 2026-08-21 | AoT 6 Atom。A2 で赤を対象外（`AC-1.24`/`AC-1.25` 保護 + 循環の原因ではない）、A4 で青の A（PM 級再導出の禁止）を保持 → 案 1 の原型が崩れ **案 1'** が残る |
| ③ 案 2 の却下 | 2026-08-21 | A5 で 3 理由（テスト assert 破壊 / design が構造として記載 / 参照元 40 件超が未調査）により却下。**廃案ではなく「全数調査後に再提起」** として保留 |
| ④ gabriel | 2026-08-21 | `refuted`/`warning`/`proceed`。案 1' の中身は支持。参照元を実測し **71 件・28 ファイル**と報告（L1 の「40 件超」は過小報告だった） |
| ⑤ HGA #26 | 2026-08-21 | gabriel の処方（文字列一致テスト）を制度の会計則違反として棄却。crux 2 で「**逐語コピーは独立に漂流し、将来の L1 が弱い方を引用できる。単一正本への統合はむしろ拘束を強める**」と案 2 の方向性自体は肯定。ただし手 1「**刃を持つ者を替える**」により、自分を縛る文に触れる編集は人間の手で |
| ⑥ 案 1' 実施 | 2026-08-21 | 黄は L1、青はユーザーの手で実施。**残る重複は赤 1 組のみ**になった |
| ⑦ 本調査 | 2026-08-22 | 4 系統の並列調査（実行系 / 仕様・ADR・タスク / 配布物・歴史記録 / 分配先の受け入れ可能性）+ 外部 3 系統。**却下理由 3 本のうち 2 本が事実に耐えず**、代わりに §4 の意味論的障害が立った |

### 価値の所在（②〜⑥ を経ての整理）

案 1' で**条項レベルの正本一本化は完了している**（黄・青とも正本が確定）。よって案 2 に残る価値は「正本の一本化」ではなく、**同じ話題を書ける場所が 2 枚ある構造そのものの解消**（再発防止）である。赤・黄・青は別々の時期に別々の理由で生えており（赤 = 2026-03 v4.0.0 / 黄 = 第 0 原則導入時 / 青 = 2026-07-07 L3 導入時）、3 回起きているなら原因は各回の不注意ではなく構造にある。

---

## 2. 却下理由 3 本の再判定

| # | 2026-08-21 の却下理由 | 本調査の判定 | 根拠 |
|:-:|:---|:---|:---|
| ① | `test_compaction_exposure.py:72` の assert を壊す | **不成立** | `load_conditional_load_rules`（`pre-compact.py:192`）は `rglob("*.md")` で実ファイルのみ走査し、`paths:` を持つものだけを辞書に収める。削除後は当該キーが存在し得ず `not in` が**恒真化**する。赤くならず**無言で空振り**になる（`rule-001` 観測 #6 と同型の病理） |
| ② | v4.0.0 design が構造として記載 | **ほぼ不成立** | `docs/specs/v4.0.0-immune-system-requirements.md` に `core-identity` は **0 件**（`grep -c` 実測）。`docs/design/…-design.md` §5 Wave 1 に対応節がなく、`§9.2` 変更サマリ表に「権限等級の**言及**」1 行のみ。「概要を置け」と指定しているのは `docs/tasks/` の `AC-1.24`/`AC-1.25` で、これは `[x]` 済の**完了記録**であり将来拘束ではない。→ **仕様改訂（PM 級）は先行しない** |
| ③ | 参照元 71 件で影響範囲が未確定 | **不成立**（当時は正しかった） | §3 のとおり必須の追随は 5 件。ただし「未確定だった」こと自体は事実であり、③ による却下は**当時の判断として妥当**だった |

**総括**: 当時の却下は「調べていなかったから」正しかったのであって、「調べたら通らない案だから」ではない。

---

## 3. 影響範囲の実測（全 92 件）

母数は `grep -rn "core-identity"`（`.md` / `.py` / `.json` / `.txt` / `.html` / `.yaml`）の **92 件**。別名参照（`行動規範` / `第 0 原則` / `Active Retrieval` / `Context Compression` / `PM 級編集の事前宣言`）も各担当が追加 grep で拾った。

### 3.1 追随が必須（5 件）

| # | file:line | 内容 | 等級 | 分配先が `permission-levels.md` の場合 |
|:-:|:---|:---|:---|:---|
| 1 | `.claude/agents/gabriel.md:70` | 「`core-identity.md` Active Retrieval 原則と同型」 | SE | 外部参照のまま（要修正） |
| 2 | `.claude/rules/permission-levels.md:83` | 事前宣言義務の参照 | PM | **同一ファイル内の自己参照**に変わり文言修正のみ |
| 3 | `.claude/rules/permission-levels.md:95` | 「§第 0 原則 が**正本**」 | PM | 同上 |
| 4 | `CHEATSHEET.md:42` | Rules ファイル一覧の行 | SE | 行の削除・置換 |
| 5 | `CHEATSHEET_en.md:42` | 同（英語版） | SE | 同上 |

### 3.2 機械的に落ちる（1 箇所）

- `.claude/tests/rules/test_clause_gate_ledger.py::test_resident_file_set_matches_ledger` の `stale` assert。`_live_resident_files()` は実ファイルを走査するため削除で live から消えるが、台帳 §A の行が残ると `stale` に検出されて **FAIL**。→ **`docs/artifacts/clause-gate-ledger.md` §A の 1 行の更新が必須**（この依存は "core-identity" という文字列を持たないため grep 92 件には現れない）

### 3.3 無言で空振りになる（1 件）

- `.claude/tests/hooks/test_compaction_exposure.py:72`。上記 §2 ①。**`phase-rules.md` 等の別の無条件常駐ファイルへ差し替えれば検査の意味が戻る**（任意・推奨）

### 3.4 追随不要（約 85 件）

| 区分 | 件数 | 扱い |
|:---|--:|:---|
| 歴史記録（`docs/artifacts/` 14 ファイル 46 行 / `docs/daily/` 3 行 / `docs/private/` 4 行） | 53 | **書き換えない**（`terminology.md` §5 の既存記述維持 + 台帳の append-only 原則） |
| `CHANGELOG.md` | 7 | 遡及編集しない慣行 |
| ディレクトリ総称（`rules/` = 行動規範）: `CLAUDE.md:58` / `README.md:55` / `CHEATSHEET.md:22` / `docs/slides/*.html` | 5 | ファイル名非依存。`rules/` は存続する |
| 概念名のみの言及（`第 0 原則` / `Active Retrieval`）: `CLAUDE.md:184,192` / `hga-summoning.md:29` / `gabriel.md:199` / `README.md:19` / slides | 8+ | パス非引用。ただし**分配後も `.claude/` 内に該当見出しが実在し続けること**が前提 |
| FR-9 のパス文字列 fixture（`.claude/hooks/tests/test_pre_tool_use.py:272,317`） | 2 | `_FR9_PATTERNS` は `^\.claude/rules/` の正規表現一致でファイル実在を見ない → 影響なし |
| 完了済 Milestone の参照・完了記録（`docs/specs/m-1-*` / `v3.9.0` / `large-scale-review` / ADR-0008 / `docs/tasks/v4.0.0-*`） | 12 | 史料としてそのまま。移設注記 1 行（SE 級）で足りる |
| `SESSION_STATE.md`（gitignore 済の作業ファイル） | 7 | 追随不要 |

### 3.5 副産物 — 「歴史記録フォルダ」に現行規律が紛れている

逆参照確認で、**`docs/artifacts/` `docs/private/` 配下に「現在も規律として参照されている文書」が 8 件**あることが判明した（`fable-l3-protocol.md` は `CLAUDE.md` と `phase-rules.md` が節番号レベルで参照 / `clause-gate-ledger.md` `hga-summon-log.md` `clause-gate-routing-design-2026-07-26.md` は skill・rules が SSOT / 正本として直接指定 / 他 4 件）。**「フォルダ＝性質」で一括処理する施策は本件に限らず危険**。本件の射程外だが記録に残す。

---

## 4. 分配先の受け入れ可能性 — 案 2 の本当の障害

| 節 | 最も自然な行き先 | 判定 |
|:---|:---|:---|
| §Context Compression | `CLAUDE.md` §Context Management | **無損失で移せる**（現行 §Context Management は auto-compact 発火点と手動判断が中心で、書き出し + リセット宣言の手順は未収載 = 補完関係） |
| §権限等級 PG/SE/PM + 事前宣言義務 | `permission-levels.md` の同名見出し | 文脈の前置き 1 文 + `:83` の参照文修正が要る |
| **§第 0 原則** | `permission-levels.md` §迷った場合 付近 | **移すと意味が変わる** —— 「以下の LAM 規則が状況を想定していない場合、この 3 変数から判断を再導出する」という**全規則に及ぶ射程**が、権限等級専用ファイルに入ると等級固有の原理に見える |
| **§Active Retrieval** | **受け皿なし** | `CLAUDE.md` に対応節がなく、`permission-levels.md` とは無関係。移動ではなく**新設**になる |

**結論**: `core-identity.md` は「重複の残骸」ではなく、**射程が全規則に及ぶ原理（第 0 原則・Active Retrieval）の置き場**だった。ドメイン別ファイルへ解体すると原理が特定ドメインの付属物に格下げされる。**当初の「一本化」は方向が逆で、正しくは役割の分離である可能性が高い。**

---

## 5. 予算・計器への影響

| 項目 | 値 |
|:---|:---|
| `core-identity.md` の指令数 | **1**（`§権限等級との接続` の「禁止」1 語 / 台帳 §A 行 #12 と一致） |
| 分配後の §A TOTAL | **不変（60）** —— 移動元も移動先もすべて R1 の会員であり、R1/R2 の所属が変わらない |
| **未払い債務（取引 #16）への充当** | **不可**。R1 内移動は取引 #9 の前例どおり**予算中立**であり退出ではない |
| compaction 挙動 | **中立**。`core-identity.md` も分配先も `paths:` を持たず、`pre-compact.py` の曝露検出の対象外 |
| 注意 | 合流時に文言を言い換えて指令キーワードが消えると §A は見かけ上減るが、規律は移設先で存続する。**§B の退出として計上してはならない**（取引 #15 → 更正 #17 と同型の罠） |

---

## 6. 案 2' の候補

| 案 | 中身 | 得るもの | 失うもの |
|:---|:---|:---|:---|
| **A. 役割分離（逆方向統合）** | `core-identity.md` = **原理**（第 0 原則 + Active Retrieval）に純化。権限等級の要約と事前宣言義務を `permission-levels.md` へ寄せ、同ファイルは**実務台帳**に純化 | 「同じ話題を書ける場所が 2 枚ある」構造が**役割の排他割当**で解消。第 0 原則の射程が保たれる。追随は §3.1 の一部のみ | ファイル数は減らない（元々目的ではない）。`permission-levels.md` が肥大 |
| B. pointer 化 | ファイルを残し各節を参照 1 行に置換 | 参照切れゼロ | コピー削減の誤計上の罠に正面から入る。「存在するが中身のない R1 ファイル」が生まれる。**`@import` を使う形は上流仕様上ムダ**（§9 参照） |
| C. 部分移動 | Context Compression と権限等級要約のみ移し、原理 2 節は残す | 無理がない。§4 の障害を回避 | 目的が半分しか達成されない |
| D. R2 降格 | `paths:` を付けて条件ロードへ | **本物の退出**になり得る（債務決済の候補） | 第 0 原則は繋留先がイベント（判断の瞬間）のため**設計 §2 Step 2 により R2 不可**。加えて上流仕様上 **`paths:` 規範は compaction で失われる**（§9） |
| E. 現状維持 | 何もしない | コストゼロ | 再発の構造が残る |

---

## 7. 未決の論点（MAGI へ送る）

1. **案 A〜E のいずれを採るか**。§4 の意味論的障害と §6 の得失をどう秤にかけるか
2. **§PM 級編集の事前宣言義務は R2 に降格できるか**。繋留先は PM 級パス集合（= ファイル繋留 ✓）、配送先は `paths:` glob ✓、再武装は自己再武装型 ✓。争点は **軸 3 が可逆か**と、**「編集する前に宣言」という要求に対し `paths:` 規範が「読んだとき」に届く**タイミングの穴（取引 #8・#11 と同型 / 上流仕様でも Edit 単独時の発火は**未定義** = §9）
3. **2 が成立する場合、それを取引 #16 の債務決済に充ててよいか**。§3.2 の交換相手制約（別途の理由で既に削除が決まっている条項は不可 / コピー削減は不可）に照らした判定
4. **実施主体**。第 0 原則は L1 自身を縛る条項であり、HGA #26 手 1（刃を持つ者を替える）の射程に入るか。手 1 は「一回性の運用であり規律化しない」と明記されている

---

## 8. 再現手順

```bash
# 母数（92 件）
grep -rn "core-identity" --include=*.md --include=*.py --include=*.json --include=*.txt --include=*.html --include=*.yaml . | sed 's|^\./||'

# 仕様側の拘束（0 件であることの確認）
grep -c "core-identity" docs/specs/v4.0.0-immune-system-requirements.md

# 指令数（台帳 §A との突合）
grep -o "MUST NOT\|MUST\|SHOULD NOT\|SHOULD\|禁止\|必須\|してはならない" .claude/rules/core-identity.md | sort | uniq -c

# 機械依存の確認
bash .claude/scripts/py_invoke.sh -m pytest .claude/tests/rules/test_clause_gate_ledger.py .claude/tests/hooks/test_compaction_exposure.py -q
```

---

## 9. 外部資料（上流仕様の裏取り / 2026-08-22 取得）

一次資料は `code.claude.com/docs/en/{memory,context-window,sub-agents,hooks,skills}` および Anthropic 公式ブログ（2026-06-18）。**本件の判断に効く事実のみを抜き出す**。

| # | 事実 | 逐語（公式） | 効く先 |
|:-:|:---|:---|:---|
| 1 | **`paths:` 規範は compaction で失われる** | 「Rules with `paths:` frontmatter \| **Lost until a matching file is read again**」/ 「If a rule must persist across compaction, drop the `paths:` frontmatter or move it to the project-root CLAUDE.md」 | **案 D の代償が確定**。設計 §1.2 (iv) 再武装要件の上流根拠でもある |
| 2 | **`@import` は文脈量を減らさない** | 「Splitting into `@path` imports helps organization but doesn't reduce context, since imported files load at launch.」 | **案 B の一形態が無効化** |
| 3 | **量が増えると遵守率が落ちる（公式明言）** | 「target under 200 lines per CLAUDE.md file. Longer files consume more context and **reduce adherence**.」/ 「Shorter files produce better adherence.」 | 誕生ゲートの天井思想の上流裏づけ。ただし**閾値は「1 CLAUDE.md ファイルあたり 200 行」のみで、指示総量の閾値は公式に存在しない** |
| 4 | **公式が問題とするのは「矛盾」と「総量」であり、非矛盾の重複ではない** | 「if two rules contradict each other, **Claude may pick one arbitrarily**」/ 階層間は「Claude uses judgment to reconcile them」= 決定論的優先順位は**ない** | 案 2 系の動機（重複の再発防止）は**矛盾リスクの予防**として正当化できるが、「重複それ自体が有害」とする公式根拠は**ない** |
| 5 | **`.claude/rules/` は公式機能**（LAM 独自ではない） | 「Rules without `paths` frontmatter are loaded at launch with the same priority as `.claude/CLAUDE.md`.」 | R1 の定義が上流と一致していることの確認 |
| 6 | **観測手段が公式にある** | `InstructionsLoaded` hook（`load_reason` = `session_start` / `nested_traversal` / `path_glob_match` / `include` / `compact`）+ `/context` | 「何がいつ入ったか」は推測せず**計測できる**。§10 の課題に直結 |
| 7 | subagent は `CLAUDE.md` 階層を丸ごと積む（Explore / Plan を除く） | 「every level of the CLAUDE.md hierarchy the main conversation loads」 | **R1 の総量は委譲のたびに複製される** = 天井の意味が L1 だけの問題ではない |

**上流に記述が無いことを確認した事項**（推測で埋めないための記録）: (a) Read を経ない Edit / Write のみで `paths:` が発火するか / (b) 条件ロード規範同士および `CLAUDE.md` との相対優先順位 / (c) subagent 内 compaction 後の再注入 / (d) 指示総量（`CLAUDE.md` + rules 合算）の閾値 / (e) 非矛盾の重複が遵守率に与える影響。

### 実測（同日 / 参考値）

`CLAUDE.md` **243 行** + 無条件 rules **13 ファイル 1,909 行**が毎セッション・毎 compaction で入る。`paths:` 付き 6 ファイル 693 行は入らない。**公式の 200 行目安をどの単位に適用するかは上流が決めていない**ため、この値は「多い / 少ない」の判定ではなく現状の記録として置く。

---

## 10. 本調査から派生した別課題（本件の射程外 / 記録のみ）

1. **R1 の総量を継続計測する手段が公式にある**（`InstructionsLoaded` hook / `/context`）。誕生ゲート §A は指令数の代理変数だが、**実際にロードされた量そのもの**を測る経路が存在する
2. **§3.5 の「歴史記録フォルダに現行規律が紛れている」8 件**。フォルダ単位の一括処理を行う施策があれば事前に除外リストが要る
3. **`CLAUDE.md` が 243 行で、公式目安 200 行を超えている**（§10.1）
4. **PM 級パス列挙が hook 実装と乖離している**（§10.2 / HGA #28 の付随観測）

### 10.2 PM 級パス列挙のドリフト（2026-08-22 発見 / HGA #28 付随観測 / 実測確認済）

**乖離の実体**:

| 所在 | 列挙している PM 級パス |
|:---|:---|
| `.claude/hooks/_hook_utils.py:61-72`（**実装 = 実際に執行される**） | `docs/specs/**.md` / `docs/adr/**.md` / `.claude/rules/**.md` / `.claude/settings*.json` / **`CLAUDE.md`**（2026-07-26 追加 / 誕生ゲート設計 §4.2-4.3・ユーザー承認済） |
| `core-identity.md` §PM 級編集の事前宣言義務（条文） | 上記のうち **`CLAUDE.md` を欠く 4 種** |
| `permission-levels.md` §ファイルパスベースの分類（条文） | 同じく **`CLAUDE.md` を欠く** |

**帰結**: 承認ゲート自体は hook が執行するため機能している（`CLAUDE.md` を編集すれば PM ダイアログは出る）。**欠けているのは自己拘束の側** —— 条文上、L1 は `CLAUDE.md` の編集について**事前宣言の義務を負っていない**ことになる。R1 で最も常駐性の高い 1 ファイルがそこから漏れている。

**本件（案 A）に混ぜない理由**: 列挙の拡張は「所在の変更」ではなく**要否の判定**であり、2026-08-21 MAGI A1 の凍結条件（**条項の要否は問わない**）に抵触する。混ぜれば移動が再判定に化ける。

**性質**: これは E5「矛盾を検出してもモデルがユーザーに知らせるのは 45%」「乖離は沈黙のうちに解決される」の**実例**である。約 4 週間、条文と実装が食い違ったまま誰も気づかなかった。

**起票済**: 台帳 §D 在庫 **#5**（2026-08-22 / 検出イベント 1 件）。**入場には真正な退出 2 件を要する**（§未払い債務が開いているため）。

### 10.3 実施後レビューで確認された既知コスト 2 件（2026-08-22 / 記録のみ・是正しない）

案 A の実施後に横断監査（quality-auditor）が検出し、**是正せず記録に留めた**もの。いずれも凍結条件（条項の要否は問わない / 本文は逐語）の下で触れないほうが安全と判断した。

| # | 内容 | 判断 |
|:-:|:---|:---|
| 1 | **`permission-levels.md` 冒頭で三段階分類が短距離に 3 回出る**（ファイル導入文 → 移設された §権限等級（PG/SE/PM）→ ## PG級 / SE級 / PM級 の詳細節） | **予見済みのコスト**。移設前は別ファイルにあり「詳細: permission-levels.md」の 1 行で橋渡しされていたが、同一ファイル内に来て自己参照化したため橋渡し文を落とした結果である。**解消には要約の削除か導入文の書き換えが要り、どちらも凍結条件に抵触する**。ISO/IEC Directives 10.1（繰り返しではなく参照せよ）に照らせば改善余地があり、**将来ゲートを通す価値のある候補**として記録する |
| 2 | **Context Compression の概念が 3 箇所に散在**（`CLAUDE.md` §Context Management / `docs/internal/02_DEVELOPMENT_FLOW.md` §Phase 3 / `docs/internal/05_MCP_INTEGRATION.md`）。相互参照なし | **移設以前から存在**した状態であり、本件が生んだものではない。`docs/internal/` は Hierarchy of Truth 第 2 位の SSOT であるため、接続文の追加は別途の判断を要する |

### 10.1 `CLAUDE.md` 243 行の件（2026-08-22 記録 / 本件の射程外）

**実測**: `CLAUDE.md` **243 行**。無条件 rules 13 ファイル **1,909 行**と合わせて、毎セッション・毎 compaction で文脈へ入る。**subagent へ委譲するたびに `CLAUDE.md` 階層は丸ごと複製される**（Explore / Plan を除く / 公式）。

**公式の根拠**:

- 「**Size**: target under 200 lines per CLAUDE.md file. Longer files consume more context and **reduce adherence**.」/「**Shorter files produce better adherence.**」（`code.claude.com/docs/en/memory`）
- 「a single CLAUDE.md at the repository root tends to either **grow to cover every subsystem's conventions**, costing context on instructions unrelated to the current task, **or stay too generic to be useful**.」（`…/large-codebases`）
- 「In a shared repository, CLAUDE.md grows the way any unowned config file does: every team appends its own instructions and **nothing gets deleted**.」（Anthropic 公式ブログ / 2026-06-18）

**なぜ本件（案 2 系）の射程外か**: 誕生ゲートの通貨（§B）は**条項単位**、ゲージ（§A）は**指令数**であり、いずれも**行数を単位にしていない**（台帳 §A の「質量の単位定義」注記が「質量は §A の計器ではない」と明記）。行数を新たな計器として持ち込むことは**帳簿単一原則に触れる**ため、本件の判断には使わない。

**それでも記録する理由**: 上流が「行数 → 遵守率低下」を明言している以上、**LAM が持たない計器で上流が語っている**状態にある。これは誕生ゲートの天井（指令数 80）とは別軸の観測量であり、**採るか採らないかは PM 級の判断**である。

**取りうる手（本文書では選ばない / 列挙のみ）**:

| # | 手 | 備考 |
|:-:|:---|:---|
| 1 | 何もしない | 上流の 200 行は「target」であり閾値ではない。**指示総量の閾値は上流に存在しない**（本文書 §9） |
| 2 | `CLAUDE.md` の節を `.claude/rules/` へ退避 | **R1 内移動であり予算中立**（取引 #9 の前例）。総量は変わらず、`CLAUDE.md` 単体の行数だけが減る = **公式目安の単位に対してのみ効く** |
| 3 | 条件ロード（R2）へ降格できる節を探す | 上流仕様上、**`paths:` は compaction で失効する**（§9 E1）。ゲート設計 §1.2 の 4 要件と §2 決定木を通すこと |
| 4 | 行数を継続計測して推移だけ見る | `InstructionsLoaded` hook（`load_reason` 別）で実測可能。**計器を増やすこと自体が通貨化圧を生む**という既知の懸念（`artifact-length-calibration.md`「常設の数値ゲージは置かない」）と衝突する |

**本件との接点（1 点のみ）**: 案 A は `core-identity.md` §Context Compression（5 行）を `CLAUDE.md` §Context Management へ移すため、**`CLAUDE.md` は 243 → 248 行になる**。話題の所有権を排他にする利得と、目安超過を 5 行広げる不利益のトレードオフであり、**案 A を採る場合はこの 5 行を承知の上で採ることになる**。
