"""test_wave2_integration.py - Wave 2 統合テスト（W2-B5-T11）

対応仕様:
  - docs/specs/b4-dashboard/tasks.md §3 W2-B5-T11
  - docs/specs/b4-dashboard/requirements.md AC-4（SESSION_STATE.md の進行中タスクが V-2 に反映）
  - docs/specs/b4-dashboard/design.md §3 / §9（エラー耐障害性）
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# .claude/scripts を sys.path に追加（既存テストと同パターン）
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# プロジェクトルートの推定
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# build_dashboard.py スクリプトパス
_SCRIPT = _PROJECT_ROOT / ".claude" / "scripts" / "build_dashboard.py"

# 生成 HTML のデフォルト出力先
_OUTPUT_HTML = _PROJECT_ROOT / "docs" / "artifacts" / "dashboard" / "dashboard.html"


# ─────────────────────────────────────────────
# ヘルパー: build_dashboard.py をサブプロセスで実行
# ─────────────────────────────────────────────

def _run_build(project_root: Path = _PROJECT_ROOT, output: Path | None = None) -> subprocess.CompletedProcess:
    """build_dashboard.py を指定したプロジェクトルートで実行する。"""
    cmd = [sys.executable, str(_SCRIPT), "--project-root", str(project_root)]
    if output is not None:
        cmd += ["--output", str(output)]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60,
    )


# ─────────────────────────────────────────────
# TC-1: build_dashboard.py 実行で HTML が生成される
# ─────────────────────────────────────────────

def test_build_dashboard_returncode_not_fatal():
    """build_dashboard.py の返り値が 0 または 1 であること（致命的エラー 2 でない）。

    design.md §9: 0=成功, 1=部分失敗（警告あり・HTML 生成は完了）, 2=致命的エラー
    """
    result = _run_build()
    assert result.returncode in (0, 1), (
        f"Expected returncode 0 or 1, got {result.returncode}\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )


def test_build_dashboard_generates_html():
    """build_dashboard.py 実行後に dashboard.html が生成されること。"""
    _run_build()
    assert _OUTPUT_HTML.exists(), f"Expected {_OUTPUT_HTML} to exist"


# ─────────────────────────────────────────────
# TC-2: 生成 HTML の構造検証（V-1 / V-2 セクション）
# ─────────────────────────────────────────────

class TestGeneratedHtmlStructure:
    """生成 HTML が V-1・V-2 セクションを含むことを検証する。"""

    @pytest.fixture(autouse=True)
    def _build_once(self):
        """各テストの前に HTML を生成する。"""
        _run_build()
        assert _OUTPUT_HTML.exists()
        self._html = _OUTPUT_HTML.read_text(encoding="utf-8")

    def test_html_contains_v1_section_id(self):
        """生成 HTML に id="v1-project-summary" が含まれること。"""
        assert 'id="v1-project-summary"' in self._html

    def test_html_contains_v2_section_id(self):
        """生成 HTML に id="v2-milestones" が含まれること。"""
        assert 'id="v2-milestones"' in self._html

    def test_html_contains_b5_milestone(self):
        """生成 HTML に "B-5" が含まれること（実 SESSION_STATE.md から抽出）。

        AC-4: SESSION_STATE.md の Milestone 情報が V-2 に反映されることを確認する。
        """
        assert "B-5" in self._html, (
            "Expected 'B-5' in generated HTML. "
            "SessionStateParser should extract B-5 from SESSION_STATE.md."
        )

    def test_html_contains_current_phase(self):
        """生成 HTML に現在の Phase 文字列が含まれること（current-phase.md から抽出）。

        CurrentPhaseParser が current-phase.md から Phase を正しく抽出し
        HTML に反映していることを確認する。実ファイルの Phase 値（BUILDING/AUDITING 等）
        に依存せず、いずれか有効な Phase が含まれることを検証する。
        """
        valid_phases = ("PLANNING", "BUILDING", "AUDITING", "AUTONOMOUS")
        found = any(phase in self._html for phase in valid_phases)
        assert found, (
            "Expected one of PLANNING/BUILDING/AUDITING/AUTONOMOUS in generated HTML. "
            "CurrentPhaseParser should extract a valid Phase from .claude/current-phase.md."
        )


# ─────────────────────────────────────────────
# TC-3: build() 関数の直接呼び出し検証（parsers 登録確認）
# ─────────────────────────────────────────────

class TestBuildFunctionWithParsers:
    """build() 関数が parsers を登録して動作することを単体で検証する。"""

    def test_build_function_importable(self):
        """build_dashboard モジュールから build 関数をインポートできること。"""
        sys.path.insert(0, str(_PROJECT_ROOT / ".claude" / "scripts"))
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "build_dashboard", _SCRIPT
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert hasattr(mod, "build")

    def test_build_function_returns_0_or_1(self, tmp_path):
        """build() 関数が 0 または 1 を返すこと（parsers が空の場合でも）。"""
        sys.path.insert(0, str(_PROJECT_ROOT / ".claude" / "scripts"))
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "build_dashboard", _SCRIPT
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        output = tmp_path / "dashboard.html"
        rc = mod.build(project_root=_PROJECT_ROOT, output_path=output)
        assert rc in (0, 1), f"Expected 0 or 1, got {rc}"
        assert output.exists()

    def test_build_function_parsers_registered(self, tmp_path):
        """build() 関数実行後、SessionStateParser と CurrentPhaseParser が動作し
        生成 HTML に B-5 と BUILDING が含まれること。

        制御済みの tmp プロジェクト（current-phase.md=BUILDING / SESSION_STATE.md に B-5 記述）
        を project_root として渡すことで、実ファイルの内容に依存せず検証する。
        """
        sys.path.insert(0, str(_PROJECT_ROOT / ".claude" / "scripts"))
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "build_dashboard", _SCRIPT
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # 制御済みプロジェクト環境を tmp_path に構築
        controlled_root = tmp_path / "project"
        controlled_root.mkdir()
        dotclaude = controlled_root / ".claude"
        dotclaude.mkdir()
        (dotclaude / "current-phase.md").write_text(
            "# Current Phase\n\n**BUILDING**\n", encoding="utf-8"
        )
        (controlled_root / "SESSION_STATE.md").write_text(
            "# SESSION_STATE\n\n## 完了タスク\n\n- W1-B5-T1: テスト実装完了\n",
            encoding="utf-8",
        )

        output = tmp_path / "dashboard.html"
        mod.build(project_root=controlled_root, output_path=output)

        html = output.read_text(encoding="utf-8")
        assert "B-5" in html
        assert "BUILDING" in html


# ─────────────────────────────────────────────
# TC-4: AC-4 部分検証 - SESSION_STATE.md 不在シミュレーション
# ─────────────────────────────────────────────

class TestSessionStateMissingFallback:
    """SESSION_STATE.md が存在しない場合のフォールバック動作を検証する（AC-4 / NFR-6）。

    実ファイルの削除は行わず、空のプロジェクトを tempdir に作成して
    --project-root で渡すことで SESSION_STATE.md 不在を擬似的に再現する。
    """

    @pytest.fixture
    def empty_project(self, tmp_path) -> Path:
        """SESSION_STATE.md を持たない最小プロジェクト環境を作成する。

        .claude/current-phase.md は存在させる（Phase は確認可能）。
        SESSION_STATE.md は作成しない（不在テスト）。
        """
        # .claude ディレクトリと current-phase.md を作成
        dotclaude = tmp_path / ".claude"
        dotclaude.mkdir()
        (dotclaude / "current-phase.md").write_text(
            "# Current Phase\n\n**BUILDING**\n", encoding="utf-8"
        )
        # SESSION_STATE.md は意図的に作成しない
        return tmp_path

    def test_build_completes_without_session_state(self, empty_project, tmp_path):
        """SESSION_STATE.md 不在でも returncode が 0 または 1 であること（HTML 生成完了）。

        returncode=2 は致命的エラー（HTML 未生成）を意味するため許容しない。
        NFR-6: 全データ源欠如時も HTML 生成は続行される。
        """
        output = tmp_path / "out" / "dashboard.html"
        result = _run_build(project_root=empty_project, output=output)
        assert result.returncode in (0, 1), (
            f"Expected returncode 0 or 1 (HTML generated), got {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    def test_build_generates_html_without_session_state(self, empty_project, tmp_path):
        """SESSION_STATE.md 不在でも dashboard.html が生成されること。"""
        output = tmp_path / "out" / "dashboard.html"
        _run_build(project_root=empty_project, output=output)
        assert output.exists(), (
            f"Expected {output} to exist even when SESSION_STATE.md is missing"
        )

    def test_build_returncode_is_1_when_session_state_missing(self, empty_project, tmp_path):
        """SESSION_STATE.md 不在の場合 returncode=1（部分失敗）になること。

        SessionStateParser が ok=False を返し parser_errors に追記されるため、
        build() は 1 を返す（HTML は生成される）。
        """
        output = tmp_path / "out" / "dashboard.html"
        result = _run_build(project_root=empty_project, output=output)
        assert result.returncode == 1, (
            f"Expected returncode=1 (partial failure) when SESSION_STATE.md is missing, "
            f"got {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
