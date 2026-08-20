"""計器隔離ガードのテスト（台帳 §D 在庫 #4 の機構化）

## 背景

`docs/artifacts/retro-2026-08-17.md` P1 が記録した実測: **1 セッションで計器に 3 回
触れて 2 回壊した**。うち 1 件は hook のスモーク実行時に環境変数名を取り違え
（`CLAUDE_PROJECT_DIR` / 正しくは `LAM_PROJECT_ROOT`）、`.claude/pre-compact-fired`
と `SESSION_STATE.md` の発火時刻に偽の値を上書きしたものである。

`.claude/tests/` 配下には `LAM_PROJECT_ROOT` を tmp へ向ける conftest が存在せず
（`dashboard/conftest.py` はモデル fixture）、hook モジュールを importlib で
in-process 読み込みするテストは、実リポジトリの計器へ書き込みうる。

在庫 #4 の条項候補は「計器に書き込みうる検証は隔離の実効を先に確認する」という
**規律**だったが、これは **検出機構に変換できる** —— セッション前後で計器の内容を
突き合わせ、変化していたら落とす。規律は忘れられるが機構は忘れない。

## 設計上の制約（機構 #7 と同型）

監視対象の**維持リストを持たない**。`.claude/hooks/*.py` のソースから
`project_root / ...` の式を導出する。維持リストは新しい計器が増えたときに
静かに漏れるため（台帳 §C 機構 #7 が同じ理由で同じ手を採っている）。
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_ROOT_CONFTEST = _REPO_ROOT / "conftest.py"
_HOOKS_DIR = _REPO_ROOT / ".claude" / "hooks"

_PATH_EXPR = re.compile(
    r'project_root\s*/\s*((?:"[^"]+"|\w+)(?:\s*/\s*(?:"[^"]+"|\w+))*)'
)
_CONST_DEF = re.compile(r'^(\w+)\s*=\s*"([^"]+)"\s*$', re.MULTILINE)


def _load_guard():
    """ルート conftest.py を独立した名前で読み込む（pytest 側の `conftest` と衝突させない）。"""
    spec = importlib.util.spec_from_file_location(
        "lam_instrument_guard_under_test", _ROOT_CONFTEST
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _independently_resolve_hook_paths() -> dict[str, set[str]]:
    """hook ソースから `project_root / ...` を独立に再導出する（テスト側の別オラクル）。

    ガード実装と同じ regex を使うが、実装を import せずテスト側で持つ。
    ガードが導出をサボった場合に、こちらが差分として検出する。
    """
    found: dict[str, set[str]] = {}
    for hook in sorted(_HOOKS_DIR.glob("*.py")):
        text = hook.read_text(encoding="utf-8")
        constants = dict(_CONST_DEF.findall(text))
        resolved: set[str] = set()
        for raw in _PATH_EXPR.findall(text):
            segments = []
            for seg in raw.split("/"):
                seg = seg.strip()
                if seg.startswith('"') and seg.endswith('"'):
                    segments.append(seg[1:-1])
                elif seg in constants:
                    segments.append(constants[seg])
                else:
                    segments = []
                    break
            if segments:
                resolved.add("/".join(segments))
        if resolved:
            found[hook.name] = resolved
    return found


# --------------------------------------------------------------------------
# 存在と API
# --------------------------------------------------------------------------


def test_root_conftest_exists() -> None:
    """ルート conftest.py が存在する。

    `pyproject.toml` の testpaths は `.claude/tests` と `.claude/hooks/tests` の
    2 ツリーであり、両方を 1 箇所で覆えるのは rootdir の conftest だけである。
    """
    assert _ROOT_CONFTEST.is_file(), (
        f"{_ROOT_CONFTEST} が無い。計器隔離ガードは rootdir conftest に置く"
    )


def test_guard_exposes_pure_functions() -> None:
    """スナップショット・差分・導出が純粋関数として取り出せる（fixture 内に埋めない）。"""
    guard = _load_guard()
    for name in (
        "derive_instrument_paths",
        "snapshot_instruments",
        "diff_snapshots",
        "format_violation",
    ):
        assert hasattr(guard, name), f"{name} が公開されていない"
        assert callable(getattr(guard, name))


# --------------------------------------------------------------------------
# 導出（維持リスト禁止）
# --------------------------------------------------------------------------


def test_derivation_finds_known_instruments() -> None:
    """hook ソースから既知の計器が導出される。"""
    guard = _load_guard()
    derived = guard.derive_instrument_paths(_REPO_ROOT)
    for expected in (
        ".claude/pre-compact-fired",
        ".claude/tdd-patterns.log",
        ".claude/doc-sync-flag",
        ".claude/lam-loop-state.json",
        ".claude/.session-pm-edit-cache.json",
        "SESSION_STATE.md",
    ):
        assert expected in derived, f"{expected} が導出されていない: {sorted(derived)}"


def test_derivation_resolves_module_level_constants() -> None:
    """`project_root / ".claude" / _PM_CACHE_FILENAME` のような定数参照も解決する。

    リテラルだけを拾う実装だと、定数経由の計器が静かに監視外になる。
    """
    guard = _load_guard()
    derived = guard.derive_instrument_paths(_REPO_ROOT)
    assert ".claude/.session-pm-edit-cache.json" in derived


def test_no_maintained_list_of_instruments_in_source() -> None:
    """ガードのソースが計器名のリテラルを維持リストとして持たない（機構 #7 と同型）。

    除外対象（`test-results.xml`）だけは、除外の根拠を書く必要があるため例外。
    """
    source = _ROOT_CONFTEST.read_text(encoding="utf-8")
    code = "\n".join(
        line for line in source.splitlines() if not line.lstrip().startswith("#")
    )
    forbidden = (
        "pre-compact-fired",
        "tdd-patterns.log",
        "doc-sync-flag",
        "lam-loop-state.json",
        ".session-pm-edit-cache.json",
        "last-test-result",
        "autonomous-state.json",
        "gd-session-state.json",
    )
    hits = [name for name in forbidden if f'"{name}"' in code or f"'{name}'" in code]
    assert not hits, (
        f"計器名がソースにリテラルで埋まっている: {hits}。"
        "監視対象は hook ソースから導出すること（維持リストは静かに漏れる）"
    )


def test_derivation_covers_every_hook_write_target() -> None:
    """hook ソース中の `project_root / ...` 式が、導出結果か除外理由のどちらかに載る。

    新しい計器が hook に足されたとき、このテストが落ちて監視漏れを可聴化する。
    """
    guard = _load_guard()
    derived = guard.derive_instrument_paths(_REPO_ROOT)
    excluded = set(guard.EXCLUDED_FROM_WATCH)

    unwatched: list[str] = []
    for hook_name, paths in _independently_resolve_hook_paths().items():
        for rel in sorted(paths):
            if rel in derived or rel in excluded:
                continue
            unwatched.append(f"{hook_name}: {rel}")
    assert not unwatched, (
        "hook が書きうるのに監視も除外もされていない経路がある:\n  "
        + "\n  ".join(unwatched)
    )


def test_every_exclusion_carries_a_reason() -> None:
    """除外には必ず理由が要る（理由なき除外は、後から汚染と区別できない）。"""
    guard = _load_guard()
    assert guard.EXCLUDED_FROM_WATCH, "除外表が空。少なくとも test-results.xml は要る"
    for path, reason in guard.EXCLUDED_FROM_WATCH.items():
        assert isinstance(reason, str) and reason.strip(), f"{path} の除外理由が空"


def test_test_results_xml_is_excluded() -> None:
    """`.claude/test-results.xml` は除外される（pytest 自身が正当に更新するため）。

    これを監視対象にすると、ガードが毎回落ちて無視されるようになり、
    結果として計器を殺すのと同じことになる（retro-2026-08-17 P2 の型）。
    """
    guard = _load_guard()
    assert ".claude/test-results.xml" in guard.EXCLUDED_FROM_WATCH


# --------------------------------------------------------------------------
# スナップショットと差分
# --------------------------------------------------------------------------


def test_snapshot_records_absent_files_as_none(tmp_path: Path) -> None:
    guard = _load_guard()
    snap = guard.snapshot_instruments(tmp_path, {"a.txt", "b/c.txt"})
    assert snap == {"a.txt": None, "b/c.txt": None}


def test_snapshot_records_directories_as_none(tmp_path: Path) -> None:
    """ディレクトリは内容比較の対象にしない（is_file でないため None）。"""
    guard = _load_guard()
    (tmp_path / "d").mkdir()
    assert guard.snapshot_instruments(tmp_path, {"d"}) == {"d": None}


def test_diff_detects_content_change(tmp_path: Path) -> None:
    guard = _load_guard()
    target = tmp_path / "a.txt"
    target.write_text("before", encoding="utf-8")
    before = guard.snapshot_instruments(tmp_path, {"a.txt"})
    target.write_text("after", encoding="utf-8")
    after = guard.snapshot_instruments(tmp_path, {"a.txt"})
    assert guard.diff_snapshots(before, after) == ["a.txt"]


def test_diff_detects_creation(tmp_path: Path) -> None:
    guard = _load_guard()
    before = guard.snapshot_instruments(tmp_path, {"a.txt"})
    (tmp_path / "a.txt").write_text("new", encoding="utf-8")
    after = guard.snapshot_instruments(tmp_path, {"a.txt"})
    assert guard.diff_snapshots(before, after) == ["a.txt"]


def test_diff_detects_deletion(tmp_path: Path) -> None:
    guard = _load_guard()
    target = tmp_path / "a.txt"
    target.write_text("x", encoding="utf-8")
    before = guard.snapshot_instruments(tmp_path, {"a.txt"})
    target.unlink()
    after = guard.snapshot_instruments(tmp_path, {"a.txt"})
    assert guard.diff_snapshots(before, after) == ["a.txt"]


def test_diff_is_empty_when_unchanged(tmp_path: Path) -> None:
    guard = _load_guard()
    (tmp_path / "a.txt").write_text("same", encoding="utf-8")
    before = guard.snapshot_instruments(tmp_path, {"a.txt"})
    after = guard.snapshot_instruments(tmp_path, {"a.txt"})
    assert guard.diff_snapshots(before, after) == []


def test_diff_returns_sorted_paths(tmp_path: Path) -> None:
    """報告順が実行順に依存しない（差分の再現性）。"""
    guard = _load_guard()
    for name in ("b.txt", "a.txt"):
        (tmp_path / name).write_text("x", encoding="utf-8")
    before = guard.snapshot_instruments(tmp_path, {"a.txt", "b.txt"})
    for name in ("b.txt", "a.txt"):
        (tmp_path / name).write_text("y", encoding="utf-8")
    after = guard.snapshot_instruments(tmp_path, {"a.txt", "b.txt"})
    assert guard.diff_snapshots(before, after) == ["a.txt", "b.txt"]


# --------------------------------------------------------------------------
# fixture の形と報告
# --------------------------------------------------------------------------


def test_guard_fixture_is_session_scoped_autouse() -> None:
    """ガードは session スコープの autouse fixture である（全テストを覆う）。"""
    guard = _load_guard()
    fixture = getattr(guard, "lam_instrument_isolation_guard", None)
    assert fixture is not None, "ガード fixture が公開されていない"
    # 属性名は pytest の世代で変わる（<=8: _pytestfixturefunction /
    # 9.0.3 実測: _fixture_function_marker）。どちらでも読めるようにする
    marker = getattr(fixture, "_fixture_function_marker", None) or getattr(
        fixture, "_pytestfixturefunction", None
    )
    assert marker is not None, (
        "pytest fixture として宣言されていない"
        f"（属性を探した: _fixture_function_marker / _pytestfixturefunction）"
    )
    assert marker.scope == "session"
    assert marker.autouse is True


def test_guard_has_no_silent_opt_out() -> None:
    """環境変数による黙認スイッチを持たない。

    黙って無効化できる検査は、無効化されたことも黙る（機構 #7 が扱った
    「消えても無音」と同じ失敗形）。
    """
    source = _ROOT_CONFTEST.read_text(encoding="utf-8")
    assert "environ" not in source, (
        "環境変数による opt-out を置かない。必要になったら可視な変更として入れる"
    )


def test_guard_failure_message_names_the_changed_paths() -> None:
    """差分検出時のメッセージが、変わったパスを名指しする。

    「何かが変わった」だけでは、汚染を後から区別できない（曝露ログを append-only に
    した判断と同じ理由 / retro-2026-08-17 K3）。
    """
    guard = _load_guard()
    message = guard.format_violation(["SESSION_STATE.md", ".claude/tdd-patterns.log"])
    assert "SESSION_STATE.md" in message
    assert ".claude/tdd-patterns.log" in message
    assert "LAM_PROJECT_ROOT" in message, (
        "対処法（隔離の張り方）をメッセージに含めること。"
        "retro P1 の事故は環境変数名の取り違えだった"
    )
