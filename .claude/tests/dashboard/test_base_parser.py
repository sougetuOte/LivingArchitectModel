"""test_base_parser.py - BaseParser 抽象クラスのテスト（W1-B5-T1）

対応仕様: docs/specs/b4-dashboard/design.md §5「パーサ共通インターフェース」
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# .claude/scripts を sys.path に追加（hooks/tests/*.py と同じパターン）
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# ─────────────────────────────────────────────
# インポートテスト
# ─────────────────────────────────────────────


def test_base_parser_importable():
    """BaseParser を dashboard.parsers.base からインポートできること。"""
    from dashboard.parsers.base import BaseParser  # noqa: F401


# ─────────────────────────────────────────────
# 抽象クラスとしての振る舞い
# ─────────────────────────────────────────────


def test_base_parser_cannot_be_instantiated_directly():
    """BaseParser を直接インスタンス化しようとすると TypeError が発生すること。"""
    from dashboard.parsers.base import BaseParser

    with pytest.raises((TypeError, NotImplementedError)):
        BaseParser()


def test_concrete_subclass_without_parse_cannot_be_instantiated():
    """parse() を実装しないサブクラスはインスタンス化できないこと。"""
    from dashboard.parsers.base import BaseParser

    class IncompleteParser(BaseParser):
        pass

    with pytest.raises((TypeError, NotImplementedError)):
        IncompleteParser()


def test_concrete_subclass_with_parse_can_be_instantiated():
    """parse() を実装した具象サブクラスはインスタンス化できること。"""
    from dashboard.parsers.base import BaseParser

    class ConcreteParser(BaseParser):
        def parse(self) -> dict:
            return {"ok": True, "error": None, "data": {}}

    parser = ConcreteParser()
    assert parser is not None


# ─────────────────────────────────────────────
# parse() 戻り値の形式
# ─────────────────────────────────────────────


def test_parse_returns_dict_with_ok_key():
    """parse() の戻り値が "ok" キーを持つ dict であること。"""
    from dashboard.parsers.base import BaseParser

    class OkParser(BaseParser):
        def parse(self) -> dict:
            return {"ok": True, "error": None, "data": {"foo": "bar"}}

    result = OkParser().parse()
    assert isinstance(result, dict)
    assert "ok" in result


def test_parse_returns_dict_with_error_key():
    """parse() の戻り値が "error" キーを持つ dict であること。"""
    from dashboard.parsers.base import BaseParser

    class OkParser(BaseParser):
        def parse(self) -> dict:
            return {"ok": True, "error": None, "data": {"foo": "bar"}}

    result = OkParser().parse()
    assert "error" in result


def test_parse_returns_dict_with_data_key():
    """parse() の戻り値が "data" キーを持つ dict であること。"""
    from dashboard.parsers.base import BaseParser

    class OkParser(BaseParser):
        def parse(self) -> dict:
            return {"ok": True, "error": None, "data": {"foo": "bar"}}

    result = OkParser().parse()
    assert "data" in result


def test_parse_ok_true_has_none_error():
    """ok=True のとき error は None であること。"""
    from dashboard.parsers.base import BaseParser

    class SuccessParser(BaseParser):
        def parse(self) -> dict:
            return {"ok": True, "error": None, "data": {"result": "value"}}

    result = SuccessParser().parse()
    assert result["ok"] is True
    assert result["error"] is None


def test_parse_ok_false_has_error_string_and_none_data():
    """ok=False のとき error は str、data は None であること。"""
    from dashboard.parsers.base import BaseParser

    class FailParser(BaseParser):
        def parse(self) -> dict:
            return {"ok": False, "error": "file not found", "data": None}

    result = FailParser().parse()
    assert result["ok"] is False
    assert isinstance(result["error"], str)
    assert result["data"] is None


def test_parse_ok_is_bool():
    """ok の値は bool 型であること。"""
    from dashboard.parsers.base import BaseParser

    class BoolParser(BaseParser):
        def parse(self) -> dict:
            return {"ok": True, "error": None, "data": {}}

    result = BoolParser().parse()
    assert isinstance(result["ok"], bool)


# ─────────────────────────────────────────────
# データモデルのインポートテスト
# ─────────────────────────────────────────────


def test_models_importable():
    """models.py から DashboardData 等をインポートできること。"""
    from dashboard.models import (  # noqa: F401
        DashboardData,
        MilestoneInfo,
        TaskInfo,
        WaveInfo,
    )


def test_milestone_info_fields():
    """MilestoneInfo が name / current_step / status フィールドを持つこと。"""
    from dashboard.models import MilestoneInfo

    m = MilestoneInfo(name="B-5", current_step="PLANNING", status="in-progress")
    assert m.name == "B-5"
    assert m.current_step == "PLANNING"
    assert m.status == "in-progress"


def test_wave_info_fields():
    """WaveInfo が milestone / wave_number / task_count / status フィールドを持つこと。"""
    from dashboard.models import WaveInfo

    w = WaveInfo(milestone="B-5", wave_number="1", task_count=5, status="in-progress")
    assert w.milestone == "B-5"
    assert w.wave_number == "1"
    assert w.task_count == 5
    assert w.status == "in-progress"


def test_task_info_fields():
    """TaskInfo が id / milestone / assignee / status フィールドを持つこと。"""
    from dashboard.models import TaskInfo

    t = TaskInfo(id="W1-B5-T1", milestone="B-5", assignee="Sonnet", status="completed")
    assert t.id == "W1-B5-T1"
    assert t.milestone == "B-5"
    assert t.assignee == "Sonnet"
    assert t.status == "completed"


def test_dashboard_data_defaults():
    """DashboardData がデフォルト値でインスタンス化できること。"""
    from dashboard.models import DashboardData

    d = DashboardData()
    assert d.milestones == []
    assert d.waves == []
    assert d.tasks == []
    assert d.current_phase == "UNKNOWN"
    assert d.generated_at == ""
    assert d.parser_errors == []
