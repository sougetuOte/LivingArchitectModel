from __future__ import annotations

import dataclasses
import hashlib
import json
import logging
from pathlib import Path

from analyzers.base import ASTNode, Issue
from analyzers.chunker import Chunk

logger = logging.getLogger(__name__)

_ISSUES_FILE = "static-issues.json"
_AST_MAP_FILE = "ast-map.json"
_HASHES_FILE = "file-hashes.json"
_SUMMARY_FILE = "summary.md"
_CHUNKS_INDEX_FILE = "chunks.json"
_CHUNK_RESULTS_DIR = "chunk-results"


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
    return [Issue(**item) for item in data]


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


def generate_summary(issues: list[Issue]) -> str:
    """NFR-4 準拠の LLM 向けサマリーを生成する。

    配置順: Critical 先頭 → レビュー指示 → 詳細 → カウント末尾
    Issue 0 件のセクションはスキップする。
    """
    criticals = [i for i in issues if i.severity == "critical"]
    warnings = [i for i in issues if i.severity == "warning"]
    infos = [i for i in issues if i.severity == "info"]

    def _format_issues(issue_list: list[Issue]) -> str:
        lines = []
        for issue in issue_list:
            entry = (
                f"- [{issue.file}:{issue.line}]"
                f" ({issue.tool}/{issue.rule_id})"
                f" {issue.message}"
            )
            lines.append(entry)
        return "\n".join(lines)

    sections: list[str] = ["# Static Analysis Summary", ""]

    # NFR-4: Critical を先頭に配置
    if criticals:
        sections.extend(["## Critical Issues", _format_issues(criticals), ""])

    # NFR-4: レビュー指示（LLM が参照する観点）
    sections.extend([
        "## Review Instructions",
        "- 静的解析で検出済みの Issue は重複検出不要",
        "- セキュリティ Issue は優先的に確認すること",
        "- 全体再レビュー原則（FR-5）: 修正後もゼロベースで再監査",
        "",
    ])

    if warnings:
        sections.extend(["## Warning Issues", _format_issues(warnings), ""])
    if infos:
        sections.extend(["## Info Issues", _format_issues(infos), ""])

    # NFR-4: カウントサマリーを末尾に配置
    sections.extend([
        "## Summary",
        f"Critical: {len(criticals)}"
        f" / Warning: {len(warnings)}"
        f" / Info: {len(infos)}",
    ])
    return "\n".join(sections)


def compute_file_hash(file_path: Path) -> str:
    return hashlib.sha256(file_path.read_bytes()).hexdigest()


def save_file_hashes(state_dir: Path, hashes: dict[str, str]) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / _HASHES_FILE).write_text(json.dumps(hashes, indent=2), encoding="utf-8")


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
    """
    path_segments = chunk.file_path.replace("/", "-").replace("\\", "-").replace(".", "-")
    return f"{path_segments}-{chunk.level}-{chunk.node_name}-{chunk.start_line}-{chunk.end_line}.json"


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
    return [Issue(**item) for item in data]


def save_chunks_index(state_dir: Path, chunks: list[Chunk]) -> None:
    """チャンク一覧を chunks.json に保存する。"""
    state_dir.mkdir(parents=True, exist_ok=True)
    data = [dataclasses.asdict(chunk) for chunk in chunks]
    (state_dir / _CHUNKS_INDEX_FILE).write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_chunks_index(state_dir: Path) -> list[dict]:
    """チャンク一覧を読み込む。"""
    path = state_dir / _CHUNKS_INDEX_FILE
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("Corrupted chunks index file: %s", path)
        return []
