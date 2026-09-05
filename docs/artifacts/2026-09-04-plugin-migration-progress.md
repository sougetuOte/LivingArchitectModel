# plugin 移行の進捗台帳（セッション 28 → 次セッション引き継ぎ）

**日付**: 2026-09-04（セッション 28）
**等級**: SE 級（`docs/artifacts/`）
**位置づけ**: 配布形態を plugin へ移す作業の**実行状態**を持つ。**決定の正本は別**（下記）。

| 種別 | 正本 |
|:--|:--|
| **決定** | `docs/artifacts/2026-09-04-magi-distribution-form.md`（MAGI AoT 6 Atom + gabriel 2 巡 + HGA #29） |
| **所在の決定** | `docs/adr/0010-global-claude-assets-governance.md` **追補 1** |
| **3 層分類** | `docs/artifacts/2026-09-04-distribution-layer-classification.md` |
| **実行状態** | **本ファイル** |

---

## §1 これだけは再導出しないこと（結論の要約）

1. **配布形態は plugin + marketplace**。ADR-0010（2026-07-04）が既に決めており、本セッションの MAGI + HGA も独立に同じ結論に到達した。**争点ではない**
2. **リポジトリは割らない**（D-1 死んだ案 #5 / ユーザー撤回 + HGA #22）。plugin は LAM リポジトリ内に置く（ADR-0010 追補 1 / ユーザー決定 2026-09-04）
3. **self-hosting は維持**（ユーザー裁定 2026-07-27 / 「放棄可」は**同日中に本人が撤回済**）
4. **名前空間は受容済**（ADR-0010 **I-4**「スキル参照は名前空間を常に明示する」）。`/lam-harness:ship` になる。**agents も `plugin:agent` に名前空間化される**（V6 実測）
5. **rules は plugin では配れない**（コンポーネント在庫は skills / agents / hooks / MCP / LSP の 5 種のみ）。`/lam-harness:init` がプロジェクトへ敷く
6. **managed 集合は「大きく始める」**（ユーザー決定 2026-09-04）。starter → managed の昇格は利用者の編集を壊すため事実上不可逆
7. **ランタイム不在時は init が完了を拒む**（ユーザー確認済 / 不可逆点 I4）

### 本セッション最大の発見

**D-1 は `fable-l3-protocol.md` を「S（要分割）を認める理由」の実例として名指ししながら、判定は X（丸ごと私物）を出していた。** 243 行中 25 行（10%）の私的記述のために、約 218 行の製品中核が配布境界の外へ出ていた。design §4 が「どちらも誤りである」と書いた 2 択のうち、誤りの側の結果になっていた。2026-08-29 に直した「`CLAUDE.md` の実況発火点から `PLANNING` 修飾が脱落」は、その最初の実害である。

---

## §2 実行状態

| 手順 | 内容 | 状態 |
|:-:|:--|:--|
| 0 | `init-harness` 欠陥 2 件の修正（`.json` → `.md` / 過大な名乗り） | **完了** |
| 0' | 条文の S 分割（§2 \| §3 / §3-§9 → `docs/internal/08_EXECUTION_DISCIPLINE.md`） | **完了** |
| 0'' | 要検証 V1-V8 | **完了**（結果は MAGI §13.6） |
| 1 | plugin 骨格 + T1/T2 検査（R3 機構 #11 / #12） | **完了** |
| 2 | Outbound Write Ban を project 層へ分離 | **完了**（D-1 決定 D4 の目標状態を達成） |
| **3** | **`/lam-harness:init` の実装 + ランタイム検査** | **完了**（2026-09-04 / 下記 §2.1） |
| ~~4~~ / ~~5~~ | **着手順を MAGI で再設計した（2026-09-04）**。手順 4 は独立工程ではなく **P3 の中相**になった。新しい相分けは下表 | **`2026-09-04-magi-migration-order.md` が正本** |
| 6 | clone-template の廃止判断 | 未 |

### 手順 4 / 5 に代わる相分け（MAGI 2 巡 / gabriel critical → warning / `2026-09-04-magi-migration-order.md`）

分岐条件は「重要度」でも「リスク」でもなく **「呼び出し先が存在するか」**。
skills / agents は名前空間が呼び出し先を分離するので**複製相が安全**。
hooks は**イベント発火型で「参照切替」という操作が存在せず**、複製した瞬間に二重発火する
（`docs/adr/0010-...md:286` =「hook は merge され置換されない。両方走る」/ **gabriel が発見**）。

| 相 | 内容 | 状態 |
|:-:|:--|:--|
| **P0** | `get_project_root()` に `CLAUDE_PROJECT_DIR` 経路 ＋ `__file__` 経路を通るテスト | **完了**（2026-09-04 / 下記 §2.2） |
| **P1** | `--plugin-dir` 予行（**hooks.json を置かない**）。**2 回に割る** —— (1) plugin ロード経路の実証は今できる / (2)(3) bare `subagent_type` 解決・description 衝突は **agents 複製後でないと測れない**（MAGI 記録 §P1 の位置の調整） | **次はここ**（**ユーザー操作** = 別セッション起動） |
| **P2** | skills: 複製 → 参照切替 → 撤去 | **複製相 完了**（2026-09-05 / 14 skills / 下記 §2.3）。次は参照切替 |
| **P3** | agents: 複製 → **名前空間化（= 旧 手順 4）** → 撤去 | **前半（複製 12 件）完了**（2026-09-05）。後半は P2 参照切替の後 |
| **P4** | hooks: 捨てプロジェクトで隔離検証 → **セッション境界でアトミック入れ替え**（複製相なし） | 未 |
| **P5** | `permissions.allow` の手作業 ＋ `init` Step 6 への反映判断 | 未（**ユーザー**） |

### 手順 3 の要件（次セッションの入口）

- `init-harness` を **`/lam-harness:init` へ置換**（skill 自体は廃止 / MAGI §13.5-D）
- 敷く対象は `templates/managed/`（rules 14 + docs-internal 10）+ starter（`CLAUDE.md` / `CHEATSHEET.md` / `CHANGELOG.md` / `SESSION_STATE.md` / `.claude/current-phase.md` / `.claude/harness.json` / `model-roster.md` / `terminology.md`）
- **ランタイム検査**: Python / bash が無ければ**完了を拒む**。根拠は V4 —— hook の `exit 2` 以外の非零終了は**非ブロッキング**で、トランスクリプトに `hook error` 通知 + stderr 1 行目が出る。**インタプリタ不在の 127 も同じバケツ**なので、放置すると fail-open とノイズが同時に起きる。init は「一度きり・利用者起動・対話的」を満たす唯一の地点であり、K6 が棄却した 7 案のいずれにも触れない
- **Layer 1（`settings.json` の `permissions.deny`）は届かないことを明示的に宣言する**（HGA §13.5-E）。「入れた瞬間に使える」の射程は Layer 0（規範）+ Layer 2（hook）まで

### §2.1 手順 3 の実施記録（2026-09-04 / セッション 29）

| 成果物 | 内容 |
|:--|:--|
| `plugins/lam-harness/skills/init/SKILL.md` | Step 0 でランタイム検査、失敗時は**部分適用せず中止**。Step 6 で Layer 1 未適用を明示し手作業手順を提示。配置対象は**テンプレートディレクトリから導出**（維持リスト不要） |
| `plugins/lam-harness/scripts/check-runtime.sh` | `py_invoke.sh` と同じ探索順（venv-first → fallback）＋「存在するが起動不能」の判定。失敗時は stderr に理由と対処 |
| `plugins/lam-harness/templates/starter/` | **8 件**（`.claude/` は `dot-claude/` に読み替えて格納）。`model-roster.md` / `terminology.md` は「構造は配る・値は記入欄」の形にした（§6 B の完全な分離は v2） |
| `.claude/tests/plugin/test_lam_harness_init.py` | **12 tests**。starter 集合の一致 / `current-phase.md` の hook 書式 / ランタイム検査の**陽性 + 陰性対照**（PATH から python を除き `.venv` の無い CWD で実行）/ 旧 skill の撤回 |
| `.claude/skills/init-harness/` | **削除**（MAGI §13.5-D =「修正して残す期間は存在の主張が半分正しい期間」） |

**機構 #10 の拡張（副産物 / 手順 3 で必要になった）**: 旧 `_COMMAND_PAT` は `/lam-harness:init` を
**`/lam-harness` で切って誤抽出**していた（`:` が文字クラス外）。名前空間つきを 1 トークンとして拾い、
`existing_commands` に **`plugins/<plugin>/skills/<skill>/` 経路**を追加した。**両経路とも実体から導出**する
（対応表を持たない）。陰性対照 4 件つき。

**検証**: `1305 → 1321 passed / 14 skipped` / 機構 #10・#11・#12 いずれも OK。

> **ランタイム検査に「テスト専用の分岐」を置かなかった**: 最初 `LAM_FORCE_NO_PYTHON` 環境変数で
> 陰性対照を作ろうとしたが、本番コードにテスト専用経路を残す形になるため取りやめ、
> **PATH から python を除き `.venv` の無い一時ディレクトリで実行する**形に変えた。
> 「実環境で起きる状況をそのまま再現する」ほうが計器として強い。

---

### §2.2 P0 の実施記録（2026-09-04 / セッション 29）

**変更**: `_hook_utils.get_project_root()` の解決順を
**`LAM_PROJECT_ROOT` → `CLAUDE_PROJECT_DIR` → `__file__`** にした（`_env_dir()` に共通化）。
最も弱い `__file__` 経路に落ちた場合は **その事実を stderr に出す**。

**なぜ移動より先に必要だったか**: hooks が plugin cache に入ると `__file__` 導出の root が
cache を指す。被害は 3 段階で**深いほど静かになる** —— 状態ファイルが `/plugin update` で消える →
`current-phase.md` が読めずフェーズガードが黙って死ぬ → **`normalize_path()` が誤った root で
相対化するため `_PM_PATH_PATTERNS` が一切マッチせず PM 級承認ゲートが丸ごと no-op になる**。

**なぜ既存テストが検出できなかったか**: `.claude/tests/` は `LAM_PROJECT_ROOT` を設定して走るため
**`__file__` 経路をそもそも通らない**。escape hatch が計器を盲目にしていた。
`test_get_project_root_default` は名前に反して `__file__` 経路を検査していなかった（両 env を外して是正）。

**canary は推測しない**（gabriel 2 巡目の指摘 (a)）: 「`.claude` があれば健全な root」という判定は、
`marketplace add` がリポジトリ全体を `.claude` ごと clone するため **clone を健全と誤検知**し fail-open する。
代わりに**最も弱い経路を使った事実そのものを可聴化**する（`rule-001` 恒久解 (c) と同型 = 推論をやめる）。

**検証**: `1321 → 1325 passed / 14 skipped`。加えて**実働で確認** —— 変更後のコマンド実行が
`.claude/logs/permission.log`（**プロジェクト側**）に記録されることを実測した（hook が生きている証拠）。

> **設計の訂正 1 件**: MAGI の当初結論は解決順を `CLAUDE_PROJECT_DIR` 最優先とし、
> 「hook 経路では必須にして落とす」としていたが、**2 点とも誤り**だった（順序を逆にすると
> セッション内テストの隔離が崩れる / 「hook 文脈の実行時判定」は推測の再導入）。
> **gabriel は 2 巡ともこれを指摘していない** —— probe は書かれた設計を検証するが、
> **実装して初めて出る誤りには構造的に届かない**。詳細は MAGI 記録の §訂正。

### §2.3 P2 複製相の実施記録（2026-09-05 / セッション 30）

**14 skills を `plugins/lam-harness/skills/` へ複製した**（`clause-gate` と `build-dashboard` は
LAM 固有ゆえ非配布 / §4.2）。project 側はまだ生きており、名前空間が呼び出し先を分離する。

| 起きたこと | 内容 |
|:--|:--|
| **機構 #12 が即座に鳴った** | `release/SKILL.md` が閉包検査を**説明する文**の中で `docs/private/` を literal で書いていた。`subprocess-encoding-convention.md` が 2026-09-04 に踏んだ「違反の説明に違反そのものを書けない」型 |
| **xfail(strict) が XPASS で落ちた** | starter の前方参照 6 種 8 箇所が複製で実体を得た瞬間。mark 撤去を促され、テストを 1 本へ戻した（**strict xfail を「解消の検知器」として使った実例**） |

#### 発見: 配布 skills が呼ぶ scripts を誰も配っていなかった

`.claude/scripts/*` への呼び出しは **11 種 47 箇所**（うち `py_invoke.sh` が 30）。しかし
`templates/managed/` には `rules` と `docs-internal` しか無く、**利用者が `/lam-harness:ship` を
打つと存在しない `py_invoke.sh` を呼んで落ちる**状態だった。§5 集計表は scripts を managed と
分類していたので、**決定は下りていて実装が追随していない**型（本日 2 例目）。

- `templates/managed/scripts/` に **12 件**を配置（10 件リスト + `distill` ペア = 分類側の漏れを是正）
- 機構 #11 の `_MANAGED_AREAS` に `scripts` を追加（恒等性が自動で守られる）
- **維持リストを持たない検査**を追加: plugin skills の本文から呼び出し先を導出し、配布集合との差を落とす

#### 未処理で残したもの（参照切替相へ）

| # | 内容 |
|:-:|:--|
| 1 | **`clause-gate` への参照 2 件**（`update-model` は `/clause-gate` を手順として指示 / `retro` は台帳を参照）。**機構 #10 は LAM リポジトリ基準で実在判定するため、この「配布後に消える参照」を構造的に検出できない**（LAM 内では実在するので永久に緑） |
| 2 | `quick-save` の `build_dashboard.py` 呼び出しは失敗許容だが、**利用者環境では毎回警告が出る**。「常時鳴る計器」型に近い |
| 3 | `docs/artifacts/` の具体ファイル参照（`clause-gate-ledger.md` / `maxturns-probe-2026-08-21.md` 他）。**未解決 C と同型だが、C は規範側の話であり skills まで射程が広がった** |

#### 撤去相の前提（確定）

`.claude-plugin/marketplace.json` は既存（`source: "./plugins/lam-harness"` = 相対パス形式 /
上流仕様に合致）。一方 `.claude/settings.json` に **`enabledPlugins` は未設定**であり、
**撤去相はユーザーの install 操作待ち**（`/plugin marketplace add` → `/plugin install --scope project`）。

### §2.4 self-hosting 形態の決着と、要検証 6 件の解消（2026-09-05 / セッション 30）

**local install はスナップショットである**ことが実測で判明し、配布形態 MAGI §A3 の前提が崩れた。
MAGI（gabriel 2 巡とも `refuted & critical` / 2 巡目 `abort` = AC-W-C-7 到達）→ **HGA #30** で決着。
続けて HGA が要求した**要検証 6 件を全て実測**し、さらに**上流の公式ドキュメントと issue tracker を調査**した。

**全文は `docs/artifacts/2026-09-05-magi-selfhosting-form.md`**（末尾の「対策の確定版」が正本 /
前半 2 節は gabriel に退けられた記録であり決定ではない）。

#### 移行計画に直接効く 4 点

| # | 内容 |
|:-:|:--|
| **1** | **P4 の前提「project hooks = 0」は既に偽**（`hooks-local/outbound-write-ban.py` が PreToolUse に登録済 / 実測）。新不変条件は「**同一スクリプトが 2 層に居ない**」で、**上流仕様と一致する**ことも確認した |
| **2** | **検出器が要るのは P4 の前ではなく P2 撤去相の前**。LAM が install した瞬間から skills がスナップショットになる（現在 LAM は未 install で 100% project 層） |
| **3** | **marketplace 名を `lam` → `sougetuote-lam` へ改名済**。同名 add は無警告で既存を上書きし（実演）、上流は **not planned** で直さない（#44042）。名前の一意性が唯一の防御線 |
| **4** | 検出器は **`claude plugin list --json` / `marketplace list --json`** で実装する。上流の私有状態を自前パースしない |

#### 上流に既に用意されていたもの（自前で作らない）

- **開発ループ**: `--plugin-dir`（install せず直読み・install 済みより優先）+ `/reload-plugins`
- **`claude plugin` CLI 一式**（`--json` / `--strict` 付き）—— **対話セッション不要で自動化できる**
- **`claude plugin validate --strict`** と **`claude plugin tag`** を `/release` に組み込み済（2026-09-05）
- 公式 Tip「**standalone `.claude/` で回し、共有段階で plugin に変換せよ**」= **LAM の現在位置が公式の推奨そのもの**

#### 上流の既知問題（4 件とも既知 / 2 件は「対応しない」）

| 問題 | 状態 |
|:--|:--|
| キャッシュ陳腐化 | 未解決（#14061 が Open のまま / 重複多数） |
| 同名 marketplace の無警告上書き | **Closed as not planned**（#44042） |
| `enabledPlugins` の無言スキップ | Closed as duplicate（#32607）/ 検出機構なし |
| hooks 二重発火 | **Closed as not planned**（#40826 / **LAM とほぼ同一のユースケースが起票されている**） |

**次セッションの実装対象**: 存在検出（`hooks-local/` の SessionStart）/ 鮮度検出（`CLAUDE_PLUGIN_ROOT` 判定）/
復旧手順（CLI 2 行 + 内容ハッシュ確認）。

### §2.5 着手順の再設計と、様式の恒久修正（2026-09-05 / セッション 31）

**正本は `docs/artifacts/2026-09-05-magi-migration-sequence.md`**（MAGI 2 巡 + gabriel 3 巡 + **HGA #31 / #32**）。
ここには次セッションが最初に知るべきことだけを置く。

| # | 内容 |
|:-:|:--|
| **1** | **着手順を「項目 + 並列配列」から「(A) 網羅表 / (B) 単一線形シナリオ 15 ステップ / (C) 証人照合 + 陰性対照」へ全面改稿**（HGA #31）。ゴールはユーザー決定により **第三者 E2E 先行 → その後 self-hosting** |
| **2** | **被検体はワークツリーでなく「HEAD の clone」**。別名 marketplace で directory 登録すれば **push なしでコミット漏れを検出できる**。github source はループ外の最終 1 発 |
| **3** | **分解表の様式を恒久修正**（HGA #32）—— 「依存 / 並列可否」列を廃し「**読む状態 / 書く状態**」列へ。gabriel rubric 観点 4 に「**状態列なき並列主張はそれ自体 critical**」を追加。`decision-making.md`（PM 級）/ `magi/SKILL.md` / `anchor-format.md` / `gabriel.md` に適用済 |
| **4** | **機構 #11 の射程を skills / agents（将来の hooks）へ拡張** —— 3 領域しか見ておらず、**本セッションで実際に 4 件の乖離を緑のまま通した**ため |
| **5** | **`lam-orchestrate/references/magi-skill.md` を両側から削除**し、`v5-fat-reduction` §4 に superseded 注記（PM 級） |
| **6** | **【未解決 / 次セッション】dangling 参照の射程は「managed 規範」ではなく「配布物全体」**。skills / agents にも LAM 固有実体への参照がある |
| **7** | **【次セッション / ユーザー指示】E2E 着手前に「範囲自体を問い直す全体レビュー」**。本セッションで**射程の見積りが 3 回とも小さかった**ため（詳細は正本 §4） |

---

## §3 いま触ると壊れるもの（重要）

**hooks / agents / skills / scripts はまだ `.claude/` にある。移動は手順 5 まで待つこと。**

plugin コンポーネントは**インストールされて初めて有効になる**。いま `.claude/` から `plugins/` へ移すと、その瞬間に無効化される（LAM 自身のハーネスが死ぬ）。移動と local install は同じ波で行う。

**templates が二重に存在するのは意図的**。rules と docs/internal は plugin コンポーネントとして配れないため、リポジトリ内に 2 部できる。これは `lam-harness` 1.0.0 を殺したのと同じ構造だが、**恒等性を機構 #11 が強制する**点が違う。「重複しているから片方消そう」としないこと —— **消すと K4 の検査対象が消える**。

---

## §4 未コミット（`/ship` はユーザー実行）

> **セッション 28 分は 2026-09-04 に push 済**（`eae403b..e89106b` / 7 コミット）。以下は**セッション 29 分**。

推奨コミット分割（依存順 / **手順 3 → 機構 #10 → P0 → 記録** の順で bisect が保たれる）:

| # | type(scope) | 内容 | 主なファイル |
|:-:|:--|:--|:--|
| 1 | `feat(dist)` | **`/lam-harness:init` の実装 + `init-harness` の撤回**（手順 3） | `plugins/lam-harness/skills/init/` / `scripts/check-runtime.sh` / `templates/starter/` 8 件 / `.claude/tests/plugin/` / **削除** `.claude/skills/init-harness/` |
| 2 | `fix(clause-gate)` | **機構 #10 が名前空間つき plugin コマンドを解決できるようにした**（`/lam-harness:init` を `/lam-harness` で誤抽出していた） | `verify_distributable_claims.py` / 同テスト |
| 3 | `fix(hooks)` | **P0** = `get_project_root()` に `CLAUDE_PROJECT_DIR` 経路 ＋ `__file__` 経路を通るテスト | `_hook_utils.py` / `test_hook_utils.py` |
| 4 | `docs(magi)` | **移行順の再設計**（MAGI 2 巡 / gabriel critical → warning）＋ 進捗台帳更新 ＋ CHANGELOG | `2026-09-04-magi-migration-order.md` / 本ファイル / `CHANGELOG.md` |

**意図的に未追跡**: `docs/private/2026-08-26-positioning-and-lecture-notes.md`（ユーザーの別案件資料）

### セッション 29 の検証状態

```
pytest .claude/tests .claude/hooks/tests   → 1325 passed / 14 skipped（1301 → +24）
verify_distributable_claims.py (機構 #10)  → OK（実在 skill 17 = project 16 + plugin 1）
verify_plugin_containment.py  (機構 #11/#12) → OK
実働確認: 変更後の hook が .claude/logs/permission.log（プロジェクト側）へ記録
```

**gitignore 対象**: `SESSION_STATE.md` / `docs/daily/` / `.claude/test-results.xml`
**意図的に未追跡**: `docs/private/2026-08-26-positioning-and-lecture-notes.md`（既存 / ユーザーの別案件資料）

---

## §5 検証状態（セッション終了時点）

```
pytest .claude/tests .claude/hooks/tests   → 1301 passed / 14 skipped
verify_distributable_claims.py (機構 #10)  → OK
verify_plugin_containment.py  (機構 #11/#12) → OK
追跡ソースへの作者絶対パス混入            → 0
```

**fresh clone の 3 件の赤は未解消**（`test_parse_with_real_git_log` = 履歴依存 / `test_outbound_write_ban` の相対形 2 件 = 配置依存）。手順 5・6 の範囲。

---

## §6 未解決（送り先つき）

| # | 内容 | 送り先 |
|:-:|:--|:--|
| ~~A~~ | ~~`distill_lessons.py` / `distill-lessons.py` の重複~~ | **解決済（2026-09-04）— 重複ではない**（下記 §6.1） |
| B | `model-roster.md` / `terminology.md` の「構造は配る・値は配らない」分離 | v2 |
| C | managed 規範から `docs/artifacts/` 等への dangling 参照 **60 件超** | T2 の射程 v2 / 公開前 |
| D | `personal > project` 解決順と `skillOverrides` の plugin 無効の再裏取り | **ADR-0010 R-1 の未了分** |
| E | `~/claude-global-assets` の `lam-harness` 1.0.0（4 プロジェクトに project スコープで導入済・**全て disabled**）の quarantine | ADR-0010 **M-2** 準拠 |
| F | `CLAUDE.md` 251 行（公式目安 200 行超） | 前セッションからの持ち越し |
| G | `docs/private/` と規律 8 件の所在整理 | **S 分割で部分的に前進**（`fable-l3-protocol.md` は 95 行に縮小）。残りは未着手 |

---

### §6.1 A の決着 —— **重複ではなく意図的な 2 ファイル構成**（2026-09-04 / セッション 29）

| ファイル | 役割 |
|:--|:--|
| `distill_lessons.py`（アンダースコア / 15,996 B） | **実装本体**。Python モジュール命名規約に従う = テストから `import distill_lessons` できる |
| `distill-lessons.py`（ハイフン / 962 B） | **entry point のみ**。`from distill_lessons import main` して呼ぶだけの薄い層。`goal-driven/SKILL.md` フロー[8] がこの名前で呼ぶ |

B-3 W4-T1 の設計であり、`.claude/agent-memory/tdd-developer/project_gd_distill_w4t1.md` に
2 ファイル構成である旨が記録されていた。**片方を消すと、テストの import かフロー[8] の
呼び出しのどちらかが壊れる。** 手順 5 での移動時も 2 件セットで動かすこと。

> **なぜ「重複」に見えたか**: 台帳を書いた時点で中身を開いておらず、名前の類似だけで
> 判定していた。ファイルサイズ（16 KB vs 1 KB）を見れば片方が wrapper だと分かる。

### §6.2 D の部分回答 —— ADR-0010 **R-1** の再裏取り（2026-09-04 / context7 経由）

| 項目 | 結果 |
|:--|:--|
| `skillOverrides` が plugin skill に効くか | **未確定のまま**。公式例のキーは素の skill 名（`{"legacy-context": "name-only", "deploy": "off"}`）であり、名前空間つきのキーを取る記述は見つからなかった。**「無効」と断定できる根拠も見つかっていない** |
| `personal > project` の解決順 | **今回の取得範囲では再確認できず**（当該記述に到達しなかった）。ADR-0010 制定時の裏取りが最後 |
| **新発見: `strictPluginOnlyCustomization`** | **settings に実在する**。`["skills"]` を指定すると **user / project パスと account sync からの custom skill 読み込みを禁止**し、plugin / bundled / managed policy のみ許可する。`["skills", "hooks"]` のように複数指定可 |

**`strictPluginOnlyCustomization` は ADR-0010 の脅威モデルに直接効く。** I-1 が防ごうとしていたのは
「personal 層が project を上書きする」ことであり、I-2 は「`skillOverrides` が plugin に効かないので
enable 粒度が唯一の防御線」と述べていた。**この設定は enable 粒度とは別の、より上流の防御線**である。

**ただし採用可否は判定しない**（`upstream-first.md` §採用可否の二段構え / 段階 1 = 実在性は確認、
段階 2 = LAM の設計思想との適合性は未評価）。**ADR-0010 の更新は PM 級**であり、ユーザー判断に送る。

## §7 このセッションで判明した運用上の事実（次セッションが同じ轍を踏まないため）

- **`settings.json` の `hooks` セクションは AI から編集できる**。auto mode がブロックするのは `permissions` 固有。記憶 `settings-json-edit-blocked` を同日修正済（丸ごと「編集不可」と覚えていると不要な手作業依頼を出す）
- **記憶ファイルの frontmatter が本文と食い違っていた** —— `lam-positioning-and-motive` の description が撤回済みの内容を述べており、L1 がそれを読んで**幻の争点を MAGI に立てた**（gabriel 第 1 回が指摘）。同日修正済
- **heredoc 経由の Python で `\n` のエスケープが潰れる**ことがある。改行を含む文字列を書くときは `splitlines()` 等でエスケープを避ける
- **台帳 §C の機構件数が「8 件」のまま 2 週間ずれていた**（#9 / #10 追加時に未追随）。12 に是正済
