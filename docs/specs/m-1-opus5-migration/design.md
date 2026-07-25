# M-1 Milestone Design: Opus 5 移行 + 規律の条項トリアージ

## メタ情報

| 項目 | 内容 |
|:-----|:-----|
| Milestone | M-1 |
| ステータス | **Approved** (2026-07-25 / ユーザー承認 / 承認前修正 2 点 + 承認前レビュー 4 点を反映後) |
| 作成日 | 2026-07-25 |
| 更新日 | 2026-07-25 |
| 親仕様 | `docs/specs/m-1-opus5-migration/requirements.md`（Approved 2026-07-25） |
| 起源 | ADR-0011（Accepted 2026-07-25） |
| SSOT | 本ファイル |
| 起草者 | design-architect subagent（L1 委譲） |
| L1 検収 | 2026-07-25 / 3 点修正: §4.1 項目 4 の gabriel verdict 集計を実スキーマ（`gabriel_output.verdict` / `invoked=false` は null）に合わせ既存 jq 集計例へ差替 / §4.1 項目 2 の Green State プロキシを Wave 末ゲート記録の Critical・Warning 件数へ変更 / §8.3 に配布実行の承認ゲートを追加 |
| 承認前修正 | 2026-07-25 / retro（`docs/artifacts/retro-R2-W1-M1-PLANNING-2026-07-25.md`）反映 2 点: (a) §5.3 をトリアージ入力の 2 カテゴリ構成へ拡張し retro 由来の新規条項候補 3 件を明示入力化 / (b) §4.1 項目 3 に計器盲点の注記を追加し §4.5（TDD パターン記録機構の較正）を W0 に新設。波及同期: §3.1 / §3.3 / §10.1 / §10.2 |
| 承認前レビュー | 2026-07-25 / **design 記載のコマンドを実行して検証**（F4 #1「作った層と別の層で確認する」）。Critical 2 件・Warning 2 件を修正: **C1** §7.2 の判定式が最優先対象 `full-review`（951 行）を取りこぼす欠陥 → `references/` ディレクトリ実在判定へ変更し実測 9 件を記載、W3 スコープを上位 4 件に確定 / **C2** §7.3 の代理指標が言及数 ≠ 起動実績（盲目の計器）かつ実行前に分岐が確定 → `agent-memory` 証跡 + 責務重複度の 2 指標へ差替 / **W1** §4.4 が引き継いでいた requirements FR-20 の実測値誤り（sonnet 8 / 不明 1 → 実測は sonnet 9 / 不明 0）を訂正 / **W2** §5.1 に条項数の参考実測（51 行ヒット = 数十条項オーダー）を追加 |

---

## §1 Problem Statement

requirements.md §1.1 が示す通り、2026-07-25 に Anthropic が Claude Opus 5 をリリースし、Claude Code の system prompt を 80% 以上削除しても coding evaluation に有意な低下がなかったという自社実測に基づく 6 つのパラダイム転換（Rules→Judgement / Examples→Design Interfaces / Put upfront→Progressive Disclosure / Repeat yourself→Simple tool descriptions / Memory in CLAUDE.md→Auto-memory / Simple specs→Rich references）を提示した。

一方 LAM は憲法型ハーネスとして規律を積み上げてきた。2026-07-25 実測（ADR-0011 §背景）で `.claude/` 配下の規律・実行資産は 44 ファイル 8,182 行（`CLAUDE.md` 269 行 / `.claude/rules/` 16 ファイル 2,176 行 / `.claude/skills/` 15 ファイル 3,656 行 / `.claude/agents/` 12 ファイル 2,081 行）に達しており、`.claude/rules/` の「禁止」39 件の 59%（23 件）が `fable-l3-protocol.md`（12 件）と `phase-rules.md`（11 件）の 2 ファイルに集中し、F0-F4 実行プロトコルと 60 秒実況が両ファイルにほぼ同内容で二重記述されている。

ADR-0011 は「M-1 は削減の Milestone ではなく、峻別基準と予防機構を作る Milestone である」と決定した（Option C 採用）。本設計は、この決定（4 軸トリアージ / `model-roster.md` 単一 SSOT / 3 層安全網 / HGA ゲート転換 / 配布 2 経路分割）を requirements.md の FR-1〜FR-21・NFR-1〜NFR-6 と対応させながら、実装可能な設計判断（配置パス・データ構造・判定手順・pseudo code）に写像したものである。requirements.md §7 が残した 7 件の Red のうち、粒度定義（Red-1）・実装形態（Red-4）・台帳形式（Red-5）・ゲート合格判定（Red-6）・skills/agents 判定軸（Red-2）の 5 件は、この設計段階で確定する（詳細は §11）。

本設計は ADR-0011 および requirements.md が確定した決定内容の展開であり、新しい設計判断を発明するものではない。

## §2 Non-Goals

requirements.md §1.3 の Non-Goals をそのまま設計視点で継承する:

1. **削減量の数値目標**（Anthropic の 80% を目標値として掲げない）
2. **全面書き直し**（ADR-0011 Option D 却下済 — 実測発火由来の規律が全損するため）
3. **ADR-0001 の supersede およびルーティング構造の変更**（直交するため）
4. **R-2 の Definition of Done 自体の変更**（W2/W3 の再スコープは行うが DoD は変更しない）
5. **HGA 新ゲート（事後条件）の M-1 実施中の適用**（移行期は旧ゲートを適用する）
6. **不変制約 4 対象の変更**（FR-5 が定める 4 対象自体の見直しは本 Milestone のスコープ外）
7. **T16（fable-l3 × Fable-Alembic snapshot 統合方針）**（R-2 Non-Goals を継承。判定作業自体もスコープ外）
8. **`D:\work7\Fable-Alembic\` 配下への書き込み**（Outbound Write Ban / `fable-l3-protocol.md` §2）

設計固有の追加 Non-Goals（2 件）:

9. **トリアージ判定の自動化**（4 軸判定は人手で行い、機械判定ロジックを実装しない — §9 却下案 3 参照）
10. **`model-roster.md` 以外の新規 SSOT ファイルの追加**（ADR-0011 決定 2 が指定する SSOT は `model-roster.md` の 1 ファイルのみであり、モデル固有記述を集約する 2 個目の SSOT を作らない）

## §3 全体構成

### §3.1 Wave の設計 view

```
W0 準備
  TDD パターン記録機構の較正（計器の盲点修正 / §4.5）  ← ベースライン測定に先行
  → ベースライン測定(6項目) → 削減台帳の器（空スケルトン）作成
  → upstream 一次資料の裏取り（Opus 5 / Fable 5）→ ADR-0001 突合
      ↓（第 1 層＝ベースライン測定の完了が W2 着手の前提条件 / FR-8）
W1 トリアージ（判定のみ・適用しない）
  4軸・決定木・不変制約の適用 → veto 先行スクリーニング → 残り精査（実質対象 ≈750行）
  → R-2 W2/W3 予定条項をトリアージ表に組込み → トリアージ表 PM 級一括承認（K5）
      ↓
  ゲート: Opus 5 安定性ゲート（3 条件） ──合格──▶ W2
      │
      └─不合格─▶ Opus 4.7 へフォールバック + M-1 一時停止（W1 の分析成果＝トリアージ表は保持）
W2 規律本体の適用
  model-roster.md 新設 + SSOT 退避 → 圧縮・削減の実行 + 削減台帳記録
  → verify_model_reference 機構（3 分岐処理）→ HGA 召喚ゲート改訂
  → R-2 W2/W3 の再スコープ実行 → trust-model.md への接続（削減台帳を検出イベント対象に含める）
W3 skills / agents の構造改善
  skills/agents 向け判定軸の定義 → progressive disclosure 化（100 行超・外部参照ゼロの 4 skill）
  → quality-auditor × code-reviewer の呼び出し実績収集 → ADR-0010 I-1〜I-6 適合確認
W4 検証・確定
  ベースライン再測定 → update-model skill 作成 → 配布（2 経路）→ Milestone retro
```

Wave 数は 5（W0〜W4）で固定する（FR-1）。W0 の第 1 層ベースライン測定が完了する前に W2（規律本体の適用）Task へ着手してはならない（FR-8 / 比較対象が永久に失われる不可逆な失敗のため）。W1 は判定のみを行い、W1 中は圧縮・削減を一切実行しない（FR-6）。

### §3.2 PM 級ファイル編集計画（K5 一括宣言の実体 / FR-3）

`permission-levels.md` §ファイルパスベースの分類に従うと、PM 級ファイルは `docs/specs/*.md` / `docs/adr/*.md` / `.claude/rules/*.md`（サブディレクトリ含む）/ `.claude/settings*.json` に限られ、`.claude/skills/` と `.claude/agents/` はこの列挙に含まれない（デフォルトは SE 級）。この分類を前提に、Wave ごとの PM 級編集計画を以下に示す。

| Wave | 承認イベント | PM 級ファイル | 対応 FR | 編集種別 |
|:----:|:-----------:|:--------------|:--------|:---------|
| W1 | K5 一括宣言（トリアージ表全体を 1 承認イベントとする / FR-6） | なし（トリアージ表自体は `docs/artifacts/` へ出力し SE 級。W1 中は PM 級ファイルへの実編集を行わない） | FR-6 | 承認のみ（適用は W2） |
| W2 | K5 一括宣言 | `.claude/rules/model-roster.md`（新規） | FR-10 | 新規作成 |
| W2 | K5 一括宣言 | `.claude/rules/model-delegation-prompting.md` | FR-10 | 圧縮（挙動デルタを移動、参照のみ残す） |
| W2 | K5 一括宣言 | `.claude/rules/hga-summoning.md` | FR-10, FR-15 | 圧縮（単価・envelope を移動）+ 召喚ゲート節改訂 |
| W2 | K5 一括宣言 | `CLAUDE.md` | FR-11 | モデル ID 直書き除去 + `model-roster.md` への導線追加 |
| W2 | K5 一括宣言 | W1 トリアージ表で圧縮・削減判定を受けた `.claude/rules/*.md` 各ファイル | FR-6, FR-7 | 圧縮・削減の実行（対象ファイルの確定は W1 出力に依存するため design 時点では列挙しない） |
| W2 | K5 一括宣言 | `docs/specs/r-2-consolidation/tasks.md` | FR-21 | 追記（Task 完了記録への判定結果反映） |
| W2 | K5 一括宣言 | `.claude/rules/terminology.md` / `.claude/rules/planning-quality-guideline.md` / `.claude/rules/model-delegation-prompting.md`（R-2 予定条項のうち判定が「実施」または「圧縮形で実施」の分のみ） | FR-21 | 追記 |
| W3 | 宣言不要（既定） | なし（`.claude/skills/` / `.claude/agents/` は §ファイルパスベースの分類で SE 級） | FR-16, FR-17 | — |
| W3 | 条件付き追加宣言 | ADR-0010 I-1〜I-6 適合確認（§7.4）で不適合が発見された場合の `docs/adr/0010-global-claude-assets-governance.md` 追記 | FR-17 | 追記（不適合発見時のみ） |
| W4 | 宣言不要（既定 / SE 級） | `docs/artifacts/m-1-distribution-catalog.md` | FR-18 | 新規作成 |

**非 PM 級で編集する主なファイル**（宣言不要・参考記載）: `.claude/scripts/verify_model_reference.py`（新規）、`docs/artifacts/m-1-baseline-w0.md`〜`m-1-baseline-w4.md`、`docs/artifacts/m-1-clause-ledger.md`、`docs/artifacts/m-1-opus5-stability-gate.md`、`.claude/skills/update-model/SKILL.md`（新規）、W3 で progressive disclosure 化する `.claude/skills/*/SKILL.md`、`.claude/agents/*.md`（frontmatter 更新）。

W1 は PM 級ファイルの編集を伴わないため、K5 一括宣言の対象は「トリアージ表という決定の承認」であり、ファイル編集一覧の宣言ではない。この点は R-2 の K5 運用（PM 級ファイルの編集予定一覧を宣言する運用）と形式が異なるため、W1 の承認プロンプトでは「本 Wave はファイル編集を行わず、トリアージ表の承認のみを求める」旨を明示する。

### §3.3 条項トリアージのデータフロー

```
[条項抽出]（W1 対象: fable-l3-protocol.md 234 行 + phase-rules.md 245 行 + CLAUDE.md 269 行 ≈ 750 行 / §5.1 の粒度定義で grep 実測）
    │
    ▼
[veto 先行スクリーニング]（§5.2）
    軸 1 = ユーザー意思/統治 → 保全（veto）で確定・以降の軸評価不要
    軸 3 = 不可逆ガード      → 保全（veto）で確定・以降の軸評価不要
    │（いずれにも該当しない条項のみ次段へ）
    ▼
[不変制約 4 対象の除外]（§5.2 / トリアージ対象外・4 軸評価を経ない）
    │
    ▼
[残り 3 分岐評価]（§5.2 決定木）
    帰属がモデル固有の事実 → SSOT 退避（model-roster.md へ移動）
    軸 4 = 実測発火あり × 軸 2 = 列挙 → 圧縮
    軸 4 = 実測発火あり × 軸 2 = 意図 → 保全
    軸 4 = 発火ゼロ     × 軸 2 = 列挙 → 削減
    軸 4 = 発火ゼロ     × 軸 2 = 意図 → 保全（低優先 / 次回 retro で再評価）
    │
    ▼
[トリアージ表]（docs/artifacts/ / §5.2 スキーマ / W1 末に PM 級一括承認 / §5.4）
    │（W1→W2 の間に Opus 5 安定性ゲート / §5.5）
    ▼
[W2 適用] 圧縮・削減・SSOT 退避の実行
    │
    ├──▶ [削減台帳への記録]（原文 / 判定軸 / 移動先 / §6.3）
    │
    └──▶ [trust-model.md への接続]（削減台帳の条項を検出イベント対象に含める / §6.6 / FR-9）
```

「条項抽出」段階には、上記 3 ファイルの既存条項に加えて **2 つの追加入力カテゴリ**（いずれも §5.3 / 未執筆条項）が合流し、同一パイプラインを通過する。

- **(i) R-2 W2/W3 の予定条項 3 件**（FR-21 前段）— 判定結果の 3 分岐（実施 / 圧縮形で実施 / スキップ）への写像は §6.5 で定義する
- **(ii) retro 由来の新規条項候補 3 件** — 対象ファイルが W1 主対象 3 ファイルの外にあるため明示入力とする

### §3.4 Wave 末ベースライン測定（FR-8 全 Wave 適用）

決定 3 第 1 層（定量ベースライン 6 項目）は W0 だけでなく、W1・W2・W3・W4 の各 Wave 末で同一手順（§4.1）を再実行する。

```bash
bash .claude/scripts/py_invoke.sh -m pytest
# 6 項目のうち「pytest 全数」は上記コマンドの PASS/FAIL/SKIP 内訳をそのまま用いる。
# 残り 5 項目（Green State 件数 / tdd-patterns.log FAIL→PASS 率 / gabriel verdict 分布 /
# PM 級ダイアログ発火数 / CLAUDE.md+rules トークン数）は §4.1 の個別手順を Wave 末に再実行する。
```

測定値は Wave ごとに `docs/artifacts/m-1-baseline-w<N>.md`（N = 0, 1, 2, 3, 4）へ記録する。NFR-3 が定める W0 起点（R-2 W1 末実績 / commit `2ac4e91` / 1043 passed + 14 skipped）を基準に、各 Wave 末で pytest PASS 数が減少していないこと（regression ゼロ）を確認する。

---

## §4 W0 設計（準備）

### §4.1 ベースライン測定 6 項目の実測手順（FR-8）

決定 3 第 1 層の測定項目 6 件それぞれについて、実測コマンドまたは取得手順を以下に定義する。

| # | 項目 | 実測手順 |
|:-:|:-----|:---------|
| 1 | pytest 全数 | `bash .claude/scripts/py_invoke.sh -m pytest` を実行し、出力末尾の PASS/FAIL/SKIP 件数をそのまま記録する。W0 起点は NFR-3 が既に確定した R-2 W1 末実績（commit `2ac4e91` / 1043 passed + 14 skipped）であり、W0 ではこの値を同一コマンドで再実測し確定させる |
| 2 | Green State 件数 | 直近の Wave 末ゲート記録に記載された Critical / Warning の件数を転記する（`code-quality-guideline.md` の Green State = Critical 0 かつ Warning 0）。W0 起点は R-2 W1 末ゲート（2026-07-25 / commit `2ac4e91`）の記録を用いる。Green State 判定を一元集計する既存機構は存在しないため、各 Wave 末ゲート記録を唯一の情報源とし、新規の集計機構を追加しない（NFR-2 準拠） |
| 3 | `tdd-patterns.log` FAIL→PASS 率 | `.claude/tdd-patterns.log` を対象に、`trust-model.md` §パターン照合ロジックと同一の手順（`/retro` Step 2.5 のペアリングロジック: 同一テスト名・時系列順で FAIL 直後の PASS を遷移として数える）を手動実行し、全 FAIL エントリ数に対する遷移ペア数の比率を記録する。新規スクリプトは追加しない（NFR-2 準拠）。**計器の既知の盲点（2026-07-25 retro §3 で実測確定）**: 本ログは委譲 TDD（Sonnet subagent 内の Red-Green）を記録しない。同日 4 つの TDD Task に対し記録は 0 件だった。M-1 の各 Wave も委譲で進むため、盲点を残したまま W0 と W4 を比較しても差分は条項トリアージの効果ではなく委譲率の副産物になる。よって **§4.5 の計器較正を本項目の測定に先行させる**。§4.5 で盲点が解消しない場合、本項目は参考値扱いとし DoD-4 の判定条件から除外する（除外の判断と理由を `docs/artifacts/m-1-baseline-w0.md` に記録する） |
| 4 | gabriel verdict 分布 | `docs/artifacts/gabriel-metrics-environment-2026-07-05.md` §集計例が既に定義している jq コマンド（`jq -c 'select(.gabriel_output.verdict=="refuted")' .claude/gabriel-metrics.log \| wc -l` の形式）をそのまま用い、`confirmed` / `refuted` / `inconclusive` の 3 値の件数と `invoked=true` の総数を記録する。**`verdict` は最上位キーではなく `gabriel_output` 配下にネストしており、`invoked=false`（`skip_lightweight` / `skip_opt_out`）の entry では `gabriel_output=null` となる**（同文書 §2 gate 経路別 nullable 判定）ため、`invoked=true` の entry のみを母数とする。新規集計スクリプトは追加しない（NFR-2 準拠） |
| 5 | PM 級ダイアログ発火数 | 自動集計機構が存在しない（`.claude/.session-pm-edit-cache.json` はセッションスコープで gitignore 対象のため永続比較に使えない）。各 Wave の K5 宣言・承認記録（FR-3 が要求する `SESSION_STATE.md` 上の記録、Wave 完了後は Milestone retro に永続化）から手動集計する。W0 時点は M-1 着手前のためゼロを記録する |
| 6 | `CLAUDE.md` + `rules` トークン数 | `cat CLAUDE.md .claude/rules/*.md .claude/rules/*/*.md \| wc -m` の文字数をそのまま近似値として記録する。真のトークナイザ値ではなく、W0 と W4 で同一手法（文字数ベース）を用いた相対比較にのみ使用する |

6 項目の測定結果は `docs/artifacts/m-1-baseline-w0.md` に記録する。

### §4.2 削減台帳の器（準備）

ADR-0011 §実装計画 W0 が定める「削減台帳の器を作成（単純表で開始）」を、`docs/artifacts/m-1-clause-ledger.md` にヘッダ行のみのスケルトンとして作成する。列構成は §6.3 で確定する 7 列（条項ID / 原文 / 出典（ファイル:節） / 判定軸（軸1〜4の値） / 判定（圧縮/削減/SSOT退避） / 移動先 / 判定日）とし、W0 時点ではヘッダ行のみを持つ空表とする。データ行の記入は W2（トリアージ適用時）に行う。

### §4.3 upstream 一次資料の裏取り手順（FR-19）

`upstream-first.md` §確認手順に準拠する。

1. context7 で Opus 5 および Fable 5 の公式スペック（context window / 価格 / リリース日）を検索する
2. context7 で取得できない場合は WebFetch にフォールバックする（`upstream-first.md` の注意書きに従い、対話モードでのみ使用する）
3. 取得した各値を一次資料の URL・取得日とともに `docs/artifacts/m-1-baseline-w0.md` に記録する
4. 取得できなかった項目は「未確認」と明記し、断定しない
5. 記録結果は W2 の `model-roster.md` §単価・envelope 節（§6.1）へそのまま転記する（FR-19 受け入れ条件 3）

### §4.4 ADR-0001 突合の grep コマンド（FR-20）

```bash
grep -n "^model:" .claude/agents/*.md
```

1. 上記コマンドで `.claude/agents/*.md` 全 12 ファイルの `model:` frontmatter 値を一覧化する
2. ADR-0001 §改訂履歴の記述（「12 agents で `command|sonnet|haiku|fable` 混在指定」）と実測値を突合する。

   **design レビュー時の実測（2026-07-25 / 上記コマンドを実行）**: `.claude/agents/*.md` は 12 ファイル、うち 12 ファイルすべてが `^model:` を持ち、内訳は **`sonnet` 9 / `haiku` 3 / 不明 0**。`command` および `fable` の指定は未検出。

   この実測は 2 つの不一致を示す。(i) requirements.md FR-20 の説明にある「sonnet 8 / haiku 3 / **不明 1**」は実測と一致しない（`sonnet` が 1 件少なく、実在しない「不明 1」を含む）。(ii) ADR-0001 §改訂履歴が記述する `command` / `fable` の混在は現在の実ファイルに存在しない（= ADR-0001 側の drift）。W0 実行時に本実測を再確認した上で、requirements FR-20 説明文の訂正と ADR-0001 の扱いを併せて PM 級判断へ上げる
3. 不一致が確認された場合、ADR-0001 への時点注記追加、または実ファイル修正のいずれかを PM 級判断で決定する
4. 判定結果を `docs/artifacts/m-1-baseline-w0.md` に記録する

### §4.5 TDD パターン記録機構の較正（FR-8 前提作業 / §4.1 項目 3 に先行）

**背景**: 2026-07-25 の retro（`docs/artifacts/retro-R2-W1-M1-PLANNING-2026-07-25.md` §3）で、`.claude/tdd-patterns.log` が委譲 TDD を記録しないことが観測で確定した。同日 4 つの TDD Task（W1-R2-T4 / T5 / T6 / T8）が Red-Green サイクルを回したにもかかわらず記録は 0 件であり、原因は次の 2 経路のいずれか（または両方）に絞られたが、既存の成果物からは切り分けできていない（寄与は未確認）。

- **経路 (a)**: subagent の Bash 呼び出しで PostToolUse hook が発火しない
- **経路 (b)**: 並列 subagent が `-o addopts=""`（`docs/daily/2026-06-02.md` で共有 XML の clobber 回避として規約化済）を使うため JUnit XML が更新されず、hook が前回の green XML を読む

経路 (b) が成立する場合、記録の欠落だけでなく**古い XML に残る失敗を当該コマンドの FAIL として記録する汚染**も起こりうる。

**本作業を M-1 に含める理由**: M-1 は「規律が実際に発火しているか」を 4 軸（特に軸 4 = 実測発火の有無）で判定する Milestone である。発火実績を測る計器が盲目のまま条項を削ると、軸 4 の判定入力そのものが汚染される。

**手順（3 手）**:

1. **probe（切り分け）**: subagent に意図的に 1 件失敗する pytest を実行させ、`.claude/tdd-patterns.log` への追記有無と `.claude/test-results.xml` の mtime 変化を観測する。`-o addopts=""` の有無で 2 通り実行し、経路 (a) と (b) を切り分ける
2. **修正**: probe 結果に応じて、hook 側（subagent 実行時の JUnit XML パス分離等）または規約側（`-o addopts=""` 運用の見直し）を修正する。**既存機構の修正であり、新規の帳簿・新規ログファイル・新規集計スクリプトは追加しない**（NFR-2 準拠）
3. **記録**: probe 結果（どちらの経路だったか）と修正内容を `docs/artifacts/m-1-baseline-w0.md` に記録する

**不成立時の扱い**: 3 手で盲点が解消しない場合、修正を M-1 のスコープ外へ送り、§4.1 項目 3 を参考値扱い（DoD-4 の判定条件から除外）とする。この判断は **W0 完了時に確定させ、W1 以降へ持ち越さない**。

---

## §5 W1 設計（トリアージ）

### §5.1 条項粒度の定義（FR-4 / Red-1 の解決 — 最重要）

**定義**: 1 条項 = 1 つの規範文。規範文とは、次のいずれかを含む文である（閉集合）:

1. RFC 2119 キーワード: `MUST` / `MUST NOT` / `SHOULD` / `SHOULD NOT` / `MAY`
2. 日本語の規範表現: 「禁止」「必須」「してはならない」「〜すること」「〜を要する」「〜に従う」

**付随する扱い**:

- 表の各行が独立した規範を表す場合、行単位で 1 条項とする（例: `security-commands.md` のコマンド許可マトリクスの各行）
- 見出し・背景説明・根拠記述・具体例は条項に付随する文脈であり、独立した条項として数えない。ただし条項が圧縮・削減される場合、付随文脈も同一の判定に従って同時に処理する
- 条項 ID は `<ファイル名>#<節>-<連番>` 形式で付与する（例: `fable-l3-protocol.md#5.4-03`）

**根拠**: ADR-0011 §背景は既に「`.claude/rules/` の『禁止』39 件」という規範文単位のカウントを用いており、本粒度定義はこの既存実測と遡及一貫する。また §5.2 の 4 軸はいずれも規範に対して評価する軸であり、説明文には適用できない。見出し単位では解像度が不足し（`fable-l3-protocol.md` は §0〜§11 の 12 条項にしかならない）、文単位では説明文まで対象化して W1 が破綻する（§9 却下案 1 参照）。

**規模見積り**: W1 の実質対象は `fable-l3-protocol.md`（234 行）+ `phase-rules.md`（245 行）+ `CLAUDE.md`（269 行）≈ 750 行。この範囲の規範文数は W0 完了後・W1 着手時に以下のコマンドで grep 実測して確定する（design 時点では断定しない）:

```bash
grep -cE "MUST NOT|MUST|SHOULD NOT|SHOULD|MAY|禁止|必須|してはならない|すること|を要する|に従う" \
  .claude/rules/fable-l3-protocol.md .claude/rules/phase-rules.md CLAUDE.md
```

上記コマンドは行単位の粗い一次スクリーニングであり、正確な条項数は各ヒット行を Read で確認し「規範文か文脈か」を個別判定した上で確定する（`subprocess-encoding-convention.md` §grep baseline と同型の「一次スクリーニング + 個別確認」手順）。

**2026-07-25 時点の参考実測（design レビュー時に実行）**: `fable-l3-protocol.md` 22 行 / `phase-rules.md` 18 行 / `CLAUDE.md` 11 行 = **計 51 行ヒット**。`grep -c` が返すのはマッチ**行数**であり条項数そのものではない（1 行に複数条項があれば過小、説明文中の「〜すること」を拾えば過大）。したがって確定値ではないが、**W1 のトリアージ対象が数十条項のオーダーであり数百ではない**ことは確認できる。本参考値は `tasks.md` 起票時の Task 分割量の見積りにのみ用い、確定値は W1 着手時の個別判定で得る。

### §5.2 4 軸・決定木・不変制約と veto 先行スクリーニング手順（FR-4, FR-5, FR-6）

#### 4 軸表（ADR-0011 決定 1 を転記）

| 軸 | 問い | 保全側 | 削減側 |
|----|------|--------|--------|
| **軸 1（帰属）** | 誰の判断を記録しているか | ユーザー / プロジェクトの意思（統治・リスク許容度・方法論の選択） | モデルの誤り予防（worst-case 回避） |
| **軸 2（形式）** | 意図か、列挙か | 意図（principle / 既に圧縮済） | 列挙（enumerated do/don't） |
| **軸 3（可逆性）** | 破ったとき巻き戻せるか | 不可逆（承認ゲート / spec freeze / 破壊操作 / 外部公開） | 可逆（書式 / 命名 / 手順 / 表現） |
| **軸 4（根拠）** | 実測発火があるか | 実測インシデント由来（検出イベント ≥ 1） | 予防的に書かれた（発火実績ゼロ） |

軸 3 は第 0 原則（`core-identity.md` §第0原則）の可逆性・復旧コストを継承する。軸 4 は `trust-model.md` §カウント単位の「検出イベント単位」定義（「1 つの検証イベント（1 セッション内の `/retro` 実行 / 1 回の HGA 召喚 / 1 回の監査 Stage / 1 回の gabriel probe 等）内で検出された複数 issue は、件数によらず 1 カウントとする」）をそのまま流用する。新機構は作らない。

#### 決定木（ADR-0011 決定 1 を転記）

```
軸1 = ユーザー意思 / 統治      → 保全（veto / 他軸を問わない）
軸3 = 不可逆ガード             → 保全（veto / 他軸を問わない）
上記いずれにも該当しない場合:
  ├ 帰属がモデル固有の事実      → SSOT 退避（model-roster.md へ / 削除ではなく移動）
  ├ 軸4 = 実測発火あり
  │    ├ 軸2 = 列挙            → 圧縮（意図 1 行に畳む / 根拠は docs/artifacts へ退避）
  │    └ 軸2 = 意図            → 保全
  └ 軸4 = 発火ゼロ
       ├ 軸2 = 列挙            → 削減
       └ 軸2 = 意図            → 保全（低優先 / 次回 retro で再評価）
```

#### 不変制約 4 対象（軸に関わらずトリアージ対象外 / MUST NOT）

gabriel 指摘 2（ADR-0011 §3 Agents Analysis）を反映し、根拠を対象ごとに分離記述する。

| 対象 | 根拠 |
|------|------|
| 体験シミュ発火点（3 点） | `fable-l3-protocol.md` §5.4 ガード 2（「発火点数の一時的減少は禁止」） |
| PM 級承認ゲート・PM 級パス列挙 | `permission-levels.md` §PM 級パスの事前計算原則 |
| gabriel probe 起動条件 | ADR-0007 / FR-W-C-3（AoT 適用時 MUST / 軽量モード MUST NOT） |
| 統治への自己書込禁止 | ADR-0005 FR-9.1 |

`fable-l3-protocol.md` §5.4 ガード 2 を体験シミュ発火点以外の根拠として引用してはならない（FR-5 受け入れ条件 2）。

#### veto 先行スクリーニングの手順

Phase A（veto 先行 / 全条項に対して実施）:

1. 軸 1 を評価する。「ユーザー / プロジェクトの意思」に該当する条項は**保全（veto）**として確定し、以降の軸評価を行わない
2. 軸 1 で確定しなかった条項について軸 3 を評価する。「不可逆ガード」に該当する条項は**保全（veto）**として確定し、以降の軸評価を行わない
3. 軸 1・軸 3 いずれにも該当しない条項が「残り精査」対象となる

Phase B（残り精査 / Phase A で veto されなかった条項のみ）:

4. 帰属がモデル固有の事実（ADR-0011 決定 2 が定める「層への割当」「設計上の性質の説明」「時点記録」のいずれかに該当する記述）であれば **SSOT 退避**
5. 4 に該当しない条項について、軸 4（実測発火の有無）× 軸 2（意図か列挙か）の組み合わせで決定木の残り 4 分岐（圧縮 / 保全 / 削減 / 保全（低優先）) を適用する

不変制約 4 対象に該当する条項は、Phase A の実施前に除外し 4 軸評価を経ない（FR-5 受け入れ条件 3）。

#### トリアージ表スキーマ

| 条項ID | 原文 | 出典（ファイル:節） | 軸1判定 | 軸2判定 | 軸3判定 | 軸4判定 | 決定木の出力 | 根拠1行 |
|:------|:-----|:-------------------|:-------|:-------|:-------|:-------|:-------------|:--------|
| （例）`fable-l3-protocol.md#5.4-03` | （原文を転記） | `fable-l3-protocol.md` §5.4 | ユーザー意思 / モデル誤り予防 のいずれか | 意図 / 列挙 | 不可逆 / 可逆 | 実測発火あり / 発火ゼロ | 保全 / 圧縮 / 削減 / SSOT退避 / 対象外 | （1 行） |

「決定木の出力」列は「保全」「圧縮」「削減」「SSOT退避」「対象外」の 5 値の閉集合とする。「対象外」は不変制約 4 対象に該当し 4 軸評価を経ていない条項に用いる。

### §5.3 トリアージ入力の追加カテゴリ（未執筆条項の組込み / FR-21 前段）

W1 の主入力は §5.1 が定める 3 ファイル（≈750 行）の既存条項だが、これに加えて**まだ本文に書かれていない条項候補**を 2 カテゴリ、トリアージ表に「未執筆条項（追加予定の規範文）」として行追加し、既存条項と同一の Phase A/B パイプラインで判定する。**両カテゴリとも閉集合とし、W1 着手後の追加は行わない**（トリアージ表の PM 級一括承認の対象範囲を確定させるため）。

#### (i) R-2 W2/W3 の予定条項 3 件（FR-21）

requirements.md FR-21 が定める閉集合。

1. `terminology.md` §4.5 の 3 小節（T9「文書内相互参照は § 見出し表記を用いる」/ T12「表・節番号の挿入規則」/ T13「成果物ファイル命名規則」/ R-2 tasks.md W2-R2-T9・T12・T13 相当）
2. `planning-quality-guideline.md` §1.5「暗黙前提明示化リスト」（R-2 tasks.md W2-R2-T13b 相当）
3. `model-delegation-prompting.md` の scratchpad 書込禁止節（R-2 tasks.md W3-R2-T24 相当）

W3-R2-T23（`evaluation-kpi.md` §7 削除）は条項の削除でありトリアージ入力に含めない（requirements.md FR-21 説明準拠）。判定結果を実施 / 圧縮形で実施 / スキップの 3 分岐へ写像する手続きは §6.5 で定義する（本節は W1 トリアージ表への入力組込みのみを扱う）。

#### (ii) retro 由来の新規条項候補 3 件

2026-07-25 の retro（`docs/artifacts/retro-R2-W1-M1-PLANNING-2026-07-25.md` §5.1）が起票した Try のうち、**規律に条項を追加・改訂する方向**の 3 件。いずれも対象ファイルが §5.1 の W1 主対象 3 ファイル（`fable-l3-protocol.md` / `phase-rules.md` / `CLAUDE.md`）の外にあるため、本カテゴリとして明示的に入力する。

| # | 内容 | 対象ファイル | 由来 Problem |
|:-:|:-----|:------------|:-------------|
| A2 | 既存ログ・既存出力形式を読むコマンドを書かせる委譲では、そのスキーマ文書を `primary_sources` に含める | `.claude/rules/hga-summoning.md` §primary_sources | subagent への一次資料未提供（同型再発） |
| A3 | MAGI Phase 0 Grounding に「`docs/adr/` の既存 ADR 一覧走査」を追加 | `.claude/skills/magi/SKILL.md` | AoT 前提検証の穴 |
| A6 | NFR-W-C-1 の gabriel タイムアウト目安（60 秒 SHOULD）を実測ベースで見直す | `docs/internal/06_DECISION_MAKING.md` | 規約と運用の乖離（294 秒実測） |

**判定の写像**: 本カテゴリは既存文書への追加・改訂であるため、決定木の出力を次の 3 分岐へ写像する。

| 決定木の出力 | 写像 |
|:-------------|:-----|
| 保全 | 原案通り追加する |
| 圧縮 | 既存条項への例追加・書式例追記など、**規範文を増やさない形**で追加する |
| 削減 | 追加しない |

3 件はいずれも「既存条項への吸収で規範文を増やさずに済むか」を W1 で判定する（retro §4 Try 表の「条項増減見込み」欄が判定の入力）。

**M-1 の目的との整合**: M-1 は条項の削減を目的とする Milestone ではない（§2 Non-Goals 1 / ADR-0011 Option C）ため、retro 由来の追加候補をトリアージにかけること自体は目的と矛盾しない。一方で、判定を経ずに条項を足すことは 4 軸トリアージの意義を損なうため、**本カテゴリの 3 件を W1 の判定を経ずに直接適用してはならない**（MUST NOT）。

### §5.4 トリアージ表の PM 級一括承認（FR-6, FR-3 接続）

トリアージ表全体を 1 承認イベントとする K5 パターンを W1 末に適用する（FR-6）。適用（圧縮・削減・SSOT 退避の実行）は W2 の Task として分離し、W1 中は実行しない。

承認記録は Wave 実施中は `SESSION_STATE.md` に残り、Milestone retro（VCS 管理下）に永続化される（FR-3 受け入れ条件 2 準拠）。§3.2 で述べた通り、W1 の承認プロンプトは「PM 級ファイルの編集予定一覧」ではなく「トリアージ表という決定内容」を対象とする。

### §5.5 Opus 5 安定性ゲート（FR-2 / Red-6 の解決）

W1 完了時点で以下 3 条件をすべて満たした場合のみ W2 へ進む。

| 条件 | 判定方法 | 母数・期間 |
|:---|:---|:---|
| malformed / tool 呼び出し異常ゼロ | `docs/artifacts/` に新規起票された tool malformed インシデント文書が 0 件 | W1 着手から W1 完了までの全セッション（最低 3 セッション。3 未満なら判定を保留し W1 を延長する） |
| pytest regression ゼロ | W0 ベースライン比で PASS 数が減っていない、かつ FAIL が 0 | W1 末の測定 1 回 |
| gabriel verdict 分布に異常なし | W1 中の gabriel probe で `verdict=refuted & severity=critical` が 2 回以上連続していない | W1 中の probe 実行全件。probe 実行 0 回の場合は本条件を「判定不能」として skip し、残り 2 条件で合否を決める |

**不合格時の手順**: Opus 4.7 へフォールバックし M-1 を一時停止する。W1 で確定したトリアージ表（分析成果）はそのまま保持され、再開時に再利用する（損失は W1 の分析リードタイム分に留まる）。

**記録先**: ゲート判定結果（合格 / 不合格）は `docs/artifacts/m-1-opus5-stability-gate.md` に記録する（FR-2 受け入れ条件 2）。

---

## §6 W2 設計（規律本体の適用）

### §6.1 `model-roster.md` 新設 + SSOT 退避（FR-10, FR-11, FR-14）

`.claude/rules/model-roster.md`（新設）は ADR-0011 決定 2 が定める 4 項目を持つ:

1. **現行ロスター表**（層 L1 / L1.5 / L2 / L3 / HGA × モデル ID × 有効日）
2. **層内閾値**（例: 当該モデルにおける L1 直接実装量の上限）
3. **挙動デルタ**（`model-delegation-prompting.md` の該当節をトリアージ後に吸収）
4. **単価・envelope**（`hga-summoning.md` の該当節を §5 のトリアージ後に吸収）

**`CLAUDE.md` に残すもの**: 層の定義（L1 = 判断 / L1.5 = 司令塔 / L2 = 実行 / L3 = 採点）のみ。モデルが変わっても層は変わらないため、層の定義とモデル名の束縛を分離する。`CLAUDE.md` §作業体制からモデル ID の直書き（`opus` / `sonnet` / `haiku` / `fable` / `claude-*-数字` パターン）を、例外登録対象（§6.2 の「時点記録」分類）を除き除去し、`model-roster.md` への導線を 1-2 行追加する（FR-11）。

**ADR-0001 との関係**: `model-roster.md` は ADR-0001 を supersede しない。ADR-0001 が決めたのはルーティングの構造（どの層で誰が判定するか / Opus をメインセッション専用にする）であり、`model-roster.md` が持つのはモデル名の束縛である。両者は直交する（FR-14）。

**移行手順**: `model-delegation-prompting.md` および `hga-summoning.md` のモデル固有記述を `model-roster.md` へ移動し、元ファイルには参照のみを残す。移動内容（移動元・移動先）は削減台帳（§6.3）に記録する。

### §6.2 `verify_model_reference` の実装形態（FR-12 / Red-4 の解決）

**確定**: 新規スクリプト `.claude/scripts/verify_model_reference.py` として実装する（既存 `verify_reference_resolution.py` へのパターン追加ではない）。

**根拠**（§9 却下案 2 に却下理由を記載）:

1. 3 分岐処理（層への割当 → SSOT 退避 / 設計上の性質の説明 → 圧縮 / 時点記録 → 例外登録）は `verify_reference_resolution.py` が扱う参照解決の検査とロジックが異なる（存在検査 vs 記述の性質分類）
2. `update-model` skill（§8.2）から単独で呼び出す必要がある（FR-13 が定める手順のステップ 3）
3. `.claude/rules/auto-generated/rule-002.md`（`verify_reference_resolution.py` 系の parser drift 保守を対象とする）が既に `verify_reference_resolution.py` を保守対象に指定しており、異ドメインの検査を足すと rule-002 の適用範囲が過大になる

**検出パターン**: モデル名の正規表現（Opus / Sonnet / Haiku / Fable ＋ バージョン数字、および `claude-opus-*` / `claude-sonnet-*` / `claude-haiku-*` 系 ID）。

**3 分岐判定ロジック（擬似コード）**:

```python
from __future__ import annotations
# NFR-4: Python 3.8 互換（match / dict merge / str.removesuffix 不使用）
# NFR-5: subprocess.run を使う場合は encoding="utf-8", errors="replace" を指定する

_MODEL_NAME_PAT = re.compile(
    r"\b(Opus|Sonnet|Haiku|Fable)[\s-]?\d+(\.\d+)?\b"
    r"|claude-(opus|sonnet|haiku)-\d[\w.-]*",
    re.IGNORECASE,
)

# 例外登録は「記述の性質」単位で判定する（ファイルパス単位ではない / gabriel 指摘 1 の反映）
def classify(match_context, source_path):
    if _is_layer_assignment(match_context):        # 例: 「L1 = Opus」のような層への割当表現
        return "layer_assignment"                    # → SSOT (model-roster.md) へ退避
    if _is_time_stamped_source(source_path):         # docs/artifacts/ / docs/adr/ / 実測ログ
        return "point_in_time_record"                 # → 例外登録（変更しない）
    return "design_property_description"             # 既定 → 圧縮対象（モデル名を落として意味が通れば落とす）
```

**出力形式**: `verify_reference_resolution.py` の出力形状（`{"total_drifts": int, "drifts_by_wave": {...}}`、各 drift エントリが `pattern` / `source` / `referenced` / `match` キーを持つ）に揃え、3 分岐の判定結果を格納する `classification` キーを追加する:

```json
{
  "total_drifts": 3,
  "drifts": [
    {
      "pattern": "model-name-literal",
      "source": ".claude/agents/gabriel.md",
      "referenced": "Opus",
      "match": "同一モデル（Opus）の別ペルソナ",
      "classification": "design_property_description"
    }
  ]
}
```

**正例・誤例（FR-12 受け入れ条件 2）**: `.claude/agents/gabriel.md` 本文の「同一モデル（Opus）の別ペルソナ」という frontmatter 外のプローズ記述を対象に実行し、`design_property_description`（圧縮対象）として正しく分類されることを誤例として実測する（現行 `verify_reference_resolution.py` にはこの分類ロジックが存在せず未検出のままであることが drift）。

**呼び出し形式**: `bash .claude/scripts/py_invoke.sh .claude/scripts/verify_model_reference.py`（`CLAUDE.md` §Python Invocation Convention の skill/手動 CLI form = 相対パス）。

### §6.3 削減台帳の配置と形式（FR-7 / Red-5 の解決）

**確定**: `docs/artifacts/m-1-clause-ledger.md`。列は 7 種（閉集合）:

| 条項ID | 原文 | 出典（ファイル:節） | 判定軸（軸1〜4の値） | 判定（圧縮/削減/SSOT退避） | 移動先 | 判定日 |
|:------|:-----|:-------------------|:---------------------|:---------------------------|:-------|:-------|

**NFR-2（帳簿単一原則）との整合**: 本台帳は記録表であり、成果物の合否を判定する帳簿ではない。成果物判定の帳簿は Green State 1 冊のみである（`fable-l3-protocol.md` §3 帳簿単一原則）。削減台帳への記載件数や記載の有無が Green State の判定条件（G1〜G5）に加算されることはない。

**FR-7 の 3 列との関係**: FR-7 が要求する最小構成（原文 / 判定軸 / 移動先）を、上記 7 列（条項ID・出典・判定日を加えた拡張版）として満たす。W1 トリアージ表の圧縮・削減判定件数と本台帳の記載件数は、判定日（W2 適用日）を基準に件数突合で確認する（FR-7 受け入れ条件 3）。

### §6.4 HGA 召喚ゲート改訂（FR-15）

ADR-0011 決定 4 の内容を `hga-summoning.md` §召喚ゲート節に反映する。

- **廃止**: 無条件召喚 2 条件（spec/design 初期 / 不可逆な設計コミット）を事後条件の判定材料へ格下げする
- **新ゲート**: MAGI `AC-W-C-7`（gabriel critical refute 2 回目 = 再 MAGI 上限到達）への接続として定義する。新規判定機構は作らない
- **移行期規定**: M-1 実施中は旧ゲートを適用する。新ゲートは M-1 完了（W4 retro）後に発効する（新ゲートの検証を新ゲート自身に委ねる自己言及を回避するため）

改訂は `hga-summoning.md` 内の該当節の書き換えとして行い、単価・envelope の `model-roster.md` への移動（§6.1）とは別の編集単位として扱う（同一ファイルへの複数編集は §3.2 の同一 K5 宣言内で処理する）。

### §6.5 R-2 W2/W3 再スコープの判定手続き（FR-21 / Red-7 の扱い）

§5.3 でトリアージ表に組み込んだ R-2 予定条項 3 件について、4 軸判定の出力を以下の 3 分岐へ写像する:

| 決定木の出力 | R-2 への写像 |
|:-------------|:--------------|
| 保全 | 実施（原案通り追加する） |
| 圧縮 | 圧縮形で実施（意図 1 行に畳んだ形で追加する） |
| 削減 | スキップ（追加しない） |

判定は W1 トリアージ表の出力に依存するため、design 時点では本手続き（3 分岐への写像規則）のみを確定し、3 件それぞれの判定結果は確定しない（Red-7）。判定結果は `docs/specs/r-2-consolidation/tasks.md` の該当 Task（W2-R2-T9 / T12 / T13、W2-R2-T13b、W3-R2-T24）完了記録に反映する（FR-21 受け入れ条件 2, 3 / §3.2 の W2 PM 級ファイル編集計画に対応）。

### §6.6 trust-model.md への接続（FR-9）

決定 3 第 3 層（復活経路）を、`trust-model.md` の既存機構（「同一パターンが 2 回以上の検出イベントで発火 → `/retro` でルール候補を提案」）への接続のみで実現する。新規実装は行わない。

削減台帳（§6.3）に記載された各条項について、その条項が本来防いでいたはずの失敗パターンが削減後に再発した場合、これを「不在起因の検出イベント」として `tdd-patterns.log` / HGA 召喚ログ / 監査 Stage 記録 / gabriel probe 記録のいずれかに記録する（`trust-model.md` §カウント単位が定める検出イベントのデータソースをそのまま用いる）。閾値 2 回に達した条項は復活候補として `/retro` Step 2.5 の既存フローに接続し、人間が承認 / 却下を判断する。新規のカウント機構・新規ログファイルは追加しない（FR-9 受け入れ条件 2）。

---

## §7 W3 設計（skills / agents の構造改善）

### §7.1 skills / agents の判定軸（FR-16 / Red-2 の解決）

規律文書向けの 4 軸（§5.2）とは別に、以下の 4 軸を定義する。

| 軸 | 問い | 分割側 | 保全側 |
|:---|:---|:---|:---|
| **軸 S1 発火頻度** | その記述は skill 起動のたびに必要か | 特定分岐でのみ必要 | 毎回必要 |
| **軸 S2 参照到達性** | 外部ファイルへの参照を既に持つか | 外部参照ゼロ（全インライン） | 既に `references/` ディレクトリへの外部参照として分離済み |
| **軸 S3 条件付き実行** | 特定の条件下でのみ実行される手順か | 条件分岐の中にのみ現れる | 無条件に実行される |
| **軸 S4 契約か手順か** | frontmatter / description（契約）か本文手順か | 本文手順（起動後に読めば足りる） | 契約（常時ロードが必要） |

**決定木**:

```
100 行超 かつ 軸S2 = 外部参照ゼロ
  → 分割候補
      → 軸S1・軸S3 で切れ目を探す
          ├ 切れ目あり → references/ 配下へ退避し本体から参照
          └ 切れ目なし → 保全（分割すると手順の意味が壊れるため）
100 行以下 または 軸S2 = 既に外部参照分離済
  → 保全（対象外）
```

### §7.2 優先対象の特定方法（FR-16）

軸 S2（参照到達性）の判定は、**`references/` ディレクトリへの実体分離の有無**で行う。本文中に他ファイルへの Markdown リンクが 1 本あることと、手順本体が外部ファイルへ分離されていることは別事象であり、progressive disclosure と呼べるのは後者のみである。

```bash
for f in .claude/skills/*/SKILL.md; do
  lines=$(wc -l < "$f")
  refdir="$(dirname "$f")/references"
  if [ "$lines" -gt 100 ] && [ ! -d "$refdir" ]; then
    printf "%5s  %s\n" "$lines" "$f"
  fi
done | sort -rn
```

**2026-07-25 時点の実測結果（design レビュー時に実行 / W3 着手時に再実測して確定する）**:

| 行数 | skill |
|---:|:---|
| 951 | `full-review` |
| 419 | `goal-driven` |
| 288 | `init-harness` |
| 268 | `spec-template` |
| 234 | `adr-template` |
| 185 | `autonomous` |
| 180 | `ship` |
| 136 | `building` |
| 135 | `retro` |

対象外（`references/` へ実体分離済）: `lam-orchestrate`（280 行）/ `magi`（329 行）。

**旧判定式の欠陥（design レビューで検出・修正済）**: 当初案は `refs=$(grep -cE "references/|\]\([^)]+\)" "$f")` が 0 であることを条件としていた。この式は Markdown リンクを外部参照とみなすため、**951 行でありながらリンクが 1 本あるだけの `full-review` を「分離済み」と誤判定して対象から外す**。旧式の実測 HIT は `building` / `init-harness` / `retro` / `ship` の 4 件であり、最優先対象であるはずの `full-review` を含まない。これは `subprocess-encoding-convention.md` §grep baseline の既知の限界と同型の、測定式が対象の構造をまたげない欠陥である。

**requirements FR-16 との不一致（W3 着手時に PM 級で訂正）**: requirements.md FR-16 は説明・受け入れ条件 2 の双方で「優先対象 **4 件**（`full-review` を含む）」を要求している。しかし新判定式の実測は **9 件**であり、旧判定式では `full-review` が対象外になる。すなわち requirements の「4 件」と「`full-review` を含む」は、**どちらの判定式でも同時には成立しない**。

**本設計の扱い**: 上表の実測（9 件 / 行数降順）を正とし、**W3 のスコープは行数降順の上位 4 件**（`full-review` / `goal-driven` / `init-harness` / `spec-template`）とする。これにより requirements の「4 件」という件数と「`full-review` を含む」という要求の双方を満たす。残り 5 件は対象として認識した上で M-1 スコープ外へ送り、**W3 の Wave 完了記録に「未着手 5 件」を明記する**（silent な打ち切りにしない）。requirements FR-16 の説明文および受け入れ条件 2 の内訳表記は、W3 着手時に本実測へ更新する（PM 級）。

progressive disclosure 化の実施後は、対象 skill の主要な発火条件・振る舞いに変更がないことを動作確認で検証する（FR-16 受け入れ条件 3）。

### §7.3 quality-auditor × code-reviewer の重複（Red-3 の扱い）

`quality-auditor`（328 行）と `code-reviewer`（97 行）の守備範囲重複は W3 で扱うが、判断材料の収集を先行させる（行数は 2026-07-25 実測）。

**当初案の破棄（design レビューで検出・修正済）**: 当初案は `grep -rl "<agent 名>" docs/artifacts/*.md | wc -l` を「呼び出し実績」の代理指標としていたが、これは 2 重に成立しない。(i) 文書内での**言及**であって**起動実績**ではない（本日の retro §3 が検出した「盲目の計器」と同型）。(ii) 実測値は `quality-auditor` 10 件 / `code-reviewer` 11 件で**両方とも非ゼロ**であり、当初案の分岐規則（「一方がゼロなら統廃合を提案、両方非ゼロなら現状維持」）は**収集 Task を実行する前に結論が「現状維持」で確定してしまう**。以下 2 指標へ差し替える。

#### 指標 1: 起動実績の直接証跡

```bash
ls -ld .claude/agent-memory/quality-auditor .claude/agent-memory/code-reviewer
```

`memory: project` 機構により、subagent は起動され知見を書いたときにのみ当該ディレクトリを更新する（`CLAUDE.md` §Subagent Persistent Memory）。**2026-07-25 時点の実測**: 両ディレクトリとも存在し、最終更新は `code-reviewer` 2026-06-11 / `quality-auditor` 2026-06-19。すなわち**どちらも死んでいない**が、**どちらも 1 か月以上更新されていない**。

**限界の明示**: 本指標が示すのは「起動されたことがあるか」と「最後に知見を書いた日」のみであり、起動回数は測れない。起動しても memory へ書かなければ更新されない。回数の集計機構は追加しない（NFR-2 準拠）。

#### 指標 2: 責務定義の重複度（Red-3 の本題）

指標 1 により「一方が未使用だから統合する」という筋は実測で否定された。よって Red-3 の判断材料を**責務定義そのものの重複度**へ移す。`.claude/agents/quality-auditor.md` と `.claude/agents/code-reviewer.md` の frontmatter `description` および本文の守備範囲記述を並置し、W3 で次の 2 点を判定する。

1. 両者の `description` が指す起動条件に重なりがあるか（重なりがあると、呼び出す側がどちらを選ぶべきか判断できない）
2. 一方の守備範囲が他方の真部分集合になっているか

**分岐**: 上記 1 と 2 の**両方が成立する場合にのみ**統廃合を提案する。それ以外は現状維持とし、`description` の書き分け（起動条件の排他化）のみを行う。統廃合そのものを目的化しない。

### §7.4 ADR-0010 I-1〜I-6 適合確認（FR-17）

ADR-0010 §統治不変条件（I-1〜I-6）に対する W3 成果物の適合を、以下のチェック表で確認する。

| I | 内容要約（ADR-0010 原文） | W3 確認観点 |
|:--|:--------------------------|:-------------|
| I-1 | project を上書きできる層（enterprise / personal）にユーザー起動・モデル起動スキルを置かない。共有 harness は名前空間付き plugin としてのみ配布する | W3 の progressive disclosure 化が `~/.claude/skills/` への直置きを発生させないことを確認する（LAM の変更は `.claude/skills/`（project 層）に閉じる） |
| I-2 | plugin の enable はプロジェクト設定スコープでのみ行う | 本 Wave はプロジェクト内変更のみのため非該当。非該当であることの確認記録のみ残す |
| I-3 | project 層のスキルは実体ファイル（vendored）。他所への symlink 禁止 | progressive disclosure 化で `references/` へ退避するファイルが実体ファイルであり symlink でないことを確認する |
| I-4 | CLAUDE.md 等からのスキル参照は名前空間を常に明示する | LAM 内部の相互参照（`CLAUDE.md` → `model-roster.md` 等）に plugin 名前空間の対象がないことを確認する（現状 LAM は project 層完結のため通常は非該当） |
| I-5 | personal 層に残る共有可変資産（hooks / settings）は版管理下に置き、変更は commit を伴う | 本 Wave は `.claude/` 配下（project 層）の変更のみのため非該当 |
| I-6 | 共有 agent の配布はスキルと同一チャネル（versioned plugin の `agents/`）で行う。personal 層への共有 agent 直置きは禁止 | W3 の agents 統廃合検討（§7.3）が `~/.claude/agents/` への直置きを発生させないことを確認する |

適合確認の実施記録（各 I に対する適合 / 不適合の判定）を W3 完了記録に残す。不適合が発見された場合、PM 級判断に差し戻す（§3.2 W3「条件付き追加宣言」に対応）。

---

## §8 W4 設計（検証・確定）

### §8.1 ベースライン再測定（FR-8）

§4.1 と同一の 6 項目・同一の手順を W4 末に再実行し、`docs/artifacts/m-1-baseline-w4.md` に記録する。§3.4 の Wave 末測定と同一の実行形式を用いる。W0 と W4 の測定値を比較し、pytest regression ゼロ（NFR-3）、および NFR-1 が定める発火点・承認ゲート・宣言イベントの数が不変であることを確認する（DoD-4）。

### §8.2 `update-model` skill の設計（FR-13, FR-14 接続）

`.claude/skills/update-model/SKILL.md` を、判断ロジックを含まない薄い順序表として作成する。

**手順（6 ステップ / FR-13 説明を踏襲）**:

1. upstream 一次資料確認（`upstream-first.md` 準拠。§4.3 と同一手順）
2. `model-roster.md` 更新
3. `verify_model_reference` 実行（§6.2 のスクリプトを呼び出す）
4. `.claude/agents/*.md` frontmatter 更新
5. ベースライン再測定（§4.1 と同一の 6 項目手順）
6. 配布カタログ（§8.3）への追記

各ステップは既存スクリプト・コマンドの呼び出しとして記述し、条件分岐・閾値判定コードを skill 内に実装しない（FR-13 受け入れ条件 1, 2）。

**FR-14 接続**: 手順 2（`model-roster.md` 更新）の直後に「ADR-0001 の『Opus は hooks/subagents で使用しない』制約を破らないことの確認」ステップを追加する（FR-14 受け入れ条件 2）。

**整合検証**: skill の手順と、手順が呼び出す各スクリプト（`verify_model_reference` を含む）の整合を検証する pytest を用意する（テストファイル名は BUILDING で確定する。design 時点では「整合検証 pytest が存在すること」のみを要求する / FR-13 受け入れ条件 3）。

### §8.3 配布 2 経路（FR-18）

| 配布対象 | 経路 | 根拠 |
|:--------|:-----|:-----|
| skills / agents の変更（W3 成果物） | ADR-0010 の plugin チャネル（`lam-harness` の version bump） | ADR-0010 I-6 / I-1 |
| 規律の変更（`CLAUDE.md` / `.claude/rules/` / `model-roster.md` パターン） | カタログ（`docs/artifacts/m-1-distribution-catalog.md`） | plugin チャネルに載らない性質のため |

カタログの列は 7 種（閉集合）: 変更項目 / 種別 / LAM 固有度 / 必要 harness バージョン / 前提モデル世代 / 依存 / 判断軸。正本は `docs/artifacts/m-1-distribution-catalog.md`、配布用コピーは LAM リポジトリ外に書き出す（ADR-0011 §決定 5 が参照する 2026-07-21 の前例を踏襲。当該前例の書き出し先パスは本設計では未確認のため、W4 着手時に既存の配布運用を確認して踏襲する）。

**配布実行の承認ゲート**: `lam-harness` plugin の version bump および LAM リポジトリ外への配布コピー書き出しは、**LAM リポジトリの外部へ変更を公開する不可逆な操作**である。`permission-levels.md` のファイルパスベース分類では PM 級パスに含まれないが、第 0 原則の軸（可逆性 / 復旧コスト）では不可逆側に立つため、**W4 の配布実行の直前にユーザー承認を得る**（`core-identity.md` §第 0 原則 / `permission-levels.md` §迷った場合）。カタログ正本（`docs/artifacts/` 配下）の作成自体は SE 級であり本ゲートの対象外とする。

### §8.4 Milestone retro（DoD-6 接続）

Milestone retro（`docs/artifacts/retro-M1-<date>.md`）に以下を記録する:

1. §6.5 の R-2 W2/W3 再スコープ結果（実施 / 圧縮形で実施 / スキップ）が `docs/specs/r-2-consolidation/tasks.md` の該当 Task 完了記録へ反映されたことの確認
2. §8.1 のベースライン比較結果（W0 vs W4）
3. 削減台帳（§6.3）のサマリ（圧縮・削減・SSOT 退避の件数内訳）
4. §6.6 の trust-model.md 接続状況（M-1 完了時点で復活候補が存在するかの確認）

---

## §9 Alternatives Considered

| # | 判断 | 採用案 | 却下案 | 却下理由 |
|:-:|:-----|:-------|:-------|:---------|
| 1 | 条項トリアージの粒度 | 1 条項 = 1 規範文（RFC 2119 キーワードまたは日本語規範表現を含む文 / §5.1） | 見出し単位（`## §N` ごとを 1 条項とする） | 解像度不足。`fable-l3-protocol.md` が §0〜§11 の 12 条項にしかならず、二重記述（F0-F4 / 60 秒実況）の解消判断に必要な粒度が得られない |
| 2 | `verify_model_reference` の実装場所 | 新規スクリプト `.claude/scripts/verify_model_reference.py`（§6.2） | 既存 `verify_reference_resolution.py` へのパターン追加 | 検査ロジックが異なる（3 分岐処理 vs 存在検査）。`update-model` skill から単独呼び出しが必要。`rule-002.md` の保守対象範囲が過大になる（§6.2 根拠 1〜3 参照） |
| 3 | トリアージ判定の実施方式 | 4 軸判定を人手で実施し、判定過程・根拠 1 行をトリアージ表へ記録する（§5.2, §5.4） | トリアージ判定を機械化（正規表現 + ルールベースの自動判定） | 軸 1（帰属 = ユーザー意思かモデルの誤り予防か）は文面から機械判定できず、誤判定が veto 対象条項の削減という不可逆な結果に直結する。要求事項 2（削減が劣化を招いた場合に検出・復活できること）とも整合しない |
| 4 | 削減台帳の運用位置づけ | 記録表として運用し、Green State とは独立させる（§6.3） | 削減台帳を Green State と並立する第 2 の判定帳簿として運用する | `fable-l3-protocol.md` §3 帳簿単一原則（成果物判定の帳簿は Green State 1 冊のみ）に違反する。NFR-2 が明示的に禁止する |
| 5 | `model-roster.md` の配置形態 | `.claude/rules/model-roster.md` として独立ファイルで新設する（§6.1） | `CLAUDE.md` 内の 1 節としてモデルロスターを統合する | requirements.md FR-10 が独立ファイルの新設を明示的に指定している。また `CLAUDE.md` は毎セッション頭に載るファイルであり、モデル世代交代のたびの差分レビュー対象を `CLAUDE.md` 全体に広げると FR-11 が要求する「層の定義のみを残す」という分離目的が損なわれる |

---

## §10 Success Criteria（DoD-1〜DoD-6 への対応）

### §10.1 DoD 対応表

| DoD | 内容（requirements.md §5 準拠） | 対応設計節 |
|:---:|:----------------------------------|:-----------|
| DoD-1 | 全 5 Wave（W0〜W4）が Green State で完了（Opus 5 安定性ゲート合格またはフォールバック手順を経て通過） | §3.4, §5.5, §8.1 |
| DoD-2 | トリアージ表が PM 級一括承認済みで、削減台帳が全圧縮・削減対象条項を網羅 | §5.4, §6.3 |
| DoD-3 | `model-roster.md` 新設 + `verify_model_reference` 機構（3 分岐処理）+ `update-model` skill（薄い順序表）の 3 点が成立し pytest で検証可能 | §6.1, §6.2, §8.2 |
| DoD-4 | W0 と W4 のベースライン測定 6 項目を比較し、pytest regression ゼロかつ NFR-1 の発火点・承認ゲート・宣言イベント数が不変であることを確認 | §8.1, §3.4, §4.5（項目 3 の計器較正 / 不成立時は項目 3 を判定条件から除外） |
| DoD-5 | 配布 2 経路が完了し、ADR-0010 I-1〜I-6 適合確認（R-3）が記録されている | §8.3, §7.4 |
| DoD-6 | Milestone retro が実施され、R-2 W2/W3 の再スコープ結果が `docs/specs/r-2-consolidation/tasks.md` に反映されている | §8.4, §6.5 |

### §10.2 FR / NFR トレーサビリティ対応表

| FR/NFR | 対応設計節 |
|:-------|:-----------|
| FR-1 | §3.1 |
| FR-2 | §5.5 |
| FR-3 | §3.2, §5.4 |
| FR-4 | §5.1, §5.2 |
| FR-5 | §5.2 |
| FR-6 | §5.2, §5.4 |
| FR-7 | §6.3 |
| FR-8 | §3.4, §4.1, §4.5, §8.1 |
| FR-9 | §6.6 |
| FR-10 | §6.1 |
| FR-11 | §6.1 |
| FR-12 | §6.2 |
| FR-13 | §8.2 |
| FR-14 | §6.1, §8.2 |
| FR-15 | §6.4 |
| FR-16 | §7.1, §7.2 |
| FR-17 | §7.4 |
| FR-18 | §8.3 |
| FR-19 | §4.3 |
| FR-20 | §4.4 |
| FR-21 | §5.3, §6.5 |
| NFR-1 | §3.4, §5.2（不変制約 4 対象が発火点・承認ゲートの不変を担保） |
| NFR-2 | §6.3, §6.6 |
| NFR-3 | §3.4, §4.1, §8.1 |
| NFR-4 | §6.2 |
| NFR-5 | §6.2 |
| NFR-6 | §2（Non-Goals 1）, §8.1（測定は報告するが DoD 条件にしない） |

FR-1〜FR-21・NFR-1〜NFR-6 のすべてが §1〜§8 のいずれかの節で扱われていることを確認した。孤児・漏れはゼロである。

---

## §11 Red 解決記録（requirements §7 準拠）

requirements.md §7 の未解決質問（7 件）について、本設計での解決状況を以下に区分する。

### 本設計で解決（5 件）

1. **Red-1（条項粒度の定義）**: §5.1 で確定（1 条項 = 1 規範文 / RFC 2119 キーワードまたは日本語規範表現を含む文）
2. **Red-2（skills / agents の progressive disclosure 判定軸）**: §7.1 で確定（軸 S1〜S4 + 決定木）
3. **Red-4（`verify_model_reference` の実装形態）**: §6.2 で確定（新規スクリプト。既存スクリプトへのパターン追加は不採用 / §9 却下案 2）
4. **Red-5（削減台帳の配置パスと形式）**: §6.3 で確定（`docs/artifacts/m-1-clause-ledger.md` / 7 列）
5. **Red-6（FR-2 安定性ゲートの合格判定の具体）**: §5.5 で確定（観測期間・母数・「異常なし」の閾値を含む 3 条件表）

### W3 で扱う（1 件）

6. **Red-3（`quality-auditor` と `code-reviewer` の守備範囲重複）**: §7.3 で手続きを確定。design レビュー時の実測（両 agent とも `agent-memory` 存在 = どちらも未使用ではない）により「一方が死んでいるから統合する」という筋は**否定済**。判断材料を責務定義の重複度へ移し、「起動条件の重なり」×「真部分集合関係」の 2 条件がともに成立する場合にのみ統廃合を提案する。統廃合の是非自体は design 段階で確定しない

### 手続きのみ確定（1 件）

7. **Red-7（R-2 W2/W3 の再スコープ判定）**: §6.5 で 3 分岐への写像手続きを確定した。判定は W1 トリアージ表の出力に依存するため、3 件それぞれの判定結果自体は design 段階では確定しない

---

## 参照

- `docs/specs/m-1-opus5-migration/requirements.md`（Approved / 本設計の入力）
- `docs/adr/0011-clause-triage-and-model-generation-governance.md`（ADR-0011 / 本設計が展開する決定の正本）
- `docs/adr/0001-model-routing-strategy.md`（ADR-0001 / FR-14, FR-20 の根拠）
- `docs/adr/0005-thin-harness-autonomous-governance.md`（ADR-0005 FR-9.1 / 不変制約の根拠）
- `docs/adr/0007-magi-v2-gabriel-integration.md`（ADR-0007 / 不変制約・§6.4 の根拠）
- `docs/adr/0009-hga-fable-summoning.md`（ADR-0009 / §6.4 の改訂対象）
- `docs/adr/0010-global-claude-assets-governance.md`（ADR-0010 / §7.4, §8.3 の根拠）
- `.claude/rules/auto-generated/trust-model.md`（§5.2, §6.6 の参照先）
- `.claude/rules/auto-generated/rule-002.md`（§6.2 根拠 3 の参照先）
- `.claude/rules/permission-levels.md`（§3.2, §5.2 の根拠）
- `.claude/rules/fable-l3-protocol.md`（§5.2, §6.3 の根拠）
- `.claude/rules/core-identity.md`（§5.2 軸 3 の根拠）
- `.claude/rules/hga-summoning.md`（§6.1, §6.4 の改訂 / 吸収対象）
- `.claude/rules/model-delegation-prompting.md`（§6.1 の吸収対象）
- `.claude/rules/upstream-first.md`（§4.3, §8.2 の根拠）
- `.claude/rules/subprocess-encoding-convention.md`（§6.2 NFR-5 の根拠）
- `.claude/rules/planning-quality-guideline.md`（品質基準）
- `.claude/rules/terminology.md`（用語階層 / §5.3 の対象文書）
- `.claude/scripts/verify_reference_resolution.py`（§6.2 の出力形式の参照元）
- `docs/specs/r-2-consolidation/tasks.md`（§5.3, §6.5 の反映先）
- `docs/specs/r-2-consolidation/design.md`（書式の型・参考元）
