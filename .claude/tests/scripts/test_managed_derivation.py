"""T1 = 配布テンプレートの導出（Action 4b / 2026-09-06 / セッション 34）.

**なぜ要るか**: T1（`.claude/rules` `docs/internal` `.claude/scripts` → `templates/managed/`）は
2026-09-06 まで **生成器を持たず検査だけがあった** —— 「同じ内容を 2 人が書き、検査で一致を
強制する」形のまま残っていた。HGA #33 が T3 について解体した形が、**向きが逆であるという理由
だけで温存されていた**。

**ADR-0010 追補 3** により、不変条件は「正本側に bare が残っていないこと」から
「**配布される側**に bare の実行参照が残っていないこと」へ一般化された。
T3 では配布側が正本、T1 では配布側が派生である。

**陰性対照を含む** —— 落ちない検査は計器として無価値。
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from verify_plugin_containment import (  # noqa: E402
    check_managed_identity,
    component_names,
    derive_managed_text,
    plugin_namespace,
    skill_names,
    invert_managed_text,
    to_project_text,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_DIR = REPO_ROOT / "plugins" / "lam-harness"

NS = "lam-harness:"
AGENTS = {"gabriel", "quality-auditor"}
SKILLS = {"ship", "retro", "full-review", "building"}


# --- 導出規則 ------------------------------------------------------------------------


def test_markdown_is_transformed():
    out = derive_managed_text(
        Path("a.md"), "`/ship` の後に gabriel を起動する", NS, AGENTS, SKILLS
    )
    assert out == "`/lam-harness:ship` の後に lam-harness:gabriel を起動する"


def test_non_markdown_is_copied_verbatim():
    """`.py` / `.sh` は実行されるコードであり、コメントの読者は開発者である。

    実測: managed scripts の slash 形は docstring・コメントの 7 箇所のみで実行参照 0。
    ここを変換すると、配布された Python のコメントだけが名前空間つきになる。
    """
    src = '"""/ship で使う。gabriel を呼ぶ。"""\n'
    assert derive_managed_text(Path("x.py"), src, NS, AGENTS, SKILLS) == src
    assert derive_managed_text(Path("x.sh"), src, NS, AGENTS, SKILLS) == src


def test_derivation_is_idempotent():
    once = derive_managed_text(Path("a.md"), "/ship と gabriel", NS, AGENTS, SKILLS)
    assert derive_managed_text(Path("a.md"), once, NS, AGENTS, SKILLS) == once


def test_output_template_fence_is_untouched():
    """除外 (T) は T1 でも効く。ここを変換すると `magi_dispatch.py` の emit と食い違う。"""
    src = "```markdown\n### gabriel probe\n実行: /ship\n```\n"
    assert derive_managed_text(Path("a.md"), src, NS, AGENTS, SKILLS) == src


# --- 往復恒等（**LAM 本体が壊れないことの証明**）------------------------------------


def test_round_trip_returns_canonical_exactly():
    """`to_project_text(導出(x)) == x` —— 付与した prefix が過不足なく剥がせること。

    これが成り立つ限り、導出は正本の情報を 1 ビットも失わない。`.claude/` 正本は
    1 バイトも変わらないため、LAM 本体（plugin disabled で `.claude/` を読む）は無影響である。
    """
    src = (
        "`/ship` と gabriel と quality-auditor\n"
        "```markdown\n### gabriel probe\n```\n"
        "`gabriel.md` を読む / docs/full-review/x.md\n"
    )
    every = AGENTS | SKILLS
    derived = derive_managed_text(Path("a.md"), src, NS, AGENTS, SKILLS)
    assert to_project_text(derived, NS, every) == src


def test_round_trip_holds_for_every_real_managed_file():
    """本番の全 managed ファイルで往復恒等が成り立つこと（生成器が使う不変条件そのもの）。"""
    sys.path.insert(0, str(SCRIPTS_DIR))
    import derive_managed_templates as dmt

    ns = plugin_namespace(PLUGIN_DIR)
    every = component_names(PLUGIN_DIR)
    from verify_plugin_containment import _MANAGED_AREAS, _iter_text_files, _read

    checked = 0
    for area, dev_dir in _MANAGED_AREAS.items():
        area_root = PLUGIN_DIR / "templates" / "managed" / area
        if not area_root.is_dir():
            continue
        for template in _iter_text_files(area_root):
            rel = template.relative_to(area_root)
            source = REPO_ROOT / dev_dir / rel
            if not source.is_file():
                continue
            canonical = _read(source)
            derived = dmt.derive_managed_text(
                rel, canonical, ns, dmt.agent_names(PLUGIN_DIR), skill_names(PLUGIN_DIR)
            )
            assert invert_managed_text(rel, derived, ns, every) == canonical, rel.as_posix()
            checked += 1
    assert checked >= 30, f"検査対象が少なすぎる（{checked} 件）= 探索の失敗を緑と誤認しないため"


# --- 陰性対照 ------------------------------------------------------------------------


def _fake_repo(tmp_path: Path, *, canonical: str, template: str) -> Path:
    root = tmp_path / "repo"
    plugin = root / "plugins" / "lam-harness"
    (plugin / ".claude-plugin").mkdir(parents=True)
    (plugin / ".claude-plugin" / "plugin.json").write_text(
        '{"name": "lam-harness"}', encoding="utf-8"
    )
    (plugin / "agents").mkdir(parents=True)
    (plugin / "agents" / "gabriel.md").write_text("---\nname: gabriel\n---\n", encoding="utf-8")
    (plugin / "skills" / "ship").mkdir(parents=True)
    (plugin / "skills" / "ship" / "SKILL.md").write_text("---\nname: ship\n---\n", encoding="utf-8")
    (plugin / "templates" / "managed" / "rules").mkdir(parents=True)
    (plugin / "templates" / "managed" / "rules" / "r.md").write_text(template, encoding="utf-8")
    (root / ".claude" / "rules").mkdir(parents=True)
    (root / ".claude" / "rules" / "r.md").write_text(canonical, encoding="utf-8")
    return root


def test_negative_control_bare_template_is_reported(tmp_path):
    """配布側が bare のまま（= 旧来のバイト恒等）だと赤くなること。

    **これが本 Action の中核**である。バイト恒等のままでは、配布された規範が
    `/ship` と書き、利用者環境で同名の personal / project skill を起動しうる。
    """
    root = _fake_repo(tmp_path, canonical="/ship を実行\n", template="/ship を実行\n")
    violations = check_managed_identity(root)
    assert [v.check for v in violations] == ["T1"]
    assert "導出結果と一致しない" in violations[0].detail


def test_positive_control_derived_template_is_clean(tmp_path):
    """偽陽性の対照 —— 正しく導出されていれば緑。**正本は bare のままが正しい**。"""
    root = _fake_repo(
        tmp_path, canonical="/ship を実行\n", template="/lam-harness:ship を実行\n"
    )
    assert check_managed_identity(root) == []


def test_negative_control_over_namespaced_canonical_is_reported(tmp_path):
    """正本まで ns 化してしまった場合も赤くなること（**LAM 本体が壊れる方向の対照**）。

    ADR-0010 追補 3 が禁じたのは「配布される側の bare」であって、
    正本を ns 化することではない。正本を ns 化すると導出で二重にはならないが、
    **LAM 自身が `/lam-harness:ship` を打つことになり動かない**。
    """
    root = _fake_repo(
        tmp_path, canonical="/lam-harness:ship を実行\n", template="/ship を実行\n"
    )
    assert [v.check for v in check_managed_identity(root)] == ["T1"]


def test_missing_counterpart_is_reported(tmp_path):
    """開発側に対応物が無い派生は違反（既存 T1 の挙動を維持していること）。"""
    root = _fake_repo(tmp_path, canonical="x\n", template="x\n")
    (root / ".claude" / "rules" / "r.md").unlink()
    violations = check_managed_identity(root)
    assert any("開発側に対応物がない" in v.detail for v in violations)


# --- 実リポジトリ --------------------------------------------------------------------


def test_real_managed_templates_match_derivation():
    """本番の配布テンプレートが正本からの導出結果と一致すること（再混入防止 gate）。"""
    assert check_managed_identity(REPO_ROOT) == []
