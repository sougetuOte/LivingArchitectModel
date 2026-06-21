"""test_git_history_parser.py - GitHistoryParser のテスト（W3-B5-T13）

対応仕様: docs/specs/b4-dashboard/design.md §5「GitHistoryParser」
実装判断: git log --oneline -100 の出力から Wave/Task 完了情報を抽出。
          コミットメッセージは Conventional Commits 形式（terminology.md §4）。
          実データパターン例:
            feat(B-5): b4-dashboard Wave 2 パーサ層（W2-B5-T7〜T11・テスト 144/144 PASS）
            chore(phase): AUDITING → BUILDING 復帰（Wave 2 docs 同期）
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# .claude/scripts を sys.path に追加
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# プロジェクトルートは .claude/ の 1 つ上
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


# ─────────────────────────────────────────────
# インポートテスト
# ─────────────────────────────────────────────


def test_git_history_parser_importable():
    """GitHistoryParser を dashboard.parsers.git_history からインポートできること。"""
    from dashboard.parsers.git_history import GitHistoryParser  # noqa: F401


# ─────────────────────────────────────────────
# クラス定義・継承テスト
# ─────────────────────────────────────────────


def test_git_history_parser_is_subclass_of_base_parser():
    """GitHistoryParser が BaseParser のサブクラスであること。"""
    from dashboard.parsers.base import BaseParser
    from dashboard.parsers.git_history import GitHistoryParser

    assert issubclass(GitHistoryParser, BaseParser)


def test_git_history_parser_accepts_project_root():
    """GitHistoryParser(project_root) でインスタンス化できること。"""
    from dashboard.parsers.git_history import GitHistoryParser

    parser = GitHistoryParser(project_root=_PROJECT_ROOT)
    assert parser is not None


# ─────────────────────────────────────────────
# parse() 戻り値の構造
# ─────────────────────────────────────────────


def test_parse_returns_dict_with_three_keys():
    """parse() の戻り値が ok / error / data の 3 キーを持つこと。"""
    from dashboard.parsers.git_history import GitHistoryParser

    fake_log = "abc1234 feat(B-5): Wave 2 実装\ndef5678 chore(phase): BUILDING\n"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=fake_log, stderr="")
        parser = GitHistoryParser(project_root=_PROJECT_ROOT)
        result = parser.parse()

    assert isinstance(result, dict)
    assert "ok" in result
    assert "error" in result
    assert "data" in result


def test_parse_ok_is_bool():
    """parse() の ok フィールドが bool 型であること。"""
    from dashboard.parsers.git_history import GitHistoryParser

    fake_log = "abc1234 feat(B-5): Wave 2 実装\n"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=fake_log, stderr="")
        result = GitHistoryParser(project_root=_PROJECT_ROOT).parse()

    assert isinstance(result["ok"], bool)


# ─────────────────────────────────────────────
# 正常系: git log 成功
# ─────────────────────────────────────────────


def test_parse_returns_ok_true_on_success():
    """git log 成功時に ok=True を返すこと。"""
    from dashboard.parsers.git_history import GitHistoryParser

    fake_log = "abc1234 feat(B-5): Wave 2 実装（W2-B5-T7〜T11・テスト 144/144 PASS）\n"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=fake_log, stderr="")
        result = GitHistoryParser(project_root=_PROJECT_ROOT).parse()

    assert result["ok"] is True
    assert result["error"] is None
    assert result["data"] is not None


def test_parse_data_has_completed_waves_key():
    """ok=True のとき data に completed_waves キーが存在すること。"""
    from dashboard.parsers.git_history import GitHistoryParser

    fake_log = "abc1234 feat(B-5): Wave 2 実装\n"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=fake_log, stderr="")
        result = GitHistoryParser(project_root=_PROJECT_ROOT).parse()

    assert "completed_waves" in result["data"]


def test_parse_data_has_completed_tasks_key():
    """ok=True のとき data に completed_tasks キーが存在すること。"""
    from dashboard.parsers.git_history import GitHistoryParser

    fake_log = "abc1234 feat(B-5): Wave 2 実装\n"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=fake_log, stderr="")
        result = GitHistoryParser(project_root=_PROJECT_ROOT).parse()

    assert "completed_tasks" in result["data"]


def test_parse_completed_waves_is_list():
    """data["completed_waves"] が list 型であること。"""
    from dashboard.parsers.git_history import GitHistoryParser

    fake_log = "abc1234 feat(B-5): Wave 2 実装\n"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=fake_log, stderr="")
        result = GitHistoryParser(project_root=_PROJECT_ROOT).parse()

    assert isinstance(result["data"]["completed_waves"], list)


def test_parse_completed_tasks_is_list():
    """data["completed_tasks"] が list 型であること。"""
    from dashboard.parsers.git_history import GitHistoryParser

    fake_log = "abc1234 feat(B-5): Wave 2 実装\n"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=fake_log, stderr="")
        result = GitHistoryParser(project_root=_PROJECT_ROOT).parse()

    assert isinstance(result["data"]["completed_tasks"], list)


# ─────────────────────────────────────────────
# 正常系: Wave 抽出 regex
# ─────────────────────────────────────────────


def test_parse_extracts_wave_number_from_commit_message():
    """「Wave 2」形式のコミットメッセージから Wave 番号を抽出すること。"""
    from dashboard.parsers.git_history import GitHistoryParser

    fake_log = "abc1234 feat(B-5): b4-dashboard Wave 2 パーサ層実装\n"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=fake_log, stderr="")
        result = GitHistoryParser(project_root=_PROJECT_ROOT).parse()

    assert result["ok"] is True
    assert "2" in result["data"]["completed_waves"]


def test_parse_extracts_wave_with_decimal_point():
    """「Wave 1.5」形式のコミットメッセージから Wave 1.5 を抽出すること。"""
    from dashboard.parsers.git_history import GitHistoryParser

    fake_log = "abc1234 docs(B-5): B-4 Wave 1.5 波及不整合修正（W-1〜W-5）\n"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=fake_log, stderr="")
        result = GitHistoryParser(project_root=_PROJECT_ROOT).parse()

    assert result["ok"] is True
    assert "1.5" in result["data"]["completed_waves"]


def test_parse_extracts_wave_case_insensitive():
    """「wave 2」（小文字）でも Wave を抽出すること。"""
    from dashboard.parsers.git_history import GitHistoryParser

    fake_log = "abc1234 feat(B-5): b4-dashboard wave 2 実装\n"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=fake_log, stderr="")
        result = GitHistoryParser(project_root=_PROJECT_ROOT).parse()

    assert result["ok"] is True
    assert "2" in result["data"]["completed_waves"]


def test_parse_deduplicates_waves():
    """同じ Wave 番号が複数行に現れても重複しないこと。"""
    from dashboard.parsers.git_history import GitHistoryParser

    fake_log = (
        "abc1234 feat(B-5): Wave 2 パーサ層実装\n"
        "def5678 fix(B-5): Wave 2 バグ修正\n"
    )
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=fake_log, stderr="")
        result = GitHistoryParser(project_root=_PROJECT_ROOT).parse()

    assert result["ok"] is True
    wave_list = result["data"]["completed_waves"]
    assert wave_list.count("2") == 1


def test_parse_extracts_multiple_wave_numbers():
    """複数の Wave 番号を含むコミット履歴から全 Wave を抽出すること。"""
    from dashboard.parsers.git_history import GitHistoryParser

    fake_log = (
        "abc1234 feat(B-5): Wave 2 実装\n"
        "def5678 feat(B-5): Wave 1 骨格実装\n"
    )
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=fake_log, stderr="")
        result = GitHistoryParser(project_root=_PROJECT_ROOT).parse()

    assert result["ok"] is True
    waves = result["data"]["completed_waves"]
    assert "1" in waves
    assert "2" in waves


# ─────────────────────────────────────────────
# 正常系: Task 抽出 regex
# ─────────────────────────────────────────────


def test_parse_extracts_task_id_w_format():
    """「W2-B5-T7」形式の Task ID をコミットメッセージから抽出すること。"""
    from dashboard.parsers.git_history import GitHistoryParser

    fake_log = "abc1234 feat(B-5): Wave 2 実装（W2-B5-T7〜T11・テスト 144/144 PASS）\n"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=fake_log, stderr="")
        result = GitHistoryParser(project_root=_PROJECT_ROOT).parse()

    assert result["ok"] is True
    assert "W2-B5-T7" in result["data"]["completed_tasks"]


def test_parse_extracts_task_id_short_format():
    """「W7-T2b」形式（Milestone 省略）の Task ID も抽出すること。"""
    from dashboard.parsers.git_history import GitHistoryParser

    fake_log = "abc1234 docs(specs): W7-T2b + PM-G3 完了チェック記入\n"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=fake_log, stderr="")
        result = GitHistoryParser(project_root=_PROJECT_ROOT).parse()

    assert result["ok"] is True
    assert "W7-T2b" in result["data"]["completed_tasks"]


def test_parse_deduplicates_tasks():
    """同じ Task ID が複数行に現れても重複しないこと。"""
    from dashboard.parsers.git_history import GitHistoryParser

    fake_log = (
        "abc1234 feat(B-5): W2-B5-T7 実装\n"
        "def5678 fix(B-5): W2-B5-T7 バグ修正\n"
    )
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=fake_log, stderr="")
        result = GitHistoryParser(project_root=_PROJECT_ROOT).parse()

    assert result["ok"] is True
    tasks = result["data"]["completed_tasks"]
    assert tasks.count("W2-B5-T7") == 1


def test_parse_returns_empty_lists_when_no_patterns_match():
    """Wave / Task のパターンにマッチしないコミットのとき空リストを返すこと（ok=True）。"""
    from dashboard.parsers.git_history import GitHistoryParser

    fake_log = "abc1234 chore: gitignore 更新\ndef5678 docs: README 修正\n"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=fake_log, stderr="")
        result = GitHistoryParser(project_root=_PROJECT_ROOT).parse()

    assert result["ok"] is True
    assert result["data"]["completed_waves"] == []
    assert result["data"]["completed_tasks"] == []


def test_parse_returns_empty_lists_when_git_log_empty():
    """git log 出力が空文字列のとき空リストを返すこと（ok=True）。"""
    from dashboard.parsers.git_history import GitHistoryParser

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        result = GitHistoryParser(project_root=_PROJECT_ROOT).parse()

    assert result["ok"] is True
    assert result["data"]["completed_waves"] == []
    assert result["data"]["completed_tasks"] == []


# ─────────────────────────────────────────────
# エラー系: git コマンド失敗
# ─────────────────────────────────────────────


def test_parse_returns_ok_false_when_returncode_nonzero():
    """git log が非ゼロ終了コードを返したとき ok=False を返すこと（FR-6）。"""
    from dashboard.parsers.git_history import GitHistoryParser

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=128, stdout="", stderr="fatal: not a git repository"
        )
        result = GitHistoryParser(project_root=_PROJECT_ROOT).parse()

    assert result["ok"] is False
    assert isinstance(result["error"], str)
    assert len(result["error"]) > 0
    assert result["data"] is None


def test_parse_error_message_contains_stderr_on_git_failure():
    """git log 失敗時の error メッセージに stderr の内容が含まれること。"""
    from dashboard.parsers.git_history import GitHistoryParser

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=128, stdout="", stderr="fatal: not a git repository"
        )
        result = GitHistoryParser(project_root=_PROJECT_ROOT).parse()

    assert result["ok"] is False
    assert "fatal: not a git repository" in result["error"]


def test_parse_returns_ok_false_when_file_not_found_error():
    """subprocess.run が FileNotFoundError（git コマンドが存在しない）を投げても ok=False を返すこと。"""
    from dashboard.parsers.git_history import GitHistoryParser

    with patch("subprocess.run", side_effect=FileNotFoundError("git: command not found")):
        result = GitHistoryParser(project_root=_PROJECT_ROOT).parse()

    assert result["ok"] is False
    assert isinstance(result["error"], str)
    assert result["data"] is None


def test_parse_returns_ok_false_when_os_error():
    """subprocess.run が OSError を投げても ok=False を返すこと。"""
    from dashboard.parsers.git_history import GitHistoryParser

    with patch("subprocess.run", side_effect=OSError("permission denied")):
        result = GitHistoryParser(project_root=_PROJECT_ROOT).parse()

    assert result["ok"] is False
    assert result["data"] is None


# ─────────────────────────────────────────────
# 例外を外に伝播させない
# ─────────────────────────────────────────────


def test_parse_does_not_raise_on_git_not_found():
    """FileNotFoundError 時に例外を外に伝播させないこと。"""
    from dashboard.parsers.git_history import GitHistoryParser

    try:
        with patch("subprocess.run", side_effect=FileNotFoundError("git not found")):
            result = GitHistoryParser(project_root=_PROJECT_ROOT).parse()
        assert result["ok"] is False
    except Exception as exc:
        pytest.fail(f"parse() が例外を外に伝播させた: {exc}")


def test_parse_does_not_raise_on_git_failure():
    """git log 非ゼロ終了時に例外を外に伝播させないこと。"""
    from dashboard.parsers.git_history import GitHistoryParser

    try:
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
            result = GitHistoryParser(project_root=_PROJECT_ROOT).parse()
        assert result["ok"] is False
    except Exception as exc:
        pytest.fail(f"parse() が例外を外に伝播させた: {exc}")


def test_parse_does_not_raise_on_unexpected_exception():
    """予期しない例外（RuntimeError 等）も外に伝播させないこと。"""
    from dashboard.parsers.git_history import GitHistoryParser

    try:
        with patch("subprocess.run", side_effect=RuntimeError("unexpected")):
            result = GitHistoryParser(project_root=_PROJECT_ROOT).parse()
        assert result["ok"] is False
    except Exception as exc:
        pytest.fail(f"parse() が例外を外に伝播させた: {exc}")


# ─────────────────────────────────────────────
# 実データテスト（プロジェクトルートの実 git log）
# ─────────────────────────────────────────────


def test_parse_with_real_git_log():
    """実プロジェクトの git log を走査し、少なくとも 1 件以上の Wave を検出すること（UQ-4）。

    実 git log のパターン（確認済み）:
        feat(B-5): b4-dashboard Wave 2 パーサ層 + V-2 ビュー実装（W2-B5-T7〜T11・テスト 144/144 PASS）
        feat(B-5): b4-dashboard Wave 1 骨格実装 (W1-B5-T1〜T5, テスト 47/47 PASS)
        docs(B-5): B-4 Wave 1.5 波及不整合修正（W-1〜W-5）
    """
    from dashboard.parsers.git_history import GitHistoryParser

    parser = GitHistoryParser(project_root=_PROJECT_ROOT)
    result = parser.parse()

    # git が存在しない環境では skip
    if not result["ok"]:
        pytest.skip(f"git log 実行失敗（CI 環境の可能性）: {result['error']}")

    assert result["data"] is not None
    waves = result["data"]["completed_waves"]
    tasks = result["data"]["completed_tasks"]

    # 実 git log には "Wave 1", "Wave 2", "Wave 1.5" 等が存在するはず
    assert len(waves) >= 1, f"Wave が 1 件も検出されなかった（completed_waves={waves}）"

    # 実 git log には "W2-B5-T7", "W1-B5-T1" 等の Task ID が存在するはず
    assert len(tasks) >= 1, f"Task が 1 件も検出されなかった（completed_tasks={tasks}）"
