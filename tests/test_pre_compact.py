"""
test_pre_compact.py - pre-compact.py のユニットテスト

テスト対象: .claude/hooks/pre-compact.py
テスト戦略: LAM_PROJECT_ROOT 環境変数で tmp ディレクトリを指定し、
           各関数の動作を個別に検証する。
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# テスト対象モジュールのインポート準備
_HOOKS_DIR = Path(__file__).resolve().parent.parent / ".claude" / "hooks"


@pytest.fixture()
def pre_compact(monkeypatch: pytest.MonkeyPatch):
    """pre-compact.py モジュールをインポートして返す。"""
    monkeypatch.syspath_prepend(str(_HOOKS_DIR))

    mod_name = "pre_compact"
    if mod_name in sys.modules:
        del sys.modules[mod_name]

    spec = importlib.util.spec_from_file_location(
        mod_name, _HOOKS_DIR / "pre-compact.py"
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


class TestWritePreCompactFlag:
    """write_pre_compact_flag のテスト。"""

    def test_creates_flag_file(self, project_root: Path, pre_compact):
        pre_compact.write_pre_compact_flag(project_root, "2026-03-12T10:00:00Z")
        flag = project_root / ".claude" / "pre-compact-fired"
        assert flag.exists()
        assert flag.read_text(encoding="utf-8") == "2026-03-12T10:00:00Z\n"

    def test_overwrites_existing_flag(self, project_root: Path, pre_compact):
        pre_compact.write_pre_compact_flag(project_root, "2026-03-12T10:00:00Z")
        pre_compact.write_pre_compact_flag(project_root, "2026-03-12T11:00:00Z")
        flag = project_root / ".claude" / "pre-compact-fired"
        assert flag.read_text(encoding="utf-8") == "2026-03-12T11:00:00Z\n"


class TestUpdateSessionState:
    """update_session_state のテスト。"""

    def test_appends_section_when_missing(self, project_root: Path, pre_compact):
        ss = project_root / "SESSION_STATE.md"
        ss.write_text("# SESSION_STATE\n**日時**: 2026-03-12\n", encoding="utf-8")
        pre_compact.update_session_state(ss, "2026-03-12T10:00:00Z")
        content = ss.read_text(encoding="utf-8")
        assert "## PreCompact 発火" in content
        assert "- 時刻: 2026-03-12T10:00:00Z" in content

    def test_updates_existing_section(self, project_root: Path, pre_compact):
        ss = project_root / "SESSION_STATE.md"
        ss.write_text(
            "# SESSION_STATE\n\n## PreCompact 発火\n- 時刻: 2026-03-12T09:00:00Z\n",
            encoding="utf-8",
        )
        pre_compact.update_session_state(ss, "2026-03-12T10:00:00Z")
        content = ss.read_text(encoding="utf-8")
        assert "- 時刻: 2026-03-12T10:00:00Z" in content
        assert "09:00:00Z" not in content

    def test_idempotent_double_call(self, project_root: Path, pre_compact):
        ss = project_root / "SESSION_STATE.md"
        ss.write_text("# SESSION_STATE\n", encoding="utf-8")
        pre_compact.update_session_state(ss, "2026-03-12T10:00:00Z")
        pre_compact.update_session_state(ss, "2026-03-12T11:00:00Z")
        content = ss.read_text(encoding="utf-8")
        assert content.count("## PreCompact 発火") == 1
        assert "- 時刻: 2026-03-12T11:00:00Z" in content


    def test_preserves_content_after_precompact_section(self, project_root: Path, pre_compact):
        """PreCompact セクションの後に別セクションがある場合、それを保持すること。"""
        ss = project_root / "SESSION_STATE.md"
        ss.write_text(
            "# SESSION_STATE\n\n"
            "## PreCompact 発火\n- 時刻: 2026-03-12T09:00:00Z\n\n"
            "## 次のステップ\n1. 何かする\n",
            encoding="utf-8",
        )
        pre_compact.update_session_state(ss, "2026-03-12T10:00:00Z")
        content = ss.read_text(encoding="utf-8")
        assert "- 時刻: 2026-03-12T10:00:00Z" in content
        assert "## 次のステップ" in content
        assert "1. 何かする" in content


class TestFallbackLog:
    """fallback_log のテスト。"""

    def test_writes_to_loop_log(self, project_root: Path, pre_compact):
        pre_compact.fallback_log(project_root, "2026-03-12T10:00:00Z")
        log = project_root / ".claude" / "logs" / "loop.log"
        assert log.exists()
        content = log.read_text(encoding="utf-8")
        assert "2026-03-12T10:00:00Z" in content
        assert "PreCompact fired" in content

    def test_appends_on_multiple_calls(self, project_root: Path, pre_compact):
        """複数回呼び出し時に追記されること。"""
        pre_compact.fallback_log(project_root, "2026-03-12T10:00:00Z")
        pre_compact.fallback_log(project_root, "2026-03-12T11:00:00Z")
        log = project_root / ".claude" / "logs" / "loop.log"
        content = log.read_text(encoding="utf-8")
        assert "10:00:00Z" in content
        assert "11:00:00Z" in content


class TestBackupLoopState:
    """backup_loop_state のテスト。"""

    def test_creates_backup_when_exists(self, project_root: Path, pre_compact):
        state_file = project_root / ".claude" / "lam-loop-state.json"
        state_file.write_text('{"active": true}', encoding="utf-8")
        pre_compact.backup_loop_state(project_root)
        bak = state_file.with_suffix(".json.bak")
        assert bak.exists()
        assert bak.read_text(encoding="utf-8") == '{"active": true}'

    def test_no_error_when_missing(self, project_root: Path, pre_compact):
        pre_compact.backup_loop_state(project_root)
        bak = project_root / ".claude" / "lam-loop-state.json.bak"
        assert not bak.exists()


class TestMainIntegration:
    """main() の統合テスト。"""

    def test_main_with_session_state(self, project_root: Path, pre_compact, monkeypatch):
        ss = project_root / "SESSION_STATE.md"
        ss.write_text("# SESSION_STATE\n", encoding="utf-8")
        state_file = project_root / ".claude" / "lam-loop-state.json"
        state_file.write_text('{"active": true}', encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            pre_compact.main()
        assert exc_info.value.code == 0

        flag = project_root / ".claude" / "pre-compact-fired"
        assert flag.exists()
        assert "## PreCompact 発火" in ss.read_text(encoding="utf-8")
        assert state_file.with_suffix(".json.bak").exists()

    def test_main_without_session_state(self, project_root: Path, pre_compact, monkeypatch):
        with pytest.raises(SystemExit) as exc_info:
            pre_compact.main()
        assert exc_info.value.code == 0

        flag = project_root / ".claude" / "pre-compact-fired"
        assert flag.exists()
        log = project_root / ".claude" / "logs" / "loop.log"
        assert log.exists()

    def test_main_exits_zero_on_exception(self, project_root: Path, pre_compact, monkeypatch):
        """例外発生時も exit 0 で正常終了すること（圧縮をブロックしない）。"""
        # .claude ディレクトリを削除して write_pre_compact_flag を失敗させる
        import shutil
        shutil.rmtree(project_root / ".claude")
        with pytest.raises(SystemExit) as exc_info:
            pre_compact.main()
        assert exc_info.value.code == 0
