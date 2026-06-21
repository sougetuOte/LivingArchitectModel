"""test_session_state_parser.py - SessionStateParser のテスト（W2-B5-T7）

対応仕様: docs/specs/b4-dashboard/design.md §5「SessionStateParser」
         docs/specs/b4-dashboard/tasks.md §3 W2-B5-T7
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest

# .claude/scripts を sys.path に追加（test_base_parser.py と同じパターン）
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# プロジェクトルートの固定パス（実データテスト用）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


# ─────────────────────────────────────────────
# インポートテスト
# ─────────────────────────────────────────────


def test_session_state_parser_importable():
    """SessionStateParser を dashboard.parsers.session_state からインポートできること。"""
    from dashboard.parsers.session_state import SessionStateParser  # noqa: F401


def test_session_state_parser_is_subclass_of_base_parser():
    """SessionStateParser が BaseParser のサブクラスであること。"""
    from dashboard.parsers.base import BaseParser
    from dashboard.parsers.session_state import SessionStateParser

    assert issubclass(SessionStateParser, BaseParser)


# ─────────────────────────────────────────────
# コンストラクタ
# ─────────────────────────────────────────────


def test_init_accepts_project_root(tmp_path):
    """__init__(project_root) でインスタンス化できること。"""
    from dashboard.parsers.session_state import SessionStateParser

    parser = SessionStateParser(tmp_path)
    assert parser is not None


# ─────────────────────────────────────────────
# ファイル不在時の挙動
# ─────────────────────────────────────────────


def test_parse_returns_ok_false_when_file_missing(tmp_path):
    """SESSION_STATE.md が存在しない場合 ok=False を返すこと。"""
    from dashboard.parsers.session_state import SessionStateParser

    parser = SessionStateParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is False
    assert isinstance(result["error"], str)
    assert len(result["error"]) > 0
    assert result["data"] is None


def test_parse_does_not_raise_when_file_missing(tmp_path):
    """SESSION_STATE.md が存在しない場合も例外を外に伝播させないこと。"""
    from dashboard.parsers.session_state import SessionStateParser

    parser = SessionStateParser(tmp_path)
    # 例外が出ないことを確認
    result = parser.parse()
    assert "ok" in result


# ─────────────────────────────────────────────
# 戻り値の構造
# ─────────────────────────────────────────────


def test_parse_returns_dict_with_three_keys(tmp_path):
    """parse() が ok / error / data の 3 キーを持つ dict を返すこと。"""
    from dashboard.parsers.session_state import SessionStateParser

    # ファイルなしでも構造を確認できる
    parser = SessionStateParser(tmp_path)
    result = parser.parse()

    assert "ok" in result
    assert "error" in result
    assert "data" in result


def test_parse_ok_true_returns_required_data_keys(tmp_path):
    """ok=True のとき data に milestones/waves/in_progress/blocked/completed が含まれること。"""
    from dashboard.parsers.session_state import SessionStateParser

    session_state = tmp_path / "SESSION_STATE.md"
    session_state.write_text(
        textwrap.dedent("""\
        # SESSION_STATE

        ## 完了タスク（本セッション）

        - W1-B5-T1: BaseParser 実装完了

        ## 進行中タスク

        - W2-B5-T7: SessionStateParser 実装中

        ## 未解決の問題

        - UQ-3 解決の docs 反映未実施
        """),
        encoding="utf-8",
    )

    parser = SessionStateParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    assert result["error"] is None
    data = result["data"]
    assert "milestones" in data
    assert "waves" in data
    assert "in_progress" in data
    assert "blocked" in data
    assert "completed" in data


def test_parse_data_types(tmp_path):
    """data の各値が正しい型であること（milestones/waves は list、その他も list）。"""
    from dashboard.parsers.session_state import SessionStateParser

    session_state = tmp_path / "SESSION_STATE.md"
    session_state.write_text(
        textwrap.dedent("""\
        # SESSION_STATE

        ## 完了タスク（本セッション）

        ## 進行中タスク

        ## 未解決の問題
        """),
        encoding="utf-8",
    )

    parser = SessionStateParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    data = result["data"]
    assert isinstance(data["milestones"], list)
    assert isinstance(data["waves"], list)
    assert isinstance(data["in_progress"], list)
    assert isinstance(data["blocked"], list)
    assert isinstance(data["completed"], list)


# ─────────────────────────────────────────────
# 進行中タスクのパース
# ─────────────────────────────────────────────


def test_parse_extracts_in_progress_tasks(tmp_path):
    """「進行中タスク」セクションからタスクを抽出できること。"""
    from dashboard.parsers.session_state import SessionStateParser

    session_state = tmp_path / "SESSION_STATE.md"
    session_state.write_text(
        textwrap.dedent("""\
        # SESSION_STATE

        ## 完了タスク（本セッション）

        ## 進行中タスク

        - W2-B5-T7: SessionStateParser 実装中
        - W2-B5-T8: CurrentPhaseParser 実装中

        ## 未解決の問題
        """),
        encoding="utf-8",
    )

    parser = SessionStateParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    in_progress = result["data"]["in_progress"]
    assert len(in_progress) == 2
    assert any("W2-B5-T7" in item for item in in_progress)
    assert any("W2-B5-T8" in item for item in in_progress)


def test_parse_in_progress_none_when_empty_section(tmp_path):
    """「進行中タスク」が「なし」の場合 in_progress は空リストであること。"""
    from dashboard.parsers.session_state import SessionStateParser

    session_state = tmp_path / "SESSION_STATE.md"
    session_state.write_text(
        textwrap.dedent("""\
        # SESSION_STATE

        ## 進行中タスク

        - なし（Wave 1 BUILDING 完了・本セッション末で ship + push 予定）

        ## 完了タスク（本セッション）

        ## 未解決の問題
        """),
        encoding="utf-8",
    )

    parser = SessionStateParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    # "なし" で始まる行は in_progress に含めない
    in_progress = result["data"]["in_progress"]
    assert len(in_progress) == 0


# ─────────────────────────────────────────────
# 完了タスクのパース
# ─────────────────────────────────────────────


def test_parse_extracts_completed_tasks(tmp_path):
    """「完了タスク」セクションからタスクを抽出できること。"""
    from dashboard.parsers.session_state import SessionStateParser

    session_state = tmp_path / "SESSION_STATE.md"
    session_state.write_text(
        textwrap.dedent("""\
        # SESSION_STATE

        ## 完了タスク（本セッション）

        - W1-B5-T1: BaseParser 実装完了
        - W1-B5-T2: build_dashboard.py スケルトン完了

        ## 進行中タスク

        ## 未解決の問題
        """),
        encoding="utf-8",
    )

    parser = SessionStateParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    completed = result["data"]["completed"]
    assert len(completed) == 2
    assert any("W1-B5-T1" in item for item in completed)


# ─────────────────────────────────────────────
# ブロック中タスクのパース
# ─────────────────────────────────────────────


def test_parse_extracts_blocked_tasks(tmp_path):
    """「未解決の問題」セクションからブロック中情報を抽出できること。"""
    from dashboard.parsers.session_state import SessionStateParser

    session_state = tmp_path / "SESSION_STATE.md"
    session_state.write_text(
        textwrap.dedent("""\
        # SESSION_STATE

        ## 完了タスク（本セッション）

        ## 進行中タスク

        ## 未解決の問題

        - UQ-3 解決の docs 反映未実施
        - retro アクション 5 件（次サイクル送り）
        """),
        encoding="utf-8",
    )

    parser = SessionStateParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    blocked = result["data"]["blocked"]
    assert len(blocked) == 2
    assert any("UQ-3" in item for item in blocked)


# ─────────────────────────────────────────────
# Milestone 抽出
# ─────────────────────────────────────────────


def test_parse_extracts_milestone_from_task_ids(tmp_path):
    """タスク ID（W1-B5-T1 等）から Milestone（B-5）を抽出できること。"""
    from dashboard.parsers.session_state import SessionStateParser

    session_state = tmp_path / "SESSION_STATE.md"
    session_state.write_text(
        textwrap.dedent("""\
        # SESSION_STATE

        ## 完了タスク（本セッション）

        - W1-B5-T1: BaseParser 実装完了
        - W1-B5-T2: build_dashboard.py 完了

        ## 進行中タスク

        - W2-B5-T7: SessionStateParser 実装中

        ## 未解決の問題
        """),
        encoding="utf-8",
    )

    parser = SessionStateParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    milestones = result["data"]["milestones"]
    milestone_names = [m.name for m in milestones]
    assert "B-5" in milestone_names


def test_parse_milestone_deduplication(tmp_path):
    """同じ Milestone が複数箇所に出現しても重複排除されること。"""
    from dashboard.parsers.session_state import SessionStateParser

    session_state = tmp_path / "SESSION_STATE.md"
    session_state.write_text(
        textwrap.dedent("""\
        # SESSION_STATE

        ## 完了タスク（本セッション）

        - W1-B5-T1: タスク1
        - W1-B5-T2: タスク2
        - W1-B5-T3: タスク3

        ## 進行中タスク

        - W2-B5-T7: タスク7

        ## 未解決の問題
        """),
        encoding="utf-8",
    )

    parser = SessionStateParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    milestones = result["data"]["milestones"]
    milestone_names = [m.name for m in milestones]
    # B-5 は 1 回だけ
    assert milestone_names.count("B-5") == 1


def test_parse_milestone_returns_milestone_info_objects(tmp_path):
    """milestones が MilestoneInfo オブジェクトのリストであること。"""
    from dashboard.models import MilestoneInfo
    from dashboard.parsers.session_state import SessionStateParser

    session_state = tmp_path / "SESSION_STATE.md"
    session_state.write_text(
        textwrap.dedent("""\
        # SESSION_STATE

        ## 完了タスク（本セッション）

        - W1-B5-T1: タスク1

        ## 進行中タスク

        ## 未解決の問題
        """),
        encoding="utf-8",
    )

    parser = SessionStateParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    milestones = result["data"]["milestones"]
    for m in milestones:
        assert isinstance(m, MilestoneInfo)


def test_parse_extracts_b4_milestone(tmp_path):
    """B-4 形式の Milestone も抽出できること（[A-Z]-\\d+ パターン）。"""
    from dashboard.parsers.session_state import SessionStateParser

    session_state = tmp_path / "SESSION_STATE.md"
    session_state.write_text(
        textwrap.dedent("""\
        # SESSION_STATE

        ## 完了タスク（本セッション）

        - W7-B4-T9: fat 削減タスク完了

        ## 進行中タスク

        ## 未解決の問題
        """),
        encoding="utf-8",
    )

    parser = SessionStateParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    milestone_names = [m.name for m in result["data"]["milestones"]]
    assert "B-4" in milestone_names


# ─────────────────────────────────────────────
# Wave 抽出
# ─────────────────────────────────────────────


def test_parse_extracts_waves_from_task_ids(tmp_path):
    """タスク ID から Wave 情報（wave_number）を抽出できること。"""
    from dashboard.parsers.session_state import SessionStateParser

    session_state = tmp_path / "SESSION_STATE.md"
    session_state.write_text(
        textwrap.dedent("""\
        # SESSION_STATE

        ## 完了タスク（本セッション）

        - W1-B5-T1: タスク1（Wave 1）

        ## 進行中タスク

        - W2-B5-T7: タスク7（Wave 2）

        ## 未解決の問題
        """),
        encoding="utf-8",
    )

    parser = SessionStateParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    waves = result["data"]["waves"]
    wave_numbers = [w.wave_number for w in waves]
    assert "1" in wave_numbers
    assert "2" in wave_numbers


def test_parse_waves_returns_wave_info_objects(tmp_path):
    """waves が WaveInfo オブジェクトのリストであること。"""
    from dashboard.models import WaveInfo
    from dashboard.parsers.session_state import SessionStateParser

    session_state = tmp_path / "SESSION_STATE.md"
    session_state.write_text(
        textwrap.dedent("""\
        # SESSION_STATE

        ## 完了タスク（本セッション）

        - W1-B5-T1: タスク1

        ## 進行中タスク

        ## 未解決の問題
        """),
        encoding="utf-8",
    )

    parser = SessionStateParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    waves = result["data"]["waves"]
    for w in waves:
        assert isinstance(w, WaveInfo)


def test_parse_wave_deduplication(tmp_path):
    """同じ Wave が複数タスクに出現しても重複排除されること。"""
    from dashboard.parsers.session_state import SessionStateParser

    session_state = tmp_path / "SESSION_STATE.md"
    session_state.write_text(
        textwrap.dedent("""\
        # SESSION_STATE

        ## 完了タスク（本セッション）

        - W1-B5-T1: タスク1
        - W1-B5-T2: タスク2
        - W1-B5-T3: タスク3

        ## 進行中タスク

        ## 未解決の問題
        """),
        encoding="utf-8",
    )

    parser = SessionStateParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    waves = result["data"]["waves"]
    # B-5 の Wave 1 は 1 件だけ
    b5_w1 = [w for w in waves if w.milestone == "B-5" and w.wave_number == "1"]
    assert len(b5_w1) == 1


# ─────────────────────────────────────────────
# 見出しのばらつき対応（UQ-1 Spike）
# ─────────────────────────────────────────────


def test_parse_handles_h2_section_heading(tmp_path):
    """## 見出しのセクションを正しくパースできること。"""
    from dashboard.parsers.session_state import SessionStateParser

    session_state = tmp_path / "SESSION_STATE.md"
    session_state.write_text(
        textwrap.dedent("""\
        # SESSION_STATE

        ## 完了タスク（本セッション）

        - W1-B5-T1: 完了

        ## 進行中タスク

        - W2-B5-T7: 進行中

        ## 未解決の問題

        - 問題1
        """),
        encoding="utf-8",
    )

    parser = SessionStateParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    assert len(result["data"]["completed"]) == 1
    assert len(result["data"]["in_progress"]) == 1
    assert len(result["data"]["blocked"]) == 1


def test_parse_handles_section_without_tasks(tmp_path):
    """セクションが存在するがタスク行がない場合でも ok=True で空リストを返すこと。"""
    from dashboard.parsers.session_state import SessionStateParser

    session_state = tmp_path / "SESSION_STATE.md"
    session_state.write_text(
        textwrap.dedent("""\
        # SESSION_STATE

        ## 完了タスク（本セッション）

        （なし）

        ## 進行中タスク

        ## 未解決の問題
        """),
        encoding="utf-8",
    )

    parser = SessionStateParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    assert result["data"]["completed"] == []
    assert result["data"]["in_progress"] == []
    assert result["data"]["blocked"] == []


def test_parse_handles_table_rows_in_completed_section(tmp_path):
    """「完了タスク」セクションにテーブル形式の記述があっても ok=True で返すこと。

    実 SESSION_STATE.md では完了タスクがマークダウンテーブルで記述されている場合がある。
    テーブル行（| W1-B5-T1 | ... |）からも Milestone/Wave 情報を抽出できること。
    """
    from dashboard.parsers.session_state import SessionStateParser

    session_state = tmp_path / "SESSION_STATE.md"
    session_state.write_text(
        textwrap.dedent("""\
        # SESSION_STATE

        ## 完了タスク（本セッション）

        | Task | 成果物 | ステータス |
        |------|-------|----------|
        | W1-B5-T1 | base.py | PASS |
        | W1-B5-T2 | build_dashboard.py | PASS |

        ## 進行中タスク

        ## 未解決の問題
        """),
        encoding="utf-8",
    )

    parser = SessionStateParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    # テーブル行からも B-5 / Wave 1 が抽出される
    milestone_names = [m.name for m in result["data"]["milestones"]]
    assert "B-5" in milestone_names


# ─────────────────────────────────────────────
# 実データテスト（R-6: 設計書出力ファイル存在確認）
# ─────────────────────────────────────────────


def test_parse_real_session_state_file():
    """実 SESSION_STATE.md（プロジェクトルート）でパースが通ること。"""
    from dashboard.parsers.session_state import SessionStateParser

    session_file = _PROJECT_ROOT / "SESSION_STATE.md"
    if not session_file.exists():
        pytest.skip("SESSION_STATE.md が存在しないためスキップ")

    parser = SessionStateParser(_PROJECT_ROOT)
    result = parser.parse()

    # 実ファイルが存在するので ok=True であること
    assert result["ok"] is True
    assert result["data"] is not None


def test_parse_real_session_state_contains_b5_milestone():
    """実 SESSION_STATE.md から B-5 が milestones に含まれること。"""
    from dashboard.parsers.session_state import SessionStateParser

    session_file = _PROJECT_ROOT / "SESSION_STATE.md"
    if not session_file.exists():
        pytest.skip("SESSION_STATE.md が存在しないためスキップ")

    parser = SessionStateParser(_PROJECT_ROOT)
    result = parser.parse()

    assert result["ok"] is True
    milestone_names = [m.name for m in result["data"]["milestones"]]
    assert "B-5" in milestone_names


def test_parse_real_session_state_contains_wave():
    """実 SESSION_STATE.md から Wave 情報が waves に含まれること。"""
    from dashboard.parsers.session_state import SessionStateParser

    session_file = _PROJECT_ROOT / "SESSION_STATE.md"
    if not session_file.exists():
        pytest.skip("SESSION_STATE.md が存在しないためスキップ")

    parser = SessionStateParser(_PROJECT_ROOT)
    result = parser.parse()

    assert result["ok"] is True
    waves = result["data"]["waves"]
    assert len(waves) >= 1


def test_parse_real_session_state_has_valid_data_structure():
    """実 SESSION_STATE.md のパース結果が正しいデータ構造を持つこと。"""
    from dashboard.models import MilestoneInfo, WaveInfo
    from dashboard.parsers.session_state import SessionStateParser

    session_file = _PROJECT_ROOT / "SESSION_STATE.md"
    if not session_file.exists():
        pytest.skip("SESSION_STATE.md が存在しないためスキップ")

    parser = SessionStateParser(_PROJECT_ROOT)
    result = parser.parse()

    assert result["ok"] is True
    data = result["data"]

    # 型チェック
    assert isinstance(data["milestones"], list)
    assert isinstance(data["waves"], list)
    assert isinstance(data["in_progress"], list)
    assert isinstance(data["blocked"], list)
    assert isinstance(data["completed"], list)

    for m in data["milestones"]:
        assert isinstance(m, MilestoneInfo)
        assert isinstance(m.name, str)
        assert len(m.name) > 0

    for w in data["waves"]:
        assert isinstance(w, WaveInfo)
        assert isinstance(w.wave_number, str)
        assert isinstance(w.milestone, str)
