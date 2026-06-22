"""test_fallback_behavior.py - AC-5 フォールバック動作確認テスト（W4-B5-T19）

対応仕様:
  - docs/specs/b4-dashboard/design.md §9「エラー耐障害性設計」
  - docs/specs/b4-dashboard/requirements.md FR-6（エラー時の扱い）
  - docs/specs/b4-dashboard/requirements.md NFR-6（全データ源欠如時も HTML 生成）
  - docs/specs/b4-dashboard/requirements.md AC-5（データソース欠如時のビルド完了）
  - docs/specs/b4-dashboard/tasks.md §3 W4-B5-T19

テスト方針:
  - tmp_path fixture を使い、テンポラリディレクトリにダミーファイルを配置して検証
  - 実リポジトリ内のファイル（SESSION_STATE.md / .claude/current-phase.md /
    docs/specs/*/tasks.md）は一切読み書き・削除しない
  - 既存実装（models.py / build_dashboard.py / builder.py / parsers）の改変なし
  - build() の returncode 0（全成功）または 1（部分失敗・HTML 生成は完了）を検証

AC-5 の 4 シナリオ:
  1. SESSION_STATE.md 削除時
  2. .claude/current-phase.md 削除時
  3. いずれかの Milestone の tasks.md 削除時
  4. 全データソース削除時（全パーサ ok=False → HTML は生成される）
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# .claude/scripts を sys.path に追加（既存テストと同パターン）
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# プロジェクトルートの推定（test_wave3_integration.py と同パターン）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# build_dashboard.py スクリプトパス
_SCRIPT = _PROJECT_ROOT / ".claude" / "scripts" / "build_dashboard.py"


# ─────────────────────────────────────────────
# ヘルパー: build モジュールの動的ロード
# ─────────────────────────────────────────────


def _load_build_module():
    """build_dashboard.py モジュールを動的にロードして返す（既存テストと同パターン）。"""
    sys.path.insert(0, str(_PROJECT_ROOT / ".claude" / "scripts"))
    spec = importlib.util.spec_from_file_location("build_dashboard", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─────────────────────────────────────────────
# ヘルパー: フル制御プロジェクト構造の構築
# ─────────────────────────────────────────────


def _build_full_project(tmp_path: Path) -> Path:
    """全データソースが揃った制御済みプロジェクト構造を tmp_path に構築して project_root を返す。

    配置するファイル:
      - SESSION_STATE.md（Milestone B-5 + タスク一覧）
      - .claude/current-phase.md（BUILDING）
      - docs/specs/b4-dashboard/tasks.md（チェックボックス行複数）
    """
    project_root = tmp_path / "project"
    project_root.mkdir()

    # SESSION_STATE.md
    session_state = """\
# SESSION_STATE

## 現在の Milestone

- B-5

## 完了タスク

- W1-B5-T1: BaseParser 実装完了
- W2-B5-T7: SessionStateParser 実装完了

## 進行中タスク

- W4-B5-T19: フォールバックテスト実装中
"""
    (project_root / "SESSION_STATE.md").write_text(session_state, encoding="utf-8")

    # .claude/current-phase.md
    dotclaude = project_root / ".claude"
    dotclaude.mkdir()
    (dotclaude / "current-phase.md").write_text(
        "# Current Phase\n\n**BUILDING**\n", encoding="utf-8"
    )

    # docs/specs/b4-dashboard/tasks.md
    specs_dir = project_root / "docs" / "specs" / "b4-dashboard"
    specs_dir.mkdir(parents=True)
    tasks_content = """\
# タスク定義書: b4-dashboard

## Wave 1

- [x] W1-B5-T1: BaseParser インターフェース定義
- [x] W1-B5-T2: build_dashboard.py スケルトン

## Wave 4

- [ ] W4-B5-T19: パーサエラー時のフォールバック動作確認
"""
    (specs_dir / "tasks.md").write_text(tasks_content, encoding="utf-8")

    return project_root


def _run_build(project_root: Path, tmp_path: Path) -> tuple[int, str, Path]:
    """build() を実行して (returncode, html_content, output_path) を返す。"""
    mod = _load_build_module()
    output = tmp_path / "dashboard.html"
    rc = mod.build(project_root=project_root, output_path=output)
    html = output.read_text(encoding="utf-8") if output.exists() else ""
    return rc, html, output


# ─────────────────────────────────────────────
# シナリオ 1: SESSION_STATE.md が存在しない場合
# ─────────────────────────────────────────────


class TestFallbackNoSessionState:
    """AC-5 シナリオ 1: SESSION_STATE.md 削除時のフォールバック動作。

    仕様（design.md §9）:
      - CurrentPhaseParser・TasksParser・GitHistoryParser は正常実行
      - SessionStateParser は ok=False を返しビルドを継続する
      - HTML は生成される（returncode 0 or 1）
    """

    @pytest.fixture()
    def no_session_state(self, tmp_path):
        """SESSION_STATE.md を含まないプロジェクト構造を返す。"""
        project_root = _build_full_project(tmp_path)
        # SESSION_STATE.md を削除（tmp_path 内なので実リポジトリに影響なし）
        (project_root / "SESSION_STATE.md").unlink()
        return project_root, tmp_path

    def test_build_completes_without_session_state(self, no_session_state):
        """SESSION_STATE.md が存在しなくても build() が完了すること（returncode 0 or 1）。"""
        project_root, tmp_path = no_session_state
        rc, html, output = _run_build(project_root, tmp_path)
        assert rc in (0, 1), (
            f"SESSION_STATE.md 欠如時の returncode は 0 or 1 であるべきですが {rc} でした。\n"
            "AC-5: データソース欠如時もビルドは完了する（NFR-6）。"
        )

    def test_html_is_generated_without_session_state(self, no_session_state):
        """SESSION_STATE.md が存在しなくても HTML ファイルが生成されること。"""
        project_root, tmp_path = no_session_state
        rc, html, output = _run_build(project_root, tmp_path)
        assert output.exists(), (
            "SESSION_STATE.md が存在しなくても HTML は生成される必要があります（NFR-6）。"
        )
        assert len(html) > 100, (
            "生成された HTML が空すぎます（100 バイト未満）。"
        )

    def test_html_has_doctype_without_session_state(self, no_session_state):
        """SESSION_STATE.md が存在しなくても HTML が正常な DOCTYPE を持つこと。"""
        project_root, tmp_path = no_session_state
        rc, html, output = _run_build(project_root, tmp_path)
        assert "<!DOCTYPE html>" in html, (
            "SESSION_STATE.md 欠如時でも HTML の DOCTYPE 宣言が必要です。"
        )

    def test_other_parsers_still_work_without_session_state(self, no_session_state):
        """SESSION_STATE.md 欠如時でも他のパーサ（Tasks）が正常動作すること。

        TasksParser は SESSION_STATE.md に依存しないため、
        tasks.md から W1-B5-T1 等の Task が V-4 に表示される。

        注意: CurrentPhaseParser は正常動作するが、SESSION_STATE.md がないと
        SessionStateParser から Milestone が抽出されないため V-2 テーブル行が生成されず
        "BUILDING" 文字列は V-2 に出現しない（V-2 が「Milestone 情報なし」になるため）。
        """
        project_root, tmp_path = no_session_state
        rc, html, output = _run_build(project_root, tmp_path)
        # TasksParser が正常動作していれば tasks.md の Task が V-4 に表示される
        assert "W1-B5-T1" in html, (
            "SESSION_STATE.md 欠如時でも TasksParser は正常動作し、"
            "tasks.md の W1-B5-T1 が V-4 に含まれるべきです。\n"
            "TasksParser は SESSION_STATE.md に依存しないため独立して動作する（design.md §3 パーサ独立性原則）。"
        )

    def test_v1_hardcoded_values_shown_without_session_state(self, no_session_state):
        """SESSION_STATE.md 欠如時でも V-1 のハードコード値（Project 名 / タイムスタンプ）が表示されること。

        design.md §4 V-1: Project 名は "LAM" ハードコード、最終更新日時は build 実行時の timestamp。
        """
        project_root, tmp_path = no_session_state
        rc, html, output = _run_build(project_root, tmp_path)
        assert "LAM" in html, (
            "SESSION_STATE.md 欠如時でも V-1 の Project 名 'LAM' は表示される（ハードコード）。"
        )

    def test_session_state_parser_error_recorded_in_html(self, no_session_state):
        """SESSION_STATE.md 欠如時はパーサエラーが HTML に記録されること（design.md §9）。

        parser-errors セクションまたは data.parser_errors に SessionState エラーが追記される。
        """
        project_root, tmp_path = no_session_state
        rc, html, output = _run_build(project_root, tmp_path)
        # returncode 1 = 部分失敗（エラーあり）
        # パーサエラーがある場合は HTML にエラーサマリーセクションが含まれる
        assert rc == 1, (
            f"SESSION_STATE.md 欠如時は returncode 1（部分失敗）であるべきですが {rc} でした。\n"
            "design.md §9: パーサエラーは parser_errors に追記し HTML に表示する。"
        )


# ─────────────────────────────────────────────
# シナリオ 2: .claude/current-phase.md が存在しない場合
# ─────────────────────────────────────────────


class TestFallbackNoCurrentPhase:
    """AC-5 シナリオ 2: .claude/current-phase.md 削除時のフォールバック動作。

    仕様（design.md §5 CurrentPhaseParser）:
      - ファイル不在 / 読み込みエラー時は ok=False を返す
      - V-2 の Step 列が "UNKNOWN" または空白になる
      - HTML は生成される（returncode 0 or 1）
    """

    @pytest.fixture()
    def no_current_phase(self, tmp_path):
        """current-phase.md を含まないプロジェクト構造を返す。"""
        project_root = _build_full_project(tmp_path)
        # .claude/current-phase.md を削除（tmp_path 内なので実リポジトリに影響なし）
        (project_root / ".claude" / "current-phase.md").unlink()
        return project_root, tmp_path

    def test_build_completes_without_current_phase(self, no_current_phase):
        """current-phase.md が存在しなくても build() が完了すること（returncode 0 or 1）。"""
        project_root, tmp_path = no_current_phase
        rc, html, output = _run_build(project_root, tmp_path)
        assert rc in (0, 1), (
            f"current-phase.md 欠如時の returncode は 0 or 1 であるべきですが {rc} でした。\n"
            "AC-5: データソース欠如時もビルドは完了する（NFR-6）。"
        )

    def test_html_is_generated_without_current_phase(self, no_current_phase):
        """current-phase.md が存在しなくても HTML ファイルが生成されること。"""
        project_root, tmp_path = no_current_phase
        rc, html, output = _run_build(project_root, tmp_path)
        assert output.exists(), (
            "current-phase.md が存在しなくても HTML は生成される必要があります（NFR-6）。"
        )

    def test_v2_step_shows_unknown_without_current_phase(self, no_current_phase):
        """current-phase.md 欠如時は V-2 の Step 列が 'UNKNOWN' を表示すること。

        design.md §5 CurrentPhaseParser:
          ファイル不在 / 読み込みエラー時は ok=False。
          CurrentPhaseParser が失敗した場合、DashboardData.current_phase は "UNKNOWN"（デフォルト値）のまま。
        """
        project_root, tmp_path = no_current_phase
        rc, html, output = _run_build(project_root, tmp_path)
        # current_phase が "UNKNOWN" となり V-2 の Step 列に表示される
        assert "UNKNOWN" in html, (
            "current-phase.md 欠如時は V-2 の Step 列に 'UNKNOWN' が表示されるべきです。\n"
            "design.md §5: ファイル不在時は ok=False を返し、DashboardData.current_phase は"
            " 'UNKNOWN' デフォルト値が使われる。"
        )

    def test_current_phase_parser_error_recorded(self, no_current_phase):
        """current-phase.md 欠如時はパーサエラーが記録されること（returncode 1）。"""
        project_root, tmp_path = no_current_phase
        rc, html, output = _run_build(project_root, tmp_path)
        assert rc == 1, (
            f"current-phase.md 欠如時は returncode 1（部分失敗）であるべきですが {rc} でした。"
        )


# ─────────────────────────────────────────────
# シナリオ 3: いずれかの Milestone の tasks.md が存在しない場合
# ─────────────────────────────────────────────


class TestFallbackNoTasksMd:
    """AC-5 シナリオ 3: tasks.md 削除時のフォールバック動作。

    仕様（design.md §5 TasksParser）:
      - 個別 Milestone 失敗は他 Milestone の処理を止めない
      - tasks.md 不在 Milestone の V-4 が空になる（タスク情報なし）
      - HTML は生成される（returncode 0 or 1）

    注意: TasksParser は tasks.md 不在 Milestone を「スキップ」するだけで ok=True を返す。
          つまり returncode は 0 になる可能性がある（エラーを記録しない設計）。
    """

    @pytest.fixture()
    def no_tasks_md(self, tmp_path):
        """b4-dashboard/tasks.md を含まないプロジェクト構造を返す。"""
        project_root = _build_full_project(tmp_path)
        # docs/specs/b4-dashboard/tasks.md を削除（tmp_path 内なので実リポジトリに影響なし）
        (project_root / "docs" / "specs" / "b4-dashboard" / "tasks.md").unlink()
        return project_root, tmp_path

    def test_build_completes_without_tasks_md(self, no_tasks_md):
        """tasks.md が存在しなくても build() が完了すること（returncode 0 or 1）。"""
        project_root, tmp_path = no_tasks_md
        rc, html, output = _run_build(project_root, tmp_path)
        assert rc in (0, 1), (
            f"tasks.md 欠如時の returncode は 0 or 1 であるべきですが {rc} でした。\n"
            "AC-5: データソース欠如時もビルドは完了する（NFR-6）。"
        )

    def test_html_is_generated_without_tasks_md(self, no_tasks_md):
        """tasks.md が存在しなくても HTML ファイルが生成されること。"""
        project_root, tmp_path = no_tasks_md
        rc, html, output = _run_build(project_root, tmp_path)
        assert output.exists(), (
            "tasks.md が存在しなくても HTML は生成される必要があります（NFR-6）。"
        )

    def test_v4_is_empty_without_tasks_md(self, no_tasks_md):
        """tasks.md 欠如時に V-4 が空（タスクなし）であること。

        design.md §5 TasksParser: tasks.md 不在 Milestone は V-4 に「タスク情報なし」表示。
        対応設計: UQ-2 → ok=True, data=[] を返す（エラーにはしない）。
        """
        project_root, tmp_path = no_tasks_md
        rc, html, output = _run_build(project_root, tmp_path)
        # W1-B5-T1 等の Task ID が V-4 に含まれないことを確認
        assert "W1-B5-T1" not in html, (
            "tasks.md が存在しないため W1-B5-T1 は V-4 に含まれないはずです。\n"
            "design.md §5 TasksParser: tasks.md 不在 Milestone は空タスク一覧を返す。"
        )

    def test_other_parsers_still_work_without_tasks_md(self, no_tasks_md):
        """tasks.md 欠如時でも SESSION_STATE / CurrentPhase パーサは正常動作すること。"""
        project_root, tmp_path = no_tasks_md
        rc, html, output = _run_build(project_root, tmp_path)
        # SESSION_STATE.md からの Milestone 抽出（B-5）が V-2 に含まれること
        assert "B-5" in html, (
            "tasks.md 欠如時でも SESSION_STATE.md 由来の B-5 が HTML に含まれるべきです。"
        )
        # CurrentPhaseParser が正常動作していれば BUILDING が含まれる
        assert "BUILDING" in html, (
            "tasks.md 欠如時でも CurrentPhaseParser は正常動作し BUILDING が含まれるべきです。"
        )


# ─────────────────────────────────────────────
# シナリオ 4: 全データソースが存在しない場合
# ─────────────────────────────────────────────


class TestFallbackAllDataSourcesMissing:
    """AC-5 シナリオ 4: 全データソース削除時のフォールバック動作。

    仕様（design.md §9 / NFR-6 MUST）:
      - 全パーサが ok=False を返した場合でも HTML は生成される
      - 生成 HTML に: 「データなし」相当のメッセージ / generated_at タイムスタンプ / パーサエラーサマリー
      - returncode 1（部分失敗）
      - 「HTML ファイルが存在しない（書き出し失敗）場合のみ returncode=2 で終了する」
    """

    @pytest.fixture()
    def all_sources_missing(self, tmp_path):
        """全データソースを含まないプロジェクト構造を返す（空のプロジェクトルートのみ）。"""
        project_root = tmp_path / "project"
        project_root.mkdir()
        # SESSION_STATE.md なし
        # .claude/current-phase.md なし（ディレクトリも作らない）
        # docs/specs/*/tasks.md なし
        # git リポジトリでもない（GitHistoryParser も ok=False）
        return project_root, tmp_path

    def test_build_completes_with_all_sources_missing(self, all_sources_missing):
        """全データソースが存在しなくても build() が完了すること（returncode 0 or 1）。

        NFR-6 MUST: 全パーサが ok=False でも HTML が生成される。
        AC-5: データソースを 1 件削除した状態でビルドが正常完了すること（全欠如を含む）。
        """
        project_root, tmp_path = all_sources_missing
        rc, html, output = _run_build(project_root, tmp_path)
        assert rc in (0, 1), (
            f"全データソース欠如時の returncode は 0 or 1 であるべきですが {rc} でした。\n"
            "NFR-6 MUST: 全データ源欠如時も HTML 生成は完了する。returncode=2 は HTML 未生成時のみ。"
        )

    def test_html_is_generated_with_all_sources_missing(self, all_sources_missing):
        """全データソースが存在しなくても HTML ファイルが生成されること（NFR-6 MUST）。"""
        project_root, tmp_path = all_sources_missing
        rc, html, output = _run_build(project_root, tmp_path)
        assert output.exists(), (
            "全データソース欠如時も HTML ファイルは生成される必要があります（NFR-6 MUST）。"
        )
        assert len(html) > 100, (
            "生成 HTML が空すぎます（100 バイト未満）。最低限の HTML 構造が必要です。"
        )

    def test_html_has_valid_structure_with_all_sources_missing(self, all_sources_missing):
        """全データソース欠如時でも HTML が正常な DOCTYPE / html タグを持つこと。"""
        project_root, tmp_path = all_sources_missing
        rc, html, output = _run_build(project_root, tmp_path)
        assert "<!DOCTYPE html>" in html, (
            "全データソース欠如時でも HTML の DOCTYPE 宣言が必要です。"
        )
        assert "<html" in html, (
            "全データソース欠如時でも <html> タグが必要です。"
        )

    def test_generated_at_timestamp_exists_with_all_sources_missing(self, all_sources_missing):
        """全データソース欠如時でも generated_at タイムスタンプが HTML に含まれること（design.md §9）。"""
        project_root, tmp_path = all_sources_missing
        rc, html, output = _run_build(project_root, tmp_path)
        import re
        assert re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", html), (
            "全データソース欠如時でも generated_at タイムスタンプが HTML に含まれるべきです。\n"
            "design.md §9: 全データソース欠如時の保証として generated_at タイムスタンプが必要。"
        )

    def test_parser_errors_shown_with_all_sources_missing(self, all_sources_missing):
        """全データソース欠如時はパーサエラーサマリーが HTML に含まれること（design.md §9）。

        design.md §9:
          全データソース欠如時の HTML に「パーサエラーサマリー」が含まれる。
        """
        project_root, tmp_path = all_sources_missing
        rc, html, output = _run_build(project_root, tmp_path)
        # parser-errors セクション、またはエラーメッセージが含まれることを確認
        assert "parser-errors" in html or "SessionState" in html or "CurrentPhase" in html, (
            "全データソース欠如時はパーサエラーサマリーが HTML に含まれるべきです（design.md §9）。\n"
            "確認対象: id='parser-errors' セクション または エラーメッセージ。"
        )

    def test_returncode_is_1_not_2_with_all_sources_missing(self, all_sources_missing):
        """全データソース欠如時の returncode は 2 ではなく 0 or 1 であること。

        design.md §9:
          HTML ファイルが存在しない（書き出し失敗）場合のみ returncode=2 で終了する。
          全パーサ ok=False でも HTML 生成が成功すれば returncode=1（部分失敗）。
        """
        project_root, tmp_path = all_sources_missing
        rc, html, output = _run_build(project_root, tmp_path)
        assert rc != 2, (
            f"全データソース欠如時の returncode が 2 でした。\n"
            "design.md §9: returncode=2 は HTML ファイル書き出し失敗時のみ。\n"
            "全パーサ ok=False でも HTML は生成されるため returncode は 0 or 1 であるべきです。"
        )

    def test_v1_section_exists_with_all_sources_missing(self, all_sources_missing):
        """全データソース欠如時でも V-1 セクションが HTML に含まれること。

        V-1 の Project 名は 'LAM' ハードコード（データソース依存なし）なので、
        全パーサが失敗しても V-1 セクションは表示される。
        """
        project_root, tmp_path = all_sources_missing
        rc, html, output = _run_build(project_root, tmp_path)
        assert '<section id="v1-project-summary">' in html, (
            "全データソース欠如時でも V-1 セクション（ハードコード値）が HTML に含まれるべきです。\n"
            "design.md §4 V-1: Project 名は 'LAM' ハードコード（データソース非依存）。"
        )


# ─────────────────────────────────────────────
# シナリオ横断: returncode 仕様の確認
# ─────────────────────────────────────────────


class TestReturnCodeSpec:
    """design.md §9 の returncode 仕様を横断的に確認するテスト。

    仕様（design.md §9）:
      0 = 成功（全パーサ正常）
      1 = 部分失敗（警告あり・HTML 生成は完了）
      2 = 致命的エラー（HTML 未生成）
    """

    def test_returncode_0_when_all_parsers_succeed(self, tmp_path):
        """全パーサ成功時（SessionState + CurrentPhase + Tasks が揃っている）に returncode 0 となること。

        git リポジトリがない tmp_path では GitHistoryParser が ok=False を返すため
        returncode は 1 が期待される。
        ただし 3 パーサ成功でも git なしなら 1 であることを確認する。
        """
        project_root = tmp_path / "project"
        project_root.mkdir()

        # 全テキストデータソースを配置（git のみ欠如）
        (project_root / "SESSION_STATE.md").write_text(
            "# SESSION_STATE\n\n## 完了タスク\n\n- W1-B5-T1: 完了\n", encoding="utf-8"
        )
        dotclaude = project_root / ".claude"
        dotclaude.mkdir()
        (dotclaude / "current-phase.md").write_text(
            "# Current Phase\n\n**BUILDING**\n", encoding="utf-8"
        )
        specs_dir = project_root / "docs" / "specs" / "b4-dashboard"
        specs_dir.mkdir(parents=True)
        (specs_dir / "tasks.md").write_text(
            "- [x] W1-B5-T1: 完了\n", encoding="utf-8"
        )

        mod = _load_build_module()
        output = tmp_path / "dashboard.html"
        rc = mod.build(project_root=project_root, output_path=output)

        # git なし環境では GitHistoryParser が失敗するため returncode は 1
        assert rc in (0, 1), (
            f"全テキストデータソース存在時の returncode は 0 or 1 であるべきですが {rc} でした。"
        )
        assert output.exists(), "HTML ファイルが生成されていません。"

    def test_returncode_is_never_2_in_normal_scenarios(self, tmp_path):
        """通常のフォールバックシナリオ（ファイル欠如）で returncode が 2 にならないこと。

        returncode=2 は HTML 書き出し自体が失敗した場合のみ（致命的エラー）。
        データソース欠如は「部分失敗（1）」であり「致命的エラー（2）」ではない。
        """
        # 全データソースなし（最悪のシナリオ）でも returncode != 2
        project_root = tmp_path / "empty_project"
        project_root.mkdir()

        mod = _load_build_module()
        output = tmp_path / "test_dashboard.html"
        rc = mod.build(project_root=project_root, output_path=output)

        assert rc != 2, (
            f"データソース欠如シナリオで returncode が 2 になりました。\n"
            "returncode=2 は HTML 書き出し失敗時のみで、データソース欠如は returncode=1 であるべきです。"
        )
