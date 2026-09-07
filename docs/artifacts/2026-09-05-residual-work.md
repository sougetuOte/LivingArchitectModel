# 残務一覧（2026-09-05 セッション 33 終了時点）

セッション 33（`/quick-load` → `/full-review` iter0 → Critical 5 件の是正）を締めるにあたり、
**次セッションが最初に読む 1 枚**として残務を集約する。個別の根拠は各リンク先が正本であり、
本ファイルは**所在と優先順のポインタ**である（内容を複製しない —— 複製は必ずドリフトする）。

---

## 0. まず読む順（次セッション）

1. **本ファイル**（残務の全体像）
2. `docs/artifacts/audit-reports/2026-09-05-iter0.md`（**監査の正本** / Warning 22 件の起票本体）
3. `docs/artifacts/2026-09-05-magi-e2e-defect-remediation.md` §Step 5 AoT Synthesis（Action 1-7 と書込集合の閉包）
4. `docs/artifacts/2026-09-04-plugin-migration-progress.md` §2.6（plugin 移行の手順台帳）

---

## 1. 本命ライン（plugin 移行 / 中断せずここへ戻る）

| # | 内容 | 状態 | 着手前に決めること |
|:-:|:--|:--|:--|
| **1** | ~~**Action 4** = 正本 97 箇所の namespaced 化~~ → **Action 4a（agent 名）として 2026-09-06 に完了** | **完了** | 実測が前提を覆した。「97 箇所」は母数ではなく、**skills を含めると T1 チェーンと分裂する**ため **Action 4b に分割**した。設計・棄却案・積み残しは `docs/artifacts/2026-09-06-magi-action4-reference-model.md`（MAGI 2 巡 + **HGA #34**） |
| **1b** | ~~**Action 4b** = skill の slash 形の名前空間化~~ → **2026-09-06 に完了** | **完了** | 本体は slash 形ではなく **T1 に生成器が無かったこと**だった。**T1 生成器を新設**し、T1 の判定を「バイト恒等」→「派生 == 導出(正本)」へ改めた。前提として **ADR-0010 追補 3**（PM 級 / 承認済）で不変条件を「**配布される側**に bare が残っていないこと」へ一般化した。設計は `docs/artifacts/2026-09-06-magi-action4b-skill-references.md` |
| **1c** | ~~**Action 4c** = 182 箇所のうち 37 箇所のパス自己参照~~ → **2026-09-07 に設計完了・PM 級 2 件承認済**。実施は未着手 | **設計完了 / 実施が次** | **前提が 3 段階で覆った**。(1) 4b が分離根拠とした「情報の欠落」は**存在しなかった**（行番号参照 0 件）(2) 192 箇所は**4 種の別問題**で、最大の層 T1 managed には `${CLAUDE_PLUGIN_ROOT}` が**原理的に届かない** (3) 計器の射程外に**機能破壊 13 箇所**と **fail-open した security 機構**が在った。設計は `docs/artifacts/2026-09-07-magi-action4c-path-references.md`（**HGA #35 + MAGI 2 巡 + gabriel 2 回**）。条文は **ADR-0010 追補 4**（承認済）。着手順は **4c-0 → 4c-1 → 4c-2** |
| **1c-0** | **4c-0** = census の 5 点是正（glob 切り詰めバグ / `rglob` 集合判定 / `exists_dev × exists_user` 行列 / フェンス内コマンドを別欄 / `py-fixture` を単一の真の理由へ） | **次はここ** | SE 級。**ゲート化の前に計器を直す**（初日から真っ赤を自作しない）。書込集合 = `census_dangling.py` + そのテスト |
| **1c-1** | **4c-1** = 決定 A・B・C の実施 ＋ 閉包導出器 | **PM 承認済** | **A**: `subprocess-encoding-convention.md` の配布をやめる（**18 箇所が消える**）/ **B**: 実害 13 は手順書き換え（`scale_detector` `build_dashboard` は配らず skip 継続）/ **C**: `incident-patterns.yaml` は hook のパス解決を `${CLAUDE_PLUGIN_ROOT}` 相対フォールバック化して配る ＋ `source_md` の非配布 retro 参照を処理。**配布集合を動かすと T1/T3 が即赤になる**ので同一コミット |
| **1c-2** | **4c-2** = 規則 R-P の実装（T1 順 / T3 逆）＋ codemod ＋ T2 差し替え | 承認済（SE） | R-P・射程・冪等性・合成順・到達性検査は設計アンカー §D1・D6 が確定形。**diff 全数レビュー必須**。**`.claude/{skills,agents}/**` の派生再生成を忘れない**（忘れると T3 が赤） |
| 2 | **Action 7** = 事後突合の計器（宣言した閉包 vs 実際に変わったもの = git 差分 + hook ログ追記） | **繰り上げ提案 / 未承認** | HGA #33 裁定 2 の処方。**末尾に置いたままだと「決めたのに実装しない」型を再生産する** |
| 3 | **Action 5**（D-2 = init のガードと Step 5 の件数一致 / `CLAUDE.md` の Context 別 form 表に 1 行 = **PM 級**） | 未着手 | Action 4・7 と独立 |
| 4 | **Action 6**（宣伝ゲートを「清浄環境で未解決参照 0」へ付け替え + `/release` 結合） | 未着手 | 同上 |
| 5 | **182 箇所の参照是正**（うち components 系 37 箇所は正しい形が `lam-harness:<name>` と確定済） | 未着手 | Action 4 の変換規則が決まれば大半が機械的に片付く |
| 6 | **第 2 段 self-hosting**（検出器 / P2 撤去 / P3 後半 / P4 / P5） | 未着手 | **入場条件**: bare `test-runner` の解決先の実測（下記 §4）。**第 1 段の合格は第 2 段の許可を意味しない**（HGA #31 4-a） |
| 7 | **X-2 = github source での人手スモーク 1 発** | **ユーザー作業** | ループ外 |

---

## 2. `/full-review` iter0 の残り（Warning 22 件 / 起票済・着手していない）

**正本は `docs/artifacts/audit-reports/2026-09-05-iter0.md`。** ここでは優先順だけを置く。
ユーザー決定（2026-09-05）により **その場で直すのは Critical と その回に触った範囲だけ**であり、
以下は「拾いに行く」対象ではなく「触ったときに一緒に直す」対象である。

| 優先 | 内容 |
|:-:|:--|
| **1** | **`-c` を廃して `.py` に寄せる**（C-1 の構造的恒久解 / 今回採らなかった案 (b)）。今回のペイロード判定は**難読化に対して完全ではない**ため価値が残る。`CLAUDE.md` の Python 呼び出し規約（**PM 級**）の改定と 26 箇所前後の変換が要る |
| 2 | **W-1〜W-4 = 監査基盤**。次回の `/full-review` がまともに回るかに直結する（W-1: `which` と CreateProcess の非対称で Stage 1 が生トレースバックで落ちる / W-2: ruff 設定不在で lint ベースラインが再現しない / W-3: 3.8 非互換で 2 ファイルが解析されていない / W-4: チャンクモードが 443 バッチで到達不能） |
| 3 | **W-5〜W-7 = 権限ゲート周辺の残り**（`incident-patterns.yaml` / `current-phase.md` が SE 級 / allow ワイルドカード） |
| 4 | W-8〜W-13（ソース品質）/ W-14〜W-16（構造整合性）/ W-17〜W-21（テスト品質） |
| 5 | ruff 565 件のうち `--fix` 可能分（`I001` / `RUF100` / `UP032` / `F401` 等）。**ただし W-2 を先に片付けないと、将来の ruff 版で結果が変わる** |

---

## 3. 手動作業（**ユーザーのみ** / AI は削除を実行しない）

- `.claude/lam-loop-state.json` —— `/full-review` のループ終了。`active: false` 済だが設計上は**削除**で表現する（gitignore 済なのでリポジトリには影響しない）
- `…/scratchpad/` の `e2e-clone` / `e2e-sandbox` / `p2-clone` と計測スクリプト（セッション 32 からの持ち越し）
- `~/.claude/plugins/cache/lam/`（孤児キャッシュ / **E2E に無害**）
- サンドボックス環境の後始末 —— `…/scratchpad/e2e-sandbox` に **plugin が enabled のまま**、marketplace **`sougetuote-lam` が登録されたまま**

> 削除は `rm` が deny、PowerShell 削除も user 層 hook が block するため、AI からは実行できない。

---

## 4. 未検証の仮説（**信じて進まない**）

| # | 仮説 | 確かめ方 |
|:-:|:--|:--|
| 1 | **py_invoke `-c` のペイロード関門が実ハーネスで発火するか** | pytest は 4 件緑だが**実セッションでの発火は未確認**。`-c "import subprocess; print('probe')"` を 1 回打てば承認ダイアログの有無で判る（**新規 / セッション 33 で作った機構**） |
| 2 | 4 プロジェクト（Mossarium / Kyozai-Athanor / godot-test / plactice-range）の `renames` 移行 | 各プロジェクトで次にセッションを開いたときに起きる。本リポジトリからは確認不能 |
| 3 | plugin 有効環境で bare `test-runner` が何を解決するか | **第 2 段の入場条件**。LAM 内では project 側が組み込みに勝つと実測済。**2026-09-06 追記（HGA #34）**: 組み込み一覧の全文は**記録に残っていない**（2026-09-05 の E2E は得ていたのに elided で記録した）。取得経路は 2 本 —— ①清浄サンドボックスで存在しない `subagent_type` を叩き `Available agents:` **全文**を貼る ②subagent 自身の system prompt の一覧を写させる。**一覧は CC 版と環境に依存するので固定リストにしない**。なお **組み込み `init` skill が実在する**ことは確認済（LAM の `init` は既に ns 済で正しい） |
| 4 | github source と directory source で展開結果に差が無いか | X-2（ユーザー実行の人手スモーク） |
| 5 | `renames` は旧名を別名として生かすため、bare `lam-harness` の曖昧さは完全には消えていない | — |

---

## 5. 長期の積み残し（何セッションも持ち越している）

| 内容 | 状況 |
|:--|:--|
| `fable-spec-opus-implementation-gap` の着手可否 | 記憶側で「緊急度: 高」と書かれたまま、**条件成立（2026-07-26）から 40 日以上未着手**。着手するか、緊急度の記述を下げるかの**どちらかを決める**べき |
| `CLAUDE.md` 251 行（公式目安 200 行超） | 6 セッション持ち越し |
| **T4（hook 宣言の実体検査）が台帳 §C に独立行を持たない** | 機構 #11 の行に併記中。番号を与えるか併記のままにするかは**未判断** |
| **機構 #10 に陰性対照が無い** | LAM 基準で実在判定するため「LAM には在るが利用者環境に無い」が緑になる。与え方は判明済（利用者環境ベースライン）だが、**今入れると 182 箇所が常時赤**になるため Action 4 の後 |
| `~/claude-global-assets` の `lam-harness-legacy` 1.0.0 が 4 プロジェクトで現に有効 | ADR-0010 M-2 の移行は未了 |
| `doc-sync-flag` は構造的に常に空（`src/` が実在しないため） | 既知・対応不要 |

---

## 6. 環境の変化（セッション 33 で変わった / 次セッションが前提にすること）

- **`.venv` に `ruff` 0.16.6 と `bandit` 1.9.4 を入れた**。これが無いと `/full-review` Stage 1 が回らない。
  ただし `pyproject.toml` に `[tool.ruff]` が無いため、**lint ベースラインは ruff のバージョンに依存する**（W-2）
- **`py_invoke.sh -c` にペイロード関門が入った**。`subprocess` / `os.system` / `shutil.rmtree` / `unlink` /
  `chmod` / `rename` / `exec(` / `eval(` / `__import__` を含む `-c` は **PM（ask）** になる。
  `-m pytest` やスクリプト呼び出し、`import json` 程度の `-c` は今までどおり素通り
- **PM 級パスが 4 件増え、判定が大文字小文字を区別しなくなった**。
  `.session-pm-edit-cache.json` / `autonomous-state.json` / `gd-session-state.json` / `lam-loop-state.json` の
  Edit / Write は承認ダイアログを伴う（Bash 経由は従来どおり到達しない）
- **gabriel probe を実施したら `.claude/gabriel-metrics.log` に 1 行追記する義務が発生した**
  （`magi/SKILL.md` §Step 4.1 の MUST）。`anchor` に MAGI 記録のパスを入れること ——
  **入れないと `verify_reference_resolution.py` の anchor カバレッジ検査が赤くなる**（2026-09-05 より後の記録が対象）

---

## 7. 異常判定の線（セッション 32 で引いた / 引き続き守る）

- **次に gabriel が critical を返したら 3 巡目**なので、局所修正で流さず **HGA へ**
- **宣言漏れ（宣言 < 実際）が 1 回でも起きたら、Action 7 を最優先に繰り上げる**
- **「緑なのに事実と食い違う」形を見たら即停止**（`rule-001` 観測 #6 型 / セッション 33 でも 1 件実見 = gabriel 計器）

---

## 8. セッション 35（2026-09-07）で判明したこと

- **`.claude/hooks/analyzers/tests` の 565 件が常用の実行対象に入っていない**。
  LAM が「1429 passed」と呼んでいるのは **`.claude/tests` ＋ `.claude/hooks/tests`** であり、
  `analyzers/tests` を足すと **1994 passed / 5 deselected** になる。
  **緑の範囲が宣言より狭い**（`rule-001` 観測 #6 型と同じ形の懸念）。
  なお `analyzers` は 4c-1 の決定 B で「配らない」と決めたパッケージである。
  **どちらが正しい常用範囲かは未判断** —— 実行時間は +3 秒程度なので、含めない理由が現時点で無い
- **計器（`census_dangling.py`）に 2 つの欠陥**があった（4c-0 で是正）——
  `PATH_RE` の glob 切り詰め（`.claude/agents/*.md` → `.claude/agents`）と、
  `py-fixture` 除外の**理由が偽**（9 件中 6 件は配布コードの docstring であってテストフィクスチャではない）
- **FS 問い合わせは NTFS で case を化かす**（実演: `ls -d .claude/Rules` は**成功する**が
  `rglob` 由来の集合では False）。`exists_dev` を `Path.is_file()` で実装してはならない ——
  `permission-levels.md` が 2026-09-05 に踏んだ罠と同型
- **`/release` のゲートは `/release` だけでは走らない** ——
  `test_verify_plugin_containment.py::test_real_repo_has_no_violations` が
  **全 pytest 実行で実リポジトリに `verify()` を走らせている**。
  配布集合を動かす作業（4c-1）は**同一コミットでないと全テストが赤になる**
