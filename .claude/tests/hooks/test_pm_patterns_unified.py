"""R1-034 + R1-I18: PM パターン一本化 TDD.

pre-tool-use.py の `_PM_PATTERNS`（PM 級パス判定）と post-tool-use.py の
`_PM_PATH_PATTERNS_FOR_CACHE`（セッションスコープ降格キャッシュ対象判定）は
手書きで別々に複製されており（4 patterns）、片方だけ更新すると PM 級判定と
キャッシュ判定が drift する保守リスクがあった（R1-034）。

out-of-root パターン（`^__out_of_root__/`）は pre 側のみが持ち、post 側の
キャッシュ判定には意図的に含まれない（R1-I18: 安全側維持 = キャッシュ対象外で
毎回 PM ダイアログ再表示）。

本テストは:
- `_hook_utils.py` に一本化された `_PM_PATH_PATTERNS`（path-only / out-of-root 除外）
  が存在することを assert
- pre-tool-use.py の `_PM_PATTERNS`（out-of-root を除く path patterns）と
  post-tool-use.py の `_PM_PATH_PATTERNS_FOR_CACHE` が、`_hook_utils._PM_PATH_PATTERNS`
  と完全一致（pattern 文字列レベル）することを assert
- out-of-root pattern が post 側キャッシュ対象に含まれないこと（R1-I18 非対称性の
  意図的維持）を assert

親 issue: `docs/artifacts/r-1-audit-tracker.md` R1-034 / R1-I18
根拠 evidence:
  - `.claude/hooks/pre-tool-use.py` L92-99 `_PM_PATTERNS`
  - `.claude/hooks/post-tool-use.py` L55-61 `_PM_PATH_PATTERNS_FOR_CACHE`
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parents[2] / "hooks"
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))


def _load_module(module_name: str, file_name: str):
    """dash を含むファイル名の hook スクリプトを importlib で動的ロードする。

    既存 test_pre_tool_use.py と同一パターン（sys.modules 登録なし・ローカル変数返却）。
    """
    spec = importlib.util.spec_from_file_location(module_name, _HOOKS_DIR / file_name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


import _hook_utils  # noqa: E402

pre_tool_use = _load_module("pre_tool_use_pm_unified_test", "pre-tool-use.py")
post_tool_use = _load_module("post_tool_use_pm_unified_test", "post-tool-use.py")


# ---- Red→Green: _hook_utils._PM_PATH_PATTERNS の存在と内容 ----


#: PM 級パスパターンの期待集合（`permission-levels.md` §ファイルパスベースの分類 の実装）。
#: 件数リテラルではなく集合で表現する —— 2026-07-26 に CLAUDE.md を追加した際、
#: `== 4` のリテラル assert が落ちた（rule-001 と同型の「literal assert 未同期」）。
#: 集合なら失敗メッセージが「何が増減したか」を直接示すため、恒久解として置換した。
_EXPECTED_PM_PATH_PATTERNS = {
    r"^docs/specs/.*\.md$",
    r"^docs/adr/.*\.md$",
    # docs/internal/（2026-09-04 追加 / retro-2026-09-04 A1 / ユーザー承認済）。
    # Hierarchy of Truth（CLAUDE.md）は docs/internal/00-08 を level 2、docs/specs/ を
    # level 3 と定めるのに、等級は specs=PM / internal=SE と逆転していた。
    # 2026-09-04 に 08_EXECUTION_DISCIPLINE.md（247 行）が無ゲートで生まれ、
    # PM ダイアログは参照側（.claude/rules/）にのみ発火した実測がある。
    # managed 配布物でもあるため、無ゲートの条文が利用者へ配られる経路でもあった。
    r"^docs/internal/.*\.md$",
    r"^\.claude/rules/.*\.md$",
    r"^\.claude/settings.*\.json$",
    r"^CLAUDE\.md$",
    # hook が書く信頼アンカー（2026-09-05 追加 / /full-review iter0 C-3・C-4 /
    # ユーザー承認済）。hook が書き、hook が読んで判断の根拠にするファイルであり、
    # モデルが直接書けると判断の前提そのものを偽造できた（実測: いずれも
    # ('SE', 'default path') で無条件に書けた）。
    # 内容と射程の限界は .claude/tests/hooks/test_pm_gate_case_and_state_files.py
    r"^\.claude/\.session-pm-edit-cache\.json$",
    r"^\.claude/autonomous-state\.json$",
    r"^\.claude/gd-session-state\.json$",
    r"^\.claude/lam-loop-state\.json$",
}


def test_hook_utils_has_pm_path_patterns_constant():
    """_hook_utils に _PM_PATH_PATTERNS（path-only / out-of-root 除外）が定義されている。"""
    assert hasattr(_hook_utils, "_PM_PATH_PATTERNS")
    actual = {p.pattern for p in _hook_utils._PM_PATH_PATTERNS}
    assert actual == _EXPECTED_PM_PATH_PATTERNS


def test_hook_utils_has_is_pm_path_pattern_function():
    """_hook_utils に is_pm_path_pattern(path_str) -> bool 関数が定義されている。"""
    assert hasattr(_hook_utils, "is_pm_path_pattern")
    assert _hook_utils.is_pm_path_pattern("docs/specs/foo.md") is True
    assert _hook_utils.is_pm_path_pattern("src/foo.py") is False


def test_docs_internal_is_pm_and_other_docs_are_not():
    """docs/internal/*.md は PM 級（Hierarchy level 2）/ 他の docs/ は SE のまま。

    陽性: Hierarchy of Truth level 2 の SSOT 群。
    陰性対照: docs/artifacts/ · docs/private/ · docs/daily/ は記録であり規範ではないため
    SE のまま（ここを巻き込むと retro / 進捗台帳の毎回書込が PM ダイアログになり、
    「常時鳴る計器は殺される」型に直行する）。
    """
    assert _hook_utils.is_pm_path_pattern("docs/internal/08_EXECUTION_DISCIPLINE.md") is True
    assert _hook_utils.is_pm_path_pattern("docs/internal/00_PROJECT_STRUCTURE.md") is True
    # 拡張子ガード: .md 以外は対象外（README 生成物等の巻き込み防止）
    assert _hook_utils.is_pm_path_pattern("docs/internal/notes.txt") is False
    # 陰性対照（SE のまま維持されること）
    assert _hook_utils.is_pm_path_pattern("docs/artifacts/retro-2026-09-04.md") is False
    assert _hook_utils.is_pm_path_pattern("docs/private/fable-l3-protocol.md") is False
    assert _hook_utils.is_pm_path_pattern("docs/daily/2026-09-04.md") is False


# ---- Red→Green: pre / post 両モジュールが _hook_utils から取得し完全一致 ----


def _pattern_strings(patterns) -> set[str]:
    """pattern リストから正規表現文字列の集合を取り出す（reason タプルの有無を吸収）。"""
    result = set()
    for item in patterns:
        pattern = item[0] if isinstance(item, tuple) else item
        result.add(pattern.pattern)
    return result


def test_pre_pm_patterns_path_subset_matches_hook_utils():
    """pre-tool-use.py の _PM_PATTERNS から out-of-root を除いた集合が _hook_utils と完全一致。"""
    pre_path_patterns = {
        p for p in _pattern_strings(pre_tool_use._PM_PATTERNS)
        if p != r"^__out_of_root__/"
    }
    hook_utils_patterns = _pattern_strings(_hook_utils._PM_PATH_PATTERNS)
    assert pre_path_patterns == hook_utils_patterns


def test_post_pm_cache_patterns_matches_hook_utils():
    """post-tool-use.py の _PM_PATH_PATTERNS_FOR_CACHE が _hook_utils と完全一致。"""
    post_patterns = _pattern_strings(post_tool_use._PM_PATH_PATTERNS_FOR_CACHE)
    hook_utils_patterns = _pattern_strings(_hook_utils._PM_PATH_PATTERNS)
    assert post_patterns == hook_utils_patterns


def test_pre_pm_patterns_still_contains_out_of_root():
    """pre-tool-use.py 側は out-of-root pattern を引き続き保持する（R1-I18 非対称性維持）。"""
    pre_patterns = _pattern_strings(pre_tool_use._PM_PATTERNS)
    assert r"^__out_of_root__/" in pre_patterns


def test_post_pm_cache_patterns_excludes_out_of_root():
    """post-tool-use.py 側キャッシュ判定は out-of-root pattern を含まない（R1-I18 意図的除外）。"""
    post_patterns = _pattern_strings(post_tool_use._PM_PATH_PATTERNS_FOR_CACHE)
    assert r"^__out_of_root__/" not in post_patterns


def test_pre_and_post_share_same_object_from_hook_utils():
    """pre / post 双方が同一の _hook_utils._PM_PATH_PATTERNS オブジェクトを import している

    （手書き複製ではなく import による単一定義の共有であることを identity で確認）。
    """
    assert pre_tool_use._PM_PATH_PATTERNS is _hook_utils._PM_PATH_PATTERNS
    assert post_tool_use._PM_PATH_PATTERNS is _hook_utils._PM_PATH_PATTERNS
