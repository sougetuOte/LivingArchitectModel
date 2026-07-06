"""R1-032 前倒し修正: _determine_by_command shell metachar チェック TDD.

pre-tool-use.py の AUDITING PG コマンド判定 (`_determine_by_command`) は、
`_PG_BLACKLISTED_ARGS` (フラグ名のみ) しかチェックせず、`;` / `&&` / `||` / `|`
/ `` ` `` / `$()` の shell 連結・置換演算子を素通ししていた。
settings.json L4-32 の allow パターン (`Bash(ruff format *)`) も prefix ベース
のため、`ruff format x.py; rm -rf /tmp` が二重防御両層 (settings.json allow +
hook PG 判定) で通過するリスクがある (R1-032 / W-R1 S3 で起票)。

本テストは:
- Red: 各種 shell メタ文字を含む PG プレフィックスコマンドが PM に降格されることを assert
- Green: 修正実装後に PASS
- Regression guard: 通常の PG コマンド / 既存 blacklisted arg 判定は退行させない

親 issue: `docs/artifacts/r-1-audit-tracker.md` R1-032
根拠 evidence: `.claude/hooks/pre-tool-use.py` L163-181 (修正前) / L65-70 コメントの「二重防御」設計意図
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parents[2] / "hooks"
sys.path.insert(0, str(_HOOKS_DIR))

_spec = importlib.util.spec_from_file_location(
    "pre_tool_use_under_test", _HOOKS_DIR / "pre-tool-use.py"
)
pre_tool_use = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pre_tool_use)


def _make_auditing_phase_file(tmp_path: Path) -> Path:
    """AUDITING フェーズ状態を模した current-phase.md fixture.

    `_read_current_phase` は `**PHASE**` 形式 (bold markdown) を正規表現で抽出する
    ため、fixture もその形式に合わせる。
    """
    phase_file = tmp_path / "current-phase.md"
    phase_file.write_text("**AUDITING**\n", encoding="utf-8")
    return phase_file


# ---- Red: shell metachar detection ----


def test_semicolon_composition_returns_pm(tmp_path):
    """`ruff format x.py; rm -rf /tmp` → PM (`;` によるコマンド連結)."""
    phase_file = _make_auditing_phase_file(tmp_path)
    level, reason = pre_tool_use._determine_by_command(
        "ruff format x.py; rm -rf /tmp", phase_file
    )
    assert level == "PM", f"expected PM, got {level!r} (reason={reason!r})"
    assert "metacharacter" in reason.lower() or "metachar" in reason.lower()


def test_and_operator_returns_pm(tmp_path):
    """`ruff format x.py && cat /etc/passwd` → PM (`&&` による連結)."""
    phase_file = _make_auditing_phase_file(tmp_path)
    level, _reason = pre_tool_use._determine_by_command(
        "ruff format x.py && cat /etc/passwd", phase_file
    )
    assert level == "PM"


def test_or_operator_returns_pm(tmp_path):
    """`ruff format x.py || echo failed` → PM (`||` による連結)."""
    phase_file = _make_auditing_phase_file(tmp_path)
    level, _reason = pre_tool_use._determine_by_command(
        "ruff format x.py || echo failed", phase_file
    )
    assert level == "PM"


def test_pipe_returns_pm(tmp_path):
    """`ruff format x.py | tee log.txt` → PM (パイプによる連結)."""
    phase_file = _make_auditing_phase_file(tmp_path)
    level, _reason = pre_tool_use._determine_by_command(
        "ruff format x.py | tee log.txt", phase_file
    )
    assert level == "PM"


def test_backtick_command_substitution_returns_pm(tmp_path):
    """``ruff format `cat evil.txt` `` → PM (backtick コマンド置換)."""
    phase_file = _make_auditing_phase_file(tmp_path)
    level, _reason = pre_tool_use._determine_by_command(
        "ruff format `cat evil.txt`", phase_file
    )
    assert level == "PM"


def test_dollar_paren_command_substitution_returns_pm(tmp_path):
    """`ruff format $(cat evil.txt)` → PM (`$()` コマンド置換)."""
    phase_file = _make_auditing_phase_file(tmp_path)
    level, _reason = pre_tool_use._determine_by_command(
        "ruff format $(cat evil.txt)", phase_file
    )
    assert level == "PM"


# ---- Regression guard: 既存の PG / PM 判定を退行させない ----


def test_normal_pg_command_still_pg(tmp_path):
    """通常の `ruff format src/foo.py` は PG のまま (regression guard)."""
    phase_file = _make_auditing_phase_file(tmp_path)
    level, _reason = pre_tool_use._determine_by_command(
        "ruff format src/foo.py", phase_file
    )
    assert level == "PG"


def test_pg_command_with_multiple_files_still_pg(tmp_path):
    """複数ファイル `ruff format src/foo.py src/bar.py` も PG のまま."""
    phase_file = _make_auditing_phase_file(tmp_path)
    level, _reason = pre_tool_use._determine_by_command(
        "ruff format src/foo.py src/bar.py", phase_file
    )
    assert level == "PG"


def test_blacklisted_arg_still_pm(tmp_path):
    """既存 `_PG_BLACKLISTED_ARGS` 判定は維持 (`--config` などフラグ名)."""
    phase_file = _make_auditing_phase_file(tmp_path)
    level, reason = pre_tool_use._determine_by_command(
        "ruff format --config /tmp/evil.toml x.py", phase_file
    )
    assert level == "PM"
    assert "blacklisted" in reason.lower()


def test_non_auditing_phase_bypasses_pg_check(tmp_path):
    """AUDITING 以外のフェーズでは PG 判定自体をスキップ (既存挙動保持)."""
    phase_file = tmp_path / "current-phase.md"
    phase_file.write_text("**BUILDING**\n", encoding="utf-8")
    level, _reason = pre_tool_use._determine_by_command(
        "ruff format x.py; rm -rf /tmp", phase_file
    )
    # AUDITING でないので PG 判定に入らず、default の SE を返す
    assert level == "SE"
