"""Task B-2a: バッチ並列オーケストレーションのテスト

対応仕様: scalable-code-review-spec.md FR-2
対応設計: scalable-code-review-design.md Section 3.3, 3.6, 3.8
"""
from __future__ import annotations

from analyzers.base import Issue
from analyzers.chunker import Chunk
from analyzers.orchestrator import (
    ReviewResult,
    batch_chunks,
    build_review_prompt,
    collect_results,
    parse_llm_issues,
)


def _make_chunk(name: str, idx: int) -> Chunk:
    """テスト用の Chunk を生成するヘルパー。"""
    return Chunk(
        file_path=f"src/{name}.py",
        start_line=1,
        end_line=10,
        content=f"def {name}():\n    pass\n",
        overlap_header="import os\n",
        overlap_footer="",
        token_count=5,
        level="L1",
        node_name=name,
    )


class TestBatchChunks:
    """batch_chunks() のテスト。"""

    def test_exact_division(self) -> None:
        """チャンク数がバッチサイズで割り切れる場合。"""
        chunks = [_make_chunk(f"f{i}", i) for i in range(8)]
        batches = batch_chunks(chunks, batch_size=4)
        assert len(batches) == 2
        assert len(batches[0]) == 4
        assert len(batches[1]) == 4

    def test_remainder(self) -> None:
        """チャンク数がバッチサイズで割り切れない場合。"""
        chunks = [_make_chunk(f"f{i}", i) for i in range(10)]
        batches = batch_chunks(chunks, batch_size=4)
        assert len(batches) == 3
        assert len(batches[0]) == 4
        assert len(batches[1]) == 4
        assert len(batches[2]) == 2

    def test_single_chunk(self) -> None:
        """チャンク 1 つ → バッチ 1 つ。"""
        chunks = [_make_chunk("single", 0)]
        batches = batch_chunks(chunks, batch_size=4)
        assert len(batches) == 1
        assert len(batches[0]) == 1

    def test_empty_chunks(self) -> None:
        """空リスト → 空リスト。"""
        batches = batch_chunks([], batch_size=4)
        assert batches == []

    def test_batch_size_larger_than_chunks(self) -> None:
        """バッチサイズがチャンク数より大きい場合 → バッチ 1 つ。"""
        chunks = [_make_chunk(f"f{i}", i) for i in range(3)]
        batches = batch_chunks(chunks, batch_size=10)
        assert len(batches) == 1
        assert len(batches[0]) == 3

    def test_preserves_order(self) -> None:
        """チャンクの順序が保持されること。"""
        chunks = [_make_chunk(f"f{i}", i) for i in range(7)]
        batches = batch_chunks(chunks, batch_size=3)
        flattened = [c for batch in batches for c in batch]
        assert [c.node_name for c in flattened] == [c.node_name for c in chunks]

    def test_50_chunks_4_parallel(self) -> None:
        """設計書 Section 3.8: 50 チャンク × 4 並列 → 13 バッチ。"""
        chunks = [_make_chunk(f"f{i}", i) for i in range(50)]
        batches = batch_chunks(chunks, batch_size=4)
        assert len(batches) == 13
        # 最後のバッチは 2 チャンク
        assert len(batches[-1]) == 2


class TestBuildReviewPrompt:
    """build_review_prompt() のテスト。"""

    def test_contains_file_path(self) -> None:
        """プロンプトにファイルパスが含まれること。"""
        chunk = _make_chunk("greet", 0)
        prompt = build_review_prompt(chunk)
        assert "src/greet.py" in prompt

    def test_contains_content(self) -> None:
        """プロンプトにチャンク内容が含まれること。"""
        chunk = _make_chunk("greet", 0)
        prompt = build_review_prompt(chunk)
        assert "def greet" in prompt

    def test_contains_overlap_header(self) -> None:
        """プロンプトにのりしろヘッダーが含まれること。"""
        chunk = _make_chunk("greet", 0)
        prompt = build_review_prompt(chunk)
        assert "import os" in prompt

    def test_contains_review_instruction(self) -> None:
        """プロンプトにレビュー指示が含まれること。"""
        chunk = _make_chunk("greet", 0)
        prompt = build_review_prompt(chunk)
        # レビュー指示のキーワードが含まれること
        assert "review" in prompt.lower() or "レビュー" in prompt


class TestCollectResults:
    """collect_results() のテスト。"""

    def test_collect_success(self) -> None:
        """成功した結果を収集できること。"""
        issue1 = Issue(
            file="a.py", line=1, severity="warning", category="lint",
            tool="test", message="issue1", rule_id="T001", suggestion="",
        )
        issue2 = Issue(
            file="b.py", line=2, severity="info", category="review",
            tool="llm", message="issue2", rule_id="", suggestion="",
        )
        results = [
            ReviewResult(chunk_name="f0", file_path="a.py", issues=[issue1], success=True),
            ReviewResult(chunk_name="f1", file_path="b.py", issues=[issue2], success=True),
        ]
        batch_result = collect_results(results)
        assert batch_result.total == 2
        assert batch_result.succeeded == 2
        assert batch_result.failed == 0
        assert len(batch_result.all_issues) == 2

    def test_collect_with_failures(self) -> None:
        """失敗を含む結果の収集。"""
        issue1 = Issue(
            file="a.py", line=1, severity="warning", category="lint",
            tool="test", message="issue1", rule_id="T001", suggestion="",
        )
        results = [
            ReviewResult(chunk_name="f0", file_path="a.py", issues=[issue1], success=True),
            ReviewResult(chunk_name="f1", file_path="b.py", issues=[], success=False, error="timeout"),
        ]
        batch_result = collect_results(results)
        assert batch_result.total == 2
        assert batch_result.succeeded == 1
        assert batch_result.failed == 1
        assert len(batch_result.failed_chunks) == 1
        assert batch_result.failed_chunks[0] == "f1"

    def test_collect_empty(self) -> None:
        """空リスト → 空の BatchResult。"""
        batch_result = collect_results([])
        assert batch_result.total == 0
        assert batch_result.succeeded == 0
        assert batch_result.all_issues == []

    def test_collect_aggregates_issues(self) -> None:
        """全チャンクの Issue が統合されること。"""
        issue1 = Issue(
            file="a.py", line=1, severity="warning", category="lint",
            tool="test", message="i1", rule_id="T001", suggestion="",
        )
        issue2 = Issue(
            file="a.py", line=2, severity="info", category="lint",
            tool="test", message="i2", rule_id="T002", suggestion="",
        )
        issue3 = Issue(
            file="b.py", line=1, severity="critical", category="security",
            tool="test", message="i3", rule_id="T003", suggestion="fix",
        )
        results = [
            ReviewResult(chunk_name="f0", file_path="a.py", issues=[issue1, issue2], success=True),
            ReviewResult(chunk_name="f1", file_path="b.py", issues=[issue3], success=True),
        ]
        batch_result = collect_results(results)
        assert len(batch_result.all_issues) == 3


class TestReviewResultIssueType:
    """ReviewResult.issues が list[Issue] 型であることのテスト（FR-7f）。"""

    def test_issues_accepts_issue_objects(self) -> None:
        """ReviewResult.issues に Issue オブジェクトを格納できること。"""
        issue = Issue(
            file="test.py", line=1, severity="warning",
            category="lint", tool="test", message="test issue",
            rule_id="T001", suggestion="fix it",
        )
        result = ReviewResult(
            chunk_name="f0", file_path="test.py",
            issues=[issue], success=True,
        )
        assert len(result.issues) == 1
        assert isinstance(result.issues[0], Issue)

    def test_batch_result_all_issues_are_issue_type(self) -> None:
        """BatchResult.all_issues も list[Issue] であること。"""
        issue = Issue(
            file="test.py", line=1, severity="warning",
            category="lint", tool="test", message="msg",
            rule_id="T001", suggestion="",
        )
        results = [
            ReviewResult(chunk_name="f0", file_path="a.py", issues=[issue], success=True),
        ]
        batch = collect_results(results)
        assert all(isinstance(i, Issue) for i in batch.all_issues)


class TestParseLlmIssues:
    """parse_llm_issues() のテスト。"""

    def test_parses_structured_output(self) -> None:
        """構造化された LLM 出力を Issue に変換できること。"""
        raw = (
            "- severity: warning\n"
            "- line: 42\n"
            "- message: Unused variable 'x'\n"
            "- suggestion: Remove the variable\n"
        )
        issues = parse_llm_issues(raw, "test.py")
        assert len(issues) >= 1
        assert issues[0].severity == "warning"
        assert issues[0].line == 42

    def test_unstructured_text_becomes_info_issue(self) -> None:
        """パースできないテキストは info Issue になること。"""
        raw = "This code looks fine overall."
        issues = parse_llm_issues(raw, "test.py")
        assert len(issues) == 1
        assert issues[0].severity == "info"
        assert issues[0].category == "review"

    def test_empty_input(self) -> None:
        """空文字列は空リストを返すこと。"""
        issues = parse_llm_issues("", "test.py")
        assert issues == []
