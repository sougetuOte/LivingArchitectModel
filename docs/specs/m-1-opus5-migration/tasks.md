# M-1 Milestone Tasks: Opus 5 移行 + 規律の条項トリアージ

## メタ情報

| 項目 | 内容 |
|:-----|:-----|
| Milestone | M-1 |
| ステータス | **Approved**（2026-07-25 / ユーザー承認 / 起票時検証 1 件反映後） |
| 作成日 | 2026-07-25 |
| requirements | [requirements.md](./requirements.md)（Approved 2026-07-25 / FR 21 / NFR 6 / DoD 6） |
| design | [design.md](./design.md)（Approved 2026-07-25 / 741 行 / §11 に Red 解決記録） |
| 起源 | ADR-0011（Accepted 2026-07-25） |
| SPIDR 分割 | 垂直分割（Wave 内で全層貫通）+ Paths 分割（W1 は Phase A / Phase B で経路分割） |
| WBS 100% Rule | 全 FR/NFR がタスクに対応（§10 トレーサビリティ表） |
| 命名規約 | `W<n>-M1-T<m>`（Wave n / Task m / `terminology.md` §4 準拠） |
| 起票者 | L1 直（design に決定が書き切られた写像作業のため委譲しない） |

**NFR-6 の明示的遵守**: 本ファイルには**削減率・削減行数の下限を完了条件とする記述を一切置かない**。W4 のベースライン再測定結果は報告するが、それ自体を DoD 判定条件として使わない（NFR-6 受け入れ条件 1, 3）。

---

## 1. Wave / Task 対応表（全体一覧）

**構成**: Task 33 件（W0 7 / W1 7 / W2 9 / W3 5 / W4 5）+ ゲート 1 件。Wave 数は 5（W0〜W4）で固定する（FR-1）。

| Wave | Task ID | 内容 | 対応 FR | 担当層 | 規模 |
|:----:|:--------|:-----|:--------|:------:|:----:|
| **W0** | W0-M1-T1 | 委譲 TDD 記録盲点の probe（経路 (a)/(b) 切り分け） | FR-8 前提 | L1 + Sonnet | M |
| **W0** | W0-M1-T2 | probe 結果に基づく機構修正 / スコープ外送りの確定 | FR-8 前提 | Sonnet | M |
| **W0** | W0-M1-T3 | ベースライン測定 6 項目（W0 起点） | FR-8 | Haiku | M |
| **W0** | W0-M1-T4 | 削減台帳スケルトン作成（7 列 / ヘッダのみ） | FR-7 | L1 | S |
| **W0** | W0-M1-T5 | upstream 一次資料の裏取り（Opus 5 / Fable 5） | FR-19 | L1 | M |
| **W0** | W0-M1-T6 | ADR-0001 突合 + requirements FR-20 説明文の訂正 | FR-20 | Haiku + L1 | M |
| **W0** | W0-M1-T7 | W0 完了判定（順序制約 + 記録完全性の確認） | FR-8 | Haiku | S |
| **W1** | W1-M1-T1 | 条項抽出 + 条項 ID 付与（3 ファイル ≈750 行） | FR-4 | Sonnet | L |
| **W1** | W1-M1-T2 | 追加入力 2 カテゴリの組込み（閉集合確定 / 計 6 件） | FR-21, FR-4 | L1 | S |
| **W1** | W1-M1-T3 | 不変制約 4 対象の除外 + ガード 2 引用範囲の grep 検証 | FR-5 | Haiku | M |
| **W1** | W1-M1-T4 | Phase A: veto 先行スクリーニング（軸 1 → 軸 3） | FR-4, FR-6 | **L1** | L |
| **W1** | W1-M1-T5 | Phase B: 残り精査（SSOT 退避 + 決定木 4 分岐） | FR-4, FR-6 | **L1** | L |
| **W1** | W1-M1-T6 | トリアージ表の PM 級一括承認（K5 / 1 承認イベント） | FR-6, FR-3 | L1 | S |
| **W1** | W1-M1-T7 | W1 末測定 + 安定性ゲート判定入力の収集 | FR-8, FR-2 | Haiku | M |
| **—** | **ゲート** | **Opus 5 安定性ゲート（W1 → W2 / 3 条件）** | **FR-2** | **L1** | **S** |
| **W2** | W2-M1-T1 | `model-roster.md` 新設（4 項目 + ADR-0001 関係明記） | FR-10, FR-14 | Sonnet | M |
| **W2** | W2-M1-T2 | SSOT 退避の実行（2 ファイル → roster / 参照のみ残す） | FR-10 | Sonnet | M |
| **W2** | W2-M1-T3 | `CLAUDE.md` のモデル ID 直書き除去 + 導線追加 | FR-11 | Sonnet | M |
| **W2** | W2-M1-T4 | `verify_model_reference.py` 新規実装（3 分岐 / TDD） | FR-12, NFR-4, NFR-5 | Sonnet | L |
| **W2** | W2-M1-T5 | トリアージ判定の適用 + 削減台帳への全件記録 | FR-6, FR-7 | Sonnet | L |
| **W2** | W2-M1-T6 | HGA 召喚ゲート改訂（事後条件化 + 移行期規定） | FR-15 | Sonnet | M |
| **W2** | W2-M1-T7 | R-2 W2/W3 再スコープの実行（3 分岐写像 → 反映） | FR-21 | L1 + Sonnet | M |
| **W2** | W2-M1-T8 | `trust-model.md` への接続（復活経路 / 新規実装なし） | FR-9 | Sonnet | S |
| **W2** | W2-M1-T9 | W2 末測定 + 件数突合（トリアージ表 vs 削減台帳） | FR-7, FR-8 | Haiku | M |
| **W3** | W3-M1-T1 | 対象再実測（9 件）+ 上位 4 件確定 + FR-16 訂正 | FR-16 | Haiku + L1 | M |
| **W3** | W3-M1-T2 | progressive disclosure 化の実施（上位 4 件）+ 動作確認 | FR-16 | Sonnet | L |
| **W3** | W3-M1-T3 | `quality-auditor` × `code-reviewer` 重複判定（2 指標） | Red-3 | **L1** | M |
| **W3** | W3-M1-T4 | ADR-0010 I-1〜I-6 適合確認 | FR-17 | Haiku | M |
| **W3** | W3-M1-T5 | W3 末測定 + **未着手 5 件の明記** | FR-8, FR-16 | Haiku | S |
| **W4** | W4-M1-T1 | `update-model` skill 作成（6 ステップ）+ 整合検証 pytest | FR-13, FR-14 | Sonnet | L |
| **W4** | W4-M1-T2 | ベースライン再測定（W4）+ W0 比較 | FR-8, DoD-4 | Haiku | M |
| **W4** | W4-M1-T3 | 配布カタログ作成（7 列） | FR-18 | Sonnet | M |
| **W4** | W4-M1-T4 | 配布実行（2 経路 / **直前にユーザー承認**） | FR-18 | **L1** | M |
| **W4** | W4-M1-T5 | Milestone retro（4 項目の記録） | DoD-6 | L1 | M |

---

## 2. 順序制約（FR-8 / FR-1 / FR-2）

本 Milestone には**破ってはならない順序制約が 3 本**ある。いずれも「先に進むと比較対象・判定入力が永久に失われる」不可逆性を持つ。

### 制約 1: W0 ベースライン測定 → W2 着手（FR-8 / MUST）

```
W0-M1-T3（ベースライン測定 6 項目）完了
    ↓ ← この線を越える前に W2 の Task に着手してはならない
W1（判定のみ）→ ゲート → W2（規律本体の適用）
```

W0-M1-T3 が未完了の状態で W2-M1-T1 以降に着手した場合、圧縮・削減の効果を比較する起点が失われる（不可逆）。**W2 の全 Task は W0-M1-T3 の完了記録（`docs/artifacts/m-1-baseline-w0.md`）の存在を着手前提とする**（FR-8 受け入れ条件 3）。

### 制約 2: 計器較正 → ベースライン測定（FR-8 前提 / design §4.5）

```
W0-M1-T1（probe）→ W0-M1-T2（修正 or スコープ外送りの確定）
    ↓ ← 測定項目 3 の意味が確定してから測る
W0-M1-T3（ベースライン測定 6 項目）
```

`.claude/tdd-patterns.log` は委譲 TDD を記録しないことが 2026-07-25 retro §3 で観測確定している。盲目の計器のまま W0 と W4 を比較すると、差分は条項トリアージの効果ではなく委譲率の副産物になる（design §4.1 項目 3）。

### 制約 3: W1 判定 → W2 適用（FR-6 / MUST）

```
W1（判定のみ / 圧縮・削減を一切実行しない）→ W1-M1-T6（PM 級一括承認）
    ↓ ← 承認前の適用は禁止
W2-M1-T5（適用の実行）
```

W1 中にトリアージ対象条項の圧縮・削減を実行してはならない（FR-6 受け入れ条件 2）。

### 依存グラフ（Wave 内）

```
W0: T1 → T2 → T3 → { T4, T5, T6 } → T7
W1: T1 → T2 → T3 → T4 → T5 → T6 → T7
     （T2 は T1 と並行着手可 / 表への行追加のみ）
ゲート: W1-M1-T7 の測定値を入力として判定
W2: T1 → { T2, T3 } → T4 → T5 → { T6, T7, T8 } → T9
     （T5 は W1-M1-T6 の承認済みトリアージ表を入力とする）
W3: T1 → T2 → { T3, T4 } → T5
W4: { T1, T3 } → T2 → T4 → T5
     （T4 配布実行は T2 の regression 確認完了後 / ユーザー承認必須）
```

---

## 3. W0: 準備

### 本 Wave で編集する PM 級ファイル一覧（K5 一括宣言）

> **注記（design §3.2 の補完）**: design §3.2 の PM 級編集計画表は W1〜W4 の行のみを持ち W0 行を欠く。しかし W0-M1-T6 は `requirements.md`（`docs/specs/` 配下 = PM 級）の訂正を含むため、FR-3 受け入れ条件 1（各 Wave 冒頭に PM 級ファイル一覧フィールドが存在すること）を満たすよう本節で補完する。

- [ ] `docs/specs/m-1-opus5-migration/requirements.md`（FR-20 説明文の実測値訂正 / W0-M1-T6）

**条件付き（probe 結果依存 / 追加宣言で扱う）**:

- [ ] `.claude/rules/auto-generated/trust-model.md` または `.claude/rules/` 配下のいずれか（W0-M1-T2 の修正が hook 側ではなく**規約側**に及ぶ場合のみ）

probe（W0-M1-T1）を実行するまで修正先が確定しないため、規約側修正が必要と判明した時点で**追加宣言 + 承認**を経る（FR-3 受け入れ条件 3）。

---

### W0 詳細タスク

#### **W0-M1-T1**: 委譲 TDD 記録盲点の probe（経路 (a)/(b) 切り分け）

**概要**: `.claude/tdd-patterns.log` が委譲 TDD（Sonnet subagent 内の Red-Green）を記録しない原因を、経路 (a)（PostToolUse hook が subagent の Bash 呼び出しで発火しない）と経路 (b)（`-o addopts=""` により JUnit XML が更新されず hook が前回の green XML を読む）に切り分ける。

**対応仕様**: design.md §4.5 手順 1 / retro §5.3-1（A1）/ requirements.md FR-8

**完了条件**:
- [ ] 意図的に 1 件失敗する pytest を用意する（tmp 配下の使い捨てテスト / リポジトリに commit しない）
- [ ] Sonnet subagent に `-o addopts=""` **あり**で実行させ、`.claude/tdd-patterns.log` への追記有無と `.claude/test-results.xml` の mtime 変化を観測する
- [ ] Sonnet subagent に `-o addopts=""` **なし**で実行させ、同じ 2 点を観測する
- [ ] 上記 2 通りの観測結果から経路 (a) / (b) / 両方 のいずれかを判定する
- [ ] 判定と観測値（mtime の before/after、log の行数 diff）を `docs/artifacts/m-1-baseline-w0.md` に記録する
- [ ] probe 用の使い捨てテストを削除し、`git status` がクリーンであることを確認する

**判定の読み方**:

| `-o addopts=""` | XML mtime | log 追記 | 示唆 |
|:---------------:|:---------:|:--------:|:-----|
| あり | 変化なし | なし | 経路 (b)（XML が更新されない） |
| なし | 変化あり | なし | 経路 (a)（hook 自体が発火しない） |
| なし | 変化あり | あり | 経路 (b) 単独（規約側の見直しで解決） |

**依存**: なし（W0 先頭 / M-1 全体の先頭）

**担当想定**: L1（probe 設計・観測判定）+ Sonnet（probe 実行体 = 委譲経路の再現に subagent 実行が必須）

**規模**: M

---

#### **W0-M1-T2**: probe 結果に基づく機構修正 / スコープ外送りの確定

**概要**: W0-M1-T1 の判定に応じて hook 側（subagent 実行時の JUnit XML パス分離等）または規約側（`-o addopts=""` 運用の見直し）を修正する。**既存機構の修正であり、新規の帳簿・新規ログファイル・新規集計スクリプトは追加しない**（NFR-2）。

**対応仕様**: design.md §4.5 手順 2, 3 / requirements.md NFR-2, NFR-4, NFR-5

**完了条件**:
- [ ] probe 判定に対応する修正を実施する（hook 側 or 規約側 / 両方の場合は両方）
- [ ] 修正後に W0-M1-T1 と同一の probe を再実行し、`tdd-patterns.log` に FAIL エントリが記録されることを確認する
- [ ] Python コードを変更した場合、NFR-4（3.8 互換）/ NFR-5（`encoding="utf-8", errors="replace"`）に準拠する
- [ ] 修正内容と再 probe の結果を `docs/artifacts/m-1-baseline-w0.md` に記録する
- [ ] **不成立時の確定**: 上記で盲点が解消しない場合、修正を M-1 スコープ外へ送り、§4.1 測定項目 3 を参考値扱い（DoD-4 の判定条件から除外）とすることを**本 Task 内で確定させる**（W1 以降へ持ち越さない / design §4.5 不成立時の扱い）

**依存**: W0-M1-T1 完了後

**担当想定**: Sonnet（TDD）

**規模**: M

**検証コマンド**:

```bash
bash .claude/scripts/py_invoke.sh -m pytest .claude/tests/hooks/
```

---

#### **W0-M1-T3**: ベースライン測定 6 項目（W0 起点）

**概要**: design §4.1 が定める 6 項目を実測し `docs/artifacts/m-1-baseline-w0.md` に記録する。3 層安全網の第 1 層。

**対応仕様**: design.md §4.1 / requirements.md FR-8, NFR-3

**完了条件**:
- [ ] 項目 1（pytest 全数）: `bash .claude/scripts/py_invoke.sh -m pytest` の PASS/FAIL/SKIP を記録。NFR-3 の起点（commit `2ac4e91` / 1043 passed + 14 skipped）と突合する
- [ ] 項目 2（Green State 件数）: R-2 W1 末ゲート記録の Critical / Warning 件数を転記する
- [ ] 項目 3（`tdd-patterns.log` FAIL→PASS 率）: `trust-model.md` §パターン照合ロジックと同一手順で手動集計。**W0-M1-T2 の結果が「不成立 = 参考値扱い」の場合はその旨を明記する**
- [ ] 項目 4（gabriel verdict 分布）: `gabriel-metrics-environment-2026-07-05.md` §集計例の jq を用い、`invoked=true` を母数に confirmed / refuted / inconclusive を集計する
- [ ] 項目 5（PM 級ダイアログ発火数）: W0 時点は M-1 着手前のためゼロを記録する
- [ ] 項目 6（`CLAUDE.md` + rules 文字数）: `cat CLAUDE.md .claude/rules/*.md .claude/rules/*/*.md | wc -m`
- [ ] 6 項目すべてが `docs/artifacts/m-1-baseline-w0.md` に記載されている（欠落ゼロ）
- [ ] 新規の集計スクリプト・新規ログファイルを追加していない（NFR-2）

**依存**: W0-M1-T2 完了後（**順序制約 2 / 計器較正が先行**）

**担当想定**: Haiku（実行 + 結果パース + 構造化報告）

**規模**: M

---

#### **W0-M1-T4**: 削減台帳スケルトン作成（7 列 / ヘッダのみ）

**概要**: `docs/artifacts/m-1-clause-ledger.md` をヘッダ行のみの空表として作成する。データ行の記入は W2-M1-T5 で行う。

**対応仕様**: design.md §4.2, §6.3 / requirements.md FR-7, NFR-2

**完了条件**:
- [ ] `docs/artifacts/m-1-clause-ledger.md` が作成されている
- [ ] 列が 7 種（条項ID / 原文 / 出典（ファイル:節）/ 判定軸（軸1〜4の値）/ 判定（圧縮・削減・SSOT退避）/ 移動先 / 判定日）で構成されている
- [ ] 冒頭に「**本台帳は記録表であり、成果物の合否を判定する帳簿ではない**（帳簿単一原則 / 成果物判定は Green State 1 冊のみ）」が明記されている（NFR-2 受け入れ条件 1）
- [ ] W0 時点でデータ行はゼロ

**依存**: なし（T3 と並行可）

**担当想定**: L1 直（1 ファイル新規 / 委譲 overhead > 効果）

**規模**: S

---

#### **W0-M1-T5**: upstream 一次資料の裏取り（Opus 5 / Fable 5）

**概要**: `upstream-first.md` §確認手順に準拠し、Opus 5 および Fable 5 の公式スペック（context window / 価格 / リリース日）を一次資料で確認する。

**対応仕様**: design.md §4.3 / requirements.md FR-19

**完了条件**:
- [ ] context7 で Opus 5 / Fable 5 の公式スペックを検索する
- [ ] context7 で取得できない項目は WebFetch にフォールバックする（**対話モードでのみ実行** / `upstream-first.md` 注意書き）
- [ ] 取得した各値を一次資料の URL・取得日とともに `docs/artifacts/m-1-baseline-w0.md` に記録する
- [ ] 取得できなかった項目は「**未確認**」と明記し、断定しない（FR-19 受け入れ条件 2）
- [ ] 記録結果を W2-M1-T1（`model-roster.md` §単価・envelope）へ転記する旨を記録に明示する

**依存**: なし（T3 と並行可）

**担当想定**: L1 直（WebFetch が対話モード限定のため委譲不可）

**規模**: M

---

#### **W0-M1-T6**: ADR-0001 突合 + requirements FR-20 説明文の訂正

**概要**: `.claude/agents/*.md` の `model:` frontmatter 実測と ADR-0001 §改訂履歴の記述を突合し、drift の有無を確定する。あわせて requirements FR-20 説明文の実測値誤りを訂正する。

**対応仕様**: design.md §4.4 / requirements.md FR-20

**完了条件**:
- [ ] `grep -n "^model:" .claude/agents/*.md` を実行し全 12 ファイルの値を一覧化する
- [ ] design §4.4 の 2026-07-25 実測（**sonnet 9 / haiku 3 / 不明 0** / `command`・`fable` は未検出）と一致するかを再確認する
- [ ] **不一致 (i)**: requirements.md FR-20 説明文の「sonnet 8 / haiku 3 / 不明 1」を実測値へ訂正する（**PM 級編集** / K5 宣言済）
- [ ] **不一致 (ii)**: ADR-0001 §改訂履歴の `command` / `fable` 混在記述が実ファイルに存在しないこと（ADR 側 drift）を記録し、「ADR-0001 への時点注記追加」か「実ファイル修正」かを **PM 級判断で決定**する
- [ ] 判定結果を `docs/artifacts/m-1-baseline-w0.md` に記録する

**依存**: なし（T3 と並行可 / ただし requirements 訂正は W0 K5 承認後）

**担当想定**: Haiku（grep 実測 + 突合表の作成）+ L1（PM 級判断・requirements 訂正）

**規模**: M

---

#### **W0-M1-T7**: W0 完了判定（順序制約 + 記録完全性の確認）

**概要**: W0 の成果物が揃い、順序制約 1・2 が満たされたことを確認して W1 着手可否を判定する。

**対応仕様**: §2 順序制約 / requirements.md FR-8, NFR-3

**完了条件**:
- [ ] `docs/artifacts/m-1-baseline-w0.md` に測定 6 項目 + probe 判定 + upstream 裏取り + ADR-0001 突合の 4 種の記録がすべて存在する
- [ ] `docs/artifacts/m-1-clause-ledger.md` が 7 列ヘッダで存在する
- [ ] pytest 再実行で regression ゼロ（W0 起点比で PASS 数が減っていない / NFR-3）
- [ ] 測定項目 3 の扱い（実測値 / 参考値）が **W0 完了時点で確定している**（W1 以降へ持ち越していない）

**依存**: W0-M1-T3 / T4 / T5 / T6 完了後

**担当想定**: Haiku（事実突合 + 構造化報告）

**規模**: S

---

## 4. W1: トリアージ（判定のみ・適用しない）

### 本 Wave で編集する PM 級ファイル一覧（K5 一括宣言）

**なし**。トリアージ表は `docs/artifacts/m-1-triage-table.md`（SE 級）へ出力し、W1 中は PM 級ファイルへの実編集を行わない。

W1 の承認イベントは「**PM 級ファイルの編集予定一覧の宣言**」ではなく「**トリアージ表という決定内容の承認**」である（design §3.2 末尾 / §5.4）。この形式差は R-2 の K5 運用と異なるため、W1-M1-T6 の承認プロンプトで「本 Wave はファイル編集を行わず、トリアージ表の承認のみを求める」旨を明示する。

> **W1 中の禁止事項（FR-6 / MUST NOT）**: トリアージ対象条項の圧縮・削減・SSOT 退避を W1 中に実行してはならない。適用はすべて W2-M1-T5 に分離する。

---

### W1 詳細タスク

#### **W1-M1-T1**: 条項抽出 + 条項 ID 付与（3 ファイル ≈750 行）

**概要**: `fable-l3-protocol.md`（234 行）+ `phase-rules.md`（245 行）+ `CLAUDE.md`（269 行）から規範文を抽出し、条項 ID を付与してトリアージ表の行を生成する（判定列は空のまま）。

**対応仕様**: design.md §5.1（Red-1 解決 = 1 条項 = 1 規範文）/ requirements.md FR-4

**条項の定義（design §5.1 / 閉集合）**:
1. RFC 2119 キーワード: `MUST` / `MUST NOT` / `SHOULD` / `SHOULD NOT` / `MAY`
2. 日本語の規範表現: 「禁止」「必須」「してはならない」「〜すること」「〜を要する」「〜に従う」

**完了条件**:
- [ ] 一次スクリーニング（grep）を実行する:

  ```bash
  grep -cE "MUST NOT|MUST|SHOULD NOT|SHOULD|MAY|禁止|必須|してはならない|すること|を要する|に従う" \
    .claude/rules/fable-l3-protocol.md .claude/rules/phase-rules.md CLAUDE.md
  ```

- [ ] **各ヒット行を Read で確認し「規範文か文脈か」を個別判定**する（grep 結果をそのまま条項数としない）
- [ ] 表の各行が独立した規範を表す場合、行単位で 1 条項として数える
- [ ] 見出し・背景説明・根拠記述・具体例は独立条項として数えない（ただし圧縮・削減時は同一判定に従って同時処理する旨を表に注記する）
- [ ] 条項 ID を `<ファイル名>#<節>-<連番>` 形式で付与する（例: `fable-l3-protocol.md#5.4-03`）
- [ ] `docs/artifacts/m-1-triage-table.md` を design §5.2 のスキーマ 9 列（条項ID / 原文 / 出典 / 軸1判定 / 軸2判定 / 軸3判定 / 軸4判定 / 決定木の出力 / 根拠1行）で作成し、抽出行を全件記載する
- [ ] 確定した条項数を記録する

**規模の参考値（design §5.1 / 2026-07-25 実測）**: grep 一次スクリーニングのヒットは `fable-l3-protocol.md` 22 行 / `phase-rules.md` 18 行 / `CLAUDE.md` 11 行 = **計 51 行**。`grep -c` はマッチ**行数**であり条項数そのものではない（1 行複数条項なら過小、説明文中の「〜すること」を拾えば過大）。**W1 の対象が数十条項のオーダーであり数百ではない**ことの確認にのみ用いる。

**依存**: W0-M1-T7 完了後（順序制約 1）

**担当想定**: Sonnet（grep + Read + ID 付与 = 機械的写像。**判定列は書かない**）

**規模**: L

---

#### **W1-M1-T2**: 追加入力 2 カテゴリの組込み（閉集合確定 / 計 6 件）

**概要**: まだ本文に書かれていない条項候補 2 カテゴリ 6 件を、トリアージ表に「未執筆条項（追加予定の規範文）」として行追加する。

**対応仕様**: design.md §5.3 / requirements.md FR-21

**カテゴリ (i): R-2 W2/W3 の予定条項 3 件（FR-21 / 閉集合）**:
- [ ] `terminology.md` §4.5 の 3 小節（T9 文書内相互参照の § 見出し表記 / T12 表・節番号の挿入規則 / T13 成果物ファイル命名規則）
- [ ] `planning-quality-guideline.md` §1.5「暗黙前提明示化リスト」（W2-R2-T13b 相当）
- [ ] `model-delegation-prompting.md` の scratchpad 書込禁止節（W3-R2-T24 相当）

> W3-R2-T23（`evaluation-kpi.md` §7 削除）は条項の**削除**でありトリアージ入力に含めない。

**カテゴリ (ii): retro 由来の新規条項候補 3 件**:

| # | 内容 | 対象ファイル |
|:-:|:-----|:------------|
| A2 | 既存ログ・既存出力形式を読むコマンドを書かせる委譲では、そのスキーマ文書を `primary_sources` に含める | `.claude/rules/hga-summoning.md` §primary_sources |
| A3 | MAGI Phase 0 Grounding に「`docs/adr/` の既存 ADR 一覧走査」を追加 | `.claude/skills/magi/SKILL.md` |
| A6 | NFR-W-C-1 の gabriel タイムアウト目安（60 秒 SHOULD）を実測ベースで見直す | `docs/internal/06_DECISION_MAKING.md` |

**完了条件**:
- [ ] 上記 6 件がトリアージ表に「未執筆条項」として行追加されている
- [ ] **両カテゴリを閉集合として確定し、W1 着手後の追加を行わない**旨がトリアージ表冒頭に明記されている（PM 級一括承認の対象範囲を確定させるため）
- [ ] カテゴリ (ii) について「決定木の出力 → 写像」の対応（保全 = 原案通り追加 / 圧縮 = 規範文を増やさない形で追加 / 削減 = 追加しない）が表に注記されている
- [ ] **カテゴリ (ii) の 3 件を W1 の判定を経ずに直接適用していない**（MUST NOT / design §5.3）

**依存**: W1-M1-T1 と並行着手可（表への行追加のみ）

**担当想定**: L1 直（閉集合の確定 = 判断）

**規模**: S

---

#### **W1-M1-T3**: 不変制約 4 対象の除外 + ガード 2 引用範囲の grep 検証

**概要**: 軸に関わらずトリアージ対象外となる 4 対象を、Phase A の実施**前**に除外し「対象外」としてマークする。あわせて FR-5 受け入れ条件 2 の grep 検証を行う。

**対応仕様**: design.md §5.2 不変制約表 / requirements.md FR-5

**不変制約 4 対象と根拠（各行が個別の根拠を持つ）**:

| 対象 | 根拠 |
|:-----|:-----|
| 体験シミュ発火点（3 点） | `fable-l3-protocol.md` §5.4 ガード 2 |
| PM 級承認ゲート・PM 級パス列挙 | `permission-levels.md` §PM 級パスの事前計算原則 |
| gabriel probe 起動条件 | ADR-0007 / FR-W-C-3 |
| 統治への自己書込禁止 | ADR-0005 FR-9.1 |

**完了条件**:
- [ ] トリアージ表の該当条項に「決定木の出力 = **対象外**」を記入し、4 軸判定列を空欄のままとする（4 軸評価を経ていないことを表で可視化する）
- [ ] **`fable-l3-protocol.md` §5.4 ガード 2 が体験シミュ発火点以外の根拠として引用されていないことを grep 実測で確認**する（FR-5 受け入れ条件 2）:

  ```bash
  grep -rn "ガード 2" .claude/rules/ docs/specs/m-1-opus5-migration/design.md
  ```

- [ ] **全ヒットを Read で個別確認**し、「体験シミュ発火点以外の不変制約の根拠として引用している箇所」が 0 件であることを確かめる（行単位 grep は一次スクリーニングであり、除外語による機械的フィルタでは判定できない）
- [ ] 個別確認の結果（各ヒットの文脈と判定）を記録する
- [ ] 除外件数を記録する

**2026-07-25 時点の事前実測（tasks.md 起票時に上記コマンドを実行 / W1 着手時に再実測する）**: ヒット **5 件**、内訳は次の通りで**全件が体験シミュ文脈または引用禁止の宣言そのもの**。現時点で FR-5 受け入れ条件 2 は成立している。

| ヒット | 内容 | 判定 |
|:-------|:-----|:-----|
| `fable-l3-protocol.md:110` | ガード 2 の定義本体（同型構文検出） | 体験シミュ文脈 |
| `fable-l3-protocol.md:116` | ガード 2/3 の判定手段（`/retro` バッチで Haiku 判定） | 体験シミュ文脈 |
| `fable-l3-protocol.md:214` | §9 検証課題「実況第 1 文のテンプレ化検出」 | 体験シミュ文脈 |
| `design.md:282` | 不変制約表の**体験シミュ発火点の行**の根拠 | 正しい引用 |
| `design.md:287` | 「体験シミュ発火点以外の根拠として引用してはならない」の宣言 | 禁止の宣言そのもの |

design.md §5.2 の不変制約表は残り 3 行に別根拠（`permission-levels.md` / ADR-0007 / ADR-0005）を持ち、ガード 2 の拡大引用は発生していない（gabriel 指摘 2 への対応が成立）。

> **判定式の注意（tasks.md 起票時の検証で検出）**: 当初案は `| grep -v "体験シミュ\|発火点"` で機械的に除外する形だったが、実行すると (i) **走査対象に `tasks.md` 自身を含むため自己言及がヒットする**、(ii) 体験シミュ文脈の行でもその行内に「体験シミュ」「発火点」の語がなければ残る、の 2 点で false positive を量産した（実測 6 件中 5 件が false positive）。これは design レビューで検出した §7.2 の C1（測定式が対象の構造をまたげない）および `subprocess-encoding-convention.md` §grep baseline の既知の限界と同型である。**行単位 grep は一次スクリーニング専用とし、判定は Read による個別確認で行う**。

**依存**: W1-M1-T1 完了後（表の行が揃ってから）

**担当想定**: Haiku（事実突合 + grep 実測）

**規模**: M

---

#### **W1-M1-T4**: Phase A — veto 先行スクリーニング（軸 1 → 軸 3）

**概要**: 不変制約で除外されなかった全条項に対し、軸 1（帰属）→ 軸 3（可逆性）の順に veto 判定を行う。該当したら**その時点で保全確定**し、以降の軸評価を行わない。

**対応仕様**: design.md §5.2 veto 先行スクリーニングの手順 / requirements.md FR-4, FR-6

**手順**:
1. 軸 1 を評価する。「ユーザー / プロジェクトの意思（統治・リスク許容度・方法論の選択）」に該当 → **保全（veto）確定**、以降の軸評価なし
2. 軸 1 で確定しなかった条項について軸 3 を評価する。「不可逆ガード（承認ゲート / spec freeze / 破壊操作 / 外部公開）」に該当 → **保全（veto）確定**、以降の軸評価なし
3. 軸 1・軸 3 いずれにも該当しない条項が Phase B（W1-M1-T5）の対象となる

**完了条件**:
- [ ] 全対象条項に軸 1 の判定値（ユーザー意思 / モデル誤り予防）が記入されている
- [ ] 軸 1 = ユーザー意思の条項に「決定木の出力 = 保全」が記入され、軸 2・軸 3・軸 4 列が空欄である（veto の外形証跡）
- [ ] 残った条項に軸 3 の判定値（不可逆 / 可逆）が記入されている
- [ ] 軸 3 = 不可逆の条項に「決定木の出力 = 保全」が記入され、軸 2・軸 4 列が空欄である
- [ ] 各 veto 判定に「根拠 1 行」列が記入されている
- [ ] Phase B へ送る条項数が確定している

**依存**: W1-M1-T3 完了後

**担当想定**: **L1**（軸 1 の帰属判定 = ユーザー意思かモデルの誤り予防かの識別は機械判定不能であり、誤判定が veto 対象条項の削減という不可逆な結果に直結する / design §9 却下案 3）

**規模**: L

---

#### **W1-M1-T5**: Phase B — 残り精査（SSOT 退避 + 決定木 4 分岐）

**概要**: Phase A で veto されなかった条項に対し、SSOT 退避判定 → 軸 4 × 軸 2 の 4 分岐を適用する。

**対応仕様**: design.md §5.2 Phase B / requirements.md FR-4

**手順**:
1. 帰属が**モデル固有の事実**（「層への割当」「設計上の性質の説明」「時点記録」のいずれか）→ **SSOT 退避**（`model-roster.md` へ移動 / 削除ではない）
2. 上記に該当しない条項について、軸 4 × 軸 2 で 4 分岐:

| 軸 4 | 軸 2 | 出力 |
|:-----|:-----|:-----|
| 実測発火あり | 列挙 | **圧縮**（意図 1 行に畳む / 根拠は `docs/artifacts/` へ退避） |
| 実測発火あり | 意図 | **保全** |
| 発火ゼロ | 列挙 | **削減** |
| 発火ゼロ | 意図 | **保全**（低優先 / 次回 retro で再評価） |

**完了条件**:
- [ ] 軸 4 の判定が `trust-model.md` §カウント単位の「**検出イベント単位**」定義（1 検証イベント内の複数 issue は件数によらず 1 カウント）をそのまま用いており、独自定義を新設していない（FR-4 受け入れ条件 3）
- [ ] Phase B 対象条項すべてに軸 2・軸 4 の判定値と「決定木の出力」が記入されている
- [ ] 「決定木の出力」列の値が **5 値の閉集合**（保全 / 圧縮 / 削減 / SSOT退避 / 対象外）に収まっている
- [ ] 各判定に「根拠 1 行」列が記入されている
- [ ] 圧縮 / 削減 / SSOT 退避 の件数内訳が集計されている（**件数は記録であり目標ではない** / NFR-6）

**依存**: W1-M1-T4 完了後

**担当想定**: **L1**（決定木の適用 = 仕様判断）

**規模**: L

---

#### **W1-M1-T6**: トリアージ表の PM 級一括承認（K5 / 1 承認イベント）

**概要**: トリアージ表全体を 1 承認イベントとしてユーザー承認を得る。

**対応仕様**: design.md §5.4 / requirements.md FR-6, FR-3

**完了条件**:
- [ ] トリアージ表が全条項について「決定木の出力」列を埋めた状態で完成している
- [ ] 承認プロンプトに「**本 Wave はファイル編集を行わず、トリアージ表の承認のみを求める**」旨が明示されている（形式差の明示 / design §3.2）
- [ ] 承認が**トリアージ表全体で 1 回の承認イベント**として記録されている（FR-6 受け入れ条件 3）
- [ ] 承認記録が `SESSION_STATE.md` に残り、Milestone retro（W4-M1-T5）で VCS 管理下へ永続化される旨が記録されている（FR-3 受け入れ条件 2）
- [ ] W1 中に圧縮・削減・SSOT 退避が**実行されていない**ことを確認する（`git diff` で `.claude/rules/` / `CLAUDE.md` に変更がないこと）

**依存**: W1-M1-T5 完了後

**担当想定**: L1

**規模**: S

---

#### **W1-M1-T7**: W1 末測定 + 安定性ゲート判定入力の収集

**概要**: §9 の共通手順で W1 末のベースライン 6 項目を測定し、あわせて Opus 5 安定性ゲート（§5）の判定に必要な 3 入力を収集する。

**対応仕様**: design.md §3.4, §5.5 / requirements.md FR-8, FR-2

**完了条件**:
- [ ] §9 の共通手順で 6 項目を測定し `docs/artifacts/m-1-baseline-w1.md` に記録する
- [ ] ゲート入力 1: W1 着手〜完了の全セッション数と、`docs/artifacts/` に新規起票された tool malformed インシデント文書の件数
- [ ] ゲート入力 2: W0 ベースライン比の pytest PASS 数差分と FAIL 件数
- [ ] ゲート入力 3: W1 中の gabriel probe 実行件数と `verdict=refuted & severity=critical` の連続発生の有無
- [ ] **セッション数が 3 未満の場合、判定を保留し W1 を延長する**旨を記録する（design §5.5）

**依存**: W1-M1-T6 完了後

**担当想定**: Haiku（実行 + 結果パース + 構造化報告）

**規模**: M

---

## 5. ゲート: Opus 5 安定性ゲート（W1 → W2）

**FR-2 が要求する独立ステップ**。W1 完了時点で以下 3 条件を**すべて**満たした場合のみ W2 へ進む。

| # | 条件 | 判定方法 | 母数・期間 |
|:-:|:-----|:---------|:-----------|
| 1 | malformed / tool 呼び出し異常ゼロ | `docs/artifacts/` に新規起票された tool malformed インシデント文書が 0 件 | W1 着手から完了までの全セッション（**最低 3 セッション**。3 未満なら判定を保留し W1 を延長） |
| 2 | pytest regression ゼロ | W0 ベースライン比で PASS 数が減っていない、かつ FAIL が 0 | W1 末の測定 1 回 |
| 3 | gabriel verdict 分布に異常なし | W1 中の gabriel probe で `verdict=refuted & severity=critical` が **2 回以上連続していない** | W1 中の probe 実行全件。**probe 実行 0 回の場合は本条件を「判定不能」として skip し、残り 2 条件で合否を決める** |

### 不合格時のフォールバック手順（FR-2 受け入れ条件 3）

1. **Opus 4.7 へフォールバック**する（実行モデルの切替）
2. **M-1 を一時停止**する
3. **W1 の分析成果（トリアージ表）はそのまま保持**する。損失は W1 の分析リードタイム分に留まり、再開時に再利用する
4. 不合格の判定理由（3 条件のどれが不成立か）を記録する

### 記録先

- [ ] ゲート判定結果（合格 / 不合格）を `docs/artifacts/m-1-opus5-stability-gate.md` に記録する（FR-2 受け入れ条件 2）
- [ ] 3 条件それぞれの実測値と判定を記載する（条件 3 が skip の場合はその旨と probe 実行 0 回の事実を明記）

**担当想定**: L1（ゲート判定 = 進行可否の判断）

---

## 6. W2: 規律本体の適用

### 本 Wave で編集する PM 級ファイル一覧（K5 一括宣言）

design §3.2 の W2 行を転記する。

- [ ] `.claude/rules/model-roster.md`（**新規作成** / W2-M1-T1）
- [ ] `.claude/rules/model-delegation-prompting.md`（圧縮: 挙動デルタを移動し参照のみ残す / W2-M1-T2）
- [ ] `.claude/rules/hga-summoning.md`（圧縮: 単価・envelope を移動 / W2-M1-T2、召喚ゲート節の改訂 / W2-M1-T6）
- [ ] `CLAUDE.md`（モデル ID 直書き除去 + `model-roster.md` への導線追加 / W2-M1-T3）
- [ ] **W1 トリアージ表で圧縮・削減判定を受けた `.claude/rules/*.md` 各ファイル**（対象確定は W1 出力に依存 / W2-M1-T5）
- [ ] `docs/specs/r-2-consolidation/tasks.md`（該当 Task 完了記録への判定結果反映 / W2-M1-T7）
- [ ] `.claude/rules/terminology.md` / `.claude/rules/planning-quality-guideline.md` / `.claude/rules/model-delegation-prompting.md`（R-2 予定条項のうち判定が「実施」または「圧縮形で実施」の分のみ / W2-M1-T7）

**条件付き（追加宣言で扱う）**:

- [ ] `.claude/rules/auto-generated/trust-model.md`（FR-9 の接続を削減台帳側の運用記述ではなく `trust-model.md` 本文に書く場合のみ / W2-M1-T8）

> **W1 出力依存の宣言運用**: 上記 5 番目の項目は W1 完了まで具体ファイル名が確定しない。**W2 冒頭の K5 宣言時に W1 トリアージ表から確定リストを転記して宣言する**（宣言の空欄化を避ける）。宣言後に新規 PM 級ファイルが必要になった場合は追加宣言 + 承認を経る（FR-3 受け入れ条件 3）。

---

### W2 詳細タスク

#### **W2-M1-T1**: `model-roster.md` 新設（4 項目 + ADR-0001 関係明記）

**概要**: `.claude/rules/model-roster.md` を新設し、モデル名束縛の単一 SSOT とする。

**対応仕様**: design.md §6.1 / requirements.md FR-10, FR-14

**完了条件**:
- [ ] `.claude/rules/model-roster.md` が新規作成され、以下 4 項目のセクションを持つ:
  1. **現行ロスター表**（層 L1 / L1.5 / L2 / L3 / HGA × モデル ID × 有効日）
  2. **層内閾値**（例: 当該モデルにおける L1 直接実装量の上限）
  3. **挙動デルタ**（W2-M1-T2 で吸収）
  4. **単価・envelope**（W2-M1-T2 で吸収 / W0-M1-T5 の裏取り結果を転記）
- [ ] 冒頭または関連節に **ADR-0001 との関係（supersede しない / 直交する）** が明記されている（FR-14 受け入れ条件 1）
- [ ] ロスター表が hooks / subagents の層（L2 / L3）に **Opus を割り当てていない**ことが確認できる（FR-14 受け入れ条件 3 / ADR-0001 制約）
- [ ] 単価・envelope 節に W0-M1-T5 の裏取り結果（一次資料 URL・取得日つき / 未確認項目は「未確認」）が反映されている（FR-19 受け入れ条件 3）

**依存**: W0-M1-T5 完了 + 安定性ゲート合格後

**担当想定**: Sonnet（design に内容が確定 = 写像作業）

**規模**: M

---

#### **W2-M1-T2**: SSOT 退避の実行（2 ファイル → roster / 参照のみ残す）

**概要**: `model-delegation-prompting.md` と `hga-summoning.md` のモデル固有記述を `model-roster.md` へ移動し、元ファイルには参照のみを残す。

**対応仕様**: design.md §6.1 移行手順 / requirements.md FR-10

**完了条件**:
- [ ] `model-delegation-prompting.md` の挙動デルタ記述が `model-roster.md` へ移動し、元ファイルには参照のみが残っている
- [ ] `hga-summoning.md` の単価・envelope 記述が `model-roster.md` へ移動し、元ファイルには参照のみが残っている
- [ ] 移動内容（移動元・移動先の対応）が削減台帳 `docs/artifacts/m-1-clause-ledger.md` に記録されている（FR-10 受け入れ条件 3）
- [ ] 移動により既存の相互参照リンクが切れていないことを確認する

**依存**: W2-M1-T1 完了後

**担当想定**: Sonnet

**規模**: M

---

#### **W2-M1-T3**: `CLAUDE.md` のモデル ID 直書き除去 + 導線追加

**概要**: `CLAUDE.md` に層の定義のみを残し、モデル名を書かない状態にする。

**対応仕様**: design.md §6.1 / requirements.md FR-11

**完了条件**:
- [ ] `CLAUDE.md` §作業体制からモデル ID の直書き（`opus` / `sonnet` / `haiku` / `fable` / `claude-*-数字` パターン）が、例外登録対象（FR-12 の「時点記録」分類）を除きすべて除去されている
- [ ] 層の定義（L1 = 判断 / L1.5 = 司令塔 / L2 = 実行 / L3 = 採点）は残されている
- [ ] `CLAUDE.md` に `model-roster.md` への導線（1-2 行の参照）が存在する
- [ ] W2-M1-T4 完了後に `verify_model_reference` を実行し、`CLAUDE.md` の drift が **ゼロ**と判定される（FR-11 受け入れ条件 3）

**依存**: W2-M1-T1 完了後（drift ゼロ確認は W2-M1-T4 完了後）

**担当想定**: Sonnet

**規模**: M

---

#### **W2-M1-T4**: `verify_model_reference.py` 新規実装（3 分岐 / TDD）

**概要**: SSOT 外のファイルにおけるモデル名直書きを検出し、3 分岐で分類する新規スクリプトを TDD で実装する。

**対応仕様**: design.md §6.2（Red-4 解決 = 新規スクリプト）/ requirements.md FR-12, NFR-4, NFR-5

**完了条件**:
- [ ] `.claude/scripts/verify_model_reference.py` を新規作成する（既存 `verify_reference_resolution.py` へのパターン追加**ではない**）
- [ ] `.claude/tests/scripts/test_verify_model_reference.py` を作成する（Red → Green → Refactor）
- [ ] 検出パターン: `\b(Opus|Sonnet|Haiku|Fable)[\s-]?\d+(\.\d+)?\b` および `claude-(opus|sonnet|haiku)-\d[\w.-]*`（大文字小文字を無視）
- [ ] 3 分岐判定を実装する: 「層への割当」→ `layer_assignment`（SSOT 退避）/ 「時点記録」（`docs/artifacts/` / `docs/adr/` / 実測ログ）→ `point_in_time_record`（例外登録）/ 既定 → `design_property_description`（圧縮対象）
- [ ] **例外登録がファイルパス単位ではなく記述の性質単位**で行われていることをテストで確認する（FR-12 受け入れ条件 3 / gabriel 指摘 1）
- [ ] 出力形式が `verify_reference_resolution.py` の形状（`total_drifts` / 各 drift が `pattern` / `source` / `referenced` / `match`）に揃い、`classification` キーが追加されている
- [ ] **誤例の実測**: `.claude/agents/gabriel.md` 本文の「同一モデル（Opus）の別ペルソナ」が `design_property_description`（圧縮対象）に分類されることを確認する（FR-12 受け入れ条件 2）
- [ ] **正例**: `model-roster.md` 自身および `docs/artifacts/` 配下が drift として報告されない（または `point_in_time_record` に分類される）ことを確認する
- [ ] NFR-4: `from __future__ import annotations` を付与し、`match` / `except*` / dict merge (`|`) / `str.removesuffix` を使用しない
- [ ] NFR-5: `subprocess.run` を使う場合 `encoding="utf-8", errors="replace"` を指定する
- [ ] `bash .claude/scripts/py_invoke.sh -m pytest .claude/tests/rules/test_subprocess_encoding_convention.py` が PASS する

**依存**: W2-M1-T2 / T3 完了後（退避後の状態を検査対象とするため）

**担当想定**: Sonnet（TDD）

**規模**: L

**検証コマンド**:

```bash
bash .claude/scripts/py_invoke.sh .claude/scripts/verify_model_reference.py
```

---

#### **W2-M1-T5**: トリアージ判定の適用 + 削減台帳への全件記録

**概要**: W1-M1-T6 で承認されたトリアージ表に従い、圧縮 / 削減 / SSOT 退避を実行し、削減台帳に全件記録する。

**対応仕様**: design.md §6.3 / requirements.md FR-6, FR-7

**完了条件**:
- [ ] 承認済みトリアージ表の「圧縮」判定条項について、意図 1 行への畳み込みを実行し、根拠を `docs/artifacts/` へ退避する
- [ ] 「削減」判定条項を削除する
- [ ] 「SSOT 退避」判定条項を `model-roster.md` へ移動する（削除ではなく移動）
- [ ] **「保全」「対象外」判定条項に一切変更を加えていない**ことを `git diff` で確認する
- [ ] 圧縮・削減判定を受けた条項が**全件**削減台帳（7 列）に記載されている
- [ ] 条項に付随する文脈（見出し・背景説明・根拠記述・具体例）が同一判定に従って同時処理されている（design §5.1 付随する扱い）
- [ ] **NFR-1 の確認**: 体験シミュ発火点 3 点が圧縮後も `phase-rules.md` または `fable-l3-protocol.md` のいずれかに明記され続けている / gabriel probe 起動条件（AoT 適用時 MUST）が変更されていない

**依存**: W1-M1-T6（承認）+ W2-M1-T4 完了後

**担当想定**: Sonnet（判定は W1 で確定済 = 写像作業）

**規模**: L

---

#### **W2-M1-T6**: HGA 召喚ゲート改訂（事後条件化 + 移行期規定）

**概要**: ADR-0011 決定 4 の内容を `hga-summoning.md` §召喚ゲート節に反映する。

**対応仕様**: design.md §6.4 / requirements.md FR-15

**完了条件**:
- [ ] 無条件召喚 2 条件（spec/design 初期 / 不可逆な設計コミット）を**事後条件の判定材料へ格下げ**する
- [ ] 召喚ゲート節が ADR-0009 追補の事後条件 3 点（`AC-W-C-7` 到達 / 第 0 原則 3 変数での不可逆判定 + L1 確信不足 / ユーザー明示指示）に改訂されている
- [ ] 新ゲートが MAGI `AC-W-C-7`（gabriel critical refute 2 回目 = 再 MAGI 上限到達）への**接続として定義**され、新規の召喚判定コードが追加されていない
- [ ] **移行期規定**「M-1 実施中は旧ゲートを適用し、新ゲートは M-1 完了（W4 retro）後に発効する」が明記されている
- [ ] 本改訂は W2-M1-T2 の単価・envelope 移動とは**別の編集単位**として扱われている（同一 K5 宣言内で処理）

**依存**: W2-M1-T5 完了後（T2 と同一ファイルのため順序を分離）

**担当想定**: Sonnet

**規模**: M

---

#### **W2-M1-T7**: R-2 W2/W3 再スコープの実行（3 分岐写像 → 反映）

**概要**: W1 トリアージ表の判定を R-2 の 3 分岐（実施 / 圧縮形で実施 / スキップ）へ写像し、R-2 tasks.md の該当 Task 完了記録に反映する。

**対応仕様**: design.md §6.5（Red-7 の手続き）/ requirements.md FR-21

**写像規則**:

| 決定木の出力 | R-2 への写像 |
|:-------------|:--------------|
| 保全 | 実施（原案通り追加する） |
| 圧縮 | 圧縮形で実施（意図 1 行に畳んだ形で追加する） |
| 削減 | スキップ（追加しない） |

**完了条件**:
- [ ] R-2 予定条項 3 件それぞれについて「実施 / 圧縮形で実施 / スキップ」の判定が確定している
- [ ] `docs/specs/r-2-consolidation/tasks.md` の該当 Task（W2-R2-T9 / T12 / T13、W2-R2-T13b、W3-R2-T24）完了記録に判定結果が反映されている
- [ ] 判定が「実施」または「圧縮形で実施」の条項について、対象ファイル（`terminology.md` / `planning-quality-guideline.md` / `model-delegation-prompting.md`）への追記が行われている
- [ ] **R-2 の Definition of Done 自体を変更していない**（Non-Goals 4）
- [ ] retro 由来 3 件（A2 / A3 / A6）の判定結果も同様に反映されている（対象ファイル: `hga-summoning.md` / `magi/SKILL.md` / `06_DECISION_MAKING.md`）

**依存**: W2-M1-T5 完了後

**担当想定**: L1（判定の写像）+ Sonnet（記録反映）

**規模**: M

---

#### **W2-M1-T8**: `trust-model.md` への接続（復活経路 / 新規実装なし）

**概要**: 削減台帳に記載された条項を `trust-model.md` の検出イベント対象に含め、閾値 2 回で復活候補として提案する経路を成立させる。3 層安全網の第 3 層。

**対応仕様**: design.md §6.6 / requirements.md FR-9, NFR-2

**完了条件**:
- [ ] `trust-model.md` または削減台帳の運用記述に、**削減済み条項の不在起因の検出イベントを既存の閾値判定ロジックに含める**旨が明記されている
- [ ] 検出イベントのデータソースが `trust-model.md` §カウント単位の既存定義（`tdd-patterns.log` / HGA 召喚ログ / 監査 Stage 記録 / gabriel probe 記録）をそのまま用いている
- [ ] 復活候補提案の手続きが `/retro` の既存 Step 2.5 フローに接続されている
- [ ] **新規のカウント機構・新規ログファイルが追加されていない**（FR-9 受け入れ条件 2 / NFR-2）
- [ ] Green State の 5 条件（G1〜G5）に安全網由来の新条件が追加されていない（NFR-2 受け入れ条件 3）

**依存**: W2-M1-T5 完了後

**担当想定**: Sonnet

**規模**: S

---

#### **W2-M1-T9**: W2 末測定 + 件数突合（トリアージ表 vs 削減台帳）

**概要**: §9 の共通手順で W2 末測定を行い、あわせて FR-7 受け入れ条件 3 の件数突合を実施する。

**対応仕様**: design.md §3.4, §6.3 / requirements.md FR-7, FR-8, NFR-3

**完了条件**:
- [ ] §9 の共通手順で 6 項目を測定し `docs/artifacts/m-1-baseline-w2.md` に記録する
- [ ] **W1 トリアージ表の「圧縮」+「削減」判定件数と、削減台帳の記載件数が一致する**（判定日 = W2 適用日を基準に突合 / FR-7 受け入れ条件 3）
- [ ] 不一致がある場合、差分の内訳（未記録 / 重複 / 判定変更）を特定し解消する
- [ ] pytest regression ゼロ（NFR-3）

**依存**: W2-M1-T6 / T7 / T8 完了後

**担当想定**: Haiku（事実突合 + 件数集計）

**規模**: M

---

## 7. W3: skills / agents の構造改善

### 本 Wave で編集する PM 級ファイル一覧（K5 一括宣言）

> **注記（design §3.2 の補完）**: design §3.2 の W3 行は「宣言不要（既定）/ なし」としているが、design §7.2 末尾は「requirements FR-16 の説明文および受け入れ条件 2 の内訳表記は、W3 着手時に本実測へ更新する（**PM 級**）」と定めている。`docs/specs/` 配下は PM 級パスであるため、本節で宣言対象に加えて補完する。

- [ ] `docs/specs/m-1-opus5-migration/requirements.md`（FR-16 の説明文・受け入れ条件 2 の内訳を実測へ更新 / W3-M1-T1）

**条件付き（追加宣言で扱う）**:

- [ ] `docs/adr/0010-global-claude-assets-governance.md`（W3-M1-T4 で I-1〜I-6 の不適合が発見された場合のみ追記）

**非 PM 級**: `.claude/skills/` および `.claude/agents/` は `permission-levels.md` §ファイルパスベースの分類で PM 級パスに含まれない（既定 SE 級）。

---

### W3 詳細タスク

#### **W3-M1-T1**: 対象再実測（9 件）+ 上位 4 件確定 + FR-16 訂正

**概要**: 軸 S2（参照到達性）の判定式で対象 skill を再実測し、W3 のスコープを確定する。あわせて requirements FR-16 の内訳表記を実測へ更新する。

**対応仕様**: design.md §7.1（軸 S1〜S4 / Red-2 解決）, §7.2 / requirements.md FR-16

**判定軸（design §7.1 / 規律文書向け 4 軸とは別）**:

| 軸 | 問い | 分割側 | 保全側 |
|:---|:-----|:-------|:-------|
| **S1 発火頻度** | skill 起動のたびに必要か | 特定分岐でのみ必要 | 毎回必要 |
| **S2 参照到達性** | 外部ファイルへの参照を既に持つか | 外部参照ゼロ（全インライン） | `references/` へ分離済み |
| **S3 条件付き実行** | 特定条件下でのみ実行される手順か | 条件分岐の中にのみ現れる | 無条件に実行される |
| **S4 契約か手順か** | frontmatter / description（契約）か本文手順か | 本文手順 | 契約（常時ロードが必要） |

**完了条件**:
- [ ] 以下のコマンドで再実測する（**`references/` ディレクトリの実在判定**であり Markdown リンクの有無では判定しない）:

  ```bash
  for f in .claude/skills/*/SKILL.md; do
    lines=$(wc -l < "$f")
    refdir="$(dirname "$f")/references"
    if [ "$lines" -gt 100 ] && [ ! -d "$refdir" ]; then
      printf "%5s  %s\n" "$lines" "$f"
    fi
  done | sort -rn
  ```

- [ ] 実測結果を design §7.2 の 2026-07-25 実測（9 件）と突合する
- [ ] **W3 のスコープ = 行数降順の上位 4 件**を確定する（design §7.2 時点の実測では `full-review` 951 / `goal-driven` 419 / `init-harness` 288 / `spec-template` 268）
- [ ] 残り 5 件（`adr-template` 234 / `autonomous` 185 / `ship` 180 / `building` 136 / `retro` 135）を **M-1 スコープ外**として記録する（W3-M1-T5 で Wave 完了記録に明記）
- [ ] **requirements FR-16 の説明文および受け入れ条件 2 の内訳表記を本実測へ更新する**（PM 級編集 / K5 宣言済）。旧記述「優先対象 4 件（`full-review` を含む）」は、旧判定式では `full-review` が対象外になり新判定式では 9 件になるため、**どちらの判定式でも同時に成立しない**

**依存**: W2-M1-T9 完了後

**担当想定**: Haiku（実測）+ L1（PM 級訂正）

**規模**: M

---

#### **W3-M1-T2**: progressive disclosure 化の実施（上位 4 件）+ 動作確認

**概要**: W3-M1-T1 で確定した上位 4 件について、軸 S1・S3 で切れ目を探し `references/` 配下へ退避する。

**対応仕様**: design.md §7.1 決定木, §7.2 / requirements.md FR-16

**決定木（design §7.1）**:

```
100 行超 かつ 軸S2 = 外部参照ゼロ
  → 分割候補 → 軸S1・軸S3 で切れ目を探す
      ├ 切れ目あり → references/ 配下へ退避し本体から参照
      └ 切れ目なし → 保全（分割すると手順の意味が壊れるため）
```

**完了条件**:
- [ ] 対象 4 件それぞれについて軸 S1・S3 で切れ目の有無を判定し、判定結果を記録する
- [ ] 切れ目ありと判定した skill について `references/` ディレクトリを新設し、条件付き実行部分・特定分岐でのみ必要な部分を退避する
- [ ] **切れ目なしと判定した skill は保全する**（分割そのものを目的化しない）
- [ ] 退避後も frontmatter / description（軸 S4 の「契約」）が本体に残っている
- [ ] **動作確認**: 対象 skill の主要な発火条件・振る舞いに変更がないことを実際に起動して検証する（FR-16 受け入れ条件 3）
- [ ] 退避したファイルが**実体ファイル**であり symlink でないことを確認する（ADR-0010 I-3 / W3-M1-T4 の入力）

**依存**: W3-M1-T1 完了後

**担当想定**: Sonnet

**規模**: L

---

#### **W3-M1-T3**: `quality-auditor` × `code-reviewer` 重複判定（2 指標）

**概要**: 2 agent の守備範囲重複について、2 指標で判断材料を収集し統廃合の是非を判定する（Red-3）。

**対応仕様**: design.md §7.3 / requirements.md §7 Red-3

**指標 1: 起動実績の直接証跡**

```bash
ls -ld .claude/agent-memory/quality-auditor .claude/agent-memory/code-reviewer
```

design レビュー時（2026-07-25）の実測: 両ディレクトリとも存在し、最終更新は `code-reviewer` 2026-06-11 / `quality-auditor` 2026-06-19。**どちらも死んでいないが、どちらも 1 か月以上更新されていない**。

> **限界の明示**: 本指標が示すのは「起動されたことがあるか」と「最後に知見を書いた日」のみ。起動回数は測れない（起動しても memory へ書かなければ更新されない）。**回数の集計機構は追加しない**（NFR-2）。

**指標 2: 責務定義の重複度（Red-3 の本題）**

**完了条件**:
- [ ] 指標 1 を再実測し記録する（W3 着手時点の最終更新日）
- [ ] `.claude/agents/quality-auditor.md` と `.claude/agents/code-reviewer.md` の frontmatter `description` および本文の守備範囲記述を並置する
- [ ] 判定 1: 両者の `description` が指す**起動条件に重なりがあるか**（重なりがあると呼び出す側がどちらを選ぶべきか判断できない）
- [ ] 判定 2: 一方の守備範囲が他方の**真部分集合**になっているか
- [ ] **分岐**: 判定 1 と判定 2 の**両方が成立する場合にのみ統廃合を提案**する。それ以外は現状維持とし、`description` の書き分け（起動条件の排他化）のみを行う
- [ ] 統廃合を提案する場合、実施は PM 級判断に上げる（**本 Task では提案までとし、agent の削除を実行しない**）
- [ ] 判定結果と根拠を W3 完了記録に残す

**依存**: W3-M1-T1 完了後（T2 と並行可）

**担当想定**: **L1**（責務定義の重複判定 = 設計判断）

**規模**: M

---

#### **W3-M1-T4**: ADR-0010 I-1〜I-6 適合確認

**概要**: W3 成果物が ADR-0010 の統治不変条件に適合していることを確認する（R-3 の発火）。

**対応仕様**: design.md §7.4 / requirements.md FR-17

**チェック項目**:

| I | W3 確認観点 | 判定 |
|:--|:------------|:----:|
| I-1 | progressive disclosure 化が `~/.claude/skills/` への直置きを発生させないこと（変更は `.claude/skills/` = project 層に閉じる） | [ ] |
| I-2 | plugin の enable 操作を行っていないこと（本 Wave はプロジェクト内変更のみ = **非該当**。非該当であることの確認記録を残す） | [ ] |
| I-3 | `references/` へ退避したファイルが**実体ファイル**であり symlink でないこと | [ ] |
| I-4 | LAM 内部の相互参照に plugin 名前空間の対象がないこと（現状 LAM は project 層完結のため通常は非該当） | [ ] |
| I-5 | personal 層の共有可変資産（hooks / settings）に変更を加えていないこと（**非該当**） | [ ] |
| I-6 | agents 統廃合検討（W3-M1-T3）が `~/.claude/agents/` への直置きを発生させないこと | [ ] |

**完了条件**:
- [ ] 上記 6 項目すべてに適合 / 不適合 / 非該当のいずれかを判定し、W3 完了記録に残す
- [ ] **不適合が発見された場合、PM 級判断に差し戻す**（`docs/adr/0010-global-claude-assets-governance.md` への追記が必要なら追加宣言 + 承認 / FR-17 受け入れ条件 3）

**依存**: W3-M1-T2 / T3 完了後

**担当想定**: Haiku（事実突合）

**規模**: M

---

#### **W3-M1-T5**: W3 末測定 + 未着手 5 件の明記

**概要**: §9 の共通手順で W3 末測定を行い、あわせて progressive disclosure 化の**未着手 5 件**を Wave 完了記録に明記する。

**対応仕様**: design.md §3.4, §7.2 / requirements.md FR-8, FR-16

**完了条件**:
- [ ] §9 の共通手順で 6 項目を測定し `docs/artifacts/m-1-baseline-w3.md` に記録する
- [ ] **未着手 5 件を Wave 完了記録に明記する**（silent な打ち切りにしない / design §7.2）。各件について行数と「M-1 スコープ外へ送った理由（上位 4 件で requirements の件数要求を満たすため）」を記載する
- [ ] pytest regression ゼロ（NFR-3）

**依存**: W3-M1-T4 完了後

**担当想定**: Haiku

**規模**: S

---

## 8. W4: 検証・確定

### 本 Wave で編集する PM 級ファイル一覧（K5 一括宣言）

**なし**（既定）。`docs/artifacts/m-1-distribution-catalog.md` および `.claude/skills/update-model/SKILL.md` はいずれも PM 級パス列挙外（SE 級）。

> **ただし配布実行は別途ユーザー承認ゲートの対象**（W4-M1-T4 / design §8.3）。`lam-harness` plugin の version bump と LAM リポジトリ外への配布コピー書き出しは **LAM リポジトリの外部へ変更を公開する不可逆な操作**であり、PM 級パス列挙外だが第 0 原則の可逆性・復旧コスト軸で不可逆側に立つため、**実行直前にユーザー承認を得る**。

---

### W4 詳細タスク

#### **W4-M1-T1**: `update-model` skill 作成（6 ステップ）+ 整合検証 pytest

**概要**: `.claude/skills/update-model/SKILL.md` を、判断ロジックを含まない**薄い順序表**として作成する。

**対応仕様**: design.md §8.2 / requirements.md FR-13, FR-14

**手順（6 ステップ）**:

| # | ステップ | 実体 |
|:-:|:---------|:-----|
| 1 | upstream 一次資料確認 | `upstream-first.md` 準拠（§4.3 と同一手順） |
| 2 | `model-roster.md` 更新 | + **ADR-0001 の「Opus は hooks/subagents で使用しない」制約を破らないことの確認**（FR-14） |
| 3 | `verify_model_reference` 実行 | `bash .claude/scripts/py_invoke.sh .claude/scripts/verify_model_reference.py` |
| 4 | `.claude/agents/*.md` frontmatter 更新 | — |
| 5 | ベースライン再測定 | §4.1 と同一の 6 項目手順 |
| 6 | 配布カタログへの追記 | `docs/artifacts/m-1-distribution-catalog.md` |

**完了条件**:
- [ ] `.claude/skills/update-model/SKILL.md` が上記 6 ステップのみを記述している
- [ ] **判断ロジック（条件分岐・閾値判定コード）を skill 内に実装していない**（FR-13 受け入れ条件 1）
- [ ] 各ステップが既存スクリプト・コマンドの呼び出しとして記述されている（FR-13 受け入れ条件 2）
- [ ] ステップ 2 の直後に FR-14 の確認ステップが存在する
- [ ] **整合検証 pytest** を用意し、skill の手順と手順が呼び出す各スクリプト（`verify_model_reference` を含む）の整合を検証する（FR-13 受け入れ条件 3 / テストファイル名は BUILDING で確定）
- [ ] 整合検証 pytest が PASS する

**依存**: 安定性ゲート合格 + W2-M1-T4 完了後（W3 と並行着手可）

**担当想定**: Sonnet（TDD）

**規模**: L

---

#### **W4-M1-T2**: ベースライン再測定（W4）+ W0 比較

**概要**: §4.1 と同一の 6 項目・同一手順を W4 末に再実行し、W0 と比較する。

**対応仕様**: design.md §8.1 / requirements.md FR-8, NFR-1, NFR-3, NFR-6 / DoD-4

**完了条件**:
- [ ] 6 項目を再測定し `docs/artifacts/m-1-baseline-w4.md` に記録する
- [ ] W0 と W4 の測定値を並置した比較表を作成する
- [ ] **pytest regression ゼロ**（NFR-3 / W0 起点比で PASS 数が減っていない）
- [ ] **NFR-1 の確認**: PM 級ダイアログ発火数に構造的な減少がない / 体験シミュ発火点 3 点が明記され続けている / gabriel probe 起動条件が変更されていない
- [ ] 測定項目 3 が W0-M1-T2 で「参考値扱い」と確定していた場合、**DoD-4 の判定条件から除外**した旨と理由を明記する
- [ ] **NFR-6 の遵守**: 測定結果（項目 6 の文字数差分等）は**報告するが、それ自体を DoD 判定条件として使わない**

**依存**: W4-M1-T1 / T3 完了後

**担当想定**: Haiku

**規模**: M

---

#### **W4-M1-T3**: 配布カタログ作成（7 列）

**概要**: 規律の変更を対象とする配布カタログ `docs/artifacts/m-1-distribution-catalog.md` を作成する。

**対応仕様**: design.md §8.3 / requirements.md FR-18

**完了条件**:
- [ ] `docs/artifacts/m-1-distribution-catalog.md` が作成され、7 列（変更項目 / 種別 / LAM 固有度 / 必要 harness バージョン / 前提モデル世代 / 依存 / 判断軸）を持つ
- [ ] 対象は**規律の変更**（`CLAUDE.md` / `.claude/rules/` / `model-roster.md` パターン）である
- [ ] **skills / agents の変更（W3 成果物）はカタログに含めない**（plugin チャネル側 / FR-18 受け入れ条件 1）
- [ ] 各行の「LAM 固有度」により、他プロジェクトへ持ち出せる項目と LAM 固有の項目が区別されている

**依存**: W2-M1-T9 完了後（W4-M1-T1 と並行可）

**担当想定**: Sonnet

**規模**: M

---

#### **W4-M1-T4**: 配布実行（2 経路 / 直前にユーザー承認）

**概要**: 配布 2 経路を実行する。**実行直前にユーザー承認を得る**（不可逆な外部公開）。

**対応仕様**: design.md §8.3 配布実行の承認ゲート / requirements.md FR-18

| 配布対象 | 経路 |
|:---------|:-----|
| skills / agents の変更（W3 成果物） | ADR-0010 の plugin チャネル（`lam-harness` の version bump） |
| 規律の変更 | カタログ（正本 `docs/artifacts/m-1-distribution-catalog.md` / 配布コピーは LAM リポジトリ外） |

**完了条件**:
- [ ] **配布実行の直前にユーザー承認を得る**（`core-identity.md` §第 0 原則 / `permission-levels.md` §迷った場合）。承認前に version bump・リポジトリ外書き出しを行わない
- [ ] W3 成果物が `lam-harness` plugin の version bump として配布されている
- [ ] カタログの配布コピーが LAM リポジトリ外に存在する。**書き出し先パスは 2026-07-21 前例の既存配布運用を W4 着手時に確認して踏襲する**（design §8.3 / 前例のパスは design 時点で未確認）
- [ ] 配布実行の記録（実行日 / version / 書き出し先）を残す

**依存**: W4-M1-T2（regression 確認）完了後

**担当想定**: **L1**（ユーザー承認の取得 + 不可逆操作の実行）

**規模**: M

---

#### **W4-M1-T5**: Milestone retro（4 項目の記録）

**概要**: `docs/artifacts/retro-M1-<date>.md` を起草し、DoD-6 を成立させる。

**対応仕様**: design.md §8.4 / requirements.md DoD-6, FR-3

**完了条件**:
- [ ] `docs/artifacts/retro-M1-<date>.md` を起草する
- [ ] 記録 1: **R-2 W2/W3 再スコープ結果**（実施 / 圧縮形で実施 / スキップ）が `docs/specs/r-2-consolidation/tasks.md` の該当 Task 完了記録へ反映されたことの確認
- [ ] 記録 2: **ベースライン比較結果**（W0 vs W4）
- [ ] 記録 3: **削減台帳のサマリ**（圧縮 / 削減 / SSOT 退避の件数内訳）
- [ ] 記録 4: **`trust-model.md` 接続状況**（M-1 完了時点で復活候補が存在するかの確認）
- [ ] 各 Wave の K5 宣言・承認記録が `SESSION_STATE.md` から retro（VCS 管理下）へ**永続化**されている（FR-3 受け入れ条件 2）
- [ ] **HGA 新ゲートの発効**（M-1 完了 = W4 retro 後）を記録する（FR-15 移行期規定）
- [ ] **NFR-6 の遵守**: retro の評価項目に**削減量の数値目標達成率を含めない**
- [ ] DoD-1〜DoD-6 の充足状況を記載する

**依存**: W4-M1-T4 完了後（M-1 最終 Task）

**担当想定**: L1

**規模**: M

---

## 9. Wave 末測定の共通手順（全 Wave / FR-8, NFR-3）

**W0・W1・W2・W3・W4 の各 Wave 末で必ず実施**する。手順は design §4.1 の 6 項目と同一であり、Wave によって変えない（比較可能性の担保）。

```bash
bash .claude/scripts/py_invoke.sh -m pytest
```

**測定 6 項目**:

| # | 項目 | 取得元 |
|:-:|:-----|:-------|
| 1 | pytest 全数 | 上記コマンドの PASS / FAIL / SKIP |
| 2 | Green State 件数 | 直近 Wave 末ゲート記録の Critical / Warning 件数 |
| 3 | `tdd-patterns.log` FAIL→PASS 率 | `trust-model.md` §パターン照合ロジックと同一手順で手動集計 |
| 4 | gabriel verdict 分布 | `gabriel-metrics-environment-2026-07-05.md` §集計例の jq（`invoked=true` を母数） |
| 5 | PM 級ダイアログ発火数 | 当該 Wave の K5 宣言・承認記録から手動集計 |
| 6 | `CLAUDE.md` + rules 文字数 | `cat CLAUDE.md .claude/rules/*.md .claude/rules/*/*.md \| wc -m` |

**記録先**: `docs/artifacts/m-1-baseline-w<N>.md`（N = 0, 1, 2, 3, 4）

**確認事項**:
- pytest 実行成功（exit code 0）
- PASS 件数が **W0 ベースライン以上**（NFR-3 / 起点は R-2 W1 末実績 `2ac4e91` / 1043 passed + 14 skipped を W0-M1-T3 で再実測して確定）
- regression なし（既存 PASS テストの FAIL 化なし）

> **新規機構を追加しない**（NFR-2）: 6 項目のいずれについても新規の集計スクリプト・新規ログファイルを作らない。既存コマンド・既存文書の手順をそのまま用いる。

---

## 10. トレーサビリティ検証（WBS 100% Rule）

### 10.1 FR / NFR → Task 対応表

| FR/NFR | 対応 Task | Wave | 完了条件の要点 |
|:-------|:----------|:----:|:---------------|
| FR-1 | §1 全体表 + §2 順序制約 + §5 ゲート | All | 5 Wave のみで構成 / ゲートが独立ステップとして明記 |
| FR-2 | §5 ゲート + W1-M1-T7 | W1→W2 | 3 条件明記 / 記録先明記 / フォールバック手順明記 |
| FR-3 | §3・§4・§6・§7・§8 の各 K5 宣言節 + W1-M1-T6 + W4-M1-T5 | All | 各 Wave 冒頭に PM 級ファイル一覧フィールドが存在 |
| FR-4 | W1-M1-T1, T4, T5 | W1 | 1 条項 = 1 規範文 / 4 軸 + 決定木 / 検出イベント単位の流用 |
| FR-5 | W1-M1-T3 | W1 | 不変制約 4 対象を 4 軸評価前に除外 / ガード 2 引用範囲の grep 検証 |
| FR-6 | W1-M1-T6, W2-M1-T5 | W1, W2 | 判定は W1 / 適用は W2 / 承認 1 イベント |
| FR-7 | W0-M1-T4, W2-M1-T5, W2-M1-T9 | W0, W2 | 台帳 7 列 / 全件記録 / 件数突合 |
| FR-8 | W0-M1-T3, W1-M1-T7, W2-M1-T9, W3-M1-T5, W4-M1-T2 + §2 制約 1 + §9 | All | 6 項目 × 全 Wave 末 / W0 未完了で W2 着手不可 |
| FR-9 | W2-M1-T8 | W2 | 既存機構への接続のみ / 新規ログなし |
| FR-10 | W2-M1-T1, T2 | W2 | roster 4 項目 / 2 ファイルから移動し参照のみ残す |
| FR-11 | W2-M1-T3 | W2 | モデル ID 直書き除去 / 導線 / drift ゼロ |
| FR-12 | W2-M1-T4 | W2 | 3 分岐 / 性質単位の例外登録 / gabriel.md 誤例実測 |
| FR-13 | W4-M1-T1 | W4 | 6 ステップの薄い順序表 / 判断ロジックなし / 整合検証 pytest |
| FR-14 | W2-M1-T1, W4-M1-T1 | W2, W4 | supersede しない明記 / L2・L3 に Opus 不割当 / skill にステップ |
| FR-15 | W2-M1-T6, W4-M1-T5 | W2, W4 | 事後条件 3 点へ改訂 / 移行期規定 / M-1 完了後に発効 |
| FR-16 | W3-M1-T1, T2, T5 | W3 | 軸 S1〜S4 / 上位 4 件を明記 / 動作確認 / 未着手 5 件を明記 |
| FR-17 | W3-M1-T4 | W3 | I-1〜I-6 チェック項目 / 記録 / 不適合時は PM 級差し戻し |
| FR-18 | W4-M1-T3, T4 | W4 | カタログ 7 列 / 2 経路 / 配布コピーはリポジトリ外 |
| FR-19 | W0-M1-T5, W2-M1-T1 | W0, W2 | 一次資料 URL + 取得日 / 未確認は明記 / roster へ反映 |
| FR-20 | W0-M1-T6 | W0 | 12 ファイル grep 実測 / 一致・不一致明記 / PM 級判断 |
| FR-21 | W1-M1-T2, W2-M1-T7 | W1, W2 | トリアージ入力に含める / 3 分岐判定 / R-2 tasks.md へ反映 |
| NFR-1 | W2-M1-T5, W4-M1-T2 | W2, W4 | 発火点・承認ゲート・宣言イベント数の不変を確認 |
| NFR-2 | W0-M1-T3, W0-M1-T4, W2-M1-T8 | W0, W2 | 台帳は記録表 / 新規ログなし / Green State 条件を増やさない |
| NFR-3 | §9 共通手順（全 Wave 末） | All | PASS 数が W0 ベースライン以上 / regression ゼロ |
| NFR-4 | W2-M1-T4 | W2 | `from __future__ import annotations` / 3.10+ 構文不使用 |
| NFR-5 | W2-M1-T4 | W2 | `encoding="utf-8", errors="replace"` / 規約 pytest PASS |
| NFR-6 | メタ情報の明示宣言 + W1-M1-T5, W4-M1-T2, W4-M1-T5 | All | 削減率・行数の下限を完了条件に置かない |

### 10.2 DoD → Task 対応表

| DoD | 対応 Task |
|:---:|:----------|
| DoD-1 | §9 共通手順（全 Wave 末）+ §5 ゲート |
| DoD-2 | W1-M1-T6 + W2-M1-T5 + W2-M1-T9 |
| DoD-3 | W2-M1-T1 + W2-M1-T4 + W4-M1-T1 |
| DoD-4 | W4-M1-T2 |
| DoD-5 | W3-M1-T4 + W4-M1-T4 |
| DoD-6 | W2-M1-T7 + W4-M1-T5 |

### 10.3 検証結果

- **Gap（仕様にあるがタスクにない）**: ゼロ。FR-1〜FR-21（21 件）/ NFR-1〜NFR-6（6 件）/ DoD-1〜DoD-6（6 件）= **33 項目すべてが Task または節に対応**する。
- **Orphan（タスクにあるが仕様にない）**: ゼロ。ただし **W3-M1-T3 のみ FR 番号を持たない**（対応は requirements §7 **Red-3**）。Red-3 は requirements §7 が「`tasks.md` 承認までに解決する」と定めた項目であり孤児ではない（§11 参照）。
- W0-M1-T1 / T2（計器較正）は FR 番号を直接持たないが、**FR-8 測定項目 3 の前提作業**として design §4.5 に位置づけられており、FR-8 行に含めて追跡する。

---

## 11. 未解決質問（Red）の解決状況

requirements.md §7 は「**本節の全項目は `tasks.md` 承認（＝PLANNING 完了）までに解決し、Red を残したまま BUILDING に進まない**」と定める。7 件の解決状況を以下に示す。

| Red | 内容 | 解決場所 | tasks.md での写像先 | 状態 |
|:---:|:-----|:---------|:--------------------|:----:|
| Red-1 | 条項粒度の定義 | design §5.1（1 条項 = 1 規範文 / 閉集合 2 分類） | W1-M1-T1 | **解決** |
| Red-2 | skills / agents の判定軸 | design §7.1（軸 S1〜S4 + 決定木） | W3-M1-T1, T2 | **解決** |
| Red-3 | `quality-auditor` × `code-reviewer` の重複 | design §7.3（2 指標 + 分岐規則を確定 / 当初案の代理指標は実測で否定済） | W3-M1-T3 | **解決（手続き確定）** |
| Red-4 | `verify_model_reference` の実装形態 | design §6.2（新規スクリプト / §9 却下案 2） | W2-M1-T4 | **解決** |
| Red-5 | 削減台帳の配置と形式 | design §6.3（`docs/artifacts/m-1-clause-ledger.md` / 7 列） | W0-M1-T4, W2-M1-T5 | **解決** |
| Red-6 | 安定性ゲートの合格判定 | design §5.5（3 条件表 / 母数・期間・閾値） | §5 ゲート | **解決** |
| Red-7 | R-2 W2/W3 の再スコープ判定 | design §6.5（3 分岐への写像手続き） | W2-M1-T7 | **解決（手続き確定）** |

### 「手続き確定」を解決とみなす根拠（Red-3 / Red-7）

Red-3 と Red-7 は、**判定結果そのものが BUILDING 中の実測・トリアージ出力に依存する**性質を持つ。PLANNING 段階で結果を先に書けば、それは実行前に結論を確定させることであり、design レビューで C2 として棄却した「実行前に分岐が確定する代理指標」と同じ誤りになる。

したがって両 Red は「**判定手続きと分岐規則が一意に定まっていること**」をもって解決とする。W3-M1-T3 / W2-M1-T7 の完了条件は、実行者が判断を挟まずに手続きを適用できる粒度まで書き下してある。

### tasks.md 起票時に新たに解決した項目（design の補完 2 件）

| # | 内容 | 補完先 |
|:-:|:-----|:-------|
| 1 | design §3.2 の PM 級編集計画表が **W0 行を欠く**。W0-M1-T6 は `requirements.md`（PM 級パス）の訂正を含むため、FR-3 受け入れ条件 1 を満たさない | §3 W0 の K5 宣言節で補完 |
| 2 | design §3.2 の W3 行は「宣言不要 / なし」だが、design §7.2 末尾が `requirements.md` FR-16 の訂正を **PM 級**と明記しており矛盾する | §7 W3 の K5 宣言節で補完 |

いずれも design 本文の記述どうしの不整合であり、**tasks.md 側での補完で解消する**（design の再承認は要さない）。ただし design を改訂する機会（W1 以降で design に触れる場合）があれば §3.2 の表に W0 行と W3 の `requirements.md` 行を追記する。

---

## 参照

- `docs/specs/m-1-opus5-migration/requirements.md`（Approved / 本 tasks の入力 / FR-16・FR-20 の訂正対象）
- `docs/specs/m-1-opus5-migration/design.md`（Approved / Task 詳細設計の SSOT）
- `docs/adr/0011-clause-triage-and-model-generation-governance.md`（決定の正本）
- `docs/adr/0001-model-routing-strategy.md`（FR-14 / FR-20 の突合対象）
- `docs/adr/0005-thin-harness-autonomous-governance.md`（不変制約「統治への自己書込禁止」の根拠）
- `docs/adr/0007-magi-v2-gabriel-integration.md`（不変制約 gabriel probe 起動条件の根拠）
- `docs/adr/0009-hga-fable-summoning.md`（W2-M1-T6 の改訂対象 / 追補が新ゲートの正本）
- `docs/adr/0010-global-claude-assets-governance.md`（W3-M1-T4 / W4-M1-T4 の根拠）
- `docs/artifacts/retro-R2-W1-M1-PLANNING-2026-07-25.md`（W0-M1-T1 / W1-M1-T2 の起源）
- `docs/artifacts/gabriel-metrics-environment-2026-07-05.md`（§9 測定項目 4 のスキーマ SSOT）
- `docs/specs/r-2-consolidation/tasks.md`（W2-M1-T7 の反映先 / 書式の型）
- `.claude/rules/auto-generated/trust-model.md`（軸 4 / W2-M1-T8 の接続先）
- `.claude/rules/permission-levels.md`（K5 宣言対象の判定根拠）
- `.claude/rules/fable-l3-protocol.md`（W1 対象 / 帳簿単一原則）
- `.claude/rules/phase-rules.md`（W1 対象）
- `.claude/rules/hga-summoning.md`（W2-M1-T2 / T6 の対象）
- `.claude/rules/model-delegation-prompting.md`（W2-M1-T2 の対象）
- `.claude/rules/upstream-first.md`（W0-M1-T5 / W4-M1-T1 の根拠）
- `.claude/rules/subprocess-encoding-convention.md`（NFR-5 の根拠）
- `.claude/rules/terminology.md`（Task ID 命名規約 / W2-M1-T7 の対象）
- `.claude/scripts/verify_reference_resolution.py`（W2-M1-T4 の出力形式の参照元）

---

## 変更履歴

| 日付 | 変更者 | 内容 |
|:-----|:-------|:-----|
| 2026-07-25 | L1 直 | 初版起票（W0〜W4 の 33 Task + 安定性ゲート 1 件 / 順序制約 3 本 / 各 Wave の K5 宣言節 / トレーサビリティ 33 項目 / Red 7 件の解決状況 + design §3.2 の補完 2 件） |
| 2026-07-25 | L1 直 | 起票時検証で W1-M1-T3 の grep 判定式の欠陥を検出・修正（`grep -v` による機械的除外が false positive 5/6 件を生む / design C1 と同型）。除外フィルタを撤廃し Read 個別確認へ変更、事前実測 5 件の内訳表を追加 |
| 2026-07-25 | L1 | **Approved**（ユーザー承認 / M-1 PLANNING 完了） |
