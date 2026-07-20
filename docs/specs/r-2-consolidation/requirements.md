# R-2 Milestone Requirements: 資産整理 (rule 整備 / 文書精度 / 環境健全化)

## メタ情報

| 項目 | 内容 |
|:-----|:-----|
| Milestone | R-2 (Refactoring シリーズ 2 回目) |
| ステータス | Draft (承認待ち) |
| 作成日 | 2026-07-20 |
| 更新日 | 2026-07-20 |
| 起源 | R-1 Milestone retro (`docs/artifacts/retro-R1-2026-07-18.md` §Step 3 Try) の T4〜T26（23 件）消化 |
| SSOT | 本ファイル |
| 意思決定記録 | HGA #15（2026-07-20 / Fable 5 裁定 / Crux A・B・C + 非 crux 即決 3 件） |
| 一次整理素材 | `docs/artifacts/r-2-planning-material-2026-07-20.md`（非 SSOT・入力素材） |
| 関連ルール | `.claude/rules/auto-generated/trust-model.md` / `.claude/rules/auto-generated/rule-001.md` / `.claude/rules/planning-quality-guideline.md` |

---

## 1. 概要

### 1.1 背景（Problem Statement）

R-1 Milestone retro（2026-07-18）は Step 3 Try として 23 件（T4〜T26）の未消化課題を残した。内訳は rule 化候補 5 件（T4〜T8）、文書精度 6 件（T9〜T14）、個別 Task 化 12 件（T15〜T26）である。これらは R-1 期の監査・実装を通じて実際に発生した問題（parser drift の再発・cp932 エンコーディング罠・KPI 定義の 2 Wave 連続未決着 等）から抽出されており、放置すると同型の問題が R-2 以降も再発する。

一方で R-1 期は 21 Stage 粒度・独立監査 Wave・Stage 単位 ship 義務という重量級の進行管理を採用しており、PM 級承認イベントが頻発した。R-2 では「必要な資産整理は完遂しつつ、承認密度を圧縮する」ことが同時に要求される。

### 1.2 ユーザーストーリー

```
As a LAM プロジェクト運用者 (L1 統括 = Living Architect),
I want R-1 retro が残した rule 化候補・文書精度課題・個別課題を、
   承認イベントを圧縮した進行管理のもとで消化する Milestone,
So that TDD 内省パイプラインの信頼度モデルが同型ドリフトを検出できる状態になり、
   かつ次 Milestone 以降の承認設計を実測データで検討できる基盤が整う.
```

### 1.3 スコープ

**含む（3 Wave 固定 / HGA #15 Crux A 準拠）**:

| Wave | 名称 | 内容 |
|:----:|:-----|:-----|
| W1 | 基盤 | T20（venv 依存突合 script。W1 先頭・全 rule 化候補 Task に先行完了） → trust-model 2 条項（カウント単位定義 + N 回目発火時の恒久解検討必須化条項） → rule 化候補 5 件（T4〜T8。うち T7 は機構を伴わない配置判定 Task であり Done 形式は FR-8/FR-10 に従う — L1 裁定 2026-07-20） |
| W2 | 文書精度 | T9〜T14（文書精度 6 件） + 対策 B（`planning-quality-guideline.md` への暗黙前提明示化リスト条項の追加） |
| W3 | 個別消化 + 監査 + retro | 残余の個別 Task（T15, T17, T22〜T25）+ T26（pending 記録）+ 最終検証（G1-G5 維持確認）+ Milestone retro を終端 Stage に畳み込む。独立監査 Wave は設けない |

Wave 数は 3 で固定する（FR-1）。Wave 追加は Milestone 再計画として扱い、PM 承認を要する。

**含まない（Non-Goals）**:

- **T16（fable-l3 × Fable-Alembic snapshot 統合方針）**: retro 自身が「Alembic 現行運用への影響大 = 独立 Milestone 化推奨」と明記しており、HGA #15 裁定により R-2 内では判定すら行わない。次 Milestone 以降の議題として送る（「独立 Milestone 化するか否か」の判定作業自体も R-2 スコープ外）
- **T26（Alembic 判断依頼への応答）**: Alembic 側の応答が前提であり LAM 側の裁量で完結しない。pending 記録のみを残し、R-2 の Definition of Done は本項目の解決に依存しない
- **T11（CHEATSHEET Rules 一覧の完全化）**: retro 推奨が「現状維持（完全化は不要）」であり、R-2 では「現状維持の確認」自体を成果として許容する。完全化作業は行わない
- **T18 / T19 / T21**: 2026-07-20 セッション内で先行消化済み（`pyproject.toml` testpaths 追加 / `r1_cycle_detect.py` inventory fallback 見直し / pytest 同名モジュール衝突解消）。R-2 requirements の対象から除外する
- **新規機能開発**: R-2 は資産整理専用であり、新規機能の追加は対象外（B-6 以降）
- **rule-001 の再改訂**: rule-001（SESSION_STATE.md fallback 保守）は R-1 で拡張済であり、本 Milestone での再改訂は対象外（rule-002 は新設対象だが rule-001 とは独立）

### 1.4 3 Wave 固定の意図（承認密度の圧縮）

R-1 の 21 Stage 粒度・独立監査 Wave・Stage 単位 ship 義務は R-2 では採用しない。一方、各 Wave 冒頭の K5 一括承認方式（PM 級ファイル編集計画を一括宣言し、承認 1 回で残りを自律消化する方式）は維持する。これにより PM 級承認イベント目標を 4±1 回（各 Wave 冒頭の K5 宣言 3 回 + trust-model 改訂の単独承認 1 回）に設定する（NFR-3）。

---

## 2. 用語

| 用語 | 定義 |
|:-----|:-----|
| **R-2** | 本 Milestone の識別子（`terminology.md` §1 Milestone 層）。Refactoring シリーズの 2 回目 |
| **W1 / W2 / W3** | R-2 内の Wave（`terminology.md` §1 Wave 層）。それぞれ「基盤」「文書精度」「個別消化+監査+retro」を指す固有名 |
| **検証イベント** | 1 回の独立した検証活動の実行。具体的には次のいずれか 1 実行を 1 イベントと数える: HGA 召喚 1 回 / gabriel probe 1 回 / 監査 Stage (subagent 監査バッチ) 1 回 / `/retro` パターン分析 1 回 / テスト実行での FAIL→PASS 遷移記録 1 セッション。同一セッション内でも独立した検証実行が複数あれば別イベントとする（例: HGA #9 と HGA #10 は近接日の別召喚 = 2 イベント） |
| **検出イベント単位** | trust-model.md のパターン発火カウント方式。**1 検証イベント内で検出された issue は件数によらず 1 カウント**とし、カウントの加算は検証イベントが異なる場合にのみ行う（セッション・日付は補助識別子であり判定基準ではない）。rule-001 の実績カウント（4 イベント = 2026-06-27 / 07-05 / 07-06 / 07-07 の各検証実行）および rule-002 候補のカウント（3 イベント = HGA #9 / HGA #10 / W-R5 監査）と遡及一貫する。本単位を trust-model.md の正式定義とする（FR-4） |
| **K5 一括宣言方式** | 各 Wave 冒頭で、当該 Wave 内で編集予定の PM 級ファイル一覧を一括宣言し、ユーザー承認 1 回を得たうえで Wave 内の残り編集を自律的に進める進行管理方式（R-1 由来 / R-2 で維持） |
| **機構を伴う Task** | rule 化・script 化・regex/検査系の実装を伴う Task。R-2 での該当は **T4, T5, T6, T8, T20 の 5 件（この列挙で閉じる）**。Done 判定に正例・誤例・grep baseline を要求する（FR-7）。T7 は配置判定 + スキーマ文書化であり機構を伴わないため対象外（FR-8/FR-10 適用 — L1 裁定 2026-07-20） |
| **純規範文書 Task** | 文書の記述・方針明確化・調査のみで完結する Task（T7, T9〜T14, T17, T22〜T25）。Done 判定は検証手段 1 つで足りる（FR-8） |
| **PM 級承認密度** | 1 Milestone 期間中に発生する PM 級ダイアログ（`permission-levels.md` 準拠）の実績回数。R-2 では目標値 4±1 を設定し、retro で実績と目標の差分を分析する（NFR-3） |

---

## 3. 機能要求 (FR)

FR は HGA #15（2026-07-20 / Fable 5 裁定）の Crux A（構造）・Crux B（trust-model）・Crux C（Done 形式）・T20 裁定・非 crux 即決 3 件から導出する。RFC 2119 準拠。骨格・番号・レベルは HGA #15 正本を無改変で採用する。

### FR-1: R-2 は 3 Wave 固定 (MUST)

**説明**: R-2 は W1「基盤」/ W2「文書精度」/ W3「個別消化+監査+retro」の 3 Wave で構成する。Wave の追加は Milestone の再計画に相当し、PM 承認を要する。R-1 の 21 Stage 粒度・独立監査 Wave・Stage 単位 ship 義務は踏襲しない。

**受け入れ条件**:
- [ ] `docs/specs/r-2-consolidation/tasks.md` が W1/W2/W3 の 3 Wave のみで構成されている（4 番目以降の Wave が存在しない）
- [ ] Wave 追加が必要と判明した場合、tasks.md 変更として PM 級承認ゲートを通過している
- [ ] 独立監査 Wave が存在しない（監査・最終検証は W3 の終端 Stage に統合されている）

**優先度**: MUST

### FR-2: 各 Wave 冒頭で PM 級ファイル編集計画を一括宣言し、承認 1 回で残りを自律消化する (MUST)

**説明**: K5 一括宣言方式を採用する。各 Wave の着手前に、当該 Wave で編集予定の PM 級ファイル（`docs/specs/` / `docs/adr/` / `.claude/rules/` / `.claude/settings*.json`）一覧を一括宣言し、ユーザーの承認判断を 1 回得たうえで Wave 内の残り編集を自律的に進める。K5 一括宣言は**プロセス慣行**であり、`permission-levels.md` の機構を変更するものではない: 個々の PM 級ファイルへの**初回** Edit ダイアログは宣言後もファイルごとに発生し得るが、宣言済み一覧に基づきユーザーは個別判断なしで承認できる（同一ファイル 2 回目以降はセッションスコープ降格機構により SE 級降格 = ダイアログ非表示）。承認密度の計測は NFR-3 の定義（宣言イベント単位）に従う。

**受け入れ条件**:
- [ ] tasks.md の各 Wave 冒頭セクションに「本 Wave で編集する PM 級ファイル一覧」フィールドが存在する
- [ ] 各 Wave の一括宣言と承認取得の記録が Wave 実施中は SESSION_STATE.md に残り、Milestone retro（VCS 管理下）に永続化される
- [ ] Wave 内で当初宣言に含まれない新規 PM 級ファイルへの編集が必要になった場合、追加宣言 + 承認を経ている

**優先度**: MUST

### FR-3: 同一 PM 級ファイルへの編集 Task は同一 Wave・同一セッションに集約配置する (SHOULD)

**説明**: FR-2 のセッションスコープ降格機構を最大限活用するため、同一 PM 級ファイル（例: `trust-model.md`）を対象とする複数 Task は、可能な限り同一 Wave・同一セッション内に配置する。Wave をまたいだ同一ファイルの分割編集は、降格機構が働かず承認回数が増えるため避ける。「同一セッション」は努力目標である: Wave が複数セッションにまたがった場合、セッション再開後の初回 PM 級 Edit でダイアログが再発生することは本 SHOULD の違反とせず、NFR-3 のダイアログ実数記録に反映する。

**受け入れ条件**:
- [ ] tasks.md 上で、同一 PM 級ファイルを対象とする Task が同一 Wave 内にグルーピングされている
- [ ] 同一ファイルへの編集が複数 Wave にまたがる場合、tasks.md に理由が明記されている（例: Wave 間の依存関係上やむを得ない場合）

**優先度**: SHOULD

### FR-4: trust-model.md にカウント単位定義（検出イベント単位）を追加する (MUST)

**説明**: `.claude/rules/auto-generated/trust-model.md` に、パターン発火のカウント単位を「検出イベント単位」（§2 用語 参照）として明記する条項を追加する。現行 trust-model.md には「同一パターン 2 回以上」という閾値記述はあるが、1 回の発火をどう数えるかの定義（1 セッション内の複数 issue を 1 カウントとするか、issue 数分カウントするか）が欠落しており、rule-002 起票の可否判定が曖昧になっている。

**受け入れ条件**:
- [ ] trust-model.md に「検出イベント単位」を定義する条項が新設されている
- [ ] 条項には「同一セッション/検証イベントで検出された複数 issue = 1 カウント」の定義が明記されている
- [ ] rule-001 の実績カウント（異セッション日付単位 4 回: 2026-06-27 / 2026-07-05 / 2026-07-06 / 2026-07-07）が新定義と遡及的に整合することが確認できる（矛盾がある場合は理由を注記する）

**優先度**: MUST

### FR-5: trust-model.md に N 回目発火時の恒久解検討必須化条項を追加する (MUST)

**説明**: R-1 retro P11 の教訓（同一パターンが 3 回目発火した際に fallback regex を場当たり的に拡張するのではなく、構造的な恒久解を検討すべきだった事例）を trust-model.md に条項として明文化する。閾値到達後も同型の応急措置が繰り返される場合、N 回目（例: 3 回目）の発火時点で恒久解（regex 汎化・構造変更等）の検討を必須化する。

**受け入れ条件**:
- [ ] trust-model.md に「N 回目発火時の恒久解検討必須化」条項が新設されている
- [ ] 条項は rule-001.md の「拡張の根拠 (2026-07-06 / R-1 W-R1 S1 T6)」節を具体事例として参照している
- [ ] N の初期値は **3** とし、条項に明記されている（rule-001 実績 = 3 回目発火で恒久解実施、と整合。変更は trust-model.md 改訂 = PM 級）

**優先度**: MUST

### FR-6: rule-002 の起票は FR-4/FR-5 の完了後とする (MUST)

**説明**: rule-002（verify_reference_resolution 系 + GitHistoryParser regex の同型 parser drift 予防 rule）の起票は、trust-model.md の 2 条項（FR-4, FR-5）が承認・反映された後に行う直列依存とする。カウント単位が未定義のまま rule-002 を起票すると、起票根拠（検出イベント 3 回 = 閾値 2 超過）の妥当性が検証不能になるため。

**受け入れ条件**:
- [ ] FR-4 / FR-5 の trust-model.md 改訂が承認・merge 済であることを rule-002 起票時点で確認できる（Git commit 履歴で順序が確認できる）
- [ ] rule-002 の起票文書（`.claude/rules/auto-generated/rule-002.md` 相当）に、FR-4 の検出イベント単位定義に基づくカウント根拠（HGA #9 = 2026-07-06 / HGA #10 = 2026-07-07 / W-R5 監査 = 2026-07-15 の 3 検出イベント。出典: `docs/artifacts/hga-summon-log.md` #9/#10 行 + `docs/artifacts/r-1-audit-tracker.md` R1-054〜058, R1-061）が記載されている
- [ ] rule-002 は rule-001 の兄弟ルールとして独立制定される（rule-001 への統合はしない）

**優先度**: MUST

### FR-7: 機構を伴う Task の Done は正例 + 誤例列挙 + 既存違反 grep baseline の 3 点を含む (MUST)

**説明**: rule 化 5 件（T4〜T8）・T20（script 化）・その他 regex/検査系の実装を伴う Task の Done 判定は、以下 3 点を **すべて** 満たすことを必須とする: (1) 正例（rule/検査を満たすケース）の列挙、(2) 誤例（rule/検査に違反するケース）の列挙、(3) 既存コードベースに対する grep 実測での違反件数 baseline。Fable→Opus 実装ギャップ 3 事例（`fable-spec-opus-implementation-gap.md` 参照）に共通する「正例だけでは検証できない暗黙前提」への直接対策として、誤例の明示を必須化する。

**受け入れ条件**:
- [ ] T4（rule-002）・T5（subprocess encoding rule）・T6（gabriel 契約 strict enum）・T8（mode enum 拡張）・T20（venv 依存突合 script）の各 Done 記述に、正例・誤例・grep baseline の 3 点が個別に記載されている
- [ ] 誤例が実際に検査・rule を fail させることが確認されている（例: 意図的に誤例を投入して検査が検出することを実測する）
- [ ] grep baseline は Task 着手前の既存違反件数として記録され、Task 完了後の再計測値と比較可能な形式である

**優先度**: MUST

### FR-8: 純規範文書 Task の Done は検証手段 1 つを含む (SHOULD)

**説明**: 純規範文書 Task（§2 用語準拠: T7, T9〜T14, T17, T22〜T25）の Done 判定は、機構を伴う Task ほど厳密な 3 点セットを要求せず、検証手段 1 つ（実コマンドによる確認、または初見読者としての 60 秒実況）で足りるものとする。W3 の個別 Task（T17, T22〜T25）にも本 FR を準用する（各 Task の Done 基準の帰属を明確化する — spec-critic C5 対応）。

**受け入れ条件**:
- [ ] T9（requirements.md 参照の § 見出し化）・T10（ADR supersede 明記）・T12（表 re-numbering 規則明文化）・T13（成果物ファイル命名規則明文化）・T14（"N 件相当" 表現の説明義務）・T7・T17・T22・T23・T24・T25 の各 Done 記述に、検証手段が 1 つ以上明記されている
- [ ] 検証手段は「実コマンドで確認可能（コマンドを Done 記述に明記）」または「初見読者として 60 秒実況し違和感がないことを確認」のいずれかの形式である

**優先度**: SHOULD

### FR-9: T20 突合 script は全 rule 化 Task に先行完了する (MUST)

**説明**: T20（venv 依存完全性突合 script。`.venv/Scripts/pip list` と `pyproject.toml` の突合）は W1 の先頭 Task として位置づけ、T4〜T8 の rule 化 Task 着手前に完了させる。独立 Wave（Wave 0）は設けず、順序制約のみを課す。

**受け入れ条件**:
- [ ] tasks.md 上で T20 が W1 の最初の Task として配置されている
- [ ] T4〜T8 の各 Task 定義に「T20 完了後に着手」の前提条件が明記されている
- [ ] T20 の実装が独立 Wave として扱われていない（W1 の一部として実施される）

**優先度**: MUST

### FR-10: gabriel-metrics はスキーマ文書を VCS 上の SSOT とし、log 本体は gitignore を維持する (MUST)

**説明**: `.claude/gabriel-metrics.log` は gitignore 対象のまま維持する（環境間で個別に蓄積されるログ本体は commit しない）。一方、そのスキーマ定義（フィールド名・型・記録タイミング）は VCS 化された文書を SSOT として整備する。これにより担保されるのは**集計方法論の裏取り可能性**（どのフィールドをどう数えるかの契約）であり、個別環境の実測値（例: 「4 entries」）そのものの環境間検証は本 FR のスコープ外とする（HGA #15 裁定: 守るべきはフィールド契約であってデータではない）。

**受け入れ条件**:
- [ ] gabriel-metrics のスキーマ定義文書が `docs/` 配下（VCS 管理下）に新規作成または既存文書への統合で存在する（配置パスは tasks.md で確定 — §7 参照）
- [ ] `.claude/gabriel-metrics.log` が引き続き `.gitignore` に含まれている
- [ ] スキーマ文書は log 本体の**全フィールドを網羅**する（2026-07-20 時点の実測フィールド: timestamp / session_id / mode / gate_decision / invoked / gabriel_output {verdict, severity, affected_atoms_count, recommended_action, confidence} / resolved_action / retry_count / elapsed_ms / opt_out / phase / subject / anchor / hga_summon_ref）。網羅性は実 log 1 entry との突合で検証する

**優先度**: MUST

### FR-11: evaluation-kpi.md §7 を削除する (MUST)

**説明**: `evaluation-kpi.md` §7 は W-R4 S3 retro（Problem 継続）→ R-1 Milestone retro（P9 として再掲）と 2 段階で先送りされてきた未決着事項である。HGA #15 裁定 + ユーザー同意（2026-07-20）により、§7 を完全削除する。§2〜§6 は無変更とする。参照状況は 2026-07-20 に grep で実測済: §7 を仕様として参照する現行文書はゼロ（ヒットは全て過去時点の記録文書 = tracker / retro / deletions であり、時点記録として更新不要）。

**受け入れ条件**:
- [ ] `evaluation-kpi.md` から §7 が削除されている
- [ ] §2〜§6 の内容が変更されていない（diff で確認可能）
- [ ] 削除 Task 実施時に §7 参照の grep を再実行し、新規の仕様参照が 0 件であることを確認する。**仕様参照が発見された場合は削除を保留し、参照元の扱いを PM 級判断に差し戻す**（contingency 条項）

**優先度**: MUST

### FR-12: R-2 の Definition of Done は外部応答（Alembic 等）に依存しない (MUST)

**説明**: T26（Alembic 判断依頼への応答）は LAM 側の裁量で完結しない継続議題である。R-2 の Definition of Done は T26 の解決を条件としない。T26 については、応答待ちである旨の pending 記録のみを残し、R-2 スコープからは除外する。

**受け入れ条件**:
- [ ] T26 に関する pending 記録（応答待ちであることの明記）が `docs/artifacts/` 配下に存在する
- [ ] R-2 requirements.md / tasks.md のいずれにも T26 完了を DoD の必要条件とする記述がない
- [ ] R-2 Milestone COMPLETE 判定時、T26 の状態（pending のまま）が明記されている

**優先度**: MUST

### FR-13: 対策 B（暗黙前提明示化リスト条項）を planning-quality-guideline.md に追加する (SHOULD)

**説明**: Fable→Opus 実装ギャップ問題（`fable-spec-opus-implementation-gap.md`）の対策として、`.claude/rules/planning-quality-guideline.md` に「暗黙前提明示化リスト」条項を追加する。設計書・仕様書起草時に、実装者が暗黙裡に補う必要のある前提（正例のみからは読み取れない境界条件・除外条件等）をリスト化して明示することを求める条項とする。本条項は R-1 retro の T-item に直接由来せず、HGA #15 裁定による新規追加である。

**受け入れ条件**:
- [ ] `planning-quality-guideline.md` に「暗黙前提明示化リスト」条項が新設されている
- [ ] 条項は Fable→Opus 実装ギャップの具体事例（`fable-spec-opus-implementation-gap.md` 参照）を根拠として引用している
- [ ] 条項が FR-7（誤例列挙必須化）と整合している旨が明記されている（両者は同一問題への異なる層での対策であるため）

**優先度**: SHOULD

### FR-14: 文書精度 6 件（T9〜T14）を消化する (SHOULD)

**説明**: W2 で T9（requirements.md § 見出し参照）・T10（ADR supersede 明記）・T11（CHEATSHEET Rules 一覧）・T12（表 re-numbering 規則明文化）・T13（成果物ファイル命名規則明文化）・T14（"N 件相当" 表現の説明義務）を消化する。T11 は「現状維持の確認」を成果として許容する（完全化作業は不要）。

**受け入れ条件**:
- [ ] T9, T10, T12, T13, T14 それぞれについて、FR-8 準拠の Done（検証手段 1 つ）を満たした成果物が存在する
- [ ] T11 については「現状維持が妥当である」ことの確認記録（Task 完了記録）が存在し、CHEATSHEET.md 自体への変更を伴わない
- [ ] T12, T13 の成果は `terminology.md` への § 追加という形式で反映されている

**優先度**: SHOULD

### FR-15: 全 Wave で G1 基準（980 passed / regression 0）を維持する (MUST)

**説明**: R-2 期を通じて、2026-07-20 時点の baseline（980 passed + 15 skipped / commit `4ab85b8` / testpaths 拡大後）から退行しないことを維持する。テスト追加は許容し、テスト削除は PM 級承認を要する。

**受け入れ条件**:
- [ ] 各 Wave 末で `pytest` 実行結果が 980 PASS 以上（+ 15 SKIP 相当）を維持している
- [ ] テスト削除が発生した場合、PM 級承認済であることが確認できる
- [ ] R-2 期間中に regression（既存 PASS テストの FAIL 化）が発生していない

**優先度**: MUST

---

## 4. 非機能要求 (NFR)

### NFR-1: Zero-Regression Policy 維持 (MUST)

**説明**: `CLAUDE.md` § Core Principles の Zero-Regression Policy に従い、R-2 期の全変更は変更前に最も遠いモジュールへの影響をシミュレーションし、実装とドキュメントを同一の不可分な単位として更新する。

**受け入れ条件**:
- [ ] rule 化候補 Task（T4〜T8, T20）は、変更対象 rule/script を参照する他ファイル（SKILL.md / 他 rules / hooks）への影響が確認されている
- [ ] 文書精度 Task（T9〜T14）は、変更対象文書を参照する他文書への影響（リンク切れ・矛盾）が確認されている
- [ ] 削除・配置変更を伴う Task（T15 = FR-11 / T7 = FR-10 / T26 = FR-12）および W3 個別 Task（T17, T22〜T25）は、変更対象を参照する他文書・他機構への影響が Task 完了記録内で確認されている

**優先度**: MUST

### NFR-2: Python 3.8 互換性維持 (MUST)

**説明**: `CLAUDE.md` § Python Invocation Convention の Python バージョン SSOT（`pyproject.toml` `requires-python = ">=3.8"`）に従い、R-2 期に新規追加する**全ての** Python コード（R-2 で予定される新規は T20 突合 script のみ。予定外の新規 script が発生した場合も同様）は 3.8 互換を維持する。

**受け入れ条件**:
- [ ] T20 突合 script に `from __future__ import annotations` が付与されている（runtime subscript generics 回避）
- [ ] `match` / `except*` / dict merge (`|`) 等の 3.10+ 構文が使用されていない
- [ ] `str.removesuffix` 等の 3.9+ 専用 API が使用されていない（使用する場合は `endswith` + slice で代替する）

**優先度**: MUST

### NFR-3: PM 級承認密度の管理 (SHOULD)

**説明**: R-2 期の**承認イベント**を目標 4±1 回に収める。ここでの承認イベントは **K5 一括宣言に対するユーザーの承認判断の回数（宣言イベント単位）** であり、`permission-levels.md` の PM 級ダイアログ表示実数とは区別する（ダイアログはファイル初回 Edit ごとに発生し得るが、宣言済み一覧の範囲内であれば 1 宣言 = 1 承認判断と数える）。想定内訳: 各 Wave 冒頭の K5 一括宣言 3 回 + trust-model.md 改訂の単独承認 1 回。

**受け入れ条件**:
- [ ] R-2 期間中の承認イベント（宣言イベント単位）実績回数と、PM 級ダイアログ表示実数の**両方**が記録されている
- [ ] Milestone retro で承認イベント実績と目標（4±1）の差分、およびダイアログ実数との乖離が分析されている（DoD-4）
- [ ] 目標を超過した場合、超過理由が記録されている（理由の形式は自由記述とし、Wave 追加による超過は FR-1 の PM 承認記録と相互参照する）

**優先度**: SHOULD

---

## 5. 成功基準 (Definition of Done)

R-2 Milestone COMPLETE の判定条件（HGA #15 DoD 骨格 5 条項をそのまま採用）:

- [ ] **DoD-1**: 全 3 Wave（W1〜W3）が Green State（FR-15 準拠）+ ship + push 済で完了している（退行なし）
- [ ] **DoD-2**: trust-model.md の 2 条項（FR-4, FR-5）+ rule-002（FR-6）が PM 承認済で merge されている
- [ ] **DoD-3**: rule 化候補 5 件（T4〜T8）すべてが各自の Done 形式を実測でクリアしている — T4/T5/T6/T8 は FR-7 形式（正例 + 誤例列挙 + grep baseline / 誤例が実際に検査を fail させることの確認を含む）、T7 は FR-8 形式 + FR-10 受け入れ条件（L1 裁定 2026-07-20: T7 は機構を伴わないため。HGA #15 DoD 骨格の「FR-7 形式」を機構有無で 2 分割する精密化であり骨格の趣旨は不変）
- [ ] **DoD-4**: PM 承認イベント実績数が Milestone retro で記録され、目標 4±1（上限 5）との差分が分析されている（R-3 以降の承認設計の実測基盤とする）
- [ ] **DoD-5**: T26 の pending 記録が存在し、R-2 の DoD が T26 の解決に非依存であることが明文化されている。加えて R-2 Milestone retro が実施済である

---

## 6. 素材トレーサビリティ

R-1 retro Try 群 23 件（T4〜T26）全件について、対応する FR または Non-Goals 該当区分を以下に示す（WBS 100% Rule 準拠 / 素材 23 件が本節で FR に紐づくか Non-Goals で除外明記されるかのいずれかであることを検証する）。

| ID | 内容（要約） | 対応 FR / 区分 |
|:--:|:-------------|:----------------|
| T4 | rule-002 化検討（parser drift 予防） | FR-4, FR-5, FR-6, FR-7 |
| T5 | subprocess encoding 統一 rule | FR-7（機構を伴う Task の Done 形式）/ W1 rule 化 5 件の一つ |
| T6 | gabriel 契約厳密検査昇格 | FR-7（機構を伴う Task の Done 形式）/ W1 rule 化 5 件の一つ |
| T7 | gabriel-metrics.log 環境非依存化 | FR-10, FR-8（Done 形式 / 機構を伴わない — L1 裁定 2026-07-20）/ W1 で実施 |
| T8 | mode enum 拡張 | FR-7（機構を伴う Task の Done 形式）/ W1 rule 化 5 件の一つ |
| T9 | requirements.md 参照は § 見出しで | FR-14, FR-8 |
| T10 | ADR-0008/0004 supersede 明記 | FR-14, FR-8 |
| T11 | CHEATSHEET Rules 一覧完全化 | Non-Goals（§1.3）+ FR-14（現状維持確認として許容） |
| T12 | 表 re-numbering 規則明文化 | FR-14, FR-8 |
| T13 | 成果物ファイル命名規則 | FR-14, FR-8 |
| T14 | "N 件相当" 表現の説明義務 | FR-14, FR-8 |
| T15 | evaluation-kpi.md §7 最終判定 | FR-11 |
| T16 | fable-l3 × Fable-Alembic snapshot 統合方針 | Non-Goals（§1.3 / 判定自体もスコープ外） |
| T17 | R1-037 followup（foreman tools: plain Agent 化） | W3 個別消化 / Done 形式は FR-8 準用（専用 FR なし） |
| T18 | Stop hook G1 testpaths | Non-Goals（2026-07-20 先行消化済） |
| T19 | r1_cycle_detect.py default inventory 挙動 | Non-Goals（2026-07-20 先行消化済） |
| T20 | venv 依存完全性突合 script | FR-9, FR-7 |
| T21 | pytest 同名モジュール衝突 | Non-Goals（2026-07-20 先行消化済） |
| T22 | retro skill argument default 動作（低優先度・調査のみ） | W3 個別消化 / Done 形式は FR-8 準用（専用 FR なし） |
| T23 | deletions.md schema template 化 | W3 個別消化 / Done 形式は FR-8 準用（専用 FR なし） |
| T24 | subagent boundary に scratchpad 書込禁止明示 | W3 個別消化 / Done 形式は FR-8 準用（専用 FR なし） |
| T25 | built-in `/code-review ultra` 起動候補未表示（調査） | W3 個別消化 / Done 形式は FR-8 準用（専用 FR なし） |
| T26 | Alembic 判断依頼（継続議題） | FR-12, Non-Goals（§1.3） |
| — | 対策 B（暗黙前提明示化リスト条項） | FR-13（T-item 起源ではなく HGA #15 裁定による新規追加） |

**検証**: 23 件（T4〜T26）のうち、T16/T18/T19/T21/T26 は Non-Goals で明示除外、T4〜T15/T20 は個別 FR に対応、T17/T22/T23/T24/T25 は専用 FR を持たないが **Done 形式は FR-8 を準用**し（FR-8 受け入れ条件に明記済）、Wave 構造・承認方式は FR-1/FR-2 に従う = 孤児タスクではない。全 23 件について漏れ・孤児がないことを確認した。

---

## 7. 未解決質問 (Red)

HGA #15 正本の骨格・内容は変更せず、以下は design.md / tasks.md の後続工程で確定すべき事項として記録する。**本節の全項目は tasks.md 承認（= PLANNING 完了）までに解決し、Red を残したまま BUILDING に進まない**（`planning-quality-guideline.md` §6 準拠 — spec-critic W6 対応）。

- [ ] FR-3「同一 Wave・同一セッションに集約配置」で、Wave 間の依存関係上やむを得ず分割する場合の判断基準が未確定（tasks.md で個別 Task の依存グラフ確定時に判断）
- [ ] FR-10 のスキーマ定義文書の具体的な配置パス（`docs/artifacts/gabriel-metrics-schema.md` 新規か、既存 gabriel 系文書への追記か）が未確定（tasks.md で確定）
- [ ] FR-13 対策 B の具体的な条項文言（リスト形式 / チェックリスト形式）が未確定。`planning-quality-guideline.md` の既存条項形式（Requirements Smells の危険な単語リスト）に倣うことを推奨するが、確定は design/tasks 工程に委ねる
- [ ] W3「個別消化」の Task 順序（T17, T22〜T25 の実施順）が未確定（tasks.md で SPIDR 分割時に決定）
- [ ] T9（§ 見出し参照化）の対象文書リスト（hardcoded L 番号参照を含む参照元 = final-audit-report / closure-report を想定）が未列挙（tasks.md で grep 実測により確定 — spec-critic I5 対応）

> 注記: 初版に含まれていた「NFR-3 の承認イベントカウント方法の曖昧さ」は、NFR-3 本文の改訂（宣言イベント単位とダイアログ実数の区別を定義）により解決済み（spec-critic C6 対応）。

---

## 8. 参照

- `docs/artifacts/retro-R1-2026-07-18.md` §Step 3 Try（T4〜T26 の原記述）
- `docs/artifacts/r-2-planning-material-2026-07-20.md`（一次整理素材 / 非 SSOT）
- `.claude/rules/auto-generated/trust-model.md`（FR-4, FR-5 の改訂対象）
- `.claude/rules/auto-generated/rule-001.md`（rule-002 の兄弟ルールとしての参照点）
- `.claude/rules/planning-quality-guideline.md`（FR-13 の追加対象）
- `.claude/rules/permission-levels.md`（FR-2, NFR-3 の承認密度管理の根拠）
- `docs/artifacts/fable-spec-opus-implementation-gap.md`相当（FR-7, FR-13 の根拠事例。ユーザー auto-memory 内参照）
- `docs/specs/large-scale-review/requirements.md`（R-1 Milestone requirements / 構成参考元）
- `docs/specs/tdd-introspection-v2.md`（trust-model の上位仕様）

---

## 9. 変更履歴

| 日付 | 変更者 | 内容 |
|:-----|:-------|:-----|
| 2026-07-20 | L2 (Sonnet) | 初版起草（HGA #15 裁定 FR-1〜FR-15 骨格の忠実展開 + 素材トレーサビリティ + 未解決質問） |
| 2026-07-20 | L1 (spec-critic 反映) | spec-critic Critical 6 / Warning 7 / Info 6 の反映: T7 の Wave/Done 帰属確定（W1 実施 + FR-8/FR-10 形式 = C1/W7）/ §1.3 W3 の T15 二重記載除去（C2）/ 検証イベントの操作的定義 + カウント論理明確化（C3）/ HGA #9/#10 出典明記（C4）/ W3 個別 Task の FR-8 準用明記（C5）/ K5 = プロセス慣行の明確化 + NFR-3 宣言イベント単位定義（C6）/ §6 素材件数 20→23 訂正（W1）/ 「等」の閉集合化 3 箇所（W2）/ NFR-1 受け入れ条件の全 Task 被覆（W3）/ FR-11 grep 実測根拠 + contingency 条項（W4）/ FR-10 担保範囲の精密化（W5）/ §7 Red の PLANNING 内解決宣言（W6）/ FR-5 N=3 確定（I1）/ FR-3 セッション努力目標化（I2）/ FR-2 記録の retro 永続化（I3）/ T9 対象文書の Red 化（I5） |
