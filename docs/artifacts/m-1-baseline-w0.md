# M-1 W0 ベースライン記録

| 項目 | 内容 |
|:-----|:-----|
| Milestone | M-1 / Wave 0（準備） |
| 対応 Task | W0-M1-T1〜T8（`docs/specs/m-1-opus5-migration/tasks.md` §3 / T8 は 2026-07-25 追加） |
| 作成日 | 2026-07-25 |
| ステータス | **W0 完了**（T1〜T8 全 8 Task 完了 / W1 着手可 / 判定は §W0-M1-T7） |

---

## W0-M1-T1: 委譲 TDD 記録盲点の probe（経路 (a)/(b) 切り分け）

**実施日**: 2026-07-25（JST 16:09〜16:15 / UTC 07:09〜07:15）
**対応仕様**: design.md §4.5 手順 1 / tasks.md W0-M1-T1

### 判定（結論）

design §4.5 が挙げた **経路 (a)・経路 (b) はいずれも記録欠落の原因ではない**（両方とも実測で否定）。

**根本原因は 1 本**である。

| # | 機構 | 内容 |
|:-:|:-----|:-----|
| **C2** | **XML 鮮度検査の欠如**（根本原因） | 通常経路（`PostToolUse`）は `.claude/test-results.xml` の鮮度を一切検査せず、**前回実行の結果をそのまま当該コマンドの結果として採用**する。`-o addopts=""` で XML が更新されない場合も、そもそもテストを実行していないコマンドでも同じ |

失敗イベント経路（`PostToolUseFailure`）は XML を読まずに直接 FAIL を書く **XML 非依存の安全網**として機能しており、C2 の害を部分的に隠している。したがって盲点が成立するのは次の 2 条件が**同時に**満たされたときに限る。

| 条件 | 内容 |
|:-----|:-----|
| (i) | コマンドが XML を更新しない（`-o addopts=""` / そもそもテストを実行していない） |
| (ii) | tool exit が 0（`\| tail` などのパイプ・`\|\| true`・`; echo` 連結）で安全網が発火しない |

このとき**失敗したテスト実行が `pass` として上書き記録される**（無音の損失 + 汚染）。実測で再現済（下記 Q 行）。

> **訂正（2026-07-25 / 同日中）**: 本節の初版は上記 C2 に加えて「**C1 記録トリガの束縛** = FAIL の記録は Bash ツールの非ゼロ終了に束縛されている」を根本原因として併記していたが、**これは誤りである**。通常経路も XML が fresh であれば `failures > 0` から FAIL を正確に記録する（`post-tool-use.py:230`）。関数レベルの実測で確認済:
>
> ```
> [fresh XML failures=1 / tool exit 0（通常経路）]
>   -> 2026-07-25T00:00:00Z  FAIL  pytest  tests=3 failures=1  "test_bad"
> [fresh XML failures=1 / tool exit != 0（失敗イベント）]
>   -> 2026-07-25T00:00:00Z  FAIL  pytest  tests=? failures=?  "PostToolUseFailure event"
> ```
>
> 誤った併記により「`is_failure_event` 依存を緩和する」という不要な修正案を導いていたため撤回する（下記 §W0-M1-T2 の方針を参照）。

### 実測データ（全 5 実験）

`.claude/tests/tmp_probe_w0m1t1/test_probe_fail.py`（`assert 1 == 2`）と `test_probe_pass.py`（`assert 1 == 1`）を probe 用に作成して使用。

| # | 実行形態 | 実行主体 | tool exit | XML 更新 | log 追記 | 記録内容 |
|:-:|:---------|:--------:|:---------:|:--------:|:--------:|:---------|
| 統制 | `echo` に **pytest の語を含むだけ**（テスト未実行） | L1 | 0 | なし | **なし** | `last-test-result` を 5 時間前の XML から `pass` に書換（**汚染**） |
| RUN-A | 失敗 pytest + `-o addopts=""` | **subagent** | 1 | なし | **あり** | `FAIL pytest tests=? failures=? "PostToolUseFailure event"` |
| RUN-B | 失敗 pytest（既定 addopts） | **subagent** | 1 | あり | **あり** | `FAIL pytest tests=? failures=? "PostToolUseFailure event"` |
| P | 成功 pytest（既定 addopts） | L1 | 0 | あり | **あり** | `PASS pytest tests=1 failures=0 "pytest (previously failed)"`（FAIL→PASS 遷移） |
| **Q** | 失敗 pytest + `-o addopts=""` + **パイプで exit 0** | L1 | 0 | なし | **なし** | **失敗実行を `pass` として記録**（log 行数 247 のまま / `last-test-result` 更新のみ） |

観測値（`stat` / `wc -l` の生値）:

```
S0  (probe 前)   last-test-result=16:09:49  test-results.xml=10:49:11  log_lines=244  content="pass pytest"
OBS-2(RUN-A 後)  last-test-result=16:11:36  test-results.xml=10:49:11  log_lines=245  +FAIL "PostToolUseFailure event"
OBS-3(RUN-B 後)  last-test-result=16:11:58  test-results.xml=16:11:58  log_lines=246  +FAIL "PostToolUseFailure event"
S-P (P 後)       last-test-result=16:13:38  test-results.xml=16:13:37  log_lines=247  +PASS (previously failed)
S-Q (Q 後)       last-test-result=16:14:02  test-results.xml=16:13:37  log_lines=247  追記なし
```

### 経路 (a)/(b) の否定根拠

- **経路 (a)（subagent の Bash で hook が発火しない）→ 否定**: RUN-A / RUN-B はいずれも **subagent** の Bash 呼び出しであり、両方とも `tdd-patterns.log` に追記された（244 → 245 → 246）。subagent でも hook は正常に発火する。
- **経路 (b)（`-o addopts=""` で XML が更新されず記録されない）→ 単独では否定**: RUN-A は `-o addopts=""` 付きで XML mtime が変わらなかった（10:49:11 のまま）にもかかわらず**記録された**。`is_failure_event=True` の分岐が XML を読まずに直接 FAIL を書くため（`post-tool-use.py:208-214`）。ただし `-o addopts=""` は **C2 の必要条件の一つ**として Q 行で効いている。

### 実装上の該当箇所（`.claude/hooks/post-tool-use.py`）

| 行 | 内容 | 関係 |
|:--|:-----|:-----|
| 66-73 | `_TEST_CMD_PATTERN` / `_is_test_command` — コマンド文字列の**字句一致**のみ | 発火条件（テスト未実行でも発火する） |
| 216-222 | `_parse_junit_xml` の呼び出し — **mtime を検査しない** | **C2 の実体（修正対象）** |
| 208-214 | `is_failure_event` 分岐 — XML を読まず直接 FAIL 記録 | 安全網（維持する） |
| 230-231 | `failures > 0` → `_record_fail` — **通常経路も FAIL を書く** | 訂正の根拠 |
| 163-179 | `_record_pass` — `prev_was_fail` が False なら**追記しない** | 無音化の実体 |
| 404-409 | `main` — `tool_name == "Bash"` かつ `hook_event_name` で分岐 | イベント振り分け |

**既存の半適用防御**: `.claude/hooks/tests/test_post_tool_use.py:272` に `test_failure_event_ignores_stale_pass_xml`（「古い PASS XML が残っていても PostToolUseFailure は FAIL を記録」）が既に存在する。すなわち **stale XML への防御は失敗イベント側にだけ実装済みで、通常経路に同じ防御が無い**。T2 は新機能の追加ではなく、半分だけ適用された防御の残り半分を入れる作業である。

### R-2 W1（2026-07-25）の記録 0 件との関係

C1 + C2 の重なりで説明できる（並列 subagent が `-o addopts=""` 規約を用い、かつ出力をパイプで受けて tool exit が 0 になる形）。**ただし当時の実コマンド文字列は残っていないため、この説明の寄与は未確認**（推測であり観測ではない）。確定しているのは「C1 + C2 が重なれば失敗が pass として記録される」という機構の存在（Q 行で実測）までである。

### W0-M1-T2 への引き継ぎ（1 行）

> **直すべきは「subagent 判定」でも「XML パス分離」でもなく、通常経路が XML の鮮度を検査していない点（C2）だけである。**

**確定した修正方針**（2026-07-25 / ユーザー判断 2 件 / NFR-2 準拠 = 新規帳簿・新規ログ・新規集計スクリプトを作らない）:

1. **鮮度判定 = 方式 A（mtime センチネル）**。前回参照した XML の mtime を既存の状態ファイル `.claude/last-test-result` に併記し、今回の mtime が前回値と同一なら「当該コマンドは XML を更新していない」と判定して**スキップ**する（`tdd-patterns.log` に触れず、`last-test-result` の判定結果も上書きしない）。WARN は既存の `post-tool-use.log` に出す。
   - **方式 B（時間窓 tolerance）を採らない理由**: 閾値 N の根拠を持てず（`planning-quality-guideline.md` §Requirements Smells の「計測不能な語」に相当）、`pytest && sleep 300` 等の長い後続処理で誤棄却する。方式 A は閾値パラメータが不要で決定論的、かつ時計ずれの影響を受けない。
   - **後方互換**: mtime 欄を持たない既存の `last-test-result`（`pass pytest` の 1 行形式）を読んだ場合は「前回値不明」として従来動作にフォールバックする（初回のみ）。
2. **失敗イベント経路（安全網）は変更しない**。XML 非依存で FAIL を書く現行挙動を維持する。
3. **`-o addopts=""` 規約は変更しない**。共有 XML の clobber 回避として正当であり、鮮度判定が入れば「更新されなかった XML を誤採用する」害だけが消える。

### 既知の限界（T2 で解消しない / ユーザー判断により M-1 スコープ外）

**並列 subagent が共有 XML を使う場合の「他人の結果の誤採用」は残存する**。鮮度判定（方式 A）は「XML が更新されたか」しか見ないため、subagent A が XML を更新した直後に subagent B の hook が走ると、B は「新しい XML」を自分の結果として採用しうる。

- **根治には JUnit XML の出力先を実行ごとに分離する必要がある**（design §4.5 が触れていた「XML パス分離」）。これは `pyproject.toml` の addopts・`-o addopts=""` 規約・dashboard 側の読み取り・クリーンアップ機構に広く波及し、W0 が実質 1 Wave 分の作業量になるため T2 のスコープに含めない。
- **残存誤差の発生頻度は未実測**（寄与は未確認）。W1 以降で実害が観測された場合に改めて起票する。
- W0 の目的（軸 4 = 実測発火の有無を測る計器を汚染しない）に対しては、単独実行時の汚染が消える時点で十分と判断した。

### 後片付け

- [x] `tdd-patterns.log` に synthetic 3 行（07:11:36Z / 07:11:58Z / 07:13:38Z）を識別する `PROBE` マーカーを追記（W0-M1-T3 の FAIL→PASS 率算定から除外するため）
- [x] **`.claude/tests/tmp_probe_w0m1t1/` を削除**（2026-07-25 / ユーザー実施 — `rm` は `security-commands.md` の deny 対象のため AI は実行しない）。`find` で `tmp_probe` / `probe_fail` / `probe_pass` の残骸ゼロを確認済、`.claude/tests/` 直下は probe 前と同一（`dashboard` / `hooks` / `rules` / `scripts` / `wave_c`）

> **環境メモ**: LAM の Bash ツール実体は Git Bash だが、**ユーザーが操作する端末は PowerShell** である。ユーザーへ削除等を依頼する際は `rm -rf <path>` ではなく `Remove-Item -Recurse -Force <path>` の形で渡すこと（`rm -rf` は PowerShell では `Remove-Item` のエイリアスに解決され `-rf` が未知パラメータとなって失敗する / 2026-07-25 実測）。

---

## W0-M1-T2: probe 結果に基づく機構修正

**実施日**: 2026-07-25（JST 16:20〜16:32）
**対応仕様**: design.md §4.5 手順 2, 3 / tasks.md W0-M1-T2
**結果**: **盲点は解消した**（M-1 スコープ外への送りは発生しなかった）

### 変更内容（`.claude/hooks/post-tool-use.py` / 方式 A = mtime センチネル）

| 追加・変更 | 内容 |
|:-----------|:-----|
| `_xml_sentinel()`（新規） | XML の世代を `"<st_mtime_ns>:<st_size>"` で表す。閾値パラメータを持たないため時計ずれの影響を受けない |
| `_read_prev_xml_sentinel()`（新規） | `last-test-result` の 2 行目 `xml=...` から前回世代を読む。**行が無い旧形式は None を返し従来動作へフォールバック**（後方互換） |
| `_write_last_result()`（新規） | `last-test-result` を「1 行目=判定 / 2 行目=センチネル」で書く共通処理 |
| `_handle_test_result()`（変更） | 通常経路に**鮮度判定**を追加。`sentinel == prev_sentinel` なら `tdd-patterns.log` に触れず `last-test-result` も更新せずに `return None`。WARN を既存の `post-tool-use.log` へ出力 |
| 失敗イベント経路（変更） | FAIL 記録の挙動は**不変**。ただし現時点のセンチネルを保存し、次回の鮮度判定の基準にする |
| `_record_fail` / `_record_pass`（変更） | センチネルを受け取り `_write_last_result()` 経由で保存（引数は既定値 `None` で後方互換） |

**`-o addopts=""` 規約・`pyproject.toml` の addopts は変更していない**（T1 の方針 3）。

### TDD 記録

新規テストクラス `TestStaleXmlFreshness`（`.claude/hooks/tests/test_post_tool_use.py`）4 件:

| テスト | 目的 |
|:-------|:-----|
| `test_unchanged_xml_is_not_readopted` | 更新されていない XML の結果を再採用しない + WARN が出る |
| `test_command_merely_mentioning_pytest_does_not_record` | **2026-07-25 に実環境で観測したケースの回帰テスト**（`echo` に語が含まれるだけで 5 時間前の XML が読まれた） |
| `test_updated_xml_is_recorded_after_skip` | スキップ状態が固着せず、更新後の XML は通常どおり記録される |
| `test_legacy_last_result_without_sentinel_falls_back` | センチネル欄を持たない旧形式でも動作する（後方互換） |

- **Red**: 2 failed / 2 passed（`TestStaleXmlFreshness` 単体）
- **Green**: 27 passed（`test_post_tool_use.py` 全体 / 既存 23 + 新規 4）
- **全数**: **1047 passed, 14 skipped**（W0 起点 1043 passed + 14 skipped に対し **+4 = 新規テスト分**、**regression ゼロ** / NFR-3）

### 実環境での検証（F4 #1「作った層と別の層で確認する」）

pytest 全数実行（XML 更新）→ センチネル保存 → 「pytest の語を含むだけのコマンド」を実行:

```
last-test-result mtime = 16:31:55   (全数 pytest 実行時のまま。16:32:17 のコマンドで上書きされていない)
test-results.xml mtime = 16:31:54
tdd-patterns.log       = 248 行（不変）
last-test-result       = "pass pytest" / "xml=1784964714759500600:158050"
post-tool-use.log      = WARN post-tool-use  pytest: test-results.xml unchanged since last check
                         (stale, not this command's result) - skipped
```

修正前は同一操作で `last-test-result` の mtime が更新されていた（T1 統制実験）。**汚染が消えたことを実環境で確認した。**

### NFR 準拠

- **NFR-2**: 新規の帳簿・ログファイル・集計スクリプトを追加していない（既存 `last-test-result` に 1 行追加 / WARN は既存 `post-tool-use.log`）
- **NFR-4**: Python 3.8 互換（`st_mtime_ns` は 3.3+ / `match`・`except*`・dict merge・`str.removesuffix` 不使用 / `from __future__ import annotations` 済）
- **NFR-5**: `subprocess.run` の追加なし（該当なし）

### T3 で確定すべき論点（本 Task では決めない）

**§4.1 測定項目 3（`tdd-patterns.log` FAIL→PASS 率）の W0 起点をどう扱うか。**

計器は修正されたが、**修正前に蓄積されたログ（〜2026-07-25）は盲目の計器で採られている**。したがって W0 の項目 3 を全履歴で算定すると、W0↔W4 の差分には「条項トリアージの効果」だけでなく「計器が変わったこと」が混入する。design §4.5 が想定した「盲点が解消しない場合は参考値扱い」とは別種の問題であり、T3 で次のいずれかを確定する必要がある。

1. 項目 3 は **W4 側のみ実測値として報告**し、W0↔W4 の差分比較には用いない（DoD-4 の判定は項目 1 = pytest regression と項目 5 = PM 級発火数で行う）
2. 修正後エントリのみを母数にする（W0 側は実質ゼロ件のため比較不能）
3. 全履歴で算定し、「計器変更の混入」を注記した上で参考値とする

**L1 の推奨は 1**（最も正直で、DoD-4 の判定根拠を汚染しない）。

#### 確定（2026-07-25 / セッション 6 / ユーザー承認）

**案 1 を採用する。** 本論点は W0 完了時点で確定済とし、W1 以降へ持ち越さない（tasks.md W0-M1-T7 完了条件 / design §4.5「不成立時の扱い」と同じ着地）。

| 項目 | 確定内容 |
|:-----|:---------|
| W0 側の項目 3 | **算定しない**（盲目の計器で採られた履歴を起点として扱わない） |
| W4 側の項目 3 | **実測値として報告する**（修正後の計器による観測のため有効） |
| W0↔W4 の差分比較 | **用いない** |
| DoD-4 の判定 | **項目 1（pytest regression）と項目 5（PM 級ダイアログ発火数）で行う** |

**根拠**: 計器（XML 鮮度判定）は W0-M1-T2 で修正されたため design §4.5 が想定した「盲点が解消しない場合」には該当しない。しかし修正前後で観測器そのものが変わっており、差分を取ると「条項トリアージの効果」と「計器変更」が分離不能になる。案 2 は W0 側が実質ゼロ件で比較が成立せず、案 3 は注記付きでも DoD-4 の判定根拠に混入値を持ち込む。**測れないものを測れたことにしない**方針として案 1 を採る。

**W0-M1-T3 への申し送り**: 項目 3 の欄には「**W0 = 算定せず（計器較正前のため）/ 差分比較に用いない**」と明記すること。空欄にせず、算定しなかった事実と理由を残す。

**除外事項**: `.claude/tdd-patterns.log` には W0-M1-T1 の probe に由来する synthetic 3 行（UTC 07:11:36 / 07:11:58 / 07:13:38）が含まれる。`PROBE` マーカーで識別可能。**W4 側の算定時にはこれらを母数から除外すること**。

---

## W0-M1-T5: upstream 一次資料の裏取り（Opus 5 / Fable 5 + 規律肥大化の対処法）

**実施日**: 2026-07-25（セッション 6）
**担当**: L1 直
**対応仕様**: design.md §4.3 / requirements.md FR-19 / tasks.md W0-M1-T5

### 1. モデルスペック（FR-19 初版スコープ）

**一次資料**: https://platform.claude.com/docs/en/about-claude/models/overview （取得日 2026-07-25）
**補足一次資料**: https://platform.claude.com/docs/en/about-claude/models/whats-new-opus-5 （同）

| 項目 | Claude Fable 5 | **Claude Opus 5** | Claude Sonnet 5 | Claude Haiku 4.5 |
|:-----|:---------------|:------------------|:----------------|:-----------------|
| API ID | `claude-fable-5` | `claude-opus-5` | `claude-sonnet-5` | `claude-haiku-4-5-20251001` |
| context window | 1M | **1M（default かつ最大 / 小 variant なし）** | 1M | 200k |
| max output | 128k | 128k | 128k | 64k |
| 価格（in/out per MTok） | **$10 / $50** | **$5 / $25** | $3 / $15 | $1 / $5 |
| adaptive thinking | Yes（**always on**） | Yes | Yes | No |
| extended thinking | No | No | No | Yes |
| reliable knowledge cutoff | Jan 2026 | **May 2026** | Jan 2026 | **Feb 2025** |
| GA / リリース | 2026-06-09 | **2026-07-24** | — | — |

**価格・課金に関する確定事項**:

- **Opus 5 は Opus 4.8 から価格据え置き**（$5 / $25）。`hga-summoning.md` §根拠の「Opus は Fable の半額」は **Opus 5 世代でも成立を継続**する（$5/$25 vs $10/$50）。
- **Opus 5 Fast mode**: $10 / $50（research preview / Claude API のみ / Bedrock・Google Cloud・Microsoft Foundry では未提供）。
- **Sonnet 5 は 2026-08-31 まで導入価格 $2 / $10**（通常 $3 / $15）。W2-M1-T1 の `model-roster.md` §単価には**期限付き価格である旨を併記すること**。
- **Opus 5 の prompt cache 最小長は 512 tokens**（Opus 4.8 は 1,024）。HGA の cache_creation 支配（`hga-summon-log.md` §day-1 実測 #5）の再評価材料になる。
- **1M context は追加課金なし**（long-context 割増ではなく standard pricing）。

**Opus 5 の破壊的変更（API）**:

- `thinking: {"type": "disabled"}` は **effort `high` 以下でのみ受理**。`xhigh` / `max` と併用すると **400 エラー**。Opus 4.8 では effort と独立だった。
- effort は 5 段階（`low` / `medium` / `high` / `xhigh` / `max`）で **default は `high`**。thinking は **on by default**。

**Fable 5 のトークナイザ注記**: Fable 5 は Opus 4.7 導入のトークナイザを使用し、**同一テキストで約 30% 多いトークン**になる（Opus 4.7 より前のモデル比）。`model-delegation-prompting.md` §1 デルタ 5 が Sonnet 5 について記載する内容と同型。HGA ブリーフの実効トークン見積に影響する。

**W2-M1-T1 への転記事項**: 上表の全値を `model-roster.md` §単価・envelope へ転記する。特に **(i) Sonnet 5 導入価格の期限（2026-08-31）**、**(ii) Haiku 4.5 の knowledge cutoff が Feb 2025 と古いこと**（L3 採点で最新事項の判断に使わない根拠）、**(iii) Opus 5 の thinking/effort 制約**の 3 点は roster に明記する。

### 2. 追加調査軸: 規律肥大化への upstream 対処法

**一次資料**（すべて取得日 2026-07-25）:

| # | URL | 位置づけ |
|:-:|:----|:---------|
| 1 | https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models | **Claude 5 世代向けの新ルール（M-1 に直撃）** |
| 2 | https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents | コンテキスト設計原則の総論 |
| 3 | https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5 | **Opus 5 固有の挙動と対処（一次資料）** |
| 4 | https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills | Agent Skills の設計原則（検索結果経由 / 本文は未読） |

#### 結論（tasks.md が定めた 3 分類）

**(a) LAM の手法と一致** — M-1 の方向性は upstream と整合する。

- **Anthropic 自身が Claude Code のシステムプロンプトを 80% 以上削減し、測定可能な性能低下がなかった**（資料 1）。M-1 の「条項トリアージによる圧縮・削減」と同じ操作を、upstream が自社ハーネスで先行実施している。
- 削減の根拠も一致: 過剰・重複・矛盾する指示は、モデルに「どれに従うか」を判断させる**余分な認知負荷**を課す（資料 1）。LAM の判定軸が想定する「条項の重複・陳腐化」と同型。
- 資料 2 の「right altitude」（具体的すぎると脆く保守コストが増える / 抽象的すぎると行動シグナルにならない）は、W1 の判定で条項を残すか削るかの一般原則として使える。
- 資料 2 の「context rot」（トークン追加ごとにモデルの注意予算が減る）は、`CLAUDE.md` + rules の文字数を測る**測定項目 6 の理論的根拠**になる。

**(b) 公式機構で代替可能** — LAM が手作業で担っている一部は既存機構に寄せられる。

| LAM の現状 | 対応する公式機構 | 備考 |
|:-----------|:-----------------|:-----|
| skills の内容を SKILL.md に集約 | **progressive disclosure の 3 レベル**（metadata 約 100 tok/skill → body 約 5,000 tok → 参照ファイルは必要時のみ） | W3-M1-T2 の対象。3 レベル構造が公式の型 |
| 規律を全部 rules に前置き | just-in-time retrieval（必要時に読む） / 事前ロードとのハイブリッド | 資料 2 は「最も単純に済む方法を採れ」を原則とする |
| MCP ツール定義の常時ロード | **ToolSearch による deferred loading**（典型構成で 85%+ 削減） | 本セッションでも稼働中 |
| セッション知見の手動蓄積 | 自動メモリ（`autoMemoryEnabled`）/ memory tool | LAM は自動メモリを既に使用中 |
| compact 後の文脈喪失 | **SessionStart hook（matcher: `compact`）による再注入** | LAM 未使用。W2/W3 の候補になりうる |

**(c) upstream に該当なし** — LAM 固有として維持すべきもの。

- 「**規律条項をトリアージする手続きそのもの**」（判定軸 4 + 決定木 4 分岐 + 削減台帳）に対応する公式機構は存在しない。upstream は「削れ」「progressive disclosure を使え」と方針を示すが、**既存の大量の条項を体系的に棚卸しする手順**は提供していない。M-1 W1 の中核は LAM 固有の価値として残る。

#### (d) 3 分類に収まらない発見 — **LAM の一部条項は Opus 5 で有害**

**これが本 Task の最大の収穫であり、当初の 3 分類が想定していなかった第 4 の結論である。**

資料 3（Opus 5 の公式プロンプティング指針）は、以前のモデル向けに書かれた**検証指示を削除せよ**と明示する。理由は Opus 5 が指示なしで自己検証するため、指示が重なると **over-verification** を起こし、品質を上げずにトークンを浪費するというもの。原文は "they cause over-verification on Claude Opus 5" と述べ、さらに **legacy harness scaffolding（旧世代ハーネスの足場）にも同じことが当てはまる**と明記している。LAM はまさにこの「legacy harness scaffolding」に該当する。

同資料が挙げる Opus 5 の挙動変化と、LAM 側の該当箇所:

| # | Opus 5 の挙動（資料 3） | 公式の推奨 | LAM 側の該当候補（**W1 で要判定**） |
|:-:|:------------------------|:-----------|:-----------------------------------|
| 1 | 指示なしで自己検証する | **検証指示を削除**（"include a final verification step" / "use a subagent to verify" 型） | `fable-l3-protocol.md` §4 自己監査 14 項目 / §6.6 F4 全体検証 5 点 / `phase-rules.md` AUDITING チェックリスト群 |
| 2 | 自分の誤りを自力で捕捉・修正する | **再チェック指示を削除**（"double-check" / "re-verify before responding" 型） | 同上 + TDD 品質チェック R-1/R-4/R-5/R-6 |
| 3 | subagent への委譲が増える | 委譲にキャップを設ける。**「自分の作業の検証に subagent を使うな」** | **`gabriel` の adversarial probe が直撃**（下記の注意を参照） |
| 4 | 「重要なものだけ報告」をリテラルに解釈し recall が落ちる | 全件報告させ、**フィルタは別パスで行う** | `code-quality-guideline.md` の重要度分類運用 / `quality-auditor` への委譲文言 |
| 5 | 応答・成果物が長くなる / 進捗ナレーションが増える | 簡潔さを明示的に指示する | 60 秒実況・報告様式まわりの条項 |
| 6 | タスクのスコープを自分で広げることがある | スコープを明示的に制約する | **F0 の「やらないこと」は upstream 推奨と一致 = 維持側**の証拠 |

**gabriel に関する重要な留保（W1 で機械的に削らないこと）**: 資料 3 の「subagent を自己検証に使うな」は**コスト効率の文脈**での推奨である。一方 LAM の `gabriel` は ADR-0007 に基づき「**同一モデルの別ペルソナは盲点が相関する**」ことへの対処として独立コンテキストを採用しており、目的が異なる。**単純な二重チェックではない**ため、この項目は W1 の判定で「upstream が削除を推奨」と機械的に扱ってはならない。**W0-M1-T8 の crux として HGA に問う価値が最も高い項目**である。

#### W1 / W2 / W3 への申し送り

1. **W1-M1-T4（veto 先行スクリーニング）の入力に本節 (d) の表を加えること**。判定軸 4 は「重複 / 陳腐化 / 過剰」を見るが、**「upstream が明示的に削除を推奨している」は独立した強いシグナル**であり、既存の 4 軸では捕捉されない可能性がある。軸を増やすか、veto の先行スクリーニングで扱うかは W0-M1-T8 の結果を待って決める。
2. **W3-M1-T2（progressive disclosure 化）は 3 レベル構造（metadata → body → 参照ファイル）を型として採用すること**。LAM 独自の分割方式を発明しない。
3. **W2-M1-T1（`model-roster.md`）に Opus 5 の thinking / effort 制約を明記すること**（§1 参照）。
4. 資料 1 が言及する `claude doctor` は**未確認**（下記）。使えるなら W4 の検証で利用余地がある。

### 3. 追加調査（2026-07-25 セッション 6 後半 / ユーザー指摘による事実確認）

**一次資料**: https://code.claude.com/docs/en/memory （取得日 2026-07-25）

#### 訂正 1: 「80% 削減」と LAM の 154,837 文字は**別レイヤー**

本記録 §2 の初版は、Anthropic の 80% 削減実績と LAM の `CLAUDE.md` + rules を同列に扱いかねない書き方をしていた。**両者はレイヤーが異なる**。

> CLAUDE.md content is delivered as **a user message after the system prompt, not as part of the system prompt itself**

- Anthropic が削減したのは **Claude Code 本体が注入するシステムプロンプト**
- LAM の 154,837 文字は**その後ろに載るユーザーメッセージ**

したがって **80% という数字は LAM に適用される保証がない**。操作の性質（重複・矛盾する指示を削る）は同型であり §2 (a) の結論「LAM の手法と upstream は一致」は維持されるが、**削減率を移植して見積もることはできない**。

#### 訂正 2（重大）: `.claude/rules/` は公式機能であり、**条件ロードが可能**

本記録 §W0-M1-T3 項目 6 で「18 ファイルが毎セッション全文注入される」と記録したが、**現象は正しく原因の記述が不足していた**。これは Claude Code の制約ではなく、**LAM が公式機能を使っていない**結果である。

> Rules **without `paths` frontmatter** are loaded at launch with the same priority as `.claude/CLAUDE.md`
> Rules can also be scoped to specific file paths, so they **only load into context when Claude works with matching files, reducing noise and saving context space**

**LAM の実測（2026-07-25）**: `.claude/rules/` 配下 18 ファイルのうち **`paths:` frontmatter を持つものは 0 件**（frontmatter 自体が全ファイルに存在しない）。したがって全 18 ファイルが無条件ロードされている。

**`paths` の仕様（一次資料より）**:

| 項目 | 内容 |
|:-----|:-----|
| 発火条件 | **Claude が glob にマッチするファイルを「読んだ」とき**。`not on every tool use` と明記 |
| パターン | glob（`**/*.py` / `docs/specs/**` / `src/**/*.{ts,tsx}` 等 / brace 展開可） |
| 予算 | 1 ルールの `paths` 全体で 1,000 展開パターン / 4 MiB |
| 注意 | `[` はブラケット式として解釈。リテラルは `\[` でエスケープ |
| 除外 | `--setting-sources` から `project` を外すと project rules は読まれない |

**未検証の制約（W2/W3 で要検証）**: 「読んだとき」発火のため、**対象ファイルを Read せずに Write する経路では規約が手遅れで届く**可能性がある。例: `subprocess-encoding-convention.md` に `paths: ["**/*.py"]` を付けた場合、新規 Python ファイルを Read なしで Write する経路で発火しない懸念。**断定せず、下記 `InstructionsLoaded` hook で実測すること**。

#### 追加で判明した機構（M-1 に利用余地あり）

| 機構 | 内容 | M-1 での利用余地 |
|:-----|:-----|:-----------------|
| **`/doctor` の trim 提案** | checked-in CLAUDE.md に対し trim を提案（v2.1.206+）。**コードベースから導出できる内容**（ディレクトリ構成 / 依存リスト / アーキテクチャ概要）を削り、**落とし穴・根拠・ツール既定と異なる規約**を残す | W2-M1-T3 の範囲拡張候補（現行はモデル ID 直書き除去のみ） |
| **`InstructionsLoaded` hook** | どの指示ファイルが**いつ・なぜ**ロードされたかをログする | **`paths` 化の効果測定・上記未検証制約の実測手段**。FR-8 の測定に接続可能 |
| **`claudeMdExcludes`** | パス/glob で CLAUDE.md・rules を除外（設定レイヤー横断でマージ） | 参考（LAM は単一リポジトリのため優先度低） |
| **CLAUDE.md の公式サイズ推奨** | **200 行以下**。「Longer files consume more context and **reduce adherence**」 | LAM は **269 行**（35% 超過） |

#### 行数実測（2026-07-25 / `wc -l`）

`CLAUDE.md` 269 行 + rules 18 ファイル = **合計 2,749 行**。上位: `hga-summoning.md` 330 / `CLAUDE.md` 269 / `phase-rules.md` 245 / `subprocess-encoding-convention.md` 236 / `fable-l3-protocol.md` 234 / `terminology.md` 228。

#### W1 / W2 / W3 への申し送り（追加 3 件）

5. **決定木に「条件ロード化」を第 7 の出力として追加するかを判断すること**。条項を 1 文字も削らずに起動時コンテキストから外せるため、**「削るか残すか」の費用計算そのものが変わる**（Fable 改訂 2「立証責任の反転」の前提に影響）。候補の粗い試算 = `subprocess-encoding-convention.md` 11,324 / `terminology.md` 9,846 / `planning-quality-guideline.md` 7,596 / `rule-002.md` 7,409 / `code-quality-guideline.md` 6,947 / `rule-001.md` 4,720 / `test-result-output.md` 3,210 = **計 51,052 文字（全体の 33%）**。**この試算は W1 の判定を拘束しない**（NFR-6 準拠 / 目標値ではない）。
6. **W3-M1-T1 の「上位 4 件」の根拠を再評価すること**。9 件中 4 件で打ち切り 5 件を未着手明記とする設計は、upstream が 3 レベル構造を公式の型として示す前に立てたもの。
7. **W2-M1-T3 の範囲に `/doctor` trim 提案の適用を含めるかを判断すること**（現行はモデル ID 直書き除去のみで行数削減を含まない）。

### 未確認（断定しない / FR-19 受け入れ条件 2）

| 項目 | 状態 |
|:-----|:-----|
| ~~`claude doctor` コマンドの実体・機能~~ | **解消（2026-07-25）**。`/doctor` の trim 提案機能として確認（上表参照 / v2.1.206+） |
| `paths` scoped rule の Write 経路での発火有無 | **未検証**。「読んだとき」発火の仕様上、Read を伴わない Write で規約が届かない懸念。`InstructionsLoaded` hook で実測可能 |
| memory tool（public beta）の Claude Code での利用可否 | **未確認**。Anthropic engineering 記事は API の機能として記載。Claude Code 側での提供有無は未検証 |
| Fable 5 の launch 詳細ページ | **未取得**。GA 日（2026-06-09）は models overview から取得したが、`introducing-claude-fable-5-and-claude-mythos-5` は未読 |
| Claude Mythos 5 | 招待制（Project Glasswing）。Fable 5 と同スペック・同価格。**LAM は対象外** |

---

## W0-M1-T3: ベースライン測定 6 項目（W0 起点）

**実施日**: 2026-07-25（セッション 6）
**担当**: L1 直（手順が design §4.1 に確定済 = 判断が残っていないため委譲 overhead > 効果）
**対応仕様**: design.md §4.1 / requirements.md FR-8, NFR-3 / tasks.md W0-M1-T3

| # | 項目 | W0 起点の実測値 | 取得方法 |
|:-:|:-----|:----------------|:---------|
| 1 | pytest 全数 | **1047 passed / 14 skipped**（29.64s / exit 0） | `bash .claude/scripts/py_invoke.sh -m pytest -q` |
| 2 | Green State 件数 | **Critical 0 / Warning 0**（G1 通過） | R-2 W1 末ゲート記録から転記（`retro-R2-W1-M1-PLANNING-2026-07-25.md` L42） |
| 3 | `tdd-patterns.log` FAIL→PASS 率 | **算定せず**（下記） | — |
| 4 | gabriel verdict 分布 | **refuted 3 / confirmed 0 / inconclusive 0**（母数 = `invoked:true` の 3 件） | `.claude/gabriel-metrics.log`（全 4 行 / うち `invoked:false` 1 件は母数外） |
| 5 | PM 級ダイアログ発火数 | **0**（M-1 着手前のため） | 定義上ゼロ |
| 6 | `CLAUDE.md` + rules 文字数 | **154,837 文字** | `cat CLAUDE.md .claude/rules/*.md .claude/rules/*/*.md \| wc -m` |

**NFR-3 との突合**: 起点 1043 passed + 14 skipped（commit `2ac4e91`）に対し **+4 passed**。増分は W0-M1-T2 で追加した XML 鮮度判定のテスト。**regression ゼロ**（PASS 数が減っていない）。

### 項目 3 を算定しない理由（確定済 / 上記 W0-M1-T2 §T3 で確定すべき論点 参照）

計器（XML 鮮度判定）は T2 で修正されたが、修正前の履歴は盲目の計器で採られている。案 1 を採用し、**W0 側は算定せず / W4 側のみ実測値として報告 / 差分比較には用いない**。DoD-4 の判定は項目 1（pytest regression）と項目 5（PM 級ダイアログ発火数）で行う。

### 項目 6 の内訳（W1 トリアージの優先順位付け入力）

**この 18 ファイルは毎セッション全文が注入される**（本記録を作成したセッションのシステムプロンプトで実測確認）。

| 文字数 | ファイル | 累積比 |
|-------:|:---------|-------:|
| 20,458 | `.claude/rules/hga-summoning.md` | 13.2% |
| 17,183 | `CLAUDE.md` | 24.3% |
| 16,097 | `.claude/rules/fable-l3-protocol.md` | 34.7% |
| 12,360 | `.claude/rules/phase-rules.md` | 42.7% |
| 11,324 | `.claude/rules/subprocess-encoding-convention.md` | 50.0% |
| 9,846 | `.claude/rules/terminology.md` | 56.3% |
| 7,596 | `.claude/rules/planning-quality-guideline.md` | 61.2% |
| 7,409 | `.claude/rules/auto-generated/rule-002.md` | 66.0% |
| 7,317 | `.claude/rules/model-delegation-prompting.md` | 70.8% |
| 6,947 | `.claude/rules/code-quality-guideline.md` | 75.2% |
| 6,751 | `.claude/rules/permission-levels.md` | 79.5% |
| 5,105 | `.claude/rules/auto-generated/trust-model.md` | 82.8% |
| 4,720 | `.claude/rules/auto-generated/rule-001.md` | 85.9% |
| 4,634 | `.claude/rules/security-commands.md` | 88.8% |
| 4,287 | `.claude/rules/decision-making.md` | 91.6% |
| 4,056 | `.claude/rules/upstream-first.md` | 94.2% |
| 3,887 | `.claude/rules/core-identity.md` | 96.7% |
| 3,210 | `.claude/rules/test-result-output.md` | 98.8% |
| 1,650 | `.claude/rules/auto-generated/README.md` | 100.0% |

**上位 3 件で 34.7%**。`subprocess-encoding-convention.md`（11,324 / 7.3%）と `terminology.md`（9,846 / 6.4%）は**参照時にのみ必要な規約**でありながら常時注入されている = W3 の progressive disclosure 化の有力候補（ただし対象選定は W1 の判定を経ること）。

### 項目 4 の解釈上の注意（W1 / T8 への申し送り）

母数 3 件と小さいが、**gabriel は `invoked:true` の全件で `refuted` を返している**（CASPAR の統合結論を 3/3 で反証）。これは gabriel が形骸化しておらず実効性を持つことの示唆であり、**「Opus 5 公式が subagent による自己検証を非推奨としている」を根拠に gabriel を機械的に削除してはならない**という T5 §2 (d) の留保を数値面から補強する。ただし母数 3 は統計的裏付けには不足するため、**断定はしない**（W4 再測定時に母数が増えるかを確認する）。

---

## W0-M1-T6: ADR-0001 突合 + requirements FR-20 説明文の訂正

**実施日**: 2026-07-25（セッション 6 / **完了** = grep 実測 + PM 級判断 2 件の実施）
**担当**: L1 直（grep 実測 + PM 級編集）
**対応仕様**: design.md §4.4 / requirements.md FR-20 / tasks.md W0-M1-T6

### grep 実測（`grep -n "^model:" .claude/agents/*.md` / 全 12 ファイル）

| model 値 | 件数 | 該当ファイル |
|:---------|-----:|:-------------|
| `sonnet` | **9** | code-reviewer / design-architect / doc-writer / gabriel / goal-driven-l2-foreman / goal-driven-l3-executor / quality-auditor / requirement-analyst / tdd-developer |
| `haiku` | **3** | goal-driven-grader / task-decomposer / test-runner |
| 不明・未設定 | **0** | — |
| `command` / `fable` | **0（未検出）** | — |

**design §4.4 の 2026-07-25 実測（sonnet 9 / haiku 3 / 不明 0）と完全一致**。

### 不一致 (i): requirements.md FR-20 説明文（**PM 級 / 実施済 2026-07-25**）

requirements.md FR-20 説明文の「**sonnet 8 / haiku 3 / 不明 1**」は**誤り**であることが確定した。実測は sonnet 9 / haiku 3 / 不明 0。**訂正が必要**（PM 級編集 / W0 の K5 宣言済）。

### 不一致 (ii): ADR-0001 の drift（**PM 級判断 / 実施済 2026-07-25**）— **3 箇所 / うち 1 件は ADR 内部の自己矛盾**

| # | 箇所 | ADR-0001 の記述 | 2026-07-25 実測 | 種別 |
|:-:|:-----|:----------------|:----------------|:-----|
| 1 | L9（改訂履歴） | 「12 agents で `command\|sonnet\|haiku\|fable` 混在指定」 | `command` 0 件 / `fable` 0 件 | **レイヤー混同** |
| 2 | L52（決定 §注記） | 「subagent 別に `command\|sonnet\|haiku\|fable` を明示」 | 同上 | **レイヤー混同** |
| 3 | L56（決定 §注記） | 「goal-driven-l3-executor = haiku」 | **`model: sonnet`** | **事実誤記** |

**#1・#2 の本質（drift ではなく自己矛盾）**: ADR-0001 自身の「決定」§表（**L44**）が `command` を「**第 1 層: パスベース / handler type = `command` / model = なし**」と定義している。すなわち `command` は **hooks の handler type** であって `.claude/agents/*.md` の `model:` 値ではない。L9 / L52 はこれを agents の model 値として列挙しており、**同一文書内でレイヤーを取り違えている**。`fable` は実ファイル・hook のいずれにも存在しない。

したがって本件は「ADR の記述が古くなった（drift）」ではなく「**ADR の記述が当初から誤っていた**」に分類すべきであり、requirements.md FR-20 の説明文もこの誤りを引き継いでいた（同ファイルに追記済）。

**#3 の位置づけ**: L56 は「12 agents 実測」と称して `goal-driven-l3-executor = haiku` を挙げるが、実ファイルは `sonnet`。2026-07-10 の注記追加時点で既に誤っていたか、その後に実ファイルが変更されたかは**未確認**（git log の追跡で判別可能だが本 Task の範囲外）。

**L1 の推奨**: 実ファイル側は一貫しているため「実ファイル修正」は不要。**ADR-0001 に時点注記を追加**し、#1・#2 は「`command` は hooks の handler type であり agents の model 値ではない / `fable` は未使用」、#3 は「2026-07-25 実測で `sonnet`」と明記する方式を推奨する。ADR の慣習として過去の決定文は書き換えず追記で訂正する。ただし **`docs/adr/` は W0 の K5 宣言に含まれていない**ため、**追加宣言 + ユーザー承認が必要**（FR-3 受け入れ条件 3 の手続きに準じる）。

### T6 の実施記録（2026-07-25 / PM 級承認済）

**追加 K5 宣言**: `docs/adr/0001-model-routing-strategy.md`（W0 の K5 一括宣言に含まれていなかったため、FR-3 受け入れ条件 3 の手続きに準じてユーザーへ追加宣言し、**同日承認を得た**）。

| 対象 | 実施内容 | 結果 |
|:-----|:---------|:-----|
| `requirements.md` FR-20 説明文 | 実測値へ訂正（sonnet 8 / haiku 3 / 不明 1 → **sonnet 9 / haiku 3 / 不明 0**）+ ADR-0001 のレイヤー混同を注記 | ✅ 完了 |
| `docs/adr/0001` §改訂履歴 | 訂正 1 行を追記（3 点の誤りの要旨 + 実ファイルは修正不要である旨） | ✅ 完了 |
| `docs/adr/0001` 「決定」§ | **注記 2** を新設し、3 点の誤りを訂正（過去の決定文は書き換えていない）+ 12 agents の実測値表を掲載 | ✅ 完了 |
| `.claude/agents/*.md` | **変更なし**（実ファイル側は一貫しており修正不要と判定） | ✅ 判定完了 |

**採用した方式**: 「ADR 側に時点注記を追加」（L1 推奨どおり）。ADR は決定の記録であるため過去の決定文は書き換えず、注記による追記訂正とした。

**未確認として残した事項**: #3（`goal-driven-l3-executor = haiku` vs 実測 `sonnet`）について、2026-07-10 の注記追加時点で既に誤っていたのか、その後に実ファイルが変更されたのかは **git log の追跡で判別可能だが本 Task の範囲外**とした（ADR 側の注記にも同旨を明記済み）。

---

## W0-M1-T8: 外部知見の照合（HGA 召喚 / M-1 方式の妥当性検証）

**実施日**: 2026-07-25（セッション 6）
**担当**: L1 直（ブリーフ編成・召喚・正本化）
**召喚形態**: Fable 単独召喚 / tight brief（5-slot）/ 通常モード
**実測**: `subagent_tokens` 100,441 / `tool_uses` **0**（資料要求 0 回 = index push + currency push が有効）/ duration 約 3.8 分
**routing**: Fable 5（`claude-fable-5`）で生成。降格の兆候なしと自己申告あり。「要検証の仮定」の申告もなし

### 総合判定: **revise**（小規模改訂 / 新 Task を増やさない形）

W1 の作業自体は改訂後ただちに進めてよい、との判定。**W0 の撤退条件（3 分岐すべてで W1 に進める）における「別方式が必要」に該当**するため、design / tasks の改訂を **PM 級で 1 回提案**する。**再召喚は行わない**（ステートレス規律）。

### crux 1: 4 軸 + 決定木は出口か次の階層か

**判断**: 現設計のままでは**次の階層**。ただし欠陥は決定木そのものではなく、その**外側の 2 つの欠落**にある。これを足せば同じ決定木が出口の部品になる。

| 欠落 | 内容 |
|:-----|:-----|
| **流入制御の不在** | 現決定木はストック（≈750 行）への一回性の処理であり、**新規条項が生まれるフローに触れていない**。フローが不変なら数 Milestone 後に同じ棚卸しが必要になり、それは定義上 M-2 = 次の階層になる |
| **大域的終了条件の不在** | 個々の判定が 5 値の閉集合で閉じることは、Milestone ジャンルが閉じることを意味しない。閉じているのは verdict であってループではない |
| **（第 3 の欠落）基質適合テストの不在** | 軸 4 の発火実績は**すべて Opus 4.x 以前の基質での観測**。検証系足場は「発火実績があっても」Opus 5 では over-verification 側の害に転じうる。**旧基質での発火は新基質での必要性の証拠にならない** |

**内部証拠**: W0 で「計器が盲目だった」ことに 2 Task 消費した事実自体が、**この手続きが保守対象の機構を増やしている**ことの実測であり、階層であることの証拠になる。また rule-002 が rule-001 型 drift の保守のために存在することも同型。

**事前分布の指摘**: Phase B の 4 セル中 2 セルが保全デフォルトである点は、Anthropic の 80% 削減実績（削って性能低下なし = **指示は既定でコスト**）と逆向きの事前分布を符号化している。この保守的事前分布のままでは体系的に削り残しが出て、残渣が次の consolidation の燃料になる。

**却下された代替案**: (a)「5 値閉集合 + 台帳で作業が有界だから既に出口」→ 却下。(b)「トリアージ全廃・一括 80% 削減して結果計測」→ **全面採用は却下**（統治条項は設計上めったに発火しないため「消して様子を見る」は損失が稀で高額な分布からのサンプリングになり、結果計測で妥当性を検証できない）。**Phase A の veto スクリーニングは本当に必要**。ただし Phase A 通過後の残りには部分採用すべき。

### crux 2: 「運用移管」を追加すべきか

**判断**: **追加すべき**。ただし無条件の値ではなく、**3 つの必須フィールド（観測シグナル / 監視面 / 失効日）と同時保有上限**を伴う値としてのみ追加する。

**根拠の核心**: **リスクを機構なしで受容するという決定は、それ自体が軸 1 のユーザー意思（リスク許容度の宣言）である**。現行の「削減」でこれを行うと、**統治判断が台帳に無記録のまま消える**。LAM 自身の第一原理（軸 1 の判断は保全対象）に照らして、リスク受容は一級の出力値として記録されるべき。

また currency push (3)(4) が生む条項クラス —「指示としては削除すべきだが、懸念自体は消えず、基質の自己検証 + 人間の折々の目視に移る」— の正しい判定値は削減でも保全でもなく運用移管である。W1 でこのクラスが確実に複数出る以上、値の不在は判定の歪みを強制する。

**無条件追加を退ける理由**: 監視面を指定しない運用移管は「削除の婉曲語」か「誰も実行しない ops 負債」に退化する。**この系で最も希少な資源は単独ユーザーの注意**であり、運用移管 1 件 = 人間注意への恒常的債権。上限とフィールドなしに多数発行すれば、ops チェックリストという名の新しい rules ファイルが生まれ、**ループが衣装を替えて再発する**。

**却下された代替案**: (a)「削減 + 台帳注記で足りる」→ 却下（注記は write-only で再読動線がなく、「リスク不存在と判定」と「リスク受容して監視」の統治上の区別が消える）。(b)「保全のサブフラグ = advisory 降格」→ 却下（認知負荷コストだけ払って強制力ゼロの両損 / 80% 削減の根拠に正面から反する）。(c)「deferred に見直し日を付けて流用」→ 却下（意味論が違う。下記）。

### crux 3: 判定基準と、deferred / characterization pin との違い

**「運用で見る」と宣言して閉じてよい 3 条件（同時充足）**:

1. **発火が無計装でも喧しい**（普通に作業していれば嫌でも気づく）← **主ゲート**
2. **Phase A を通過済み**（= 可逆・爆風半径が有界）
3. **発火頻度 × 復旧コスト < 機構維持コスト**（機構が将来の監査対象面になるコストを含む）

加えて **シグナル 1 行 + 監視面（= retro のみ）+ 失効日**を記録し、ユーザーがリスク受容を承認（PM 級 1 行）した場合に限る。

**主ゲートの理由**: 機構の存在理由は**沈黙する失敗の検出**であり、失敗が自ら騒ぐなら機構は冗長。逆に静かに潜伏する類（データの静かな破損 / セキュリティ）は運用の注意では原理的に捕まらず、**運用移管は永久に不可**。

**機構維持コストの過小評価**: LAM では系統的に過小評価されてきた（計器が盲目で 2 Task / rule-001 の regex が命名体系変更のたびに発火し rule-002 がその保守のために起票）。**機構は監査面を増やし、監査面は issue を増やす**。この二次コストを算入すると条件 3 を満たす条項は直感より多い。

**三者の意味論の区別（この定義を SSOT とする）**:

| 概念 | 意味論 | 帰結 |
|:-----|:-------|:-----|
| **deferred** | **未決定** | tracker に未完了作業として居座り、以後の全 design doc に再出現する（R1-054〜058 が実証）。**deferred の在庫自体がループ燃料** |
| **characterization pin** | **観測の機構化・判断の先送り** | 判断していないのに保守コスト（same-commit 更新義務という恒常税）が発生。機構である以上、監査対象面でもあり続ける |
| **運用移管** | **決定済み・非機構化を選択・クローズ** | 作業台帳から消え、リスク受容記録として残る |

**再機構化の経路は新設不要**（決定的に安い）: 移管済みリスクが発火すれば、それは既存定義の「検出イベント」1 カウントであり、`trust-model.md` の閾値 2 で既存の draft rule 起票フローに自動合流する。**運用移管は既存ループの入口に接続するだけ**で、独自のエスカレーション機構を一切要さない。

**失効日の対称性**: 窓内に発火すれば既存機構が拾い、窓を沈黙で満了すれば懸念ごと消滅（リスクが実在しなかった事後証明）。**どちらに転んでも閉じる**。

### 提案された改訂 5 点（新 Task を増やさず、決定木の定義と W1 の判定手順に畳み込む）

| # | 改訂内容 | 影響先 |
|:-:|:---------|:-------|
| 1 | **運用移管を第 6 値として追加**。台帳記録は 4 値に（圧縮 / 削減 / SSOT 退避 / 運用移管）。エスカレーションは `trust-model.md` の既存閾値に接続し**新機構ゼロ**で実装 | design §5.2 決定木 / §6.3 台帳 / tasks W0-M1-T4 |
| 2 | **Phase B の立証責任を反転**。「発火ゼロ × 意図」セルの既定を保全（低優先）→ **削減または運用移管**に変更。**保全判定に理由 1 行を必須とし、削減には理由を要求しない** | design §5.2 決定木 / tasks W1-M1-T5 |
| 3 | **基質適合テストを Phase B に 1 問追加**: 「**Opus 5 は指示なしでこれをやるか**」。検証系足場（自己監査 14 項目 / F4 / AUDITING チェックリスト / TDD R 系）は**旧基質での発火実績を軸 4 の証拠として無効扱い**にする | design §5.2 / tasks W1-M1-T4, T5 |
| 4 | **出口宣言を M-1 の完了条件に含める**（3 点）: (a) M-1 は一回性であり consolidation 系 Milestone のジャンルをここで閉じる / (b) 以後この決定木は**新規条項の誕生ゲート**として適用し（流入制御）、定期棚卸しとしては再実行しない / (c) 規範負荷の総量に **no-net-growth**（新条項 1 追加 = 既存から同等量の削減）を課す | requirements DoD / tasks W4-M1-T5 |
| 5 | **gabriel は基質適合テストを通過しうる**（公式が禁じるのは「自己出力の検証への subagent 使用」であり、gabriel は相関盲点を持つ合議**判断**への脱相関コンテキストからの敵対 probe で**対象クラスが異なる**）。ただし通過は自動ではなく **W1 で個別判定**せよ | tasks W1-M1-T4 |

**改訂 4 の重み**: この 3 点がなければ、どれほど良い判定を積んでも M-1 は次の階層として記録される、との判定。

### 弱い仮定（Fable 自己申告）

唯一の弱い仮定は「**新規条項の流入速度が現在も有意**」であること。流入が既に枯れている（`trust-model.md` の閾値運用で新 rule 起票が年数件レベルに落ちている）なら流入制御の緊急度は下がるが、その場合でも害はない。

**L1 補足（実測）**: 本 W0 期間中に `rule-002` が新規起票されている（2026-07-25 / R-2 W1-R2-T4）。**流入は枯れていない**ため、この弱い仮定は現時点で成立側にある。

---

## W0-M1-T4: 削減台帳スケルトン作成（8 列 / ヘッダのみ）

**実施日**: 2026-07-25（セッション 6）
**担当**: L1 直
**成果物**: `docs/artifacts/m-1-clause-ledger.md`

T8 の判定 `revise` を受けた PM 級改訂（ユーザー承認 / 2026-07-25）により、**列構成が 7 列 → 8 列**、**判定列が 3 値 → 5 値**に変更されたため、**改訂の確定を待って作成した**（先に 7 列で作れば即座に手戻りになるため / 順序判断は本セッションの L1 判断）。

**完了条件の充足**:

| 完了条件 | 状態 |
|:---------|:-----|
| ファイルが作成されている | ✅ |
| 列が 8 種（条項ID / 原文 / 出典 / 判定軸（軸1〜4 + 基質適合）/ 判定 / 移動先・監視条件 / ロード条件 / 判定日） | ✅ |
| 「判定」列が 5 値の閉集合であることを表の直下に明記 | ✅ |
| 「移動先 / 監視条件」列の運用移管書式（`retro / シグナル: <1 行> / 失効: YYYY-MM-DD`）を明記 | ✅ |
| 冒頭に帳簿単一原則を明記（NFR-2 受け入れ条件 1） | ✅ |
| W0 時点でデータ行がゼロ | ✅ |

**あわせて記載した事項**（W2-M1-T5 / T9 の実行時の誤読を防ぐため）: 記録対象の定義（実ファイルを変更した全件 / 「保全（無変更）」「対象外」は記録しない）、**トリアージ表と本台帳の件数が一致しないこと**、運用移管の判定 3 条件・同時保有上限 5 件・PM 級承認要件、再機構化が `trust-model.md` の既存閾値へ自動合流すること、deferred / characterization pin との意味論の区別。

---

## W0-M1-T7: W0 完了判定（順序制約 + 記録完全性の確認）

**実施日**: 2026-07-25（セッション 6）
**担当**: L1 直（記録の突合 + pytest 1 回 = 委譲 overhead > 効果のため / 応答内 1 行で可視化済）
**判定**: **W0 完了 / W1 着手可**

### 完了条件の充足

| # | 完了条件 | 結果 |
|:-:|:---------|:-----|
| 1 | 本ファイルに記録 5 種（測定 6 項目 / probe 判定 / upstream 裏取り / ADR-0001 突合 / T8 crux 回答）がすべて存在 | ✅ T1・T2・T3・T4・T5・T6・T8 の 7 節を確認 |
| 2 | `m-1-clause-ledger.md` が **8 列**ヘッダで存在（データ行ゼロ） | ✅ ヘッダ 1 行 + 区切り行のみ / 直下に「W0 時点でデータ行はゼロ」を明記 |
| 3 | `hga-summon-log.md` に T8 の召喚記録が追記されている | ✅ **#17**（2026-07-25 / tool_uses 0 / 往復 0） |
| 4 | pytest 再実行で regression ゼロ | ✅ **1047 passed / 14 skipped**（W0 起点 = `2ac4e91` の 1043+14 に T2 の新規 4 件 / **PASS 数の減少なし**） |
| 5 | 測定項目 3 の扱いが W0 完了時点で確定（W1 へ持ち越さない） | ✅ **案 1 で確定**（W0 側は算定せず / W4 側のみ実測値 / 差分比較に用いない / DoD-4 へ反映済） |

### 順序制約の充足（tasks.md §2）

| 制約 | 内容 | 状態 |
|:----:|:-----|:-----|
| 制約 1 | W0 ベースライン測定 → W2 着手 | ✅ T3 完了。**W2 の全 Task が着手可能な前提を満たした** |
| 制約 2 | 計器較正 → ベースライン測定 | ✅ T1（probe）→ T2（XML 鮮度判定の実装）→ T3 の順で実施済 |
| 制約 3 | W1 判定 → W2 適用 | — （W1 未着手 / W1 中の圧縮・削減は禁止） |

### W0 で確定した事項（W1 着手時の入力）

1. **計器の較正**: `tdd-patterns.log` の記録盲点の根本原因は C2（XML 鮮度検査の欠如）1 本と確定し、mtime センチネル方式で修正済。**並列共有 XML の誤採用は残存**（M-1 スコープ外 / 実害が出たら起票）
2. **測定 6 項目の W0 起点**: pytest 1047+14 / Critical 0・Warning 0 / 項目 3 は算定せず / gabriel refuted 3（母数 3）/ PM 級発火 0 / **`CLAUDE.md` + rules = 154,837 字・2,749 行**
3. **upstream 一次資料**: Opus 5（2026-07-24 リリース / 1M / $5・$25 / effort 5 段階 / thinking 既定 ON）ほか 4 モデルのスペックを取得。**規律肥大化への upstream 対処法**を 3 分類 + 想定外の第 4 分類（**LAM の一部条項は Opus 5 で有害**）で記録
4. **ADR-0001 の drift 3 箇所**を確定し訂正（うち 2 件は ADR 内部のレイヤー混同）。実ファイル側は一貫しており修正不要
5. **M-1 の方式妥当性**: HGA #17 の判定 `revise` を受け、**PM 級改訂 9 点**を design / requirements / tasks に反映済（Task はゼロ増）。決定木は **6 値**、台帳は **8 列**、**ロード条件は直交属性**、**DoD-7（出口宣言 3 点）** を新設

### W1 への申し送り

- **W1-M1-T1 のトリアージ表は 11 列**で作成する（基質適合 / ロード条件を含む）
- **Phase B の立証責任は「残す」側にある**（「発火ゼロ × 意図」の既定は削減または運用移管 / 保全にのみ理由 1 行必須）
- **基質適合テストで gabriel を機械的に無効化しない**（対象クラスが異なる / 個別判定して根拠を記録）
- **条件ロード化を理由に削減判定を保全へ覆さない**（MUST NOT / design §5.2.4 ガード）
- 運用移管は **同時保有上限 5 件** / 3 フィールド（観測シグナル / 監視面=retro / 失効日）必須 / **W1-M1-T6 の一括承認でリスク受容の承認を得る**

> **注**: W0-M1-T8（外部知見の照合 / HGA 召喚）は 2026-07-25 セッション 6 で追加された Task。
> 実行順は T5 完了後・T7 の前（tasks.md §3 / §2 依存グラフ）。
