"""Scalable Code Review Phase 2: AST チャンキングエンジン

Task B-1a: Chunk データモデル + トークンカウント
Task B-1b: tree-sitter 統合 + チャンク分割エンジン

対応仕様: scalable-code-review-spec.md FR-2
対応設計: scalable-code-review-design.md Section 3.0, 3.1, 3.4, 3.5
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

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


@dataclass
class _ChunkContext:
    """チャンク生成に必要な共有パラメータをまとめたコンテキスト。

    7引数関数の引数リストを削減するために使用する内部データクラス。
    """

    source_bytes: bytes
    file_path: str
    root: Any  # tree_sitter.Node
    header: str
    max_overlap_tokens: int
    chunk_size_tokens: int


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
    """関数/クラスノードからシグネチャ行（先頭行 + "..."）を抽出する。"""
    if node.type in ("function_definition", "class_definition"):
        text = _extract_node_text(source_bytes, node)
        return text.split("\n")[0] + " ..."
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


def _trim_header(header: str, max_tokens: int) -> str:
    """header が max_tokens を超える場合、行単位で先頭から切り詰める。"""
    header_lines = header.split("\n")
    trimmed: list[str] = []
    tokens_so_far = 0
    for line in header_lines:
        line_tokens = count_tokens(line)
        if tokens_so_far + line_tokens > max_tokens:
            break
        trimmed.append(line)
        tokens_so_far += line_tokens
    return "\n".join(trimmed) + "\n" if trimmed else ""


def _trim_footer(footer: str, max_tokens: int) -> str:
    """footer が max_tokens を超える場合、行単位で先頭から切り詰める。"""
    footer_lines = footer.split("\n")
    trimmed: list[str] = []
    tokens_so_far = 0
    for line in footer_lines:
        line_tokens = count_tokens(line)
        if tokens_so_far + line_tokens > max_tokens:
            break
        trimmed.append(line)
        tokens_so_far += line_tokens
    return "\n".join(trimmed) + "\n" if trimmed else ""


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
        return _trim_header(header, max_overlap_tokens), ""

    # footer を行単位で切り詰め
    return header, _trim_footer(footer, remaining)


def _process_function_node(ctx: _ChunkContext, node: tree_sitter.Node) -> Chunk:
    """トップレベル関数ノードから L1 チャンクを生成する。"""
    chunk = _make_chunk(ctx, node, "L1")
    if chunk.token_count > ctx.chunk_size_tokens:
        logger.warning(
            "Function %s is too large (%d tokens > %d)",
            chunk.node_name, chunk.token_count, ctx.chunk_size_tokens,
        )
    return chunk


def _process_class_node(ctx: _ChunkContext, node: tree_sitter.Node) -> list[Chunk]:
    """クラスノードから L2 チャンク、またはメソッド単位の L1 チャンクリストを生成する。

    クラス全体がチャンクサイズ以内なら L2 として 1 チャンク。
    超過する場合はメソッドごとに L1 チャンクに分割する。
    """
    class_text = _extract_node_text(ctx.source_bytes, node)
    class_tokens = count_tokens(class_text)

    if class_tokens <= ctx.chunk_size_tokens:
        return [_make_chunk(ctx, node, "L2")]

    # クラス定義行をメソッドの overlap_header に含める
    class_def_line = class_text.split("\n")[0]
    method_ctx = _ChunkContext(
        source_bytes=ctx.source_bytes,
        file_path=ctx.file_path,
        root=ctx.root,
        header=ctx.header + class_def_line + "\n",
        max_overlap_tokens=ctx.max_overlap_tokens,
        chunk_size_tokens=ctx.chunk_size_tokens,
    )
    chunks: list[Chunk] = []
    for child in node.children:
        if child.type == "block":
            for block_child in child.children:
                if block_child.type == "function_definition":
                    chunk = _make_chunk(method_ctx, block_child, "L1")
                    if chunk.token_count > ctx.chunk_size_tokens:
                        logger.warning(
                            "Method %s is too large (%d tokens > %d)",
                            chunk.node_name,
                            chunk.token_count,
                            ctx.chunk_size_tokens,
                        )
                    chunks.append(chunk)
    return chunks


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
        Chunk のリスト。巨大関数は Warning ログのみ出力する。
        Issue 生成は呼び出し元の責務（Phase 3 で対応予定）。

    Raises:
        TreeSitterNotAvailable: tree-sitter 未インストール時

    Note:
        Python 専用実装。多言語対応は Phase 2 以降でリファクタリング予定。
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

    ctx = _ChunkContext(
        source_bytes=source_bytes,
        file_path=file_path,
        root=root,
        header=header,
        max_overlap_tokens=max_overlap_tokens,
        chunk_size_tokens=chunk_size_tokens,
    )
    chunks: list[Chunk] = []

    for node in root.children:
        if node.type == "function_definition":
            chunks.append(_process_function_node(ctx, node))
        elif node.type == "class_definition":
            chunks.extend(_process_class_node(ctx, node))

    return chunks


def _make_chunk(ctx: _ChunkContext, node: tree_sitter.Node, level: str) -> Chunk:
    """tree-sitter Node から Chunk を生成する（のりしろ付き）。"""
    content = _extract_node_text(ctx.source_bytes, node)
    name = _get_node_name(node)
    start_line = node.start_point.row + 1
    end_line = node.end_point.row + 1

    footer = _build_footer(ctx.source_bytes, ctx.root, name)
    content_tokens = count_tokens(content)
    trimmed_header, trimmed_footer = _trim_overlap(
        ctx.header, footer, content_tokens, ctx.max_overlap_tokens,
    )

    full_text = trimmed_header + content + trimmed_footer
    token_count = count_tokens(full_text)

    return Chunk(
        file_path=ctx.file_path,
        start_line=start_line,
        end_line=end_line,
        content=content,
        overlap_header=trimmed_header,
        overlap_footer=trimmed_footer,
        token_count=token_count,
        level=level,
        node_name=name,
    )
