#!/usr/bin/env python3
"""r1_cycle_detect.py — R-1 W-R1 S1 T3.

自作 AST + 自前 DFS で module 1/2/5 の Python 循環依存を検出する。
tests (module 4) は除外 (tasks.md T3 準拠)。

Usage:
    python .claude/scripts/r1_cycle_detect.py [--inventory PATH] [--output PATH]

Refs:
    docs/specs/large-scale-review/design.md §4.2
    docs/specs/large-scale-review/tasks.md T3
    docs/specs/large-scale-review/requirements.md R-G8
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Union

TARGET_MODULES: list[str] = ["1", "2", "5"]

# 標準ライブラリ / 明示除外モジュール (誤検知防止)
_STDLIB_HINTS = {
    "__future__", "os", "sys", "json", "pathlib", "datetime", "typing",
    "argparse", "ast", "glob", "re", "collections", "itertools", "functools",
    "subprocess", "logging", "io", "abc", "enum", "dataclasses",
    "unittest", "pytest", "yaml", "html", "fnmatch", "shutil", "tempfile",
    "hashlib", "base64", "urllib", "http", "email", "csv", "socket",
    "math", "time", "random", "copy", "string", "textwrap", "warnings",
    "traceback", "inspect", "types", "weakref", "gc",
}


def load_inventory(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_file_registry(inv: dict) -> dict[str, str]:
    """Import 名 → ファイルパス の逆引き辞書を構築.

    1 ファイルにつき複数のキー候補を登録する:
      - basename (stem) 例: 'builder'
      - dotted path (scripts/ or hooks/ 以下) 例: 'dashboard.builder'
      - __init__.py はディレクトリ名 (例: 'dashboard')
    """
    registry: dict[str, str] = {}
    for m in TARGET_MODULES:
        for f in inv.get(m, {}).get("python_ast", {}):
            p = Path(f)
            parts = list(p.parts)
            stem = p.stem

            candidates: list[str] = []

            if stem == "__init__":
                # __init__.py の場合は親ディレクトリ名で参照される
                if len(parts) >= 2:
                    candidates.append(parts[-2])
            else:
                candidates.append(stem)

            # dotted path: .claude/scripts/dashboard/builder.py → 'dashboard.builder'
            if ".claude" in parts:
                idx = parts.index(".claude")
                if idx + 2 < len(parts):
                    subroot = parts[idx + 1]
                    if subroot in ("scripts", "hooks"):
                        tail_parts = parts[idx + 2:]
                        if tail_parts:
                            tail_parts = list(tail_parts)
                            if tail_parts[-1].endswith(".py"):
                                tail_parts[-1] = tail_parts[-1][:-3]
                            if tail_parts[-1] == "__init__":
                                tail_parts = tail_parts[:-1]
                            if tail_parts:
                                candidates.append(".".join(tail_parts))

            for cand in candidates:
                if cand and cand not in registry:
                    registry[cand] = f
    return registry


def _resolve_relative(
    file_path: str, module: str, level: int
) -> Union[str, None]:
    """Relative import を「同ディレクトリ or 親ディレクトリ内の実ファイル」に解決."""
    base = Path(file_path).parent
    for _ in range(level - 1):
        base = base.parent

    if module:
        rel = module.replace(".", "/")
        candidates = [
            base / (rel + ".py"),
            base / rel / "__init__.py",
        ]
        for cp in candidates:
            cps = str(cp).replace("\\", "/")
            if os.path.exists(cps):
                return cps
    return None


def build_graph(inv: dict, registry: dict[str, str]) -> dict[str, set[str]]:
    """file → set(imported local files) の有向グラフを構築."""
    graph: dict[str, set[str]] = {}
    for m in TARGET_MODULES:
        for f, ast_data in inv.get(m, {}).get("python_ast", {}).items():
            if "parse_error" in ast_data:
                graph[f] = set()
                continue

            deps: set[str] = set()

            for fi in ast_data.get("from_imports", []):
                mod = fi.get("module", "")
                level = fi.get("level", 0)

                if level > 0:
                    resolved = _resolve_relative(f, mod, level)
                    if resolved is not None:
                        deps.add(resolved)
                    elif mod in registry:
                        deps.add(registry[mod])
                elif mod:
                    if mod in _STDLIB_HINTS or mod.split(".")[0] in _STDLIB_HINTS:
                        continue
                    if mod in registry:
                        deps.add(registry[mod])

            for imp in ast_data.get("imports", []):
                if imp in _STDLIB_HINTS or imp.split(".")[0] in _STDLIB_HINTS:
                    continue
                if imp in registry:
                    deps.add(registry[imp])

            # 自己参照除外
            deps.discard(f)
            graph[f] = deps
    return graph


def detect_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """3-color DFS + stack でサイクルを検出.

    Returns:
        list of cycles, each represented as a list of nodes (最後は最初と同じ).
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {n: WHITE for n in graph}
    stack: list[str] = []
    cycles: list[list[str]] = []
    seen_cycles: set[tuple[str, ...]] = set()

    sys.setrecursionlimit(max(sys.getrecursionlimit(), 5000))

    def dfs(node: str) -> None:
        color[node] = GRAY
        stack.append(node)
        for neighbor in graph.get(node, set()):
            if neighbor not in color:
                continue
            if color[neighbor] == GRAY:
                try:
                    idx = stack.index(neighbor)
                except ValueError:
                    continue
                cycle_nodes = stack[idx:]
                # 正規化: 最小要素起点で回転
                min_idx = cycle_nodes.index(min(cycle_nodes))
                rotated = cycle_nodes[min_idx:] + cycle_nodes[:min_idx]
                key = tuple(rotated)
                if key not in seen_cycles:
                    seen_cycles.add(key)
                    cycles.append(rotated + [rotated[0]])
            elif color[neighbor] == WHITE:
                dfs(neighbor)
        stack.pop()
        color[node] = BLACK

    for node in list(graph.keys()):
        if color[node] == WHITE:
            dfs(node)

    return cycles


def resolve_inventory_path(
    explicit: Union[str, None],
    today_str: str,
    artifacts_dir: str = "docs/artifacts",
) -> str:
    """--inventory 未指定時のデフォルト解決.

    1. explicit が指定されていればそのまま返す（探索なし）
    2. today 日付の inventory ファイルが存在すればそれを返す
    3. 存在しなければ artifacts_dir 内の r-1-inventory-*.json を glob し、
       ファイル名の日付（YYYY-MM-DD、辞書順 = 時系列順）が最新のものを返す
    4. 候補が 1 件もなければ、探索パターンと --inventory 指定を促す
       FileNotFoundError を送出する
    """
    if explicit:
        return explicit

    today_path = os.path.join(artifacts_dir, f"r-1-inventory-{today_str}.json")
    if os.path.exists(today_path):
        return today_path

    pattern = os.path.join(artifacts_dir, "r-1-inventory-*.json")
    candidates = glob.glob(pattern)
    if not candidates:
        raise FileNotFoundError(
            f"No R-1 inventory file found. Tried '{today_path}' and "
            f"fallback pattern '{pattern}', but no matches exist. "
            f"Specify --inventory explicitly to point at an inventory JSON."
        )

    prefix = "r-1-inventory-"

    def _inventory_date_key(path: str) -> str:
        stem = Path(path).stem
        return stem[len(prefix):] if stem.startswith(prefix) else stem

    candidates.sort(key=_inventory_date_key)
    return candidates[-1]


def main(argv: Union[list[str], None] = None) -> int:
    parser = argparse.ArgumentParser(description="R-1 W-R1 S1 T3 cycle detector")
    parser.add_argument("--inventory", default=None,
                        help="Path to inventory JSON (default: today's file, "
                             "falling back to the most recent "
                             "docs/artifacts/r-1-inventory-*.json)")
    parser.add_argument("--output", default=None,
                        help="Output JSON path (default: docs/artifacts/r-1-cycles-<today>.json)")
    args = parser.parse_args(argv)

    inv_path = resolve_inventory_path(args.inventory, date.today().isoformat())
    inv = load_inventory(inv_path)

    registry = build_file_registry(inv)
    graph = build_graph(inv, registry)
    cycles = detect_cycles(graph)

    result = {
        "generated_at": date.today().isoformat(),
        "source_inventory": inv_path,
        "target_modules": TARGET_MODULES,
        "file_count": len(graph),
        "edge_count": sum(len(v) for v in graph.values()),
        "registry_size": len(registry),
        "cycles": cycles,
        "cycle_count": len(cycles),
    }

    output_path = args.output or f"docs/artifacts/r-1-cycles-{date.today().isoformat()}.json"
    parent = os.path.dirname(output_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"file_count={result['file_count']} "
          f"edge_count={result['edge_count']} "
          f"cycle_count={result['cycle_count']}")
    if cycles:
        for c in cycles[:5]:
            print(f"  cycle: {' -> '.join(c)}")
    print(f"written: {output_path}")

    # R-G8: 循環 = 0 なら rc=0、循環あれば rc=1 (baseline 起票トリガ)
    return 0 if not cycles else 1


if __name__ == "__main__":
    sys.exit(main())
