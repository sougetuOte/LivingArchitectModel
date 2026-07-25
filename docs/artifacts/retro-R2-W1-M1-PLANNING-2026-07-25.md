# Retro: R-2 Wave 1 + M-1 PLANNING（2026-07-25）

**実施日**: 2026-07-25
**対象**: R-2 Wave 1（セッション 1-2）+ M-1 PLANNING requirements/design 起票（セッション 3）
**モード**: 軽量（非 AoT / MAGI 合議なし・gabriel probe なし / `decision-making.md` §Execution Flow のモード宣言 MUST 準拠）
**実施者**: L1（Opus 5 / 直実施 = 判断・査定のため委譲せず）
**位置づけ**: 本 retro の Try は **M-1 W1 条項トリアージの入力**となる（2026-07-25 ユーザー決定 / SESSION_STATE §次のステップ 1）

---

## 1. スコープ

| 項目 | 値 |
|:---|:---|
| 期間 | 2026-07-25（単日 3 セッション） |
| Milestone | R-2（Wave 1 完走）/ M-1（PLANNING 進行中） |
| Task | W1-R2-T4 / T5 / T6 / T7 / T8（5 件）+ MAGI 合議 + ADR 2 件 + requirements / design 起票 |
| コミット | 10 件（`983110b` 〜 `7377d0f`） |
| テスト | 980 → **1043 passed** / 14 skipped / 0 failed（regression 0） |

### セッション別コミット

| セッション | 内容 | commit |
|:---|:---|:---|
| 1 | MAGI 合議録（AoT 6 Atom + gabriel probe）/ ADR-0011 Accepted + ADR-0009 追補 | `983110b` `d6eda32` |
| 2 | W1-R2-T4〜T8（rule-002 起票 / subprocess encoding 規約 / gabriel strict enum / スキーマ追記 / mode enum） | `45eef37` `0af0125` `0f55bbd` `351437e` `2ac4e91` |
| 3 | current-phase 切替 / requirements.md Approved / design.md 起票（承認待ち） | `d12cf23` `09fc7e2` `7377d0f` |

---

## 2. 定量分析

| 指標 | 値 |
|:---|:---|
| 実装タスク数 | 5（T4 / T5 / T6 / T7 / T8） |
| PLANNING 成果物 | 2（requirements.md 484 行 Approved / design.md 649 行 承認待ち） |
| テスト追加数 | **+63**（980 → 1043） |
| 新規 rule 制定 | 2（`rule-002.md` / `subprocess-encoding-convention.md`） |
| 既存 rule 改訂 | 1（`trust-model.md` 2 条項 = カウント単位 / N 回目恒久解） |
| 誤例修正 | 14 箇所（subprocess encoding / 9 ファイル） |
| 解消済み issue | 1（R1-059 = gabriel 契約 substring 弱検査） |
| Wave 末ゲート Issue | Critical 0 / Warning 0（G1 通過） |
| L1 検収での介入 | **7 点**（requirements 4 / design 3） |
| 承認イベント消化（NFR-3） | 2 件（#1 K5 一括宣言 / #2 trust-model 単独） |

---

## 3. TDD パターン分析（Step 2.5）

### 3.1 集計結果

最終 `ANALYZED` マーカー（`2026-07-18T21:30:00Z` / retro-R1）以降のエントリ = **13 件**。
内訳: 2026-07-19 が 11 件 / 2026-07-20 が 2 件。**2026-07-25 の 3 セッション分は 0 件**。

`trust-model.md` §カウント単位（1 検出イベント = 1 カウント）で数えると **2 検出イベント**。
同一パターンの 2 回以上発火は**なし** → **ルール候補 0 件**（閾値 2 未達）。

### 3.2 記録 0 件の原因（観測で裏取り済 / F4 #3）

本日 4 つの TDD Task（T4 / T5 / T6 / T8）が Red-Green サイクルを回したにもかかわらず、
`tdd-patterns.log` への記録は 0 件だった。以下を実測した。

| # | 観測対象 | 実測値 |
|:--|:---|:---|
| 1 | `.claude/test-results.xml` | mtime `2026-07-25 10:49` / `tests=1020 failures=0 skipped=15` |
| 2 | `.claude/last-test-result` | `pass pytest` |
| 3 | `post-tool-use.py:163-177` `_record_pass()` | **`prev_was_fail` が True のときのみ** log に追記する |
| 4 | `.claude/logs/post-tool-use.log` | **ファイルごと不在** = WARN 未発生 = `_parse_junit_xml` が None を返した実績ゼロ |

観測 1-4 から、本体コンテキストで実行された pytest は常に `failures=0` かつ直前状態が `pass` であり、
FAIL 記録も PASS 記録も発生しない状態が本日一日継続していた。Red の失敗は Sonnet subagent の
内部で発生し、パイプラインに到達していない。

**未確定の分岐（寄与は未確認 / F4 #4）**: 上記から次の 2 経路のいずれか（または両方）に絞られるが、
既存の成果物からは切り分けできない。

- **経路 (a)**: subagent の Bash 呼び出しで PostToolUse hook が発火しない
- **経路 (b)**: 並列 subagent が `-o addopts=""` を使用したため JUnit XML が更新されず、
  hook が**前回の green XML**を読んだ

経路 (b) の状況証拠は強い。`subprocess-encoding-convention.md:217` の検証コマンドが実際に
`-o addopts=""` 形式であり（T5 の Sonnet subagent が執筆）、`docs/daily/2026-06-02.md` は
「並列サブエージェントの pytest は `-o addopts=""` で共有 `.claude/test-results.xml` clobber を回避」
を既に規約化している。観測 4（WARN 不在 = XML は常に読めていた）とも整合する。

### 3.3 発見の重大性

これは記録が「抜けた」だけの問題ではない。

1. **委譲率に反比例してパイプラインが盲目になる**。`CLAUDE.md` §作業体制は TDD 実装を Sonnet に
   委譲することを既定としており、規律に従うほど `tdd-patterns.log` が空になる。
   `trust-model.md` は §カウント単位で検出イベントを HGA 召喚 / 監査 Stage / gabriel probe まで
   広げたが、**自動記録経路（hook）側には対応する拡張がない**。
2. **経路 (b) が成立する場合、記録の欠落だけでなく汚染が起こりうる**。古い XML に `failures>0` が
   残っている状態で subagent が `-o addopts=""` の green 実行を行うと、hook は無関係な過去の失敗を
   当該コマンドの FAIL として記録する（逆も同様）。

### 3.4 副産物: W1 末ゲート基準の向きの誤り

`docs/specs/r-2-consolidation/tasks.md` W1 末ゲートの G1 基準は
`980 PASS + 15 SKIP 以上、regression 0 維持` と書かれているが、実測は **14 SKIP**。

SKIP を**下限（floor）**で書いているため、skip の減少（= カバレッジ向上方向）が基準違反の向きに出る。
持ち越し議題「SKIP 15→14 の出所未特定」について、**出所は依然未特定**であるものの、
**基準の書き方自体が誤った向きである**ことが確定した。同じ表現が W2 / W3 末ゲートにも波及している
可能性があるため、R-2 W2 再開時に一括確認する。

---

## 4. 定性分析（KPT）

### Keep（続けること）

| # | 内容 |
|:--|:---|
| K1 | **L1 全文検収が実行不能コードを捕捉した**。design §4.1 の gabriel verdict 集計（`json.loads(l)['verdict']`）は実スキーマが `gabriel_output.verdict` にネストし、`invoked=false` 時は null になるため、実行すれば必ず KeyError/TypeError で落ちる。委譲成果物の「全文検収」を省略していたら設計書に埋没していた |
| K2 | **2 名並列委譲（T5∥T6 / T7∥T8）が機能した**。兄弟間衝突なしで 5 commit を 1 セッションで消化 |
| K3 | **Sonnet が baseline の構造的限界を自己申告した**。T5 で「14 箇所修正したのに baseline が 20→20 で動かない」ことを検出し、真の違反数を pytest 静的検査で別途担保した上で規約文書に「baseline の既知の限界」節を明記。取り繕わずに限界を書いた |
| K4 | **委譲先からの逆方向指摘が機能した**。design-architect が「requirements.md のステータスが Draft のまま」という L1 側の反映漏れを自己申告 |
| K5 | **実環境での自然再現が模擬より強い証跡になった**。`/quick-save` の dashboard 生成失敗（`git_history.py:63` の cp932 `UnicodeDecodeError`）が T5 の誤例証跡としてそのまま使えた。design §4.4 は monkeypatch での模擬を設計していた |
| K6 | **retro を tasks.md 起票より先に回す判断**（本 retro そのもの）。Try が条項を増やす方向に働くため、W1 トリアージ表の PM 級一括承認より先に確定させることで判定のやり直しを回避した |

### Problem（問題だったこと）

| # | 内容 | 新規/持越 |
|:--|:---|:---|
| P1 | **TDD 内省パイプラインが委譲 TDD を記録しない**（本日 4 Task / 記録 0 件）。委譲率に反比例して盲目化し、経路 (b) では偽記録も起こりうる（§3 参照） | **新規・重大** |
| P2 | **subagent に一次資料を渡さないと実行不能コードが設計書に入る**。`hga-summoning.md` §primary_sources 追加の根拠（2026-07-06 / R-1 W-R1 S2 事例 #4）が「subagent は rich source を能動的に引かない」と既に警告しており、**同型の失敗を繰り返した**。皮肉なことに、参照すべきスキーマ文書は同日セッション 2 の T7 で自分たちが更新したファイルだった | 新規（同型再発） |
| P3 | **MAGI Phase 0 Grounding に既存 ADR 一覧の棚卸しがない**。議題が「既存規律の全面見直し」だったにもかかわらず合議も gabriel probe も `docs/adr/` を走査せず、ADR-0001 / ADR-0010 との整合を合議**後**の ADR 起草準備で自己検出した。今回は結論を否定せず制約追加で済んだが、順序が逆なら A6（配布ガイダンス）は ADR-0010 の既存 plugin チャネルと二重化した設計を出していた | 持越 |
| P4 | **FR-7 grep baseline の構造的不完全性**。行単位の `grep -v encoding=` は複数行呼び出しを拾えず、「完了後の再計測値と比較可能な形式である」という受け入れ条件が対象言語の構文をまたぐ場合に成立しない | 持越 |
| P5 | **Wave 末ゲート G1 の SKIP 判定が下限（floor）で書かれている**。カバレッジ向上が基準違反の向きに出る（§3.4） | **新規**（持越議題の一部を解決） |
| P6 | **gabriel 所要 294 秒**。NFR-W-C-1 のタイムアウト目安 60 秒（SHOULD）を大幅超過。規約通りなら inconclusive 扱いだが、proceed かつ実ファイル 11 本に基づく具体的指摘のため内容を採用した = **規約と運用が乖離している** | 持越 |
| P7 | **未回収 6 件**。design §4.4 の広い測定式では 28 件ヒットし、T5 の 20 件 baseline 外に 6 件（`test_build_dashboard.py` 4 / `test_wave2_integration.py` 1 / `test_r1_inventory.py` 1）が未着手のまま残存 | 持越 |

### Try（次に試すこと）

各 Try は **M-1 の条項削減目標と衝突しないこと**を設計制約とする。M-1 は条項トリアージ
（Red-1: 1 条項 = 1 規範文）による削減を目的とするため、retro Try を素朴に条項追加として実装すると
W1 の作業量を自ら増やすことになる。**既存条項の修正・置換で吸収する案を第一候補とし、
純増は W1 トリアージの判定にかける**。

| # | Try | 対応 Problem | 条項増減見込 |
|:--|:---|:---|:---|
| T1 | tdd-patterns 記録の委譲盲点を**機構で**塞ぐ。まず経路 (a)/(b) を切り分ける最小 probe（subagent に意図的に 1 件失敗する pytest を実行させ、log 追記の有無を観測）を実施し、結果に応じて hook 側（XML パス分離 / subagent 判定）か規約側（`-o addopts=""` 運用の見直し）を修正 | P1 | **±0**（機構修正 / 規範文の追加なし） |
| T2 | 「既存ログ・既存出力形式を読むコマンドを書かせる委譲では、そのスキーマ文書を `primary_sources` に含める」を `hga-summoning.md` §primary_sources の**既存条項の書式例へ追記**（新規 MUST 文を立てない） | P2 | **±0〜+1** |
| T3 | MAGI Phase 0 Grounding に「`docs/adr/` の既存 ADR 一覧走査」を**既存チェック項目に追記**（新規条項化しない） | P3 | **±0〜+1** |
| T4 | FR-7 の baseline を grep ベースから**機構ベース（pytest 静的検査）へ格上げ**。grep は一次スクリーニング専用と位置づけ直す（FR-7 の既存文の置換） | P4 | **±0**（置換） |
| T5 | Wave 末ゲート G1 の SKIP 表現を下限から**上限側（`≤ baseline` または別枠追跡）へ修正**。W2 / W3 末ゲートへの波及も一括確認 | P5 | **±0**（既存文修正） |
| T6 | NFR-W-C-1 の gabriel タイムアウト目安 60 秒を**実測ベースで見直す**（294 秒実測 / 規約と運用の乖離解消）。数値の改訂であり条項は増えない | P6 | **±0**（数値改訂） |
| T7 | 未回収 6 件を R-2 W2 の Task として明示的に載せる（「既知のギャップ」記述のまま放置しない） | P7 | **±0** |
| T8 | K5（実環境での自然再現 > monkeypatch 模擬）を Knowledge Layer に蓄積 | — | — |

---

## 5. アクション（Step 4）

### 5.1 反映先分類

| # | アクション | 反映先 | 等級 | 優先度 | 処理経路 |
|:--|:---|:---|:---|:---|:---|
| A1 | T1: 委譲 TDD 盲点の probe → 機構修正 | `.claude/hooks/post-tool-use.py` / `trust-model.md` | PM | **高** | **M-1 tasks.md に Task 化** |
| A2 | T2: primary_sources へスキーマ文書条項 | `.claude/rules/hga-summoning.md` | PM | **高** | **M-1 W1 トリアージ入力** |
| A3 | T3: MAGI Phase 0 に ADR 棚卸し | `.claude/skills/magi/SKILL.md` | SE | **高** | **M-1 W1 トリアージ入力** |
| A4 | T4: FR-7 baseline を機構ベースへ格上げ | `docs/specs/r-2-consolidation/requirements.md` | PM | 中 | R-2 W2 再開時 |
| A5 | T5: Wave 末ゲート SKIP 判定の向き修正 | `docs/specs/r-2-consolidation/tasks.md` | PM | 中 | R-2 W2 再開時 |
| A6 | T6: gabriel タイムアウト目安の実測見直し | `docs/internal/06_DECISION_MAKING.md` | PM | 低 | M-1 W1 トリアージ入力 |
| A7 | T7: 未回収 6 件の Task 化 | `docs/specs/r-2-consolidation/tasks.md` W2 | PM | 低 | R-2 W2 再開時 |
| A8 | T8: 自然再現 > 模擬 の知見蓄積 | `docs/artifacts/knowledge/` | SE | 低 | 次セッション以降 |

### 5.2 即時反映しない判断とその理由

**本 retro では A1-A8 のいずれも即時反映しない**。理由は本 retro を tasks.md 起票より先に回した
目的そのものにある。

- A2 / A3 / A6 は**規律に条項を追加・改訂する方向**であり、M-1 W1 の条項トリアージ対象そのものを
  変える。W1 トリアージ表は PM 級一括承認を通すため、承認後に条項が増えれば判定のやり直しになる。
  よって**トリアージの入力として渡し、W1 の中で判定させる**のが正しい経路である
- A1 は機構修正（条項純増ゼロ）だが、**経路 (a)/(b) の切り分け probe が前提**であり、
  probe 未実施の段階で hook を書き換えるのは原因未確定のままの修正になる
- A4 / A5 / A7 は R-2 の仕様書・タスク定義への修正であり、R-2 W2 再開が M-1 W1 トリアージ表の
  承認待ちである以上、W2 再開時にまとめて処理するのが手戻りが少ない

### 5.3 M-1 tasks.md 起票時に必ず反映すること

1. **A1 を Task として明示的に起票する**（probe → 切り分け → 機構修正の 3 手）。
   M-1 は「規律が実際に発火しているか」を問う Milestone であり、
   **発火しない機構を抱えたまま条項だけ削るのは最悪の組み合わせ**になる
2. **A2 / A3 / A6 を W1 トリアージ表の入力リストに含める**（新規追加候補として、
   既存条項と同じ判定軸にかける）
3. Red-1（1 条項 = 1 規範文）の粒度定義に照らし、A2 / A3 が「既存条項への例追加」で
   吸収可能か（= 規範文が増えないか）を W1 で判定する

---

## 6. tdd-patterns.log への記録

本 retro の分析完了に伴い、`ANALYZED` マーカーを追記済み（PG 級 / `trust-model.md` §権限等級）。

```
2026-07-25T04:28:38Z	ANALYZED	retro-R2-W1-M1-PLANNING-2026-07-25	scope=R-2_W1+M-1_PLANNING_2026-07-25	frequent_patterns=0	rule_candidates=0	"delegated-TDD blind spot: 0 entries for 4 TDD tasks (see retro §3)"
```

---

## 7. 参照

- `SESSION_STATE.md`（スコープ・持ち越し議題 7 件の出所）
- `docs/daily/2026-07-25.md` §課題・気づき（セッション 1-3）
- `.claude/tdd-patterns.log`（13 エントリ / 最終 ANALYZED = 2026-07-18）
- `.claude/hooks/post-tool-use.py:163-177`（`_record_pass` の記録条件）
- `.claude/rules/auto-generated/trust-model.md`（カウント単位 / N 回目恒久解 / 閾値 2）
- `.claude/rules/hga-summoning.md` §primary_sources 追加の根拠（P2 の同型先行事例）
- `.claude/rules/subprocess-encoding-convention.md` §grep baseline の既知の限界（P4 / K3）
- `docs/specs/r-2-consolidation/tasks.md` W1 末ゲート（P5）
- `docs/specs/m-1-opus5-migration/{requirements,design}.md`（Try の反映先）
- `docs/artifacts/retro-R1-2026-07-18.md`（前 retro / rule-002 を R-2 送りにした記録）
