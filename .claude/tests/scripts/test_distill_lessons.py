"""R-1 W-R2 S2/S3: distill_lessons.py の regression テスト (R1-007).

R1-007 対応: `distill()` の `is_small_task` パラメータは未使用の dead code
(design §9.1 の小タスクルート分岐は distill() 内部ではなく caller 側
(SKILL.md フロー[8] のコマンド組み立て) で完結している)。
本テストは dead code 除去前後で distill() の出力形式・重複スキップ・
空ログスキップ挙動が不変であることを保証する。

対応仕様: docs/specs/goal-driven-orchestration/design.md §13 / §9.1
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from distill_lessons import distill  # noqa: E402


def _grader_log_fail_then_pass(tmp_path: Path) -> list[str]:
    """fail→pass 遷移を含む合成 grader ログ 2 件を tmp_path に書き出す。"""
    import json

    loop1 = tmp_path / "loop01-grader.json"
    loop1.write_text(json.dumps({
        "overall": "fail",
        "items": [{"id": "1", "result": "fail", "reason": "テスト未追加"}],
    }), encoding="utf-8")

    loop2 = tmp_path / "loop02-grader.json"
    loop2.write_text(json.dumps({
        "overall": "pass",
        "items": [{"id": "1", "result": "pass", "reason": "テスト追加済み"}],
    }), encoding="utf-8")

    return [str(loop1), str(loop2)]


def test_distill_writes_entry_for_fail_to_pass_transition(tmp_path):
    """fail→pass 遷移がある grader ログから lessons.md にエントリが追記される。"""
    grader_log_paths = _grader_log_fail_then_pass(tmp_path)
    lessons_path = tmp_path / "lessons.md"

    distill(
        task_id="gd-test-001",
        grader_log_paths=grader_log_paths,
        lessons_path=lessons_path,
    )

    assert lessons_path.is_file()
    content = lessons_path.read_text(encoding="utf-8")
    assert "gd-test-001" in content
    assert "検証済み" in content
    assert "テスト未追加" in content
    assert "テスト追加済み" in content


def test_distill_skips_duplicate_task_id(tmp_path):
    """同一 task_id のエントリは重複追記されない。"""
    grader_log_paths = _grader_log_fail_then_pass(tmp_path)
    lessons_path = tmp_path / "lessons.md"

    distill(task_id="gd-test-002", grader_log_paths=grader_log_paths, lessons_path=lessons_path)
    first_content = lessons_path.read_text(encoding="utf-8")

    distill(task_id="gd-test-002", grader_log_paths=grader_log_paths, lessons_path=lessons_path)
    second_content = lessons_path.read_text(encoding="utf-8")

    assert first_content == second_content


def test_distill_skips_empty_grader_log(tmp_path):
    """grader ログが空リストの場合は lessons.md を作成しない (FR-2.1)。"""
    lessons_path = tmp_path / "lessons.md"

    distill(task_id="gd-test-003", grader_log_paths=[], lessons_path=lessons_path)

    assert not lessons_path.exists()


def test_distill_single_grader_log_small_task_style(tmp_path):
    """小タスクルート相当の呼び出し (grader ログ 1 件のみ) でも正常動作する。

    design §9.1: 小タスクルートは caller (SKILL.md フロー[8]) 側で
    --grader-log を 1 件のみ渡す呼び出し方の違いのみであり、
    distill() 自体の入力・処理ロジックは中/大タスクルートと同一。
    """
    import json

    log = tmp_path / "loop01-grader.json"
    log.write_text(json.dumps({
        "overall": "pass",
        "items": [{"id": "1", "result": "pass", "reason": "初回合格"}],
    }), encoding="utf-8")
    lessons_path = tmp_path / "lessons.md"

    distill(task_id="gd-small-001", grader_log_paths=[str(log)], lessons_path=lessons_path)

    assert lessons_path.is_file()
    content = lessons_path.read_text(encoding="utf-8")
    assert "gd-small-001" in content
    assert "未検証" in content  # 単一ログには fail→pass 遷移がないため自動判定は未検証
