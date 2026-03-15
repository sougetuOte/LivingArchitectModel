"""card_generator のテスト。

Task C-1a: 概要カード生成エンジン（機械的フィールド）
Task C-1b: Phase 2 Agent プロンプト拡張（責務フィールド生成）
Task C-2a: Layer 2 モジュール統合（要約カード生成）
Task C-2b: Layer 3 システムレビュー（循環依存検出、命名パターン違反、仕様ドリフト）
対応仕様: scalable-code-review-spec.md
対応設計: scalable-code-review-design.md Section 4.3, 4.4, 4.5
"""
from __future__ import annotations

from pathlib import Path

import pytest

from analyzers.base import ASTNode, Issue
from analyzers.card_generator import (
    FileCard,
    ModuleCard,
    _condense_sccs,
    build_topo_order,
    check_all_exports,
    check_name_collisions,
    check_unused_reexports,
    collect_spec_drift_context,
    detect_circular_dependencies,
    detect_module_naming_violations,
    detect_module_boundaries,
    generate_file_cards,
    generate_module_cards,
    load_file_card,
    load_module_card,
    merge_responsibilities,
    parse_responsibility,
    save_file_card,
    save_module_card,
)


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------


def _make_function_node(name: str, start: int = 1, end: int = 10) -> ASTNode:
    return ASTNode(
        name=name,
        kind="function",
        start_line=start,
        end_line=end,
        signature=f"def {name}():",
        children=[],
        docstring=None,
    )


def _make_class_node(name: str, methods: list[ASTNode] | None = None) -> ASTNode:
    return ASTNode(
        name=name,
        kind="class",
        start_line=1,
        end_line=50,
        signature=f"class {name}:",
        children=methods or [],
        docstring=None,
    )


def _make_module_node(children: list[ASTNode]) -> ASTNode:
    """module ノード（ルート）を作成する。"""
    return ASTNode(
        name="module",
        kind="module",
        start_line=1,
        end_line=100,
        signature="",
        children=children,
        docstring=None,
    )


def _make_issue(file: str, severity: str) -> Issue:
    return Issue(
        file=file,
        line=1,
        severity=severity,
        category="lint",
        tool="ruff",
        message="test issue",
        rule_id="TEST001",
        suggestion="fix it",
    )


@pytest.fixture()
def simple_ast_map() -> dict[str, ASTNode]:
    """src/foo.py に関数 2 つとクラス 1 つを持つ ASTNode マップ。"""
    func_a = _make_function_node("func_a", 1, 10)
    func_b = _make_function_node("func_b", 12, 20)
    my_class = _make_class_node("MyClass", [_make_function_node("method_x", 25, 35)])
    module_node = _make_module_node([func_a, func_b, my_class])
    return {"src/foo.py": module_node}


@pytest.fixture()
def multi_file_ast_map() -> dict[str, ASTNode]:
    """複数ファイルの ASTNode マップ。"""
    foo_module = _make_module_node([
        _make_function_node("parse"),
        _make_class_node("Parser"),
    ])
    bar_module = _make_module_node([
        _make_function_node("run"),
    ])
    return {
        "src/foo.py": foo_module,
        "src/bar.py": bar_module,
    }


# ---------------------------------------------------------------------------
# test_generate_file_card_public_api
# ---------------------------------------------------------------------------


def test_generate_file_card_public_api(simple_ast_map: dict[str, ASTNode]) -> None:
    """トップレベル children の関数/クラス名が public_api に含まれること。"""
    import_map: dict[str, list[str]] = {"src/foo.py": []}
    issues: list[Issue] = []
    chunk_issues: dict[str, list[Issue]] = {}

    cards = generate_file_cards(simple_ast_map, import_map, issues, chunk_issues)

    assert "src/foo.py" in cards
    card = cards["src/foo.py"]
    assert "func_a" in card.public_api
    assert "func_b" in card.public_api
    assert "MyClass" in card.public_api


def test_generate_file_card_public_api_excludes_methods(
    simple_ast_map: dict[str, ASTNode],
) -> None:
    """クラス内メソッドは public_api に含まれないこと（トップレベルのみ）。

    (simple_ast_map fixture を使用、test_generate_file_card_public_api と同じ Act だが検証観点が異なる)
    """
    import_map: dict[str, list[str]] = {"src/foo.py": []}
    issues: list[Issue] = []
    chunk_issues: dict[str, list[Issue]] = {}

    cards = generate_file_cards(simple_ast_map, import_map, issues, chunk_issues)

    card = cards["src/foo.py"]
    assert "method_x" not in card.public_api


# ---------------------------------------------------------------------------
# test_generate_file_card_dependencies
# ---------------------------------------------------------------------------


def test_generate_file_card_dependencies() -> None:
    """import_map から依存先が正しく取得されること。"""
    ast_map: dict[str, ASTNode] = {
        "src/foo.py": _make_module_node([_make_function_node("foo")]),
    }
    import_map = {
        "src/foo.py": ["os", "sys", "src.bar", "src.baz"],
    }
    issues: list[Issue] = []
    chunk_issues: dict[str, list[Issue]] = {}

    cards = generate_file_cards(ast_map, import_map, issues, chunk_issues)

    card = cards["src/foo.py"]
    assert "os" in card.dependencies
    assert "sys" in card.dependencies
    assert "src.bar" in card.dependencies
    assert "src.baz" in card.dependencies


def test_generate_file_card_dependencies_empty_when_no_imports() -> None:
    """import がないファイルの dependencies は空リストであること。"""
    ast_map: dict[str, ASTNode] = {
        "src/foo.py": _make_module_node([]),
    }
    import_map: dict[str, list[str]] = {}
    issues: list[Issue] = []
    chunk_issues: dict[str, list[Issue]] = {}

    cards = generate_file_cards(ast_map, import_map, issues, chunk_issues)

    assert cards["src/foo.py"].dependencies == []


# ---------------------------------------------------------------------------
# test_generate_file_card_dependents
# ---------------------------------------------------------------------------


def test_generate_file_card_dependents() -> None:
    """import_map の逆引きで依存元が正しく取得されること。"""
    ast_map: dict[str, ASTNode] = {
        "src/foo.py": _make_module_node([_make_function_node("foo")]),
        "src/bar.py": _make_module_node([_make_function_node("bar")]),
        "src/baz.py": _make_module_node([_make_function_node("baz")]),
    }
    # bar と baz が foo を import している
    import_map = {
        "src/foo.py": [],
        "src/bar.py": ["src.foo"],
        "src/baz.py": ["src.foo", "src.bar"],
    }
    issues: list[Issue] = []
    chunk_issues: dict[str, list[Issue]] = {}

    cards = generate_file_cards(ast_map, import_map, issues, chunk_issues)

    foo_card = cards["src/foo.py"]
    assert "src/bar.py" in foo_card.dependents
    assert "src/baz.py" in foo_card.dependents


def test_generate_file_card_dependents_empty_when_no_one_imports() -> None:
    """誰も import していないファイルの dependents は空リストであること。"""
    ast_map: dict[str, ASTNode] = {
        "src/foo.py": _make_module_node([_make_function_node("foo")]),
        "src/bar.py": _make_module_node([_make_function_node("bar")]),
    }
    import_map = {
        "src/foo.py": ["os"],
        "src/bar.py": ["sys"],
    }
    issues: list[Issue] = []
    chunk_issues: dict[str, list[Issue]] = {}

    cards = generate_file_cards(ast_map, import_map, issues, chunk_issues)

    assert cards["src/foo.py"].dependents == []
    assert cards["src/bar.py"].dependents == []


# ---------------------------------------------------------------------------
# test_generate_file_card_issue_counts
# ---------------------------------------------------------------------------


def test_generate_file_card_issue_counts_from_static_issues() -> None:
    """static-issues から Issue 数が正しく集計されること。"""
    ast_map: dict[str, ASTNode] = {
        "src/foo.py": _make_module_node([_make_function_node("foo")]),
    }
    import_map: dict[str, list[str]] = {}
    issues = [
        _make_issue("src/foo.py", "critical"),
        _make_issue("src/foo.py", "critical"),
        _make_issue("src/foo.py", "warning"),
        _make_issue("src/bar.py", "info"),  # 別ファイルの Issue は含まない
    ]
    chunk_issues: dict[str, list[Issue]] = {}

    cards = generate_file_cards(ast_map, import_map, issues, chunk_issues)

    counts = cards["src/foo.py"].issue_counts
    assert counts["critical"] == 2
    assert counts["warning"] == 1
    assert counts["info"] == 0


def test_generate_file_card_issue_counts_from_chunk_issues() -> None:
    """chunk-results から Issue 数が正しく集計されること（static と合算）。"""
    ast_map: dict[str, ASTNode] = {
        "src/foo.py": _make_module_node([_make_function_node("foo")]),
    }
    import_map: dict[str, list[str]] = {}
    issues = [
        _make_issue("src/foo.py", "warning"),
    ]
    chunk_issues = {
        "src/foo.py": [
            _make_issue("src/foo.py", "critical"),
            _make_issue("src/foo.py", "info"),
        ],
    }

    cards = generate_file_cards(ast_map, import_map, issues, chunk_issues)

    counts = cards["src/foo.py"].issue_counts
    assert counts["critical"] == 1
    assert counts["warning"] == 1
    assert counts["info"] == 1


def test_generate_file_card_issue_counts_zero_when_no_issues() -> None:
    """Issue がないファイルのカウントはすべて 0 であること。"""
    ast_map: dict[str, ASTNode] = {
        "src/foo.py": _make_module_node([]),
    }
    import_map: dict[str, list[str]] = {}
    issues: list[Issue] = []
    chunk_issues: dict[str, list[Issue]] = {}

    cards = generate_file_cards(ast_map, import_map, issues, chunk_issues)

    counts = cards["src/foo.py"].issue_counts
    assert counts["critical"] == 0
    assert counts["warning"] == 0
    assert counts["info"] == 0


# ---------------------------------------------------------------------------
# test_generate_file_cards_multiple_files
# ---------------------------------------------------------------------------


def test_generate_file_cards_multiple_files(
    multi_file_ast_map: dict[str, ASTNode],
) -> None:
    """複数ファイルのカードが全件生成されること。"""
    import_map = {
        "src/foo.py": ["os"],
        "src/bar.py": ["src.foo"],
    }
    issues: list[Issue] = []
    chunk_issues: dict[str, list[Issue]] = {}

    cards = generate_file_cards(multi_file_ast_map, import_map, issues, chunk_issues)

    assert len(cards) == 2
    assert "src/foo.py" in cards
    assert "src/bar.py" in cards

    # bar は foo に依存している
    assert "src.foo" in cards["src/bar.py"].dependencies

    # foo は bar から import されている
    assert "src/bar.py" in cards["src/foo.py"].dependents


# ---------------------------------------------------------------------------
# test_save_and_load_file_card
# ---------------------------------------------------------------------------


def test_save_and_load_file_card(tmp_path: Path) -> None:
    """FileCard の保存と読み込みのラウンドトリップ。"""
    state_dir = tmp_path / "review-state"
    card = FileCard(
        file_path="src/foo.py",
        public_api=["func_a", "MyClass"],
        dependencies=["os", "sys"],
        dependents=["src/bar.py"],
        issue_counts={"critical": 1, "warning": 2, "info": 0},
        responsibility="",
    )

    save_file_card(state_dir, card)
    loaded = load_file_card(state_dir, "src/foo.py")

    assert loaded is not None
    assert loaded.file_path == card.file_path
    assert loaded.public_api == card.public_api
    assert loaded.dependencies == card.dependencies
    assert loaded.dependents == card.dependents
    assert loaded.issue_counts == card.issue_counts
    assert loaded.responsibility == card.responsibility


def test_save_file_card_creates_directory(tmp_path: Path) -> None:
    """保存先ディレクトリが存在しない場合でも自動作成されること。"""
    state_dir = tmp_path / "nonexistent" / "review-state"
    card = FileCard(
        file_path="src/foo.py",
        public_api=[],
        dependencies=[],
        dependents=[],
        issue_counts={"critical": 0, "warning": 0, "info": 0},
        responsibility="",
    )

    save_file_card(state_dir, card)

    cards_dir = state_dir / "cards" / "file-cards"
    assert cards_dir.exists()


def test_load_file_card_returns_none_when_missing(tmp_path: Path) -> None:
    """存在しないカードを読み込んだ場合 None が返ること。"""
    state_dir = tmp_path / "review-state"
    state_dir.mkdir()

    result = load_file_card(state_dir, "src/nonexistent.py")

    assert result is None


def test_save_file_card_path_with_subdirectory(tmp_path: Path) -> None:
    """ネストしたパスのファイルカードが正しく保存・読み込みされること。"""
    state_dir = tmp_path / "review-state"
    card = FileCard(
        file_path="src/hooks/analyzers/base.py",
        public_api=["ASTNode", "Issue"],
        dependencies=["dataclasses"],
        dependents=[],
        issue_counts={"critical": 0, "warning": 1, "info": 3},
        responsibility="",
    )

    save_file_card(state_dir, card)
    loaded = load_file_card(state_dir, "src/hooks/analyzers/base.py")

    assert loaded is not None
    assert loaded.file_path == "src/hooks/analyzers/base.py"


# ---------------------------------------------------------------------------
# test_dependents_reverse_lookup_accuracy
# ---------------------------------------------------------------------------


def test_dependents_reverse_lookup_accuracy() -> None:
    """A→B, C→B の場合、B の dependents = [A, C] が正確に構築されること。"""
    ast_map: dict[str, ASTNode] = {
        "src/a.py": _make_module_node([_make_function_node("a_func")]),
        "src/b.py": _make_module_node([_make_function_node("b_func")]),
        "src/c.py": _make_module_node([_make_function_node("c_func")]),
    }
    import_map = {
        "src/a.py": ["src.b"],  # A → B
        "src/b.py": [],
        "src/c.py": ["src.b"],  # C → B
    }
    issues: list[Issue] = []
    chunk_issues: dict[str, list[Issue]] = {}

    cards = generate_file_cards(ast_map, import_map, issues, chunk_issues)

    b_card = cards["src/b.py"]
    assert sorted(b_card.dependents) == ["src/a.py", "src/c.py"]

    # A, C 自身には依存元がない
    assert cards["src/a.py"].dependents == []
    assert cards["src/c.py"].dependents == []


def test_dependents_does_not_include_self() -> None:
    """自己参照は dependents に含まれないこと。"""
    ast_map: dict[str, ASTNode] = {
        "src/foo.py": _make_module_node([_make_function_node("foo")]),
    }
    import_map = {
        "src/foo.py": ["src.foo"],  # 自己参照（循環防止確認）
    }
    issues: list[Issue] = []
    chunk_issues: dict[str, list[Issue]] = {}

    cards = generate_file_cards(ast_map, import_map, issues, chunk_issues)

    # 自己参照は逆引きで自分自身に戻るが、dependents には含めない
    assert "src/foo.py" not in cards["src/foo.py"].dependents


# ---------------------------------------------------------------------------
# test_file_card_format_markdown
# ---------------------------------------------------------------------------


def test_file_card_format_markdown() -> None:
    """FileCard の Markdown 出力が設計書 Section 4.3 の形式に合致すること。"""
    card = FileCard(
        file_path="src/foo.py",
        public_api=["func_a", "MyClass"],
        dependencies=["os", "sys"],
        dependents=["src/bar.py"],
        issue_counts={"critical": 1, "warning": 2, "info": 3},
        responsibility="",
    )

    md = card.to_markdown()

    assert "## src/foo.py" in md
    assert "**責務**" in md
    assert "**公開 API**" in md
    assert "**依存先**" in md
    assert "**依存元**" in md
    assert "**Issue 数**" in md
    assert "Critical: 1" in md
    assert "Warning: 2" in md
    assert "Info: 3" in md


def test_file_card_format_markdown_with_responsibility() -> None:
    """責務フィールドが設定されている場合、正しく出力されること。"""
    card = FileCard(
        file_path="src/foo.py",
        public_api=["func_a"],
        dependencies=[],
        dependents=[],
        issue_counts={"critical": 0, "warning": 0, "info": 0},
        responsibility="Python AST 解析を担当するモジュール",
    )

    md = card.to_markdown()

    assert "Python AST 解析を担当するモジュール" in md


def test_file_card_format_markdown_empty_lists() -> None:
    """API・依存先・依存元が空の場合でも Markdown が出力されること。"""
    card = FileCard(
        file_path="src/empty.py",
        public_api=[],
        dependencies=[],
        dependents=[],
        issue_counts={"critical": 0, "warning": 0, "info": 0},
        responsibility="",
    )

    md = card.to_markdown()

    assert "## src/empty.py" in md
    assert "**公開 API**" in md


# ---------------------------------------------------------------------------
# C-1b: parse_responsibility
# ---------------------------------------------------------------------------

_AGENT_OUTPUT_WITH_RESPONSIBILITY = """\
## レビュー結果

いくつかの問題が見つかりました。

- [W-1] 命名が不明瞭です (src/foo.py:10)
- [W-2] エラー処理が不足しています (src/foo.py:25)

---FILE-CARD-RESPONSIBILITY---
Python AST 解析と構文ノードのラッパー変換を担当するモジュール
---END-FILE-CARD-RESPONSIBILITY---
"""

_AGENT_OUTPUT_WITHOUT_RESPONSIBILITY = """\
## レビュー結果

特に問題は見つかりませんでした。
"""

_AGENT_OUTPUT_EMPTY_RESPONSIBILITY = """\
---FILE-CARD-RESPONSIBILITY---

---END-FILE-CARD-RESPONSIBILITY---
"""


def test_parse_responsibility_normal() -> None:
    """Agent 出力からマーカー間の責務フィールドを抽出できること。"""
    result = parse_responsibility(_AGENT_OUTPUT_WITH_RESPONSIBILITY)
    assert result == "Python AST 解析と構文ノードのラッパー変換を担当するモジュール"


def test_parse_responsibility_missing_marker() -> None:
    """マーカーがない場合は空文字を返すこと（フォールバック）。"""
    result = parse_responsibility(_AGENT_OUTPUT_WITHOUT_RESPONSIBILITY)
    assert result == ""


def test_parse_responsibility_empty_between_markers() -> None:
    """マーカー間が空の場合は空文字を返すこと。"""
    result = parse_responsibility(_AGENT_OUTPUT_EMPTY_RESPONSIBILITY)
    assert result == ""


def test_parse_responsibility_strips_whitespace() -> None:
    """責務フィールドの前後の空白が除去されること。"""
    output = (
        "---FILE-CARD-RESPONSIBILITY---\n"
        "  責務の説明  \n"
        "---END-FILE-CARD-RESPONSIBILITY---\n"
    )
    result = parse_responsibility(output)
    assert result == "責務の説明"


# ---------------------------------------------------------------------------
# C-1b: merge_responsibilities
# ---------------------------------------------------------------------------


def test_merge_responsibilities_updates_cards() -> None:
    """責務マップに基づいて FileCard の responsibility が更新されること。"""
    cards = {
        "src/foo.py": FileCard(
            file_path="src/foo.py",
            public_api=["foo"],
            dependencies=[],
            dependents=[],
            issue_counts={"critical": 0, "warning": 0, "info": 0},
            responsibility="",
        ),
        "src/bar.py": FileCard(
            file_path="src/bar.py",
            public_api=["bar"],
            dependencies=[],
            dependents=[],
            issue_counts={"critical": 0, "warning": 0, "info": 0},
            responsibility="",
        ),
    }
    responsibilities = {
        "src/foo.py": "データ変換ユーティリティ",
        "src/bar.py": "設定ファイルの読み込み",
    }

    merge_responsibilities(cards, responsibilities)

    assert cards["src/foo.py"].responsibility == "データ変換ユーティリティ"
    assert cards["src/bar.py"].responsibility == "設定ファイルの読み込み"


def test_merge_responsibilities_skips_missing_files() -> None:
    """cards に存在しないファイルの責務はスキップされること。"""
    cards = {
        "src/foo.py": FileCard(
            file_path="src/foo.py",
            public_api=[],
            dependencies=[],
            dependents=[],
            issue_counts={"critical": 0, "warning": 0, "info": 0},
            responsibility="",
        ),
    }
    responsibilities = {
        "src/foo.py": "ユーティリティ",
        "src/nonexistent.py": "存在しないファイル",
    }

    merge_responsibilities(cards, responsibilities)

    assert cards["src/foo.py"].responsibility == "ユーティリティ"
    assert "src/nonexistent.py" not in cards


def test_merge_responsibilities_preserves_existing_when_empty() -> None:
    """空文字の責務ではカードの既存値を上書きしないこと。"""
    cards = {
        "src/foo.py": FileCard(
            file_path="src/foo.py",
            public_api=[],
            dependencies=[],
            dependents=[],
            issue_counts={"critical": 0, "warning": 0, "info": 0},
            responsibility="既存の責務",
        ),
    }
    responsibilities = {
        "src/foo.py": "",
    }

    merge_responsibilities(cards, responsibilities)

    assert cards["src/foo.py"].responsibility == "既存の責務"


# ---------------------------------------------------------------------------
# C-2a: ModuleCard / detect_module_boundaries
# ---------------------------------------------------------------------------


def test_detect_module_boundaries_with_init_py() -> None:
    """__init__.py が存在するディレクトリがモジュールとして検出されること。"""
    file_paths = [
        "src/analyzers/__init__.py",
        "src/analyzers/base.py",
        "src/analyzers/card_generator.py",
    ]

    result = detect_module_boundaries(file_paths)

    assert "src/analyzers" in result
    assert "src/analyzers/__init__.py" in result["src/analyzers"]
    assert "src/analyzers/base.py" in result["src/analyzers"]
    assert "src/analyzers/card_generator.py" in result["src/analyzers"]


def test_detect_module_boundaries_fallback_to_directory() -> None:
    """__init__.py がない場合ディレクトリ単位にフォールバックすること。"""
    file_paths = [
        "src/utils/helper.py",
        "src/utils/common.py",
    ]

    result = detect_module_boundaries(file_paths)

    assert "src/utils" in result
    assert "src/utils/helper.py" in result["src/utils"]
    assert "src/utils/common.py" in result["src/utils"]


def test_detect_module_boundaries_nested_modules() -> None:
    """ネストしたモジュール構造で各階層が正しく分類されること。"""
    file_paths = [
        "src/__init__.py",
        "src/foo.py",
        "src/bar/__init__.py",
        "src/bar/baz.py",
    ]

    result = detect_module_boundaries(file_paths)

    # src はモジュール（__init__.py あり）
    assert "src" in result
    assert "src/foo.py" in result["src"]
    # src/bar もモジュール（__init__.py あり）
    assert "src/bar" in result
    assert "src/bar/baz.py" in result["src/bar"]


def test_check_name_collisions_detects_duplicates() -> None:
    """複数ファイルで同名の関数/クラスが存在する場合に警告が返ること。"""
    module_files = ["src/foo.py", "src/bar.py"]
    ast_map = {
        "src/foo.py": _make_module_node([
            _make_function_node("parse"),
            _make_class_node("Config"),
        ]),
        "src/bar.py": _make_module_node([
            _make_function_node("parse"),  # 同名
            _make_function_node("run"),
        ]),
    }

    issues = check_name_collisions(module_files, ast_map)

    assert len(issues) > 0
    assert any("parse" in msg for msg in issues)


def test_check_name_collisions_no_duplicates() -> None:
    """衝突がない場合は空リストが返ること。"""
    module_files = ["src/foo.py", "src/bar.py"]
    ast_map = {
        "src/foo.py": _make_module_node([
            _make_function_node("parse"),
            _make_class_node("Config"),
        ]),
        "src/bar.py": _make_module_node([
            _make_function_node("run"),
            _make_class_node("Runner"),
        ]),
    }

    issues = check_name_collisions(module_files, ast_map)

    assert issues == []


def test_check_unused_reexports_detects_unused() -> None:
    """__init__.py が import するが誰にも使われていないモジュールを検出すること。"""
    module_files = ["src/__init__.py", "src/foo.py", "src/bar.py"]
    ast_map = {
        "src/__init__.py": _make_module_node([]),
        "src/foo.py": _make_module_node([_make_function_node("foo_func")]),
        "src/bar.py": _make_module_node([_make_function_node("bar_func")]),
    }
    # __init__.py が src.foo を import しているが、他の誰も src.__init__ を import しない
    import_map = {
        "src/__init__.py": ["src.foo"],
        "src/foo.py": [],
        "src/bar.py": [],
    }

    issues = check_unused_reexports(module_files, ast_map, import_map)

    # src.foo は __init__ で re-export されているが、誰も __init__ を使っていない
    assert any("src.foo" in msg for msg in issues)


def test_check_unused_reexports_all_used() -> None:
    """全ての re-export が使われている場合は空リストが返ること。"""
    module_files = ["src/__init__.py", "src/foo.py", "src/bar.py"]
    ast_map = {
        "src/__init__.py": _make_module_node([]),
        "src/foo.py": _make_module_node([_make_function_node("foo_func")]),
        "src/bar.py": _make_module_node([_make_function_node("bar_func")]),
    }
    # __init__.py が src.foo を import し、外部（src/bar.py）が src.__init__ を import している
    import_map = {
        "src/__init__.py": ["src.foo"],
        "src/foo.py": [],
        "src/bar.py": ["src"],  # src package（__init__）を使っている
    }

    issues = check_unused_reexports(module_files, ast_map, import_map)

    assert issues == []


def test_check_all_exports_missing_init() -> None:
    """__init__.py がないモジュールでは空リストが返ること（チェック不要）。"""
    module_files = ["src/foo.py", "src/bar.py"]
    ast_map = {
        "src/foo.py": _make_module_node([_make_function_node("foo")]),
        "src/bar.py": _make_module_node([_make_function_node("bar")]),
    }

    issues = check_all_exports(module_files, ast_map)

    assert issues == []


def _make_file_card(
    file_path: str,
    public_api: list[str] | None = None,
    issue_counts: dict[str, int] | None = None,
) -> FileCard:
    return FileCard(
        file_path=file_path,
        public_api=public_api or [],
        dependencies=[],
        dependents=[],
        issue_counts=issue_counts or {"critical": 0, "warning": 0, "info": 0},
        responsibility="",
    )


def test_generate_module_cards_basic() -> None:
    """file_cards からモジュールカードが生成されること。"""
    file_cards = {
        "src/analyzers/__init__.py": _make_file_card("src/analyzers/__init__.py"),
        "src/analyzers/base.py": _make_file_card("src/analyzers/base.py"),
    }
    ast_map = {
        "src/analyzers/__init__.py": _make_module_node([]),
        "src/analyzers/base.py": _make_module_node([_make_function_node("parse")]),
    }
    import_map: dict[str, list[str]] = {
        "src/analyzers/__init__.py": [],
        "src/analyzers/base.py": [],
    }

    module_cards = generate_module_cards(file_cards, ast_map, import_map)

    assert "src/analyzers" in module_cards
    card = module_cards["src/analyzers"]
    assert "src/analyzers/__init__.py" in card.file_cards
    assert "src/analyzers/base.py" in card.file_cards


def test_generate_module_cards_aggregates_issues() -> None:
    """各ファイルの Issue 数がモジュールカードに集計されること。"""
    file_cards = {
        "src/mod/__init__.py": _make_file_card(
            "src/mod/__init__.py",
            issue_counts={"critical": 1, "warning": 0, "info": 0},
        ),
        "src/mod/util.py": _make_file_card(
            "src/mod/util.py",
            issue_counts={"critical": 0, "warning": 2, "info": 1},
        ),
    }
    ast_map = {
        "src/mod/__init__.py": _make_module_node([]),
        "src/mod/util.py": _make_module_node([_make_function_node("util")]),
    }
    import_map: dict[str, list[str]] = {
        "src/mod/__init__.py": [],
        "src/mod/util.py": [],
    }

    module_cards = generate_module_cards(file_cards, ast_map, import_map)

    card = module_cards["src/mod"]
    assert card.total_issue_counts["critical"] == 1
    assert card.total_issue_counts["warning"] == 2
    assert card.total_issue_counts["info"] == 1


def test_save_and_load_module_card(tmp_path: Path) -> None:
    """ModuleCard の保存と読み込みのラウンドトリップ。"""
    state_dir = tmp_path / "review-state"
    card = ModuleCard(
        module_name="src/analyzers",
        file_cards=["src/analyzers/__init__.py", "src/analyzers/base.py"],
        total_issue_counts={"critical": 1, "warning": 2, "info": 3},
        boundary_issues=["衝突: parse が複数ファイルに存在"],
    )

    save_module_card(state_dir, card)
    loaded = load_module_card(state_dir, "src/analyzers")

    assert loaded is not None
    assert loaded.module_name == card.module_name
    assert loaded.file_cards == card.file_cards
    assert loaded.total_issue_counts == card.total_issue_counts
    assert loaded.boundary_issues == card.boundary_issues


def test_module_card_to_markdown() -> None:
    """ModuleCard の Markdown 出力が必要なフィールドを含むこと。"""
    card = ModuleCard(
        module_name="src/analyzers",
        file_cards=["src/analyzers/__init__.py", "src/analyzers/base.py"],
        total_issue_counts={"critical": 1, "warning": 2, "info": 0},
        boundary_issues=["衝突: parse が複数ファイルに存在"],
    )

    md = card.to_markdown()

    assert "## src/analyzers" in md
    assert "**ファイル数**" in md
    assert "src/analyzers/__init__.py" in md
    assert "Critical: 1" in md
    assert "Warning: 2" in md
    assert "衝突: parse が複数ファイルに存在" in md


# ===================================================================
# C-2b: Layer 3 システムレビュー
# ===================================================================


class TestDetectCircularDependencies:
    """循環依存検出のテスト。

    設計書 Section 4.5: ast-map.json の import 情報からグラフ構築 → SCC 検出。
    """

    def test_no_cycles_returns_empty(self) -> None:
        """循環がない場合は空リストを返す。"""
        import_map = {
            "a.py": ["b"],
            "b.py": ["c"],
            "c.py": [],
        }
        issues = detect_circular_dependencies(import_map)
        assert issues == []

    def test_simple_cycle_detected(self) -> None:
        """A→B→A の単純な循環を検出する。"""
        import_map = {
            "a.py": ["b"],
            "b.py": ["a"],
        }
        issues = detect_circular_dependencies(import_map)
        assert len(issues) == 1
        assert issues[0].severity == "warning"
        assert issues[0].category == "circular-dependency"
        assert all(f in issues[0].message for f in ["a.py", "b.py"])

    def test_three_node_cycle(self) -> None:
        """A→B→C→A の3ノード循環を検出する。"""
        import_map = {
            "a.py": ["b"],
            "b.py": ["c"],
            "c.py": ["a"],
        }
        issues = detect_circular_dependencies(import_map)
        assert len(issues) == 1
        assert issues[0].severity == "warning"

    def test_multiple_independent_cycles(self) -> None:
        """独立した2つの循環を別々に検出する。"""
        import_map = {
            "a.py": ["b"],
            "b.py": ["a"],
            "c.py": ["d"],
            "d.py": ["c"],
            "e.py": [],
        }
        issues = detect_circular_dependencies(import_map)
        assert len(issues) == 2

    def test_self_import_detected(self) -> None:
        """自己参照（A→A）を検出する。"""
        import_map = {
            "a.py": ["a"],
        }
        issues = detect_circular_dependencies(import_map)
        assert len(issues) == 1

    def test_empty_import_map(self) -> None:
        """空の import_map は空リストを返す。"""
        issues = detect_circular_dependencies({})
        assert issues == []

    def test_issue_fields_populated(self) -> None:
        """Issue の各フィールドが正しく設定されていること。"""
        import_map = {
            "src/foo.py": ["src.bar"],
            "src/bar.py": ["src.foo"],
        }
        issues = detect_circular_dependencies(import_map)
        assert len(issues) == 1
        issue = issues[0]
        assert issue.tool == "card_generator"
        assert issue.rule_id == "circular-dependency"
        assert issue.line == 0


class TestDetectModuleNamingViolations:
    """モジュール横断の命名パターン違反検出のテスト。

    設計書 Section 4.5: snake_case / camelCase の混在をモジュール横断で検出。
    """

    def test_consistent_naming_returns_empty(self) -> None:
        """全てsnake_caseなら空リストを返す。"""
        ast_map: dict[str, ASTNode] = {
            "a.py": _make_module_node([
                _make_function_node("my_func"),
                _make_function_node("another_func", 12, 20),
            ]),
            "b.py": _make_module_node([
                _make_function_node("helper_func"),
            ]),
        }
        issues = detect_module_naming_violations(ast_map)
        assert issues == []

    def test_mixed_naming_detected(self) -> None:
        """snake_case と camelCase の混在を検出する。"""
        ast_map: dict[str, ASTNode] = {
            "a.py": _make_module_node([_make_function_node("my_func")]),
            "b.py": _make_module_node([_make_function_node("myFunc")]),
        }
        issues = detect_module_naming_violations(ast_map)
        assert len(issues) >= 1
        assert issues[0].severity == "warning"
        assert issues[0].category == "naming-violation"

    def test_pascal_case_classes_not_flagged(self) -> None:
        """PascalCase のクラス名は違反としない。"""
        ast_map: dict[str, ASTNode] = {
            "a.py": _make_module_node([
                _make_function_node("my_func"),
                _make_class_node("MyClass"),
            ]),
        }
        issues = detect_module_naming_violations(ast_map)
        assert issues == []

    def test_empty_ast_map(self) -> None:
        """空の ast_map は空リストを返す。"""
        issues = detect_module_naming_violations({})
        assert issues == []


class TestCollectSpecDriftContext:
    """仕様ドリフト検出用コンテキスト収集のテスト。

    設計書 Section 4.5: 要約カード群 + docs/specs/ を LLM に渡す。
    """

    def test_collects_module_cards_and_specs(self, tmp_path: Path) -> None:
        """モジュールカードと仕様書の両方を収集する。"""
        # モジュールカード
        state_dir = tmp_path / "review-state"
        card = ModuleCard(
            module_name="src/core",
            file_cards=["src/core/main.py"],
            total_issue_counts={"critical": 0, "warning": 1, "info": 0},
            boundary_issues=[],
        )
        save_module_card(state_dir, card)

        # 仕様書
        specs_dir = tmp_path / "docs" / "specs"
        specs_dir.mkdir(parents=True)
        (specs_dir / "api-spec.md").write_text("# API Spec\nGET /users returns 200")

        context = collect_spec_drift_context(state_dir, specs_dir)

        assert "src/core" in context
        assert "API Spec" in context
        assert "GET /users" in context

    def test_empty_specs_dir(self, tmp_path: Path) -> None:
        """仕様書が存在しない場合も動作する。"""
        state_dir = tmp_path / "review-state"
        specs_dir = tmp_path / "docs" / "specs"
        specs_dir.mkdir(parents=True)

        context = collect_spec_drift_context(state_dir, specs_dir)

        assert "仕様書" in context or "specs" in context.lower()

    def test_no_module_cards(self, tmp_path: Path) -> None:
        """モジュールカードがない場合も動作する。"""
        state_dir = tmp_path / "review-state"
        specs_dir = tmp_path / "docs" / "specs"
        specs_dir.mkdir(parents=True)
        (specs_dir / "test.md").write_text("# Test Spec")

        context = collect_spec_drift_context(state_dir, specs_dir)

        assert "Test Spec" in context


# ===================================================================
# D-1: 依存グラフ構築 + トポロジカルソート（FR-7a）
# ===================================================================


class TestCondenseSccs:
    """_condense_sccs() のテスト（D-1: FR-7a）。"""

    def test_no_sccs_returns_original_graph(self):
        """SCC がない場合、元のグラフがそのまま返ること。"""
        graph = {"a": ["b"], "b": ["c"], "c": []}
        all_nodes = {"a", "b", "c"}
        sccs = []  # SCC なし
        condensed, scc_map = _condense_sccs(graph, all_nodes, sccs)
        # ノード数は変わらない
        assert set(condensed.keys()) == {"a", "b", "c"}
        assert scc_map == {}

    def test_single_scc_condensed_to_supernode(self):
        """A→B→A の循環が 1 つのスーパーノードに縮約されること。"""
        graph = {"a": ["b"], "b": ["a", "c"], "c": []}
        all_nodes = {"a", "b", "c"}
        sccs = [["a", "b"]]
        condensed, scc_map = _condense_sccs(graph, all_nodes, sccs)
        # スーパーノード名にはSCCメンバーが含まれる
        super_nodes = [k for k in condensed if k.startswith("scc_")]
        assert len(super_nodes) == 1
        # スーパーノードは c への辺を持つ
        assert "c" in condensed[super_nodes[0]]
        # scc_map で元ノードがスーパーノードにマップされている
        assert scc_map["a"] == super_nodes[0]
        assert scc_map["b"] == super_nodes[0]

    def test_multiple_sccs(self):
        """複数の SCC が各々スーパーノードに縮約されること。"""
        graph = {"a": ["b"], "b": ["a"], "c": ["d"], "d": ["c"], "e": []}
        all_nodes = {"a", "b", "c", "d", "e"}
        sccs = [["a", "b"], ["c", "d"]]
        condensed, scc_map = _condense_sccs(graph, all_nodes, sccs)
        super_nodes = [k for k in condensed if k.startswith("scc_")]
        assert len(super_nodes) == 2
        # e は通常ノードとして残る
        assert "e" in condensed


class TestBuildTopoOrder:
    """build_topo_order() のテスト（D-1: FR-7a）。"""

    def test_linear_dependency(self):
        """A→B→C の線形依存が正しいトポロジカル順になること。"""
        import_map = {
            "a.py": ["b"],
            "b.py": ["c"],
            "c.py": [],
        }
        result = build_topo_order(import_map)
        order = result["topo_order"]
        # c が b より前、b が a より前
        assert order.index("c") < order.index("b")
        assert order.index("b") < order.index("a")

    def test_no_dependencies(self):
        """依存なしの場合、全ノードがトポロジカル順に含まれること。"""
        import_map = {
            "x.py": [],
            "y.py": [],
            "z.py": [],
        }
        result = build_topo_order(import_map)
        assert len(result["topo_order"]) == 3
        assert result["sccs"] == []

    def test_with_cycle(self):
        """循環依存がある場合、SCC 縮約後にトポロジカル順が得られること。"""
        import_map = {
            "a.py": ["b"],
            "b.py": ["a"],  # A↔B 循環
            "c.py": ["a"],  # C→A
        }
        result = build_topo_order(import_map)
        assert len(result["topo_order"]) >= 2  # SCC + c
        assert len(result["sccs"]) == 1  # A↔B の SCC

    def test_result_contains_required_keys(self):
        """結果に topo_order, sccs, node_to_file が含まれること。"""
        import_map = {"a.py": []}
        result = build_topo_order(import_map)
        assert "topo_order" in result
        assert "sccs" in result
        assert "node_to_file" in result

    def test_complex_graph_with_multiple_sccs(self):
        """複数SCC + 外部ノードの複合グラフ。"""
        import_map = {
            "a.py": ["b"],
            "b.py": ["a"],       # SCC1: a↔b
            "c.py": ["d"],
            "d.py": ["c"],       # SCC2: c↔d
            "e.py": ["a", "c"],  # e → SCC1, SCC2
        }
        result = build_topo_order(import_map)
        assert len(result["sccs"]) == 2
        order = result["topo_order"]
        assert len(order) >= 3  # SCC1, SCC2, e
