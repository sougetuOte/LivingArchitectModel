"""Scalable Code Review Phase 0: 静的解析パイプライン

Task A-6: full-review Phase 0 統合
対応仕様: scalable-code-review-spec.md FR-1, NFR-2, NFR-4
対応設計: scalable-code-review-design.md Section 2.4
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from analyzers.base import AnalyzerRegistry, Issue
from analyzers.config import ReviewConfig
from analyzers.python_analyzer import PythonAnalyzer
from analyzers.javascript_analyzer import JavaScriptAnalyzer
from analyzers.rust_analyzer import RustAnalyzer
from analyzers.state_manager import (
    generate_summary,
    save_issues,
)

_CODE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".rs",
    ".go", ".java", ".c", ".cpp", ".h", ".hpp",
    ".rb", ".php", ".swift", ".kt", ".scala",
    ".sh", ".bash", ".zsh",
}

_DEFAULT_EXCLUDE_DIRS = {"node_modules", ".venv", "venv", "vendor", "dist",
                         "__pycache__", ".git", ".tox", ".mypy_cache",
                         ".pytest_cache", "build", "target", ".next"}


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
    """プロジェクトのコード行数をカウントする。"""
    excludes = set(exclude_dirs) if exclude_dirs is not None else _DEFAULT_EXCLUDE_DIRS
    total = 0
    for path in project_root.rglob("*"):
        if path.is_file() and path.suffix in _CODE_EXTENSIONS:
            if not any(part in excludes for part in path.relative_to(project_root).parts):
                try:
                    total += len(path.read_text(errors="replace").splitlines())
                except (OSError, UnicodeDecodeError):
                    pass
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
    if line_count >= 10000:
        return "suggest"
    return "skip"


def _build_registry() -> AnalyzerRegistry:
    """組み込み Analyzer を登録した Registry を返す。"""
    registry = AnalyzerRegistry()
    registry.register(PythonAnalyzer)
    registry.register(JavaScriptAnalyzer)
    registry.register(RustAnalyzer)
    return registry


def run_phase0(
    project_root: Path,
    config: ReviewConfig | None = None,
) -> Phase0Result:
    """Phase 0（静的解析パイプライン）を実行する。

    1. 言語検出
    2. ツール検証
    3. lint + security 実行
    4. 結果を review-state/ に永続化
    5. summary.md 生成
    """
    if config is None:
        config = ReviewConfig.load(project_root)

    registry = _build_registry()
    # 自動探索（カスタム Analyzer がある場合）
    analyzers_dir = project_root / ".claude" / "hooks" / "analyzers"
    if analyzers_dir.is_dir():
        registry.auto_discover(analyzers_dir)

    analyzers = registry.detect_languages(project_root)

    # 除外言語をフィルタ（language_name プロパティで照合）
    if config.exclude_languages:
        exclude_set = {lang.lower() for lang in config.exclude_languages}
        analyzers = [
            a for a in analyzers
            if a.language_name.lower() not in exclude_set
        ]

    if not analyzers:
        return Phase0Result()

    # ツール検証
    registry.verify_tools(analyzers)

    # 行数カウント
    line_count = count_lines(project_root, config.exclude_dirs)

    # lint + security 実行
    issues: list[Issue] = []
    for analyzer in analyzers:
        issues.extend(analyzer.run_lint(project_root))
        issues.extend(analyzer.run_security(project_root))

    # 結果永続化
    state_dir = project_root / ".claude" / "review-state"
    save_issues(state_dir, issues)

    # summary.md 生成（state_dir は save_issues() 内で mkdir 済み）
    summary_content = generate_summary(issues)
    summary_path = state_dir / "summary.md"
    summary_path.write_text(summary_content, encoding="utf-8")

    # 検出言語名リスト
    language_names = [a.language_name for a in analyzers]

    return Phase0Result(
        issues=issues,
        languages=language_names,
        line_count=line_count,
        summary_path=summary_path,
    )
