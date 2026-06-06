"""影響範囲分析（FR-7d）と再利用判定。

Task ⑤ で card_generator.py L1093-1262 から切り出し
（collect_spec_drift_context は ModuleCard 依存のため card_generator 側に残置）。

対応仕様: scalable-code-review-spec.md FR-7d
対応設計: scalable-code-review-design.md Section 5.4
"""

from __future__ import annotations

import logging
from collections import deque

from analyzers.graph.scc import (
    _build_import_graph,
    _file_path_to_module_name,
    _find_sccs,
)

logger = logging.getLogger(__name__)


def _build_reverse_graph(
    graph: dict[str, list[str]],
    all_nodes: set[str],
) -> dict[str, list[str]]:
    """グラフの逆引きを構築する（import 方向の逆 → 依存元方向）。

    graph は A→B (A imports B) の方向なので、
    逆引きは B→A (B を import しているのは A) の方向を返す。
    """
    reverse: dict[str, list[str]] = {node: [] for node in all_nodes}
    for src, neighbors in graph.items():
        for dst in neighbors:
            if dst in reverse:
                reverse[dst].append(src)
    return reverse


def _expand_scc_members(
    initial_scope: set[str],
    sccs: list[list[str]],
    node_to_file: dict[str, str],
) -> set[str]:
    """SCC 内の1ノードが in_scope なら SCC 全体をノード名で返す。

    戻り値はノード名（モジュール名）の集合。
    """
    scc_expanded: set[str] = set(initial_scope)
    for scc in sccs:
        scc_node_names = set(scc)
        if scc_node_names & initial_scope:
            scc_expanded |= scc_node_names
    return scc_expanded


def _bfs_upstream(
    start_nodes: set[str],
    reverse_graph: dict[str, list[str]],
    sccs: list[list[str]],
    node_to_file: dict[str, str],
) -> set[str]:
    """逆引きグラフで上流方向に BFS し、到達可能なノード集合を返す。

    上流ノードが SCC に属する場合、その SCC 全体も展開する。
    Note: キューは collections.deque を使用し pop/append を O(1) で実行する（W2-4）。
    """
    visited: set[str] = set(start_nodes)
    queue: deque[str] = deque(start_nodes)
    while queue:
        current = queue.popleft()
        for upstream in reverse_graph.get(current, []):
            if upstream not in visited:
                visited.add(upstream)
                queue.append(upstream)
                expanded = _expand_scc_members({upstream}, sccs, node_to_file)
                for node in expanded - visited:
                    visited.add(node)
                    queue.append(node)
    return visited


def _partition_files_by_scope(
    import_map: dict[str, list[str]],
    visited: set[str],
    modified_files: list[str],
) -> tuple[list[str], list[str]]:
    """import_map 内のファイルを in_scope / out_of_scope に分類する。

    import_map にないが modified_files に含まれるファイルも in_scope に追加する。
    """
    file_to_node = {fp: _file_path_to_module_name(fp) for fp in import_map}
    in_scope_files: list[str] = []
    out_of_scope_files: list[str] = []

    for fp in import_map:
        node = file_to_node.get(fp)
        if node in visited:
            in_scope_files.append(fp)
        else:
            out_of_scope_files.append(fp)

    for fp in modified_files:
        if fp not in import_map and fp not in in_scope_files:
            in_scope_files.append(fp)

    return in_scope_files, out_of_scope_files


def analyze_impact(
    modified_files: list[str],
    import_map: dict[str, list[str]],
) -> dict[str, list[str]]:
    """修正ファイルから影響範囲を計算する（FR-7d）。

    依存グラフを構築し、修正ファイルから上流方向（= そのファイルを
    import しているファイル）に推移的に辿る。
    SCC 内の1ノードが修正されている場合、SCC 全体を影響範囲に含める。

    Args:
        modified_files: 修正されたファイルパスのリスト。
        import_map: ファイルパス → ドット区切りモジュール名リスト の辞書。

    Returns:
        {"in_scope": [...], "out_of_scope": [...]} の辞書。

    Raises:
        SccDetectionSkippedError: SCC 検出が完遂できなかった場合（FR-7a-bis / FR-7d 補足）。
            呼び出し側で縮退戦略（全ファイル regenerate、または fail-fast 停止）を
            明示選択する SHOULD。
    """
    graph, all_nodes, node_to_file = _build_import_graph(import_map)
    sccs = _find_sccs(graph, all_nodes)

    file_to_node = {fp: _file_path_to_module_name(fp) for fp in import_map}
    modified_nodes: set[str] = {
        file_to_node[fp] for fp in modified_files if fp in file_to_node
    }

    scope_nodes = _expand_scc_members(modified_nodes, sccs, node_to_file)
    reverse_graph = _build_reverse_graph(graph, all_nodes)
    visited = _bfs_upstream(scope_nodes, reverse_graph, sccs, node_to_file)

    in_scope_files, out_of_scope_files = _partition_files_by_scope(
        import_map, visited, modified_files
    )
    return {"in_scope": in_scope_files, "out_of_scope": out_of_scope_files}


def classify_impact_for_cards(
    in_scope: list[str],
    out_of_scope: list[str],
    current_hashes: dict[str, str],
    previous_hashes: dict[str, str],
) -> dict[str, str]:
    """影響範囲に基づいて各ファイルの概要カード再利用判定を行う（FR-7d）。

    Args:
        in_scope: 影響範囲内のファイルパスリスト。
        out_of_scope: 影響範囲外のファイルパスリスト。
        current_hashes: 現在のファイルハッシュ辞書。
        previous_hashes: 前回のファイルハッシュ辞書。

    Returns:
        {file_path: "regenerate" | "reuse_mechanical"} の辞書。
        in_scope のファイル → "regenerate"（全フィールド再生成）。
        out_of_scope かつハッシュ未変更 → "reuse_mechanical"。
        out_of_scope かつハッシュ変更あり → "regenerate"。
    """
    result: dict[str, str] = {}

    for fp in in_scope:
        result[fp] = "regenerate"

    for fp in out_of_scope:
        current = current_hashes.get(fp)
        previous = previous_hashes.get(fp)
        if current is not None and current == previous:
            result[fp] = "reuse_mechanical"
        else:
            result[fp] = "regenerate"

    return result
