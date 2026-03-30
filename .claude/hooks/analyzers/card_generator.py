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

import graphlib
import json
import logging
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

from analyzers.base import ASTNode, Issue
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


def _file_path_to_module_name(file_path: str) -> str:
    """ファイルパスをモジュール名に変換する。

    例: "src/foo.py" -> "src.foo"
    """
    return file_path.replace("/", ".").replace("\\", ".").removesuffix(".py")


def _build_reverse_import_map(
    ast_map: dict[str, ASTNode],
    import_map: dict[str, list[str]],
) -> dict[str, list[str]]:
    """import_map を逆引きし、各ファイルの依存元を構築する。

    import_map の値はドット区切りモジュール名（例: "src.foo"）で、
    ast_map のキーはパス形式（例: "src/foo.py"）なので変換が必要。
    """
    # ファイルパス → モジュール名の対応表
    path_to_module = {fp: _file_path_to_module_name(fp) for fp in ast_map}
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


def save_file_card(state_dir: Path, card: FileCard) -> None:
    """概要カードを review-state/cards/file-cards/ に永続化する。"""
    cards_dir = state_dir / _CARDS_DIR / _FILE_CARDS_DIR
    cards_dir.mkdir(parents=True, exist_ok=True)

    filename = _card_filename(card.file_path)
    data = asdict(card)
    (cards_dir / filename).write_text(json.dumps(data, indent=2), encoding="utf-8")


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
    data = asdict(card)
    (contracts_dir / filename).write_text(json.dumps(data, indent=2), encoding="utf-8")


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
    """
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
    既知の制限: 深いパスでの import 検出は不完全（Phase 3 以降で精度向上予定）。
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
    data = asdict(card)
    (cards_dir / filename).write_text(json.dumps(data, indent=2), encoding="utf-8")


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
# ===================================================================


def _build_import_graph(
    import_map: dict[str, list[str]],
) -> tuple[dict[str, list[str]], set[str], dict[str, str]]:
    """import_map からグラフ（隣接リスト）を構築する。

    import_map のキーはファイルパス形式（例: "src/foo.py"）、
    値はドット区切りモジュール名のリスト（例: ["src.bar", "os"]）。

    Returns:
        (graph, all_nodes, node_to_file) のタプル。
        graph: ノード名 → 隣接ノード名リスト。
        all_nodes: 全ノード名の集合。
        node_to_file: ノード名 → 元のファイルパスの逆引き辞書。
    """
    file_to_node = {fp: _file_path_to_module_name(fp) for fp in import_map}
    node_to_file: dict[str, str] = {v: k for k, v in file_to_node.items()}
    all_nodes: set[str] = set(file_to_node.values())

    graph: dict[str, list[str]] = {}
    for file_path, imports in import_map.items():
        src = file_to_node[file_path]
        graph[src] = [imp for imp in imports if imp in all_nodes]

    return graph, all_nodes, node_to_file


def _find_sccs(graph: dict[str, list[str]], all_nodes: set[str]) -> list[list[str]]:
    """Tarjan のアルゴリズムで強連結成分（SCC）を検出する。

    サイズ2以上の SCC、または自己参照を含む SCC のみ返す。

    Note: 再帰実装のため、ノード数が Python の再帰上限（デフォルト1000）を
    超えるプロジェクトでは RecursionError が発生する可能性がある。
    大規模プロジェクト対応が必要な場合は反復実装に置き換えること。
    """
    index_counter = [0]
    stack: list[str] = []
    on_stack: set[str] = set()
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    sccs: list[list[str]] = []

    def strongconnect(v: str) -> None:
        indices[v] = index_counter[0]
        lowlinks[v] = index_counter[0]
        index_counter[0] += 1
        stack.append(v)
        on_stack.add(v)

        for w in graph.get(v, []):
            if w not in indices:
                strongconnect(w)
                lowlinks[v] = min(lowlinks[v], lowlinks[w])
            elif w in on_stack:
                lowlinks[v] = min(lowlinks[v], indices[w])

        if lowlinks[v] == indices[v]:
            scc: list[str] = []
            while True:
                w = stack.pop()
                on_stack.discard(w)
                scc.append(w)
                if w == v:
                    break
            if len(scc) > 1 or (len(scc) == 1 and v in graph.get(v, [])):
                sccs.append(scc)

    for node in sorted(all_nodes):
        if node not in indices:
            strongconnect(node)

    return sccs


def detect_circular_dependencies(
    import_map: dict[str, list[str]],
) -> list[Issue]:
    """import_map からグラフを構築し、循環依存（SCC）を検出する。

    サイズ2以上の SCC（または自己参照）を Warning Issue として返す。
    """
    graph, all_nodes, node_to_file = _build_import_graph(import_map)
    try:
        sccs = _find_sccs(graph, all_nodes)
    except RecursionError:
        logger.warning(
            "Import graph too large for recursive SCC detection (%d nodes)",
            len(all_nodes),
        )
        return []

    issues: list[Issue] = []
    for scc in sccs:
        file_paths = [node_to_file.get(n, n) for n in sorted(scc)]
        issues.append(
            Issue(
                file=file_paths[0],
                line=0,
                severity="warning",
                category="circular-dependency",
                tool="card_generator",
                message=f"Circular dependency detected: {' → '.join(file_paths)}",
                rule_id="circular-dependency",
                suggestion="Break the cycle by introducing an interface or restructuring imports",
            )
        )

    return issues


def _condense_sccs(
    graph: dict[str, list[str]],
    all_nodes: set[str],
    sccs: list[list[str]],
) -> tuple[dict[str, list[str]], dict[str, str]]:
    """SCC をスーパーノードに縮約し、縮約済みグラフと元ノードのマッピングを返す。

    Args:
        graph: ノード名 → 隣接ノード名リスト（隣接リスト）。
        all_nodes: グラフ内の全ノード名の集合。
        sccs: 縮約対象の SCC リスト（各要素はノード名リスト）。

    Returns:
        (condensed_graph, scc_map) のタプル。
        condensed_graph: SCC をスーパーノードに置き換えた縮約済みグラフ。
        scc_map: 元ノード名 → スーパーノード名のマッピング。SCC 外のノードは含まない。
    """
    # 元ノード → スーパーノード名のマッピングを構築
    scc_map: dict[str, str] = {}
    for idx, scc_members in enumerate(sccs):
        super_name = f"scc_{idx}"
        for member in scc_members:
            scc_map[member] = super_name

    def _resolve(node: str) -> str:
        """ノードをスーパーノード名に解決する。SCC 外はそのまま返す。"""
        return scc_map.get(node, node)

    # SCC メンバーを除いた通常ノードを収集
    scc_members_all = set(scc_map.keys())
    regular_nodes = all_nodes - scc_members_all
    super_nodes = {_resolve(m) for m in scc_members_all}

    condensed: dict[str, list[str]] = {}
    for node in regular_nodes:
        condensed[node] = _resolve_node_edges(graph, node, _resolve)
    for super_name in super_nodes:
        members = [m for m, s in scc_map.items() if s == super_name]
        condensed[super_name] = _collect_supernode_edges(
            graph, members, super_name, _resolve
        )
    return condensed, scc_map


def _resolve_node_edges(
    graph: dict[str, list[str]],
    node: str,
    resolve: Callable[[str], str],
) -> list[str]:
    """通常ノードの辺をスーパーノード名に解決する。自己ループと重複を除外。"""
    edges: list[str] = []
    for neighbor in graph.get(node, []):
        resolved = resolve(neighbor)
        if resolved != node and resolved not in edges:
            edges.append(resolved)
    return edges


def _collect_supernode_edges(
    graph: dict[str, list[str]],
    members: list[str],
    super_name: str,
    resolve: Callable[[str], str],
) -> list[str]:
    """SCC メンバーの全外部辺を収集してスーパーノードの辺リストを構築する。

    SCC 内部の辺（自己ループ）は除外する。重複辺も除外する。
    """
    edges: list[str] = []
    for member in members:
        for neighbor in graph.get(member, []):
            resolved = resolve(neighbor)
            if resolved != super_name and resolved not in edges:
                edges.append(resolved)
    return edges


def build_topo_order(
    import_map: dict[str, list[str]],
) -> dict:
    """import_map からトポロジカル順序と SCC 情報を計算する。

    循環依存がある場合は SCC をスーパーノードに縮約してからトポロジカルソートを行う。

    Args:
        import_map: ファイルパス → ドット区切りモジュール名リスト の辞書。

    Returns:
        以下のキーを持つ辞書:
        - topo_order: トポロジカル順のノード名（または SCC スーパーノード名）のリスト。
        - sccs: 検出された SCC のリスト（各要素はノード名リスト）。
        - node_to_file: ノード名 → 元ファイルパスの逆引き辞書。
    """
    graph, all_nodes, node_to_file = _build_import_graph(import_map)

    try:
        sccs = _find_sccs(graph, all_nodes)
    except RecursionError:
        logger.warning(
            "Import graph too large for recursive SCC detection (%d nodes)",
            len(all_nodes),
        )
        sccs = []

    condensed, _scc_map = _condense_sccs(graph, all_nodes, sccs)

    try:
        sorter = graphlib.TopologicalSorter(condensed)
        topo_order = list(sorter.static_order())
    except graphlib.CycleError:
        logger.warning("Cycle detected in condensed graph; returning partial order")
        topo_order = list(condensed.keys())

    return {
        "topo_order": topo_order,
        "sccs": sccs,
        "node_to_file": node_to_file,
    }


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
# ===================================================================


def _build_reverse_graph(
    graph: dict[str, list[str]],
    all_nodes: set[str],
) -> dict[str, list[str]]:
    """グラフの逆引きを構築する（import 方向の逆 → 依存元方向）。

    graph は A→B (A imports B) の方向なので、
    逆引きは B→A (B を import しているのは A) の方向を返す。
    """
    reverse: dict[str, list[str]] = {node: [] for node in all_nodes}
    for src, neighbors in graph.items():
        for dst in neighbors:
            if dst in reverse:
                reverse[dst].append(src)
    return reverse


def _expand_scc_members(
    initial_scope: set[str],
    sccs: list[list[str]],
    node_to_file: dict[str, str],
) -> set[str]:
    """SCC 内の1ノードが in_scope なら SCC 全体をノード名で返す。

    戻り値はノード名（モジュール名）の集合。
    """
    scc_expanded: set[str] = set(initial_scope)
    for scc in sccs:
        scc_node_names = set(scc)
        if scc_node_names & initial_scope:
            scc_expanded |= scc_node_names
    return scc_expanded


def _bfs_upstream(
    start_nodes: set[str],
    reverse_graph: dict[str, list[str]],
    sccs: list[list[str]],
    node_to_file: dict[str, str],
) -> set[str]:
    """逆引きグラフで上流方向に BFS し、到達可能なノード集合を返す。

    上流ノードが SCC に属する場合、その SCC 全体も展開する。
    """
    visited: set[str] = set(start_nodes)
    queue = list(start_nodes)
    while queue:
        current = queue.pop(0)
        for upstream in reverse_graph.get(current, []):
            if upstream not in visited:
                visited.add(upstream)
                queue.append(upstream)
                expanded = _expand_scc_members({upstream}, sccs, node_to_file)
                for node in expanded - visited:
                    visited.add(node)
                    queue.append(node)
    return visited


def _partition_files_by_scope(
    import_map: dict[str, list[str]],
    visited: set[str],
    modified_files: list[str],
) -> tuple[list[str], list[str]]:
    """import_map 内のファイルを in_scope / out_of_scope に分類する。

    import_map にないが modified_files に含まれるファイルも in_scope に追加する。
    """
    file_to_node = {fp: _file_path_to_module_name(fp) for fp in import_map}
    in_scope_files: list[str] = []
    out_of_scope_files: list[str] = []

    for fp in import_map:
        node = file_to_node.get(fp)
        if node in visited:
            in_scope_files.append(fp)
        else:
            out_of_scope_files.append(fp)

    for fp in modified_files:
        if fp not in import_map and fp not in in_scope_files:
            in_scope_files.append(fp)

    return in_scope_files, out_of_scope_files


def analyze_impact(
    modified_files: list[str],
    import_map: dict[str, list[str]],
) -> dict[str, list[str]]:
    """修正ファイルから影響範囲を計算する（FR-7d）。

    依存グラフを構築し、修正ファイルから上流方向（= そのファイルを
    import しているファイル）に推移的に辿る。
    SCC 内の1ノードが修正されている場合、SCC 全体を影響範囲に含める。

    Args:
        modified_files: 修正されたファイルパスのリスト。
        import_map: ファイルパス → ドット区切りモジュール名リスト の辞書。

    Returns:
        {"in_scope": [...], "out_of_scope": [...]} の辞書。
    """
    graph, all_nodes, node_to_file = _build_import_graph(import_map)

    try:
        sccs = _find_sccs(graph, all_nodes)
    except RecursionError:
        logger.warning(
            "Import graph too large for recursive SCC detection (%d nodes)",
            len(all_nodes),
        )
        sccs = []

    file_to_node = {fp: _file_path_to_module_name(fp) for fp in import_map}
    modified_nodes: set[str] = {
        file_to_node[fp] for fp in modified_files if fp in file_to_node
    }

    scope_nodes = _expand_scc_members(modified_nodes, sccs, node_to_file)
    reverse_graph = _build_reverse_graph(graph, all_nodes)
    visited = _bfs_upstream(scope_nodes, reverse_graph, sccs, node_to_file)

    in_scope_files, out_of_scope_files = _partition_files_by_scope(
        import_map, visited, modified_files
    )
    return {"in_scope": in_scope_files, "out_of_scope": out_of_scope_files}


def classify_impact_for_cards(
    in_scope: list[str],
    out_of_scope: list[str],
    current_hashes: dict[str, str],
    previous_hashes: dict[str, str],
) -> dict[str, str]:
    """影響範囲に基づいて各ファイルの概要カード再利用判定を行う（FR-7d）。

    Args:
        in_scope: 影響範囲内のファイルパスリスト。
        out_of_scope: 影響範囲外のファイルパスリスト。
        current_hashes: 現在のファイルハッシュ辞書。
        previous_hashes: 前回のファイルハッシュ辞書。

    Returns:
        {file_path: "regenerate" | "reuse_mechanical"} の辞書。
        in_scope のファイル → "regenerate"（全フィールド再生成）。
        out_of_scope かつハッシュ未変更 → "reuse_mechanical"。
        out_of_scope かつハッシュ変更あり → "regenerate"。
    """
    result: dict[str, str] = {}

    for fp in in_scope:
        result[fp] = "regenerate"

    for fp in out_of_scope:
        current = current_hashes.get(fp)
        previous = previous_hashes.get(fp)
        if current is not None and current == previous:
            result[fp] = "reuse_mechanical"
        else:
            result[fp] = "regenerate"

    return result


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
            except (json.JSONDecodeError, TypeError):
                logger.warning("Corrupted module card: %s", card_file)
                card = None
            if card:
                sections.append(card.to_markdown())
                sections.append("")
    if len(sections) == 1:
        sections.append("(モジュールカードなし)\n")

    # 仕様書を収集
    sections.append("## 仕様書（docs/specs/）\n")
    if specs_dir.exists():
        spec_files = sorted(specs_dir.glob("*.md"))
        for spec_file in spec_files:
            content = spec_file.read_text(encoding="utf-8", errors="ignore")
            sections.append(f"### {spec_file.name}\n")
            sections.append(content)
            sections.append("")
    if not specs_dir.exists() or not list(specs_dir.glob("*.md")):
        sections.append("(仕様書なし)\n")

    return "\n".join(sections)
