"""verify_plugin_containment.py テスト（2026-09-04 / セッション 28）.

R3 機構 #11（T1 包含）/ #12（T2 閉包）。

**なぜ要るか**: `lam-harness` 1.0.0（2026-07-02 / 別リポジトリ配置）は skills 14 件のうち
9 件が現行 LAM に存在しない状態で 2 か月間放置された。K4「配布集合 ⊆ 開発ロード集合」は
**原則としては書かれていたが検査が無く、破れても誰も気づかなかった**。

本テストは陰性対照（違反を仕込んだ偽リポジトリで実際に落ちること）を両検査について含む
—— 「落ちない検査」は計器として無価値であるため（機構 #10 と同じ構え）。

**偽陽性の対照も含む**: T2 のドライブレター検出は URL（`https://`）と衝突しやすい。
`p:` `s:` を誤検出すると配布物のあらゆる参照が赤になるため、明示的に対照を置く。
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import verify_plugin_containment as vpc  # noqa: E402
from verify_plugin_containment import (  # noqa: E402
    check_hook_declaration,
    check_managed_identity,
    check_mirror_identity,
    check_reference_closure,
    main,
    verify,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def _fake_repo(tmp_path: Path, *, template_body: str, source_body: str | None) -> Path:
    """plugin テンプレートと開発側を持つ最小の偽リポジトリを作る。

    `source_body=None` のときは開発側の対応物を作らない（欠落の対照）。
    """
    tpl = tmp_path / "plugins" / "lam-harness" / "templates" / "managed" / "rules"
    tpl.mkdir(parents=True)
    # write_text は newline=None のため `\n` を os.linesep に再変換する（Windows で
    # "a\r\nb" が "a\r\r\nb" になる）。改行コードを検査する対照なのでバイトで書く。
    (tpl / "sample.md").write_bytes(template_body.encode("utf-8"))
    if source_body is not None:
        dev = tmp_path / ".claude" / "rules"
        dev.mkdir(parents=True)
        (dev / "sample.md").write_bytes(source_body.encode("utf-8"))
    return tmp_path


# --- 実リポジトリ ---------------------------------------------------------


def test_real_repo_has_no_violations():
    """実リポジトリが T1 / T2 を満たす。"""
    violations = verify(REPO_ROOT)
    assert violations == [], "\n".join(f"[{v.check}] {v.path} — {v.detail}" for v in violations)


def test_check_is_not_vacuous():
    """検査対象が 0 件なら「常に緑」になるため、実テンプレートの存在を要求する。

    機構 #10 と同じ構え —— 対象が消えたことを緑で報告する計器を作らない。
    """
    managed = REPO_ROOT / "plugins" / "lam-harness" / "templates" / "managed"
    assert managed.is_dir(), "managed テンプレートディレクトリが存在しない"
    files = [p for p in managed.rglob("*") if p.is_file()]
    assert len(files) >= 20, f"テンプレートが少なすぎる（{len(files)} 件）= 検査が空回りしている"


def test_t3_check_is_not_vacuous():
    """T3 の検査対象（両側一致エントリ）が実リポジトリで十分な件数あることを要求する。

    0 件なら「常に緑」になる（機構 #10 / test_check_is_not_vacuous と同じ構え）。
    """
    matched = list(vpc._iter_mirror_matches(REPO_ROOT))
    assert len(matched) >= 20, (
        f"複製相の一致エントリが少なすぎる（{len(matched)} 件）= 検査が空回りしている"
    )


def test_main_returns_zero_on_real_repo(capsys):
    assert main() == 0
    assert "OK" in capsys.readouterr().out


# --- T1 陰性対照 ----------------------------------------------------------


def test_t1_detects_content_drift(tmp_path):
    """テンプレートと開発側の内容が食い違えば検出する（= lam-harness 1.0.0 の事故）。"""
    repo = _fake_repo(tmp_path, template_body="old\n", source_body="new\n")
    violations = check_managed_identity(repo)
    assert len(violations) == 1
    assert violations[0].check == "T1"
    assert "内容が異なる" in violations[0].detail


def test_t1_detects_missing_source(tmp_path):
    """開発側に対応物が無ければ検出する（配布集合 ⊄ 開発ロード集合）。"""
    repo = _fake_repo(tmp_path, template_body="x\n", source_body=None)
    violations = check_managed_identity(repo)
    assert len(violations) == 1
    assert "開発側に対応物がない" in violations[0].detail


def test_t1_ignores_line_ending_difference(tmp_path):
    """CRLF/LF の差だけでは落ちない（Windows の git 変換で偽陽性を出さない）。"""
    repo = _fake_repo(tmp_path, template_body="a\r\nb\r\n", source_body="a\nb\n")
    assert check_managed_identity(repo) == []


# --- T3 陰性対照（複製相の恒等性） -----------------------------------------


def _mirror_repo(tmp_path: Path, *, plugin: dict, dev: dict, area: str = "skills") -> Path:
    """複製相（skills/agents）を持つ最小の偽リポジトリを作る。

    `plugin` / `dev` は {相対パス文字列: 内容} 形式。
    skills なら "skillname/SKILL.md"、agents なら "name.md" を渡す。
    write_bytes で書く（CRLF 対照のため改行コードを保持する / `_fake_repo` と同じ理由）。
    """
    plugin_root = tmp_path / "plugins" / "lam-harness" / area
    dev_root = tmp_path / ".claude" / area
    for rel, body in plugin.items():
        p = plugin_root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(body.encode("utf-8"))
    for rel, body in dev.items():
        p = dev_root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(body.encode("utf-8"))
    return tmp_path


def test_t3_detects_content_drift(tmp_path):
    """同名 skill の内容が食い違えば検出する（本 Task の発端となった事故と同型）。"""
    repo = _mirror_repo(
        tmp_path,
        plugin={"sample/SKILL.md": "old\n"},
        dev={"sample/SKILL.md": "new\n"},
    )
    violations = check_mirror_identity(repo)
    assert len(violations) == 1
    assert violations[0].check == "T3"
    assert "内容が異なる" in violations[0].detail


def test_t3_detects_missing_on_dev_side(tmp_path):
    """plugin 側にのみ存在するファイルが同名 skill 配下にあれば検出する。"""
    repo = _mirror_repo(
        tmp_path,
        plugin={"sample/SKILL.md": "x\n", "sample/references/extra.md": "y\n"},
        dev={"sample/SKILL.md": "x\n"},
    )
    violations = check_mirror_identity(repo)
    assert len(violations) == 1
    assert "開発側に対応物がない" in violations[0].detail


def test_t3_detects_missing_on_plugin_side(tmp_path):
    """開発側にのみ存在するファイルが同名 skill 配下にあれば検出する（未複製）。"""
    repo = _mirror_repo(
        tmp_path,
        plugin={"sample/SKILL.md": "x\n"},
        dev={"sample/SKILL.md": "x\n", "sample/references/extra.md": "y\n"},
    )
    violations = check_mirror_identity(repo)
    assert len(violations) == 1
    assert "plugin 側に複製されていない" in violations[0].detail


def test_t3_ignores_one_sided_entries(tmp_path):
    """片側にしか存在しない skill/agent は違反として報告しない（意図的な差分）。

    実例: 開発側のみの `build-dashboard`（非配布）/ `clause-gate`（LAM 固有）、
    plugin 側のみの `init`（plugin 専用）。ここを違反扱いにすると、意図的な非対称を
    毎回赤にする「常時落ちる計器」になり検査自体が殺される。
    """
    repo = _mirror_repo(
        tmp_path,
        plugin={"init/SKILL.md": "plugin only\n"},
        dev={"build-dashboard/SKILL.md": "dev only\n"},
    )
    assert check_mirror_identity(repo) == []


def test_t3_agent_files_are_compared_directly(tmp_path):
    """agents は単一ファイルの複製相なので、ディレクトリを経由せず直接比較する。"""
    repo = _mirror_repo(
        tmp_path,
        plugin={"test-runner.md": "old\n"},
        dev={"test-runner.md": "new\n"},
        area="agents",
    )
    violations = check_mirror_identity(repo)
    assert len(violations) == 1
    assert violations[0].check == "T3"
    assert "内容が異なる" in violations[0].detail


def test_t3_ignores_line_ending_difference(tmp_path):
    """CRLF/LF の差だけでは落ちない（T1 と同じ配慮）。"""
    repo = _mirror_repo(
        tmp_path,
        plugin={"sample/SKILL.md": "a\r\nb\r\n"},
        dev={"sample/SKILL.md": "a\nb\n"},
    )
    assert check_mirror_identity(repo) == []


def test_t3_matching_mirror_has_no_violations(tmp_path):
    """完全に一致する複製相は違反ゼロ（陽性対照）。"""
    repo = _mirror_repo(
        tmp_path,
        plugin={"sample/SKILL.md": "same\n", "sample/references/a.md": "b\n"},
        dev={"sample/SKILL.md": "same\n", "sample/references/a.md": "b\n"},
    )
    assert check_mirror_identity(repo) == []


# --- T2 陰性対照 ----------------------------------------------------------


def _closure_repo(tmp_path: Path, body: str) -> Path:
    d = tmp_path / "plugins" / "lam-harness"
    d.mkdir(parents=True)
    (d / "note.md").write_text(body, encoding="utf-8")
    return tmp_path


def test_t2_detects_windows_absolute_path(tmp_path):
    repo = _closure_repo(tmp_path, 'cwd="D:/work7/LivingArchitectModel"\n')
    violations = check_reference_closure(repo)
    assert len(violations) == 1
    assert violations[0].check == "T2"
    assert "絶対パス" in violations[0].detail


def test_t2_detects_backslash_absolute_path(tmp_path):
    repo = _closure_repo(tmp_path, r"see C:\Users\someone\knowledge\x.md" + "\n")
    assert len(check_reference_closure(repo)) == 1


def test_t2_detects_posix_home_path(tmp_path):
    repo = _closure_repo(tmp_path, "see /home/someone/notes.md\n")
    assert len(check_reference_closure(repo)) == 1


def test_t2_detects_non_distributed_reference(tmp_path):
    repo = _closure_repo(tmp_path, "詳細は docs/private/protocol.md を参照\n")
    violations = check_reference_closure(repo)
    assert len(violations) == 1
    assert "配布されないディレクトリ" in violations[0].detail


# --- T2 偽陽性の対照 ------------------------------------------------------


def test_t2_does_not_flag_urls(tmp_path):
    """URL のスキーム（`https:` の `s:`）をドライブレターと誤認しない。

    誤認すると配布物のあらゆる外部参照が赤になり、計器が殺される。
    """
    body = (
        "- https://code.claude.com/docs/en/plugins\n"
        "- http://example.com/a\n"
        "- file:///tmp/x\n"
    )
    assert check_reference_closure(_closure_repo(tmp_path, body)) == []


def test_t2_does_not_flag_project_relative_paths(tmp_path):
    """プロジェクト相対パス（利用者環境で解決される）は違反ではない。"""
    body = "`.claude/rules/phase-rules.md` と `docs/internal/06_DECISION_MAKING.md` を参照\n"
    assert check_reference_closure(_closure_repo(tmp_path, body)) == []


def test_t2_does_not_flag_plugin_root_variable(tmp_path):
    """`${CLAUDE_PLUGIN_ROOT}` 形式の参照は正しい書き方なので通す。"""
    body = 'bash "${CLAUDE_PLUGIN_ROOT}/scripts/py_invoke.sh" "${CLAUDE_PROJECT_DIR}/x.py"\n'
    assert check_reference_closure(_closure_repo(tmp_path, body)) == []


# --- 射程の明示 -----------------------------------------------------------


def test_t2_scope_v1_allows_record_references(tmp_path):
    """v1 の射程は意図的に狭い —— `docs/artifacts/` 等への参照は**通す**。

    managed 規範から LAM 自身の記録への参照は 60 件超あり（2026-09-04 実測）、
    一律に禁じると検査が最初から赤で埋まる（`security-commands.md` §計器への書き込みを伴う検証
    が警告する「常時落ちる計器は殺される」型）。既知ギャップとして
    `docs/artifacts/2026-09-04-distribution-layer-classification.md` §7 が持つ。

    **本テストは射程が意図的なものであることの記録であり、将来 v2 で狭める際に
    ここが赤くなることで「射程を変えた」と気づける。**
    """
    body = "経緯は `docs/artifacts/2026-09-04-magi-distribution-form.md` を参照\n"
    assert check_reference_closure(_closure_repo(tmp_path, body)) == []


def test_module_exposes_scope_constants():
    """射程を決める定数が module 上に公開されている（変更が diff に出る）。"""
    assert len(vpc._ABSOLUTE_PATH_PATTERNS) == 3
    assert len(vpc._NON_DISTRIBUTED_REFS) == 1
    # 2026-09-05（P2 複製相）: `scripts` を追加。配布 skills が呼ぶ
    # `.claude/scripts/*` を init が敷いておらず、利用者環境では存在しない
    # `py_invoke.sh` を呼んで落ちる状態だった。本 assert は射程変更を
    # diff に出すためのトリップワイヤであり、実際にそう働いた。
    assert set(vpc._MANAGED_AREAS) == {"rules", "docs-internal", "scripts"}
    # 2026-09-05（複製相の恒等性検査 T3 追加）: skills / agents は開発側・plugin 側
    # 双方に実体を持つ複製相であり、_MANAGED_AREAS（一方向テンプレート）とは
    # 別定数として管理する。本 assert は射程変更を diff に出すトリップワイヤ。
    # 2026-09-05（P-1）: `hooks` を追加。hooks も複製相に入った。
    assert set(vpc._MIRROR_AREAS) == {"skills", "agents", "hooks"}


# --- T4 hook 宣言の実体（陰性対照）----------------------------------------


def _hooks_repo(tmp_path: Path, *, config: str, targets: tuple = ()) -> Path:
    """plugin の hooks.json と、それが名指しする実体を持つ最小の偽リポジトリを作る。"""
    plugin = tmp_path / "plugins" / "lam-harness"
    (plugin / "hooks").mkdir(parents=True)
    (plugin / "hooks" / "hooks.json").write_text(config, encoding="utf-8")
    for rel in targets:
        p = plugin / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# stub\n", encoding="utf-8")
    return tmp_path


_WELL_FORMED = """{
  "hooks": {
    "PreToolUse": [
      {"hooks": [{"type": "command",
        "command": "bash \\"${CLAUDE_PLUGIN_ROOT}/hooks/pre-tool-use.py\\""}]}
    ]
  }
}
"""


def test_t4_accepts_well_formed_declaration(tmp_path):
    repo = _hooks_repo(tmp_path, config=_WELL_FORMED, targets=("hooks/pre-tool-use.py",))
    assert check_hook_declaration(repo) == []


def test_t4_detects_missing_target(tmp_path):
    """宣言された実体が配布されていなければ落ちる（**そのイベントだけが黙って発火しない**形）。"""
    repo = _hooks_repo(tmp_path, config=_WELL_FORMED)  # 実体を置かない
    violations = check_hook_declaration(repo)
    assert len(violations) == 1
    assert violations[0].check == "T4"
    assert "PreToolUse" in violations[0].detail
    assert "hooks/pre-tool-use.py" in violations[0].detail


def test_t4_detects_broken_json(tmp_path):
    repo = _hooks_repo(tmp_path, config='{"hooks": {')
    violations = check_hook_declaration(repo)
    assert len(violations) == 1
    assert "JSON として読めない" in violations[0].detail


def test_t4_detects_missing_hooks_object(tmp_path):
    """`hooks` キーが無ければ 1 件も発火しない。**構文は正しいので黙って無音になる。**"""
    repo = _hooks_repo(tmp_path, config='{"description": "no hooks here"}')
    violations = check_hook_declaration(repo)
    assert len(violations) == 1
    assert "hooks" in violations[0].detail


def test_t4_detects_reference_outside_plugin(tmp_path):
    """`${CLAUDE_PLUGIN_ROOT}` を使わない宣言は install 先で解決しないため落とす。"""
    config = (
        '{"hooks": {"Stop": [{"hooks": [{"type": "command",'
        ' "command": "bash \\"$CLAUDE_PROJECT_DIR/.claude/hooks/lam-stop-hook.py\\""}]}]}}'
    )
    repo = _hooks_repo(tmp_path, config=config)
    violations = check_hook_declaration(repo)
    assert len(violations) == 1
    assert "CLAUDE_PLUGIN_ROOT" in violations[0].detail


def test_t4_check_is_not_vacuous():
    """実リポジトリの hooks.json が実際に複数イベントを宣言していることを要求する。

    0 件なら「常に緑」になる（機構 #10 / 他の not_vacuous と同じ構え）。
    """
    cfg = REPO_ROOT / "plugins" / "lam-harness" / "hooks" / "hooks.json"
    assert cfg.is_file(), "plugin 側 hooks.json が存在しない = T4 が空回りしている"
    import json

    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert len(data["hooks"]) >= 5, "宣言イベントが少なすぎる（settings.json 側は 5 イベント）"


def test_hooks_mirror_is_not_vacuous():
    """hooks の複製相が実際に比較されていることを要求する（片側のみなら黙って 0 件になる）。"""
    matched = [
        (p, d)
        for p, d in vpc._iter_mirror_matches(REPO_ROOT)
        if "hooks" in p.parts
    ]
    assert len(matched) >= 7, (
        f"hooks の一致エントリが少なすぎる（{len(matched)} 件）= 複製されていない"
    )
