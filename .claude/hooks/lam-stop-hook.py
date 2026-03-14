#!/usr/bin/env python3
"""
lam-stop-hook.py - LAM Stop hook: 自律ループの収束判定

bash 版 lam-stop-hook.sh の Python 移植版。
stdin から JSON を受け取り、自律ループを継続すべきか判定する。

判定ロジック:
  1. 再帰防止チェック（最優先）
  2. 状態ファイル確認
  3. 反復上限チェック
  4. コンテキスト残量チェック（PreCompact 発火検出）
  5. Green State 判定（テスト + lint + セキュリティ）
  6. エスカレーション条件チェック
  7. 継続（block）

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
    now_utc_iso8601,
    read_stdin_json,
    run_command,
)

# 結果定数（exit code ではなく内部判定用。0 は「未判定」として予約）
RESULT_PASS = 1
RESULT_FAIL = 2

# PreCompact 発火から何秒以内を「直近」とみなすか（10分）
PRE_COMPACT_THRESHOLD_SECONDS = 600

# シークレットスキャン用の正規表現パターン（モジュールレベルで1回だけコンパイル）
# グループ2でシークレット値部分をキャプチャし、_SAFE_PATTERN は値部分のみに適用する
_SECRET_PATTERN = re.compile(
    r'(password|secret|api_key|apikey|token|private_key)\s*[=:]\s*["\']([^"\']{8,})',
    re.IGNORECASE,
)
# _SECRET_PATTERN のグループ2（値部分）に適用し、テスト用ダミー値を除外する
_SAFE_PATTERN = re.compile(
    r"(\btest\b|\bspec\b|\bmock\b|\bexample\b|\bplaceholder\b|\bxxx\b|\bchangeme\b)",
    re.IGNORECASE,
)

# シークレットスキャン時に除外するディレクトリ
_SCAN_EXCLUDE_DIRS = frozenset({".git", "node_modules", "__pycache__", ".venv", ".pytest_cache"})

# シークレットスキャン対象の拡張子
_SCAN_TARGET_EXTENSIONS = frozenset({
    ".py", ".js", ".ts", ".json", ".yaml", ".yml",
    ".toml", ".cfg", ".ini", ".sh", ".env", ".md", ".txt",
})


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


def _save_loop_log(
    project_root: Path,
    state: dict,
    log_file: Path,
    convergence_reason: str = "green_state",
) -> None:
    """ループ終了ログを .claude/logs/ に保存する。"""
    try:
        logs_dir = log_file.parent
        logs_dir.mkdir(parents=True, exist_ok=True)
        now = now_utc_iso8601()
        now_dt = datetime.datetime.fromisoformat(now.replace("Z", "+00:00"))
        loop_log_file = logs_dir / f"loop-{now_dt.strftime('%Y%m%d-%H%M%S')}.txt"
        lines = [
            "=== LAM Loop Log ===",
            f"Command: {state.get('command', '')}",
            f"Target: {state.get('target', '')}",
            f"Started: {state.get('started_at', '')}",
            f"Completed: {now}",
            f"Total Iterations: {state.get('iteration', 0)}",
            f"Convergence: {convergence_reason}",
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
    - それ以外: PROJECT_ROOT にフォールバック
    """
    if not cwd:
        return project_root

    check_dir = Path(cwd).resolve()
    if not check_dir.is_absolute():
        return project_root

    # PROJECT_ROOT 配下の場合のみ OK（resolve() で symlink を解決済み）
    try:
        check_dir.relative_to(project_root.resolve())
        return check_dir
    except ValueError:
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

    # .eslintrc* または eslint.config.* ファイルが存在するか（legacy + flat config 対応）
    eslint_files = list(check_dir.glob(".eslintrc*")) + list(check_dir.glob("eslint.config.*"))
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
    # pyproject.toml に [project] セクションがある場合、または requirements.txt がある場合のみ実行
    # （pytest 設定のみの pyproject.toml でグローバル環境を監査する偽陽性を防止）
    has_python_deps = (check_dir / "requirements.txt").exists()
    if not has_python_deps:
        pyproject = check_dir / "pyproject.toml"
        if pyproject.exists():
            try:
                content = pyproject.read_text(encoding="utf-8", errors="replace")
                has_python_deps = "[project]" in content or "[tool.poetry" in content
            except Exception:
                pass
    if has_python_deps:
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
            test_count = len(re.findall(r"^ok\t", stdout, re.MULTILINE))
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
            _log(log_file, "WARN", f"G5: {tool_name} timeout (60s) → treating as FAIL")
            sec_fail = True

    # シークレットスキャン（check_dir 全体を再帰走査）
    secret_count = 0
    for scan_file in check_dir.rglob("*"):
        if scan_file.is_symlink():
            continue
        if not scan_file.is_file():
            continue
        # 除外ディレクトリ内のファイルをスキップ
        try:
            rel_parts = scan_file.relative_to(check_dir).parts
        except ValueError:
            continue
        if any(part in _SCAN_EXCLUDE_DIRS for part in rel_parts):
            continue
        try:
            if scan_file.stat().st_size > 1_000_000:
                continue
        except OSError:
            continue
        # テキストファイルのみ対象（拡張子で判定）
        if scan_file.suffix not in _SCAN_TARGET_EXTENSIONS:
            continue
        try:
            content = scan_file.read_text(encoding="utf-8", errors="replace")
            try:
                rel = scan_file.relative_to(check_dir)
            except ValueError:
                rel = scan_file.name
            for line_no, line in enumerate(content.splitlines(), 1):
                m = _SECRET_PATTERN.search(line)
                if m and not _SAFE_PATTERN.search(m.group(2)):
                    secret_count += 1
                    _log(log_file, "WARN", f"G5: potential secret in {rel}:{line_no} (key={m.group(1)})")
        except Exception as e:
            try:
                rel = scan_file.relative_to(check_dir)
            except ValueError:
                rel = scan_file.name
            _log(log_file, "WARN", f"G5: failed to read {rel}: {type(e).__name__}")
    if secret_count > 0:
        _log(log_file, "WARN", f"G5: potential secret leak detected ({secret_count} matches)")
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
    return (
        last.get("issues_found", 0) > 0
        and last.get("issues_fixed", 0) == 0
        and prev.get("issues_found", 0) > 0
        and prev.get("issues_fixed", 0) == 0
    )


def _cleanup_state_file(state_file: Path) -> None:
    """状態ファイルを安全に削除する。"""
    try:
        state_file.unlink()
    except Exception:
        pass


def _check_recursion_and_state(
    input_data: dict, state_file: Path, log_file: Path
) -> dict:
    """STEP 1-2: 再帰防止・状態ファイル確認。有効な state dict を返す。

    停止条件に該当した場合は _stop() で SystemExit を送出する。
    """
    if input_data.get("stop_hook_active") is True:
        _stop(log_file, "stop_hook_active=true → recursion guard exit")

    if not state_file.exists():
        _stop(log_file, "no state file → normal stop")

    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception as e:
        _log(log_file, "ERROR", f"state file read/parse error: {type(e).__name__}: {e}")
        _stop(log_file, "failed to read state file → normal stop")

    if not state.get("active"):
        _stop(log_file, "active=false → loop disabled, normal stop")

    if state.get("pm_pending"):
        _stop(log_file, "pm_pending=true → waiting for human decision")

    return state


def _check_max_iterations(
    state: dict, state_file: Path, project_root: Path, log_file: Path
) -> tuple[int, int]:
    """STEP 3: 反復上限チェック。(iteration, max_iterations) を返す。"""
    iteration = int(state.get("iteration", 0))
    max_iterations = int(state.get("max_iterations", 5))

    if iteration >= max_iterations:
        _log(log_file, "WARN", f"max_iterations reached ({iteration}/{max_iterations}) → stop loop")
        _save_loop_log(project_root, state, log_file, "max_iterations")
        _cleanup_state_file(state_file)
        _stop(log_file, "max_iterations reached → stopped")

    return iteration, max_iterations


def _check_context_pressure(
    pre_compact_flag: Path, state: dict, state_file: Path, project_root: Path, log_file: Path
) -> None:
    """STEP 4: コンテキスト残量チェック（PreCompact 発火検出）。"""
    if not pre_compact_flag.exists():
        return

    try:
        flag_content = pre_compact_flag.read_text(encoding="utf-8").strip()
        flag_dt = datetime.datetime.fromisoformat(flag_content.replace("Z", "+00:00"))
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        elapsed = (now_dt - flag_dt).total_seconds()
        if elapsed <= PRE_COMPACT_THRESHOLD_SECONDS:
            _save_loop_log(project_root, state, log_file, "context_exhaustion")
            _cleanup_state_file(state_file)
            _stop(log_file, f"PreCompact fired {elapsed:.0f}s ago → context pressure, stop loop")
    except Exception:
        try:
            flag_mtime = os.path.getmtime(str(pre_compact_flag))
            elapsed = time.time() - flag_mtime
            if elapsed <= PRE_COMPACT_THRESHOLD_SECONDS:
                _save_loop_log(project_root, state, log_file, "context_exhaustion")
                _cleanup_state_file(state_file)
                _stop(log_file, f"PreCompact fired {elapsed:.0f}s ago (mtime) → context pressure, stop loop")
        except Exception:
            pass


def _check_escalation(
    state: dict, test_count: int, state_file: Path, project_root: Path, log_file: Path
) -> None:
    """STEP 6: エスカレーション条件チェック。"""
    log_entries = state.get("log", [])
    prev_test_count = 0
    if log_entries:
        prev_test_count = int(log_entries[-1].get("test_count", 0))

    if prev_test_count > 0 and test_count > 0 and test_count < prev_test_count:
        _log(log_file, "WARN", f"ESC: test count decreased ({prev_test_count} → {test_count}) → escalate to human")
        _save_loop_log(project_root, state, log_file, "escalation")
        _cleanup_state_file(state_file)
        _stop(log_file, f"ESC: test count decreased ({prev_test_count} → {test_count}) → escalate to human")

    if _check_issue_recurrence(state):
        _save_loop_log(project_root, state, log_file, "escalation")
        _cleanup_state_file(state_file)
        _stop(log_file, "ESC: same issues recurring (no fix for 2 cycles) → escalate to human")


def _check_unanalyzed_tdd_patterns(project_root: Path, log_file: Path) -> None:
    """通知B: tdd-patterns.log の未分析パターンをチェックしてログに記録する。"""
    tdd_log = project_root / ".claude" / "tdd-patterns.log"
    if not tdd_log.exists():
        return
    try:
        lines = tdd_log.read_text(encoding="utf-8").splitlines()
        # ANALYZED マーカー以降の FAIL→PASS 遷移を数える
        last_analyzed_idx = -1
        for i, line in enumerate(lines):
            if "\tANALYZED\t" in line:
                last_analyzed_idx = i
        unanalyzed = [
            line for line in lines[last_analyzed_idx + 1:]
            if "\tPASS\t" in line
        ]
        if unanalyzed:
            _log(
                log_file, "INFO",
                f"TDD patterns: {len(unanalyzed)}件の未分析 FAIL→PASS パターンあり。/retro を推奨。",
            )
    except Exception:
        pass


def _evaluate_green_state(
    state: dict,
    test_result: int,
    lint_result: int,
    security_result: int,
    state_file: Path,
    project_root: Path,
    log_file: Path,
) -> tuple[bool, bool, list[str]]:
    """STEP 5: Green State 条件の総合判定。

    Green State のうち G1（テスト）, G2（lint）, G5（セキュリティ）を自動判定する。
    G3（Issue ゼロ）, G4（仕様差分ゼロ）は /full-review (Claude) 側の責務。

    Returns:
        (green_state, fullscan_pending, fail_parts)
    """
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
        else:
            _log(log_file, "INFO", "Green State achieved → stop loop (normal convergence)")
            _check_unanalyzed_tdd_patterns(project_root, log_file)
            _save_loop_log(project_root, state, log_file)
            _cleanup_state_file(state_file)
            _stop(log_file, "Green State achieved → loop converged")

    return green_state, fullscan_pending, fail_parts


def _continue_loop(
    state: dict,
    iteration: int,
    test_count: int,
    green_state: bool,
    fullscan_pending: bool,
    fail_parts: list[str],
    state_file: Path,
    log_file: Path,
) -> None:
    """STEP 7: 状態更新と継続（block）。"""
    new_iteration = iteration + 1
    state["iteration"] = new_iteration

    # log エントリは /full-review (Phase 2) が各イテレーション開始時に書き込む前提。
    # log が空の場合は test_count の更新をスキップする（_check_escalation も安全に動作する）。
    log_entries = state.get("log", [])
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


def main() -> None:
    project_root = get_project_root()
    state_file = project_root / ".claude" / "lam-loop-state.json"
    pre_compact_flag = project_root / ".claude" / "pre-compact-fired"
    log_file = _get_log_file(project_root)

    input_data = read_stdin_json()

    # STEP 1-2: 再帰防止・状態ファイル確認
    state = _check_recursion_and_state(input_data, state_file, log_file)

    # STEP 3: 反復上限チェック
    iteration, max_iterations = _check_max_iterations(state, state_file, project_root, log_file)
    command = state.get("command", "")
    _log(log_file, "INFO", f"loop active: command={command}, iteration={iteration}/{max_iterations}")

    # STEP 4: コンテキスト残量チェック
    _check_context_pressure(pre_compact_flag, state, state_file, project_root, log_file)

    # STEP 5: Green State 判定（テスト + lint + セキュリティ）
    cwd = input_data.get("cwd", "")
    check_dir = _validate_check_dir(cwd, project_root)
    test_result, test_count = _run_tests(check_dir, log_file)
    lint_result = _run_lint(check_dir, log_file)
    security_result = _run_security(check_dir, log_file)

    # STEP 6: エスカレーション条件チェック
    _check_escalation(state, test_count, state_file, project_root, log_file)

    # STEP 5 (cont.): Green State 総合判定
    green_state, fullscan_pending, fail_parts = _evaluate_green_state(
        state, test_result, lint_result, security_result,
        state_file, project_root, log_file,
    )

    # STEP 7: 継続（block）
    _continue_loop(
        state, iteration, test_count,
        green_state, fullscan_pending, fail_parts,
        state_file, log_file,
    )


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        # 障害時は exit 0（hook 障害で Claude をブロックしない）
        sys.exit(0)
