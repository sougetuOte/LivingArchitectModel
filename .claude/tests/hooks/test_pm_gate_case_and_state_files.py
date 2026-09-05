r"""PM 級ゲートの 2 つの穴を塞ぐ TDD（/full-review 2026-09-05 iter0 の C-2 / C-3 / C-4）.

いずれも「`_PM_PATH_PATTERNS` が集合として不完全」という単一原因の別断面である。

## C-2: 大文字小文字による迂回

`CLAUDE.md` §Execution Environment が明記するとおり実行環境は Windows であり、
NTFS は既定で case-insensitive（かつ case-preserving）である。一方
`_hook_utils.normalize_path` の相対パス分岐は FS に問い合わせず、`.`/`..` の
字句畳み込みのみを行う（意図的な設計 / FS 非アクセス）。したがって
`.claude/Rules/security-commands.md`（大文字 R）は正規化後もそのままであり、
大文字小文字を区別する `^\.claude/rules/.*\.md$` に一致しない。

実測（2026-09-05 / 実際の `_determine_by_path` を呼んで確認）:

    .claude/rules/security-commands.md -> ('PM', 'rules/ path')
    .claude/Rules/security-commands.md -> ('SE', 'default path')   ← 穴
    CLAUDE.md                          -> ('PM', 'root CLAUDE.md')
    Claude.md                          -> ('SE', 'default path')   ← 穴

かつ `head -1 ".claude/Rules/security-commands.md"` は実ファイルを読み出す。
すなわち **判定は SE、書込先は PM 級ファイル本体**という経路が成立していた。

## C-3 / C-4: hook が書く信頼アンカーが PM 級集合の外にある

- `.claude/.session-pm-edit-cache.json`: 偽造すると以後の PM 承認が全て SE へ降格する
  （判定は session_id とパス文字列の一致のみで偽造耐性が無い / session_id は
  トランスクリプトのファイル名として `ls` だけで得られる）
- `.claude/autonomous-state.json`: `active` を false にすると G1 checker を
  一度も評価せずにループが「正常終了」する
- `.claude/gd-session-state.json`: token/time bound の強制を回避できる
- `.claude/lam-loop-state.json`: ループ制御そのものを外側から書き換えられる

## 射程の限界（意図的に守らないもの）

本修正が塞ぐのは **Edit / Write 経路のみ**である。`Bash("cat > ...")` は
`file_path` を持たず `_determine_by_command` に落ちるため到達しない。これは
AUTONOMOUS の FR-9 / FR-3.4 deny や PLANNING の設定凍結と同じ既知の限界であり、
本テストはその限界を変えない（`phase-rules.md` の同趣旨の注記を参照）。
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_HOOKS_DIR = Path(__file__).resolve().parents[2] / "hooks"
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))


def _load_pre_tool_use():
    spec = importlib.util.spec_from_file_location(
        "ptu_case_gate", _HOOKS_DIR / "pre-tool-use.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---- C-2: 大文字小文字変種 ----------------------------------------------

_CASE_VARIANTS = [
    ".claude/Rules/security-commands.md",
    ".claude/RULES/permission-levels.md",
    "CLAUDE.MD",
    "Claude.md",
    "docs/Specs/x.md",
    "docs/ADR/0010-x.md",
    "docs/Internal/08_EXECUTION_DISCIPLINE.md",
    ".claude/Settings.json",
]


def test_case_variant_paths_are_pm():
    """大文字小文字が異なるだけの PM 級パスも PM と判定される。

    Windows の FS は case-insensitive なので、これらは全て実在の PM 級
    ファイルへの書込になる。判定側だけが区別していると穴になる。
    """
    import _hook_utils

    for path in _CASE_VARIANTS:
        assert _hook_utils.is_pm_path_pattern(path), f"{path} が PM 判定されていない"


# ---- C-3 / C-4: hook が書く信頼アンカー ----------------------------------

_STATE_FILES = [
    ".claude/.session-pm-edit-cache.json",
    ".claude/autonomous-state.json",
    ".claude/gd-session-state.json",
    ".claude/lam-loop-state.json",
]


def test_hook_owned_state_files_are_pm():
    """hook が書く信頼アンカーはモデルからの Edit/Write に対して PM 級である。"""
    import _hook_utils

    for path in _STATE_FILES:
        assert _hook_utils.is_pm_path_pattern(path), f"{path} が PM 判定されていない"


def test_hook_owned_state_files_are_pm_case_insensitively():
    """状態ファイルも大文字小文字変種で迂回できない（C-2 と C-3/C-4 の合流）。"""
    import _hook_utils

    assert _hook_utils.is_pm_path_pattern(".claude/Autonomous-State.json")
    assert _hook_utils.is_pm_path_pattern(".CLAUDE/lam-loop-state.json")


# ---- 陰性対照: 巻き込んではいけないもの ----------------------------------


def test_records_under_docs_stay_non_pm():
    """`docs/` 配下の記録（規範ではないもの）は PM に巻き込まない。

    巻き込むと retro・進捗台帳の毎回の書込が PM ダイアログになり、
    「常時鳴る計器は殺される」型に直行する（permission-levels.md の
    `docs/internal/` 追加時に同じ理由で陰性対照が置かれている）。
    """
    import _hook_utils

    for path in [
        "docs/artifacts/retro-2026-09-05.md",
        "docs/daily/2026-09-05.md",
        "docs/private/notes.md",
        "docs/Artifacts/audit-reports/2026-09-05-iter0.md",
    ]:
        assert not _hook_utils.is_pm_path_pattern(path), f"{path} を PM に巻き込んでいる"


def test_unrelated_state_like_paths_stay_non_pm():
    """`.claude/` 配下でも、hook の信頼アンカーでないものは PM にしない。"""
    import _hook_utils

    for path in [
        ".claude/logs/permission.log",
        ".claude/tdd-patterns.log",
        ".claude/skills/magi/SKILL.md",
        ".claude/agents/gabriel.md",
        ".claude/states/phase.json",
        ".claude/review-state/summary.md",
    ]:
        assert not _hook_utils.is_pm_path_pattern(path), f"{path} を PM に巻き込んでいる"


# ---- 経路全体（_determine_by_path 越し） ---------------------------------


def test_determine_by_path_returns_pm_for_case_variants(tmp_path):
    """判定関数の経路全体で PM が返る（is_pm_path_pattern 単体ではなく）。"""
    ptu = _load_pre_tool_use()
    phase_file = tmp_path / "current-phase.md"
    phase_file.write_text("**BUILDING**", encoding="utf-8")

    for path in _CASE_VARIANTS + _STATE_FILES:
        level, _reason = ptu._determine_by_path(path, _REPO_ROOT, phase_file)
        assert level == "PM", f"{path} -> {level}（PM でない）"


def test_pm_reasons_length_still_matches_patterns():
    """`_PM_PATH_REASONS` と `_PM_PATH_PATTERNS` の要素数が一致し続ける。

    `zip` は末尾を静かに切り捨てるため、pattern だけ足すと「追加したつもり」
    のまま PM 判定に載らない。本ファイルでパターンを増やしたので再掲する。
    """
    import _hook_utils

    ptu = _load_pre_tool_use()
    assert len(ptu._PM_PATH_REASONS) == len(_hook_utils._PM_PATH_PATTERNS)
