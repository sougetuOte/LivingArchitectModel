"""概要カード生成エンジン。

Task C-1a: 概要カード生成エンジン（機械的フィールド）
Task C-1b: Phase 2 Agent プロンプト拡張（責務フィールド生成）
Task C-2a: Layer 2 モジュール統合（要約カード生成）
対応仕様: scalable-code-review-spec.md FR-4
対応設計: scalable-code-review-design.md Section 4.3, 4.4
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

from analyzers.base import ASTNode, Issue

logger = logging.getLogger(__name__)

_CARDS_DIR = "cards"
_FILE_CARDS_DIR = "file-cards"
_MODULE_CARDS_DIR = "module-cards"


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
    content = agent_output[start_idx + len(_RESPONSIBILITY_START):end_idx]
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
    """__init__.py で re-export しているが実際に使われていないシンボルのチェック。

    - __init__.py の import_map から import しているモジュールを取得
    - それらが他のファイル（__init__.py 以外）から import されているか確認
    - 誰にも import されていない re-export → 警告

    Note: _ast_map は将来の __all__ 解析拡張のためにシグネチャに含める。
    C-2a スコープでは _ast_map は未使用。将来の __all__ 解析拡張で利用予定。
    C-2a の近似チェックでは import_map のみを使用する。

    既知の制限: 深いパス（src.analyzers）での import 検出は不完全。
    Phase 3 以降で精度向上予定。
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
        init_dir,                    # パス表記でも
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
        boundary_issues.extend(check_unused_reexports(module_files, ast_map, import_map))

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
