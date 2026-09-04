# 配布 3 層の分類（managed / starter / 私物）

**日付**: 2026-09-04（セッション 28）
**等級**: SE 級（`docs/artifacts/`）
**根拠**: `docs/artifacts/2026-09-04-magi-distribution-form.md` §13.2（HGA #29 = 「層は 2 つでなく 3 つ」）+ ユーザー決定 2 件（2026-09-04）
**上位決定**: ADR-0010 追補 1（plugin を LAM リポジトリ内へ）/ 不変条件 I-1〜I-6 は存続

---

## §1 3 層の定義と、分類が不可逆である理由

| 層 | 意味 | 更新 | 利用者の編集 |
|:--|:--|:--|:--|
| **managed** | plugin が所有し、`/plugin update` で更新され続ける | 届く | 上書きされる（編集しない前提） |
| **starter** | `/lam:init` が初回だけ敷き、以後は利用者の資産 | 届かない | 自由 |
| **私物** | そもそも配らない（作者環境限定 / LAM 自身の記録） | — | — |

**managed → starter の降格は無害**（更新が止まるだけ）。**starter → managed の昇格は利用者の編集を破壊する**。
したがって **v1 で managed に入れなかったものは事実上永久に更新できない**。

**ユーザー決定（2026-09-04）: 「大きく始める」** —— 将来更新したくなりうるものは managed 側に倒し、
後から外す。基盤 rules と `docs/internal` も managed に含める。

> **実測の裏付け**: `lam-harness` 1.0.0（2026-07-02 / 別リポジトリ配置）は skills 14 件中 **9 件が現行 LAM に
> 存在しない**状態で 2 か月間放置された。更新が届かない層は静かに腐る。

---

## §2 managed（plugin 所有 / 更新が届く）

### 2.1 hooks — **7 件すべて**

`_hook_utils.py` / `_incident_patterns.py` / `autonomous_state.py` / `lam-stop-hook.py` /
`post-tool-use.py` / `pre-compact.py` / `pre-tool-use.py`

> **2026-09-04 実施済**: `pre-tool-use.py` の `_OUTBOUND_WRITE_BAN_ROOTS` /
> `_OUTBOUND_WRITE_ALLOW_ROOTS`（作者マシンの絶対パス 2 件）を
> `.claude/hooks-local/outbound-write-ban.py` へ**分離した**（MAGI §10.2 A4b）。
> 配布物側に作者パスが残っていないことは `test_distributed_hook_has_no_author_paths` が固定している。
> 条文・機構・テストの 3 点がすべて配布物の外に出た = **D-1 design §5 決定 D4 の目標状態を達成**。

### 2.2 agents — **12 件すべて**（ADR-0010 **I-6** 準拠）

`code-reviewer` / `design-architect` / `doc-writer` / `gabriel` / `goal-driven-grader` /
`goal-driven-l2-foreman` / `goal-driven-l3-executor` / `quality-auditor` / `requirement-analyst` /
`task-decomposer` / `tdd-developer` / `test-runner`

> **V6 の帰結**: agents も `plugin:agent` に名前空間化される。**skills 内の `subagent_type=gabriel` 等の
> 参照をすべて書き換える必要がある**（移行作業として計上）。

### 2.3 skills — **13 / 17 件**

`adr-template` / `autonomous` / `building` / `full-review` / `goal-driven` / `lam-orchestrate` /
`magi` / `quick-load` / `quick-save` / `release` / `retro` / `ship` / `spec-template`

`init-harness` は **`/lam-harness:init` に置換して廃止**（MAGI §13.5-D）。

### 2.4 scripts — **10 件**

`py_invoke.sh`（**単一 entry point / SPOF**）/ `detect-permission-mode.py` / `gd_guard.py` /
`gd_loop.py` / `gd_state.py` / `magi_dispatch.py` / `verify_distributable_claims.py` /
`verify_import_availability.py` / `verify_model_reference.py` / `verify_reference_resolution.py`

> **要判断 A**: `distill_lessons.py` と `distill-lessons.py` が**両方存在する**（アンダースコア版と
> ハイフン版 / どちらも「goal-driven メモリ蒸留」）。**片方は entry point、片方は実体**と読めるが、
> 配布前に重複の要否を確定すること。

### 2.5 rules — **14 / 19 件**

| ファイル | 理由 |
|:--|:--|
| `core-identity.md` | 第 0 原則（原理） |
| `permission-levels.md` | PG/SE/PM の定義と PM 級パス列挙（**hook 実装と対**） |
| `phase-rules.md` | 三フェーズ規律 |
| `code-quality-guideline.md` | Green State の判定基準 |
| `planning-quality-guideline.md` | PLANNING 成果物の品質基準 |
| `decision-making.md` | MAGI の実行時要約 |
| `security-commands.md` | コマンド許可マトリクス（**`settings.json` と対**） |
| `upstream-first.md` | 上流仕様優先 |
| `test-result-output.md` | テスト結果の出力規約 |
| `subprocess-encoding-convention.md` | Windows/Git Bash のエンコーディング規約 |
| `artifact-length-calibration.md` | 成果物の長さ較正 |
| `model-delegation-prompting.md` | 委譲プロンプトの書き方（汎用） |
| `auto-generated/README.md` + `auto-generated/trust-model.md` | TDD 内省パイプラインの**機構定義** |

### 2.6 docs/internal — **10 件すべて**

`00_PROJECT_STRUCTURE` 〜 `08_EXECUTION_DISCIPLINE` + `99_reference_generic`

> `08_EXECUTION_DISCIPLINE.md` は本日新設（`fable-l3-protocol.md` の S 分割 / §3-§9）。
> **Hierarchy of Truth 第 2 位を配布するか否か = HGA が名指しした不可逆点 I5**。
> 「大きく始める」の決定により **managed に含める**（含めない場合、`CLAUDE.md` テンプレートから
> 第 2 位への参照を落とすことになり、それは製品定義の変更にあたる）。

---

## §3 starter（初回だけ敷く / 利用者の資産）

| ファイル | 理由 |
|:--|:--|
| `CLAUDE.md` | プロジェクト憲法。Identity はプロジェクト固有 |
| `CHEATSHEET.md` | 「このプロジェクトのクセ」欄が利用者の資産 |
| `CHANGELOG.md` | 白紙から開始 |
| `SESSION_STATE.md` | 見出しのみ（中身は `/quick-save` が書く / gitignore 推奨） |
| `.claude/current-phase.md` | **hook が読む書式**（`^\*\*[A-Z]+\*\*`）。本日是正済 |
| `.claude/harness.json` | 適用バージョンの記録 |
| `.claude/rules/model-roster.md` | 層 → モデルの束縛。**構造は汎用だが値は利用者ごと** |
| `.claude/rules/terminology.md` | Project/Milestone/Step/Wave/Task の階層は汎用だが、**語彙は利用者が決める** |

> **要判断 B**: `model-roster.md` と `terminology.md` を starter にすると、**LAM 側の改善（新モデル世代への
> 追随・用語規約の改良）が利用者に届かない**。managed にすると利用者が自分のモデル構成を書けない。
> **HGA の逃げ道**（基盤層を小さく非論争的に保つ / 論争的な閾値は rules に置かず `userConfig` に出す）を
> 適用する余地がある。**v1 では starter とし、値と構造の分離は v2 の課題として記録する。**

---

## §4 私物（配らない）

### 4.1 作者環境限定

| 対象 | 理由 |
|:--|:--|
| `docs/private/fable-l3-protocol.md`（§0-§2 / 95 行） | 外部リポジトリの絶対パス・L3 宣言・Outbound Write Ban の SSOT。**本日 S 分割済**（§3-§9 は `docs/internal/08` へ） |
| `.claude/rules/hga-summoning.md` | Fable 召喚規律。作者の課金体制・weekly quota 前提 |
| `.claude/hooks-local/outbound-write-ban.py` | 作者マシンの絶対パスを持つ私的ガード。**2026-09-04 に `pre-tool-use.py` から分離済**（独立 PreToolUse hook / `exit 2` / `settings.json` に**追加**登録） |
| `.claude/scripts/hga_usage.py` | HGA 召喚コスト集計 |

### 4.2 LAM 自身の記録・一時物

| 対象 | 件数 | 理由 |
|:--|--:|:--|
| `.claude/scripts/r1_*.py` / `r-1-*.py` | 4 | R-1 Milestone のワンショット。`r-1-git-log-usage.py` は `D:/work7/LivingArchitectModel` をハードコード |
| `.claude/rules/auto-generated/rule-001.md` / `rule-002.md` | 2 | **このプロジェクトが学習した結果**。新規プロジェクトは空から始まるのが正しい |
| `.claude/skills/clause-gate` | 1 | 誕生ゲート台帳（LAM 固有の統治装置 / 天井 80・交換レート 1 対 1） |
| `.claude/skills/build-dashboard` + `.claude/scripts/build_dashboard.py` + `dashboard/` | — | LAM の `SESSION_STATE.md` 書式と Milestone 語彙に強く依存。**fresh clone の赤 1 件の原因でもある** |
| `.claude/agent-memory/` | 42 | `b3-` / `b5-` 等 LAM 固有の設計文脈 |
| `docs/specs/` / `docs/adr/` / `docs/artifacts/` / `docs/slides/` | 303 | LAM 自身の記録 |
| `README.md` / `README_en.md` / `QUICKSTART.md` / `QUICKSTART_en.md` | 4 | LAM の紹介。利用者のプロジェクトに敷くものではない |

> **要判断 C**: `.claude/skills/update-model` は「モデル世代交代の手順」であり**どのプロジェクトでも起きる事象**
> だが、`model-roster.md`（starter）と `verify_model_reference.py`（managed）に依存する。
> **v1 では managed に置き、roster が starter であることを前提に動くよう手順側で吸収する。**

---

## §5 集計

| 層 | hooks | agents | skills | scripts | rules | docs/internal | ルート文書 |
|:--|--:|--:|--:|--:|--:|--:|--:|
| **managed** | 7 | 12 | **14**（update-model 含む） | 10 | **14** | 10 | 0 |
| **starter** | 0 | 0 | 0 | 0 | 2 | 0 | 6 |
| **私物** | （定数 2 件のみ分離） | 0 | 3 | 8 | **3** | 0 | 4 |

> **rules の内訳（19 件）**: managed **14**（上位 12 + `auto-generated/README.md` + `auto-generated/trust-model.md`）/ starter 2（`model-roster` / `terminology`）/ 私物 3（`hga-summoning` / `auto-generated/rule-001` / `auto-generated/rule-002`）。
> 2026-09-04 の骨格構築時に、本表の旧値（managed 13 / 私物 4）が §2.5 の列挙と食い違っていたため是正した。

**配布物コア = 66 ファイル前後**（+ `docs/internal` 10 + starter 8）。
現在の追跡 663 ファイルに対し、**利用者に「有効化される」のは 1 割強**になる。

---

## §6 この分類が要求する検査（HGA §13.5-B / A5 の完成形）

分類は**リストであり、リストは腐る**。したがって以下 2 検査を機構として置く（維持リスト不要・基質から導出）:

| # | 検査 | 内容 |
|:-:|:--|:--|
| **T1** | **K4 の包含検査** | plugin が敷くテンプレートのそれぞれについて、**同一内容のファイルが開発側に存在する**こと。`lam-harness` 1.0.0 の 2 か月 stale を構造的に不可能にする |
| **T2** | **plugin 内参照の閉包検査** | plugin ディレクトリ内のファイルが参照する先は、**plugin 内か `${CLAUDE_*}` 環境変数形式**でのみ閉じること。作者環境の絶対パス・`docs/artifacts/` 等への参照を弾く |

既存の **R3 機構 #10**（`verify_distributable_claims.py` = 存在の主張の検査）と同じ系統。

> **2026-09-04 実装済**: `.claude/scripts/verify_plugin_containment.py` +
> `.claude/tests/scripts/test_verify_plugin_containment.py`（**15 tests** / 陰性対照・偽陽性対照つき）。
> 台帳 §C に **機構 #11 / #12** として登録し、`/release` Phase 2.5 に接続した。
> **導入直後に 5 件を検出**（4 件は同日作成の `docs/internal/08_EXECUTION_DISCIPLINE.md` の
> `docs/private/` 参照 / 1 件は `subprocess-encoding-convention.md` の作者絶対パス）—— いずれも是正済。
>
> **T2 の射程は v1 では狭い**（作者絶対パス + `docs/private/` のみ）。`docs/artifacts/` 等への
> dangling 参照 60 件超は §7 の既知ギャップとして残る。

---

## §7 未解決（本分類では決めない）

| # | 内容 | 送り先 |
|:-:|:--|:--|
| A | `distill_lessons.py` / `distill-lessons.py` の重複 | 配布前に要確定 |
| B | `model-roster.md` / `terminology.md` の「構造は配る・値は配らない」分離 | v2 |
| C | `update-model` skill が starter に依存する構造 | v1 は手順側で吸収 |
| D | ランタイム（Python / bash）不在時の挙動 | **不可逆点 I4** / `/lam-harness:init` で検査して完了を拒む案が HGA 推奨 |
| E | `personal > project` 解決順と `skillOverrides` の再裏取り | ADR-0010 **R-1** の未了分 |
| F | `~/claude-global-assets` の `lam-harness` 1.0.0 の quarantine | ADR-0010 **M-2** 準拠 |
