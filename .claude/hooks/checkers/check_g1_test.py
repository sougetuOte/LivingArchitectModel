#!/usr/bin/env python3
"""check_g1_test.py - G1（テスト全パス）の決定的 checker（design D3）。

green-state-definition.md §3.1 のテストフレームワーク自動検出を実装し、
検出したテストコマンドをサブプロセス実行して exit code で G1 を判定する。

出力規約（findings B / design D3）:
  PASS  → exit 0（stdout/stderr 何も出さない）
  FAIL  → exit 2（stderr に赤の詳細）
テストFW 未検出・コマンド未導入は PASS-skip（exit 0）でループを阻害しない。
timeout（既定 120s）超過は FAIL 扱い（exit 2）。

Stop hook が `python3 checkers/check_g1_test.py` としてサブプロセス実行する想定。
exit code は hook が checker_results に記録する（モデル改竄不能）。

対応仕様: docs/specs/green-state-definition.md §3.1 / design.md D3 / FR-4.1a / FR-4.3
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

# sys.path に hooks ディレクトリを追加（_hook_utils を import するため）
_HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from _hook_utils import build_allowlisted_env, get_project_root  # noqa: E402

# green-state §3.1: 各テストコマンドの既定 timeout（hooks 全体 600s 内に収める）
DEFAULT_TIMEOUT = 120


def detect_test_command(project_root: Path) -> list[str] | None:
    """green-state §3.1 のテストFW自動検出。検出順に判定し、論理コマンドを返す。

    検出順序:
      1. pyproject.toml に [tool.pytest] または pytest 依存 → pytest
      2. package.json に "test" スクリプト           → npm test
      3. go.mod が存在                                → go test ./...
      4. Makefile に test ターゲット                  → make test
      5. いずれもなし                                 → None（PASS-skip）
    """
    pyproject = project_root / "pyproject.toml"
    if pyproject.is_file():
        try:
            content = pyproject.read_text(encoding="utf-8")
        except OSError:
            content = ""
        # "pytest" の broad match は意図的仕様:
        # pytest への依存記述（dependencies = ["pytest>=7"]等）も検出対象とするため。
        if content and ("[tool.pytest" in content or "pytest" in content):
            return ["pytest"]

    package_json = project_root / "package.json"
    if package_json.is_file():
        try:
            pkg = json.loads(package_json.read_text(encoding="utf-8"))
        except Exception:
            pkg = {}
        scripts = pkg.get("scripts")
        if isinstance(scripts, dict) and "test" in scripts:
            return ["npm", "test"]

    if (project_root / "go.mod").is_file():
        return ["go", "test", "./..."]

    makefile = project_root / "Makefile"
    if makefile.is_file():
        try:
            content = makefile.read_text(encoding="utf-8")
        except OSError:
            content = ""
        if content and re.search(r"^test:", content, re.MULTILINE):
            return ["make", "test"]

    return None


def _to_exec_command(cmd: list[str]) -> list[str]:
    """論理コマンドを実行コマンドへ変換。

    pytest は PATH 非依存にするため `python -m pytest` で実行する
    （green-state §3.1 の「pytest」と等価）。他はコマンド名のまま。
    """
    if cmd == ["pytest"]:
        return [sys.executable, "-m", "pytest"]
    return cmd


def run_check(project_root: Path, timeout: int = DEFAULT_TIMEOUT) -> tuple[int, str]:
    """G1 を判定する。

    Returns:
        (exit_code, detail): exit_code は 0=PASS / 2=FAIL。
        detail は FAIL 時の赤の詳細、または PASS-skip の理由。
    """
    cmd = detect_test_command(project_root)
    if cmd is None:
        return 0, "no test framework detected (G1 PASS-skip)"

    exec_cmd = _to_exec_command(cmd)
    try:
        proc = subprocess.run(
            exec_cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
            env=build_allowlisted_env(),
        )
    except subprocess.TimeoutExpired:
        return 2, f"G1 test timeout after {timeout}s: {' '.join(cmd)}"
    except FileNotFoundError:
        return 0, f"test command not found: {cmd[0]} (G1 PASS-skip)"

    if proc.returncode == 0:
        return 0, "G1 tests passed"

    detail = ((proc.stdout or "") + (proc.stderr or "")).strip()
    return (
        2,
        f"G1 tests failed (exit {proc.returncode}): {' '.join(cmd)}\n{detail[-2000:]}",
    )


def main() -> None:
    """Stop hook からサブプロセス実行されるエントリポイント。"""
    project_root = get_project_root()
    exit_code, detail = run_check(project_root)
    if exit_code != 0:
        sys.stderr.write(detail + "\n")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
