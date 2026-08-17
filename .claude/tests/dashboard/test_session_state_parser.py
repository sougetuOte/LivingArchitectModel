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


def test_parse_real_session_state_contains_milestone():
    """実 SESSION_STATE.md が Milestone の状態を**宣言**しており、それが解釈可能なこと。

    2026-08-17 に検査対象を変更した（rule-001 §構造的論点の恒久解 (c)）。

    旧: 「[A-Z]-N 形式の Milestone が 1 件以上抽出されること」。これは Milestone 不在期に
        (i) 痕跡テキストの保持を強制する（観測 #5 / 赤くなる形）か、
        (ii) 過去への言及から誤った現在状態を導出して**緑のまま嘘をつく**（2026-08-17 /
             `W1-D1-T1` というセッション 18 の記録 1 箇所から `D-1 / in-progress` を導出。
             D-1 は 2026-08-13 クローズ済）
        のいずれかになる。

    新: **宣言欄が存在し解釈可能であること**を検査する。「なし」は正当な値であり、
        パターンの残存を要求しない。推論をやめて宣言を読む（R3 機構 #7 で採った
        「維持リストではなく基質から導出する」と同型の手）。
    """
    from dashboard.parsers.session_state import SessionStateParser, parse_declared_milestone

    session_file = _PROJECT_ROOT / "SESSION_STATE.md"
    if not session_file.exists():
        pytest.skip("SESSION_STATE.md が存在しないためスキップ")

    declared = parse_declared_milestone(session_file.read_text(encoding="utf-8"))
    assert declared is not None, (
        "SESSION_STATE.md に `**現在の Milestone**:` 宣言欄がない。"
        "欄を追加すること（値は Milestone 名または「なし」）"
    )
    # 「なし」も Milestone 名も正当。ただし**どちらとも解釈できない値は不可**
    # （典型: 誤字。ここを緩めると宣言欄が黙って「なし」に化ける）
    assert declared.interpretable, f"宣言欄の値が解釈できない: {declared.raw!r}"
    if declared.name is not None:
        import re

        assert re.fullmatch(r"[A-Z]-\d+", declared.name)

    result = SessionStateParser(_PROJECT_ROOT).parse()
    assert result["ok"] is True
    names = [m.name for m in result["data"]["milestones"]]
    if declared.name is None:
        assert names == [], f"Milestone なしと宣言されているのに抽出された: {names}"
    else:
        assert declared.name in names


def test_parse_real_session_state_contains_wave():
    """実 SESSION_STATE.md の waves が、宣言された Milestone 状態と整合すること。

    2026-08-17 に検査対象を変更（上記 test_..._contains_milestone と同じ恒久解）。
    旧: `len(waves) >= 1` を無条件に要求 → Milestone 不在期に嘘の緑を生んでいた。
    """
    from dashboard.parsers.session_state import SessionStateParser, parse_declared_milestone

    session_file = _PROJECT_ROOT / "SESSION_STATE.md"
    if not session_file.exists():
        pytest.skip("SESSION_STATE.md が存在しないためスキップ")

    declared = parse_declared_milestone(session_file.read_text(encoding="utf-8"))
    assert declared is not None

    waves = SessionStateParser(_PROJECT_ROOT).parse()["data"]["waves"]
    if declared.name is None:
        assert waves == [], f"Milestone なしと宣言されているのに Wave が導出された: {waves}"


# --- 宣言欄の解析（2026-08-17 / rule-001 恒久解 (c)）---------------------------


def _session_state_with(tmp_path, body: str):
    (tmp_path / "SESSION_STATE.md").write_text(body, encoding="utf-8")
    return tmp_path


def test_parse_declared_milestone_returns_none_when_field_absent():
    """宣言欄が無ければ None（= 旧書式）。legacy 経路へ落とすための判定。"""
    from dashboard.parsers.session_state import parse_declared_milestone

    assert parse_declared_milestone("# SESSION_STATE\n\n本文のみ\n") is None


def test_parse_declared_milestone_reads_none_value():
    """`**なし**（注釈）` を「Milestone なし」として解釈する。"""
    from dashboard.parsers.session_state import parse_declared_milestone

    declared = parse_declared_milestone(
        "**現在の Milestone**: **なし**（D-1 は 2026-08-13 クローズ）\n"
    )
    assert declared is not None
    assert declared.name is None


def test_parse_declared_milestone_reads_milestone_name():
    """`**B-5**（注釈）` から B-5 を取り出す。"""
    from dashboard.parsers.session_state import parse_declared_milestone

    declared = parse_declared_milestone("**現在の Milestone**: **B-5**（BUILDING 中）\n")
    assert declared is not None
    assert declared.name == "B-5"


def test_declared_none_suppresses_prose_inference(tmp_path):
    """宣言が「なし」なら、散文中の履歴 task ID から Milestone を導出しない。

    2026-08-17 のバグの回帰テスト: `W1-D1-T1` は過去セッションの記録であり、
    現在の状態ではない。
    """
    from dashboard.parsers.session_state import SessionStateParser

    root = _session_state_with(
        tmp_path,
        "# SESSION_STATE\n\n"
        "**現在の Milestone**: **なし**（D-1 は 2026-08-13 クローズ）\n\n"
        "## 参考: 直近実績\n\n- セッション 18: W1-D1-T1 完了\n",
    )
    data = SessionStateParser(root).parse()["data"]
    assert data["milestones"] == []
    assert data["waves"] == []


def test_declared_milestone_is_authoritative(tmp_path):
    """宣言された Milestone が正本であり、散文の別 Milestone に上書きされない。"""
    from dashboard.parsers.session_state import SessionStateParser

    root = _session_state_with(
        tmp_path,
        "# SESSION_STATE\n\n"
        "**現在の Milestone**: **B-5**\n\n"
        "## 参考: 直近実績\n\n- セッション 18: W1-D1-T1 完了\n",
    )
    names = [m.name for m in SessionStateParser(root).parse()["data"]["milestones"]]
    assert names == ["B-5"]


def test_absent_declaration_preserves_legacy_inference(tmp_path):
    """宣言欄が無い旧書式では、従来どおり task ID から推論する（後方互換）。"""
    from dashboard.parsers.session_state import SessionStateParser

    root = _session_state_with(
        tmp_path, "# SESSION_STATE\n\n## 完了タスク\n\n- W1-D1-T1 完了\n"
    )
    data = SessionStateParser(root).parse()["data"]
    assert [m.name for m in data["milestones"]] == ["D-1"]
    assert len(data["waves"]) == 1


def test_fallback_milestone_regex_matches_r_series():
    """R-1 W-R1 S1 T6: fallback milestone regex が R-N 系を捕捉 (旧 B-N 専用の恒久解)."""
    from dashboard.parsers.session_state import _FALLBACK_MILESTONE_RE

    content = "現在の Milestone は R-1 (前 Milestone = B-5)。"
    matches = [m.group(1) for m in _FALLBACK_MILESTONE_RE.finditer(content)]
    assert "R-1" in matches
    assert "B-5" in matches


def test_fallback_milestone_regex_matches_any_letter_prefix():
    """R-1 W-R1 S1 T6: [A-Z]-N の任意 1 文字 prefix を捕捉 (将来の命名体系変更に耐性)."""
    from dashboard.parsers.session_state import _FALLBACK_MILESTONE_RE

    for token in ["A-1", "B-5", "C-10", "R-1", "S-3", "Z-99"]:
        content = f"context {token} context"
        matches = [m.group(1) for m in _FALLBACK_MILESTONE_RE.finditer(content)]
        assert token in matches, f"{token} not captured by _FALLBACK_MILESTONE_RE"


def test_fallback_wave_hyphen_regex_matches_w_r_series():
    """R-1 W-R1 S1 T6: fallback wave regex が W-R1 系 (ハイフン記法) を捕捉."""
    from dashboard.parsers.session_state import _FALLBACK_WAVE_HYPHEN_RE

    content = "W-R1 S1 T6 進行中。W-R2 は次 Wave。"
    matches = [m.group(1) for m in _FALLBACK_WAVE_HYPHEN_RE.finditer(content)]
    assert "R1" in matches
    assert "R2" in matches


def test_fallback_wave_regex_still_matches_plain_wave():
    """R-1 W-R1 S1 T6: 旧 "Wave N" 記法も引き続き捕捉 (後方互換)."""
    from dashboard.parsers.session_state import _FALLBACK_WAVE_RE

    content = "Wave 1 完了。Wave 1.5 で fix。Wave 8 が最終。"
    matches = [m.group(1) for m in _FALLBACK_WAVE_RE.finditer(content)]
    assert "1" in matches
    assert "1.5" in matches
    assert "8" in matches


def test_parse_r_series_synthetic_session_state(tmp_path):
    """R-1 W-R1 S1 T6: R-N milestone + W-R N wave のみの SESSION_STATE.md を parse できる.

    「B-5 Wave 8」応急措置に依存せず R-1 系表記のみで milestones/waves が抽出されることを保証。
    """
    from dashboard.parsers.session_state import SessionStateParser

    session_content = (
        "# SESSION_STATE\n"
        "\n"
        "**現在の Milestone**: R-1 (大規模レビュー & リファクタリング)\n"
        "\n"
        "## 進行中タスク\n"
        "- W-R1 S1 T6: rule-001 拡張中\n"
        "\n"
        "## 次のステップ\n"
        "- W-R1 S1 T7: Stage 末 ship\n"
    )
    session_file = tmp_path / "SESSION_STATE.md"
    session_file.write_text(session_content, encoding="utf-8")

    parser = SessionStateParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    milestone_names = [m.name for m in result["data"]["milestones"]]
    assert "R-1" in milestone_names
    wave_nums = [w.wave_number for w in result["data"]["waves"]]
    assert "R1" in wave_nums


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
