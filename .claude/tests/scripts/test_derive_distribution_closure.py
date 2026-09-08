"""derive_distribution_closure.py のテスト（2026-09-08 / Action 4c-1）.

**なぜ要るか**: ADR-0010 追補 4 の K4 拡張は「配布集合は**エントリポイントからの到達閉包**として
導出する」と定めた。本スクリプトはその閉包を実際に計算する器であり、**PM 級の配布集合決定の
入力**になる。誤った閉包は誤った決定を生むため、判定の各段に対照を置く。

閉包の定義（設計 `docs/artifacts/2026-09-07-magi-action4c-path-references.md` §D4）:

    配布集合 = 閉包( エントリポイント )
    エントリポイント = 配布 hooks ∪ 配布 .md（skills / agents / managed 規範）の
                     **フェンス内コマンド**が名指しする実体
    到達関係       = import 閉包 ∪ 実行時データ依存

**件数は固定しない**（4c-1 の決定で配布集合が動けば出力は変わる）。固定するのは
「導出が機能していること」と「写像が正しいこと」である。
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import derive_distribution_closure as dc  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]


# --- 配布先の写像 ------------------------------------------------------------------


def test_dist_location_maps_mirror_areas():
    """複製相（hooks / skills / agents）は plugin 直下に配布実体を持つ。"""
    assert dc.dist_location(".claude/hooks/pre-tool-use.py") == (
        "plugins/lam-harness/hooks/pre-tool-use.py"
    )
    assert dc.dist_location(".claude/agents/gabriel.md") == (
        "plugins/lam-harness/agents/gabriel.md"
    )
    assert dc.dist_location(".claude/skills/magi/SKILL.md") == (
        "plugins/lam-harness/skills/magi/SKILL.md"
    )


def test_dist_location_maps_managed_areas():
    """managed テンプレート（rules / docs-internal / scripts）は templates/managed 配下。"""
    assert dc.dist_location(".claude/rules/permission-levels.md") == (
        "plugins/lam-harness/templates/managed/rules/permission-levels.md"
    )
    assert dc.dist_location("docs/internal/06_DECISION_MAKING.md") == (
        "plugins/lam-harness/templates/managed/docs-internal/06_DECISION_MAKING.md"
    )
    assert dc.dist_location(".claude/scripts/py_invoke.sh") == (
        "plugins/lam-harness/templates/managed/scripts/py_invoke.sh"
    )


def test_dist_location_is_none_for_non_distributed():
    """**配られていないものは None**（これが gap の判定そのもの）。"""
    assert dc.dist_location(".claude/scripts/r1_inventory.py") is None
    assert dc.dist_location(".claude/rules/hga-summoning.md") is None
    assert dc.dist_location("docs/artifacts/whatever.md") is None


def test_dist_location_does_not_query_the_filesystem_by_case():
    """大文字小文字を FS に判定させないこと（NTFS の case-insensitive 対策 / 4c-0 (b) と同型）。"""
    assert dc.dist_location(".claude/Hooks/pre-tool-use.py") is None


# --- import 閉包 --------------------------------------------------------------------


def test_resolve_imports_finds_package_modules(tmp_path):
    root = tmp_path
    (root / "pkg").mkdir()
    (root / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (root / "pkg" / "mod.py").write_text("VALUE = 1\n", encoding="utf-8")
    (root / "sibling.py").write_text("X = 1\n", encoding="utf-8")
    entry = root / "entry.py"
    entry.write_text(
        "import sys\nfrom pkg.mod import VALUE\nimport sibling\nimport json\n",
        encoding="utf-8",
    )
    found = dc.resolve_imports(entry, root, [root])
    assert "pkg/mod.py" in found
    assert "pkg/__init__.py" in found, "パッケージの __init__.py も閉包に入る"
    assert "sibling.py" in found
    assert not any(f.startswith("json") for f in found), "標準ライブラリは閉包に入れない"


def test_resolve_imports_tolerates_unparsable_file(tmp_path):
    """構文エラーで**落ちない**こと（計器が沈黙するより、その 1 件を諦める）。"""
    broken = tmp_path / "broken.py"
    broken.write_text("def (:\n", encoding="utf-8")
    assert dc.resolve_imports(broken, tmp_path, [tmp_path]) == set()


# --- 実行時データ依存 ---------------------------------------------------------------


def test_runtime_data_deps_finds_literal_data_paths(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "patterns.yaml").write_text("a: 1\n", encoding="utf-8")
    src = tmp_path / "reader.py"
    src.write_text(
        'PATTERNS = "docs/patterns.yaml"\nOTHER = "docs/missing.yaml"\nN = 3\n',
        encoding="utf-8",
    )
    deps = dc.runtime_data_deps(src, tmp_path)
    assert deps == {"docs/patterns.yaml"}, "実在しない文字列は依存として数えない"


def test_runtime_data_deps_ignores_docstrings(tmp_path):
    """**docstring は実行時依存ではない**（provenance の記述であって読み込みではない）。

    初版はこれを数えたため、gap に `docs/specs/**` が 20 件以上並んだ ——
    実体は「hook の docstring が仕様書を参照している」だけだった。
    4c-0 で直した `py-fixture` の偽の理由と**同じ型の誤り**である。
    """
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "spec.md").write_text("x\n", encoding="utf-8")
    (tmp_path / "docs" / "data.yaml").write_text("a: 1\n", encoding="utf-8")
    src = tmp_path / "reader.py"
    src.write_text(
        '"""仕様は docs/spec.md にある。"""\n'
        'PATTERNS = "docs/data.yaml"\n'
        "def f():\n"
        '    """詳細は docs/spec.md 参照。"""\n'
        "    return 1\n",
        encoding="utf-8",
    )
    assert dc.runtime_data_deps(src, tmp_path) == {"docs/data.yaml"}


def test_runtime_data_deps_follows_path_division(tmp_path):
    """`root / "docs" / "artifacts" / "x.yaml"` の**組み立て**を辿れること。

    これが拾えないと `incident-patterns.yaml` が見えない —— ADR-0010 追補 4 が
    「fail-open を黙認しない」と書いた当の依存であり、**単一リテラルでは書かれていない**。
    """
    (tmp_path / "docs" / "artifacts").mkdir(parents=True)
    (tmp_path / "docs" / "artifacts" / "incident-patterns.yaml").write_text("a: 1\n", encoding="utf-8")
    src = tmp_path / "hook.py"
    src.write_text(
        "from pathlib import Path\n"
        "def f(project_root):\n"
        '    return project_root / "docs" / "artifacts" / "incident-patterns.yaml"\n',
        encoding="utf-8",
    )
    assert dc.runtime_data_deps(src, tmp_path) == {"docs/artifacts/incident-patterns.yaml"}


def test_runtime_data_deps_ignores_runtime_artifacts(tmp_path):
    """実行時生成物は「配る対象」ではない（census の除外規則を**再利用**する）。"""
    (tmp_path / ".claude" / "logs").mkdir(parents=True)
    (tmp_path / ".claude" / "logs" / "permission.log").write_text("", encoding="utf-8")
    src = tmp_path / "writer.py"
    src.write_text('LOG = ".claude/logs/permission.log"\n', encoding="utf-8")
    assert dc.runtime_data_deps(src, tmp_path) == set()


def test_runtime_data_deps_excludes_python_sources(tmp_path):
    """`.py` は import 閉包の担当であり、データ依存として二重に数えない。"""
    (tmp_path / "other.py").write_text("", encoding="utf-8")
    src = tmp_path / "reader.py"
    src.write_text('P = "other.py"\n', encoding="utf-8")
    assert dc.runtime_data_deps(src, tmp_path) == set()


# --- フェンス内のエントリポイント ---------------------------------------------------


def test_fence_entry_points_resolve_syspath_imports(tmp_path):
    """`sys.path.insert` + `import` の形から**実体**を導けること。

    これが設計の見落としだった —— フェンス内のパストークンは `.claude/hooks` という
    ディレクトリでしかなく、実際に名指しされている実体は `analyzers.chunker` である。
    """
    hooks = tmp_path / ".claude" / "hooks" / "analyzers"
    hooks.mkdir(parents=True)
    (hooks / "__init__.py").write_text("", encoding="utf-8")
    (hooks / "chunker.py").write_text("", encoding="utf-8")
    doc = tmp_path / "skill.md"
    doc.write_text(
        "本文\n\n```bash\n"
        "bash .claude/scripts/py_invoke.sh -c \"\n"
        "import sys; sys.path.insert(0, '.claude/hooks')\n"
        "from analyzers.chunker import chunk_file\n"
        '"\n'
        "```\n",
        encoding="utf-8",
    )
    found = dc.fence_entry_points(doc, tmp_path)
    assert ".claude/hooks/analyzers/chunker.py" in found
    assert ".claude/hooks/analyzers/__init__.py" in found


def test_fence_entry_points_ignore_runtime_artifacts(tmp_path):
    """ディレクトリ図やログの言及を配布対象にしない（同じ除外規則を通す）。"""
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "tdd-patterns.log").write_text("", encoding="utf-8")
    doc = tmp_path / "skill.md"
    doc.write_text("```\n.claude/tdd-patterns.log — パターン記録\n```\n", encoding="utf-8")
    assert dc.fence_entry_points(doc, tmp_path) == {}


def test_fence_entry_points_skip_directories(tmp_path):
    """ディレクトリはエントリポイントにしない（実体ではないため）。"""
    (tmp_path / ".claude" / "hooks").mkdir(parents=True)
    doc = tmp_path / "skill.md"
    doc.write_text("```bash\nls .claude/hooks\n```\n", encoding="utf-8")
    assert dc.fence_entry_points(doc, tmp_path) == {}


# --- 実リポジトリでの導出 -----------------------------------------------------------


def test_hook_entry_points_come_from_hooks_json():
    """配布 hooks のエントリポイントは `hooks.json` の実測から採ること（列挙しない）。"""
    entries = dc.hook_entry_points()
    assert ".claude/hooks/pre-tool-use.py" in entries
    assert ".claude/scripts/py_invoke.sh" in entries, "py_invoke.sh も hooks.json が名指しする"
    assert len(entries) >= 4


def test_closure_contains_its_entry_points():
    entries = dc.entry_points()
    closed = dc.closure(entries)
    assert entries, "エントリポイントが 0 件なら導出は失敗（緑と誤認しない）"
    for e in entries:
        assert e in closed, f"エントリポイント {e} が閉包に含まれていない"
    assert len(closed) > len(entries), "到達関係が 1 件も辿れていない"


def test_gap_is_exactly_the_unshipped_part_of_the_closure():
    """gap = 閉包 − 配布集合。**gap の各要素は配布先を持たない**ことが定義。"""
    closed = dc.closure(dc.entry_points())
    gap = dc.gap(closed)
    assert set(gap) <= set(closed)
    for dev_rel in gap:
        assert dc.dist_location(dev_rel) is None
    for dev_rel in set(closed) - set(gap):
        assert dc.dist_location(dev_rel) is not None


def test_closure_stays_inside_the_repo():
    """閉包はリポジトリ相対パスのみで構成されること（作者環境の絶対パスが混じらない）。"""
    for dev_rel in dc.closure(dc.entry_points()):
        assert not Path(dev_rel).is_absolute()
        assert ".." not in dev_rel.split("/")
        assert (REPO_ROOT / dev_rel).exists(), f"{dev_rel} は実在しない"


def test_resolve_imports_handles_from_package_import_module(tmp_path):
    """`from . import mod` / `from pkg import mod` の形を解決できること。

    **初版はこれを取り逃していた** —— `ast.ImportFrom` の `node.module` は
    `from . import static_assets` では **None** であり、モジュール名は `names` 側にある。
    実測: `.claude/scripts/dashboard/builder.py:36` がこの形で `static_assets` を引き、
    そこから `_radix_colors` へ繋がる枝が**閉包から丸ごと落ちていた**。
    配布集合が実際より小さくなる = 配ったのに動かない形である。
    """
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "leaf.py").write_text("", encoding="utf-8")
    (pkg / "entry.py").write_text("from . import leaf\n", encoding="utf-8")
    found = dc.resolve_imports(pkg / "entry.py", tmp_path, [tmp_path])
    assert "pkg/leaf.py" in found

    (tmp_path / "top.py").write_text("from pkg import leaf\n", encoding="utf-8")
    found2 = dc.resolve_imports(tmp_path / "top.py", tmp_path, [tmp_path])
    assert "pkg/leaf.py" in found2, "from pkg import mod もモジュール参照でありうる"


def test_fence_entry_points_recognize_both_syspath_forms(tmp_path):
    """`sys.path.insert(...)` と `sys.path[:0] = [...]` の**両方**を認識すること。

    4c-1 の codemod で配布 skill を後者の形へ書き換えた直後、計器が前者しか知らず
    **閉包が 18 → 11 に縮んだ**（計器が自分の測定対象に追随していなかった）。
    宣言が実際より小さくなる形であり、gabriel rubric #4 が狙う欠陥そのもの。
    """
    pkg = tmp_path / ".claude" / "hooks" / "analyzers"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "chunker.py").write_text("", encoding="utf-8")
    doc = tmp_path / "skill.md"
    doc.write_text(
        "```bash\n"
        "bash x -c \"\n"
        "import sys, os; _r = r'${CLAUDE_PLUGIN_ROOT}' or ''; "
        "sys.path[:0] = ([_r, _r + '/hooks'] if _r else []) + ['.claude/hooks']\n"
        "from analyzers.chunker import chunk_file\n"
        '"\n'
        "```\n",
        encoding="utf-8",
    )
    found = dc.fence_entry_points(doc, tmp_path)
    assert ".claude/hooks/analyzers/chunker.py" in found


def test_dist_location_maps_analyzers_to_plugin_root():
    """analyzers は **plugin 直下**に配布される（`hooks/` 配下ではない）。

    hooks/ 配下に置くと T3 の積集合に入り、開発側 `tests/` 22 件が非対称違反になる
    （gabriel 2026-09-07 実測 / 2026-09-08 に L1 が `_iter_mirror_matches` を実読して裏づけた）。
    **前方一致は長い方を先に試す**ことが要件である。
    """
    assert dc.dist_location(".claude/hooks/analyzers/chunker.py") == (
        "plugins/lam-harness/analyzers/chunker.py"
    )
    assert dc.dist_location(".claude/hooks/analyzers/graph/scc.py") == (
        "plugins/lam-harness/analyzers/graph/scc.py"
    )
    # hooks 本体は従来どおり hooks/ 配下
    assert dc.dist_location(".claude/hooks/pre-tool-use.py") == (
        "plugins/lam-harness/hooks/pre-tool-use.py"
    )
    # 開発側だけの `tests/` は配布されない（片側無視の対象）
    assert dc.dist_location(".claude/hooks/analyzers/tests/test_e2e_review.py") is None


def test_fence_entry_points_mark_guarded_commands_as_conditional(tmp_path):
    """`[ -f X ] &&` / `[ -d X ] &&` で守られた呼び出しは**硬い依存ではない**こと。

    ADR-0010 追補 4 は「配られるか、**その不在時の挙動が仕様として明示されている**か」を
    要求する。`[ -f X ]` ガードは**その仕様を実行可能な形で書いたもの**であり、
    prose の「LAM 開発時のみ」より強い。文意判定ではなく**構文**で切れる。
    """
    (tmp_path / ".claude" / "scripts").mkdir(parents=True)
    (tmp_path / ".claude" / "scripts" / "only_dev.py").write_text("", encoding="utf-8")
    doc = tmp_path / "skill.md"
    doc.write_text(
        "```bash\n"
        "[ -f .claude/scripts/only_dev.py ] && python .claude/scripts/only_dev.py || echo skip\n"
        "```\n",
        encoding="utf-8",
    )
    found = dc.fence_entry_points(doc, tmp_path)
    assert ".claude/scripts/only_dev.py" not in found, "ガード付きは硬い依存に数えない"


def test_fallback_map_matches_the_hook():
    """ファイル単位のフォールバック写像が、**hook の実際の解決と一致**すること。

    計器と実装がずれると、計器は「配ってある」と嘘をつく。
    `resolve_incident_yaml` が `${CLAUDE_PLUGIN_ROOT}/hooks/incident-patterns.yaml` を
    見に行くことを、hook の実文と突き合わせて固定する。
    """
    hook = (REPO_ROOT / "plugins" / "lam-harness" / "hooks" / "pre-tool-use.py").read_text(
        encoding="utf-8"
    )
    assert "def resolve_incident_yaml" in hook
    for dev_rel, plugin_rel in dc._FALLBACK_MAP:
        tail = plugin_rel.split("/", 1)[1]
        assert f'"{tail}"' in hook or f"'{tail}'" in hook, (
            f"hook が {plugin_rel} を見ていない（写像が実装とずれている）"
        )
        assert dc.dist_location(dev_rel) == f"plugins/lam-harness/{plugin_rel}"
