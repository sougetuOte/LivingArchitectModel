#!/usr/bin/env python3
"""
lam-stop-hook.py - LAM Stop hook: 自律ループの収束判定

bash 版 lam-stop-hook.sh の Python 移植版。
stdin から JSON を受け取り、自律ループを継続すべきか判定する。

判定ロジック:
  0. 再帰防止チェック（最優先）
  1. 状態ファイル確認
  2. 反復上限チェック
  3. コンテキスト残量チェック（PreCompact 発火検出）
  4. Green State 判定（テスト + lint）
  5. エスカレーション条件チェック
  6. 継続（block）

出力:
  正常停止時: exit 0（何も出力しない）
  継続時: stdout に {"decision": "block", "reason": "..."} を出力して exit 0
  障害時: exit 0（hook 障害で Claude をブロックしない）

対応仕様: docs/specs/hooks-python-migration/design.md H3（lam-stop-hook）
"""
from __future__ import annotations

import datetime
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

# sys.path に hooks ディレクトリを追加（_hook_utils を import するため）
_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from _hook_utils import (  # noqa: E402
    atomic_write_json,
    get_project_root,
    log_entry,
    read_stdin_json,
    run_command,
)

# 結果定数
RESULT_PASS = 1
RESULT_FAIL = 2

# PreCompact 発火から何秒以内を「直近」とみなすか（10分）
PRE_COMPACT_THRESHOLD_SECONDS = 600

# シークレットスキャン用の正規表現パターン（モジュールレベルで1回だけコンパイル）
_SECRET_PATTERN = re.compile(
    r'(password|secret|api_key|apikey|token|private_key)\s*=\s*["\'][^"\']{8,}',
    re.IGNORECASE,
)
_SAFE_PATTERN = re.compile(
    r"(test|spec|mock|example|placeholder|xxx|changeme)",
    re.IGNORECASE,
)


def _get_log_file(project_root: Path) -> Path:
    return project_root / ".claude" / "logs" / "loop.log"


def _log(log_file: Path, level: str, message: str) -> None:
    try:
        log_entry(log_file, level, "stop-hook", message)
    except Exception:
        pass


def _stop(log_file: Path, message: str) -> None:
    """停止許可: 何も出力せず exit 0。"""
    _log(log_file, "INFO", message)
    sys.exit(0)


def _block(log_file: Path, reason: str) -> None:
    """継続指示: block JSON を stdout に出力して exit 0。"""
    _log(log_file, "INFO", f"block: {reason}")
    print(json.dumps({"decision": "block", "reason": reason}), flush=True)
    sys.exit(0)


def _loop_result_label(state: dict) -> str:
    """ループ終了時の result ラベルを返す。"""
    log_entries = state.get("log")
    if not log_entries:
        return "GREEN_STATE"
    last_found = log_entries[-1].get("issues_found", 0)
    return "GREEN_STATE" if last_found == 0 else "CONVERGED"


def _save_loop_log(project_root: Path, state: dict, log_file: Path) -> None:
    """ループ終了ログを .claude/logs/ に保存する。"""
    try:
        logs_dir = project_root / ".claude" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        now = now_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        loop_log_file = logs_dir / f"loop-{now_dt.strftime('%Y%m%d-%H%M%S')}.txt"
        lines = [
            "=== Loop Log ===",
            f"timestamp: {now}",
            f"command: {state.get('command', '')}",
            f"target: {state.get('target', '')}",
            f"iterations: {state.get('iteration', 0)}",
            f"max_iterations: {state.get('max_iterations', 5)}",
            f"started_at: {state.get('started_at', '')}",
            f"result: {_loop_result_label(state)}",
            "",
            "--- Iteration Log ---",
        ]
        for entry in state.get("log", []):
            lines.append(
                f"iter {entry.get('iteration', '?')}: "
                f"found={entry.get('issues_found', 0)} "
                f"fixed={entry.get('issues_fixed', 0)} "
                f"pg={entry.get('pg', 0)} "
                f"se={entry.get('se', 0)} "
                f"pm={entry.get('pm', 0)} "
                f"tests={entry.get('test_count', 0)}"
            )
        loop_log_file.write_text("\n".join(lines), encoding="utf-8")
        _log(log_file, "INFO", f"Loop log saved to {loop_log_file}")
    except Exception:
        pass


def _validate_check_dir(cwd: str, project_root: Path) -> Path:
    """
    CWD の安全性を検証してチェック対象ディレクトリを返す。

    W-7: パストラバーサル防止。
    - PROJECT_ROOT 配下: OK
    - 実在する絶対パス: OK
    - 存在しない or 相対パス: PROJECT_ROOT にフォールバック
    """
    if not cwd:
        return project_root

    check_dir = Path(cwd)
    if not check_dir.is_absolute():
        return project_root

    # PROJECT_ROOT 配下の場合は OK
    try:
        check_dir.relative_to(project_root)
        return check_dir
    except ValueError:
        pass

    # 実在する絶対パスは OK
    if check_dir.is_dir():
        return check_dir

    return project_root


# ================================================================
# テスト・lint・セキュリティの自動検出と実行
# ================================================================


def _detect_test_framework(check_dir: Path) -> tuple[str, list[str]] | tuple[None, None]:
    """
    テストフレームワークを自動検出して (framework_name, command_args) を返す。
    検出できない場合は (None, None)。

    検出順序: pyproject.toml → package.json → go.mod → Makefile
    """
    # pyproject.toml に pytest 設定があるか
    pyproject = check_dir / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8", errors="replace")
        if "[tool.pytest" in content:
            return ("pytest", ["pytest"])

    # package.json に test スクリプトがあるか
    pkg_json = check_dir / "package.json"
    if pkg_json.exists():
        try:
            pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
            scripts = pkg.get("scripts", {})
            if "test" in scripts:
                return ("npm", ["npm", "test"])
        except Exception:
            pass

    # go.mod が存在するか
    if (check_dir / "go.mod").exists():
        return ("go", ["go", "test", "./..."])

    # Makefile に test ターゲットがあるか
    makefile = check_dir / "Makefile"
    if makefile.exists():
        content = makefile.read_text(encoding="utf-8", errors="replace")
        if re.search(r"^test\s*:", content, re.MULTILINE):
            return ("make", ["make", "test"])

    return (None, None)


def _detect_lint_tool(check_dir: Path) -> tuple[str, list[str]] | tuple[None, None]:
    """
    lint ツールを自動検出して (tool_name, command_args) を返す。
    検出できない場合は (None, None)。

    検出順序: ruff → npm lint → eslint → make lint
    """
    # pyproject.toml に ruff 設定があるか
    pyproject = check_dir / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8", errors="replace")
        if "[tool.ruff" in content:
            return ("ruff", ["ruff", "check", "."])

    # package.json に lint スクリプトがあるか
    pkg_json = check_dir / "package.json"
    if pkg_json.exists():
        try:
            pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
            scripts = pkg.get("scripts", {})
            if "lint" in scripts:
                return ("npm-lint", ["npm", "run", "lint"])
        except Exception:
            pass

    # .eslintrc* ファイルが存在するか
    eslint_files = list(check_dir.glob(".eslintrc*"))
    if eslint_files:
        return ("eslint", ["npx", "eslint", "."])

    # Makefile に lint ターゲットがあるか
    makefile = check_dir / "Makefile"
    if makefile.exists():
        content = makefile.read_text(encoding="utf-8", errors="replace")
        if re.search(r"^lint\s*:", content, re.MULTILINE):
            return ("make-lint", ["make", "lint"])

    return (None, None)


def _detect_security_tools(check_dir: Path) -> list[tuple[str, list[str]]]:
    """
    セキュリティチェックツールを検出してリストを返す。
    [(tool_name, command_args), ...]
    """
    tools = []

    if (check_dir / "package-lock.json").exists() or (check_dir / "package.json").exists():
        if shutil.which("npm"):
            tools.append(("npm-audit", ["npm", "audit", "--audit-level=critical"]))

    # npm と pip-audit は排他ではなく両方検出する（モノレポ対応）
    if (check_dir / "pyproject.toml").exists() or (check_dir / "requirements.txt").exists():
        if shutil.which("pip-audit"):
            tools.append(("pip-audit", ["pip-audit", "--desc"]))
        elif shutil.which("safety"):
            tools.append(("safety", ["safety", "check"]))

    return tools


def _run_tests(check_dir: Path, log_file: Path) -> tuple[int, int]:
    """
    テストを実行して (result, test_count) を返す。
    result: RESULT_PASS / RESULT_FAIL
    test_count: パスしたテスト数（不明の場合は 0）
    """
    framework, cmd_args = _detect_test_framework(check_dir)

    if framework is None:
        _log(log_file, "INFO", f"G1: no test framework found in {check_dir} → PASS (skip)")
        return (RESULT_PASS, 0)

    _log(log_file, "INFO", f"G1: running {framework}: {' '.join(cmd_args)}")
    exit_code, stdout, stderr = run_command(cmd_args, str(check_dir), timeout=120)

    if exit_code == 0:
        _log(log_file, "INFO", f"G1: tests PASSED ({framework})")
        # テスト数の抽出
        test_count = 0
        if framework == "pytest":
            m = re.search(r"(\d+) passed", stdout)
            if m:
                test_count = int(m.group(1))
        elif framework == "npm":
            m = re.search(r"Tests:\s+(\d+) passed", stdout)
            if m:
                test_count = int(m.group(1))
        elif framework == "go":
            test_count = stdout.count("\nok ")
        # make: テスト数抽出はスキップ
        return (RESULT_PASS, test_count)

    # タイムアウト検出（run_command は timeout 時に exit_code=1 を返す）
    if "timed out" in stderr:
        _log(log_file, "WARN", "G1: test timeout (120s) → FAIL")
    else:
        _log(log_file, "INFO", f"G1: tests FAILED (exit {exit_code})")
    return (RESULT_FAIL, 0)


def _run_lint(check_dir: Path, log_file: Path) -> int:
    """
    lint を実行して result を返す。
    result: RESULT_PASS / RESULT_FAIL
    """
    tool, cmd_args = _detect_lint_tool(check_dir)

    if tool is None:
        _log(log_file, "INFO", f"G2: no lint tool found in {check_dir} → PASS (skip)")
        return RESULT_PASS

    _log(log_file, "INFO", f"G2: running {tool}: {' '.join(cmd_args)}")
    exit_code, _, stderr = run_command(cmd_args, str(check_dir), timeout=60)

    if exit_code == 0:
        _log(log_file, "INFO", f"G2: lint PASSED ({tool})")
        return RESULT_PASS

    if "timed out" in stderr:
        _log(log_file, "WARN", "G2: lint timeout (60s) → FAIL")
    else:
        _log(log_file, "INFO", f"G2: lint FAILED (exit {exit_code})")
    return RESULT_FAIL


def _run_security(check_dir: Path, log_file: Path) -> int:
    """
    セキュリティチェックを実行して result を返す。
    """
    tools = _detect_security_tools(check_dir)
    sec_fail = False

    for tool_name, cmd_args in tools:
        _log(log_file, "INFO", f"G5: running {tool_name}")
        exit_code, _, stderr = run_command(cmd_args, str(check_dir), timeout=60)
        if exit_code != 0 and "timed out" not in stderr:
            _log(log_file, "INFO", f"G5: {tool_name} found issues")
            sec_fail = True
        elif "timed out" in stderr:
            _log(log_file, "WARN", f"G5: {tool_name} timeout (60s)")

    # シークレットスキャン（src/ ディレクトリが存在する場合）
    src_dir = check_dir / "src"
    if src_dir.is_dir():
        secret_count = 0
        for src_file in src_dir.rglob("*"):
            if not src_file.is_file():
                continue
            # 1MB超のファイルはバイナリ等の可能性が高いためスキップ
            try:
                if src_file.stat().st_size > 1_000_000:
                    continue
            except OSError:
                continue
            try:
                content = src_file.read_text(encoding="utf-8", errors="replace")
                for line in content.splitlines():
                    if _SECRET_PATTERN.search(line) and not _SAFE_PATTERN.search(line):
                        secret_count += 1
            except Exception:
                pass
        if secret_count > 0:
            _log(log_file, "WARN", f"G5: potential secret leak detected in src/ ({secret_count} matches)")
            sec_fail = True

    if sec_fail:
        _log(log_file, "INFO", "G5: security checks FAILED")
        return RESULT_FAIL

    _log(log_file, "INFO", "G5: security checks PASSED")
    return RESULT_PASS


def _check_issue_recurrence(state: dict) -> bool:
    """
    同一 Issue 再発チェック。
    前サイクルで issues_fixed=0 が連続した場合 True を返す。
    """
    log = state.get("log", [])
    if len(log) < 2:
        return False
    last = log[-1]
    prev = log[-2]
    if (
        last.get("issues_found", 0) > 0
        and last.get("issues_fixed", 0) == 0
        and prev.get("issues_found", 0) > 0
        and prev.get("issues_fixed", 0) == 0
    ):
        return True
    return False


def main() -> None:
    project_root = get_project_root()
    state_file = project_root / ".claude" / "lam-loop-state.json"
    pre_compact_flag = project_root / ".claude" / "pre-compact-fired"
    log_file = _get_log_file(project_root)

    # stdin から JSON を読み取る
    input_data = read_stdin_json()

    # ================================================================
    # STEP 0: 再帰防止チェック（最優先）(AC-2.8c)
    # ================================================================
    if input_data.get("stop_hook_active") is True:
        _stop(log_file, "stop_hook_active=true → recursion guard exit")

    # ================================================================
    # STEP 1: 状態ファイル確認 (AC-2.5)
    # ================================================================
    if not state_file.exists():
        _stop(log_file, "no state file → normal stop")

    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception:
        _stop(log_file, "failed to read state file → normal stop")

    if not state.get("active"):
        _stop(log_file, "active=false → loop disabled, normal stop")

    iteration = int(state.get("iteration", 0))
    max_iterations = int(state.get("max_iterations", 5))
    command = state.get("command", "")

    _log(log_file, "INFO", f"loop active: command={command}, iteration={iteration}/{max_iterations}")

    # ================================================================
    # STEP 2: 反復上限チェック (AC-2.6)
    # ================================================================
    if iteration >= max_iterations:
        _log(log_file, "WARN", f"max_iterations reached ({iteration}/{max_iterations}) → stop loop")
        _save_loop_log(project_root, state, log_file)
        try:
            state_file.unlink()
        except Exception:
            pass
        _stop(log_file, "max_iterations reached → stopped")

    # ================================================================
    # STEP 3: コンテキスト残量チェック (AC-2.7, AC-2.11a)
    # ================================================================
    if pre_compact_flag.exists():
        try:
            flag_content = pre_compact_flag.read_text(encoding="utf-8").strip()
            # タイムスタンプをパースしてエポック秒に変換
            flag_dt = datetime.datetime.fromisoformat(flag_content.replace("Z", "+00:00"))
            now_dt = datetime.datetime.now(datetime.timezone.utc)
            elapsed = (now_dt - flag_dt).total_seconds()
            if elapsed <= PRE_COMPACT_THRESHOLD_SECONDS:
                try:
                    state_file.unlink()
                except Exception:
                    pass
                _stop(log_file, f"PreCompact fired {elapsed:.0f}s ago → context pressure, stop loop")
        except Exception:
            # ファイルの mtime をフォールバックとして使用
            try:
                flag_mtime = os.path.getmtime(str(pre_compact_flag))
                elapsed = time.time() - flag_mtime
                if elapsed <= PRE_COMPACT_THRESHOLD_SECONDS:
                    try:
                        state_file.unlink()
                    except Exception:
                        pass
                    _stop(log_file, f"PreCompact fired {elapsed:.0f}s ago (mtime) → context pressure, stop loop")
            except Exception:
                pass

    # ================================================================
    # STEP 4: Green State 判定 (AC-2.8, AC-2.8a, AC-2.8b)
    # ================================================================
    cwd = input_data.get("cwd", "")
    check_dir = _validate_check_dir(cwd, project_root)

    test_result, test_count = _run_tests(check_dir, log_file)
    lint_result = _run_lint(check_dir, log_file)
    security_result = _run_security(check_dir, log_file)

    # ================================================================
    # STEP 5: エスカレーション条件チェック (AC-2.9)
    # ================================================================

    # テスト数減少チェック
    log_entries = state.get("log", [])
    prev_test_count = 0
    if log_entries:
        prev_test_count = int(log_entries[-1].get("test_count", 0))

    # test_count=0 はフレームワーク未検出等でカウント不明の場合。誤検知を避けるためスキップ
    if prev_test_count > 0 and test_count > 0 and test_count < prev_test_count:
        _log(log_file, "WARN", f"ESC: test count decreased ({prev_test_count} → {test_count}) → escalate to human")
        try:
            state_file.unlink()
        except Exception:
            pass
        _stop(log_file, f"ESC: test count decreased ({prev_test_count} → {test_count}) → escalate to human")

    # 同一 Issue 再発チェック
    if _check_issue_recurrence(state):
        try:
            state_file.unlink()
        except Exception:
            pass
        _stop(log_file, "ESC: same issues recurring (no fix for 2 cycles) → escalate to human")

    # ================================================================
    # STEP 5b: Green State 条件の総合判定
    # ================================================================
    fail_parts = []
    if test_result == RESULT_FAIL:
        fail_parts.append("テスト失敗")
    if lint_result == RESULT_FAIL:
        fail_parts.append("lint 失敗")
    if security_result == RESULT_FAIL:
        fail_parts.append("セキュリティチェック失敗")

    green_state = len(fail_parts) == 0
    fullscan_pending = bool(state.get("fullscan_pending", False))

    if green_state:
        if fullscan_pending:
            _log(log_file, "INFO", "Green State achieved, fullscan_pending=true → clear flag, continue next cycle for fullscan")
            state["fullscan_pending"] = False
            try:
                atomic_write_json(state_file, state)
            except Exception:
                pass
            # fullscan のため継続（fall through to block）
        else:
            _log(log_file, "INFO", "Green State achieved → stop loop (normal convergence)")
            _save_loop_log(project_root, state, log_file)
            try:
                state_file.unlink()
            except Exception:
                pass
            _stop(log_file, "Green State achieved → loop converged")

    # ================================================================
    # STEP 6: 継続（block）(AC-2.10)
    # ================================================================
    new_iteration = iteration + 1
    state["iteration"] = new_iteration
    # テスト数を log エントリに記録。log_entries[-1] は前サイクルの最終エントリ。
    # test_count=0 はフレームワーク未検出等でカウント不明のため記録しない。
    if test_count > 0 and log_entries:
        log_entries[-1]["test_count"] = test_count
    try:
        atomic_write_json(state_file, state)
    except Exception:
        pass

    _log(log_file, "INFO", f"continuing: iteration {iteration} → {new_iteration}")

    if green_state and fullscan_pending:
        reason = f"Green State 達成。fullscan を実行するためサイクル {new_iteration} を開始。"
    else:
        remaining_msg = " + ".join(fail_parts) if fail_parts else "Green State 未達"
        reason = f"Green State 未達。サイクル {new_iteration} を開始。残Issue: {remaining_msg}"

    _block(log_file, reason)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        # 障害時は exit 0（hook 障害で Claude をブロックしない）
        sys.exit(0)
