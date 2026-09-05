"""derive_managed_templates.py — T1 の派生（`templates/managed/`）を正本から導出する。

## なぜ要るか

T1（`.claude/rules` / `docs/internal` / `.claude/scripts` → `plugins/*/templates/managed/`）は
2026-09-06 まで **生成器を持たず、検査だけがあった** —— つまり「同じ内容を 2 人が書き、
検査で一致を強制する」形のまま残っていた。HGA #33 が T3 について「解体せよ」と裁定した形が、
**向きが逆であるという理由だけで温存されていた**。

本スクリプトはそれを解体する。**著者は `.claude/` 側を 1 つ書き、LAM 自身がそれを読み、
利用者は導出物を読む**（入力 1・出力 2）。

## 向きと変換

**正本は `.claude/` 側**（ADR-0010 追補 2 決定 1 / 追補 3 で不変）。理由は 2 つ:

1. `.claude/rules/` 19 件のうち **5 件は配布されない**（`hga-summoning` / `model-roster` /
   `terminology` / `auto-generated/rule-001` / `auto-generated/rule-002`）。向きを反転すれば
   14 件が plugins 正本・5 件が `.claude/` 正本という **正本の分裂**が起きる
2. **PM 級ゲートが `.claude/rules/` と `docs/internal/` を指している**

変換は **prefix の付与**（`derive_managed_text` = 規則 R-A ∘ R-S / Markdown のみ）。
T3 の除去とは向きが逆だが、**どちらも同じ不変条件の帰結**である ——
**ADR-0010 追補 3: 「配布される側に bare の実行参照が残っていないこと」**。
T3 では配布側が正本、T1 では配布側が派生であるだけ。

付与が「分類」ではなく「導出」でありうるのは、規則 R-A / R-S が**全域規則**だからである
（除外は構文的に判定できる位置のみ / 置換候補 125 箇所を全数レビューして誤爆 0 を実測）。

## 使い方

    bash .claude/scripts/py_invoke.sh .claude/scripts/derive_managed_templates.py --check
    bash .claude/scripts/py_invoke.sh .claude/scripts/derive_managed_templates.py --write

## 往復恒等（**LAM 本体が壊れないことの証明**）

`--write` は書き込み前に **`逆写像(導出(x)) == x`** を全ファイルで検証する（逆写像は `.md` のみ<br>prefix 除去 = `invert_managed_text` / **`.py`・`.sh` に当ててはならない** —— そこは導出が恒等写像であり、<br>もともと名前空間つきで書かれた記述まで剥がしてしまう）。
成り立たなければ何も書かずに落ちる。

これは「付与した prefix が過不足なく剥がせる」＝ **導出が正本の情報を 1 ビットも失わない**ことを意味する。
`.claude/` 正本は 1 バイトも変わらないため、LAM 本体（plugin disabled で `.claude/` を読む）は無影響である。

## 正本を書くときの約束

`derive_project_copies.py` の同名節と同じ注意が、向きを逆にして当てはまる ——
**正本の散文に「bare 表記そのものを主題にした言及」を書かないこと。** 変換は文字列操作としては
無損失だが、意味としては損失しうる。破っても沈黙はしない（生成器が書き換え対象を列挙し、
`git diff` に派生側の変更として現れる）。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_plugin_containment import (  # noqa: E402
    _MANAGED_AREAS,
    _iter_text_files,
    _read,
    agent_names,
    component_names,
    derive_managed_text,
    invert_managed_text,
    plugin_namespace,
    skill_names,
)


def plan(repo_root: Path):
    """(派生パス, 正本テキスト, 期待テキスト, 名前空間, 全component名) のうち現在と異なるもの。"""
    pending = []
    for plugin_dir in sorted((repo_root / "plugins").glob("*/")):
        managed_root = plugin_dir / "templates" / "managed"
        if not managed_root.is_dir():
            continue
        namespace = plugin_namespace(plugin_dir)
        agents = agent_names(plugin_dir)
        skills = skill_names(plugin_dir)
        every = component_names(plugin_dir)
        for area, dev_dir in _MANAGED_AREAS.items():
            area_root = managed_root / area
            if not area_root.is_dir():
                continue
            for template in _iter_text_files(area_root):
                rel = template.relative_to(area_root)
                source = repo_root / dev_dir / rel
                if not source.is_file():
                    # 開発側に対応物が無い非対称は T1 が違反として報告する。
                    # 生成器は新規作成しない（片側だけの存在を機械的に増やさない）。
                    continue
                canonical = _read(source)
                expected = derive_managed_text(rel, canonical, namespace, agents, skills)
                if _read(template) != expected:
                    pending.append((template, rel, canonical, expected, namespace, every))
    return pending


def _round_trip_failures(pending) -> list:
    """往復恒等の検証。`逆写像(導出(x)) != x` になるファイルを返す（空なら安全）。"""
    return [
        path
        for path, rel, canonical, expected, namespace, every in pending
        if invert_managed_text(rel, expected, namespace, every) != canonical
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="派生を上書きする")
    parser.add_argument("--check", action="store_true", help="差分の有無だけを見る（既定）")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    pending = plan(repo_root)

    if not pending:
        print("OK  配布テンプレートは正本からの導出結果と一致している（更新 0 件）")
        return 0

    for path, _, _, _, _, _ in pending:
        print(f"更新対象: {path.relative_to(repo_root).as_posix()}")
    print(f"{len(pending)} ファイルが導出結果と異なる")

    if not args.write:
        print("（--write を付けると再生成する）")
        return 1

    broken = _round_trip_failures(pending)
    if broken:
        print("NG  往復恒等が破れる。何も書かずに中止する:")
        for path in broken:
            print(f"  {path.relative_to(repo_root).as_posix()}")
        return 1

    for path, _, _, expected, _, _ in pending:
        path.write_text(expected, encoding="utf-8", newline="\n")
    print(f"{len(pending)} ファイルを再生成した（往復恒等を検証済 = 正本の情報を失っていない）")
    print("**差分を git で確認してからコミットすること** —— この変換は意味を変える")
    print("（bare は短縮形ではなく、利用者環境の同名 skill を拾う別解決である）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
