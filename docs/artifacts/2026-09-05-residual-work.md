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
| **1** | **Action 4** = 正本 97 箇所の namespaced 化 → 派生を再生成 → 「正本に bare 実行参照が残っていない」検査を追加 | **次はここ** | **どれを「実行参照」と見なすか**。`gabriel` の 63 箇所は大半が散文で変換対象ではない。曖昧なまま機械置換すると `release/SKILL.md` で踏んだ「意味が壊れる」型を 97 箇所へ広げる |
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
| 3 | plugin 有効環境で bare `test-runner` が何を解決するか | **第 2 段の入場条件**。LAM 内では project 側が組み込みに勝つと実測済 |
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
