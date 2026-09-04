# MAGI — plugin 移行 手順 4 / 手順 5 の着手順（AoT 適用モード）

**日付**: 2026-09-04（セッション 29）
**等級**: SE 級（`docs/artifacts/`）
**モード**: **AoT 適用**（判断ポイント 4 / 影響レイヤー 6 / 選択肢 3+）
**gabriel probe**: **2 巡**（1 巡目 `refuted`/`critical`/`re-magi` → 再 MAGI 1 ラウンド → 2 巡目 `refuted`/**`warning`**/`proceed`）
**書き込み権限**: CASPAR（Single-Writer）

> **HGA は召喚していない。** 新ゲート条件 1（`refuted & critical` ×2）は **未到達**（critical → warning と下がったため）。
> 条件 2 も満たさない —— 残る論点はすべて**実測で潰せる未検証の仮定**であり、HGA が効く「実測で潰せない
> 概念的 crux」ではない。**P1 の実測が想定と食い違ったときが召喚のタイミング**である。

---

## Step 0: AoT Decomposition

| Atom | 判断内容 | 依存 |
|:--|:--|:--|
| **A1** | `get_project_root()` の `__file__` 導出をどうするか | なし |
| **A2** | `permissions.allow` の py_invoke prefix が壊れる問題 | なし |
| **A3** | 手順 4 を手順 5 の前 / 同時 / 後のどれにするか | A5 |
| **A4** | 移動の粒度（一括 / コンポーネント種別ごと） | A1, A2 |
| **A5** | bare な `subagent_type` が plugin agent に解決するか | なし |
| **A6** | 予行演習（`--plugin-dir`）をどこに挟むか | A4 |

**既存 ADR の走査**: ADR-0001〜0011 を確認。**着手順を決めた ADR は無い**。ADR-0010 **I-4** が
「スキル参照は名前空間を常に明示する」と決めているのは**方針**であって順序ではない。

---

## 調査で得た事実（MAGI の入力 / すべて本セッションで裏取り）

| # | 事実 | 出所 |
|:-:|:--|:--|
| **F1** | plugin hooks は `hooks/hooks.json`（または plugin.json インライン）で宣言し `${CLAUDE_PLUGIN_ROOT}` で解決する | 上流 code.claude.com（context7） |
| **F2** | `permissions.allow` に `Bash(bash .claude/scripts/py_invoke.sh *)` がある。scripts が動くと prefix が効かなくなるが `permissions` は **AI 編集不可**（V8 ハードブロック） | `.claude/settings.json` 実測 |
| **F3** | `claude --plugin-dir <path>` でインストールせずセッション限定ロードができる（同名 marketplace plugin を上書き） | 上流 |
| **F4** | `_hook_utils.get_project_root()` は **`__file__` から 2 階層上って** root を導出する。`$CLAUDE_PROJECT_DIR` を参照していない | `.claude/hooks/_hook_utils.py:96-114` 実測 |
| **F5** | 上流は「plugin namespace は**プラグイン間の曖昧性解消のため**に前置する」と書く。bare な `subagent_type` の解決可否は**未確認** | 上流（`claude --agent my-plugin:security-reviewer` の説明） |
| **F6** | **hook は設定レベル間で merge され置換されない。plugin hook と project hook は両方走る** | `docs/adr/0010-...md:286`（**gabriel 1 巡目の指摘で発見**） |

> **F6 はリポジトリに既にあった。** L1 は §13.5 / §13.6 は読んだが追補 1 の当該行を取り出せておらず、
> **gabriel に指摘されて初めて参照した**。前回 retro の P3（記憶の frontmatter だけを読んで争点を立てた）と
> **同じ型**である —— 資料は在ったが、読む範囲を自分で狭めていた。

---

## Step 1-3: Divergence / Debate / Convergence

### Atom A1: `get_project_root()` の `__file__` 導出

**[MELCHIOR]**: env 優先経路（`LAM_PROJECT_ROOT`）が既にある。1 行足せば済むので移動と同時でよい。

**[BALTHASAR]**: 間に合わない。被害は 3 段階で、**深いほど静かになる**:

1. 状態ファイル（`tdd-patterns.log` / `permission.log` / PM キャッシュ）が plugin cache に書かれる →
   上流が「`${CLAUDE_PLUGIN_ROOT}` に永続状態を置くな」と明記するとおり **`/plugin update` で消える**
2. `current-phase.md` が読めない → **フェーズ依存のガードが黙って死ぬ**
   （`init-harness` の `.json` 欠陥・`rule-001` 観測 #6 と同型 / LAM は既に 2 回踏んでいる）
3. **最悪**: `normalize_path(file_path, project_root)` が誤った root で相対化するため
   `_PM_PATH_PATTERNS` が一切マッチせず、**PM 級承認ゲートが丸ごと no-op になる**

さらに **既存テストはこれを検出できない**。`.claude/tests/` は `LAM_PROJECT_ROOT` を設定して走るため
**`__file__` 経路をそもそも通らない**。計器が escape hatch で盲目になっている。

**[CASPAR]**: **BALTHASAR を採る。A1 は移動の前提条件であり、`.claude/` にいる状態で先に直す。**

**採用しなかった選択肢**: (a) 移動と同時 → 壊れたとき原因が「移動」か「解決方式」か切り分けられない /
(b) settings の `env` で `LAM_PROJECT_ROOT` を固定 → **利用者全員に同じ手作業**を強いるため配布物として不適。

### Atom A2: `permissions.allow` の py_invoke prefix

**[MELCHIOR]**: hooks はハーネスが直接 spawn するので `permissions` を経由しない。影響は skill 内 bash のみ。

**[BALTHASAR]**: 数ではなく**主体**の問題。`permissions` は AI 編集不可なので**ユーザーの手作業が挟まる**。
同じ手作業は**配布先の利用者全員にも発生する**。「plugin を入れれば使える」の反例であり Layer 1 と同型の穴。

**[CASPAR]**: **`py_invoke.sh` は当面 project 側に残す。** 理由 = (1) `CLAUDE.md` §Python Invocation Convention が
「**allowlist prefix 1 本に載せるための単一 entry point**」と設計目的を明記しており、動かすとそれが壊れる
(2) 動かすなら `/lam-harness:init` Step 6 に allow エントリ追加を足す必要があり、**init の射程を広げる別判断**。

**採用しなかった選択肢**: (a) plugin の `bin/`（PATH 自動追加）経由 → allow エントリは依然必要で経路が増えるだけ /
(b) 全部動かして手作業依頼 → **切替の最中に承認地獄**が起き、ロールバック判断が濁る。

### Atom A5: bare な `subagent_type` は解決するか

**[MELCHIOR]**: 単一 plugin なら bare でも通る可能性が高い。

**[BALTHASAR]**: 「可能性が高い」で移行計画を組むのは、**前回 gabriel が 2 度突いた「前提を確かめずに設計した」型**そのもの。

**[CASPAR]**: **実測するまで決めない。かつ、計画を bare 解決の可否に依存させない**（下記 A3 の設計は可否によらず成立）。

### Atom A3 + A4 + A6（**再 MAGI で修正**）

#### 1 巡目の CASPAR 結論（gabriel が refute）

移動を「複製 → 参照切替 → 撤去」の 3 相に分け、**全コンポーネントに一律適用**する。

#### gabriel 1 巡目の指摘（`critical` / 裏取り済）

> skills/agents は名前空間で呼び出し先が構造的に分離されるが、**hooks は event 発火型で
> 「参照切替」という操作自体が存在せず**、複製した瞬間から project 版と plugin 版が同一イベントで同時発火する。
> `security-commands.md` §計器への書き込みを伴う検証は `tdd-patterns.log` の **2026-08-17 復元不能インシデント**を
> 根拠に隔離確認を MUST 化しているが、複製相ではこの隔離が満たされない。

#### 2 巡目の CASPAR 結論（採用）

**3 相モデルは維持するが、hooks を適用対象から外す。分岐条件は「重要度」でも「リスク」でもなく
「呼び出し先が存在するか」。**

| 性質 | 対象 | 切替方式 |
|:--|:--|:--|
| **呼び出し先がある**（名前で指す） | skills / agents / skills から呼ばれる scripts | **複製 → 参照切替 → 撤去**（重なりは安全） |
| **呼び出し先が無い**（イベント発火） | hooks | **セッション境界での 1 回のアトミック入れ替え**（複製相を持たない） |

**L1 が追加で認識した点**: **P1 の予行演習自体が二重発火を起こしうる。** `--plugin-dir` でロードする plugin が
`hooks/hooks.json` を持てば project hooks が生きたまま加算される —— **予行が本番より危険**という倒錯。
よって予行は `hooks/hooks.json` を置かない状態で行う。

**採用しなかった選択肢**: (a) hooks も複製 → 二重追記で**復元不能な**計器汚染 /
(b) hooks を最初に動かす → **無音の失敗を最初に置く**ことになり以降の切り分けが全部濁る /
(c) 二重発火を冪等化して許容 → **計器の追記は本質的に冪等化できない**うえ、冪等化コード自体が新たな維持対象。

---

## Step 4: gabriel probe

### 1 巡目

- verdict: **refuted** / severity: **critical** / affected_atoms: [A3, A4, A6]
- recommended_action: **re-magi** / confidence: 0.75
- 処理: MAGI 結論を破棄し、**再 MAGI 1 ラウンド**を実施（AC-W-C-5 / 上限 1 回）
- **L1 による裏取り**: `docs/adr/0010-...md:286` を実測し、指摘が正しいことを確認した

### 2 巡目

- verdict: **refuted** / severity: **warning** / affected_atoms: [P0, P1, P4]
- recommended_action: **proceed** / confidence: 0.55
- 処理: **指摘を結論に併記して進む**（AC-W-C-6）

> **[WARNING by gabriel]**: 3 件はいずれも「設計の欠陥」ではなく **未検証の仮定**である。
> ただし (a) は L1 の canary 設計への直撃であり、**そのまま実装すると fail-open する**。

| # | 指摘 | 扱い |
|:-:|:--|:--|
| **(a)** | **P0 の root 健全性 canary は空振りしうる。** `marketplace add` はリポジトリ全体（`.claude/` 込み）を clone する（V2 実測）ため、「`.claude/` があれば健全な root」という判定は clone を健全と誤検知する。**PM 級書込ゲートの fail-open に直結** | **設計変更（下記 P0 参照）** |
| **(b)** | **skills/agents 複製相の安全性は明示参照（名前空間）についてのみ確認されている。** description 一致による**モデル自動選択時**の衝突は未検証で、P1 の予行にも含まれていない | **P1 の検証項目に追加** |
| **(c)** | **「セッション境界がアトミック性を与える」に一次資料が無い。** `settings.json` の hooks 再読込と plugin 有効化が同一境界で同期する保証は未確認。崩れれば P4 は critical へ動く | **P4 の前提条件として明示 / 先に裏取り** |

**gabriel が確認した非衝突**: ADR-0010 **M-1**（旧 marketplace 空化は依存 PJ 全ての移行完了が前提）は
`~/claude-global-assets` 側の別資産に対する条項であり、**本手順とは独立**。

---

## Step 5: AoT Synthesis

### 最終結論

**手順 4 と手順 5 は逐次実行しない。** コンポーネントの性質で切替方式を分け、
**失敗が無音のものを最後**に置く。手順 4（参照の名前空間化）は独立した工程ではなく、
**P3（agents）の中相**として実施される。

| 相 | 内容 | 失敗の見え方 | gabriel 指摘の反映 |
|:-:|:--|:--|:--|
| **P0** ✅ | `get_project_root()` に **`CLAUDE_PROJECT_DIR` 経路**を追加 ＋ **`__file__` 経路を通るテスト**（現行テストは `LAM_PROJECT_ROOT` で盲目）。**2026-09-04 完了 / 1321 → 1325 passed** | テストで可視 | **(a)** |
| **P1** | `--plugin-dir` 予行（**`hooks/hooks.json` を置かない**）→ skills/agents のロード / bare 解決（A5）/ **description 衝突**を実測 | 大きい音 | **(b)** |
| **P2** | skills: 複製 → 参照切替 → 撤去 | 大きい音 | — |
| **P3** | agents: 複製 → **`subagent_type` 名前空間化（= 手順 4）** → 撤去 | 中 | — |
| **P4** | hooks: **捨てプロジェクトで隔離検証** → セッション境界でアトミック入れ替え（複製相なし）。**着手前に (c) を裏取りする** | **無音 → だから最後** | **(c)** |
| **P5** | `permissions.allow` の手作業（ユーザー）＋ `/lam-harness:init` Step 6 への反映判断 | ユーザー | — |

### P0 の canary 設計（gabriel (a) を反映して変更）

**「root が健全か」を推測で検証しない。** 推測は必ず空振りする（(a) がその実例）。代わりに:

- **`CLAUDE_PROJECT_DIR` を `__file__` より上に置く**（上流は hook 実行時に注入すると規定している）
- `__file__` fallback は残すが、**そこへ落ちたという事実そのものを stderr に出す**。
  hook 実行時の stderr は上流がトランスクリプトに表示するため、沈黙にならない
- テストは両 env を**外した状態**で `__file__` 経路を 1 件通し、
  現行テストの盲点（escape hatch による無条件迂回）を塞ぐ

> これは `rule-001` 恒久解 (c) と同型の手である —— **推論をやめて宣言を読む**。

> ### 訂正（2026-09-04 / P0 実装時に判明）
>
> 本 MAGI は当初、解決順を **`$CLAUDE_PROJECT_DIR` → `LAM_PROJECT_ROOT` → `__file__`** と書き、
> 「hook 経路では `CLAUDE_PROJECT_DIR` を必須にして不在なら落とす」としていた。**2 点とも誤りである。**
>
> 1. **順序が逆**: `CLAUDE_PROJECT_DIR` を最優先にすると、**Claude Code セッション内で走る全テストが
>    実プロジェクトを掴み**、`tmp_path` による隔離が崩れる。`LAM_PROJECT_ROOT` はテストの明示 override
>    であり最優先でなければならない。正しい順は **`LAM_PROJECT_ROOT` → `CLAUDE_PROJECT_DIR` → `__file__`**
> 2. **「必須にして落とす」は過剰**: `get_project_root()` は hook 以外（`checkers/` / 手動 CLI）からも
>    呼ばれるため、hook 文脈を実行時に判定する必要が生じる。**それは推測の再導入**であり、
>    (a) を招いた思考と同型。落とすのではなく **可聴化**で足りる
>
> **gabriel はこの誤りを 2 巡とも指摘していない。** probe は「書かれた設計」を検証するが、
> **実装して初めて出る種類の誤りには構造的に届かない**。これは probe の欠陥ではなく射程である。

### Action Items

1. ~~**P0**~~ **完了**（2026-09-04 / 1321 → 1325 passed / 実働確認済）
2. **P1 の前に (c) を裏取り**: `settings.json` hooks の再読込タイミングと plugin 有効化タイミング
3. **P1**: `--plugin-dir` 予行（別セッション / hooks.json なし）—— A5 と (b) を実測
4. **P2 → P3 → P4** を順に。**各相の終わりに全テスト + 機構 #10/#11/#12 を回す**
5. **P5** はユーザー作業（`permissions` は AI 編集不可）

### P1 の位置の調整（2026-09-04 / P0 完了時に判明 / **相の順序を現実に合わせる**）

**P1 で測りたい 3 点のうち、いま測れるのは 1 点だけである。**

| # | 予行で確認したいこと | いま測れるか |
|:-:|:--|:--|
| 1 | `/lam-harness:init` が skill 一覧に載るか（plugin ロード経路の実証） | **測れる** |
| 2 | **bare な `subagent_type` が plugin agent に解決するか**（A5） | **測れない** —— plugin に `agents/` がまだ無い |
| 3 | **description 一致時のモデル自動選択の衝突**（gabriel (b)） | **測れない** —— 同上 |

したがって実効的な順序は **P1(1) → P2（skills 複製）→ P3 前半（agents 複製）→ P1(2)(3) → P3 後半（参照切替・撤去）** となる。
**相の定義は変えない**（分岐条件「呼び出し先が存在するか」は不変）。変わるのは
**予行を 1 回でなく 2 回に割る**点だけである —— 予行は「複製が済んだ対象についてしか測れない」ため。

> **これは MAGI の欠陥ではなく、MAGI が「複製前に予行できる」と暗黙に仮定していた箇所である。**
> gabriel の (b) は「P1 の予行に description 衝突が含まれていない」と正しく指摘したが、
> **含められない理由（agents がまだ plugin に無い）までは踏み込んでいない**。

### 未検証のまま残るもの（明示）

- bare `subagent_type` の解決可否（A5 / P1 で解消）
- description 一致時のモデル自動選択の挙動（(b) / P1 で解消）
- `settings.json` hooks 再読込と plugin 有効化の同期（(c) / P4 前に解消）
- **これらが想定と食い違ったときが HGA 召喚のタイミング**（実測で潰せない crux に変わるため）

---

## 参照

- `docs/artifacts/2026-09-04-plugin-migration-progress.md`（実行状態の正本）
- `docs/adr/0010-global-claude-assets-governance.md` 追補 1（**F6 の出所**）
- `docs/artifacts/2026-09-04-magi-distribution-form.md` §13.5 / §13.6（V1-V8）
- `.claude/rules/security-commands.md` §計器への書き込みを伴う検証（**2026-08-17 の復元不能インシデント**）
- `docs/internal/06_DECISION_MAKING.md` §6.6（**critical 2 回目が意味するもの** / 本日追記）
