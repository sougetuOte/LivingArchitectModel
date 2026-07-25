# ADR-0011: 条項トリアージによる規律の峻別とモデル世代交代の構造的予防（M-1）

## メタ情報

| 項目 | 内容 |
|------|------|
| ステータス | **Accepted**（2026-07-25） |
| 日付 | 2026-07-25 |
| 意思決定者 | sougetuOte（最終承認 / 2026-07-25）/ Living Architect（起草 / Opus 5）/ gabriel（adversarial 検証） |
| 関連 ADR | [ADR-0001](./0001-model-routing-strategy.md)（モデルルーティング / **supersede しない・直交**）, [ADR-0007](./0007-magi-v2-gabriel-integration.md)（gabriel 起動条件）, [ADR-0008](./0008-approval-gate-redesign.md)（承認ゲート）, [ADR-0009](./0009-hga-fable-summoning.md)（HGA / **本 ADR と同時に追補**）, [ADR-0010](./0010-global-claude-assets-governance.md)（配布チャネル I-1/I-6） |
| 関連資産 | `docs/artifacts/2026-07-25-magi-m1-opus5-migration.md`（MAGI 合議録 = 本 ADR の根拠）, `docs/specs/m-1-opus5-migration/`（起票予定）, `docs/specs/r-2-consolidation/tasks.md`（統合対象） |

---

## コンテキスト

### 背景

2026-07-25、Anthropic が **Claude Opus 5** をリリースし、同日 **"The new rules of context engineering for Claude 5 models"** を公開した。後者は Claude Code の system prompt を **80% 以上削除しても coding evaluation に有意な低下がなかった**という自社実測を根拠に、6 つのパラダイム転換を提示している（Rules→Judgement / Examples→Design Interfaces / Put upfront→Progressive Disclosure / Repeat→Simple tool descriptions / CLAUDE.md memory→Auto-memory / Simple specs→Rich references）。

一方 LAM は**憲法型ハーネス**として意図的に規律を積み上げてきた。実測（2026-07-25 / Sonnet 調査 tool_uses 33）:

| 領域 | ファイル数 | 総行数 |
|------|:---------:|:------:|
| `CLAUDE.md` | 1 | 269 |
| `.claude/rules/` | 16 | 2,176 |
| `.claude/skills/` | 15 | 3,656 |
| `.claude/agents/` | 12 | 2,081 |
| **合計** | **44** | **8,182** |

うち `.claude/rules/` の「禁止」39 件の **59%（23 件）が `fable-l3-protocol.md`（12）と `phase-rules.md`（11）の 2 ファイルに集中**しており、さらに **F0-F4 実行プロトコルと 60 秒実況が両ファイルにほぼ同内容で二重記述**されている。Anthropic が名指しした最大の害（"several conflicting messages in a single request"）に該当する構造が LAM 内に実在する。

### 問題

1. Anthropic 指針を LAM にそのまま適用すべきか判断する**写像層が存在しない**。LAM の規律には「モデルの誤りを防ぐ防御」と「ユーザーの統治意思の記録」が混在しており、前者だけが Anthropic の削減対象である
2. 規律を削減した場合、**劣化を検出する手段がない**。Green State は Critical/Warning の件数であり「規律が欠落したこと」を測らない
3. モデル固有記述が全域に散在しており、**世代交代のたびに 8,182 行の見直しが再発する**構造になっている
4. 改修中の Milestone **R-2** の残 Wave（W2/W3）が、規律に条項を**追加する**方向の作業を含んでおり、本 ADR の方向と衝突しうる
5. 変更内容を他プロジェクト（Kage-Shiki / Mossarium / etm-diary 等）へ伝える経路が未整理

### 制約条件

- **ユーザー既決事項**（2026-07-25 / 変更不可の前提）:
  1. Opus 5 へ **L1 完全切替**（4.7 廃止）
  2. Fable HGA は「**Opus 5 でも詰まった時のみ**」に格下げ
  3. **R-2 W1 完了後に M-1 着手**（W2/W3 に入る前に統合再スコープ）
  4. 予防策は「**SSOT ファイル新設 + `update-model` skill 作成**」
- 権限等級: **PM 級**（`docs/adr/` 新規作成 + `.claude/rules/` 変更 + `CLAUDE.md` 変更）
- **Hierarchy of Truth**: User Intent が最上位。統治意思を記録した条項を「モデルが賢くなったから」を理由に削除することはこれに反する
- **upstream-first**: Opus 5 / Fable 5 の単価・性能は一次資料未確認（readme.txt 記載は伝聞）。断定は W0 の裏取り後
- **Opus 5 はリリースから 24 時間未満**。実挙動の実測がゼロ

### 要求事項

1. 峻別基準が **LAM 内在的に正当化できる**こと（Anthropic 指針の無批判な外挿でないこと）
2. 削減が劣化を招いた場合に**検出・復活できる**こと
3. **次のモデル世代交代で同規模の見直しが再発しない**こと
4. 既存 ADR（0001 / 0007 / 0009 / 0010）と矛盾しないこと
5. 発火点・承認ゲート・宣言イベントの**数**を減らさないこと

---

## 検討した選択肢

### Option A: Anthropic 6 原則を直接チェックリスト化して一括適用

**概要**: 6 原則を判定項目とし、全 44 ファイルを一括で見直す。

**メリット**: 実装が単純。Anthropic の実測を最大限活用できる。着手が早い。

**デメリット**:
- 6 原則は Anthropic の製品文脈（**汎用コーディングエージェント**が任意ユーザーに対して最悪ケースを避ける）に紐付いており、LAM の統治文脈への写像層がない
- Anthropic の実測は **coding evaluation** であり、LAM の価値（複数セッションにまたがる統治と一貫性）を測っていない。外挿の根拠が提示されていない
- 「Rules→Judgement」を `permission-levels.md` §PM 級パスの事前計算原則（「実行時に第 0 原則で PM 級を降格することを**禁止する**」）に適用すると、**禁止条項自体を judgement で外す**という自己言及的な不正が生じる

### Option B: 現状維持（Opus 5 切替のみ / 規律は触らない）

**概要**: モデルを Opus 5 に切り替えるだけで、規律は一切変更しない。

**メリット**: リスクゼロ。Opus 5 の実挙動を十分に観測してから判断できる。

**デメリット**:
- 二重記述（F0-F4 / 60 秒実況）による conflicting messages が残り続ける。これは Opus 5 の judgement を阻害する側の問題であり、モデルが賢くなるほど**害が相対的に大きくなる**
- モデル固有記述の散在が解消されず、次の世代交代でも同じ規模の見直しが発生する（要求事項 3 の不達）
- 課題そのものが先送りされるだけで、判断コストは減らない

### Option C: 条項トリアージ + モデルロスター SSOT + 3 層安全網 — **採用**

**概要**: LAM 自身の原則（第 0 原則 / Hierarchy of Truth / trust-model の検出イベント）から導出した 4 軸の判定基準を作り、**条項単位**で保全 / 圧縮 / 削減 / SSOT 退避に振り分ける。モデル固有記述は単一 SSOT に集約し直書きを機構で禁じる。削減には 3 層の安全網を敷く。

**メリット**:
- 峻別基準が LAM 内在的に導出されるため、Anthropic の実測が LAM に外挿できるかという未解決問題を**回避できる**（要求事項 1）
- 削減量が目標ではなく結果になる。Anthropic の 80% も結果であって目標ではない
- 安全網が既存機構（pytest / Green State / trust-model）への接続のみで構成され、新規機構を作らない（`fable-l3-protocol.md` §3 帳簿単一原則と整合）
- SSOT 化により世代交代コストが「1 ファイル + grep 検証」に畳まれる（要求事項 3）

**デメリット**:
- 分析フェーズ（トリアージ）に 1 Wave を要する。着手から効果までのリードタイムが長い
- 4 軸の判定が主観に流れる余地がある（特に軸 1「ユーザー意思 vs モデル誤り予防」の境界）
- Wave 数が増え、途中で力尽きた場合「規律が半分書き換わった状態」が残る

### Option D: 全面書き直し（LAM v6 として作り直す）

**概要**: 8,182 行を白紙に戻し、Claude 5 世代前提で最小構成から書き直す。

**メリット**: 最もクリーンな結果が得られる。過去のしがらみを断てる。

**デメリット**:
- **実測発火由来の規律が全損する**。`rule-001`（4 検出イベント）、`trust-model` の閾値設計、インシデント履歴（Opus 4.8 malformed / Fable→Opus 実装ギャップ）から生まれた条項は、書き直しでは復元できない
- 承認ゲートの再設計を伴い、ADR-0008 の決定を無効化する
- 検証不能。「前と同じ品質か」を比較する基準が消える

---

## 3 Agents Analysis

> **本決定の多角的検証は MAGI 合議（AoT 適用モード / Atom 6 個 / gabriel adversarial probe）が担った。**
> 全文: `docs/artifacts/2026-07-25-magi-m1-opus5-migration.md`。以下はその要約である
> （議論の詳細を本 ADR に再掲しないのは、本 ADR が採用する Progressive Disclosure の実践でもある）。

### [MELCHIOR / Affirmative] 推進者の視点

- 2,445 行（`CLAUDE.md` + `rules/`）が毎セッション頭に載る。削減は**毎セッション複利で効く**
- 推敲された Anthropic の system prompt ですら 80% 削減できた。**推敲の甘い LAM 側にこそ余地が大きい**
- 二重記述の解消は節約ではなく**品質改善**（conflicting messages の除去）
- LAM は既に「意図への圧縮」の前例を持つ。`rule-001` の `B-\d+` → `[A-Z]-\d+` 汎化（2026-07-06）は列挙的対処を抽象パターンに畳んだ実例であり、`trust-model.md` §N 回目発火時の恒久解検討がこれを制度化済み

### [BALTHASAR / Critical] 批判者の視点

- **エビデンスのドメイン差**: Anthropic の実測は coding eval。LAM の価値を測っていない
- **カテゴリエラー**: LAM の PM 級承認ゲートは「モデルが賢いかどうか」と無関係に、**ユーザーが承認したいから**存在する。Anthropic が削った「worst-case 回避の防御」と同一視できない
- **メタ規範の自己書き換え**: 「Rules→Judgement」を `permission-levels.md` の降格禁止条項に適用すると自己言及的に不正
- **儀式は L3 契約下**: 60 秒実況・自己監査 14 項目は Fable-Alembic L3 受け入れの一部。`fable-l3-protocol.md` §3 が「削減は正義ではない / 半分だけの移植は移植しないより悪い」と**明示的に警告済み**
- **タイミング**: Opus 5 リリース 24 時間未満。LAM 自身のインシデント履歴（Opus 4.8 malformed → 4.7 据置き）が示す通り危険
- **劣化検出の不在**: 規律の欠落は数週間のドリフトとして現れ、その時点で原因特定は困難

### [CASPAR / Mediator] 調停者の視点

- **軸 1（帰属）に veto 権を与える**ことでカテゴリエラーとメタ規範の自己書き換えを同時に解決する。ユーザー意思の記録は他軸を問わず保全
- **エビデンスのドメイン差は「LAM 側で実測する」ことで回避**。ただし実測には削減前のベースラインが必須 → **W0 を削減着手の前提条件**とする（BALTHASAR の主張を全面採用）
- **儀式の扱いは「発火点の数」と「記述箇所の数」を分離**することで解決する。減らすのは記述箇所であり、発火点は不変
- **タイミングは W1→W2 のゲートで解決**。分析（W0/W1）は適用を伴わず実挙動に依存しない。むしろ**分析期間そのものが Opus 5 の実測期間になる**
- **削減 / 圧縮の 2 値化は Anthropic 指針の誤読**。同社の実例自体が「列挙の削除」ではなく「意図への圧縮」だった

### [gabriel] 独立検証者の視点（adversarial probe / 独立コンテキスト）

**verdict: refuted / severity: warning / confidence: 0.72 / recommended_action: proceed**

CASPAR 結論を破棄せず、以下 2 点の指摘を併記して進むと判定（`AC-W-C-6`）:

1. **モデル名直書き禁止の例外リストが不完全**: `.claude/agents/gabriel.md` の本文に「同一モデル（Opus）の別ペルソナ」という frontmatter 外のリテラルが存在する。パスベースの例外リストでは検査機構が false positive を出す
2. **不変制約の根拠が過大**: `fable-l3-protocol.md` §5.4 ガード 2 は体験シミュ発火点に限定された警句であり、PM 級ゲート・gabriel 起動条件まで同条項を根拠にするのは拡大引用

gabriel は R-2 の DoD（NFR-3）/ ADR-0009 移行期注記 / `AC-W-C-7` との整合を個別に確認し「矛盾なし」と判定した。

---

## 決定

**採用: Option C（条項トリアージ + モデルロスター SSOT + 3 層安全網）**

M-1 は「削減の Milestone」ではなく、**「峻別基準と予防機構を作る Milestone」**である。削減量は結果であって目標ではない。

### 決定 1: 条項トリアージ（Clause Triage）

ファイル単位ではなく**条項単位**で 4 軸を評価し、決定木で振り分ける。

| 軸 | 問い | 保全側 | 削減側 |
|----|------|--------|--------|
| **軸 1（帰属）** | 誰の判断を記録しているか | ユーザー / プロジェクトの意思（統治・リスク許容度・方法論の選択） | モデルの誤り予防（worst-case 回避） |
| **軸 2（形式）** | 意図か、列挙か | 意図（principle / 既に圧縮済） | 列挙（enumerated do/don't） |
| **軸 3（可逆性）** | 破ったとき巻き戻せるか | 不可逆（承認ゲート / spec freeze / 破壊操作 / 外部公開） | 可逆（書式 / 命名 / 手順 / 表現） |
| **軸 4（根拠）** | 実測発火があるか | 実測インシデント由来（検出イベント ≥ 1） | 予防的に書かれた（発火実績ゼロ） |

軸 3 は**第 0 原則**の可逆性・復旧コストを継承する。軸 4 は `trust-model.md` §カウント単位の「検出イベント単位」定義を**そのまま流用**する（新機構を作らない）。

**決定木**:

```
軸1 = ユーザー意思 / 統治      → 保全（veto / 他軸を問わない）
軸3 = 不可逆ガード             → 保全（veto / 他軸を問わない）
上記いずれにも該当しない場合:
  ├ 帰属がモデル固有の事実      → SSOT 退避（決定 2 のロスターへ / 削除ではなく移動）
  ├ 軸4 = 実測発火あり
  │    ├ 軸2 = 列挙            → 圧縮（意図 1 行に畳む / 根拠は docs/artifacts へ退避）
  │    └ 軸2 = 意図            → 保全
  └ 軸4 = 発火ゼロ
       ├ 軸2 = 列挙            → 削減
       └ 軸2 = 意図            → 保全（低優先 / 次回 retro で再評価）
```

**不変制約（軸に関わらずトリアージ対象外 / MUST NOT）** — gabriel 指摘 2 を反映し**根拠を対象ごとに分離記述**する:

| 対象 | 根拠 |
|------|------|
| 体験シミュ発火点（3 点） | `fable-l3-protocol.md` §5.4 ガード 2（「発火点数の一時的減少は禁止」） |
| PM 級承認ゲート・PM 級パス列挙 | `permission-levels.md` §PM 級パスの事前計算原則 |
| gabriel probe 起動条件 | ADR-0007 / FR-W-C-3（AoT 適用時 MUST / 軽量モード MUST NOT） |
| 統治への自己書込禁止 | ADR-0005 FR-9.1 |

**手続き**: トリアージの**判定は提案**に留め、**適用は PM 級承認**を経る（R-2 W1 で実績のある K5 一括宣言パターンを流用 = トリアージ表全体を 1 承認イベント）。圧縮・削減した条項は**全件台帳に残す**。

### 決定 2: `model-roster.md` を単一 SSOT とし、モデル名直書きを機構で禁じる

`.claude/rules/model-roster.md`（新設）が持つもの:

1. 現行ロスター表（層 L1 / L1.5 / L2 / L3 / HGA × モデル ID × 有効日）
2. 層内閾値（そのモデルにおける「L1 直作業の上限」等）
3. 挙動デルタ（`model-delegation-prompting.md` をトリアージ後に吸収）
4. 単価・envelope（`hga-summoning.md` の該当部を決定 3 のトリアージ後に吸収）

**`CLAUDE.md` に残すもの**: **層の定義**（L1 = 判断 / L1.5 = 司令塔 / L2 = 実行 / L3 = 採点）。モデルが変わっても層は変わらない。

**ADR-0001 との関係**: 本決定は ADR-0001 を **supersede しない**。ADR-0001 が決めたのは**ルーティングの構造**（どの層で誰が判定するか / Opus をメインセッション専用にする）であり、`model-roster.md` が持つのは**モデル名の束縛**である。両者は直交する。`update-model` skill には **ADR-0001 の「Opus は hooks/subagents で使用しない」制約を破らないことの確認**を含める。

**直書き禁止の機構化**（gabriel 指摘 1 を反映）: 検査は「モデル名の出現をすべて禁じる」のではなく、**検出結果を 3 分岐で処理する**。例外は**ファイルパスではなく「記述の性質」**で定義する。

| 検出された記述の性質 | 処理 |
|---------------------|------|
| **層への割当**（「L1 = Opus」等） | SSOT へ退避 |
| **設計上の性質の説明**（「MAGI 3 者は同一モデルの別ペルソナ」） | **圧縮** — モデル名を落として意味が通るなら落とす（世代交代で陳腐化するため） |
| **時点記録**（`docs/artifacts/` / `docs/adr/` / 実測ログ） | 例外登録（変更しない） |

`update-model` skill は**薄い順序表**とし、判断ロジックを持たせない（実体は検証スクリプト側に置き、pytest で陳腐化を検出する）。

### 決定 3: 3 層の安全網。第 1 層は削減着手の前提条件

| 層 | 内容 | 実施時期 | 新規実装 |
|----|------|---------|---------|
| **第 1 層: 定量ベースライン** | pytest 全数 / Green State 件数 / `tdd-patterns.log` FAIL→PASS 率 / gabriel verdict 分布 / PM 級ダイアログ発火数 / `CLAUDE.md`+`rules` トークン数 | **削減前（W0）と各 Wave 末** | 不要 |
| **第 2 層: 削減台帳** | 圧縮・削減した全条項を「原文 / 判定軸 / 移動先」付きで記録 | トリアージ適用時 | 不要 |
| **第 3 層: 復活経路** | 台帳の条項を `trust-model.md` の**検出イベント対象に含める**。不在起因の検出イベントが閾値（2 回）に達したら復活候補として自動提案 | 削減後（恒久） | 不要 |

**第 1 層が未実施の状態で削減に進んではならない**（比較対象が永久に失われるため / 不可逆）。

### 決定 4: HGA 召喚ゲートを事前条件から事後条件へ転換する（ADR-0009 追補）

詳細は ADR-0009 の追補セクションに記載する。本 ADR では方針のみ決定する:

- **廃止**: 無条件召喚 2 条件（spec/design 初期 / 不可逆な設計コミット）→ 事後条件の判定材料に格下げ
- **新ゲート**: MAGI `AC-W-C-7`（gabriel critical refute 2 回目 = 再 MAGI 上限到達）への**接続**として定義し、新規判定機構を作らない
- **移行期**: **M-1 実施中は旧ゲートを適用**する。新ゲートは M-1 完了（W4 retro）後に発効（新ゲートの検証を新ゲート自身に委ねる自己言及を回避するため）

### 決定 5: 配布は 2 経路に分割する（ADR-0010 との整合）

| 配布対象 | 経路 | 根拠 |
|---------|------|------|
| **skills / agents の変更** | ADR-0010 の **plugin チャネル**（`lam-harness` の version bump） | ADR-0010 I-6 / I-1 |
| **規律の変更**（`CLAUDE.md` / `rules` / `model-roster.md` パターン） | **カタログ**（メタデータ列付き / 各 PJ が取捨選択） | plugin チャネルに載らない性質のため |

カタログの列: 変更項目 / 種別 / **LAM 固有度**（高 = 移植不可 / 中 = 要調整 / 低 = そのまま可）/ **必要 harness バージョン** / **前提モデル世代** / 依存 / 判断軸。正本は `docs/artifacts/m-1-distribution-catalog.md`、配布用コピーを LAM リポジトリ外に書き出す（2026-07-21 の前例を踏襲）。

### 却下理由

- **Option A（6 原則の直接適用）**: 写像層がなく軸 1 のカテゴリエラーを起こす。かつ `permission-levels.md` の降格禁止条項に対して自己言及的に不正
- **Option B（現状維持）**: 二重記述による conflicting messages が残る。モデルが賢くなるほど害が相対的に大きくなる。要求事項 3（世代交代コストの構造的削減）が不達
- **Option D（全面書き直し）**: 実測発火由来の規律が全損する。検証の基準が消える

---

## 影響

### ポジティブな影響

- 峻別基準が LAM 内在的に導出され、「Anthropic の coding eval を統治ハーネスに外挿してよいか」という未解決問題を回避できる
- モデル世代交代のコストが「8,182 行の見直し」から「1 ファイル + grep 検証 + 指標再測定」に畳まれる
- 二重記述（F0-F4 / 60 秒実況）の解消により conflicting messages が減り、Opus 5 の judgement が阻害されにくくなる
- 削減の失敗が既存機構（`trust-model` 検出イベント）で自動的に復活候補として提案される

### ネガティブな影響

- 分析フェーズ（W0/W1）に着手から効果までのリードタイムが生じる
  （緩和策: 分析期間そのものが Opus 5 の実挙動の実測期間になる。W1→W2 の安定性ゲートで活用する）
- 4 軸の判定に主観が入る余地がある
  （緩和策: veto 2 軸を先行適用して精査対象を絞る。判定は提案に留め PM 級承認を経る）
- R-2 の完了が M-1 W1 の完了に依存する
  （緩和策: これはユーザー決定「W2/W3 に入る前に統合再スコープ」の必然的帰結であり、新規に導入する結合ではない。R-2 の DoD 自体は変更しない）
- Wave 途中で中断した場合「規律が半分書き換わった状態」が残る
  （緩和策: 規律本体の適用を W2 の 1 Wave に閉じる。W3 は構造改善であり規律の一貫性を壊さない）

### 影響を受けるコンポーネント

| コンポーネント | 影響内容 |
|--------------|---------|
| `CLAUDE.md` | トリアージ対象。§Python Invocation Convention（46 行）/ §References / §作業体制の委譲表が候補 |
| `.claude/rules/`（16 ファイル） | トリアージ対象。特に `fable-l3-protocol.md` / `phase-rules.md`（二重記述） |
| `.claude/rules/model-roster.md` | **新設** |
| `.claude/rules/hga-summoning.md` | 召喚ゲート改訂 + 単価・envelope の SSOT 退避 |
| `.claude/rules/model-delegation-prompting.md` | 挙動デルタの SSOT 吸収（トリアージ後） |
| `.claude/skills/`（15 ファイル） | W3 で progressive disclosure 化（`full-review` 951 行ほか） |
| `.claude/agents/`（12 ファイル） | W3 で統廃合検討 + `model:` frontmatter の `update-model` 管理下移行 |
| `.claude/scripts/verify_model_reference.py` | **新設**（既存 `verify_reference_resolution.py` へのパターン追加でも可 / 実装時判断） |
| `docs/specs/r-2-consolidation/tasks.md` | W2/W3 の予定条項がトリアージ入力になる。判定結果を Task 完了記録に反映 |
| ADR-0009 | **追補**（Superseded にしない） |

---

## 実装計画

M-1 の詳細は `docs/specs/m-1-opus5-migration/`（requirements → design → tasks）に起票する。本 ADR では Wave 骨子のみ決定する。

### 前提: R-2 W1 の完走

- [ ] R-2 W1-T4 / T5 / T6 / T7 / T8 完了 + W1 末ゲート（pytest 980+ PASS / regression 0）

### W0: 準備

- [ ] 決定 3 第 1 層のベースライン測定
- [ ] 削減台帳の器を作成（単純表で開始 / R-2 W3-T23 の template 化は前倒ししない）
- [ ] **upstream 一次資料の裏取り**: Opus 5 / Fable 5 の公式スペック・単価（`upstream-first.md` 準拠）
- [ ] ADR-0001 §改訂履歴の「`fable` 混在指定」記述と実ファイル（`.claude/agents/*.md`）の突合

### W1: トリアージ（判定のみ / 適用しない）

- [ ] veto 先行スクリーニング（軸 1 / 軸 3 該当条項を保全確定）
- [ ] 残りを精査（`fable-l3-protocol.md` 234 + `phase-rules.md` 245 + `CLAUDE.md` 269 ≈ 750 行が実質対象）
- [ ] **R-2 W2/W3 の予定条項**をトリアージ表に含める
- [ ] トリアージ表を PM 級一括承認（K5 パターン）

### ゲート: Opus 5 安定性確認（W1 → W2）

- [ ] malformed / tool 呼び出し異常の発生ゼロ
- [ ] pytest regression ゼロ（W0 ベースライン比）
- [ ] gabriel verdict 分布に異常なし

> 不合格時: Opus 4.7 へフォールバックし M-1 を一時停止。峻別基準（W1 の分析成果）は保持されるため損失は Wave 1 本分に留まる。

### W2: 規律本体の適用

- [ ] `model-roster.md` 新設 + SSOT 退避
- [ ] 圧縮・削減の実行 + 台帳記録
- [ ] `verify_model_reference` 機構（3 分岐処理）
- [ ] HGA 召喚ゲート改訂（決定 4）
- [ ] R-2 W2/W3 の再スコープ実行（実施 / 圧縮形で実施 / スキップ）

### W3: skills / agents の構造改善

- [ ] progressive disclosure 化（`full-review` 951 行ほか / 100 行超かつ外部参照ゼロの 4 skill を優先）
- [ ] agents 統廃合検討（`quality-auditor` 328 行 と `code-reviewer` 97 行 の守備範囲重複）
- [ ] **ADR-0010 I-1〜I-6 適合確認**（R-3 の発火）

### W4: 検証・確定

- [ ] 決定 3 第 1 層のベースライン再測定
- [ ] `update-model` skill 作成
- [ ] 配布（決定 5 の 2 経路）
- [ ] Milestone retro

---

## 検証方法

### この決定が正しかったかを検証する方法

1. **定量**: W0 と W4 のベースライン比較。pytest regression 0 / Green State 悪化なし / `CLAUDE.md`+`rules` トークン数の減少
2. **定性**: 削減台帳の各条項について、M-1 完了後 90 日以内に「不在起因の検出イベント」が発生したか（決定 3 第 3 層）
3. **構造**: 次のモデル世代交代時に、実際に「`model-roster.md` + agents frontmatter のみの変更」で完了するか（要求事項 3 の真の検証はここでしか行えない）

### 見直しのトリガー条件

- **T-1**: 決定 3 第 3 層により、削減した条項の復活候補が**閾値 2 回に達した**場合 → 当該条項の判定を再評価し、4 軸の妥当性を retro 議題化
- **T-2**: Opus 5 安定性ゲート**不合格**の場合 → M-1 を一時停止し、Opus 4.7 前提での再設計を検討
- **T-3**: Claude Code のメジャー更新時 → ADR-0010 R-1 と併せて、本 ADR の前提（Progressive Disclosure の機構 / skills 解決順）を再裏取り
- **T-4**: Fable の後継世代リリース時 → 決定 4 の召喚ゲートを再評価（ADR-0009 §争点 E の「条件変化」に該当するか判断）

---

## 参考資料

- `docs/artifacts/2026-07-25-magi-m1-opus5-migration.md`（MAGI 合議録 / AoT 6 Atom + gabriel probe / **本 ADR の根拠**）
- Anthropic "The new rules of context engineering for Claude 5 models"（2026-07-25 / claude.com blog / Thariq @trq212）
- LAM 現状実測（2026-07-25 / Sonnet 調査 / `.claude/` 44 ファイル 8,182 行）
- [ADR-0001](./0001-model-routing-strategy.md) — ルーティング構造（本 ADR と直交）
- [ADR-0007](./0007-magi-v2-gabriel-integration.md) — gabriel 起動条件（不変制約の根拠）
- [ADR-0009](./0009-hga-fable-summoning.md) — HGA 型（本 ADR と同時に追補）
- [ADR-0010](./0010-global-claude-assets-governance.md) — 配布チャネル I-1 / I-6 / R-3
- `.claude/rules/permission-levels.md` §PM 級パスの事前計算原則（不変制約の根拠）
- `.claude/rules/fable-l3-protocol.md` §3 帳簿単一原則 / §5.4 ガード 2
- `.claude/rules/auto-generated/trust-model.md` §カウント単位（軸 4 の定義元）
