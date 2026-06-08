"""依存グラフ解析: SCC 検出 / トポロジカルソート / 循環依存検出。

Task ⑤ で card_generator.py L799-1090 から切り出し。
対応仕様: scalable-code-review-spec.md FR-7a, FR-7a-bis
対応設計: scalable-code-review-design.md Section 5.3
            docs/artifacts/audit-2026-06-01/S2b-card-generator.md L131-146
"""

from __future__ import annotations

import graphlib
import logging
from collections.abc import Callable
from dataclasses import dataclass

from analyzers.base import Issue, file_path_to_module_name

logger = logging.getLogger(__name__)


class SccDetectionSkippedError(RuntimeError):
    """SCC 検出が完遂できなかったことを示す。

    Why: 「循環なし（空 SCC）」と「検出スキップ（未知）」を戻り値で区別不能な
    構造はサイレント false negative を生む（FR-7a-bis）。本例外を伝播させて
    fail-fast にし、呼び出し側が縮退戦略を明示選択できるようにする。

    現行実装は再帰 Tarjan の RecursionError から変換していたが、反復実装後は
    通常の DFS では発生しない。将来的にメモリ不足等の失敗モードに備えて
    契約として残す。
    """


@dataclass(frozen=True)
class TopoOrderResult:
    """build_topo_order の戻り値型（FR-7a-bis）。

    Why: 元 dict 型は呼び出し側がキー名を文字列でアクセスするしかなく、
    typo や欠落キーが静的解析で検出できなかった（W: dict 型不明瞭）。
    frozen dataclass で型を明示し、不変性も保証する。
    """

    topo_order: list[str]
    sccs: list[list[str]]
    node_to_file: dict[str, str]


def _build_import_graph(
    import_map: dict[str, list[str]],
) -> tuple[dict[str, list[str]], set[str], dict[str, str]]:
    """import_map から依存グラフを構築する。

    Args:
        import_map: ファイルパス → ドット区切りモジュール名リスト の辞書。

    Returns:
        (graph, all_nodes, node_to_file) のタプル。
        graph: 隣接リスト形式の有向グラフ。
        all_nodes: グラフに含まれる全ノード名（モジュール名）。
        node_to_file: モジュール名 → ファイルパスの逆引き。
    """
    file_to_node = {fp: file_path_to_module_name(fp) for fp in import_map}
    node_to_file: dict[str, str] = {v: k for k, v in file_to_node.items()}
    all_nodes: set[str] = set(file_to_node.values())

    graph: dict[str, list[str]] = {}
    for file_path, imports in import_map.items():
        src = file_to_node[file_path]
        graph[src] = [imp for imp in imports if imp in all_nodes]

    return graph, all_nodes, node_to_file


def _find_sccs(graph: dict[str, list[str]], all_nodes: set[str]) -> list[list[str]]:
    """Tarjan のアルゴリズムで強連結成分（SCC）を検出する（反復実装）。

    サイズ2以上の SCC、または自己参照を含む SCC のみ返す。

    Raises:
        SccDetectionSkippedError: 検出処理が完遂できなかった場合（FR-7a-bis）。
            反復実装後は通常の DFS では発生しない。将来的に
            メモリ不足等の失敗モードを契約として残すための例外。

    Note: 反復スタックで DFS を駆動するため、Python の再帰上限に依存しない。
    旧再帰実装の closure 変異（index_counter = [0]）の workaround は不要。
    """
    index_counter = 0
    scc_stack: list[str] = []
    on_stack: set[str] = set()
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    sccs: list[list[str]] = []

    for start in sorted(all_nodes):
        if start in indices:
            continue

        indices[start] = index_counter
        lowlinks[start] = index_counter
        index_counter += 1
        scc_stack.append(start)
        on_stack.add(start)
        # 各フレームは (node, 隣接ノードのイテレータ)
        work_stack: list = [(start, iter(graph.get(start, [])))]

        while work_stack:
            v, neighbors = work_stack[-1]
            next_w = next(neighbors, None)
            if next_w is not None:
                if next_w not in indices:
                    # 新しい子フレームを push（再帰版の strongconnect(w) に相当）
                    indices[next_w] = index_counter
                    lowlinks[next_w] = index_counter
                    index_counter += 1
                    scc_stack.append(next_w)
                    on_stack.add(next_w)
                    work_stack.append(
                        (next_w, iter(graph.get(next_w, [])))
                    )
                elif next_w in on_stack:
                    lowlinks[v] = min(lowlinks[v], indices[next_w])
                # else: 訪問済みかつ on_stack でない（別 SCC）→ 無視
                continue

            # 全隣接ノードを処理し終えたフレームを pop（再帰版 return 相当）
            work_stack.pop()
            if lowlinks[v] == indices[v]:
                scc: list[str] = []
                while True:
                    w = scc_stack.pop()
                    on_stack.discard(w)
                    scc.append(w)
                    if w == v:
                        break
                if len(scc) > 1 or (len(scc) == 1 and v in graph.get(v, [])):
                    sccs.append(scc)
            # 親フレームに lowlink を伝搬
            if work_stack:
                parent = work_stack[-1][0]
                lowlinks[parent] = min(lowlinks[parent], lowlinks[v])

    return sccs


def detect_circular_dependencies(
    import_map: dict[str, list[str]],
) -> list[Issue]:
    """import_map からグラフを構築し、循環依存（SCC）を検出する。

    サイズ2以上の SCC（または自己参照）を Warning Issue として返す。
    返り値の空リストは「循環依存なし」のみを意味する（FR-7a-bis）。

    Raises:
        SccDetectionSkippedError: SCC 検出が完遂できなかった場合。
            呼び出し側で伝播または明示的な縮退戦略を選択する SHOULD。
    """
    graph, all_nodes, node_to_file = _build_import_graph(import_map)
    sccs = _find_sccs(graph, all_nodes)

    issues: list[Issue] = []
    for scc in sccs:
        file_paths = [node_to_file.get(n, n) for n in sorted(scc)]
        issues.append(
            Issue(
                file=file_paths[0],
                line=0,
                severity="warning",
                category="circular-dependency",
                tool="card_generator",
                message=f"Circular dependency detected: {' → '.join(file_paths)}",
                rule_id="circular-dependency",
                suggestion="Break the cycle by introducing an interface or restructuring imports",
            )
        )

    return issues


def _condense_sccs(
    graph: dict[str, list[str]],
    all_nodes: set[str],
    sccs: list[list[str]],
) -> tuple[dict[str, list[str]], dict[str, str]]:
    """SCC をスーパーノードに縮約し、縮約済みグラフと元ノードのマッピングを返す。

    Args:
        graph: ノード名 → 隣接ノード名リスト（隣接リスト）。
        all_nodes: グラフ内の全ノード名の集合。
        sccs: 縮約対象の SCC リスト（各要素はノード名リスト）。

    Returns:
        (condensed_graph, scc_map) のタプル。
        condensed_graph: SCC をスーパーノードに置き換えた縮約済みグラフ。
        scc_map: 元ノード名 → スーパーノード名のマッピング。SCC 外のノードは含まない。
    """
    # 元ノード → スーパーノード名のマッピングと、スーパーノード → メンバー逆引きを
    # 同一ループで同時構築する（iter2-Info: O(N^2) → O(N)）。
    scc_map: dict[str, str] = {}
    super_to_members: dict[str, list[str]] = {}
    for idx, scc_members in enumerate(sccs):
        super_name = f"scc_{idx}"
        super_to_members[super_name] = list(scc_members)
        for member in scc_members:
            scc_map[member] = super_name

    def _resolve(node: str) -> str:
        """ノードをスーパーノード名に解決する。SCC 外はそのまま返す。"""
        return scc_map.get(node, node)

    # SCC メンバーを除いた通常ノードを収集
    regular_nodes = all_nodes - set(scc_map.keys())

    condensed: dict[str, list[str]] = {}
    for node in regular_nodes:
        condensed[node] = _resolve_node_edges(graph, node, _resolve)
    for super_name, members in super_to_members.items():
        condensed[super_name] = _collect_supernode_edges(
            graph, members, super_name, _resolve
        )
    return condensed, scc_map


def _resolve_node_edges(
    graph: dict[str, list[str]],
    node: str,
    resolve: Callable[[str], str],
) -> list[str]:
    """通常ノードの辺をスーパーノード名に解決する。自己ループと重複を除外。"""
    edges: list[str] = []
    for neighbor in graph.get(node, []):
        resolved = resolve(neighbor)
        if resolved != node and resolved not in edges:
            edges.append(resolved)
    return edges


def _collect_supernode_edges(
    graph: dict[str, list[str]],
    members: list[str],
    super_name: str,
    resolve: Callable[[str], str],
) -> list[str]:
    """SCC メンバーの全外部辺を収集してスーパーノードの辺リストを構築する。

    SCC 内部の辺（自己ループ）は除外する。重複辺も除外する。
    """
    edges: list[str] = []
    for member in members:
        for neighbor in graph.get(member, []):
            resolved = resolve(neighbor)
            if resolved != super_name and resolved not in edges:
                edges.append(resolved)
    return edges


def build_topo_order(
    import_map: dict[str, list[str]],
) -> TopoOrderResult:
    """import_map からトポロジカル順序と SCC 情報を計算する。

    循環依存がある場合は SCC をスーパーノードに縮約してからトポロジカルソートを行う。

    Args:
        import_map: ファイルパス → ドット区切りモジュール名リスト の辞書。

    Returns:
        TopoOrderResult dataclass（frozen）。フィールド:
        - topo_order: トポロジカル順のノード名（または SCC スーパーノード名）のリスト。
        - sccs: 検出された SCC のリスト（各要素はノード名リスト）。
        - node_to_file: ノード名 → 元ファイルパスの逆引き辞書。

    Raises:
        SccDetectionSkippedError: SCC 検出が完遂できなかった場合（FR-7a-bis）。
        graphlib.CycleError: SCC 縮約後グラフは DAG であることが Tarjan アルゴリズムの
            保証なので、論理的に発生しない。仮に raise された場合は縮約ロジックの
            バグ（握り潰さず再 raise）。
    """
    graph, all_nodes, node_to_file = _build_import_graph(import_map)
    sccs = _find_sccs(graph, all_nodes)
    condensed, _scc_map = _condense_sccs(graph, all_nodes, sccs)

    sorter = graphlib.TopologicalSorter(condensed)
    topo_order = list(sorter.static_order())

    return TopoOrderResult(
        topo_order=topo_order,
        sccs=sccs,
        node_to_file=node_to_file,
    )
