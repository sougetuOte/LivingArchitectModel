"""test_settings_autonomous.py - 層1（permissions.deny 決定的層）の内容テスト。

T1-4 層1（design D7）: autonomous 専用 settings `.claude/settings.autonomous.json` を
`claude --settings` で起動時注入し、FR9_PATTERNS への書込を override 不可で deny する。
共有 settings.json には置かない（自己ロック回避・選択肢2）。

本テストは実プロジェクトの settings.autonomous.json（コミット対象の宣言的成果物）を読み、
以下の不変条件を検証する:
  - JSON として妥当で permissions.deny を持つ
  - 層2 _FR9_PATTERNS（pre-tool-use.py）の5パス系列を Edit+Write 併記で網羅（二重防御の整合）
  - FR-3.4 spec freeze（docs/specs/**）を Edit+Write 併記で deny（FR-9 とは別系統・成果物の即時停止）
  - disableBypassPermissionsMode=disable（bypass 経由の deny 回避封鎖）
  - defaultMode=auto（auto mode 既定・FR-2 利便層）

裏取り: docs/artifacts/research/2026-06-01-layer1-settings/findings.md
対応仕様: docs/specs/autonomous-mode/design.md D7 / tasks.md T1-4(b) / FR-9.1 / SC-7
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# テストファイルは .claude/hooks/tests/ にあるため parents[3] が実プロジェクトルート。
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_SETTINGS_FILE = _PROJECT_ROOT / ".claude" / "settings.autonomous.json"

# 層2 _FR9_PATTERNS（pre-tool-use.py）に対応する層1 deny のパス glob。
# 二重防御として層1 deny は層2 の全パス系列をミラーしなければならない。
_FR9_DENY_PATHS = (
    "/.claude/rules/**",
    "/docs/adr/**",
    "/.claude/settings*.json",
    "/.claude/hooks/**",
    "/.claude/skills/autonomous/**",
)

# FR-3.4 spec freeze（requirements FR-3.4・design D2/D7 層1）の層1 deny パス。
# spec は FR-9 統治ファイルではなく成果物だが、FR-3.4 が「spec 書換」を即時ハードストップに
# 明示列挙するため層1 でも deny する（FR-9 とは別系統）。
_FR34_SPEC_DENY_PATH = "/docs/specs/**"


@pytest.fixture(scope="module")
def settings() -> dict:
    """実プロジェクトの settings.autonomous.json を読み込む。"""
    assert _SETTINGS_FILE.is_file(), f"層1 settings が存在しない: {_SETTINGS_FILE}"
    return json.loads(_SETTINGS_FILE.read_text(encoding="utf-8"))


class TestLayer1Settings:
    """層1 permissions.deny の決定的境界を検証（design D7・SC-7）。"""

    def test_settings_file_exists(self) -> None:
        """settings.autonomous.json が実在する（design §7 出力ファイル）。"""
        assert _SETTINGS_FILE.is_file()

    def test_valid_json_with_permissions(self, settings: dict) -> None:
        """JSON 妥当・permissions.deny を持つ。"""
        assert isinstance(settings.get("permissions"), dict)
        assert isinstance(settings["permissions"].get("deny"), list)

    @pytest.mark.parametrize("path", _FR9_DENY_PATHS)
    def test_fr9_path_denied_for_edit_and_write(self, settings: dict, path: str) -> None:
        """各 FR9 パスが Edit+Write 併記で deny される（防御的・NotebookEdit 未確認対策）。"""
        deny = settings["permissions"]["deny"]
        assert f"Edit({path})" in deny, f"Edit deny 欠落: {path}"
        assert f"Write({path})" in deny, f"Write deny 欠落: {path}"

    def test_fr34_spec_path_denied_for_edit_and_write(self, settings: dict) -> None:
        """FR-3.4 spec freeze: docs/specs/** が Edit+Write 併記で deny される（FR-9 とは別系統）。"""
        deny = settings["permissions"]["deny"]
        assert f"Edit({_FR34_SPEC_DENY_PATH})" in deny, f"Edit spec deny 欠落: {_FR34_SPEC_DENY_PATH}"
        assert f"Write({_FR34_SPEC_DENY_PATH})" in deny, f"Write spec deny 欠落: {_FR34_SPEC_DENY_PATH}"

    def test_disable_bypass_permissions_mode(self, settings: dict) -> None:
        """bypassPermissions 経由の deny 回避を封鎖する。"""
        assert settings["permissions"].get("disableBypassPermissionsMode") == "disable"

    def test_default_mode_auto(self, settings: dict) -> None:
        """auto mode を既定にする（FR-2 利便層・classifier）。"""
        assert settings["permissions"].get("defaultMode") == "auto"

    def test_deny_only_no_allow_widening(self, settings: dict) -> None:
        """層1 は deny 専用。allow による権限拡大を持たない（自己ロック回避と別に、

        専用 settings が誤って権限を緩めないことを保証）。"""
        assert "allow" not in settings["permissions"], (
            "層1 settings に allow を置かない（deny 専用の決定的境界）"
        )
