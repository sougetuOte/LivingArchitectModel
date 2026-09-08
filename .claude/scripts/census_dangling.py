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

**2026-09-08（Action 4c-0）に 5 点を是正した** —— (a) glob 切り詰め (b) `exists_dev` を
`rglob` 由来の集合で判定 (c) 2 環境行列 (d) フェンス内コマンドを別欄 (e) `py-fixture` の
**偽の除外理由**を訂正。設計は `docs/artifacts/2026-09-07-magi-action4c-path-references.md`
Atom C0'。是正後の実測は **89 参照 / 179 箇所**（(a) の偽陽性が消えた分）に加え、
新設のフェンス欄が **12 参照 / 25 箇所**の未解決を出す（**こちらは機能破壊であり、
参照の綴りでは直らない** → Action 4c-1）。**5 点すべてに陰性対照がある**
（`.claude/tests/scripts/test_census_dangling.py`）。

## 何を出すか

- **パス参照**を分類（`OK-file` / `OK-dir` / `OK-selfref` / `NG-*`）して件数を出す。
  分類名は上記レビュー §2 の表と対応しており、**名前を変えると記録との突合が切れる**
- **2 環境行列**（`exists_dev` × `exists_user`）—— 機構 #10 との役割分担を可視化する（下記）
- **フェンス内コマンド**（別欄 / 読者が**実行する**もの）が利用者環境で解決するか
- **スラッシュコマンド**が実在 skill を指すかを判定する

さらに **除外（理由つき）** を適用した「残り = 利用者環境で解決しない参照」を出す。
`--out <path>` を与えると詳細を JSON で書き出す（既定は集計のみ）。

## 2 環境行列 —— 機構 #10 との役割分担（Action 4c-0 / 2026-09-08）

| | `exists_user` | `¬exists_user` |
|:--|:--|:--|
| **`exists_dev`** | 両環境で解決する | **本スクリプトの射程**（LAM には在るが利用者環境に無い） |
| **`¬exists_dev`** | 配るが LAM に無い（生成物・異常） | **機構 #10 の領分**（誤記 / 意図的な誤記 / 実在しない） |

`exists_dev` は **`rglob` 由来の集合**で判定する。**`Path.is_file()` を使ってはならない** ——
NTFS は case-insensitive であり `.claude/Rules/...` が True になる。これは
`permission-levels.md` が 2026-09-05 に踏んだ罠（`normalize_path` が FS に問い合わせないため
大文字の `Rules` が SE 判定になった）と**同型**である。

なお R-P 分岐 2 が要求する `exists_dist`（plugin 内実体の有無）は **4c-2 の領分**である ——
T3 の派生写像を要するため、ここでは持たない。

## フェンス内コマンドを**別欄**にする理由（Action 4c-0 / 2026-09-08）

D4 は構文で線を引く —— **フェンス内は「実行する」、コードスパンは「読む」**。
前者は*配布集合*（閉包）の問題であり、**コマンド引数に R-P を当ててはならない**:
URL 化すればコマンドとして壊れ、`${CLAUDE_PLUGIN_ROOT}` 化しても*非配布*なら実体が無い。
**綴りでは直らず、配るか手順から外すかの二択**である。混ぜると配布集合の判断材料が
参照書き換えの変換対象に流れ込む。

## 射程の限界（**下界である / 過大評価しないこと**）

- パス参照の走査対象はコードスパン（`` ` `` 囲い）と Markdown リンクのみ。
  **素の散文に書かれたパスは拾わない**
- プレースホルダ（`<...>` / `NNN` / `YYYY` / glob `*` 等）を含む行は除外する。
  **除外しすぎている可能性がある**
- フェンス欄はフェンス内の全パストークンを採るため、ディレクトリ図や出力例が混じりうる
  （**上界側の誤差**。実行時生成物は `runtime` 除外で分離する）
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


_DEV_SKIP_DIRS = {".git", "__pycache__", ".venv", "node_modules", ".pytest_cache", ".ruff_cache"}


def build_dev_env(repo: Path = REPO):
    """**LAM 開発リポジトリ**に実在するパスの集合を返す（`exists_dev` の基準）。

    **`Path.is_file()` / `Path.exists()` を使わない。** NTFS は case-insensitive なので
    `.claude/Rules/security-commands.md` が True になり、意図的な誤記（PM ゲートの
    大小文字非区別を説明する証拠テキスト）を「実在」と誤判定する。
    `rglob` で採った集合に対する厳密一致なら、その罠を踏まない。
    """
    files = set()
    dirs = set()
    for p in repo.rglob("*"):
        rel = p.relative_to(repo)
        if _DEV_SKIP_DIRS & set(rel.parts):
            continue
        (dirs if p.is_dir() else files).add(rel.as_posix())
    return files, dirs


# glob / ブレースのメタ文字を**語構成文字に含める**（Action 4c-0 (a) / 2026-09-08）。
# 含めないと `` `.claude/agents/*.md` `` が `.claude/agents` で**切り詰められ**、
# その後の PLACEHOLDER 検査は切り詰めた後の文字列に走るため除外に掛からなかった。
# **glob は分類問題ではなくトークナイザ問題**であり、例外表を持たずに消える。
PATH_RE = re.compile(r"(?:\.claude|docs|plugins|src|tests|scripts)(?:/[\w.@+*?{}-]+)+")
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
    """`(利用者環境, パス参照の分類, スラッシュコマンド, 生のパス参照)` を返す。

    4 要素目（`path_hits`）は 2 環境行列（`env_matrix`）の入力である。
    """
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

    env = {"files": files, "dirs": dirs, "skills": skills, "agents": agents}
    return env, result, cmd_result, path_hits


# 2 環境行列の象限名。**役割分担を名前で持つ**（表は docstring §2 環境行列）。
MATRIX_QUADRANTS = (
    ("dev+user+", "両環境で解決する"),
    ("dev+user-", "**本スクリプトの射程** — LAM には在るが利用者環境に無い"),
    ("dev-user+", "配るが LAM に無い（生成物・異常）"),
    ("dev-user-", "機構 #10 の領分（誤記 / 意図的な誤記 / 実在しない）"),
)


def env_matrix(path_hits: dict, user_env, dev_env) -> dict:
    """パス参照を `exists_dev` × `exists_user` の 4 象限に振り分ける。

    どちらの実在判定も **集合メンバシップ**であり、FS への問い合わせを含まない。
    """
    ufiles, udirs = user_env
    dfiles, ddirs = dev_env
    matrix: dict = {name: [] for name, _ in MATRIX_QUADRANTS}
    for ref, sites in sorted(path_hits.items()):
        in_user = ref in ufiles or ref in udirs
        in_dev = ref in dfiles or ref in ddirs
        key = f"dev{'+' if in_dev else '-'}user{'+' if in_user else '-'}"
        matrix[key].append((ref, sorted(set(sites))))
    return matrix


_FENCE_RE = re.compile(r"^\s*(?:```|~~~)")


def collect_fence_refs(plugin_dir: Path = PLUGIN, repo: Path = REPO) -> dict:
    """フェンス内（``` / ~~~）のパストークンを採る —— **読者が実行する**もの。

    パス参照の走査（`collect`）とは**別欄**である。理由は docstring §フェンス内コマンド。
    `templates/starter/**` は射程外（利用者所有ファイル / R-P の第 3 層と同じ扱い）。
    """
    hits: dict = {}
    for p in sorted(plugin_dir.rglob("*.md")):
        rel = p.relative_to(repo).as_posix()
        if "/templates/starter/" in f"/{rel}":
            continue
        inside = False
        lines = p.read_text(encoding="utf-8", errors="replace").split("\n")
        for lineno, line in enumerate(lines, start=1):
            if _FENCE_RE.match(line):
                inside = not inside
                continue
            if not inside:
                continue
            for m in PATH_RE.finditer(line):
                ref = m.group(0)
                if PLACEHOLDER.search(line[: m.start()] + ref):
                    continue
                hits.setdefault(ref, []).append(f"{rel}:{lineno}")
    return hits


# 除外規則（**理由必須** / 機構 #10 の EXCLUDED_FROM_SCAN と同じ思想）。
# 2026-09-05 のレビューでは本工程が別スクリプト（`triage.py`）に分かれていた。
# **分けていたこと自体が片方だけ残る事故の元**だったため 1 本に統合した（2026-09-06）。
_EXCLUSIONS = {
    "placeholder": (
        re.compile(r"(?:-$|/xxx|xxx\.|/research/|feat-|api-$|data-$)"),
        "命名パターンの提示であり特定の実体を指していない",
    ),
    # 2026-09-08（4c-1 の閉包導出で発覚）: 3 件を補い、1 件の綴りを直した。
    # `\.pre-compact-fired` は**実体が `.claude/pre-compact-fired`（先頭ドットなし）**であり、
    # この除外は一度も発火していなかった。`gd-session-state.json` / `last-test-result` は
    # hook が書く実行時状態で、列挙から漏れていた（前 2 者は `permission-levels.md` が
    # 「hook が書く信頼アンカー」として PM 級に挙げている当のファイルである）。
    "runtime": (
        re.compile(
            r"^\.claude/(logs|review-state|states|projects|agent-memory|commands|settings"
            r"|tdd-patterns\.log|test-results\.xml|doc-sync-flag|lam-loop-state\.json"
            r"|gd-session-state\.json|last-test-result"
            r"|\.session-pm-edit-cache\.json|\.?pre-compact-fired|compaction-exposure\.log"
            r"|gabriel-metrics\.log|rubric-tmp\.md)"
        ),
        "実行時に生成される / 利用者が作る出力先であり事前に存在しなくてよい",
    ),
    "write-dest": (
        # 2026-09-08: `artifacts/dashboard` を追加（`build_dashboard.py` の**出力先**であり
        # 読み込む依存ではない。計器は read / write を判別できないため、ここで落とす）。
        re.compile(
            r"^docs/(artifacts/(knowledge|tdd-patterns|audit-reports|dashboard)|tasks/)"
        ),
        "書込先ディレクトリ（init が docs/artifacts を作る / 中身は利用者が生む）",
    ),
}

# **理由を訂正した**（Action 4c-0 (e) / 2026-09-08）。旧名 `py-fixture` / 旧理由
# 「テストフィクスチャ内の文字列定数」は**偽**だった —— 実測 9 件は全て `.py` 内だが、
# うち 6 件は配布コード（`hooks/*.py` / `managed/scripts/*.py`）の docstring・定数であって
# フィクスチャではない。判定条件（**参照元が全て `.py`**）は元から正しく、偽だったのは
# 理由の側である。真の理由は 1 つで 9 件すべてを覆える。
_PY_SCOPE_KEY = "py-out-of-scope"
_PY_SCOPE_REASON = "参照元が .py であり R-P の射程外（読者は開発者 / 拡張子は構文的）"


def triage(result: dict):
    """NG 分類から「正当に解決しなくてよい参照」を理由つきで落とす。

    残ったものが「**利用者環境で解決しない参照**」である。
    """
    kept: dict = {}
    dropped: dict = {name: [] for name in _EXCLUSIONS}
    dropped[_PY_SCOPE_KEY] = []

    for cat, entries in result.items():
        if not cat.startswith("NG"):
            continue
        for ref, sites in entries:
            hit = next((n for n, (rx, _) in _EXCLUSIONS.items() if rx.search(ref)), None)
            if hit:
                dropped[hit].append((ref, sites))
            elif all(s.split(":")[0].endswith(".py") for s in sites):
                dropped[_PY_SCOPE_KEY].append((ref, sites))
            else:
                kept.setdefault(cat, []).append((ref, sites))
    return dropped, kept


FENCE_BUCKETS = ("resolved", *_EXCLUSIONS, "out-of-scope", "unresolved")


def triage_fence(fence_hits: dict, user_env, dev_env) -> dict:
    """フェンス内パスを振り分ける。**残った `unresolved` が実害**である。

    判定は**厳密**（`ref in files or ref in dirs` のみを解決とみなす。上位ディレクトリの
    実在を根拠に配下を解決済み扱いしない —— gabriel が 2026-09-07 に自分の probe で
    そのバグを踏み、50 件すべて緑だったものが厳密化で 13 件に落ちた）。

    除外は**既存の `_EXCLUSIONS` を再利用**する（新しい除外表を作らない）。
    `out-of-scope` は **2 環境行列と同じ象限定義**であり、これも新規の表ではない ——
    本計器の射程は `exists_dev ∧ ¬exists_user` であって、開発環境にも無いもの
    （`src/foo.py` 等の説明用の作例・誤記）は機構 #10 の領分である。
    """
    ufiles, udirs = user_env
    dfiles, ddirs = dev_env
    out: dict = {name: [] for name in FENCE_BUCKETS}
    for ref, sites in sorted(fence_hits.items()):
        sites = sorted(set(sites))
        hit = next((n for n, (rx, _) in _EXCLUSIONS.items() if rx.search(ref)), None)
        if ref in ufiles or ref in udirs:
            out["resolved"].append((ref, sites))
        elif hit:
            out[hit].append((ref, sites))
        elif ref not in dfiles and ref not in ddirs:
            out["out-of-scope"].append((ref, sites))
        else:
            out["unresolved"].append((ref, sites))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="配布物の参照が利用者環境で解決するかを実測する")
    parser.add_argument("--out", help="詳細を JSON で書き出す先（既定: 書き出さない）")
    args = parser.parse_args()

    env, result, cmd_result, path_hits = census()
    dev_files, dev_dirs = build_dev_env()

    print("=== 利用者環境（init 後 / テンプレートの実在から導出）===")
    print(
        f"files={len(env['files'])} dirs={len(env['dirs'])} "
        f"skills={len(env['skills'])} agents={len(env['agents'])}"
    )
    print("=== 開発環境（LAM / rglob 由来の集合 — is_file() は使わない）===")
    print(f"files={len(dev_files)} dirs={len(dev_dirs)}")
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

    matrix = env_matrix(path_hits, (env["files"], env["dirs"]), (dev_files, dev_dirs))
    print("=== 2 環境行列（exists_dev × exists_user / 機構 #10 との役割分担）===")
    for name, meaning in MATRIX_QUADRANTS:
        entries = matrix[name]
        n_site = sum(len(s) for _, s in entries)
        print(f"{name:10} refs={len(entries):4}  sites={n_site:4}  — {meaning}")
    print()

    dropped, kept = triage(result)
    print("=== 除外（理由つき / 正当に解決しなくてよいもの）===")
    for name, items in dropped.items():
        reason = _EXCLUSIONS.get(name, (None, _PY_SCOPE_REASON))[1]
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
    fence = triage_fence(
        collect_fence_refs(), (env["files"], env["dirs"]), (dev_files, dev_dirs)
    )
    print("=== フェンス内コマンド（別欄 / **R-P を当ててはならない** = 配布集合の問題）===")
    for bucket in FENCE_BUCKETS:
        n_site = sum(len(s) for _, s in fence[bucket])
        print(f"{bucket:14} refs={len(fence[bucket]):3} sites={n_site:3}")
    if fence["unresolved"]:
        print("  --- 利用者環境で解決しない（**実行すれば落ちる**）---")
        for ref, sites in fence["unresolved"]:
            print(f"  {ref}")
            for s in sites:
                print(f"      {s}")
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
                {
                    "paths": result,
                    "unresolved": kept,
                    "excluded": dropped,
                    "commands": cmd_result,
                    "matrix": matrix,
                    "fence": fence,
                },
                ensure_ascii=False,
                indent=1,
            ),
            encoding="utf-8",
        )
        print(f"\n詳細: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
