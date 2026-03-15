"""Plan D パイプラインの統合チェーンテスト。

モックデータで関数チェーン全体のデータフローを検証する。
LLM 出力は使用しない（決定的テスト）。

対応タスク: D-5
Plan E 設計ノート参照: docs/tasks/scalable-code-review-tasks.md
"""
from __future__ import annotations

from pathlib import Path

from analyzers.base import ASTNode
from analyzers.card_generator import (
    ContractCard,
    FileCard,
    analyze_impact,
    build_topo_order,
    classify_impact_for_cards,
    load_contract_card,
    merge_contracts,
    parse_contract,
    save_contract_card,
)
from analyzers.chunker import Chunk
from analyzers.orchestrator import (
    build_review_prompt_with_contracts,
    order_chunks_by_topo,
)
from analyzers.state_manager import (
    load_dependency_graph,
    save_dependency_graph,
)


# ---------------------------------------------------------------------------
# テスト用ヘルパー
# ---------------------------------------------------------------------------

MOCK_AGENT_OUTPUT = """\
レビュー結果: 問題なし。

---FILE-CARD-RESPONSIBILITY---
データ変換ユーティリティ
---END-FILE-CARD-RESPONSIBILITY---

---CONTRACT-CARD---
preconditions: [input must be non-empty]
postconditions: [returns valid result]
side_effects: [writes to log]
invariants: [state is consistent]
---END-CONTRACT-CARD---
"""


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


def _make_module_node(children: list[ASTNode]) -> ASTNode:
    return ASTNode(
        name="module",
        kind="module",
        start_line=1,
        end_line=100,
        signature="",
        children=children,
        docstring=None,
    )


def _make_chunk(file_path: str, name: str) -> Chunk:
    return Chunk(
        file_path=file_path,
        start_line=1,
        end_line=10,
        content=f"def {name}():\n    pass\n",
        overlap_header="",
        overlap_footer="",
        token_count=5,
        level="L1",
        node_name=name,
    )


# ---------------------------------------------------------------------------
# テストクラス
# ---------------------------------------------------------------------------


class TestPlanDIntegrationPipeline:
    """Plan D パイプラインの統合チェーンテスト。

    モックデータで関数チェーン全体のデータフローを検証する。
    LLM 出力は使用しない（決定的テスト）。

    対応タスク: D-5
    Plan E 設計ノート参照: docs/tasks/scalable-code-review-tasks.md
    """

    def test_topo_order_to_chunk_ordering(self) -> None:
        """build_topo_order → order_chunks_by_topo のチェーン。

        3ファイル（A→B→C）の依存関係で:
        1. build_topo_order が正しいトポロジカル順を返し
        2. order_chunks_by_topo がその順序でチャンクをグループ化する
        """
        # A→B→C の依存関係（A は B を import、B は C を import）
        import_map = {
            "src/a.py": ["src.b"],
            "src/b.py": ["src.c"],
            "src/c.py": [],
        }

        result = build_topo_order(import_map)
        topo_order = result["topo_order"]
        node_to_file = result["node_to_file"]
        sccs = result["sccs"]

        # 各チャンクを作成
        chunks = [
            _make_chunk("src/a.py", "func_a"),
            _make_chunk("src/b.py", "func_b"),
            _make_chunk("src/c.py", "func_c"),
        ]

        groups = order_chunks_by_topo(chunks, topo_order, node_to_file, sccs)

        # 3グループになること
        assert len(groups) == 3

        # グループは C→B→A の順（C が最上流 = 依存されていない側）
        all_files_in_order = [g[0].file_path for g in groups]
        # C は A, B の前に来る（C を誰も import していない）
        c_idx = all_files_in_order.index("src/c.py")
        b_idx = all_files_in_order.index("src/b.py")
        a_idx = all_files_in_order.index("src/a.py")
        assert c_idx < b_idx < a_idx

    def test_contract_card_roundtrip_through_pipeline(self, tmp_path: Path) -> None:
        """parse_contract → merge_contracts → save → load のチェーン。

        モック Agent 出力（マーカー付き契約フィールド）を入力として:
        1. parse_contract で抽出
        2. merge_contracts でモジュール集約
        3. save_contract_card で永続化
        4. load_contract_card で復元
        5. 元データと一致を確認
        """
        # 1. parse_contract でフィールド抽出
        contract_fields = parse_contract(MOCK_AGENT_OUTPUT)

        assert contract_fields["preconditions"] == ["input must be non-empty"]
        assert contract_fields["postconditions"] == ["returns valid result"]
        assert contract_fields["side_effects"] == ["writes to log"]
        assert contract_fields["invariants"] == ["state is consistent"]

        # 2. merge_contracts でモジュール集約
        # テスト用 FileCard と AST を構築
        file_node = _make_module_node([_make_function_node("transform")])
        ast_map = {"src/utils.py": file_node}
        file_cards = {
            "src/utils.py": FileCard(
                file_path="src/utils.py",
                public_api=["transform"],
                dependencies=[],
                dependents=[],
                issue_counts={"critical": 0, "warning": 0, "info": 0},
                responsibility="",
            )
        }
        module_to_files = {"src": ["src/utils.py"]}
        contract_fields_map = {"src": contract_fields}

        contracts = merge_contracts(file_cards, contract_fields_map, module_to_files, ast_map)

        assert "src" in contracts
        card = contracts["src"]
        assert card.module_name == "src"
        assert card.preconditions == ["input must be non-empty"]
        assert card.postconditions == ["returns valid result"]

        # 3. save_contract_card で永続化
        state_dir = tmp_path / "review-state"
        save_contract_card(state_dir, card)

        # 4. load_contract_card で復元
        loaded = load_contract_card(state_dir, "src")

        # 5. 元データと一致を確認
        assert loaded is not None
        assert loaded.module_name == card.module_name
        assert loaded.preconditions == card.preconditions
        assert loaded.postconditions == card.postconditions
        assert loaded.side_effects == card.side_effects
        assert loaded.invariants == card.invariants

    def test_topo_review_with_contract_injection(self) -> None:
        """トポロジカル順レビュー + 契約カード注入の統合テスト。

        A→B の依存関係で:
        1. A のレビュープロンプトには契約カードなし（上流なし）
        2. A の Agent 出力から契約カードを parse
        3. B のレビュープロンプトに A の契約カードが含まれる
        """
        import_map = {
            "src/a.py": [],         # A は誰も import しない（最上流）
            "src/b.py": ["src.a"],  # B は A を import
        }

        result = build_topo_order(import_map)
        topo_order = result["topo_order"]
        node_to_file = result["node_to_file"]
        sccs = result["sccs"]

        chunks = [
            _make_chunk("src/a.py", "func_a"),
            _make_chunk("src/b.py", "func_b"),
        ]

        groups = order_chunks_by_topo(chunks, topo_order, node_to_file, sccs)
        assert len(groups) == 2

        # 1. A のレビュープロンプトには契約カードなし
        a_chunk = groups[0][0]
        a_prompt_no_contract = build_review_prompt_with_contracts(a_chunk, [])
        assert "---CONTRACT-CARD---" not in a_prompt_no_contract

        # 2. A の Agent 出力から契約カードを parse
        contract_fields = parse_contract(MOCK_AGENT_OUTPUT)
        a_contract = ContractCard(
            module_name="src.a",
            public_api=["func_a"],
            signatures=["def func_a():"],
            preconditions=contract_fields.get("preconditions", []),
            postconditions=contract_fields.get("postconditions", []),
            side_effects=contract_fields.get("side_effects", []),
            invariants=contract_fields.get("invariants", []),
        )

        # 3. B のレビュープロンプトに A の契約カードが含まれる
        b_chunk = groups[1][0]
        b_prompt = build_review_prompt_with_contracts(b_chunk, [a_contract])

        assert "---CONTRACT-CARD---" in b_prompt
        assert "---END-CONTRACT-CARD---" in b_prompt
        assert "src.a" in b_prompt
        # B 自身の内容も含まれること
        assert "src/b.py" in b_prompt

    def test_impact_analysis_with_graph(self) -> None:
        """build_topo_order → analyze_impact のチェーン。

        A→B→C の依存関係で C を修正:
        1. build_topo_order でグラフ構築
        2. analyze_impact で影響範囲計算
        3. A, B, C が in_scope
        """
        import_map = {
            "src/a.py": ["src.b"],
            "src/b.py": ["src.c"],
            "src/c.py": [],
        }

        # build_topo_order でグラフ情報を取得
        topo_result = build_topo_order(import_map)
        assert len(topo_result["topo_order"]) == 3

        # C を修正した場合の影響範囲計算
        impact = analyze_impact(["src/c.py"], import_map)

        in_scope = impact["in_scope"]
        # C が修正されると A, B も影響を受ける
        assert "src/c.py" in in_scope
        assert "src/b.py" in in_scope
        assert "src/a.py" in in_scope

    def test_impact_classify_with_hashes(self, tmp_path: Path) -> None:
        """analyze_impact → classify_impact_for_cards のチェーン。

        影響範囲分析結果 + ファイルハッシュ情報から:
        1. in_scope ファイルは regenerate
        2. out_of_scope かつハッシュ未変更は reuse_mechanical
        """
        import_map = {
            "src/a.py": ["src.b"],
            "src/b.py": [],
            "src/c.py": [],  # A, B とは独立
        }

        # B を修正した場合
        impact = analyze_impact(["src/b.py"], import_map)
        in_scope = impact["in_scope"]
        out_of_scope = impact["out_of_scope"]

        # B が修正されると A も影響範囲
        assert "src/b.py" in in_scope
        assert "src/a.py" in in_scope
        # C は影響なし
        assert "src/c.py" in out_of_scope

        # ハッシュ情報
        current_hashes = {
            "src/a.py": "hash_a",
            "src/b.py": "hash_b_new",
            "src/c.py": "hash_c_same",
        }
        previous_hashes = {
            "src/a.py": "hash_a_old",
            "src/b.py": "hash_b_old",
            "src/c.py": "hash_c_same",
        }

        classify = classify_impact_for_cards(in_scope, out_of_scope, current_hashes, previous_hashes)

        # in_scope は全て regenerate
        assert classify["src/a.py"] == "regenerate"
        assert classify["src/b.py"] == "regenerate"
        # C は out_of_scope かつハッシュ未変更 → reuse_mechanical
        assert classify["src/c.py"] == "reuse_mechanical"

    def test_full_pipeline_e2e(self, tmp_path: Path) -> None:
        """Plan D パイプライン全体の end-to-end テスト。

        3ファイル（A→B→C, D は独立）で:
        1. build_topo_order でグラフ構築・永続化
        2. order_chunks_by_topo でチャンク順序付け
        3. build_review_prompt_with_contracts で各チャンクのプロンプト生成
        4. parse_contract でモック契約フィールド抽出
        5. merge_contracts でモジュール集約
        6. save/load_contract_card で永続化ラウンドトリップ
        7. analyze_impact で C 修正時の影響範囲計算
        8. classify_impact_for_cards で再利用判定
        全ステップが連鎖的にデータを受け渡し、最終結果が期待値と一致すること
        """
        # --- 依存関係の定義 ---
        # A→B→C の線形チェーン + D は独立
        import_map = {
            "src/a.py": ["src.b"],
            "src/b.py": ["src.c"],
            "src/c.py": [],
            "src/d.py": [],
        }

        # Step 1: build_topo_order でグラフ構築
        topo_result = build_topo_order(import_map)
        topo_order = topo_result["topo_order"]
        node_to_file = topo_result["node_to_file"]
        sccs = topo_result["sccs"]

        assert len(topo_order) == 4  # A, B, C, D の 4 ノード

        # Step 1b: 依存グラフを永続化
        state_dir = tmp_path / "review-state"
        save_dependency_graph(state_dir, topo_result)
        loaded_graph = load_dependency_graph(state_dir)
        assert set(loaded_graph["topo_order"]) == set(topo_order)

        # Step 2: order_chunks_by_topo でチャンク順序付け
        chunks = [
            _make_chunk("src/a.py", "func_a"),
            _make_chunk("src/b.py", "func_b"),
            _make_chunk("src/c.py", "func_c"),
            _make_chunk("src/d.py", "func_d"),
        ]
        groups = order_chunks_by_topo(chunks, topo_order, node_to_file, sccs)

        # 4グループになること（A, B, C, D 各1グループ）
        assert len(groups) == 4

        # Step 3: 最初のグループ（最上流）のプロンプト生成（契約なし）
        first_chunk = groups[0][0]
        prompt_no_contract = build_review_prompt_with_contracts(first_chunk, [])
        assert "---CONTRACT-CARD---" not in prompt_no_contract

        # Step 4: parse_contract でモック契約フィールド抽出
        contract_fields = parse_contract(MOCK_AGENT_OUTPUT)
        assert "preconditions" in contract_fields
        assert "postconditions" in contract_fields

        # Step 5: merge_contracts でモジュール集約
        # C ファイルの FileCard と AST を構築
        c_node = _make_module_node([_make_function_node("func_c")])
        ast_map = {
            "src/a.py": _make_module_node([_make_function_node("func_a")]),
            "src/b.py": _make_module_node([_make_function_node("func_b")]),
            "src/c.py": c_node,
            "src/d.py": _make_module_node([_make_function_node("func_d")]),
        }
        # ファイル名（拡張子なし）から関数名を導出: "src/a.py" → "func_a"
        def _func_name_for(file_path: str) -> str:
            stem = file_path.split("/")[-1].removesuffix(".py")
            return f"func_{stem}"

        file_cards = {
            fp: FileCard(
                file_path=fp,
                public_api=[_func_name_for(fp)],
                dependencies=list(import_map[fp]),
                dependents=[],
                issue_counts={"critical": 0, "warning": 0, "info": 0},
                responsibility="",
            )
            for fp in import_map
        }
        module_to_files = {"src": list(import_map.keys())}
        contract_fields_map = {"src": contract_fields}

        contracts = merge_contracts(file_cards, contract_fields_map, module_to_files, ast_map)
        assert "src" in contracts
        src_contract = contracts["src"]
        assert src_contract.preconditions == ["input must be non-empty"]

        # Step 6: save_contract_card / load_contract_card ラウンドトリップ
        save_contract_card(state_dir, src_contract)
        loaded_contract = load_contract_card(state_dir, "src")
        assert loaded_contract is not None
        assert loaded_contract.preconditions == src_contract.preconditions
        assert loaded_contract.postconditions == src_contract.postconditions

        # Step 7: analyze_impact で C 修正時の影響範囲計算
        impact = analyze_impact(["src/c.py"], import_map)
        in_scope = impact["in_scope"]
        out_of_scope = impact["out_of_scope"]

        assert "src/c.py" in in_scope
        assert "src/b.py" in in_scope
        assert "src/a.py" in in_scope
        assert "src/d.py" in out_of_scope  # D は独立

        # Step 8: classify_impact_for_cards で再利用判定
        current_hashes = {
            "src/a.py": "hash_a_new",
            "src/b.py": "hash_b_new",
            "src/c.py": "hash_c_new",
            "src/d.py": "hash_d_same",  # D はハッシュ変更なし
        }
        previous_hashes = {
            "src/a.py": "hash_a_old",
            "src/b.py": "hash_b_old",
            "src/c.py": "hash_c_old",
            "src/d.py": "hash_d_same",  # D は変更なし
        }

        classify = classify_impact_for_cards(in_scope, out_of_scope, current_hashes, previous_hashes)

        # in_scope は全て regenerate
        assert classify["src/a.py"] == "regenerate"
        assert classify["src/b.py"] == "regenerate"
        assert classify["src/c.py"] == "regenerate"
        # D は out_of_scope かつハッシュ未変更 → reuse_mechanical
        assert classify["src/d.py"] == "reuse_mechanical"
