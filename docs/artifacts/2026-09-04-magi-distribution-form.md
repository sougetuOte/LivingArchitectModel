# MAGI: 配布形態の再設計（clone してすぐ使える状態の達成）

**日付**: 2026-09-04（セッション 28）
**モード**: **AoT 適用**（判断ポイント 6 / 影響レイヤー 6 / 選択肢 7）
**等級**: SE 級（`docs/artifacts/`）
**書込権限**: CASPAR（Single-Writer）

## §0 発端と制約

ユーザー質問: 「リリースの度に洗浄するのはよろしくない。clone したらすぐ使えるようにするには？」
明示された制約: **利用者は作者だけではない** / プロジェクト構成の変更も視野 / MAGI + HGA を回す。

### 実測（2026-09-04 / fresh clone from GitHub）

| 項目 | 値 |
|:--|--:|
| 追跡ファイル | 663 |
| うち LAM 固有の記録 | **379（57%）** |
| 配布物コア | 284 |
| fresh clone の pytest | **1268 passed / 3 failed / 20 skipped** |
| 配布物コア内の作者環境ハードコード | **5 件**（うち実働ガード 2 件） |
| LAM 固有識別子を含む rules | **14 / 19 枚** |

### 上流の現況（2026-09-04 / context7 + WebSearch）

- plugin は skills / agents / hooks / commands / MCP を 1 単位で配布し、`${CLAUDE_PLUGIN_ROOT}`（機構）と `${CLAUDE_PROJECT_DIR}`（状態）を**両方 hook プロセスに export** する
- **`.claude/rules/*.md` は project instructions として扱われ、プロジェクト側の `.claude/rules/` から読まれる** → **rules は plugin では配れない**（硬い制約）
- `managed-settings.json` の `claudeMd` は物理ファイルなしで CLAUDE.md 相当を注入できるが **managed scope 限定**（組織配布向け / 個人利用者には使えない）
- 同型の先行例（`Chachamaru127/claude-code-harness`）は `/plugin marketplace add <repo>` → install → `/harness-setup` の 3 手で入る。**clone-template は配布形式として一世代前**

### 既存決定の走査（Step 0 前提 / ADR 11 件 + D-1 成果物）

| 既存決定 | 内容 | 本 MAGI との関係 |
|:--|:--|:--|
| **D-1 / 死んだ案 #5** | **リポジトリ分割は棄却**（ユーザー撤回 + HGA #22「self-hosting は LAM 唯一の QA 機構」） | **拘束する**。分割案は再提出しない |
| **D-1 決定** | 境界は**パッケージング境界**として実装し、リポジトリは割らない | **拘束する**。plugin 化はこの命令に合致 |
| D-1 §2.3 | 現在の配布物 = リポジトリの全内容。ハードコードは 31 リリース全部で配布済 | 前提として引き継ぐ |
| D-1 残余 #1 | **skills / agents / hooks の配布判定は未実施** | 本件で消化しうる |
| D-1 残余 #2 | `_OUTBOUND_WRITE_BAN_ROOTS` の実在検査は置けなかった（hooks がスコープ外） | 本件で消化しうる |
| ADR-0001 | Opus をメインセッション専用に | 影響なし |
| ADR-0008 | 自己責任モデル + 反面教師制約 D1/D4 | 検査設計に効く |

**失効しうる前提**: ユーザーは 2026-07-27 に「**self-hosting は本質ではないので放棄可**」と述べている（L1 記憶 `lam-positioning-and-motive`）。HGA #22 の裁定と**表面上は逆向き**であり、A3 の争点となる。

---

## §1 AoT Decomposition

| Atom | 判断内容 | 依存 |
|:--|:--|:--|
| **A3** | self-hosting を維持するか（D-1 の前提が今も生きているか） | なし（他の前提） |
| **A1** | 配布の器は何か（clone template / dist 生成 / plugin+marketplace / 併存） | A3 |
| **A2** | 規範（CLAUDE.md + `.claude/rules/`）をどう配るか（plugin 不可の制約下） | A1 |
| **A4** | 配布物コアの環境依存・LAM 固有語をどう除去するか | なし |
| **A6** | 既存 `/init-harness` の処分 と コマンド名前空間の破壊的変更 | A1, A2 |
| **A5** | 「clone してすぐ使える」を誰が検査するか | A1, A4 |

---

## §2 Atom A3: self-hosting を維持するか

**[MELCHIOR]**: 放棄すれば全部が楽になる。配布物を薄く保つ最大の障害は「LAM が LAM の上で開発される」ことで、開発すれば必ず `docs/artifacts/` が増え配布物が汚れる。ユーザー自身が 2026-07-27 に「本質ではない」と言っている。利用者が作者だけでない以上、作者の QA 都合より利用者の初回体験を優先すべきだ。

**[BALTHASAR]**: 放棄の代償が見えていない。HGA #22 の裁定は「self-hosting は**原則ではなく唯一の QA 機構**」であり、これは思想ではなく**機能**の指摘だ。LAM には利用者テストも CI もない。self-hosting をやめた瞬間、hooks も rules も skills も**誰も踏まない配布物**になる。今日 fresh clone で 3 件の赤と 5 件のハードコードが見つかったのは、self-hosting が**それを検出できなかった**ことの証拠でもあるが、self-hosting がなければ **1268 件の緑すら存在しない**。
また「本質ではないので放棄可」は「放棄せよ」ではない。ユーザー発言は**放棄の許可**であって**放棄の指示ではない**。許可を指示と読み替えるのは User Intent の拡大解釈だ。

**[MELCHIOR]**: では条件を切り分けよう。self-hosting が守っているのは「機構が実際に踏まれること」であって「配布物と記録が同居すること」ではない。**同居は self-hosting の必要条件ではない**。LAM が自分自身に対して plugin として LAM を適用すれば、self-hosting は維持されたまま同居が解ける。

**[BALTHASAR]**: それは成立する。ただし条件がある —— LAM が使う plugin が**配布されるものと同一の実体**であること。開発用にローカルの別実体を使ったら、それは self-hosting ではなく「似たものを使っている」だけだ。plugin の local install（`--scope project` / `plugins: [{type:"local", path:"./..."}]`）が同一実体を指せるかが分かれ目になる。

**[CASPAR]**: 結論: **self-hosting は維持する。ただし「同居」から「同一実体の local install」へ形を変える。**

D-1 の死んだ案 #5 は今も有効であり、リポジトリ分割は行わない。ユーザーの「放棄可」発言は放棄の**許可**であって指示ではなく、BALTHASAR の指摘どおり LAM には self-hosting 以外の QA 機構が存在しない。一方で MELCHIOR の切り分けは正しい —— **self-hosting が要求するのは「機構が実際に踏まれること」であり、「配布物と記録が同一ディレクトリにあること」ではない**。

したがって A3 の答えは「維持」だが、その維持形態は **同一リポジトリ内の plugin ディレクトリを local install して LAM 自身が使う** とする。これは D-1 が命じた「パッケージング境界として実装し、リポジトリは割らない」と完全に一致する。

**採用しなかった選択肢とその理由**:
- **self-hosting 放棄** → 代替 QA 機構が存在せず、配布物が誰も踏まないコードになる。ユーザー発言は許可であって指示ではない
- **リポジトリ分割** → D-1 死んだ案 #5（再提出しない）
- **現状の同居を維持** → 開発が配布物を汚す構造が残り、洗浄が再発し続ける（本 MAGI の発端そのもの）

---

## §3 Atom A1: 配布の器

**[MELCHIOR]**: plugin + marketplace 一択だ。`/plugin marketplace add sougetuOte/LivingArchitectModel` → `/plugin install lam` の 2 手で入り、`git clone` も `rm -rf .git` も要らない。更新は `/plugin update` で伝播する —— **これは clone-template には原理的に存在しない機能**で、利用者が作者だけでないなら決定的だ。今のやり方だと利用者は v5.1.0 の LAM を clone した瞬間からバージョンが凍る。

**[BALTHASAR]**: 3 つ引っかかる。
1. **rules が配れない**。LAM の規範の核（`.claude/rules/` 19 枚 2497 行）は plugin の対象外で、プロジェクト側に敷く別機構が要る（A2 へ）。plugin だけでは LAM は成立しない
2. **コマンドが名前空間化する**。`/ship` → `/lam:ship` になり、CHEATSHEET・QUICKSTART・スライド・skills 内の相互参照が全部ずれる。今日の「実在しないコマンド 42 箇所」と**同じ型の欠陥を自分で新規に作る**
3. **Python 依存が利用者側に移る**。hooks は `${CLAUDE_PLUGIN_ROOT}` から起動されるが、Python 実行系は利用者マシンのものだ。今は「clone した人が venv を作る」で済んでいるが、plugin だと**入れた瞬間に動く期待**が生まれ、Python 不在で hook が沈黙する

**[MELCHIOR]**: 3 点とも実在する。ただし 1 と 2 は plugin の欠陥ではなく**移行コスト**だ。3 は今も同じで、QUICKSTART が「Python は必須です」と書いている。むしろ plugin なら `${CLAUDE_PLUGIN_DATA}` に依存を置けるので改善余地がある。

**[BALTHASAR]**: 移行コストを軽く見るな。2 は「配布物が実体より強い主張をする」型の欠陥を**大量に一度に**生む。今日 51 箇所直したばかりで、その原因は「コマンドを消したのにドキュメントを直さなかった」だ。名前空間化はそれを全ファイルに対して一斉に起こす。

**[MELCHIOR]**: だから A5（検査）が要る。名前空間化の追随漏れは **`verify_distributable_claims.py` が既に検査している対象そのもの**（コマンド実在検査）で、機構が拾う。むしろ今回は機構がある状態で移行できる**初めての機会**だ。

**[CASPAR]**: 結論: **plugin + marketplace を配布の器として採用する。ただし clone-template を即座に廃止せず、移行期は併存させる。**

理由 3 点:
1. 利用者が作者だけでない前提では、**更新が伝播すること**が clone-template との決定的差になる。現状の利用者はリリース時点の LAM で凍る
2. plugin 化は D-1 が命じた「パッケージング境界」の唯一の上流ネイティブ実装であり、リポジトリを割らずに配布物と記録を分離できる
3. BALTHASAR の 3 懸念は全て実在するが、いずれも**移行作業**であって**採否の否定材料ではない**。特に懸念 2（名前空間の追随漏れ）は R3 機構 #10 が検査可能な対象であり、機構を持つ今が移行の最良時期

併存を置く理由は BALTHASAR の懸念 2 の緩和である。既存利用者の `/ship` が突然消えると、こちらが今日直したのと同じ「存在しないコマンドの参照」を利用者の手元で発生させる。

**採用しなかった選択肢とその理由**:
- **clone-template の維持（現状）** → 更新が伝播せず、洗浄が再発し続ける
- **dist ディレクトリの機械生成** → 除外リスト = 維持リストの保守が生じる。LAM が最も嫌う型（R3 機構 #7 で「維持リストを持たず基質から導出」を採ったのと逆行）
- **npm / degit 等の別配布系** → Claude Code の外の依存を増やす。plugin が上流ネイティブにある以上、採る理由がない
- **plugin 即時単独化（clone 廃止）** → 既存利用者に破壊的。移行期を置かない理由がない

---

## §4 Atom A2: 規範（CLAUDE.md + rules）の配り方

**[MELCHIOR]**: plugin 内に `/lam:init` skill を置き、それがプロジェクト側に `CLAUDE.md` と `.claude/rules/` を敷く。テンプレートは plugin 内に持つので、**本体と drift しない**（`${CLAUDE_PLUGIN_ROOT}` から読む）。今の `init-harness` が本体と drift している原因は、テンプレートをインライン文字列で二重に持っていることだ。

**[BALTHASAR]**: それは正しいが、**rules をコピーした瞬間に更新が止まる**ことを見落とすな。plugin 本体は `/plugin update` で更新されるのに、プロジェクトにコピーされた rules 19 枚は**利用者の手元で凍る**。clone-template の欠点を rules だけが引き継ぐ。しかも rules は LAM の規範の核だ —— 一番古びてほしくないものが一番古びる。

**[MELCHIOR]**: rules は**利用者がカスタマイズする対象**でもある。凍るのは仕様とも言える。

**[BALTHASAR]**: 両方ではありえない。「更新されるべき基盤」と「カスタマイズされる利用者の資産」は同じファイルには置けない。今の LAM の rules は 14/19 枚に LAM 固有識別子が入っていて、この区別を一度もしていない。

**[CASPAR]**: 結論: **`/lam:init` が rules をプロジェクトへ敷く。ただし rules を「基盤」と「プロジェクト固有」の 2 層に分け、基盤層のみ再敷設可能（idempotent な上書き）とする。**

BALTHASAR の指摘が本質的である。現在の rules 19 枚は 2 種類が混ざっており（基盤 = `permission-levels` / `phase-rules` / `core-identity` / `code-quality-guideline` 等、LAM 固有 = `hga-summoning` / `model-roster` / `terminology` の LAM 用語部 等）、この未分離が「14/19 枚に LAM 固有語」の実測値そのものである。

2 層に分けることで:
- 基盤層は `/lam:init --update` で再敷設でき、更新が届く
- プロジェクト固有層は利用者の資産として触らない
- **A4（環境依存の除去）が A2 の副産物として構造化される** —— どの rules が配布物かを決める作業と、LAM 固有語を抜く作業は同じ作業になる

**採用しなかった選択肢とその理由**:
- **`managed-settings.json` の `claudeMd`** → managed scope 限定で個人利用者に届かない
- **rules を plugin に置いて CLAUDE.md から絶対パス参照** → plugin の install path は更新で変わる（公式が「persistent state を置くな」と明記）。参照が壊れる
- **rules をコピーせず「plugin を入れれば規範も効く」とする** → 上流仕様上、不可能（rules は project から読まれる）
- **単層コピー（現状の延長）** → 規範の核が利用者の手元で永久に凍る

---

## §5 Atom A4: 配布物コアの環境依存・LAM 固有語の除去

**[MELCHIOR]**: 実測が出ている。ハードコード 5 件のうち実働は 2 件（`_OUTBOUND_WRITE_BAN_ROOTS` / `_OUTBOUND_WRITE_ALLOW_ROOTS`）。これらは**作者の別プロジェクトを守るための私的なガード**であり、利用者には無意味どころか「動いているように見えて何も守らない死んだコード」だ。設定ファイルへ追い出せばよい。

**[BALTHASAR]**: **それは D-1 で MAGI が既に否決した案だ**（死んだ案 7 件 / `2026-07-27-magi-outbound-ban-path.md`）。「パスだけ直す（兄弟導出 / 設定ファイル化 / 条文パース）」は「沈黙の条件をずらすだけで消さない」として棄却されている。同じ案を別 MAGI で通すのは、決着済みの判断の蒸し返しだ。

**[MELCHIOR]**: 前提が変わっている。あの否決は「LAM リポジトリ内で当該ガードをどう表現するか」の議論だった。今は**配布物とプロジェクトの層が分かれる**という新しい選択肢がある。当該ガードは「作者のプロジェクト固有 rules」であり、**A2 の 2 層分離で言えばプロジェクト固有層に属する** —— 配布物から抜くのであって、設定ファイル化するのではない。

**[BALTHASAR]**: それなら通る。ただし**抜いた後にガードが消えないこと**を保証しろ。作者の環境では今も生きている必要がある（Fable-Alembic への誤書込は実際に防ぎたい事象だ）。

**[CASPAR]**: 結論: **配布物コアからは抜き、作者のプロジェクト固有層に残す。「設定ファイル化」ではなく「層の帰属変更」として実施する。**

D-1 の否決（死んだ案）と矛盾しないことを明示する —— 否決されたのは**単層前提での表現変更**（同じ層の中でパスの書き方を変える）であり、本結論は**層そのものを分ける**。前提条件が異なるため蒸し返しには当たらない。ただしこの判定は境界的であり、**gabriel の検証対象として明示する**。

LAM 固有語（14/19 枚）については A2 の 2 層分離で自動的に処理される。`terminology.md`（LAM 固有語 25 件）は丸ごとプロジェクト固有層、`hga-summoning.md` / `model-roster.md` は作者の課金体制に依存するため同じくプロジェクト固有層とする。

**採用しなかった選択肢とその理由**:
- **設定ファイル化 / 兄弟導出 / 条文パース** → D-1 で否決済（死んだ案 7 件）。単層前提の案であり再提出しない
- **ハードコードのまま配る** → 31 リリース続けてきた現状。利用者には死んだコード
- **ガードごと削除** → 作者環境で実際に防ぎたい事象が防げなくなる

---

## §6 Atom A6: `/init-harness` の処分 と 名前空間の破壊的変更

**[MELCHIOR]**: `init-harness` は**廃止して `/lam:init` に置換**すべきだ。実測で 2 つの欠陥がある —— (a) rules / hooks / agents / settings.json を一切配らないのに「三フェーズ規律 + Three Agents Model を適用する」と名乗る、(b) `.claude/current-phase.json` を生成するが hook が読むのは `.md` なので**初期状態でガードが沈黙する**。直すより置換が速い。

**[BALTHASAR]**: 廃止には同意するが、(b) は**単なる drift ではなく重大**だ。init-harness を信じて使った利用者は、ガードが一切効かない状態で「ハーネスを適用した」と信じている。これは今日掃除した「存在の主張」型の中で最も害が大きい部類で、**優先度は plugin 化より上**の可能性がある。plugin 化は数週間かかるが、これは今すぐ直せる。

**[MELCHIOR]**: 名前空間については、`/lam:ship` への移行は CHEATSHEET / QUICKSTART / スライド / skills 相互参照の全域に及ぶ。ただし**機械検査が既にある**（`verify_distributable_claims.py` のコマンド実在検査）ので、追随漏れは検出される。

**[BALTHASAR]**: その検査は「LAM リポジトリ内のドキュメントが LAM 内のコマンドを正しく参照しているか」を見ている。plugin 名前空間の参照を検査対象に含める改修が要る。**検査が自動で追随すると思うな**。

**[CASPAR]**: 結論: **(1) `init-harness` の欠陥 (b) は plugin 化を待たず即時修正する。(2) `init-harness` 自体は `/lam:init` に置換して廃止する。(3) 名前空間移行は検査の改修とセットでのみ実施する。**

BALTHASAR の優先度指摘を採る。欠陥 (b) は「ガードが沈黙する初期状態を配っている」ことであり、plugin 化という数週間の作業の後ろに置く理由がない。分離して先行させる。

**採用しなかった選択肢とその理由**:
- **`init-harness` を直して残す** → plugin 内 `/lam:init` と二重の配布経路が残り、drift が再発する（現に今 drift している）
- **名前空間を避けるため plugin を使わない** → A1 の結論を覆す
- **検査改修を後回しにして先に移行** → 今日直した 42 箇所と同じ型を自分で作る

---

## §7 Atom A5: 「clone してすぐ使える」を誰が検査するか

**[MELCHIOR]**: 今日 L1 が手でやったこと（GitHub から clone → pytest）をそのまま機構化する。R3 機構 #11 として `/release` の前提条件に入れれば、リリース毎に「配布物が成立するか」が機械判定される。

**[BALTHASAR]**: 2 点。(a) fresh clone のテストは**環境依存で赤くなる**（今日の 3 件のうち `test_parse_with_real_git_log` は履歴依存、outbound ban 2 件は配置依存）。検査自体が誤検知すれば「常時落ちる計器は殺される」型に直行する —— `conftest.py` の除外理由が先回りで警告している通りだ。(b) plugin 化後は検査対象が変わる（clone ではなく install）。今作ると作り直しになる。

**[MELCHIOR]**: (a) は検査の設計次第だ。「fresh clone で全緑」ではなく「**環境依存で落ちるテストが列挙されたリストと一致する**」を検査すればいい。(b) は plugin install の検査に置き換わるが、**移行期は両方要る**。

**[BALTHASAR]**: 「列挙されたリストと一致」は**維持リスト**だ。A1 で dist 生成案を「維持リストだから」と却下したのに、ここで維持リストを導入するのは一貫性がない。

**[CASPAR]**: 結論: **検査は置く。ただし維持リスト方式を避け、「環境依存を検出する」検査として設計する。**

BALTHASAR の一貫性指摘を採る。「落ちてよいテストの名簿」ではなく、**配布物コアに環境依存が含まれていないこと自体を検査する**（絶対パスリテラル / 作者名 / 特定リポジトリ名の混入検出）。これは基質から導出する検査であり、R3 機構 #7 / #10 と同型で維持リストを持たない。

fresh clone smoke そのものは**リリース時に 1 回走らせる補助**として残すが、その合否は「全緑」ではなく「**前回リリースからの退行がないこと**」で判定する。

**採用しなかった選択肢とその理由**:
- **fresh clone 全緑を必須条件にする** → 環境依存テストで常時落ちる計器になり、殺される
- **落ちてよいテストの名簿を持つ** → 維持リスト（A1 で却下した型と同じ）
- **検査を置かない** → 今日見つけた 5 件のハードコードが次も 31 リリース続く
- **plugin 化まで検査を作らない** → 移行期こそ最も壊れやすい

---

## §8 CASPAR 統合結論（Step 3 完結 / gabriel 検証前）

| Atom | 結論 |
|:--|:--|
| **A3** | self-hosting は**維持**。ただし「同居」から「**同一リポジトリ内 plugin の local install**」へ形を変える。リポジトリ分割は行わない（D-1 死んだ案 #5 を尊重） |
| **A1** | **plugin + marketplace を採用**。clone-template は移行期のみ併存 |
| **A2** | 規範は plugin 内 `/lam:init` がプロジェクトへ敷く。**rules を基盤層 / プロジェクト固有層の 2 層に分離**し、基盤層のみ再敷設可能とする |
| **A4** | 環境依存・LAM 固有語は「設定ファイル化」ではなく「**層の帰属変更**」で除去（D-1 否決案とは前提が異なる / **要 gabriel 検証**） |
| **A6** | `init-harness` の欠陥 (b)（`current-phase.json` でガードが沈黙）は**即時修正**。skill 自体は `/lam:init` に置換して廃止。名前空間移行は検査改修とセット |
| **A5** | 「配布物コアに環境依存が含まれない」ことを**基質から検査**（維持リストなし）。fresh clone smoke は退行検出の補助 |

**実施順序**（依存に従う）:

```
0. init-harness 欠陥 (b) 即時修正        ← 独立・最優先（ガードが沈黙している）
1. A4/A2: rules の 2 層分離 + 環境依存の帰属変更
2. A5: 環境依存検査（R3 機構 #11）
3. A1/A2: plugin 骨格 + /lam:init
4. A6: 名前空間移行 + 検査改修 + ドキュメント追随
5. clone-template の廃止判断（移行期の終了）
```

---

## §9 gabriel probe（第 1 回）

- **verdict**: `refuted` / **severity**: `critical` / **confidence**: 0.62
- **affected_atoms**: A1, A2, A3, A4
- **recommended_action**: `re-magi`
- **処理**: AC-W-C-5 に従い**再 MAGI 1 ラウンド**を実施（§10）。CASPAR 結論を破棄し、gabriel.reasoning を Divergence 入力に追加

**指摘 3 件（要約）**:

1. **A3 の引用が不正確** —— `lam-positioning-and-motive` の「self-hosting 放棄可」は frontmatter の description のみであり、**本文で同日中に撤回されている**（「配布するために出来が悪いものを使うのは本質ではない」「self-hosting を捨てると製品を試せなくなる」）。提示した対立は実在しない。結論（維持）は正しいが前提が誤りで、後続が「未決の対立」と誤読する危険
2. **A4 が hooks を扱えていない** —— 「層の帰属変更」は A2 の rules 2 層分離に依拠するが、A2 が扱うのは `.claude/rules/*.md` のみ。実際にハードコードがあるのは `pre-tool-use.py`（Python コード）で、**その層分離機構は未設計**。D-1 残余 #2 が未消化のまま消化済みと記録されうる
3. **依存宣言と実施順序が矛盾** —— §1 は A2→A1 / A5→A1,A4 と宣言しながら、§8 の順序は A1（step 3）より前に A2 / A5 を置く。概念依存と実装依存の区別が無説明
4. （自己申告）**gabriel は WebFetch / context7 を持たないため §0 の上流主張を一次資料で再検証できなかった**

**L1 による事実確認**（再 MAGI の入力として）:

| # | 判定 | 根拠 |
|:-:|:--|:--|
| 1 | **指摘は正しい。L1 の誤り** | 記憶ファイル本文を実読。撤回済であることを確認 |
| 2 | **指摘は正しい。ただし「蒸し返し」ではない** | `2026-07-27-magi-outbound-ban-path.md` の結論は「現状維持」ではなく「**根は配布境界にある**」と特定して D-1 へ送ること。D-1 は残余 #2 で「hooks を対象に含む後続 Milestone」へ再送済。**本 MAGI がその宛先である**。ただし機構未設計という指摘自体は妥当 |
| 3 | **指摘は正しい**（ただし A5 については後述の反論あり） | — |
| 4 | **L1 側で裏取り済**（§10 冒頭に追記） | context7 で確定 |

---

## §10 再 MAGI（ラウンド 1 / 上限 1 回・AC-W-C-7）

### §10.0 追加入力

**(i) 上流の追加裏取り**（gabriel の指摘 4 に対応 / context7 / 2026-09-04）:

- **plugin のコンポーネント在庫は Skills / Agents / Hooks / MCP servers / LSP servers の 5 種**（`claude plugin details` の出力仕様）。**`rules` は存在しない** → §0 の制約は確定
- **plugin hooks は `<plugin>/hooks/hooks.json`**、**プロジェクト hooks は `.claude/settings.json`** に**別々に登録される**（両者は同一スキーマ）→ **A4b の解に直結**
- plugin skills は `/plugin-name:skill-name` で名前空間化される（公式例 `/quality-review-plugin:quality-review`）
- `${CLAUDE_PLUGIN_ROOT}` / `${CLAUDE_PLUGIN_DATA}` / `${CLAUDE_PROJECT_DIR}` は hook プロセス・MCP・LSP に export され、skills / agents / commands 内でもインライン解決される
- **未実測**: plugin hook と project hook が**同一イベントで両方発火するか**（ドキュメントは明示していない。**A4b の成立条件であり実測必須**）

**(ii) 記憶本文から回収した拘束条件**（A3 の訂正に伴い発見 / これまでの合議に入っていなかった）:

| # | 条件 | 効く先 |
|:-:|:--|:--|
| **C1** | **「配布は上流に立てない。配布可能性を理由に自分の道具を劣化させる決定はすべて誤り」** | **A6**（名前空間移行は作者の道具の劣化にあたりうる） |
| **C2** | **不変条件: 配布集合 ⊆ 開発ロード集合。私的規範は「追加」のみ許し「置換」を許さない** | **A2 / A4**（2 層分離の形を規定する） |
| **C3** | 「self-hosting は唯一の QA 機構。**smoke test / installer E2E が検証できるのはインストール可否だけ**」 | **A5**（検査の射程を先回りで限定している） |
| **C4** | 境界は**パッケージング境界**（`init-harness` のマニフェスト）で実装する | A1 / A6 |

---

### §10.1 Atom A3'（訂正）: self-hosting

**[CASPAR]**: 結論: **self-hosting は維持する。争点は存在しない。**

前回 §2 が提示した「ユーザー発言と HGA #22 の対立」は **L1 の引用誤りによる幻の争点**であり、削除する。ユーザーは 2026-07-27 に一度「曲げてよい」と述べ、**同日中に自ら撤回**している。したがって A3 に MELCHIOR / BALTHASAR の対立は不要であり、**維持は既決事項**として扱う。

維持形態についての前回の判断（「同居」→「同一リポジトリ内 plugin の local install」）は **C2 に照らして再検証が必要**である。C2 は「配布集合 ⊆ 開発ロード集合」を要求する —— LAM 自身が local install した plugin を使う限りこれは満たされる（配布される実体そのものを開発でロードする）。**むしろ現状より C2 への適合が上がる**（現状は配布集合 = 開発集合で等号だが、私的規範が「追加」ではなく配布物に混入している = C2 の後半に違反している）。

**採用しなかった選択肢**: self-hosting 放棄（ユーザー撤回済 / 再提出しない）/ リポジトリ分割（D-1 死んだ案 #5）。

---

### §10.2 Atom A4'（分割）: 環境依存の除去

gabriel の指摘 2 を受け、A4 を性質の異なる 2 つに分割する。

#### A4a: rules / ドキュメントの LAM 固有語（14/19 枚）

**[CASPAR]**: 結論: **前回の結論を維持**（A2 の 2 層分離の副産物として処理）。ただし **C2 により形が確定する** —— 基盤層は配布物であり開発でも必ずロードされる。LAM 固有 rules は基盤層への**追加**であって置換ではない。`terminology.md` の LAM 用語部・`hga-summoning.md`・`model-roster.md` は追加層に置く。

#### A4b: hooks の私的ガード（`pre-tool-use.py` の 2 定数）

**[MELCHIOR]**: §10.0(i) が新しい解を出した。**plugin hooks と project hooks は別ファイル・別登録**である。したがって:

- 配布される `pre-tool-use.py` は plugin 側（`${CLAUDE_PLUGIN_ROOT}/hooks/`）に置き、**`_OUTBOUND_WRITE_BAN_ROOTS` を持たない**
- 作者の私的ガードは **LAM リポジトリの `.claude/settings.json` に追加の hook エントリ**として登録し、project-local なスクリプトが担う
- これは C2 の「**追加のみ許し置換を許さない**」に厳密に一致する。配布物の hook を書き換えるのではなく、その横にもう 1 本足す

**2026-07-27 の死んだ案 7 件のいずれにも該当しない**: 兄弟導出でも設定ファイル化（`settings*.json` に**パスを書く**案）でもない。settings.json に書くのは**フックの登録**であって**パスの値**ではなく、パスは project-local スクリプト内のリテラルとして残る（= ハードコード維持という A1 の生きた結論を保存する）。

**[BALTHASAR]**: 3 つ突く。

1. **`settings.json` は AI 編集不可**（記憶 `settings-json-edit-blocked` / auto-mode ハードブロック）。死んだ案の「設定ファイル化」が殺された理由の半分はこれだ。hook 登録の追加も同じ壁に当たる
2. **両方発火するかが未実測**。plugin hook が project hook を上書きする実装なら、この案は根本から成立しない
3. **沈黙は消えたのか**。project-local スクリプトが消えれば静かにガードが消える。2026-07-27 の中核的判定「**沈黙は導出方式を変えても消えない —— 条件がずれるだけ**」に、この案も当たるのではないか

**[MELCHIOR]**: 1 は手順の問題で、案の否定ではない（PM が手で 1 回書く / 記憶にある 3 手順 = 案提示 → PM 手動 → AI 検証）。2 は**実測すればよい**。3 が本質的な問いだ。

**[BALTHASAR]**: 3 に答えろ。答えられないなら A4b は前回と同じ「決めたつもり」になる。

**[MELCHIOR]**: 答えは「**沈黙は消えないが、沈黙の検出責任が配布物から作者の環境へ移る**」だ。現状の沈黙が問題なのは、**配布物の中に沈黙する機構がある**ことで、利用者は「動いているように見えて何も守らないコード」を受け取る。分離後は、配布物には当該ガードが存在しないので**利用者側に沈黙は生じない**。作者側の沈黙は残るが、それは**既に対策済**である —— 2026-07-27 の Action Item 1 が実装した所有者ゲートつき実在検査（`SESSION_STATE.md` の存在をゲートとし、vacuous でないことの対照検査つき）がそれを拾う。**検査を作者側の層へ一緒に移せばよい**。

**[CASPAR]**: 結論: **A4b は「plugin 層 / project 層への分離」で解く。ただし成立条件 2 件を実測で確認するまで確定しない。**

MELCHIOR の反論を採る。2026-07-27 の判定「沈黙は消えない」は**単層前提での判定**であり、本案は沈黙を消すのではなく**沈黙の所在を配布物の外へ出す**。利用者から見た害（死んだガードを受け取る）は消え、作者側の沈黙は既存の所有者ゲート検査が担う。

BALTHASAR の懸念 1・2 は**成立条件**として明示する:

| 条件 | 内容 | 確認方法 |
|:--|:--|:--|
| **G1** | plugin hook と project hook が**同一イベントで両方発火する** | 実測（canary） |
| **G2** | `settings.json` への hook 追加登録が PM 手動経路で実施可能 | 既知（3 手順） |

**G1 が偽なら A4b は不成立**であり、その場合は「配布物コアにハードコードを残したまま、検査（A5）で新規混入のみ止める」に後退する（**劣後案として明記**）。

**採用しなかった選択肢**: 死んだ案 7 件（再提出しない）/ ガードごと削除（作者環境で防ぎたい事象が防げない）/ 前回の「層の帰属変更」（機構未設計のまま = gabriel 指摘 2）。

---

### §10.3 Atom A6'（訂正）: 名前空間と C1

**[BALTHASAR]**: C1 が新しく効く。「**配布可能性を理由に自分の道具を劣化させる決定はすべて誤り**」——`/ship` が `/lam:ship` になるのは、作者の日常操作の劣化だ。配布のためにそれを飲むのは C1 の禁止に正面から当たる。

**[MELCHIOR]**: 劣化と言えるか。3 文字増えるだけだ。

**[BALTHASAR]**: 判定は L1 の主観ではなくユーザーの原則に属する。C1 は「配布は上流に立てない」と書いてある。**この判定はユーザーに返すべき事項**だ。

**[CASPAR]**: 結論: **名前空間の受容可否は PM 級としてユーザーに返す。L1 は決めない。**

C1 はユーザー自身が立てた優先順位の原則であり、「3 文字なら劣化ではない」という判定を L1 が代行するのは越権である。A6 の他の部分（`init-harness` 欠陥 (b) の即時修正 / `/lam:init` への置換 / 検査改修とセットにする条件）は**不変**とする。

**採用しなかった選択肢**: L1 判断で名前空間を受容（C1 に抵触）/ 名前空間を避けるため plugin を採らない（A1 を覆す / 費用対効果が逆）。

---

### §10.4 Atom A5'（訂正）: 順序と C3

**[CASPAR]**: 結論: **検査の内容は前回どおり。順序は「検査が先」で正しく、これは矛盾ではなく TDD の Red-Green である。**

gabriel の指摘 3 は A2 については正しいが、A5 については**反論する**。「配布物コアに環境依存が含まれない」検査を A4 の除去より**先**に置くのは、LAM 自身の BUILDING 規律（Red → Green → Refactor）に従った結果であり、依存の取り違えではない。§1 の依存表が「A5 は A1, A4 に依存」と書いたのが不正確で、正しくは **A5 は A4 の完了に依存しない**（検査を先に置き、赤い状態から緑にする）。依存表を訂正する。

C3（「smoke test が検証できるのはインストール可否だけ」）はユーザーが先回りで書いた射程限定であり、**A5 の位置づけと一致する** —— A5 は製品価値を検証しない。「配布物に環境依存が混入していないこと」だけを見る。この限定を A5 の定義に明記する。

---

### §10.5 CASPAR 統合結論（再 MAGI 後 / Step 3 完結）

| Atom | 結論 | 前回からの変更 |
|:--|:--|:--|
| **A3'** | self-hosting **維持**（既決 / 争点なし）。形態 = 同一リポジトリ内 plugin の local install | **争点の記述を削除**（L1 の引用誤り） |
| **A1** | **plugin + marketplace 採用**。clone-template は移行期併存 | 不変 |
| **A2** | `/lam:init` が規範をプロジェクトへ敷く。rules を**基盤層 / 追加層**に分離（**C2: 追加のみ・置換不可**） | C2 により形を確定 |
| **A4a** | rules / ドキュメントの LAM 固有語は追加層へ | 不変 |
| **A4b** | hooks の私的ガードは **plugin 層 / project 層の分離**で解く。**成立条件 G1（両方発火）の実測が必要**。偽なら劣後案へ後退 | **新規**（前回は未設計） |
| **A6'** | `init-harness` 欠陥 (b) 即時修正 / `/lam:init` へ置換。**名前空間の受容可否は C1 により PM 級でユーザーへ返す** | **名前空間を L1 判断から外した** |
| **A5'** | 「配布物コアに環境依存が含まれない」ことを基質から検査（維持リストなし）。**射程は C3 のとおりインストール可否相当に限定**。順序は検査が先（Red→Green） | 依存表を訂正 |

**実施順序（訂正版）**:

```
0. init-harness 欠陥 (b) 即時修正           ← 独立・最優先（ガードが沈黙する初期状態を配っている）
1. G1 の実測（plugin hook と project hook の同時発火 canary）  ← A4b の成立条件
2. A5': 環境依存検査を置く（Red で構わない）
3. A4a/A2: rules の基盤層 / 追加層の分類（plugin 不要・分類のみ）
4. A1: plugin 骨格 + marketplace.json + local install で self-hosting を切替
5. A2/A4b: /lam:init 実装 + hook の層分離（G1 が真の場合）→ A5' が緑になる
6. A6': 名前空間の PM 判断 → 検査改修とセットで移行
7. clone-template 廃止判断（移行期の終了）
```

---

## §11 gabriel probe（第 2 回）

- **verdict**: `refuted` / **severity**: `critical` / **confidence**: 0.72
- **affected_atoms**: A4b, A2, A6
- **recommended_action**: **`abort`**
- **処理**: 分岐優先順位 `abort > critical+re-magi` に従い、**再 MAGI を行わず即時人間エスカレーション**。MAGI 結論を**「保留」**として記録する。同時に **AC-W-C-7（2 回目の critical refute / 再 MAGI 上限到達）**にも該当し、両経路が同じ宛先を指す

> [ABORT by gabriel]: 即時人間判断必須。MAGI 結論を「保留」として記録し、人間（L1 統括）の対応を待つ。

**指摘（要約）**:

1. **A4b が D-1 design §5 決定 D4 の波及先 4 点のうち 1 点しか扱っていない**
2. **`docs/private/` へ移された条文が「ロード対象外」のまま全クローンへ複製され続けている**扱いが未定義
3. 前回指摘 3 のうち **A2 部分の訂正が示されず**、暗黙の step 分割に委ねられた（A5 部分の反論は妥当と評価）
4. **A6' の PM 級エスカレーションが「見せかけの伺い」になりうる** —— A1 で plugin を採用した時点で名前空間化は上流仕様上不可避であり、選択肢が消えた後に是非を問うことになる

### L1 による一次資料での検証（**全件裏付けられた**）

**指摘 1**: `docs/specs/d-1-distribution-boundary/design.md` §5 決定 D4 を実読。波及先 4 点が明記され、さらに**目標状態が定義されている**:

| 波及先 | 内容 |
|:--|:--|
| `.claude/hooks/pre-tool-use.py` | `_OUTBOUND_WRITE_BAN_ROOTS` は `fable-l3-protocol.md` §2 を SSOT とする |
| `.claude/tests/hooks/test_outbound_write_ban.py` | `test_banned_root_matches_rule_document` が条文の存在と内容に依存 |
| `.claude/tests/rules/test_clause_gate_ledger.py` | R1 集合を実測して台帳 §A と突合（ファイルが減れば §A も動く） |
| `docs/artifacts/clause-gate-ledger.md` §A | 同上 |

> 「無条件検査が置ける条件は『**hook・テスト・条文がすべて配布物から外れる**』ことであり、それは **hooks を対象に含む後続 Milestone の仕事**である」

**§10.2 の A4b は hook 1 点のみを設計していた。** 目標状態が既に一次資料で定義されているのに、それを参照せずに再設計した。指摘 1 は正当。

**指摘 4**: 正当。A1（plugin 採用）と A6'（名前空間の是非をユーザーへ）の順序が逆である。plugin を採ると skills は `/plugin-name:skill-name` に名前空間化されるため、**A1 を決めた時点で A6' の答えは決まっている**。C1（配布可能性を理由に道具を劣化させるな）を持ち出すなら、**A1 の採否そのものに掛けるべき**であった。

### 保留となった結論（人間判断待ち）

§10.5 の統合結論は**確定していない**。特に以下 3 点が未解決:

- **U1**: `fable-l3-protocol.md` を含む「hook・テスト・条文」の一括除去をどう設計するか（D4 の 4 波及先 + 逆依存 12 参照）
- **U2**: 名前空間化の受容可否を **A1 の前に**問い直すか。あるいは名前空間化を回避する構成があるか
- **U3**: `docs/private/` の条文が配布され続けている現状の扱い

### 実施順序 0（`init-harness` 欠陥 (b)）について

**この 1 件は保留の対象外とする。** gabriel は 2 巡とも A6 の「`init-harness` が `current-phase.json` を生成し、hook が読む `.md` と食い違うためガードが沈黙する」という事実認定を**実装突合で正確と確認**しており（第 1 回の JSON 外補足）、争点になっていない。保留は「配布形態の設計」に対するものであり、既存の壊れた配布経路の修理を止める理由はない。

---

## §12 HGA 召喚（#25）

**ゲート**: 条件 1（gabriel が `refuted & critical` を 2 回 = AC-W-C-7 到達 / 人間エスカレーション経路）+ 条件 3（ユーザーの明示指示）

ブリーフと結果は §13 に追記する。

---

## §13 HGA 結果（召喚 #29 / 2026-09-04）

> safety routing による降格の兆候なし（HGA 自己申告 / ブリーフに cybersecurity・bio 領域を含まず）。tool_uses 4 / 索引 push から一次資料を実読。

### §13.1 中核の指摘: **gabriel の 3 指摘は 1 つの誤判定の症状である**

**D-1 は `fable-l3-protocol.md` を S（要分割）の典型例として名指ししながら、判定は X（丸ごと私物）を出した。**

design §4（S を認める理由 / **逐語**）:

> 例えば `fable-l3-protocol.md` は、外部リポジトリのパス（私物）と、自己監査 14 項目・体験シミュ・F0-F4（**LAM の製品価値の中核**）が同居している。2 値判定を強制すると「**製品の中核を私物として捨てる**」か「私物を配り続ける」の二択になり、**どちらも誤りである**。

**L1 による一次資料検証（全件裏付け済 / 2026-09-04）**:

| 主張 | 検証 |
|:--|:--|
| design §4 が S の典型例として名指し | **真**（design.md:105 逐語一致） |
| 私的記述は 243 行中 25 行（10%） | **真**（`d-1-evidence-2026-07-28.md` §3-8 / 内訳 19+24+0+0+1） |
| 判定は X | **真**（evidence 集計: P 9 / **X 1 = 本ファイル** / S 5） |
| S 機構は他 5 件に適用済 | **真**（`CLAUDE.md` / `core-identity.md` / `hga-summoning.md` / `permission-levels.md` / `phase-rules.md`） |
| 製品側 12 参照は §5・§6・§7・§9 を指す | **真**（実測: §5.1 / §5.4 / §6.1 / §6.2 / §6.7 / §7 / §9） |
| §0-§2 を指すのは hook とテストの 2 点のみ | **真**（実測） |

**すなわち D-1 は、自分の設計書が「誤り」と名指しした 2 択のうち「製品の中核を私物として捨てる」側の結果を出した。**

帰結:
- **U1 の「逆依存 12 参照」は逆依存ではない**。製品中核が私物ファイルに紛れて配布境界の外へ出たことの表れ。**分割すれば自然に解消する**（付け替え不要）
- **U3 の「無効なのに配られている」も誤り**。配られているものの 9 割は製品中核
- **CHANGELOG 先頭の事故（2026-08-29 / 実況発火点の `PLANNING` 修飾脱落）がこの誤判定の最初の実害**。正本が非ロード側にあったため drift した
- **第一手は plugin ではなく、D-1 が自分で予告した S を遅れて実行すること**。これは D-1 の再開ではなく **design §4 の判定手順の未完了ステップ**として扱える（新 Milestone 不要 / 台帳の増減は §A テストが拾う既存設計）

### §13.2 L1 の到達点 1-4 への判定

| # | 判定 | 追加された分岐 |
|:-:|:--|:--|
| 1（plugin 採用） | **同意。ただし「配布」の定義を先に固定せよ** | 「ディスクに届く bytes」か「有効化される集合」か。K1（リポジトリ分割棄却）の下で bytes 遮断は原理的に不可能なので、**「配布 = 有効化される集合」以外に一貫した立場はない** |
| 2（`/lam:init`） | **同意。ただし分岐が 2 つ足りない** | **(a)** `docs/internal/00-07`（Hierarchy of Truth 第 2 位）は plugin の 5 コンポーネントに無い。init が敷くか、テンプレートから参照を消すかの二択 / **(b) Layer 1（`settings.json` の deny）は plugin でも init でも届かない**。「入れた瞬間に使える」の射程は Layer 0 + Layer 2 まで。**隠すと今日直した「存在の主張」型をまた作る** |
| 3（2 層分離） | **分岐の置き方が誤り** | **層は 3 つ**（managed / starter / 私物）。かつ **starter → managed の昇格は利用者の編集を破壊するため事実上不可逆**。「小さく始めて後で広げる」は逆で、**v1 の managed 集合は将来更新したいものを全部含む側に倒す**のが安全 |
| 4（hook 層分離） | **同意。ただし本当の障壁は別** | **Python ランタイムと bash**。`py_invoke.sh` の venv-first はプロジェクト直下 `.venv` 前提。不在時の挙動が沈黙なら init-harness 欠陥 (b) と同型、警告なら K6 が棄却した UX 破壊。**init に置くのが唯一 K6 に触れない置き方**（一度きり・利用者起動・対話的） |

### §13.3 U1 / U2 / U3 の解

**U1**: 分割線は **§2 | §3 の 1 本**。§0-§2（25 行 = パス・L3 宣言・ban SSOT）は `docs/private/` に残し、hook + テストと**一緒に** project 層へ。§3-§9（約 218 行 = 製品中核）は製品側へ戻す。戻し先 3 択のうち **HGA 推奨は「`docs/internal/` に第 2 位 SSOT として置き、`phase-rules.md` を実行時要約に据える」**（通貨 0 / `decision-making.md` ↔ `docs/internal/06` の既存パターンと同型）。条件: **§3-§9 は一体で動かす**（条文 §3「半分だけの移植は移植しないより悪い」= ユーザー veto 領域）。

**U2**: **実施順序が「見せかけの伺い」を構造的に作っていた** —— local install への切替（順序 4）が PM 判断（順序 6）より前にあり、切替の瞬間に作者の `/ship` は変わる。**PM 判断を切替の前に置くだけで解消**。問いの形も変える —— 「`/lam:ship` を受容するか」ではなく「**手打ち skill をどこに置くか**」。手打ちは `/ship` `/quick-save` `/quick-load` `/retro` `/magi` 程度の**小集合**であり、description 起動の skill に名前空間は見えない。

> **V1（plugin skill は接頭辞なしで起動できるか）は L1 が即日検証し、偽と判定**。本セッションの Skill ツール契約が「Plugin skills use `plugin:skill`」と明記し、実ロード中の plugin skill は全て接頭辞つき（`hookify:help` / `engineering:debug` / `anthropic-skills:docx` 等）。**U2 は消滅せず生きている。**

**U3**: 「解く」対象ではなく「**定義の帰結として消える**」対象。配布 = 有効化される集合と定義すれば `docs/private/` は clone 期でも配布されていない。**untrack は誤り**（§2 は hook の SSOT でテストが読む / 外すと self-hosting の QA から外れる = K2 違反）。

### §13.4 名指しされた不可逆な決定 5 点（**§10.5 の順序に 1 つも現れていなかった**）

| # | 不可逆点 | なぜ巻き戻せないか |
|:-:|:--|:--|
| **I1** | **v1 の managed 集合の中身** | starter → managed の昇格は利用者の編集を壊す。一度 starter で出したファイルは二度と更新対象にできない。**名前空間より巻き戻せない** |
| **I2** | **plugin 名 = 名前空間接頭辞** | 全利用者の呼び出し面と全ドキュメントに固定。改名は破壊的変更 |
| **I3** | **marketplace の所在 = リポジトリ URL** | 利用者が `marketplace add` した URL は移せない。K1 の下で後から別リポジトリへは不可能。**最初の URL が最後の URL** |
| **I4** | **ランタイム不在時の挙動**（fail-open / fail-closed / init で拒否） | 初回公開後に変えると既存利用者の hook 挙動が変わる |
| **I5** | **`docs/internal` を init が敷くか** | 敷かないなら `CLAUDE.md` テンプレートから Hierarchy of Truth 第 2 位が落ちる = **製品定義の変更** |

### §13.5 L1 と gabriel の両方が見ていなかった分岐（召喚の主目的）

| | 内容 |
|:--|:--|
| **A** | **誤判定の是正が plugin の前提であり、順序が逆**。`docs/private/` は init が敷く対象になりえないので、**製品中核が私物側にあるままでは plugin に製品中核が入らない** |
| **B** | **plugin ディレクトリの実在が K4 を「原則」から「テスト」に変える**。「plugin が敷くテンプレート各々について同一内容が開発側に存在する」は基質から導出できる検査（R3 #7 / #10 と同型 / 維持リスト不要）。これが **洗浄を不要にする本体** —— 配布物が plugin ディレクトリに閉じ、閉じていることをテストが保証すれば、`docs/artifacts/` がいくら増えても配布物は汚れない。**MAGI の A5 はここに届いていなかった** |
| **C** | **K2 の「self-hosting は唯一の QA」が失効しつつある**。`claude plugin eval` の ablation は self-hosting が測れないもの（**規範が無い状態との差分**）を測る。覆すのではなく認知のみ求める |
| **D** | **`/init-harness` は「直す」でも「置換」でもなく「撤回」が先**。rules / hooks / agents を配らずに名乗る skill は R3 #10 が拾うべき主張そのもの。修正して残す期間は「存在の主張が半分正しい」期間 |
| **E** | **Layer 1 が届かないことを宣言せよ**。射程を Layer 0 + Layer 2 と明示し、Layer 1 は init が「利用者の手作業として提示する」 |

### §13.6 要検証 8 件 —— **全件解決**（2026-09-04 / L1）

検証手段: 上流ドキュメント（code.claude.com）+ ローカル `claude` CLI **v2.1.259** + **インストール済み plugin の実体**（`~/.claude/plugins/` / 公式 marketplace の 15 plugin）。

| # | 仮定 | 判定 | 根拠と含意 |
|:-:|:--|:--|:--|
| **V1** | plugin skill は接頭辞なしで起動できる | **偽** | 本セッションの Skill ツール契約が「Plugin skills use `plugin:skill`」と明記。実ロード中の plugin skill は全て接頭辞つき。**加えて ADR-0010 I-4 が「名前空間を常に明示する（例: `/lam-harness:ship`）」と既に規定していた**（§15） |
| **V2** | `marketplace add` はリポジトリ全体を clone する | **真。ただし内訳が重要** | 実測: `marketplaces/agenticnotetaking/` = **440 ファイル（リポジトリ全体 / `.git` つき）**。一方 `plugin install` が展開するのは `cache/<marketplace>/<plugin>/<version>/` = **plugin ディレクトリのみ**。→ **「配布 = 有効化される集合」は plugin レベルでは成立するが、marketplace 登録の時点でリポジトリ全体の bytes は利用者のディスクに載る** |
| **V3** | `${CLAUDE_PLUGIN_ROOT}` は plugin 所有のものでのみ解決 | **真** | 公式 plugin の commands / SKILL.md での使用を実測。hookify 自身が「Plugin commands have access to `${CLAUDE_PLUGIN_ROOT}`」と記述。→ **プロジェクトへコピーした skill では解決されない**（HGA の「敷けるのは純プロンプトの skill だけ」判定を裏付け） |
| **V4** | exit 2 以外の非零終了は非ブロッキング + stderr 表示 | **真。かつ HGA の想定より悪い** | 公式: exit 2 以外は「action proceeds」+ トランスクリプトに `<hook name> hook error` 通知 + **stderr 1 行目**。**インタプリタ不在（exit 127）も同じバケツ**で、公式が `/bin/sh: ...: No such file or directory` を例示。→ **Python 不在時は fail-open と UX ノイズが同時に起きる**（HGA は二択と想定していた） |
| **V5** | plugin にランタイム依存の宣言機構は無い | **真。ただし公式の解法が前例化している** | 実マニフェスト 4 件を実測（`name` / `description` / `version` / `author` / `mcpServers` のみ）。**一方 Anthropic 公式 plugin `security-guidance` は `hooks/sg-python.sh` で Python を自力解決**しており、**Windows + Git Bash の Microsoft Store stub が exit 49 で黙って落ちる問題まで文書化**している。= LAM の `py_invoke.sh` と同型の解が公式に前例化されている |
| **V6** | agents も `plugin:agent` に名前空間化される | **真** | 本セッションの agent 一覧に **`hookify:conversation-analyzer`** が実在。ファイル側の frontmatter は `name: conversation-analyzer`。→ **LAM の skills 内 `subagent_type=gabriel` / `goal-driven-grader` 等の参照が全部壊れる**（U2 の射程は skills だけではない） |
| **V7** | `plugin eval` は hook の deny 挙動を測れない | **たぶん偽（HGA の想定が保守的すぎた）** | eval は plugin をロードした実エージェント実行を採点するため、hook の deny は「ツールが使われなかった / 変更が起きなかった」として grader が**間接的に観測できる**。ただし **hook 専用 grader は無く**、**`plugin eval` は early access**、LLM grader は課金（`--max-cost-usd` あり）。→ §13.5-C の「K2 の『唯一』が失効しつつある」はより強く成立するが、**無償・自動ではない** |
| **V8** | 利用者環境で init が `settings.json` を新規作成できる | **偽** | `permissions` への編集は auto mode の安全クラシファイアが**ハードブロック**（実測 2 回 / ユーザー承認でも解除されず / 構文修正すら不可 / 記憶 `settings-json-edit-blocked`）。→ **HGA §13.5-E の前者（Layer 1 は手作業として提示する）が正しい**。ただし観測は 2026-06-13 で約 3 か月前のため、公開前に再確認する |

**V1-V8 が実施順序に与える変更**: V6 により U2 の射程が「手打ち skill」から「**skills + agents の参照面全体**」へ広がる。V4 により I4 の選択肢は「沈黙 or UX 破壊」ではなく「**既定で両方起きる**」ため、init でのランタイム検査（HGA 推奨）が必須に近づく。V2 により「配布 = 有効化される集合」の定義は**維持できるが、marketplace 登録の bytes については別に説明が要る**。

---

## §15 検証中に発見: **ADR-0010 が本件の核心を既に決めていた**（2026-07-04 Accepted）

`~/.claude/plugins/` の実測中に、**`lam-global` という marketplace が既に登録済み**であることが判明した（2026-07-02 登録 / source = `directory` → `C:\Users\metral\claude-global-assets\lam-marketplace`）。中身は plugin **`lam-harness` 1.0.0**（skills 14 件）。

そして [ADR-0010](../adr/0010-global-claude-assets-governance.md)（**Accepted 2026-07-04** / HGA 召喚 #4 が設計分岐点の正本）が、本 MAGI が扱っている論点の多くを**既に決定していた**。

### ADR-0010 の決定（逐語要約）

> **採用**: Option A + B のハイブリッド
> 1. 共有 harness は **`lam-harness` plugin（marketplace `lam-global`）としてのみ配布する**
> 2. personal 層（`~/.claude/skills/`）は原則ゼロに空化する
> 3. customization は各 project の **vendored 実ファイル**で持つ
> 4. plugin の enable は**プロジェクトスコープ限定**とする
> 5. グローバル層を git 統治下に置く

### 統治不変条件（既に発効中）

| # | 内容 | 本 MAGI との関係 |
|:--|:--|:--|
| **I-1** | project を名前解決で上書きできる層（enterprise / personal）にユーザー・モデル起動スキルを置かない。**共有 harness は名前空間付き plugin としてのみ配布する** | **A1（plugin 採用）は既決**だった |
| **I-2** | plugin の enable は**プロジェクト設定スコープでのみ**行う（`skillOverrides` は plugin に無効 = enable 粒度が唯一の防御線） | 到達点 1 の install scope 判断に直結 |
| **I-3** | project 層のスキルは**実体ファイル（vendored）**。symlink 禁止 | A2 の「敷く」設計を既に規定 |
| **I-4** | **CLAUDE.md 等からのスキル参照は名前空間を常に明示する（例: `/lam-harness:ship`）** | **U2 は既決**。「名前空間を受容するか」は 2026-07-04 に決まっていた |
| **I-6** | 共有 **agent** も同一チャネル（plugin の `agents/`）で配布。personal 層への直置きは禁止 | **V6 の帰結を先取りしていた** |

### 前提となった上流仕様（ADR-0010 が裏取り済）

> Claude Code のスキル名解決は **`enterprise > personal(~/.claude/skills) > project(.claude/skills) > bundled`** であり、**personal（グローバル）が project を常に上書きする**。逆転設定は存在しない。

**実害の記録**: etm-diary で `/ship` 実行時に project 版でなく**グローバル汎用版が起動**し、規約の CHANGELOG 再生成工程が欠落した。

### 何が起きているか

**ADR-0010 は「plugin 化する」と決め、実装も始まっていた。しかし `lam-harness` 1.0.0 の skills は 2026-07-02 の世代で凍っている。**

実測した 14 skills: `adr-template` / `audit-mode` / `build-mode` / `clarify` / `design-mode` / `init-harness` / `magi` / `project-status` / `retro` / `session-load` / `session-save` / `ship` / `spec-template` / `tdd-twada` / `ui-design-guide`。

**このうち `audit-mode` / `build-mode` / `design-mode` / `clarify` / `project-status` / `session-load` / `session-save` / `tdd-twada` / `ui-design-guide` は現在の LAM に存在しない**（現行は `building` / `quick-save` / `quick-load` / `full-review` / `autonomous` / `goal-driven` / `clause-gate` / `release` / `update-model` / `build-dashboard` / `lam-orchestrate`）。

**すなわち K4「配布集合 ⊆ 開発ロード集合」が既に破れており、それが 2 か月間検出されなかった。** これは HGA §13.5-B が「K4 を原則からテストに変える」と述べた必要性の、**実測による裏付け**である。

### ADR-0010 と D-1 死んだ案 #5 の緊張

ADR-0010（2026-07-04）は harness を**別リポジトリ**（`~/claude-global-assets` / remote `sougetuOte/claude-global-assets`）に置いた。D-1（2026-07-27）は**リポジトリ分割を死んだ案 #5 として棄却**した。**この 2 つの関係は本 MAGI では判定しない**（ユーザー判断領域 / §16 の承認イベントに含める）。

### 再検証トリガー（ADR-0010 R-1 が本日発火している）

> **R-1**: Claude Code のメジャー更新時、I-1 / I-2 の前提（`personal > project` 解決順・plugin 名前空間の非衝突・`skillOverrides` の plugin 無効）を公式ドキュメントで再裏取りする。

ADR-0010 制定時は v2.1.x 初期、現在 **v2.1.259**。**R-1 の再裏取りは未実施**であり、本 MAGI の V1-V8 がその一部を果たしたが、`skillOverrides` の plugin 無効は未確認。

### §13.7 HGA の結び（逐語）

> L1 の到達点は方向として正しい。gabriel が 2 度 abort に至ったのは設計が間違っていたからではなく、**設計の前提（何が私物で何が製品か）が D-1 の段階で 1 度ずれていた**からで、その上にいくら層を積んでも根が動かなかった。根は D-1 design §4 が自分で書いている。

---

## §14 決定の順序（HGA 版 / 保留解除の候補）

```
0.  init-harness 欠陥 (b) 即時修正 + 名乗りの縮小（§13.5-D）        ← 独立・着手可
0'. 条文の S 分割（§2|§3 / §3-§9 を docs/internal へ）              ← plugin と独立・先行
0''. V2-V8 を潰す（安価な順）
1.  「配布 = 有効化される集合」を定義として置く（U3 はここで消える）
2.  不可逆 5 点（I1-I5）を 1 承認イベントで並べる。**特に I1 は「大きく始める」側へ**
3.  K4 テスト +「plugin 内参照の閉包」テストを Red で置く（§13.5-B / A5 の完成形）
4.  plugin 骨格（hooks / agents / init）。skills の所在は I1・U2 の PM 判断に従う
5.  A4b（project hook 層 + §0-§2 + テストの対）
6.  local install で self-hosting 切替       ← ここで初めて作者の呼び出し面が変わる
7.  clone-template 廃止判断 =「fresh clone の pytest 緑」が要件から外れる日
```

**§10.5 との差**: 順序 0'（S 分割）が新設され plugin より前に来た / 不可逆 5 点の承認イベントが新設された / PM 判断が local install 切替より前に移った / A5 が 2 検査に拡張された。

---

## §10 参照

- `docs/artifacts/d-1-rationale-2026-07-27.md` §2.3 / §2.4 / §3（死んだ案 #5 / パッケージング境界）
- `docs/artifacts/retro-D1-2026-08-13.md` §1 議題 4（残余 #1 / #2）
- `docs/artifacts/2026-07-27-magi-outbound-ban-path.md`（死んだ案 7 件 / A4 の前提）
- `docs/artifacts/clause-gate-ledger.md` §C 機構 #10（A5 の同型先例）
- 上流: code.claude.com/docs/en/plugins-reference / plugin-marketplaces / agent-sdk/claude-code-features
