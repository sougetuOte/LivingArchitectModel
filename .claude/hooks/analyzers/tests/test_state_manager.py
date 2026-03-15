"""state_manager のテスト。

Task A-5: コンパクション対策 — 外部永続化
対応仕様: scalable-code-review-design.md Section 2.5
"""
from __future__ import annotations

import dataclasses
import hashlib
from pathlib import Path

import pytest

from analyzers.base import ASTNode, Issue
from analyzers.chunker import Chunk
from analyzers.state_manager import (
    chunk_result_filename,
    compute_file_hash,
    generate_summary,
    get_changed_files,
    load_ast_map,
    load_chunk_result,
    load_chunks_index,
    load_dependency_graph,
    load_file_hashes,
    load_issues,
    save_ast_map,
    save_chunk_result,
    save_chunks_index,
    save_dependency_graph,
    save_file_hashes,
    save_issues,
)


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_issues() -> list[Issue]:
    return [
        Issue(
            file="src/foo.py",
            line=10,
            severity="critical",
            category="security",
            tool="bandit",
            message="SQL injection risk",
            rule_id="B608",
            suggestion="Use parameterized queries",
        ),
        Issue(
            file="src/bar.py",
            line=20,
            severity="warning",
            category="lint",
            tool="ruff",
            message="Unused import",
            rule_id="F401",
            suggestion="Remove unused import",
        ),
        Issue(
            file="src/baz.py",
            line=5,
            severity="info",
            category="lint",
            tool="ruff",
            message="Line too long",
            rule_id="E501",
            suggestion="Wrap line",
        ),
    ]


@pytest.fixture()
def sample_ast_map() -> dict[str, ASTNode]:
    child = ASTNode(
        name="helper",
        kind="method",
        start_line=5,
        end_line=10,
        signature="def helper(self) -> None",
        children=[],
        docstring=None,
    )
    root = ASTNode(
        name="MyClass",
        kind="class",
        start_line=1,
        end_line=20,
        signature="class MyClass:",
        children=[child],
        docstring="A sample class.",
    )
    return {"src/foo.py": root}


# ---------------------------------------------------------------------------
# Issue の保存・読み込みラウンドトリップ
# ---------------------------------------------------------------------------


def test_save_and_load_issues_roundtrip(tmp_path: Path, sample_issues: list[Issue]) -> None:
    state_dir = tmp_path / "review-state"
    state_dir.mkdir()

    save_issues(state_dir, sample_issues)

    assert (state_dir / "static-issues.json").exists()

    loaded = load_issues(state_dir)

    assert loaded == sample_issues


def test_load_issues_returns_empty_when_file_missing(tmp_path: Path) -> None:
    state_dir = tmp_path / "review-state"
    state_dir.mkdir()

    result = load_issues(state_dir)

    assert result == []


# ---------------------------------------------------------------------------
# ASTNode の保存・読み込みラウンドトリップ（ネスト含む）
# ---------------------------------------------------------------------------


def test_save_and_load_ast_map_roundtrip(
    tmp_path: Path, sample_ast_map: dict[str, ASTNode]
) -> None:
    state_dir = tmp_path / "review-state"
    state_dir.mkdir()

    save_ast_map(state_dir, sample_ast_map)

    assert (state_dir / "ast-map.json").exists()

    loaded = load_ast_map(state_dir)

    assert loaded == sample_ast_map


def test_load_ast_map_returns_empty_when_file_missing(tmp_path: Path) -> None:
    state_dir = tmp_path / "review-state"
    state_dir.mkdir()

    result = load_ast_map(state_dir)

    assert result == {}


def test_ast_map_preserves_nested_children(tmp_path: Path) -> None:
    grandchild = ASTNode(
        name="inner",
        kind="function",
        start_line=3,
        end_line=5,
        signature="def inner() -> None",
        children=[],
        docstring=None,
    )
    child = ASTNode(
        name="outer",
        kind="function",
        start_line=1,
        end_line=10,
        signature="def outer() -> None",
        children=[grandchild],
        docstring="outer func",
    )
    ast_map = {"src/deep.py": child}

    state_dir = tmp_path / "review-state"
    state_dir.mkdir()
    save_ast_map(state_dir, ast_map)
    loaded = load_ast_map(state_dir)

    assert loaded["src/deep.py"].children[0] == grandchild


# ---------------------------------------------------------------------------
# summary.md フォーマット検証
# ---------------------------------------------------------------------------


def test_issue_with_invalid_severity_is_not_counted_in_summary() -> None:
    """無効な severity を持つ Issue は generate_summary() のカウントに含まれないこと。

    Issue は単純な dataclass でバリデーションを持たないため、無効値でもインスタンス化できる。
    ただし generate_summary() は critical / warning / info のみをカウント対象とするため、
    無効 severity の Issue は各カテゴリのカウントに現れないことを確認する。
    """
    valid_issue = Issue(
        file="x.py", line=1, severity="critical",
        category="lint", tool="t", message="m",
        rule_id="R1", suggestion="",
    )
    invalid_issue_unknown = Issue(
        file="y.py", line=2, severity="unknown",
        category="lint", tool="t", message="m",
        rule_id="R2", suggestion="",
    )
    invalid_issue_high = Issue(
        file="z.py", line=3, severity="high",
        category="security", tool="t", message="m",
        rule_id="R3", suggestion="",
    )
    summary = generate_summary([valid_issue, invalid_issue_unknown, invalid_issue_high])
    # Critical は valid_issue の1件のみ
    assert "Critical: 1" in summary
    # Warning / Info は 0 件
    assert "Warning: 0" in summary
    assert "Info: 0" in summary


def test_generate_summary_format(sample_issues: list[Issue]) -> None:
    result = generate_summary(sample_issues)

    # Critical が先頭のセクションとして登場する
    critical_pos = result.index("## Critical Issues")
    warning_pos = result.index("## Warning Issues")
    info_pos = result.index("## Info Issues")
    summary_pos = result.index("## Summary")

    assert critical_pos < warning_pos < info_pos < summary_pos


def test_generate_summary_count_line(sample_issues: list[Issue]) -> None:
    result = generate_summary(sample_issues)

    # Summary セクションにカウントが含まれる
    assert "Critical: 1" in result
    assert "Warning: 1" in result
    assert "Info: 1" in result


def test_generate_summary_issue_content(sample_issues: list[Issue]) -> None:
    result = generate_summary(sample_issues)

    assert "src/foo.py" in result
    assert "SQL injection risk" in result
    assert "Unused import" in result


def test_generate_summary_empty_issues() -> None:
    result = generate_summary([])

    assert "# Static Analysis Summary" in result
    assert "Critical: 0" in result
    assert "Warning: 0" in result
    assert "Info: 0" in result


# ---------------------------------------------------------------------------
# ファイルハッシュの計算・保存・読み込み
# ---------------------------------------------------------------------------


def test_compute_file_hash(tmp_path: Path) -> None:
    target = tmp_path / "sample.py"
    target.write_text("print('hello')\n")

    result = compute_file_hash(target)

    expected = hashlib.sha256(target.read_bytes()).hexdigest()
    assert result == expected


def test_save_and_load_file_hashes_roundtrip(tmp_path: Path) -> None:
    state_dir = tmp_path / "review-state"
    state_dir.mkdir()
    hashes = {"src/foo.py": "abc123", "src/bar.py": "def456"}

    save_file_hashes(state_dir, hashes)

    assert (state_dir / "file-hashes.json").exists()

    loaded = load_file_hashes(state_dir)

    assert loaded == hashes


def test_load_file_hashes_returns_empty_when_file_missing(tmp_path: Path) -> None:
    state_dir = tmp_path / "review-state"
    state_dir.mkdir()

    result = load_file_hashes(state_dir)

    assert result == {}


# ---------------------------------------------------------------------------
# 変更ファイル検出
# ---------------------------------------------------------------------------


def test_get_changed_files_detects_modified(tmp_path: Path) -> None:
    state_dir = tmp_path / "review-state"
    state_dir.mkdir()
    old_hashes = {"src/foo.py": "oldhash", "src/bar.py": "samehash"}
    save_file_hashes(state_dir, old_hashes)

    current_hashes = {"src/foo.py": "newhash", "src/bar.py": "samehash"}

    changed = get_changed_files(state_dir, current_hashes)

    assert "src/foo.py" in changed
    assert "src/bar.py" not in changed


def test_get_changed_files_detects_new_files(tmp_path: Path) -> None:
    state_dir = tmp_path / "review-state"
    state_dir.mkdir()
    old_hashes = {"src/foo.py": "hash1"}
    save_file_hashes(state_dir, old_hashes)

    current_hashes = {"src/foo.py": "hash1", "src/new.py": "hash2"}

    changed = get_changed_files(state_dir, current_hashes)

    assert "src/new.py" in changed
    assert "src/foo.py" not in changed


def test_get_changed_files_no_changes(tmp_path: Path) -> None:
    state_dir = tmp_path / "review-state"
    state_dir.mkdir()
    hashes = {"src/foo.py": "hash1", "src/bar.py": "hash2"}
    save_file_hashes(state_dir, hashes)

    changed = get_changed_files(state_dir, hashes)

    assert changed == []


def test_get_changed_files_no_previous_state(tmp_path: Path) -> None:
    state_dir = tmp_path / "review-state"
    state_dir.mkdir()

    current_hashes = {"src/foo.py": "hash1"}

    changed = get_changed_files(state_dir, current_hashes)

    assert "src/foo.py" in changed


# ---------------------------------------------------------------------------
# state_dir の自動作成
# ---------------------------------------------------------------------------


def test_save_issues_creates_state_dir_if_missing(tmp_path: Path) -> None:
    state_dir = tmp_path / "nonexistent" / "review-state"

    save_issues(state_dir, [])

    assert state_dir.exists()


def test_save_ast_map_creates_state_dir_if_missing(tmp_path: Path) -> None:
    state_dir = tmp_path / "nonexistent" / "review-state"

    save_ast_map(state_dir, {})

    assert state_dir.exists()


def test_save_file_hashes_creates_state_dir_if_missing(tmp_path: Path) -> None:
    state_dir = tmp_path / "nonexistent" / "review-state"

    save_file_hashes(state_dir, {})

    assert state_dir.exists()


# ============================================================
# B-3: チャンク結果の永続化
# ============================================================


def _make_test_chunk(name: str = "foo", level: str = "L1") -> Chunk:
    return Chunk(
        file_path="src/main.py",
        start_line=1,
        end_line=10,
        content=f"def {name}(): pass",
        overlap_header="import os\n",
        overlap_footer="",
        token_count=5,
        level=level,
        node_name=name,
    )


class TestChunkResultFilename:
    """chunk_result_filename() のテスト。"""

    def test_basic_format(self) -> None:
        chunk = _make_test_chunk("foo", "L1")
        name = chunk_result_filename(chunk)
        assert name == "src-main-py-L1-foo-1-10.json"

    def test_nested_path(self) -> None:
        chunk = dataclasses.replace(
            _make_test_chunk("bar", "L2"),
            file_path="src/hooks/analyzers/base.py",
            start_line=42,
            end_line=187,
        )
        name = chunk_result_filename(chunk)
        assert name == "src-hooks-analyzers-base-py-L2-bar-42-187.json"

    def test_l3_uses_node_name(self) -> None:
        chunk = _make_test_chunk("module", "L3")
        name = chunk_result_filename(chunk)
        assert "L3-module" in name


class TestSaveLoadChunkResult:
    """save_chunk_result / load_chunk_result のテスト。"""

    def test_roundtrip(self, tmp_path: Path) -> None:
        state_dir = tmp_path / "review-state"
        chunk = _make_test_chunk()
        issues = [
            Issue(file="src/main.py", line=5, severity="warning",
                  category="lint", tool="ruff", message="msg",
                  rule_id="E501", suggestion="fix"),
        ]
        save_chunk_result(state_dir, chunk, issues)
        loaded = load_chunk_result(state_dir, chunk)
        assert len(loaded) == 1
        assert loaded[0].file == "src/main.py"
        assert loaded[0].rule_id == "E501"

    def test_load_missing_returns_empty(self, tmp_path: Path) -> None:
        state_dir = tmp_path / "review-state"
        chunk = _make_test_chunk()
        loaded = load_chunk_result(state_dir, chunk)
        assert loaded == []

    def test_creates_chunk_results_dir(self, tmp_path: Path) -> None:
        state_dir = tmp_path / "review-state"
        chunk = _make_test_chunk()
        save_chunk_result(state_dir, chunk, [])
        assert (state_dir / "chunk-results").is_dir()

    def test_multiple_chunks(self, tmp_path: Path) -> None:
        state_dir = tmp_path / "review-state"
        c1 = _make_test_chunk("alpha", "L1")
        c2 = _make_test_chunk("beta", "L2")
        i1 = Issue(file="a.py", line=1, severity="info", category="lint",
                   tool="ruff", message="m1", rule_id="R1", suggestion="")
        i2 = Issue(file="b.py", line=2, severity="critical", category="security",
                   tool="bandit", message="m2", rule_id="B101", suggestion="")
        save_chunk_result(state_dir, c1, [i1])
        save_chunk_result(state_dir, c2, [i2])
        assert load_chunk_result(state_dir, c1)[0].rule_id == "R1"
        assert load_chunk_result(state_dir, c2)[0].rule_id == "B101"


class TestChunksIndex:
    """save_chunks_index / load_chunks_index のテスト。"""

    def test_roundtrip(self, tmp_path: Path) -> None:
        state_dir = tmp_path / "review-state"
        chunks = [_make_test_chunk("a"), _make_test_chunk("b")]
        save_chunks_index(state_dir, chunks)
        loaded = load_chunks_index(state_dir)
        assert len(loaded) == 2
        assert loaded[0].node_name == "a"
        assert loaded[1].node_name == "b"

    def test_load_missing_returns_empty(self, tmp_path: Path) -> None:
        state_dir = tmp_path / "review-state"
        loaded = load_chunks_index(state_dir)
        assert loaded == []

    def test_preserves_all_fields(self, tmp_path: Path) -> None:
        state_dir = tmp_path / "review-state"
        chunk = _make_test_chunk("foo")
        save_chunks_index(state_dir, [chunk])
        loaded = load_chunks_index(state_dir)
        assert loaded[0].file_path == "src/main.py"
        assert loaded[0].start_line == 1
        assert loaded[0].end_line == 10
        assert loaded[0].level == "L1"


# ============================================================
# D-1: 依存グラフの永続化（FR-7a）
# ============================================================


class TestDependencyGraphPersistence:
    """dependency-graph.json の永続化テスト（D-1: FR-7a）。"""

    def test_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        """保存→読込のラウンドトリップで同一データが得られること。"""
        graph_data = {
            "topo_order": ["c", "b", "a"],
            "sccs": [["a", "b"]],
            "node_to_file": {"a": "a.py", "b": "b.py", "c": "c.py"},
        }
        save_dependency_graph(tmp_path, graph_data)
        loaded = load_dependency_graph(tmp_path)
        assert loaded["topo_order"] == ["c", "b", "a"]
        assert loaded["sccs"] == [["a", "b"]]
        assert loaded["node_to_file"] == {"a": "a.py", "b": "b.py", "c": "c.py"}

    def test_load_returns_empty_when_missing(self, tmp_path: Path) -> None:
        """ファイルが存在しない場合、空の構造を返すこと。"""
        loaded = load_dependency_graph(tmp_path)
        assert loaded["topo_order"] == []
        assert loaded["sccs"] == []
        assert loaded["node_to_file"] == {}

    def test_load_handles_corrupted_file(self, tmp_path: Path) -> None:
        """壊れた JSON ファイルがあっても空の構造を返すこと。"""
        state_dir = tmp_path
        state_dir.mkdir(exist_ok=True)
        (state_dir / "dependency-graph.json").write_text("not json", encoding="utf-8")
        loaded = load_dependency_graph(tmp_path)
        assert loaded["topo_order"] == []
