# R-2 Milestone Design: 資産整理（rule 整備 / 文書精度 / 環境健全化）

## メタ情報

| 項目 | 内容 |
|:-----|:-----|
| Milestone | R-2 |
| ステータス | Draft（承認待ち） |
| 起草日 | 2026-07-20 |
| 入力 | `docs/specs/r-2-consolidation/requirements.md`（Approved / FR-1〜FR-15, NFR-1〜3, DoD-1〜5） |
| 起草者 | design-architect subagent（L1 委譲） |
| 改訂 | spec-critic + HGA #16（Fable adversarial）二重レビュー統合裁定（Critical 3 / Warning 8 / Info 15）反映（2026-07-20） |

---

## §1 Problem Statement

R-1 retro（`docs/artifacts/retro-R1-2026-07-18.md`）が残した 23 件の Try（T4〜T26）は、以下 3 種の未消化リスクを内包している。

1. **信頼度モデルの構造欠陥**: trust-model.md のカウント単位（検出イベント単位）が未定義のまま rule-002 起票根拠を組み立てると、閾値判定が事後的に恣意化する（FR-4〜FR-6）。
2. **暗黙前提の Fable→Opus 実装ギャップ再発**: rule/検査を「正例だけ」で仕様化すると、誤例で初めて判明する境界条件が実装まで温存される（FR-7, FR-13）。R-1 期の rule-001 拡張（3 回目発火まで応急措置を繰り返した事例）が具体的反証。
3. **文書精度の摩耗**: hardcoded 行番号参照・"N 件相当" 表現・表番号方式の不統一が、編集のたびに静かに劣化する（FR-9〜FR-14）。

本設計は、これら 3 種のリスクに対する **具体的な挿入位置・機構・Done 形式** を確定する。requirements.md の FR/NFR は再展開せず、設計判断の根拠としてのみ参照する。

## §2 Non-Goals

- rule-002 / 各 rule 条項の **完成文面**（BUILDING で執筆する。本設計は挿入位置・構成・参照する事例のみ確定する）
- T16（fable-l3 × Fable-Alembic snapshot 統合方針）・T26（Alembic 応答待ち）の実質検討（requirements.md Non-Goals 通り）
- Wave 4 以降の追加（FR-1 準拠 / 3 Wave 固定）
- 既存 rule-001.md の再改訂（requirements.md Non-Goals 通り）
- **`pyproject.toml` への `dependencies` 追記**（T20 / C1 反映: `pyproject.toml` 冒頭コメントが明記する pip-audit スキップ設計を維持する。dependencies 未記載は意図的な既存決定であり、本 Milestone で覆さない）

## §3 全体構成

### §3.1 3 Wave の設計 view

```
W1 基盤
  T20（突合 script）→ trust-model 2 条項（FR-4, FR-5）→ rule-002 起票（FR-6）
  → T5（encoding 規約）/ T6・T8（gabriel 契約強化）/ T7（gabriel-metrics schema, 機構なし）

W2 文書精度
  T9〜T14（文書精度 6 件） + FR-13 対策 B（暗黙前提明示化リスト条項）

W3 個別消化 + 監査 + retro
  T15（evaluation-kpi §7 削除）+ T17, T22〜T25（個別消化）+ T26（pending 記録）
  + 最終検証（G1-G5 維持確認）+ Milestone retro
```

依存順序（FR-6 直列依存 + FR-9 順序制約）:

```
T20 → (T4, T5, T6, T7, T8 は T20 完了後に着手可 / 相互に独立)
T4 は FR-4, FR-5（trust-model 2 条項）完了後にのみ起票可（FR-6）
```

### §3.2 PM 級ファイル編集計画（K5 一括宣言の実体 / FR-2）

**承認イベント構成（W-b 反映）**: W1 は **2 承認イベント**に分割する。(1) K5 一括宣言（rule-002.md 新規 + subprocess-encoding-convention.md 新規 + large-scale-review/design.md 追記）、(2) trust-model.md 改訂の**単独承認**（DoD-2 の旗艦成果物であり、rule-002 起票の直列前提となるため独立判断枠として扱う）。W2・W3 は各 1 回の K5 一括宣言とする。合計 = K5×3（W1 分割宣言 + W2 + W3）+ trust-model 単独 1 = **4 回**（NFR-3 の目標 4±1 と一致）。

| Wave | 承認イベント | PM 級ファイル | 対応 Task | 編集種別 |
|:----:|:-----------:|:--------------|:----------|:---------|
| W1-(1) | K5 一括宣言 | `.claude/rules/auto-generated/rule-002.md`（新規） | FR-6 / T4 | 新規作成 |
| W1-(1) | K5 一括宣言 | `.claude/rules/subprocess-encoding-convention.md`（新規） | T5 | 新規作成 |
| W1-(1) | K5 一括宣言 | `docs/specs/large-scale-review/design.md` | T6, T8 | 追記（§5.2 パターン節を拡張） |
| W1-(2) | 単独承認 | `.claude/rules/auto-generated/trust-model.md` | FR-4, FR-5 | 追記（2 条項） |
| W2 | K5 一括宣言 | `.claude/rules/terminology.md` | T9, T12, T13 | 追記（新設節） |
| W2 | K5 一括宣言 | `.claude/rules/planning-quality-guideline.md` | FR-13 対策 B | 追記（新設節） |
| W2 | K5 一括宣言 | `docs/adr/0004-bash-read-commands-allow-list.md` | T10 | 追記（ヘッダに関連 ADR 注記） |
| W2 | K5 一括宣言 | `docs/adr/0008-approval-gate-redesign.md` | T10 | 追記（関連 ADR 表に 0004 追加） |
| W3 | K5 一括宣言 | `docs/specs/evaluation-kpi.md` | T15 / FR-11 | 削除（§7） |
| W3 | K5 一括宣言 | `.claude/rules/model-delegation-prompting.md` | T24 | 追記（新設節） |

**非 PM 級で編集する主なファイル**（宣言不要・参考記載）: `.claude/scripts/*.py`（T20, T6/T8 の検査ロジック）、`.claude/tests/**`、`docs/artifacts/*.md`（T7 のスキーマ追記・T9 の hardcoded 参照修正・T23 の template 化）。

> **T7 の編集種別訂正**: T7 は `docs/artifacts/gabriel-metrics-environment-2026-07-05.md`（非 PM 級 / `docs/artifacts/` は SE 級）への**スキーマ追記**であり、Wave 1 の宣言対象 PM 級ファイル一覧には含まれない（§4.6 参照。旧稿の「実測突合」という表現を「スキーマ追記」に訂正）。
>
> **セッション跨ぎの追加ダイアログ（FR-3 接続）**: Wave が複数セッションにまたがり、セッション再開後の初回 PM 級 Edit で追加ダイアログが発生した場合、これは requirements.md FR-3 の「努力目標」条項の許容範囲内であり FR-3 違反とはしない。ただし NFR-3 のダイアログ実数記録には反映する。

### §3.3 機構を伴う Task と純規範文書 Task の対応（requirements §2 用語の再掲・参照用）

| Task | 分類 | Done 形式 |
|:----:|:-----|:----------|
| T4, T5, T6, T8, T20 | 機構を伴う Task | FR-7（正例 + 誤例 + grep baseline） |
| T7, T9〜T14, T17, T22〜T25 | 純規範文書 Task | FR-8（検証手段 1 つ） |

### §3.4 Wave 末 G1 チェック（W-g 反映 / FR-15 全 Wave 適用）

FR-15 は「全 Wave」で G1 基準（980 PASS + 15 SKIP 以上 / regression 0）の維持を求める。§6.4 に加え、**W1 末・W2 末でも同一手順を実施する**:

```bash
bash .claude/scripts/py_invoke.sh -m pytest
# .venv 経由 pytest 実行 / py_invoke.sh の venv-first fallback chain に従う
```

各 Wave 末の Task 完了記録に実行結果（PASS/SKIP 件数）を残す。

---

## §4 Wave 1 設計（基盤）

### §4.1 T20: import 走査 × importability 突合 script（FR-9, FR-7 / W1 先頭 / C1 反映で全面差替）

**旧定義の破棄（C1 対応）**: 初版設計は「`pyproject.toml` の宣言依存 vs `.venv` 実インストール」の突合としていたが、`pyproject.toml` は **意図的に `dependencies` 未記載**（pip-audit スキップ設計 / 同ファイル冒頭コメント確認済み: 「dependencies は未記載＝pip-audit で監査対象が空＝事実上のスキップ設計を維持」）であり、「宣言側」が実在しない。この前提誤りにより初版の突合定義は成立しない。

**新定義**: **「hooks/scripts/tests の第三者 import 全数走査 vs `.venv` での importability」**。retro T20 の原意（2026-07-20 の PyYAML 検出事例 = ある script が `import yaml` するが `.venv` に未インストールで初回実行時に失敗した、という同型の drift）に一致させる。

**配置**:
- スクリプト本体: `.claude/scripts/verify_import_availability.py`（新規 / 非 PM 級）
- テスト: `.claude/tests/scripts/test_verify_import_availability.py`（新規 / 既存 pytest 設定に相乗り）
- 呼び出し: `bash .claude/scripts/py_invoke.sh .claude/scripts/verify_import_availability.py`（`CLAUDE.md` §Python Invocation Convention の skill/手動 CLI form = 相対パス。**素の `python` 起動は使わない** — py_invoke.sh の venv-first fallback chain を経由することで環境差異を吸収する）

**実装方針**:

```python
from __future__ import annotations
# 1. 走査側: hooks/scripts/tests 配下の .py 全ファイルを ast.parse で走査し
#    import 文（import X / from X import Y）のトップレベルモジュール名を集合として抽出
# 2. importability 側: 抽出した各モジュール名について importlib.util.find_spec(name)
#    を .venv インタプリタ上で実行し、None（=見つからない）を drift として報告
# 3. stdlib は importable なので自動的に drift にならない
#    → stdlib 除外リストが不要（sys.stdlib_module_names は 3.10+ 専用 API のため
#      3.8 互換の観点からもこの設計の方が安全 = NFR-2 適合）
# 4. drift 発見時の contingency: pip install 実行を促すメッセージを出力し、
#    grep baseline には「発見時点で未解決の drift 件数」として記録する
#    （script 自体は自動 pip install しない — 副作用を持つ操作は人間判断に委ねる）
```

**正例**: hooks/scripts/tests のいずれかで import され、かつ `.venv` で `find_spec` が成功するモジュール（例: `pytest`, `json`, `pathlib`）→ drift 報告に出現しない。

**誤例**: 意図的に `.venv` から既知パッケージ（例: テスト用に 1 件、実行環境を汚さない方法として一時的な `sys.path` 操作や `importlib.util.find_spec` のモック化で「見つからない」状態を模擬する）を排除した状態を作り、drift として検出されることを確認する（BUILDING の Red ステップで実施。実 `.venv` からのアンインストールは環境破壊を伴うため避け、`monkeypatch` でのシミュレーションを優先する）。

**grep baseline**: 「0 件想定」という事前の決め打ちはしない。BUILDING 着手時に `verify_import_availability.py` を一度実行し、現状の drift 件数（実測値）を Task 完了記録に残す。2026-07-20 の PyYAML 検出事例が示す通り、drift が実在する可能性を前提に設計する。

**NFR-2 準拠**: `from __future__ import annotations` 必須 / `match` 文・`str.removesuffix`・`sys.stdlib_module_names`（3.10+ 専用）不使用。

### §4.2 trust-model.md 2 条項（FR-4, FR-5）

`.claude/rules/auto-generated/trust-model.md` の既存構成（現物確認済 / 全 91 行）に対し、以下 2 箇所に追記する。行番号は**起草時点実測の補助情報**であり、見出し名を主たる位置特定手段とする（BUILDING 時に再実測すること）。

#### 挿入位置 (a): 「## 閾値」節（見出し名で特定 / 起草時点実測: 29-36 行目付近）の直後に新設「## カウント単位」節

- requirements.md §2 用語「検出イベント単位」の定義文をそのまま正として転記する
- 「1 検証イベント内で検出された issue は件数によらず 1 カウント」の定義を明記
- rule-001 実績（4 検証イベント: 2026-06-27 / 07-05 / 07-06 / 07-07）と遡及一貫することを注記
- **データソース拡張の明記（W-c 反映）**: trust-model.md 冒頭「## データソース」節は現状 `tdd-patterns.log`（FAIL→PASS 遷移）のみに閉じているが、検出イベントはこれに限らない。requirements.md §2 用語「検証イベント」の定義（HGA 召喚 1 回 / gabriel probe 1 回 / 監査 Stage 1 回 / `/retro` パターン分析 1 回 / テスト実行 FAIL→PASS 1 セッション）を踏まえ、「検出イベント単位」条項内に **「検出イベントは tdd-patterns.log の FAIL→PASS 遷移に限らず、HGA 召喚・監査 Stage・gabriel probe 等の検証イベント全般を含む」旨を 1 文で明記する**（rule-002 の根拠イベント = HGA #9/#10 + W-R5 監査、がデータソース節の外側に取り残されないようにするため）

#### 挿入位置 (b): 「## ルール寿命管理」節（見出し名で特定 / 起草時点実測: 73-77 行目付近）の直後に新設「## N 回目発火時の恒久解検討」節

- N の初期値 = 3
- rule-001.md「### 拡張の根拠 (2026-07-06 / R-1 W-R1 S1 T6)」節（見出し名で特定 / 起草時点実測: 44-51 行目付近）を具体事例として参照
- 「N 回目発火時点で恒久解（regex 汎化・構造変更等）の検討を必須化する」旨を明文化
- N の変更は trust-model.md 改訂＝PM 級である旨を明記

**Done 検証**（W-f(3) 反映 / 2 条項を個別パターンで 1 件ずつ確認する）:
- 検証手段:
  ```bash
  grep -c "検出イベント単位" .claude/rules/auto-generated/trust-model.md
  grep -c "N 回目発火" .claude/rules/auto-generated/trust-model.md
  ```
  それぞれ 1 件以上ヒットすることを確認する（1 コマンドに圧縮すると `\|`（BRE alternation）の可搬性リスクがあるため分離する）。

### §4.3 rule-002 起票（FR-6 / T4 / C3 反映で FR-7 3 点セット設計を追加）

`.claude/rules/auto-generated/rule-002.md`（新規）を rule-001.md と同構成で起票する。

**C3 の要点**: rule-002 は「散文ルール」であり、rule-001（SESSION_STATE.md の正規表現保守）と異なり単体で pytest fail に直結する対象を持たない。そのため FR-7 が要求する機構実体を以下のように定義する。

**機構実体 = 「parser 世代追随 pytest 群」**（rule-002 の遵守を検証するテスト群）:

1. **(a) GitHistoryParser の Task ID regex テスト**: `.claude/scripts/dashboard/parsers/git_history.py`（または同等の GitHistoryParser 実装）の Task ID 抽出 regex が、現行 Milestone 世代の記法（`W-R\d+-S\d+-T\d+` 等）を正しく捕捉することを assert するテスト。R1-061（GitHistoryParser dashboard 系の残 issue）の修正を含む
2. **(b) verify_reference_resolution の多階層参照・大文字ファイル名捕捉テスト**: R1-054〜058 系（多階層参照退化・regex 非捕捉退化・大文字ファイル名等）の再発を防ぐ assert テスト

**正例**: 現行 Milestone 世代記法（`R-1`, `W-R1`, `W-R2` 等）が両テストで正しく捕捉されること（rule-001.md の fallback regex 拡張と同種の実測）。

**誤例（C3 明記）**: 新世代記法の fixture（例: 架空の次世代命名 `S-1`, `W-S3-T7` 等）を**現行（拡張前）の旧 regex** に投入し、Red ステップで fail することを実証する。この誤例実証により「規則を守らないとテストが落ちる」ことが機構として担保される。

**grep baseline**: 現行 regex が捕捉できない記法の実在件数を BUILDING 着手時に実測する（R1-054〜058, R1-061 の該当箇所を対象に、修正前の drift 件数を記録）。

**rule-002 文書の「検証コマンド」欄**: この pytest 群を指す（rule-001.md が SessionStateParser retention test を検証コマンド欄に記載しているのと同型）。

**構成**（rule-001.md の見出し構造を踏襲）:

```
# Rule 002: [タイトルは BUILDING で確定 — verify_reference_resolution.py 系 +
             GitHistoryParser regex の同型 parser drift 予防]

**生成日** / **ステータス** / **観測回数**: 3 / **last_matched**

## 根拠パターン
| # | 日付 | 検出イベント | 内容 |
|---|------|-------------|------|
| 1 | 2026-07-06 | HGA #9 | R1-054 / R1-055（多階層参照退化・regex 非捕捉退化） |
| 2 | 2026-07-07 | HGA #10 | R1-056 / R1-057 / R1-058（多階層参照退化・regex 非捕捉退化 3 態様・走査 scope 外） |
| 3 | 2026-07-15 | W-R5 監査 | R1-061（GitHistoryParser dashboard 系） |

## ルール
[BUILDING で執筆。機構実体 = §4.3 の parser 世代追随 pytest 群（(a) GitHistoryParser Task ID regex / (b) verify_reference_resolution 多階層参照・大文字ファイル名捕捉）]

## 検証コマンド
[BUILDING で確定 / (a)(b) の pytest 群を指すコマンド]

## 適用範囲
## 権限等級
## 寿命管理
## 参照
```

**根拠パターン表の帰属訂正（W-h 反映）**: 初版は 1 行に圧縮していたが、issue 単位で日付・検出イベントが異なるため 3 行に分解する（上表）。**R1-059（gabriel 契約 substring 弱検査）は T6 の対象であり rule-002 の根拠には含めない**（誤って混入させない）。BUILDING 着手時にイベント単位（HGA #9 / HGA #10 / W-R5 監査）の再確認を Done 条件に含める。

**出典**: `docs/artifacts/hga-summon-log.md` #9（2026-07-06）/ #10（2026-07-07）/ `docs/artifacts/r-1-audit-tracker.md` R1-054〜058, R1-061（2026-07-15 W-R5 監査）。

**FR-6 直列依存の実装**: rule-002.md の起票コミットは trust-model.md 2 条項のコミット後に行う（Git commit 順序で確認可能とする受け入れ条件を満たす）。§3.2 の承認イベント構成（W1-(2) 単独承認が W1-(1) の一部である rule-002.md 宣言より先行しなければならない）と整合させる。

### §4.4 T5: subprocess encoding 規約（FR-7）

**背景（grounding）**: `.claude/scripts/r1_inventory.py` の `subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True)`（59-62 行目）は `encoding=` を指定せず Windows既定ロケール（cp932）に依存する一方、`.claude/scripts/r-1-git-log-usage.py`（45-51 行目）は `encoding="utf-8", errors="replace"` を明示している。両者が LAM リポジトリ内に混在していることを実測確認した。また `.claude/tests/rules/test_reference_resolution.py`（138-144 行目）に `_utf8_env()`（`PYTHONIOENCODING=utf-8` を注入する env ヘルパー）が既に 1 箇所実装されているが、共有ユーティリティ化されていない。

**配置**: `.claude/rules/subprocess-encoding-convention.md`（新規）

**構成**:
- 適用範囲: LAM リポジトリ内の Python 全域（`.claude/scripts/`, `.claude/hooks/`, `.claude/tests/`）
- 規約本文（BUILDING で執筆）: `subprocess.run(..., text=True, encoding="utf-8", errors="replace")` を既定形とする。カスタム `env=` を渡す場合は `_utf8_env()` パターン（`PYTHONIOENCODING=utf-8` を注入）を用いる
- **正例**: `r-1-git-log-usage.py` の実装（`encoding="utf-8", errors="replace"` 明示）
- **誤例**: `r1_inventory.py` の現行実装（`encoding=` 省略）— 本 Task で修正対象として grep baseline に含める
- **grep baseline**: `grep -rn "subprocess.run(" .claude/scripts .claude/hooks .claude/tests` の全ヒットのうち `encoding=` を伴わないものを列挙する（BUILDING 着手時に実測。design.md 起草時点の概算確認では `.claude/scripts/r1_inventory.py`・`.claude/scripts/dashboard/parsers/git_history.py`・`.claude/hooks/lam-stop-hook.py` 等、`encoding=` 省略の呼び出しが複数存在することを確認済 — 正確な件数は BUILDING の Red ステップで確定する）

**FR-7 誤例の実検証（Info 反映: ロケール非依存化）**: cp932 特有の decode 失敗は実行環境のロケールに依存するため、**ロケール非依存の `monkeypatch`** で再現する。具体的には `subprocess.run` をモック化し、`encoding=` 未指定時のデコード経路（`locale.getpreferredencoding()` 相当）を cp932 相当のバイト列で模擬し、`UnicodeDecodeError`（またはサイレントな文字化け）を再現してから修正することを Done 条件に含める。実マシンのロケール設定に依存する再現手順は用いない。

### §4.5 T6: gabriel 契約検査の strict enum 化（FR-7 / W-d, W-e 反映）

**背景（grounding）**: `.claude/scripts/verify_reference_resolution.py` 222-243 行目「パターン 3: gabriel 契約 6 フィールド」は、`_GABRIEL_CONTRACT_FIELDS`（64-71 行目 = `verdict, severity, affected_atoms, reasoning, recommended_action, confidence`）の各フィールド名が対象ファイル本文に **substring として出現するか** (`f not in text`) のみを判定しており、無関係な散文中の出現でも充足してしまう弱検査である（R1-059 / `r-1-audit-tracker.md` 822-830 行目で deferred 記録済）。

**設計方針**: 対象フィールドのうち **enum 値を持つ 3 フィールド（`verdict` / `severity` / `recommended_action`）** を、構造化パース（行頭 `key: value` 形式または `"key":` JSON 風表記の regex）で検査する strict enum 化に昇格する。`affected_atoms` / `reasoning` / `confidence` は enum を持たない自由記述系フィールドのため、既存の presence（substring）検査を維持する（構造化検査の対象外）。

**検査対象の限定（W-e 反映 / Critical 相当の設計修正）**: `verify_reference_resolution.py` の gabriel_targets には `.claude/scripts/magi_dispatch.py` が含まれる（220-227 行目付近）。同ファイルは **Python ソースコード**であり、enum 値は `f"- verdict: {verdict}\n"` のような f-string や dict アクセス（`gabriel_output["verdict"]`）として出現する（実測: 218-232 行目）。「行頭 `key: value`」regex は Python ソースに対して未定義動作（f-string 内のプレースホルダを誤検出、または検出漏れ）となるため、**strict enum 検査の対象を文書系ファイル（`.claude/agents/gabriel.md`, `.claude/skills/magi/SKILL.md` 等の Markdown）に限定**する。`magi_dispatch.py` の enum 整合性は、既存または新規の **pytest**（`gabriel_output` の enum 値集合を assert する単体テスト）で別途担保する（構造化 regex とは異なる検証手段を使う設計に変更）。

**配置**: 文書系ファイル向けの検査は `verify_reference_resolution.py` の既存パターン 3 を拡張する形で行う（新規スクリプトを増やさない）。`magi_dispatch.py` 向けの enum assert は `.claude/tests/wave_c/test_wave_c_magi_integration.py`（既存）への追加、または新規テストファイルのいずれかを BUILDING で選定する。仕様変更は `docs/specs/large-scale-review/design.md` **§5.2**（W-d 反映: `verify_reference_resolution.py` 63 行目コメント「design §5.2 パターン 3」で現物確認済み。旧稿の §5.1 は誤り）に追記し、SSOT を一致させる。BUILDING 時に §5.2 の現物再確認を Done に含める。

**正例**: `.claude/agents/gabriel.md` / `.claude/skills/magi/SKILL.md` 内の `verdict: confirmed / refuted / inconclusive` のような行頭 key-value 表記。

**誤例**: enum フィールド名が単なる散文中の言及として出現するケース（例: 「confidence という語を含む説明文」のみで実際の enum 値定義を伴わない）を対象文書に意図的に投入し、strict 化後は drift として検出される（現行の substring 検査では検出されない）ことを確認する。

**grep baseline**: BUILDING 着手時に `verify_reference_resolution.py --wave all` を実行し、strict 化前後での drift 件数差分を記録する（現行は 0 drift 想定 — 対象を文書系 2 ファイルに絞った上での実測値を確認する）。

### §4.6 T7: gabriel-metrics 環境非依存化（FR-10, FR-8 / 機構なし）

**FR-10 配置裁定（Red 解決 #1 / requirements §7 二項目）**: **既存 `docs/artifacts/gabriel-metrics-environment-2026-07-05.md` §2「ログ保存位置と形式」への追記**を採用する（新規 `gabriel-metrics-schema.md` は作成しない）。

**採用理由**:
- 同ファイル §2 に JSONL スキーマ定義が既に存在し、SSOT が既に 1 箇所に集約されている
- `.claude/gabriel-metrics.log` の実測 4 entry（**起草環境ローカル実測 / 2026-07-05 ×3, 2026-07-18 ×1** — BUILDING 実施環境では entry 数が異なり得るため、以下の検証は件数非依存の設計とする）を確認した結果、既存スキーマ定義には **3 フィールドの欠落**があることを実測確認した: `subject`（string / 議題名）, `anchor`（string / 関連 anchor ファイルパス）, `hga_summon_ref`（string, nullable / HGA 召喚ログ参照。実測 4 entry 中 1 entry のみ保持）
- 新規ファイルに分裂させると、FR-10 が求める「SSOT の裏取り可能性」がかえって損なわれる（LAM 思想 = Zero-Regression Policy の「実装とドキュメントは同一の不可分な単位」に整合）

**Alternatives Considered**: 新規 `docs/artifacts/gabriel-metrics-schema.md` を作成し、既存ファイルから schema 節を移設する案。長所は「環境定義（§1, §3-§8 = 運用手順）」と「スキーマ契約（§2）」の関心を分離できる点。却下理由: 移設は既存ファイルの § 番号を崩し（T12 の表 re-numbering 規則が扱う問題と同型のリスクを文書構成レベルで持ち込む）、参照リンクの破損リスクを増やす。追記の方が変更コストが小さく（Postel's Law 的判断 = `code-quality-guideline.md` §モジュール間帰責判断フローチャートに準拠）、採用しない。

**具体的な追記内容**（§2 の JSONL スキーマ例を更新）:
- `"mode": "aot" | "lightweight"` → `"mode": "aot" | "lightweight" | "widescan_verify"`（T8 と連動 / 実測で `widescan_verify` の使用を確認済み = 起草環境ローカル実測の 2026-07-18 entry）
- スキーマ example JSON の末尾に `"subject": "...", "anchor": "docs/artifacts/...", "hga_summon_ref": "docs/artifacts/hga-summon-log.md#N" | null` を追加
- §5「実運用開始条件」チェックリストに「スキーマ文書の全フィールド網羅を実 log entry との突合で確認」項目を追加

**FR-10 受け入れ条件との対応**: 「網羅性は実 log 1 entry との突合で検証する」は本設計 §4.6 の実測（起草環境ローカルの 2026-07-18 entry = 全フィールド保持）を用いる。BUILDING 実施環境で件数・内容が異なる場合は、その時点の実 entry で再突合する。

**Done 検証（FR-8 準拠 / 検証手段 1 つ / W-f(2) 反映で出力を明示）**:
```bash
python3 -c "
import json
fields = set()
with open('.claude/gabriel-metrics.log', encoding='utf-8') as f:
    for line in f:
        fields |= json.loads(line).keys()
print(sorted(fields))
"
```
上記コマンドの出力（フィールド集合）が、更新後スキーマ文書に列挙された全フィールド名の集合に包含されることを確認する。

### §4.7 T8: mode enum 拡張（FR-7）

**設計方針**: T7（§4.6）でスキーマ文書上の `mode` enum は `"aot" | "lightweight" | "widescan_verify"` に拡張済みとする。T8 の機構部分は、この enum を実行時に検査する軽量チェックを `verify_reference_resolution.py` に **新規パターン（パターン 4: gabriel-metrics mode enum 準拠）** として追加する。

**実装方針**:
```python
# パターン 4: .claude/gabriel-metrics.log の mode フィールドが
# 許可 enum {"aot", "lightweight", "widescan_verify"} に含まれるか検査。
# ファイル不在（gitignore 対象・環境依存）の場合は skip（T7 の設計通り log 本体は commit しない）。
_GABRIEL_MODE_ENUM = {"aot", "lightweight", "widescan_verify"}
```

**正例**: 現行 `.claude/gabriel-metrics.log` 全 4 entry（起草環境ローカル実測 / `mode` = `aot` ×3, `widescan_verify` ×1）→ drift 報告に出現しない。

**誤例（Info 反映: fixture のパラメータ化）**: `mode` に enum 外の値（例: `"unknown_mode"`）を含む entry を、**実 `.claude/gabriel-metrics.log` を書き換えず** `tmp_path`（pytest fixture）に一時ファイルとして生成し、検査対象パスをそのファイルに差し替えて drift として検出されることを確認する。

**grep baseline**: BUILDING 着手時点の `.claude/gabriel-metrics.log` 実 entry 数・内容（起草環境ローカル実測: 4 件、うち enum 準拠 4 件 = drift 0 件）を記録する。ログはローカル環境依存のため、grep baseline は「本設計起草時点（2026-07-20）の L1 実測値」として記録し、BUILDING 実施環境での再実測値と併記する（件数非依存の検証設計）。

---

## §5 Wave 2 設計（文書精度）

### §5.1 terminology.md への § 追加（T9, T12, T13 / W-f(5) 反映で見出し階層を既存規約に統一）

`.claude/rules/terminology.md` の既存構成（§1〜§6 / **実測 229 行**）に対し、既存の見出し規約（`## §N 見出し名`〈h2〉+ 配下は `### 見出し名`〈h3・§記号なしの平文〉）に合わせ、**§4「命名規則」の直後に新設 `## §4.5 文書参照・表記の精度規則`（h2）** として以下 3 小節（各 `### T9: ...` 形式の h3）を追加する（§5「移行猶予条項」の前に挿入し、既存 §番号のズレを避けるため §4.5 という中間番号を用いる — これ自体が §5.1 内 T12 が扱う「表・節番号の insert 規則」の実例）。

#### `### T9: 文書内相互参照は § 見出し表記を用いる`

- 規則: 他ドキュメントの特定箇所を参照する際、行番号（`L296` 等）ではなく `§` 見出し番号または見出し名を用いる
- 根拠: `requirements.md` の行番号は編集の都度ズレる。実測（本設計起草時点 / 2026-07-20）で `docs/artifacts/r-1-final-audit-report-2026-07-15.md`（140, 182 行目）および `docs/artifacts/r-1-tracker-closure-report-2026-07-15.md`（52 行目）に `requirements.md L296` / `L283` のハードコード参照が **3 箇所現存**することを grep で確認した（詳細は §10 参照 — この事実確認は L1 依頼文の前提「残存 0 件」を上書きする訂正である。§10「grounding 訂正」節参照）
- 正例: 「`requirements.md` NFR-1 参照」
- 誤例: 「`requirements.md` L296 参照」

#### `### T12: 表・節番号の挿入規則`

- 規則: 既存の番号付き表・リストに項目を追加する際、①末尾追加（番号を延長）②中間挿入（`7b` のような補助枝番）③全体 re-numbering、のいずれを用いるかを以下の基準で選ぶ:
  - 発見順・時系列に意味がある表（例: 監査 issue 番号 R1-054〜061） → 末尾追加または枝番（re-numbering しない。既存番号への外部参照が破損するため）
  - 論理的な分類順に意味がある表（例: FR 番号） → 全体 re-numbering も許容（Wave 内で完結する場合）
- 具体例: `r-1-audit-tracker.md` の R1-059 は枝番ではなく新規連番（R1-054〜061 は時系列連番のまま維持）で追加された実例

#### `### T13: 成果物ファイル命名規則（起草日 vs 実行日）`

- 規則: 成果物ファイル名に日付を含める場合、レポート・分析文書は **起草日**、ログ・JSON 等の機械生成物は **実行日** を用いる
- 具体例: `retro-R1-2026-07-18.md`（起草日）vs `.claude/gabriel-metrics.log` の各 entry `timestamp`（実行日時）
- 現状は `evaluation-kpi.md` §9 変更履歴等で個別に説明されているのみであり、本節が terminology.md での一元化 SSOT となる

**Done 検証（FR-8 / W-f(6) 反映: 親見出しの存在も確認する）**:
```bash
grep -n "^## §4.5 文書参照・表記の精度規則" .claude/rules/terminology.md
grep -cE "^### T(9|12|13):" .claude/rules/terminology.md
```
1 つ目のコマンドで親見出しの存在、2 つ目のコマンドで 3 小節の存在（3 件ヒット）を確認する。

### §5.2 planning-quality-guideline.md への FR-13 対策 B（暗黙前提明示化リスト条項 / W-f(4) 反映で見出し記法を既存規約に統一）

**配置**: `.claude/rules/planning-quality-guideline.md` の既存見出し規約（`## N. 節タイトル`〈§ 記号を使わない番号付き h2〉）に合わせ、**§1「Requirements Smells」の直後に新設 `## 1.5 暗黙前提明示化リスト（設計書・仕様書向け）`**（既存 `## 2.` 以降の番号は変更しない — 中間番号で挿入する。§5.1 T12 規則の「中間挿入」パターンの実例でもある）。

**形式**（既存 §1「危険な単語リスト」の表形式に倣う — Red 解決 #2 / requirements §7 三項目）:

| カテゴリ | 例 | 対処 |
|:--------|:---|:-----|
| 言語標準ライブラリの癖 | `glob.glob()` は `.gitignore` を関知しない（R1-008 実例: `.claude/scripts/r1_inventory.py` は `git ls-files` との突合で対処済み） | 標準ライブラリの既知の落とし穴を設計書内に明記し、対処方針（突合・フィルタ）を併記する |
| 文字クラスの網羅性 | 「英大文字」規定が実際には小文字・underscore・多階層パスを含むケースを想定していない | 正規表現・文字クラスを設計書に書く際は、大文字/小文字/記号/パス区切りの網羅可否を明示する |
| 命名体系変更時の既存 hardcode grep | Milestone 命名が `B-N` → `R-N` に変わった際、`SessionStateParser` の fallback regex が `B` 専用のまま残存し 3 回発火した（rule-001.md 拡張の根拠事例） | 命名体系・enum に依存する設計を書く際は、変更時の既存コード grep 手順を Done 条件に含める |
| 正例だけでなく誤例 | rule/検査の「満たすべきケース」のみ記述し「違反ケース」を書かない | FR-7（本 Milestone）と同一問題への異なる層での対策。誤例を最低 1 つ設計書に含める |

**FR-13 受け入れ条件との対応**: 表最終行の説明文がそのまま「条項が FR-7 と整合している旨」の記述を兼ねる。

**Done 検証（FR-8）**: `grep -n "^## 1.5 暗黙前提明示化リスト" .claude/rules/planning-quality-guideline.md` で節の存在を確認する（§ 記号は用いない — 既存ファイルの番号付き見出し規約 `## N.` に合わせる）。

### §5.3 ADR-0008 / ADR-0004 の supersede 注記（T10）

**設計方針**: 全面的な supersede 関係ではなく、**部分的な関連（security-commands.md の allowlist 設計思想の変遷）** を相互参照として明記する（ADR-0004 は「Bash cat/grep の無制限許可を維持する」という Read-Only 特化の決定であり、ADR-0008 の D1/D4 反面教師制約とはスコープが異なるため、全面 supersede は不正確 — 現物確認済み）。

- **ADR-0004** ヘッダの「関連」行（現行 5 行目 `**関連**: `.claude/settings.json`, `.claude/rules/security-commands.md``）に `docs/adr/0008-approval-gate-redesign.md`（allowlist 設計思想の後継議論）を追記する
- **ADR-0008** メタ情報表の「関連 ADR」行（現行 9 行目 = ADR-0005/0006/0007 を列挙）に ADR-0004 を追加する

**Done 検証（FR-8）**: 両ファイルの該当行に相互参照が存在することを目視確認する。**60 秒実況（受け手= 「ADR-0004 を初めて読む後続 L1 セッション」/ 制約 = ADR-0008 の存在を知らない）**: 「Bash cat/grep 無制限許可の根拠を確認したい → ADR-0004 を開く → ヘッダの『関連』行に ADR-0008 への参照がある → 承認ゲート再設計との関係を辿れる」という経路が成立することを確認する。

### §5.4 T11: CHEATSHEET.md Rules 一覧の現状維持確認（W-a 反映 / 新設）

requirements.md Non-Goals（§1.3）+ FR-14 の通り、T11 は「完全化作業は行わない」ことが確定済みだが、FR-14 受け入れ条件が「現状維持が妥当であることの確認記録」を要求するため、W2 内で軽量に処理する。

**手順**:
1. `grep -n "抜粋\|一覧" CHEATSHEET.md` で、Rules 一覧が「抜粋」であることの明示（省略表現・「等」等の記載）が現状維持されていることを確認する
2. 確認結果（「抜粋明示が維持されている / CHEATSHEET.md 自体への変更は不要」）を Task 完了記録に 1 行残す

**Done 検証（FR-8）**: 上記 grep コマンドの実行 + 出力確認（1 コマンドで足りる）。

### §5.5 T14: "N 件相当" 表現の説明義務（純規範文書 Task / rule 化不要）

**設計方針**: requirements.md の T14 記述通り「rule 化までは不要」であり、W2 では **本設計自体の §4.6・§4.7 のような実測記述パターン**（「実測 4 件、うち◯件が△」等、集計方法を本文中に明示する）を模範として Task 完了記録に残すのみとする。専用の rule 条項は追加しない（FR-8 の検証手段 = 「W2 内の文書編集（例: §4.6・§4.7 の記述）が集計方法を明示しているかを初見読者として確認」）。

---

## §6 Wave 3 設計（個別消化 + 監査 + retro）

### §6.1 T15: evaluation-kpi.md §7 削除（FR-11 / C2 反映で grep 判定基準を精密化）

**旧手順の破棄（C2 対応）**: 初版は裸の `grep "§7\|KPI ダッシュボード" docs/ .claude/` を用いていたが、これは無関係の §7 見出し（他文書の 7 番目の節。本 design.md 自身の見出し番号を含む）に必ずヒットし、判定基準が「ヒット 0 件」を要求する限り実装がデッドロックする。

**新手順**:

1. **検索**: `grep -rnE "evaluation-kpi.*§7|KPI ダッシュボード" .`（リポジトリルートから実行 / `evaluation-kpi` という語との共起、または `KPI ダッシュボード` という固有フレーズに限定することで無関係な §7 見出しを除外する）
2. **ヒットを 2 分類する**:
   - **仕様参照**（削除条件に効く）: `docs/specs/`（`r-2-consolidation` 配下を除く。本設計・requirements.md 自身への言及は時点記録として扱う）/ `docs/internal/` / `.claude/` / `CLAUDE.md` / `CHEATSHEET.md` 内のヒット
   - **時点記録**（削除条件に効かない）: `docs/artifacts/` 内のヒット（tracker / retro / deletions 等は過去時点の記録であり、§7 削除後も「当時 §7 が存在した」という事実の記録として更新不要）
3. **削除条件**: 仕様参照が **0 件**（時点記録のヒット件数は不問）
4. **2026-07-20 L1 実測**: 上記手順で実行した結果、仕様参照 0 件・時点記録のみ（`docs/artifacts/r-1-audit-tracker.md` 等）であることを確認済み。BUILDING 着手時に同一手順で再実測し、結果が変わっていないことを確認する
5. `evaluation-kpi.md` §7（実測: 144-159 行目 / 見出し `## 7. KPI ダッシュボード` から次の `---` 区切り線の直前まで）を削除する
6. 削除後、`git diff docs/specs/evaluation-kpi.md` で §2〜§6（12-140 行目相当）が無変更であることを確認する
7. 参照が発見された場合は削除を保留し、PM 級判断に差し戻す（FR-11 contingency 条項通り）

### §6.2 T17, T22〜T25 設計方針

| Task | 方針（1-3 行） |
|:----:|:---------------|
| T17 | `.claude/agents/goal-driven-l2-foreman.md` **L7**（Info 反映: 現物確認済 / `tools: Read, Glob, Grep, Agent(goal-driven-l3-executor)`）から plain `Agent` 権限（限定 `Agent(goal-driven-l3-executor)` ではなく無制限 `Agent`）を持たせるか否かを user 判定材料として整理する。設計判断は行わず、選択肢と影響（nested spawn 可否）を提示する調査 Task |
| T22 | `/retro` skill の argument default 動作を **Claude Code 公式 docs（context7 `/websites/code_claude`）**（Info 反映: upstream-first 原則に従いローカル SKILL.md 参照ではなく公式ドキュメントを一次資料とする）で確認する調査 Task。低優先度のため設計上の分岐は不要 |
| T23 | `docs/artifacts/r-1-deletions.md` の 6 列 + commit 列を独立 field 化した template（例: YAML frontmatter または markdown 表の列固定化）を LAM 側 SSOT として `docs/artifacts/` 配下に新設する。具体列名は BUILDING で `r-1-deletions.md` の既存列を転記して確定する |
| T24 | `.claude/rules/model-delegation-prompting.md` に「scratchpad 書込禁止」を明示する新設節を追加する（配置: 既存 §2 Sonnet 委譲プロンプト必須 7 項の直後）。本文言は本タスクの委譲プロンプト自身が実例として使用した文言（「task boundaries: ... scratchpad 書込禁止」）を叩き台にする |
| T25 | `.claude/settings.json` の `permissions.allow` に built-in `/code-review ultra` 起動を阻害する項目がないか確認し、plugin 一覧（`.claude/plugins/` 相当）と突合する調査 Task。**contingency（Info 反映）**: 調査結果が `.claude/settings.json` の変更に帰着した場合、同ファイルは §3.2 表に含まれない PM 級ファイルであるため、FR-2 の追加宣言（当初宣言に含まれない新規 PM 級ファイル）が必要になる |

### §6.3 T26: pending 記録（FR-12）

`docs/artifacts/r-2-t26-pending.md`（新規・SE 級）に以下を記録する:
- Alembic 側への判断依頼内容の要約
- 応答待ちである旨
- R-2 の DoD が本項目の解決に非依存であることの明記（DoD-5 準拠）

### §6.4 最終検証

1. **G1 (FR-15)**: `bash .claude/scripts/py_invoke.sh -m pytest` 実行で 980 PASS + 15 SKIP 以上を確認（W3 終端。§3.4 で定義した Wave 末チェックと同一手順を W1/W2 に続き W3 でも実施する）
2. **R-2 変更 rule/script の整合確認**: trust-model.md / rule-002.md / subprocess-encoding-convention.md / terminology.md / planning-quality-guideline.md / model-delegation-prompting.md の相互参照リンク切れがないことを `grep` で確認
3. **Milestone retro**: `docs/artifacts/retro-R2-<date>.md` を起草し、NFR-3 の承認イベント実績（宣言イベント単位 + ダイアログ実数）を記録する（DoD-4）

---

## §7 Done 条件テンプレート

### §7.1 機構を伴う Task（T4, T5, T6, T8, T20 / FR-7 形式）

```markdown
## Done: [Task ID]

- [ ] 正例: [満たすケースの列挙 / 具体ファイル・行番号を含む]
- [ ] 誤例: [違反ケースの列挙 / 意図的に投入し検査が fail することを実測。実データ破壊を伴う場合は
      tmp_path / monkeypatch 等のロケール・環境非依存な手段を用いる]
- [ ] grep baseline: [着手前の既存違反件数] → [完了後の再計測値]
- [ ] 誤例による fail の実測ログ（コマンド + 出力の要約）
```

### §7.2 純規範文書 Task（T7, T9〜T14, T17, T22〜T25 / FR-8 形式）

```markdown
## Done: [Task ID]

- [ ] 検証手段: [実コマンド 1 つ、または「初見読者として 60 秒実況し違和感がないことを確認」]
- [ ] 検証結果: [コマンド出力の要約、または実況で拾った懸念とその対処]
```

---

## §8 Alternatives Considered

| # | 判断 | 採用案 | 却下案 | 却下理由 |
|:-:|:-----|:-------|:-------|:---------|
| 1 | FR-10 スキーマ配置 | 既存 `gabriel-metrics-environment-2026-07-05.md` への追記 | 新規 `gabriel-metrics-schema.md` | SSOT 分裂・移設コストが追記コストを上回る（§4.6 参照） |
| 2 | T6/T8 の実装場所 | `verify_reference_resolution.py` の既存パターンを拡張（文書系ファイルのみ対象） | 新規検証スクリプトを追加 / `magi_dispatch.py` にも同一 regex 検査を適用 | 検査ロジックの分散を避ける。ただし Python ソース（`magi_dispatch.py`）への構造化 regex 適用は未定義動作を招くため、pytest による enum assert に分離する（W-e） |
| 3 | T5 rule の配置 | 新規 `.claude/rules/subprocess-encoding-convention.md` | `security-commands.md` への追記 | encoding 規約はコマンド許可マトリクスと主題が異なる。`test-result-output.md` と同型の「Python コーディング規約」ファイルとして独立させる方が発見性が高い |
| 4 | T9〜T14 の配置 | `terminology.md` §4.5 として集約 | 各 Task ごとに個別ファイルを新設 | requirements.md FR-14 が明示的に「terminology.md への § 追加」を指定（T12, T13）。T9 も同系の文書精度規則であり同居が自然 |
| 5 | T20 script の突合方式 | hooks/scripts/tests の import 全数走査 vs `.venv` importability（C1） | `pyproject.toml` 宣言依存 vs `.venv` 実インストールの突合（初版） | `pyproject.toml` は dependencies 未記載が意図的設計（pip-audit スキップ）であり「宣言側」が実在しない。初版の前提誤りを HGA #16 adversarial review で検出（Critical） |
| 6 | T10 の supersede 表現 | 部分的relation（相互参照）を追記 | ADR-0004 全体を deprecated 化 | ADR-0004 は Read-Only コマンド許可という独立した決定であり、ADR-0008 に包含されない部分（cat/grep 無制限）が現役で有効なため全面 supersede は不正確 |
| 7 | T15 grep 判定基準 | 仕様参照/時点記録の 2 分類 + 仕様参照 0 件を削除条件とする（C2） | 単純な文字列 grep 0 件を削除条件とする（初版） | 裸の grep は無関係な §7 見出し（本 design.md 自身を含む）に必ずヒットし判定がデッドロックする |
| 8 | rule-002 の機構実体 | parser 世代追随 pytest 群（(a) GitHistoryParser Task ID regex / (b) 多階層参照・大文字ファイル名捕捉）（C3） | rule-002 を純規範文書 Task として FR-8 形式で済ませる | rule-002 は requirements.md FR-7 受け入れ条件で明示的に機構を伴う Task（T4）として指定されており、FR-8 への降格は仕様逸脱になる |

---

## §9 Success Criteria（DoD 5 条項への対応）

| DoD | 本設計での対応 |
|:---:|:----------------|
| DoD-1 | §4〜§6 の Wave 別設計が Green State（FR-15）維持を各 Wave 末で要求（§3.4, §6.4） |
| DoD-2 | §4.2（trust-model 2 条項）+ §4.3（rule-002）で PM 承認対象・順序を確定 |
| DoD-3 | §4.1, §4.3〜§4.7（T4〜T8）+ §7.1 Done テンプレートで FR-7/FR-8 形式の帰属を確定（T7 は FR-8+FR-10 / T4,T5,T6,T8 は FR-7） |
| DoD-4 | §6.4 手順 3 で Milestone retro に承認イベント実績記録を明記 |
| DoD-5 | §6.3 T26 pending 記録の設計で DoD-5 の明文化要件を満たす |

---

## §10 Red 解決記録（requirements §7 準拠）

requirements.md §7 の未解決質問（5 件）のうち、本設計で解決した項目と tasks.md へ送る項目を以下に区分する。

**venue 注記**: requirements.md §7 は FR-10 スキーマ配置パス・FR-13 条項形式・T9 対象文書リストの 3 項目を「tasks.md で確定」と指定していたが、design.md の起草過程で先行して解決可能と判断し、本 §10 の通り **design 段階で確定した**（tasks.md 送りとしなかった）。これは requirements.md の指定工程を早めた変更であり、tasks.md 起草時に本 §10 を SSOT として参照すること。

### 本設計で解決（3 件 / タスク冒頭の指示 (a)(b)(c) に対応）

1. **FR-10 スキーマ配置パス**: §4.6 で確定（既存 `gabriel-metrics-environment-2026-07-05.md` への追記。§8 Alternatives #1 で却下案を記録）
2. **FR-13 対策 B の条項形式**: §5.2 で確定（Requirements Smells 表形式に倣った表を `planning-quality-guideline.md` §1.5 として新設）
3. **T9 の対象文書リスト**: §5.1 で確定。**ただし grounding 訂正が必要**（下記「grounding 訂正」参照）

### tasks.md へ送る（2 件）

4. **FR-3 の Wave 間分割判断基準**: tasks.md で個別 Task の依存グラフ確定時に判断（requirements.md 記載通り、本設計は Wave 構成（§3.1）のみ確定し、Task 単位の依存グラフ化は tasks.md の役割とする）
5. **W3 個別消化の Task 順序（T17, T22〜T25）**: tasks.md で SPIDR 分割時に決定。本設計 §6.2 は各 Task の方針のみ示し、順序は確定しない

### grounding 訂正（T9 対象文書リストに関する事実確認結果）

L1 依頼文の指示 3. は「2026-07-20 L1 実測で `requirements.md L\d+` 形式の hardcoded 参照は final-audit-report / closure-report 現行版に**残存 0 件**」としていたが、これは**誤りであることを本設計の再実測で確認した**（依頼文前提の誤り / 本節で訂正済み）。再実測（`grep -nE "requirements\.md.*L[0-9]+|L[0-9]+.*requirements\.md" docs/artifacts` — BRE 非対応の `\d` ではなく `[0-9]+` を用いる）では以下 **3 箇所の残存を確認した**（ツール結果に基づく事実）:

- `docs/artifacts/r-1-final-audit-report-2026-07-15.md:140`（`requirements.md NFR-1 L296`）
- `docs/artifacts/r-1-final-audit-report-2026-07-15.md:182`（`requirements.md L283`）
- `docs/artifacts/r-1-tracker-closure-report-2026-07-15.md:52`（`requirements.md L283 準拠`）

T9 の対象文書リストは requirements.md 記述通り「final-audit-report / closure-report」の 2 ファイルで正しいが、**両ファイルとも現時点で修正未了**である。§5.1 の規則（§ 見出し参照化）は W2 で新設した上で、この 2 ファイル・3 箇所の実修正は W2 の T9 Task 内 grep baseline（着手前 3 箇所 → 完了後 0 箇所）として tasks.md に反映することを推奨する。

---

## 参照

- `docs/specs/r-2-consolidation/requirements.md`（Approved / 本設計の入力）
- `.claude/rules/auto-generated/trust-model.md` / `rule-001.md`
- `docs/artifacts/gabriel-metrics-environment-2026-07-05.md`
- `.claude/scripts/verify_reference_resolution.py`
- `.claude/scripts/magi_dispatch.py`
- `.claude/rules/terminology.md` / `planning-quality-guideline.md` / `model-delegation-prompting.md`
- `docs/artifacts/r-1-audit-tracker.md`（R1-054〜059, 061 の evidence）
- `pyproject.toml`（§4.1 C1 反映の根拠 / dependencies 未記載の pip-audit スキップ設計コメント）
