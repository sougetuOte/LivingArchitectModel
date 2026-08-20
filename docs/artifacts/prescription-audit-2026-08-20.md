# 処方監査 2026-08-20 — 規範文書が配る指示の全数点検

**契機**: `retro-2026-08-17.md` P2 の未処理項。**条件ロードの害は「消えること」だけではない —— 生きている間に誤った処方を配ることもある。** 実例は `subprocess-encoding-convention.md` の `-o addopts=""` で、TDD 内省パイプラインのデータ源を無音で殺していた。**同型が他にないかは未点検**のまま在庫化していた。

**問い**: 規範文書・skill・agent 定義が読み手に配っている「処方」（実行させるコマンド / 参照させるパス / 参照させるテスト名・数値）は、現在も事実か。

**対象**: 73 ファイル / 抽出約 320 件
`.claude/rules/**/*.md`（19）+ `CLAUDE.md` / `.claude/skills/**/*.md`（32）/ `.claude/agents/*.md`（12）+ `docs/internal/*.md`（9）

**方法**: L2 3 並列で抽出 → **L1 が全指摘を自分のコマンドで再実行して検収**。抽出時は pytest・hook 実行を禁止（`pyproject.toml` の addopts が `.claude/test-results.xml` を上書きするため = 監査自体が計器を汚す経路）。

---

## §1 検出と対処

### A. 現役の導線上で誤った処方を配っていた（P2 と同型）

| # | 場所 | 内容 | 対処 |
|:-:|:--|:--|:--|
| A1 | `.claude/skills/magi/references/anchor-format.md` | 本文が Reflection 形式のまま「v5② gabriel 統合**予定**」と書いていた。統合は ADR-0007（Accepted 2026-07-02）で完了済。**孤児ではなく `magi/SKILL.md` が「フォーマットはこれを参照」と名指しする現役ファイル** | 修正 |
| A2 | `.claude/rules/model-roster.md` §6 | 「W2-M1-T4 完了までは手順 2 が存在しないため目視で確認する」→ `verify_model_reference.py` も `/update-model` も実在。**存在する検査を使わせない誘導**だった | 修正（PM 級） |
| A3 | `pyproject.toml` §testpaths コメント | 「引数なし `pytest` で**全 suite** を収集する」→ `.claude/hooks/analyzers/tests` の **565 件が収集対象外**。単独実行では 565 passed で全て通るため、壊れているから外れているのではない | コメントのみ修正（値は据え置き） |
| A4 | `.claude/skills/magi/SKILL.md` §参照 | 「`06_DECISION_MAKING.md` の Reflection セクションは後続 Stage 4 で gabriel probe 記述に**置換予定**」→ 当の §6 は既に「gabriel Adversarial Probe（AoT 適用時のみ / 旧 Reflection）」 | 修正 |
| A5 | 同上 | 「`decision-making.md` の Step 4 は後続 Stage 4 で**置換予定**」→ 既に置換済 | 修正 |

> **A1・A4・A5 は同一の壊れ方**である —— gabriel 統合（ADR-0007 / 2026-07-02）で**本体は直り、それを指す側が直らなかった**。A1 に至っては、正しい本体（`magi/SKILL.md`）が誤ったテンプレート（`references/anchor-format.md`）を名指しで参照していた。**規範を変えたときの下流消費者の点検漏れ**という、commit `1e5992f`（`/quick-save` の rule-001 旧仕様引用）と同じ型が、1 か月半後も別の場所で生きていた。

### B. 事実の陳腐化（対象は実在するが数値が古い）

| # | 場所 | 主張 → 実測 | 対処 |
|:-:|:--|:--|:--|
| B1 | `CLAUDE.md` §Subagent Persistent Memory | 「全 **8** エージェント」→ **12**（12 件すべて `memory: project` 設定済で、設定の主張自体は真） | 修正（PM 級） |
| B2 | `.claude/rules/decision-making.md` | wave_c テスト「**26**+21+16 件」→ **31**+21+16 | 修正（PM 級） |
| B3 | `docs/internal/06_DECISION_MAKING.md` | 同上 | 修正 |
| B4 | `.claude/skills/goal-driven/references/background.md` | `tasks.md` **v1.2.0** → **v1.4.6**（requirements / design の版は正しい） | 修正 |

### C. 存在しない対象を指していた

| # | 場所 | 内容 | 対処 |
|:-:|:--|:--|:--|
| **C1** | `goal-driven/SKILL.md` ×3 + `references/route-and-bound.md` | **文書の誤記ではなく機構の欠落**。§2 参照 | 未実装と明記 |
| C2 | `docs/internal/00_PROJECT_STRUCTURE.md` / `02_DEVELOPMENT_FLOW.md` | `src/backend/` `src/frontend/` `tests/` を構造として記述 → **`src/` ごと不在** | 注記（§3 の判断参照） |
| C3 | `init-harness/SKILL.md` | `docs/specs/init-harness/spec.md` 不在 | 修正 |
| C4 | `full-review/references/scalable-code-review.md` | `docs/memos/2026-03-10-scalable-review-and-eval-ideas.md` 不在 | 修正 |

### D. 重複・残骸（**削除は人間が実行** / `rm` は `security-commands.md` で deny）

`.claude/skills/lam-orchestrate/SKILL.md` の `Step 4: Reflection` 記載は修正済。残りは削除候補として保留する。

| 候補 | 実測 | 判断材料 |
|:--|:--|:--|
| `.claude/skills/lam-orchestrate/references/` の 2 件（`magi-skill.md` 4.4KB / `anchor-format.md` 1.9KB / 2026-06-20） | **git 追跡あり** | 現役導線から未参照（`SKILL.md` は `magi/references/` を参照）。内容も gabriel 統合前。削除すれば commit が立つ |
| `.claude/skills/skill-creator/references/` の 2 件 | git 追跡あり | `SKILL.md` は R-1 W-R4 S3 で削除済（`r-1-deletions.md`）。**skill として起動不能な状態で `references/` だけ残っている** |
| `docs/artifacts/tmp/` **38 件** | **git 追跡ゼロ**（全て未追跡） | 大半が 2026-06-20 の監査作業残骸。参照しているのは `retro-B4-W1-W15-2026-06-20.md`（当時の retro）と本ファイルのみ。削除しても git 履歴に影響しない |
| `.claude/grep_output.txt` / `.claude/grep_raw.txt` / `.claude/scripts/scan_nfr_refs.py` / `scan_nfr_refs2.py` | **git 追跡ゼロ** / 全て 2026-06-20 | 本監査で付随的に発見。同じ 2026-06-20 の作業残骸 |
| `.claude/lam-loop-state.json.bak` | **git 追跡あり** / 2026-05-26 | `.bak` が追跡下にある。`quality-auditor.md` のテンプレート例示が `lam-loop-state.json` を指すが、実体はこの `.bak` のみ |

---

## §2 C1 は文書の誤りではない —— bound 機構が実在しないキーに依存していた

`goal-driven` は「L3 の暴走はエージェントフロントマターの `max_turns`（小10/中20/大15）で打ち切る（AC-7 Plan B 対応）」と記述している。同じ主張が `docs/specs/goal-driven-orchestration/` の `design.md` / `config.md` にもある。

**公式仕様の裏取り**（context7 `/websites/code_claude` / 2026-08-20 取得）: subagent frontmatter の有効キーは `name` / `description` / `tools` / `disallowedTools` / `model` / `isolation` / `hooks`。**`max_turns`（snake_case）は存在しない。** 近いものは 2 つだけ:

- **plugin** agent フロントマターの `maxTurns:`（camelCase / `plugins-reference`）
- CLI フラグ `--max-turns`（`cli-reference`）

**goal-driven の 3 agent にはどちらも設定されていない**（実測 0 件）。つまり **L3 のターン打ち切りは現時点で効いていない**。

### なぜ `maxTurns` へ書き換えなかったか

効くかどうかを検証せずに書き換えると、「担保した」という記述だけが復活して**同じ失敗を作り直す**ことになる。`plugins-reference` の例は plugin agent 向けであり、`.claude/agents/*.md` に効くかは未確認である。よって**文書側は「未実装」と明記するに留め、機構をどうするかは別判断とした**。

`docs/specs/goal-driven-orchestration/` は PM 級のため本監査では未修正。**specs 側は依然として「担保する」と書いている。**

---

## §3 判断を要した点と、その判断

**C2（`src/` 構造）を実態へ置換しなかった。** `src/backend`（Python/FastAPI）/ `src/frontend`（React/Vite）という具体は、LAM 本体ではなく**配布先プロジェクト向けのテンプレート枠**と読める。LAM の実構造へ置換するとテンプレート機能が壊れる。一方で放置すれば虚偽の主張が残る。**注記を添えて両立させた** —— 虚偽だけを止め、枠は残す。`phase-rules.md` が既に「`src/` が実在しない（条文は残すが現時点では空振りする）」と自己申告しており、同じ扱いに揃う。

---

## §4 検収で棄却した指摘 —— 委譲の教訓

**wave_c テスト件数の指摘は 3 件中 2 件が誤検出だった。** 2 名の担当が**独立に同じ誤りを犯した**:

| ファイル | 文書の主張 | `def test_` grep | **実収集数** | 真の判定 |
|:--|--:|--:|--:|:--|
| `test_wave_c_magi_integration.py` | 26 | 31 | **31** | 不一致 |
| `test_wave_c_e2e_integration.py` | 21 | 16 | **21** | **一致**（誤検出） |
| `test_wave_c_gabriel_output.py` | 16 | 9 | **16** | **一致**（誤検出） |

原因は `grep -c "def test_"` が **parametrize 展開分を数え落とす**こと。

**教訓**: 「件数を数えろ」と委譲すると、**L2 は数え方を自分で選び、選び方は報告しない**。tool guidance に数え方（`--collect-only -q`）まで書くべきだった。これは memory `feedback-delegation-overhead-wallclock` の「委譲は検収込みで 1 工程」が効いた実例であり、検収を省いていれば PM 級ファイル 2 件に誤った値を書き込んでいた。

**修正フェーズでも同型が 1 件出た。** `scalable-code-review.md` を直した担当が「兄弟行の `docs/design/...` と `docs/tasks/...` も同様に怪しい」と報告したが、実測すると**3 件とも実在**した。境界（触ってよいファイル）を明示していたため担当は手を出さず、報告に留めた —— **境界が疑いを行動に変えるのを防いだ**。

**両方向に効いた**: L2 の指摘は棄却されることもあれば（件数 2 件・兄弟行 3 件）、L1 が拾えていなかったものを持ってくることもある（**A4・A5 は抽出フェーズが見落とし、修正フェーズの担当が発見した**）。

---

## §5 未処理（次回 retro の入力）

| # | 内容 | 理由 |
|:-:|:--|:--|
| 1 | `docs/specs/goal-driven-orchestration/` の `max_turns` 主張（design.md / config.md） | PM 級。§2 の機構判断とセット |
| 2 | L3 のターン打ち切りを実際に実装するか | `maxTurns` が `.claude/agents/` に効くかの実測が先 |
| 3 | `.claude/hooks/analyzers/tests` 565 件を `testpaths` に入れるか | 入れると「全数」が 1235 → 1800。挙動変更のため人間判断 |
| 4 | `task-decomposer` だけ `haiku`（同じ PLANNING 系の `requirement-analyst` / `design-architect` は `sonnet`） | roster に個別根拠の記載なし |
| 5 | §1 D 群の削除 | 削除は人間が実行（`rm` は deny） |

---

## §6 射程の限界（この監査が**見ていない**もの）

- **`docs/specs/` / `docs/adr/` / `docs/artifacts/` を対象にしていない。** 対象は「常時または条件付きで Claude に配送される文書」に絞った。仕様書・ADR は配送されず、読みに行ったときだけ効く
- **UNVERIFIED が約 35 件残る。** 大半はプレースホルダ（`draft-NNN.md` 等）・実行時生成の transient ファイル・外部ツール（`gotestsum` / `npm audit` 等）・外部 URL。「機械確認の手段がない」であって「誤りがない」ではない
- **意味の正しさは見ていない。** 見たのは「指す先が実在するか」「数値が合うか」であり、**規範の中身が妥当かは対象外**
- **抽出の網羅性は regex と L2 の読解に依存する。** 散文中に埋まった処方を取りこぼしている可能性は排除できていない

---

## 参照

- `docs/artifacts/retro-2026-08-17.md` §Step 2.5・P2（本監査の契機）
- `docs/artifacts/clause-gate-ledger.md` §C 機構 #7（「消えること」を検出する機構 / 本監査が扱ったのは**その裏側**）
- memory `feedback-delegation-overhead-wallclock`（§4 の教訓の既存形）
- memory `subagent-audit-supervision`（生指摘の棄却・降格が常発することの先行記録）
