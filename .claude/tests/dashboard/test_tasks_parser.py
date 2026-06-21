"""test_tasks_parser.py - TasksParser のテスト（W3-B5-T12）

対応仕様: docs/specs/b4-dashboard/design.md §5「TasksParser」
         docs/specs/b4-dashboard/tasks.md §3 W3-B5-T12
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest

# .claude/scripts を sys.path に追加
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# プロジェクトルートの固定パス（実データテスト用）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


# ─────────────────────────────────────────────
# インポートテスト
# ─────────────────────────────────────────────


def test_tasks_parser_importable():
    """TasksParser を dashboard.parsers.tasks からインポートできること。"""
    from dashboard.parsers.tasks import TasksParser  # noqa: F401


def test_tasks_parser_is_subclass_of_base_parser():
    """TasksParser が BaseParser のサブクラスであること。"""
    from dashboard.parsers.base import BaseParser
    from dashboard.parsers.tasks import TasksParser

    assert issubclass(TasksParser, BaseParser)


# ─────────────────────────────────────────────
# コンストラクタ
# ─────────────────────────────────────────────


def test_init_accepts_project_root(tmp_path):
    """__init__(project_root) でインスタンス化できること。"""
    from dashboard.parsers.tasks import TasksParser

    parser = TasksParser(tmp_path)
    assert parser is not None


# ─────────────────────────────────────────────
# docs/specs/ 不在時の挙動
# ─────────────────────────────────────────────


def test_parse_returns_ok_true_when_specs_dir_missing(tmp_path):
    """docs/specs/ ディレクトリが存在しない場合 ok=True / tasks=[] を返すこと。"""
    from dashboard.parsers.tasks import TasksParser

    # tmp_path には docs/specs/ が存在しない
    parser = TasksParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    assert result["error"] is None
    assert result["data"] == {"tasks": []}


def test_parse_does_not_raise_when_specs_dir_missing(tmp_path):
    """docs/specs/ が存在しない場合も例外を外に伝播させないこと。"""
    from dashboard.parsers.tasks import TasksParser

    parser = TasksParser(tmp_path)
    result = parser.parse()
    assert "ok" in result


# ─────────────────────────────────────────────
# 戻り値の構造
# ─────────────────────────────────────────────


def test_parse_returns_dict_with_three_keys(tmp_path):
    """parse() が ok / error / data の 3 キーを持つ dict を返すこと。"""
    from dashboard.parsers.tasks import TasksParser

    parser = TasksParser(tmp_path)
    result = parser.parse()

    assert "ok" in result
    assert "error" in result
    assert "data" in result


def test_parse_ok_true_returns_tasks_key(tmp_path):
    """ok=True のとき data に tasks キーが含まれること。"""
    from dashboard.parsers.tasks import TasksParser

    specs_dir = tmp_path / "docs" / "specs"
    specs_dir.mkdir(parents=True)

    parser = TasksParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    assert "tasks" in result["data"]
    assert isinstance(result["data"]["tasks"], list)


# ─────────────────────────────────────────────
# チェックボックス行のパース（status 変換）
# ─────────────────────────────────────────────


def test_parse_completed_checkbox_returns_completed_status(tmp_path):
    """[x] チェックボックス行が status="completed" に変換されること。"""
    from dashboard.parsers.tasks import TasksParser

    milestone_dir = tmp_path / "docs" / "specs" / "B-5"
    milestone_dir.mkdir(parents=True)
    (milestone_dir / "tasks.md").write_text(
        textwrap.dedent("""\
        # タスク

        - [x] W1-B5-T1: BaseParser 実装完了
        """),
        encoding="utf-8",
    )

    parser = TasksParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    tasks = result["data"]["tasks"]
    assert len(tasks) == 1
    assert tasks[0].status == "completed"


def test_parse_not_started_checkbox_returns_not_started_status(tmp_path):
    """[ ] チェックボックス行が status="not-started" に変換されること。"""
    from dashboard.parsers.tasks import TasksParser

    milestone_dir = tmp_path / "docs" / "specs" / "B-5"
    milestone_dir.mkdir(parents=True)
    (milestone_dir / "tasks.md").write_text(
        textwrap.dedent("""\
        # タスク

        - [ ] W2-B5-T7: SessionStateParser 実装予定
        """),
        encoding="utf-8",
    )

    parser = TasksParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    tasks = result["data"]["tasks"]
    assert len(tasks) == 1
    assert tasks[0].status == "not-started"


# ─────────────────────────────────────────────
# TaskInfo フィールド検証（R-1: 仕様突合）
# ─────────────────────────────────────────────


def test_parse_task_info_has_required_fields(tmp_path):
    """TaskInfo が id / milestone / assignee / status フィールドを持つこと。"""
    from dashboard.parsers.tasks import TasksParser

    milestone_dir = tmp_path / "docs" / "specs" / "my-milestone"
    milestone_dir.mkdir(parents=True)
    (milestone_dir / "tasks.md").write_text(
        textwrap.dedent("""\
        - [x] W1-B5-T1: タスク説明
        """),
        encoding="utf-8",
    )

    parser = TasksParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    tasks = result["data"]["tasks"]
    assert len(tasks) == 1
    task = tasks[0]
    assert hasattr(task, "id")
    assert hasattr(task, "milestone")
    assert hasattr(task, "assignee")
    assert hasattr(task, "status")


def test_parse_task_assignee_is_dash_when_no_assignee_column(tmp_path):
    """tasks.md に担当列がない場合 assignee="-" となること。"""
    from dashboard.parsers.tasks import TasksParser

    milestone_dir = tmp_path / "docs" / "specs" / "my-milestone"
    milestone_dir.mkdir(parents=True)
    (milestone_dir / "tasks.md").write_text(
        textwrap.dedent("""\
        - [ ] W1-B5-T1: タスク説明
        """),
        encoding="utf-8",
    )

    parser = TasksParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    assert result["data"]["tasks"][0].assignee == "-"


def test_parse_task_milestone_matches_parent_directory(tmp_path):
    """TaskInfo.milestone が tasks.md の親ディレクトリ名と一致すること。"""
    from dashboard.parsers.tasks import TasksParser

    milestone_dir = tmp_path / "docs" / "specs" / "b4-dashboard"
    milestone_dir.mkdir(parents=True)
    (milestone_dir / "tasks.md").write_text(
        textwrap.dedent("""\
        - [x] W1-B5-T1: タスク説明
        """),
        encoding="utf-8",
    )

    parser = TasksParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    assert result["data"]["tasks"][0].milestone == "b4-dashboard"


# ─────────────────────────────────────────────
# regex: チェックボックス行のみ抽出
# ─────────────────────────────────────────────


def test_parse_ignores_non_checkbox_lines(tmp_path):
    """チェックボックス形式でない行は無視されること。"""
    from dashboard.parsers.tasks import TasksParser

    milestone_dir = tmp_path / "docs" / "specs" / "my-milestone"
    milestone_dir.mkdir(parents=True)
    (milestone_dir / "tasks.md").write_text(
        textwrap.dedent("""\
        # タスク一覧

        通常のテキスト行は無視されます。

        - [x] W1-B5-T1: 完了タスク
        - これはチェックボックスなし箇条書き
        - [ ] W1-B5-T2: 未着手タスク

        | テーブル | 行 | 無視 |

        ## セクション見出し
        """),
        encoding="utf-8",
    )

    parser = TasksParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    tasks = result["data"]["tasks"]
    # チェックボックス行は 2 件のみ
    assert len(tasks) == 2


def test_parse_checkbox_regex_matches_correct_pattern(tmp_path):
    """regex ^-\\s\\[( |x)\\]\\s(.+)$ のパターンにのみマッチすること。"""
    from dashboard.parsers.tasks import TasksParser

    milestone_dir = tmp_path / "docs" / "specs" / "my-milestone"
    milestone_dir.mkdir(parents=True)
    (milestone_dir / "tasks.md").write_text(
        textwrap.dedent("""\
        - [x] 完了済みタスク（正しい形式）
        - [ ] 未着手タスク（正しい形式）
        -[x] スペースなし（マッチしない）
        - [X] 大文字X（マッチしない）
        - [*] アスタリスク（マッチしない）
        """),
        encoding="utf-8",
    )

    parser = TasksParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    tasks = result["data"]["tasks"]
    # 正しい形式の 2 件のみ
    assert len(tasks) == 2


# ─────────────────────────────────────────────
# 複数 Milestone 走査
# ─────────────────────────────────────────────


def test_parse_scans_multiple_milestones(tmp_path):
    """docs/specs/ 配下の複数 Milestone の tasks.md を走査し、両方の Task を返すこと。"""
    from dashboard.parsers.tasks import TasksParser

    specs_dir = tmp_path / "docs" / "specs"

    ms1_dir = specs_dir / "milestone-a"
    ms1_dir.mkdir(parents=True)
    (ms1_dir / "tasks.md").write_text(
        textwrap.dedent("""\
        - [x] W1-A1-T1: Milestone A の完了タスク
        - [ ] W1-A1-T2: Milestone A の未着手タスク
        """),
        encoding="utf-8",
    )

    ms2_dir = specs_dir / "milestone-b"
    ms2_dir.mkdir(parents=True)
    (ms2_dir / "tasks.md").write_text(
        textwrap.dedent("""\
        - [ ] W2-B1-T1: Milestone B の未着手タスク
        """),
        encoding="utf-8",
    )

    parser = TasksParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    tasks = result["data"]["tasks"]
    # 2 Milestone 合計 3 件
    assert len(tasks) == 3


def test_parse_tasks_from_both_milestones_have_correct_milestone_field(tmp_path):
    """複数 Milestone 走査時、各 Task.milestone が正しい Milestone 名を持つこと。"""
    from dashboard.parsers.tasks import TasksParser

    specs_dir = tmp_path / "docs" / "specs"

    (specs_dir / "alpha").mkdir(parents=True)
    (specs_dir / "alpha" / "tasks.md").write_text(
        "- [x] W1-A1-T1: Alpha タスク\n", encoding="utf-8"
    )

    (specs_dir / "beta").mkdir(parents=True)
    (specs_dir / "beta" / "tasks.md").write_text(
        "- [ ] W1-B1-T1: Beta タスク\n", encoding="utf-8"
    )

    parser = TasksParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    tasks = result["data"]["tasks"]
    milestones_in_tasks = {t.milestone for t in tasks}
    assert "alpha" in milestones_in_tasks
    assert "beta" in milestones_in_tasks


# ─────────────────────────────────────────────
# tasks.md 不在 Milestone
# ─────────────────────────────────────────────


def test_parse_milestone_without_tasks_md_returns_ok_true_empty(tmp_path):
    """tasks.md が存在しない Milestone がある場合 ok=True / tasks=[] を返すこと。"""
    from dashboard.parsers.tasks import TasksParser

    # docs/specs/ は存在するが tasks.md なしのサブディレクトリのみ
    milestone_dir = tmp_path / "docs" / "specs" / "no-tasks-milestone"
    milestone_dir.mkdir(parents=True)
    (milestone_dir / "requirements.md").write_text("# 要件書\n", encoding="utf-8")

    parser = TasksParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    assert result["data"]["tasks"] == []


def test_parse_mixed_milestones_includes_only_existing_tasks_md(tmp_path):
    """tasks.md あり Milestone と なし Milestone が混在する場合、あり側の Task のみ返すこと。"""
    from dashboard.parsers.tasks import TasksParser

    specs_dir = tmp_path / "docs" / "specs"

    # tasks.md あり
    (specs_dir / "has-tasks").mkdir(parents=True)
    (specs_dir / "has-tasks" / "tasks.md").write_text(
        "- [x] W1-A1-T1: 完了タスク\n", encoding="utf-8"
    )

    # tasks.md なし
    (specs_dir / "no-tasks").mkdir(parents=True)
    (specs_dir / "no-tasks" / "design.md").write_text("# 設計書\n", encoding="utf-8")

    parser = TasksParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    tasks = result["data"]["tasks"]
    assert len(tasks) == 1
    assert tasks[0].milestone == "has-tasks"


# ─────────────────────────────────────────────
# 例外の外部伝播禁止
# ─────────────────────────────────────────────


def test_parse_does_not_raise_on_unreadable_tasks_md(tmp_path):
    """個別 Milestone の失敗が例外として外に伝播しないこと。"""
    from dashboard.parsers.tasks import TasksParser

    # 壊れた tasks.md（読み取りエラーを模擬）でも ok=True で継続する
    # ここでは空ファイルで代用（parse は ok=True で空リストを返すこと）
    milestone_dir = tmp_path / "docs" / "specs" / "empty-milestone"
    milestone_dir.mkdir(parents=True)
    (milestone_dir / "tasks.md").write_text("", encoding="utf-8")

    parser = TasksParser(tmp_path)
    # 例外が発生しないことを確認
    result = parser.parse()
    assert "ok" in result
    assert result["ok"] is True


def test_parse_returns_ok_true_and_no_exception_on_inaccessible_specs(tmp_path):
    """specs ディレクトリ自体が存在しない場合も例外なく ok=True / tasks=[] を返すこと。"""
    from dashboard.parsers.tasks import TasksParser

    # docs/specs/ が存在しない tmp_path をそのまま渡す
    parser = TasksParser(tmp_path)
    result = parser.parse()

    assert "ok" in result
    assert result["ok"] is True
    assert result["error"] is None


# ─────────────────────────────────────────────
# TaskInfo オブジェクト型検証
# ─────────────────────────────────────────────


def test_parse_tasks_are_task_info_objects(tmp_path):
    """tasks リストの要素が TaskInfo オブジェクトであること。"""
    from dashboard.models import TaskInfo
    from dashboard.parsers.tasks import TasksParser

    milestone_dir = tmp_path / "docs" / "specs" / "my-milestone"
    milestone_dir.mkdir(parents=True)
    (milestone_dir / "tasks.md").write_text(
        textwrap.dedent("""\
        - [x] W1-B5-T1: 完了タスク
        - [ ] W1-B5-T2: 未着手タスク
        """),
        encoding="utf-8",
    )

    parser = TasksParser(tmp_path)
    result = parser.parse()

    assert result["ok"] is True
    for task in result["data"]["tasks"]:
        assert isinstance(task, TaskInfo)


# ─────────────────────────────────────────────
# 実データテスト（R-6）
# ─────────────────────────────────────────────


def test_parse_real_specs_directory_returns_ok_true():
    """実 docs/specs/ ディレクトリでパースが ok=True を返すこと。"""
    from dashboard.parsers.tasks import TasksParser

    specs_dir = _PROJECT_ROOT / "docs" / "specs"
    if not specs_dir.exists():
        pytest.skip("docs/specs/ が存在しないためスキップ")

    parser = TasksParser(_PROJECT_ROOT)
    result = parser.parse()

    assert result["ok"] is True
    assert result["data"] is not None


def test_parse_real_specs_directory_returns_at_least_one_task():
    """実 docs/specs/ 走査で Task が 1 件以上抽出されること。"""
    from dashboard.parsers.tasks import TasksParser

    specs_dir = _PROJECT_ROOT / "docs" / "specs"
    if not specs_dir.exists():
        pytest.skip("docs/specs/ が存在しないためスキップ")

    parser = TasksParser(_PROJECT_ROOT)
    result = parser.parse()

    assert result["ok"] is True
    tasks = result["data"]["tasks"]
    assert len(tasks) >= 1


def test_parse_real_specs_tasks_are_task_info_instances():
    """実データで抽出された全 Task が TaskInfo インスタンスであること。"""
    from dashboard.models import TaskInfo
    from dashboard.parsers.tasks import TasksParser

    specs_dir = _PROJECT_ROOT / "docs" / "specs"
    if not specs_dir.exists():
        pytest.skip("docs/specs/ が存在しないためスキップ")

    parser = TasksParser(_PROJECT_ROOT)
    result = parser.parse()

    assert result["ok"] is True
    for task in result["data"]["tasks"]:
        assert isinstance(task, TaskInfo)
        assert isinstance(task.id, str)
        assert isinstance(task.milestone, str)
        assert isinstance(task.assignee, str)
        assert task.status in {"completed", "not-started"}
