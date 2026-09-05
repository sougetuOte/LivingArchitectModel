"""derive_project_copies.py — 複製相の開発側（`.claude/`）を正本（`plugins/`）から導出する。

## なぜ要るか

LAM は skills / agents / hooks を `.claude/` と `plugins/` の**両方に実体を持つ複製相**で運用している。
これを「同じ事実を 2 人が書き、検査で一致を強制する」形のまま維持すると、
**「LAM 本体は bare 名で動く」と「配布物は名前空間つき」が定義上同時に成立しない**
（plugin 由来の agent は `subagent_type` で必ず名前空間が付き、bare 名は解決しない / 2026-09-05 実測）。

そこで複製相を「**正本 1 部 + 変換つき生成**」へ解体した（ADR-0010 追補 2 / HGA #33）。

## 向き —— 正本は `plugins/`、開発側は導出物

一般規則: **正本は、第 2 段（self-hosting = project 側撤去）の後に生き残る側に置く。**

- rules は `.claude/rules/` が正本（plugin は rules を運べない）→ `templates/managed/` が派生（T1）
- **skills / agents / hooks は `plugins/` が正本** → `.claude/` が派生（T3）

T1 と T3 の向きが逆に見えるのは正しい（同じ規則の帰結）。

根拠（HGA #33 裁定 1）: ①`lam-harness:gabriel → gabriel` は固定 prefix の除去で**無損失**だが、
逆向きは「実行指示か概念の言及か」の分類を要し、**分類は導出ではない** ②第 2 段で消えるのは
`.claude/` 側であり、**消える側を派生にすれば第 2 段が純粋な削除になる** ③staleness は
**操作者に見える側**へ置く（plugin 側が古いと利用者が踏むまで誰も気づかない）。

## 使い方

    bash .claude/scripts/py_invoke.sh .claude/scripts/derive_project_copies.py --check
    bash .claude/scripts/py_invoke.sh .claude/scripts/derive_project_copies.py --write

`--check` は差分があれば exit 1（`verify_plugin_containment.py` の T3 と同じ判定）。
`--write` は開発側を上書きする。**片側にしか無いエントリには触れない**
（開発側のみの `build-dashboard` / `clause-gate`、plugin 側のみの `init` 等）。

## 変換規則

名前空間 prefix を、**基質から導出した名前集合**（agents のファイル stem + skills のディレクトリ名）に
前置されている場合にのみ除去する。**維持リストを持たない**（機構 #7 / #11 と同型）。
実装は `verify_plugin_containment.to_project_text`（検査と生成で**同一の関数**を使う
—— 別実装にすると両者がドリフトする）。

### 正本を書くときの約束（2026-09-05 / 導入初回の `--check` が実際に検出した）

**正本の散文に「名前空間つき表記そのものを主題にした言及」を書かないこと。** 変換は文字列操作としては
無損失だが、**意味としては損失しうる** —— 導入初回に `skills/release/SKILL.md` の
「利用者環境の `/lam-harness:release` が存在しないスクリプトを呼んで落ちる」という一文が該当した
（prefix を剥がすと「利用者環境の `/release` が」となり、**利用者環境では名前空間つきである**という
主題そのものが消える）。**リテラルに依存しない言い換え**（「利用者環境の本 skill が」）に直すこと。

この約束を破っても**沈黙はしない** —— 生成器が書き換え対象ファイルを列挙し、`git diff` に derived 側の
変更として現れる。ただし**気づくのは書いた後**なので、書くときに思い出せるよう本節を置く。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_plugin_containment import (  # noqa: E402
    _iter_mirror_matches,
    _read,
    _relative_text_files,
    component_names,
    plugin_namespace,
    to_project_text,
)


def plan(repo_root: Path):
    """(開発側パス, 期待内容) のうち、**現在と異なるもの**を列挙する。"""
    pending = []
    for plugin_dir, plugin_entry, dev_entry in _iter_mirror_matches(repo_root):
        namespace = plugin_namespace(plugin_dir)
        names = component_names(plugin_dir)
        plugin_map = _relative_text_files(plugin_entry)
        dev_map = _relative_text_files(dev_entry)
        for rel, src in sorted(plugin_map.items()):
            if rel not in dev_map:
                # 複製相の非対称は T3 が違反として報告する。生成器は新規作成しない
                # （片側だけの存在は意図的な差分でありうるため、機械的に増やさない）
                continue
            expected = to_project_text(_read(src), namespace, names)
            if _read(dev_map[rel]) != expected:
                pending.append((dev_map[rel], expected))
    return pending


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="差分の有無だけを見る（書き込まない）")
    group.add_argument("--write", action="store_true", help="開発側を正本から再生成する")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    pending = plan(repo_root)

    if not pending:
        print("OK  開発側は正本からの導出結果と一致している（更新 0 件）")
        return 0

    for path, _ in pending:
        print(f"  {str(path.relative_to(repo_root)).replace(chr(92), '/')}")

    if args.check:
        print(f"NG  導出結果と異なる開発側ファイル {len(pending)} 件（--write で再生成する）")
        return 1

    for path, expected in pending:
        # 改行は開発側の既存ファイルに合わせず LF で書く（`_read` が LF 正規化して比較するため
        # CRLF で書くと比較は通るが diff が汚れる）。Git の autocrlf が最終形を決める。
        path.write_text(expected, encoding="utf-8", newline="\n")
    print(f"OK  {len(pending)} 件を正本から再生成した")
    return 0


if __name__ == "__main__":
    sys.exit(main())
