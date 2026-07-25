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

design §4.5 が挙げた **経路 (a)・経路 (b) はいずれも記録欠落の原因ではない**（両方とも実測で否定）。真の機構は次の 2 つで、**両者が重なったときにのみ**記録が失われる。

| # | 機構 | 内容 |
|:-:|:-----|:-----|
| **C1** | **記録トリガの束縛** | FAIL の記録は「pytest が失敗したこと」ではなく「**Bash ツールが非ゼロ終了したこと（PostToolUseFailure イベント）**」に束縛されている。`\| tail` などのパイプ・`\|\| true`・`; echo` 連結で tool exit が 0 に潰れると、Red は失敗イベントとして扱われない |
| **C2** | **XML 鮮度検査の欠如** | 非失敗イベント経路（`PostToolUse`）は `.claude/test-results.xml` の鮮度を一切検査せず、**前回実行の結果をそのまま当該コマンドの結果として採用**する。`-o addopts=""` で XML が更新されない場合や、そもそもテストを実行していないコマンドでも同じ |

**C1 + C2 が重なると、失敗したテスト実行が `pass` として上書き記録される**（無音の損失 + 汚染）。実測で再現済（下記 Q 行）。

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
| 66-73 | `_TEST_CMD_PATTERN` / `_is_test_command` — コマンド文字列の**字句一致**のみ | C2（テスト未実行でも発火） |
| 208-214 | `is_failure_event` 分岐 — XML を読まず直接 FAIL 記録 | C1（この経路だけが FAIL を書く） |
| 216-222 | `_parse_junit_xml` — **mtime を検査しない** | C2 |
| 163-179 | `_record_pass` — `prev_was_fail` が False なら**追記しない** | 無音化 |
| 404-409 | `main` — `tool_name == "Bash"` かつ `hook_event_name` で分岐 | C1 |

### R-2 W1（2026-07-25）の記録 0 件との関係

C1 + C2 の重なりで説明できる（並列 subagent が `-o addopts=""` 規約を用い、かつ出力をパイプで受けて tool exit が 0 になる形）。**ただし当時の実コマンド文字列は残っていないため、この説明の寄与は未確認**（推測であり観測ではない）。確定しているのは「C1 + C2 が重なれば失敗が pass として記録される」という機構の存在（Q 行で実測）までである。

### W0-M1-T2 への引き継ぎ（1 行）

> **直すべきは「subagent 判定」でも「XML パス分離」でもなく、(C1) FAIL 記録を tool の終了コードに依存させている点と、(C2) XML の鮮度を検査していない点である。**

修正案の方向（T2 で判断 / NFR-2 準拠 = 新規帳簿・新規ログ・新規集計スクリプトを作らない）:

1. `_handle_test_result` の非失敗イベント経路に **XML mtime の鮮度検査**を追加し、hook 起動時刻より古い XML は「当該コマンドの結果ではない」として WARN 記録のみでスキップする（C2 の解消）
2. 鮮度検査が入れば、`is_failure_event` に依存せず XML の `failures > 0` から FAIL を記録できるようになる（C1 の緩和）
3. `-o addopts=""` 運用そのものは共有 XML の clobber 回避として維持し、規約側は変更しない（鮮度検査があれば「更新されなかった XML を誤採用する」害が消えるため）

### 後片付け

- [x] `tdd-patterns.log` に synthetic 3 行（07:11:36Z / 07:11:58Z / 07:13:38Z）を識別する `PROBE` マーカーを追記（W0-M1-T3 の FAIL→PASS 率算定から除外するため）
- [x] **`.claude/tests/tmp_probe_w0m1t1/` を削除**（2026-07-25 / ユーザー実施 — `rm` は `security-commands.md` の deny 対象のため AI は実行しない）。`find` で `tmp_probe` / `probe_fail` / `probe_pass` の残骸ゼロを確認済、`.claude/tests/` 直下は probe 前と同一（`dashboard` / `hooks` / `rules` / `scripts` / `wave_c`）

> **環境メモ**: LAM の Bash ツール実体は Git Bash だが、**ユーザーが操作する端末は PowerShell** である。ユーザーへ削除等を依頼する際は `rm -rf <path>` ではなく `Remove-Item -Recurse -Force <path>` の形で渡すこと（`rm -rf` は PowerShell では `Remove-Item` のエイリアスに解決され `-rf` が未知パラメータとなって失敗する / 2026-07-25 実測）。

---

## W0-M1-T2〜T7

（未着手）
