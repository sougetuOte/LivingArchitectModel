"""test_lam_stop_hook_env_allowlist.py - W-14: G1 checker サブプロセス env allowlist 化

仕様: docs/tasks/hooks-security-hardening-ci.md W-14
- `_run_g1_checker` が機密環境変数（AWS_SECRET_ACCESS_KEY 等）を子プロセスに渡さない
- LAM_PROJECT_ROOT は必ず引き継ぐ
- allowlist 内の必須キー（PATH など）は引き継ぐ
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

_HOOKS_DIR = Path(__file__).resolve().parent.parent
_STOP_HOOK_PATH = _HOOKS_DIR / "lam-stop-hook.py"


@pytest.fixture()
def stop_hook(monkeypatch: pytest.MonkeyPatch):
    """lam-stop-hook.py を importlib.util 経由で読み込む（ハイフン回避）。"""
    monkeypatch.syspath_prepend(str(_HOOKS_DIR))
    spec = importlib.util.spec_from_file_location("lam_stop_hook", _STOP_HOOK_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def capture_env(monkeypatch: pytest.MonkeyPatch, stop_hook):
    """stop_hook モジュール内の subprocess.run を捕獲し、渡された env を返す。"""
    captured: dict = {}

    def fake_run(cmd, **kwargs):
        captured["env"] = kwargs.get("env")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(stop_hook.subprocess, "run", fake_run)
    return captured


class TestEnvAllowlist:
    """W-14: G1 checker 起動時の env が allowlist 化されている。"""

    def test_secret_env_not_propagated(
        self,
        capture_env,
        stop_hook,
        project_root: Path,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """機密環境変数は G1 checker に継承されない。"""
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "should-not-leak")
        monkeypatch.setenv("GITHUB_TOKEN", "should-not-leak")
        monkeypatch.setenv("OPENAI_API_KEY", "should-not-leak")

        log_file = project_root / ".claude" / "logs" / "test.log"
        stop_hook._run_g1_checker(project_root, log_file)

        env = capture_env["env"]
        assert env is not None, "_run_g1_checker は env を明示的に渡さねばならない"
        assert "AWS_SECRET_ACCESS_KEY" not in env
        assert "GITHUB_TOKEN" not in env
        assert "OPENAI_API_KEY" not in env

    def test_lam_project_root_propagated(
        self,
        capture_env,
        stop_hook,
        project_root: Path,
    ):
        """LAM_PROJECT_ROOT は必ず子プロセスに渡る。"""
        log_file = project_root / ".claude" / "logs" / "test.log"
        stop_hook._run_g1_checker(project_root, log_file)

        env = capture_env["env"]
        assert env is not None
        assert env.get("LAM_PROJECT_ROOT") == str(project_root)

    def test_path_propagated_when_present(
        self,
        capture_env,
        stop_hook,
        project_root: Path,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """PATH（allowlist 内）は親環境にあれば子プロセスに渡る。"""
        monkeypatch.setenv("PATH", "/fake/path")

        log_file = project_root / ".claude" / "logs" / "test.log"
        stop_hook._run_g1_checker(project_root, log_file)

        env = capture_env["env"]
        assert env is not None
        assert env.get("PATH") == "/fake/path"


class TestAllowlistDefinition:
    """W-14: allowlist 定義が _hook_utils に存在し、テストの allowlist と一致する。"""

    def test_checker_env_allowlist_exists(self, hook_utils):
        """_hook_utils に CHECKER_ENV_ALLOWLIST が公開されている。"""
        assert hasattr(hook_utils, "CHECKER_ENV_ALLOWLIST")
        allowlist = hook_utils.CHECKER_ENV_ALLOWLIST
        assert isinstance(allowlist, tuple)
        # 最低限必要なキーが含まれる
        for required in ("PATH", "HOME", "LANG", "LAM_PROJECT_ROOT", "VIRTUAL_ENV"):
            assert required in allowlist, f"{required} は allowlist に必要"

    def test_build_allowlisted_env_helper(
        self, hook_utils, monkeypatch: pytest.MonkeyPatch
    ):
        """build_allowlisted_env が allowlist のみを抽出し extra をマージする。"""
        monkeypatch.setenv("PATH", "/fake/path")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "should-not-leak")

        env = hook_utils.build_allowlisted_env({"LAM_PROJECT_ROOT": "/tmp/root"})

        assert env.get("PATH") == "/fake/path"
        assert env.get("LAM_PROJECT_ROOT") == "/tmp/root"
        assert "AWS_SECRET_ACCESS_KEY" not in env
