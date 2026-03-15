#!/usr/bin/env python3
"""
post-tool-use.py - LAM PostToolUse hook: ツール実行後の処理

bash 版 post-tool-use.sh の Python 移植版。
stdin から JSON を受け取り、ツール実行結果に基づいて副作用を生成する。

責務:
  1. TDD パターン検出（テスト結果の記録）
     - .claude/test-results.xml（JUnit XML）を読取りテスト成否を判定
     - 失敗を tdd-patterns.log に FAIL 記録
     - 前回失敗後の成功を PASS 記録 + systemMessage で /retro 推奨
     - .claude/last-test-result で前回結果を追跡
  2. doc-sync-flag の設定（src/ 配下の Edit/Write 検知）
     - 重複防止: 既に記録済みのパスはスキップ
  3. ループログへの記録（lam-loop-state.json が存在する場合）
     - tool_events 配列に atomic_write_json で追記

エラーが発生しても exit 0 を返す（PostToolUse hook は Claude の動作をブロックしない）

対応仕様:
  - docs/design/hooks-python-migration-design.md H2（post-tool-use）
  - docs/specs/tdd-introspection-v2.md Section 4（PostToolUse の変更）
"""
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
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
    log_entry,
    normalize_path,
    now_utc_iso8601,
    read_stdin_json,
)

# tool_events の最大保持件数（ループ中の状態ファイル肥大化を防止）
_MAX_TOOL_EVENTS = 500

# テストコマンドの正規表現パターン（bash 版パリティ）
_TEST_CMD_PATTERN = re.compile(
    r"(^|[\s])(pytest|npm[\s]+test|go[\s]+test|make[\s]+test)(?:[\s]|$)"
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
    if "make test" in command:
        return "make test"
    return "pytest"


def _append_to_tdd_log(tdd_log: Path, line: str) -> None:
    """tdd-patterns.log に1行追記する。ディレクトリが存在しない場合は作成する。"""
    tdd_log.parent.mkdir(parents=True, exist_ok=True)
    with open(tdd_log, "a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")


def _parse_junit_xml(xml_path: Path) -> dict | None:
    """JUnit XML 結果ファイルをパースして結果 dict を返す。

    Returns:
        {"tests": int, "failures": int, "failed_names": list[str]} or None（パース失敗時）
    """
    if not xml_path.exists():
        return None
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        # <testsuites> or <testsuite> がルート
        if root.tag == "testsuites":
            suites = root.findall("testsuite")
        else:
            suites = [root]

        total_tests = sum(int(s.get("tests", 0)) for s in suites)
        total_failures = sum(int(s.get("failures", 0)) for s in suites)
        total_errors = sum(int(s.get("errors", 0)) for s in suites)

        failed_names = []
        for suite in suites:
            for tc in suite.findall("testcase"):
                if tc.find("failure") is not None or tc.find("error") is not None:
                    failed_names.append(tc.get("name", "unknown"))

        return {
            "tests": total_tests,
            "failures": total_failures + total_errors,
            "failed_names": failed_names,
        }
    except ET.ParseError:
        return None
    except OSError:
        return None


def _read_prev_result(last_result_file: Path) -> bool:
    """前回のテスト結果を読み取り、失敗だったか返す。"""
    if last_result_file.exists():
        try:
            return last_result_file.read_text(encoding="utf-8").splitlines()[0].startswith("fail")
        except Exception:
            pass
    return False


def _record_fail(
    tdd_log: Path, last_result_file: Path, timestamp: str,
    test_cmd: str, tests: int, failures: int, failed_names: list[str],
) -> None:
    """テスト失敗を記録する。"""
    summary = ", ".join(failed_names[:5])[:120].replace("\t", " ")
    _append_to_tdd_log(
        tdd_log,
        f'{timestamp}\tFAIL\t{test_cmd}\ttests={tests} failures={failures}\t"{summary}"',
    )
    last_result_file.write_text(f"fail {test_cmd}\n", encoding="utf-8")
    return None


def _record_pass(
    tdd_log: Path, last_result_file: Path, timestamp: str,
    test_cmd: str, tests: int, prev_was_fail: bool,
) -> str | None:
    """テスト成功を記録する。FAIL→PASS 遷移時は通知メッセージを返す。"""
    if prev_was_fail:
        _append_to_tdd_log(
            tdd_log,
            f'{timestamp}\tPASS\t{test_cmd}\ttests={tests} failures=0\t"{test_cmd} (previously failed)"',
        )
        last_result_file.write_text(f"pass {test_cmd}\n", encoding="utf-8")
        return (
            "TDD パターンが記録されました（FAIL→PASS 遷移）。"
            "セッション終了時に /retro でパターン分析を推奨します。"
        )
    last_result_file.write_text(f"pass {test_cmd}\n", encoding="utf-8")
    return None


def _handle_test_result(
    command: str,
    tdd_log: Path,
    test_results_xml: Path,
    last_result_file: Path,
    log_file: Path,
    timestamp: str,
    is_failure_event: bool = False,
) -> str | None:
    """テストコマンドの結果を処理し、TDD パターンを記録する。

    Args:
        is_failure_event: PostToolUseFailure イベント時は True。
            古い XML による誤判定を防ぐため、XML 読取をスキップし直接 FAIL 記録する。

    Returns:
        systemMessage 文字列（FAIL→PASS 遷移時）。通知不要なら None。
    """
    if not _is_test_command(command):
        return None

    test_cmd = _get_test_cmd_label(command)
    last_result_file.parent.mkdir(parents=True, exist_ok=True)

    # PostToolUseFailure: ツール実行自体が失敗（非ゼロ exit）→ 直接 FAIL 記録
    # XML は前回実行の古い結果が残っている可能性があるため読み取らない
    if is_failure_event:
        _append_to_tdd_log(
            tdd_log,
            f'{timestamp}\tFAIL\t{test_cmd}\ttests=? failures=?\t"PostToolUseFailure event"',
        )
        last_result_file.write_text(f"fail {test_cmd}\n", encoding="utf-8")
        return None

    # JUnit XML 結果ファイルを読み取る
    result = _parse_junit_xml(test_results_xml)
    if result is None:
        # WARN は操作ログに記録（tdd-patterns.log ではなく post-tool-use.log）
        log_entry(log_file, "WARN", "post-tool-use",
                  f"{test_cmd}: test-results.xml not found or parse error")
        return None

    tests = result["tests"]
    failures = result["failures"]
    failed_names = result["failed_names"]

    prev_was_fail = _read_prev_result(last_result_file)

    if failures > 0:
        return _record_fail(tdd_log, last_result_file, timestamp, test_cmd, tests, failures, failed_names)
    return _record_pass(tdd_log, last_result_file, timestamp, test_cmd, tests, prev_was_fail)


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
        return  # read/parse 失敗時はループ状態を破壊しないよう書き込みを行わない

    event = {
        "timestamp": timestamp,
        "tool_name": tool_name,
        "command": command,
        "file_path": file_path,
        "exit_code": exit_code,
    }

    if "tool_events" in loop_json and isinstance(loop_json["tool_events"], list):
        loop_json["tool_events"].append(event)
    else:
        loop_json["tool_events"] = [event]

    # 上限超過時は古いイベントを切り捨て
    if len(loop_json["tool_events"]) > _MAX_TOOL_EVENTS:
        loop_json["tool_events"] = loop_json["tool_events"][-_MAX_TOOL_EVENTS:]

    atomic_write_json(loop_state_path, loop_json)


def main() -> None:
    project_root = get_project_root()
    tdd_log = project_root / ".claude" / "tdd-patterns.log"
    test_results_xml = project_root / ".claude" / "test-results.xml"
    doc_sync_flag = project_root / ".claude" / "doc-sync-flag"
    last_result_file = project_root / ".claude" / "last-test-result"
    loop_state_path = project_root / ".claude" / "lam-loop-state.json"
    log_file = project_root / ".claude" / "logs" / "post-tool-use.log"

    # .claude/ ディレクトリを確保
    (project_root / ".claude").mkdir(parents=True, exist_ok=True)

    # stdin から JSON 読み込み
    data = read_stdin_json()

    # フィールドを抽出
    tool_name = get_tool_name(data)
    command = get_tool_input(data, "command")
    file_path = get_tool_input(data, "file_path")
    hook_event_name = data.get("hook_event_name", "")

    timestamp = now_utc_iso8601()

    # 1. TDD パターン検出（JUnit XML 方式）
    system_message = None
    if tool_name == "Bash":
        is_failure = hook_event_name == "PostToolUseFailure"
        system_message = _handle_test_result(
            command, tdd_log, test_results_xml, last_result_file, log_file, timestamp,
            is_failure_event=is_failure,
        )

    # 2. doc-sync-flag の設定
    _handle_doc_sync_flag(tool_name, file_path, project_root, doc_sync_flag)

    # 3. ループログ記録
    # exit_code は空文字: PostToolUse/PostToolUseFailure の入力データに exit code が含まれないため
    _handle_loop_log(tool_name, command, file_path, "", loop_state_path, timestamp)

    # 4. 通知A: FAIL→PASS 遷移時に systemMessage を出力
    if system_message:
        print(json.dumps({"systemMessage": system_message}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        # フック障害時にも Claude をブロックしない
        pass
    sys.exit(0)
