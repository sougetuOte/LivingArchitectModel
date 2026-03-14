"""
conftest.py - pytest 共通 fixtures

W2-T1: conftest.py（共通 pytest fixtures）
対応仕様: design.md Section 4
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# テスト実行に必要な最小限の環境変数のみ引き継ぐ
_ENV_ALLOWLIST = (
    "PATH", "HOME", "LANG", "LC_ALL", "TERM",
    "TMPDIR", "TEMP", "TMP",
    "VIRTUAL_ENV", "CONDA_PREFIX",
    "PYTHONPATH", "PYTHONDONTWRITEBYTECODE",
)

# hooks ディレクトリのパス
_HOOKS_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture()
def project_root(tmp_path: Path) -> Path:
    """テスト用の仮プロジェクトルートを作成する。

    .claude/logs/ ディレクトリと .claude/ ディレクトリを作成し、
    フックが期待するディレクトリ構造を再現する。
    実プロジェクトへの汚染を防ぐため tmp_path を使用する。
    """
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    logs_dir = claude_dir / "logs"
    logs_dir.mkdir()
    return tmp_path


@pytest.fixture(autouse=True)
def _set_project_root(project_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """LAM_PROJECT_ROOT を自動設定する。"""
    monkeypatch.setenv("LAM_PROJECT_ROOT", str(project_root))


@pytest.fixture()
def hooks_on_syspath(monkeypatch: pytest.MonkeyPatch) -> Path:
    """hooks ディレクトリを sys.path に追加し、テスト後に自動復元する。"""
    monkeypatch.syspath_prepend(str(_HOOKS_DIR))
    return _HOOKS_DIR


@pytest.fixture()
def hook_utils(hooks_on_syspath: Path):
    """_hook_utils モジュールを import して返す。sys.path は自動復元される。"""
    import _hook_utils

    return _hook_utils


@pytest.fixture()
def hook_runner(project_root: Path):
    """フックを subprocess で実行するヘルパー関数を返す fixture。

    返す run_hook() 関数の仕様:
    - subprocess.run で sys.executable を使用（python3 ハードコード回避）
    - stdin JSON 入力対応
    - stdout, stderr, exit code を CompletedProcess として返却
    - タイムアウト 30 秒設定
    - LAM_PROJECT_ROOT を tmp_path に設定（実プロジェクト汚染防止）
    """

    def run_hook(
        hook_path: Path | str,
        input_json: dict | None = None,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """フックスクリプトを subprocess で実行する。

        Args:
            hook_path: 実行するフックスクリプトのパス（Path または str）
            input_json: stdin に渡す JSON オブジェクト。None の場合は空文字列を渡す
            env: 追加の環境変数。LAM_PROJECT_ROOT は自動設定される

        Returns:
            subprocess.CompletedProcess: stdout, stderr, returncode を含む
        """
        stdin_input = json.dumps(input_json) if input_json is not None else ""
        merged_env = {
            k: v for k, v in os.environ.items() if k in _ENV_ALLOWLIST
        }
        merged_env["LAM_PROJECT_ROOT"] = str(project_root)
        merged_env.update(env or {})
        return subprocess.run(
            [sys.executable, str(hook_path)],
            input=stdin_input,
            capture_output=True,
            text=True,
            env=merged_env,
            timeout=30,
        )

    return run_hook


def write_state(project_root: Path, state: dict) -> Path:
    """テスト用の lam-loop-state.json を書き込む共通ヘルパー。"""
    state_file = project_root / ".claude" / "lam-loop-state.json"
    state_file.write_text(json.dumps(state), encoding="utf-8")
    return state_file
