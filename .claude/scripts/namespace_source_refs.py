"""namespace_source_refs.py — 正本（`plugins/`）の agent 名参照を名前空間つきへ変換する。

## なぜ要るか

plugin 由来の agent は `subagent_type` で **必ず名前空間つき**でしか解決しない（2026-09-05 実測）。
正本に bare 名が書かれていると、利用者環境では

- `gabriel` → `not found` で**止まる**（うるさいが安全）
- **`test-runner` → 止まらずに「組み込みの `test-runner`」が動く**（**別物が黙って実行される**）

という 2 種類の壊れ方をする。後者があるため、bare 参照は「動かない」ではなく「別物が動く」性質を持つ。

## 規則（**分類をしない** / MAGI 2 巡 + HGA #34）

判定は `verify_plugin_containment.to_namespaced_agent_text` が持つ（**検査と同一関数**）。
要約すると「agent 名は固有名詞なので**全出現を ns 化**し、除外は構文的に判定できる 3 位置のみ」——
(D) frontmatter `name:` の値 / (P) `<name>.md` のファイル名文脈 / (T) 言語タグが
`markdown` / `json` のフェンス内（= 出力テンプレート・スキーマ）。

**skills は対象外**（Action 4b）。`phase="building"` のような別名前空間の値と衝突し、
かつ slash 形は T1 チェーン 55 箇所と分裂するため、独立した設計判断を要する。

設計の全文と棄却案は `docs/artifacts/2026-09-06-magi-action4-reference-model.md`。

## 使い方

    bash .claude/scripts/py_invoke.sh .claude/scripts/namespace_source_refs.py --check
    bash .claude/scripts/py_invoke.sh .claude/scripts/namespace_source_refs.py --write

`--write` の後は `derive_project_copies.py --write` で派生を再生成すること。

## 往復恒等（**Zero-Regression の証明**）

`--write` は書き込み前に、**変換後の正本から導出される開発側テキストが、変換前から導出される
ものとバイト一致する**ことを検証する（`to_project_text` は prefix 除去なので、ns 化した分は
そのまま剥がれて元に戻る）。一致しなければ何も書かずに落ちる。

これにより「`.claude/` 側は 1 バイトも変わらない」が**テストの結果ではなく変換の性質として**
保証される —— LAM 自身は plugin disabled で `.claude/` の実体で動いているため、これが
本 codemod の Zero-Regression の中身である。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_plugin_containment import (  # noqa: E402
    _iter_text_files,
    _read,
    agent_names,
    plugin_namespace,
    to_namespaced_agent_text,
    to_project_text,
)

_AREAS = ("skills", "agents")


def plan(repo_root: Path):
    """(パス, 変換後テキスト) のうち、**現在と異なるもの**を列挙する。"""
    pending = []
    for plugin_dir in sorted((repo_root / "plugins").glob("*/")):
        namespace = plugin_namespace(plugin_dir)
        names = agent_names(plugin_dir)
        if not namespace or not names:
            continue
        for area in _AREAS:
            root = plugin_dir / area
            if not root.is_dir():
                continue
            for path in _iter_text_files(root):
                if path.suffix.lower() != ".md":
                    continue
                before = _read(path)
                after = to_namespaced_agent_text(before, namespace, names)
                if after != before:
                    pending.append((path, before, after, namespace, names))
    return pending


def _derivation_is_stable(pending) -> list:
    """往復恒等の検証。導出結果が変わってしまうファイルを返す（空なら安全）。"""
    broken = []
    for path, before, after, namespace, names in pending:
        # 導出は skills / agents 双方の名前を剥がすため、component 名の全集合を使う
        from verify_plugin_containment import component_names

        plugin_dir = path
        while plugin_dir.parent.name != "plugins":
            plugin_dir = plugin_dir.parent
        all_names = component_names(plugin_dir)
        if to_project_text(after, namespace, all_names) != to_project_text(
            before, namespace, all_names
        ):
            broken.append(path)
    return broken


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="正本を書き換える")
    parser.add_argument("--check", action="store_true", help="差分の有無だけを見る（既定）")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    pending = plan(repo_root)

    if not pending:
        print("OK  正本の agent 名参照はすべて名前空間つきである（規則 R-A）")
        return 0

    for path, _, _, _, _ in pending:
        print(f"変換対象: {path.relative_to(repo_root).as_posix()}")
    print(f"{len(pending)} ファイルに bare な agent 名参照がある")

    if not args.write:
        print("（--write を付けると書き換える）")
        return 1

    broken = _derivation_is_stable(pending)
    if broken:
        print("NG  往復恒等が破れる。何も書かずに中止する:")
        for path in broken:
            print(f"  {path.relative_to(repo_root).as_posix()}")
        return 1

    for path, _, after, _, _ in pending:
        path.write_text(after, encoding="utf-8", newline="\n")
    print(f"{len(pending)} ファイルを書き換えた（往復恒等を検証済 = 派生は 1 バイトも変わらない）")
    print("次に `derive_project_copies.py --check` で派生が無変更であることを確かめること")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
