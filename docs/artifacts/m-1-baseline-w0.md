# M-1 W0 ベースライン記録

| 項目 | 内容 |
|:-----|:-----|
| Milestone | M-1 / Wave 0（準備） |
| 対応 Task | W0-M1-T1〜T7（`docs/specs/m-1-opus5-migration/tasks.md` §3） |
| 作成日 | 2026-07-25 |
| ステータス | **記録中**（T1 完了 / T2〜T7 未着手） |

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

---

## W0-M1-T3〜T7

（未着手）
