"""Task B-2b: Reduce（横断チェック + 重複排除）のテスト

対応仕様: scalable-code-review-spec.md FR-2
対応設計: scalable-code-review-design.md Section 3.3
"""
from __future__ import annotations

from analyzers.base import Issue
from analyzers.reducer import deduplicate_issues, check_naming_consistency


class TestDeduplicateIssues:
    """重複排除のテスト。"""

    def test_no_duplicates(self) -> None:
        """重複なし → そのまま返す。"""
        issues = [
            Issue(file="a.py", line=1, severity="warning", category="lint",
                  tool="ruff", message="msg1", rule_id="E501", suggestion=""),
            Issue(file="b.py", line=2, severity="warning", category="lint",
                  tool="ruff", message="msg2", rule_id="E502", suggestion=""),
        ]
        result = deduplicate_issues(issues)
        assert len(result) == 2

    def test_exact_duplicates(self) -> None:
        """同一ファイル・行・ルールの重複を排除。"""
        issue = Issue(file="a.py", line=10, severity="warning", category="lint",
                      tool="ruff", message="line too long", rule_id="E501", suggestion="")
        issues = [issue, issue, issue]
        result = deduplicate_issues(issues)
        assert len(result) == 1

    def test_same_file_line_rule(self) -> None:
        """ファイル・行・ルールが同じでメッセージが異なる → 重複とみなす。"""
        i1 = Issue(file="a.py", line=10, severity="warning", category="lint",
                   tool="ruff", message="message A", rule_id="E501", suggestion="")
        i2 = Issue(file="a.py", line=10, severity="warning", category="lint",
                   tool="ruff", message="message B", rule_id="E501", suggestion="fix")
        result = deduplicate_issues([i1, i2])
        assert len(result) == 1

    def test_different_lines_not_deduplicated(self) -> None:
        """同一ファイル・ルールでも行が異なれば重複ではない。"""
        i1 = Issue(file="a.py", line=10, severity="warning", category="lint",
                   tool="ruff", message="msg", rule_id="E501", suggestion="")
        i2 = Issue(file="a.py", line=20, severity="warning", category="lint",
                   tool="ruff", message="msg", rule_id="E501", suggestion="")
        result = deduplicate_issues([i1, i2])
        assert len(result) == 2

    def test_empty_list(self) -> None:
        """空リスト → 空リスト。"""
        assert deduplicate_issues([]) == []

    def test_preserves_first_occurrence(self) -> None:
        """重複時は最初の出現を保持する。"""
        i1 = Issue(file="a.py", line=10, severity="critical", category="lint",
                   tool="ruff", message="first", rule_id="E501", suggestion="")
        i2 = Issue(file="a.py", line=10, severity="warning", category="lint",
                   tool="ruff", message="second", rule_id="E501", suggestion="")
        result = deduplicate_issues([i1, i2])
        assert result[0].severity == "critical"


class TestCheckNamingConsistency:
    """命名規則の統一性チェックのテスト。"""

    def test_consistent_snake_case(self) -> None:
        """全て snake_case → Issue なし。"""
        names = ["get_user", "set_name", "calculate_total"]
        issues = check_naming_consistency(names, "module.py")
        assert len(issues) == 0

    def test_consistent_camel_case(self) -> None:
        """全て camelCase → Issue なし。"""
        names = ["getUser", "setName", "calculateTotal"]
        issues = check_naming_consistency(names, "module.py")
        assert len(issues) == 0

    def test_mixed_naming(self) -> None:
        """snake_case と camelCase の混在 → Issue あり。"""
        names = ["get_user", "setName", "calculate_total"]
        issues = check_naming_consistency(names, "module.py")
        assert len(issues) >= 1
        assert any("naming" in i.message.lower() or "命名" in i.message for i in issues)

    def test_single_word_names_ignored(self) -> None:
        """1 ワードの名前は判定対象外（snake も camel も同じ）。"""
        names = ["get", "set", "run"]
        issues = check_naming_consistency(names, "module.py")
        assert len(issues) == 0

    def test_empty_names(self) -> None:
        """空リスト → Issue なし。"""
        issues = check_naming_consistency([], "module.py")
        assert len(issues) == 0

    def test_dunder_names_excluded(self) -> None:
        """__init__ 等のダンダー名は判定対象外。"""
        names = ["__init__", "__str__", "get_user", "set_name"]
        issues = check_naming_consistency(names, "module.py")
        assert len(issues) == 0

    def test_private_names_follow_convention(self) -> None:
        """_private_name は snake_case として扱う。"""
        names = ["_private_method", "get_user", "_helper"]
        issues = check_naming_consistency(names, "module.py")
        assert len(issues) == 0
