"""census_dangling.py のスモークテスト（2026-09-06 / セッション 34）.

**なぜ要るか**: 本スクリプトは 2026-09-05 の範囲レビューで scratchpad（temp ディレクトリ）に
書かれ、**リポジトリ外にしか存在しなかった**。Action 4c / Action 6 の中核となる計測器が
一時領域にあるのは事故待ちであり、2026-09-06 に repo へ移した。

移設時に**作者環境の絶対パス 2 箇所**（`D:/work7/LivingArchitectModel` と、削除済みの
scratchpad を指す出力先）を実測で発見した。**その再混入を止めるのが本テストの主目的**である。
—— 同型の違反は `.claude/rules/subprocess-encoding-convention.md` でも 2026-09-04 に是正されており、
`verify_plugin_containment` の T2 が `plugins/` 配下について検出する。本スクリプトは
`.claude/scripts/` にあり T2 の射程外なので、ここで受ける。

## Action 4c-0 の陰性対照（2026-09-08 追加）

計器を直したなら、**是正が効いていることを示す対照**が要る（BALTHASAR / Atom C0 (iii)）——
gabriel は 2026-09-07 に自分の probe が「ディレクトリ配下を無条件に解決済み扱いする」バグを
持っていたのを陰性対照で発見した（50 件すべて緑 → 厳密化して 13 件）。
設計 `docs/artifacts/2026-09-07-magi-action4c-path-references.md` Atom C0' の 5 点に対応する:

| # | 是正 | 本ファイルの対照 |
|:-:|:--|:--|
| a | glob 切り詰め | `test_glob_paths_are_not_truncated` |
| b | `exists_dev` を集合で判定 | `test_exists_dev_is_not_fooled_by_case` |
| c | 2 環境行列 | `test_env_matrix_has_all_four_quadrants` |
| d | フェンス内コマンドを別欄 | `test_fence_*`（3 件） |
| e | `py-fixture` の偽の理由を訂正 | `test_py_scope_reason_matches_its_criterion` |

**件数は固定しない**（出力は下界であり、増減そのものは違反ではない）。固定するのは
「走査と分離が機能していること」である。
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
    assert [r for r, _ in dropped[cd._PY_SCOPE_KEY]] == ["docs/specs/other/design.md"]
    assert [r for r, _ in kept["NG-other"]] == ["docs/specs/real/design.md"]
    for name in dropped:
        reason = cd._EXCLUSIONS.get(name, (None, cd._PY_SCOPE_REASON))[1]
        assert reason, f"{name} に理由が無い"


def test_census_runs_on_real_repo():
    """本番のリポジトリで最後まで走ること（**gate ではないので合否は問わない**）。"""
    env, result, cmd_result, path_hits = cd.census()
    assert env["files"] and env["skills"]
    assert result, "参照が 1 件も採れないのは走査の失敗（緑と誤認しない）"
    assert path_hits, "生のパス参照は 2 環境行列の入力であり、空なら行列も無意味になる"
    dropped, kept = cd.triage(result)
    unresolved = sum(len(s) for entries in kept.values() for _, s in entries)
    # 2026-09-06 実測 = 192 箇所 / 4c-0 の glob 是正後は 179 箇所。**下界**であり、
    # 増減そのものは違反ではない。ここで固定するのは「走査が機能していること」。
    assert unresolved > 0
    assert set(dropped) == {"placeholder", "runtime", "write-dest", cd._PY_SCOPE_KEY}


# --- Action 4c-0 (a): glob 切り詰め ------------------------------------------------


def _refs_in(span: str) -> list:
    """`collect()` と同じ手順で 1 スパンからパス参照を採る。"""
    return [
        m.group(0)
        for m in cd.PATH_RE.finditer(span)
        if not cd.PLACEHOLDER.search(span[: m.start()] + m.group(0))
    ]


def test_glob_paths_are_not_truncated():
    """glob を含むパスは**切り詰めず**、プレースホルダとして除外されること。

    是正前は `PATH_RE` が `*` を語構成文字に含まないため `.claude/agents/*.md` が
    `.claude/agents` に切り詰められ、その後の PLACEHOLDER 検査は**切り詰めた後の文字列**に
    走るので除外に掛からなかった（= 偽陽性）。**分類問題ではなくトークナイザ問題**である。
    """
    assert _refs_in(".claude/agents/*.md") == []
    assert _refs_in(".claude/{skills,agents}/**") == []
    assert _refs_in("docs/specs/*/design.md") == []
    # **消しすぎていないこと**（glob を含まない実在参照は残る）
    assert _refs_in(".claude/agents/gabriel.md") == [".claude/agents/gabriel.md"]


# --- Action 4c-0 (b): exists_dev を集合で判定 --------------------------------------


def test_exists_dev_is_not_fooled_by_case():
    """`exists_dev` は `rglob` 由来の集合で判定し、**FS 問い合わせに頼らない**こと。

    NTFS は case-insensitive なので `Path.is_file()` は `.claude/Rules/...` に True を返す。
    それに頼ると、PM ゲートの大小文字非区別を説明する**証拠テキスト**（意図的な誤記）を
    「実在」と誤判定する。`permission-levels.md` が 2026-09-05 に踏んだ罠と同型。
    """
    files, dirs = cd.build_dev_env()
    assert ".claude/rules/security-commands.md" in files
    assert ".claude/Rules/security-commands.md" not in files
    assert "docs/specs" in dirs and "docs/Specs" not in dirs
    # **食い違うことこそが主眼**（case-insensitive な FS 上でのみ観測できる）
    if (REPO_ROOT / ".claude/Rules/security-commands.md").is_file():
        assert ".claude/Rules/security-commands.md" not in files, (
            "FS 問い合わせ（is_file）で実装すると、この行が通らなくなる"
        )
    assert ".git" not in {p.split("/")[0] for p in files}, "走査除外が効いていない"


# --- Action 4c-0 (c): 2 環境行列 ----------------------------------------------------


def test_env_matrix_partitions_by_two_environments():
    hits = {
        "a": ["x.md:1"],  # dev+ user+
        "b": ["x.md:2"],  # dev+ user-
        "c": ["x.md:3"],  # dev- user+
        "d": ["x.md:4"],  # dev- user-
    }
    m = cd.env_matrix(hits, ({"a", "c"}, set()), ({"a", "b"}, set()))
    assert [r for r, _ in m["dev+user+"]] == ["a"]
    assert [r for r, _ in m["dev+user-"]] == ["b"]
    assert [r for r, _ in m["dev-user+"]] == ["c"]
    assert [r for r, _ in m["dev-user-"]] == ["d"]


def test_env_matrix_has_all_four_quadrants():
    """実リポジトリで 4 象限すべてに件数が出ること（役割分担が可視化されている）。

    空の象限があるなら、それは「無い」のではなく**判定が壊れている**可能性が高い。
    """
    env, _result, _cmd, path_hits = cd.census()
    m = cd.env_matrix(path_hits, (env["files"], env["dirs"]), cd.build_dev_env())
    for name, _meaning in cd.MATRIX_QUADRANTS:
        assert m[name], f"象限 {name} が空（判定の破損を疑う）"


# --- Action 4c-0 (d): フェンス内コマンドを別欄 -------------------------------------


def test_fence_refs_are_collected_separately_from_spans():
    """フェンス内は「実行する」、コードスパンは「読む」—— **別の欄**であること。

    コマンド引数に R-P（URL 化）を当ててはならないため、両者を混ぜてはいけない。
    """
    fence_hits = cd.collect_fence_refs()
    assert fence_hits, "フェンス走査が 1 件も採れないのは失敗（緑と誤認しない）"
    _env, _result, _cmd, path_hits = cd.census()
    # 同じ参照が両方に現れうるが、**別々の辞書として出る**ことが要件
    assert fence_hits is not path_hits


def test_fence_triage_separates_runtime_and_out_of_scope():
    """実行時生成物が偽陽性として分離され、開発環境にも無いものは射程外に落ちること。"""
    hits = {
        ".claude/rules/permission-levels.md": ["a.md:1"],  # resolved
        ".claude/lam-loop-state.json": ["a.md:2"],  # runtime（実行時生成物）
        "src/foo.py": ["a.md:3"],  # out-of-scope（dev にも無い作例）
        ".claude/scripts/build_dashboard.py": ["a.md:4"],  # unresolved = 実害
    }
    user = ({".claude/rules/permission-levels.md"}, set())
    dev = ({".claude/rules/permission-levels.md", ".claude/scripts/build_dashboard.py"}, set())
    out = cd.triage_fence(hits, user, dev)
    assert [r for r, _ in out["resolved"]] == [".claude/rules/permission-levels.md"]
    assert [r for r, _ in out["runtime"]] == [".claude/lam-loop-state.json"]
    assert [r for r, _ in out["out-of-scope"]] == ["src/foo.py"]
    assert [r for r, _ in out["unresolved"]] == [".claude/scripts/build_dashboard.py"]


def test_fence_resolution_is_strict_not_prefix_based():
    """上位ディレクトリの実在を根拠に配下を解決済み扱いしないこと。

    **gabriel が 2026-09-07 に自分の probe で踏んだバグ**（50 件すべて緑 → 厳密化で 13 件）。
    """
    hits = {".claude/scripts/build_dashboard.py": ["a.md:1"]}
    dev = ({".claude/scripts/build_dashboard.py"}, set())
    out = cd.triage_fence(hits, (set(), {".claude/scripts"}), dev)
    assert out["resolved"] == []
    assert [r for r, _ in out["unresolved"]] == [".claude/scripts/build_dashboard.py"]


def test_fence_skips_starter_templates():
    """`templates/starter/**` は射程外（利用者所有ファイル / R-P の第 3 層と同じ）。"""
    sites = [s for sites in cd.collect_fence_refs().values() for s in sites]
    assert not [s for s in sites if "/templates/starter/" in s]


# --- Action 4c-0 (e): py-fixture の偽の理由を訂正 -----------------------------------


def test_py_scope_reason_matches_its_criterion():
    """除外の**理由**が判定条件と一致すること。

    旧理由「テストフィクスチャ内の文字列定数」は**偽**だった —— 実測 9 件のうち 6 件は
    配布コード（`hooks/*.py` / `managed/scripts/*.py`）の docstring・定数でフィクスチャではない。
    判定条件（参照元が全て `.py`）は元から正しく、偽だったのは理由の側である。
    """
    assert cd._PY_SCOPE_KEY == "py-out-of-scope"
    assert "射程外" in cd._PY_SCOPE_REASON
    assert "フィクスチャ" not in cd._PY_SCOPE_REASON, "偽だった旧理由が復活している"

    _env, result, _cmd, _hits = cd.census()
    dropped, _kept = cd.triage(result)
    entries = dropped[cd._PY_SCOPE_KEY]
    assert entries, "実リポジトリで 1 件も落ちないなら、条件と実体が食い違っている"
    for ref, sites in entries:
        assert all(s.split(":")[0].endswith(".py") for s in sites), (
            f"{ref} の参照元に .py 以外が混じっており、理由が成立しない"
        )
