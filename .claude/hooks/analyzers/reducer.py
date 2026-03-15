"""Scalable Code Review Phase 2: Reduce（横断チェック + 重複排除）

Task B-2b: Issue 統合・重複排除・命名規則チェック

対応仕様: scalable-code-review-spec.md FR-2
対応設計: scalable-code-review-design.md Section 3.3
"""
from __future__ import annotations

from analyzers.base import Issue


def deduplicate_issues(issues: list[Issue]) -> list[Issue]:
    """同一ファイル・行・ルールの重複 Issue を排除する。

    最初の出現を保持し、後続の重複を除去する。
    """
    seen: set[tuple[str, int, str]] = set()
    result: list[Issue] = []

    for issue in issues:
        key = (issue.file, issue.line, issue.rule_id)
        if key not in seen:
            seen.add(key)
            result.append(issue)

    return result


def classify_name(name: str) -> str | None:
    """名前の命名規則を判定する。

    Returns:
        "snake_case", "camelCase", "PascalCase", or None (判定不能/対象外)
    """
    # ダンダー名は対象外
    if name.startswith("__") and name.endswith("__"):
        return None

    # 先頭アンダースコアを除去して判定
    stripped = name.lstrip("_")
    if not stripped:
        return None

    # 1 ワード（アンダースコアも大文字境界もない）は判定不能
    has_underscore = "_" in stripped
    has_upper_internal = any(c.isupper() for c in stripped[1:])  # 先頭以外に大文字
    starts_with_upper = stripped[0].isupper()

    if not has_underscore and not has_upper_internal:
        return None  # 単一ワード

    if has_underscore:
        return "snake_case"

    # アンダースコアなしで内部に大文字がある場合
    if starts_with_upper and has_upper_internal:
        return "PascalCase"
    if has_upper_internal:
        return "camelCase"

    return None


def check_naming_consistency(
    names: list[str],
    file_path: str,
) -> list[Issue]:
    """名前リストの命名規則の統一性をチェックする。

    snake_case と camelCase が混在している場合に Issue を生成する。
    PascalCase はクラス名として許容し、混在検出の対象としない。

    将来的に複数 Issue を返す拡張に備えてリスト型を採用している。
    """
    conventions: dict[str, list[str]] = {"snake_case": [], "camelCase": []}

    for name in names:
        conv = classify_name(name)
        if conv and conv in conventions:
            conventions[conv].append(name)

    snake_names = conventions["snake_case"]
    camel_names = conventions["camelCase"]

    if snake_names and camel_names:
        # 同数の場合は snake_case を majority として扱う（Python 規約優先）
        snake_is_dominant = len(snake_names) >= len(camel_names)
        minority = camel_names if snake_is_dominant else snake_names
        majority_style = "snake_case" if snake_is_dominant else "camelCase"

        return [
            Issue(
                file=file_path,
                line=0,  # ファイル全体横断 Issue は line=0 を使用する慣例（設計書 Section 2.3）
                severity="warning",
                category="lint",
                tool="reducer",
                message=(
                    f"Naming convention inconsistency: "
                    f"{majority_style} is dominant but found mixed names: "
                    f"{', '.join(minority)}"
                ),
                rule_id="naming-consistency",
                suggestion=f"Use {majority_style} consistently",
            )
        ]

    return []
