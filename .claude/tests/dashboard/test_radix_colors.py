"""test_radix_colors.py - Radix Colors 定数モジュールの smoke test（W6-B5-T32）

対応仕様:
  - docs/specs/b4-dashboard/wave6/tasks.md §6 T32
  - docs/specs/b4-dashboard/wave6/design.md §6 Layer 1
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# .claude/scripts を sys.path に追加（既存テストと同じパターン）
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from dashboard._radix_colors import RADIX_DARK, RADIX_LIGHT

_EXPECTED_COLORS = {"gray", "blue", "green", "amber"}
_EXPECTED_STEPS = set(range(1, 13))
_HEX_PATTERN = re.compile(r"^#[0-9a-f]{6}$")


def test_light_has_four_colors() -> None:
    """RADIX_LIGHT に gray/blue/green/amber の 4 色が含まれること。"""
    assert set(RADIX_LIGHT.keys()) == _EXPECTED_COLORS


def test_dark_has_four_colors() -> None:
    """RADIX_DARK に gray/blue/green/amber の 4 色が含まれること。"""
    assert set(RADIX_DARK.keys()) == _EXPECTED_COLORS


def test_each_color_has_steps_1_to_12() -> None:
    """各色テーマで step 1〜12 がすべて揃うこと。"""
    for theme_name, theme in [("light", RADIX_LIGHT), ("dark", RADIX_DARK)]:
        for color_name, steps in theme.items():
            assert set(steps.keys()) == _EXPECTED_STEPS, (
                f"{theme_name}.{color_name}: step keys が {_EXPECTED_STEPS} と一致しない"
            )


def test_all_hex_values_are_valid_format() -> None:
    """全 hex 値が #[0-9a-f]{6} 形式（小文字 6 桁）であること。"""
    for theme_name, theme in [("light", RADIX_LIGHT), ("dark", RADIX_DARK)]:
        for color_name, steps in theme.items():
            for step, hex_val in steps.items():
                assert _HEX_PATTERN.match(hex_val), (
                    f"{theme_name}.{color_name}.{step} = {hex_val!r} が #[0-9a-f]{{6}} 形式でない"
                )


def test_total_96_values() -> None:
    """RADIX_LIGHT + RADIX_DARK の合計が 96 値（4 色 × 12 step × 2 テーマ）であること。"""
    light_count = sum(len(steps) for steps in RADIX_LIGHT.values())
    dark_count = sum(len(steps) for steps in RADIX_DARK.values())
    assert light_count == 48, f"RADIX_LIGHT: 期待 48 値、実際 {light_count} 値"
    assert dark_count == 48, f"RADIX_DARK: 期待 48 値、実際 {dark_count} 値"
