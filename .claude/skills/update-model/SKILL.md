---
name: update-model
description: "モデル世代交代の手順（model-roster.md 更新 → ADR-0001 確認 → drift 検査 → agents 更新 → 再測定 → カタログ追記）"
version: 1.0.0
disable-model-invocation: true
---

# /update-model - モデル世代交代手順

`.claude/rules/model-roster.md` §1（層 → モデル名の束縛）を更新するときに実行する
**薄い順序表**。判断ロジック（条件分岐・閾値判定）は本 skill に実装しない。
判断が必要な箇所（ADR-0001 制約への抵触・drift の扱い等）は、既存の PM 級承認ゲート
（`.claude/rules/permission-levels.md`）に委ねる。

対応仕様: `docs/specs/m-1-opus5-migration/design.md` §8.2 / `requirements.md` FR-13, FR-14。

## ステップ1: upstream 一次資料確認

`.claude/rules/upstream-first.md` §確認手順に準拠する
（`docs/specs/m-1-opus5-migration/design.md` §4.3 と同一手順）。

1. context7 で新世代モデルの公式スペック（context window / 価格 / リリース日）を検索する
2. context7 で取得できない場合は WebFetch にフォールバックする（対話モードでのみ使用）
3. 取得した各値を一次資料の URL・取得日とともに記録する
4. 取得できなかった項目は「未確認」と明記し、断定しない

## ステップ2: `model-roster.md` §1 の表を更新

`.claude/rules/model-roster.md` §1 の表（層 → モデル名の束縛）を、ステップ1で確認した
新世代モデルの情報に基づいて更新する。モデル名を束縛してよいのは本ファイルのみ
（`model-roster.md` §0 が定める SSOT）。

## ステップ2直後: ADR-0001 制約の確認（FR-14）

`docs/adr/0001-model-routing-strategy.md` が定める「Opus は hooks/subagents で使用しない。
メインセッション専用」の制約を、ステップ2の更新後の割当が破っていないことを確認する。

```bash
grep -n "^model:" .claude/agents/*.md
```

上記の出力に `opus` が含まれないことを確認する。含まれる場合は更新内容を差し戻し、
ADR-0001 の制約と矛盾しないモデル割当へ修正した上でステップ3へ進む。

## ステップ3: `verify_model_reference` を実行

```bash
bash .claude/scripts/py_invoke.sh .claude/scripts/verify_model_reference.py
```

出力の `total_drifts` を確認する。drift が検出された場合は `drifts` 配列の
`classification`（`layer_assignment` / `design_property_description`）を確認し、
該当箇所を `model-roster.md` への参照に置き換える。

## ステップ4: `.claude/agents/*.md` frontmatter 更新

各 subagent の `model:` frontmatter を、ステップ2で更新した `model-roster.md` §1 の
割当に合わせて更新する。

## ステップ5: ベースライン再測定

`docs/specs/m-1-opus5-migration/design.md` §4.1 と同一の 6 項目・同一手順を再実行する。

```bash
bash .claude/scripts/py_invoke.sh -m pytest
```

上記コマンドの PASS/FAIL/SKIP 内訳を項目 1（pytest 全数）として記録する。
残り 5 項目（Green State 件数 / `tdd-patterns.log` FAIL→PASS 率 / gabriel verdict 分布 /
PM 級ダイアログ発火数 / `CLAUDE.md` + `rules` トークン数）は、design.md §4.1 の表が定める
個別の実測手順にそのまま従う。

## ステップ5直後: 補償条項のバッチ再監査（HGA #20 B-4 / 2026-07-26 新設）

**世代交代は、補償条項の唯一の恒久排出点である。** レジームが変わることで、
`m-1-triage-table.md` の「軸1 = モデル誤り予防」条項は**新レジームに対して未収載に戻る**。
したがってここでの再監査は「棚卸しの再開」ではなく世代交代手続の一部であり、
`hga-summon-log.md` #18 の 3 テスト（起点 / 閉集合 / 対象）を構造的に全通過する。
これを行わない場合、補償条項は現レジームの寿命を超えて残り続ける。

1. 対象を列挙する（**軸1 = モデル誤り予防**の条項のみ。ユーザー意思 veto 分と不変制約は対象外）:

```bash
grep -c "モデル誤り予防" docs/artifacts/m-1-triage-table.md
```

2. 判定材料を集める。材料は **`docs/private/fable-l3-protocol.md` §9 観測チャンネル対応表**が指す
   現レジームの発火痕（CH-1 残置 2 行 / CH-2 `tdd-patterns.log` / CH-3 `gabriel-metrics.log`）に限る。

3. **新基質の自己申告を判定材料にしない。** 「あなたは指示なしでこれをやるか」を新基質自身に問う形は
   採らない。根拠となる前例 2 件:
   - `docs/artifacts/retro-M1-2026-07-26.md` Try 1 — 予備判定が実測で **No** と確認された事例
   - 誕生ゲート台帳 `docs/artifacts/clause-gate-ledger.md` §B 取引 #2 — **YES 申告が実測ゼロのまま
     削除根拠**になり、同 #12 で更正された事例
4. 発火痕が無い条項（§9 対応表で「痕跡なし」の群）は、材料を作る / 材料なしで判定する / 据え置く
   のいずれかを選ぶ。判定に迷う条項は**世代境界の HGA 召喚**に載せる（`hga-summoning.md` 新ゲート条件 2）。
5. 判定の結果として条項を動かす場合は `/clause-gate` を通し、誕生ゲート台帳 §B に記録する。
6. **hard ceiling の再見積り**: `clause-gate-ledger.md` §A の hard ceiling 80 は
   arXiv:2607.19257 由来の借用値で、**減衰の knee はモデル族依存**（新世代の測定値ではない）。
   新世代について測定方法論が出現していれば見積りを更新し、無ければ据え置いた旨を記録する。

> 本ステップは常駐条項を増やさない（skill 本文 = R2 / 誕生ゲート予算の対象外）。

## ステップ6: 配布カタログへの追記

`docs/artifacts/m-1-distribution-catalog.md` に、本回のモデル世代交代の変更内容を
7 列（変更項目 / 種別 / LAM 固有度 / 必要 harness バージョン / 前提モデル世代 / 依存 /
判断軸）で追記する。

## 参照

- `docs/specs/m-1-opus5-migration/design.md` §8.2（本 skill の設計根拠）
- `docs/specs/m-1-opus5-migration/requirements.md` FR-13, FR-14
- `.claude/rules/model-roster.md`（§0 SSOT 宣言 / §1 更新対象の表 / §6 更新手順の概要）
- `.claude/rules/upstream-first.md`（ステップ1の根拠）
- `docs/adr/0001-model-routing-strategy.md`（ステップ2直後の確認対象）
- `.claude/scripts/verify_model_reference.py`（ステップ3が呼び出すスクリプト）
- `.claude/tests/rules/test_update_model_skill.py`（本 skill の整合検証 pytest）
- `docs/private/fable-l3-protocol.md` §9（ステップ5直後の判定材料 = 観測チャンネル対応表 / D-1 で移動 2026-08-13）
- `docs/artifacts/clause-gate-ledger.md`（ステップ5直後 5. の記録先 / §A hard ceiling）
- `docs/artifacts/hga-summon-log.md` §20（ステップ5直後の設計根拠 = 失効の検出 3 層）
