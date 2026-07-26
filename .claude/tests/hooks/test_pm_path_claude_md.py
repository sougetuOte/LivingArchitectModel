"""ルート `CLAUDE.md` の PM 級パス化 TDD.

`_PM_PATH_PATTERNS` は specs / adr / rules / settings の 4 件のみで、**ルート
`CLAUDE.md` が不在**だった（2026-07-26 実測）。CLAUDE.md は無条件ロードされる
最も常駐性の高い 1 ファイルであり、そこへの条項追加が PM ダイアログも
事前宣言義務も経ないという穴になっていた（HGA #19 仮定 5-iii）。

設計: docs/artifacts/clause-gate-routing-design-2026-07-26.md v0.3 §4.2 / §4.3 #3
ユーザー承認: 2026-07-26（「追加する」を選択）

あわせて `pre-tool-use.py` の `_PM_PATH_REASONS` は `zip` で
`_PM_PATH_PATTERNS` と組まれるため、**要素数が一致しないと末尾の pattern が
静かに脱落する**。この静かな脱落を検出する assert を持つ。
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_HOOKS_DIR = Path(__file__).resolve().parents[2] / "hooks"
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))


def _load_module(module_name: str, file_name: str):
    spec = importlib.util.spec_from_file_location(module_name, _HOOKS_DIR / file_name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_claude_md_is_pm_path():
    """ルート `CLAUDE.md` が PM 級パスとして判定される。"""
    import _hook_utils

    assert _hook_utils.is_pm_path_pattern("CLAUDE.md")


def test_nested_claude_md_is_not_matched_by_root_pattern():
    """nested な CLAUDE.md はルートパターンに一致しない（意図的）。

    `/compact` 後に再注入されるのはプロジェクトルート `CLAUDE.md` のみであり
    （2026-07-26 調査）、常駐性の根拠はルートに限られる。
    """
    import _hook_utils

    assert not _hook_utils.is_pm_path_pattern("docs/CLAUDE.md")
    assert not _hook_utils.is_pm_path_pattern(".claude/CLAUDE.md")


def test_pm_reasons_length_matches_patterns():
    """`_PM_PATH_REASONS` と `_PM_PATH_PATTERNS` の要素数が一致する。

    不一致だと `zip` が末尾を静かに切り捨て、追加した pattern が
    PM 判定に載らないまま「追加したつもり」になる。
    """
    import _hook_utils

    pre = _load_module("pre_tool_use_reasons", "pre-tool-use.py")
    assert len(pre._PM_PATH_REASONS) == len(_hook_utils._PM_PATH_PATTERNS)


def test_pre_tool_use_classifies_claude_md_as_pm(tmp_path):
    """hook のパスベース判定が `CLAUDE.md` を PM に分類する。"""
    pre = _load_module("pre_tool_use_claude_md", "pre-tool-use.py")
    phase_file = tmp_path / "current-phase.md"
    phase_file.write_text("# Current Phase\n\n**BUILDING**\n", encoding="utf-8")

    level, _reason = pre._determine_by_path(
        "CLAUDE.md", _REPO_ROOT, phase_file
    )
    assert level == "PM"
