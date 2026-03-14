"""Task B-2a: バッチ並列オーケストレーションのテスト

対応仕様: scalable-code-review-spec.md FR-2
対応設計: scalable-code-review-design.md Section 3.3, 3.6, 3.8
"""
from __future__ import annotations

from analyzers.chunker import Chunk
from analyzers.orchestrator import (
    ReviewResult,
    batch_chunks,
    build_review_prompt,
    collect_results,
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
        results = [
            ReviewResult(chunk_name="f0", file_path="a.py", issues=["issue1"], success=True),
            ReviewResult(chunk_name="f1", file_path="b.py", issues=["issue2"], success=True),
        ]
        batch_result = collect_results(results)
        assert batch_result.total == 2
        assert batch_result.succeeded == 2
        assert batch_result.failed == 0
        assert len(batch_result.all_issues) == 2

    def test_collect_with_failures(self) -> None:
        """失敗を含む結果の収集。"""
        results = [
            ReviewResult(chunk_name="f0", file_path="a.py", issues=["issue1"], success=True),
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
        results = [
            ReviewResult(chunk_name="f0", file_path="a.py", issues=["i1", "i2"], success=True),
            ReviewResult(chunk_name="f1", file_path="b.py", issues=["i3"], success=True),
        ]
        batch_result = collect_results(results)
        assert len(batch_result.all_issues) == 3
