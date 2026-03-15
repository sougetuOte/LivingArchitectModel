#!/usr/bin/env python3
"""
lam-stop-hook.py - LAM Stop hook: 自律ループの安全ネット

stdin から JSON を受け取り、アクティブなループ中に Claude が
応答を終了しようとした場合に 1 回 block して引き戻す。

判定ロジック:
  1. 再帰防止チェック（最優先）
  2. 状態ファイル確認
  3. 反復上限チェック
  4. コンテキスト残量チェック（PreCompact 発火検出）
  5. 安全ネット継続（block）

ループの主制御（Green State 判定、イテレーション管理）は
/full-review（Claude 側）が行う。Stop hook はあくまで安全ネット。

出力:
  正常停止時: exit 0（何も出力しない）
  継続時: stdout に {"decision": "block", "reason": "..."} を出力して exit 0
  障害時: exit 0（hook 障害で Claude をブロックしない）

対応仕様: docs/design/hooks-python-migration-design.md H3（lam-stop-hook）
"""

from __future__ import annotations

import datetime
import json
import os
import sys
import time
from pathlib import Path

# sys.path に hooks ディレクトリを追加（_hook_utils を import するため）
_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from _hook_utils import (  # noqa: E402
    get_project_root,
    log_entry,
    now_utc_iso8601,
    read_stdin_json,
)

# PreCompact 発火から何秒以内を「直近」とみなすか（10分）
PRE_COMPACT_THRESHOLD_SECONDS = 600


def _get_log_file(project_root: Path) -> Path:
    return project_root / ".claude" / "logs" / "loop.log"


def _log(log_file: Path, level: str, message: str) -> None:
    try:
        log_entry(log_file, level, "stop-hook", message)
    except Exception as e:
        sys.stderr.write(f"stop-hook log error: {e}\n")


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
        _log(log_file, "ERROR", f"state file read/parse error: {type(e).__name__}")
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
        _log(
            log_file,
            "WARN",
            f"max_iterations reached ({iteration}/{max_iterations}) → stop loop",
        )
        _save_loop_log(project_root, state, log_file, "max_iterations")
        _cleanup_state_file(state_file)
        _stop(log_file, "max_iterations reached → stopped")

    return iteration, max_iterations


def _check_context_pressure(
    pre_compact_flag: Path,
    state: dict,
    state_file: Path,
    project_root: Path,
    log_file: Path,
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
            _stop(
                log_file,
                f"PreCompact fired {elapsed:.0f}s ago → context pressure, stop loop",
            )
    except Exception:
        try:
            flag_mtime = os.path.getmtime(str(pre_compact_flag))
            elapsed = time.time() - flag_mtime
            if elapsed <= PRE_COMPACT_THRESHOLD_SECONDS:
                _save_loop_log(project_root, state, log_file, "context_exhaustion")
                _cleanup_state_file(state_file)
                _stop(
                    log_file,
                    f"PreCompact fired {elapsed:.0f}s ago (mtime) → context pressure, stop loop",
                )
        except Exception:
            pass


def main() -> None:
    project_root = get_project_root()
    state_file = project_root / ".claude" / "lam-loop-state.json"
    pre_compact_flag = project_root / ".claude" / "pre-compact-fired"
    log_file = _get_log_file(project_root)

    input_data = read_stdin_json()

    # STEP 1-2: 再帰防止・状態ファイル確認
    state = _check_recursion_and_state(input_data, state_file, log_file)

    # STEP 3: 反復上限チェック
    iteration, max_iterations = _check_max_iterations(
        state, state_file, project_root, log_file
    )
    command = state.get("command", "")
    _log(
        log_file,
        "INFO",
        f"loop active: command={command}, iteration={iteration}/{max_iterations}",
    )

    # STEP 4: コンテキスト残量チェック
    _check_context_pressure(pre_compact_flag, state, state_file, project_root, log_file)

    # STEP 5: 安全ネットとして block
    #
    # ループ制御は /full-review（Claude 側）が行う。
    # Stop hook は「Claude が途中で止まろうとした場合に引き戻す」安全ネット。
    # stop_hook_active=true の再帰防止により、同一ターン内での再帰は防止される。

    _log(
        log_file,
        "INFO",
        f"safety net: blocking to continue loop (iteration {iteration})",
    )
    _block(
        log_file,
        f"ループ継続中（イテレーション {iteration}）。Phase 2 に戻って再監査してください。",
    )


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        # 障害時は exit 0（hook 障害で Claude をブロックしない）
        sys.exit(0)
