# R-2 Milestone PLANNING 素材文書

**作成日**: 2026-07-20
**出典**: [retro-R1-2026-07-18.md](./retro-R1-2026-07-18.md) §Step 3 Try（T4〜T26 / 23 件。T1-T3 は R-1 Milestone 内で消化済のため除外）
**位置づけ**: R-2 Milestone PLANNING 開始時に `requirements.md` の入力素材として使う一次整理。**本文書自体は非 SSOT**（requirements.md 確定前の草案）。RFC 2119 キーワードの確定的付与は行わない。
**権限等級**: SE（`docs/artifacts/` 配下）

---

## §1 カテゴリ別一覧表

retro の分類（rule 化候補 5 / 文書精度 6 / 個別 Task 化 12 = 計 23 件）をそのまま踏襲する。「想定権限等級」は本文書作成者の見立てであり、PLANNING で正式決定する。

### 1.1 rule 化候補（5 件）

| ID | 内容 | retro 推奨 | 想定権限等級 |
|:--:|:-----|:-----------|:------------:|
| T4 | rule-002 化検討 — verify_reference_resolution 系（R1-054/055/056/057/058）+ GitHistoryParser regex（R1-061）の**同型 parser drift** 予防 rule。rule-001 の兄弟化 | R-2 で単一 rule-002 として制定（`docs/specs/tdd-introspection-v2.md` 信頼度モデル閾値 2 到達検討） | PM（`.claude/rules/` 配下） |
| T5 | subprocess encoding 統一 rule — Windows cp932 罠（`subprocess.run(text=True)` が `locale.getpreferredencoding()`=cp932 を使い UTF-8 出力 script と衝突） | R-2 で LAM rule 制定（`subprocess.run(..., encoding="utf-8", env=_utf8_env())` パターンを標準化） | PM（`.claude/rules/` 配下） |
| T6 | gabriel 契約厳密検査昇格（R1-059）— substring 弱検査を strict enum 検査に | R-2 でメタ改善（実運用 abort 損失 0 件 = 現状で機能中のため優先度低） | SE（実装内部・非仕様） |
| T7 | gabriel-metrics.log 環境非依存化（I3）— gitignore を外す or `docs/artifacts/gabriel-log.jsonl` へ移動 | R-2 で判定（実 $ 影響なし / metrics 統計の環境間比較が容易化） | SE（ログ配置変更） |
| T8 | mode enum 拡張（I4）— gabriel.md or design.md に `mode: "aot" \| "widescan_verify" \| ...` 列挙 | R-2 でメタ改善 | PM（design.md 変更を伴う場合） |

### 1.2 文書精度（6 件）

| ID | 内容 | retro 推奨 | 想定権限等級 |
|:--:|:-----|:-----------|:------------:|
| T9 | requirements.md 参照は § 見出しで（I1）— hardcoded L 番号回避 | 本 retro 直後 or 次 doc 編集時に markdown anchor（`{#r-g6}` 等）導入検討 | PM（`docs/specs/` 変更） |
| T10 | ADR-0008/0004 supersede 明記（R1-048 引継）— Info 降格済だが retro 議題引継 | R-2 で ADR 個別編集（実害なし） | PM（`docs/adr/` 変更） |
| T11 | CHEATSHEET Rules 一覧完全化（R1-051 引継）— 現状「抜粋」明示可能で Info 降格済 | 現状維持（「抜粋」の意図が明確 = 完全化は不要） | SE（実施する場合は root doc 編集） |
| T12 | 表 re-numbering 規則明文化（I2）— 7b insert vs full re-numbering | R-2 で terminology.md § 追加 | PM（`.claude/rules/` 配下） |
| T13 | 成果物ファイル命名規則（I5）— report 起草日 vs JSON 実行日 | R-2 で terminology.md § 追加（現状は §9 変更履歴で個別説明） | PM（`.claude/rules/` 配下） |
| T14 | "N 件相当" 表現の説明義務（I6）— 集計方法本文明示 | 本 retro 直後の doc 編集規範として意識化（rule 化までは不要） | SE（rule 化しない前提） |

### 1.3 個別 Task 化（12 件）

| ID | 内容 | retro 推奨 | 想定権限等級 |
|:--:|:-----|:-----------|:------------:|
| T15 | evaluation-kpi.md §7 最終判定（W-R4 S3 P9 継続）— 完全削除 / 独立 spec 化 / 現状保持のいずれか | R-2 で PM 級判定 | PM（`docs/specs/` 変更） |
| T16 | fable-l3 × Fable-Alembic snapshot 統合方針（R1-060）— R-1 scope 外の設計判断 | R-2 or 別 Milestone で判定（Alembic 現行運用への影響大 = 独立 Milestone 化推奨） | PM（ADR / rules 相当の設計判断） |
| T17 | R1-037 followup — foreman `tools:` 行 plain `Agent` 化 = user 承認要 | R-2 で user 判定 | PM（ユーザー承認要と retro 明記） |
| T18 | Stop hook G1 testpaths — `pyproject.toml [tool.pytest.ini_options] testpaths = [".claude/tests"]` 追加検討 | R-2 で LAM 側 pyproject 修正 | SE（build 設定） — **2026-07-20 セッションで消化済（§4 参照）** |
| T19 | r1_cycle_detect.py default inventory 挙動 — today 日付前提の見直し（fallback で最新 inventory 探索 or `--inventory` 必須化） | R-2 で script 修正 | SE（script 内部修正） — **2026-07-20 セッションで消化済（§4 参照）** |
| T20 | venv 依存完全性 — jsonschema 以外の移行漏れ検査 | R-2 で `.venv/Scripts/pip list` vs `pyproject.toml` の突合 script 作成 | SE（検査 script 新規作成） |
| T21 | pytest 同名モジュール衝突（`.claude/tests/hooks/test_pre_tool_use.py` vs `.claude/hooks/tests/test_pre_tool_use.py`） | R-2 で pyproject.toml `[tool.pytest.ini_options] rootdir` or 一方 rename | SE（テストファイル改名） — **2026-07-20 セッションで消化済（§4 参照）** |
| T22 | retro skill argument default 動作（W-R4 S3 P12）— 低優先度 | R-2 で upstream 仕様確認 | SE（調査のみ） |
| T23 | deletions.md schema template 化（W-R4 S3 P13）— 6 列 + commit 列を独立 field 化 | R-2 で LAM 側 template SSOT 化 | SE（`docs/artifacts/` 配下テンプレ） |
| T24 | subagent boundary に scratchpad 書込禁止明示（P10 継続）— model-delegation-prompting.md 追記 | R-2 で次 Sonnet 委譲時に反映 | PM（`.claude/rules/` 配下） |
| T25 | built-in `/code-review ultra` 起動候補未表示（P15）— plugin 干渉 or 未インストール | R-2 で plugin 一覧確認 + `.claude/settings.json` `permissions.allow` 確認 | SE（調査） / PM（settings.json 変更が必要な場合） |
| T26 | Alembic 判断依頼（継続議題）— brief 品質 pre-flight 規約化要否 | 応答待ち継続（Alembic 側の応答次第） | 未定（Alembic 側の応答が前提） |

---

## §2 優先度案（High / Mid / Low）

判断軸: **(a) 実害の既発生有無 / (b) 再発頻度 / (c) 修正コスト**。retro 本文の推奨記述を根拠として引用する。

### High（実害既発生 or 高頻度 + 低〜中コストで即着手価値あり）

| ID | 判定根拠 |
|:--:|:---------|
| **T4** | (a) 実害あり: retro §2.5「新規 Python 資産」+ tracker 669/680/782/793/804/815 行で **R1-054〜058/061 の同型 parser drift が複数 issue として deferred 計上**済（本文書 primary_sources 裏取り）。(b) 高頻度: 「同型 parser drift」と retro が明記＝rule-001（3 回発火）と同種の再発パターン。(c) 低コスト: rule-001 の兄弟化のため実装済み構造を流用可 |
| **T5** | (a) 実害あり: retro §Step 3 P2「pytest cp932 罠」= 実バグとして 1 件修復済・残 2 warning が現存（`test_wave2_integration.py` + `test_git_history_parser.py`）。(b) 中〜高頻度: Windows 環境依存のため今後も同型発生の余地。(c) 低コスト: 既に修復パターン（`_utf8_env()`）が確立済で rule 化は文書化のみ |
| **T15** | (a) 実害あり: retro P9「W-R4 S3 retro Problem 継続」= **2 Wave 連続で未決着**（KPI 定義の帰属先が宙に浮いた状態が長期化）。(c) 低コスト: 判定自体は PM 級だが作業量は小さい（削除/独立化/現状保持の三択） |

### Mid（実害小 or 頻度中、コストが中程度）

| ID | 判定根拠 |
|:--:|:---------|
| **T7** | (a) 実害あり: final-audit-report §6.2「4 entries」主張が gitignore により**環境依存で裏取り不能**（retro P6）。(c) 中コスト: gitignore 変更 + 既存ログ移行の判断を要する |
| **T9** | (a) 実害あり: retro P7「requirements.md 更新で破綻リスク」として既に hardcoded 参照が final-audit-report/closure-report に複数存在。(c) 中コスト: markdown anchor 導入は仕様書全体への影響検討を要する |
| **T16** | (a) 実害小: R-1 scope 外の設計判断のため現時点で実害なし。(b) 低頻度だが影響大: retro 自身が「Alembic 現行運用への影響大 = 独立 Milestone 化推奨」と明記。(c) 高コスト: 独立 Milestone 化が前提のため R-2 内では判定のみ |
| **T20** | (a) 実害不明（未検査のため潜在リスク）。(c) 中コスト: 突合 script 新規作成 |
| **T23** | (a) 実害あり: retro P13「6 列 table 意図に対し commit 列がなかった」実バグが 1 度発生済。(c) 低〜中コスト: template 化のみ |
| **T24** | (a) 実害小: retro P10「実質 repo 影響なしで妥当」と明記済（boundary_deviations 2 件は軽微）。(b) 中頻度: 次回 Sonnet 委譲全般に波及する予防的措置。(c) 低コスト: 既存ルールへの追記のみ |
| **T6, T8, T10, T12, T13, T17** | いずれも retro が「実害なし」または「優先度低」と明記（T6「実運用 abort 損失 0 件」/ T10「実害なし」等）。頻度・コストは中程度に留まる |

### Low（実害なし・低頻度・現状維持が推奨されている）

| ID | 判定根拠 |
|:--:|:---------|
| **T11** | retro 推奨が「現状維持（完全化は不要）」と明言 — 着手自体が推奨されていない |
| **T14** | retro 推奨が「rule 化までは不要」と明言 — doc 編集時の意識化のみで足りる |
| **T22** | retro が「低優先度」と明記 |
| **T25** | ローカル環境固有の plugin 干渉調査であり、他 Task への波及なし |
| **T26** | Alembic 側の応答待ちであり LAM 側の裁量で着手不可 |
| **T18 / T19 / T21** | **2026-07-20 セッションで先行消化済**（§4 参照）につき R-2 スコープからは除外。優先度検討は不要 |

---

## §3 R-2 スコープ判定の論点

### 3.1 rule-002 の粒度（T4 関連）

- **論点**: rule-001（SESSION_STATE.md fallback regex 保守）の「R-1 節」削除後、rule-002 を rule-001 の**兄弟ルール**として独立制定するか、あるいは rule-001 を「parser drift 予防」全般に拡張する形で**統合**するかの選択。
- retro T4 の推奨は「rule-001 の兄弟化」＝独立 rule-002 案。理由: rule-001 は SESSION_STATE.md の Milestone/Wave 表記抽出という単一責務に特化しており、verify_reference_resolution 系（R1-054〜058）+ GitHistoryParser（R1-061）の対象は別ファイル・別 parser のため、責務混在を避ける観点で独立が妥当と見られる。
- **未決着点**: `docs/specs/tdd-introspection-v2.md` の信頼度モデル閾値（初期値 2 回）に rule-002 が到達しているかの判定は tracker の deferred 6 件（R1-054/055/056/057/058/061）の発火回数カウント方法次第。同一 Wave 内での複数 issue 検出を「1 回」と数えるか「issue 数分」と数えるかで結論が変わる。PLANNING で明確化が必要。

### 3.2 gabriel-metrics.log の SSOT 位置（T7 関連）

- **論点**: 現状 `.claude/gabriel-metrics.log` は gitignore 対象（ローカル限定）。final-audit-report の「gabriel 4 entries」主張の裏取りが clone 環境で不能という構造的欠陥（retro P6）。
- 選択肢: (1) gitignore を外して repo 管理下に置く（環境非依存だが機微情報混入リスクの検討要）、(2) `docs/artifacts/gabriel-log.jsonl` 等の別ファイルへ移動し集計結果のみ commit する、(3) 現状維持 + final-audit-report 側に「ローカル限定情報」と明記する運用回避。
- retro T7 は (1) or (2) を「R-2 で判定」としており、PLANNING での決定事項に該当。

### 3.3 T16 fable-l3 × Fable-Alembic snapshot 統合方針は独立 Milestone 化推奨

- retro 自身が明記: 「R-1 scope 外の設計判断」「Alembic 現行運用への影響大 = 独立 Milestone 化推奨」。
- **R-2 での扱い**: R-2 requirements.md に Task として組み込まず、**R-2 PLANNING 内で「独立 Milestone 化するか否か」のみ判定**し、実行は別 Milestone に切り出す運用が retro の意図に沿う。R-2 tasks.md に直接タスク化することは推奨されない。

### 3.4 T15 evaluation-kpi.md §7 の 2 Wave 継続未決着

- W-R4 S3 retro（Problem 継続）→ R-1 Milestone retro（P9 として再掲）と**2 段階で先送り**されている。retro は「完全削除 / 独立 spec 化 / 現状保持のいずれか」を R-2 で PM 級判定するよう明記。放置するとさらに 1 Wave 先送りされる構造リスクがあるため、R-2 requirements.md の早期 Task 化が望ましい。

### 3.5 T6 の優先度は「実運用実害ゼロ」が根拠

- gabriel 契約検査（substring 弱検査）の厳密化は、retro が「実運用 abort 損失 0 件」と明記しており、これは「バグは起きていないが理論上の脆弱性がある」パターン。PLANNING で Warning 相当（`code-quality-guideline.md` 基準）として扱うか、Info 相当で見送るかの判断が必要。

---

## §4 本日（2026-07-20）先行消化済み Task の注記

以下 3 件は 2026-07-20 セッションで**先行消化済み**であり、R-2 requirements.md への組み込みは不要（**R-2 スコープから除外**）:

- **T18**（Stop hook G1 testpaths / `pyproject.toml [tool.pytest.ini_options] testpaths` 追加）
- **T19**（r1_cycle_detect.py default inventory fallback 見直し）
- **T21**（pytest 同名モジュール衝突 = rename による解消）

R-2 PLANNING 時にこれら 3 件を再度 Task 化しないよう、requirements.md ドラフト作成者は本節を確認すること。

---

## 最終報告

作成ファイル: `D:/work7/LivingArchitectModel/docs/artifacts/r-2-planning-material-2026-07-20.md`

セクション行数（本ファイル内 見出し基準の概算）:
- §1 カテゴリ別一覧表: 約 35 行（3 表 = rule化候補 5 行 + 文書精度 6 行 + 個別Task化 12 行 + ヘッダ/見出し込み）
- §2 優先度案: 約 30 行（High 3 件 + Mid 7 グループ + Low 6 件の根拠付き）
- §3 R-2 スコープ判定の論点: 約 20 行（5 論点）
- §4 先行消化済み Task の注記: 約 5 行

逸脱の自己申告:
- task boundaries で指定された「作成してよいファイルは 1 件のみ」を遵守。他ファイルの Read / Grep のみ実施（`retro-R1-2026-07-18.md` を Read、`r-1-audit-tracker.md` を Grep で参照）し、編集は行っていない。
- primary_sources として指定された `retro-R1-2026-07-18.md` §Step 3 を一次資料とし、tracker への言及は「deferred 理由の裏取り」目的の補助参照に留めた（T4 根拠の実在性確認のため）。
- RFC 2119 キーワードによる確定的要件化は行わず、「想定」「推奨」等の非確定語を用いた。
- 想定権限等級はすべて本文書作成者（Doc Writer）の見立てであり、PLANNING で正式決定する旨を §1 冒頭に明記した。
