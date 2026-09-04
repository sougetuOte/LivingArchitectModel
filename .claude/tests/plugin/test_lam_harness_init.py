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
