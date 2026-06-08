"""test_tdd_notification_b.py - W-9: Stop hook 通知B（未分析パターン通知）

仕様: docs/specs/tdd-introspection-v2.md §5.1 / §7 step 7
- ループ終了時に tdd-patterns.log の最終 ANALYZED マーカー以降のエントリ数をカウント
- 未分析エントリが1件以上あれば loop.log に「/retro を推奨」を INFO 記録
- ログ出力のみ。ループ動作には影響しない（提案のみ）
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parent.parent
_STOP_HOOK_PATH = _HOOKS_DIR / "lam-stop-hook.py"


@pytest.fixture()
def stop_hook(monkeypatch: pytest.MonkeyPatch):
    """lam-stop-hook.py を importlib.util 経由で読み込む（ハイフン回避）。"""
    monkeypatch.syspath_prepend(str(_HOOKS_DIR))
    spec = importlib.util.spec_from_file_location("lam_stop_hook", _STOP_HOOK_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# tdd-patterns.log の行サンプル（タブ区切り・実書式準拠）
_FAIL = '2026-06-09T00:00:00Z\tFAIL\tpytest\ttests=5 failures=1\t"test_x"'
_PASS = '2026-06-09T00:01:00Z\tPASS\tpytest\ttests=5 failures=0\t"pytest (previously failed)"'
_ANALYZED = '2026-06-09T00:02:00Z\tANALYZED\tretro\t"analyzed 2 entries: no pattern"'


def _write_tdd_log(project_root: Path, lines: list[str]) -> Path:
    tdd_log = project_root / ".claude" / "tdd-patterns.log"
    tdd_log.parent.mkdir(parents=True, exist_ok=True)
    tdd_log.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return tdd_log


class TestCountUnanalyzedPatterns:
    """_count_unanalyzed_tdd_patterns の集計ロジック"""

    def test_no_file_returns_zero(self, stop_hook, project_root):
        """ファイル不在時は 0 を返す。"""
        tdd_log = project_root / ".claude" / "tdd-patterns.log"
        assert not tdd_log.exists()
        assert stop_hook._count_unanalyzed_tdd_patterns(tdd_log) == 0

    def test_empty_file_returns_zero(self, stop_hook, project_root):
        """空ファイルは 0。"""
        tdd_log = _write_tdd_log(project_root, [])
        assert stop_hook._count_unanalyzed_tdd_patterns(tdd_log) == 0

    def test_no_analyzed_marker_counts_all_entries(self, stop_hook, project_root):
        """ANALYZED マーカーがなければ全エントリが未分析。"""
        tdd_log = _write_tdd_log(project_root, [_FAIL, _PASS, _FAIL])
        assert stop_hook._count_unanalyzed_tdd_patterns(tdd_log) == 3

    def test_counts_only_entries_after_last_marker(self, stop_hook, project_root):
        """最終 ANALYZED マーカー以降のエントリのみカウントする。"""
        tdd_log = _write_tdd_log(
            project_root, [_FAIL, _PASS, _ANALYZED, _FAIL, _PASS]
        )
        assert stop_hook._count_unanalyzed_tdd_patterns(tdd_log) == 2

    def test_marker_at_end_returns_zero(self, stop_hook, project_root):
        """ANALYZED マーカー以降にエントリがなければ 0。"""
        tdd_log = _write_tdd_log(project_root, [_FAIL, _PASS, _ANALYZED])
        assert stop_hook._count_unanalyzed_tdd_patterns(tdd_log) == 0

    def test_multiple_markers_uses_last(self, stop_hook, project_root):
        """複数 ANALYZED マーカーがある場合、最後のマーカー以降を数える。"""
        tdd_log = _write_tdd_log(
            project_root, [_FAIL, _ANALYZED, _PASS, _ANALYZED, _FAIL]
        )
        assert stop_hook._count_unanalyzed_tdd_patterns(tdd_log) == 1

    def test_non_utf8_file_returns_zero(self, stop_hook, project_root):
        """非 UTF-8 バイト混入時もフェイルセーフに 0（例外を投げない）。

        通知B は advisory 機能でループ動作に影響してはならない（spec §5.1）。
        UnicodeDecodeError は OSError のサブクラスではないため明示捕捉が必要。
        """
        tdd_log = project_root / ".claude" / "tdd-patterns.log"
        tdd_log.parent.mkdir(parents=True, exist_ok=True)
        tdd_log.write_bytes(b"\xff\xfe not valid utf-8\n")
        assert stop_hook._count_unanalyzed_tdd_patterns(tdd_log) == 0


class TestNotifyUnanalyzedPatterns:
    """_notify_unanalyzed_patterns の通知B 出力（loop.log への INFO 記録）"""

    def test_notifies_when_unanalyzed_exist(self, stop_hook, project_root):
        """未分析が1件以上あれば loop.log に件数付きで /retro 推奨を記録する。"""
        _write_tdd_log(project_root, [_FAIL, _PASS])
        log_file = project_root / ".claude" / "logs" / "loop.log"

        stop_hook._notify_unanalyzed_patterns(project_root, log_file)

        content = log_file.read_text(encoding="utf-8")
        assert "2件の未分析パターン" in content
        assert "/retro" in content

    def test_silent_when_none_unanalyzed(self, stop_hook, project_root):
        """未分析が 0 件なら通知B を出さない。"""
        _write_tdd_log(project_root, [_FAIL, _PASS, _ANALYZED])
        log_file = project_root / ".claude" / "logs" / "loop.log"

        stop_hook._notify_unanalyzed_patterns(project_root, log_file)

        content = log_file.read_text(encoding="utf-8") if log_file.exists() else ""
        assert "未分析パターン" not in content

    def test_silent_when_no_log_file(self, stop_hook, project_root):
        """tdd-patterns.log 不在時は通知B を出さない（例外も投げない）。"""
        log_file = project_root / ".claude" / "logs" / "loop.log"

        stop_hook._notify_unanalyzed_patterns(project_root, log_file)

        content = log_file.read_text(encoding="utf-8") if log_file.exists() else ""
        assert "未分析パターン" not in content
