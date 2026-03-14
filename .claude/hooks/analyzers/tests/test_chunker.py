"""Task B-1a: Chunk データモデル + トークンカウントのテスト

対応仕様: scalable-code-review-spec.md FR-2
対応設計: scalable-code-review-design.md Section 3.4, 3.5
"""
from __future__ import annotations

import pytest

from analyzers.chunker import Chunk, count_tokens


class TestCountTokens:
    """count_tokens() のテスト。"""

    def test_empty_string(self) -> None:
        """空文字列は 0 トークン。"""
        assert count_tokens("") == 0

    def test_single_word(self) -> None:
        """1 ワードは 1 トークン。"""
        assert count_tokens("hello") == 1

    def test_multiple_words(self) -> None:
        """複数ワードのカウント。"""
        assert count_tokens("def foo(x: int) -> str:") == 5

    def test_multiline_code(self) -> None:
        """複数行のコードのカウント。"""
        code = "def foo():\n    return 42\n"
        assert count_tokens(code) == 4

    def test_whitespace_only(self) -> None:
        """空白のみは 0 トークン。"""
        assert count_tokens("   \n\t  \n") == 0


class TestChunkDataclass:
    """Chunk dataclass のテスト。"""

    def test_create_chunk(self) -> None:
        """Chunk を正しくインスタンス化できること。"""
        chunk = Chunk(
            file_path="src/main.py",
            start_line=10,
            end_line=50,
            content="def foo():\n    pass\n",
            overlap_header="import os\n",
            overlap_footer="def bar(): ...\n",
            token_count=5,
            level="L2",
            node_name="FooClass",
        )
        assert chunk.file_path == "src/main.py"
        assert chunk.start_line == 10
        assert chunk.end_line == 50
        assert chunk.level == "L2"
        assert chunk.node_name == "FooClass"

    def test_chunk_level_values(self) -> None:
        """level は L1/L2/L3 のいずれか。"""
        for level in ("L1", "L2", "L3"):
            chunk = Chunk(
                file_path="f.py",
                start_line=1,
                end_line=10,
                content="x = 1",
                overlap_header="",
                overlap_footer="",
                token_count=3,
                level=level,
                node_name="test",
            )
            assert chunk.level == level

    def test_chunk_total_content(self) -> None:
        """overlap_header + content + overlap_footer の結合が可能。"""
        chunk = Chunk(
            file_path="f.py",
            start_line=1,
            end_line=5,
            content="def foo():\n    pass\n",
            overlap_header="import os\n\n",
            overlap_footer="\ndef bar(): ...\n",
            token_count=10,
            level="L1",
            node_name="foo",
        )
        full = chunk.overlap_header + chunk.content + chunk.overlap_footer
        assert "import os" in full
        assert "def foo" in full
        assert "def bar" in full

    def test_chunk_serialization(self) -> None:
        """Chunk が dataclasses.asdict でシリアライズ可能。"""
        import dataclasses

        chunk = Chunk(
            file_path="f.py",
            start_line=1,
            end_line=10,
            content="x = 1",
            overlap_header="",
            overlap_footer="",
            token_count=3,
            level="L1",
            node_name="test",
        )
        d = dataclasses.asdict(chunk)
        assert d["file_path"] == "f.py"
        assert d["token_count"] == 3
        assert isinstance(d, dict)
