"""census_dangling.py のスモークテスト（2026-09-06 / セッション 34）.

**なぜ要るか**: 本スクリプトは 2026-09-05 の範囲レビューで scratchpad（temp ディレクトリ）に
書かれ、**リポジトリ外にしか存在しなかった**。Action 4c / Action 6 の中核となる計測器が
一時領域にあるのは事故待ちであり、2026-09-06 に repo へ移した。

移設時に**作者環境の絶対パス 2 箇所**（`D:/work7/LivingArchitectModel` と、削除済みの
scratchpad を指す出力先）を実測で発見した。**その再混入を止めるのが本テストの主目的**である。
—— 同型の違反は `.claude/rules/subprocess-encoding-convention.md` でも 2026-09-04 に是正されており、
`verify_plugin_containment` の T2 が `plugins/` 配下について検出する。本スクリプトは
`.claude/scripts/` にあり T2 の射程外なので、ここで受ける。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import census_dangling as cd  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = SCRIPTS_DIR / "census_dangling.py"

# 作者環境の絶対パス（T2 の `_ABSOLUTE_PATH_PATTERNS` と同じ形）
_AUTHOR_PATH_RE = (
    re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/]"),
    re.compile(r"/home/[A-Za-z0-9_.-]+/"),
    re.compile(r"/Users/[A-Za-z0-9_.-]+/"),
)


def test_no_author_absolute_path():
    """作者環境の絶対パスを持たないこと（**移設時に実際に 2 箇所あった**）。"""
    text = SCRIPT.read_text(encoding="utf-8")
    offenders = [rx.pattern for rx in _AUTHOR_PATH_RE if rx.search(text)]
    assert offenders == [], f"作者環境の絶対パスが混入している: {offenders}"


def test_repo_root_is_derived_from_file_location():
    """リポジトリルートは `__file__` から導出されること（環境非依存）。"""
    assert cd.REPO == REPO_ROOT
    assert cd.PLUGIN == REPO_ROOT / "plugins" / "lam-harness"


def test_user_env_is_derived_from_templates():
    """判定基準は LAM の実在ではなく **plugin が配るもの + init が敷くもの**であること。

    ここが機構 #10 との違いであり、本スクリプトが存在する理由そのものである。
    """
    files, dirs, skills, agents = cd.build_user_env()
    # managed から敷かれるもの
    assert ".claude/rules/permission-levels.md" in files
    assert "docs/internal/02_DEVELOPMENT_FLOW.md" in files
    # starter から敷かれるもの
    assert "CLAUDE.md" in files
    # init が作る空ディレクトリ
    assert "docs/specs" in dirs
    # **配布されないものは利用者環境に無い**（判定基準が LAM の実在でないことの対照）
    assert ".claude/rules/hga-summoning.md" not in files
    assert len(skills) >= 15 and len(agents) >= 12


def test_classify_path_buckets():
    files, dirs = {".claude/rules/x.md"}, {".claude/rules"}
    assert cd.classify_path(".claude/rules/x.md", files, dirs) == "OK-file"
    assert cd.classify_path(".claude/rules", files, dirs) == "OK-dir"
    assert cd.classify_path("plugins/lam-harness/skills/magi", files, dirs) == "OK-selfref"
    assert cd.classify_path(".claude/skills/magi/SKILL.md", files, dirs) == "NG-components"
    assert cd.classify_path(".claude/agents/gabriel.md", files, dirs) == "NG-components"
    assert cd.classify_path("docs/specs/x/design.md", files, dirs) == "NG-specs"
    assert cd.classify_path("src/whatever.py", files, dirs) == "NG-other"


def test_triage_drops_with_reasons():
    """除外は理由とセットで持つこと（機構 #10 の EXCLUDED_FROM_SCAN と同じ思想）。"""
    result = {
        "NG-other": [
            (".claude/logs/permission.log", ["a.md:1"]),  # runtime
            ("docs/tasks/x.md", ["a.md:2"]),  # write-dest
            ("docs/specs/real/design.md", ["a.md:3"]),  # 残る
            ("docs/specs/other/design.md", ["b.py:4"]),  # py-fixture
        ],
        "OK-file": [("x", ["a.md:9"])],  # NG 以外は triage の対象外
    }
    dropped, kept = cd.triage(result)
    assert [r for r, _ in dropped["runtime"]] == [".claude/logs/permission.log"]
    assert [r for r, _ in dropped["write-dest"]] == ["docs/tasks/x.md"]
    assert [r for r, _ in dropped["py-fixture"]] == ["docs/specs/other/design.md"]
    assert [r for r, _ in kept["NG-other"]] == ["docs/specs/real/design.md"]
    for name in dropped:
        reason = cd._EXCLUSIONS.get(name, (None, cd._PY_FIXTURE_REASON))[1]
        assert reason, f"{name} に理由が無い"


def test_census_runs_on_real_repo():
    """本番のリポジトリで最後まで走ること（**gate ではないので合否は問わない**）。"""
    env, result, cmd_result = cd.census()
    assert env["files"] and env["skills"]
    assert result, "参照が 1 件も採れないのは走査の失敗（緑と誤認しない）"
    dropped, kept = cd.triage(result)
    unresolved = sum(len(s) for entries in kept.values() for _, s in entries)
    # 2026-09-06 実測 = 192 箇所。**下界**であり、増減そのものは違反ではない。
    # ここで固定するのは「走査が機能していること」であって件数ではない。
    assert unresolved > 0
    assert set(dropped) == {"placeholder", "runtime", "write-dest", "py-fixture"}
