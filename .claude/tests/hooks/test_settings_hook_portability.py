"""R1-033: settings.json hook 起動コマンドの portability + shim 回避 TDD.

`.claude/settings.json` の全 5 hook 起動コマンド（PreToolUse / PostToolUse /
PostToolUseFailure / Stop / PreCompact）は元々 `python3 "$CLAUDE_PROJECT_DIR"/...`
で固定されていた（R1-033 起票時点）。CLAUDE.md は「Windows 11 Pro + Git Bash」を
明記するが、素の Windows Python installer は `python3` エイリアスを提供しない
（旧環境は pyenv-win 経由で解決していたため気づきにくかった）。将来環境変更や
新規 contributor 環境で hook 起動自体が silent failure し、permission システム
全体が機能しなくなるリスクがある（hook 起動失敗は Claude Code 側で気づきにくい）。

R1-033 は当初「command 内に `command -v python3` fallback を強制」で portability を
守っていたが、2027 年頃の VBScript 廃止（pyenv-win shim = VBScript 依存）対策として
`.venv` 直接パス経由の shim 回避へ移行する必要が生じた。

HGA #14 (Fable adversarial review 2026-07-12) F14 の方向修正に従い、本テストは
「.venv 優先」と「fallback chain 保証」の **AND 強化** で新体制を守る:

- (venv-first) 全 hook command が `.venv` interpreter を優先する呼び出しを持つこと。
  実装は `.claude/scripts/py_invoke.sh` helper 経由（推奨: 内部で .venv 優先 +
  fallback + 実起動可能性判定）または `.venv/Scripts/python.exe` /
  `.venv/bin/python` 直接パスのいずれか。
- (fallback) 全 hook command が fallback chain を持つこと。py_invoke.sh 経由なら
  helper 内部の `_resolve_python()` が fallback を保証、直接呼びなら command 文字列
  内に `command -v python3` fallback を含むこと。

親 issue: `docs/artifacts/r-1-audit-tracker.md` R1-033
関連: HGA #14 (Fable adversarial review / F11 silent failure 対策 / F14 AND 強化)
根拠 evidence: `.claude/settings.json` L74, 80, 86, 91, 96
helper 実体: `.claude/scripts/py_invoke.sh`
"""
from __future__ import annotations

import json
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_SETTINGS_PATH = _PROJECT_ROOT / ".claude" / "settings.json"


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


def test_hook_commands_use_venv_first():
    """全 hook command が .venv 経由 interpreter を優先する呼び出しを持つ。

    HGA #14 F14 の AND 強化 (venv-first 側):
    - py_invoke.sh 経由なら helper 内部で .venv 優先解決 (実装は helper に閉じる)
    - 直接呼びなら `.venv/Scripts/python.exe` または `.venv/bin/python` を含むこと

    素の `python3 "$CLAUDE_PROJECT_DIR"/...` 直起動は pyenv-win shim 経由で
    VBScript を発火させるため禁止 (2027 VBScript 廃止対策)。
    """
    settings = json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
    commands = _iter_hook_commands(settings)
    for command in commands:
        has_helper = "py_invoke.sh" in command
        has_venv_direct = (
            ".venv/Scripts/python.exe" in command
            or ".venv/bin/python" in command
        )
        assert has_helper or has_venv_direct, (
            "hook command lacks .venv-first invocation "
            "(neither py_invoke.sh helper nor direct .venv path): "
            f"{command!r}"
        )


def test_hook_commands_have_fallback_chain():
    """全 hook command が fallback chain を保証する経路を持つ。

    HGA #14 F14 の AND 強化 (fallback 側):
    - py_invoke.sh 経由なら helper 内部の _resolve_python() が
      `.venv` 起動不能時に `python3 -> python` fallback へ落ちる (F11 対策)。
    - 直接 `.venv` パス呼びなら command 文字列内に `command -v python3` fallback
      を含むこと (R1-033 元趣旨 = bare Windows env 対策)。

    存在チェックのみで .venv に落として fallback を失うと、
    「存在するが起動不能な .venv」で全 5 hook が silent failure し
    permission システムが丸ごと落ちる (R1-033 が元々守ろうとしたリスク)。
    """
    settings = json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
    commands = _iter_hook_commands(settings)
    for command in commands:
        has_helper = "py_invoke.sh" in command
        has_direct_fallback = "command -v python3" in command
        assert has_helper or has_direct_fallback, (
            "hook command lacks fallback chain "
            "(neither py_invoke.sh helper nor direct `command -v python3`): "
            f"{command!r}"
        )


def test_hook_commands_still_reference_correct_script_path():
    """venv-first 化後も各 hook が正しいスクリプトパスを参照し続けている（regression guard）。"""
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
