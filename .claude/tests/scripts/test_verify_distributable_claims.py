"""verify_distributable_claims.py テスト（2026-08-29 / セッション 27）.

配布物の「存在の主張」が実体と合っているかの検査。2 種類:

- **command**: 2026-07-13 の skill 削除 8 件のうち 6 件が配布物にコマンド名を残し、
  計 42 箇所が約 6 週間生存した
- **directory**: 空の `.claude/commands/` を機能として紹介する記載が、2026-08-27 に
  2 箇所修正されたあと 7 箇所残存していた（2 度の再発 / 人手チェックが機能しなかった実測）

本テストは陰性対照（実体のない主張を仕込んだ偽リポジトリで実際に落ちること）を
両検査について含む —— 「落ちない検査」は計器として無価値であるため。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import verify_distributable_claims as vdc  # noqa: E402
from verify_distributable_claims import (  # noqa: E402
    BUILTIN_COMMANDS,
    DIRECTORY_MENTION_EXCEPTIONS,
    EXCLUDED_FROM_SCAN,
    empty_claude_dirs,
    existing_commands,
    find_command_violations,
    find_directory_violations,
    find_violations,
    iter_distributables,
    main,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = SCRIPTS_DIR / "verify_distributable_claims.py"


def _fake_repo(
    root: Path,
    *,
    skills: list[str] | None = None,
    claude_dirs: dict[str, bool] | None = None,
    docs: dict[str, str] | None = None,
) -> Path:
    """偽リポジトリを組み立てる。claude_dirs は {名前: 中身を持つか}。"""
    for name in skills or []:
        (root / ".claude" / "skills" / name).mkdir(parents=True, exist_ok=True)
    for name, has_content in (claude_dirs or {}).items():
        d = root / ".claude" / name
        d.mkdir(parents=True, exist_ok=True)
        if has_content:
            (d / "placeholder.md").write_text("x", encoding="utf-8")
    for rel, text in (docs or {}).items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return root


# ==========================================================================
# 本番検査（実リポジトリ）
# ==========================================================================


def test_script_exists() -> None:
    assert SCRIPT_PATH.is_file()


def _is_starter(violation: dict) -> bool:
    return "/templates/starter/" in str(violation["file"])


def test_repository_has_no_phantom_commands() -> None:
    """starter 以外の配布物に phantom は無い（移行中も検出力を落とさない）。

    starter を除くのは、plugin 移行 P2 完了までそこに前方参照が残るためである。
    ここで starter ごと赤にすると「赤 1 件は既知」という運用が生まれ、
    **他領域に新しい phantom が入っても気づかなくなる**（`code-quality-guideline.md`
    が警戒する「常時鳴る計器は殺される」型）。starter 側は下の xfail が受け持つ。
    """
    violations = [v for v in find_command_violations(REPO_ROOT) if not _is_starter(v)]
    assert violations == [], "実在しないコマンドの提示: " + "; ".join(
        f"{v['file']}:{v['line']} {v['subject']}" for v in violations
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "plugin 移行 P2 完了まで starter は /lam-harness:{building,magi,ship,retro,"
        "quick-save,quick-load} を前方参照する（skills はまだ .claude/skills/ にある）。"
        "strict なので、P2 で解消した瞬間に xpass で落ちて本 mark の撤去を促す "
        "= 除外を書き忘れて機構が恒久的に盲目になる経路を持たない。"
    ),
)
def test_starter_has_no_phantom_commands() -> None:
    violations = [v for v in find_command_violations(REPO_ROOT) if _is_starter(v)]
    assert violations == [], "実在しないコマンドの提示: " + "; ".join(
        f"{v['file']}:{v['line']} {v['subject']}" for v in violations
    )


def test_repository_does_not_advertise_empty_directories() -> None:
    violations = find_directory_violations(REPO_ROOT)
    assert violations == [], "空ディレクトリの紹介: " + "; ".join(
        f"{v['file']}:{v['line']} {v['subject']}" for v in violations
    )


def test_distributables_are_derived_not_listed() -> None:
    names = {p.name for p in iter_distributables(REPO_ROOT)}
    for expected in ("README.md", "QUICKSTART.md", "CHEATSHEET.md", "CLAUDE.md"):
        assert expected in names, f"{expected} が検査対象に含まれていない"
    assert any(p.suffix == ".html" for p in iter_distributables(REPO_ROOT))


def test_existing_commands_derived_from_skills_dir() -> None:
    """実在コマンドは 2 経路とも実体から導出される（維持リストを持たない）。

    2026-09-04 に plugin 経路を追加した。project skill だけを期待すると、
    plugin skill が増えた瞬間にこの検査が落ちる（= 期待側が維持リストになる）ため、
    両経路とも実体から組み立てて突合する。
    """
    project = {
        p.name
        for p in (REPO_ROOT / ".claude" / "skills").iterdir()
        if p.is_dir() and not p.name.startswith("__")
    }
    plugin = {
        "{0}:{1}".format(plugin_dir.name, skill.name)
        for plugin_dir in (REPO_ROOT / "plugins").iterdir()
        if plugin_dir.is_dir()
        for skill in (plugin_dir / "skills").iterdir()
        if (plugin_dir / "skills").is_dir() and skill.is_dir()
    }
    assert plugin, "plugin skill が 1 件も導出されていない（経路が死んでいる）"
    assert existing_commands(REPO_ROOT) == project | plugin


def test_empty_dirs_derived_from_filesystem() -> None:
    """空判定は実体から導出される（維持リストを持たない）。"""
    empties = empty_claude_dirs(REPO_ROOT)
    for name in empties:
        d = REPO_ROOT / ".claude" / name
        assert d.is_dir()
        assert not vdc._has_content(d)


# ==========================================================================
# 除外の作法（理由必須）
# ==========================================================================


def test_every_file_exclusion_carries_a_reason() -> None:
    for name, reason in EXCLUDED_FROM_SCAN.items():
        assert reason and reason.strip(), f"{name} の除外に理由がない"
        assert len(reason) >= 20, f"{name} の除外理由が短すぎる"


def test_every_directory_exception_carries_a_reason() -> None:
    for name, reason in DIRECTORY_MENTION_EXCEPTIONS.items():
        assert reason and reason.strip(), f"{name} の例外に理由がない"
        assert len(reason) >= 20, f"{name} の例外理由が短すぎる"


def test_changelog_is_excluded() -> None:
    assert "CHANGELOG.md" in EXCLUDED_FROM_SCAN
    assert "CHANGELOG.md" not in {p.name for p in iter_distributables(REPO_ROOT)}


def test_directory_exceptions_are_runtime_generated_only() -> None:
    """例外は「実行時生成ゆえに空でありうる」ものに限る（機能の不在を隠さない）。"""
    for name, reason in DIRECTORY_MENTION_EXCEPTIONS.items():
        assert any(k in reason for k in ("実行時", "生成", "clone")), (
            f"{name} の例外理由が実行時生成に基づいていない: {reason}"
        )
        assert name != "commands", "commands/ を例外にすると本機構の存在理由が消える"


# ==========================================================================
# 陰性対照 — command
# ==========================================================================


def test_detects_phantom_command(tmp_path: Path) -> None:
    root = _fake_repo(
        tmp_path,
        skills=["building"],
        docs={"README.md": "Use `/building` to start.\nThen run `/ghost` to finish.\n"},
    )
    violations = find_command_violations(root)
    assert len(violations) == 1
    assert violations[0]["subject"] == "/ghost"
    assert violations[0]["line"] == 2


def test_accepts_existing_command(tmp_path: Path) -> None:
    root = _fake_repo(
        tmp_path,
        skills=["building", "retro"],
        docs={"README.md": "`/building` and `/retro [wave|phase]`\n"},
    )
    assert find_command_violations(root) == []


def test_detects_phantom_in_html_slides(tmp_path: Path) -> None:
    root = _fake_repo(
        tmp_path,
        skills=["building"],
        docs={"docs/slides/intro.html": "<p>Use <code>/vanished</code> here</p>\n"},
    )
    assert [v["subject"] for v in find_command_violations(root)] == ["/vanished"]


def test_path_like_tokens_are_not_commands(tmp_path: Path) -> None:
    """`/etc/...` `/absolute/path/...` はコマンドではない（直後が `/`）。"""
    root = _fake_repo(
        tmp_path,
        skills=["building"],
        docs={
            "README.md": (
                "See `/etc/claude-code/managed-settings.json` and "
                "`/absolute/path/to/your/project`.\n"
            )
        },
    )
    assert find_command_violations(root) == []


def test_builtin_commands_are_accepted(tmp_path: Path) -> None:
    root = _fake_repo(tmp_path, docs={"README.md": "Run `/model` or `/config`.\n"})
    assert find_command_violations(root) == []
    assert "model" in BUILTIN_COMMANDS


# ==========================================================================
# 陰性対照 — directory
# ==========================================================================


def test_detects_empty_directory_in_tree_diagram(tmp_path: Path) -> None:
    """2026-08-29 に見落とした形そのもの（ASCII ツリー内の記載）。"""
    root = _fake_repo(
        tmp_path,
        claude_dirs={"commands": False, "skills": True},
        docs={
            "CHEATSHEET.md": (
                "```\n.claude/\n"
                "├── commands/              # スラッシュコマンド\n"
                "├── skills/                # スキル\n"
                "```\n"
            )
        },
    )
    violations = find_directory_violations(root)
    assert len(violations) == 1
    assert violations[0]["subject"] == ".claude/commands/"
    assert violations[0]["line"] == 3


def test_detects_empty_directory_in_table_row(tmp_path: Path) -> None:
    root = _fake_repo(
        tmp_path,
        claude_dirs={"commands": False},
        docs={"QUICKSTART_en.md": "| `.claude/commands/` | Phase controls |\n"},
    )
    assert [v["subject"] for v in find_directory_violations(root)] == [".claude/commands/"]


def test_detects_empty_directory_in_html_slide(tmp_path: Path) -> None:
    root = _fake_repo(
        tmp_path,
        claude_dirs={"commands": False},
        docs={"docs/slides/architecture.html": "&boxvr; commands/&nbsp;&larr; Slash<br>\n"},
    )
    assert len(find_directory_violations(root)) == 1


def test_non_empty_directory_is_fine(tmp_path: Path) -> None:
    root = _fake_repo(
        tmp_path,
        claude_dirs={"skills": True},
        docs={"README.md": "See `.claude/skills/` for details.\n"},
    )
    assert find_directory_violations(root) == []


def test_excepted_directory_may_be_mentioned_while_empty(tmp_path: Path) -> None:
    """実行時生成ディレクトリ（例外登録済）は空でも紹介してよい。"""
    root = _fake_repo(
        tmp_path,
        claude_dirs={"logs": False},
        docs={"README.md": "Runtime logs land in `.claude/logs/`.\n"},
    )
    assert find_directory_violations(root) == []
    assert "logs" in DIRECTORY_MENTION_EXCEPTIONS


def test_directory_check_ignores_similarly_named_paths(tmp_path: Path) -> None:
    """`docs/commands/` のような別の場所は `.claude/commands/` の主張ではない。"""
    root = _fake_repo(
        tmp_path,
        claude_dirs={"commands": False},
        docs={"README.md": "See `docs/other/commands/` elsewhere.\n"},
    )
    assert find_directory_violations(root) == []


def test_excluded_file_is_not_scanned(tmp_path: Path) -> None:
    root = _fake_repo(
        tmp_path,
        skills=["building"],
        claude_dirs={"commands": False},
        docs={"CHANGELOG.md": "Removed `/planning` and emptied commands/ in v5.0.0.\n"},
    )
    assert find_violations(root) == []


# ==========================================================================
# CLI
# ==========================================================================


def test_main_exits_zero_when_clean(tmp_path: Path, capsys) -> None:
    root = _fake_repo(tmp_path, skills=["building"], docs={"README.md": "`/building`\n"})
    assert main(["--root", str(root), "--exit-nonzero-on-drift"]) == 0
    assert "OK" in capsys.readouterr().out


def test_main_exits_nonzero_on_command_drift(tmp_path: Path, capsys) -> None:
    root = _fake_repo(tmp_path, skills=["building"], docs={"README.md": "`/ghost`\n"})
    assert main(["--root", str(root), "--exit-nonzero-on-drift"]) == 1
    assert "/ghost" in capsys.readouterr().out


def test_main_exits_nonzero_on_directory_drift(tmp_path: Path, capsys) -> None:
    root = _fake_repo(
        tmp_path,
        claude_dirs={"commands": False},
        docs={"README.md": "`.claude/commands/`\n"},
    )
    assert main(["--root", str(root), "--exit-nonzero-on-drift"]) == 1
    assert "directory" in capsys.readouterr().out


def test_main_without_flag_exits_zero_even_on_drift(tmp_path: Path) -> None:
    root = _fake_repo(tmp_path, skills=["building"], docs={"README.md": "`/ghost`\n"})
    assert main(["--root", str(root)]) == 0


def test_main_json_output(tmp_path: Path, capsys) -> None:
    root = _fake_repo(tmp_path, skills=["building"], docs={"README.md": "`/ghost`\n"})
    main(["--root", str(root), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["violations"][0]["subject"] == "/ghost"
    assert payload["skills"] == ["building"]


def test_module_docstring_records_both_contexts() -> None:
    """機構は「なぜ要るか」を持つ（沈黙したときに読み返せるように）。"""
    assert vdc.__doc__ is not None
    assert "2026-07-13" in vdc.__doc__
    assert "2026-08-27" in vdc.__doc__


def test_directory_scope_is_limited_to_claude(tmp_path: Path) -> None:
    """`src/` `tests/` 等のテンプレート枠へ射程を広げない（2026-08-27 D-2 の決着）。"""
    root = _fake_repo(
        tmp_path,
        claude_dirs={"skills": True},
        docs={"README.md": "Put your code in `src/` and tests in `tests/`.\n"},
    )
    assert find_directory_violations(root) == []
    assert "D-2" in vdc.__doc__


# ---- 名前空間つき plugin コマンド（2026-09-04 / 手順 3） ----
#
# plugin skill は `/lam-harness:init` の形で起動する（上流仕様 / V1 実測）。
# 拡張前の `_COMMAND_PAT` は `:` の手前で切れるため `/lam-harness` を誤抽出し、
# 「そんな skill は無い」という**偽陽性**を出していた。


def test_namespaced_plugin_command_resolves_to_plugin_dir(tmp_path: Path) -> None:
    """`/plugin:skill` は plugins/<plugin>/skills/<skill>/ で解決する（陽性）。"""
    root = tmp_path
    (root / "plugins" / "lam-harness" / "skills" / "init").mkdir(parents=True)
    (root / ".claude" / "skills" / "building").mkdir(parents=True)
    (root / "README.md").write_text("Run `/lam-harness:init` first.\n", encoding="utf-8")
    assert find_command_violations(root) == []


def test_namespaced_command_with_missing_skill_is_reported(tmp_path: Path) -> None:
    """plugin 側に実体が無ければ落ちる（陰性対照）。"""
    root = tmp_path
    (root / "plugins" / "lam-harness" / "skills" / "init").mkdir(parents=True)
    (root / "README.md").write_text("Run `/lam-harness:ghost`.\n", encoding="utf-8")
    violations = find_command_violations(root)
    assert [v["subject"] for v in violations] == ["/lam-harness:ghost"]


def test_namespaced_command_is_not_truncated_at_colon(tmp_path: Path) -> None:
    """`/lam-harness:init` から `/lam-harness` を誤抽出しない（拡張前の実際の欠陥）。"""
    root = tmp_path
    (root / "plugins" / "lam-harness" / "skills" / "init").mkdir(parents=True)
    (root / "README.md").write_text("`/lam-harness:init`\n", encoding="utf-8")
    subjects = [v["subject"] for v in find_command_violations(root)]
    assert "/lam-harness" not in subjects, "コロンの手前で切って誤抽出している"


def test_unknown_plugin_namespace_is_reported(tmp_path: Path) -> None:
    """存在しない plugin 名の名前空間も落ちる（陰性対照）。"""
    root = tmp_path
    (root / "README.md").write_text("`/nope:init`\n", encoding="utf-8")
    subjects = [v["subject"] for v in find_command_violations(root)]
    assert subjects == ["/nope:init"]


# ==========================================================================
# plugin templates の走査（2026-09-05 / P1(1) 予行で発見した射程漏れ）
#
# 配布物の集合が plugin 側（templates/starter/）へ広がったのに、走査の起点だけが
# project ルート + docs/ のままだった。starter は `/lam-harness:init` が利用者の
# プロジェクトへ敷くファイルであり、まさに本機構が守る「配布物」である。
# 実測: starter が `/lam-harness:building` 他 6 件の不在コマンドを名乗っていたが、
# 検査は 2 passed（緑）のままだった。
# ==========================================================================


def test_starter_templates_are_scanned(tmp_path: Path) -> None:
    """plugin の starter テンプレートが走査対象に入る（陽性）。"""
    root = tmp_path
    (root / "plugins" / "lam-harness" / "skills" / "init").mkdir(parents=True)
    starter = root / "plugins" / "lam-harness" / "templates" / "starter"
    (starter / "dot-claude").mkdir(parents=True)
    (starter / "dot-claude" / "current-phase.md").write_text(
        "BUILDING へ移るときは `/lam-harness:ghost` を実行する。\n", encoding="utf-8"
    )
    subjects = [v["subject"] for v in find_command_violations(root)]
    assert subjects == ["/lam-harness:ghost"], (
        "starter テンプレートが走査対象に入っていない（射程漏れ）"
    )


def test_managed_templates_are_not_scanned(tmp_path: Path) -> None:
    """managed テンプレートは走査しない（陰性対照）。

    managed は project 側の実体（`.claude/rules/` と `docs/internal/`）の複製であり、
    恒等性は R3 機構 #11 が強制する。ここを走査すると同一の違反を二重に報告するか、
    project 側で未走査の領域（`.claude/rules/`）を複製経由で暗黙に走査対象へ
    引き込むことになる。射程を広げるなら project 側の起点として明示的に決める。
    """
    root = tmp_path
    managed = root / "plugins" / "lam-harness" / "templates" / "managed" / "rules"
    managed.mkdir(parents=True)
    (managed / "phase-rules.md").write_text("`/ghost` を使う。\n", encoding="utf-8")
    assert find_command_violations(root) == []


def test_real_starter_templates_are_in_scope() -> None:
    """実リポジトリの starter が実際に走査対象へ入っている。"""
    scanned = {str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in iter_distributables(REPO_ROOT)}
    assert any(
        p.startswith("plugins/") and "/templates/starter/" in p for p in scanned
    ), "実リポジトリの starter が 1 件も走査されていない"
