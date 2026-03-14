from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path

from analyzers.base import ASTNode, Issue

_ISSUES_FILE = "static-issues.json"
_AST_MAP_FILE = "ast-map.json"
_HASHES_FILE = "file-hashes.json"
_SUMMARY_FILE = "summary.md"


def save_issues(state_dir: Path, issues: list[Issue]) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    data = [dataclasses.asdict(issue) for issue in issues]
    (state_dir / _ISSUES_FILE).write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_issues(state_dir: Path) -> list[Issue]:
    path = state_dir / _ISSUES_FILE
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
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
    data = json.loads(path.read_text(encoding="utf-8"))
    return {key: _dict_to_ast_node(node) for key, node in data.items()}


def generate_summary(issues: list[Issue]) -> str:
    criticals = [i for i in issues if i.severity == "critical"]
    warnings = [i for i in issues if i.severity == "warning"]
    infos = [i for i in issues if i.severity == "info"]

    def format_issues(issue_list: list[Issue]) -> str:
        if not issue_list:
            return ""
        lines = []
        for issue in issue_list:
            lines.append(f"- [{issue.file}:{issue.line}] ({issue.tool}/{issue.rule_id}) {issue.message}")
        return "\n".join(lines)

    sections = [
        "# Static Analysis Summary",
        "",
        "## Critical Issues",
        format_issues(criticals),
        "",
        "## Warning Issues",
        format_issues(warnings),
        "",
        "## Info Issues",
        format_issues(infos),
        "",
        "## Summary",
        f"Critical: {len(criticals)} / Warning: {len(warnings)} / Info: {len(infos)}",
    ]
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
    return json.loads(path.read_text(encoding="utf-8"))


def get_changed_files(state_dir: Path, current_hashes: dict[str, str]) -> list[str]:
    previous = load_file_hashes(state_dir)
    changed = []
    for file_path, current_hash in current_hashes.items():
        if previous.get(file_path) != current_hash:
            changed.append(file_path)
    return changed
