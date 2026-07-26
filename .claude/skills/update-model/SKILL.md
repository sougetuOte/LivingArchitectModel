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
