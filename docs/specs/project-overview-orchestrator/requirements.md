# 要件定義書: Project Overview Orchestrator（POO）

- バージョン: 0.5.0
- 作成日: 2026-06-29
- 更新日: 2026-06-29（R5 Final Green 確定修正）
- ステータス: Draft（PM 承認待ち）
- 対応フェーズ: PLANNING（requirements）
- 関連 Milestone: B-5（Wave 10 / 骨子 ⑥）
- 起草者: a-design1（design-architect）
- 関連 ADR: `docs/adr/0006-loop-engineering-vocabulary-and-lam-alignment.md`（Stage 3 位置付け根拠）

---

## §1 Problem Statement

### 背景

LAM プロジェクトは Milestone / Step / Wave / Task の 4 階層で作業を管理し（`.claude/rules/terminology.md` §1）、
`/autonomous`、`/goal-driven`、`/lam-orchestrate`、`/full-review` の各スキルを保有している。
これらは Wave 単位の実装ループ（Stage 2 Loop）として機能するが、いずれも **Wave 内で完結** する設計であり、
複数 Wave・複数 Milestone をまたぐ俯瞰的な把握と推奨の機能は持たない。

その結果、各 Wave 完了後の「次に着手すべき Milestone / Step / Wave は何か」という判断は、
L1 統括（人間）が SESSION_STATE.md / tasks.md / retro を手動で読み合わせて下している。
ADR-0006 は ⑥（骨子 プロジェクト俯瞰オーケストレータ）を **Loop Engineering Stage 3 Orchestrated Teams の典型設計**
および **coordinator 層の常駐化** として位置付けており（ADR-0006 §後続 Milestone への推奨改善方針）、
この手動フローが Loop Engineering Stage 3 の未実装ギャップに相当する。

### ギャップの具体的影響

| 問題 | 現状 | 影響 |
|:-----|:-----|:-----|
| **Milestone 俯瞰の手動化** | SESSION_STATE.md / retro を手動で読み現在地を判断 | 判断コストが L1 統括（人間）に集中する |
| **次着手推奨の欠如** | Wave 完了後の next-step は人間の経験則に依存 | 着手順序の根拠が揮発し、引き継ぎ時に再発見コストが発生する |
| **Milestone SSOT の未統合** | Milestone 情報が SESSION_STATE.md / tasks.md に分散し、単一参照点が存在しない | b4-dashboard の Wave 8 で MilestoneSourceMerger を整備したが、より上位の Registry が未整備のため再利用性が限定的 |
| **既存スキルの起動判断が手動** | 「今は /lam-orchestrate か /autonomous か」をユーザーが毎回判断 | Stage 3 coordinator の不在が手動意思決定を強制している |

本要件定義書は、上記ギャップを解消する **Project Overview Orchestrator（POO）** の要件を定義する。
POO は Stage 3 coordinator として、**Milestone 単位の俯瞰・現在地特定・次着手推奨** を担う。
ただし POO は **推奨（recommendation）専用** であり、自動起動権限を持たない。
ユーザー（L1 統括）の最終承認判断を侵さないことを設計の根幹とする。

---

## §2 Goals / Non-Goals

### Goals

| Goal | 指標 | 達成判定 |
|:-----|:-----|:--------|
| G1: Milestone 現在地の即時特定 | Milestone × Step × Wave × Task の 4 次元で「現在地」を特定できる | POO 実行後に「現在: B-5 / BUILDING Step / Wave 10 / Task N」形式の出力が得られる |
| G2: 次着手推奨の提示 | 「次に着手すべき作業」を理由付きで提示する | 推奨候補を priority 順に提示し、根拠となる FR / AC / retro の参照を明示する |
| G3: 既存スキルの起動 API 契約定義 | `/autonomous` / `/goal-driven` / `/lam-orchestrate` / `/full-review` への呼び出し契約を薄い定義として整備する | 各スキルの呼び出し口（引数・前提条件・期待出力）が spec に記述されている |
| G4: MilestoneRegistry read-only API の整備 | MilestoneSourceMerger（Wave 8）を共通基盤として SSOT 化し、read-only API を定義する | b4-dashboard と POO が同一 Registry を参照できる状態になっている（dashboard 側コードは変更しない）|
| G5: Phase 規律との統合 | POO の推奨は現在の Phase（PLANNING / BUILDING / AUDITING）を考慮する | Phase が BUILDING の状態で PLANNING スキル（lam-orchestrate 等）を推奨しない |
| G6: b4-dashboard との SSOT 共有 | MilestoneRegistry を POO と b4-dashboard の共通参照点として確立する | dashboard.html の Milestone リストと POO の Milestone 認識が同一データを参照する（dashboard 側の変更は対象外）|

### Non-Goals（明示的に Wave 10 で対応しないこと）

- **自動起動権限**: POO は推奨を提示するに留め、スキルを自動的に起動してはならない（MUST NOT）。ユーザーが「承認」を明示してから各スキルを起動する運用を維持する
- **gabriel 統合 / MAGI v2**: gabriel（骨子 ②）との統合は v2 以降の別 ADR で扱う
- **書き戻し系処理**: SESSION_STATE.md / tasks.md への書き戻しは Wave 11 以降。POO は read-only（MUST NOT write）
- **dashboard UI 変更**: b4-dashboard の HTML / CSS / JS は変更対象外
- **既存スキルの内部改修**: `/autonomous` / `/goal-driven` / `/lam-orchestrate` / `/full-review` 各スキルの内部実装は変更しない（MUST NOT modify）
- **動的 Workflow / Agent Teams**: プラットフォームの dynamic workflows は必須依存にしない（MAY として将来候補）
- **MilestoneRegistry への書き込み権限**: Wave 10 では read-only API のみ。書き戻しは Wave 11+ で別途検討

---

## §3 機能要件（RFC 2119）

### FR-W10-1: Milestone 現在地の特定（MUST）

POO は実行時に、LAM プロジェクトの現在地を以下の 4 次元で特定しなければならない（MUST）。

| 次元 | データソース | 取得方法 |
|:-----|:-----------|:--------|
| Milestone | `MilestoneRegistry`（FR-W10-4 参照）| read-only API からの一覧取得 |
| Step | `SESSION_STATE.md` | 「現在の Step」フィールドの読み取り |
| Wave | `SESSION_STATE.md` / `docs/specs/<milestone>/tasks.md` | 進行中 Wave の特定 |
| Task | `docs/specs/<milestone>/tasks.md` | 未完了 Task の特定 |

特定結果は以下の形式で出力しなければならない（MUST）:

```
現在地: Milestone=<名前> / Step=<PLANNING|BUILDING|AUDITING> / Wave=<番号> / Task=<ID>
```

データソースが存在しない次元は `unknown` と表示し、他次元の表示を継続しなければならない（MUST）。
`tasks.md` が存在しない Milestone は Wave / Task 次元を `unknown` として出力を継続しなければならない（MUST）。

> **Phase について**: 現在の Phase は FR-W10-5 のフィルタリング処理で内部参照する（`.claude/current-phase.md` 読み取り）。
> Phase は出力フォーマットの次元としては表示しない。FR-W10-5 参照。

### FR-W10-2: 次着手推奨の提示（MUST）

POO は「次に着手すべき作業」を以下の要件に従い提示しなければならない（MUST）。

**MUST 項目**:
- 推奨候補を最大 3 件、priority 順（1: 最優先）でリストアップする（MUST）
- 各候補に対し、推奨根拠（FR / AC / retro アクション等の参照）を 1 件以上明示する（MUST）
- 現在の Phase に基づいて推奨をフィルタリングする（MUST。FR-W10-5 参照）
- POO は推奨を提示するに留める（MUST）。スキルを自動起動してはならない（MUST NOT）
- 推奨理由が存在しない場合（全タスク完了等）はその旨を出力し、推奨なしを明示する（MUST）
- Phase フィルタリング（FR-W10-5）後の推奨候補が 0 件になった場合、**「推奨なし」を明示出力**し、**どの前提条件が欠如しているか**を状況説明として併記しなければならない（MUST）
- **MUST 5（推奨理由が存在しない / 全タスク完了等）と MUST 6（Phase フィルタ後 0 件）が同時発生した場合、両方の状況説明を統合した単一の「推奨なし」出力を返す（両方の前提条件欠如を併記）**

**SHOULD 項目**:
- 推奨候補の選定に用いたロジック（着手順序のルール等）をユーザーが確認できる形で説明することが望ましい（SHOULD）

### FR-W10-3: 既存スキルへの起動 API 契約定義（MUST）

POO は以下の既存スキルへの呼び出し契約を定義しなければならない（MUST）。
既存スキルの内部実装は変更してはならない（MUST NOT）。

| スキル | 呼び出し前提条件 | 期待出力 |
|:------|:--------------|:--------|
| `/autonomous` | 対象 spec が確定しており BUILDING Phase にある | Green State 達成または PM ハードストップ報告 |
| `/goal-driven` | rubric.md が存在しており BUILDING Phase にある | Green State または grader 判定報告 |
| `/lam-orchestrate` | PLANNING Step にある | design / tasks 成果物の生成 |
| `/full-review` | AUDITING Phase にある | 監査レポート（Critical / Warning / Info 件数）|

契約定義は POO の推奨出力に「このスキルを次に使用してください / 理由: …」として含めるとよい（SHOULD）。

> **注記**: 本表の「呼び出し前提条件」は POO の推奨フィルタリング（FR-W10-5 を介して）として確認する条件であり、**スキル側の起動ガードではない**。スキル側の起動時前提検証は各 SKILL.md の責務として独立する。

### FR-W10-4: MilestoneRegistry read-only API（MUST）

POO は `MilestoneRegistry` read-only API を通じて Milestone 一覧を取得しなければならない（MUST）。

**MUST 項目**:
- `MilestoneRegistry` は Wave 8 で定義した `MilestoneProvider` Protocol を実装しなければならない（MUST）
- `MilestoneRegistry.get_milestones()` は `list[MilestoneInfo]` を返さなければならない（MUST）
- `MilestoneRegistry` は read-only である。SESSION_STATE.md / tasks.md への書き戻しを実装してはならない（MUST NOT）
- `MilestoneProvider` Protocol を実装することで、昇格（extend）または差し替え（replace）のいずれかにより SSOT 共有を実現しなければならない（MUST）。昇格 vs 差し替えの実装選択は Wave 11 設計書で確定する

**エラー耐障害性 MUST 項目**:
- データソースの一部が欠如している場合でも、取得できた Milestone を返し継続しなければならない（MUST）
- 全データソースが欠如している場合は空リストを返し、POO は「Milestone 情報なし」として出力を継続しなければならない（MUST）

### FR-W10-5: Phase 規律との統合（MUST）

POO は現在の Phase（`.claude/current-phase.md`）を読み取り、推奨にフィルタリングを適用しなければならない（MUST）。
この Phase 読み取りは FR-W10-1 の出力次元としてではなく、推奨生成の**内部処理**として用いる。

| 現在の Phase | 推奨対象スキル | 非推奨（SHOULD NOT）|
|:-----------|:------------|:----------------|
| PLANNING | `/lam-orchestrate` | `/autonomous` / `/goal-driven` / `/full-review` |
| BUILDING | `/autonomous` / `/goal-driven` | `/lam-orchestrate` / `/full-review` |
| AUDITING | `/full-review` | `/autonomous` / `/goal-driven` / `/lam-orchestrate` |

以下の 3 点を個別に規定する（いずれも II-C-N2 / 前提 5 由来）:

- **(a) SHOULD NOT 逸脱判定の限定**: SHOULD NOT 対象スキルの推奨候補追加は、**ユーザーが明示的に当該スキルを指定した場合のみ** SHOULD NOT の正当な逸脱として認める。**SHOULD NOT 対象スキルへの逸脱判定はユーザー明示指定の確認に限定し**、POO は当該スキルを推奨候補に含める際にその旨を出力に明示するのみとする（SE 級相当）。
- **(b) Phase 規律の棲み分け**: **Phase 規律の上書き判断はユーザーが別途 `.claude/rules/phase-rules.md` §フェーズ警告テンプレートに従って行う**。POO は Phase 警告の責任を負わない（SE 級相当）。
- **(c) `current-phase.md` 消失時の Phase=unknown と Step 整合**: `current-phase.md` が存在しない場合、POO は Phase 次元を `unknown` として扱う。**この際、AC-W10-1 の 4 次元出力フォーマット（Milestone / Step / Wave / Task）は変更せず、その直後の別行注記として `[注記] Phase=unknown (current-phase.md 不在)` の形式で出力しなければならない（MUST）**。Step 次元は SESSION_STATE.md 由来の値を継続使用する。

**既知 4 スキル（`/autonomous` / `/goal-driven` / `/lam-orchestrate` / `/full-review`）以外**のスキルが推奨候補として現れた場合は「未分類」として提示し、推奨対象外とする（MUST）。

### FR-W10-6: b4-dashboard との SSOT 共有（MUST）

POO と b4-dashboard は `MilestoneRegistry`（FR-W10-4）を共通の SSOT として参照しなければならない（MUST）。

**MUST 項目**:
- b4-dashboard の `DashboardData.milestones` と POO の Milestone 認識が同一 `MilestoneRegistry` を参照する（MUST）
- b4-dashboard の実装（builder.py / build_dashboard.py 等）は変更してはならない（MUST NOT）
- `MilestoneRegistry` の導入後、b4-dashboard が現行の `MilestoneSourceMerger` から `MilestoneRegistry` を参照する経路は、`MilestoneProvider` Protocol の差し替えのみで実現しなければならない（MUST）

---

## §4 非機能要件（RFC 2119）

| ID | 要件 | 基準 |
|:---|:-----|:-----|
| NFR-W10-1 | 実行時間 | POO のメイン処理（現在地特定 + 推奨生成）は **30 秒以内** に完了しなければならない（MUST）。ファイル I/O は逐次的に行い、外部ネットワーク接続に依存してはならない（MUST NOT）|
| NFR-W10-2 | 既存スキル Signature 維持 | `/autonomous` / `/goal-driven` / `/lam-orchestrate` / `/full-review` の呼び出し Signature（フロントマター / 入力引数）は変更してはならない（MUST NOT）|
| NFR-W10-3 | 標準ライブラリ依存 | **POO の実装は Python 3.x 標準ライブラリのみを使用しなければならない（MUST）。ただし NFR-W10-1 (30 秒以内) を標準ライブラリで達成できない実測値がある場合に限り、追加ライブラリを `pyproject.toml` に明示した上で採用してよい（MAY）。それ以外の追加は NFR-W10-3 違反として扱う**。**測定基準**: 「標準ライブラリで達成できない実測値」とは、NFR-W10-1 の試験条件（POO の起動から初回出力完了まで）で標準ライブラリのみ使用した実装が **30 秒** を超えることを意味する。測定対象データ量・試験環境は Wave 11 設計書で具体化する。|
| NFR-W10-4 | 単独実行可能 | **依存資産（`MilestoneRegistry` を含む）が利用不可の場合、当該次元を `unknown` として出力を継続し、AC-W10-1 形式の出力を返さなければならない（MUST）。POO 自体は起動完了し、正常終了する**|
| NFR-W10-5 | read-only 保証 | POO は SESSION_STATE.md / tasks.md / `.claude/current-phase.md` をはじめとする全ファイルを読み取り専用で扱わなければならない（MUST）。ファイルへの書き込みを実行してはならない（MUST NOT）|
| NFR-W10-6 | 推奨件数上限 | POO が 1 回の実行で提示する推奨候補は最大 3 件とする（MUST）。Hick's Law（選択肢数と意思決定時間の対数関係）に基づき、推奨上限を 3 件と定数固定する |

> NFR-W10-1 の 30 秒はダッシュボード生成（NFR-4）と同一基準を採用した。Wave 10 Spike で実測後に見直す。

---

## §5 制約・前提

- **プラットフォーム**: Windows 11 / Git Bash（パスはフォワードスラッシュ）。`CLAUDE.md §Execution Environment` 参照。
- **MilestoneSourceMerger 前提**: Wave 8 で定義した `MilestoneProvider` Protocol および `MilestoneSourceMerger` が BUILDING 済みであることを前提とする。
- **read-only 制約**: POO は全データソースに対して read-only アクセスのみを行う。MUST NOT write は全ファイルに適用する。
- **権限等級**: POO の推奨提示は SE 級。スキルの起動判断・承認はユーザー（L1 統括）の PM 級操作に該当する。POO が PM 級操作を代行してはならない。
- **Phase 規律との整合**: POO は `.claude/rules/phase-rules.md` のフェーズ規律を尊重し、現在の Phase に反する推奨を優先提示してはならない。
- **self-governance の不可侵**: POO は `/autonomous` の FR-9.1 に準拠し、`.claude/rules/` / `docs/adr/` / `.claude/settings*.json` 等の統治ファイルへの書き込みを実行してはならない。
- **前提 1（Wave 8 BUILDING 完了）**: Wave 8（b4-dashboard MilestoneSourceMerger）BUILDING が完了済であること。Wave 8 未完了時は POO の MilestoneRegistry 実装着手（Wave 11 BUILDING）を保留する。**FR-W10-6 の MUST 群（差し替えのみで実現 / dashboard 変更なし）は Wave 8 design.md §10 G4 達成条件 3（`build_dashboard.py` が `MilestoneProvider` 型変数として参照）が満たされていることを前提とする**。
- **前提 2（DQ-N1 解消 / 前提 1 の後続条件）**: Wave 8 BUILDING 完了後（前提 1 達成後）、Wave 8 design.md §11 DQ-N1（循環インポート可能性）の解消が確認されていること。未解消時は POO の MilestoneInfo 参照経路（Wave 11 BUILDING）を保留する。
- **前提 3（SESSION_STATE.md フォーマット安定性）**: SESSION_STATE.md のフォーマット仕様は本 Wave 内では参照しない。実機合わせは Wave 11 BUILDING で行う。
- **前提 5**: `current-phase.md` 消失時の **Phase=unknown 別行注記ルール**（詳細は FR-W10-5 末尾 (c) 参照）。
- **FR-W10-5 の Phase 逸脱推奨はユーザー入力の中継に留まり、POO は Phase 警告の責任を負わない（SE 級相当）**。`.claude/rules/phase-rules.md` §フェーズ警告テンプレートとの棲み分け: Phase 警告は POO の責務外。

---

## §6 用語

本節は POO スコープで使用する用語の定義を示す。
`docs/adr/0006-loop-engineering-vocabulary-and-lam-alignment.md` §Glossary と `.claude/rules/terminology.md` と矛盾する場合は、ADR-0006 および terminology.md が優先する。

| 用語 | 定義 |
|:-----|:-----|
| **POO**（Project Overview Orchestrator）| 本仕様書が定義する Milestone 単位の俯瞰・現在地特定・次着手推奨スキル。略称は POO に固定する |
| **Milestone-level orchestrator** | POO の別称。Wave 単位のオーケストレータ（`/autonomous` 等）と区別する際に使用する |
| **MilestoneRegistry** | `MilestoneProvider` Protocol を実装する共通基盤。Wave 8 の `MilestoneSourceMerger` が昇格（extend）または差し替え（replace）される対象（実装選択は Wave 11 設計書で確定）|
| **現在地** | FR-W10-1 で定義した「Milestone × Step × Wave × Task」の 4 次元の状態 |
| **推奨（recommendation）** | POO が提示する「次に着手すべき作業」の候補。自動起動権限は持たない |
| **coordinator（Stage 3 用語）** | ADR-0006 §Glossary に定義された Loop Engineering 用語。LAM では L1.5 司令塔に相当するが、POO は Milestone 俯瞰に特化した coordinator として機能する |
| **起動 API 契約** | FR-W10-3 で定義した、各既存スキルへの呼び出し前提条件・期待出力の薄い定義 |

---

## §7 受け入れ条件（Definition of Done）

| ID | 条件 | 対応 FR / NFR |
|:---|:-----|:------------|
| AC-W10-1 | POO を実行すると、現在の Milestone / Step / Wave / Task が 4 次元形式で出力される。**`current-phase.md` が存在しない場合、本 4 次元出力の直後に Phase=unknown を別行注記として併記する（詳細は FR-W10-5 末尾 (c) を参照）** | FR-W10-1 |
| AC-W10-2 | データソースが 1 件欠如していても POO が出力を継続し、欠如次元を `unknown` として表示する。`tasks.md` が存在しない Milestone は Wave / Task 次元を `unknown` として出力継続する（データソース欠如に含む）| FR-W10-1 / NFR-W10-4 |
| AC-W10-3 | POO の出力に「次着手推奨」が最大 3 件、priority 順で含まれ、各推奨に根拠参照が明示されている | FR-W10-2 / NFR-W10-6 |
| AC-W10-4 | Phase が BUILDING の状態で POO を実行すると、`/autonomous` または `/goal-driven` が推奨候補に含まれ、`/lam-orchestrate` は推奨に含まれない | FR-W10-5 |
| AC-W10-5 | `MilestoneRegistry.get_milestones()` が `MilestoneProvider` Protocol に従い `list[MilestoneInfo]` を返す。**`MilestoneRegistry` が未起動（Wave 11 実装前）の状態でも AC-W10-1 形式の出力（該当次元は `unknown`）が返ることを確認できる**（検証は Wave 11 BUILDING 開始時）。**Wave 10 内では spec への記述が受け入れ条件である。実機検証は Wave 11 BUILDING 開始時に実測する**| FR-W10-4 / NFR-W10-4 |
| AC-W10-6 | `MilestoneRegistry` にファイル書き込みメソッドが存在しない（read-only 保証） | FR-W10-4 / NFR-W10-5 |
| AC-W10-7 | b4-dashboard を `MilestoneSourceMerger` から `MilestoneRegistry` に切り替えた場合に、既存 dashboard の pytest が全件 PASS を維持する。検証は Wave 11 BUILDING 開始時に実測する。Wave 10 内では spec への記述が受け入れ条件である | FR-W10-6 |
| AC-W10-8 | POO 実行から現在地特定 + 推奨出力完了まで 30 秒以内 | NFR-W10-1 |
| AC-W10-9 | FR-W10-3 で定義した 4 スキルの起動 API 契約（呼び出し前提条件・期待出力）が spec に記述されている（コードとの突合は Wave 11 tasks.md 確定後）| FR-W10-3 |

---

## §8 Out-of-scope（明示的な非スコープ）

以下は本仕様（Wave 10）のスコープ外とし、該当する将来 Wave または ADR で扱う。

| 項目 | 予定先 |
|:-----|:------|
| gabriel 統合（MAGI v2 / 骨子 ②） | 別 ADR / POO v2 |
| 自動起動権限（POO がスキルを自律的に起動する機能） | Wave 11+ で別途 ADR 合議 |
| MilestoneRegistry への書き戻し（SESSION_STATE.md / tasks.md への同期） | Wave 11+ |
| dashboard UI 変更（HTML / CSS / JS の改修） | b4-dashboard 系 Wave（変更予定なし）|
| 既存スキルの内部改修（autonomous / goal-driven / lam-orchestrate / full-review）| 各スキル固有の Wave |
| POO の tasks.md / design.md（Wave 10 内では起票しない） | Wave 11 着手時に Wave 11 PLANNING で確定 |
| **Wave 8 G4 達成条件 3 が満たされていない場合の FR-W10-6 代替経路**（最小限の型注釈追加のみ許可の代替パス詳細）。**根拠**: 「最小限の型注釈追加」は b4-dashboard 既存実装に対する**最小侵襲性**の観点から推奨される代替案であり、Wave 11 PLANNING で実装影響範囲を MAGI 合議で再評価して確定する。本 Wave では確定しない。 | **Wave 11 PLANNING で確定する**。Wave 10 ではこの代替経路の詳細は扱わない |

---

## §9 解決済み質問

本節は Wave 10 起票時の MAGI 合議（AoT 4 Atom）で確定した設計決定を記録する。
起票前の合議結論を要件として再構成したものであり、MAGI 合議ログの引用ではない。

| # | 論点 | 確定内容 |
|:--|:-----|:--------|
| A1 | 機能の主軸 | Milestone 俯瞰主軸 + coordinator は既存スキル呼出機構として束ねる。既存スキル自体は不改修 |
| A2 | 起動 API 契約の粒度 | 上位呼び出し + 起動 API 契約の薄い定義のみ追加。既存スキルの Signature は固定し内部を touch しない |
| A3 | MilestoneRegistry の Wave 10 スコープ | Wave 8 の MilestoneSourceMerger を共通基盤として SSOT 化するが、Wave 10 では read-only API のみ定義する。書き戻しは Wave 11+ で別途扱う |
| A4 | Wave 10 の成果物スコープ | **requirements.md + spike/README.md のみ**（design.md / tasks.md は Wave 11 PLANNING で起草）|
| P1 | FR-W10-4 MUST vs OQ-1 の整合（案 X 採用）| `MilestoneProvider` Protocol を実装することで昇格（extend）または差し替え（replace）のいずれかにより SSOT 共有を実現する（MUST）。昇格 vs 差し替えの実装選択は Wave 11 設計書で確定。OQ-1 は Wave 11 design で解消予定として維持 |
| P2 | FR-W10-3 脱字 + SHOULD 維持（案 A 採用）| 「含めるよい」→「含めるとよい」に訂正。SHOULD は維持（推奨出力への埋め込みは任意）|
| P3 | G1 / FR-W10-1 出力次元を 4 次元に統合（案 X 採用）| Phase 列を出力フォーマットから削除し 4 次元（Milestone × Step × Wave × Task）に統合。Phase は FR-W10-5 のフィルタリング内部処理として参照 |
| R3-C1 | FR-W10-6 MUST 群と Wave 8 G4 達成依存（案 X 採用）| FR-W10-6 本文は変更せず MUST 維持。§5 前提 1 に Wave 8 design.md §10 G4 達成条件 3 依存を注記。§8 に G4 未達時の代替経路（Wave 11 PLANNING 確定）を Out-of-scope エントリとして追記 |
| R3-C2 | FR-W10-5 と §5 権限等級の矛盾（案 A 採用）| FR-W10-5 に SHOULD NOT 逸脱判定の限定とユーザー中継旨の追記。§5 に Phase 逸脱棲み分け（POO の Phase 警告責任外）を追記 |
| R3-W1 | NFR-W10-3 SHOULD + MUST 入れ子混濁 → MUST + MAY（例外条件付き）に統一 | 旧 SHOULD 表現を削除し「MUST 使用 / NFR-W10-1 実測未達時のみ MAY で追加ライブラリ許可」に書き換え |
| R3-W2 | FR-W10-3 cross-spec 整合確認（§11 に記録）| 4 スキル全て整合確認済。FR-W10-3 表への訂正なし |
| R3-W3 | AC-W10-5 と AC-W10-7 の Wave 10 受入条件非対称 | AC-W10-5 に「Wave 10 内では spec 記述が受入条件 / 実機検証は Wave 11 BUILDING」を追記。AC-W10-7 と対称化 |
| R3-W4 | §5 前提 2 が前提 1 への依存を明示していない | 前提 2 に「前提 1 の後続条件」表記と Wave 8 BUILDING 完了後条件を明記 |
| R3-I1 | FR-W10-2 MUST 5/6 重複可能性 | MUST 5/6 同時発生時は統合した単一「推奨なし」出力（両方の前提条件欠如を併記）を追記 |
| R3-I2 | spike §3 V-3 概算根拠が薄い | spike/README.md §3 V-3 に概算根拠の未確定注記と Wave 11 実測検証方針を追記 |
| R3-I3 | §12 v0.2.0 W5 エントリと I-I-5 混在 | v0.2.0 W5 エントリを「spike 側のみ修正 / 本ファイル側修正なし」に訂正。I-I-5 独立エントリとして分離 |
| R3-前提5 | current-phase.md 消失時の Phase=unknown と Step 整合 | FR-W10-5 に Phase=unknown 時の Step 次元継続使用と AC-W10-1 出力での明示併記を追記 |
| R4-W1 | FR-W10-3 表「呼び出し前提条件」の意味の曖昧さ（W-R3-1 / 選択肢 A 採用）| FR-W10-3 表後に「呼び出し前提条件は POO の推奨フィルタリングとして確認する条件であり、スキル側の起動ガードではない」注記を追加。OQ-4 として Wave 11 PLANNING 確定事項（具体的な確認手順）を登録 |
| R4-W2 | 前提 5 のセクション配置（W-R3-2 / 選択肢 A 採用）| §5 に「前提 5: current-phase.md 消失時の Phase=unknown と Step 併記ルール（詳細は FR-W10-5 末尾参照）」を前提 1〜3 と並列で追記。FR-W10-5 末尾段落の詳細仕様は現状維持（§5 はサマリ / FR-W10-5 が詳細）|
| R4-I1 | FR-W10-5 末尾段落の構造（I-R3-1 / 3 箇条分割）| FR-W10-5 末尾段落を (a) SHOULD NOT 逸脱判定の限定 / (b) Phase 規律の棲み分け / (c) current-phase.md 消失時の Phase=unknown と Step 整合 の 3 箇条に分割 |
| R4-I2 | §8 代替経路の「最小限の型注釈追加のみ許可」根拠未検証（I-R3-2）| §8 Out-of-scope の該当エントリに「根拠: 最小侵襲性の観点から推奨 / Wave 11 PLANNING で MAGI 合議により確定 / 本 Wave では確定しない」を追記 |
| R4-I3 | NFR-W10-3 実測値の測定手順未定義（I-R3-3）| NFR-W10-3 に「測定基準: 標準ライブラリのみ実装が 30 秒超 / 測定対象データ量・環境は Wave 11 設計書で具体化」を追記 |
| R4-I4 | §12 v0.3.0「前提 4」の記述ずれ（I-R3-4）| v0.3.0 「前提 4」エントリを「Wave 8 G4 達成条件 3 依存の言語化を II-C-N1 修正に統合（前提 4 単独の新規エントリは作成せず）」に書き換え |
| R5-W1 | FR-W10-5 (c) と AC-W10-1 (4 次元) の矛盾（W-R4-1 / 別行注記案採用）| AC-W10-1 の 4 次元フォーマットは変更せず、Phase=unknown は 4 次元出力の直後の別行注記として出力する（MUST）。§5 前提 5 を 1 行サマリに縮小し、FR-W10-5 (c) が詳細 SSOT。AC-W10-1 注記を追加 |
| R5-I2 | OQ-4 と FR-W10-3 注記の重複読み取り（I-R4-2）| OQ-4 の質問文を「FR-W10-3 注記で論理的条件は確定済み / Wave 11 PLANNING で確定する実装レベルの詳細（Step 判定の参照ファイル経路 / unknown 条件の閾値）に限定」と明確化 |

---

## §10 Open Questions

起票時点での未解決論点。Wave 11 tasks.md 確定前に回答が必要なものを記録する。

| # | 質問 | 想定回答先 |
|:--|:-----|:---------|
| OQ-1 | `MilestoneRegistry` と `MilestoneSourceMerger` の関係: 昇格（extend）か差し替え（replace）か | Wave 11 設計書（Wave 10 Spike で方針確認）|
| OQ-2 | POO の出力形式: Markdown テキスト出力か、構造化データ（JSON 等）か | Wave 11 設計書（Wave 10 Spike で方針確認）|
| OQ-3 | `tasks.md` が存在しない Milestone（PLANNING 段階で tasks.md 未確定の Milestone）の現在地特定方法 | Wave 10 Spike |
| OQ-4 | **FR-W10-3 表の「呼び出し前提条件」は本 spec で「POO 推奨フィルタとしての論理的条件」として確定済み（FR-W10-3 注記参照）**。Wave 11 PLANNING で確定する **実装レベル**の詳細 — 具体的には (1) Step 判定の参照ファイル経路（`SESSION_STATE.md` のどのキー / どの正規表現）と (2) `SESSION_STATE.md` または `tasks.md` の値が `unknown` となる条件（欠損 / パースエラー / 値域外）を区別する閾値 — は Wave 11 PLANNING で確定する | Wave 11 PLANNING |

---

## §11 トレーサビリティ

| FR / NFR | 根拠 |
|:---------|:-----|
| FR-W10-1（現在地特定・4 次元）| ADR-0006 §ギャップ「Stage 2→3 の橋渡しが手動」/ retro-W7 §6 引き継ぎ「骨子 ⑥ 次ステップ」。R2 修正: Phase 列削除により 5 次元→4 次元に統合（P3）|
| FR-W10-2（次着手推奨）| ADR-0006 §推奨改善方針「coordinator 層の常駐化」/ `docs/specs/autonomous-mode/requirements.md` FR-2（権限エンベロープ）の権限境界設計を参考。R2 修正: フィルタ後 0 件時の「推奨なし」明示出力を追加（W6）|
| FR-W10-3（起動 API 契約）| ADR-0006 §Stage 3 Orchestrated Teams / `docs/specs/goal-driven-orchestration/requirements.md` FR-1（スキル呼び出し設計）参考 |
| FR-W10-4（MilestoneRegistry read-only API）| `docs/specs/b4-dashboard/wave8/requirements.md` §2 Non-Goals「MilestoneRegistry 本格化（FC-10）」/ `docs/specs/b4-dashboard/wave8/design.md` §10 Registry 昇格契約。R2 修正: MUST 表現を昇格/差し替え両パス許容に変更（P1）|
| FR-W10-5（Phase 規律統合）| `.claude/rules/phase-rules.md` §BUILDING / §PLANNING / §AUDITING。R2 修正: Phase は FR-W10-1 出力次元から削除し内部処理として明記（P3）。SHOULD NOT 逸脱条件と第 5 スキル扱いを追記（W3）|
| FR-W10-6（b4-dashboard SSOT 共有）| `docs/specs/b4-dashboard/requirements.md` §9 将来候補「/project-vision スキル連携（⑥）」/ FC-10 |
| NFR-W10-2（スキル Signature 維持）| A2 確定事項（既存スキル不改修）/ `docs/specs/autonomous-mode/requirements.md` FR-9.1（自己統治の不可侵）|
| NFR-W10-3（標準ライブラリ依存）| R2 修正: SHOULD 正当逸脱条件（NFR-W10-1 実測値ベース）を追記（W2）|
| NFR-W10-4（単独実行可能 / graceful degradation）| A3 確定事項（write 操作は Wave 11+）。R2 修正: 「依存資産利用不可時に unknown 出力して正常終了」に書き換え（W7）|
| NFR-W10-5（read-only 保証）| A3 確定事項（write 操作は Wave 11+）/ `docs/specs/b4-dashboard/wave8/requirements.md` §2 Non-Goals「双方向同期 MUST NOT」|
| AC-W10-2（データソース欠如継続）| R2 修正: tasks.md 非存在 Milestone の扱いを明記（W1）|
| AC-W10-5（MilestoneRegistry 未起動時動作）| R2 修正: Wave 11 実装前の unknown 出力確認を追記（W7）|
| AC-W10-7（dashboard テスト継続）| R2 修正: 検証タイミング（Wave 11 BUILDING）を明記（W4）|
| §5 制約・前提（Wave 8 / DQ-N1 / SESSION_STATE）| R2 修正: 前提 1〜3 を新規追記（見えない前提 1〜3）|
| FR-W10-3（起動 API 契約 / cross-spec 整合）| **Wave 10 PLANNING で cross-spec 整合確認済（a-design3 / 2026-06-29）**: `/autonomous`（SC-1 Green State 達成 / SC-3 決定的 checker 接地）・`/goal-driven`（FR-1 rubric ファースト / FR-2 独立 grader）・`/lam-orchestrate`（Phase 1-4 設計成果物生成フロー）・`/full-review`（監査レポート Critical/Warning/Info 件数出力）いずれも FR-W10-3 表の期待出力と整合。FR-W10-3 表への訂正なし |
| FR-W10-3（呼び出し前提条件の意味 / R4 修正）| R4 修正（W-R3-1）: 「呼び出し前提条件は POO 推奨フィルタリングとして確認する条件であり、スキル側の起動ガードではない」注記を FR-W10-3 表後に追加。スキル側起動ガードは各 SKILL.md の責務として独立することを明示 |
| FR-W10-5（末尾段落の構造 / R4 修正）| R4 修正（I-R3-1）: 末尾 1 段落を (a)(b)(c) 3 箇条に分割。各論点（SHOULD NOT 逸脱限定 / Phase 規律棲み分け / current-phase.md 消失時整合）が明確化 |
| §5（前提 5 サマリ / R4 修正）| R4 修正（W-R3-2）: §5 に前提 5 エントリを追加。詳細は FR-W10-5 (c) が SSOT として機能し、§5 はサマリ参照 |
| NFR-W10-3（測定基準 / R4 修正）| R4 修正（I-R3-3）: 「標準ライブラリで達成できない実測値」の測定基準を明示。試験条件・データ量・試験環境は Wave 11 設計書で具体化 |
| FR-W10-5 (c)（Phase=unknown 別行注記 / R5 修正）| R5 修正（W-R4-1 (a)）: (c) を「AC-W10-1 の 4 次元フォーマット変更なし / Phase=unknown は別行注記として 4 次元の外に出力する（MUST）」に書き換え |
| AC-W10-1（Phase=unknown 注記 / R5 修正）| R5 修正（W-R4-1 (c)）: AC-W10-1 表の直後に「current-phase.md 不在時は 4 次元出力直後に Phase=unknown 別行注記を追記する（FR-W10-5 末尾 (c) 参照）」注記を追加 |
| §5 前提 5（サマリ縮小 / R5 修正）| R5 修正（W-R4-1 (b) / I-R4-1 同時解消）: 前提 5 を 1 行サマリ「Phase=unknown 別行注記ルール（詳細は FR-W10-5 末尾 (c) 参照）」に縮小。重複詳細を削除し FR-W10-5 (c) が詳細 SSOT として機能 |
| §10 OQ-4（質問文詳細化 / R5 修正）| R5 修正（I-R4-2）: OQ-4 の質問文を「FR-W10-3 注記で論理的条件は確定済み」を明示した上で、Wave 11 確定事項を「実装レベルの詳細（Step 判定の参照ファイル経路 / unknown 条件の閾値）」に限定 |

---

## §12 変更履歴

| バージョン | 日付 | 変更内容 |
|:----------|:-----|:--------|
| 0.1.0 | 2026-06-29 | 初版起稿。MAGI 合議（AoT 4 Atom）確定事項に基づく FR-W10-1〜6 / NFR-W10-1〜6 / AC-W10-1〜9 定義。Wave 10 スコープ（requirements + Spike）確定 |
| 0.2.0 | 2026-06-29 | R2 一括修正（spec-critic R1 指摘 15 件対応）。[P1] FR-W10-4 MUST 表現を昇格/差し替え両パス許容に変更・OQ-1 維持。[P2] FR-W10-3 脱字訂正（「含めるよい」→「含めるとよい」）。[P3] G1・FR-W10-1・§6 現在地を 5 次元→4 次元に変更（Phase 削除・FR-W10-5 内部処理化）。[W1] AC-W10-2 に tasks.md 非存在 Milestone の扱いを明記。[W2] NFR-W10-3 に SHOULD 正当逸脱条件を追記。[W3] FR-W10-5 に SHOULD NOT 逸脱条件と第 5 スキル扱いを追記。[W4] AC-W10-7 に検証タイミング（Wave 11 BUILDING）を明記。[W5] spike/README.md §6 の循環依存を訂正（本ファイル側の修正なし / spike 側のみ）。[W6] FR-W10-2 にフィルタ後 0 件時の「推奨なし」明示出力を追記。[W7] NFR-W10-4 を「unknown 出力して正常終了」に書き換え・AC-W10-5 を補強。[I-I-4] NFR-W10-6 脚注を Hick's Law 正式表現に訂正。[I-I-5] §9 A4 を Wave 10 成果物スコープ（requirements.md + spike/README.md のみ）に訂正。[前提 1〜3] §5 に Wave 8 完了・DQ-N1 解消・SESSION_STATE.md フォーマット安定性の前提を追記 |
| 0.3.0 | 2026-06-29 | R3 一括修正（spec-critic R2 指摘 11 件対応）。[II-C-N1] §5 前提 1 に Wave 8 design.md §10 G4 達成条件 3 依存注記追加 / §8 に Wave 8 G4 未達時代替経路（Wave 11 PLANNING）を Out-of-scope エントリ追加。[II-C-N2] FR-W10-5 に SHOULD NOT 逸脱判定の SE 級限定とユーザー中継追記 / §5 に Phase 逸脱棲み分け追記（POO は Phase 警告責任外）。[II-W-N1] NFR-W10-3 を SHOULD+MUST 入れ子から MUST+MAY（例外条件付き）に書き換え。[II-W-N2] §11 トレーサビリティに cross-spec 整合確認記録追記（4 スキル整合済 / FR-W10-3 表訂正なし）。[II-W-N3] AC-W10-5 に「Wave 10 内では spec 記述が受入条件 / Wave 11 BUILDING 実測」を追記し AC-W10-7 と対称化。[II-W-N4] §5 前提 2 を「前提 1 の後続条件」表記に書き換え。[II-I-N1] FR-W10-2 に MUST 5/6 同時発生時の統合「推奨なし」出力ルール追記。[II-I-N2] spike/README.md §3 V-3 に概算根拠の未確定注記追記（v0.3 適用）。[II-I-N3] §12 v0.2.0 W5 エントリを「spike 側のみ修正 / 本ファイル側修正なし」に訂正 / I-I-5 独立エントリとして分離記録。[前提 4] **Wave 8 G4 達成条件 3 依存の言語化**を II-C-N1 の §5 前提 1 注記追加 + §8 代替経路エントリで実現（前提 4 単独の新規エントリは作成せず、II-C-N1 修正に統合）。[前提 5] FR-W10-5 に current-phase.md 消失時の Phase=unknown / Step=SESSION_STATE.md 値の整合ルール追記。§9 に R3 確定論点（R3-C1〜R3-前提 5）追記 |
| 0.4.0 | 2026-06-29 | R4 一括修正（spec-critic R3 Warning 2 件 + Info 4 件 / Final Green 狙い）。[W-R3-1（選択肢 A）] FR-W10-3 表後に「呼び出し前提条件は POO 推奨フィルタリングとして確認する条件 / スキル側の起動ガードではない」注記を追加。§10 OQ-4 として Wave 11 PLANNING 確定事項（具体的な確認手順）を登録。[W-R3-2（選択肢 A）] §5 に「前提 5: current-phase.md 消失時の Phase=unknown と Step 併記ルール（詳細は FR-W10-5 末尾参照）」を前提 1〜3 と並列で追加。FR-W10-5 の詳細仕様は現状維持（§5 はサマリ）。[I-R3-1] FR-W10-5 末尾段落を (a) SHOULD NOT 逸脱判定の限定 / (b) Phase 規律の棲み分け / (c) current-phase.md 消失時の Phase=unknown と Step 整合 の 3 箇条に分割し、各論点の対応関係を明確化。[I-R3-2] §8 Out-of-scope の代替経路エントリに「根拠: 最小侵襲性の観点から推奨 / Wave 11 PLANNING で MAGI 合議により確定 / 本 Wave では確定しない」を追記。[I-R3-3] NFR-W10-3 に「測定基準: 標準ライブラリのみ実装が 30 秒超 / 測定対象データ量・試験環境は Wave 11 設計書で具体化」を追記。[I-R3-4] §12 v0.3.0「前提 4」エントリを「Wave 8 G4 達成条件 3 依存の言語化を II-C-N1 修正に統合（前提 4 単独の新規エントリは作成せず）」に書き換え。§9 に R4 確定論点（R4-W1 / R4-W2 / R4-I1〜I4）追記。§11 トレーサビリティに R4 修正対応エントリを追記 |
| 0.5.0 | 2026-06-29 | R5 Final Green 確定修正（spec-critic R4 Warning 1 件 + Info 3 件 / 完全 Green State 確定狙い）。[W-R4-1 (a)（別行注記案採用）] FR-W10-5 (c) を「AC-W10-1 の 4 次元フォーマット変更なし / Phase=unknown は 4 次元出力の直後に別行注記 `[注記] Phase=unknown (current-phase.md 不在)` として出力（MUST）」に書き換え。[W-R4-1 (b)（I-R4-1 同時解消）] §5 前提 5 を 1 行サマリ「Phase=unknown 別行注記ルール（詳細は FR-W10-5 末尾 (c) 参照）」に縮小し重複詳細を削除。[W-R4-1 (c)] AC-W10-1 にフォーマット変更なし・Phase=unknown 別行注記の説明を統合（テーブル内記述 / FR-W10-5 末尾 (c) 参照）。[I-R4-2] §10 OQ-4 の質問文を「FR-W10-3 注記で論理的条件は確定済み / Wave 11 PLANNING で確定する実装レベル詳細（Step 判定の参照ファイル経路 / unknown 条件の閾値）を明示」に詳細化。§9 に R5 確定論点（R5-W1 / R5-I2）追記。§11 トレーサビリティに R5 修正対応エントリを追記 |

---

## 権限等級

本ファイルの変更: **PM 級**（仕様書変更）
AC 追加・修正: **PM 級**
表記の微調整・typo 修正: **PG 級**

---

## 参照

- `docs/adr/0006-loop-engineering-vocabulary-and-lam-alignment.md`（Stage 3 位置付け / Glossary / 推奨改善方針）
- `docs/specs/b4-dashboard/wave8/requirements.md`（MilestoneRegistry 本格化 FC-10 / MilestoneProvider Protocol）
- `docs/specs/b4-dashboard/wave8/design.md`（MilestoneSourceMerger アーキテクチャ / Protocol 昇格契約）
- `docs/specs/b4-dashboard/requirements.md`（b4-dashboard SSOT / §9 将来候補 ⑥ 連携）
- `docs/specs/autonomous-mode/requirements.md`（FR-2 権限エンベロープ / FR-9.1 自己統治の不可侵）
- `docs/specs/goal-driven-orchestration/requirements.md`（rubric ファースト / 独立 grader 要件）
- `docs/artifacts/retro-W7-B5-2026-06-28.md`（A1 NFR 寿命管理 / A4 MAGI Reflection / A9 担当層判断基準 / §6 着手順序）
- `.claude/rules/planning-quality-guideline.md`（Requirements Smells / RFC 2119 / WBS 100% Rule）
- `.claude/rules/terminology.md`（Milestone / Step / Wave / Task 用語ガイドライン）
- `.claude/rules/permission-levels.md`（PG/SE/PM 等級）
- `.claude/rules/phase-rules.md`（フェーズ規律 / ガードレール）
