"""Scalable Code Review Phase 0: 静的解析パイプライン

Task A-6: full-review Phase 0 統合
対応仕様: scalable-code-review-spec.md FR-1, NFR-2, NFR-4
対応設計: scalable-code-review-design.md Section 2.4, gitleaks-integration-design.md Section 5.4
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from analyzers.base import AnalyzerRegistry, Issue, LanguageAnalyzer
from analyzers.config import ReviewConfig
from analyzers.gitleaks_scanner import run_detect as gitleaks_run_detect
from analyzers.python_analyzer import PythonAnalyzer
from analyzers.javascript_analyzer import JavaScriptAnalyzer
from analyzers.rust_analyzer import RustAnalyzer
from analyzers.state_manager import (
    generate_summary,
    save_issues,
)

logger = logging.getLogger(__name__)

_CODE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".rs",
    ".go", ".java", ".c", ".cpp", ".h", ".hpp",
    ".rb", ".php", ".swift", ".kt", ".scala",
    ".sh", ".bash", ".zsh",
}

_DEFAULT_EXCLUDE_DIRS = {"node_modules", ".venv", "venv", "vendor", "dist",
                         "__pycache__", ".git", ".tox", ".mypy_cache",
                         ".pytest_cache", "build", "target", ".next"}

# config.exclude_dirs が指定された場合も常に除外するディレクトリ
_ALWAYS_EXCLUDE_DIRS = {".git", "__pycache__"}

_SUGGEST_THRESHOLD = 10000


@dataclass
class Phase0Result:
    """Phase 0 の実行結果。"""
    issues: list[Issue] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    line_count: int = 0
    summary_path: Path = field(default_factory=lambda: Path())


def count_lines(
    project_root: Path,
    exclude_dirs: list[str] | None = None,
) -> int:
    """プロジェクトのコード行数をカウントする。

    exclude_dirs が指定された場合はその値を尊重しつつ、
    _ALWAYS_EXCLUDE_DIRS (.git, __pycache__) を常に追加する。
    未指定の場合は _DEFAULT_EXCLUDE_DIRS を使用する。
    """
    if exclude_dirs is not None:
        excludes = set(exclude_dirs) | _ALWAYS_EXCLUDE_DIRS
    else:
        excludes = _DEFAULT_EXCLUDE_DIRS
    total = 0
    for path in project_root.rglob("*"):
        if path.is_file() and path.suffix in _CODE_EXTENSIONS:
            if not any(part in excludes for part in path.relative_to(project_root).parts):
                try:
                    total += len(path.read_text(errors="replace").splitlines())
                except OSError as e:
                    logger.debug("Skipping unreadable file %s: %s", path, e)
    return total


def should_enable_static_analysis(
    line_count: int,
    auto_threshold: int = 30000,
) -> str:
    """行数に基づいて静的解析の有効化レベルを返す。

    Returns:
        "skip" — 10K 未満、現行 full-review のまま
        "suggest" — 10K-30K、ユーザーに提案
        "auto" — 30K 以上、自動有効化
    """
    if line_count >= auto_threshold:
        return "auto"
    if line_count >= _SUGGEST_THRESHOLD:
        return "suggest"
    return "skip"


def _build_registry() -> AnalyzerRegistry:
    """組み込み Analyzer を登録した Registry を返す。

    組み込み Analyzer を明示的に登録し、auto_discover でカスタム Analyzer を追加探索する。
    auto_discover はクラス名ベースの重複チェックで組み込み分をスキップする（base.py _load_module）。
    同名クラスのカスタム Analyzer は組み込みよりも優先されない（クラス名ベースの重複チェックによりスキップされる）。
    """
    registry = AnalyzerRegistry()
    registry.register(PythonAnalyzer)
    registry.register(JavaScriptAnalyzer)
    registry.register(RustAnalyzer)
    return registry


def _detect_analyzers(
    project_root: Path,
    config: ReviewConfig,
) -> list[LanguageAnalyzer]:
    """言語検出・除外フィルタ・ツール検証を行い、有効な Analyzer リストを返す。"""
    registry = _build_registry()
    analyzers_dir = project_root / ".claude" / "hooks" / "analyzers"
    if analyzers_dir.is_dir():
        registry.auto_discover(analyzers_dir)

    analyzers = registry.detect_languages(project_root)

    if config.exclude_languages:
        exclude_set = {lang.lower() for lang in config.exclude_languages}
        analyzers = [
            a for a in analyzers
            if a.language_name.lower() not in exclude_set
        ]

    if analyzers:
        registry.verify_tools(analyzers)

    return analyzers


def _persist_results(
    project_root: Path,
    issues: list[Issue],
) -> Path:
    """Issue リストと summary.md を review-state/ に永続化する。"""
    state_dir = project_root / ".claude" / "review-state"
    save_issues(state_dir, issues)

    summary_content = generate_summary(issues)
    summary_path = state_dir / "summary.md"
    summary_path.write_text(summary_content, encoding="utf-8")
    return summary_path


def run_phase0(
    project_root: Path,
    config: ReviewConfig | None = None,
) -> Phase0Result:
    """Phase 0（静的解析パイプライン）を実行する。

    言語別静的解析 + gitleaks シークレットスキャンを実行する。
    gitleaks は言語非依存のため、言語 Analyzer が見つからない場合でも実行する。
    """
    if config is None:
        config = ReviewConfig.load(project_root)

    analyzers = _detect_analyzers(project_root, config)

    line_count = count_lines(project_root, config.exclude_dirs) if analyzers else 0

    issues: list[Issue] = []
    for analyzer in analyzers:
        issues.extend(analyzer.run_lint(project_root))
        issues.extend(analyzer.run_security(project_root))

    # gitleaks シークレットスキャン（言語非依存、オプトアウト可）
    issues.extend(gitleaks_run_detect(project_root, enabled=config.gitleaks_enabled))

    summary_path = _persist_results(project_root, issues)

    return Phase0Result(
        issues=issues,
        languages=[a.language_name for a in analyzers],
        line_count=line_count,
        summary_path=summary_path,
    )
