"""概要カード生成エンジン。

Task C-1a: 概要カード生成エンジン（機械的フィールド）
Task C-1b: Phase 2 Agent プロンプト拡張（責務フィールド生成）
Task C-2a: Layer 2 モジュール統合（要約カード生成）
Task C-2b: Layer 3 システムレビュー（循環依存検出、命名パターン違反）
Task D-1: 依存グラフ構築 + トポロジカルソート（FR-7a）
Task D-2: 契約カード生成（FR-7c）
対応仕様: scalable-code-review-spec.md FR-4, FR-7a, FR-7c
対応設計: scalable-code-review-design.md Section 4.3, 4.4, 4.5, 5.3
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

# Task ⑤ 後方互換: グラフ解析・影響範囲分析関連シンボルは
# analyzers.graph.scc / analyzers.analysis.impact が SSOT。
# 既存テスト / 呼び出し側の `from analyzers.card_generator import ...` を維持するため、
# 本モジュールから re-export する。`as` 形式は PEP 484 explicit re-export
# として静的解析（ruff F401 等）に認識される。
from analyzers.analysis.impact import (
    _bfs_upstream as _bfs_upstream,
    _build_reverse_graph as _build_reverse_graph,
    _expand_scc_members as _expand_scc_members,
    _partition_files_by_scope as _partition_files_by_scope,
    analyze_impact as analyze_impact,
    classify_impact_for_cards as classify_impact_for_cards,
)
from analyzers.base import ASTNode, Issue, file_path_to_module_name
from analyzers.graph.scc import (
    SccDetectionSkippedError as SccDetectionSkippedError,
    TopoOrderResult as TopoOrderResult,
    _build_import_graph as _build_import_graph,
    _collect_supernode_edges as _collect_supernode_edges,
    _condense_sccs as _condense_sccs,
    _find_sccs as _find_sccs,
    _resolve_node_edges as _resolve_node_edges,
    build_topo_order as build_topo_order,
    detect_circular_dependencies as detect_circular_dependencies,
)
from analyzers.reducer import classify_name

logger = logging.getLogger(__name__)

_CARDS_DIR = "cards"
_FILE_CARDS_DIR = "file-cards"
_MODULE_CARDS_DIR = "module-cards"
_CONTRACTS_DIR = "contracts"


@dataclass
class FileCard:
    """ファイル概要カード。

    設計書 Section 4.3 に対応。
    機械的フィールド（C-1a）と LLM 生成フィールド（C-1b）を持つ。
    """

    file_path: str
    public_api: list[str]
    dependencies: list[str]
    dependents: list[str]
    issue_counts: dict[str, int]
    responsibility: str

    def to_markdown(self) -> str:
        """設計書 Section 4.3 の形式で Markdown を出力する。"""
        api_str = ", ".join(self.public_api) if self.public_api else "(なし)"
        deps_str = ", ".join(self.dependencies) if self.dependencies else "(なし)"
        depts_str = ", ".join(self.dependents) if self.dependents else "(なし)"
        counts = self.issue_counts
        issue_str = (
            f"Critical: {counts.get('critical', 0)}"
            f" / Warning: {counts.get('warning', 0)}"
            f" / Info: {counts.get('info', 0)}"
        )
        return (
            f"## {self.file_path}\n"
            f"- **責務**: {self.responsibility or '(未生成)'}\n"
            f"- **公開 API**: {api_str}\n"
            f"- **依存先**: {deps_str}\n"
            f"- **依存元**: {depts_str}\n"
            f"- **Issue 数**: {issue_str}\n"
        )


@dataclass
class ModuleCard:
    """モジュール（ディレクトリ）単位の要約カード。

    設計書 Section 4.4 に対応。
    複数 FileCard を集約し、モジュール境界チェック結果を保持する。
    """

    module_name: str
    file_cards: list[str]
    total_issue_counts: dict[str, int]
    boundary_issues: list[str]

    def to_markdown(self) -> str:
        """設計書 Section 4.4 の形式で Markdown を出力する。"""
        counts = self.total_issue_counts
        issue_str = (
            f"Critical: {counts.get('critical', 0)}"
            f" / Warning: {counts.get('warning', 0)}"
            f" / Info: {counts.get('info', 0)}"
        )
        file_list = "\n".join(f"  - {f}" for f in self.file_cards)
        boundary_list = (
            "\n".join(f"  - {b}" for b in self.boundary_issues)
            if self.boundary_issues
            else "  (なし)"
        )
        return (
            f"## {self.module_name}\n"
            f"- **ファイル数**: {len(self.file_cards)}\n"
            f"{file_list}\n"
            f"- **Issue 数**: {issue_str}\n"
            f"- **境界チェック**:\n{boundary_list}\n"
        )


@dataclass
class ContractCard:
    """モジュール単位の契約カード。

    設計書 Section 5.3 に対応。
    機械的フィールド（public_api, signatures）と LLM 推論フィールドを持つ。
    """

    module_name: str
    public_api: list[str]       # 機械的（FileCard から流用）
    signatures: list[str]       # 機械的（AST の signature フィールド）
    preconditions: list[str]    # LLM 推論
    postconditions: list[str]   # LLM 推論
    side_effects: list[str]     # LLM 推論
    invariants: list[str]       # LLM 推論


def _build_reverse_import_map(
    ast_map: dict[str, ASTNode],
    import_map: dict[str, list[str]],
) -> dict[str, list[str]]:
    """import_map を逆引きし、各ファイルの依存元を構築する。

    import_map の値はドット区切りモジュール名（例: "src.foo"）で、
    ast_map のキーはパス形式（例: "src/foo.py"）なので変換が必要。
    """
    # ファイルパス → モジュール名の対応表
    path_to_module = {fp: file_path_to_module_name(fp) for fp in ast_map}
    module_to_path = {mod: fp for fp, mod in path_to_module.items()}

    dependents: dict[str, list[str]] = {fp: [] for fp in ast_map}

    for importer_path, imports in import_map.items():
        for imported_module in imports:
            target_path = module_to_path.get(imported_module)
            if target_path is not None and target_path != importer_path:
                dependents[target_path].append(importer_path)

    return dependents


def _count_issues_by_file(
    issues: list[Issue],
    chunk_issues: dict[str, list[Issue]],
    file_path: str,
) -> dict[str, int]:
    """static-issues + chunk-results から特定ファイルの Issue 数を集計する。"""
    counts = {"critical": 0, "warning": 0, "info": 0}

    for issue in issues:
        if issue.file == file_path and issue.severity in counts:
            counts[issue.severity] += 1

    for issue in chunk_issues.get(file_path, []):
        if issue.severity in counts:
            counts[issue.severity] += 1

    return counts


def generate_file_cards(
    ast_map: dict[str, ASTNode],
    import_map: dict[str, list[str]],
    issues: list[Issue],
    chunk_issues: dict[str, list[Issue]],
) -> dict[str, FileCard]:
    """全ファイルの概要カードを生成する。"""
    reverse_map = _build_reverse_import_map(ast_map, import_map)
    cards: dict[str, FileCard] = {}

    for file_path, root_node in ast_map.items():
        # 公開 API: トップレベル children の関数/クラス名
        public_api = [
            child.name
            for child in root_node.children
            if child.kind in ("function", "class")
        ]

        # 依存先: import_map から取得
        dependencies = list(import_map.get(file_path, []))

        # 依存元: 逆引き
        dependents = reverse_map.get(file_path, [])

        # Issue 数
        issue_counts = _count_issues_by_file(issues, chunk_issues, file_path)

        cards[file_path] = FileCard(
            file_path=file_path,
            public_api=public_api,
            dependencies=dependencies,
            dependents=dependents,
            issue_counts=issue_counts,
            responsibility="",
        )

    return cards


def _card_filename(file_path: str) -> str:
    """ファイルパスからカードのファイル名を生成する。

    設計書 Section 4.6: パスの / を - に置換。
    """
    return file_path.replace("/", "-").replace("\\", "-").replace(".", "-") + ".json"


def _write_card_file(path: Path, data: dict, *, label: str) -> None:
    """カードデータを path に JSON で書き込む（save_* 共通）。

    state_manager._write_json_file と同じ信頼性設計：書き込み失敗（OSError）でも
    パイプライン全体を停止させず、warning ログに記録して継続する。
    """
    try:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError as e:
        logger.warning("Failed to save %s to %s: %s", label, path, e)


def save_file_card(state_dir: Path, card: FileCard) -> None:
    """概要カードを review-state/cards/file-cards/ に永続化する。"""
    cards_dir = state_dir / _CARDS_DIR / _FILE_CARDS_DIR
    cards_dir.mkdir(parents=True, exist_ok=True)

    filename = _card_filename(card.file_path)
    _write_card_file(cards_dir / filename, asdict(card), label="file card")


def load_file_card(state_dir: Path, file_path: str) -> FileCard | None:
    """概要カードを読み込む。"""
    cards_dir = state_dir / _CARDS_DIR / _FILE_CARDS_DIR
    filename = _card_filename(file_path)
    path = cards_dir / filename

    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("Corrupted file card: %s", path)
        return None

    return FileCard(**data)


# ============================================================
# C-1b: 責務フィールドのパース・マージ
# ============================================================

_RESPONSIBILITY_START = "---FILE-CARD-RESPONSIBILITY---"
_RESPONSIBILITY_END = "---END-FILE-CARD-RESPONSIBILITY---"


def parse_responsibility(agent_output: str) -> str:
    """Agent 出力から責務フィールドを抽出する。

    マーカー間のテキストを返す。マーカーがない場合は空文字を返す。
    """
    start_idx = agent_output.find(_RESPONSIBILITY_START)
    if start_idx == -1:
        return ""
    end_idx = agent_output.find(_RESPONSIBILITY_END, start_idx)
    if end_idx == -1:
        return ""
    content = agent_output[start_idx + len(_RESPONSIBILITY_START) : end_idx]
    return content.strip()


def merge_responsibilities(
    cards: dict[str, FileCard],
    responsibilities: dict[str, str],
) -> None:
    """責務マップに基づいて FileCard の responsibility を更新する。

    空文字の責務では既存値を上書きしない。
    """
    for file_path, responsibility in responsibilities.items():
        if file_path in cards and responsibility:
            cards[file_path].responsibility = responsibility


# ============================================================
# D-2: 契約カード生成（FR-7c）
# ============================================================

_CONTRACT_START = "---CONTRACT-CARD---"
_CONTRACT_END = "---END-CONTRACT-CARD---"

_CONTRACT_FIELDS = ("preconditions", "postconditions", "side_effects", "invariants")


def _parse_contract_list(value: str) -> list[str]:
    """'[item1, item2]' 形式の文字列をリストに変換する。

    前後のブラケットを除去して各要素を strip する。
    """
    value = value.strip()
    if value.startswith("["):
        value = value[1:]
    if value.endswith("]"):
        value = value[:-1]
    if not value.strip():
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_contract(agent_output: str) -> dict[str, list[str]]:
    """Agent 出力から CONTRACT-CARD マーカー間のフィールドを抽出する。

    マーカーがない場合は空辞書を返す（フォールバック）。
    各フィールドは 'field_name: [item1, item2]' 形式。
    """
    start_idx = agent_output.find(_CONTRACT_START)
    if start_idx == -1:
        return {}
    end_idx = agent_output.find(_CONTRACT_END, start_idx)
    if end_idx == -1:
        return {}

    content = agent_output[start_idx + len(_CONTRACT_START) : end_idx]
    result: dict[str, list[str]] = {}
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        for field in _CONTRACT_FIELDS:
            prefix = field + ":"
            if line.startswith(prefix):
                value = line[len(prefix):].strip()
                result[field] = _parse_contract_list(value)
                break
    return result


# ---------------------------------------------------------------------------
# Blame Hint parsing (cross-module-blame FR-2c)
# ---------------------------------------------------------------------------

_BLAME_START = "---BLAME-HINT---"
_BLAME_END = "---END-BLAME-HINT---"
_BLAME_FIELDS = ("issue", "suspected_responsible", "module", "reason")
_VALID_RESPONSIBLE = frozenset({"upstream", "downstream", "spec_ambiguity", "unknown"})

BlameHint = dict[str, str]


def parse_blame_hint(agent_output: str) -> list[BlameHint]:
    """Agent 出力から BLAME-HINT マーカー間のフィールドを抽出する。

    複数の BLAME-HINT ブロックに対応。
    マーカーがない場合は空リストを返す（フォールバック）。
    """
    hints: list[BlameHint] = []
    search_start = 0

    while True:
        start_idx = agent_output.find(_BLAME_START, search_start)
        if start_idx == -1:
            break
        end_idx = agent_output.find(_BLAME_END, start_idx)
        if end_idx == -1:
            search_start = start_idx + len(_BLAME_START)
            continue

        content = agent_output[start_idx + len(_BLAME_START) : end_idx]
        hint: BlameHint = {}
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            for field in _BLAME_FIELDS:
                prefix = field + ":"
                if line.startswith(prefix):
                    hint[field] = line[len(prefix) :].strip()
                    break

        if hint:
            responsible = hint.get("suspected_responsible", "")
            if responsible and responsible not in _VALID_RESPONSIBLE:
                hint["suspected_responsible"] = "unknown"
            hints.append(hint)

        search_start = end_idx + len(_BLAME_END)

    return hints


def _collect_signatures_for_files(
    file_paths: list[str],
    ast_map: dict[str, ASTNode],
) -> list[str]:
    """指定ファイル群のトップレベルノードの signature を収集する。"""
    signatures: list[str] = []
    for fp in file_paths:
        node = ast_map.get(fp)
        if node is None:
            continue
        for child in node.children:
            if child.kind in ("function", "class") and child.signature:
                signatures.append(child.signature)
    return signatures


def merge_contracts(
    file_cards: dict[str, FileCard],
    contract_fields: dict[str, dict],
    module_to_files: dict[str, list[str]],
    ast_map: dict[str, ASTNode],
) -> dict[str, ContractCard]:
    """FileCard 群と契約フィールドをモジュール単位に集約して ContractCard を生成する。

    Args:
        file_cards: ファイルパス → FileCard の辞書。
        contract_fields: モジュール名 → parse_contract() の返り値の辞書。
        module_to_files: detect_module_boundaries() の出力。
        ast_map: ファイルパス → ASTNode の辞書。

    Returns:
        モジュール名 → ContractCard の辞書。
    """
    result: dict[str, ContractCard] = {}

    for module_name, module_files in module_to_files.items():
        # public_api: モジュール内の全 FileCard から集約
        public_api: list[str] = []
        for fp in module_files:
            card = file_cards.get(fp)
            if card is not None:
                for name in card.public_api:
                    if name not in public_api:
                        public_api.append(name)

        # signatures: AST の signature フィールドから収集
        signatures = _collect_signatures_for_files(module_files, ast_map)

        # LLM 推論フィールド: contract_fields から取得（なければ空リスト）
        fields = contract_fields.get(module_name, {})
        result[module_name] = ContractCard(
            module_name=module_name,
            public_api=public_api,
            signatures=signatures,
            preconditions=fields.get("preconditions", []),
            postconditions=fields.get("postconditions", []),
            side_effects=fields.get("side_effects", []),
            invariants=fields.get("invariants", []),
        )

    return result


def _contract_card_filename(module_name: str) -> str:
    """モジュール名から契約カードのファイル名を生成する。

    設計書 Section 4.6: パスの / を - に置換。
    """
    return module_name.replace("/", "-") + ".json"


def save_contract_card(state_dir: Path, card: ContractCard) -> None:
    """契約カードを review-state/contracts/ に永続化する。"""
    contracts_dir = state_dir / _CONTRACTS_DIR
    contracts_dir.mkdir(parents=True, exist_ok=True)

    filename = _contract_card_filename(card.module_name)
    _write_card_file(contracts_dir / filename, asdict(card), label="contract card")


def format_contract_cards_for_prompt(contracts: list[ContractCard]) -> str:
    """契約カードリストを Agent プロンプトに埋め込むための文字列に整形する。

    JSON 形式で出力する。空リストの場合は空文字列を返す。
    設計書 Section 5.2: 上流契約カードをコンテキストとして注入する。
    """
    if not contracts:
        return ""

    parts: list[str] = []
    for card in contracts:
        card_json = json.dumps(asdict(card), ensure_ascii=False, indent=2)
        parts.append(f"---CONTRACT-CARD---\n{card_json}\n---END-CONTRACT-CARD---")

    return "\n\n".join(parts)


def load_contract_card(state_dir: Path, module_name: str) -> ContractCard | None:
    """契約カードを読み込む。存在しない場合は None を返す。"""
    contracts_dir = state_dir / _CONTRACTS_DIR
    filename = _contract_card_filename(module_name)
    path = contracts_dir / filename

    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("Corrupted contract card: %s", path)
        return None

    return ContractCard(**data)


# ============================================================
# C-2a: Layer 2 モジュール統合（要約カード生成）
# ============================================================


def _collect_module_dirs(file_paths: list[str]) -> set[str]:
    """__init__.py または package.json があるディレクトリを収集する。

    ファイルシステムにアクセスせず、file_paths リストの内容だけで判定する。
    """
    module_dirs: set[str] = set()
    for fp in file_paths:
        basename = fp.split("/")[-1]
        if basename in ("__init__.py", "package.json"):
            parent = "/".join(fp.split("/")[:-1])
            if parent:
                module_dirs.add(parent)
    return module_dirs


def _resolve_effective_modules(
    file_paths: list[str],
    module_dirs: set[str],
) -> set[str]:
    """有効なモジュールディレクトリセットを返す。

    module_dirs が非空であればそのまま返す。
    空の場合はファイルパスからディレクトリ単位のフォールバックセットを構築する。
    """
    if module_dirs:
        return module_dirs
    effective: set[str] = set()
    for fp in file_paths:
        parts = fp.split("/")
        if len(parts) > 1:
            effective.add("/".join(parts[:-1]))
    return effective


def _assign_files_to_modules(
    file_paths: list[str],
    module_dirs: set[str],
) -> dict[str, list[str]]:
    """各ファイルをモジュールディレクトリに分類する。

    各ファイルは最も深くマッチするモジュールディレクトリに割り当てられる。
    module_dirs が空の場合はディレクトリ単位にフォールバックする。
    """
    effective_modules = _resolve_effective_modules(file_paths, module_dirs)

    result: dict[str, list[str]] = {m: [] for m in effective_modules}

    for fp in file_paths:
        parts = fp.split("/")
        if len(parts) <= 1:
            # ルート直下ファイルはディレクトリなし → スキップ
            continue

        file_dir = "/".join(parts[:-1])

        # 最も深くマッチするモジュールディレクトリへ割り当てる
        matched_module = None
        best_depth = -1
        for mod_dir in effective_modules:
            if file_dir == mod_dir or file_dir.startswith(mod_dir + "/"):
                depth = mod_dir.count("/")
                if depth > best_depth:
                    best_depth = depth
                    matched_module = mod_dir

        if matched_module is not None:
            result[matched_module].append(fp)

    return result


def detect_module_boundaries(
    file_paths: list[str],
) -> dict[str, list[str]]:
    """ファイルパス群からモジュール境界を検出する。

    設計書 Section 4.4 + 仕様 FR-4 に基づく判定ルール:
    - Python: __init__.py が存在するディレクトリ → そのディレクトリがモジュール
    - JavaScript/TS: package.json が存在するディレクトリ → そのディレクトリがモジュール
    - どちらもない場合: ディレクトリ単位にフォールバック

    注意: ファイルシステムにアクセスせず、file_paths リストの内容だけで判定する。
    つまり file_paths に "src/analyzers/__init__.py" が含まれていれば
    "src/analyzers" がモジュールと判定される。

    入力規約: file_paths は POSIX 形式（/ 区切り）であること。以降の処理は
    split("/") に依存するため、Windows の \\ 区切りが混入すると分割に失敗し
    モジュール検出が崩壊する。防御的に入口で正規化する。
    """
    file_paths = [fp.replace("\\", "/") for fp in file_paths]
    module_dirs = _collect_module_dirs(file_paths)
    result = _assign_files_to_modules(file_paths, module_dirs)
    # 空のモジュールを除去
    return {k: v for k, v in result.items() if v}


def check_all_exports(
    module_files: list[str],
    ast_map: dict[str, ASTNode],
) -> list[str]:
    """__init__.py の公開 API と他ファイルの公開 API の乖離チェック。

    __init__.py がない場合は空リストを返す（チェック不要）。
    ast_map ベースの近似チェック（C-2a スコープ）。
    """
    init_files = [f for f in module_files if f.endswith("__init__.py")]
    if not init_files:
        return []

    issues: list[str] = []
    init_file = init_files[0]
    init_node = ast_map.get(init_file)
    if init_node is None:
        return []

    init_api = {
        child.name
        for child in init_node.children
        if child.kind in ("function", "class")
    }

    # 他ファイルの公開 API を収集
    for fp in module_files:
        if fp == init_file:
            continue
        node = ast_map.get(fp)
        if node is None:
            continue
        for child in node.children:
            if child.kind in ("function", "class") and child.name not in init_api:
                if init_api:  # __init__ に定義があるのに漏れているケース
                    issues.append(
                        f"{child.name} は {fp} に定義されているが __init__.py に公開されていない",
                    )

    return issues


def check_unused_reexports(
    module_files: list[str],
    _ast_map: dict[str, ASTNode],
    import_map: dict[str, list[str]],
) -> list[str]:
    """__init__.py で re-export しているが使われていないシンボルのチェック。

    _ast_map は将来の __all__ 解析拡張用（C-2a では未使用）。

    既知の制限:
    - import_map のキーはファイルパス形式（例: "src/__init__.py"）、
      値はドット区切りモジュール名（例: ["src.foo"]）。
      init_module_candidates にはドット区切り形式とパス形式の両候補を生成しているが、
      all_other_imports（import_map の値）はドット区切りのみのため、
      パス形式の候補（例: "src/core"）は実際にはマッチしない（無効な余剰候補）。
      ただしドット区切り形式の候補が正しくマッチするため、機能上の偽陰性は生じない。
    - 深いパスや動的 import、条件付き import による検出漏れは Phase 3 以降で対応予定。
    """
    init_files = [f for f in module_files if f.endswith("__init__.py")]
    if not init_files:
        return []

    init_file = init_files[0]
    init_imports = import_map.get(init_file, [])
    if not init_imports:
        return []

    # __init__ 以外のファイルが import しているモジュールを収集
    all_other_imports: set[str] = set()
    for fp, imports in import_map.items():
        if fp == init_file:
            continue
        all_other_imports.update(imports)

    # __init__ が import しているが誰にも使われていないものを検出
    # ここでは __init__ を含むモジュール名（ドット区切り）での参照を確認
    init_dir = "/".join(init_file.split("/")[:-1])
    # __init__ を指すモジュール名の候補を作成
    init_module_candidates = {
        init_dir.replace("/", "."),  # "src" → "src"
        init_dir,  # パス表記でも
    }

    issues: list[str] = []
    # __init__ 自身が誰にも import されていない場合、re-export は使われていない
    init_is_used = bool(init_module_candidates & all_other_imports)

    if not init_is_used:
        for imported in init_imports:
            issues.append(
                f"__init__.py で re-export している '{imported}' は誰にも使われていない",
            )

    return issues


def check_name_collisions(
    module_files: list[str],
    ast_map: dict[str, ASTNode],
) -> list[str]:
    """モジュール内のファイル間で同名の関数/クラスが衝突していないかチェック。"""
    # 各ファイルのトップレベル公開 API 名を収集
    name_to_files: dict[str, list[str]] = {}
    for fp in module_files:
        node = ast_map.get(fp)
        if node is None:
            continue
        for child in node.children:
            if child.kind in ("function", "class"):
                name_to_files.setdefault(child.name, []).append(fp)

    issues: list[str] = []
    for name, files in name_to_files.items():
        if len(files) > 1:
            files_str = ", ".join(files)
            issues.append(
                f"名前衝突: '{name}' が複数ファイルに定義されている ({files_str})",
            )

    return issues


def generate_module_cards(
    file_cards: dict[str, FileCard],
    ast_map: dict[str, ASTNode],
    import_map: dict[str, list[str]],
) -> dict[str, ModuleCard]:
    """概要カード群からモジュール単位の要約カードを生成する。"""
    file_paths = list(file_cards.keys())
    module_to_files = detect_module_boundaries(file_paths)

    result: dict[str, ModuleCard] = {}

    for module_name, module_files in module_to_files.items():
        # Issue 数の集計
        total_counts: dict[str, int] = {"critical": 0, "warning": 0, "info": 0}
        for fp in module_files:
            card = file_cards.get(fp)
            if card is None:
                continue
            for severity, count in card.issue_counts.items():
                if severity in total_counts:
                    total_counts[severity] += count

        # モジュール境界チェック
        boundary_issues: list[str] = []
        boundary_issues.extend(check_name_collisions(module_files, ast_map))
        boundary_issues.extend(check_all_exports(module_files, ast_map))
        boundary_issues.extend(
            check_unused_reexports(module_files, ast_map, import_map)
        )

        result[module_name] = ModuleCard(
            module_name=module_name,
            file_cards=module_files,
            total_issue_counts=total_counts,
            boundary_issues=boundary_issues,
        )

    return result


def _module_card_filename(module_name: str) -> str:
    """モジュール名からカードのファイル名を生成する。

    設計書 Section 4.6: パスの / を - に置換。
    """
    return module_name.replace("/", "-") + ".json"


def save_module_card(state_dir: Path, card: ModuleCard) -> None:
    """モジュールカードを review-state/cards/module-cards/ に永続化する。"""
    cards_dir = state_dir / _CARDS_DIR / _MODULE_CARDS_DIR
    cards_dir.mkdir(parents=True, exist_ok=True)

    filename = _module_card_filename(card.module_name)
    _write_card_file(cards_dir / filename, asdict(card), label="module card")


def load_module_card(state_dir: Path, module_name: str) -> ModuleCard | None:
    """モジュールカードを読み込む。"""
    cards_dir = state_dir / _CARDS_DIR / _MODULE_CARDS_DIR
    filename = _module_card_filename(module_name)
    path = cards_dir / filename

    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("Corrupted module card: %s", path)
        return None

    return ModuleCard(**data)


# ===================================================================
# Layer 3: システムレビュー（Task C-2b）
# 設計書 Section 4.5
# グラフ解析（SCC / トポロジカルソート / 循環依存検出）は analyzers.graph.scc に切り出し
# （Task ⑤）。本モジュールでは冒頭で re-export している。
# ===================================================================


def _collect_function_names(root_node: ASTNode) -> list[str]:
    """ASTNode ツリーから関数/メソッド名を再帰的に収集する。"""
    names: list[str] = []
    if root_node.kind in ("function", "method"):
        names.append(root_node.name)
    for child in root_node.children:
        names.extend(_collect_function_names(child))
    return names


def detect_module_naming_violations(
    ast_map: dict[str, ASTNode],
) -> list[Issue]:
    """モジュール横断で命名規則の混在を検出する。

    全ファイルの関数名を集約し、snake_case と camelCase の混在を検出する。
    PascalCase（クラス名）は除外する。
    """
    conventions: dict[str, list[tuple[str, str]]] = {
        "snake_case": [],
        "camelCase": [],
    }

    for file_path, root_node in ast_map.items():
        for name in _collect_function_names(root_node):
            conv = classify_name(name)
            if conv and conv in conventions:
                conventions[conv].append((file_path, name))

    snake = conventions["snake_case"]
    camel = conventions["camelCase"]

    if snake and camel:
        snake_dominant = len(snake) >= len(camel)
        minority = camel if snake_dominant else snake
        majority_style = "snake_case" if snake_dominant else "camelCase"

        examples = [f"{f}:{name}" for f, name in minority[:5]]
        return [
            Issue(
                file="(project-wide)",
                line=0,
                severity="warning",
                category="naming-violation",
                tool="card_generator",
                message=(
                    f"Cross-module naming inconsistency: "
                    f"{majority_style} is dominant ({len(snake)} snake vs {len(camel)} camel). "
                    f"Violations: {', '.join(examples)}"
                ),
                rule_id="naming-consistency",
                suggestion=f"Standardize on {majority_style} across the project",
            )
        ]

    return []


# ===================================================================
# D-4: 影響範囲分析（FR-7d）
# 設計書 Section 5.4
# 影響範囲分析（analyze_impact / classify_impact_for_cards / 内部関数）は
# analyzers.analysis.impact に切り出し（Task ⑤）。本モジュールでは冒頭で re-export。
# collect_spec_drift_context は ModuleCard 依存のためここに残置。
# ===================================================================


def collect_spec_drift_context(
    state_dir: Path,
    specs_dir: Path,
) -> str:
    """仕様ドリフト検出用のコンテキストを収集する。

    モジュールカード（Layer 2 出力）と docs/specs/ の仕様書を
    LLM に渡すための単一テキストに整形する。
    """
    sections: list[str] = []

    # モジュールカードを収集
    sections.append("## モジュール実装サマリー（Layer 2 出力）\n")
    cards_dir = state_dir / _CARDS_DIR / _MODULE_CARDS_DIR
    if cards_dir.exists():
        card_files = sorted(cards_dir.glob("*.json"))
        for card_file in card_files:
            try:
                data = json.loads(card_file.read_text(encoding="utf-8"))
                card = ModuleCard(**data)
            except (OSError, json.JSONDecodeError, TypeError):
                logger.warning("Corrupted module card: %s", card_file)
                card = None
            if card:
                sections.append(card.to_markdown())
                sections.append("")
    if len(sections) == 1:
        sections.append("(モジュールカードなし)\n")

    # 仕様書を収集（サブディレクトリも再帰的に / I-2）
    sections.append("## 仕様書（docs/specs/）\n")
    spec_files: list[Path] = []
    if specs_dir.exists():
        spec_files = sorted(specs_dir.rglob("*.md"))
        for spec_file in spec_files:
            try:
                content = spec_file.read_text(encoding="utf-8", errors="ignore")
            except OSError as e:
                # rglob は *.md 名のディレクトリにもマッチする。読取不能な
                # エントリでパイプラインを停止させない（iter3 SRC-B-1）
                logger.warning("Failed to read spec file %s: %s", spec_file, e)
                continue
            # サブディレクトリの場合は specs_dir からの相対パスを表示
            display_name = spec_file.relative_to(specs_dir).as_posix()
            sections.append(f"### {display_name}\n")
            sections.append(content)
            sections.append("")
    if not spec_files:
        sections.append("(仕様書なし)\n")

    return "\n".join(sections)
