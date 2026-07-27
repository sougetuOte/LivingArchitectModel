# 指示の実効ロード機序 — upstream 一次資料の確定記録（2026-07-27）

**位置づけ**: 「LAM の指示が**いつ・どこまで実際にモデルの context に載るか**」を Claude Code 公式ドキュメントから確定した記録。HGA #24（指示の実効性の再診断）の currency push として作成した。
**取得日**: 2026-07-27 / **取得手段**: Opus subagent による一次資料 fetch（context7 + 公式 docs / tool_uses 30）
**なぜ残すか**: 本記録は **LAM の既存前提を 4 つ覆している**（§3）。セッション限りで失うと、同じ誤った前提の上で次の設計判断が積まれる。

> **本ファイルの性格**: これは**事実の記録**であり、規範ではない。指令を 1 つも含まず、`docs/artifacts/` 配下（= R1 の外）にあるため常駐面の予算を消費しない。**将来ここに「〜すべき」を書き足さないこと**（WC-6「対応表の第二帳簿化」と同型の罠）。

---

## §1 「常駐」は 1 種類ではない — compaction を跨いだ生死が機構ごとに違う

**これが本調査の最重要発見。** 公式 [`context-window` §What survives compaction](https://code.claude.com/docs/en/context-window) の逐語表:

| 機構 | compaction 後 |
|:---|:---|
| system prompt / output style | 不変（メッセージ履歴の一部ではない） |
| **project-root `CLAUDE.md` と `paths:` なしの rules** | **ディスクから再注入される** |
| auto memory | ディスクから再注入される |
| **`paths:` frontmatter つき rules** | **失われる。マッチするファイルが再び読まれるまで戻らない** |
| サブディレクトリの入れ子 `CLAUDE.md` | 同上 |
| invoke 済み skill 本文 | 再注入されるが **1 skill あたり 5,000 トークン / 合計 25,000 トークンで打ち切り**（古いものから落ちる） |
| hooks | 該当なし（コードとして走り、context ではない） |

**同節の逐語**:
> 規則が compaction を跨いで persist しなければならないなら、**`paths:` frontmatter を外すか、project-root の `CLAUDE.md` へ移せ**。

> truncation はファイルの先頭を保持するので、**最重要の指示は `SKILL.md` の先頭付近に置け**。

**一般挙動**（[`how-claude-code-works`](https://code.claude.com/docs/en/how-claude-code-works) §When context fills up / 逐語）:
> 古いツール出力を先に消し、必要なら会話を要約する。あなたの要求と主要なコード片は保持されるが、**会話の早い段階の詳細な指示は失われうる**。永続的な規則は会話履歴に頼らず `CLAUDE.md` に置け。

---

## §2 ロードの契機は enum 化されており 5 種のみ

`InstructionsLoaded` hook の matcher（[`hooks`](https://code.claude.com/docs/en/hooks)）:

`session_start` / `nested_traversal` / `path_glob_match` / `include` / `compact`

**「フェーズ遷移」「コマンド実行」に相当する値は存在しない。**

- **`paths:` の発火条件**（[`memory`](https://code.claude.com/docs/en/memory) §Path-specific rules / 逐語）: 「Path-scoped rules は **Claude がパターンにマッチするファイルを読んだとき**に発火する。**すべての tool use で発火するのではない**。」
- **`paths:` なし**（同 / 逐語）: 「`paths` frontmatter を持たない rules は起動時にロードされ、**`.claude/CLAUDE.md` と同じ優先度**を持つ。」
- **`CLAUDE.md` の投入形式**（同 / 逐語）: 「`CLAUDE.md` の内容は**システムプロンプトの一部としてではなく、システムプロンプトの後のユーザーメッセージとして**配送される。」
- **常駐コスト**（[`features-overview`](https://code.claude.com/docs/en/features-overview) §Context cost by feature）: `CLAUDE.md` は「Session start にロード / Full content / **Every request**」

---

## §3 LAM の既存前提を覆した 4 点

| # | LAM の前提 | upstream の事実 | 影響 |
|:-:|:---|:---|:---|
| **1** | **R2 降格（`paths:` つき化）は「常駐から外す」操作である** | その通りだが、**同時に「compaction 後に失効する」操作でもある**。マッチファイルが再び読まれるまで戻らない | v5.0.0 の 99→80 の主要手段が R2 降格。**長いセッションの後半で当該条項が沈黙する**。設計 §1.2 の R2 要件（ファイル繋留 ∧ 配送先明記 ∧ 可逆）は compaction を考慮していない → **HGA #24 副問 2 で審理中** |
| **2** | **subagent には親の rules が届かないので `.claude/agents/*.md` に移設が要る** | [`sub-agents`](https://code.claude.com/docs/en/sub-agents) 逐語: subagent は「メインの会話がロードする **CLAUDE.md 階層のすべてのレベル**（`~/.claude/CLAUDE.md`、**project rules**、`CLAUDE.local.md`、managed policy files を含む）」を継承する。**組込 Explore / Plan のみ例外で、変更する frontmatter も設定も存在しない** | **含意は 2 つに分かれる**（下記の訂正を参照）。継承**しない**もの = auto memory / 会話履歴 / invoke 済み skill / 既読ファイル |

> **訂正（HGA #24 / 2026-07-27 同日 / この誤りは L1 が一度ユーザーに報告した）**: 上記 #2 から「v5.0.0 の agents 12 枚移設は upstream 上の重複である」と結論するのは**誤り**。移設元の `model-delegation-prompting.md` は同時に **R2 へ降格して R1 から退去済み**であり、agent 定義は **R1 継承と重ならない唯一の写し**である。したがって移設は重複ではなく、**compaction 不死の spawn 時配送チャネルへの正しい避難**だった（#24 副問 2 / 5）。
>
> **本当の重複は別の場所にある**（#24 が実測で特定）: (i) `hga-summoning.md` §Sonnet L2 委譲時の追加防御（A + C の boilerplate）は agent 定義の §受領側の恒久制約と同内容でありながら **R1 に残っている** / (ii) `CLAUDE.md` §Memory Policy の大半は**基質挙動の再記述**であり、`/doctor` の trim 基準「コードベースから導出可能な内容は削る」に該当する。
>
> **含意の本体はむしろこちら**: R1 質量 137,537 文字は **subagent の spawn ごとに隔離コンテキストへ複製される**（Explore / Plan を除く全 subagent）。**3.5 層委譲モデルは注意の希釈から逃げる装置のつもりで、希釈を掛け算する装置になっている**（#24 の失敗様式 M8 / **LAM は本様式に対して裸**）。
| **3** | **skill 化すれば常駐コストはゼロ**（設計 §6 仮定 3 / HGA #23 要検証仮定 3） | **ゼロではない**。description（+ `when_to_use` / 合計 **1,536 文字上限**）が**毎リクエスト**載る。逐語: 「model-invocable な skill については、Claude は**毎リクエスト**で名前と description を見る」。ゼロにする唯一の手段は **`disable-model-invocation: true`** | 経路 4（`hga-summoning.md` の skill 化）の利得が目減りする。ただし 20,324 字 → 1,536 字上限なら依然として大幅減 |
| **4** | **1M モデルでも auto-compact は 200K 付近で発火する**（`CLAUDE.md` §Context Management の注記 = 仮説として記載） | **公式仕様では否定される。** `CLAUDE_CODE_AUTO_COMPACT_WINDOW` の既定は「モデルの context window、**標準モデルは 200K、extended context モデルは 1M**」。Sonnet 5 は約 **967K**。200K で圧縮されるのは **3 例外のみ**（LLM gateway 経由 / `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` / extended context 無効の Sonnet 4.6・Opus 4.6） | `CLAUDE.md` の閾値運用（180K で `/quick-save` 推奨）の根拠が弱まる。**ただし仕様と実測の食い違いは前例がある**（changelog v2.1.207 = 「Opus 4.8 on Bedrock で auto-compact が発火しないバグ」の修正）ため、仕様が実測を否定するわけではない |

---

## §4 量と遵守率 — 公式が明言している（逐語）

- [`memory`](https://code.claude.com/docs/en/memory): 「**指示が具体的かつ簡潔であるほど、Claude はより一貫してそれに従う。**」
- 同: 「**サイズ**: `CLAUDE.md` 1 ファイルあたり **200 行未満**を目標にせよ。**長いファイルはより多くの context を消費し、遵守率を下げる。**」
- 同: **機構的上限はない** —— 「この制限（200 行 / 25KB）は **`MEMORY.md` にのみ適用される**。**`CLAUDE.md` ファイルは長さによらず全文ロードされる**。ただし短いファイルの方が良い遵守率を生む。」
- [`features-overview`](https://code.claude.com/docs/en/features-overview): 「多すぎると context window を埋めるだけでなく、**ノイズを加えて Claude の実効性を下げる。skill が正しく発火しなくなったり、Claude があなたの conventions を見失ったりする。**」
- `memory` §Consistency: 「**2 つの規則が互いに矛盾する場合、Claude はどちらかを恣意的に選びうる。**」
- 同: 「`@path` import への分割は整理には役立つが、**context を減らさない**。import されたファイルは起動時にロードされるからである。」

> **含意**: 天井 80 に upstream の対応物は存在しない。upstream が持つのは 200 行**推奨**と、上記の**遵守率の言明のみ**。

---

## §5 enforcement と request の区別（逐語 / **§4 より重要かもしれない**）

- [`features-overview`](https://code.claude.com/docs/en/features-overview) §Hook vs Skill: 「**guardrail は hook に置け。** `CLAUDE.md` や skill に書かれた『`.env` を絶対に編集するな』という指示は、**保証ではなく要求である**。編集をブロックする `PreToolUse` hook が enforcement である。**規則が毎回成立しなければならないなら、prompt の指示ではなく hook にせよ。**」
- [`memory`](https://code.claude.com/docs/en/memory) 冒頭: 「Claude はこれらを **enforced configuration ではなく context として**扱う。Claude の判断によらず行為をブロックするには、代わりに `PreToolUse` hook を使え。」
- 変換規則: 「エントリが **multi-step の手順である、またはコードベースの一部にしか関係しない**場合、skill か path-scoped rule へ移せ。」/ 「指示が **特定の時点で必ず走らねばならない**もの（コミット前・各ファイル編集後 等）なら、**hook として書け**。hook は固定のライフサイクルイベントでシェルコマンドとして実行され、**Claude が何を決めるかによらず適用される**。」
- **hook のコンテキストコストは、出力を返さない限り厳密にゼロ。**
- `/doctor` の trim 基準（v2.1.206〜）: 「**コードベースから導出できる**内容（ディレクトリ構成・依存リスト・アーキテクチャ概観）を**切り**、**pitfalls・rationale・ツール既定と異なる conventions** を**残す**。」

---

## §6 compaction 後の再注入用の公式機構（**LAM は未使用**）

[`hooks-guide`](https://code.claude.com/docs/en/hooks-guide) §Re-inject context after compaction（逐語）:
> **`compact` matcher つきの `SessionStart` hook** を使って、圧縮のたびに critical context を再注入せよ。コマンドが stdout に書いたテキストは Claude の context に追加される。

関連機構: `PostCompact` hook / `InstructionsLoaded` hook。hook の `additionalContext` は **system reminder として注入**され、Claude はそれを平文として読む。

> **注意**: 再注入は「compaction による軽量化」を打ち消す操作でもある。無条件採用は WC-13「境界固着の側圧」を悪化させうる。

---

## §7 attention budget / context rot（[Anthropic engineering blog](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) / 逐語）

- 「context window 内のトークン数が増えるにつれ、**その context から情報を正確に想起する能力は低下する**。」
- 「LLM は大量の context を parse する際に引き出す『**attention budget**』を持つ。」
- 「**新しいトークンが 1 つ入るたびにこの予算がいくらか目減りし**、利用可能なトークンを慎重に選別する必要が高まる。」
- 「したがって context は**逓減する限界収益を持つ有限資源**として扱わねばならない。」
- 「良い context engineering とは、望む結果の尤度を最大化する **最小の高信号トークン集合**を見つけることである。」
- 機構的説明: n トークンで **n² の pairwise 関係**が生じ、context 長が伸びるほど関係の捕捉が薄く引き伸ばされる。加えてモデルは**短い系列がより一般的な訓練分布**から attention パターンを獲得している。

---

## §8 未確定（**事実として扱わないこと**）

| 問い | 探した範囲と結果 |
|:---|:---|
| **Claude 系モデルの位置別 recall 曲線**（lost-in-the-middle / primacy / recency） | **Anthropic 公式の測定値は存在しない。** 公表されているのは「20k+ トークン入力でクエリを末尾に置くと**最大 30% 改善**」という運用助言 1 点のみ（[prompt-engineering §Long context tips](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/long-context-tips)）。これは配置に関する助言であって位置別 recall 曲線ではない。探索範囲 = platform.claude.com の prompt-engineering / long-context-tips、anthropic.com/engineering、code.claude.com/context-window |
| **2026 年の新研究で §4 / §7 を更新するもの** | 決定的な資料は取れなかった。`arXiv:2605.12922`「When Attention Closes: How LLMs Lose the Thread in Multi-Turn Interaction」(2026-05-14) が最も近いが **PDF の本文抽出に失敗**し、数値も Claude 固有測定の有無も未確認 |
| 第三者ベンチの転移可能性 | IFScale（`arXiv:2507.11538` / 2025-07）は "bias towards earlier instructions" と `claude-sonnet-4` の **linear decay** を報告するが、**Anthropic 公式ではなく Claude 4 世代の測定**。Opus 5 / Sonnet 5 では未検証 |
| `CLAUDE.md` の「毎ターンディスク再読込はしない」の明示的否定文 | 見つからず。ただし `InstructionsLoaded` の matcher enum に「毎ターン」相当値が**存在しない**ことが間接証拠 |
| changelog のバージョン → 日付対応 | **未確認**。「2026-05 以降」の切り分けは版番号の連続性からの推定であり確定ではない |
| **LAM の per-turn 実効同時指令数** | **未計測**（HGA #23 が「最初に測るべき」と指定した数字 / 本調査の対象外） |

---

## §9 2026-05 以降の変化点（delta のみ / 日付対応は §8 のとおり未確定）

| version | 変化 |
|:---|:---|
| **v2.1.198** | 圧縮の要約リクエストがセッションの extended thinking 設定を継承（従来は非継承）/ `paths:` マッチが symlink 経由でも有効に / Explore が親の model を継承 |
| **v2.1.202** | **skill の再 invoke で本文が二重 append されなくなった**（同一内容なら「既にロード済み」の短い注記に置換）。それ以前は毎回フルコピーが積まれていた |
| **v2.1.206** | `/doctor` に `CLAUDE.md` トリム提案が追加 / subagent の sibling roster（system reminder）追加 |
| **v2.1.207** | Opus 4.8 on Bedrock で auto-compact が発火しないバグ修正 / auto mode が `.claude/settings.local.json` の `autoMode` を読まなくなった |
| **v2.1.210** | `MEMORY.md` が read limit 付近／超過時に警告・エラーを返す機構が新設（従来は黙って切り捨て） |
| **v2.1.211** | `MEMORY.md` の上限計測が「実際にロードされる内容のみ」に変更 / **nested `.claude/rules/*.md` が `--setting-sources` から project を除外しても読まれていたバグを修正** |
| **v2.1.214** | memory ファイルに ISO `modified` frontmatter タイムスタンプを自動付与 |
| **v2.1.216** | 長セッションでメッセージ正規化コストが**ターン数に対し二次関数的に増大**していたスローダウンを修正。transcript サイズを最大 79 倍削減 |
| **v2.1.217 / .218** | `paths:` の brace 展開に予算上限（1,000 パターン / 4 MiB）導入。それ以前は brace group の多い `paths` が起動時に CLI を停止・OOM させていた |
| 時期未特定（現行仕様） | `InstructionsLoaded` hook（ロード理由 5 種 matcher）/ `PostCompact` hook / `CLAUDE_CODE_AUTO_COMPACT_WINDOW` / `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` / managed settings の `claudeMd` キー / `claudeMdExcludes` / Sonnet 5 の 1M 既定 + 967K auto-compact |

---

## §10 参照

- HGA #24 のブリーフ（本記録を currency push として全量畳み込み）: `docs/artifacts/hga-summon-log.md` §24
- HGA #23 の裁定（計器 / 質量の分割 / 置換問い）: 同 §23 詳細
- `docs/artifacts/lam-reconstruction-handoff-2026-07-27.md`（セッション引き継ぎ正本）
- `docs/artifacts/clause-gate-routing-design-2026-07-26.md` §1.2（**R2 要件 / §3-1 の影響を受ける**）
- `.claude/rules/upstream-first.md`（本調査の根拠となる規律 / 段階1 = 実在性・段階2 = 適合性の二段構え）
