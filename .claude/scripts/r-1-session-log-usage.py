#!/usr/bin/env python3
"""R-1 W-R4 S1-T3: Session log 30-day window usage grep (agents / skills / hooks).

Scans ``~/.claude/projects/D--work7-LivingArchitectModel/*.jsonl`` for launch
records of agents, skills, and hooks within a configurable trailing window
(default: 30 days) and reports hit counts / last-hit timestamps per target.

Detection patterns (confirmed by docs/artifacts/r-1-jsonl-fields-2026-07-11.md):

- agent:  message.content[].type == "tool_use" and name == "Agent"
          and input.subagent_type == <slug>
- skill:  TWO paths, combined with OR (missing either underreports hits):
          (1) message.content[].type == "tool_use" and name == "Skill"
              and input.skill == <slug>
          (2) user message text containing
              "<command-name>/<slug></command-name>" (with or without the
              leading slash captured by the tag itself)
- hook:   TWO event shapes must both be scanned (confirmed by probing this
          repo's own jsonl -- not covered by the S1-T1 field memo, which
          only documented the PreToolUse/PostToolUse shape):
          (1) top-level attachment.type == "hook_success" -- covers
              PreToolUse / PostToolUse. attachment.command holds the
              actual invoked script path (attachment.hookName is a
              per-tool label like "PreToolUse:Bash", not a file
              reference, so file-level aggregation must key off
              `command`, not `hookName`).
          (2) top-level type == "system" and subtype == "stop_hook_summary"
              -- covers the Stop hook. The command lives in each entry of
              hookInfos[].command, not in attachment.
          NOTE (caveat, not silently dropped): no PreCompact-equivalent
          summary event was found anywhere in the 76-session corpus for
          this repo, so pre-compact.py's hit_count_window will read 0
          even if it fires -- this is a logging-coverage gap, not
          necessarily evidence of non-use. Flagged explicitly in the
          generated report.

Usage:
    python r-1-session-log-usage.py [--window-days N] [--markdown]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROJECT_JSONL_DIR = os.path.join(
    os.path.expanduser("~"), ".claude", "projects", "D--work7-LivingArchitectModel"
)

COMMAND_NAME_RE = re.compile(r"<command-name>/?([^<]+)</command-name>")
HOOK_SCRIPT_RE = re.compile(r"([\w.\-]+\.py)")

# Hook script basenames that are known helper modules (imported by the
# registered hook entrypoints) rather than commands directly invoked by
# Claude Code's hook system. They will structurally never appear in
# attachment.command / hookInfos[].command, so a 0 hit_count_window here
# is expected and is not itself a "delete candidate" signal.
NON_ENTRYPOINT_HOOK_BASENAMES = {"_hook_utils.py", "_incident_patterns.py", "autonomous_state.py"}


def _slug_from_agent_path(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def _slug_from_skill_path(path: str) -> str:
    # .claude/skills/<slug>/SKILL.md -> <slug>
    return os.path.basename(os.path.dirname(path))


def _slug_from_hook_path(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def discover_targets():
    """Glob agent / skill / hook target paths from the repo (SE-1 basis)."""
    targets = []

    agent_paths = sorted(
        glob.glob(os.path.join(REPO_ROOT, ".claude", "agents", "*.md"))
    )
    for p in agent_paths:
        rel = os.path.relpath(p, REPO_ROOT).replace("\\", "/")
        targets.append(
            {"path": rel, "resource_type": "agent", "slug": _slug_from_agent_path(p)}
        )

    skill_paths = sorted(
        glob.glob(os.path.join(REPO_ROOT, ".claude", "skills", "*", "SKILL.md"))
    )
    for p in skill_paths:
        rel = os.path.relpath(p, REPO_ROOT).replace("\\", "/")
        targets.append(
            {"path": rel, "resource_type": "skill", "slug": _slug_from_skill_path(p)}
        )

    hook_paths = sorted(
        glob.glob(os.path.join(REPO_ROOT, ".claude", "hooks", "*.py"))
    )
    for p in hook_paths:
        rel = os.path.relpath(p, REPO_ROOT).replace("\\", "/")
        targets.append(
            {
                "path": rel,
                "resource_type": "hook",
                "slug": _slug_from_hook_path(p),
                "basename": os.path.basename(p),
            }
        )

    return targets


def _parse_timestamp(ts: str):
    if not ts:
        return None
    try:
        # jsonl timestamps observed as ISO 8601 with trailing "Z" (UTC).
        normalized = ts.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def _iter_jsonl_records(jsonl_dir: str):
    files = sorted(glob.glob(os.path.join(jsonl_dir, "*.jsonl")))
    for path in files:
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    yield path, obj
        except OSError as exc:
            print(f"WARNING: failed to read {path}: {exc}", file=sys.stderr)


def _extract_text_blocks(message: dict):
    """Yield plain-text strings found in a message's content (str or list)."""
    content = message.get("content")
    if isinstance(content, str):
        yield content
    elif isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text")
                if isinstance(text, str):
                    yield text


def _record_hook_command(
    command: str,
    hook_event_label: str,
    ts_raw,
    hook_hits: Counter,
    hook_last_ts: dict,
    hook_event_breakdown: dict,
):
    """Match a raw hook `command` string against known script basenames and
    record a hit for the matching file. A single command string can only
    match one script (the last .py path segment), so this records at most
    one hit per call."""
    scripts = HOOK_SCRIPT_RE.findall(command)
    if not scripts:
        return
    basename = scripts[-1]
    hook_hits[basename] += 1
    if ts_raw and (basename not in hook_last_ts or ts_raw > hook_last_ts[basename]):
        hook_last_ts[basename] = ts_raw
    hook_event_breakdown.setdefault(basename, Counter())[hook_event_label] += 1


def scan(jsonl_dir: str, window_days: int):
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)

    agent_hits: dict[str, list] = {}
    skill_hits: dict[str, list] = {}
    hook_hits: Counter = Counter()
    hook_last_ts: dict[str, str] = {}
    hook_event_breakdown: dict[str, Counter] = {}

    sessions_scanned = set()
    total_records = 0

    for path, obj in _iter_jsonl_records(jsonl_dir):
        session_id = obj.get("sessionId")
        if session_id:
            sessions_scanned.add(session_id)
        total_records += 1

        ts_raw = obj.get("timestamp")
        ts = _parse_timestamp(ts_raw) if ts_raw else None
        in_window = ts is not None and ts >= cutoff

        # --- agent / skill (tool_use) detection ---
        message = obj.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict) or block.get("type") != "tool_use":
                        continue
                    name = block.get("name")
                    block_input = block.get("input") or {}
                    if name == "Agent":
                        slug = block_input.get("subagent_type")
                        if slug and in_window:
                            agent_hits.setdefault(slug, []).append(ts_raw)
                    elif name == "Skill":
                        slug = block_input.get("skill")
                        if slug and in_window:
                            skill_hits.setdefault(slug, []).append(ts_raw)

            # --- skill detection path 2: <command-name> in user text ---
            for text in _extract_text_blocks(message):
                for m in COMMAND_NAME_RE.finditer(text):
                    slug = m.group(1).strip()
                    if slug and in_window:
                        skill_hits.setdefault(slug, []).append(ts_raw)

        if not in_window:
            continue

        # --- hook detection, shape 1: PreToolUse / PostToolUse ---
        attachment = obj.get("attachment")
        if isinstance(attachment, dict) and attachment.get("type") == "hook_success":
            command = attachment.get("command", "")
            hook_event_label = attachment.get("hookName", attachment.get("hookEvent", "<unknown>"))
            _record_hook_command(
                command, hook_event_label, ts_raw, hook_hits, hook_last_ts, hook_event_breakdown
            )

        # --- hook detection, shape 2: Stop hook summary ---
        if obj.get("type") == "system" and obj.get("subtype") == "stop_hook_summary":
            for info in obj.get("hookInfos", []) or []:
                if not isinstance(info, dict):
                    continue
                command = info.get("command", "")
                _record_hook_command(
                    command, "Stop", ts_raw, hook_hits, hook_last_ts, hook_event_breakdown
                )

    return {
        "cutoff": cutoff,
        "agent_hits": agent_hits,
        "skill_hits": skill_hits,
        "hook_hits": hook_hits,
        "hook_last_ts": hook_last_ts,
        "hook_event_breakdown": hook_event_breakdown,
        "sessions_scanned": len(sessions_scanned),
        "total_records": total_records,
    }


def build_report(targets, scan_result, window_days: int):
    agent_hits = scan_result["agent_hits"]
    skill_hits = scan_result["skill_hits"]
    hook_hits = scan_result["hook_hits"]
    hook_last_ts = scan_result["hook_last_ts"]

    out_targets = []
    for t in targets:
        rtype = t["resource_type"]
        slug = t["slug"]
        if rtype == "agent":
            hits = agent_hits.get(slug, [])
            detection_paths = ["tool_use.Agent.subagent_type"] if hits else []
            last_ts = max(hits) if hits else None
        elif rtype == "skill":
            hits = skill_hits.get(slug, [])
            # detection_paths reflects which of the 2 paths could have
            # contributed; both are always checked, so report both as
            # "possible" sources when there is at least one hit.
            detection_paths = (
                ["tool_use.Skill.input.skill", "user_text.command-name"]
                if hits
                else []
            )
            last_ts = max(hits) if hits else None
        else:  # hook -- matched by script basename (e.g. "pre-tool-use.py")
            basename = t["basename"]
            count = hook_hits.get(basename, 0)
            detection_paths = []
            if count:
                detection_paths = ["attachment.hook_success.command"]
                if "Stop" in scan_result["hook_event_breakdown"].get(basename, {}):
                    detection_paths.append("system.stop_hook_summary.hookInfos[].command")
            last_ts = hook_last_ts.get(basename)

        entry = {
            "path": t["path"],
            "resource_type": rtype,
            "slug": slug,
            "hit_count_window": len(hits) if rtype != "hook" else hook_hits.get(t.get("basename", ""), 0),
            "last_hit_timestamp": last_ts,
            "detection_paths": detection_paths,
        }
        if rtype == "hook" and t["basename"] in NON_ENTRYPOINT_HOOK_BASENAMES:
            entry["note"] = (
                "helper module, not a registered hook entrypoint -- "
                "0 hits here is structurally expected, not a usage signal"
            )
        out_targets.append(entry)

    hook_event_breakdown_json = {
        basename: dict(counter)
        for basename, counter in scan_result["hook_event_breakdown"].items()
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "window_days": window_days,
        "sessions_scanned": scan_result["sessions_scanned"],
        "timestamp_field": "timestamp",
        "targets": out_targets,
        "hook_event_breakdown": hook_event_breakdown_json,
    }


def render_markdown(report: dict) -> str:
    lines = []
    lines.append("# Session log usage (window)")
    lines.append("")
    lines.append(f"- generated_at: {report['generated_at']}")
    lines.append(f"- window_days: {report['window_days']}")
    lines.append(f"- sessions_scanned: {report['sessions_scanned']}")
    lines.append("")
    lines.append("| path | resource_type | slug | hit_count_window | last_hit_timestamp | detection_paths |")
    lines.append("|---|---|---|---|---|---|")
    for t in sorted(
        report["targets"], key=lambda x: (x["resource_type"], -x["hit_count_window"])
    ):
        lines.append(
            "| {path} | {resource_type} | {slug} | {hit_count_window} | {last_hit_timestamp} | {detection_paths} |".format(
                path=t["path"],
                resource_type=t["resource_type"],
                slug=t["slug"],
                hit_count_window=t["hit_count_window"],
                last_hit_timestamp=t["last_hit_timestamp"] or "-",
                detection_paths=", ".join(t["detection_paths"]) or "-",
            )
        )
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--window-days", type=int, default=30)
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument("--jsonl-dir", default=PROJECT_JSONL_DIR)
    args = parser.parse_args()

    targets = discover_targets()
    scan_result = scan(args.jsonl_dir, args.window_days)
    report = build_report(targets, scan_result, args.window_days)

    if args.markdown:
        print(render_markdown(report))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
