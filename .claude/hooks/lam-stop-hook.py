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
import subprocess
import sys
import time
from pathlib import Path

# sys.path に hooks ディレクトリを追加（_hook_utils を import するため）
_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from _hook_utils import (  # noqa: E402
    build_allowlisted_env,
    get_project_root,
    log_entry,
    now_utc_iso8601,
    read_stdin_json,
)

import autonomous_state  # noqa: E402

# PreCompact 発火から何秒以内を「直近」とみなすか（10分）
PRE_COMPACT_THRESHOLD_SECONDS = 600

# AUTONOMOUS: checker サブプロセスの timeout（hooks 全体 600s 上限内）
CHECKER_TIMEOUT = 600


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
    except Exception as e:
        # ループログ保存失敗は致命的ではないが、黙殺せず警告として残す（監査 W-2）。
        _log(log_file, "WARNING", f"Failed to save loop log: {type(e).__name__}: {e}")
    # 通知B（W-9）: ループ終了時に未分析の TDD パターンがあれば /retro を推奨。
    # ループログ保存の成否に依存させないため try の外で呼ぶ。
    _notify_unanalyzed_patterns(project_root, log_file)


def _count_unanalyzed_tdd_patterns(tdd_log: Path) -> int:
    """tdd-patterns.log の最終 ANALYZED マーカー以降のエントリ行数を返す（通知B・W-9）。

    エントリ行は PASS/FAIL 記録、マーカー行は field[1] == "ANALYZED"。
    ファイル不在・読取失敗時はフェイルセーフに 0 を返す（提案機能のため）。
    """
    try:
        if not tdd_log.is_file():
            return 0
        lines = [
            ln for ln in tdd_log.read_text(encoding="utf-8").splitlines() if ln.strip()
        ]
    except OSError:
        return 0
    last_marker = -1
    for i, line in enumerate(lines):
        fields = line.split("\t")
        if len(fields) >= 2 and fields[1] == "ANALYZED":
            last_marker = i
    return len(lines) - (last_marker + 1)


def _notify_unanalyzed_patterns(project_root: Path, log_file: Path) -> None:
    """未分析の TDD パターンが1件以上あれば loop.log に /retro 推奨を INFO 記録する（通知B・W-9）。

    仕様 docs/specs/tdd-introspection-v2.md §5.1。ログ出力のみでループ動作には影響しない。
    """
    tdd_log = project_root / ".claude" / "tdd-patterns.log"
    count = _count_unanalyzed_tdd_patterns(tdd_log)
    if count >= 1:
        _log(
            log_file,
            "INFO",
            f"TDD patterns: {count}件の未分析パターンあり。/retro を推奨。",
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


def _load_active_autonomous_state(
    auto_state_file: Path, log_file: Path
) -> dict | None:
    """autonomous-state.json をロードし active=true の state dict を返す（fail-close）。

    非存在 / 読取・パース失敗 / active≠true はいずれも None を返す。main() はこの
    単一読込結果だけで autonomous フローへ分岐するため、旧 _is_autonomous_active +
    _handle_autonomous 内再読込による「二度読み」fail-open 経路（design D3）を持たない。
    読取失敗は観測性のため WARN ログに残す（黙殺せず None=fail-close へ落とす）。
    """
    if not auto_state_file.exists():
        return None
    try:
        state = json.loads(auto_state_file.read_text(encoding="utf-8"))
    except Exception as e:
        _log(
            log_file,
            "WARN",
            f"autonomous state read/parse error: {type(e).__name__} → fail-close (None)",
        )
        return None
    if state.get("active") is not True:
        return None
    return state


def _write_autonomous_state(auto_state_file: Path, state: dict) -> None:
    """autonomous-state.json を更新する（hook が書くためモデル改竄不能）。"""
    try:
        auto_state_file.write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception as e:
        sys.stderr.write(f"autonomous-state write error: {e}\n")


def _run_g1_checker(project_root: Path, log_file: Path) -> int:
    """G1 checker をサブプロセス厳密実行し実 exit code を返す。

    0=PASS / 非0=FAIL。障害（未検出・timeout・例外）は FAIL(2) 扱いとし、
    誤って completion させない（決定的 gate を維持）。
    """
    checker_path = _HOOKS_DIR / "checkers" / "check_g1_test.py"
    if not checker_path.is_file():
        _log(log_file, "ERROR", f"G1 checker not found: {checker_path}")
        return 2
    try:
        proc = subprocess.run(
            [sys.executable, str(checker_path)],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=CHECKER_TIMEOUT,
            env=build_allowlisted_env({"LAM_PROJECT_ROOT": str(project_root)}),
        )
    except subprocess.TimeoutExpired:
        _log(log_file, "ERROR", f"G1 checker timeout after {CHECKER_TIMEOUT}s")
        return 2
    except Exception as e:
        _log(log_file, "ERROR", f"G1 checker error: {type(e).__name__}")
        return 2
    if proc.stderr:
        _log(log_file, "INFO", f"G1 checker stderr: {proc.stderr.strip()[:500]}")
    return proc.returncode


def _handle_autonomous(
    input_data: dict,
    state: dict,
    auto_state_file: Path,
    project_root: Path,
    log_file: Path,
) -> None:
    """AUTONOMOUS フロー（design D3）: checker(G1) 厳密実行で completion を gate する。

    state は main() の _load_active_autonomous_state が読込済みの active=true 状態を
    引数で受け取る（二度読み廃止）。停止条件に該当した場合は _stop()/_block() で
    SystemExit を送出する。
    """
    stop_hook_active = input_data.get("stop_hook_active")
    _log(log_file, "INFO", f"autonomous flow: stop_hook_active={stop_hook_active}")

    iteration = int(state.get("iteration", 0))
    max_iterations = int(state.get("max_iterations", 20))

    # 反復上限（主 bound・無限ループ防止）
    if iteration >= max_iterations:
        state["active"] = False
        _write_autonomous_state(auto_state_file, state)
        _stop(
            log_file,
            f"autonomous: max_iterations reached ({iteration}/{max_iterations}) → stop",
        )

    # G1 checker 実行 → 結果に応じて completion(stop)/継続(block) を gate
    _apply_g1_result(
        state, auto_state_file, project_root, iteration, max_iterations, log_file
    )


def _apply_g1_result(
    state: dict,
    auto_state_file: Path,
    project_root: Path,
    iteration: int,
    max_iterations: int,
    log_file: Path,
) -> None:
    """G1 checker を厳密実行し、実 exit code に応じて completion/継続を gate する。

    exit code は checker_results に記録（モデル改竄不能）。PASS(0) なら active=false で
    _stop()、FAIL なら iteration++ で building へ _block()。いずれも SystemExit を送出する。
    """
    g1_exit = _run_g1_checker(project_root, log_file)
    results = state.setdefault("checker_results", {})
    results["g1_exit"] = g1_exit
    results["checked_at"] = now_utc_iso8601()

    if g1_exit == 0:
        # 全 PASS → completion 許可
        state["active"] = False
        state["phase"] = "done"
        _write_autonomous_state(auto_state_file, state)
        _stop(log_file, "autonomous: G1 PASS → completion (active=false)")
    else:
        # FAIL → block でループ継続（building へ戻す）
        state["iteration"] = iteration + 1
        state["phase"] = "building"
        _write_autonomous_state(auto_state_file, state)
        _block(
            log_file,
            f"autonomous: G1 test checker が赤 (exit {g1_exit})。"
            f"building へ戻りテストを修正してください"
            f"（iteration {iteration + 1}/{max_iterations}）。",
        )


def main() -> None:
    project_root = get_project_root()
    state_file = project_root / ".claude" / "lam-loop-state.json"
    pre_compact_flag = project_root / ".claude" / "pre-compact-fired"
    log_file = _get_log_file(project_root)

    input_data = read_stdin_json()

    # AUTONOMOUS フロー（design D3・最優先）: autonomous-state.json の active を検出したら
    # checker(G1) を厳密実行して completion を gate する。既存 full-review フローとは
    # 独立ファイルで分離し、非active時は以降の lam-loop-state.json フローが不変。
    auto_state_file = autonomous_state.state_file_path(project_root)
    auto_state = _load_active_autonomous_state(auto_state_file, log_file)
    if auto_state is not None:
        _handle_autonomous(
            input_data, auto_state, auto_state_file, project_root, log_file
        )
        return

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
