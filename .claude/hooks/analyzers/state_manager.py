"""レビュー状態の永続化管理。

Task A-5: コンパクション対策 — 外部永続化
Task B-3: チャンク結果の永続化
対応仕様: scalable-code-review-spec.md FR-5, FR-6
対応設計: scalable-code-review-design.md Section 2.5, 3.7
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import logging
import re
from pathlib import Path

from analyzers.base import ASTNode, Issue
from analyzers.chunker import Chunk

logger = logging.getLogger(__name__)

_ISSUES_FILE = "static-issues.json"
_ISSUE_FIELDS = {
    f.name for f in dataclasses.fields(Issue)
}  # インポート時に一度だけ計算（軽量な副作用）
_AST_MAP_FILE = "ast-map.json"
_HASHES_FILE = "file-hashes.json"
_SUMMARY_FILE = "summary.md"
_CHUNKS_INDEX_FILE = "chunks.json"
_CHUNK_RESULTS_DIR = "chunk-results"


def _deserialize_issue(item: dict, source_path: Path) -> Issue | None:
    """辞書から Issue を復元する。不正なデータは None を返してスキップする。

    Args:
        item: JSON から読み込んだ辞書
        source_path: ログ出力用のファイルパス

    Returns:
        Issue インスタンス、またはデータが不正な場合は None
    """
    if not isinstance(item.get("file"), str):
        logger.warning("Invalid file field in issue data, skipping")
        return None

    severity = item.get("severity")
    if severity not in {"critical", "warning", "info"}:
        logger.warning(
            "Invalid severity %r in %s; falling back to 'warning'",
            severity,
            source_path,
        )
        item = {**item, "severity": "warning"}
    sanitized = {k: v for k, v in item.items() if k in _ISSUE_FIELDS}
    try:
        return Issue(**sanitized)
    except TypeError as e:
        logger.warning("Skipping malformed issue in %s: %s", source_path, e)
        return None


_CHUNK_FIELDS = {
    f.name for f in dataclasses.fields(Chunk)
}  # インポート時に一度だけ計算（軽量な副作用）


def save_issues(state_dir: Path, issues: list[Issue]) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    data = [dataclasses.asdict(issue) for issue in issues]
    (state_dir / _ISSUES_FILE).write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_issues(state_dir: Path) -> list[Issue]:
    path = state_dir / _ISSUES_FILE
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("Corrupted issues file: %s", path)
        return []
    validated = []
    for item in data:
        issue = _deserialize_issue(item, path)
        if issue is not None:
            validated.append(issue)
    return validated


def save_ast_map(state_dir: Path, ast_map: dict[str, ASTNode]) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    data = {key: dataclasses.asdict(node) for key, node in ast_map.items()}
    (state_dir / _AST_MAP_FILE).write_text(json.dumps(data, indent=2), encoding="utf-8")


def _dict_to_ast_node(d: dict) -> ASTNode:
    children = [_dict_to_ast_node(c) for c in d.get("children", [])]
    return ASTNode(
        name=d["name"],
        kind=d["kind"],
        start_line=d["start_line"],
        end_line=d["end_line"],
        signature=d["signature"],
        children=children,
        docstring=d.get("docstring"),
    )


def load_ast_map(state_dir: Path) -> dict[str, ASTNode]:
    path = state_dir / _AST_MAP_FILE
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("Corrupted ast map file: %s", path)
        return {}
    return {key: _dict_to_ast_node(node) for key, node in data.items()}


def _format_issues(issue_list: list[Issue]) -> str:
    """Issue リストを Markdown 箇条書き形式に変換する。"""
    lines = []
    for issue in issue_list:
        entry = (
            f"- [{issue.file}:{issue.line}]"
            f" ({issue.tool}/{issue.rule_id})"
            f" {issue.message}"
        )
        lines.append(entry)
    return "\n".join(lines)


def generate_summary(issues: list[Issue]) -> str:
    """NFR-4 準拠の LLM 向けサマリーを生成する。

    配置順: Critical 先頭 → レビュー指示 → 詳細 → カウント末尾
    Issue 0 件のセクションはスキップする。
    """
    criticals = [i for i in issues if i.severity == "critical"]
    warnings = [i for i in issues if i.severity == "warning"]
    infos = [i for i in issues if i.severity == "info"]

    sections: list[str] = ["# Static Analysis Summary", ""]

    # NFR-4: Critical を先頭に配置
    if criticals:
        sections.extend(["## Critical Issues", _format_issues(criticals), ""])

    # NFR-4: レビュー指示（LLM が参照する観点）
    sections.extend(
        [
            "## Review Instructions",
            "- 静的解析で検出済みの Issue は重複検出不要",
            "- セキュリティ Issue は優先的に確認すること",
            "- 全体再レビュー原則（FR-5）: 修正後もゼロベースで再監査",
            "",
        ]
    )

    if warnings:
        sections.extend(["## Warning Issues", _format_issues(warnings), ""])
    if infos:
        sections.extend(["## Info Issues", _format_issues(infos), ""])

    # NFR-4: カウントサマリーを末尾に配置
    sections.extend(
        [
            "## Summary",
            f"Critical: {len(criticals)}"
            f" / Warning: {len(warnings)}"
            f" / Info: {len(infos)}",
            "",
            "**FR-5 リマインド**: 修正後もゼロベースで全体を再監査すること。",
        ]
    )
    return "\n".join(sections)


def compute_file_hash(file_path: Path) -> str:
    """ファイルの SHA-256 ハッシュを計算する。チャンク読み込みで大ファイルにも対応。"""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def save_file_hashes(state_dir: Path, hashes: dict[str, str]) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / _HASHES_FILE).write_text(
        json.dumps(hashes, indent=2), encoding="utf-8"
    )


def load_file_hashes(state_dir: Path) -> dict[str, str]:
    path = state_dir / _HASHES_FILE
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("Corrupted hashes file: %s", path)
        return {}


def get_changed_files(state_dir: Path, current_hashes: dict[str, str]) -> list[str]:
    """前回のハッシュと現在のハッシュを比較し、変更されたファイルパスのリストを返す。"""
    previous = load_file_hashes(state_dir)
    changed = []
    for file_path, current_hash in current_hashes.items():
        if previous.get(file_path) != current_hash:
            changed.append(file_path)
    return changed


# ============================================================
# B-3: チャンク結果の永続化
# ============================================================


def chunk_result_filename(chunk: Chunk) -> str:
    """チャンクの結果ファイル名を生成する。

    設計書 Section 3.7: {path_segments}-{level}-{node_name}-{start}-{end}.json
    node_name はファイルシステム安全な文字（英数字・アンダースコア・ハイフン）のみに制限する。
    """
    path_segments = (
        chunk.file_path.replace("/", "-").replace("\\", "-").replace(".", "-")
    )
    safe_name = re.sub(r"[^\w-]", "_", chunk.node_name)
    return f"{path_segments}-{chunk.level}-{safe_name}-{chunk.start_line}-{chunk.end_line}.json"


def save_chunk_result(state_dir: Path, chunk: Chunk, issues: list[Issue]) -> None:
    """チャンクごとの Issue リストを個別ファイルで保存する。"""
    results_dir = state_dir / _CHUNK_RESULTS_DIR
    results_dir.mkdir(parents=True, exist_ok=True)

    filename = chunk_result_filename(chunk)
    data = [dataclasses.asdict(issue) for issue in issues]
    (results_dir / filename).write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_chunk_result(state_dir: Path, chunk: Chunk) -> list[Issue]:
    """チャンクの Issue リストを読み込む。"""
    results_dir = state_dir / _CHUNK_RESULTS_DIR
    filename = chunk_result_filename(chunk)
    path = results_dir / filename
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("Corrupted chunk result file: %s", path)
        return []
    validated = []
    for item in data:
        issue = _deserialize_issue(item, path)
        if issue is not None:
            validated.append(issue)
    return validated


def save_chunks_index(state_dir: Path, chunks: list[Chunk]) -> None:
    """チャンク一覧を chunks.json に保存する。"""
    state_dir.mkdir(parents=True, exist_ok=True)
    data = [dataclasses.asdict(chunk) for chunk in chunks]
    (state_dir / _CHUNKS_INDEX_FILE).write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )


def load_chunks_index(state_dir: Path) -> list[Chunk]:
    """チャンク一覧を読み込む。"""
    path = state_dir / _CHUNKS_INDEX_FILE
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("Corrupted chunks index file: %s", path)
        return []
    chunks = []
    for item in data:
        sanitized = {k: v for k, v in item.items() if k in _CHUNK_FIELDS}
        try:
            chunks.append(Chunk(**sanitized))
        except TypeError as e:
            logger.warning("Skipping malformed chunk in %s: %s", path, e)
    return chunks


# ============================================================
# D-1: 依存グラフの永続化（FR-7a）
# ============================================================

_DEPENDENCY_GRAPH_FILE = "dependency-graph.json"
_CONTRACTS_DIR = "contracts"


def _empty_dependency_graph() -> dict:
    """空の依存グラフ構造を生成する。呼び出しごとに新しいインスタンスを返す。"""
    return {"topo_order": [], "sccs": [], "node_to_file": {}}


def save_dependency_graph(state_dir: Path, graph_data: dict) -> None:
    """依存グラフをJSONファイルに永続化する。"""
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / _DEPENDENCY_GRAPH_FILE).write_text(
        json.dumps(graph_data, indent=2), encoding="utf-8"
    )


def load_dependency_graph(state_dir: Path) -> dict:
    """依存グラフを読み込む。ファイルが存在しないかパース失敗時は空の構造を返す。"""
    path = state_dir / _DEPENDENCY_GRAPH_FILE
    if not path.exists():
        return _empty_dependency_graph()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("Corrupted dependency graph file: %s", path)
        return _empty_dependency_graph()
    return {
        "topo_order": data.get("topo_order", []),
        "sccs": data.get("sccs", []),
        "node_to_file": data.get("node_to_file", {}),
    }
