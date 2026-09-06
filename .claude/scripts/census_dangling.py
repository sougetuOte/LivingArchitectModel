"""census_dangling.py — 配布物の参照が「利用者環境」で解決するかを実測する。

## なぜ要るか —— 機構 #10 の欠陥を回避するため

既存の `verify_distributable_claims.py`（機構 #10）は、参照先の実在を **LAM リポジトリ**に対して
判定する。そのため「**LAM には在るが利用者環境には無い**」参照が構造的に緑になる。

本スクリプトは判定基準を差し替える —— **plugin が配るもの ＋ init が敷くもの**の和集合から
「init 後の利用者環境」を導出し、それに対して配布物内の参照を突き合わせる。
基準は `templates/` の実在から導出するため**維持リストを持たない**（機構 #7 / #11 と同型）。

初出は 2026-09-05 の範囲レビュー（`docs/artifacts/2026-09-05-distribution-scope-review.md`）。
そこでは **86 参照 / 182 箇所**が解決しないと実測された。本スクリプトはその計測器そのものである。

**2026-09-06 に scratchpad（temp）から repo へ移した。** 移設時に作者環境の絶対パス 2 箇所を
是正し、別スクリプトだった `triage.py`（除外規則）を統合した —— **2 本に分けていたこと自体が
片方だけ残る事故の元**だったため。同日の実測は **91 参照 / 192 箇所**（4a・4b で本文が増えた分）。

## 何を出すか

- **パス参照**を分類（`OK-file` / `OK-dir` / `OK-selfref` / `NG-*`）して件数を出す。
  分類名は上記レビュー §2 の表と対応しており、**名前を変えると記録との突合が切れる**
- **スラッシュコマンド**が実在 skill を指すかを判定する

さらに **除外（理由つき）** を適用した「残り = 利用者環境で解決しない参照」を出す。
`--out <path>` を与えると詳細を JSON で書き出す（既定は集計のみ）。

## 射程の限界（**下界である / 過大評価しないこと**）

- 走査対象はコードスパン（`` ` `` 囲い）と Markdown リンクのみ。**素の散文に書かれたパスは拾わない**
- プレースホルダ（`<...>` / `NNN` / `YYYY` 等）を含む行は除外する。**除外しすぎている可能性がある**
- 「解決しない」と「消すべき」は別である。開発記録への provenance 参照が意図的に残る余地は残る
  —— その判断は Action 4c / Action 6 が行う

したがって出力は **下界**として扱う（レビュー §2 の「86 / 182 は下界である」と同じ扱い）。

## 使い方

    bash .claude/scripts/py_invoke.sh .claude/scripts/census_dangling.py
    bash .claude/scripts/py_invoke.sh .claude/scripts/census_dangling.py --out census.json

**本スクリプトは gate ではない**（常に exit 0）。ゲート化するなら陰性対照が要る
（レビュー §3 が与え方を持つ）。ただし現況では 192 箇所が赤なので、**そのまま入れると
「常時赤 = 殺される計器」**になる —— 先に実体を減らすか、初期状態を凍結するかの判断が先である。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):  # Windows cp932 で UnicodeEncodeError を避ける
    sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
PLUGIN = REPO / "plugins" / "lam-harness"
TEXT_SUFFIXES = {".md", ".json", ".py", ".sh", ".txt", ".yaml", ".yml", ".html"}


def build_user_env(plugin_dir: Path = PLUGIN):
    """init 後の利用者環境に存在するパスの集合を、テンプレートの実在から導出する。"""
    files = set()
    dirs = set()

    mapping = [
        (plugin_dir / "templates/managed/rules", ".claude/rules"),
        (plugin_dir / "templates/managed/docs-internal", "docs/internal"),
        (plugin_dir / "templates/managed/scripts", ".claude/scripts"),
        (plugin_dir / "templates/starter/dot-claude", ".claude"),
    ]
    for src, dest in mapping:
        if not src.is_dir():
            continue
        for p in src.rglob("*"):
            if p.is_file():
                files.add(f"{dest}/{p.relative_to(src).as_posix()}")

    starter = plugin_dir / "templates/starter"
    if starter.is_dir():
        for p in starter.iterdir():
            if p.is_file():
                files.add(p.name)

    # init が明示的に作る空ディレクトリ（init/SKILL.md Step 3）
    for d in [".claude/states", "docs/specs", "docs/adr", "docs/tasks", "docs/artifacts"]:
        dirs.add(d)
    for f in files:
        parts = f.split("/")
        for i in range(1, len(parts)):
            dirs.add("/".join(parts[:i]))

    skills_dir = plugin_dir / "skills"
    agents_dir = plugin_dir / "agents"
    skills = {p.name for p in skills_dir.iterdir() if p.is_dir()} if skills_dir.is_dir() else set()
    agents = {p.stem for p in agents_dir.glob("*.md")} if agents_dir.is_dir() else set()
    return files, dirs, skills, agents


PATH_RE = re.compile(r"(?:\.claude|docs|plugins|src|tests|scripts)(?:/[\w.@+-]+)+")
CMD_RE = re.compile(r"(?<![\w/`])/(?:lam-harness:)?([a-z][a-z0-9-]{2,})(?![\w/-])")
CODE_RE = re.compile(r"`([^`\n]{2,200})`")
LINK_RE = re.compile(r"\]\(([^)\s]{2,200})\)")
PLACEHOLDER = re.compile(r"[<>{}*?]|NNN|YYYY|\bN\b")

# 分類名は `docs/artifacts/2026-09-05-distribution-scope-review.md` §2 の表と対応する。
# **変更すると記録との突合が切れる。**
_NG_PREFIXES = (
    ("docs/artifacts/", "NG-artifacts"),
    ("docs/specs/", "NG-specs"),
    ("docs/adr/", "NG-adr"),
    (".claude/tests/", "NG-tests"),
    (".claude/hooks/", "NG-hooks"),
    (".claude/skills/", "NG-components"),
    (".claude/agents/", "NG-components"),
    (".claude/rules/", "NG-rules"),
    (".claude/scripts/", "NG-scripts"),
)

KNOWN_NON_COMMANDS = {"lam-harness"}


def classify_path(ref: str, files: set, dirs: set) -> str:
    if ref in files:
        return "OK-file"
    if ref in dirs:
        return "OK-dir"
    if ref.startswith("plugins/"):
        return "OK-selfref"
    for prefix, label in _NG_PREFIXES:
        if ref.startswith(prefix):
            return label
    return "NG-other"


def collect(plugin_dir: Path = PLUGIN, repo: Path = REPO):
    """(パス参照 -> 出現箇所, コマンド -> 出現箇所) を返す。"""
    path_hits: dict = {}
    cmd_hits: dict = {}
    for p in sorted(plugin_dir.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in TEXT_SUFFIXES:
            continue
        rel = p.relative_to(repo).as_posix()
        text = p.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.split("\n"), start=1):
            for span in CODE_RE.findall(line) + LINK_RE.findall(line):
                if span.startswith(("http://", "https://")):
                    continue
                for m in PATH_RE.finditer(span):
                    ref = m.group(0)
                    if PLACEHOLDER.search(span[: m.start()] + ref):
                        continue
                    path_hits.setdefault(ref, []).append(f"{rel}:{lineno}")
                for m in CMD_RE.finditer(span):
                    cmd_hits.setdefault(m.group(1), []).append(f"{rel}:{lineno}")
    return path_hits, cmd_hits


def census(plugin_dir: Path = PLUGIN, repo: Path = REPO):
    files, dirs, skills, agents = build_user_env(plugin_dir)
    path_hits, cmd_hits = collect(plugin_dir, repo)

    result: dict = {}
    for ref, sites in sorted(path_hits.items()):
        result.setdefault(classify_path(ref, files, dirs), []).append((ref, sorted(set(sites))))

    cmd_result: dict = {"OK": [], "NG": []}
    for cmd, sites in sorted(cmd_hits.items()):
        if cmd in KNOWN_NON_COMMANDS:
            continue
        cmd_result["OK" if cmd in skills else "NG"].append((cmd, sorted(set(sites))))

    return {"files": files, "dirs": dirs, "skills": skills, "agents": agents}, result, cmd_result


# 除外規則（**理由必須** / 機構 #10 の EXCLUDED_FROM_SCAN と同じ思想）。
# 2026-09-05 のレビューでは本工程が別スクリプト（`triage.py`）に分かれていた。
# **分けていたこと自体が片方だけ残る事故の元**だったため 1 本に統合した（2026-09-06）。
_EXCLUSIONS = {
    "placeholder": (
        re.compile(r"(?:-$|/xxx|xxx\.|/research/|feat-|api-$|data-$)"),
        "命名パターンの提示であり特定の実体を指していない",
    ),
    "runtime": (
        re.compile(
            r"^\.claude/(logs|review-state|states|projects|agent-memory|commands|settings"
            r"|tdd-patterns\.log|test-results\.xml|doc-sync-flag|lam-loop-state\.json"
            r"|\.session-pm-edit-cache\.json|\.pre-compact-fired|compaction-exposure\.log"
            r"|gabriel-metrics\.log|rubric-tmp\.md)"
        ),
        "実行時に生成される / 利用者が作る出力先であり事前に存在しなくてよい",
    ),
    "write-dest": (
        re.compile(r"^docs/(artifacts/(knowledge|tdd-patterns|audit-reports)$|tasks/)"),
        "書込先ディレクトリ（init が docs/artifacts を作る / 中身は利用者が生む）",
    ),
}

_PY_FIXTURE_REASON = "テストフィクスチャ内の文字列定数（配布物の主張ではない）"


def triage(result: dict):
    """NG 分類から「正当に解決しなくてよい参照」を理由つきで落とす。

    残ったものが「**利用者環境で解決しない参照**」である。
    """
    kept: dict = {}
    dropped: dict = {name: [] for name in _EXCLUSIONS}
    dropped["py-fixture"] = []

    for cat, entries in result.items():
        if not cat.startswith("NG"):
            continue
        for ref, sites in entries:
            hit = next((n for n, (rx, _) in _EXCLUSIONS.items() if rx.search(ref)), None)
            if hit:
                dropped[hit].append((ref, sites))
            elif all(s.split(":")[0].endswith(".py") for s in sites):
                dropped["py-fixture"].append((ref, sites))
            else:
                kept.setdefault(cat, []).append((ref, sites))
    return dropped, kept


def main() -> int:
    parser = argparse.ArgumentParser(description="配布物の参照が利用者環境で解決するかを実測する")
    parser.add_argument("--out", help="詳細を JSON で書き出す先（既定: 書き出さない）")
    args = parser.parse_args()

    env, result, cmd_result = census()

    print("=== 利用者環境（init 後 / テンプレートの実在から導出）===")
    print(
        f"files={len(env['files'])} dirs={len(env['dirs'])} "
        f"skills={len(env['skills'])} agents={len(env['agents'])}"
    )
    print()
    print("=== パス参照の分類（ユニーク参照数 / 出現箇所数）===")
    ng_refs = ng_sites = 0
    for k in sorted(result):
        n_ref = len(result[k])
        n_site = sum(len(s) for _, s in result[k])
        if k.startswith("NG"):
            ng_refs += n_ref
            ng_sites += n_site
        print(f"{k:16} refs={n_ref:4}  sites={n_site:4}")
    print(f"{'NG 生の合計':16} refs={ng_refs:4}  sites={ng_sites:4}")
    print()

    dropped, kept = triage(result)
    print("=== 除外（理由つき / 正当に解決しなくてよいもの）===")
    for name, items in dropped.items():
        reason = _EXCLUSIONS.get(name, (None, _PY_FIXTURE_REASON))[1]
        n_site = sum(len(s) for _, s in items)
        print(f"{name:12} refs={len(items):3} sites={n_site:3}  — {reason}")
    print()
    print("=== 残り = **利用者環境で解決しない参照**（下界 / 射程の限界は docstring）===")
    tot_r = tot_s = 0
    for cat in sorted(kept):
        n_r = len(kept[cat])
        n_s = sum(len(s) for _, s in kept[cat])
        tot_r += n_r
        tot_s += n_s
        print(f"{cat:16} refs={n_r:3} sites={n_s:3}")
    print(f"{'合計':16} refs={tot_r:3} sites={tot_s:3}")
    print()
    print("=== 参照元ファイル別（sites 降順 / 上位 10）===")
    by_file: dict = {}
    for entries in kept.values():
        for _, sites in entries:
            for s in sites:
                by_file[s.split(":")[0]] = by_file.get(s.split(":")[0], 0) + 1
    for f, n in sorted(by_file.items(), key=lambda kv: -kv[1])[:10]:
        print(f"  {n:3}  {f}")
    print()
    print("=== スラッシュコマンド ===")
    for k in ("OK", "NG"):
        n_ref = len(cmd_result[k])
        n_site = sum(len(s) for _, s in cmd_result[k])
        print(f"{k:16} refs={n_ref:4}  sites={n_site:4}")
    if cmd_result["NG"]:
        print("  NG:", ", ".join(c for c, _ in cmd_result["NG"]))

    if args.out:
        out = Path(args.out)
        out.write_text(
            json.dumps(
                {"paths": result, "unresolved": kept, "excluded": dropped, "commands": cmd_result},
                ensure_ascii=False,
                indent=1,
            ),
            encoding="utf-8",
        )
        print(f"\n詳細: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
