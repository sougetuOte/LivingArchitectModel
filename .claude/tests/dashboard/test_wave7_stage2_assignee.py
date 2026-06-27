"""test_wave7_stage2_assignee.py - Wave 7 Stage 2 / FR-W7-2 / T50 対応

_extract_assignee() の単体テスト。
design.md §7 のシグネチャ・挙動仕様に基づく。

シグネチャ: _extract_assignee(description: str) -> tuple[str, str]
戻り値:     (clean_description, assignee) / 未マッチ時は (description, "-")
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# .claude/scripts を sys.path に追加（test_tasks_parser.py と同一パターン）
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


# ─────────────────────────────────────────────
# 正常系 — @<assignee> が末尾に 1 つある場合
# ─────────────────────────────────────────────


@pytest.mark.parametrize(
    "description, expected_clean, expected_assignee",
    [
        # 正常系1: 小文字 assignee
        ("Task 説明 @sonnet", "Task 説明", "sonnet"),
        # 正常系2: 大文字始まり assignee
        ("Task 説明 @Sonnet", "Task 説明", "Sonnet"),
        # 正常系3: 推奨値 human
        ("Task 説明 @human", "Task 説明", "human"),
    ],
    ids=["lowercase_assignee", "capitalized_assignee", "human_assignee"],
)
def test_extract_assignee_normal(description, expected_clean, expected_assignee):
    """正常系: description 末尾の @<assignee> が抽出され、clean description が返ること。"""
    from dashboard.parsers.tasks import _extract_assignee

    clean, assignee = _extract_assignee(description)
    assert clean == expected_clean
    assert assignee == expected_assignee


# ─────────────────────────────────────────────
# 異常系 — @タグなし
# ─────────────────────────────────────────────


def test_extract_assignee_no_at_tag_returns_dash():
    """異常系: description に @ タグがない場合、(description, "-") を返すこと。"""
    from dashboard.parsers.tasks import _extract_assignee

    description = "Task 説明のみ"
    clean, assignee = _extract_assignee(description)
    assert clean == description
    assert assignee == "-"


# ─────────────────────────────────────────────
# エッジケース
# ─────────────────────────────────────────────


def test_extract_assignee_trailing_whitespace():
    """エッジケース1: description 末尾に空白がある場合もタグを正しく抽出すること。

    "Task 説明 @sonnet  " → ("Task 説明", "sonnet")
    """
    from dashboard.parsers.tasks import _extract_assignee

    clean, assignee = _extract_assignee("Task 説明 @sonnet  ")
    assert clean == "Task 説明"
    assert assignee == "sonnet"


def test_extract_assignee_multiple_at_signs_takes_last():
    """エッジケース2: 複数の @ がある場合、末尾の 1 個のみ採用すること。

    design.md §7 注記: 「複数記載時は最後の 1 個のみ採用」
    "Task 説明 @foo @bar" → ("Task 説明 @foo", "bar")
    """
    from dashboard.parsers.tasks import _extract_assignee

    clean, assignee = _extract_assignee("Task 説明 @foo @bar")
    assert clean == "Task 説明 @foo"
    assert assignee == "bar"


def test_extract_assignee_mid_at_sign_preserved_in_clean():
    """エッジケース3: 中間の @ は clean_description に保持されること。

    design.md §7 注記: 「中間 @ 含む description でも末尾のみ採用」
    "メール @example.com を更新 @Sonnet" → ("メール @example.com を更新", "Sonnet")
    """
    from dashboard.parsers.tasks import _extract_assignee

    clean, assignee = _extract_assignee("メール @example.com を更新 @Sonnet")
    assert clean == "メール @example.com を更新"
    assert assignee == "Sonnet"


def test_extract_assignee_regex_allowed_chars():
    """エッジケース4: regex が許容する文字 [A-Za-z0-9_-] を含む assignee を正しく抽出すること。

    "Task @A-1_b" → ("Task", "A-1_b")
    """
    from dashboard.parsers.tasks import _extract_assignee

    clean, assignee = _extract_assignee("Task @A-1_b")
    assert clean == "Task"
    assert assignee == "A-1_b"


def test_extract_assignee_empty_string_returns_dash():
    """エッジケース5: 空文字列の場合 ("", "-") を返すこと（防御的処理）。"""
    from dashboard.parsers.tasks import _extract_assignee

    clean, assignee = _extract_assignee("")
    assert clean == ""
    assert assignee == "-"


def test_extract_assignee_only_tag_no_description():
    """エッジケース6: 説明なしで @<assignee> 単独の場合の挙動確認。

    design.md §7 ASSIGNEE_REGEX は空白文字+で始まるため、
    行頭からの "@sonnet" はマッチしない → ("@sonnet", "-") を返す。
    """
    from dashboard.parsers.tasks import _extract_assignee

    clean, assignee = _extract_assignee("@sonnet")
    # ASSIGNEE_REGEX の先頭は空白文字必須のため、行頭 @ にはマッチしない
    assert clean == "@sonnet"
    assert assignee == "-"
