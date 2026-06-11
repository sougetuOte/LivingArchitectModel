# Retro: B-2 full-review 完了（真の Green State 達成）

**実施日**: 2026-06-11
**対象**: B-2 LAM 全体 full-review（iter1〜7 監査ループ）
**承認**: PM 査定完了・ユーザー承認取得（2026-06-11）

---

## 1. スコープ

**期間**: 2026-06-09（前セッション・D-1/W-12 修正直後） 〜 2026-06-11（iter7 Green State 確定）

**B-2 関連コミット（`git log --oneline --since=2026-06-09` 抽出・B-2 直接関連分）**: 8件

| hash | subject |
|------|---------|
| `77e602c` | docs(audit): B-2 iter4-7 監査レポート + Green State 達成記録 + セッション記録 |
| `46da9e4` | docs(specs): B-2 PM3/PM4 決着の仕様同期 |
| `4e45f14` | test(hooks): B-2 iter4-6 のテスト網羅補完 |
| `ec84f13` | fix(hooks): B-2 iter4-6 のエラー黙殺解消・防御対称化・Dead Code 削除 |
| `6f73732` | docs(audit): B-2 iter1-3 監査レポート + SKILL 表記更新 + セッション記録 |
| `7a6eb99` | docs(specs): B-2 iter1 PM級 8 件決着の仕様同期 |
| `60942a2` | test(hooks): B-2 監査対応のテスト追加・品質改善 |
| `52eecc7` | fix(hooks): B-2 full-review iter1-3 の堅牢性・契約・セキュリティ修正 |

（参考: `be95f74` e2e fixture PG 修正、`bece7f4` D-1 修正、`7078b22` C-2 改訂は B-2 ループ外だが同期間のコミット）

---

## 2. 定量分析

### 確定 Issue 推移（監督査定後・確定値）

**確定 Warning 推移（iter7 総括表を正とする）**: `40 → 4 → 5 → 9 → 1 → 3 → 0`（Green State）

> **注釈（集計基準差）**: iter1 の「40」は iter7 レポート総括表（`2026-06-11-iter7.md`）および SESSION_STATE の値。
> iter1 レポート本文の査定後確定値は C1 + W23 + Info修正8 = **32 件**であり、集計基準差がある
> （「40」は生指摘ベースまたは修正不要 Info を含む集計と推定）。

| iter | 実施日 | 確定 Critical | 確定 Warning | 確定 Info（修正対象） | PM 級 | 棄却/降格 |
|------|--------|------------|------------|---------------------|-------|----------|
| iter1 | 2026-06-10 | 1 | 23 | 8（修正）+ 9（記録のみ） | 8 | 棄却4 / 降格8 |
| iter2 | 2026-06-10 | 0 | 4 | 5（修正）+ 11（記録のみ） | 0 | 棄却1 / 降格6 + 帰属訂正1 |
| iter3 | 2026-06-10 | 0 | 5 | 4（修正）+ 多数（記録のみ） | 3 | 棄却4 / 降格8+1 |
| iter4 | 2026-06-11 | 0 | 9 | 1（修正）+ 少数（記録のみ） | 1 | 降格3 |
| iter5 | 2026-06-11 | 0 | 1 | 0 | 0 | 0 |
| iter6 | 2026-06-11 | 0 | 3 | 0（記録のみ4） | 0 | 0（haiku 突合3件全て事実確認） |
| iter7 | 2026-06-11 | 0 | 0 | 0 | 0 | 0（**Before=0**） |

### テスト数推移

| 状態 | テスト数 | 変化の理由 |
|------|---------|-----------|
| iter1 着手前（D-1修正後） | 739 passed | ─ |
| iter1 完了（PM-3 TDD 実装後） | 740 | +1（PM-3: auto_discover パス検証テスト） |
| iter2 完了 | 735 | -7+2（W2-3 Dead Code `get_tool_response` テスト削除7 + 新規2） |
| iter3 完了 | 738 | +3 |
| iter4 完了 | 743 | +5（テスト網羅補完 W4-6/W4-7/W4-8 等） |
| iter5 完了 | 743 | ±0（W5-1 はログ追加のみ） |
| iter6 完了 | 752 | +9（W6-1/W6-2/W6-3） |
| iter7（Green State） | **752 passed** | ±0 |

### PM 決着件数（計 12 件）

| グループ | 件数 | 内容 | 決着方式 |
|---------|------|------|---------|
| iter1 PM（PM-1〜PM-8） | 8件 | セキュリティ強化1・仕様補記5・タスク委譲1・現状維持1 | PM-3 のみ TDD 実装、残7は仕様補記または現状維持 |
| iter3 PM（PM3-1〜3） | 3件 | 仕様書への追記（§4.1 PASS 時フォーマット / AUTONOMOUS×G5 注記 / gitleaks NFR-1 タイムアウト列） | A バンドル承認（仕様補記のみ・実装変更なし） |
| iter4 PM（PM4-1） | 1件 | `loop-log-schema.md` §3.1 フォーマット乖離の実装同期 | A 承認（仕様を実装に合わせる） |

### 仕様書更新数

- iter1 PM 決着: `autonomous-mode/requirements.md`, `green-state-definition.md`, `scalable-code-review-spec.md`(×2), `loop-log-schema.md`, `tdd-introspection-v2.md` — 5ファイル
- iter3 PM3 決着: `tdd-introspection-v2.md`, `green-state-definition.md`, `gitleaks-integration-spec.md` — 3ファイル
- iter4 PM4 決着: `loop-log-schema.md` — 1ファイル
- iter1 W-19/W-20/W-21/W-23 等 SKILL 修正: `full-review/SKILL.md`, `lam-orchestrate/SKILL.md`（iter3 QA-10 含む）
- **合計**: 9ファイル以上

### 累計修正件数

iter7 レポート総括: **70+ 件**（Critical 黙殺系・契約違反・防御対称性・テスト網羅・仕様ドリフト）

### サブエージェント査定の棄却/降格件数

- iter1 確定: 棄却4件 / 降格8件 = 査定12件（メモリの「49件中12件」は棄却+降格合計を指す）
- iter2 確定: 棄却1件 / 降格6件 + 帰属訂正1件 = 査定8件
- iter3 確定: 棄却4件 / 降格8+1件 = 査定13件
- iter4〜7: 降格3件（iter4）のみ、棄却ゼロ
- daily 2026-06-10 の記録: 「Critical 6件中5件が過大評価」「49 件中 4 件が検証で誤り」（iter1 生指摘総数ベースの累積値）

---

## 3. KPT

### Keep（うまくいったプラクティス）

**K-1: ゼロベース再スキャン原則の貫徹（Before=0 まで止まらない）**
iter5 で max_iterations=5 到達後も Before=0 が未確認のままループを延長し、iter7 で真の Green State を確認した（iter7 レポート、SKILL.md「修正後にゼロ」ではなく「スキャンでゼロ」の原則）。これを妥協しなかったことで偽 Green State を回避できた。

**K-2: 監督査定（棄却・降格）を標準工程化したことで指摘精度が向上**
iter1〜3 で棄却計9件・降格計23件超を監督検証（実行・grep・公式ドキュメント参照）で確定した。daily 2026-06-10「Critical 6件中5件が過大評価」という記録が示すとおり、査定なしでは過修正が発生していた。実行検証（Python re の `\s` テスト、`run_protect_staged` 呼出元 grep、QA-8 context7 裏取り）を査定の標準工程として定着させた。

**K-3: 前巡 Info 降格記録の次巡プロンプト注入による再指摘抑制**
iter3 で「前巡の Info 降格記録を再指摘不要リストとして次巡プロンプトに注入」を試行し有効だったことを daily 2026-06-10 に記録。iter6〜7 でも適用し、同一系統の再出を抑制した。

**K-4: 3層体制の導入（Fable=判断 / Sonnet=実行 / Haiku=事実突合）**
iter6 から導入。Haiku が file:line の Yes/No 事実突合（iter6 では W6-3 の PascalCase 分岐の未テスト等を確認）、Sonnet が修正実装を担当することで、Fable のレート制限枯渇を防ぎながら高速な修正サイクルを実現（SESSION_STATE、daily 2026-06-11）。

**K-5: 縮小構成3体（SRC+SEC統合・TEST統合・QA）による収束とトークン削減**
iter7 で Critical/契約違反/セキュリティ系が3巡連続ゼロの実績を根拠に縮小構成を採用。Warning 判定基準を「新系統 Critical 級・契約違反・具体的攻撃シナリオ・guideline 閾値の明確な超過」に限定したことが Before=0 達成の決め手（iter7 レポート、daily 2026-06-11）。トークン 2/3 削減も両立。

**K-6: PM 決着の分離・バンドル承認でループ停止期間を最小化**
PM3 の3件が「A バンドル承認・仕様補記のみ・実装変更なし」で即決着（iter3 レポート PM3 決着記録）。PM 決着を「ループ外決断として素早く」パターン化し、不必要なループ中断を回避した。

**K-7: 防御対称性パターンの体系的修正**
iter3（W3-3: JS/Rust の `errors="replace"` 欠如）・iter4（W4-3: `load_ast_map` の防御非対称）・iter6（W6-1: `run_security` ログ非対称）など、同型の「対称性漏れ」が複数ファイルに渡り発見・修正された。iter4 で W4-1〜W4-4 が同系統で連続修正されるなど、横展開が一部で機能した。

### Problem（つまずき・課題）

**P-1: iter4 で Warning が 9件に増加（前回比: 4→5→9）**
iter3 で5件だった Warning が iter4 で9件に増加した。増加の内訳: W4-6（`_sanitize_target` のテスト欠如 — セキュリティロジック追加時のテスト抜け）、W4-7（`_parse_junit_xml` の `<testsuites>` 分岐テスト欠如）、W4-8（PreCompact 閾値超過パステスト欠如）。いずれも iter1〜3 の修正実装で付随的に生じたテスト網羅の漏れであり、「修正が新たなテスト欠如を産む」パターンが繰り返し出現した（iter4 レポート）。

**P-2: max_iterations デフォルト5での打ち切りリスク（Before=0 未確認のまま終了）**
iter5 で max_iterations=5 に到達したが Before=0 が未確認だった。ユーザー判断でループを延長し iter7 で Green State を確認できたが、「SKILL.md の max_iterations=5 デフォルト」と「Before=0 確認まで終了禁止」の原則が衝突する運用上の曖昧さが発生した（iter5 レポート）。

**P-3: 静的解析ノイズ（ルート直下 verify_audit*.py による偽陽性 10件）**
iter4 の Stage 1 静的解析で前セッション残置の `verify_audit*.py` が 10 件のノイズを発生させた（iter4 レポート「対象外ノイズ」）。監査対象外ファイルが静的解析スコープに入り込み、査定工数を増やした。ファイルはセッション終了時点でもルートに残存。

**P-4: sonnet 監査のボーダーライン指摘が毎巡発生し、査定負荷が高止まり**
iter3〜6 にかけて sonnet 監査は毎巡「Long Function の行数縁・投機的セキュリティ・過剰抽象化提案」などボーダーラインの指摘を新規生成した（daily 2026-06-10、iter6 レポート所見）。前巡 Info 降格記録の注入で抑制を図ったが、完全には防ぎきれず監督査定が毎回必要だった。

**P-5: レート制限による中断がセッション跨ぎを引き起こした**
iter5 でレート制限中断が発生し、3層体制導入のきっかけとなった（SESSION_STATE）。中断後の再開ではコンテキストの再ロードが必要であり、non-trivial なセッション復旧コストが発生した。

**P-6: iter1 でのサブエージェント回帰テスト範囲漏れ（analyzers のみ 538 件で報告）**
daily 2026-06-10 に記録: sonnet に回帰テストを任せると実行範囲が漏れる（analyzers のみの 538 件で完了と報告）。全体件数基準（739〜752）との突合を監督側で実施する必要があった。

**P-7: tdd-patterns.log への計装ノイズ混入**
tdd-patterns.log に `PostToolUseFailure event`（tests=? failures=?）エントリが 12 回混入（2026-06-08〜06-11、Haiku 集計）。テスト失敗ではなく hook 失敗イベントが FAIL として記録され、TDD パターン分析を汚染。

### Try（改善案）

**T-1: max_iterations を Before=0 確認まで自動延長する運用ルール化（P-2 対）**
SKILL.md に「max_iterations 到達時、Before=0 未確認なら上限延長を即承認するデフォルト運用」を明記する。「ループを延長するか」をユーザーに都度聞くのではなく、Before=0 確認までの延長を事前承認として設定する。

**T-2: 前巡 Info 降格記録を監査プロンプトに自動注入するプロセス化（P-4 対）**
現状は「前巡 Info 降格記録を次巡プロンプトに注入する」を手動で実施している（iter3 で有効と確認）。これを SKILL.md の Stage 2 プロンプト生成手順に明示し、過去 iter レポートから Info/棄却ログを抽出して監査プロンプトに差し込む工程として定型化する。

**T-3: 対称性修正時の全ファイル横展開チェックを標準工程化（P-1 対）**
「A で対称性修正をしたら、同型の非対称が B/C/D にないか grep する」を Stage 4 修正手順に追記する。iter4 で9件増加した主因は iter3 修正の横展開確認不足であり、この工程を明示することで次回ループの膨らみを抑制できる。

**T-4: 静的解析スコープの明示限定と一時ファイルノイズの排除（P-3 対）**
full-review 開始前の前処理として「untracked ファイルが存在する場合は警告を出して確認を求める」を Stage 0 に追加する。

**T-5: 3層体制の開始条件をレート限界前に前倒し（P-5 対）**
今回は「レート制限中断後」に3層体制を導入したが、B-3 以降は full-review 開始時から3層体制をデフォルト採用する。「Critical/SEC 系ゼロが2巡以上」を条件として縮小構成に移行するトリガーも SKILL.md に明示する。

**T-6: 回帰テストの実行範囲を Sonnet 委譲時に明示指定（P-6 対）**
Sonnet に回帰テストを委譲する際は「フル回帰コマンド: `cd .claude/hooks && python -m pytest tests/ analyzers/ checkers/ -o addopts="" -q`」をプロンプトに必ず含め、実行件数の期待下限を明示する（MEMORY.md `test-execution-claude-hooks.md` に記録済み。SKILL.md にも注記追加）。

**T-7: PostToolUseFailure 混入の記録条件見直し（P-7 対）**
`post-tool-use.py` の記録条件を調査し、JUnit XML 不在/解析不能時のエントリ形式を見直す（A-9 として起票済み）。

---

## 4. Step 2.5: TDD パターン分析の結果

FAIL→PASS 17 ペアを分析。`test_g1_pass_completion_stops` 2 回は同一作業内で反復性なし。
PostToolUseFailure ×12 は計装ノイズでありコードの失敗パターンではない。
→ **ルール候補（draft）起票なし**（ユーザー承認済み 2026-06-11）。ANALYZED マーカー追記済み。

---

## 5. アクション（全件承認済み 2026-06-11）

| # | アクション | 反映先 | 優先度 | 根拠 | ステータス |
|---|-----------|--------|--------|------|-----------|
| A-1 | Stage 5 Step 3 に「max_iterations 到達時 Before=0 未確認なら即延長承認」のデフォルト運用を明記 | `.claude/skills/full-review/SKILL.md` Stage 5 | 高 | P-2。iter5 で発生した運用曖昧さの再発防止 | 承認済み（2026-06-11）・適用済み |
| A-2 | Stage 2 Step 3 に「前巡 Info/棄却記録の次巡プロンプト自動注入」手順を追記 | `.claude/skills/full-review/SKILL.md` Stage 2 | 高 | P-4。iter3・7 で有効と確認 | 承認済み（2026-06-11）・適用済み |
| A-3 | Stage 4 共通ポリシーに「対称性修正時は同型の全ファイル横展開 grep を実施」を追記 | `.claude/skills/full-review/SKILL.md` Stage 4 | 中 | P-1。iter4 の Warning 増加（4→9）の主因 | 承認済み（2026-06-11）・適用済み |
| A-4 | Stage 0 に「untracked ファイル存在時に警告・確認を求める前処理」を追加 | `.claude/skills/full-review/SKILL.md` Stage 0 | 中 | P-3。`verify_audit*.py` が静的解析ノイズを発生 | 承認済み（2026-06-11）・適用済み |
| A-5 | Stage 2 Step 3 の監査構成に「Critical/SEC 系2巡連続ゼロなら縮小構成移行」トリガーを追記 | `.claude/skills/full-review/SKILL.md` Stage 2 | 中 | P-4/P-5。iter7 で効果を実証（トークン 2/3 削減・Before=0 達成） | 承認済み（2026-06-11）・適用済み |
| A-6 | Stage 5 Step 1 に「Sonnet 委譲時はフル回帰コマンドと件数下限を明示」注記を追加 | `.claude/skills/full-review/SKILL.md` Stage 5 | 中 | P-6。「analyzers のみ 538 件で完了報告」の再発防止 | 承認済み（2026-06-11）・適用済み |
| A-7 | 3層体制（Fable=判断 / Sonnet=実行 / Haiku=事実突合）を CLAUDE.md に明記し、B-3 以降の full-review 開始時から適用 | `CLAUDE.md` | 低 | K-4。次セッション新規 Fable が参照可能にする | **PM 承認済み**（2026-06-11）・適用済み |
| A-8 | code-reviewer agent-memory の陳腐化 Warning（解消済みだが Critical/Warning 欄に残存している古い Issue）を整理 | `.claude/agent-memory/code-reviewer/` | 低 | K-2。次 full-review の参照ノイズになる（SE級） | 承認済み（2026-06-11）・適用済み |
| A-9 | PostToolUseFailure 混入の記録条件調査 | `.claude/hooks/post-tool-use.py`（SE級） | 中 | Step 2.5 の Haiku 集計（P-7） | 承認済み（2026-06-11）・決着済み（案 A 適用） |

> **A-9 決着（2026-06-11）**: 調査の結果、PostToolUseFailure の FAIL 記録は 2026-03-14 実装の意図的動作（古い JUnit XML による誤遷移防止）でありバグではない。案 A（実装・仕様・テスト無変更、/retro スキル Step 2.5 に「PostToolUseFailure event 行は集計除外」を追記）を採用・適用済み。

---

*起草メモ*: 「確定 Warning 40→4→5→9→1→3→0」の「40」は iter7 レポート総括表の値を正とした。iter1 レポート本文の査定後確定値は C1+W23+Info修正8=32 件（集計基準差あり）。
