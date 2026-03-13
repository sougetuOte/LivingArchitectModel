"""
test_lam_stop_hook.py - lam-stop-hook.py のユニットテスト

テスト対象: .claude/hooks/lam-stop-hook.py
テスト戦略: LAM_PROJECT_ROOT 環境変数で tmp ディレクトリを指定し、
           状態ファイルを自由に操作する。stdin はモンキーパッチで差し替え。
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

# テスト対象モジュールのインポート準備
_HOOKS_DIR = Path(__file__).resolve().parent.parent / ".claude" / "hooks"


def _write_state(project_root: Path, state: dict) -> Path:
    """lam-loop-state.json を書き込む。"""
    state_file = project_root / ".claude" / "lam-loop-state.json"
    state_file.write_text(json.dumps(state), encoding="utf-8")
    return state_file


def _make_stdin(data: dict) -> io.StringIO:
    return io.StringIO(json.dumps(data))


def _run_hook(monkeypatch: pytest.MonkeyPatch, stdin_data: dict, capsys) -> tuple[int, str]:
    """hook の main() を実行し、(exit_code, stdout) を返す。"""
    monkeypatch.setattr("sys.stdin", _make_stdin(stdin_data))

    # モジュールを毎回リロード（グローバル状態のリセット）
    if "lam_stop_hook" in sys.modules:
        del sys.modules["lam_stop_hook"]

    # hooks ディレクトリを sys.path に追加（monkeypatch で自動復元）
    monkeypatch.syspath_prepend(str(_HOOKS_DIR))

    # ハイフン入りファイル名なので importlib を使用
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "lam_stop_hook", _HOOKS_DIR / "lam-stop-hook.py"
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec from {_HOOKS_DIR / 'lam-stop-hook.py'}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["lam_stop_hook"] = mod

    exit_code = 0
    try:
        spec.loader.exec_module(mod)
        mod.main()
    except SystemExit as e:
        exit_code = e.code if e.code is not None else 0

    captured = capsys.readouterr()
    return exit_code, captured.out


# ================================================================
# テストケース
# ================================================================


class TestNoStateFile:
    """状態ファイルが存在しない場合、正常停止する。"""

    def test_no_state_file_allows_stop(
        self, project_root: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ):
        exit_code, stdout = _run_hook(monkeypatch, {}, capsys)
        assert exit_code == 0
        assert stdout.strip() == ""  # block JSON が出力されない = 停止許可


class TestActiveFlag:
    """active=false の場合、正常停止する。"""

    def test_inactive_loop_allows_stop(
        self, project_root: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ):
        _write_state(project_root, {"active": False, "iteration": 0, "max_iterations": 5})
        exit_code, stdout = _run_hook(monkeypatch, {}, capsys)
        assert exit_code == 0
        assert stdout.strip() == ""


class TestPmPending:
    """pm_pending=true の場合、block せず停止を許可する。"""

    def test_pm_pending_allows_stop(
        self, project_root: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ):
        _write_state(
            project_root,
            {
                "active": True,
                "pm_pending": True,
                "iteration": 1,
                "max_iterations": 5,
                "command": "full-review",
                "log": [],
            },
        )
        exit_code, stdout = _run_hook(monkeypatch, {}, capsys)
        assert exit_code == 0
        assert stdout.strip() == ""  # block しない

    def test_pm_pending_false_continues_loop(
        self, project_root: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ):
        """pm_pending=false でテスト未通過の場合はループ継続（block）。"""
        # pyproject.toml を置いて pytest を検出させる（テストなし → exit 5 → FAIL）
        (project_root / "pyproject.toml").write_text(
            "[tool.pytest.ini_options]\n", encoding="utf-8"
        )
        _write_state(
            project_root,
            {
                "active": True,
                "pm_pending": False,
                "iteration": 1,
                "max_iterations": 5,
                "command": "full-review",
                "log": [],
            },
        )
        exit_code, stdout = _run_hook(monkeypatch, {}, capsys)
        assert exit_code == 0
        parsed = json.loads(stdout.strip())
        assert parsed["decision"] == "block"


class TestMaxIterations:
    """反復上限に達した場合、停止する。"""

    def test_max_iterations_stops_loop(
        self, project_root: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ):
        _write_state(
            project_root,
            {
                "active": True,
                "iteration": 5,
                "max_iterations": 5,
                "command": "full-review",
                "log": [],
            },
        )
        exit_code, stdout = _run_hook(monkeypatch, {}, capsys)
        assert exit_code == 0
        assert stdout.strip() == ""
        # 状態ファイルが削除されている
        state_file = project_root / ".claude" / "lam-loop-state.json"
        assert not state_file.exists()


class TestRecursionGuard:
    """stop_hook_active=true の場合、再帰防止で停止する。"""

    def test_recursion_guard(
        self, project_root: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ):
        _write_state(
            project_root,
            {"active": True, "iteration": 0, "max_iterations": 5, "command": "full-review", "log": []},
        )
        exit_code, stdout = _run_hook(monkeypatch, {"stop_hook_active": True}, capsys)
        assert exit_code == 0
        assert stdout.strip() == ""


class TestFullscanPending:
    """fullscan_pending=true の場合、Green State でも継続する。"""

    def test_fullscan_pending_continues(
        self, project_root: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ):
        _write_state(
            project_root,
            {
                "active": True,
                "fullscan_pending": True,
                "iteration": 1,
                "max_iterations": 5,
                "command": "full-review",
                "log": [],
            },
        )
        exit_code, stdout = _run_hook(monkeypatch, {}, capsys)
        assert exit_code == 0
        # Green State でも fullscan_pending=true なら block
        parsed = json.loads(stdout.strip())
        assert parsed["decision"] == "block"
        assert "fullscan" in parsed["reason"]
