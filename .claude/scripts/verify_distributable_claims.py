#!/usr/bin/env python3
"""verify_distributable_claims.py — 配布物の「存在の主張」が実体と合っているか検査する。

配布物（README / QUICKSTART / CHEATSHEET / CLAUDE / スライド / docs/internal）が
**存在すると主張しているもの**が実際にあるかを 2 種類検査する。

| 検査 | 主張 | 実体 |
|:-----|:-----|:-----|
| **command** | `` `/x` `` / `<code>/x</code>` で提示されたスラッシュコマンド | `.claude/skills/<x>/` |
| **directory** | `x/` の形で紹介された `.claude/` 直下ディレクトリ | `.claude/<x>/` が存在し、かつ**空でない** |

## なぜ要るか（2026-08-29 / セッション 27 実測）

**command 検査の契機**: 2026-07-13（`e3c7907`）に skill 8 件を削除した際、削除基準の
「grep 参照ゼロ」が見ていたのは**パス**（`.claude/skills/planning/SKILL.md`）であって
**コマンド名**（`/planning`）ではなかった。8 件中 6 件が配布物にコマンド名を残し、計 42 箇所が生存。
`QUICKSTART.md` Step 2 が「存在しないコマンドを新規ユーザーの最初の一手として案内する」
状態が約 6 週間続いた。2026-08-27 の配布物点検も同じ穴（パスは見るがコマンド名は見ない）で
検出できなかった —— **削除する側と点検する側が同一の盲点を共有していた。**

**directory 検査の契機**: 空の `.claude/commands/` を機能として紹介する記載が、
2026-08-27 に 2 箇所修正されたあと **7 箇所残存**していた（2026-08-29 に独立監査が検出）。
同日に「日本語版だけ直して英語版を置き去りにしていないか」という**人手チェック項目を新設した
そのコミットの中で**、まさにその形の見落としが残っていた。**2 度再発した型であり、
人手チェックリストが機能しなかった実測がある**ため機械化する。

## 設計

**維持リストを持たない**（`rule-001` 恒久解 (c) / conftest.py の計器隔離ガード = R3 機構 #8 と同型）:

- 「実在するコマンド」は `.claude/skills/` のディレクトリ名から導出する
- 「空のディレクトリ」は `.claude/` の実体から導出する
- 「検査対象の配布物」は glob から導出する
- 除外は `EXCLUDED_FROM_SCAN` / `DIRECTORY_MENTION_EXCEPTIONS` に**理由とセットで**書く
  （理由なしの除外はテストが落とす）

## 射程の限界（過大評価しないこと）

- 見ているのは**存在**のみ。**説明が現行の製品を指しているか**は見ていない
  （概念名の改名・削除された機能の説明・日英の乖離は射程外 → `/release` Phase 2.5 の人手分）
- directory 検査は **`.claude/` 直下に限る**。`src/` `tests/` `docs/memos/` 等の
  「配布先プロジェクトのテンプレート枠」は 2026-08-27 に**誤検出として明示的に取り下げ済**
  （`2026-08-27-distribution-docs-sweep.md` D-2）であり、ここへ射程を広げることは
  **決着済みの判断を蒸し返す**ことになる

Usage:
    bash .claude/scripts/py_invoke.sh .claude/scripts/verify_distributable_claims.py \
        [--json] [--exit-nonzero-on-drift]

Refs:
    docs/artifacts/2026-08-27-distribution-docs-sweep.md §5 / D-2
    docs/artifacts/r-1-deletions.md §1（2026-07-13 の skill 削除 8 件）
    conftest.py（除外に理由を添える作法の参照元）
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# 除外 — 検査しないものは、必ず理由とセットで書く
# --------------------------------------------------------------------------

EXCLUDED_FROM_SCAN: dict[str, str] = {
    "CHANGELOG.md": (
        "歴史記録。過去に実在したコマンド・ディレクトリへの言及は正当であり、"
        "削除済みのものが現れることそのものが仕様である。"
        "ここを検査すると履歴を書き換える圧力が生まれる。"
    ),
    "SESSION_STATE.md": (
        "gitignore 済のローカル作業状態。配布されないため配布物ではない。"
    ),
}

# 空でも言及してよい `.claude/` 直下ディレクトリ（理由必須）。
DIRECTORY_MENTION_EXCEPTIONS: dict[str, str] = {
    "worktrees": (
        "git worktree の作業領域。実行時に作られて使用後に消えるため、"
        "平常時に空であることが正常な状態である（空 = 未整備ではない）。"
    ),
    "logs": (
        "実行時に生成されるログ置き場。clone 直後は空だが、"
        "配布物がその存在を説明することは正当である。"
    ),
    "states": (
        "フェーズ承認ゲートの状態ファイル置き場。PLANNING 開始時に生成されるため、"
        "clone 直後は空でありうる。"
    ),
    "review-state": (
        "`/full-review` の中間状態。実行時に生成されるため clone 直後は空でありうる。"
    ),
    "tmp": (
        "一時領域。実行時に生成され、処理の完了後に空になることが正常な状態である。"
    ),
}

# Claude Code 組み込みコマンド。LAM の skill ではないが実在するため、欠落として数えない。
BUILTIN_COMMANDS: frozenset[str] = frozenset(
    {
        "agents", "artifacts", "clear", "compact", "config", "doctor", "help",
        "hooks", "mcp", "model", "permissions", "plugin", "quit", "resume",
    }
)

# 「コマンドとして提示されている」形だけを拾う。
# 直後が `/` のものはパス（`/etc/...` `/absolute/path/...`）なので拾わない。
#
# 末尾の否定先読みに `[a-z0-9-]` を含めるのは必須。`(?!/)` だけだと、`/etc/` に対して
# 正規表現が `/etc` からバックトラックして `/et`（直後が `c` で `/` ではない）を
# 拾ってしまう。トークン境界そのものを表明する必要がある。
_COMMAND_PAT = re.compile(r"(?:`|<code>)(/[a-z][a-z0-9-]*)(?![a-z0-9-/])")


def iter_distributables(base: Path) -> list[Path]:
    """配布物を glob から導出する（維持リストを持たない）。"""
    paths: list[Path] = []
    paths.extend(sorted(base.glob("*.md")))
    paths.extend(sorted((base / "docs" / "slides").glob("*.html")))
    paths.extend(sorted((base / "docs" / "internal").glob("*.md")))
    return [p for p in paths if p.name not in EXCLUDED_FROM_SCAN]


def existing_commands(base: Path) -> set[str]:
    """`.claude/skills/` のディレクトリ名から実在コマンドを導出する。"""
    skills_dir = base / ".claude" / "skills"
    if not skills_dir.is_dir():
        return set()
    return {p.name for p in skills_dir.iterdir() if p.is_dir() and not p.name.startswith("__")}


def _has_content(directory: Path) -> bool:
    """`__pycache__` を無視して中身があるか判定する。"""
    for child in directory.rglob("*"):
        if "__pycache__" in child.parts:
            continue
        return True
    return False


def empty_claude_dirs(base: Path) -> set[str]:
    """`.claude/` 直下の空ディレクトリを実体から導出する。"""
    root = base / ".claude"
    if not root.is_dir():
        return set()
    return {
        p.name
        for p in root.iterdir()
        if p.is_dir() and not p.name.startswith("__") and not _has_content(p)
    }


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def find_command_violations(base: Path) -> list[dict[str, object]]:
    """配布物が提示するコマンドのうち、実在しないものを列挙する。"""
    known = existing_commands(base) | BUILTIN_COMMANDS
    out: list[dict[str, object]] = []
    for path in iter_distributables(base):
        text = _read(path)
        if text is None:
            continue
        for match in _COMMAND_PAT.finditer(text):
            name = match.group(1)[1:]
            if name in known:
                continue
            out.append(
                {
                    "kind": "command",
                    "file": str(path.relative_to(base)).replace("\\", "/"),
                    "line": text[: match.start()].count("\n") + 1,
                    "subject": "/" + name,
                    "reason": "対応する .claude/skills/ が存在しない",
                }
            )
    return out


def find_directory_violations(base: Path) -> list[dict[str, object]]:
    """空の `.claude/` 直下ディレクトリを内容があるかのように紹介している箇所を列挙する。"""
    targets = empty_claude_dirs(base) - set(DIRECTORY_MENTION_EXCEPTIONS)
    if not targets:
        return []
    # 2 通りの現れ方を拾う:
    #   (1) `.claude/commands/`  — フルパス形
    #   (2) `├── commands/`      — ツリー図・見出し形（直前がパス区切りでない）
    #
    # (2) だけでは `.claude/commands/` を取り逃がす（直前が `/` で否定後読みに自分で
    # 引っかかる）。逆に (2) の否定後読みを外すと `docs/other/commands/` を誤検出する。
    # Python の後読みは固定長のため、選択肢を 2 本に分けて表明する必要がある。
    pats = {
        name: re.compile(
            rf"(?:\.claude/{re.escape(name)}/|(?<![\w./-]){re.escape(name)}/)"
        )
        for name in sorted(targets)
    }

    out: list[dict[str, object]] = []
    for path in iter_distributables(base):
        text = _read(path)
        if text is None:
            continue
        for name, pat in pats.items():
            for match in pat.finditer(text):
                out.append(
                    {
                        "kind": "directory",
                        "file": str(path.relative_to(base)).replace("\\", "/"),
                        "line": text[: match.start()].count("\n") + 1,
                        "subject": f".claude/{name}/",
                        "reason": "ディレクトリは存在するが空（中身のある機能として紹介している）",
                    }
                )
    return out


def find_violations(base: Path) -> list[dict[str, object]]:
    """全検査を実行する。"""
    return find_command_violations(base) + find_directory_violations(base)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=None, help="リポジトリルート（既定: 自動判定）")
    parser.add_argument("--json", action="store_true", help="JSON で出力する")
    parser.add_argument(
        "--exit-nonzero-on-drift",
        action="store_true",
        help="実体と食い違う主張を検出したら exit 1",
    )
    args = parser.parse_args(argv)

    base = args.root or _repo_root()
    violations = find_violations(base)
    scanned = len(iter_distributables(base))
    known = sorted(existing_commands(base))
    empties = sorted(empty_claude_dirs(base))

    if args.json:
        print(
            json.dumps(
                {
                    "scanned_files": scanned,
                    "skills": known,
                    "empty_claude_dirs": empties,
                    "violations": violations,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(f"検査した配布物: {scanned} 件 / 実在 skill: {len(known)} 件 / 空ディレクトリ: {len(empties)} 件")
        if violations:
            print(f"\nNG  実体と食い違う主張 {len(violations)} 件:")
            for v in violations:
                print(f"  [{v['kind']}] {v['file']}:{v['line']}  {v['subject']} — {v['reason']}")
        else:
            print("OK  配布物が存在を主張するコマンド・ディレクトリはすべて実体を伴う")

    return 1 if (violations and args.exit_nonzero_on_drift) else 0


if __name__ == "__main__":
    sys.exit(main())
