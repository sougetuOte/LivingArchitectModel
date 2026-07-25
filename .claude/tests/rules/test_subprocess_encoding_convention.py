"""test_subprocess_encoding_convention.py

`.claude/rules/subprocess-encoding-convention.md` (W1-R2-T5 / FR-7) のテスト。

対応仕様:
    docs/specs/r-2-consolidation/design.md §4.4（T5: subprocess encoding 規約）
    docs/specs/r-2-consolidation/tasks.md W1-R2-T5

検証観点:
    1. cp932 の符号化・復号失敗をロケール非依存に実証する（誤例の実害の根拠）
    2. UTF-8 明示指定・errors="replace" による解決を実証する（規約の既定形の効果）
    3. 修正対象ファイルの subprocess.run(...) 呼び出しが実際に encoding="utf-8" を
       渡していることを回帰テストする（GitHistoryParser / r1_inventory）
    4. 修正対象ファイル群を対象に、複数行呼び出しにも対応した括弧対応抽出で
       「encoding= を伴わない subprocess.run(...) が1件も残っていないこと」を
       静的検査する（素朴な行単位 grep の false positive を避ける）
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_SCRIPTS_DIR = _REPO_ROOT / ".claude" / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


# ─────────────────────────────────────────────
# 誤例の実害をロケール非依存に実証する（Red 相当）
# ─────────────────────────────────────────────


def test_cp932_cannot_encode_checkmark_symbol():
    """U+2713 (チェックマーク記号) は cp932 で符号化不能。

    実測 (本 BUILDING セッション): `.claude/hooks/analyzers/scale_detector.py` の
    `format_scale_detection()` がチェックマーク系記号を含む文字列を
    Windows cp932 環境下で `print()` すると `UnicodeEncodeError` が実際に発生し、
    `test_e2e_review.py::TestCLIEntryPoint` 2 件が FAIL していた
    （subprocess-encoding-convention.md §誤例 参照）。
    本テストはその原因（cp932 の文字集合が Unicode 全域をカバーしないこと）を
    ロケール非依存に再現する（テストファイル自体・pytest 失敗出力での表示問題を
    避けるため対象文字は `chr(0x2713)` で構築し、ソース中にリテラル記号を
    埋め込まない）。
    """
    checkmark = chr(0x2713)  # U+2713 CHECK MARK (chr() でリテラル文字混入を回避)
    with pytest.raises(UnicodeEncodeError):
        checkmark.encode("cp932")


def test_cp932_decode_fails_on_utf8_encoded_japanese_bytes():
    """UTF-8 でエンコードされた日本語バイト列は cp932 でデコードできないことがある。

    実測 (本 BUILDING セッション): `/quick-save` 実行時に
    `.claude/scripts/dashboard/parsers/git_history.py`（修正前）が
    `subprocess.run(["git", "log", ...], text=True)`（encoding 未指定）で
    日本語コミットメッセージ（UTF-8）を読み取り、
    `UnicodeDecodeError: 'cp932' codec can't decode byte 0x9c ...` で失敗した。
    本テストはロケール非依存にその失敗モードを再現する。
    """
    utf8_bytes = "ADR-0011 条項トリアージ".encode("utf-8")
    with pytest.raises(UnicodeDecodeError):
        utf8_bytes.decode("cp932")


# ─────────────────────────────────────────────
# 規約の既定形による解決を実証する（Green 相当）
# ─────────────────────────────────────────────


def test_utf8_decode_succeeds_for_same_bytes():
    """同じ UTF-8 バイト列は encoding="utf-8" 指定で正しく往復デコードできる。"""
    original = "ADR-0011 条項トリアージ"
    utf8_bytes = original.encode("utf-8")
    assert utf8_bytes.decode("utf-8") == original


def test_errors_replace_prevents_crash_on_encoding_mismatch():
    """encoding 不一致時でも errors="replace" なら例外を出さず処理を継続できる。

    規約の既定形 `encoding="utf-8", errors="replace"` の後半（安全網）を検証する。
    """
    utf8_bytes = "条項".encode("utf-8")
    result = utf8_bytes.decode("cp932", errors="replace")  # 意図的な不一致
    assert isinstance(result, str)
    assert result != ""


# ─────────────────────────────────────────────
# 修正対象呼び出しの回帰テスト（実際に encoding="utf-8" を渡しているか）
# ─────────────────────────────────────────────


def test_git_history_parser_passes_utf8_encoding_to_subprocess_run():
    """GitHistoryParser._do_parse() が subprocess.run に encoding="utf-8" を渡すこと。"""
    from dashboard.parsers.git_history import GitHistoryParser

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        GitHistoryParser(project_root=_REPO_ROOT).parse()

    _, kwargs = mock_run.call_args
    assert kwargs.get("encoding") == "utf-8"
    assert kwargs.get("errors") == "replace"


def test_r1_inventory_tracked_files_passes_utf8_encoding_to_subprocess_run():
    """r1_inventory._tracked_files() が subprocess.run に encoding="utf-8" を渡すこと。"""
    import r1_inventory

    r1_inventory._TRACKED_FILES_CACHE = None
    try:
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="")
            r1_inventory._tracked_files()

        _, kwargs = mock_run.call_args
        assert kwargs.get("encoding") == "utf-8"
        assert kwargs.get("errors") == "replace"
    finally:
        r1_inventory._TRACKED_FILES_CACHE = None


# ─────────────────────────────────────────────
# 静的検査: 修正対象ファイル群の subprocess.run(...) が
# 複数行呼び出しでも encoding= を伴うこと（規約違反の機構的検出）
# ─────────────────────────────────────────────


def _extract_subprocess_run_calls(source: str) -> list:
    """`subprocess.run(` 呼び出し全体（複数行・括弧対応）をテキストとして抽出する。

    素朴な行単位 grep（`grep "subprocess.run(" | grep -v encoding=`）は、
    `encoding=` が別の行にある複数行呼び出しを誤検出する
    （design.md §4.4 実測 / 本 Task の F1 baseline 実測で確認済み）。
    本関数は開き括弧からの深さカウントで呼び出し全体を1つの文字列として
    切り出し、その全体に対して `encoding=` の有無を判定できるようにする。
    """
    calls = []
    for match in re.finditer(r"subprocess\.run\(", source):
        start = match.end() - 1  # 開き括弧の位置
        depth = 0
        end = None
        for i in range(start, len(source)):
            if source[i] == "(":
                depth += 1
            elif source[i] == ")":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end is not None:
            calls.append(source[match.start():end])
    return calls


# 修正対象と判定した 9 ファイル（W1-R2-T5 F4 判定結果のうち「修正対象」区分。
# 対象外・false positive のファイルは含めない）。
_FIXED_TARGET_FILES = (
    ".claude/scripts/dashboard/parsers/git_history.py",
    ".claude/scripts/r1_inventory.py",
    ".claude/hooks/analyzers/javascript_analyzer.py",
    ".claude/hooks/analyzers/python_analyzer.py",
    ".claude/hooks/analyzers/rust_analyzer.py",
    ".claude/hooks/analyzers/tests/test_e2e_review.py",
    ".claude/hooks/checkers/check_g1_test.py",
    ".claude/hooks/lam-stop-hook.py",
    ".claude/hooks/tests/conftest.py",
)


@pytest.mark.parametrize("rel_path", _FIXED_TARGET_FILES)
def test_fixed_files_all_subprocess_run_calls_declare_utf8_encoding(rel_path):
    """修正対象ファイルの subprocess.run(...) 呼び出しが1件残らず encoding= を伴うこと。

    check_g1_test.py は `--version` 探索呼び出し（対象外 / ASCII 固定出力のみ返す
    例外規定に該当）を含むため、その呼び出しのみ既定形チェックから除外する。
    """
    path = _REPO_ROOT / rel_path
    source = path.read_text(encoding="utf-8")
    calls = _extract_subprocess_run_calls(source)
    assert calls, f"{rel_path} に subprocess.run(...) 呼び出しが見つからない"

    for call_text in calls:
        if rel_path.endswith("check_g1_test.py") and '"--version"' in call_text:
            continue  # 対象外: ASCII 固定出力のみ返す --version 探索（規約の例外規定）
        assert "encoding=" in call_text, (
            f"{rel_path} の subprocess.run 呼び出しに encoding= がない:\n{call_text}"
        )
