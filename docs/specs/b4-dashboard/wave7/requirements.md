# b4-dashboard Wave 7 — requirements.md

- バージョン: 0.2.3
- 作成日: 2026-06-27
- 更新日: 2026-06-27（v0.2.3 = v0.2.2 + spec-critic 4 回目レビュー反映 / Critical 3 + Warning 4 + Info 3 対処）
- ステータス: **Approved**（v0.2.3 PM 補追承認 2026-06-27 / spec-critic 4 回目盲点解消）
- マイルストーン: B-5（Wave 7 / PoC 指摘パッケージ）
- 関連:
  - `docs/specs/b4-dashboard/requirements.md` v0.2.0（PoC 仕様 / 継承元）
  - `docs/specs/b4-dashboard/design.md` §5（Assignee タグ規約たたき台 / commit `4448d4c`）
  - `docs/specs/b4-dashboard/wave6/requirements.md` v0.2.0（Wave 6 / 直近 Wave）
  - `docs/artifacts/2026-06-27-magi-wave7-planning.md`（本 Wave スコープ確定の MAGI 合議）
  - `docs/artifacts/retro-W6-B5-2026-06-27.md`（Wave 6 retro / 課題引き継ぎ）
  - `docs/artifacts/knowledge/l2-delegation-guardrails.md`（L2 委譲ガードレール 4 点 / Stage 委譲時挿入）

---

## §1 Problem Statement

B-5 b4-dashboard は Wave 6 BUILDING（Stage 1〜4）を経て CSS スタイリング + ソート + フィルタ +
Lighthouse 97 達成という実用化基盤を獲得した。ただしユーザー PoC レビュー（2026-06-27）にて
**dashboard データの正確性・意味性に関する 4 件の指摘**が挙がり、うち 3 件が parser/data 仕様
問題として Wave 7 統合スコープに格上げされた。

| # | 起源 chip | 問題 |
|:--|:---------|:-----|
| 1 | `task_eec7ce2d` | V-4 担当者列が全行 `-` で意味なし → tasks.md に担当者情報がない / 抽出規約もない |
| 2 | `task_954a1e90` | V-4 Task ID 列に本文行が誤抽出される → TasksParser regex が `[x] 説明文...` 形式まで Task として認識する |
| 3 | `task_52c46569` | V-2/V-3 ビューが Milestone を単一エントリで表示し、複数 Milestone の比較が困難 |

Wave 7 はこの 3 件を「**PoC 指摘パッケージ**」として一括解消し、dashboard の data 品質を
PoC 段階から実用段階へ引き上げる。

> Wave 6 PoC レビュー指摘 4 件のうち「状態フィルタ『全て』で定型句が独立 Task として出る」は
> 指摘 #2 と同根のため #2 に統合（重複削減）。

---

## §2 Goals

Wave 7 で達成する成果を SMART で定義する。

| Goal | 指標 | 達成判定 |
|:-----|:-----|:--------|
| G1: V-4 Task 行の正確性向上 | TasksParser が `W{n}-B{n}-T{n}` 形式のみを Task として抽出 | 既存 task のうち誤抽出行が 0 になる |
| G2: V-4 担当者列の意味化 | tasks.md の `@<assignee>` タグから TasksParser が抽出 + V-4 表示 | dashboard.html 上で `-` 以外の担当値が表示される（≥ 1 件） |
| G3: V-2 複数 Milestone 一覧化 | V-2 で B-4 と B-5 など複数 Milestone を同時可視化 | dashboard.html 上で 2 つ以上の Milestone が並列表示される |
| G4: Wave 6 達成値の退行防止 | Lighthouse Accessibility ≥ 95 / CSS ≤ **16,384 bytes (v0.2.4 改訂)** / pytest 全件 PASS | Stage 4 で全項目達成 |
| G5: PoC 指摘パッケージ完全解消 | 起源 chip 3 件すべてが「解消」または「将来送り」明示 | Stage 4 PoC レビューで判定 |

---

## §3 Non-Goals（明示的に Wave 7 で対応しないこと）

- **複合担当タグ**（`@L2:Sonnet @L3:Haiku` 等）の対応 — design.md §5 Non-Goals 継承
- **Wave→担当の自動推定** — 同上
- **assignee 値の妥当性検証**（任意文字列受入） — 同上
- **複数 Milestone 並列の横並び表示**（option 1） — MAGI A3 で却下 / option 4 採用
- **複数 Milestone のフィルタトグル**（option 2） — 後方互換で追加可能な設計のみ確保。Wave 7 では実装しない
- **Milestone フィルタ仕様乖離**（chip `task_68008f88`） — B-5 内別タスクとして Wave 7 スコープ外
- **既存テスト広範な書き換え** — Wave 6 既存緩和は維持。Stage 1 の parser 修正で必要最小限の更新のみ
- **CSS の意匠面の大幅見直し** — Wave 7 は data 仕様問題の解消が主軸。意匠は Wave 8+ で再検討

---

## §4 機能要件（FR）

### FR-W7-1: TasksParser Task ID 抽出制約（MUST）

TasksParser は `tasks.md` のチェックボックス行から Task を抽出する際、以下の形式のみを Task として認識する:

```
- [<box>] <Task ID>: <description>
```

ここで `<Task ID>` は **`W{n}[.{m}]-B{n}-T{n}` 形式または `T{n}` 形式**（正規表現: `^W\d+(?:\.\d+)?-[A-Z]\d+-T\d+$` または `^T\d+$`）に限定する。Wave 番号は **`W1` / `W7` のような整数 + `W1.5` のような整数.5 形式の両方**を許容する（`.claude/rules/terminology.md` §2 で Wave 1.5 が正例として明記されているため）。それ以外の行（説明文のみ、定型句、本文の続き等）は Task として抽出しない。

**既存実装との整合**: `.claude/scripts/dashboard/parsers/tasks.py` 既存 `_TASK_ID_PREFIX_RE` は `r"^(W\d+(?:\.\d+)?-[A-Za-z0-9]+-T\d+)"` であり、Wave 1.5 形式を許容している。本 FR の regex はこれと整合（Milestone 名側のみ `[A-Z]\d+` に厳格化 / 小文字混在は LAM の命名規約 (`.claude/rules/terminology.md` 大文字 B + 数字) に従い対象外）。

**根拠**: chip `task_954a1e90` — 現状は `- [x] 説明文...` 形式の本文継続行が Task ID として誤抽出され、V-4 に意味のない行が表示される。

**抽出されないケースの例**:

| tasks.md 行 | 現状 | 期待 |
|:-----------|:-----|:-----|
| `- [x] W1-B5-T1: BaseParser 実装完了` | 抽出（id=`W1-B5-T1`） | 抽出（id=`W1-B5-T1`） |
| `- [x] W1.5-B4-T9: 波及修正` | 抽出（id=`W1.5-B4-T9`） | **抽出（id=`W1.5-B4-T9`）** ✅（Wave 1.5 維持） |
| `- [x] T99: 連絡先更新` | 抽出（id=`T99`） | 抽出（id=`T99`） |
| `- [x] 詳細: ...` | 誤抽出（id=`詳細:`） | **抽出しない** |
| `- [ ] さらに具体的な ...` | 誤抽出（id=`さらに具体的な`） | **抽出しない** |

### FR-W7-2: Assignee タグ抽出（MUST）

TasksParser は `tasks.md` の Task 行の description 末尾から `@<assignee>` タグを抽出し、
`TaskInfo.assignee` フィールドに格納する。詳細は元 design.md §5「Assignee タグ規約（Wave 7+ 追加）」に準拠する。

**MUST 項目**:
- 正規表現: `\s+@([A-Za-z0-9_-]+)\s*$`
- マッチした場合: `TaskInfo.assignee = <抽出値>`、description 本文からタグ部分を除去
- 未マッチの場合: `TaskInfo.assignee = "-"`（後方互換）

### FR-W7-3: V-4 Assignee 列表示の意味化（MUST）

`build_dashboard.py` は V-4 Task 一覧ビューの Assignee 列に、TasksParser が抽出した `TaskInfo.assignee` 値を表示する。

**MUST 項目**:
- `@` 接頭辞は除去（例: `@Sonnet` → 表示は `Sonnet`）
- 未指定（`-`）は従来通り `-` を表示

### FR-W7-4: V-2 複数 Milestone 一覧化（MUST）

V-2 Milestone 一覧ビューは、**`SessionStateParser` が SESSION_STATE.md 内のタスク ID（`W{wave}-B{milestone_num}-T{task}` 形式）から検出した複数の Milestone** を、すべて一覧表示する。

**MUST 項目**:
- 現状の単一エントリ表示（実体は単 Milestone のため 1 行のみ）から「検出された全 Milestone を縦に列挙」する形に拡張
- 表示順は Milestone 名の昇順（例: B-4 → B-5）
- 各 Milestone エントリには既存と同等の情報（名前 / Step / 状態）を含める
- **Step 列は `self.data.current_phase` を使用（全 Milestone 共通 / 現状仕様維持）** — Milestone 別の Step 管理は Wave 7 スコープ外（将来候補）

**実装基盤の確認**:
- `MilestoneInfo` は SessionStateParser が SESSION_STATE.md の Task ID から逆引きで構築する（既存実装）。
- `docs/specs/<dirname>/tasks.md` の glob 走査は元 design.md §5 の記述と実装が乖離している（既存の仕様ドリフト）が、Wave 7 では実装ベース（SessionStateParser）を SSOT とする。元 design.md の修正は将来の別タスク（chip `task_68008f88` 関連の仕様乖離整理と合わせて検討）。
- 結果として「V-2 に 2 件以上の Milestone が表示される」ためには SESSION_STATE.md に 2 件以上の Milestone を参照する Task ID が記述されている必要がある（現状: `W{n}-B5-T{n}` のみが多数 / `B4` は MAGI 議事録等のテキスト中言及はあるが Task ID 形式での出現は限定的）。Wave 7 内で SESSION_STATE.md への Milestone 言及拡充は Stage 4 の手動確認（T-S4-7）で対応する。

**MAGI A3 で却下した方式**:
- 横並び表示（option 1）: responsive 設計負荷大
- タブ切替（option 3）: 「並列」とは言いがたい
- フィルタトグル（option 2）: 後方互換で将来追加可能な設計のみ確保（Wave 7 実装スコープ外）

---

## §5 非機能要件（NFR）

### NFR-W7-1: CSS 予算管理（SHOULD / v0.2.4 改訂）

**継承履歴**: Wave 6 NFR-W6-3「追加 CSS ≤ 10 KB」継承（v0.1.0〜v0.2.3）→ **v0.2.4 で再評価上書き**
**次回再評価**: Milestone B-5 完了時 retro（NFR 寿命管理ルール準拠）

Wave 7 で CSS を追加する場合、追加前に CSS 合計サイズを事前計測し、目安内に収まることを確認する。

**SHOULD 項目**（v0.2.4 で MUST → SHOULD 降格）:
- 上限目安: **16,384 bytes（16 KiB）**（v0.2.4 で 10,240 → 16,384 / 1.6 倍に緩和）
- Wave 6 終端実測: 9,922 bytes（残 6,462 bytes）
- 1 Wave あたり ~300 bytes 成長率前提で約 20 Wave 分の改修余地を確保
- Stage 3（V-2 複数 Milestone 一覧化）で CSS 追加が発生する場合、設計段階で残予算内に収まる根拠を design.md に明記

**3 段階レベル制（v0.2.4 新設）**:

| レベル | 範囲 | 対応 |
|:------:|:-----|:-----|
| **緑帯** | < 11,469 bytes（70%） | 自由に追加可 |
| **黄帯** | 11,469 〜 14,745 bytes（70-90%） | Wave 開始時に CSS 追加見込みを記録 + 適宜縮退検討 |
| **赤帯** | ≥ 14,746 bytes（90%） | その Wave の retro で予算改定議題を **必須化** + 改定 or ミニマル化を選ぶ |

**MAY 項目**:
- 上限超過時は意匠の縮退 or 要件の縮小で対応（Wave 8+ への切り出しを優先検討）

**改定根拠**（v0.2.4）:
- Wave 7 Stage 3 着手で予算逼迫（残 18 bytes 想定）が顕在化 → MAGI 合議（AoT 5 Atom）で改定確定
- 旧上限 10,240 bytes は Wave 6 NFR-W6-3 のキリ番継承 / 技術根拠は薄い（dashboard.html は `file://` 配信のため CRP/TCP slow-start 制約は無関係）
- 16 KiB は業界相場（初期 CSS 50-150 KiB）に対しても依然ミニマル
- **MUST → SHOULD** は実害低（`file://`）を踏まえた緩和。ただし 3 段階レベル制で退行検知は維持
- 詳細: `docs/artifacts/2026-06-28-magi-nfr-w7-1-budget-revision.md`

**Wave 6 NFR-W6-3 との関係**: Wave 7 v0.2.4 で上書き継承（Wave 6 文書は更新せず歴史的記述として残す / Wave 8+ は本上書き値を使用）

> retro Wave 6 Try A4 の早期回収（上書きの上で完了扱い）。

### NFR-W7-2: Lighthouse Accessibility 退行防止（MUST）

Wave 6 で達成した Lighthouse Accessibility スコア **97** を Wave 7 終端で **95 以上**に維持する。

**MUST 項目**:
- Stage 4 で Lighthouse 計測を実施（snapshot モード / device=desktop）
- スコア < 95 となった場合は Stage 4 内で原因特定 + 修正

**MAY 項目（記録 monitoring）**:
- Best Practices / SEO / Agentic Browsing の Wave 7 終端スコアを記録する（Wave 6 終端: 100 / 60 / 50）。退行は **MUST 違反ではない** が、結果記録のうえで顕著な退行（≥ 10 ポイント低下）が見られた場合は将来の retro 候補とする。SEO と Agentic Browsing は dashboard 用途では適用外のため大幅な変動も許容（Wave 6 §11 と整合）。

### NFR-W7-3: pytest 全件 PASS 維持（MUST）

Wave 6 終端時点の pytest 367 PASS + 5 SKIP を、Wave 7 追加分も含めて全件 PASS で維持する。

**MUST 項目**:
- Stage 1〜3 各 Stage 末で pytest 全件実行 → 既存 PASS を退行させない
- 既存テストの緩和は **L1 事前承認必須**（L2 委譲ガードレール #2 適用）

### NFR-W7-4: 後方互換（MUST）

Wave 7 の変更は以下の後方互換を保つ:

- 既存 tasks.md（`@<assignee>` タグ未記入）は従来通り動作（`assignee="-"` 表示）
- 既存 Task ID 形式（`W{n}-B{n}-T{n}` / `T{n}`）は全件抽出継続
- 既存 V-2 ビューの単一 Milestone 表示は複数 Milestone 一覧化に自然移行（既存テストは可能な限り維持）

### NFR-W7-5: tasks.md パイロット運用（MUST / v0.2.3 改訂）

Wave 7 の tasks.md は新規格チェックボックス形式を採用する **パイロット運用** を行う。

> **義務レベル変更（v0.2.3）**: spec-critic 4 回目 Warning「SHOULD の NFR が MUST の AC-W7-3 の前提条件になっている矛盾」指摘を受け、SHOULD → **MUST** に昇格。AC-W7-3（MUST）達成の必須前提として位置付ける。

**MUST 項目**:
- Wave 7 tasks.md の本実装タスク（T44-T55 + T56）は `- [ ] W7-B5-T44: 既存テスト構造変更影響分析 @sonnet` 形式のチェックボックス行で記述する（表形式との並存可）
- T-S* 検証タスクは引き続き太字記法 `- [ ] **T-S1-1**: ...` を使用（TasksParser 抽出対象外 / design.md §2 維持）
- Wave 6 以前の tasks.md は terminology.md §5 移行猶予条項に従い旧表記維持（書き換え不要）
- TasksParser がディレクトリ再帰走査を実装した上で（T56）、Wave 7 tasks.md §3.5 を読み取れる状態にする

**MAY 項目**:
- 既存 tasks.md エントリへの遡及記入は実施しない（後方互換 / NFR-W7-4 と整合）
- Wave 8+ で全 tasks.md の新規格統一を別途検討

**根拠**: Wave 7 Stage 1 MAGI 合議（[2026-06-27-magi-wave7-stage1-pivot.md](../../../artifacts/2026-06-27-magi-wave7-stage1-pivot.md)）+ spec-critic 4 回目レビューで、AC-W7-3 達成のために (1) Wave 7 tasks.md 自身を新規格 Task ID 行で構成 + (2) TasksParser ディレクトリ再帰走査の両方が必要と確定。

---

## §6 アクセプタンス条件（AC）

### AC-W7-1: TasksParser 誤抽出ゼロ化（FR-W7-1 対応 / MUST）

`docs/specs/` 配下の全 tasks.md を対象に TasksParser を実行し、抽出された Task ID がすべて `W{n}-B{n}-T{n}` 形式または `T{n}` 形式である。

### AC-W7-2: Assignee タグ抽出動作（FR-W7-2 対応 / MUST）

TasksParser のテストにおいて、`- [ ] W7-B5-T44: 説明 @Sonnet` および `- [x] W7-B5-T44: 説明 @Sonnet` の両方の box 状態から `assignee="Sonnet"` が抽出される。`@<assignee>` 無しの行は `assignee="-"` で返る。

### AC-W7-3: V-4 Assignee 列の意味データ表示（FR-W7-3 対応 / MUST）

dashboard.html を生成し、V-4 ビュー内に少なくとも 1 件の意味ある Assignee 値（例: `Sonnet` / `Haiku` 等）が表示される。

### AC-W7-4: V-2 複数 Milestone 表示（FR-W7-4 対応 / MUST）

dashboard.html を生成し、V-2 ビュー内に **2 件以上の Milestone エントリ**（例: B-4 と B-5）が縦に並んで表示される。

**達成手段の補足**: SessionStateParser が SESSION_STATE.md の Task ID から Milestone を逆引きするため、SESSION_STATE.md に **2 件以上の Milestone を参照する Task ID** が記述されている必要がある。Stage 4 の T-S4-7 でユーザー確認時に必要なら SESSION_STATE.md に検証用 Task ID 行を追加する（運用作業）。

**Step 列の扱い**: 全 Milestone に同じ Step（current_phase）が表示されることは現状仕様（FR-W7-4 注記に基づく）であり、AC 違反ではない。

### AC-W7-5: CSS 予算遵守（NFR-W7-1 対応 / SHOULD / v0.2.4 改訂）

dashboard.html 生成後の CSS 合計サイズが **16,384 bytes（16 KiB）以下**である。緑帯（< 11,469 bytes / 70%）が望ましい。赤帯（≥ 14,746 bytes / 90%）到達時はその Wave の retro で予算改定議題を必須化する。

### AC-W7-6: Lighthouse Accessibility ≥ 95（NFR-W7-2 対応 / MUST）

Stage 4 で Lighthouse 計測し、Accessibility スコアが **95 以上**である。

### AC-W7-7: pytest 全件 PASS（NFR-W7-3 対応 / MUST）

Wave 7 終端で pytest 全件 PASS（既存 367 + Wave 7 追加分）。

### AC-W7-8: 後方互換（NFR-W7-4 対応 / MUST）

`@<assignee>` タグ未記入の既存 tasks.md エントリが従来通り表示される（`-` 表示で抽出失敗しない）。

### AC-W7-9: PoC レビュー（MUST / 客観基準 + 主観評価併用）

ユーザーが dashboard.html を実機確認し、起源 chip 3 件すべてが「解消」または「将来送り明示」となっている。

**chip ごとの解消の客観基準**（Stage 4 で確認）:

| chip | 客観基準（自動検証可能） | 主観評価ポイント |
|:-----|:----------------------|:----------------|
| `task_954a1e90`（TasksParser Task ID 誤抽出） | AC-W7-1 達成（誤抽出ゼロ化）で技術的には解消 | 実機確認で V-4 に「説明文の続き」のような非 Task 行が混入していないこと |
| `task_eec7ce2d`（V-4 担当者列無価値） | AC-W7-3 達成（≥ 1 件の意味値表示）で技術的には解消 | 実機確認で担当者列が dashboard の判断材料として機能していること |
| `task_52c46569`（複数 Milestone/Wave 並列対応） | AC-W7-4 達成（≥ 2 Milestone 表示）で技術的には解消 | 実機確認で「単一 Milestone のみ」よりも比較しやすくなったとユーザーが評価すること |

**客観基準と主観評価の関係**: 各 chip は客観基準を満たすことで AC 達成。主観評価は **Wave 8+ への送りタスクの起票判断**に使用する（不満足点があれば新規 chip 起票）。AC-W7-9 自体は「客観基準達成 + 主観評価のフィードバック取得」を達成条件とする。

---

## §7 既存仕様からの継承・差分

### 継承（変更なし）

- 元 `requirements.md` v0.2.0 の FR-1〜FR-11 / NFR-1〜6 / AC-1〜8 はすべて継承
- Wave 6 wave6/requirements.md v0.2.0 の FR-W6-1〜5 / NFR-W6-1〜3 / AC-W6-* はすべて継承（既存挙動維持）
- 元 design.md §5「Assignee タグ規約」（commit `4448d4c`）はすべて SSOT として継承

### 差分（Wave 7 追加）

- FR-W7-1〜4（本文書 §4）
- NFR-W7-1〜4（本文書 §5）
- AC-W7-1〜9（本文書 §6）

### 上書き（変更あり）

- TasksParser の Task 抽出 regex を厳格化（FR-W7-1）→ 既存テストのうち緩い regex を前提とするものは事前影響分析の上で更新
- V-2 ビューの表示構造を「単一 Milestone」から「複数 Milestone 一覧」に拡張（FR-W7-4）→ 既存 V-2 テストの一部は更新が必要

---

## §8 Wave 7 内部 Stage 分割（情報）

MAGI 合議（2026-06-27）で確定した 4 Stage 構成:

| Stage | 内容 | 対応 FR/NFR | 主担当層 |
|:------|:-----|:-----------|:--------|
| Stage 1 | TasksParser Task ID 誤抽出修正 | FR-W7-1 | Sonnet（L2） |
| Stage 2 | Assignee タグ規約の実装 | FR-W7-2, FR-W7-3 | Sonnet（L2） |
| Stage 3 | 複数 Milestone 一覧化 | FR-W7-4, NFR-W7-1 | Sonnet（L2） |
| Stage 4 | 統合テスト + Lighthouse + PoC レビュー | NFR-W7-2, NFR-W7-3, AC-W7-5〜9 | L1 統括 + Haiku 採点 |

### Stage ゲート条件（各 Stage 末の確認事項）

- 該当 FR/NFR の AC 達成
- pytest 全件 PASS（NFR-W7-3）
- 既存テスト緩和が発生した場合は L1 承認済（L2 委譲ガードレール #2）
- ship + push 完了

---

## §9 将来候補（Wave 8+ への送り）

- 複合担当タグ（`@L2:Sonnet @L3:Haiku` 等）
- Wave→担当の自動推定
- 複数 Milestone のフィルタトグル（option 2 実装）
- 複数 Milestone の横並び表示（option 1）
- Milestone フィルタ仕様乖離（chip `task_68008f88`）
- CSS の意匠面の大幅見直し

---

## §10 PM 確定回答記録

### 2026-06-27: requirements.md v0.1.0 承認

PM（ユーザー）が本要件書 v0.1.0 を Approved。design.md 起稿に進行。

### 2026-06-27: 3 文書セット v0.2.1 PM 最終承認

ユーザー（PM）が requirements.md v0.2.1 + design.md v0.2.1 + tasks.md v0.2.1 の 3 文書セットを一括承認。
spec-critic 3 回独立レビュー結果（C → B → B → A 想定）を反映済。BUILDING フェーズ遷移可。
次の主担当: Stage 1（T44 影響分析 → T45 regex 厳格化 → T46 既存テスト更新）。

### 2026-06-27: spec-critic 独立レビュー結果（v0.2.0 改訂）

spec-critic から Critical 4 件 / Warning 6 件 / Info 4 件 / 総合 C 評価の指摘を受領。
本要件書への反映項目:
- #C-2（V-2 Step 表示のデータソース未定義）→ FR-W7-4 に「Step は全 Milestone 共通（current_phase）」明記
- #C-4（承認ステータス不整合）→ ステータスを「Conditional Approved / 3 文書セット PM 最終承認待ち」に変更
- #W-5（Lighthouse 他項目の閾値）→ NFR-W7-2 に MAY 項目（記録 monitoring）追加
- #W-6（PoC 客観基準）→ AC-W7-9 に chip ごとの客観基準テーブル追加
- #I-2（[<box>] 表記）→ AC-W7-2 を `[ ]` / `[x]` 具体例に統一

design.md / tasks.md にも v0.2.0 改訂で連動。3 文書セットでの PM 最終承認を依頼。

### 2026-06-27: Wave 7 スコープ確定（MAGI 合議結果）

| 質問 | 回答 |
|:-----|:----|
| Wave 7 スコープ | (C): #1 Assignee タグ規約 + #2 TasksParser 修正 + #3 複数 Milestone 一覧化 |
| 着手順序 | #2 → #1 → #3 → 統合 |
| Stage 分割 | 4 Stage（Wave 6 リズム踏襲） |
| 並列対応方式 | option 4（全 Milestone 一覧化）+ フィルタは後方互換で追加可能設計 |
| design.md §5 切り出し | しない（wave7/design.md は追加事項のみ） |

→ 詳細議事録: [2026-06-27-magi-wave7-planning.md](../../../artifacts/2026-06-27-magi-wave7-planning.md)

### 2026-06-27: v0.2.2 補追承認（Wave 7 Stage 1 MAGI Pivot 反映）

Wave 7 Stage 1 BUILDING 着手時に T45 実装後の pytest 検証で発覚した「design.md §6 新 regex 仕様と実 tasks.md 運用の構造的乖離」に対し、MAGI 合議（[2026-06-27-magi-wave7-stage1-pivot.md](../../../artifacts/2026-06-27-magi-wave7-stage1-pivot.md)）でスコープ縮小 + パイロット運用方針を確定。本要件書への補追:

- NFR-W7-5 新規追加（tasks.md パイロット運用 / SHOULD）
- ステータスを v0.2.2 Approved（PM 補追承認）に更新

design.md / tasks.md にも v0.2.2 で連動補追。

### 2026-06-27: v0.2.3 補追承認（spec-critic 4 回目レビュー反映）

v0.2.2 補追を spec-critic 4 回目に独立レビューさせた結果、Critical 3 件（うち 1 件は実機確認で昇格）+ Warning 4 件 + Info 3 件の指摘を受領。MAGI 4 Atom Reflection でも検出できなかった「実装コードとの整合性」盲点が露呈。本要件書への補追:

- NFR-W7-5 を SHOULD → **MUST** 昇格（spec-critic Warning「SHOULD の NFR が MUST の AC-W7-3 の前提条件」矛盾解消）
- ステータスを v0.2.3 Approved（PM 補追承認）に更新
- design.md §6 / §10.5 / §14 + tasks.md §3 / §3.5 / §6 で連動補追（T56 追加 / 達成依存チェーン明示 / §3 §3.5 同期ルール明示 等）

詳細な指摘内容と対処マッピングは design.md §13 v0.2.3 補追承認記録を参照。

### 2026-06-28: v0.2.4 補追承認（NFR-W7-1 CSS 予算根本見直し）

Wave 7 Stage 3 BUILDING 着手時に予算逼迫（残 18 bytes 想定）が顕在化。L1 が「予算根拠そのものの再検討」を提起し、AoT 5 Atom MAGI 合議で NFR-W7-1 を根本改定。本要件書への補追:

- **NFR-W7-1 を MUST → SHOULD 降格** + **上限 10,240 → 16,384 bytes**（1.6 倍緩和）
- **3 段階レベル制（緑/黄/赤）導入** — 退行検知は維持
- 継承履歴タグと次回再評価タイミング（Milestone B-5 完了 retro）を明示
- Wave 6 NFR-W6-3 を上書き継承（Wave 6 文書は歴史的記述として維持）
- ステータスを v0.2.4 Approved（PM 補追承認）に更新

design.md / tasks.md / execution-plan.md にも v0.2.4 で連動補追。
関連 knowledge: `docs/artifacts/knowledge/nfr-lifecycle-management.md`（NFR 寿命管理ルール新設）
詳細議事録: `docs/artifacts/2026-06-28-magi-nfr-w7-1-budget-revision.md`

---

## §11 upstream-first 裏取りステータス

| 対象 | 実在性確認 | LAM 適合性 | 備考 |
|:-----|:----------|:----------|:----|
| Python `re` 正規表現（`^W\d+-[A-Z]\d+-T\d+$`） | ✅（Python 標準ライブラリ） | ✅ | 既存実装で同種 regex を使用中 |
| `\s+@([A-Za-z0-9_-]+)\s*$`（Assignee タグ） | ✅（design.md §5 で裏取り済） | ✅ | 既存 design に承認済 |
| Lighthouse snapshot モード | ✅（Wave 6 Stage 4 で実証） | ✅ | file:// URL 対応確認済 |
| chrome-devtools-mcp `lighthouse_audit` | ✅（Wave 5/6 で実証） | ✅ | 既存利用パターン継続 |

---

## §12 Definition of Ready チェックリスト

- [x] 起源 chip 3 件すべて特定（task_eec7ce2d / task_954a1e90 / task_52c46569）
- [x] スコープ確定（MAGI 合議で (C) 確定）
- [x] Stage 分割確定（4 Stage / Wave 6 リズム踏襲）
- [x] 並列対応方式確定（option 4 / フィルタは将来対応）
- [x] design.md §5 既存（Assignee タグ規約のたたき台）
- [x] L2 委譲ガードレール 4 点（knowledge）
- [x] design.md v0.2.1 起稿（spec-critic 3 回レビュー反映済 / Conditional Approved）
- [x] tasks.md v0.2.1 起稿（spec-critic 3 回レビュー反映済 / Draft）
- [x] PM 最終承認（**2026-06-27 ユーザーが 3 文書セット v0.2.1 を一括承認** → BUILDING 遷移可）

---

## §13 権限等級

- 本要件書の変更: **PM 級**（仕様変更）
- AC 追加・修正: **PM 級**
- 表記の微調整・typo 修正: **PG 級**

---

## §14 参照

- [元 design.md §5](../design.md#assignee-タグ規約wave-7-追加--rfc-2119-should)
- [MAGI 議事録 2026-06-27](../../../artifacts/2026-06-27-magi-wave7-planning.md)
- [retro Wave 6](../../../artifacts/retro-W6-B5-2026-06-27.md)
- [L2 委譲ガードレール](../../../artifacts/knowledge/l2-delegation-guardrails.md)
- [phase-rules](../../../../.claude/rules/phase-rules.md)
- [code-quality-guideline](../../../../.claude/rules/code-quality-guideline.md)
- [planning-quality-guideline](../../../../.claude/rules/planning-quality-guideline.md)

---

## §15 改訂履歴

| バージョン | 日付 | 変更内容 |
|:----------|:-----|:--------|
| 0.1.0 | 2026-06-27 | 初版起稿 — MAGI 合議結果（2026-06-27）に基づく FR/NFR/AC 定義 |
| 0.2.0 | 2026-06-27 | spec-critic 独立レビュー指摘の反映 — FR-W7-4 Step 共通明記 (#C-2) / NFR-W7-2 MAY 項目追加 (#W-5) / AC-W7-2 表記統一 (#I-2) / AC-W7-4 達成手段補足 / AC-W7-9 chip 客観基準テーブル追加 (#W-6) / ステータス Conditional Approved (#C-4) |
| 0.2.0+1 | 2026-06-27 | spec-critic 再レビュー（v0.2.0 → B 評価）指摘のインライン補記 — §12 DoR チェックリスト v0.2.0 反映 (#NI-2) / design.md 連動: §8 Opt 4 表記修正 (#NI-1) / tasks.md 連動: T51 昇順ソート実装明示 (#NW-2), T53 モックフィクスチャ方針 (#NW-1), T-S3-4 B-3 表記修正 (#NW-3), 内部参照を v0.2.0 に更新 |
| **0.2.1** | 2026-06-27 | spec-critic 再々レビュー（v0.2.0+1 → B 維持）指摘の追加補記 + バージョン正式 bump — FR-W7-1 regex を Wave 1.5 形式 `W\d+(?:\.\d+)?-[A-Z]\d+-T\d+` に拡張（**継続懸念解消 / terminology.md §2 準拠**） / design.md 連動: §6 regex 拡張 + エッジケース表 (Wave 1.5 / W10) 追加, §3 A3-4 にソート方式（文字列辞書順）と将来 (B-10 以降の数値順) 切替方針明示 (#NW4) / tasks.md 連動: T53 §6 にフィクスチャ実装具体例追加 (#NW-1 完全解消) / DoR と参照を v0.2.1 に統一 (#NI-2 / #NI4 解消) |
| **0.2.2** | 2026-06-27 | Wave 7 Stage 1 BUILDING 着手時の構造的乖離発覚に対する MAGI 合議結果反映 — NFR-W7-5 新規追加（tasks.md パイロット運用 / SHOULD）/ §10 に v0.2.2 PM 補追承認記録 / ステータスを Approved（v0.2.2 補追承認）に更新 / design.md §6 補足 + §10.5 パイロット運用ルール追加 / tasks.md §3.5 V-4 表示用チェックボックス行追加で連動 / 根拠議事録: `2026-06-27-magi-wave7-stage1-pivot.md` |
| **0.2.3** | 2026-06-27 | spec-critic 4 回目レビュー（v0.2.2 補追の独立レビュー）指摘の反映 — NFR-W7-5 を SHOULD → MUST 昇格（spec-critic Warning「SHOULD/MUST 矛盾」解消）/ §10 に v0.2.3 PM 補追承認記録 / design.md §6 + §10.5 + §13 + §14 + tasks.md §3 + §3.5 + §6 で連動補追（T56 ディレクトリ走査再帰化 + AC-W7-3 達成依存チェーン明示 + §3/§3.5 同期ルール明示 + Stage 3 ゲート T-S3-4 conditional pass 基準明示 等）|
| **0.2.4** | 2026-06-28 | Stage 3 着手時の CSS 予算逼迫を契機とした NFR-W7-1 根本見直し — MUST → SHOULD 降格 / 上限 10,240 → 16,384 bytes / 3 段階レベル制（緑/黄/赤）導入 / 継承履歴タグ + 再評価タイミング明示 / §10 に v0.2.4 PM 補追承認記録 / design.md §8 + tasks.md §3 / §7 + execution-plan.md §6 / §8 で連動補追 / knowledge 記録新設（NFR 寿命管理）/ 議事録: `2026-06-28-magi-nfr-w7-1-budget-revision.md` |
