"""Detect Claude Code permission mode for ADR-0008 Phase A AutoMode advisory.

This helper inspects user settings, managed settings, CC version, and the
CLAUDE_CODE_ENABLE_AUTO_MODE env var to determine the active permission
defaultMode. Output is a single-line JSON document on stdout, consumed by
the /quick-load and init-harness skills.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


VALID_MODES = {"default", "acceptEdits", "bypassPermissions", "plan", "dontAsk", "auto"}


def _read_settings_default_mode(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"WARNING: cannot read {path}: {exc}", file=sys.stderr)
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"WARNING: invalid JSON in {path}: {exc}", file=sys.stderr)
        return None
    if not isinstance(data, dict):
        return None
    permissions = data.get("permissions")
    if not isinstance(permissions, dict):
        return None
    mode = permissions.get("defaultMode")
    if mode is None:
        return None
    if mode not in VALID_MODES:
        print(f"WARNING: unrecognised defaultMode '{mode}' in {path}", file=sys.stderr)
        return None
    return mode


def detect_user_settings_mode() -> dict | None:
    home = Path.home()
    candidate = home / ".claude" / "settings.json"
    mode = _read_settings_default_mode(candidate)
    if mode is None:
        return None
    return {"mode": mode, "source": "user_settings", "path": str(candidate)}


def detect_managed_settings_mode() -> dict | None:
    candidates: list[Path] = []
    if os.name == "nt":
        program_data = os.environ.get("PROGRAMDATA")
        if program_data:
            candidates.append(Path(program_data) / "ClaudeCode" / "managed-settings.json")
    else:
        candidates.append(Path("/etc/claude-code/managed-settings.json"))
        candidates.append(Path("/Library/Application Support/ClaudeCode/managed-settings.json"))
    for candidate in candidates:
        try:
            exists = candidate.is_file()
        except OSError as exc:
            print(f"WARNING: cannot stat {candidate}: {exc}", file=sys.stderr)
            continue
        if not exists:
            continue
        mode = _read_settings_default_mode(candidate)
        if mode is None:
            continue
        return {"mode": mode, "source": "managed_settings", "path": str(candidate)}
    return None


def detect_available() -> dict:
    version = "unknown"
    try:
        completed = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if completed.returncode == 0:
            output = (completed.stdout or completed.stderr or "").strip()
            if output:
                version = output.splitlines()[0].strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
        print(f"WARNING: claude --version failed: {exc}", file=sys.stderr)
    auto_mode_env = bool(os.environ.get("CLAUDE_CODE_ENABLE_AUTO_MODE"))
    return {"version": version, "auto_mode_env": auto_mode_env}


def detect() -> dict:
    detected = detect_managed_settings_mode() or detect_user_settings_mode()
    available = detect_available()
    if detected is None:
        return {"mode": None, "source": "unknown", "available": available}
    return {
        "mode": detected["mode"],
        "source": detected["source"],
        "path": detected.get("path"),
        "available": available,
    }


if __name__ == "__main__":
    result = detect()
    json.dump(result, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
