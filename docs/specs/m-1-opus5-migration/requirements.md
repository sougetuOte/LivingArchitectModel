# M-1 Milestone Requirements: Opus 5 移行 + 規律の条項トリアージ

## メタ情報

| 項目 | 内容 |
|:-----|:-----|
| Milestone | M-1 (Opus 5 移行 + 規律の条項トリアージ) |
| ステータス | **Approved** (2026-07-25 / ユーザー承認) |
| 作成日 | 2026-07-25 |
| 更新日 | 2026-07-25 |
| 起源 | ADR-0011 (Accepted 2026-07-25) |
| SSOT | 本ファイル |
| 意思決定記録 | MAGI 合議 (AoT 6 Atom + gabriel probe / 2026-07-25) |
| 一次素材 | 合議録（`docs/artifacts/2026-07-25-magi-m1-opus5-migration.md`） |
| 関連ルール | `.claude/rules/auto-generated/trust-model.md` / `.claude/rules/permission-levels.md` / `.claude/rules/fable-l3-protocol.md` / `.claude/rules/hga-summoning.md` / `.claude/rules/model-delegation-prompting.md` |

---

## 1. 概要

### 1.1 背景（Problem Statement）

2026-07-25、Anthropic は Claude Opus 5 をリリースし、同日 "The new rules of context engineering for Claude 5 models" を公開した。同記事は Claude Code の system prompt を 80% 以上削除しても coding evaluation に有意な低下がなかったという自社実測を根拠に、6 つのパラダイム転換（Rules→Judgement / Examples→Design Interfaces / Put upfront→Progressive Disclosure / Repeat yourself→Simple tool descriptions / Memory in CLAUDE.md→Auto-memory / Simple specs→Rich references）を提示している。

一方 LAM は憲法型ハーネスとして意図的に規律を積み上げてきた。2026-07-25 時点の実測（Sonnet 調査 / tool_uses 33）では、`.claude/` 配下の規律・実行資産は 44 ファイル 8,182 行（`CLAUDE.md` 269 行 / `.claude/rules/` 16 ファイル 2,176 行 / `.claude/skills/` 15 ファイル 3,656 行 / `.claude/agents/` 12 ファイル 2,081 行）に達している。うち `.claude/rules/` の「禁止」39 件の 59%（23 件）が `fable-l3-protocol.md`（12 件）と `phase-rules.md`（11 件）の 2 ファイルに集中しており、F0-F4 実行プロトコルと 60 秒実況が両ファイルにほぼ同内容で二重記述されている。

ADR-0011 の中核判断は次の一文に集約される: 「M-1 は『削減の Milestone』ではなく『峻別基準と予防機構を作る Milestone』である。削減量は結果であって目標ではない。」本 requirements.md は、この ADR-0011（Accepted）の決定内容を実装可能な要求仕様として写像したものであり、新しい設計判断を追加するものではない。

### 1.2 ユーザーストーリー

```
As a LAM プロジェクト運用者 (L1 統括 = Living Architect),
I want Opus 5 世代への移行にあたり、LAM の規律群を「保全すべき統治意思」と
   「圧縮・削減可能な予防的記述」に条項単位で峻別し、モデル世代交代のたびに
   規律全体を見直す構造を単一 SSOT に畳む Milestone,
So that Anthropic の新しい context engineering 原則を LAM 固有の統治文脈に
   安全に適用でき、かつ次のモデル世代交代コストが「1 ファイル + grep 検証」
   に収まる状態になる.
```

### 1.3 スコープ

**含む（W0〜W4 の 5 Wave 固定 / ADR-0011 §実装計画準拠）**:

| Wave | 名称 | 内容 |
|:----:|:-----|:-----|
| W0 | 準備 | 決定 3 第 1 層のベースライン測定 / 削減台帳の器（単純表）の作成 / upstream 一次資料の裏取り（Opus 5・Fable 5 の公式スペック・単価）/ ADR-0001 §改訂履歴の「`fable` 混在指定」記述と実ファイル（`.claude/agents/*.md`）の突合 |
| W1 | トリアージ（判定のみ・適用しない） | veto 先行スクリーニング（軸 1・軸 3 該当条項を保全確定）/ 残りの精査（`fable-l3-protocol.md` 234 行 + `phase-rules.md` 245 行 + `CLAUDE.md` 269 行 ≈ 750 行が実質対象）/ R-2 W2/W3 の予定条項をトリアージ表に含める / トリアージ表の PM 級一括承認（K5 パターン） |
| — | ゲート: Opus 5 安定性確認（W1 → W2） | malformed / tool 呼び出し異常の発生ゼロ / pytest regression ゼロ（W0 ベースライン比）/ gabriel verdict 分布に異常なし。不合格時は Opus 4.7 へフォールバックし M-1 を一時停止（W1 の分析成果は保持される） |
| W2 | 規律本体の適用 | `model-roster.md` 新設 + SSOT 退避 / 圧縮・削減の実行 + 台帳記録 / `verify_model_reference` 機構（3 分岐処理）/ HGA 召喚ゲート改訂（決定 4）/ R-2 W2/W3 の再スコープ実行 |
| W3 | skills / agents の構造改善 | progressive disclosure 化（対象: 100 行超かつ外部参照ゼロの 4 skill。`full-review`（951 行）を含む）/ agents 統廃合検討（`quality-auditor` 328 行と `code-reviewer` 97 行の守備範囲重複）/ ADR-0010 I-1〜I-6 適合確認（R-3 の発火） |
| W4 | 検証・確定 | 決定 3 第 1 層のベースライン再測定 / `update-model` skill 作成 / 配布（決定 5 の 2 経路）/ Milestone retro |

Wave 数は 5（W0〜W4）で固定する（FR-1）。Wave 追加は Milestone 再計画として扱い、PM 承認を要する。

**含まない（Non-Goals）**:

1. **削減量の数値目標**（Anthropic の 80% を目標値として掲げない）
2. **全面書き直し**（ADR-0011 Option D 却下済 — 実測発火由来の規律が全損するため）
3. **ADR-0001 の supersede およびルーティング構造の変更**（直交するため）
4. **R-2 の Definition of Done 自体の変更**（W2/W3 の再スコープは行うが DoD は変更しない）
5. **HGA 新ゲート（事後条件）の M-1 実施中の適用**（移行期は旧ゲートを適用する）
6. **不変制約 4 対象の変更**（FR-5 が定める 4 対象自体の見直しは本 Milestone のスコープ外）
7. **T16（fable-l3 × Fable-Alembic snapshot 統合方針）**（R-2 Non-Goals を継承。判定作業自体もスコープ外）
8. **`D:\work7\Fable-Alembic\` 配下への書き込み**（Outbound Write Ban / `fable-l3-protocol.md` §2）

### 1.4 M-1 の位置づけ

M-1 は R-2 を吸収しない。R-2 の Definition of Done は R-2 のまま維持され、M-1 W1 のトリアージ出力（R-2 W2/W3 の予定条項に対する判定）を R-2 に一方向でフィードバックする依存関係を持つ（Non-Goals 4 / FR-21）。この依存により R-2 W2/W3 の着手は M-1 W1 完了後となるが、これはユーザー既決事項（「R-2 W1 完了後に M-1 着手 / W2/W3 に入る前に統合再スコープ」）の必然的帰結であり、新規に導入する結合ではない。

M-1 は ADR-0011（本 requirements の起源）および ADR-0009 への追補（HGA 召喚ゲートの事後条件化）と対応する。ADR-0001（モデルルーティング戦略）とは supersede 関係を持たず直交し（Non-Goals 3 / FR-14）、ADR-0010（グローバル `~/.claude` 資産の統治）とは配布経路（決定 5 / FR-18）で整合する。

---

## 2. 用語

| 用語 | 定義 |
|:-----|:-----|
| **M-1** | 本 Milestone の識別子（`terminology.md` §1 Milestone 層）。「Opus 5 移行 + 規律の条項トリアージ」を指す |
| **W0〜W4** | M-1 内の Wave（`terminology.md` §1 Wave 層）。それぞれ「準備」「トリアージ」「規律本体の適用」「skills/agents の構造改善」「検証・確定」を指す固有名 |
| **条項トリアージ (Clause Triage)** | ファイル単位ではなく条項単位で 4 軸を評価し、決定木で保全 / 圧縮 / 削減 / SSOT 退避に振り分ける手続き（FR-4） |
| **4 軸** | 条項トリアージの判定軸（軸 1 帰属 / 軸 2 形式 / 軸 3 可逆性 / 軸 4 根拠）。軸 3 は第 0 原則の可逆性・復旧コストを継承し、軸 4 は `trust-model.md` §カウント単位の検出イベント単位定義をそのまま流用する（FR-4） |
| **不変制約** | 軸に関わらずトリアージ対象外となる 4 対象（体験シミュ発火点 3 点 / PM 級承認ゲート・PM 級パス列挙 / gabriel probe 起動条件 / 統治への自己書込禁止）。根拠は対象ごとに分離記述する（FR-5） |
| **検出イベント単位** | `trust-model.md` §カウント単位の既存定義。1 検証イベント内で検出された複数 issue は件数によらず 1 カウントとする。軸 4 の判定はこの既存定義をそのまま用いる |
| **K5 一括宣言方式** | 各 Wave 冒頭で編集予定の PM 級ファイル一覧を一括宣言し、ユーザー承認 1 回を得たうえで Wave 内の残り編集を自律的に進める進行管理方式（R-2 由来 / M-1 でも FR-3 として継承） |
| **`model-roster.md`** | `.claude/rules/model-roster.md`（新設）。モデル名束縛の単一 SSOT。現行ロスター表 / 層内閾値 / 挙動デルタ / 単価・envelope の 4 項目を持つ（FR-10） |
| **`verify_model_reference`** | SSOT 外のファイルにおけるモデル名直書きを検出し、検出結果を 3 分岐（層への割当 / 設計上の性質の説明 / 時点記録）で処理する検査機構（FR-12） |
| **削減台帳** | 圧縮・削減と判定された条項を「原文 / 判定軸 / 移動先」の 3 列で全件記録する表（3 層安全網の第 2 層 / FR-7） |
| **Opus 5 安定性ゲート** | W1 と W2 の間に置く合格判定。malformed / tool 呼び出し異常ゼロ・pytest regression ゼロ・gabriel verdict 分布に異常なしの 3 条件を満たすことを W2 着手の前提とする（FR-2） |
| **HGA 召喚ゲート（事後条件）** | 無条件召喚 2 条件を廃止し、MAGI `AC-W-C-7`（gabriel critical refute 2 回目）への接続として再定義する新ゲート。M-1 完了（W4 retro）後に発効する（FR-15） |
| **配布 2 経路** | skills / agents の変更は ADR-0010 の plugin チャネル（`lam-harness` の version bump）、規律の変更はカタログ（`docs/artifacts/m-1-distribution-catalog.md`）という 2 経路に分割した配布方式（FR-18） |

---

## 3. 機能要求 (FR)

FR は ADR-0011「決定」節（決定 1〜5）・「実装計画」節（Wave 骨子）・gabriel 指摘 2 件・追補 2 件を出典とする。骨格・番号・義務レベルは ADR-0011 を無改変で採用する。

### FR-1: M-1 は W0〜W4 の 5 Wave で構成する (MUST)

**説明**: ADR-0011 §実装計画の Wave 骨子（W0 準備 / W1 トリアージ / W2 規律本体の適用 / W3 構造改善 / W4 検証・確定）をそのまま 5 Wave 構成として採用する。Wave の追加は Milestone の再計画に相当し、PM 承認を要する。

**受け入れ条件**:
- [ ] `docs/specs/m-1-opus5-migration/tasks.md` が W0〜W4 の 5 Wave のみで構成されている（6 番目以降の Wave が存在しない）
- [ ] Wave 追加が必要と判明した場合、`tasks.md` 変更として PM 級承認ゲートを通過している
- [ ] W1 と W2 の間に Opus 5 安定性ゲート（FR-2）が独立したステップとして明記されている

**優先度**: MUST

### FR-2: W1 と W2 の間に Opus 5 安定性ゲートを置く (MUST)

**説明**: 合格条件 3 点（malformed / tool 呼び出し異常の発生ゼロ / pytest regression ゼロ（W0 ベースライン比）/ gabriel verdict 分布に異常なし）をすべて満たした場合のみ W2 へ進む。不合格時は Opus 4.7 へフォールバックし M-1 を一時停止する（W1 の分析成果＝トリアージ表は保持される）。

**受け入れ条件**:
- [ ] `tasks.md` にゲート合格条件 3 点が明記されている
- [ ] ゲート判定結果（合格 / 不合格）が `docs/artifacts/` に記録される
- [ ] 不合格時のフォールバック手順（Opus 4.7 切替 + M-1 一時停止 + W1 成果保持）が `tasks.md` に明記されている

**優先度**: MUST

### FR-3: 各 Wave 冒頭で PM 級ファイル編集計画を K5 一括宣言し、承認 1 回で残りを自律消化する (MUST)

**説明**: R-2 で採用した K5 一括宣言方式（各 Wave の着手前に編集予定の PM 級ファイル一覧を一括宣言し、承認 1 回を得たうえで Wave 内の残り編集を自律的に進める方式）を M-1 の PM 級ファイル編集（`.claude/rules/` / `CLAUDE.md` / `docs/adr/` 等）にそのまま継承する。

**受け入れ条件**:
- [ ] `tasks.md` の各 Wave 冒頭セクションに「本 Wave で編集する PM 級ファイル一覧」フィールドが存在する
- [ ] 各 Wave の一括宣言と承認取得の記録が Wave 実施中は `SESSION_STATE.md` に残り、Milestone retro（VCS 管理下）に永続化される
- [ ] Wave 内で当初宣言に含まれない新規 PM 級ファイルへの編集が必要になった場合、追加宣言 + 承認を経ている

**優先度**: MUST

### FR-4: 条項トリアージを 4 軸と決定木で定義し、条項単位で判定する (MUST)

**説明**: 4 軸（軸 1 帰属 / 軸 2 形式 / 軸 3 可逆性 / 軸 4 根拠）表と決定木を ADR-0011 決定 1 の内容のまま採用する。判定はファイル単位ではなく条項単位で行う。軸 3 は第 0 原則の可逆性・復旧コストを継承し、軸 4 は `trust-model.md` §カウント単位の「検出イベント単位」定義をそのまま流用する（新機構を作らない）。

**受け入れ条件**:
- [ ] `design.md` に 4 軸表と決定木が転記されている
- [ ] 決定木の分岐（軸 1 = ユーザー意思 → 保全 veto / 軸 3 = 不可逆ガード → 保全 veto / SSOT 退避 / 圧縮 / 削減）が ADR-0011 決定 1 と一致している
- [ ] 軸 4 の判定基準が `trust-model.md` §カウント単位の検出イベント単位定義を参照し、独自定義を新設していない

**優先度**: MUST

### FR-5: 不変制約 4 対象をトリアージ対象外とする (MUST)

**説明**: 体験シミュ発火点 3 点（根拠: `fable-l3-protocol.md` §5.4 ガード 2）/ PM 級承認ゲート・PM 級パス列挙（根拠: `permission-levels.md` §PM 級パスの事前計算原則）/ gabriel probe 起動条件（根拠: ADR-0007 / FR-W-C-3）/ 統治への自己書込禁止（根拠: ADR-0005 FR-9.1）の 4 対象は、4 軸評価を経ずにトリアージ対象外とする。gabriel 指摘 2 を反映し、根拠は対象ごとに分離記述する（`fable-l3-protocol.md` §5.4 ガード 2 を 4 対象すべての根拠として引用してはならない）。

**受け入れ条件**:
- [ ] `design.md` の不変制約表が 4 行で構成され、各行に個別の根拠文書・節が記載されている
- [ ] `fable-l3-protocol.md` §5.4 ガード 2 が体験シミュ発火点以外の根拠として引用されていない（grep 実測で確認）
- [ ] W1 トリアージ表において不変制約 4 対象に該当する条項が「対象外」として明示され、4 軸評価を経ていない

**優先度**: MUST

### FR-6: トリアージの判定は提案に留め、適用は PM 級一括承認を経る (MUST)

**説明**: トリアージ表全体を 1 承認イベントとする K5 パターンを W1 末に適用する。判定結果の適用（圧縮・削減の実行）は W2 で行い、W1 では実行しない。

**受け入れ条件**:
- [ ] W1 完了時点でトリアージ表が PM 級承認済みとして記録されている
- [ ] W1 中にトリアージ対象条項の圧縮・削減が実行されていない（適用は W2 の Task として分離されている）
- [ ] トリアージ表の承認がトリアージ表全体で 1 回の承認イベント（K5 一括宣言方式）として記録されている

**優先度**: MUST

### FR-7: 圧縮・削減した条項を全件、削減台帳に「原文 / 判定軸 / 移動先」付きで記録する (MUST)

**説明**: 3 層安全網の第 2 層。W2 のトリアージ適用時に、圧縮または削減と判定された条項全件について原文・適用された判定軸・移動先（SSOT 退避先または `docs/artifacts/` 退避先）を記録する。

**受け入れ条件**:
- [ ] 削減台帳（単純表 / `docs/artifacts/` 配下）が存在し、圧縮・削減判定を受けた条項が全件記載されている
- [ ] 削減台帳の各行が「原文」「判定軸」「移動先」の 3 列を持つ
- [ ] W1 トリアージ表の圧縮・削減判定件数と削減台帳の記載件数が一致する（件数突合で確認）

**優先度**: MUST

### FR-8: W0 で定量ベースラインを測定し、未実施の状態で削減に進まない (MUST)

**説明**: 3 層安全網の第 1 層。測定項目 6 件（pytest 全数 / Green State 件数 / `tdd-patterns.log` FAIL→PASS 率 / gabriel verdict 分布 / PM 級ダイアログ発火数 / `CLAUDE.md` + `rules` トークン数）を W0 で測定する。各 Wave 末でも再測定する。第 1 層が未実施の状態で W2（規律本体の適用）に進んではならない（比較対象が永久に失われる＝不可逆であるため）。

**受け入れ条件**:
- [ ] W0 完了時点で測定項目 6 件すべての値が `docs/artifacts/` に記録されている
- [ ] W1・W2・W3・W4 の各 Wave 末に同一 6 項目の再測定値が記録されている
- [ ] W0 のベースライン測定が完了する前に W2（規律本体の適用）Task が着手されていないことが `tasks.md` の順序制約で確認できる

**優先度**: MUST

### FR-9: 削減台帳の条項を trust-model.md の検出イベント対象に含め、不在起因の検出イベントが閾値 2 回に達した条項を復活候補として提案する (MUST)

**説明**: 3 層安全網の第 3 層。既存機構（`trust-model.md` の「同一パターン 2 回以上 → ルール候補提案」）への接続のみで実現し、新規実装は行わない。

**受け入れ条件**:
- [ ] `trust-model.md` または削減台帳の運用記述に、削減済み条項の不在起因の検出イベントを既存の閾値判定ロジックに含める旨が明記されている
- [ ] 新規のカウント機構・新規ログファイルが追加されていない（既存 `tdd-patterns.log` / `trust-model.md` の機構のみで完結する）
- [ ] 復活候補提案の手続きが `/retro` の既存 Step 2.5 フローに接続されている

**優先度**: MUST

### FR-10: `.claude/rules/model-roster.md` を新設し、モデル名束縛の単一 SSOT とする (MUST)

**説明**: 保持する 4 項目＝現行ロスター表（層 L1 / L1.5 / L2 / L3 / HGA × モデル ID × 有効日）/ 層内閾値 / 挙動デルタ / 単価・envelope。`model-delegation-prompting.md` と `hga-summoning.md` の該当部をトリアージ後に吸収する。

**受け入れ条件**:
- [ ] `.claude/rules/model-roster.md` が新規作成され、4 項目（ロスター表 / 層内閾値 / 挙動デルタ / 単価・envelope）のセクションを持つ
- [ ] `model-delegation-prompting.md` および `hga-summoning.md` のモデル固有記述が `model-roster.md` へ移動し、元ファイルには参照のみが残る
- [ ] 既存ファイルからの移動内容について、移動元・移動先の対応が削減台帳に記録される

**優先度**: MUST

### FR-11: CLAUDE.md には層の定義のみを残し、モデル名を書かない (MUST)

**説明**: 層の定義（L1＝判断 / L1.5＝司令塔 / L2＝実行 / L3＝採点）は `CLAUDE.md` §作業体制に残す。モデルが変わっても層は変わらないため、層の定義とモデル名の束縛を分離する。

**受け入れ条件**:
- [ ] `CLAUDE.md` §作業体制からモデル ID の直書き（`opus` / `sonnet` / `haiku` / `fable` / `claude-*-数字` パターン）が、例外登録対象（FR-12）を除きすべて除去されている
- [ ] `CLAUDE.md` に `model-roster.md` への導線（1-2 行の参照）が存在する
- [ ] `verify_model_reference`（FR-12）の検査で `CLAUDE.md` の drift がゼロと判定される

**優先度**: MUST

### FR-12: モデル名直書きの検査は検出後 3 分岐で処理する (MUST)

**説明**: 例外はファイルパスではなく記述の性質で定義する（gabriel 指摘 1 の反映）。3 分岐＝「層への割当」（例:「L1＝Opus」）→ SSOT 退避 / 「設計上の性質の説明」（例:「MAGI 3 者は同一モデルの別ペルソナ」）→ 圧縮（モデル名を落として意味が通るなら落とす）/ 「時点記録」（`docs/artifacts/` / `docs/adr/` / 実測ログ）→ 例外登録。

**受け入れ条件**:
- [ ] `verify_model_reference` の実装（新規スクリプトまたは既存 `verify_reference_resolution.py` へのパターン追加）が、検出結果を「層への割当」「設計上の性質の説明」「時点記録」の 3 分岐で判定するロジックを持つ
- [ ] `.claude/agents/gabriel.md` 本文の「同一モデル（Opus）の別ペルソナ」等、frontmatter 外のプローズ内モデル名記述が 3 分岐の「設計上の性質の説明」に正しく分類され、圧縮対象として検出されることを誤例として実測している
- [ ] 例外登録がファイルパス単位ではなく記述の性質単位で行われていることが実装コードまたはテストで確認できる

**優先度**: MUST

### FR-13: update-model skill を薄い順序表として作成し、判断ロジックを持たせない (MUST)

**説明**: 実体は検証スクリプト側に置き、陳腐化は pytest で検出する。手順＝upstream 一次資料確認 → `model-roster.md` 更新 → `verify_model_reference` 実行 → agents frontmatter 更新 → ベースライン再測定 → 配布カタログへの追記。

**受け入れ条件**:
- [ ] `.claude/skills/update-model/SKILL.md` が手順（上記 6 ステップ相当）のみを記述し、判断ロジック（条件分岐・閾値判定コード）を含まない
- [ ] 各ステップが既存スクリプト・コマンドの呼び出しとして記述されている（新規判断ロジックが skill 内に実装されていない）
- [ ] skill の手順と対応スクリプト（`verify_model_reference` 等）の整合を検証する pytest が存在する

**優先度**: MUST

### FR-14: model-roster.md は ADR-0001 を supersede しない (MUST)

**説明**: `update-model` skill に「ADR-0001 の『Opus は hooks/subagents で使用しない』制約を破らないことの確認」を含める。

**受け入れ条件**:
- [ ] `model-roster.md` の冒頭または関連節に ADR-0001 との関係（supersede しない・直交する）が明記されている
- [ ] `update-model` skill の手順内に「ADR-0001 の Opus 不使用制約を破らないことの確認」ステップが存在する
- [ ] `model-roster.md` のロスター表が hooks / subagents の層（L2 / L3）に Opus を割り当てていないことが確認できる

**優先度**: MUST

### FR-15: HGA 召喚ゲートを事前条件から事後条件へ転換する (MUST)

**説明**: 無条件召喚 2 条件（spec/design 初期 / 不可逆な設計コミット）は事後条件の判定材料へ格下げし、新ゲートは MAGI `AC-W-C-7`（gabriel critical refute 2 回目＝再 MAGI 上限到達）への接続として定義する。新規判定機構は作らない。M-1 実施中は旧ゲートを適用し、新ゲートは M-1 完了（W4 retro）後に発効する。

**受け入れ条件**:
- [ ] `hga-summoning.md` の召喚ゲート節が ADR-0009 追補の内容（事後条件 3 点＝`AC-W-C-7` 到達 / 第 0 原則 3 変数での不可逆判定 + L1 確信不足 / ユーザー明示指示）に改訂されている
- [ ] `hga-summoning.md` に「M-1 実施中は旧ゲート適用、新ゲートは M-1 完了（W4 retro）後に発効」の移行期規定が明記されている
- [ ] 新ゲートが既存の MAGI `AC-W-C-7` 判定機構への接続のみで実装され、新規の召喚判定コードが追加されていない

**優先度**: MUST

### FR-16: W3 の skills / agents には規律文書向けの 4 軸とは別の判定軸を定義してから progressive disclosure 化を適用する (MUST)

**説明**: 判定式（100 行超 かつ `references/` へ未分離）による実測は **9 件**（2026-07-26 / W3-M1-T1 再実測 / design §7.2 の 2026-07-25 実測と完全一致）。W3 の対象は**行数降順の上位 4 件**（`full-review` 951 行 / `goal-driven` 419 行 / `init-harness` 288 行 / `spec-template` 268 行）。残り 5 件（`adr-template` 234 / `autonomous` 185 / `ship` 180 / `building` 136 / `retro` 135）は対象として認識したうえで **M-1 スコープ外**とし、W3 完了記録に明記する（silent な打ち切りにしない）。

**スコープ再評価（2026-07-26 / W3-M1-T1 / PM 級承認済）**: 当初の「4 件打ち切り」は「分割の効果が未知数」という前提で置かれたが、その前提は変化した。**件数は拡大しない**。根拠: upstream 一次資料（context7 / `code.claude.com/docs/en/context-window`）で **SKILL.md の body は常時ロードされない**（起動時に載るのは description のみ / `disable-model-invocation: true` の skill は description すら載らない）ことを確認したため、分割は常時ロード量に寄与せず、対象拡大の費用対効果は当初想定より**低い**と判定した。

> **未確認（断定しない）**: W0-M1-T5 記録の「body 約 5,000 tok」という 3 レベル構造の目安値は、2026-07-26 の狙い撃ち 2 クエリでは upstream に確認できなかった。本 FR のスコープ判断の根拠には**用いていない**。

**受け入れ条件**:
- [ ] `design.md` または W3 の Task 定義に、skills / agents 向けの判定軸（規律文書向け 4 軸とは別の軸）が明記されている
- [ ] 100 行超かつ `references/` へ未分離の skill が実測で列挙され（**9 件**）、うち優先対象 **4 件**（`full-review` を含む行数降順の上位 4 件）が `tasks.md` に明記されている
- [ ] progressive disclosure 化の実施後、対象 skill の主要な発火条件・振る舞いに変更がないことが動作確認で検証されている

**優先度**: MUST

### FR-17: W3 の完了条件に ADR-0010 I-1〜I-6 適合確認（R-3 の発火）を含める (MUST)

**説明**: skills / agents の構造改善（progressive disclosure 化・統廃合検討）が ADR-0010 の配布統治規律（I-1〜I-6）に適合していることを確認する。

**受け入れ条件**:
- [ ] W3 の Task 定義（`tasks.md`）に ADR-0010 I-1〜I-6 適合確認のチェック項目が含まれている
- [ ] 適合確認の実施記録（各 I に対する適合 / 不適合の判定）が W3 完了記録に残される
- [ ] 不適合が発見された場合、PM 級判断に差し戻す手続きが明記されている

**優先度**: MUST

### FR-18: 配布を 2 経路に分割する (MUST)

**説明**: skills / agents の変更＝ADR-0010 の plugin チャネル（`lam-harness` の version bump）/ 規律の変更＝カタログ（正本 `docs/artifacts/m-1-distribution-catalog.md`、配布コピーは LAM リポジトリ外）。カタログの列 7 種＝変更項目 / 種別 / LAM 固有度 / 必要 harness バージョン / 前提モデル世代 / 依存 / 判断軸。

**受け入れ条件**:
- [ ] W3 の成果物（skills / agents の変更）が `lam-harness` plugin の version bump として配布されている（`docs/artifacts/` カタログには含まれない）
- [ ] `docs/artifacts/m-1-distribution-catalog.md` が規律変更を対象に作成され、7 列（変更項目 / 種別 / LAM 固有度 / 必要 harness バージョン / 前提モデル世代 / 依存 / 判断軸）を持つ
- [ ] カタログの配布コピーが LAM リポジトリ外（2026-07-21 前例と同一の書き出し先）に存在する

**優先度**: MUST

### FR-19: W0 で Opus 5 / Fable 5 の公式スペック・単価を upstream 一次資料で裏取りする (MUST)

**説明**: `upstream-first.md` 準拠。現時点は未確認であり断定しない。

**受け入れ条件**:
- [ ] W0 完了時点で Opus 5 の公式スペック（context window / 価格等）が一次資料（Anthropic 公式ドキュメント URL または context7 取得結果）とともに記録されている
- [ ] Fable 5 の公式スペック・単価が同様に一次資料で確認され、未確認の場合は「未確認」と明記されている
- [ ] 裏取り結果が `model-roster.md` の単価・envelope 節に反映されている

**優先度**: MUST

### FR-20: W0 で ADR-0001 の記述と実ファイルの突合を行い drift の有無を確定する (MUST)

**説明**: ADR-0001 §改訂履歴の記述（「12 agents で `command|sonnet|haiku|fable` 混在指定」）と実ファイル `.claude/agents/*.md` を突合する。**2026-07-25 の grep 実測（W0-M1-T6）は sonnet 9 / haiku 3 / 不明 0（全 12 ファイル）であり、`command` / `fable` はいずれも未検出**。したがって drift は ADR-0001 側にあり、突合結果に応じて ADR 側注記か実ファイル修正かを判断する。

> **訂正記録（2026-07-25 / W0-M1-T6 / PM 級 / W0 K5 宣言済）**: 本説明文の初版は「sonnet 8 / haiku 3 / 不明 1」と記載していたが、これは誤りだった。`grep -n "^model:" .claude/agents/*.md` による全 12 ファイルの実測値は **sonnet 9 / haiku 3 / 不明 0** であり、design §4.4 の実測と一致する。実測記録は `docs/artifacts/m-1-baseline-w0.md` §W0-M1-T6 を参照。
>
> **追加の構造的誤り（2026-07-25 実測で判明）**: 本 FR が引用する ADR-0001 の「`command|sonnet|haiku|fable` 混在指定」という表現自体が**レイヤーを取り違えている**。ADR-0001 自身の「決定」§表（L44）が `command` を「**hooks 第 1 層の handler type**（model 指定なし）」と定義しており、`.claude/agents/*.md` の `model:` 値ではない。`fable` は実ファイル・hook のいずれにも存在しない。したがって ADR-0001 の drift は「値の古さ」ではなく「**agents の model 値と hook の handler type の混同**」であり、突合結果の扱い（受け入れ条件）を判断する際はこの点を踏まえること。

**受け入れ条件**:
- [ ] W0 完了時点で `.claude/agents/*.md` 全 12 ファイルの `model:` frontmatter 値が grep 実測で一覧化されている
- [ ] ADR-0001 §改訂履歴の記述と実測値の一致・不一致が明記されている
- [ ] 不一致が確認された場合、ADR-0001 への時点注記追加または実ファイル修正のいずれかが PM 級判断で決定され記録されている

**優先度**: MUST

### FR-21: R-2 W2/W3 の予定条項をトリアージ入力に含め、再スコープ結果を R-2 tasks.md の Task 完了記録に反映する (MUST)

**説明**: R-2 W2/W3 が規律への**追加**を予定している条項は次の 3 件で閉じる（`docs/specs/r-2-consolidation/tasks.md` 実測 / 2026-07-25）: (1) `terminology.md` §4.5 の 3 小節（W2-R2-T9 / T12 / T13）、(2) `planning-quality-guideline.md` §1.5「暗黙前提明示化リスト」（W2-R2-T13b）、(3) `model-delegation-prompting.md` の scratchpad 書込禁止節（W3-R2-T24）。この 3 件を W1 トリアージ表の入力に含め、判定結果（実施 / 圧縮形で実施 / スキップ）を `docs/specs/r-2-consolidation/tasks.md` の Task 完了記録に反映する。W3-R2-T23（`evaluation-kpi.md` §7 削除）は条項の削除でありトリアージ入力に含めない。R-2 の Definition of Done 自体は変更しない（Non-Goals 4）。

**受け入れ条件**:
- [ ] W1 トリアージ表に R-2 W2/W3 の予定条項（各 Task の追加箇所）が入力として含まれている
- [ ] R-2 の該当 Task について「実施 / 圧縮形で実施 / スキップ」のいずれかの判定が W2 完了時点で記録されている
- [ ] `docs/specs/r-2-consolidation/tasks.md` の該当 Task 完了記録に判定結果が反映されている

**優先度**: MUST

---

## 4. 非機能要求 (NFR)

### NFR-1: 発火点・承認ゲート・宣言イベントの数を減らさない (MUST NOT)

**説明**: 減らすのは記述箇所であり発火点は不変（ADR-0011 要求事項 5 / CASPAR「発火点の数と記述箇所の数を分離する」）。

**受け入れ条件**:
- [ ] W0 と W4 のベースライン測定で PM 級ダイアログ発火数（FR-8 の測定項目の一つ）に構造的な減少がないことが確認されている
- [ ] 体験シミュ発火点 3 点（PLANNING 承認直前 / `/ship` Phase 3.5 / AUDITING 監査レポート提出直前）が W2 の圧縮後も `phase-rules.md` または `fable-l3-protocol.md` のいずれかに明記され続けている
- [ ] gabriel probe 起動条件（AoT 適用時 MUST）が圧縮後も変更されていない

**優先度**: MUST NOT

### NFR-2: 安全網 3 層と検査機構は既存機構への接続のみで構成し、新規の帳簿を作らない (MUST NOT)

**説明**: `fable-l3-protocol.md` §3 帳簿単一原則（成果物判定の帳簿は Green State 1 冊のみ）に従う。

**受け入れ条件**:
- [ ] 削減台帳（第 2 層）が Green State とは独立した「成果物判定」の新帳簿として運用されていない（記録表であり判定帳簿ではないことが明記されている）
- [ ] 第 1 層・第 3 層の実装が既存ファイル（pytest 結果 / `tdd-patterns.log` / `gabriel-metrics.log` / `trust-model.md`）への接続のみで完結し、新規ログファイルが追加されていない
- [ ] Green State の 5 条件（G1〜G5）に安全網由来の新条件が追加されていない

**優先度**: MUST NOT

### NFR-3: Zero-Regression Policy を維持する (MUST)

**説明**: pytest regression 0 / Green State 悪化なし。W0 ベースラインの起点は R-2 W1 末実績（2026-07-25 / commit `2ac4e91` / 1043 passed + 14 skipped）とし、W0 で再実測して確定する。

**受け入れ条件**:
- [ ] 各 Wave 末で pytest 実行結果が W0 ベースライン以上の PASS 数を維持している
- [ ] W0 実測で確定したベースライン数値が `docs/artifacts/` のベースライン記録に明記されている
- [ ] M-1 期間中に regression（既存 PASS テストの FAIL 化）が発生していない

**優先度**: MUST

### NFR-4: M-1 で新規追加する Python コードは Python 3.8 互換を維持する (MUST)

**説明**: `pyproject.toml` `requires-python = ">=3.8"` に従う。対象は `verify_model_reference` 系の新規コード。

**受け入れ条件**:
- [ ] `verify_model_reference`（新規スクリプトの場合）に `from __future__ import annotations` が付与されている
- [ ] `match` / `except*` / dict merge (`|`) 等の 3.10+ 構文が使用されていない
- [ ] `str.removesuffix` 等の 3.9+ 専用 API が使用されていない（使用する場合は `endswith` + slice で代替する）

**優先度**: MUST

### NFR-5: M-1 で新規追加する Python コードは subprocess-encoding-convention.md に準拠する (MUST)

**説明**: `encoding="utf-8", errors="replace"` を既定形とする。

**受け入れ条件**:
- [ ] `verify_model_reference`（新規スクリプトの場合）の `subprocess.run` 呼び出しが `encoding="utf-8", errors="replace"` を指定している
- [ ] `.claude/tests/rules/test_subprocess_encoding_convention.py` の検証コマンドが新規コードに対しても PASS する

**優先度**: MUST

### NFR-6: 削減量を目標値として掲げない (MUST NOT)

**説明**: Wave 完了判定・DoD のいずれにも削減率・削減行数の下限を置かない。

**受け入れ条件**:
- [ ] `tasks.md` / 本 requirements.md のいずれにも削減率・削減行数の下限を完了条件とする記述が存在しない
- [ ] Milestone retro の評価項目に削減量の数値目標達成率が含まれていない
- [ ] W4 のベースライン再測定結果は報告されるが、それ自体が DoD 判定条件として使われていない（NFR-3 の regression ゼロとは独立に扱う）

**優先度**: MUST NOT

---

## 5. 成功基準 (Definition of Done)

M-1 Milestone COMPLETE の判定条件:

- [ ] **DoD-1**: 全 5 Wave（W0〜W4）が Green State（NFR-3 準拠）で完了している（Opus 5 安定性ゲートを合格、またはフォールバック手順を経て通過している）
- [ ] **DoD-2**: 条項トリアージ表が PM 級一括承認済みで、削減台帳（design §6.3 の **8 列**）が **W2 で実ファイルに変更を加えた全条項**を網羅している（判定 5 パターン = 圧縮 / 削減 / SSOT 退避 / **運用移管** / 保全（ロード条件変更のみ））
- [ ] **DoD-3**: `model-roster.md` 新設 + `verify_model_reference` 機構（3 分岐処理）+ `update-model` skill（薄い順序表）の 3 点が成立し、pytest で検証可能な状態になっている
- [ ] **DoD-4**: W0 と W4 のベースライン測定を比較し、pytest regression ゼロ、かつ NFR-1 が定める発火点・承認ゲート・宣言イベントの数が不変であることを確認している。
  - **判定に用いる項目**（2026-07-25 確定 / W0-M1-T2・T3）: **項目 1（pytest regression）と項目 5（PM 級ダイアログ発火数）**。
  - **項目 3（`tdd-patterns.log` FAIL→PASS 率）は判定に用いない**: 計器（XML 鮮度判定）を W0-M1-T2 で修正したため、W0 側の履歴は較正前の盲目の計器で採られている。差分を取ると「条項トリアージの効果」と「計器変更」が分離不能になる。**W0 側は算定せず、W4 側のみ実測値として報告する**（`docs/artifacts/m-1-baseline-w0.md` §W0-M1-T2「確定」参照）。
- [ ] **DoD-5**: 配布 2 経路（skills/agents＝`lam-harness` plugin の version bump / 規律＝`docs/artifacts/m-1-distribution-catalog.md`）が完了し、ADR-0010 I-1〜I-6 適合確認（R-3）が記録されている
- [ ] **DoD-6**: Milestone retro が実施され、R-2 W2/W3 の再スコープ結果（実施 / 圧縮形で実施 / スキップ）が `docs/specs/r-2-consolidation/tasks.md` に反映されている
- [ ] **DoD-7**（2026-07-25 追加 / HGA #17 改訂 4）: **出口宣言 3 点**が Milestone retro に明記されている — **(a) 一回性宣言**（M-1 は一回性であり consolidation 系 Milestone のジャンルをここで閉じる）/ **(b) 決定木の転用**（以後は「新規条項の誕生ゲート」として適用し、定期棚卸しとしては再実行しない = 流入制御）/ **(c) no-net-growth**（新条項 1 追加 = 既存から同等量の削減。**計測対象は「規範ストック総量」**であり起動時ロード量ではない）。
  - **趣旨**: M-1 の中核である 4 軸 + 決定木は「ストックへの一回性の処理」であり、**新規条項が生まれるフローに触れていない**。フローが不変なら数 Milestone 後に同じ棚卸しが必要になり、それは定義上「次の階層」である（HGA #17 crux 1）。本 DoD は M-1 を出口として成立させるための条件であり、**削減量の数値目標ではない**（NFR-6 に抵触しない）。
  - **対象外**: 「LAM の機構が Claude Code の公式仕様と重複・矛盾・陳腐化していないか」を問う **upstream 仕様突合は別ジャンル**であり、本宣言の対象に含まない（M-1 の 4 軸では upstream drift を原理的に捕捉できないため / tasks.md W4-M1-T5 §出口宣言 3 点 の注記参照）。

---

## 6. トレーサビリティ

ADR-0011 決定 5 件・ADR-0011 §実装計画の Wave 骨子 5 件（W0〜W4）+ Opus 5 安定性ゲート 1 件・gabriel 指摘 2 件・追補 2 件・合議録の未解決事項 3 件（計 18 項目）について、対応する FR / Non-Goals / Red 区分を以下に示す（WBS 100% Rule 準拠）。

| ID | 内容（要約） | 対応 FR / 区分 |
|:--:|:-------------|:----------------|
| D1 | 決定 1: 条項トリアージ（4 軸 + 決定木 + 不変制約） | FR-4, FR-5, FR-6 |
| D2 | 決定 2: `model-roster.md` 単一 SSOT 化 + 直書き禁止機構 | FR-10, FR-11, FR-12, FR-13, FR-14 |
| D3 | 決定 3: 3 層の安全網（第 1 層＝削減着手の前提条件） | FR-7, FR-8, FR-9 |
| D4 | 決定 4: HGA 召喚ゲート 事前条件→事後条件転換（ADR-0009 追補） | FR-15, Non-Goals 5 |
| D5 | 決定 5: 配布 2 経路分割（ADR-0010 との整合） | FR-18 |
| W0 | Wave 骨子 W0: 準備（ベースライン測定 / 台帳の器 / upstream 裏取り / ADR-0001 突合） | FR-1, FR-7, FR-8, FR-19, FR-20 |
| W1 | Wave 骨子 W1: トリアージ（veto 先行スクリーニング / 残り精査 / R-2 予定条項を含める / PM 級一括承認） | FR-1, FR-4, FR-5, FR-6, FR-21 |
| WG | Wave 骨子 ゲート: Opus 5 安定性ゲート（W1→W2） | FR-2 |
| W2 | Wave 骨子 W2: 規律本体の適用（SSOT 退避 / 圧縮削減実行 / `verify_model_reference` / HGA ゲート改訂 / R-2 再スコープ実行） | FR-10, FR-12, FR-15, FR-21 |
| W3 | Wave 骨子 W3: skills / agents の構造改善（progressive disclosure 化 / agents 統廃合検討 / ADR-0010 適合確認） | FR-16, FR-17 |
| W4 | Wave 骨子 W4: 検証・確定（ベースライン再測定 / `update-model` skill / 配布 / Milestone retro） | FR-8, FR-13, FR-18, DoD-6 |
| G1 | gabriel 指摘 1: A3 直書き禁止機構の例外リスト不完全（frontmatter 外のプローズ記述） | FR-12 |
| G2 | gabriel 指摘 2: A1 不変制約 #1 の根拠が過大（§5.4 ガード 2 の拡大引用） | FR-5 |
| S1 | 追補 1: ADR-0001（モデルルーティング戦略）との関係 — supersede しない / 直交 / drift 実例 | FR-14, FR-20, Non-Goals 3 |
| S2 | 追補 2: ADR-0010（グローバル資産統治）との関係 — 配布 2 経路への修正 | FR-17, FR-18 |
| U1 | 未解決 1: トリアージの条項粒度の定義 | §7 Red-1 |
| U2 | 未解決 2: skills / agents の判定軸（規律文書向け 4 軸とは別） | FR-16, §7 Red-2 |
| U3 | 未解決 3: `quality-auditor` と `code-reviewer` の守備範囲重複 | §7 Red-3 |

**検証**: 18 項目（D1〜D5 の 5 件 / W0〜W4 の 5 件 + WG 1 件 / G1〜G2 の 2 件 / S1〜S2 の 2 件 / U1〜U3 の 3 件）のすべてについて、対応する FR または Non-Goals または §7 Red のいずれかに紐づくことを確認した。孤児・漏れはゼロである。

---

## 7. 未解決質問 (Red)

ADR-0011 および MAGI 合議録の骨格・内容は変更せず、以下は `design.md` / `tasks.md` の後続工程で確定すべき事項として記録する。**本節の全項目は `tasks.md` 承認（＝PLANNING 完了）までに解決し、Red を残したまま BUILDING に進まない**（`planning-quality-guideline.md` §6 準拠）。

1. トリアージの**条項粒度**の定義（見出し単位 / 箇条書き 1 項単位 / 文単位）— W1 の規模見積りに直結（合議録 未解決 1 / design で確定）
2. skills / agents の progressive disclosure 判定軸の具体（合議録 未解決 2 / FR-16 の実体 / design で確定）
3. `quality-auditor`（328 行）と `code-reviewer`（97 行）の守備範囲重複の扱い — 呼び出し実績データが存在せず判断材料不足（合議録 未解決 3 / W3 で扱う）
4. `verify_model_reference` の実装形態（新規 script か既存 `verify_reference_resolution.py` へのパターン追加か / ADR-0011 §影響を受けるコンポーネントが「実装時判断」としている）
5. 削減台帳の配置パスと形式（`docs/artifacts/` 配下の単純表で開始する方針のみ決定済）
6. FR-2 安定性ゲートの合格判定の具体（観測期間・母数・「異常なし」の閾値）
7. R-2 W2/W3 の再スコープ判定（実施 / 圧縮形 / スキップ）は W1 トリアージ出力に依存するため PLANNING 時点で確定しない

---

## 8. 参照

- `docs/adr/0011-clause-triage-and-model-generation-governance.md`（ADR-0011 / 本 requirements の起源・正本）
- `docs/artifacts/2026-07-25-magi-m1-opus5-migration.md`（MAGI 合議録 / AoT 6 Atom + gabriel probe）
- `docs/adr/0001-model-routing-strategy.md`（ADR-0001 / FR-14, FR-20, Non-Goals 3 の根拠）
- `docs/adr/0005-thin-harness-autonomous-governance.md`（ADR-0005 FR-9.1 / FR-5 不変制約「統治への自己書込禁止」の根拠）
- `docs/adr/0007-magi-v2-gabriel-integration.md`（ADR-0007 / FR-5 不変制約の根拠）
- `docs/adr/0009-hga-fable-summoning.md`（ADR-0009 / FR-15 の追補対象）
- `docs/adr/0010-global-claude-assets-governance.md`（ADR-0010 / FR-17, FR-18 の根拠）
- `.claude/rules/auto-generated/trust-model.md`（FR-4, FR-9 の参照先）
- `.claude/rules/permission-levels.md`（FR-5 不変制約の根拠）
- `.claude/rules/fable-l3-protocol.md`（FR-5, NFR-1 の根拠）
- `.claude/rules/hga-summoning.md`（FR-15, FR-10 の改訂 / 吸収対象）
- `.claude/rules/model-delegation-prompting.md`（FR-10 の吸収対象）
- `.claude/rules/upstream-first.md`（FR-19 の根拠）
- `.claude/rules/planning-quality-guideline.md`（品質基準）
- `.claude/rules/terminology.md`（用語階層）
- `docs/specs/r-2-consolidation/tasks.md`（FR-21 の反映先）
- `docs/specs/r-2-consolidation/requirements.md`（書式の型・参考元）

---

## 9. 変更履歴

| 日付 | 変更者 | 内容 |
|:-----|:-------|:-----|
| 2026-07-25 | L2 (Sonnet) | 初版起草（ADR-0011 決定 1〜5・Wave 骨子・gabriel 指摘 2 件・追補 2 件の requirements 形式への写像。FR-1〜FR-21 / NFR-1〜NFR-6 / DoD-1〜DoD-6 / トレーサビリティ / 未解決質問 7 件） |
| 2026-07-25 | L1 (検収) | 4 点修正: FR-21 の R-2 予定条項を `tasks.md` 実測に基づく閉集合 3 件に確定し「等」を除去（Requirements Smells §1 逃げ道カテゴリ）/ §6 トレーサビリティの項目数を 17 → 18 に訂正（安定性ゲート WG が表に含まれるため）/ NFR-3 に W0 ベースライン起点の実測値（`2ac4e91` / 1043 passed + 14 skipped）を明記 / §8 参照に ADR-0005 を追加。FR-15 の事後条件 3 点は ADR-0009 追補（2026-07-25 Accepted）との一致を実測確認済 |
| 2026-07-25 | L1 直 | **W0-M1-T6 実測に基づく FR-20 の訂正**（PM 級 / W0 K5 宣言済）: 説明文の「sonnet 8 / haiku 3 / 不明 1」を実測値 **sonnet 9 / haiku 3 / 不明 0** に訂正。あわせて **ADR-0001 の記述がレイヤーを取り違えている**ことを注記（`command` は ADR-0001 自身の「決定」§表が定義する **hooks 第 1 層の handler type** であり `.claude/agents/*.md` の `model:` 値ではない / `fable` は実ファイル・hook のいずれにも不在）。したがって当該 drift は「値の古さ」ではなく「**agents の model 値と hook の handler type の混同**」である |
| 2026-07-25 | L1 直 | **HGA #17（W0-M1-T8）判定 `revise` の反映**（ユーザー承認済）: **DoD-7 を新設**（出口宣言 3 点 = 一回性 / 決定木を新規条項の誕生ゲートへ転用＝流入制御 / no-net-growth。計測対象は「規範ストック総量」であり起動時ロード量ではない。**upstream 仕様突合は別ジャンルとして対象外**）。**DoD-2 を更新**（削減台帳 3 列 → design §6.3 の 8 列 / 判定 5 パターン = 圧縮・削減・SSOT退避・**運用移管**・保全（ロード条件変更のみ））。**DoD-4 を更新**（判定に用いるのは項目 1 と項目 5。**項目 3 は計器較正前後の非可比性により判定に用いない** = W0 側は算定せず W4 側のみ実測値として報告）。DoD 総数 6 → 7 |
