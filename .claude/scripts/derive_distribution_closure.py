"""derive_distribution_closure.py — 配布集合を「列挙」ではなく「閉包の導出」として計算する。

## なぜ要るか —— 閉包を計算したエントリポイントが hook だけだった

`verify_plugin_containment.py` の `_MIRROR_AREAS` は「開発側の analyzers / checkers / tests は
**hook の import 閉包に含まれない**」と注記していた。**その計算自体は正しかった。**
誤っていたのは入力である —— `/lam-harness:full-review` が analyzers を呼ぶことが、
閉包のエントリポイントに入っていなかった。

ADR-0010 追補 4（K4 拡張 / 2026-09-07 承認）は、これを条文にした:

    配布集合 = 閉包( エントリポイント )

    エントリポイント = 配布 hooks ∪ 配布 .md（skills / agents / managed 規範）の
                     ***フェンス内コマンド***が名指しする実体
    到達関係       = import 閉包 ∪ 実行時データ依存

**フェンスで切るのは文意判定を規則から外すため**である。読者が*実行する*ものはフェンス内、
*読む*ものはコードスパン内、という構文の線を引いた（設計 §D4）。後者は参照規則 R-P の
担当であり、**コマンド引数に R-P を当ててはならない**（URL 化すればコマンドが壊れる）。

## 何を出すか

- **エントリポイント**（由来つき）
- **閉包**（各要素が「なぜ到達可能か」の経路つき）
- **gap = 閉包 − 配布集合** —— これが PM 級の決定に諮る対象である。
  各要素について「配るか / 手順を書き換えるか / 不在時の挙動を仕様化するか」を選ぶ

## 射程の限界（**下界である**）

- フェンス内の import は `sys.path.insert(0, '<dir>')` を伴う形のみ解決する
- 実行時データ依存は**文字列リテラル**のみ。`Path(x) / y / z` の組み立ては拾わない
- 展開されるのは `.py` のみ。`.sh` の中から呼ばれる実体は辿らない
- `templates/starter/**` は射程外（利用者所有ファイル）

したがって gap は**下界**である。「これだけ配れば足りる」の証明にはならない。

## 使い方

    bash .claude/scripts/py_invoke.sh .claude/scripts/derive_distribution_closure.py
    bash .claude/scripts/py_invoke.sh .claude/scripts/derive_distribution_closure.py --out closure.json

**本スクリプトは gate ではない**（常に exit 0）。ゲート化は 4c-2 の領分である。
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# トークナイザは census と**共有する**。2 本持つと必ず片方だけ直る
# （`triage.py` を分けていたことが事故の元だった / census docstring 参照）。
import census_dangling as cd  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):  # Windows cp932 で UnicodeEncodeError を避ける
    sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
PLUGIN = REPO / "plugins" / "lam-harness"

# 配布先の写像。**`verify_plugin_containment.py` の _MANAGED_AREAS / _MIRROR_AREAS と
# 同じ対応**であり、向きが逆（dev → 配布先）である。片方を動かしたら他方も動く。
_MANAGED_MAP = (
    (".claude/rules/", "templates/managed/rules/"),
    ("docs/internal/", "templates/managed/docs-internal/"),
    (".claude/scripts/", "templates/managed/scripts/"),
)
_MIRROR_MAP = (
    (".claude/hooks/", "hooks/"),
    (".claude/skills/", "skills/"),
    (".claude/agents/", "agents/"),
)

_SYSPATH_RE = re.compile(r"sys\.path\.insert\(\s*\d+\s*,\s*['\"]([^'\"]+)['\"]\s*\)")
_FROM_IMPORT_RE = re.compile(r"^\s*from\s+([A-Za-z_][\w.]*)\s+import\b")
_IMPORT_RE = re.compile(r"^\s*import\s+([A-Za-z_][\w.]*)")
_FENCE_RE = re.compile(r"^\s*(?:```|~~~)")

_dev_files_cache: dict = {}


def _is_excluded(ref: str) -> bool:
    """census の除外規則を**再利用**する（実行時生成物 / 書込先 / 命名パターンの提示）。

    ここで新しい除外表を作らない —— 理由が同じなら規則も同じものを通す。
    """
    return any(rx.search(ref) for rx, _reason in cd._EXCLUSIONS.values())


def _dev_files(root: Path) -> set:
    """`root` 配下の実在ファイル集合（相対 posix）。**`is_file()` に判定させない**。

    NTFS は case-insensitive なので、FS へ問い合わせると `.claude/Hooks/...` が
    実在扱いになる（4c-0 (b) と同じ罠 / `permission-levels.md` 2026-09-05）。
    """
    key = str(root)
    if key not in _dev_files_cache:
        found = set()
        for p in root.rglob("*"):
            rel = p.relative_to(root)
            if cd._DEV_SKIP_DIRS & set(rel.parts):
                continue
            if p.is_file():
                found.add(rel.as_posix())
        _dev_files_cache[key] = found
    return _dev_files_cache[key]


def dist_location(dev_rel: str, plugin_dir: Path = PLUGIN, repo: Path = REPO):
    """dev tree の相対パスに対応する**配布実体**の位置。無ければ `None`。

    `None` であることが「配られていない」の定義そのものであり、gap 判定の核である。
    """
    plugin_files = _dev_files(plugin_dir)
    plugin_rel = plugin_dir.relative_to(repo).as_posix()
    candidates = []
    for src, dest in (*_MANAGED_MAP, *_MIRROR_MAP):
        if dev_rel.startswith(src):
            candidates.append(dest + dev_rel[len(src) :])
    if dev_rel.startswith(".claude/"):
        candidates.append("templates/starter/dot-claude/" + dev_rel[len(".claude/") :])
    if "/" not in dev_rel:
        candidates.append("templates/starter/" + dev_rel)
    for c in candidates:
        if c in plugin_files:
            return f"{plugin_rel}/{c}"
    return None


def _module_candidates(module: str) -> list:
    """`a.b.c` から探索すべき相対パス候補（親パッケージの `__init__.py` を含む）。"""
    parts = module.split(".")
    out = [f"{'/'.join(parts)}.py", f"{'/'.join(parts)}/__init__.py"]
    for i in range(1, len(parts)):
        out.append(f"{'/'.join(parts[:i])}/__init__.py")
    return out


def _resolve_module(module: str, search_roots, root: Path) -> set:
    """モジュール名を dev tree の相対パス集合へ解決する（見つからなければ空）。"""
    known = _dev_files(root)
    found = set()
    for base in search_roots:
        try:
            prefix = base.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            continue
        prefix = "" if prefix == "." else prefix + "/"
        for cand in _module_candidates(module):
            rel = prefix + cand
            if rel in known:
                found.add(rel)
    return found


def resolve_imports(py_path: Path, root: Path, search_roots) -> set:
    """`py_path` が import する **dev tree 内**のモジュールを返す（標準ライブラリは含まない）。

    構文エラーで例外を投げない —— **計器が沈黙するより、その 1 件を諦める方がよい**。
    """
    try:
        tree = ast.parse(py_path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return set()
    roots = [py_path.parent, *search_roots]
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found |= _resolve_module(alias.name, roots, root)
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # 相対 import は自分の位置を起点にする
                base = py_path.parent
                for _ in range(node.level - 1):
                    base = base.parent
                found |= _resolve_module(node.module or "", [base], root)
            elif node.module:
                found |= _resolve_module(node.module, roots, root)
    return found


def _div_chain_parts(node) -> list:
    """`x / "a" / "b"` 形の連結から文字列部分を左から順に返す（混ざれば空）。

    `pathlib.Path` の実務上いちばん多い書き方であり、**単一リテラルの走査では見えない**。
    """
    parts: list = []
    cur = node
    while isinstance(cur, ast.BinOp) and isinstance(cur.op, ast.Div):
        right = cur.right
        if not (isinstance(right, ast.Constant) and isinstance(right.value, str)):
            return []
        parts.append(right.value)
        cur = cur.left
    if isinstance(cur, ast.Constant) and isinstance(cur.value, str):
        parts.append(cur.value)
    return list(reversed(parts))


def runtime_data_deps(py_path: Path, root: Path) -> set:
    """`py_path` の**文字列リテラル**が名指しする、dev tree 内の非 `.py` ファイル。

    ADR-0010 追補 4 の「到達関係は import 閉包に加えて**実行時データ依存**を含む」。
    `.py` を除くのは import 閉包の担当だからであり、二重計上を避けるためである。

    **docstring は数えない。** 裸の文字列式は provenance の記述であって読み込みではない
    —— 初版はこれを数え、gap に `docs/specs/**` が 20 件以上並んだ（実体は hook の
    docstring が仕様書を参照していただけ）。4c-0 で直した `py-fixture` の偽の理由と同型。
    """
    try:
        tree = ast.parse(py_path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return set()
    docstrings = {
        id(node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    }
    known = _dev_files(root)
    found = set()

    def _take(text: str) -> None:
        for m in cd.PATH_RE.finditer(text):
            ref = m.group(0)
            if ref.endswith(".py") or cd.PLACEHOLDER.search(ref) or _is_excluded(ref):
                continue
            if ref in known:
                found.add(ref)

    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            parts = _div_chain_parts(node)
            if parts:
                _take("/".join(parts))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if id(node) not in docstrings:
                _take(node.value)
    return found


def fence_entry_points(md_path: Path, root: Path) -> dict:
    """配布 Markdown の**フェンス内コマンド**が名指しする実体（由来つき）。

    パストークンだけでは足りない —— `sys.path.insert(0, '.claude/hooks')` の直後の
    `from analyzers.chunker import ...` は、トークンとしては `.claude/hooks` という
    **ディレクトリ**にしか見えない。実体は `analyzers/chunker.py` である。
    """
    known = _dev_files(root)
    rel_doc = md_path.relative_to(root).as_posix() if md_path.is_relative_to(root) else str(md_path)
    out: dict = {}
    inside = False
    syspath_roots: list = []
    for lineno, line in enumerate(md_path.read_text(encoding="utf-8", errors="replace").split("\n"), 1):
        if _FENCE_RE.match(line):
            inside = not inside
            if inside:
                syspath_roots = []
            continue
        if not inside:
            continue
        site = f"{rel_doc}:{lineno}"
        for m in _SYSPATH_RE.finditer(line):
            syspath_roots.append(root / m.group(1))
        for m in cd.PATH_RE.finditer(line):
            ref = m.group(0)
            if cd.PLACEHOLDER.search(line[: m.start()] + ref) or _is_excluded(ref):
                continue
            if ref in known:  # ディレクトリは実体ではないので入らない
                out.setdefault(ref, []).append(site)
        if syspath_roots:
            for rx in (_FROM_IMPORT_RE, _IMPORT_RE):
                m = rx.search(line)
                if not m:
                    continue
                for ref in _resolve_module(m.group(1), syspath_roots, root):
                    out.setdefault(ref, []).append(site)
    return out


def hook_entry_points(plugin_dir: Path = PLUGIN, repo: Path = REPO) -> dict:
    """`hooks.json` が名指しする実体を dev tree 側に引き戻す（**列挙しない**）。"""
    hooks_json = plugin_dir / "hooks" / "hooks.json"
    out: dict = {}
    if not hooks_json.is_file():
        return out
    text = hooks_json.read_text(encoding="utf-8")
    plugin_files = _dev_files(plugin_dir)
    known = _dev_files(repo)
    for m in re.finditer(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w./-]+)", text):
        plugin_rel = m.group(1)
        if plugin_rel not in plugin_files:
            continue
        for src, dest in (*_MANAGED_MAP, *_MIRROR_MAP):
            if plugin_rel.startswith(dest):
                dev_rel = src + plugin_rel[len(dest) :]
                if dev_rel in known:
                    out.setdefault(dev_rel, []).append("hooks/hooks.json")
                break
    return out


def _distributed_markdown(plugin_dir: Path = PLUGIN):
    """フェンス走査の対象 = 配布 `.md`（`templates/starter/**` を除く）。"""
    for p in sorted(plugin_dir.rglob("*.md")):
        if "/templates/starter/" in f"/{p.as_posix()}":
            continue
        yield p


def entry_points(plugin_dir: Path = PLUGIN, repo: Path = REPO) -> dict:
    """エントリポイント（dev tree 相対 -> 由来の一覧）。"""
    out: dict = {k: list(v) for k, v in hook_entry_points(plugin_dir, repo).items()}
    for md in _distributed_markdown(plugin_dir):
        for ref, sites in fence_entry_points(md, repo).items():
            out.setdefault(ref, []).extend(sites)
    return {k: sorted(set(v)) for k, v in sorted(out.items())}


def closure(entries: dict, repo: Path = REPO) -> dict:
    """到達閉包（dev tree 相対 -> なぜ到達可能かの経路）。"""
    search_roots = [repo / ".claude" / "hooks", repo / ".claude" / "scripts", repo]
    reached: dict = {k: list(v) for k, v in entries.items()}
    work = list(entries)
    while work:
        cur = work.pop()
        if not cur.endswith(".py"):
            continue
        path = repo / cur
        for nxt in resolve_imports(path, repo, search_roots) | runtime_data_deps(path, repo):
            if nxt == cur:
                continue
            if nxt not in reached:
                reached[nxt] = []
                work.append(nxt)
            reached[nxt].append(f"← {cur}")
    return {k: sorted(set(v)) for k, v in sorted(reached.items())}


def gap(closed: dict, plugin_dir: Path = PLUGIN, repo: Path = REPO) -> list:
    """閉包 − 配布集合。**これが PM 級の決定に諮る対象**である。"""
    return [rel for rel in closed if dist_location(rel, plugin_dir, repo) is None]


def main() -> int:
    parser = argparse.ArgumentParser(description="配布集合を到達閉包として導出する")
    parser.add_argument("--out", help="詳細を JSON で書き出す先")
    args = parser.parse_args()

    entries = entry_points()
    closed = closure(entries)
    missing = gap(closed)

    print("=== エントリポイント（hooks.json ∪ 配布 .md のフェンス内コマンド）===")
    print(f"count={len(entries)}")
    for rel, why in entries.items():
        mark = " " if dist_location(rel) else "!"
        print(f" {mark} {rel}")
        for w in why[:3]:
            print(f"       {w}")
        if len(why) > 3:
            print(f"       … 他 {len(why) - 3} 箇所")
    print()
    print("=== 閉包（到達関係 = import 閉包 ∪ 実行時データ依存）===")
    print(f"count={len(closed)}  （うち配布済 {len(closed) - len(missing)} / 未配布 {len(missing)}）")
    print()
    print("=== gap = 閉包 − 配布集合（**PM 級の決定対象**）===")
    by_dir: dict = {}
    for rel in missing:
        by_dir.setdefault(rel.rsplit("/", 1)[0], []).append(rel)
    for d, rels in sorted(by_dir.items()):
        print(f"  {d}/  ({len(rels)} 件)")
        for rel in rels:
            why = closed[rel]
            head = why[0] if why else "?"
            print(f"    {rel.rsplit('/', 1)[1]:34} {head}")
    print()
    print("=== 配布済だが閉包の外（参考 / 減らす候補ではない）===")
    print("  ※ skills / agents / 規範そのものは閉包の入力側であり、ここには出ない設計")

    if args.out:
        out = Path(args.out)
        out.write_text(
            json.dumps(
                {"entry_points": entries, "closure": closed, "gap": missing},
                ensure_ascii=False,
                indent=1,
            ),
            encoding="utf-8",
        )
        print(f"\n詳細: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
