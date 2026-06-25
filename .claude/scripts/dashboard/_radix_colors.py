"""_radix_colors.py — Radix Colors パレット定数（W6-B5-T32 で作成）

取得元:
  ライト: https://github.com/radix-ui/colors/blob/main/src/light.ts
  ダーク:  https://github.com/radix-ui/colors/blob/main/src/dark.ts

取得日: 2026-06-25

スケール: gray / blue / green / amber × 12 step × 2 テーマ = 96 値

公開定数:
  RADIX_LIGHT: dict[str, dict[int, str]]  ライトテーマ Radix スケール変数
  RADIX_DARK:  dict[str, dict[int, str]]  ダークテーマ Radix スケール変数

キー形式:
  外側キー = 色名（str）: "gray" | "blue" | "green" | "amber"
  内側キー = step 番号（int）: 1〜12
  値 = hex カラーコード（str）: "#xxxxxx"（小文字 6 桁）
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# Layer 1: Radix Colors ライトテーマ スケール変数
# 転記元: https://github.com/radix-ui/colors/blob/main/src/light.ts
# ─────────────────────────────────────────────────────────────────────────────

RADIX_LIGHT: dict[str, dict[int, str]] = {
    "gray": {
        1: "#fcfcfc",
        2: "#f9f9f9",
        3: "#f0f0f0",
        4: "#e8e8e8",
        5: "#e0e0e0",
        6: "#d9d9d9",
        7: "#cecece",
        8: "#bbbbbb",
        9: "#8d8d8d",
        10: "#838383",
        11: "#646464",
        12: "#202020",
    },
    "blue": {
        1: "#fbfdff",
        2: "#f4faff",
        3: "#e6f4fe",
        4: "#d5efff",
        5: "#c2e5ff",
        6: "#acd8fc",
        7: "#8ec8f6",
        8: "#5eb1ef",
        9: "#0090ff",
        10: "#0588f0",
        11: "#0d74ce",
        12: "#113264",
    },
    "green": {
        1: "#fbfefc",
        2: "#f4fbf6",
        3: "#e6f6eb",
        4: "#d6f1df",
        5: "#c4e8d1",
        6: "#adddc0",
        7: "#8eceaa",
        8: "#5bb98b",
        9: "#30a46c",
        10: "#2b9a66",
        11: "#218358",
        12: "#193b2d",
    },
    "amber": {
        1: "#fefdfb",
        2: "#fefbe9",
        3: "#fff7c2",
        4: "#ffee9c",
        5: "#fbe577",
        6: "#f3d673",
        7: "#e9c162",
        8: "#e2a336",
        9: "#ffc53d",
        10: "#ffba18",
        11: "#ab6400",
        12: "#4f3422",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Layer 1: Radix Colors ダークテーマ スケール変数
# 転記元: https://github.com/radix-ui/colors/blob/main/src/dark.ts
# ─────────────────────────────────────────────────────────────────────────────

RADIX_DARK: dict[str, dict[int, str]] = {
    "gray": {
        1: "#111111",
        2: "#191919",
        3: "#222222",
        4: "#2a2a2a",
        5: "#313131",
        6: "#3a3a3a",
        7: "#484848",
        8: "#606060",
        9: "#6e6e6e",
        10: "#7b7b7b",
        11: "#b4b4b4",
        12: "#eeeeee",
    },
    "blue": {
        1: "#0d1520",
        2: "#111927",
        3: "#0d2847",
        4: "#003362",
        5: "#004074",
        6: "#104d87",
        7: "#205d9e",
        8: "#2870bd",
        9: "#0090ff",
        10: "#3b9eff",
        11: "#70b8ff",
        12: "#c2e6ff",
    },
    "green": {
        1: "#0e1512",
        2: "#121b17",
        3: "#132d21",
        4: "#113b29",
        5: "#174933",
        6: "#20573e",
        7: "#28684a",
        8: "#2f7c57",
        9: "#30a46c",
        10: "#33b074",
        11: "#3dd68c",
        12: "#b1f1cb",
    },
    "amber": {
        1: "#16120c",
        2: "#1d180f",
        3: "#302008",
        4: "#3f2700",
        5: "#4d3000",
        6: "#5c3d05",
        7: "#714f19",
        8: "#8f6424",
        9: "#ffc53d",
        10: "#ffd60a",
        11: "#ffca16",
        12: "#ffe7b3",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# 構造検証（import 時に実行）
# ─────────────────────────────────────────────────────────────────────────────

_EXPECTED_COLORS = {"gray", "blue", "green", "amber"}
_EXPECTED_STEPS = set(range(1, 13))

assert set(RADIX_LIGHT.keys()) == _EXPECTED_COLORS, "RADIX_LIGHT: 色名が期待値と不一致"
assert set(RADIX_DARK.keys()) == _EXPECTED_COLORS, "RADIX_DARK: 色名が期待値と不一致"
assert all(set(v.keys()) == _EXPECTED_STEPS for v in RADIX_LIGHT.values()), (
    "RADIX_LIGHT: step 1-12 が揃っていない色が存在する"
)
assert all(set(v.keys()) == _EXPECTED_STEPS for v in RADIX_DARK.values()), (
    "RADIX_DARK: step 1-12 が揃っていない色が存在する"
)
