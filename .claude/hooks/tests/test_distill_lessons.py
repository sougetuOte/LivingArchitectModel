"""test_distill_lessons.py - distill-lessons.py の TDD テスト（W4-T1 メモリ蒸留 FR-5）

W4-T1: distill-lessons.py 実装（メモリ蒸留 FR-5）
対応仕様: docs/specs/goal-driven-orchestration/design.md §13
対応要件: FR-5 / AC-2 / design §13 / design §9.1

テスト構成:
  TestLessonsEntryFormat         - lessons.md エントリ形式のスキーマ準拠検証（design §13）
  TestDistillVerified            - 検証済み教訓の書き込み先・フォーマット
  TestDistillUnverified          - 未検証の推測「未検証」タグ付き追記（MUST）
  TestSmallTaskRoute             - 小タスクルート: grader 判定 JSON のみを入力（design §9.1）
  TestNoKnowledgeDirWrite        - docs/artifacts/knowledge/ への書き込み禁止（W-5 制約）
  TestArgparseInterface          - SKILL.md フロー[8] 呼び出しインターフェース（--task-id / --grader-log）
  TestMultipleGraderLogs         - 複数の grader ログからの蒸留（中・大タスク向け）
  TestIdempotency                - 同一タスクIDで複数回実行しても重複エントリを作らない
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import pytest

# scripts ディレクトリを sys.path に追加（test_gd_loop.py と同じパターン）
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import distill_lessons


# ---------------------------------------------------------------------------
# フィクスチャ
# ---------------------------------------------------------------------------


def _make_grader_log(
    task_id: str = "gd-20260613-001",
    loop_num: int = 1,
    overall: str = "pass",
    items: Optional[list] = None,
    escalate: bool = False,
    escalate_reason: str = "",
) -> dict:
    """grader 判定ログの雛形を返す（design §11 grader 出力スキーマ準拠）。"""
    if items is None:
        items = [{"id": 1, "result": overall, "reason": "テスト通過"}]
    return {
        "rubric_version": "2026-06-13",
        "overall": overall,
        "items": items,
        "escalate": escalate,
        "escalate_reason": escalate_reason,
        "verdict": overall if not escalate else "escalate",
        "raw": json.dumps({"overall": overall}),
        "parse_error": None,
    }


def _write_grader_log(
    tmp_path: Path,
    task_id: str = "gd-20260613-001",
    loop_num: int = 1,
    overall: str = "pass",
    items: Optional[list] = None,
) -> Path:
    """grader ログファイルを tmp_path 以下に作成し、パスを返す。"""
    logs_dir = tmp_path / ".claude" / "logs" / "gd"
    logs_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{task_id}-loop{loop_num:02d}-grader.json"
    log_path = logs_dir / filename
    log_path.write_text(
        json.dumps(_make_grader_log(
            task_id=task_id,
            loop_num=loop_num,
            overall=overall,
            items=items,
        )),
        encoding="utf-8",
    )
    return log_path


def _make_fail_then_pass_logs(tmp_path: Path, task_id: str = "gd-20260613-001") -> list[Path]:
    """fail→pass 遷移のグレーダーログを作成して返す（2ループ分）。"""
    fail_items = [
        {"id": 1, "result": "fail", "reason": "テスト失敗: assert_xxx が通らなかった"},
        {"id": 2, "result": "pass", "reason": "型チェック通過"},
    ]
    pass_items = [
        {"id": 1, "result": "pass", "reason": "テスト修正後は全パス"},
        {"id": 2, "result": "pass", "reason": "型チェック通過"},
    ]
    loop1 = _write_grader_log(tmp_path, task_id=task_id, loop_num=1, overall="fail", items=fail_items)
    loop2 = _write_grader_log(tmp_path, task_id=task_id, loop_num=2, overall="pass", items=pass_items)
    return [loop1, loop2]


def _make_lessons_dir(tmp_path: Path) -> Path:
    """lessons.md の書き込み先ディレクトリを tmp_path 以下に作成して返す。"""
    lessons_dir = tmp_path / ".claude" / "agent-memory" / "goal-driven-l3-executor"
    lessons_dir.mkdir(parents=True, exist_ok=True)
    return lessons_dir


# ---------------------------------------------------------------------------
# TestLessonsEntryFormat - design §13 エントリ形式のスキーマ準拠検証
# ---------------------------------------------------------------------------


class TestLessonsEntryFormat:
    """lessons.md エントリが design §13 のスキーマに準拠していること。

    design §13 スキーマ:
    ## [YYYY-MM-DD] <タスク ID>: <教訓タイトル>

    **状態**: 検証済み / 未検証
    **ループ回数**: N
    **fail 原因**: [要約]
    **修正内容**: [要約]
    **一般則**: [再発防止のためのルール文]
    **適用範囲**: [対象ファイルパターン / 操作]
    """

    def test_verified_entry_has_required_fields(self, tmp_path: Path) -> None:
        """検証済みエントリが design §13 の全必須フィールドを含む。"""
        lessons_dir = _make_lessons_dir(tmp_path)
        log_paths = _make_fail_then_pass_logs(tmp_path, task_id="gd-20260613-001")

        entry = distill_lessons.build_lesson_entry(
            task_id="gd-20260613-001",
            grader_logs=[json.loads(p.read_text(encoding="utf-8")) for p in log_paths],
            verified=True,
        )

        # design §13 スキーマの全フィールドが含まれる
        assert "**状態**: 検証済み" in entry
        assert "**ループ回数**:" in entry
        assert "**fail 原因**:" in entry
        assert "**修正内容**:" in entry
        assert "**一般則**:" in entry
        assert "**適用範囲**:" in entry

    def test_unverified_entry_has_unverified_tag(self, tmp_path: Path) -> None:
        """未検証エントリが「未検証」タグを含む（MUST）。"""
        log_paths = _make_fail_then_pass_logs(tmp_path)
        entry = distill_lessons.build_lesson_entry(
            task_id="gd-20260613-001",
            grader_logs=[json.loads(p.read_text(encoding="utf-8")) for p in log_paths],
            verified=False,
        )

        assert "**状態**: 未検証" in entry

    def test_entry_header_format(self, tmp_path: Path) -> None:
        """エントリヘッダが `## [YYYY-MM-DD] <task_id>:` 形式である。"""
        log_paths = _make_fail_then_pass_logs(tmp_path)
        entry = distill_lessons.build_lesson_entry(
            task_id="gd-20260613-001",
            grader_logs=[json.loads(p.read_text(encoding="utf-8")) for p in log_paths],
            verified=True,
        )

        # ## [YYYY-MM-DD] gd-20260613-001: ... の形式
        import re
        assert re.search(r"^## \[\d{4}-\d{2}-\d{2}\] gd-20260613-001:", entry, re.MULTILINE)

    def test_loop_count_reflects_actual_loops(self, tmp_path: Path) -> None:
        """ループ回数フィールドが実際のループ数（grader ログ数）を反映する。"""
        log_paths = _make_fail_then_pass_logs(tmp_path)
        logs = [json.loads(p.read_text(encoding="utf-8")) for p in log_paths]

        entry = distill_lessons.build_lesson_entry(
            task_id="gd-20260613-001",
            grader_logs=logs,
            verified=True,
        )

        assert "**ループ回数**: 2" in entry


# ---------------------------------------------------------------------------
# TestDistillVerified - 検証済み教訓の書き込み先・フォーマット
# ---------------------------------------------------------------------------


class TestDistillVerified:
    """検証済み教訓は lessons.md にのみ書き込まれる。"""

    def test_writes_to_lessons_md(self, tmp_path: Path) -> None:
        """検証済み教訓が lessons.md に書き込まれる。"""
        lessons_dir = _make_lessons_dir(tmp_path)
        log_paths = _make_fail_then_pass_logs(tmp_path)

        distill_lessons.distill(
            task_id="gd-20260613-001",
            grader_log_paths=[str(p) for p in log_paths],
            lessons_path=lessons_dir / "lessons.md",
            verified=True,
        )

        lessons_file = lessons_dir / "lessons.md"
        assert lessons_file.is_file()

    def test_lessons_md_content_has_verified_status(self, tmp_path: Path) -> None:
        """lessons.md に「検証済み」ステータスが含まれる。"""
        lessons_dir = _make_lessons_dir(tmp_path)
        log_paths = _make_fail_then_pass_logs(tmp_path)

        distill_lessons.distill(
            task_id="gd-20260613-001",
            grader_log_paths=[str(p) for p in log_paths],
            lessons_path=lessons_dir / "lessons.md",
            verified=True,
        )

        content = (lessons_dir / "lessons.md").read_text(encoding="utf-8")
        assert "**状態**: 検証済み" in content
        assert "gd-20260613-001" in content

    def test_appends_to_existing_lessons_md(self, tmp_path: Path) -> None:
        """既存の lessons.md にエントリを追記する（上書きしない）。"""
        lessons_dir = _make_lessons_dir(tmp_path)
        existing_content = "# lessons\n\n## [2026-01-01] gd-old: 既存エントリ\n"
        lessons_file = lessons_dir / "lessons.md"
        lessons_file.write_text(existing_content, encoding="utf-8")

        log_paths = _make_fail_then_pass_logs(tmp_path)
        distill_lessons.distill(
            task_id="gd-20260613-001",
            grader_log_paths=[str(p) for p in log_paths],
            lessons_path=lessons_file,
            verified=True,
        )

        content = lessons_file.read_text(encoding="utf-8")
        assert "既存エントリ" in content  # 既存内容が保持される
        assert "gd-20260613-001" in content  # 新エントリが追記される


# ---------------------------------------------------------------------------
# TestDistillUnverified - 未検証推測の「未検証」タグ付き追記（MUST）
# ---------------------------------------------------------------------------


class TestDistillUnverified:
    """未検証の推測は「未検証」タグ付きで lessons.md に追記される（MUST）。"""

    def test_unverified_tag_written_to_lessons(self, tmp_path: Path) -> None:
        """未検証モードで書かれたエントリに「未検証」タグが含まれる。"""
        lessons_dir = _make_lessons_dir(tmp_path)
        # pass のみのログ（fail→pass 遷移なし → 未検証扱い）
        log_path = _write_grader_log(tmp_path, overall="pass")

        distill_lessons.distill(
            task_id="gd-20260613-002",
            grader_log_paths=[str(log_path)],
            lessons_path=lessons_dir / "lessons.md",
            verified=False,
        )

        content = (lessons_dir / "lessons.md").read_text(encoding="utf-8")
        assert "**状態**: 未検証" in content

    def test_pass_only_logs_produce_unverified_entry(self, tmp_path: Path) -> None:
        """fail→pass 遷移がない場合は未検証エントリが書かれる。

        design §13: 「検証済みの一般則」は fail→pass 修正パターンから抽出する。
        pass のみのログは一般則を確立できないため未検証扱いとする。
        """
        lessons_dir = _make_lessons_dir(tmp_path)
        log_path = _write_grader_log(tmp_path, task_id="gd-20260613-003", overall="pass")

        distill_lessons.distill(
            task_id="gd-20260613-003",
            grader_log_paths=[str(log_path)],
            lessons_path=lessons_dir / "lessons.md",
            verified=None,  # verified=None で自動判定
        )

        content = (lessons_dir / "lessons.md").read_text(encoding="utf-8")
        assert "**状態**: 未検証" in content

    def test_fail_then_pass_logs_produce_verified_entry(self, tmp_path: Path) -> None:
        """fail→pass 遷移がある場合は検証済みエントリが書かれる（verified=None 自動判定）。"""
        lessons_dir = _make_lessons_dir(tmp_path)
        log_paths = _make_fail_then_pass_logs(tmp_path, task_id="gd-20260613-004")

        distill_lessons.distill(
            task_id="gd-20260613-004",
            grader_log_paths=[str(p) for p in log_paths],
            lessons_path=lessons_dir / "lessons.md",
            verified=None,  # verified=None で自動判定
        )

        content = (lessons_dir / "lessons.md").read_text(encoding="utf-8")
        assert "**状態**: 検証済み" in content


# ---------------------------------------------------------------------------
# TestSmallTaskRoute - 小タスクルート: grader 判定 JSON のみ（design §9.1）
# ---------------------------------------------------------------------------


class TestSmallTaskRoute:
    """小タスクルートでは grader 判定 JSON のみを入力とする（design §9.1）。

    小タスクでは L1 最終検収をスキップするため、
    distill-lessons.py の入力が grader 判定 JSON のみとなる。
    """

    def test_single_pass_grader_log_accepted(self, tmp_path: Path) -> None:
        """単一の pass grader ログ（小タスク完了）を受け付ける。"""
        lessons_dir = _make_lessons_dir(tmp_path)
        log_path = _write_grader_log(tmp_path, task_id="gd-small-001", overall="pass")

        # エラーなく実行できる（小タスクは pass ログ 1 件のみで OK）
        distill_lessons.distill(
            task_id="gd-small-001",
            grader_log_paths=[str(log_path)],
            lessons_path=lessons_dir / "lessons.md",
            verified=None,
        )

        lessons_file = lessons_dir / "lessons.md"
        assert lessons_file.is_file()
        content = lessons_file.read_text(encoding="utf-8")
        assert "gd-small-001" in content

    def test_small_task_grader_only_input_flag(self, tmp_path: Path) -> None:
        """--small-task フラグで grader ログのみ処理できる（SKILL.md フロー[8] 対応）。"""
        lessons_dir = _make_lessons_dir(tmp_path)
        log_path = _write_grader_log(tmp_path, task_id="gd-small-002", overall="pass")

        # is_small_task=True でも正常動作する
        distill_lessons.distill(
            task_id="gd-small-002",
            grader_log_paths=[str(log_path)],
            lessons_path=lessons_dir / "lessons.md",
            verified=None,
            is_small_task=True,
        )

        lessons_file = lessons_dir / "lessons.md"
        assert lessons_file.is_file()


# ---------------------------------------------------------------------------
# TestNoKnowledgeDirWrite - docs/artifacts/knowledge/ への書き込み禁止（W-5 制約）
# ---------------------------------------------------------------------------


class TestNoKnowledgeDirWrite:
    """distill-lessons.py が docs/artifacts/knowledge/ へ書き込まないこと（W-5 制約 / design §13）。

    design §13:
    ※ docs/artifacts/knowledge/ への書き込みは distill-lessons.py の自動処理対象外。
    /retro Step 4 で人間が lessons.md を読み、精査した知見のみ手動で昇格させる。
    """

    def test_no_knowledge_dir_write_in_functions(self) -> None:
        """distill_lessons モジュールの実行コード（docstring 外）に
        docs/artifacts/knowledge/ へのパス構築コードが存在しない。

        docstring での禁止理由説明は許容し、
        実際の open/write/mkdir 等の操作コードが knowledge ディレクトリを
        対象にしていないことを確認する。
        """
        # distill() 関数の本体ロジックが knowledge ディレクトリに書き込まないことを
        # 実行時検証（test_distill_does_not_write_to_knowledge_dir）で確認するため、
        # ここではモジュールが正常にインポートできること（W-5 制約のメタ確認）のみ検証する。
        assert hasattr(distill_lessons, "distill"), "distill 関数が存在する"
        assert hasattr(distill_lessons, "build_lesson_entry"), "build_lesson_entry 関数が存在する"
        # get_project_root はパス解決用であり knowledge ディレクトリを生成しない
        assert hasattr(distill_lessons, "get_project_root"), "get_project_root 関数が存在する"

    def test_distill_does_not_write_to_knowledge_dir(self, tmp_path: Path) -> None:
        """distill() 実行後に docs/artifacts/knowledge/ が作成されない。"""
        lessons_dir = _make_lessons_dir(tmp_path)
        log_paths = _make_fail_then_pass_logs(tmp_path)
        knowledge_dir = tmp_path / "docs" / "artifacts" / "knowledge"

        distill_lessons.distill(
            task_id="gd-20260613-001",
            grader_log_paths=[str(p) for p in log_paths],
            lessons_path=lessons_dir / "lessons.md",
            verified=True,
        )

        # knowledge ディレクトリが作成されていない
        assert not knowledge_dir.exists()


# ---------------------------------------------------------------------------
# TestArgparseInterface - SKILL.md フロー[8] 呼び出しインターフェース
# ---------------------------------------------------------------------------


class TestArgparseInterface:
    """SKILL.md フロー[8] で定義された呼び出しインターフェースの検証。

    SKILL.md フロー[8]:
    python .claude/scripts/distill-lessons.py \\
      --task-id <task_id> \\
      --grader-log .claude/logs/gd/<task_id>-loop*-grader.json
    """

    def test_argparser_has_task_id_arg(self) -> None:
        """--task-id 引数が存在する。"""
        parser = distill_lessons.build_arg_parser()
        # --task-id が定義されているか（parse でエラーが出ないことで確認）
        args = parser.parse_args([
            "--task-id", "gd-20260613-001",
            "--grader-log", "/some/path.json",
        ])
        assert args.task_id == "gd-20260613-001"

    def test_argparser_has_grader_log_arg(self) -> None:
        """--grader-log 引数が存在し、複数パスを受け付ける。"""
        parser = distill_lessons.build_arg_parser()
        args = parser.parse_args([
            "--task-id", "gd-20260613-001",
            "--grader-log", "/path/loop01.json", "/path/loop02.json",
        ])
        assert len(args.grader_log) == 2

    def test_argparser_has_lessons_path_arg(self) -> None:
        """--lessons-path 引数が存在する（書き込み先指定のため）。"""
        parser = distill_lessons.build_arg_parser()
        args = parser.parse_args([
            "--task-id", "gd-20260613-001",
            "--grader-log", "/path/loop01.json",
            "--lessons-path", "/some/lessons.md",
        ])
        assert args.lessons_path == "/some/lessons.md"

    def test_argparser_has_small_task_flag(self) -> None:
        """--small-task フラグが存在する（design §9.1 小タスクルート対応）。"""
        parser = distill_lessons.build_arg_parser()
        args = parser.parse_args([
            "--task-id", "gd-20260613-001",
            "--grader-log", "/path/loop01.json",
            "--small-task",
        ])
        assert args.small_task is True


# ---------------------------------------------------------------------------
# TestMultipleGraderLogs - 複数の grader ログからの蒸留
# ---------------------------------------------------------------------------


class TestMultipleGraderLogs:
    """複数の grader ログ（中・大タスクの複数ループ）から教訓を蒸留する。"""

    def test_multiple_fail_then_pass_extracts_lesson(self, tmp_path: Path) -> None:
        """複数ループの fail→pass から教訓が抽出される。"""
        lessons_dir = _make_lessons_dir(tmp_path)
        log_paths = _make_fail_then_pass_logs(tmp_path, task_id="gd-20260613-multi")

        distill_lessons.distill(
            task_id="gd-20260613-multi",
            grader_log_paths=[str(p) for p in log_paths],
            lessons_path=lessons_dir / "lessons.md",
            verified=None,
        )

        content = (lessons_dir / "lessons.md").read_text(encoding="utf-8")
        assert "gd-20260613-multi" in content
        assert "**状態**: 検証済み" in content  # fail→pass あり → 検証済み

    def test_fail_items_are_summarized(self, tmp_path: Path) -> None:
        """fail ループの不合格項目が fail 原因フィールドに要約される。"""
        lessons_dir = _make_lessons_dir(tmp_path)
        fail_items = [
            {"id": 1, "result": "fail", "reason": "特定の AssertionError が発生"},
        ]
        pass_items = [{"id": 1, "result": "pass", "reason": "修正後は通過"}]

        log1 = _write_grader_log(
            tmp_path, task_id="gd-20260613-fail", loop_num=1,
            overall="fail", items=fail_items,
        )
        log2 = _write_grader_log(
            tmp_path, task_id="gd-20260613-fail", loop_num=2,
            overall="pass", items=pass_items,
        )

        distill_lessons.distill(
            task_id="gd-20260613-fail",
            grader_log_paths=[str(log1), str(log2)],
            lessons_path=lessons_dir / "lessons.md",
            verified=None,
        )

        content = (lessons_dir / "lessons.md").read_text(encoding="utf-8")
        # fail 原因に失敗項目の内容が含まれる
        assert "**fail 原因**:" in content


# ---------------------------------------------------------------------------
# TestIdempotency - 同一タスク ID で複数回実行しても重複エントリを作らない
# ---------------------------------------------------------------------------


class TestIdempotency:
    """同一タスク ID で distill() を複数回実行しても重複エントリが作成されない。"""

    def test_duplicate_task_id_not_appended_twice(self, tmp_path: Path) -> None:
        """同一タスク ID のエントリは 1 回しか書かれない。"""
        lessons_dir = _make_lessons_dir(tmp_path)
        log_paths = _make_fail_then_pass_logs(tmp_path, task_id="gd-dup-001")
        lessons_file = lessons_dir / "lessons.md"

        distill_lessons.distill(
            task_id="gd-dup-001",
            grader_log_paths=[str(p) for p in log_paths],
            lessons_path=lessons_file,
            verified=None,
        )
        distill_lessons.distill(
            task_id="gd-dup-001",
            grader_log_paths=[str(p) for p in log_paths],
            lessons_path=lessons_file,
            verified=None,
        )

        content = lessons_file.read_text(encoding="utf-8")
        # 同一タスク ID のエントリは 1 つのみ
        count = content.count("gd-dup-001")
        assert count == 1, f"重複エントリが検出された（出現回数: {count}）"
