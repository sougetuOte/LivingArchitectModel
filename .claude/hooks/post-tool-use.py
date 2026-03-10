#!/usr/bin/env python3
"""
post-tool-use.py - LAM PostToolUse hook: ツール実行後の処理

bash 版 post-tool-use.sh の Python 移植版。
stdin から JSON を受け取り、ツール実行結果に基づいて副作用を生成する。

責務:
  1. TDD パターン検出（テスト結果の記録）
     - pytest/npm test/go test の失敗を tdd-patterns.log に FAIL 記録
     - 前回失敗後の成功を PASS 記録
     - .claude/last-test-result で前回結果を追跡
  2. doc-sync-flag の設定（src/ 配下の Edit/Write 検知）
     - 重複防止: 既に記録済みのパスはスキップ
  3. ループログへの記録（lam-loop-state.json が存在する場合）
     - tool_events 配列に atomic_write_json で追記

エラーが発生しても exit 0 を返す（PostToolUse hook は Claude の動作をブロックしない）

対応仕様: docs/specs/hooks-python-migration/design.md H2（post-tool-use）
"""
from __future__ import annotations

import datetime
import json
import re
import sys
from pathlib import Path

# sys.path に hooks ディレクトリを追加（_hook_utils を import するため）
_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from _hook_utils import (  # noqa: E402
    atomic_write_json,
    get_project_root,
    get_tool_input,
    get_tool_name,
    get_tool_response,
    normalize_path,
    read_stdin_json,
)

# テストコマンドの正規表現パターン（bash 版パリティ）
_TEST_CMD_PATTERN = re.compile(
    r"(^|[\s])(pytest|npm[\s]+test|go[\s]+test)([\s]|$)"
)


def _is_test_command(command: str) -> bool:
    """pytest/npm test/go test を含むコマンドかどうかを判定する。"""
    return bool(_TEST_CMD_PATTERN.search(command))


def _get_test_cmd_label(command: str) -> str:
    """コマンド文字列から短縮形のラベルを返す（pytest/npm test/go test）。"""
    if "npm" in command:
        return "npm test"
    if "go test" in command:
        return "go test"
    return "pytest"


def _extract_exit_code(data: dict) -> str:
    """tool_response から exit_code を文字列で取得する。

    exitCode と exit_code の両方を試みる（bash 版パリティ）。
    取得できない場合は空文字を返す。
    """
    raw = get_tool_response(data, "exitCode", None)
    if raw is None:
        raw = get_tool_response(data, "exit_code", None)
    if raw is None:
        return ""
    return str(raw)


def _now_utc() -> str:
    """UTC タイムスタンプを ISO 8601 形式で返す。"""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _append_to_tdd_log(tdd_log: Path, line: str) -> None:
    """tdd-patterns.log に1行追記する。ディレクトリが存在しない場合は作成する。"""
    tdd_log.parent.mkdir(parents=True, exist_ok=True)
    with open(tdd_log, "a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")


def _record_tdd_fail(tdd_log: Path, test_cmd: str, stdout: str, timestamp: str) -> None:
    """tdd-patterns.log に FAIL エントリを追記する。

    summary は stdout の最初の3行を結合し、120文字にトランケートする。
    """
    lines = stdout.splitlines()
    # タブ・改行をエスケープして TSV 構造を保護
    summary = " ".join(lines[:3])[:120].replace("\t", " ").replace("\n", " ")
    _append_to_tdd_log(tdd_log, f'{timestamp}\tFAIL\t{test_cmd}\t"{summary}"')


def _record_tdd_pass(tdd_log: Path, test_cmd: str, timestamp: str) -> None:
    """tdd-patterns.log に PASS エントリを追記する（失敗→成功パターン）。"""
    _append_to_tdd_log(tdd_log, f'{timestamp}\tPASS\t{test_cmd}\t"{test_cmd} (previously failed)"')


def _handle_test_result(
    command: str,
    exit_code: str,
    stdout: str,
    tdd_log: Path,
    last_result_file: Path,
    timestamp: str,
) -> None:
    """テストコマンドの結果を処理し、TDD パターンを記録する。"""
    if not _is_test_command(command):
        return

    test_cmd = _get_test_cmd_label(command)

    # 前回の結果を読み取る
    prev_result = ""
    if last_result_file.exists():
        try:
            prev_result = last_result_file.read_text(encoding="utf-8").splitlines()[0]
        except Exception:
            pass

    last_result_file.parent.mkdir(parents=True, exist_ok=True)

    # exit_code が空文字 = exit code 未取得（Bash 以外のツール等）→ スキップ
    if exit_code != "0" and exit_code != "":
        # 失敗パターンを記録
        _record_tdd_fail(tdd_log, test_cmd, stdout, timestamp)
        last_result_file.write_text(f"fail {test_cmd}\n", encoding="utf-8")
    elif exit_code == "0":
        # 成功: 前回失敗だった場合は「失敗→成功」パターンを記録
        if prev_result.startswith("fail"):
            _record_tdd_pass(tdd_log, test_cmd, timestamp)
        last_result_file.write_text(f"pass {test_cmd}\n", encoding="utf-8")


def _handle_doc_sync_flag(
    tool_name: str,
    file_path: str,
    project_root: Path,
    doc_sync_flag: Path,
) -> None:
    """Edit/Write + src/ 配下のファイルを doc-sync-flag に追記する。"""
    if tool_name not in ("Edit", "Write"):
        return
    if not file_path:
        return

    normalized = normalize_path(file_path, project_root)

    # src/ 配下かどうかチェック
    if not normalized.startswith("src/"):
        return

    # 重複防止: 既に記録済みのパスはスキップ
    existing_paths: set[str] = set()
    if doc_sync_flag.exists():
        try:
            existing_paths = set(
                line.strip()
                for line in doc_sync_flag.read_text(encoding="utf-8").splitlines()
                if line.strip()
            )
        except Exception:
            pass

    if normalized not in existing_paths:
        doc_sync_flag.parent.mkdir(parents=True, exist_ok=True)
        with open(doc_sync_flag, "a", encoding="utf-8", newline="\n") as f:
            f.write(f"{normalized}\n")


def _handle_loop_log(
    tool_name: str,
    command: str,
    file_path: str,
    exit_code: str,
    loop_state_path: Path,
    timestamp: str,
) -> None:
    """lam-loop-state.json が存在する場合、tool_events に追記する。"""
    if not loop_state_path.exists():
        return

    try:
        loop_json = json.loads(loop_state_path.read_text(encoding="utf-8"))
    except Exception:
        loop_json = {}

    event = {
        "timestamp": timestamp,
        "tool_name": tool_name,
        "command": command,
        "file_path": file_path,
        "exit_code": exit_code,
    }

    if "tool_events" in loop_json:
        loop_json["tool_events"].append(event)
    else:
        loop_json["tool_events"] = [event]

    atomic_write_json(loop_state_path, loop_json)


def main() -> None:
    project_root = get_project_root()
    tdd_log = project_root / ".claude" / "tdd-patterns.log"
    doc_sync_flag = project_root / ".claude" / "doc-sync-flag"
    last_result_file = project_root / ".claude" / "last-test-result"
    loop_state_path = project_root / ".claude" / "lam-loop-state.json"

    # .claude/ ディレクトリを確保
    (project_root / ".claude").mkdir(parents=True, exist_ok=True)

    # stdin から JSON 読み込み
    data = read_stdin_json()

    # フィールドを抽出
    tool_name = get_tool_name(data)
    command = get_tool_input(data, "command")
    file_path = get_tool_input(data, "file_path")
    exit_code = _extract_exit_code(data)

    stdout = get_tool_response(data, "stdout", "")
    if not isinstance(stdout, str):
        stdout = ""

    timestamp = _now_utc()

    # 1. TDD パターン検出
    if tool_name == "Bash":
        _handle_test_result(command, exit_code, stdout, tdd_log, last_result_file, timestamp)

    # 2. doc-sync-flag の設定
    _handle_doc_sync_flag(tool_name, file_path, project_root, doc_sync_flag)

    # 3. ループログ記録
    _handle_loop_log(tool_name, command, file_path, exit_code, loop_state_path, timestamp)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # フック障害時にも Claude をブロックしない
        pass
    sys.exit(0)
