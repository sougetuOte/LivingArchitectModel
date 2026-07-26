# M-1 W3 記録（skills / agents の構造改善）

**Milestone**: M-1（Opus 5 移行）/ **Wave**: W3
**起草日**: 2026-07-26
**関連**: `docs/specs/m-1-opus5-migration/tasks.md` §7 / `design.md` §7 / `requirements.md` FR-16・FR-17

> 本ファイルは W3 の正本。W3-M1-T5（Wave 末測定）が §9 共通手順の 6 項目を追記する。

---

## W3-M1-T1: 対象再実測 + スコープ確定 + FR-16 訂正

### 1. 再実測（design §7.2 の判定式をそのまま実行 / 2026-07-26）

判定式: `100 行超` かつ `references/` ディレクトリが実在しない（Markdown リンクの有無では判定しない）。

| # | skill | 行数 | 字数 | est. tok | `disable-model-invocation` | W3 対象 |
|--:|:------|-----:|-----:|---------:|:---------------------------|:--------|
| 1 | `full-review` | 951 | 53,628 | 13,407 | true | **対象** |
| 2 | `goal-driven` | 419 | 18,097 | 4,524 | true | **対象** |
| 3 | `init-harness` | 288 | 8,811 | 2,202 | — | **対象** |
| 4 | `spec-template` | 268 | 6,549 | 1,637 | — | **対象** |
| 5 | `adr-template` | 234 | 5,883 | 1,470 | — | M-1 スコープ外 |
| 6 | `autonomous` | 185 | 11,987 | 2,996 | true | M-1 スコープ外 |
| 7 | `ship` | 180 | 7,551 | 1,887 | true | M-1 スコープ外 |
| 8 | `building` | 136 | 4,355 | 1,088 | true | M-1 スコープ外 |
| 9 | `retro` | 135 | 4,103 | 1,025 | true | M-1 スコープ外 |

対象外（`references/` へ実体分離済）: `lam-orchestrate`（280 行）/ `magi`（331 行）。

**design §7.2 との突合**: **9 件・行数とも完全一致**（drift なし / 2026-07-25 実測から変化なし）。`/doctor`（2026-07-26）の trim は `.claude/rules/` と `CLAUDE.md` に閉じており、skills には及んでいないことの傍証でもある。

**est. tok は字数 ÷ 4**（`/doctor` の実測換算比と同一 = 23,746 字 ≈ 5.9k est. tok に整合）。

### 2. upstream 裏取り（context7 / 2026-07-26 / `upstream-first.md` §設計フェーズへの適用）

| # | 事実 | 状態 | 出典 |
|--:|:-----|:-----|:-----|
| 1 | SKILL.md の **body は常時ロードされない**。起動時に載るのは skill description のみで、body は「実際にその skill を使ったときだけ」ロードされる | **確認** | `code.claude.com/docs/en/context-window`（Skill descriptions の項） |
| 2 | `disable-model-invocation: true` の skill は **description すら起動時リストに載らない**（`/name` で呼ぶまで完全に context 外） | **確認** | 同上 |
| 3 | 3 レベル構造（SKILL.md = overview and navigation / 参照ファイル = loaded when needed）の存在と分割の型 | **確認** | `code.claude.com/docs/en/slash-commands`（Skill Directory Structure） |
| 4 | 「body 約 5,000 tok」という目安値（W0-M1-T5 記録） | **未確認** | 狙い撃ち 2 クエリで upstream に出現せず。**スコープ判断の根拠に用いない** |

**#3 の細部の差**: upstream の例は skill 直下のフラットファイル（`reference.md` / `examples.md`）だが、LAM の既存 2 skill（`magi` / `lam-orchestrate`）は `references/` サブディレクトリを使う。どちらも「必要時ロードの補助ファイル」であり型としては同一のため、**LAM の既存慣行（`references/`）を維持**する（W0-M1-T5 申し送り 2「独自の分割方式を発明しない」に反しない）。

### 3. スコープ再評価の結論（tasks.md W3-M1-T1 完了条件 / PM 級承認済 2026-07-26）

**結論: 上位 4 件を維持（件数を拡大しない）。**

**根拠 1 行**: upstream 実測で **SKILL.md の body は常時ロードされない**と確認されたため、分割は M-1 の趣旨である常時ロード量の削減に寄与せず、対象拡大の費用対効果は当初想定より低いと判定した。

補足（判断の内訳）:

- 当初の「4 件打ち切り」の前提は「分割の効果が未知数」だった。この前提は変化したが、**変化の向きは拡大側ではなく縮小側**だった。W3-M1-T2 の効果は「常時ロードの削減」ではなく「**その skill を起動したときの一発のコストの削減**」である
- 常時ロードされる skill 由来のコストは、`disable-model-invocation` を持たない 5 skill（`adr-template` / `init-harness` / `lam-orchestrate` / `magi` / `spec-template`）の description 計 **2,742 字 ≈ 685 est. tok** のみ。既にほぼ絞り切れており、M-1 で触る価値はない
- 上位 4 件の総量 **21,770 est. tok** のうち `full-review` 単独が **13,407（61.6%）**。効果の大半は 1 件に集中している

**既知の不整合（記録に残す）**: 「上位 4 件」は design §7.2 が定めた**行数降順**である。est. tok 降順では `autonomous`（2,996）と `ship`（1,887）が `spec-template`（1,637）を上回るため、順位の基準を変えると構成が変わる。本 Wave では design の定義（行数降順）と requirements の「`full-review` を含む 4 件」を維持し、構成は変更しない。差は小さく、実効の薄い対象は W3-M1-T2 の**「切れ目なし → 保全」分岐**で正直に落とせる設計になっている。

### 4. FR-16 訂正（PM 級 / 実施済）

`requirements.md` FR-16 の説明文と受け入れ条件 2 を本実測へ更新した。

| 箇所 | 旧 | 新 |
|:-----|:---|:---|
| 説明 | 「優先対象は 100 行超かつ外部参照ゼロの **4 skill**」 | 「実測は **9 件**、うち W3 対象は行数降順の**上位 4 件**」＋未着手 5 件の明記 |
| 受け入れ条件 2 | 「grep 実測で列挙され、優先対象 4 件が明記されている」 | 「実測で列挙され（**9 件**）、うち優先対象 **4 件** が明記されている」 |
| — | （なし） | スコープ再評価の結論と根拠、および「body 約 5,000 tok」を**未確認**とする注記を追加 |

**訂正の必要性**（design §7.2 が指摘した矛盾）: 旧 FR-16 は「4 件」と「`full-review` を含む」を同時に要求していたが、旧判定式では `full-review` が対象外となり、新判定式では 9 件になる。**どちらの判定式でも同時には成立しない**記述だった。

### 5. 未着手 5 件（M-1 スコープ外 / W3-M1-T5 で Wave 完了記録へ再掲）

`adr-template`（234 行 / 1,470 est. tok）/ `autonomous`（185 / 2,996）/ `ship`（180 / 1,887）/ `building`（136 / 1,088）/ `retro`（135 / 1,025）。

**M-1 スコープ外へ送った理由**: 上位 4 件で requirements FR-16 の件数要求を満たすため。加えて上記 §3 のとおり、分割は常時ロード量に寄与しないことが判明しており、拡大の費用対効果が低い。

---

## W3-M1-T3: `quality-auditor` × `code-reviewer` 重複判定（Red-3）

### 指標 1: 起動実績の直接証跡（2026-07-26 再実測）

| agent | ディレクトリ最終更新 | 蓄積ファイル |
|:------|:---------------------|:-------------|
| `code-reviewer` | **2026-06-11** | `MEMORY.md` + 3 件（hook 構造 / hooks セキュリティ / テスト構造） |
| `quality-auditor` | **2026-06-19** | `MEMORY.md` + 1 件（magi reflection 監査） |

**design レビュー時（2026-07-25）から変化なし**。どちらも死んでいないが、どちらも **1.5 か月**更新されていない。

> **限界（design §7.3 の明示を再掲）**: 本指標が示すのは「起動されたことがあるか」と「最後に知見を書いた日」のみ。**起動回数は測れない**（起動しても memory へ書かなければ更新されない）。回数の集計機構は追加しない（NFR-2）。

### 指標 2: 責務定義の重複度（Red-3 の本題）

#### `description` の並置

| agent | `description` が指す起動条件 |
|:------|:-----------------------------|
| `quality-auditor` | 「品質監査に特化。コード品質、ドキュメント整合性、アーキテクチャ健全性を検証。**AUDITING フェーズでの監査作業で使用推奨**」＝ **フェーズ駆動** |
| `code-reviewer` | 「コードレビューの専門。LAM の品質基準に基づいたレビュー。**Use proactively after code changes** to review quality, security, and maintainability」＝ **イベント駆動** |

#### 判定 1: 起動条件に重なりがあるか → **成立（重なりあり）**

「**AUDITING フェーズ中にコードを変更した直後**」は両方の起動条件を同時に満たす。加えて両者とも掲げる観点が「品質・セキュリティ・保守性」で一致しており、**呼ぶ側がどちらを選ぶべきか description から判断できない**。

#### 判定 2: 一方が他方の真部分集合か → **成立（`code-reviewer` ⊂ `quality-auditor`）**

`code-reviewer` のレビュー観点 5 つは、すべて `quality-auditor` 側に対応節が存在する。

| # | `code-reviewer` の観点 | `quality-auditor` の対応 |
|--:|:-----------------------|:-------------------------|
| 1 | コード品質（Quality Gates） | §コード品質監査（命名・可読性 / 構造・設計 / エラー処理 / テスト） |
| 2 | コード明確性（Clarity over Brevity） | **同名節が存在**（§コード明確性（Clarity over Brevity）） |
| 3 | セキュリティ | §セキュリティ監査（OWASP Top 10 / 機密情報） |
| 4 | ドキュメント整合性 | §ドキュメント整合性監査 + 仕様ドリフトチェック |
| 5 | モジュール間帰責（契約カード注入時のみ） | **同名・同括弧書きの Step 2.5 が存在** |

`quality-auditor` はさらに以下を**単独で**持つ: 構造整合性チェック（v4.0.0 / スキーマ・参照・データフロー・設定・ドキュメント間の 5 種）/ 仕様ドリフトチェック / 3 Agents Analysis / 監査レポート出力形式。

観点 2 と観点 5 が**括弧書きまで一字一句同一**であることから、両者は同一の記述を出自とする派生関係にあると判断する。行数は `code-reviewer` 97 行 / `quality-auditor` 328 行。

### 分岐判定（tasks.md W3-M1-T3 完了条件）

判定 1・判定 2 はともに成立するため、tasks.md の条文上は「統廃合を提案する」分岐に該当する。**初回はそのとおり一本化を提案したが、参照実態の調査により提案を撤回し、「それ以外」分岐＝`description` の書き分けを採用した**（2026-07-26 / ユーザー承認済）。撤回の経緯を以下に残す。

#### 撤回の根拠: `code-reviewer` は現役の実行部品である

`code-reviewer` への参照を全域走査した結果、**死んだ agent ではなく `/full-review` パイプラインの稼働部品**であることが判明した。

| 参照元 | 実体 |
|:-------|:-----|
| `.claude/skills/full-review/references/stage-2.md:70-73` | Stage 2 が **`code-reviewer` を 3 並列**で起動（(1) ソース品質 / (2) テスト品質 / (3) セキュリティ）＋ `quality-auditor` 1 の **4 並列構成** |
| `.claude/skills/full-review/references/stage-1.md:57` | セキュリティ Issue を `code-reviewer` へ優先的に渡す |
| `.claude/skills/lam-orchestrate/SKILL.md:157` | 「コードレビュー系 → `code-reviewer`」の分配表 |
| `.claude/tests/rules/test_reference_resolution.py:93` | `_resolve_agent("code-reviewer") is True` を **assert**（削除すれば FAIL） |
| `.claude/hooks/tests/test_subagent_boundary.py:57` | `subagent_type` の値として使用 |
| `.claude/rules/fable-l3-protocol.md:170` | 判定系 subagent として列挙（**PM 級ファイル**） |

#### 判定軸の欠落（本 Task の方法論上の教訓）

**真部分集合であることが、まさに `code-reviewer` を「安い並列ワーカー」たらしめている。** 97 行 vs 328 行であり、`full-review` は 3 並列で起動するため、置換すると 1 回のレビューで **3 × 231 行**ぶんプロンプトが増える。加えて `quality-auditor` の固有部分（構造整合性チェック / 仕様ドリフト / 3 Agents Analysis / レポート形式）は、ソース品質担当のワーカーには不要な積荷である。

design §7.3 が定めた 2 指標（起動実績・責務定義の重複度）は**守備範囲**しか見ておらず、**運用上の役割（軽量並列ワーカーか、横断監査か）を捉える軸を持っていなかった**。「守備範囲が包含関係にある」ことと「統合すべき」は別である。指標 1（agent-memory の最終更新日）も、`full-review` 経由の起動では memory を書かないため**稼働実態を捉えられていなかった**。

> **W4 retro への申し送り**: agent の統廃合判定には「**呼び出し側の実参照**（どの skill / test が subagent_type として指名しているか）」を軸に加えること。memory の更新日と description の重複度だけでは、稼働中の部品を死んだ部品と誤認する。

#### 採用: `description` の書き分け（起動条件の排他化 / 実施済）

スコープの広狭と役割で切り、呼ぶ側が迷わないようにした。

| agent | 新しい起動条件 |
|:------|:---------------|
| `quality-auditor` | **リポジトリ横断**の品質監査。単一差分では見えない検証（構造整合性 / 仕様ドリフト / アーキテクチャ健全性）＋ 3 Agents Model の改善提案とレポート。AUDITING の全体監査と `/full-review` Stage 2 の QA 枠 |
| `code-reviewer` | **単一の変更差分**に対する短距離レビュー（軽量・並列ワーカー向け）。コード品質 / テスト品質 / セキュリティのうち呼び出し側が指定した **1 観点**を担当。フェーズ非依存。`/full-review` Stage 2 では観点別に 3 並列 |

両 description に相互参照（「〜には他方を使うこと」）を明記した。`code-reviewer` 側には守備範囲が包含されることと、それでも使い分ける理由（軽量ゆえの並列ワーカー）を明記している。

**agent の削除は行っていない**（tasks.md「本 Task では提案までとし agent の削除を実行しない」を遵守）。`code-reviewer` の agent-memory 14.5KB も現状維持（統廃合しないため移送・破棄の必要が消滅）。

> **訂正記録**: 初回の提案時に「agent-memory の消失は不可逆」と記述したが、`.claude/agent-memory/` は **git 管理下**（`git ls-files` で 42 ファイル確認）であり **可逆**である。

---

## W3-M1-T2: progressive disclosure 化の実施（上位 4 件）

### 実施方式

**本文の retype を禁じ、`sed -n 'A,Bp'` による行範囲抽出のみで実施**した（Windows の大規模 Write 破損実績への対処 / `claude-code-malformed-write-bug` 既知事象）。切断点は事前にコードフェンス内外を判定し、フェンス内の `## ` 見出し（テンプレート本文）を誤って切断点に採らないようにした。

### 軸 S1・S3 による切れ目の判定結果

| skill | 切れ目 | 判定根拠 |
|:------|:------:|:---------|
| `full-review` | **あり** | 6 Stage の逐次パイプライン。Stage 4/5 は Stage 3 が issue を出したときのみ到達（軸 S3）。Stage 0 は無条件実行のため本体に残置（軸 S3 の保全側） |
| `goal-driven` | **あり** | 三段階ルート詳細・bound 機構はフロー [3]/[6] からの参照時のみ必要（軸 S1）。実装ステータス・Loop Engineering 観点・参照文献は実行手順ではない（軸 S1） |
| `init-harness` | **あり** | テンプレート定義は Step 4.2 到達時のみ必要（軸 S3）。Step 1-3（dry-run 範囲）では不要 |
| `spec-template` | **あり** | 3 テンプレートは選択ガイドで 1 種類に絞られた後、その 1 つだけが必要（軸 S3）。3 つとも読む状況は存在しない |

**保全した要素（軸 S4 = 契約）**: 全 4 件で frontmatter（`name` / `description` / `version` / `disable-model-invocation` / `argument-hint` / `paths` / `allowed-tools`）を本体に残置。原本との diff で完全一致を確認済み。

### 生成物

| skill | SKILL.md | `references/` 配下 |
|:------|---------:|:-------------------|
| `full-review` | 951 → **177 行** | `stage-1.md` 108 / `stage-2.md` 241 / `stage-3.md` 180 / `stage-4.md` 105 / `stage-5.md` 139 / `scalable-code-review.md` 15 |
| `goal-driven` | 419 → **336 行** | `route-and-bound.md` 55 / `background.md` 33 |
| `init-harness` | 288 → **218 行** | `templates.md` 74 |
| `spec-template` | 268 → **68 行** | `template-feature-spec.md` 105 / `template-api-spec.md` 69 / `template-data-model.md` 36 |

### 初回ロード量の変化

| skill | 前 | 後 | est. tok |
|:------|---:|---:|:---------|
| `full-review` | 53,628 字 | 8,760 字 | 13,407 → **2,190** |
| `goal-driven` | 18,097 | 14,296 | 4,524 → **3,574** |
| `init-harness` | 8,811 | 7,294 | 2,202 → **1,823** |
| `spec-template` | 6,281 | 2,580 | 1,570 → **645** |
| **計** | | | **21,703 → 8,232（-62%）** |

> 前の値は `git show HEAD:`（LF）、後の値は作業ツリー（CRLF）から取得しているため、前の値は行数分だけ小さく出る。削減幅はごく僅かに過小評価されている。
>
> **`goal-driven` の削減は 21% に留まる**。フロー [1]〜[9]（250 行）が無条件実行のため保全側であり、切れ目が限定的だったことによる。分割そのものを目的化しない設計（design §7.1 決定木）に従った結果であり、失敗ではない。

### 検証（L1 で独立に再実行 / 4 件すべて）

| 検証 | 結果 |
|:-----|:-----|
| **内容同一性**（原本 vs 退避ファイル再結合の `diff`） | **4/4 差分ゼロ** |
| 行数保存 | 4/4 一致（951 / 419 / 288 / 268） |
| frontmatter 一致 | **4/4 完全一致** |
| コードフェンス整合（全 15 ファイル） | **奇数個の fence ゼロ**（分割で開閉が割れていない） |
| `references/` リンクの解決 | **未解決リンクゼロ** |
| symlink 判定（ADR-0010 I-3） | **全 11 ファイルが実体ファイル** |

### 動作確認（FR-16 受け入れ条件 3）— **未充足。構造検証のみ**

**正直に記録する**: 「実際に起動して振る舞い不変を検証する」は**実施していない**。

| skill | 直接起動の可否 | 未実施の理由 |
|:------|:---------------|:-------------|
| `init-harness` | 可（skill 一覧に登録あり） | 実行するとプロジェクトを scaffold する副作用がある |
| `full-review` / `goal-driven` | `/name` のみ（`disable-model-invocation: true`） | 長時間パイプラインで git / 状態ファイルへの副作用がある |
| `spec-template` / `adr-template` | **不可** | `paths:` を持つパススコープ skill で、名前起動できない（`Unknown skill` / **分割前の HEAD 版でも同じ**＝本 Wave の変更とは無関係） |

**得られている間接証跡**: (1) 分割後に `init-harness` がセッションの skill 一覧へ description 付きで列挙された＝レジストリが新 SKILL.md を正常に再パースした実証、(2) frontmatter（＝発火条件）の完全一致、(3) 本文の diff 差分ゼロ、(4) 参照リンクの全解決。

**残る未検証リスク**: 「参照先を読みに行かず素通りする」挙動。構造検証では捕捉できない。**M-1 スコープ内で消化するなら、小さな対象への `/full-review` 実走 1 回が最小の検証**となる（W4 で判断）。

### 付随して発見した事項（Task を増やさない / HGA #17 準拠のため記録のみ）

**`spec-template` / `adr-template` の `paths:` glob が現行の spec 配置と部分的に噛み合っていない。**

- `spec-template` の `paths: docs/specs/*.md` は `docs/specs/` **直下の 15 件**にはマッチするが、`docs/specs/<milestone>/` **サブディレクトリ配下（12 ディレクトリ）にはマッチしない**。M-1 / R-2 等の現行 Milestone の spec はすべて後者にあり、**現行の運用では発火しない**
- `adr-template` の `paths: docs/adr/*.md`（11 件）は直下運用のため問題なし

**修正を自動では行わない**理由: glob を `docs/specs/**/*.md` に広げると、Milestone spec を編集するたびに skill 本体が注入され、**常時ロードではないが編集のたびのロードが増える**。W1 以降の削減方針とトレードオフになるため、採否は PM 級判断に委ねる。

---

## W3-M1-T4: ADR-0010 I-1〜I-6 適合確認（FR-17）

| I | 確認観点 | 判定 | 根拠 |
|:--|:---------|:----:|:-----|
| I-1 | progressive disclosure 化が `~/.claude/skills/` への直置きを発生させない | **適合** | 変更は全て `.claude/skills/`（project 層）に閉じる。`git status --short` の全エントリがリポジトリ内パス |
| I-2 | plugin の enable 操作を行っていない | **非該当** | 本 Wave はプロジェクト内変更のみ。プラグイン 5 件の無効化は W2 セッションの `/doctor` であり本 Wave 外 |
| I-3 | `references/` へ退避したファイルが実体ファイルで symlink でない | **適合** | 全 11 ファイルを `os.path.islink` で判定し symlink ゼロ。`ls -la` でも全て `-rw-r--r--` |
| I-4 | LAM 内部の相互参照に plugin 名前空間の対象がない | **適合** | 本 Wave で新規追加した相互参照は全て相対パス `references/*.md`。plugin 名前空間への参照ゼロ |
| I-5 | personal 層の共有可変資産（hooks / settings）に変更を加えていない | **非該当** | `git status` は project 内変更のみ。`~/.claude/` への書込みなし |
| I-6 | agents 統廃合検討が `~/.claude/agents/` への直置きを発生させない | **適合** | W3-M1-T3 は**提案のみ**でファイル変更ゼロ |

**不適合ゼロ** → FR-17 受け入れ条件 3 の PM 級差し戻しは**発生しない**。ADR-0010 への追記も不要（条件付き K5 宣言は未使用）。

---

## W3-M1-T5: W3 末測定（§9 共通手順の 6 項目）

| # | 項目 | W2 末 | **W3 末** | 差分 |
|:-:|:-----|:------|:----------|:-----|
| 1 | pytest 全数 | 1085 passed / 14 skipped | **1095 passed / 14 skipped** | **+10**（`verify_model_reference` FP 修正の新規テスト）/ **regression ゼロ** |
| 2 | Green State 件数 | Critical 0 / Warning 0 | **Critical 0 / Warning 0** | 変化なし |
| 3 | `tdd-patterns.log` FAIL→PASS 率 | 0 件（W1 は判定のみの Wave） | **0 件** | 下記注記 |
| 4 | gabriel verdict 分布 | probe 0 件（log 最終更新 2026-07-18） | **probe 0 件**（同上・log 不変） | 変化なし |
| 5 | PM 級ダイアログ発火数 | — | **1 回**（`requirements.md` FR-16 訂正 / K5 宣言済） | — |
| 6 | `CLAUDE.md` + rules 文字数 | 169,030 字 / 2,905 行 | **166,638 字 / 2,898 行** | **-2,392 字 / -7 行** |

### 項目 6 が W3 の成果を反映しない件（**重要 / 数値が動かないことが正しい**）

**項目 6 の測定対象は `CLAUDE.md` + `.claude/rules/` のみであり、`.claude/skills/` を含まない。** したがって W3 の progressive disclosure 化（-13,471 est. tok）は**この数値に一切現れない**。

上表の **-2,392 字は W2 残件の `/doctor` trim（commit `1aa50a9` / 履歴記述 54 行の削除）に帰属**し、W3 の作業に由来しない（W2 末測定は `/doctor` 実行前に取得されていたため差分として現れている）。

これは W3-M1-T1 §2 の upstream 裏取り（**SKILL.md の body は常時ロードされない**）と整合する。skills の分割は起動時コンテキストではなく **skill 起動時の一発のコスト**に効くため、常時ロードを測る項目 6 では原理的に検出できない。

### 項目 3 の注記（測定手順の既知ギャップ）

本 Wave の TDD サイクル（`verify_model_reference` の Red→Green）は `tdd-patterns.log` に記録されていない。原因は検証コマンドに `-o addopts=""` を用いており、`pyproject.toml` の `addopts` にある `--junitxml=.claude/test-results.xml` が無効化され、PostToolUse hook が読む JUnit XML が生成されなかったため。

**新規機構を追加しない**（NFR-2）ため本 Wave では対処しない。記録のみ残す。

---

## W3 未着手 5 件（M-1 スコープ外 / T5 完了条件の明記事項）

| skill | 行数 | est. tok | M-1 スコープ外へ送った理由 |
|:------|-----:|---------:|:---------------------------|
| `adr-template` | 234 | 1,470 | 上位 4 件で requirements FR-16 の件数要求を満たすため |
| `autonomous` | 185 | 2,996 | 同上 |
| `ship` | 180 | 1,887 | 同上 |
| `building` | 136 | 1,088 | 同上 |
| `retro` | 135 | 1,025 | 同上 |

共通の補足理由（W3-M1-T1 §3）: 分割は常時ロード量に寄与しないことが upstream 裏取りで判明しており、対象拡大の費用対効果は当初想定より低い。**silent な打ち切りではなく、対象として認識したうえでの明示的な見送り**である。

---

## 追記: FR-16 受け入れ条件 3（動作確認）の充足記録 — W4 で実施（2026-07-26）

W3 完了時点で **未充足**として W4 に持ち越していた項目（「progressive disclosure 化の実施後、対象 skill の主要な発火条件・振る舞いに変更がないことが動作確認で検証されている」）を、W4 着手時に消化した。**判定: 充足**。

### 方法

W3 の作業内容を知らない subagent を「これらの skill を初めて使う実行者」として起動し、`SKILL.md` を起点に指示を追わせ、**読んだファイルを実測**させた。合否判定は subagent に行わせず、L1 が git 実測で裏取りした（subagent には `git log` / `git show` を禁じ、「今そこにあるファイルだけを読む実行者」に固定した）。

2 ラウンド実施した。第 1 ラウンドは停止条件を「最初の実作業ステップを開始できるまで」としたため `references/` への遷移が 1 度も発生せず、**risk を検証できなかった**（この設計ミスは L1 側にある）。第 2 ラウンドで開始地点を参照先への遷移点（`full-review` = Stage 1 / `goal-driven` = フロー [3] / `init-harness` = Step 4.2 / `spec-template` = 機能仕様書ケース）に設定し直して再実行した。

### 結果

| skill | 参照先への到達 | ハンドオフ | 備考 |
|:------|:---|:---|:---|
| `full-review` | `references/stage-1.md` | **成立** | 実行可能なコマンドが参照先に記載され、そのまま Stage 1 を開始できる |
| `goal-driven` | `references/route-and-bound.md` | **成立** | 本体のフロー [3] だけでも開始可能。参照先は補強 |
| `init-harness` | `references/templates.md` | **不成立** | CHANGELOG.md / SESSION_STATE.md のテンプレート本文が参照先に無い |
| `spec-template` | `references/template-feature-spec.md` | **成立** | 完全なインラインテンプレートが揃っている |

### 「不成立 1 件」を W3 の退行としない根拠（git 実測）

| 指摘 | 実測 | 帰属 |
|:-----|:-----|:-----|
| `init-harness` の CHANGELOG / SESSION_STATE 本文が無い | W3 **直前版でも**「Keep a Changelog 1.1.0 雛形 + `[Unreleased]` セクション。」の 1 行のみ（`git show 7454629^` で確認） | **既存欠陥** |
| `goal-driven` の判定条件が本体と参照先で重複 | 「rubric 項目数」の出現回数は W3 前後とも **2 回**で不変 | **既存**（分割で増えていない） |
| `full-review` 本体が Stage 1 の no-op 制限に触れていない | no-op 注記は W3 直前版にも 6 箇所存在。分割で本体から `stage-1.md` 側へ移動した | **Info**（参照先を読めば見える = ハンドオフは成立） |

### 発火条件と情報量の不変確認

- **frontmatter の W3 前後 diff**: `full-review` / `goal-driven` / `init-harness` の 3 件は**完全同一**。`spec-template` のみ `paths:` に `docs/specs/*/*.md` が 1 行**追加**（付随 commit `de47334` の意図的な実配置整合。発火機会は減らない）
- **本体 + `references/` の総量**: 4 件すべて W3 直前版**以上**（`full-review` +861 / `goal-driven` +357 / `init-harness` +212 / `spec-template` +521 字）。差分は分割に伴う見出し・参照表の増分であり、**情報の欠落はゼロ**

以上より、W3 の progressive disclosure 化による**発火条件および振る舞いの変更はゼロ**である。

### 本確認で新たに検出した既存欠陥（M-1 スコープ外 / 別途処理）

1. **`init-harness` Step 4.2 が実行不能** — SKILL.md は「参照先のインライン文字列を使用」と指示しているが、CHANGELOG.md / SESSION_STATE.md の本文が `references/templates.md` に存在しない。W3 以前から同じ状態
2. **`spec-template` のテンプレート選択ガイドが実配置と不一致** — 案内する命名規則（`feat-*` / `api-*` / `data-*` / `ui-*`）に一致する実ファイルは `docs/specs/ui-lam-slides.md` の 1 件のみで、実配置は `docs/specs/<milestone>/{requirements,design,tasks}.md` が主。付随 commit `de47334` は `paths:` のみ整合させ本文は未整合
3. **`spec-template` の UI テンプレートが不在** — 選択ガイドは 4 種を提示するが参照表は 3 種のみ。W3 以前から実体なし

いずれも W3 由来ではないため W4 のスコープに取り込まない（出口宣言 (a) 一回性との整合）。**silent に落とさず本節に記録する**。

> **追記 (2026-07-26 / M-1 スコープ外の別セッションで消化 = 3 件すべて解消)**:
> 1. `references/templates.md` に `CHANGELOG.md`（Keep a Changelog 1.1.0）と
>    `SESSION_STATE.md`（見出し 6 種 / `/quick-save` §1 と対応）のインライン本文を追記し、
>    Step 4.2 の指示文を参照先の実体に合わせた
> 2. `spec-template/SKILL.md` の選択ガイドを「Step 1 配置を決める（Milestone ディレクトリ形式 /
>    単独 flat 形式）→ Step 2 内容の種類でテンプレートを選ぶ」に再構成。`<milestone-slug>` の SSOT は
>    `.claude/rules/terminology.md` §4 を参照する形にした（同ファイルは未変更 = PM 級ダイアログ発生なし）
> 3. UI テンプレートは**新設せず選択ガイドから行を落とした**。判断根拠は (i) 単独 UI 仕様の実績は
>    `docs/specs/ui-lam-slides.md` 1 件のみで、当時もテンプレート不在のまま書けている
>    (ii) 機能仕様書テンプレートに `### UI（該当する場合）` 節が既にある
>    (iii) 出口宣言 (c) no-net-growth に照らし新ファイル 1 件の純増を避ける。
>    代替として機能仕様書テンプレートへ誘導する 4 行を置いた
>
> 検証: `.claude/tests/rules/` 84 passed / 全 suite **1103 passed + 14 skipped**（W4 末と同値 = regression ゼロ）/
> `verify_reference_resolution.py --wave all` total_drifts 0。
