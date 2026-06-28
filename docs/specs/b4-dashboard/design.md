# 設計書: b4-dashboard（可視化レイヤー）

- バージョン: 0.2.7
- 作成日: 2026-06-20
- 更新日: 2026-06-28（v0.2.7 = 最終クリーニング / Green State 完全達成）
- ステータス: Draft（Wave 9 設計反映 / PM 承認待ち）
- 根拠文書: `docs/specs/b4-dashboard/requirements.md`（FR-1〜FR-11 / NFR-1〜6 / AC-1〜8）
- 参照文書: `docs/specs/b4-dashboard/glossary-draft.md`（v0.2.0）
- 参照文書: `docs/specs/b4-dashboard/wave8/requirements.md`（FR-W8-1〜 / Wave 8 追加要件）
- 参照文書: `docs/specs/b4-dashboard/wave8/design.md`（Wave 8 詳細設計）
- 参照文書: `docs/specs/b4-dashboard/wave9/requirements.md`（FR-W9-1〜 / Wave 9 追加要件）
- 参照文書: `docs/specs/b4-dashboard/wave9/design.md`（Wave 9 詳細設計）

---

## §1 概要 / Problem Statement

### Problem Statement

LAM プロジェクトは Project / Milestone / Step / Wave / Task の 4 + Phase 補助の階層で作業を管理しているが、
現時点では作業状態の可視化手段が存在しない（`docs/specs/b4-dashboard/requirements.md` §1 より）。

設計観点で追加する問題は以下の通り:

| 問題 | 設計上の影響 |
|------|------------|
| SESSION_STATE.md はプレーンテキストであり機械的な状態抽出が困難 | パーサを設計する際に regex ベースの脆弱な実装になりやすい |
| データソースが複数ファイルに分散し形式も不統一（Markdown / plain text / git log）| パーサ間のインターフェースを統一しないと拡張コストが高騰する |
| `/quick-save` 連動で HTML が頻繁に生成されるため生成速度と安定性が要求される | 30 秒以内（NFR-4）・エラー耐障害性（NFR-6）の両立が設計制約になる |

本設計書は上記問題を「単一 HTML 生成スクリプト + ビュー単位パーサ + `/quick-save` フック」の構成で解決する。

---

## §2 Goals / Non-Goals

### Goals（要件書より継承）

- LAM プロジェクトの Milestone・Step・Wave・Task レベルの進捗状態を単一 HTML ファイルで表示する
- 既存ファイル群（SESSION_STATE.md / `docs/specs/<milestone>/tasks.md` / `.claude/current-phase.md` / git log）をデータソースとして活用し、別途データベースを構築しない
- ネットワーク接続なしにローカル環境でダッシュボードを表示できる
- `/quick-save` 実行時にダッシュボードを自動更新する（FR-11 SHOULD）

### 設計スコープの追加目標

- データソースパーサのインターフェースを統一し、将来のデータソース追加コストを局所化する
- エラー耐障害性を「各パーサが独立して失敗する」設計で実現し、部分失敗が全体を止めないようにする

### Non-Goals（非スコープ）

要件書 §2 Non-Goals を継承し、設計でも以下は対象外とする:

- 具体的な CSS スタイリング・配色設計: 最小限の inline style のみ。UI デザインは PoC 後のフェーズで決める
- 特定 JavaScript フレームワークの確定: 候補を列挙するに留め、確定は BUILDING フェーズへ委ねる
- 多言語化（i18n）
- ダッシュボードからの作業操作（表示専用）
- リアルタイム自動更新（ファイル監視）
- MCP 連携: B → C ハイブリッド拡張として future-candidates に記録済み（requirements.md §9）
- モバイル対応

#### Wave 8 追加 Non-Goals（v0.2.0）

- **MilestoneRegistry 本格化（案 3）**: Wave 8（案 5）は `MilestoneSourceMerger` を将来の Registry 昇格への踏み石として位置付けるが、Registry 自体の実装は Wave 8 のスコープ外とする。Registry 昇格は骨子 ⑥（プロジェクト俯瞰オーケストレータ）の設計確定時に実施する（FC-10 参照）。
- **FC-7 Step 別管理**: Milestone 別の Step（PLANNING/BUILDING/AUDITING）管理は引き続き将来候補。本 Wave 8 の `MilestoneSourceMerger` はデータソース統合（集合演算）のみを担い、Step 別管理は含まない。
- **双方向同期**: Merger は read-only 集約レイヤであり、SessionState や tasks.md への書き戻し（双方向同期）は行わない（MUST NOT）。

#### Wave 9 追加 Non-Goals（v0.2.3）

- **description キーワードフィルタ**: V-4 の description 列を対象にしたテキストフィルタ機能は将来候補（FC 候補）。Wave 9 では既存テキスト検索（filter-text / Task ID・担当対象）の拡張は行わない。
- **詳細表示モーダル**: description を全文表示するモーダルウィンドウは将来候補。Wave 9 では `title` 属性 tooltip のみで対応。
- **description の多行折り返し**: 省略表示（ellipsis）のみとし、多行折り返しモードは実装しない。
- **description ソート**: description 列にソートボタンは設けない（MAGI 合議 2026-06-28 B2 確定）。
- **V-4 CSS 意匠変更**: Wave 9 で追加する `.description-cell` スタイル以外の CSS 意匠変更（配色テーマ・レイアウト）は対象外。

---

## §3 アーキテクチャ概要

### コンポーネント構成（v0.2.0 / Wave 8 集約レイヤ追加）

```
[データソース層]                  [パーサ層]                [集約レイヤ（Wave 8 新設）]   [生成スクリプト]        [出力]
SESSION_STATE.md    ──→  SessionStateParser  ─┐
                                              ├─→  MilestoneSourceMerger  ─┐
tasks.md（各 Milestone）──→  TasksParser      ─┘                            │
                                                                             ├→  DashboardBuilder → dashboard.html
current-phase.md    ──→  CurrentPhaseParser  ──────────────────────────────┤
git log（コマンド出力）──→  GitHistoryParser  ───────────────────────────────┘
                                                                            ↑
                                               build_dashboard.py（オーケストレータ）
                                                                            ↑
                                    `/build-dashboard` スキル  または  `/quick-save` スキル（Step 追加）
```

**集約レイヤの位置付け**: `MilestoneSourceMerger`（Wave 8 新設）は SessionStateParser と TasksParser の両出力から Milestone 集合を統合し、V-2 および V-4 フィルタ UI に対して単一の SSOT を提供する。他の 2 パーサ（CurrentPhaseParser / GitHistoryParser）は MilestoneSourceMerger を経由しない。

### データフロー（v0.2.0）

1. `build_dashboard.py` が各パーサを呼び出す
2. 各パーサは `parse() -> dict` を実行し、データまたは空のフォールバック値を返す
3. `MilestoneSourceMerger` が SessionStateParser 結果と TasksParser 結果から Milestone 集合を統合し `DashboardData.milestones` を確定する（Wave 8 追加）
4. `DashboardBuilder` が全パーサ結果（MilestoneSourceMerger 経由の統合 Milestone を含む）を受け取り、HTML テンプレートを展開する
5. 生成 HTML を `docs/artifacts/dashboard/dashboard.html` に書き出す

### パーサの独立性原則（v0.2.0 / Merger との関係を明示）

各パーサは他のパーサの結果に依存してはならない（MUST NOT）。
1 つのパーサが例外で失敗しても、`build_dashboard.py` は残りのパーサを継続呼び出しし、
失敗したビューのみ「データなし」状態で描画する（FR-6 / NFR-6 の実現）。

**MilestoneSourceMerger との関係**: Merger は「上位集約レイヤ」であり、パーサの独立性原則に違反しない。
Merger はパーサ同士を直接参照させるのではなく、`build_dashboard.py`（オーケストレータ）が各パーサ結果を取得した後に Merger へ渡す設計とする。パーサ層と集約レイヤは依存方向が一方向（パーサ → Merger）であり、循環依存を持たない。

---

## §4 ビュー設計

各ビューは HTML の `<section>` 要素単位で独立させ、`id` 属性でアンカーリンクを提供する。

### V-1: Project サマリービュー

**表示要素:**

| 要素 | データソース | 表示ロジック |
|------|------------|------------|
| Project 名 | ハードコード（"LAM"） | 固定文字列 |
| アクティブ Milestone 数 | SessionStateParser | `in-progress` 状態の Milestone カウント |
| 全体ステータス | SessionStateParser | 最上位状態（`blocked` > `in-progress` > `not-started` > `completed`） |
| 最終更新日時 | `build_dashboard.py` 実行時の timestamp | `datetime.now()` |

**DOM 構成案:**

```html
<section id="v1-project-summary">
  <h1>LAM Dashboard</h1>
  <dl>
    <dt>Project</dt><dd>LAM（Living Architect Model）</dd>
    <dt>アクティブ Milestone</dt><dd data-value="N">N 件</dd>
    <dt>全体ステータス</dt><dd><span class="badge" data-status="in-progress">進行中</span></dd>
    <dt>最終更新</dt><dd>YYYY-MM-DD HH:MM:SS</dd>
  </dl>
</section>
```

### V-2: Milestone 一覧ビュー

**表示要素（v0.2.0 / データソースを集約レイヤ経由に整合化）:**

| 要素 | データソース | 表示ロジック |
|------|------------|------------|
| Milestone 名 | **MilestoneSourceMerger**（Wave 8 SSOT） | SessionState の Milestone 集合 + tasks.md 由来の Milestone 集合を merge して提供 |
| 現在の Step（属性列）| CurrentPhaseParser | `.claude/current-phase.md` の Phase 文字列を regex で全文抽出 |
| 状態 | SessionStateParser（Merger 経由） | 4 値ステータスバッジ（"in-progress" 等）|

> **Wave 7 → Wave 8 の整合化（v0.2.0）**: Wave 7 では V-2 の Milestone リストを「SessionStateParser が SESSION_STATE.md 内の Task ID から逆引きで構築」する実装ベース SSOT として暫定維持していた（wave7/design.md §8 「Milestone 識別の実装ベース定義」）。Wave 8 では `MilestoneSourceMerger` を新設し、SessionState 由来の Milestone 集合と tasks.md 由来の Milestone 集合を集合演算で統合した結果が V-2 の SSOT となる。これにより chip `task_68008f88`「Milestone フィルタ仕様乖離」が正式解決される。

> V-2 Step 属性列は CurrentPhaseParser が返す単一フェーズ文字列（"PLANNING" / "BUILDING" / "AUDITING"）。
> 複数 Milestone が存在する場合は全 Milestone に同じ Step を表示する（現時点は LAM 単一プロジェクト固定）。
> Step の Milestone 別管理は引き続き将来候補（FC-7）。

**DOM 構成案（Wave 7 実装継承）:**

```html
<section id="v2-milestones">
  <h2>Milestone 一覧</h2>
  <div class="milestones-container">
    <article class="milestone-card" data-milestone="B-4">
      <h3>B-4</h3>
      <p>Step: <span class="step">BUILDING</span></p>
      <p>状態: <span class="status">in-progress</span></p>
    </article>
    <article class="milestone-card" data-milestone="B-5">
      <h3>B-5</h3>
      <p>Step: <span class="step">BUILDING</span></p>
      <p>状態: <span class="status">in-progress</span></p>
    </article>
  </div>
</section>
```

### V-3: Wave 一覧ビュー

**表示要素:**

| 要素 | データソース | 表示ロジック |
|------|------------|------------|
| Wave 番号 | SessionStateParser | SESSION_STATE.md から抽出 |
| Wave 内 Task 数 | TasksParser | 対応 tasks.md のチェック行カウント |
| Wave 状態 | SessionStateParser + GitHistoryParser（補完） | 基本は SessionStateParser。git log で `completed` を補完 |

**DOM 構成案:**

```html
<section id="v3-waves-B-5">
  <h2>Wave 一覧（B-5）</h2>
  <table>
    <thead>
      <tr><th>Wave</th><th>Task 数</th><th>状態</th></tr>
    </thead>
    <tbody>
      <tr data-wave="1">
        <td>Wave 1</td>
        <td>5</td>
        <td><span class="badge" data-status="in-progress">進行中</span></td>
      </tr>
    </tbody>
  </table>
</section>
```

### V-4: Task 一覧ビュー

**表示要素（v0.2.3 / description 列追加 / フィルタ選択肢のデータソースを Merger 経由に整合化）:**

| 要素 | データソース | 表示ロジック | 列位置 |
|------|------------|------------|--------|
| Task ID | TasksParser | `docs/specs/<milestone>/tasks.md` から抽出 | 1列目 |
| description | TasksParser | Task ID・assignee タグ除去後の本文（§5「TasksParser」参照）。空文字列時は空セル | **2列目**（Task ID 右隣）|
| 担当（AI 種別）| TasksParser | tasks.md チェック行末の `@<assignee>` タグ（§5「Assignee タグ規約」）。未記入時は `-` | 3列目 |
| 状態 | TasksParser | チェックボックス状態（`[x]` = `completed` / `[ ]` = `not-started`） + SessionStateParser で `in-progress` / `blocked` を補完 | 4列目 |
| 完了判定 | TasksParser | `[x]` チェック | — |

> **フィルタ選択肢の SSOT（v0.2.0）**: V-4 の「Milestone フィルタ」選択肢（`<select id="filter-milestone">`）は、Wave 7 以前では `DashboardData.milestones`（SessionStateParser の逆引き結果のみ）を参照していた。Wave 8 では `MilestoneSourceMerger` の統合結果を参照するように変更する（`_render_filter_controls()` が Merger SSOT を反映）。これにより tasks.md にしか存在しない Milestone（SESSION_STATE.md に Task ID が記録されていない Milestone）もフィルタ選択肢に現れるようになる。

**DOM 構成案（v0.2.3 / 4 列 / description は 2 列目）:**

```html
<section id="v4-tasks">
  <h2>Task 一覧</h2>
  <table id="tasks-table">
    <thead>
      <tr>
        <th id="th-task-id" aria-sort="none">
          <button class="sort-btn" data-col="0">Task ID</button>
        </th>
        <th id="th-description">description</th><!-- ソートボタンなし / aria-sort属性なし -->
        <th id="th-assignee" aria-sort="none">
          <button class="sort-btn" data-col="2">担当</button>
        </th>
        <th id="th-status" aria-sort="none">
          <button class="sort-btn" data-col="3">状態</button>
        </th>
      </tr>
    </thead>
    <tbody>
      <tr data-task-id="W1-B5-T1" data-milestone="B-5">
        <td>W1-B5-T1</td>
        <td class="description-cell" title="BaseParser 実装完了">BaseParser 実装完了</td>
        <td>Sonnet</td>
        <td><span class="badge" data-status="completed">完了</span></td>
      </tr>
    </tbody>
  </table>
</section>
```

> **Wave 9 変更点**: Task ID 右隣（2 列目）に description を追加。**JS 定数値（`COL_ASSIGNEE` / `COL_STATUS`）および
> `data-col` 属性値（担当 th / 状態 th）の両方が更新必須**（選択肢 A 補完 / 2026-06-28 ユーザー承認）:
> - (a) JS 定数値: `COL_DESCRIPTION=1` 新規追加 / `COL_ASSIGNEE 1→2` / `COL_STATUS 2→3`
> - (b) data-col 属性値: 担当 th `data-col="1"→"2"` / 状態 th `data-col="2"→"3"` / Task ID th `data-col="0"` 変更なし
>
> これにより `sortTable()` の `cells[columnIndex]`（data-col 経由）と `applyFilters()` の
> `cells[COL_STATUS]`/`cells[COL_ASSIGNEE]`（定数経由）の両方が物理列と整合する。
> 詳細は `wave9/design.md §6「JS 定数値 + data-col 属性値更新」節`および `wave9/requirements.md FR-W9-N1` を参照。
> description 列ヘッダは `sort-btn` を持たず `aria-sort` 属性なし（FR-W9-4 MUST NOT）。

### ナビゲーション（FR-3 SHOULD）

V-1 → V-2 → V-3 → V-4 のドリルダウンは同一ページ内アンカーリンクで実現する。
V-2 の Milestone 名から `#v3-waves-<milestone>` へリンクを張る。
JavaScript による動的展開（アコーディオン等）は BUILDING フェーズで選定する（MAY）。

---

## §5 データソース層

### パーサ共通インターフェース

各パーサは以下のインターフェースに準拠する（Python 3.x ABC を使用 MAY、duck typing での実装も可）:

```python
class BaseParser:
    def parse(self) -> dict:
        """
        データソースを読み込み、正規化されたデータを返す。

        戻り値の形式:
          {
            "ok": bool,           # 読み込み成功フラグ
            "error": str | None,  # 失敗時のエラーメッセージ（ok=False のとき）
            "data": dict | None,  # 成功時のパース結果（ok=False のときは None）
          }

        例外は外に伝播させず、ok=False の dict を返すこと（MUST）。
        """
        raise NotImplementedError
```

### 各パーサの責務

#### SessionStateParser

| 項目 | 内容 |
|------|------|
| 入力 | `SESSION_STATE.md`（プロジェクトルート直下）|
| 責務 | 進行中タスク・完了タスク・未解決問題・次ステップを Markdown テキストから抽出 |
| 戻り値キー | `milestones: list[MilestoneInfo]`, `waves: list[WaveInfo]`, `in_progress: list[str]`, `blocked: list[str]`, `completed: list[str]` |
| パース方針 | `##` 見出しでセクション分割 → `###` 見出しで項目抽出 → 箇条書き行から値を取得 |
| 失敗条件 | ファイル不在 / 読み込みエラー。パース結果が空でも `ok=True` で空リストを返す |

#### CurrentPhaseParser

| 項目 | 内容 |
|------|------|
| 入力 | `.claude/current-phase.md` |
| 責務 | 現在の Phase 文字列（"PLANNING" / "BUILDING" / "AUDITING" / "AUTONOMOUS"）を全文 regex で抽出 |
| 戻り値キー | `phase: str` |
| パース方針 | 全文を読み regex `\*\*(PLANNING\|BUILDING\|AUDITING\|AUTONOMOUS)\*\*` で抽出。最初にマッチした Phase 名を返す。マッチしない場合・空ファイルの場合は `phase: "UNKNOWN"` を返す |
| 失敗条件 | ファイル不在 / 読み込みエラー |

> **実装との整合（2026-06-21 BUILDING で確定）**: 当初設計案は「1 行目を strip()」だったが、
> 実 `.claude/current-phase.md` は 1 行目が `# Current Phase` の見出しで Phase 名ではない。
> Phase 名は本文中に `**BUILDING**` の bold 記法で記載される構造のため、
> W2-B5-T8（commit `db878bc`）で regex 全文抽出方式を採用した。
> 本表記は実装に合わせて AUDITING フェーズ（次セッション）で正式更新（2026-06-21 反映）。

#### TasksParser

| 項目 | 内容 |
|------|------|
| 入力 | `docs/specs/<milestone>/tasks.md`（存在するすべての Milestone 分）|
| 責務 | チェックボックス行（`- [ ]` / `- [x]`）をスキャンし Task エントリを構築 |
| 戻り値キー | `tasks: list[TaskInfo]`（各 Task に `id`, `status`, `assignee`, `milestone`, `description`）|
| パース方針 | regex `^-\s\[( |x)\]\s(.+)$` でチェックボックス行を抽出。`[x]` → `completed`, `[ ]` → `not-started`。description 末尾の `@<assignee>` タグを抽出し `TaskInfo.assignee` に格納（§5「Assignee タグ規約」）。タグ未記入時は `assignee="-"`（後方互換）。**Wave 9 追加**: `_extract_assignee(raw_description)` の戻り値第 1 要素（`clean_description`）を `TaskInfo.description` に渡す 1 行追加のみ。parser ロジックの追加ゼロ（既存 `raw_description` の活用）。詳細は `wave9/design.md §5` を参照 |
| 失敗条件 | Milestone ディレクトリが存在しない / tasks.md 不在。個別 Milestone 失敗は他 Milestone の処理を止めない |
| Milestone 検出 | `docs/specs/` 配下を `**/tasks.md` で再帰走査（T56 / Wave 7 Stage 1 実装済）し、`tasks.md` が存在するものを対象とする。Milestone 名は Task ID（`W{n}-B{n}-T{n}`）の `B{n}` 部分から `B-{n}` 形式に変換して逆引き。TasksParser は自身が検出した Milestone 名リストを `MilestoneSourceMerger` に提供する（Wave 8 追加）|

##### Assignee タグ規約（Wave 7+ 追加 / RFC 2119 SHOULD）

**目的**: V-4 担当列に意味のあるデータを供給する。SSOT は `tasks.md` 一本に保つ。

**記法**:

```
- [<box>] <Task ID>: <description> @<assignee>
```

- `<assignee>` は半角英数とハイフン・アンダースコアのみで構成される単語（regex: `[A-Za-z0-9_-]+`）。例: `Sonnet`, `Haiku`, `Fable`, `Opus`, `human`
- 推奨値は 3.5 層委譲モデル（`CLAUDE.md §作業体制`）の主担当層を示す単一値: `Sonnet`, `Haiku`, `Fable`, `Opus`, `human` 等。複合担当（L2/L3 同時記載）は本規約のスコープ外（将来拡張で複合タグを再検討）
- タグは行末に **1 個まで**。複数記載時は最後の 1 個のみ採用する
- `<description>` 内の `@` を含む通常テキスト（例: メールアドレス）と衝突しないよう、行末固定で抽出する

**抽出規則（TasksParser）**:

- 正規表現: `\s+@([A-Za-z0-9_-]+)\s*$`（description 末尾、空白区切り、改行直前）
- マッチした場合: `TaskInfo.assignee = <抽出値>`、description 本文からタグ部分を除去
- 未マッチの場合: `TaskInfo.assignee = "-"`（後方互換、既存挙動維持）

**例**:

| tasks.md 行 | 抽出結果 |
|------------|---------|
| `- [x] W1-B5-T1: BaseParser 実装完了` | id=`W1-B5-T1`, assignee=`-` |
| `- [ ] W7-B5-T50: 担当列実装 @Sonnet` | id=`W7-B5-T50`, assignee=`Sonnet` |
| `- [x] W7-B5-T51: 採点 @Haiku` | id=`W7-B5-T51`, assignee=`Haiku` |
| `- [ ] T99: 連絡先 contact@example.com を更新` | id=`T99`（タグ判定対象外、`@example.com` は行末から空白区切り単語として切り出されない可能性あり。実装時にエッジケース確認）|

**表示変換（DashboardBuilder）**:

- HTML 出力時は `@` を除去した値をそのまま表示（例: tasks.md で `@Sonnet` → V-4 表示は `Sonnet`）
- 未指定（`-`）は従来通り `-` を表示

**遡及方針**:

- 既存 tasks.md への遡及記入は **強制しない**（SHOULD ではなく MAY）
- 新規 Task から自然蓄積させ、`-` 表示と意味あるラベルの混在を許容
- 一括記入したい場合は別途 Milestone レベルで人間判断（PM 級）

**スコープ外（Non-Goals）**:

- 複合担当タグ（`@L2:Sonnet @L3:Haiku` 等）の対応
- Wave→担当の自動推定
- assignee 値の妥当性検証（任意文字列を受け入れる）

**根拠**: B-5 Wave 6 PoC レビュー（2026-06-27）で V-4 担当列が全タスク `-` 表示となり情報無価値と判明。MAGI 合議（2026-06-27）で SSOT 一本化と後方互換を優先する本方針を採択。

#### GitHistoryParser

| 項目 | 内容 |
|------|------|
| 入力 | `git log --oneline -100` コマンド出力（ファイルパスではない） |
| 責務 | コミットメッセージから Wave・Task の完了情報を補完する |
| 戻り値キー | `completed_waves: list[str]`, `completed_tasks: list[str]` |
| パース方針 | `subprocess.run(["git", "log", "--oneline", "-100"])` → 各行から Wave/Task キーワードを regex 抽出 |
| 失敗条件 | `git` コマンドが存在しない / `subprocess` が非ゼロ終了。`ok=False` を返し V-3 補完なしで継続 |
| 重要制約 | git log の実行失敗はエラー終了してはならない（MUST NOT, FR-6）|

### データモデル（暫定）

```python
from dataclasses import dataclass, field

@dataclass
class MilestoneInfo:
    name: str                   # 例: "B-5"
    current_step: str           # 例: "PLANNING"（CurrentPhaseParser から補完）
    status: str                 # "not-started" / "in-progress" / "blocked" / "completed"

@dataclass
class WaveInfo:
    milestone: str              # 例: "B-5"
    wave_number: str            # 例: "1", "1.5"
    task_count: int             # V-4 TasksParser から補完
    status: str

@dataclass
class TaskInfo:
    id: str                     # 例: "W1-B5-T1"
    milestone: str
    assignee: str               # 例: "Sonnet", "-"
    status: str
    description: str = ""       # Wave 9 追加（FR-W9-2）: Task ID・assignee タグ除去後の本文。既定値 "" で後方互換維持

@dataclass
class DashboardData:
    milestones: list[MilestoneInfo] = field(default_factory=list)
    waves: list[WaveInfo] = field(default_factory=list)
    tasks: list[TaskInfo] = field(default_factory=list)
    current_phase: str = "UNKNOWN"
    generated_at: str = ""
    parser_errors: list[str] = field(default_factory=list)  # エラーサマリーを HTML に表示
```

### 状態値の決定ロジック

`glossary-draft.md` §2 に記載された暫定ロジックを設計レベルで具体化する:

```
Task の状態決定（優先順位順）:
  1. SESSION_STATE.md「完了タスク」に記録あり → "completed"
  2. SESSION_STATE.md「進行中タスク」に記録あり → "in-progress"
  3. SESSION_STATE.md「未解決の問題」に記録あり → "blocked"
  4. tasks.md に `[x]` チェックあり → "completed"
  5. tasks.md に `[ ]` チェックあり → "not-started"
  6. いずれにも該当しない → "not-started"

Wave の状態決定:
  1. 配下の全 Task が "completed" → "completed"
  2. GitHistoryParser で当該 Wave のコミットを確認 → "completed"（補完）
  3. 配下に "in-progress" Task あり → "in-progress"
  4. 配下に "blocked" Task あり → "blocked"
  5. 全 Task が "not-started" → "not-started"
```

> 上記ロジックは設計フェーズの初期案。BUILDING フェーズで実データを使った検証後に調整する（MAY）。

### MilestoneSourceMerger — 集約レイヤ仕様（Wave 8 新設 / v0.2.0）

#### 位置付け

`MilestoneSourceMerger` は Wave 8 で新設する「上位集約レイヤ」であり、パーサ層とは独立した
モジュールとして `.claude/scripts/dashboard/merger.py` に配置する。
パーサの独立性原則（§3）に違反しない（Merger はパーサを直接呼び出さず、
`build_dashboard.py` がパーサ結果を Merger に渡す）。

#### クラス設計（スケッチ / BUILDING フェーズで確定）

> **I-C-3 反映（v0.2.1）**: `MilestoneProvider.get_milestones()` は無引数シグネチャのため、
> Merger は constructor で 2 入力を受け取り `get_milestones()` で結果を返す設計に変更。
> `_merge()` は内部ロジック用 private メソッドとして整理する。

```python
from dataclasses import dataclass, field
from dashboard.models import MilestoneInfo


@dataclass
class MergedMilestone:
    """統合後 Milestone エントリ。出典タグ付き（Registry 昇格時の拡張型として残置）。

    ※ Wave 8 段階では使用しない（Merger.get_milestones() の戻り値は MilestoneInfo）。
       将来 Registry 昇格時に sources フィールドを持つ拡張型として利用予定（出典タグ機能用）。
    """
    name: str                         # 例: "B-5"
    status: str                       # "in-progress" 等（SessionState 由来を優先）
    sources: list[str] = field(default_factory=list)  # 例: ["session_state", "tasks"]


class MilestoneSourceMerger:
    """SessionStateParser と TasksParser の Milestone 集合を統合する集約レイヤ。

    責務:
      - constructor で 2 入力（session_milestones / task_milestone_names）を受け取る
      - get_milestones() で MilestoneProvider Protocol を実装し、統合結果を返す
      - エラー耐障害性: 片方が空または取得失敗でも残方で継続（MUST）
      - read-only 集約: SessionState / tasks.md への書き戻しは行わない（MUST NOT）
    """

    def __init__(
        self,
        session_milestones: list[MilestoneInfo],
        task_milestone_names: list[str],
    ) -> None:
        self._session_milestones = session_milestones
        self._task_milestone_names = task_milestone_names

    def get_milestones(self) -> list[MilestoneInfo]:
        """Protocol MilestoneProvider 実装。統合後 Milestone リストを返す。

        Returns:
            重複排除・名前昇順ソート済みの MilestoneInfo リスト。
            SessionState 由来のエントリは status 等の属性を保持する。
            tasks.md 由来のみのエントリは status="unknown" で補完する
            （SESSION_STATE.md は揮発的なため「記録なし = 未着手」とは限らない）。
        """
        return self._merge()

    def _merge(self) -> list[MilestoneInfo]:
        """内部統合ロジック（旧 merge()）。"""
        ...
```

#### 入力契約

| 入力 | 型 | 出所 |
|------|----|----|
| `session_milestones` | `list[MilestoneInfo]` | SessionStateParser.parse()["data"]["milestones"] |
| `task_milestone_names` | `list[str]` | TasksParser.parse()["data"]["tasks"] の milestone フィールドを集合化 |

> **I-C-2 反映（v0.2.1）: SessionStateParser の milestones 出力契約**:
> `session_milestones` は `name` 重複なしで渡される。
> SessionStateParser 内部の `seen_milestones: set[str]` 機構（`session_state.py` L195-209 の
> `_build_milestone_wave_lists()` および L235 の `_extract_milestones_waves_fallback()`）が
> 重複排除を保証する。
> Merger 側は防衛として dict 変換で後勝ち集約（`{ms.name: ms for ms in session_milestones}`）を
> 行うが、parser 側での重複発生は設計上想定しない。

#### 出力契約

| 出力 | 型 | 説明 |
|------|----|----|
| 統合 Milestone リスト | `list[MilestoneInfo]` | 重複排除・名前昇順ソート済み。`DashboardData.milestones` に直接代入される |

#### merge ロジック（集合演算）

```
手順:
1. session_milestones から name 集合 A を取得
2. task_milestone_names から name 集合 B を取得
3. A ∪ B（和集合）を作成
4. A に存在する name は SessionStateParser の MilestoneInfo（status 属性付き）を使用
5. B のみに存在する name は MilestoneInfo(name=n, current_step="UNKNOWN", status="unknown") で補完
   （SESSION_STATE.md は揮発的なため「SESSION_STATE にない = 未着手」とは言えない。"unknown" で中立補完）
6. 重複排除後、name 昇順（文字列辞書順）でソートして返す
```

**重複排除ルール**: 同一 name が両方に存在する場合、SessionState 由来のエントリを優先（status / current_step を保持）。
tasks.md 由来のみの Milestone は `status="unknown"` で補完する（`"not-started"` ではない）。

> **I-W-2 設計根拠（v0.2.1）**: SESSION_STATE.md は gitignore 対象かつセッション切替で変動する揮発的ファイルである。
> 「SESSION_STATE.md に記録がない = 未着手」とは限らず、完了済み Milestone が誤って `"not-started"` 表示されるリスクがある。
> これを回避するため、補完値は中立な `"unknown"` とする。

**順序保証**: 出力は name の文字列辞書順でソートされる（Wave 7 A3-4 の決定踏襲）。将来 B-10 以降では自然順ソートに変更可能（互換破壊なし）。

#### エラー耐障害性

- `session_milestones` が空リストの場合: `task_milestone_names` のみで Milestone リストを構築（MUST）
- `task_milestone_names` が空リストの場合: `session_milestones` のみを返す（MUST）
- 両方が空の場合: 空リストを返す（MUST）。ダッシュボードは「Milestone 情報なし」を表示する
- `session_milestones` 内に `name` 重複がある場合（parser 側設計上は発生しない）:
  dict 変換で後勝ちで 1 件に集約（防衛的実装）。parser 側の `seen_milestones` 機構が一次保証（I-C-2）

#### Registry 昇格契約（将来 ⑥ A 設計時の継承点）

`MilestoneSourceMerger` は `MilestoneProvider` という Protocol 型を実装する形で設計する。
将来 `MilestoneRegistry` へ昇格する際は、この Protocol の実装クラスを差し替えるだけで
`build_dashboard.py` のオーケストレータコードを変更せずに済む設計を目指す。

```python
from typing import Protocol

class MilestoneProvider(Protocol):
    """Milestone 一覧を提供するコンポーネントの契約。

    MilestoneSourceMerger（Wave 8）も MilestoneRegistry（将来 ⑥ A）も
    このプロトコルを実装することで、オーケストレータ側の変更なしに差し替え可能にする。
    """
    def get_milestones(self) -> list[MilestoneInfo]: ...
```

> このスケッチは Wave 8 BUILDING フェーズで実装時に確定する。Protocol 名・メソッド名は仮称。

---

## §6 ビルドコマンド設計

### スクリプトの配置

```
.claude/scripts/build_dashboard.py    ← メインスクリプト（オーケストレータ）
.claude/scripts/dashboard/
    __init__.py
    parsers/
        __init__.py
        base.py                       ← BaseParser 定義
        session_state.py              ← SessionStateParser
        current_phase.py              ← CurrentPhaseParser
        tasks.py                      ← TasksParser
        git_history.py                ← GitHistoryParser
    merger.py                         ← MilestoneSourceMerger（Wave 8 新設 / 集約レイヤ）
    builder.py                        ← DashboardBuilder（HTML テンプレート展開）
    models.py                         ← データクラス定義（DashboardData 等）
```

> 既存 `.claude/scripts/distill_lessons.py` と同様に `get_project_root()` パターンを採用し、
> 環境変数 `LAM_PROJECT_ROOT` 優先 → `__file__` の祖先推定のフォールバックとする。

### `build_dashboard.py` の実行インターフェース

```
python .claude/scripts/build_dashboard.py [--output PATH] [--project-root PATH]
```

| オプション | デフォルト | 説明 |
|----------|----------|------|
| `--output` | `docs/artifacts/dashboard/dashboard.html` | 出力ファイルパス |
| `--project-root` | 自動推定（`LAM_PROJECT_ROOT` or `__file__` 祖先）| プロジェクトルート |

### `/build-dashboard` スキル（FR-10 SHOULD）

スキル名は **`/build-dashboard`** に確定（B-5 Wave 1 BUILDING / 2026-06-21 / UQ-3 解決）。
フロントマター書式は `.claude/skills/` 内の既存スキル（`quick-save` / `project-status` / `lam-orchestrate` / `ship`）に準拠する（FR-10 MUST、スキル実装時）。
実装: `.claude/skills/build-dashboard/SKILL.md`（W1-B5-T5 で新設・commit `1ce48ea`）。

**スキルの最小フロー:**

```
1. build_dashboard.py を subprocess.run で呼び出す
2. 戻り値（returncode）を確認
3. 成功: 出力パスを表示
4. 失敗: エラーメッセージを表示（スキル自体は非ゼロ終了しない）
```

`disable-model-invocation: true` を設定し、モデル呼び出しなしで実行できるようにする（既存スキル統一書式）。

---

## §7 `/quick-save` 連動設計

### フック位置

`/quick-save` スキル（`.claude/skills/quick-save/SKILL.md`）の末尾（現行 Step 4「完了報告」の直後）に
Step 5 を追加する。

**追加する Step の案（SKILL.md への記載内容）:**

```
## 5. ダッシュボード更新（SHOULD）

build_dashboard.py を呼び出してダッシュボードを更新する。

実行:
  python .claude/scripts/build_dashboard.py

成功時: 完了報告に「Dashboard: docs/artifacts/dashboard/dashboard.html 更新済み」を追記する。
失敗時: 警告を表示し、quick-save 全体の成否には影響させない（エラー終了しない）。
```

> SKILL.md は `disable-model-invocation: true` のため、Python 実行は Claude Code の Bash ツール経由で呼び出す。

### エラー時の挙動（FR-6 / NFR-6 準拠）

| シナリオ | 対応 |
|---------|------|
| `build_dashboard.py` が非ゼロで終了 | 警告メッセージを表示し、`/quick-save` 自体は正常完了とする |
| `docs/artifacts/dashboard/` が存在しない | `build_dashboard.py` 内で `Path.mkdir(parents=True, exist_ok=True)` を呼ぶ（FR-8 MUST）|
| 全データソースファイルが存在しない | 各パーサが `ok=False` を返し、DashboardBuilder が「データなし」HTML を生成して出力する（NFR-6 MUST）|

### NFR-4 への影響（30 秒上乗せ）

requirements.md FR-11 注記に従い、`/quick-save` 実行時間に NFR-4（30 秒以内）が上乗せされる。
build_dashboard.py は処理開始と完了の timestamp を stderr に出力し、実測値の確認を可能にする（MAY）。

---

## §8 出力形式

### 単一 HTML ファイルの構造

> **注記**: 以下の DOM 構成案 HTML 内の配色値（`#28a745` / `#007bff` / `#dc3545` / `#6c757d` 等）は
> あくまで構造例示のための仮置きであり、確定的な UI 仕様ではない。
> 配色・スタイリングの確定は PoC 後の UI フェーズで決める（§2 Non-Goals 参照）。

```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LAM Dashboard</title>
  <style>
    /* --- inline CSS（最小限）--- */
    /* 配色・レイアウト詳細は PoC 後の UI フェーズで決める */
    .badge[data-status="completed"]   { background: #28a745; color: #fff; }
    .badge[data-status="in-progress"] { background: #007bff; color: #fff; }
    .badge[data-status="blocked"]     { background: #dc3545; color: #fff; }
    .badge[data-status="not-started"] { background: #6c757d; color: #fff; }
    /* Wave 8 追加: "unknown" バッジ (FR-W8-N2 / AC-W8-N1 / I-W-N2 v0.2.2) */
    /* .badge[data-status="unknown"] { background: <gray-9相当>; color: #fff; } */
    /* ↑ 配色は BUILDING で確定。既存 4 値の挙動・配色は無改変 (MUST) */
    .badge { padding: 2px 8px; border-radius: 4px; font-size: 0.85em; }
    /* Wave 9 追加: description 列 (FR-W9-5 SHOULD / NFR-W9-CSS) */
    /* .description-cell { max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; } */
    /* ↑ max-width 値は BUILDING で実測後に確定。title 属性 tooltip で full content を提供 (FR-W9-5) */
    /* 既存テーブルレイアウト・列幅は無改変 (MUST NOT) */
    /* ... 最小スタイル ... */
  </style>
</head>
<body>
  <!-- V-1: Project サマリー -->
  <section id="v1-project-summary"> ... </section>

  <!-- V-2: Milestone 一覧 -->
  <section id="v2-milestones"> ... </section>

  <!-- V-3: Wave 一覧（Milestone ごと）-->
  <section id="v3-waves-B-5"> ... </section>

  <!-- V-4: Task 一覧 -->
  <section id="v4-tasks"> ... </section>

  <!-- パーサエラーサマリー（エラーがある場合のみ表示）-->
  <section id="parser-errors"> ... </section>

  <script>
    /* --- inline JavaScript（MAY: 折りたたみ・フィルター等）--- */
    /* フレームワーク候補: 素 JS / Alpine.js / Lit / Petite-Vue（BUILDING フェーズで選定）*/
  </script>
</body>
</html>
```

### CSS/JS 埋め込み方針

- CSS と JavaScript は `<style>` / `<script>` タグで inline 埋め込みとする（FR-5 外部依存禁止）
- 外部 CDN（Bootstrap, jQuery 等）を参照してはならない（MUST NOT）
- NFR-1（500KB 未満）を満たすため、素 JS または軽量フレームワーク（Lit / Alpine.js / Petite-Vue 等）を候補とする
- フレームワーク選定は BUILDING フェーズで実測後に確定する（MAY）

### JavaScript フレームワーク候補評価（BUILDING フェーズへの引き渡し）

| 候補 | gzip 後サイズ（目安）| 特徴 | NFR-1 適合 |
|------|---------------------|------|-----------|
| 素 JS | 0KB | 依存なし・最軽量 | 確実 |
| Alpine.js | ~16KB | リアクティブ・HTML 属性ベース | 適合 |
| Petite-Vue | ~7KB | Vue ライクな軽量版 | 適合 |
| Lit | ~7KB（コア）| Web Components ベース | 適合 |
| Vue 3 | ~33KB | 多機能・やや重い | 要確認 |

> PoC 実装は素 JS で行い、必要に応じて Alpine.js / Petite-Vue へ移行することを推奨する（MAY）。

### `.gitignore` 方針

`docs/artifacts/dashboard/` ディレクトリを `.gitignore` に追加することを推奨する（FR-8 確定事項、SHOULD）。

理由: `/quick-save` 連動で頻繁に生成・更新される生成物のため、バージョン管理対象にするとコミット履歴が汚染される。
手動での git 追加は MAY とする（デモ・共有目的で一時的にコミットしたい場合）。

`.gitignore` への追記内容:

```
# b4-dashboard 生成物（/quick-save 連動・頻繁更新のため除外）
docs/artifacts/dashboard/
```

---

## §9 エラー耐障害性設計

### 設計原則

FR-6 / NFR-6 を「各パーサが独立して失敗できる」設計で実現する。
`build_dashboard.py` は全パーサ呼び出しを `try/except` で囲み、
個別失敗を `DashboardData.parser_errors` に追記してビルドを継続する。

### フォールバック設計

```python
def build(project_root: Path, output_path: Path) -> int:
    """
    戻り値: 0=成功, 1=部分失敗（警告あり・HTML 生成は完了）, 2=致命的エラー（HTML 未生成）
    """
    data = DashboardData(generated_at=datetime.now().isoformat())

    parsers = [
        ("SessionState",  SessionStateParser(project_root)),
        ("CurrentPhase",  CurrentPhaseParser(project_root)),
        ("Tasks",         TasksParser(project_root)),
        ("GitHistory",    GitHistoryParser(project_root)),
    ]

    for name, parser in parsers:
        try:
            result = parser.parse()
            if result["ok"]:
                _merge_into(data, name, result["data"])
            else:
                data.parser_errors.append(f"{name}: {result['error']}")
        except Exception as e:
            data.parser_errors.append(f"{name}: unexpected error: {e}")

    # パーサエラーがあっても HTML 生成は続行（NFR-6 MUST）
    output_path.parent.mkdir(parents=True, exist_ok=True)
    html = DashboardBuilder(data).render()
    output_path.write_text(html, encoding="utf-8")

    return 1 if data.parser_errors else 0
```

### パーサエラーの HTML 表示

`DashboardData.parser_errors` が 1 件以上ある場合、HTML 末尾の `<section id="parser-errors">` に
エラーサマリーを表示する（非エンジニアが見ても「一部データが取得できていない」と判断できる文言で）。

### 全データソース欠如時の保証（NFR-6）

全パーサが `ok=False` を返した場合でも、以下を含む HTML が生成されること:

- 「データなし（全データソースが読み込めませんでした）」メッセージ
- `generated_at` タイムスタンプ
- パーサエラーサマリー

HTML ファイルが存在しない（書き出し失敗）場合のみ returncode=2 で終了する。

---

## §10 Alternatives Considered

### 案 A: Mermaid 自動生成

**概要**: SESSION_STATE.md や tasks.md を読み込み、Mermaid 記法の `.md` ファイルを生成する。
GitHub の Mermaid レンダリング機能でブラウザ表示する方式。

**メリット:**
- Markdown との統合が自然で、既存ドキュメントと一体化できる
- GitHub レンダリングがそのまま動作する
- 生成スクリプトの実装が比較的シンプル

**デメリット:**
- Mermaid は状態遷移・フロー図に特化しており、V-1〜V-4 の 4 ビュー構成（テーブル表示・ドリルダウン）の表現が困難
- ステータスバッジ（色付きラベル）や動的フィルタリングは Mermaid 記法では実現不可
- データソース別ビューを独立した図に分割する場合、ナビゲーションが困難
- LAM プロジェクトのローカル環境ではブラウザで GitHub プレビューが利用できないことが多い

**評価: 却下。ただし Mermaid 図表は補助的に HTML 内に埋め込み可能（MAY）。**

---

### 案 C: MCP 連携

**概要**: ダッシュボードデータを MCP サーバーとして公開し、Claude Code 等のツールが直接データ取得する方式。

**メリット:**
- 他のツール（Claude Code / 外部クライアント）からプログラム的にダッシュボードデータを取得できる
- リアルタイムデータ取得が可能（ファイル生成なし）
- 将来的な自動化・エージェント連携の基盤になる

**デメリット:**
- MCP サーバーの常駐が必要（Windows 環境でのプロセス管理コストが高い）
- 実装コストが案 B（単一 HTML 生成）の数倍
- ブラウザからの参照には追加の HTTP アダプタ層が必要
- `.claude/settings.json` への MCP サーバー設定追加が必要（PM 級変更）
- LAM プロジェクトの設計思想「外部サービス依存なし・オフライン動作」（FR-5）と部分的に矛盾する

**評価: 案 B 完成後の拡張として future-candidates に記録（B → C ハイブリッド構成）。**

```
B → C ハイブリッド拡張の方針:
  Phase 1（B-5）: 単一 HTML 生成スクリプト（案 B）を実装
  Phase 2（将来）: build_dashboard.py のパーサ層を MCP サーバーのエンドポイントとして公開
                   HTML 生成はクライアントサイドで MCP API を呼ぶ形式に移行
```

---

### 採用: 案 B（単一 HTML ダッシュボード）

**採用理由:**
- オフライン動作・外部依存なし（FR-5 完全準拠）
- Python 標準ライブラリのみで実装可能（NFR-5 適合）
- `/quick-save` 連動によるファイル生成アプローチが LAM プロジェクトの既存パターンと整合する
- V-1〜V-4 の 4 ビュー構成・ステータスバッジ・ドリルダウンが HTML/CSS/JS で自然に実現できる
- 将来の MCP 拡張（案 C）への移行パスを残せる（§3 アーキテクチャのパーサ層独立設計）

---

## §11 Success Criteria

requirements.md §7 AC との対応表:

| AC ID | 受け入れ条件 | 検証方法 | 対応 FR/NFR | 設計での実現手段 |
|-------|------------|---------|------------|----------------|
| AC-1 | `/quick-save` 実行時に HTML が `docs/artifacts/dashboard/` に自動生成されること | ファイル存在確認 | FR-11 SHOULD | §7 `/quick-save` Step 5 追加 |
| AC-2 | V-1〜V-4 のビューが HTML に含まれること | `grep "id=\"v1-\|v2-\|v3-\|v4-"` | FR-1 MUST | §4 各ビュー・§8 HTML 構造 |
| AC-3 | 各エントリに FR-2 の状態値 4 値のいずれかが表示されること | `grep "data-status="` で 4 値確認 | FR-2 MUST | §5 状態値決定ロジック |
| AC-4 | SESSION_STATE.md の「進行中タスク」が V-2/V-3 に反映されること | 実データ目視確認 | FR-4 MUST | §5 SessionStateParser |
| AC-5 | データソースファイルを 1 件削除した状態でビルドが正常完了すること | 削除後 `python .claude/scripts/build_dashboard.py` → returncode 0 or 1 | NFR-6 MUST | §9 フォールバック設計 |
| AC-6 | 生成 HTML がブラウザで 3 秒以内に全ビュー描画を完了すること | Chrome DevTools Lighthouse / 手動計測 | NFR-2 MUST | §8 軽量 JS 選定 / §6 NFR-1 500KB 未満 |
| AC-7 | オフラインでブラウザ表示が完了すること | ネットワーク無効化後にファイルを開く | FR-5 MUST | §8 外部 CDN 参照禁止 |
| AC-8 | `/quick-save` 実行時のダッシュボード自動生成を含めた総実行時間が 30 秒以内であること | quick-save 実行時間計測 | NFR-4 MUST | §7 NFR-4 上乗せ方針・§6 スクリプト設計 |

---

## §12 用語

本設計書で使用する用語は `docs/specs/b4-dashboard/glossary-draft.md`（v0.2.0）に準拠する。
`.claude/rules/terminology.md` と矛盾する場合は terminology.md が優先する。

| 用語 | 参照定義 |
|------|---------|
| Project / Milestone / Step / Wave / Task | terminology.md §1 |
| Phase | terminology.md §2 補助用語 |
| ダッシュボード / ビュー / データソース / ビルド / 状態値 | glossary-draft.md §4 / §3 / §2 |
| SessionState / CurrentPhase / MilestoneTasks / GitHistory | glossary-draft.md §3（識別名）|

---

## §13 未解決設計事項

以下は BUILDING フェーズ着手前に確認・決定が必要な事項を示す。

| ID | 事項 | 優先度 | 解決方針 |
|----|------|--------|---------|
| UQ-1 | SESSION_STATE.md のパース方針の堅牢性 | 高 | BUILDING フェーズで実データ（SESSION_STATE.md 数件）を使ってパーサ実装を試験し、セクション見出しパターンのばらつきに対応する |
| UQ-2 | tasks.md が存在しない Milestone の扱い | 中 | `tasks.md` 不在 Milestone は V-4 に「タスク情報なし」表示。TasksParser は `ok=True, data=[]` を返す |
| UQ-3 | ~~`/visualize` スキル名の確定 / `disable-model-invocation` 書式の裏取り~~ | ~~中~~ | **解決済み（2026-06-21 / B-5 Wave 1 BUILDING / commit `1ce48ea`）**: スキル名は `/build-dashboard` に確定（動詞+名詞ケバブケース・既存スキル統一）。context7 MCP 利用不可のため `.claude/rules/upstream-first.md §3` フォールバック適用 → 既存スキル 4 件（`quick-save` / `project-status` / `lam-orchestrate` / `ship`）の `disable-model-invocation: true` 書式を権威的参照として採用。本セッション（AUDITING・2026-06-21）で requirements.md FR-10 / design.md §6 / §13 に反映完了 |
| UQ-4 | git log のパース regex の定義 | 中 | BUILDING フェーズで実 git log を参照し、Wave/Task のコミットメッセージパターンを特定する（terminology.md §4 コミットメッセージ規約を参照）|
| UQ-5 | `.gitignore` 変更の権限等級 | 低 | `.gitignore` 変更は SE 級扱い（permission-levels.md 参照）。BUILDING フェーズで追記する |
| UQ-6 | DashboardBuilder の HTML テンプレート管理方法 | 中 | Python の `string.Template` または f-string 展開で実装（外部テンプレートエンジン依存を避ける）|
| UQ-7 | ~~複数 Milestone 時の Step 表示方針~~ | ~~低~~ | **将来候補へ移管（2026-06-22 / 採点軽微指摘 #3 対応）**: 同一トピックが `docs/specs/b4-dashboard/future-candidates.md` FC-7 で追跡されており、UQ-7 は実質クローズ。LAM が単一 Milestone である限り発生しないため、FC-7 を一次管理とし本表からは将来削除候補とする |

#### Wave 8 追加未解決事項（v0.2.0）

| ID | 事項 | 優先度 | 解決方針 |
|----|------|--------|---------|
| UQ-8 | `MilestoneSourceMerger` の配置モジュール確定 | 中 | Wave 8 BUILDING フェーズで `merger.py` として実装。§5 MilestoneSourceMerger 節のクラス設計を SSOT とする |
| UQ-11 | `models.py` の `MilestoneInfo.status` コメントへ "unknown" 追記 | 低 | BUILDING 段階で `models.py` の `MilestoneInfo.status` フィールドコメントに `"unknown"` を追記する（SE 級 / FR-W8-N2 対応 / 既存 4 パーサ無改変原則の範囲外）。I-W-N2（v0.2.2）反映 |
| UQ-9 | ⑥ A 着手時の `MilestoneRegistry` 昇格判断 | 低 | 骨子 ⑥（プロジェクト俯瞰オーケストレータ）の設計確定後に、`MilestoneProvider` Protocol を継承する形で `MilestoneRegistry` を実装するか評価する。FC-7（Step 別管理）と合わせて実施可能性を検討する。**Note（I-I-3）: FC-7（Step 別管理）と FC-10（/project-vision 連携）は採用判断が相互依存的であり、どちらを先に進めるかは両者の状況確認が必要。単独で先行採用する場合は依存関係を要確認** |
| UQ-10 | FC-7（Step 別管理）と Wave 8 Merger の関係整理 | 低 | Wave 8 の Merger は Milestone 名の集合演算のみを担い、Step 情報は扱わない（§5 Non-Goals に明記済み）。FC-7 の採用判断は Registry 昇格時（UQ-9）と同タイミングで行う |

#### Wave 9 追加未解決事項（v0.2.3）

| ID | 事項 | 優先度 | 解決方針 |
|----|------|--------|---------|
| UQ-12 | description の max-width 実測値確定 | 中 | Wave 9 BUILDING フェーズでブラウザ上の実表示を確認し、300px から調整する（MAY）。`wave9/design.md §7` で仮値を提示 |
| UQ-13 | ~~description 列と既存ソート JS の整合確認~~ | ~~中~~ | **解決済み（案 A + 選択肢 A 補完 + sortTable() aria-sort 修正 / 2026-06-28 ユーザー承認）**: JS 定数値（`COL_DESCRIPTION=1 / COL_ASSIGNEE=2 / COL_STATUS=3`）を更新し、thead テンプレートの data-col 属性値（担当: 1→2 / 状態: 2→3）を同期更新し、さらに `sortTable()` の `ths.forEach` 内 aria-sort 更新ロジックを `idx === columnIndex` 比較から `thCol === columnIndex`（`thCol` は `th.querySelector('.sort-btn')?.dataset.col` を parseInt したもの）比較に変更することで、aria-sort 属性更新・cells アクセスの両方が Wave 9 後の物理列と整合する。BUILDING での AC-W9-N1 実動作確認は引き続き必須（`wave9/requirements.md` 参照） |
| UQ-14 | description キーワードフィルタの将来取込 | 低 | filter-text（既存）を description も対象に拡張するかは Wave 9+ で PM 判断。Wave 9 では変更なし（Non-Goals） |

---

## §14 権限等級

| 対象 | 等級 |
|------|------|
| 本ファイル（design.md）の変更 | PM 級（仕様変更）|
| `build_dashboard.py` および `.claude/scripts/dashboard/` の実装 | SE 級（新規コード追加）|
| `merger.py`（MilestoneSourceMerger）の新規実装 | SE 級（新規コード追加）|
| `/quick-save` SKILL.md への Step 5 追加 | SE 級（スキル内部変更・公開 API 不変）|
| `/build-dashboard` スキルの新規作成 | SE 級（スキル追加）|
| `.gitignore` への `docs/artifacts/dashboard/` 追記 | SE 級（permission-levels.md 参照）|
| `docs/specs/b4-dashboard/future-candidates.md` 新規作成 | SE 級（ドキュメント追加）|

---

## §15 改訂履歴

| バージョン | 日付 | 変更内容 |
|:----------|:-----|:--------|
| 0.1.0 | 2026-06-20 | 初版起稿 — FR-1〜FR-11 / NFR-1〜6 / AC-1〜8 対応設計 |
| 0.2.0 | 2026-06-28 | Wave 8 MAGI 合議（案 5）反映 — §2 Wave 8 Non-Goals 追加 / §3 MilestoneSourceMerger 集約レイヤ追加 / §4 V-2・V-4 データソース記述を Merger 経由に整合化 / §5 MilestoneSourceMerger 仕様（クラス設計・入出力契約・merge ロジック・Registry 昇格契約）追加 / §6 merger.py 配置追加 / §13 UQ-8〜10 追加 / §14 merger.py 権限等級追加 / 参照文書更新 |
| 0.2.1 | 2026-06-28 | spec-critic レビュー反映（Critical 3 / Warning 6 / Info 4 / L1 追加 1）— §5 クラス設計を constructor 注入版に変更（I-C-3）/ §5 入力契約に SessionStateParser の milestones 重複なし保証を追記（I-C-2）/ §5 merge ロジック補完 status を "not-started" → "unknown" に変更し SESSION_STATE 揮発性を根拠化（I-W-2）/ §5 エラー耐障害性に session 内重複ケース追加（I-C-2）/ §5 MergedMilestone に Wave 8 非使用の脚注追加（L-Q2）/ §13 UQ-9 に FC-7/FC-10 相互依存 Note 追加（I-I-3）|
| 0.2.2 | 2026-06-28 | spec-critic ラウンド 2 反映（Warning 2 / Info 4 / "unknown" バッジ Wave 8 スコープ化）— §8 CSS ブロックに "unknown" バッジルール Note 追加（I-W-N2）/ §13 UQ-11（models.py コメント更新）追加（I-W-N2）|
| 0.2.3 | 2026-06-28 | Wave 9 V-4 description 列追加 / chip task_5de9563e 対応 / Wave 7 retro A10 — ヘッダ更新 / §2 Wave 9 Non-Goals 追加 / §4 V-4 表示要素テーブルを 4 列化・DOM 構成案更新 / §5 TaskInfo に description フィールド追加・TasksParser 節に description 処理記述追加 / §8 CSS に .description-cell Note 追加 / §13 UQ-12〜14 追加 / 参照文書に wave9/ 追加 |
| 0.2.4 | 2026-06-28 | spec-critic ラウンド 1 反映（Critical 2 / Warning 6 / Info 4 / 案 A 採用）— §4 V-4 data-col Note 訂正（I-W-1 / JS 定数値更新必須を明示）/ §13 UQ-13 Critical 解決済化（案 A / JS 定数値更新 / I-C-2・I-I-3）|
| 0.2.5 | 2026-06-28 | spec-critic ラウンド 2 反映（選択肢 A 補完 / 2026-06-28 ユーザー承認）— §4 V-4 data-col Note 再訂正（data-col 属性値も更新必須: 担当 1→2 / 状態 2→3）/ §4 V-4 DOM 構成案 thead の data-col 値を担当=2 / 状態=3 に更新 / §13 UQ-13 に「選択肢 A 補完」追記（data-col 属性値同期更新を解決内容に追加）|
| 0.2.6 | 2026-06-28 | spec-critic ラウンド 3 反映（選択肢 A + sortTable() aria-sort 修正 / 2026-06-28 ユーザー承認）— §13 UQ-13 解決済み記述に「sortTable() aria-sort 更新ロジック修正（thCol 比較）」を追記（I-C-R1）|
| 0.2.7 | 2026-06-28 | 最終クリーニング / Green State 完全達成（Critical = 0 / Warning = 0 / Info = 0）— ヘッダ版数 v0.2.7 化（wave9/ 各ファイルとバージョン統一）|

---

## 参照

- `docs/specs/b4-dashboard/requirements.md`（v0.2.0・SSOT）
- `docs/specs/b4-dashboard/wave8/requirements.md`（FR-W8-1〜 / Wave 8 追加要件）
- `docs/specs/b4-dashboard/wave8/design.md`（Wave 8 詳細設計）
- `docs/specs/b4-dashboard/wave9/requirements.md`（FR-W9-1〜 / Wave 9 追加要件）
- `docs/specs/b4-dashboard/wave9/design.md`（Wave 9 詳細設計）
- `docs/specs/b4-dashboard/glossary-draft.md`（v0.2.0）
- `docs/specs/b4-dashboard/future-candidates.md`（FC-7 / FC-10 参照）
- `.claude/rules/terminology.md`（用語階層の権威的定義）
- `.claude/rules/planning-quality-guideline.md`（Design Doc チェックリスト）
- `.claude/skills/quick-save/SKILL.md`（連動対象スキル）
- `.claude/scripts/distill_lessons.py`（スクリプトパターン参考）
- `docs/specs/v5-fat-reduction/design.md`（設計書章構成の参考）
- `docs/artifacts/retro-W7-B5-2026-06-28.md`（Wave 7 retro / 引き継ぎ事項）

