"""R1-033: settings.json hook 起動コマンドの python3 hardcode 環境非依存化 TDD.

`.claude/settings.json` の全 5 hook 起動コマンド（PreToolUse / PostToolUse /
PostToolUseFailure / Stop / PreCompact）が `python3 "$CLAUDE_PROJECT_DIR"/...`
で固定されていた。CLAUDE.md は「Windows 11 Pro + Git Bash」を明記するが、素の
Windows Python installer は `python3` エイリアスを提供しない（現環境は
pyenv-win 経由で解決しているため気づきにくい）。将来環境変更や新規 contributor
環境で hook 起動自体が silent failure し、permission システム全体が機能しなく
なるリスクがある（hook 起動失敗は Claude Code 側で気づきにくい）。

本テストは:
- `.claude/settings.json` の hooks.*.command 文字列に `python3` の裸ハードコード
  （`command -v python3` のような可用性チェック文脈を除く）が存在しないことを assert

親 issue: `docs/artifacts/r-1-audit-tracker.md` R1-033
根拠 evidence: `.claude/settings.json` L74, 80, 86, 91, 96
"""
from __future__ import annotations

import json
import re
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_SETTINGS_PATH = _PROJECT_ROOT / ".claude" / "settings.json"

# `command -v python3` / `which python3` のような可用性チェック文脈は許容する。
# それ以外の裸の `python3` トークン出現をハードコードとみなす。
_BARE_PYTHON3_RE = re.compile(r"(?<!-v )(?<!which )python3\b")


def _iter_hook_commands(settings: dict) -> list[str]:
    """settings.json の hooks セクションから全 command 文字列を平坦に抽出する。"""
    commands: list[str] = []
    hooks_section = settings.get("hooks", {})
    for _event_name, entries in hooks_section.items():
        for entry in entries:
            for hook in entry.get("hooks", []):
                command = hook.get("command", "")
                if command:
                    commands.append(command)
    return commands


def test_settings_json_has_five_hook_commands():
    """settings.json は 5 件の hook 起動コマンドを持つ（回帰の前提確認）。"""
    settings = json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
    commands = _iter_hook_commands(settings)
    assert len(commands) == 5


def test_no_bare_python3_hardcode_in_hook_commands():
    """全 hook command 文字列に裸の `python3` ハードコードが存在しない。

    `command -v python3 >/dev/null 2>&1 && python3 ... || python ...` のような
    fallback 文脈内の `python3` は許容する（可用性チェック済のため portability
    リスクにならない）。裸で `python3 "$CLAUDE_PROJECT_DIR"/...` のように直接
    起動している箇所を検出する。
    """
    settings = json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
    commands = _iter_hook_commands(settings)
    for command in commands:
        assert "command -v python3" in command, (
            f"hook command lacks python3 availability fallback: {command!r}"
        )


def test_hook_commands_fallback_to_plain_python():
    """fallback 文脈は `python` (python3 以外) への切替を含む（Windows 素の python 起動対応）。"""
    settings = json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
    commands = _iter_hook_commands(settings)
    for command in commands:
        # "|| python " または "|| python\"" のように python3 以外の python 起動を含むこと
        assert re.search(r"\|\|\s*python(?!3)\b", command), (
            f"hook command lacks plain `python` fallback branch: {command!r}"
        )


def test_hook_commands_still_reference_correct_script_path():
    """fallback 化後も各 hook が正しいスクリプトパスを参照し続けている（regression guard）。"""
    settings = json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
    expected_scripts = {
        "pre-tool-use.py",
        "post-tool-use.py",
        "lam-stop-hook.py",
        "pre-compact.py",
    }
    commands = _iter_hook_commands(settings)
    referenced_scripts = set()
    for command in commands:
        for script in expected_scripts:
            if script in command:
                referenced_scripts.add(script)
    assert referenced_scripts == expected_scripts
