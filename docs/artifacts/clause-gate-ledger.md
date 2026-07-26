# 誕生ゲート台帳（R1 常駐 / R3 機構 / R4 在庫）

**発効日**: 2026-07-26
**正本**: 本ファイルは **M-1 出口宣言 (c) の通貨（常駐集合建て）の正本**である（retro-M1 §出口宣言 (c) の旧通貨「規範ストック総量」を改定 / 根拠 = HGA #18 自己修正 1）
**設計**: `docs/artifacts/clause-gate-routing-design-2026-07-26.md`（v0.3）
**機械検査**: `.claude/tests/rules/test_clause_gate_ledger.py`

## 本台帳の 2 つの表の役割（混同しないこと）

| 表 | 役割 | 単位 | 検査 |
|:--|:-----|:-----|:-----|
| **§A 常駐面ベースライン** | **天井ゲージ**（hard ceiling 80 との対比 / 「同時指令数」の代理変数） | ファイル別の指令出現数 | **pytest で機械検査**（追加すれば落ちる） |
| **§B 条項取引簿** | **通貨**（no-net-growth の 1 対 1 / net-negative の 1 対 2） | 1 行 = 1 条項 | 人手（判断の記録 / 機械判定不能） |

**§A は通貨ではない。** §A は「常駐面がどれだけ混んでいるか」の観測量であり、§B は「誰が何と引き換えに入場したか」の仕訳である。**§A の指令数が動かない条項の出入りもある**（例: 箇条書き 1 行の削除は RFC 2119 キーワードを含まないため §A に現れない）。この非対称は代理変数の既知の限界であり、§B が判断の記録を担うことで補う。

---

## §A 常駐面ベースライン（2026-07-26 実測）

**R1 の定義**: ルート `CLAUDE.md` + `.claude/rules/**/*.md` のうち **`paths:` frontmatter を持たないもの**（= 無条件ロード）。

**指令カウントの定義（機械検査の対象 / 変更は PM 級）**: 各ファイル内の以下の**出現回数**（行数ではない）。

```
MUST NOT | MUST | SHOULD NOT | SHOULD | 禁止 | 必須 | してはならない
```

| # | ファイル | 指令数 |
|:-:|:---------|------:|
| 1 | `.claude/rules/fable-l3-protocol.md` | 18 |
| 2 | `.claude/rules/planning-quality-guideline.md` | 12 |
| 3 | `.claude/rules/phase-rules.md` | 12 |
| 4 | `.claude/rules/hga-summoning.md` | 9 |
| 5 | `.claude/rules/model-roster.md` | 8 |
| 6 | `.claude/rules/model-delegation-prompting.md` | 8 |
| 7 | `.claude/rules/decision-making.md` | 7 |
| 8 | `.claude/rules/code-quality-guideline.md` | 5 |
| 9 | `CLAUDE.md` | 4 |
| 10 | `.claude/rules/security-commands.md` | 4 |
| 11 | `.claude/rules/permission-levels.md` | 3 |
| 12 | `.claude/rules/upstream-first.md` | 2 |
| 13 | `.claude/rules/auto-generated/trust-model.md` | 2 |
| 14 | `.claude/rules/auto-generated/README.md` | 2 |
| 15 | `.claude/rules/core-identity.md` | 1 |
| 16 | `.claude/rules/auto-generated/rule-001.md` | 1 |
| 17 | `.claude/rules/terminology.md` | 0 |

**TOTAL: 98**

> 発効時の初回実測は **99**。§B の取引 #2（`fable-l3-protocol.md` §6.7 の削除）で **98** に更新した。
> **取引 #1（`phase-rules.md`）は §A を動かしていない** —— 削除した箇条書きが RFC 2119 キーワードを
> 含まないため。これは代理変数の既知の限界であり（本ファイル冒頭 §2 表の注記）、**実測で確認された**。

### 天井との対比

| 項目 | 値 |
|:-----|:---|
| hard ceiling（外部定数 / arXiv:2607.19257 / **物理定数ではない** = 設計 §3.3） | **80** |
| 現在値 | **98** |
| 超過 | **+18** |
| **交換レート** | **net-negative（1 行追加 = 2 行退出）** ← 設計 §3.5 が発動中 |

**発動理由**: 80 超過。80 以下に戻ったら 1 対 1 に復帰する。減少は**新規流入が起きた時だけ**起こる（定期棚卸しはしない = 出口宣言 (a)(b) と整合）。

### R2（条件ロード / 予算外 / 参考）

| ファイル | 状態 |
|:---------|:-----|
| `.claude/rules/subprocess-encoding-convention.md` | `paths:` あり = 条件ロード |
| `.claude/rules/test-result-output.md` | `paths:` あり = 条件ロード |
| `.claude/rules/auto-generated/rule-002.md` | `paths:` あり = 条件ロード |

---

## §B 条項取引簿（append-only / 1 行 = 1 条項）

**記録義務**: R1 に条項を追加する / R1 から退出させる操作は、必ず本表に 1 行を追加する。`退出先` は R2 降格 / R3 機構化 / R4 退避 / R5 削減 のいずれか。

| # | 日付 | 操作 | 条項（要約） | 出典 | 宛先 / 退出先 | 交換相手 | 根拠 |
|:-:|:-----|:-----|:-------------|:-----|:--------------|:---------|:-----|
| 1 | 2026-07-26 | **退出** | 「1 サイクル完了ごとにユーザーに報告」 | `phase-rules.md` BUILDING §必須 | **R5（削減）** | ゲート発効の初回取引 | A 型 = 基質適合テスト YES（Opus 5 は指示なしで報告する）/ 保留 ① |
| 2 | 2026-07-26 | **退出** | 「試行カウントを報告に明示」 | `fable-l3-protocol.md` §6.7 | **R5（削減）** | 同上 | 同上 |

**初回取引の注記**: ゲート自身の発効は R1 を消費しない（契機は R3 = pytest + hook / 手順本文は R2 = skill / 設計 §4.4）。したがって上記 2 件は「発効と引き換えの退出」ではなく、**保留 ① の消化を初回取引として台帳に載せたもの**である。設計 §3.2 の交換相手制約（「別途の理由で既に削除が決まっている条項を交換相手に使わない」）に照らし、**この 2 件は将来の入場の交換相手として再利用できない**（既に退出済みとして記録されるため）。

---

## §C R3 台帳（決定的機構 / 予算外 / 会計は設計 §1.1）

| # | 機構 | トリガのスキーマ出典 | 判定コマンド | 同時更新義務 |
|:-:|:-----|:---------------------|:-------------|:-------------|
| 1 | 常駐面ベースライン検査 | 本ファイル §A の表（構造化 markdown 表） | `pytest .claude/tests/rules/test_clause_gate_ledger.py` | **無**（台帳と常駐ファイルは同一 commit で動くのが正常 / 外部の漂流入力を追わない） |
| 2 | PM 級パス判定への `additionalContext` 1 本 | `pre-tool-use.py` の `tool_input.file_path`（公式スキーマ） | hook の exit 0 + JSON | **無** |

**§1.1 の禁止条項**: 「同時更新義務 = 有」の機構は R3 に置けない（`rule-002` 型の恒常税を新規に作らない）。上記 2 件はいずれも「無」。

---

## §D R4 在庫（knowledge 層 / 検出イベント 0 件で待機中 / 再入場は 1 件目の発生時）

**同一ファイルに置く理由**: ゲートを通すたびに本表が目に入るようにするため（設計 §4.3 / R4 の一方通行を防ぐ）。

| # | 条項候補 | 検出イベント | 記録日 | 出典 |
|:-:|:---------|:------------:|:-------|:-----|
| 1 | 委譲プロンプト設計における仮定タグ（F1）不在 | **1 件** | 2026-07-26 | `retro-M1-2026-07-26.md` §Try 1 |

> 注: #1 は既に検出イベント 1 件のため、設計 §2 Step 4（≥ 1 → Step 5 へ）では R1 入場の資格を持つ。ただし**入場は net-negative の 2 行退出を要する**ため、次に本件が再発した時点でゲートを通す。

---

## 権限等級

- **§A の指令カウント定義の変更**: **PM 級**（通貨の定義変更にあたる）
- §A の数値更新 / §B・§C・§D への追記: **SE 級**（機械検査が正しさを担保する）

## 参照

- `docs/artifacts/clause-gate-routing-design-2026-07-26.md`（設計 v0.3 / 判定順序 §2 / 通貨 §3）
- `docs/artifacts/hga-summon-log.md` #18（通貨改定の根拠）/ #19（設計の敵対レビュー）
- `docs/artifacts/retro-M1-2026-07-26.md` §出口宣言 (c)（旧通貨 / 本ファイルが正本を引き継ぐ）
- `.claude/skills/clause-gate/SKILL.md`（判定手順）
