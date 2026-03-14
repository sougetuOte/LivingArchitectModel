"""Scalable Code Review Phase 2: AST チャンキングエンジン

Task B-1a: Chunk データモデル + トークンカウント
Task B-1b: tree-sitter 統合 + チャンク分割エンジン

対応仕様: scalable-code-review-spec.md FR-2
対応設計: scalable-code-review-design.md Section 3.0, 3.1, 3.4, 3.5
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    import tree_sitter
    import tree_sitter_python

    _PYTHON_LANGUAGE = tree_sitter.Language(tree_sitter_python.language())
    _TREE_SITTER_AVAILABLE = True
except ImportError:
    _TREE_SITTER_AVAILABLE = False


class TreeSitterNotAvailable(Exception):
    """tree-sitter が未インストールの場合に送出される例外。"""


@dataclass
class Chunk:
    """チャンキングエンジンが生成するレビュー単位。

    設計書 Section 3.4 に対応。各チャンクはソースコードの一部
    （関数/クラス/モジュール）と、周辺コンテキストを提供する
    のりしろ（overlap）で構成される。
    """

    file_path: str          # 対象ファイルの相対パス
    start_line: int         # チャンク本体の開始行
    end_line: int           # チャンク本体の終了行
    content: str            # チャンク本体のソースコード
    overlap_header: str     # のりしろ（ファイルヘッダー: import + 定数）
    overlap_footer: str     # のりしろ（シグネチャサマリー: 同一ファイル内 + 呼び出し先）
    token_count: int        # チャンク全体（本体 + のりしろ）の推定トークン数
    level: str              # "L1" | "L2" | "L3"（チャンク粒度）
    node_name: str          # 対象のクラス名/関数名（L3 の場合はファイル名）


def count_tokens(text: str) -> int:
    """テキストの推定トークン数を返す。

    len(text.split()) でワード数を近似トークン数として使用する。
    外部トークナイザ（tiktoken 等）への依存は NFR-3 により追加しない。
    """
    return len(text.split())


_DEFAULT_CHUNK_SIZE = 3000
_DEFAULT_OVERLAP_RATIO = 0.2

# のりしろ対象のトップレベルノード種別
_HEADER_NODE_TYPES = frozenset({
    "import_statement",
    "import_from_statement",
    "expression_statement",  # 定数代入 (e.g. MAX_SIZE = 100)
})


def _extract_node_text(source_bytes: bytes, node: tree_sitter.Node) -> str:
    """tree-sitter Node からソーステキストを抽出する。"""
    return source_bytes[node.start_byte:node.end_byte].decode("utf-8")


def _get_node_name(node: tree_sitter.Node) -> str:
    """関数/クラスノードから名前を取得する。"""
    for child in node.children:
        if child.type == "identifier":
            return child.text.decode("utf-8")
    return "<anonymous>"


def _get_signature(source_bytes: bytes, node: tree_sitter.Node) -> str:
    """関数/クラスノードからシグネチャ行を抽出する。"""
    if node.type == "function_definition":
        # "def name(args) -> ret:" まで
        text = _extract_node_text(source_bytes, node)
        first_line = text.split("\n")[0]
        return first_line + " ..."
    elif node.type == "class_definition":
        text = _extract_node_text(source_bytes, node)
        first_line = text.split("\n")[0]
        return first_line + " ..."
    return ""


def _build_header(source_bytes: bytes, root: tree_sitter.Node) -> str:
    """ファイルヘッダーのりしろを構築する（import + モジュールレベル定数）。"""
    lines: list[str] = []
    for node in root.children:
        if node.type in _HEADER_NODE_TYPES:
            lines.append(_extract_node_text(source_bytes, node))
    return "\n".join(lines) + "\n" if lines else ""


def _build_footer(
    source_bytes: bytes,
    root: tree_sitter.Node,
    exclude_name: str,
) -> str:
    """シグネチャサマリーのりしろを構築する（同一ファイル内の他の関数/クラス）。"""
    sigs: list[str] = []
    for node in root.children:
        if node.type in ("function_definition", "class_definition"):
            name = _get_node_name(node)
            if name != exclude_name:
                sigs.append(_get_signature(source_bytes, node))
    return "\n".join(sigs) + "\n" if sigs else ""


def _trim_overlap(
    header: str,
    footer: str,
    content_tokens: int,
    max_overlap_tokens: int,
) -> tuple[str, str]:
    """のりしろが上限を超える場合、末尾から切り詰める。"""
    header_tokens = count_tokens(header)
    footer_tokens = count_tokens(footer)
    total_overlap = header_tokens + footer_tokens

    if total_overlap <= max_overlap_tokens:
        return header, footer

    # header を優先し、footer を切り詰める
    remaining = max(0, max_overlap_tokens - header_tokens)
    if remaining == 0:
        # header すら超過 → header も切り詰め
        header_lines = header.split("\n")
        trimmed: list[str] = []
        tokens_so_far = 0
        for line in header_lines:
            line_tokens = count_tokens(line)
            if tokens_so_far + line_tokens > max_overlap_tokens:
                break
            trimmed.append(line)
            tokens_so_far += line_tokens
        return "\n".join(trimmed) + "\n" if trimmed else "", ""

    # footer を行単位で切り詰め
    footer_lines = footer.split("\n")
    trimmed_footer: list[str] = []
    tokens_so_far = 0
    for line in footer_lines:
        line_tokens = count_tokens(line)
        if tokens_so_far + line_tokens > remaining:
            break
        trimmed_footer.append(line)
        tokens_so_far += line_tokens
    return header, "\n".join(trimmed_footer) + "\n" if trimmed_footer else ""


def chunk_file(
    source: str,
    file_path: str,
    chunk_size_tokens: int = _DEFAULT_CHUNK_SIZE,
    overlap_ratio: float = _DEFAULT_OVERLAP_RATIO,
) -> list[Chunk]:
    """Python ソースコードを構文的に妥当なチャンクに分割する。

    設計書 Section 3.5 のアルゴリズムを実装。

    Args:
        source: Python ソースコードの文字列
        file_path: チャンクに記録するファイルパス
        chunk_size_tokens: チャンクサイズ上限（トークン数）
        overlap_ratio: のりしろサイズ上限（チャンクサイズに対する比率）

    Returns:
        Chunk のリスト

    Raises:
        TreeSitterNotAvailable: tree-sitter 未インストール時
    """
    if not _TREE_SITTER_AVAILABLE:
        raise TreeSitterNotAvailable(
            "tree-sitter is not installed. "
            "Run: pip install tree-sitter tree-sitter-python"
        )

    if not source.strip():
        return []

    source_bytes = source.encode("utf-8")
    parser = tree_sitter.Parser(_PYTHON_LANGUAGE)
    tree = parser.parse(source_bytes)
    root = tree.root_node

    header = _build_header(source_bytes, root)
    max_overlap_tokens = int(chunk_size_tokens * overlap_ratio)

    chunks: list[Chunk] = []

    for node in root.children:
        if node.type == "function_definition":
            chunk = _make_chunk(
                source_bytes, node, file_path, "L1",
                root, header, max_overlap_tokens,
            )
            if chunk.token_count > chunk_size_tokens:
                logger.warning(
                    "Function %s is too large (%d tokens > %d)",
                    chunk.node_name, chunk.token_count, chunk_size_tokens,
                )
            chunks.append(chunk)

        elif node.type == "class_definition":
            class_text = _extract_node_text(source_bytes, node)
            class_tokens = count_tokens(class_text)

            if class_tokens <= chunk_size_tokens:
                chunks.append(
                    _make_chunk(
                        source_bytes, node, file_path, "L2",
                        root, header, max_overlap_tokens,
                    )
                )
            else:
                for child in node.children:
                    if child.type == "block":
                        for block_child in child.children:
                            if block_child.type == "function_definition":
                                chunk = _make_chunk(
                                    source_bytes, block_child, file_path, "L1",
                                    root, header, max_overlap_tokens,
                                )
                                if chunk.token_count > chunk_size_tokens:
                                    logger.warning(
                                        "Method %s is too large (%d tokens > %d)",
                                        chunk.node_name,
                                        chunk.token_count,
                                        chunk_size_tokens,
                                    )
                                chunks.append(chunk)

    return chunks


def _make_chunk(
    source_bytes: bytes,
    node: tree_sitter.Node,
    file_path: str,
    level: str,
    root: tree_sitter.Node,
    header: str,
    max_overlap_tokens: int,
) -> Chunk:
    """tree-sitter Node から Chunk を生成する（のりしろ付き）。"""
    content = _extract_node_text(source_bytes, node)
    name = _get_node_name(node)
    start_line = node.start_point.row + 1
    end_line = node.end_point.row + 1

    footer = _build_footer(source_bytes, root, name)
    content_tokens = count_tokens(content)
    trimmed_header, trimmed_footer = _trim_overlap(
        header, footer, content_tokens, max_overlap_tokens,
    )

    full_text = trimmed_header + content + trimmed_footer
    token_count = count_tokens(full_text)

    return Chunk(
        file_path=file_path,
        start_line=start_line,
        end_line=end_line,
        content=content,
        overlap_header=trimmed_header,
        overlap_footer=trimmed_footer,
        token_count=token_count,
        level=level,
        node_name=name,
    )
