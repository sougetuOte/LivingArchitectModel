#!/usr/bin/env python3
"""R-1 W-R4-S1-T2: git log usage scan for .claude/ agents / skills / hooks / commands.

Collects, for each target_path (agent/skill/hook/command resource):
  - first/last commit date + commit count (via `git log --follow`)
  - rename history (via `git log --diff-filter=R --name-status`)
Also collects repo-wide deletion history under .claude/ (via
`git log --diff-filter=D --name-only`) and cross-references it against the
current resource-path glob patterns to build `orphan_history` (deleted
resources that no longer exist on disk).

No third-party dependencies (stdlib only). Designed to run with CWD = repo
root (D:\\work7\\LivingArchitectModel), matching Git Bash conventions used
elsewhere in this repo (forward-slash paths).

Usage:
    python .claude/scripts/r-1-git-log-usage.py            # JSON to stdout
    python .claude/scripts/r-1-git-log-usage.py --markdown # Markdown table to stdout
"""

from __future__ import annotations

import fnmatch
import json
import subprocess
import sys
from datetime import datetime, timezone

# Resource type -> glob pattern (relative to repo root, forward slashes).
# Matches the target_path definitions in the task brief / design.md §7.2.
RESOURCE_GLOBS = {
    "agent": ".claude/agents/*.md",
    "skill": ".claude/skills/*/SKILL.md",
    "hook": ".claude/hooks/*.py",
    "command": ".claude/commands/*.md",
}


def run_git(args: list[str]) -> str:
    """Run a git command from repo root and return stdout as text.

    Raises RuntimeError (not silently swallowed) on non-zero exit so
    failures surface instead of producing a silently empty result.
    """
    result = subprocess.run(
        ["git", *args],
        cwd="D:/work7/LivingArchitectModel",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed (exit {result.returncode}): {result.stderr.strip()}"
        )
    return result.stdout


def path_matches_glob(path: str, pattern: str) -> bool:
    """Segment-wise glob match (each '/'-delimited part matched independently).

    Python's fnmatch.fnmatch translates '*' to a regex '.*' that freely
    crosses '/' boundaries, which would make '.claude/hooks/*.py' also match
    nested files like '.claude/hooks/analyzers/foo.py'. That over-matches
    relative to the true target set (shell/Glob-tool semantics keep '*'
    within a single path segment), so match segment counts and contents
    explicitly instead of using fnmatch.fnmatch on the whole string.
    """
    path_parts = path.split("/")
    pattern_parts = pattern.split("/")
    if len(path_parts) != len(pattern_parts):
        return False
    return all(fnmatch.fnmatch(pp, pat) for pp, pat in zip(path_parts, pattern_parts))


def list_target_paths() -> list[dict]:
    """Enumerate current on-disk target paths per resource type via git ls-files.

    Using `git ls-files` (not Glob) keeps this script self-contained (no
    dependency on the harness's Glob tool) while matching the same glob
    patterns declared in RESOURCE_GLOBS.
    """
    tracked = run_git(["ls-files", "--", ".claude/"]).splitlines()
    targets = []
    for resource_type, pattern in RESOURCE_GLOBS.items():
        matches = sorted(p for p in tracked if path_matches_glob(p, pattern))
        for path in matches:
            targets.append({"path": path, "resource_type": resource_type})
    return targets


def get_file_history(path: str) -> dict:
    """Return first/last commit date, commit count, and rename history for path.

    Uses `git log --follow` so history survives renames (design.md §7.1
    "改名追跡: 過去の改名歴のみ --follow で補完").
    """
    log_output = run_git(
        [
            "log",
            "--follow",
            "--date=short",
            "--pretty=format:%H|%ad",
            "--",
            path,
        ]
    )
    lines = [ln for ln in log_output.splitlines() if ln.strip()]
    commit_count = len(lines)
    if commit_count == 0:
        return {
            "first_commit_date": None,
            "last_commit_date": None,
            "commit_count": 0,
            "renames": [],
        }
    # git log lists newest-first; last line (oldest) = first commit.
    last_line = lines[0]
    first_line = lines[-1]
    last_commit_date = last_line.split("|", 1)[1]
    first_commit_date = first_line.split("|", 1)[1]

    renames = get_rename_history_for_path(path)

    return {
        "first_commit_date": first_commit_date,
        "last_commit_date": last_commit_date,
        "commit_count": commit_count,
        "renames": renames,
    }


def get_rename_history_for_path(path: str) -> list[dict]:
    """Return rename events (from -> to) where `to` == path, using --follow --name-status."""
    output = run_git(
        [
            "log",
            "--follow",
            "--date=short",
            "--name-status",
            "--pretty=format:__COMMIT__%H|%ad",
            "--",
            path,
        ]
    )
    renames = []
    current_commit = None
    current_date = None
    for line in output.splitlines():
        if line.startswith("__COMMIT__"):
            rest = line[len("__COMMIT__"):]
            current_commit, current_date = rest.split("|", 1)
            continue
        if line.startswith("R"):
            # Format: "R100\told/path\tnew/path"
            parts = line.split("\t")
            if len(parts) == 3:
                _status, old_path, new_path = parts
                if new_path == path:
                    renames.append(
                        {
                            "from": old_path,
                            "to": new_path,
                            "date": current_date,
                            "commit": current_commit,
                        }
                    )
    # Oldest-first for readability.
    renames.reverse()
    return renames


def classify_resource_type(path: str) -> str | None:
    for resource_type, pattern in RESOURCE_GLOBS.items():
        if path_matches_glob(path, pattern):
            return resource_type
    return None


def get_orphan_history(existing_paths: set[str]) -> list[dict]:
    """Return deletion events for .claude/ paths that no longer exist on disk.

    Uses repo-wide `git log --diff-filter=D --name-only` scoped to .claude/,
    then filters to paths matching a RESOURCE_GLOBS pattern and not present
    in existing_paths (i.e. genuinely deleted, not renamed-away-then-back).
    """
    output = run_git(
        [
            "log",
            "--diff-filter=D",
            "--name-only",
            "--date=short",
            "--pretty=format:__COMMIT__%H|%ad",
            "--",
            ".claude/",
        ]
    )
    deletions_by_path: dict[str, dict] = {}
    current_commit = None
    current_date = None
    for line in output.splitlines():
        if line.startswith("__COMMIT__"):
            rest = line[len("__COMMIT__"):]
            current_commit, current_date = rest.split("|", 1)
            continue
        line = line.strip()
        if not line:
            continue
        resource_type = classify_resource_type(line)
        if resource_type is None:
            continue
        if line in existing_paths:
            # Currently exists (e.g. deleted then re-added later) -> not an orphan.
            continue
        # Keep the MOST RECENT deletion event per path (first one seen,
        # since git log is newest-first).
        if line not in deletions_by_path:
            deletions_by_path[line] = {
                "path": line,
                "resource_type": resource_type,
                "deleted_at": current_date,
                "deleted_by_commit": current_commit,
            }

    # For each orphan, find the last content-seen date (commit right before deletion).
    orphans = []
    for path, info in deletions_by_path.items():
        last_seen = get_last_content_seen(path, info["deleted_by_commit"])
        info["last_content_seen"] = last_seen
        orphans.append(info)

    orphans.sort(key=lambda o: (o["deleted_at"] or ""), reverse=True)
    return orphans


def get_last_content_seen(path: str, deletion_commit: str) -> str | None:
    """Return the commit date immediately before deletion_commit that touched path."""
    output = run_git(
        [
            "log",
            "--follow",
            "--date=short",
            "--pretty=format:%H|%ad",
            f"{deletion_commit}~1",
            "--",
            path,
        ]
    )
    lines = [ln for ln in output.splitlines() if ln.strip()]
    if not lines:
        return None
    # Newest-first; first line = most recent commit before deletion.
    return lines[0].split("|", 1)[1]


def build_report() -> dict:
    targets_meta = list_target_paths()
    existing_paths = {t["path"] for t in targets_meta}

    targets = []
    for meta in targets_meta:
        history = get_file_history(meta["path"])
        targets.append(
            {
                "path": meta["path"],
                "resource_type": meta["resource_type"],
                "exists_now": True,
                "first_commit_date": history["first_commit_date"],
                "last_commit_date": history["last_commit_date"],
                "commit_count": history["commit_count"],
                "deletions": [],  # existing files have no deletion event by definition
                "renames": history["renames"],
            }
        )

    orphan_history = get_orphan_history(existing_paths)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "targets": targets,
        "orphan_history": orphan_history,
    }


def render_markdown(report: dict) -> str:
    lines = []
    lines.append(f"# git log usage scan (generated {report['generated_at']})")
    lines.append("")
    by_type: dict[str, list[dict]] = {}
    for t in report["targets"]:
        by_type.setdefault(t["resource_type"], []).append(t)
    for resource_type in RESOURCE_GLOBS:
        items = by_type.get(resource_type, [])
        lines.append(f"## {resource_type} ({len(items)})")
        lines.append("")
        lines.append("| path | first_commit | last_commit | commit_count | renames |")
        lines.append("|---|---|---|---|---|")
        for t in items:
            renames = "; ".join(f"{r['from']}→{r['to']} ({r['date']})" for r in t["renames"]) or "-"
            lines.append(
                f"| `{t['path']}` | {t['first_commit_date']} | {t['last_commit_date']} | "
                f"{t['commit_count']} | {renames} |"
            )
        lines.append("")

    lines.append(f"## orphan_history ({len(report['orphan_history'])})")
    lines.append("")
    lines.append("| path | resource_type | deleted_at | deleted_by_commit | last_content_seen |")
    lines.append("|---|---|---|---|---|")
    for o in report["orphan_history"]:
        lines.append(
            f"| `{o['path']}` | {o['resource_type']} | {o['deleted_at']} | "
            f"{o['deleted_by_commit']} | {o['last_content_seen']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    try:
        report = build_report()
    except RuntimeError as exc:
        # Do not silently swallow: surface the failure clearly (Critical per
        # code-quality-guideline.md "Error Swallowing / Silent Failure").
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if "--markdown" in sys.argv:
        print(render_markdown(report))
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
