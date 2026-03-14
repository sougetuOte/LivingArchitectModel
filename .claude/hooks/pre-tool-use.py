#!/usr/bin/env python3
"""
pre-tool-use.py - LAM PreToolUse hook: 権限等級判定（PG/SE/PM）

bash 版 pre-tool-use.sh の Python 移植版。
stdin から JSON を受け取り、ツール名とファイルパスに基づいて
PG/SE/PM の等級を判定する。

判定結果:
  PG級 → exit 0（許可）
  SE級 → exit 0 + ログ記録
  PM級 → stdout に hookSpecificOutput JSON（permissionDecision: "ask"）を出力して exit 0
        Claude Code のネイティブ許可ダイアログでユーザーに判断を委ねる

対応仕様: docs/design/hooks-python-migration-design.md H1（pre-tool-use）
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# sys.path に hooks ディレクトリを追加（_hook_utils を import するため）
_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from _hook_utils import (  # noqa: E402
    get_project_root,
    get_tool_input,
    get_tool_name,
    log_entry,
    normalize_path,
    read_stdin_json,
)

# 読み取り専用ツール: 常に PG 許可
_READ_ONLY_TOOLS = frozenset({"Read", "Glob", "Grep", "WebSearch", "WebFetch"})

# AUDITING フェーズの PG 許可コマンドのプレフィックス
# 注: settings.json の allow リストにも同コマンドが登録されている。
# Claude Code は allow マッチ時に hook をスキップする場合があるため、
# このブラックリストチェックは「二重防御」として機能する。
# allow 側の粗いワイルドカード（例: "Bash(ruff check --fix *)"）を
# hook 側で精密にフィルタする設計。実害が確認された場合は
# allow からの削除を検討し、hook に一元化すること。
_AUDITING_PG_COMMANDS = (
    "npx prettier",
    "npx eslint --fix",
    "ruff check --fix",
    "ruff format",
)

# PG コマンドで禁止する引数（悪意ある設定ファイル読み込み等を防止）
_PG_BLACKLISTED_ARGS = (
    "--config",
    "--settings",
    "--ruleset",
    "--rule-dir",
    "--rulesdir",
    "--plugin",
    "--resolve-plugins-relative-to",
    "--stdin-filename",
    "--ignore-path",
    "--ext",
)

# パス判定パターン（PM 級）
_PM_PATTERNS = [
    (re.compile(r"^__out_of_root__/"), "out-of-root path"),
    (re.compile(r"^docs/specs/.*\.md$"), "specs/ path"),
    (re.compile(r"^docs/adr/.*\.md$"), "adr/ path"),
    (re.compile(r"^\.claude/rules/.*\.md$"), "rules/ path"),
    (re.compile(r"^\.claude/settings.*\.json$"), "settings path"),
]

# パス判定パターン（SE 級）
_SE_PATTERNS = [
    (re.compile(r"^docs/"), "docs/ path (non-specs/adr)"),
    (re.compile(r"^src/"), "src/ path"),
]


def _determine_level_and_reason(
    tool_name: str,
    file_path: str,
    command: str,
    project_root: Path,
    phase_file: Path,
) -> tuple[str, str]:
    """ツール名とパスから権限等級とその理由を判定する。

    Returns:
        (level, reason): level は "PG" | "SE" | "PM"
    """
    # 1. ファイルパスが存在する場合はパスベース判定
    if file_path:
        normalized = normalize_path(file_path, project_root)

        # PM パターン照合
        for pattern, reason in _PM_PATTERNS:
            if pattern.match(normalized):
                return "PM", reason

        # SE パターン照合
        for pattern, reason in _SE_PATTERNS:
            if pattern.match(normalized):
                return "SE", reason

        return "SE", "default path"

    # 2. コマンドベース判定（Bash ツール等）
    if command:
        # AUDITING フェーズの PG コマンド特別処理
        current_phase = _read_current_phase(phase_file)
        if current_phase == "AUDITING":
            for pg_prefix in _AUDITING_PG_COMMANDS:
                if command == pg_prefix or command.startswith(pg_prefix + " "):
                    # ブラックリスト引数チェック（単語境界で照合し誤マッチを防止）
                    args_part = command[len(pg_prefix):]
                    if any(
                        re.search(r'(?:^|\s)' + re.escape(bl) + r'(?:\s|=|$)', args_part, re.IGNORECASE)
                        for bl in _PG_BLACKLISTED_ARGS
                    ):
                        return "PM", "PG command with blacklisted arg"
                    return "PG", "AUDITING phase PG allow"

        return "SE", "command (default SE)"

    # 3. パスもコマンドもない（Agent 等）
    return "SE", "no-path (default SE)"


def _read_current_phase(phase_file: Path) -> str:
    """current-phase.md から現在のフェーズ名を読み取る。

    **PHASE** 形式から PHASE を抽出する。
    ファイルが存在しない/読み込み失敗時は空文字を返す。
    """
    if not phase_file.exists():
        return ""
    try:
        content = phase_file.read_text(encoding="utf-8")
        for line in content.splitlines():
            match = re.match(r"^\*\*([A-Z]+)\*\*", line)
            if match:
                return match.group(1)
    except Exception:
        pass
    return ""


def main() -> None:
    project_root = get_project_root()
    log_file = project_root / ".claude" / "logs" / "permission.log"
    phase_file = project_root / ".claude" / "current-phase.md"

    # stdin から JSON 読み込み
    data = read_stdin_json()

    # ツール名を取得（取得失敗時は SE 扱いで終了）
    tool_name = get_tool_name(data)
    if not tool_name:
        log_entry(log_file, "SE", "unknown", "tool_name extraction failed")
        sys.exit(0)

    # 1. 読み取り専用ツールは常に PG 許可
    if tool_name in _READ_ONLY_TOOLS:
        log_entry(log_file, "PG", tool_name, "- read-only tool")
        sys.exit(0)

    # ファイルパスとコマンドを取得
    file_path = get_tool_input(data, "file_path")
    command = get_tool_input(data, "command")

    # 権限等級判定
    level, reason = _determine_level_and_reason(
        tool_name, file_path, command, project_root, phase_file
    )

    # ログ用のターゲット文字列（100 文字にトランケート、タブ/改行をエスケープ）
    raw_target = file_path or command or "-"
    target = raw_target[:100].replace("\t", " ").replace("\n", " ")

    # ログ記録（TSV 形式: timestamp\tlevel\ttool_name\ttarget\t"reason"）
    log_entry(log_file, level, tool_name, f"{target}\t\"{reason}\"")

    # 応答
    if level == "PM":
        ask_output = {
            "hookSpecificOutput": {
                "permissionDecision": "ask",
                "permissionDecisionReason": f"PM級変更です。承認してください: {target}",
            }
        }
        print(json.dumps(ask_output, ensure_ascii=False))

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # フック障害時にも Claude をブロックしない
        sys.exit(0)
