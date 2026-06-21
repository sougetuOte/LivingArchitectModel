r"""test_current_phase_parser.py - CurrentPhaseParser のテスト（W2-B5-T8）

対応仕様: docs/specs/b4-dashboard/design.md §5「CurrentPhaseParser」
実装判断: L1 確定。仕様の「1行目 strip()」ではなく実データ構造に合わせ
           regex ``\*\*(PLANNING|BUILDING|AUDITING|AUTONOMOUS)\*\*`` で全文抽出。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# .claude/scripts を sys.path に追加（test_base_parser.py と同じパターン）
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# プロジェクトルートは .claude/ の 1 つ上
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


# ─────────────────────────────────────────────
# インポートテスト
# ─────────────────────────────────────────────


def test_current_phase_parser_importable():
    """CurrentPhaseParser を dashboard.parsers.current_phase からインポートできること。"""
    from dashboard.parsers.current_phase import CurrentPhaseParser  # noqa: F401


# ─────────────────────────────────────────────
# クラス定義・継承テスト
# ─────────────────────────────────────────────


def test_current_phase_parser_is_subclass_of_base_parser():
    """CurrentPhaseParser が BaseParser のサブクラスであること。"""
    from dashboard.parsers.base import BaseParser
    from dashboard.parsers.current_phase import CurrentPhaseParser

    assert issubclass(CurrentPhaseParser, BaseParser)


def test_current_phase_parser_accepts_project_root():
    """CurrentPhaseParser(project_root) でインスタンス化できること。"""
    from dashboard.parsers.current_phase import CurrentPhaseParser

    parser = CurrentPhaseParser(project_root=_PROJECT_ROOT)
    assert parser is not None


# ─────────────────────────────────────────────
# parse() 戻り値の構造
# ─────────────────────────────────────────────


def test_parse_returns_dict_with_three_keys(tmp_path):
    """parse() の戻り値が ok / error / data の 3 キーを持つこと。"""
    from dashboard.parsers.current_phase import CurrentPhaseParser

    phase_file = tmp_path / ".claude" / "current-phase.md"
    phase_file.parent.mkdir(parents=True)
    phase_file.write_text("# Current Phase\n\n**PLANNING**\n", encoding="utf-8")

    parser = CurrentPhaseParser(project_root=tmp_path)
    result = parser.parse()

    assert isinstance(result, dict)
    assert "ok" in result
    assert "error" in result
    assert "data" in result


def test_parse_ok_is_bool(tmp_path):
    """parse() の ok フィールドが bool 型であること。"""
    from dashboard.parsers.current_phase import CurrentPhaseParser

    phase_file = tmp_path / ".claude" / "current-phase.md"
    phase_file.parent.mkdir(parents=True)
    phase_file.write_text("# Current Phase\n\n**BUILDING**\n", encoding="utf-8")

    result = CurrentPhaseParser(project_root=tmp_path).parse()
    assert isinstance(result["ok"], bool)


# ─────────────────────────────────────────────
# 正常系: Phase 名抽出
# ─────────────────────────────────────────────


def test_parse_returns_planning(tmp_path):
    """PLANNING が bold 記法で記載されているとき phase: "PLANNING" を返すこと。"""
    from dashboard.parsers.current_phase import CurrentPhaseParser

    phase_file = tmp_path / ".claude" / "current-phase.md"
    phase_file.parent.mkdir(parents=True)
    phase_file.write_text("# Current Phase\n\n**PLANNING**\n\n_detail_\n", encoding="utf-8")

    result = CurrentPhaseParser(project_root=tmp_path).parse()
    assert result["ok"] is True
    assert result["error"] is None
    assert result["data"] == {"phase": "PLANNING"}


def test_parse_returns_building(tmp_path):
    """BUILDING が bold 記法で記載されているとき phase: "BUILDING" を返すこと。"""
    from dashboard.parsers.current_phase import CurrentPhaseParser

    phase_file = tmp_path / ".claude" / "current-phase.md"
    phase_file.parent.mkdir(parents=True)
    phase_file.write_text("# Current Phase\n\n**BUILDING**\n\n_detail_\n", encoding="utf-8")

    result = CurrentPhaseParser(project_root=tmp_path).parse()
    assert result["ok"] is True
    assert result["data"] == {"phase": "BUILDING"}


def test_parse_returns_auditing(tmp_path):
    """AUDITING が bold 記法で記載されているとき phase: "AUDITING" を返すこと。"""
    from dashboard.parsers.current_phase import CurrentPhaseParser

    phase_file = tmp_path / ".claude" / "current-phase.md"
    phase_file.parent.mkdir(parents=True)
    phase_file.write_text("# Current Phase\n\n**AUDITING**\n\n_detail_\n", encoding="utf-8")

    result = CurrentPhaseParser(project_root=tmp_path).parse()
    assert result["ok"] is True
    assert result["data"] == {"phase": "AUDITING"}


def test_parse_returns_autonomous(tmp_path):
    """AUTONOMOUS が bold 記法で記載されているとき phase: "AUTONOMOUS" を返すこと。"""
    from dashboard.parsers.current_phase import CurrentPhaseParser

    phase_file = tmp_path / ".claude" / "current-phase.md"
    phase_file.parent.mkdir(parents=True)
    phase_file.write_text("# Current Phase\n\n**AUTONOMOUS**\n\n_detail_\n", encoding="utf-8")

    result = CurrentPhaseParser(project_root=tmp_path).parse()
    assert result["ok"] is True
    assert result["data"] == {"phase": "AUTONOMOUS"}


def test_parse_extracts_first_match_when_multiple_bold_phases(tmp_path):
    """複数の bold Phase 記法があるとき、最初にマッチしたものを返すこと。"""
    from dashboard.parsers.current_phase import CurrentPhaseParser

    phase_file = tmp_path / ".claude" / "current-phase.md"
    phase_file.parent.mkdir(parents=True)
    # 実ファイルには「次フェーズ: AUDITING」のような記述がある可能性がある
    phase_file.write_text(
        "# Current Phase\n\n**BUILDING**\n\n_次: **AUDITING** 予定_\n",
        encoding="utf-8",
    )

    result = CurrentPhaseParser(project_root=tmp_path).parse()
    assert result["ok"] is True
    assert result["data"] == {"phase": "BUILDING"}


# ─────────────────────────────────────────────
# エッジケース: UNKNOWN
# ─────────────────────────────────────────────


def test_parse_returns_unknown_when_no_bold_phase(tmp_path):
    """Phase 名の bold 記法がないとき phase: "UNKNOWN" を返すこと（ok=True）。"""
    from dashboard.parsers.current_phase import CurrentPhaseParser

    phase_file = tmp_path / ".claude" / "current-phase.md"
    phase_file.parent.mkdir(parents=True)
    phase_file.write_text("# Current Phase\n\n(未設定)\n", encoding="utf-8")

    result = CurrentPhaseParser(project_root=tmp_path).parse()
    assert result["ok"] is True
    assert result["error"] is None
    assert result["data"] == {"phase": "UNKNOWN"}


def test_parse_returns_unknown_when_empty_file(tmp_path):
    """空ファイルのとき phase: "UNKNOWN" を返すこと（ok=True）。"""
    from dashboard.parsers.current_phase import CurrentPhaseParser

    phase_file = tmp_path / ".claude" / "current-phase.md"
    phase_file.parent.mkdir(parents=True)
    phase_file.write_text("", encoding="utf-8")

    result = CurrentPhaseParser(project_root=tmp_path).parse()
    assert result["ok"] is True
    assert result["data"] == {"phase": "UNKNOWN"}


# ─────────────────────────────────────────────
# エラー系: ファイル不在
# ─────────────────────────────────────────────


def test_parse_returns_ok_false_when_file_missing(tmp_path):
    """current-phase.md が存在しないとき ok=False を返すこと。"""
    from dashboard.parsers.current_phase import CurrentPhaseParser

    # .claude ディレクトリを作るが current-phase.md は作らない
    (tmp_path / ".claude").mkdir(parents=True)

    result = CurrentPhaseParser(project_root=tmp_path).parse()
    assert result["ok"] is False
    assert isinstance(result["error"], str)
    assert len(result["error"]) > 0
    assert result["data"] is None


def test_parse_returns_ok_false_when_dotclaude_dir_missing(tmp_path):
    """.claude ディレクトリ自体が存在しないとき ok=False を返すこと。"""
    from dashboard.parsers.current_phase import CurrentPhaseParser

    result = CurrentPhaseParser(project_root=tmp_path).parse()
    assert result["ok"] is False
    assert result["data"] is None


# ─────────────────────────────────────────────
# 例外を外に伝播させない
# ─────────────────────────────────────────────


def test_parse_does_not_raise_on_missing_file(tmp_path):
    """ファイル不在時に例外を外に伝播させないこと（ok=False を返すだけ）。"""
    from dashboard.parsers.current_phase import CurrentPhaseParser

    # 例外が発生しないことを確認
    try:
        result = CurrentPhaseParser(project_root=tmp_path).parse()
        assert result["ok"] is False
    except Exception as exc:
        pytest.fail(f"parse() が例外を外に伝播させた: {exc}")


# ─────────────────────────────────────────────
# 実データテスト（プロジェクトルートの実ファイル）
# ─────────────────────────────────────────────


def test_parse_with_controlled_current_phase_file(tmp_path):
    """制御済みの tmp current-phase.md を読み込み "BUILDING" を返すこと。

    実 .claude/current-phase.md の内容（BUILDING/AUDITING 等）に依存せず、
    tmp ディレクトリ内の制御済みファイルで動作を検証する。
    """
    from dashboard.parsers.current_phase import CurrentPhaseParser

    phase_file = tmp_path / ".claude" / "current-phase.md"
    phase_file.parent.mkdir(parents=True)
    phase_file.write_text("# Current Phase\n\n**BUILDING**\n", encoding="utf-8")

    parser = CurrentPhaseParser(project_root=tmp_path)
    result = parser.parse()

    assert result["ok"] is True, f"tmp ファイル読み込み失敗: {result.get('error')}"
    assert result["data"] is not None
    assert result["data"]["phase"] == "BUILDING"
