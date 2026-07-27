# MAGI: HGA #24 手 2（PLANNING §禁止の hook 化）の設計判断

**モード宣言**: **AoT 適用モード**（判断ポイント 4 / 影響レイヤー 3+ = hooks・rules・tests / 選択肢 3+）
**日付**: 2026-07-27
**議題**: HGA #24 が「手 2 = 既決」とした配置是正の実装設計。**新しいアライメント（配送の管理）の初手**であり、precedent を作る。
**召喚の契機**: ユーザー指示（「初手となり今後のアライメントを定める大事な一手だ。MAGI か HGA でレビューすべき」）。L1 は **HGA ではなく MAGI を推奨**した（新ゲート条件 1・2 とも未該当 / 可逆・復旧コスト小 / #24 の実装を同じ Fable に諮るのは自己確認のループ）。

---

## Step 0: AoT Decomposition

### 既存 ADR の走査（分解の前提 / 同じ判断が決定済みでないかの確認）

| ADR | 関連 | 判定 |
|:---|:---|:---|
| **0005** thin-harness-autonomous-governance | FR-9（統治ファイルの自己統治不可侵）/ FR-3.4（spec freeze）が **AUTONOMOUS フェーズ限定の deny** として実装済み | **本件は同型だが別フェーズ**。0005 は AUTONOMOUS のみを扱い PLANNING に触れていない。**再決定ではない** |
| **0008** approval-gate-redesign | 自己責任モデル + 反面教師制約 D1（deny ↔ allow 二重化必須）/ D4（ワイルドカード非依存・明示列挙） | **本件に制約として効く**。deny を足すなら対応する allow を併記する必要がある |
| **0011** clause-triage-and-model-generation-governance | 誕生ゲート / 配置是正は予算外 | **本件の合法性根拠**。再採点ではなく誤配の是正 |

⇒ **同じ判断の既決なし。前提の失効なし。分解を続行する。**

### Step 0 で確定させた実測事実（**合議はこれを前提とする**）

| # | 事実 | 出典 |
|:-:|:---|:---|
| **F1** | `_read_current_phase()` は読取失敗時に **空文字を返す = フェイルオープン**。コード内コメントが「フェーズ読取失敗は FR-9/FR-3.4 判定を無効化しうる（フェイルオープン方向）」と**自認済み** | `.claude/hooks/pre-tool-use.py:284-305` |
| **F2** | **`.claude/current-phase.md` は PM 級パスではない**（`_PM_PATH_PATTERNS` = `docs/specs/` / `docs/adr/` / `.claude/rules/` / `.claude/settings*.json` / ルート `CLAUDE.md` の 5 つのみ）。**被規制者である L1 が、承認なしにフェーズを書き換えられる** | `.claude/hooks/_hook_utils.py:61-72` |
| **F3** | 現に phase を読んで enforce しているのは **AUTONOMOUS の統治ファイル deny** と **AUDITING の PG allow** のみ。PLANNING §禁止 4 項は**一切 enforce されていない** | `pre-tool-use.py:156-213` |
| **F4** | AUTONOMOUS への遷移は **`/autonomous <spec>` の実行・承認時**に書かれる（承認フロー内）。PLANNING / AUDITING は **skill 廃止済のため手動更新** | `.claude/current-phase.md` §更新タイミング |
| **F5** | L1 は本セッション中に `current-phase.md` を **手で 2 回**動かした（BUILDING → PLANNING → BUILDING）。かつ本ファイルは M-1 完了後 **1 日以上 stale** だった | 本セッションの実測 |

### Atom 分解と依存 DAG

| Atom | 判断内容 | 依存 |
|:-----|:---------|:-----|
| **A2** | `current-phase.md` に決定的な書き手がいないまま enforcement を建ててよいか | なし（**根**） |
| **A1** | hook 化の範囲（3 項 / 4 項 / 別の切り方） | **A2** |
| **A3** | Outbound Write Ban の R3 二重化の可否 | なし（独立） |
| **A4** | 1 波でやるか分けるか | A1, A2, A3 |

> **順序の訂正**: ユーザー提示は ①範囲 ②書き手 ③二重化 ④波 だったが、**②が①を支配する**（書き手問題の結論次第で範囲が変わる）。DAG に従い A2 から処理する。

---

## Atom A2: 書き手不在のまま enforcement を建ててよいか

**[MELCHIOR]**（推進 / Value・Speed・Innovation）

建てるべきである。3 点。

1. **「保証」でなくても価値がある。** hook が与えるのは「規則が毎回成立する保証」ではなく「**無意識の違反を、意図的で記録に残る行為へ変換すること**」である。現状、私が PLANNING 中に実装を始めても**何も起きない**。hook があれば、違反するには先に `current-phase.md` を書き換えねばならず、それは `git diff` に残る。これは**誕生ゲートと同型の価値**であり（条項を偶然追加できない / 意識的に取引する必要がある）、LAM が既に採用済みの設計思想である。
2. **さらに 4 項目めも機構化できる可能性がある。** `current-phase.md` を `_PM_PATH_PATTERNS` に追加すれば、フェーズ遷移が PM ダイアログを通る。これは「承認があったか」を意味判断するのではなく、**遷移そのものを承認ゲートに通す**ことで「未承認での次サブフェーズ開始」を機構化する。`phase-rules.md` の「ユーザーが承認と言うまで次へ進まない」という散文が、初めて執行歯を得る。
3. **コストが極小。** 新規常駐条項ゼロ。既存の `_determine_by_path` に分岐を足すだけ。配置是正 = 予算外。可逆（数分で revert）。

**[BALTHASAR]**（批判 / Risk・Security・Debt）

4 点で反対する。うち 2 点は MELCHIOR 案 2 を**明確に殺す**。

1. **失敗様式が非対称で、危険な側が沈黙する。** 過剰ブロック（実際は BUILDING なのにファイルが PLANNING と言う）は**騒がしく自己修正する** —— L1 が即座に踏んで気づく。過少ブロック（実際は PLANNING なのにファイルが BUILDING と言う）は**完全に沈黙する**。そして **F5 のとおり、今日実際に起きた stale はまさに後者の方向**だった。これは M6（request を保証と誤認）を、今度は**機構の側で**再生産する。「hook があるから守られている」という誤った安心が生まれる分、**現状より悪くなりうる**。
2. **MELCHIOR 案 2 は R1 = PM 級パス集合の完全一致を壊す。** gabriel #2 が「R1 の編集は PM 級」と裁定できたのは、`_PM_PATH_PATTERNS` が **R1 の定義集合と一致している**からである（handoff §3 の機構実測）。ここに `current-phase.md`（R1 ではない / `.claude/rules/` 配下でもない）を足すと、**この一致が壊れ、「PM 級パス = R1」という現在成立している不変条件が失われる**。得るものは執行歯 1 本、失うものは体系の整合性 1 本。
3. **MELCHIOR 案 2 は効果自体も薄い。** `permission-levels.md` のセッションスコープ降格により、**同一セッション内 2 回目以降の同一ファイル編集は自動的に SE 級へ降格**する。**L1 は今日 1 セッションで 2 回フェーズを動かした（F5）。2 回目は素通りする。** 最も守りたい場面（作業中に方針が動いてフェーズを動かす場面）でこそ効かない。
4. **スコープ拡大。** #24 が既決としたのは「PLANNING §禁止 4 項の hook 化」であり、PM 級パス集合の変更は**別の設計コミット**である。#24 自身が「死案 #4 の復活の前提条件は『フェーズ状態に決定的な書き手を与える』という**別の設計コミット**」と明記している。ここで一気に片付けようとするのは、まさに #24 が分離せよと言った操作である。

**[CASPAR]**（調停 / Synthesis・Balance・Decision）

**結論: 建ててよい。ただし MELCHIOR 案 2（PM 級パス追加）は却下する。そして「承認ゲートを機構化した」と記録してはならない。**

裁定の根拠を 3 段で示す。

- **BALTHASAR 2・3 を採る。** PM 級パス追加は、不変条件（PM 級パス = R1）を壊す代償に対して、セッションスコープ降格で 2 回目以降が素通りするため**効果が構造的に不足している**。損得が合わない。**却下**。
- **BALTHASAR 1 は正しいが、「建てるな」の結論には届かない。** 「hook があるから守られている」という誤った安心が生じるのは、**hook が保証だと記録した場合のみ**である。MELCHIOR 1 が正確に述べたとおり、得られるのは「無意識の違反 → 意図的で記録に残る行為」への変換であり、これは実在の利得である。したがって危険は「建てること」ではなく「**建てたものを過大に記録すること**」にある。⇒ **`phase-rules.md` の条文を残したまま hook を建てる**（設計 §1.3 の R1 + R3 複宛先の型 / 軸 3 = 不可逆ではないが、**機構の沈黙を知る規範を残す**という §1.3 の趣旨は同じく適用できる）。条文が残るので「機構が全部やってくれる」という読みは発生しない。
- **BALTHASAR 4 を採る。** 「フェーズ状態に決定的な書き手を与える」は本 Atom のスコープ外とし、**未解決の既知ギャップとして明示的に記録する**。解かないことを選ぶのではなく、**解いていないことを記録に残す**（これが今日の §9 の教訓 —— 観測が構造的にできなかったものを「発火ゼロ」と誤読した失敗の逆をやる）。

**採用しなかった選択肢とその理由**（MUST）:

| 選択肢 | 却下理由 |
|:---|:---|
| **建てない（書き手が立つまで待つ）** | 「決定的な書き手」の設計は未着手であり、待つと**唯一の既知 enforcement ギャップが無期限に開いたまま**になる。かつ hook を建てても書き手問題は悪化しない（現状は enforcement ゼロ = 下限） |
| **`current-phase.md` を PM 級パスに追加**（MELCHIOR 案 2） | BALTHASAR 2・3。不変条件（PM 級パス = R1）の破壊 + セッションスコープ降格による効果不足 |
| **フェイルクローズ化**（読取失敗時に全実装をブロック） | 読取失敗は稀であり、**失敗時に全作業が止まる**代償が過大。かつ真の問題は読取失敗ではなく **stale**（読めてしまう）であり、フェイルクローズは stale に無力 |
| **hook 化と同時に `phase-rules.md` の条文を削除**（単線化） | WC-3「不可逆ガードの単線化」。機構が沈黙したときにそれを知る規範が消える |

---

## Atom A1: hook 化の範囲

**[MELCHIOR]**

**4 項すべてを狙うべきではないが、3 項は確実に取れる。** `phase-rules.md` PLANNING §禁止の 4 項のうち:

| 項 | 判定 | 根拠（clause-gate Step 1 = 入力にスキーマ契約 / exit-code 級機械判定 / 意味解釈不要） |
|:---|:---|:---|
| 実装コード生成（`.ts` / `.py` / `.go` 等） | **○** | 拡張子で機械判定。入力 = tool_input のパス = スキーマ契約あり |
| `src/` への変更 | **○** | パス prefix 一致 |
| 設定ファイル変更（`package.json` / `pyproject.toml` 等） | **○** | ファイル名一致。**`settings*.json` は既に PM 級だが `pyproject.toml` / `package.json` は PM 級パスではない**ため、純粋な追加価値がある |
| 未承認での次サブフェーズ開始 | **×** | 「承認」の有無は意味判断。A2 で PM パス経由の機構化も却下された |

加えて **ADR-0008 D1（deny ↔ allow 二重化必須）**への対応が要る。deny を足すなら対応する allow を明示する —— PLANNING 中でも `docs/specs/` / `docs/adr/` / `docs/tasks/` / `docs/artifacts/` への書き込みと**既存コードの読取**は許可される（`phase-rules.md` PLANNING §許可 がそのまま allow list になる）。

**[BALTHASAR]**

3 項に同意するが、**3 項目め（設定ファイル）に落とし穴がある**。

1. **「等」の解釈が開いている。** 条文は「設定ファイル変更（package.json, pyproject.toml **等**）」と書いており、**閉じた列挙ではない**。hook 化するには列挙を閉じねばならず、それは**条文の意味を狭める操作**である。ADR-0008 D4（ワイルドカード非依存・明示列挙）に従えば明示列挙が正しいが、**列挙から漏れた設定ファイルは「hook が通した = 許可された」と読まれうる**（過少ブロックの沈黙）。
2. **1 項目めの巻き添え。** 「実装コード生成」を拡張子で判定すると、**`.claude/hooks/*.py` や `.claude/tests/*.py` も `.py`** である。PLANNING 中に hook やテストを触るのは正当な場面がありうる（まさに今回のような配置是正）。**自分自身を建てる作業がブロックされる**という自己言及的な罠がある。
3. **`docs/` 配下の `.md` は当然除外**だが、`docs/specs/` に**コードブロックを含む設計書**を書くのは PLANNING の正当な作業である。ファイル単位の判定なら問題ないが、念のため明示すべき。

**[CASPAR]**

**結論: 3 項を hook 化する。ただし BALTHASAR の 3 指摘をすべて設計に織り込む。**

| 項 | 実装方針 |
|:---|:---|
| 実装コード生成 | 拡張子ベース。**ただし `.claude/` 配下は除外**（ハーネス自身の保守は PLANNING 中も正当 / BALTHASAR 2）。除外は明示的に記述し、理由をコメントに残す |
| `src/` への変更 | パス prefix 一致。除外なし |
| 設定ファイル変更 | **明示列挙**（`package.json` / `pyproject.toml` / `tsconfig.json` / `Cargo.toml` 等）。ADR-0008 D4 準拠。**「列挙外は許可の意味ではない」旨をコメントとテストに残す**（BALTHASAR 1 への対処 —— 沈黙を沈黙のまま置かない） |
| 未承認での次サブフェーズ開始 | **hook 化しない。`phase-rules.md` の条文として残す。** 理由を条文の隣に 1 行残す（「意味判断のため機構化できない」= 機構の沈黙を知る規範） |

**deny ↔ allow 二重化（ADR-0008 D1 / MUST）**: `phase-rules.md` PLANNING §許可（`docs/specs/` `docs/adr/` `docs/tasks/` `docs/artifacts/` への出力 / 既存コード読取 / Mermaid / `.claude/states/*.json`）を allow として実装に明記する。

**採用しなかった選択肢とその理由**（MUST）:

| 選択肢 | 却下理由 |
|:---|:---|
| **4 項すべて hook 化** | 4 項目めは意味判断であり、無理に機構化すると「判定できないものを判定するふりをする hook」ができて M6 を機構側で再生産する |
| **1 項目のみ（`src/` だけ）** | 最も価値の高い「実装コード生成」を落とす。LAM は `src/` をほとんど持たず、実体は `.claude/` 配下にあるため、`src/` だけでは実質何も守らない |
| **拡張子除外なし（`.claude/` も含めてブロック）** | 自己言及的な罠（BALTHASAR 2）。ハーネス自身の配置是正が PLANNING 中にできなくなる |
| **ワイルドカードで設定ファイルを広く捕捉** | ADR-0008 D4 が明示列挙を要求（Claude Code のワイルドカード未尊重バグが未解決） |

---

## Atom A3: Outbound Write Ban の R3 二重化

**[MELCHIOR]**

**やるべきである。** `fable-l3-protocol.md` §2 の Outbound Write Ban（`D:\work7\Fable-Alembic\` 配下への書込・編集の禁止 / 全レベル共通 MUST NOT）は:

- **軸 1 = ユーザー意思**（handoff §3 が triage 表で確認済み / `#2-01`）
- **軸 3 = 不可逆**（他リポジトリの破壊）
- **clause-gate Step 1 を全通過**（対象パス文字列の一致 = スキーマ契約あり / 機械判定 / 意味解釈不要）
- **HGA #17 crux 3 の「静かに潜伏する失敗クラス」**（違反しても誰も気づかない = 永久に運用移管不可 = 機構化が必須の類）

設計 §1.3 により **不可逆ガードは R1 + R3 の複宛先が許される**ため、条文を残したまま hook を建てられる。予算外。

**[BALTHASAR]**

方向に異論はないが、**A1 と同じ波に混ぜることに反対する**。3 点。

1. **判定経路が別。** A1 はフェーズ依存（`_read_current_phase` を通る）、A3 はパス依存のみ（フェーズ非依存）。同一コミットに混ぜると、**テストが落ちたときにどちらの経路が原因か切り分けられない**。
2. **`__out_of_root__` の扱いが未確認。** `_hook_utils.py` のコメントは out-of-root パスを PM パターンから意図的に除外し、`pre-tool-use.py` 側で別途ローカル維持していると書いている。**`D:\work7\Fable-Alembic\` はリポジトリ外**であり、既存の out-of-root 経路とどう相互作用するかを**実測していない**。未実測のまま実装するのは今日の教訓に反する。
3. **#24 の文言は「同じ波で判定」であって「同じ波で実装」ではない。** 判定 = やるべきか否かを決めること。実装の波割りは別の判断（= A4）。

**[CASPAR]**

**結論: 実施する（可否 = 可）。ただし A1 とは別の波・別コミットとする。** BALTHASAR 1・3 を採用。

**BALTHASAR 2 を Action Item に昇格させる**: 実装前に `pre-tool-use.py` の out-of-root 経路を実測し、`D:\work7\Fable-Alembic\` 配下のパスが現状どう扱われるかを確認する。**未実測のまま書かない。**

**採用しなかった選択肢とその理由**（MUST）:

| 選択肢 | 却下理由 |
|:---|:---|
| **A1 と同波で実装** | 判定経路が別（フェーズ依存 vs パス依存）で切り分け不能。BALTHASAR 1 |
| **やらない（条文のまま）** | 「静かに潜伏する失敗クラス」= HGA #17 crux 3 の基準で**永久に運用移管不可**の類。条文だけでは違反が沈黙する |
| **条文を削って hook だけにする** | WC-3 単線化。設計 §1.3 が不可逆ガードに複宛先を許すのはまさにこの型 |

---

## Atom A4: 1 波でやるか分けるか

**[MELCHIOR]**

hook ファイルは 1 つ（`pre-tool-use.py`）であり、編集を 1 回にまとめれば手戻りが少ない。1 波が速い。

**[BALTHASAR]**

A3 で述べた切り分け不能の問題に加え、**今日 L1 の未検証の提案が繰り返し覆されている**（HGA が 7 件、gabriel が 2 回、upstream 裏取りが 4 前提）。**初手であればこそ、失敗したときに何が失敗したかが分かる形で刻むべき**である。

**[CASPAR]**

**結論: 2 波に分ける。** BALTHASAR を採用。

| 波 | 内容 | 検証 |
|:-:|:---|:---|
| **W1** | A1（PLANNING 3 項の hook 化 + allow 二重化）+ `phase-rules.md` に「4 項目めは機構化できない」理由 1 行 | TDD（Red → Green）/ pytest 全通過 / **PLANNING 中に `.claude/` の `.py` を触れることを実証するテストを含める**（BALTHASAR A1-2 への回帰テスト） |
| **W2** | A3（Outbound Write Ban の R3 二重化）。**着手前に out-of-root 経路を実測** | TDD / pytest 全通過 |

**採用しなかった選択肢とその理由**（MUST）: 「1 波」= 切り分け不能（上記）。「3 波以上」= A1 の 3 項は同一経路・同一テストファイルであり分割の利得がない（過剰分割は overhead）。

---

## Step 3 時点の統合結論（gabriel probe 前 / **下記 gabriel #3 により破棄された**）

1. **A2**: 建てる。ただし **PM 級パス追加は却下**（不変条件の破壊 + セッションスコープ降格による効果不足）。`phase-rules.md` の条文は**残す**（R1 + R3 複宛先）。**「承認ゲートを機構化した」と記録してはならない** —— 得られるのは「無意識の違反 → 意図的で記録に残る行為」への変換のみ。**「フェーズ状態に決定的な書き手がいない」ことを未解決の既知ギャップとして明示記録する。**
2. **A1**: **3 項**を hook 化。`.claude/` 配下は除外（自己言及の罠）。設定ファイルは明示列挙（ADR-0008 D4）+「列挙外は許可の意味ではない」をコメントとテストに残す。allow 二重化（ADR-0008 D1）必須。4 項目めは条文として残し、機構化できない理由 1 行を隣に置く。
3. **A3**: 実施可。ただし **A1 とは別波**。着手前に out-of-root 経路を実測。
4. **A4**: **2 波**（W1 = A1 / W2 = A3）。各波で TDD + pytest 全通過。

---

## Step 4: gabriel adversarial probe（第 1 回）

- **verdict**: `refuted`
- **severity**: `critical`
- **affected_atoms**: A1, A2, A3, A4（**全 Atom**）
- **recommended_action**: `re-magi`
- **confidence**: 0.75
- **処理**: **MAGI 結論を破棄し、再 MAGI 1 ラウンドを実施**（AC-W-C-5 / 初回 / 上限 1 回）

> **[CRITICAL by gabriel]**: `_determine_by_command` は AUDITING 以外で常に SE を返すため、`Bash("cat > x.py <<EOF")` 等は `file_path` を持たず **A1 の拡張子ベース判定を完全に迂回する**。これは新設 PLANNING deny だけでなく **既存の AUTONOMOUS FR-9 / FR-3.4 deny も同様に迂回可能**という未検証事実であり、F3 の楽観的前提を揺るがす。加えて item1 は `.claude/` 全除外 + `src/` 不在により**この repo の実コードをほぼ守らない**（A1 自身が「`src/` だけでは無力」と認めた批判の再来）。A2 の価値主張「無意識の違反 → 記録に残る行為」も、**Bash 経由なら `current-phase.md` を改変せずに成立するため崩れる**。

### gabriel が裏取りした事項（L1 の Step 0 実測の検証）

| 事実 | gabriel の判定 |
|:---|:---|
| F1（フェイルオープン） | **正確**（`pre-tool-use.py:284-305`） |
| F2（`current-phase.md` は PM 級パス外） | **正確**（`_hook_utils.py:61-72`） |
| F4（AUTONOMOUS は承認フロー / PLANNING は手動） | **正確** |
| BALTHASAR A2-3（セッションスコープ降格で 2 回目以降素通り） | **正確**。`post-tool-use.py` の `_PM_PATH_PATTERNS_FOR_CACHE = _PM_PATH_PATTERNS`（**共有タプル**）により、PM 級パスに追加すれば自動的にキャッシュ対象になることを確認 |
| F5（L1 が 2 回フェーズを動かした） | 自己報告のため**独立検証不能**（低リスク） |

### gabriel の追加発見（Warning 級 / 誰も検討していなかった）

`docs/artifacts/cross-module-blame-package/blame_hint_parser.py` が**実在する**。A1 item1 は `docs/` への明示除外を持たないため、**PLANNING §許可 の範囲内にある正当な `.py` 成果物を誤ってブロックしうる**。

---

## 再 MAGI ラウンド 1（gabriel.reasoning を Divergence 入力に追加 / 再 MAGI カウンター = 1）

### L1 が追加実測した事実（gabriel 指摘の独立検証）

| # | 事実 | 実測 |
|:-:|:---|:---|
| **F6** | **`src/` ディレクトリは存在しない** | `ls -d src` → 不在 |
| **F7** | **リポジトリ内の `.py` は 1 件を除きすべて `.claude/` 配下**（`.claude/tests/` 31 / `.claude/hooks/tests/` 22 / `.claude/hooks/analyzers/tests/` 18 / `.claude/scripts/` 16 …）。**唯一の例外が `docs/artifacts/cross-module-blame-package/blame_hint_parser.py`** = PLANNING §**許可**範囲内 | `git ls-files "*.py"` の全数集計 |
| **F8** | `_determine_by_command` は AUDITING 以外で常に `("SE", "command (default SE)")` を返す。`Bash` の `tool_input` は `command` を持つが `file_path` を持たないため、パス判定に到達しない | gabriel 実測（`pre-tool-use.py:189-212` / `215-238`）+ L1 再確認 |

⇒ **A1 の 3 項のうち、item1 と item2 は「守る対象が存在しない」。** item1 は `.claude/` を除外した瞬間に対象が消え、しかも**残った唯一の対象（`docs/artifacts/` の 1 件）は誤ブロックの対象**である。item2 の `src/` は存在しない。**元案は空振りする hook を建てる提案だった。**

### 再 Divergence

**[MELCHIOR]**

元案は価値の大半を失った。しかし **gabriel は同時に、より価値の高い標的を発見している**。

1. **既存の AUTONOMOUS FR-9 / FR-3.4 deny が Bash 経由で迂回可能**。これは新機能の話ではなく、**現に稼働している防御に空いた穴**である。親決定（`CHANGELOG.md` §決定）が定めた優先順位「**執行の正しさ ＞ 矛盾の最小化 ＞ 常駐質量 ＞ カウント**」に照らせば、**最優先事項に直撃する**。
2. **A3（Outbound Write Ban）の相対価値が上がった**。A1 が空振りする一方、A3 は (i) パス判定でスキーマ契約があり (ii) **守る対象が実在し**（別リポジトリ）(iii) 静かに潜伏する失敗クラスであり (iv) clause-gate Step 1 を全通過する。**A1 より明確に価値が高い。**
3. したがって**初手を差し替え、波の順序を逆転させるべき**である。

**[BALTHASAR]**

MELCHIOR 1（Bash 穴を塞ぐ）に**強く反対する**。標的の差し替え自体には賛成する。

1. **Bash コマンド文字列の判定は regex であり、スキーマ契約を持たない。** `cat > x.py` / `python -c "open(...).write(...)"` / `sed -i` / `tee` / heredoc / リダイレクトの変種 —— **列挙は必ず漏れる**。そして漏れた経路は「hook が通した = 許可された」と読まれる（A1 で指摘したのと同じ沈黙の再生産）。
2. **これは誕生ゲート自身の基準で不適格である。** clause-gate Step 1 は「入力にスキーマ契約があるか」を要求する（HGA #19 必須修正 ① が「トリガの構造化」と「入力の構造化」の混同を正した箇所）。**Bash の `command` は自由文字列であり、スキーマ契約を持たない。**
3. **rule-001 / rule-002 の再生産である。** HGA #18 の自己修正 2 が「病理は『機構であること』ではなく『**散文に結合した機構であること**』」と定めた、まさにその型（漂流する非構造入力を regex で追う）。計 7 検出イベントの drift 保守を生んだ機構と同じ設計を、今度は執行層で作ることになる。
4. **穴の所在は upstream の層にある。** Bash コマンドの制限は `.claude/settings.json` の `permissions.deny`（Layer 1 = ネイティブ権限）が担う設計であり、`security-commands.md` が既に「Layer 1 で deny / ask の実際の制御粒度を設定する」と明記している。**hook（Layer 2）で regex を書くのは層の誤り**である。

**[CASPAR]**

**結論: 初手を差し替える。BALTHASAR の 4 指摘をすべて採用し、Bash 穴は本波で塞がない。**

裁定を Atom ごとに示す。

#### A1 の改訂: **item1・item2 を落とし、item3 のみ実施する**

| 項 | 改訂後 | 理由 |
|:---|:---|:---|
| 実装コード生成 | **hook 化しない** | F7 により、`.claude/` 除外後に守る対象が存在しない。残る唯一の対象は PLANNING **許可**範囲内であり、実装すれば**誤ブロックだけが残る**（gabriel の追加発見） |
| `src/` への変更 | **hook 化しない** | F6 により対象が存在しない。**この条文は現時点で dead letter である**（下記の記録事項へ） |
| 設定ファイル変更 | **hook 化する**（明示列挙 / ADR-0008 D4） | `pyproject.toml` は実在し、PLANNING 中の変更には実害がある。**3 項のうち唯一、守る対象が実在する** |
| 未承認での次サブフェーズ開始 | hook 化しない（初回結論を維持） | 意味判断 |

#### A2 の改訂: **結論は維持されるが、価値の見積りを下方修正する**

初回結論「無意識の違反 → 意図的で記録に残る行為への変換」は、**gabriel が示したとおり Bash 経由では成立しない**（`current-phase.md` を改変せずに迂回できる）。したがって得られる利得は当初想定より**小さい**。ただし A1 が item3 のみに縮小された結果、**フェーズ依存の判定自体が 1 項目に減る**ため、書き手不在問題の露出面も同時に縮小する。**建てる判断は維持するが、「これで PLANNING 規律が執行される」とは記録しない。**

#### A3 の改訂: **本命に昇格。W1（初手）とする**

A1 が縮小した結果、**A3 が最も価値の高い操作になった**。パス判定 / スキーマ契約あり / 対象が実在 / 静かに潜伏する失敗クラス / Step 1 全通過。**初手はこれである。**

#### A4 の改訂: **順序を逆転する**

| 波 | 内容 |
|:-:|:---|
| **W1（初手）** | **A3 = Outbound Write Ban の R3 二重化**。着手前に out-of-root 経路を実測。条文は残す（§1.3 複宛先） |
| **W2** | A1 item3 = 設定ファイル変更の明示列挙 deny + ADR-0008 D1 の allow 二重化 |

#### 記録のみ行い、本波では手を付けない事項（**沈黙させない**）

| # | 事項 | 扱い |
|:-:|:---|:---|
| **R-a** | **既存の AUTONOMOUS FR-9 / FR-3.4 deny が Bash 経由で迂回可能**（F8）。これは新設分だけの問題ではなく、**現に稼働している防御の穴**である | **実測記録として残す。** 塞ぐ手段は hook の regex ではなく `.claude/settings.json` の `permissions.deny`（Layer 1）が正しい層。ただし settings.json は **PM 級かつ AI 編集不可**（案提示 → ユーザー手動 → AI 検証の 3 手順）。**ユーザーへの報告事項** |
| **R-b** | `phase-rules.md` PLANNING §禁止「`src/` への変更」は **dead letter**（F6 = `src/` が存在しない） | **記録のみ。条文の削除は行わない**（既収載条項の再採点 = 転落条件 ②）。HGA #23 副問 2 の「法と運用の乖離（事実上の desuetude）」の実例として `docs/artifacts/` に残す |
| **R-c** | `docs/artifacts/cross-module-blame-package/blame_hint_parser.py` の存在（PLANNING 許可範囲内の `.py`） | 記録のみ。将来 item1 を再検討する場合の必須の境界条件 |

### 再 Convergence の「採用しなかった選択肢とその理由」（MUST）

| 選択肢 | 却下理由 |
|:---|:---|
| **Bash 穴を hook の regex で塞ぐ** | BALTHASAR 1-4。スキーマ契約なし = clause-gate Step 1 不適格 / rule-001・002 型の drift 負債を執行層に新造 / 層の誤り（Layer 1 が正しい） |
| **`.claude/` 除外を撤回して item1 を有効化** | LAM の「実装」の実体が `.claude/` である以上、PLANNING 中のハーネス保守（**まさに本作業**）が全面停止する。自己言及的に不能 |
| **item1・item2 を「空振りでも条文と機構の対応が取れるから」実装する** | **機構の存在自体が監査面を増やす**（M-1 retro 記録 5）。守る対象がない機構は純粋な負債であり、かつ「hook がある = 守られている」という誤った安心を生む |
| **手 2 全体を取り下げる** | A1 item3 と A3 には実在の価値がある。全取り下げは過剰反応 |
| **`src/` 条文を今すぐ削除する** | 既収載条項の再採点 = 転落条件 ②。記録に留める |

---

## Step 4: gabriel adversarial probe（第 2 回 / 再 MAGI 後）

- **verdict**: `refuted`
- **severity**: **`warning`**（第 1 回の `critical` から降格 = 戦略判断そのものは覆らない）
- **affected_atoms**: A1, A3
- **recommended_action**: **`proceed`**
- **confidence**: 0.62
- **処理**: **AC-W-C-6** に従い、以下の指摘を MAGI 結論に**併記**して進む（再 MAGI 上限には到達せず / 人間エスカレーション不要）

> **[WARNING by gabriel]**: 戦略判断（W1 = A3 / W2 = A1 item3）は覆らないが、文書が 3 つのギャップを**記録さえしていない**状態で残している。

### 併記する指摘 3 件（**すべて着手前に解消すること**）

| # | 指摘 | 対処 |
|:-:|:---|:---|
| **G-1** | **A1 item3 自身も Bash 経由で迂回できる。** BALTHASAR が hook-regex 案を却下した根拠（`_determine_by_command` が AUDITING 以外で常に SE / `file_path` を持たない Bash はパス判定に到達しない）は、**W2 で新設する item3 にそのまま適用される**。`Bash("cat >> pyproject.toml")` は item3 の deny を迂回する。にもかかわらず「PLANNING 中の変更には実害がある」という価値主張が、**gabriel 第 1 回が A2 に対して行った批判と同型の脆弱性を抱えたまま再掲されている**。記録事項 R-a/R-b/R-c は既存 AUTONOMOUS deny のみを対象にしており、**新設 item3 には同種の記録が存在しない** | **item3 の価値を「Edit/Write 経路の保護に限られる」と明記する。** Bash 経路は保護対象外であることを、実装コメント・テスト・記録の 3 箇所に残す。**item1・item2 と違い対象は実在する**ため実施自体は維持するが、**「PLANNING の設定ファイル禁止が執行される」とは記録しない** |
| **G-2** | **A3 に ADR-0008 D1（deny ↔ allow 二重化必須）の allow 対が明記されていない。** A1 は `phase-rules.md` PLANNING §許可 を allow として明示したのに、**初手に昇格した A3 には対応する allow がない**。`fable-l3-protocol.md` §2 が明記する **`D:\work7\etc-to-alembic\handoff\` への書込許可**がその allow に相当するはずだが、本文中に一度も引用されていない。**初手（precedent を作る操作）であればこそ、この非対称は看過できない** | **W1 の実装に allow を明記する**: deny = `D:\work7\Fable-Alembic\` 配下への書込 / allow = `D:\work7\etc-to-alembic\handoff\` 経由の受け渡し。両者を対で実装・テストする |
| **G-3** | **境界条件 2 件が未検討。** (a) `_hook_utils.py:196-220` の `normalize_path` は out-of-root 判定時に `resolved`（symlink 展開済）ではなく **生の `file_path` 文字列**を `__out_of_root__/{file_path}` として保持する。したがって単純な前方一致 regex では **`D:\work7\Fable-Alembic\...` と `D:/work7/Fable-Alembic/...` が別文字列**となり片方が検知漏れしうる (b) 実装が `"alembic"` の**部分一致**（case-insensitive 含む）で書かれると、**`etc-to-alembic` を誤って deny 対象に含める** —— G-2 の allow をまさに殺す | **CASPAR が A3 で立てた Action Item（out-of-root 経路の実測）に、この 2 点を明示的なテストケースとして含める**: セパレータ正規化（`\` / `/` / 相対パス / symlink）と handoff との名前衝突 |

### gabriel が独立再検証した前提（**すべて正確 / 覆らない**）

| 事実 | 検証手段 |
|:---|:---|
| **F6** `src/` 不在 | `Glob("src/**")` / `Glob("src")` ともに 0 件 |
| **F7** `.py` は 1 件を除き `.claude/` 配下（例外 = `docs/artifacts/cross-module-blame-package/blame_hint_parser.py`） | `Glob("**/*.py")`（`.venv` 除外）で整合確認 |
| **F8** `_determine_by_command` は AUDITING 以外で無条件に `("SE", "command (default SE)")` | `pre-tool-use.py:189-212` の直接読解 |

---

## Step 5: AoT Synthesis

### 統合結論（再 MAGI ラウンド 1 の CASPAR 結論 + gabriel 第 2 回の warning 併記）

**初手は差し替わった。** 当初 L1 が提案した「PLANNING §禁止 3 項の hook 化」は、**この repository では守る対象がほぼ存在しない空振りの提案だった**（`src/` 不在 / `.py` は `.claude/` に集中し、その `.claude/` は自己言及の罠を避けるため除外せざるを得ない）。gabriel 第 1 回の `critical` refute と L1 の追加実測がこれを確定させた。

| Atom | 最終結論 |
|:---|:---|
| **A1** | **item3（設定ファイル変更の明示列挙 deny）のみ**を hook 化する。item1（実装コード生成）と item2（`src/`）は**守る対象が存在しないため実施しない**。**item3 の価値は Edit/Write 経路に限られる**（G-1 / Bash 経路は保護対象外）。4 項目め（未承認での次サブフェーズ開始）は意味判断のため条文に残す |
| **A2** | enforcement は建ててよい。ただし **PM 級パス追加は却下**（PM 級パス = R1 という不変条件の破壊 + セッションスコープ降格による効果不足）。**`phase-rules.md` の条文は残す**（R1 + R3 複宛先）。**「PLANNING 規律が執行される」とは記録しない**。「フェーズ状態に決定的な書き手がいない」ことを**未解決の既知ギャップとして明示記録する** |
| **A3** | **初手（W1）に昇格。** Outbound Write Ban の R3 二重化を実施する。**allow 対（`etc-to-alembic/handoff/`）を必ず併設**（G-2 / ADR-0008 D1）。着手前に out-of-root 経路を実測し、**セパレータ正規化と handoff 名前衝突をテストケースに含める**（G-3） |
| **A4** | **2 波。W1 = A3（Outbound Write Ban）/ W2 = A1 item3（設定ファイル）。** 順序は当初案から**逆転**した |

### Action Items

1. **[W1 着手前]** `pre-tool-use.py` の out-of-root 経路を実測する（`normalize_path` が `__out_of_root__/{生 file_path}` を保持する挙動 / `D:\work7\Fable-Alembic\` 配下のパスが現状どう扱われるか）。**未実測のまま書かない**
2. **[W1]** Outbound Write Ban の deny + `etc-to-alembic/handoff/` の allow を対で実装（ADR-0008 D1）。TDD（Red → Green）。テストケースに **セパレータ 4 形（`\` / `/` / 相対 / symlink）** と **`etc-to-alembic` の誤 deny 回帰**を含める
3. **[W1]** `fable-l3-protocol.md` §2 の条文は**残す**（設計 §1.3 の不可逆ガード複宛先）。条文の隣に機構の所在を 1 行示す
4. **[W2]** `phase-rules.md` PLANNING §禁止 3 項目め（設定ファイル）の明示列挙 deny + PLANNING §許可 の allow 二重化。**「Bash 経路は保護対象外」をコメント・テスト・記録の 3 箇所に残す**
5. **[記録のみ / 本波では実装しない]** **R-a**: 既存の AUTONOMOUS FR-9 / FR-3.4 deny が Bash 経由で迂回可能（F8）。**塞ぐ手段は `.claude/settings.json` の `permissions.deny`（Layer 1）であり hook の regex ではない**。settings.json は **PM 級かつ AI 編集不可**のため、案提示 → ユーザー手動編集 → AI 検証の 3 手順。**ユーザーへの報告事項**
6. **[記録のみ]** **R-b**: `phase-rules.md` PLANNING §禁止「`src/` への変更」は dead letter（`src/` 不在）。**条文の削除は行わない**（再採点 = 転落条件 ②）。HGA #23 副問 2 の「法と運用の乖離」の実例として記録
7. **[記録のみ]** **R-c**: `docs/artifacts/cross-module-blame-package/blame_hint_parser.py` の存在。将来 item1 を再検討する場合の必須の境界条件

### 本 MAGI が実証したこと（メタ）

**ユーザーの判断（「初手だからレビューすべき」）は正しかった。** レビューなしで進めていれば、**守る対象が存在しない hook を「唯一の enforcement ギャップを閉じた」と記録して commit していた**。検出したのは gabriel（独立コンテキスト）であり、L1 の自己検証では届かなかった。これは memory `self-verification-scope-limit`（「自己検証は自分の理解の内側でしか働かない」）の実測 n+1 例目である。

---

## W1 実施記録（2026-07-27 / BUILDING）

**Action Items 1-3 完了。** TDD（Red 8 failed → Green 16 passed）→ 全体回帰 → E2E 実測の順で実施。

### 実装

| 対象 | 内容 |
|:---|:---|
| `.claude/hooks/pre-tool-use.py` | `_OUTBOUND_WRITE_BAN_ROOTS` / `_OUTBOUND_WRITE_ALLOW_ROOTS` / `_is_under` / `_resolve_for_outbound_check` / `_check_outbound_write_ban` を新設。`_determine_by_path` の**最前段**（`normalize_path` より前 / フェーズ非依存）で判定。`_build_deny_reason` に第 3 系統の分岐を追加 |
| `.claude/tests/hooks/test_outbound_write_ban.py` | **新規 16 tests**（セパレータ 4 形 / フェーズ非依存 4 種 / handoff allow 4 種 / リポジトリ内回帰 4 種 / 条文 drift 検査） |
| `.claude/rules/fable-l3-protocol.md` §2 | **条文は無変更**。機構の所在・allow 対・**Bash 経路は対象外**を示す 1 段落を追記（**指令キーワードを追加していない** = §A 不変） |
| `docs/artifacts/clause-gate-ledger.md` §C | 機構 #5 として記録。あわせて「上記 **2** 件」という stale な件数（機構 #3・#4 追加時に未追随）を **5** 件へ更正 |

### Action Item 1 の実測結果（着手前の必須作業）

**現状の `Fable-Alembic` への書込は out-of-root → `_PM_OUT_OF_ROOT_PATTERN` → PM 級（ask）だった。** すなわち「ユーザーが承認すれば書ける」状態であり、条文の **MUST NOT（絶対禁止）と格差**があった。本実装でこの格差が閉じた。

また gabriel G-3(a) の懸念（`normalize_path` が out-of-root 時に**生の file_path** を保持する / `_hook_utils.py:218-220`）を実測で確認し、**`normalize_path` を経由せず `Path.resolve()` で独立に正規化する**設計を採った。

### 検証

| 検証 | 結果 |
|:---|:---|
| 新規テスト | **16 passed** |
| 全体回帰 | **1161 passed + 14 skipped**（従来 1145 + 14 → **+16 = 新規分ちょうど** / regression ゼロ） |
| §A 指令カウント | **80**（不変 = 天井超過なし / net-negative 非発動） |
| 台帳テスト | 19 passed |
| **E2E 実測**（hook をサブプロセス起動して `permissionDecision` を確認） | **8 ケース全通過** —— 禁止 4 形（バックスラッシュ / フォワードスラッシュ / **大文字小文字違い** / 相対 traversal）= すべて `deny` / 許可 2 形（handoff / その兄弟 `etc-to-alembic/README.md`）= `ask`（**誤 deny なし** = gabriel G-3(b) の回帰）/ リポジトリ内 2 形 = 従来どおり |

> **E2E で一度「発火しない」と観測したが、原因はプローブ側のシェルエスケープ**（`echo` / `printf` が `\` を `\` に潰し、JSON の `\w` `\F` が不正エスケープになっていた）。JSON 生成から hook 起動までを Python 内で完結させたところ全ケース通過。**hook 側の欠陥ではない。** —— 記録しておくのは、次に同型の E2E を書く者が同じ 15 分を溶かさないため。

### 残（W1 の外）

- **W2**: `phase-rules.md` PLANNING §禁止 3 項目め（設定ファイル）の明示列挙 deny + allow 二重化。**価値は Edit/Write 経路に限られる**ことを 3 箇所に残す（gabriel G-1）
- **R-a（ユーザー報告事項）**: 既存の AUTONOMOUS FR-9 / FR-3.4 deny も Bash 経由で迂回可能。対処は `.claude/settings.json` の `permissions.deny`（Layer 1）。**settings.json は PM 級かつ AI 編集不可**のため、案提示 → ユーザー手動 → AI 検証の 3 手順
- **R-b / R-c**: 記録済（`src/` 条文の dead letter / `docs/artifacts/` 配下の `.py` の存在）

---

## W2 実施記録（2026-07-27 / BUILDING）

**Action Item 4 完了。** TDD（Red 7 failed → Green 21 passed）→ 全体回帰 → E2E 実測。

### 実装

| 対象 | 内容 |
|:---|:---|
| `.claude/hooks/pre-tool-use.py` | `_PLANNING_CONFIG_DENY_BASENAMES`（**basename の閉じた集合** / ADR-0008 D4）と `_PLANNING_ALLOW_PATTERNS`（**allow 対** / ADR-0008 D1）を新設。`_check_planning_config_freeze` を `_determine_by_path` の PM 照合より前段・**PLANNING フェーズ限定**で判定。`_build_deny_reason` に第 4 系統の分岐を追加。あわせて `_read_current_phase` の二重呼出を 1 回に集約（挙動不変） |
| `.claude/tests/hooks/test_planning_config_deny.py` | **新規 21 tests**（deny 7 / フェーズ依存 4 / phase 読取不能 1 / allow 対 6 / settings 除外 1 / 列挙外 1 / basename 部分一致回帰 1 / Outbound Ban との優先順位 1） |
| `.claude/rules/phase-rules.md` PLANNING §禁止 | **条文 4 項は無変更**。機構の所在・**射程の限界**・残 3 項に機構がない理由を示す 1 段落を追記（**指令キーワードを追加していない** = §A 不変） |
| `docs/artifacts/clause-gate-ledger.md` §C | 機構 #6 として記録（件数行を 5 → 6 に追随） |

### 4 項のうち 1 項のみを機構化した（gabriel 第 1 回の指摘を受けた縮小）

| 項 | 機構 | 理由 |
|:---|:---:|:---|
| 実装コード生成 | **なし** | `src/` 不在 + `.py` が `.claude/` に集中。ハーネス保守は PLANNING 中も正当なので除外必須 → 除外すると対象が消える。唯一の例外（`docs/artifacts/` 配下）は**許可**範囲内で、実装すれば誤ブロックだけが残る |
| `src/` への変更 | **なし** | **`src/` が実在しない**（dead letter / R-b として記録・条文は残す） |
| **設定ファイル変更** | **あり** | 3 項のうち唯一、対象が実在する（`pyproject.toml` / `requirements-dev.txt`） |
| 未承認での次サブフェーズ開始 | **なし** | 「承認」の有無は意味判断 |

### gabriel G-1 への対処（**射程を過大評価しない**）

**Edit / Write 経路のみを保護する**ことを **3 箇所**に残した: 実装コメント（`_PLANNING_CONFIG_DENY_BASENAMES` の注記）/ テスト docstring（モジュール冒頭）/ 条文側の追記（`phase-rules.md`）。`Bash("cat >> pyproject.toml")` は `file_path` を持たず `_determine_by_command` に落ちるため捕捉しない。

同様に「**列挙外は許可の意味ではない**」を `test_unenumerated_config_file_is_not_denied` が明示的に記録する（BALTHASAR の「過少ブロックの沈黙」指摘への対処）。

### 検証

| 検証 | 結果 |
|:---|:---|
| 新規テスト | **21 passed**（W1 分 16 と合わせて 37） |
| 全体回帰 | **1182 passed + 14 skipped**（W1 完了時 1161 + 14 → **+21 = 新規分ちょうど** / regression ゼロ） |
| §A 指令カウント | **80**（不変） |
| **E2E 実測** | **11 ケース全通過** —— PLANNING で `pyproject.toml` / `requirements-dev.txt` / `package.json` = `deny` / `.claude/states/*.json`・`docs/specs/`・`docs/artifacts/` = **deny されない**（allow 対が機能）/ `.gitleaks.toml`（列挙外）と `notes-about-pyproject.toml.md`（部分一致回帰）= deny されない / **BUILDING・AUDITING・AUTONOMOUS では非発動**（フェーズ依存） |
| W1 プローブの回帰 | **8 ケース全通過**（W2 実装後も Outbound Write Ban は不変） |

> **E2E の実施方法**: 実ファイル `.claude/current-phase.md` を書き換えずに検証するため、`LAM_PROJECT_ROOT`（`_hook_utils.get_project_root` のテスト用差替口）で一時ディレクトリを渡し、そこにフェーズファイルを置いた。実行後に実ファイルが無変更であることを `git diff` で確認済み。

### 手 2（HGA #24）の完了状況

| Action Item | 状態 |
|:---|:---|
| 1. out-of-root 経路の実測 | **完了**（W1） |
| 2. Outbound Write Ban の deny + allow 対 | **完了**（W1 / 機構 #5） |
| 3. `fable-l3-protocol.md` §2 に機構の所在 | **完了**（W1） |
| 4. PLANNING 設定ファイル deny + allow 二重化 | **完了**（W2 / 機構 #6） |
| 5. **R-a**: 既存 AUTONOMOUS deny の Bash 迂回 | **未着手**（`settings.json` = PM 級かつ AI 編集不可 / **ユーザーへの報告事項**） |
| 6. **R-b**: `src/` 条文の dead letter | **記録済**（条文は削除しない = 再採点 = 転落条件 ②） |
| 7. **R-c**: `docs/artifacts/` 配下の `.py` の存在 | **記録済** |
