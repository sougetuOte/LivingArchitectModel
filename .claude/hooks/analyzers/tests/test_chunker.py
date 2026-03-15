"""Task B-1a/B-1b: Chunk データモデル + チャンク分割エンジンのテスト

対応仕様: scalable-code-review-spec.md FR-2
対応設計: scalable-code-review-design.md Section 3.4, 3.5
"""
from __future__ import annotations

import dataclasses
import textwrap

from analyzers.chunker import (
    Chunk,
    TreeSitterNotAvailable,
    chunk_file,
    count_tokens,
)


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
        # 空白区切り: ["def", "foo(x:", "int)", "->", "str:"] = 5 ワード
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


# ============================================================
# B-1b: tree-sitter 統合 + チャンク分割エンジン
# ============================================================

# --- サンプル Python ソースコード ---

SMALL_FUNC = textwrap.dedent("""\
    import os
    import sys

    MAX_SIZE = 100

    def hello(name: str) -> str:
        return f"Hello, {name}"
""")

TWO_FUNCTIONS = textwrap.dedent("""\
    import os

    def foo() -> int:
        return 1

    def bar() -> int:
        return 2
""")

SMALL_CLASS = textwrap.dedent("""\
    import os

    class Greeter:
        def __init__(self, name: str):
            self.name = name

        def greet(self) -> str:
            return f"Hello, {self.name}"
""")

# 巨大関数: chunk_size_tokens を超えるようなコード
BIG_FUNCTION = textwrap.dedent("""\
    def giant():
        {body}
""").format(body="\n        ".join(f"x{i} = {i}" for i in range(200)))

BIG_CLASS_WITH_METHODS = textwrap.dedent("""\
    class BigClass:
        def method_a(self):
            return 1

        def method_b(self):
            return 2

        def method_c(self):
            {body}
""").format(body="\n            ".join(f"x{i} = {i}" for i in range(200)))


class TestTreeSitterImport:
    """tree-sitter の import と例外のテスト。"""

    def test_tree_sitter_not_available_is_exception(self) -> None:
        """TreeSitterNotAvailable が Exception のサブクラスであること。"""
        assert issubclass(TreeSitterNotAvailable, Exception)


class TestChunkFile:
    """chunk_file() のテスト。"""

    def test_single_function(self) -> None:
        """トップレベル関数 1 つ → L1 チャンク 1 つ。"""
        chunks = chunk_file(SMALL_FUNC, "small.py")
        func_chunks = [c for c in chunks if c.level == "L1"]
        assert len(func_chunks) == 1
        assert func_chunks[0].node_name == "hello"
        assert "def hello" in func_chunks[0].content

    def test_two_functions(self) -> None:
        """トップレベル関数 2 つ → L1 チャンク 2 つ。"""
        chunks = chunk_file(TWO_FUNCTIONS, "two.py")
        func_chunks = [c for c in chunks if c.level == "L1"]
        assert len(func_chunks) == 2
        names = {c.node_name for c in func_chunks}
        assert names == {"foo", "bar"}

    def test_small_class_is_l2(self) -> None:
        """小さなクラス → L2 チャンク（分割されない）。"""
        chunks = chunk_file(SMALL_CLASS, "cls.py")
        class_chunks = [c for c in chunks if c.node_name == "Greeter"]
        assert len(class_chunks) == 1
        assert class_chunks[0].level == "L2"

    def test_big_class_splits_to_l1(self) -> None:
        """chunk_size_tokens を超えるクラス → L1 に分割（メソッド単位）。"""
        chunks = chunk_file(
            BIG_CLASS_WITH_METHODS, "big_cls.py", chunk_size_tokens=50
        )
        l1_chunks = [c for c in chunks if c.level == "L1"]
        assert len(l1_chunks) >= 2  # method_a, method_b, method_c の少なくとも 2 つ

    def test_file_path_propagated(self) -> None:
        """chunk_file に渡した file_path が各 Chunk に設定されること。"""
        chunks = chunk_file(SMALL_FUNC, "my/path.py")
        for c in chunks:
            assert c.file_path == "my/path.py"

    def test_start_end_lines_valid(self) -> None:
        """start_line <= end_line で、1 以上であること。"""
        chunks = chunk_file(TWO_FUNCTIONS, "f.py")
        for c in chunks:
            assert c.start_line >= 1
            assert c.end_line >= c.start_line

    def test_token_count_matches_content(self) -> None:
        """token_count がチャンク全体のワード数と一致すること。"""
        chunks = chunk_file(SMALL_FUNC, "f.py")
        for c in chunks:
            full = c.overlap_header + c.content + c.overlap_footer
            assert c.token_count == count_tokens(full)

    def test_giant_function_warning(self) -> None:
        """chunk_size_tokens を超える巨大関数 → chunks に含まれ、level は L1。"""
        chunks = chunk_file(BIG_FUNCTION, "big.py", chunk_size_tokens=50)
        giant_chunks = [c for c in chunks if c.node_name == "giant"]
        assert len(giant_chunks) == 1
        # 巨大関数でも 1 チャンクとして処理される（構文的妥当性を優先）
        assert giant_chunks[0].level == "L1"
        assert giant_chunks[0].token_count > 50

    def test_empty_file(self) -> None:
        """空ファイル → 空リスト。"""
        chunks = chunk_file("", "empty.py")
        assert chunks == []

    def test_only_imports(self) -> None:
        """import のみのファイル → チャンクなし or 最小限。"""
        source = "import os\nimport sys\n"
        chunks = chunk_file(source, "imports.py")
        # import のみなのでレビュー対象のチャンクは不要
        func_chunks = [c for c in chunks if c.level in ("L1", "L2")]
        assert len(func_chunks) == 0


# ============================================================
# B-1c: のりしろ付与
# ============================================================

SOURCE_WITH_IMPORTS_AND_FUNCS = textwrap.dedent("""\
    import os
    import sys
    from pathlib import Path

    MAX_RETRIES = 3
    DEFAULT_NAME = "world"

    def greet(name: str) -> str:
        return f"Hello, {name}"

    def farewell(name: str) -> str:
        return f"Goodbye, {name}"

    def helper() -> int:
        return 42
""")

SOURCE_CLASS_AND_FUNC = textwrap.dedent("""\
    import json

    TIMEOUT = 30

    class Parser:
        def __init__(self, data: str):
            self.data = data

        def parse(self) -> dict:
            return json.loads(self.data)

    def standalone(x: int) -> int:
        return x * 2
""")


class TestOverlapHeader:
    """overlap_header（ファイルヘッダーのりしろ）のテスト。"""

    def test_header_contains_imports(self) -> None:
        """overlap_header に import 文が含まれること。"""
        chunks = chunk_file(SOURCE_WITH_IMPORTS_AND_FUNCS, "f.py")
        for c in chunks:
            assert "import os" in c.overlap_header
            assert "import sys" in c.overlap_header
            assert "from pathlib import Path" in c.overlap_header

    def test_header_contains_module_constants(self) -> None:
        """overlap_header にモジュールレベル定数が含まれること。"""
        chunks = chunk_file(SOURCE_WITH_IMPORTS_AND_FUNCS, "f.py")
        for c in chunks:
            assert "MAX_RETRIES" in c.overlap_header
            assert "DEFAULT_NAME" in c.overlap_header

    def test_header_does_not_contain_function_body(self) -> None:
        """overlap_header に関数本体が含まれないこと。"""
        chunks = chunk_file(SOURCE_WITH_IMPORTS_AND_FUNCS, "f.py")
        for c in chunks:
            assert "return f\"Hello" not in c.overlap_header


class TestOverlapFooter:
    """overlap_footer（シグネチャサマリーのりしろ）のテスト。"""

    def test_footer_contains_other_signatures(self) -> None:
        """overlap_footer に同一ファイル内の他の関数シグネチャが含まれること。"""
        chunks = chunk_file(SOURCE_WITH_IMPORTS_AND_FUNCS, "f.py")
        greet_chunk = [c for c in chunks if c.node_name == "greet"][0]
        # greet のフッターには farewell と helper のシグネチャが含まれるべき
        assert "farewell" in greet_chunk.overlap_footer
        assert "helper" in greet_chunk.overlap_footer

    def test_footer_excludes_own_signature(self) -> None:
        """overlap_footer に自分自身のシグネチャは含まれないこと。"""
        chunks = chunk_file(SOURCE_WITH_IMPORTS_AND_FUNCS, "f.py")
        greet_chunk = [c for c in chunks if c.node_name == "greet"][0]
        # フッターの各行に "def greet" が含まれないこと
        footer_lines = greet_chunk.overlap_footer.split("\n")
        assert not any("def greet" in line for line in footer_lines)

    def test_footer_contains_class_signature(self) -> None:
        """関数のフッターにクラスのシグネチャが含まれること。"""
        chunks = chunk_file(SOURCE_CLASS_AND_FUNC, "f.py")
        func_chunk = [c for c in chunks if c.node_name == "standalone"][0]
        assert "Parser" in func_chunk.overlap_footer

    def test_class_footer_contains_function_signature(self) -> None:
        """クラスのフッターに同一ファイルの関数シグネチャが含まれること。"""
        chunks = chunk_file(SOURCE_CLASS_AND_FUNC, "f.py")
        class_chunk = [c for c in chunks if c.node_name == "Parser"][0]
        assert "standalone" in class_chunk.overlap_footer


class TestOverlapSizeLimit:
    """のりしろサイズ制限のテスト。"""

    def test_total_within_limit(self) -> None:
        """チャンク全体（本体+のりしろ）が chunk_size * (1+overlap_ratio) 以内。"""
        chunks = chunk_file(
            SOURCE_WITH_IMPORTS_AND_FUNCS, "f.py",
            chunk_size_tokens=3000, overlap_ratio=0.2,
        )
        max_tokens = int(3000 * 1.2)
        for c in chunks:
            assert c.token_count <= max_tokens, (
                f"{c.node_name}: {c.token_count} > {max_tokens}"
            )

    def test_token_count_includes_overlap(self) -> None:
        """token_count がのりしろ込みの値であること。"""
        chunks = chunk_file(SOURCE_WITH_IMPORTS_AND_FUNCS, "f.py")
        for c in chunks:
            full = c.overlap_header + c.content + c.overlap_footer
            assert c.token_count == count_tokens(full)
