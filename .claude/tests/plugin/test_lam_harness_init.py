"""/lam-harness:init（手順 3）の受け入れ検査。

`init-harness` skill を plugin 側へ置換して廃止した際の不動点を固定する。
検査は「存在」と「導出結果との一致」のみで、意味解釈を含まない（誕生ゲート設計 §1.1 の R3 要件）。

**維持リストを持たない設計**: managed の領域名も starter の対象も、
可能な限り実ディレクトリから導出する（R3 機構 #7 / #10 / #11 と同型）。

根拠:
- 手順 3 の要件: docs/artifacts/2026-09-04-plugin-migration-progress.md §2
- ランタイム検査が必須である根拠 (V4): 同 MAGI §13.6
  hook の exit 2 以外の非零終了は非ブロッキングで、インタプリタ不在の 127 も同じバケツ。
  放置すると fail-open と UX ノイズが同時に起きる。
- Layer 1 が届かない根拠 (V8 / HGA §13.5-E): settings.json の permissions は
  auto mode の安全クラシファイアがハードブロックする。
"""

from __future__ import annotations

import re
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "lam-harness"
INIT_SKILL = PLUGIN_ROOT / "skills" / "init" / "SKILL.md"
RUNTIME_CHECK = PLUGIN_ROOT / "scripts" / "check-runtime.sh"
STARTER_ROOT = PLUGIN_ROOT / "templates" / "starter"
MANAGED_ROOT = PLUGIN_ROOT / "templates" / "managed"

#: starter 層の対象（`2026-09-04-distribution-layer-classification.md` §3 が正本 / 8 件）。
#: plugin 側では `.claude/` を `dot-claude/` に読み替えて格納する
#: （ドット始まりディレクトリは配布・展開時に取りこぼされやすいため）。
_EXPECTED_STARTER = {
    "CLAUDE.md",
    "CHEATSHEET.md",
    "CHANGELOG.md",
    "SESSION_STATE.md",
    "dot-claude/current-phase.md",
    "dot-claude/harness.json",
    "dot-claude/rules/model-roster.md",
    "dot-claude/rules/terminology.md",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---- skill 本体 ----


def test_init_skill_exists():
    """plugin skill として `/lam-harness:init` が実在する。"""
    assert INIT_SKILL.is_file(), "plugin skill が無い: {0}".format(INIT_SKILL)


def test_init_skill_has_description_frontmatter():
    """description frontmatter を持つ（skill 一覧に載る条件）。"""
    text = _read(INIT_SKILL)
    assert text.startswith("---\n"), "frontmatter が無い"
    head = text.split("---", 2)[1]
    assert "description:" in head, "description frontmatter が無い"


def test_init_skill_declares_runtime_gate():
    """ランタイム不在時に完了を拒むことが skill 本文に書かれている（I4 / ユーザー確認済）。"""
    text = _read(INIT_SKILL)
    assert "check-runtime.sh" in text, "ランタイム検査スクリプトへの言及が無い"
    assert "完了を拒" in text, "「完了を拒む」という拒否の宣言が無い"


def test_init_skill_declares_layer1_out_of_scope():
    """Layer 1（settings.json の permissions）が届かないことを明示している（HGA §13.5-E / V8）。"""
    text = _read(INIT_SKILL)
    assert "Layer 1" in text, "Layer 1 への言及が無い"
    assert "permissions" in text, "permissions が届かない旨の記述が無い"


def test_init_skill_covers_every_managed_area():
    """skill が managed の全領域に言及している（領域はディレクトリから導出 / 維持リスト不要）。"""
    areas = sorted(p.name for p in MANAGED_ROOT.iterdir() if p.is_dir())
    assert areas, "managed テンプレートの領域が 1 つも無い"
    text = _read(INIT_SKILL)
    missing = [a for a in areas if a not in text]
    assert not missing, "skill が言及していない managed 領域: {0}".format(missing)


# ---- starter テンプレート ----


def test_starter_templates_match_expected_set():
    """starter の実体が分類表 §3 の 8 件と一致する。"""
    assert STARTER_ROOT.is_dir(), "starter テンプレートが無い: {0}".format(STARTER_ROOT)
    live = {
        p.relative_to(STARTER_ROOT).as_posix()
        for p in STARTER_ROOT.rglob("*")
        if p.is_file()
    }
    assert live == _EXPECTED_STARTER, (
        "starter の実体と分類表 §3 が不一致。実測 {0} / 期待 {1}".format(
            sorted(live), sorted(_EXPECTED_STARTER)
        )
    )


@pytest.mark.skipif(shutil.which("git") is None, reason="git が無い環境")
def test_starter_templates_are_all_git_tracked():
    """starter テンプレートが 1 件も gitignore されていない（2026-09-04 追加）。

    **ファイルシステム上の存在は、配布されることと同じではない。**
    2026-09-04、`.gitignore` のアンカーされていない `SESSION_STATE.md` が
    `plugins/lam-harness/templates/starter/SESSION_STATE.md`（配布物）を巻き込み、
    **git 管理外のまま**になっていた。`test_starter_templates_match_expected_set` は
    ファイルシステムを見ているため緑のままで、`/ship` Phase 1 の staged 一覧で初めて露見した。

    配布物の定義は「ディスクにあること」ではなく「git に入っていること」である。
    """
    files = sorted(p for p in STARTER_ROOT.rglob("*") if p.is_file())
    assert files, "starter テンプレートが 1 件も無い（空振り防止）"
    result = subprocess.run(
        [shutil.which("git"), "check-ignore", "-v", *[str(p) for p in files]],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    # check-ignore は「無視される対象があった」ときに 0 を返す
    assert result.returncode != 0, (
        "gitignore されている starter テンプレートがある（配布されない）:\n{0}".format(
            result.stdout.strip()
        )
    )


def test_starter_current_phase_matches_hook_format():
    """current-phase.md が hook の読む書式（行頭 `**PHASE**` / 大文字のみ）を満たす。

    2026-09-04 まで `.json` を配っており、フェーズ依存のガードが初期状態で沈黙していた。
    """
    import re

    text = _read(STARTER_ROOT / "dot-claude" / "current-phase.md")
    assert re.search(r"^\*\*[A-Z]+\*\*$", text, re.MULTILINE), (
        "hook が読む書式 ^\\*\\*[A-Z]+\\*\\*$ に一致する行が無い"
    )


def test_starter_files_are_not_managed_duplicates():
    """starter と managed が同じパスを二重に配らない（層の分類は排他）。"""
    managed = {
        p.relative_to(MANAGED_ROOT).as_posix().replace("docs-internal/", "")
        for p in MANAGED_ROOT.rglob("*")
        if p.is_file()
    }
    starter_basenames = {
        p.name for p in STARTER_ROOT.rglob("*") if p.is_file()
    }
    managed_basenames = {Path(m).name for m in managed}
    overlap = starter_basenames & managed_basenames
    assert not overlap, "starter と managed が同じファイル名を配っている: {0}".format(
        sorted(overlap)
    )


# ---- ランタイム検査 ----


def test_runtime_check_script_exists():
    assert RUNTIME_CHECK.is_file(), "ランタイム検査スクリプトが無い: {0}".format(RUNTIME_CHECK)


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash が無い環境")
def test_runtime_check_passes_in_this_environment():
    """この開発環境では検査が通る（陽性）。"""
    result = subprocess.run(
        [shutil.which("bash"), str(RUNTIME_CHECK)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert result.returncode == 0, (
        "本環境で検査が落ちた: rc={0} / {1}".format(result.returncode, result.stderr)
    )


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash が無い環境")
def test_runtime_check_fails_without_python(tmp_path):
    """Python が PATH に無いとき非零で落ち、理由を stderr に出す（陰性対照）。

    これが落ちなければ「fail-open のまま init が完了する」= I4 が守られていない。
    """
    assert RUNTIME_CHECK.is_file(), "検査対象のスクリプトが無い（空振り防止）"
    bash = shutil.which("bash")
    # テスト専用の分岐をスクリプトに置かない。実環境で Python が見つからない状況を
    # そのまま再現する: (1) PATH から python を除く (2) .venv の無いディレクトリで実行する。
    env = dict(os.environ)
    env["PATH"] = str(Path(bash).parent)
    result = subprocess.run(
        [bash, str(RUNTIME_CHECK)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    assert shutil.which("python", path=env["PATH"]) is None, (
        "PATH の除去が効いていない（陰性対照が成立しない）"
    )
    assert result.returncode != 0, "Python 不在でも成功してしまった（fail-open）"
    assert result.stderr.strip(), "落ちた理由が stderr に出ていない"


# ---- 旧 skill の撤回 ----


def test_old_init_harness_skill_is_retracted():
    """`.claude/skills/init-harness/` が撤回されている（MAGI §13.5-D）。

    「修正して残す期間」は存在の主張が半分正しい期間である、というのが召喚の結論。
    """
    old = REPO_ROOT / ".claude" / "skills" / "init-harness"
    assert not old.exists(), "旧 init-harness skill が残っている: {0}".format(old)


def test_step0_guards_unresolved_plugin_root() -> None:
    """Step 0 は `${CLAUDE_PLUGIN_ROOT}` 未解決を「Python 不在」と誤診しない。

    bash は未設定の変数を空文字に展開するため、ガードが無いと
    `bash "/scripts/check-runtime.sh"` = exit 127 となり、Step 0 の
    「非零なら中止」に落ちる。中止するのは正しいが、利用者には
    「Python を用意して再実行してください」と案内される —— 真因は別で、
    その案内に従っても直らない。LAM は同型を一度踏んでいる
    （CLAUDE.md §Python Invocation Convention / 段2 fixup 教訓 = `$CLAUDE_PROJECT_DIR`）。
    """
    text = (PLUGIN_ROOT / "skills" / "init" / "SKILL.md").read_text(encoding="utf-8")
    assert ':?' in text and "CLAUDE_PLUGIN_ROOT" in text, (
        "Step 0 に ${CLAUDE_PLUGIN_ROOT:?...} ガードが無い"
    )
    guard_pos = text.index(':?')
    check_pos = text.index("check-runtime.sh")
    assert guard_pos < check_pos, "ガードが check-runtime.sh の呼び出しより後にある"


# ==========================================================================
# 配布 skills が呼ぶ scripts は配布されているか（2026-09-05 / P2 複製相で発覚）
#
# 3 層分類 §5 は scripts を managed 10 件と分類していたが、templates/managed/ には
# rules と docs-internal しか無く、init は scripts を敷いていなかった。
# 利用者が /lam-harness:ship を打つと、存在しない py_invoke.sh を呼んで落ちる。
# ==========================================================================

NON_DISTRIBUTED_SCRIPTS: dict[str, str] = {
    "build_dashboard.py": (
        "LAM の SESSION_STATE.md 書式と Milestone 語彙に強く依存するため非配布"
        "（3 層分類 §4.2）。quick-save からの呼び出しは SHOULD かつ失敗を許容する"
        "設計であり、不在でも quick-save 全体は成功する。"
    ),
    "verify_plugin_containment.py": (
        "plugin ディレクトリの封じ込め（機構 #11/#12）を検査する開発者向け機構。"
        "利用者のプロジェクトには plugins/ が存在しないため配る意味がない。"
        "呼び出し元の release skill 側で plugins/ 不在時にスキップする。"
    ),
}


def _scripts_called_by_plugin_skills() -> set[str]:
    """plugin skills が呼ぶ `.claude/scripts/<name>` を実体から導出する。"""
    pat = re.compile(r"\.claude/scripts/([A-Za-z0-9._-]+\.(?:py|sh))")
    called: set[str] = set()
    for path in (PLUGIN_ROOT / "skills").rglob("*.md"):
        called |= set(pat.findall(path.read_text(encoding="utf-8")))
    return called


def test_every_script_called_by_plugin_skills_is_distributed() -> None:
    called = _scripts_called_by_plugin_skills()
    assert called, "plugin skills が scripts を 1 件も呼んでいない（導出が壊れている）"
    distributed = {
        p.name for p in (PLUGIN_ROOT / "templates" / "managed" / "scripts").glob("*")
        if p.is_file()
    }
    missing = called - distributed - set(NON_DISTRIBUTED_SCRIPTS)
    assert not missing, (
        "配布 skills が呼ぶのに配布されない script: " + ", ".join(sorted(missing))
    )


def test_every_non_distributed_script_carries_a_reason() -> None:
    for name, reason in NON_DISTRIBUTED_SCRIPTS.items():
        assert len(reason) >= 20, f"{name} の非配布理由が短すぎる"


def test_distill_lessons_pair_moves_together() -> None:
    """entry point とその実体は 2 件セットで配る（§6.1 / 片方だけだと壊れる）。"""
    scripts = PLUGIN_ROOT / "templates" / "managed" / "scripts"
    pair = {"distill-lessons.py", "distill_lessons.py"}
    present = {n for n in pair if (scripts / n).is_file()}
    assert present in (set(), pair), (
        "distill の 2 ファイル構成が片側だけ配られている: " + ", ".join(sorted(present))
    )


# ==========================================================================
# 上流公式ツールの組み込み（2026-09-05 / 外部調査で発見）
#
# `claude plugin validate --strict` と `claude plugin tag` は上流が提供する
# 公式の検証系である。前者は manifest スキーマ・コンポーネントパス・frontmatter を
# 検査し、community marketplace の審査パイプラインと同じチェックを走らせる。
# 後者は plugin.json と marketplace エントリの version 一致を検証しつつ tag を作る。
# 自前で書くより上流に寄せる（維持対象を増やさない）。
# ==========================================================================


def test_release_skill_runs_official_plugin_validate() -> None:
    text = (REPO_ROOT / ".claude" / "skills" / "release" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "claude plugin validate" in text, (
        "/release が上流公式の plugin validate を呼んでいない"
    )
    assert "--strict" in text, "validate が --strict で呼ばれていない（CI 相当の厳格さ）"


def test_marketplace_name_is_collision_resistant() -> None:
    """marketplace 名は所有者を含む（同名衝突は無警告で上書きされ、上流は直さない）。

    根拠: anthropics/claude-code #44042 は「同名 marketplace の add が既存を
    無警告で上書きする」を **Closed as not planned** としている。実害例では
    別リポジトリの plugin が壊れたまま 1 週間気づかれなかった。
    上流に防御が無い以上、**名前の一意性が唯一の防御線**である。
    """
    import json as _json

    name = _json.loads(
        (REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
    )["name"]
    assert len(name) >= 8, f"marketplace 名が短すぎて衝突しやすい: {name}"
    assert "-" in name, (
        f"marketplace 名に所有者/プロジェクトの区切りが無い: {name}"
        "（#44042 の推奨は org-prefixed な命名）"
    )
